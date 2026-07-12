"""C1 EXTENDED panel (adversarial-verifier hardening).

Adds 6 NON-AT CLIP towers (varied pretraining corpora / patch size / capacity) to the
original 6-tower panel, so the eta/L robustness ranking is tested against genuinely diverse
non-AT encoders and is not merely an "AT detector" on a 4-vs-2 split. These non-AT towers are
Linf-non-robust; we confirm S~0 with a strong-but-shorter APGD (apgd-ce + apgd-t, 50 iters)
rather than the full 100-iter ensemble (which is only needed where S>0). We record
clean acc, SC_pred, SC_cos, eta, L1, L2, eta/L1, eta/L2, and S_apgd at eps in {2,4}/255,
plus per-image eta/L1 ratio + per-image robust radius on a FINER grid (sub-1/255) so
non-robust towers are not floored.

Everything encoder-level, GPU 1 only. Reads/writes results/c1_tower/*_ext.* and does NOT
overwrite the original c1_results_main.json (kept for provenance).
"""
import os, sys, json, time, argparse
import torch

import data, towers
import diagnostics as D
import attacks as A

RESULTS = "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower"
CACHE = os.path.join(RESULTS, "in100val_cache.pt")

# 6 new NON-AT CLIP towers (all Linf-non-robust, spanning eta/L + SC range)
EXT_PANEL = ["clip_l14_laion2b", "clip_l14_datacomp", "clip_b16_openai",
             "clip_b16_laion2b", "clip_b32_laion2b", "clip_l14_metaclip"]


def _t(msg, t0):
    print(f"[C1x]   .. {msg}: {time.time()-t0:.0f}s", flush=True)
    return time.time()


def run_tower(name, imgs, labels, class_names, args, device):
    t0 = time.time()
    tower = towers.load_clip_tower(name, class_names, device)
    res = {"tower": name}
    tk = _t("tower built", t0)

    pred = D.predict(tower, imgs, bs=args.bs, device=device)
    correct = (pred == labels)
    res["clean_acc"] = correct.float().mean().item()
    res["n_eval"] = int(len(labels))
    tk = _t("clean acc", tk)

    diag = D.margin_and_grad(tower, imgs, labels, q_list=(1, 2), bs=args.diag_bs,
                             device=device, correct_only=True)
    summ = D.eta_L_summary(diag, q_list=(1, 2))
    res.update({k: v for k, v in summ.items() if not k.startswith("_")})
    tk = _t("margin+grad", tk)

    offsets = D.patch_grid_offsets(max_shift=args.max_shift, step=1, compact=True)
    sc = D.shift_consistency(tower, imgs, labels, offsets, bs=args.bs, device=device,
                             base_correct_mask=diag["correct"], max_images=args.sc_max_images)
    res["sc_pred"] = sc["sc_pred"]
    res["sc_cos"] = sc["sc_cos"]
    res["n_offsets"] = sc["n_offsets"]
    tk = _t(f"SC ({sc['n_offsets']} off)", tk)

    ci = torch.where(correct)[0]
    if args.n_attack and len(ci) > args.n_attack:
        g = torch.Generator().manual_seed(0)
        ci = ci[torch.randperm(len(ci), generator=g)[:args.n_attack]]
    xi, yi = imgs[ci], labels[ci]
    res["n_attack"] = int(len(ci))

    res["S_apgd"], res["S_pgd40"], res["S_fgsm"] = {}, {}, {}
    for eps in args.eps:
        tag = f"{eps:.5f}"
        res["S_fgsm"][tag] = A.run_fgsm_eval(tower, xi, yi, eps, bs=args.bs, device=device)
        res["S_pgd40"][tag] = A.run_pgd_eval(tower, xi, yi, eps, steps=40, restarts=1,
                                             bs=args.attack_bs, device=device)
        aa = A.run_autoattack(tower, xi, yi, eps, n_classes=len(class_names),
                              bs=args.attack_bs, device=device, square=False,
                              n_iter=args.apgd_iters)
        res["S_apgd"][tag] = aa["robust_acc"]
        tk = _t(f"attacks eps={tag}", tk)

    # per-image radius on a FINER grid (sub-1/255) so non-robust towers are not floored
    eps_grid = args.radius_grid
    nr = min(args.radius_max_images, len(xi))
    ci_r = ci[:nr]
    radius, flipped = A.per_image_robust_radius_linf(
        tower, imgs[ci_r], labels[ci_r], eps_grid, steps=args.radius_steps,
        bs=args.attack_bs, device=device)
    per_image = {"radius_idx": ci_r.cpu(), "labels": labels[ci_r].cpu(),
                 "robust_radius_linf": radius.cpu(), "flipped": flipped.cpu()}
    corr_idx = torch.where(diag["correct"])[0]
    pos = {int(v): k for k, v in enumerate(corr_idx.tolist())}
    sel = torch.tensor([pos[int(j)] for j in ci_r.tolist()])
    per_image["ratio_l1"] = summ["_per_image_ratio_L1"][sel].cpu()
    per_image["ratio_l2"] = summ["_per_image_ratio_L2"][sel].cpu()
    per_image["margin"] = summ["_per_image_margin"][sel].cpu()
    torch.save(per_image, os.path.join(RESULTS, f"per_image_{name}_ext.pt"))
    tk = _t("per-image radius", tk)

    res["seconds"] = time.time() - t0
    del tower
    torch.cuda.empty_cache()
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--towers", nargs="+", default=EXT_PANEL)
    ap.add_argument("--n_diag", type=int, default=2000)
    ap.add_argument("--n_attack", type=int, default=300)
    ap.add_argument("--eps", type=float, nargs="+", default=[2/255, 4/255])
    ap.add_argument("--max_shift", type=int, default=8)
    ap.add_argument("--sc_max_images", type=int, default=800)
    ap.add_argument("--bs", type=int, default=128)
    ap.add_argument("--diag_bs", type=int, default=48)
    ap.add_argument("--attack_bs", type=int, default=64)
    # FINER low-end grid: 0.25/255 .. 8/255 so non-robust towers get real (non-floored) radii
    ap.add_argument("--radius_grid", type=float, nargs="+",
                    default=[0.25/255, 0.5/255, 1/255, 2/255, 3/255, 4/255, 6/255, 8/255])
    ap.add_argument("--radius_steps", type=int, default=20)
    ap.add_argument("--apgd_iters", type=int, default=50,
                    help="APGD iters for the non-AT confirm sweep (S~0); 100 for AT towers")
    ap.add_argument("--radius_max_images", type=int, default=300)
    ap.add_argument("--tag", type=str, default="ext")
    args = ap.parse_args()

    device = "cuda"
    class_names = data.get_class_names()
    imgs, labels = data.load_val(n=args.n_diag, seed=0, cache_path=CACHE)
    print(f"[C1x] loaded {len(labels)} val images; ext panel={args.towers}", flush=True)

    all_res = []
    out_path = os.path.join(RESULTS, f"c1_results_{args.tag}.json")
    for name in args.towers:
        print(f"[C1x] === tower {name} ===", flush=True)
        r = run_tower(name, imgs, labels, class_names, args, device)
        print(f"[C1x] {name}: clean={r['clean_acc']:.3f} SC={r['sc_pred']:.4f} "
              f"SCcos={r['sc_cos']:.4f} eta/L1={r['eta_over_L1']:.5f} "
              f"S_apgd={r['S_apgd']} ({r['seconds']:.0f}s)", flush=True)
        all_res.append(r)
        with open(out_path, "w") as f:
            json.dump({"args": vars(args), "results": all_res}, f, indent=2, default=str)
    print(f"[C1x] DONE -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
