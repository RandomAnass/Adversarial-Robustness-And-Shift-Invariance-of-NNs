"""C1 pilot driver: run the full tower panel end-to-end and dump per-tower + per-image results.

For each tower in the panel (common 224 px):
  1. clean zero-shot accuracy on ImageNet-100 val
  2. shift-consistency SC (patch-grid phase sweep) on the correct subset
  3. attack-free diagnostics: eta, L1 (threat-matched for Linf), L2 (mismatched), eta/L1, eta/L2
     + per-image margin and per-image ratio
  4. STRONG attack: AutoAttack (APGD-CE + APGD-DLR, +Square) -> robust zero-shot acc S
  5. gradient-masking audit: FGSM, PGD-40 robust acc (must be >= APGD); Square gap
  6. per-image Linf robust radius (PGD bisection over eps grid) for per-image Spearman

Outputs: results/c1_tower/c1_results_<tag>.json  (per-tower scalars + arrays)
         results/c1_tower/per_image_<tower>.pt   (per-image tensors)

Everything encoder-level, no decoder. GPU 1 only (set by caller via CUDA_VISIBLE_DEVICES=1).
"""
import os, sys, json, time, argparse
import torch

import data, towers
import diagnostics as D
import attacks as A

RESULTS = "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower"
CACHE = os.path.join(RESULTS, "in100val_cache.pt")
DINO_HEAD = os.path.join(RESULTS, "dinov2_head.pt")

PANEL = ["clip", "fare2", "fare4", "tecoa2", "tecoa4", "dinov2", "clip_aa"]


def build_tower(name, class_names, device):
    if name == "dinov2":
        bb = towers.load_dinov2_backbone(device)
        h = torch.load(DINO_HEAD, map_location=device)
        t = towers.LinearProbeZeroShot(bb, h["head_w"].to(device), h["head_b"].to(device),
                                       towers.IN_MEAN, towers.IN_STD).to(device).eval()
        for p in t.parameters():
            p.requires_grad_(False)
        return t
    if name == "clip_aa":
        return towers.load_clip_tower("clip", class_names, device, anti_alias=True, blur_size=3)
    return towers.load_clip_tower(name, class_names, device)


def _t(msg, t0):
    print(f"[C1]   .. {msg}: {time.time()-t0:.0f}s", flush=True)
    return time.time()


def run_tower(name, imgs, labels, class_names, args, device):
    t0 = time.time()
    tower = build_tower(name, class_names, device)
    res = {"tower": name}
    tk = _t("tower built", t0)

    # 1. clean accuracy
    pred = D.predict(tower, imgs, bs=args.bs, device=device)
    correct = (pred == labels)
    res["clean_acc"] = correct.float().mean().item()
    res["n_eval"] = int(len(labels))
    tk = _t("clean acc", tk)

    # 2 + 3. diagnostics on the full eval set (margin/grad); eta,L over correct
    diag = D.margin_and_grad(tower, imgs, labels, q_list=(1, 2), bs=args.diag_bs,
                             device=device, correct_only=True)
    summ = D.eta_L_summary(diag, q_list=(1, 2))
    res.update({k: v for k, v in summ.items() if not k.startswith("_")})
    tk = _t("margin+grad diagnostics", tk)

    # SC on the SAME correct subset (round2_C fix 5)
    offsets = D.patch_grid_offsets(max_shift=args.max_shift, step=args.shift_step,
                                   compact=args.sc_compact)
    sc = D.shift_consistency(tower, imgs, labels, offsets, bs=args.bs, device=device,
                             base_correct_mask=diag["correct"], max_images=args.sc_max_images)
    res["sc_pred"] = sc["sc_pred"]
    res["sc_cos"] = sc["sc_cos"]
    res["n_offsets"] = sc["n_offsets"]
    tk = _t(f"SC ({sc['n_offsets']} offsets)", tk)

    # attack subset: correctly-classified images (standard robust-acc convention)
    ci = torch.where(correct)[0]
    if args.n_attack and len(ci) > args.n_attack:
        g = torch.Generator().manual_seed(0)
        ci = ci[torch.randperm(len(ci), generator=g)[:args.n_attack]]
    xi = imgs[ci]
    yi = labels[ci]
    res["n_attack"] = int(len(ci))

    # 5. masking audit: FGSM, PGD-40 (cheap), then STRONG AutoAttack (apgd-ce+apgd-t),
    #    then Square (black-box) for the masking gap.
    res["eps_list"] = args.eps
    (res["S_apgd"], res["S_pgd40"], res["S_fgsm"],
     res["S_square"], res["S_square_gap"]) = {}, {}, {}, {}, {}
    per_image = {"attack_idx": ci.cpu(), "labels": yi.cpu()}
    for eps in args.eps:
        tag = f"{eps:.5f}"
        res["S_fgsm"][tag] = A.run_fgsm_eval(tower, xi, yi, eps, bs=args.bs, device=device)
        res["S_pgd40"][tag] = A.run_pgd_eval(tower, xi, yi, eps, steps=40, restarts=1,
                                             bs=args.attack_bs, device=device)
        # STRONG white-box: AutoAttack apgd-ce + targeted apgd-dlr (no square) = headline S
        aa = A.run_autoattack(tower, xi, yi, eps, n_classes=len(class_names),
                              bs=args.attack_bs, device=device, square=False)
        res["S_apgd"][tag] = aa["robust_acc"]
        # black-box Square on the same subset -> masking gap = S_square - S_apgd (>=0 if no masking)
        sq = A.run_square_gap(tower, xi, yi, eps, bs=args.attack_bs, device=device,
                              n_queries=args.square_queries)
        res["S_square"][tag] = sq
        res["S_square_gap"][tag] = sq - aa["robust_acc"]
        tk = _t(f"attacks eps={tag} (FGSM/PGD40/APGD/Square)", tk)

    # 6. per-image Linf robust radius via PGD bisection (for per-image Spearman)
    if args.per_image_radius:
        eps_grid = args.radius_grid
        # radius on a capped subset (7-eps PGD sweep is expensive); enough for per-image Spearman
        nr = min(args.radius_max_images, len(xi))
        ci_r = ci[:nr]
        radius, flipped = A.per_image_robust_radius_linf(
            tower, imgs[ci_r], labels[ci_r], eps_grid, steps=args.radius_steps,
            bs=args.attack_bs, device=device)
        per_image["radius_idx"] = ci_r.cpu()
        per_image["robust_radius_linf"] = radius.cpu()
        per_image["flipped"] = flipped.cpu()
        # align per-image eta/L1 ratio to the radius images:
        corr_idx = torch.where(diag["correct"])[0]
        pos = {int(v): k for k, v in enumerate(corr_idx.tolist())}
        ratio1 = summ["_per_image_ratio_L1"]
        ratio2 = summ["_per_image_ratio_L2"]
        marg = summ["_per_image_margin"]
        sel = torch.tensor([pos[int(j)] for j in ci_r.tolist()])
        ci = ci_r  # per-image arrays below align to the radius subset
        per_image["ratio_l1"] = ratio1[sel].cpu()
        per_image["ratio_l2"] = ratio2[sel].cpu()
        per_image["margin"] = marg[sel].cpu()
        # SC per-image is defined only on the SC subset (positions within the correct set);
        # map each attack image to its SC value if present, else NaN.
        sc_pos = sc["sc_subset_pos"].tolist()  # positions within correct set
        sc_val = sc["sc_pred_per_image"]       # aligned to sc_subset_pos order
        sc_lookup = {int(p): float(sc_val[k]) for k, p in enumerate(sc_pos)}
        sc_aligned = torch.tensor(
            [sc_lookup.get(int(pos[int(j)]), float("nan")) for j in ci.tolist()])
        per_image["sc_pred_per_image"] = sc_aligned
        tk = _t("per-image robust radius", tk)

    torch.save(per_image, os.path.join(RESULTS, f"per_image_{name}_{args.tag}.pt"))
    res["seconds"] = time.time() - t0
    del tower
    torch.cuda.empty_cache()
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--towers", nargs="+", default=PANEL)
    ap.add_argument("--n_diag", type=int, default=2000, help="images for clean/SC/diag")
    ap.add_argument("--n_attack", type=int, default=1000, help="correct imgs for attacks")
    ap.add_argument("--eps", type=float, nargs="+", default=[2/255, 4/255])
    ap.add_argument("--max_shift", type=int, default=8)
    ap.add_argument("--shift_step", type=int, default=2)
    ap.add_argument("--sc_max_images", type=int, default=800,
                    help="cap SC image count (SC is a mean; bounds O(n_off x N) cost)")
    ap.add_argument("--sc_compact", action="store_true", default=True,
                    help="use a representative ~12-offset phase set (bounds SC cost)")
    ap.add_argument("--bs", type=int, default=128)
    ap.add_argument("--diag_bs", type=int, default=48)
    ap.add_argument("--attack_bs", type=int, default=64)
    ap.add_argument("--per_image_radius", action="store_true", default=True)
    ap.add_argument("--radius_grid", type=float, nargs="+",
                    default=[0.5/255, 1/255, 2/255, 3/255, 4/255, 6/255, 8/255])
    ap.add_argument("--radius_steps", type=int, default=25)
    ap.add_argument("--radius_max_images", type=int, default=400)
    ap.add_argument("--square_queries", type=int, default=2000)
    ap.add_argument("--tag", type=str, default="main")
    args = ap.parse_args()

    device = "cuda"
    class_names = data.get_class_names()
    imgs, labels = data.load_val(n=args.n_diag, seed=0, cache_path=CACHE)
    print(f"[C1] loaded {len(labels)} val images at {imgs.shape[-1]}px; panel={args.towers}",
          flush=True)

    all_res = []
    out_path = os.path.join(RESULTS, f"c1_results_{args.tag}.json")
    for name in args.towers:
        print(f"[C1] === tower {name} ===", flush=True)
        r = run_tower(name, imgs, labels, class_names, args, device)
        print(f"[C1] {name}: clean={r['clean_acc']:.3f} SC={r['sc_pred']:.4f} "
              f"eta/L1={r['eta_over_L1']:.5f} "
              f"S_apgd={r['S_apgd']} S_pgd40={r['S_pgd40']} ({r['seconds']:.0f}s)", flush=True)
        all_res.append(r)
        # incremental save
        with open(out_path, "w") as f:
            json.dump({"args": vars(args), "results": all_res}, f, indent=2, default=str)
    print(f"[C1] DONE -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
