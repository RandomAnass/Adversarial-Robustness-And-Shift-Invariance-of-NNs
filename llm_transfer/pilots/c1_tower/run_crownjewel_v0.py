"""Crown-Jewel v0 pilot: MULTIMODAL invariance-vs-robustness dissociation on zero-shot CLIP.

Shows, on ImageNet-100 val, that TWO invariances are saturated across CLIP encoders --
  (a) SHIFT-consistency (visual, image circular shift)  [reused: diagnostics.shift_consistency]
  (b) PARAPHRASE-consistency (textual, prompt rewording) [NEW here, minimal]
-- while ADVERSARIAL robustness is a separate, dissociated axis that
  (c) eta/L1 (threat-matched Linf margin-to-Lipschitz) and gradient anisotropy A predict,
      but NEITHER consistency does.

All heavy lifting (margin/grad, SC, AutoAttack, per-image radius) is REUSED verbatim from
diagnostics.py / attacks.py / towers.py -- no attack or margin code is reimplemented.

The ONLY new piece is paraphrase-consistency: for each tower we build ONE text prototype per
class per paraphrase template (single-template head), classify with it, and measure the fraction
of paraphrase templates under which each image's top-1 is UNCHANGED vs the reference template
"a photo of a {}." (the textual analog of shift top-1 agreement).

To keep the panel internally consistent, every measurement (clean acc, margin, gradients,
attacks, SC, PC) is defined against the SAME reference single-template head "a photo of a {}.".

GPU 1 ONLY (set CUDA_VISIBLE_DEVICES=1). One tower at a time, del + empty_cache between towers.
"""
import os, json, time, argparse
import torch
import torch.nn.functional as F

import data, towers
import diagnostics as D
import attacks as A

RESULTS = "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower"
CACHE = os.path.join(RESULTS, "in100val_cache.pt")

# Reference single-template head (paraphrase-consistency is measured relative to this).
REFERENCE_TEMPLATE = "a photo of a {}."

# Curated SEMANTICALLY-EQUIVALENT paraphrases: all say "here is a {class}" in different words,
# WITHOUT changing the depicted object or its attributes. Selected from the standard OpenAI
# ImageNet 80-template ensemble (open_clip.OPENAI_IMAGENET_TEMPLATES); medium/quantity/size/
# quality/degradation templates are EXCLUDED (those are distribution shifts, not paraphrases).
PARAPHRASE_TEMPLATES = [
    "a photo of a {}.",        # == reference (self-consistency sanity = 1.0)
    "a photo of the {}.",
    "an image of a {}.",
    "a picture of a {}.",
    "a photo of one {}.",
    "a good photo of a {}.",
    "a close-up photo of a {}.",
    "a cropped photo of a {}.",
    "a bright photo of a {}.",
    "itap of a {}.",
    "a bad photo of a {}.",
]

# Panel: >=3 non-robust openai/laion + >=4 robust FARE/TeCoA (all ViT-L/14 base share text tower).
PANEL_NONROBUST = ["clip", "clip_b16_openai", "clip_b32_laion2b", "clip_l14_laion2b"]
PANEL_ROBUST = ["fare4", "tecoa4", "fare2", "tecoa2", "fare4_b32", "fare4_b16"]
DEFAULT_PANEL = PANEL_NONROBUST + PANEL_ROBUST


# ---------------------------------------------------------------------------
# Single-template text prototypes (isolates the effect of the wording).
# ---------------------------------------------------------------------------
@torch.no_grad()
def build_single_template_features(clip_model, tokenizer, class_names, template, device):
    """One text prototype per class from ONE template (no ensemble averaging)."""
    feats = []
    for name in class_names:
        primary = name.split(",")[0].strip()
        toks = tokenizer([template.format(primary)]).to(device)
        tf = clip_model.encode_text(toks)
        tf = F.normalize(tf, dim=-1)[0]
        feats.append(tf)
    return torch.stack(feats, 0)  # [n_classes, d]


def load_tower_with_reference_head(name, class_names, device):
    """Load an open_clip tower whose zero-shot head is the SINGLE reference template
    "a photo of a {}." (so margins/gradients/attacks/SC are defined against it), and also
    return the raw clip_model + tokenizer so we can build the paraphrase heads."""
    arch, pretrained = towers.CLIP_TOWERS[name]
    if pretrained is not None:
        model, _, _ = towers.open_clip.create_model_and_transforms(arch, pretrained=pretrained)
        tokenizer = towers.open_clip.get_tokenizer(arch)
    else:
        model, _, _ = towers.open_clip.create_model_and_transforms(arch)
        tokenizer = towers.open_clip.get_tokenizer("ViT-L-14")
    model = model.to(device).eval()
    for p in model.parameters():
        p.requires_grad_(False)
    ref_tf = build_single_template_features(model, tokenizer, class_names, REFERENCE_TEMPLATE, device)
    tower = towers.ClipZeroShot(model, ref_tf, towers.CLIP_MEAN, towers.CLIP_STD).to(device).eval()
    for p in tower.parameters():
        p.requires_grad_(False)
    return tower, model, tokenizer


@torch.no_grad()
def paraphrase_consistency(tower, clip_model, tokenizer, class_names, images, device,
                           templates, ref_template, bs=128):
    """PC per image = fraction of paraphrase templates under which top-1 == top-1(reference).

    `tower` already carries the reference head, so its predictions ARE the reference predictions.
    For each template we swap in that template's per-class prototypes, reclassify, and compare.
    Runs on the passed `images` (the correct-under-reference subset). Returns:
      pc (mean over images of fraction-agree), per-image fraction, and per-template agreement.
    """
    logit_scale = tower.logit_scale
    # embed images ONCE (reference and all paraphrases share the same image embeddings)
    embs = []
    ref_pred = []
    for i in range(0, len(images), bs):
        xb = images[i:i + bs].to(device)
        e = tower.encode(xb)  # normalized image embedding [b,d]
        embs.append(e)
        ref_logits = logit_scale * e @ tower.text_features.t()
        ref_pred.append(ref_logits.argmax(1))
    emb = torch.cat(embs)          # [N,d]
    ref_pred = torch.cat(ref_pred) # [N]
    N = len(ref_pred)
    n_tmpl = len(templates)
    agree_sum = torch.zeros(N, device=device)
    per_template = {}
    for t in templates:
        tf = build_single_template_features(clip_model, tokenizer, class_names, t, device)  # [C,d]
        logits = logit_scale * emb @ tf.t()
        pred = logits.argmax(1)
        agree = (pred == ref_pred).float()
        agree_sum += agree
        per_template[t] = agree.mean().item()
    pc_per_image = (agree_sum / n_tmpl).cpu()
    return {
        "pc": pc_per_image.mean().item(),
        "pc_per_image": pc_per_image,
        "per_template_agreement": per_template,
        "n_images": N,
        "n_templates": n_tmpl,
        "ref_template": ref_template,
    }


def run_tower(name, imgs, labels, class_names, args, device):
    t0 = time.time()
    tower, clip_model, tokenizer = load_tower_with_reference_head(name, class_names, device)
    res = {"tower": name, "robust": name in towers.ROBUST_TOWERS}
    print(f"[CJ]   tower built ({time.time()-t0:.0f}s)", flush=True)

    # 1. clean accuracy under the REFERENCE single-template head
    pred = D.predict(tower, imgs, bs=args.bs, device=device)
    correct = (pred == labels)
    res["clean_acc"] = correct.float().mean().item()
    res["n_eval"] = int(len(labels))
    ci = torch.where(correct)[0]           # correct-under-reference subset
    xi_all, yi_all = imgs[ci], labels[ci]

    # 2. margin + gradient diagnostics (reused) -> eta, L1, L2, eta/L1, per-image ratios, A
    diag = D.margin_and_grad(tower, imgs, labels, q_list=(1, 2), bs=args.diag_bs,
                             device=device, correct_only=True)
    summ = D.eta_L_summary(diag, q_list=(1, 2))
    res.update({k: v for k, v in summ.items() if not k.startswith("_")})
    # anisotropy A = ||grad M||_1 / ||grad M||_2 = per-image (ratio_l2 / ratio_l1); mean over correct
    r1 = summ["_per_image_ratio_L1"]
    r2 = summ["_per_image_ratio_L2"]
    aniso_per_image = (r2 / r1.clamp_min(1e-12))
    res["anisotropy_A"] = aniso_per_image.mean().item()
    print(f"[CJ]   eta/L1={res['eta_over_L1']:.5f} A={res['anisotropy_A']:.2f} "
          f"({time.time()-t0:.0f}s)", flush=True)

    # 3a. SHIFT-consistency (reused; repo's exact patch-grid phase set), correct subset
    offsets = D.patch_grid_offsets(max_shift=args.max_shift, step=1, compact=True)
    sc = D.shift_consistency(tower, imgs, labels, offsets, bs=args.bs, device=device,
                             base_correct_mask=diag["correct"], max_images=args.sc_max_images)
    res["sc_pred"] = sc["sc_pred"]
    res["sc_cos"] = sc["sc_cos"]
    res["n_offsets"] = sc["n_offsets"]

    # 3b. PARAPHRASE-consistency (NEW), on the correct-under-reference subset
    xi_pc = xi_all if args.pc_max_images is None or len(xi_all) <= args.pc_max_images \
        else xi_all[:args.pc_max_images]
    pc = paraphrase_consistency(tower, clip_model, tokenizer, class_names, xi_pc, device,
                                PARAPHRASE_TEMPLATES, REFERENCE_TEMPLATE, bs=args.bs)
    res["pc"] = pc["pc"]
    res["pc_per_template"] = pc["per_template_agreement"]
    res["pc_n_images"] = pc["n_images"]
    res["pc_n_templates"] = pc["n_templates"]
    # sanity: reference-vs-reference agreement must be exactly 1.0
    res["pc_self_check"] = pc["per_template_agreement"][REFERENCE_TEMPLATE]
    print(f"[CJ]   SC={res['sc_pred']:.4f} PC={res['pc']:.4f} "
          f"(self={res['pc_self_check']:.3f}) ({time.time()-t0:.0f}s)", flush=True)

    # 4. adversarial robustness: AutoAttack (APGD-CE + APGD-t), Linf, eps=4/255, correct subset
    if args.n_attack and len(ci) > args.n_attack:
        g = torch.Generator().manual_seed(0)
        sel = torch.randperm(len(ci), generator=g)[:args.n_attack]
        ci_a = ci[sel]
    else:
        ci_a = ci
    xi, yi = imgs[ci_a], labels[ci_a]
    res["n_attack"] = int(len(ci_a))
    res["S_apgd"] = {}
    for eps in args.eps:
        tag = f"{eps:.5f}"
        # non-AT towers -> S~0; short APGD confirms; AT towers get more iters
        n_iter = args.apgd_iters_at if res["robust"] else args.apgd_iters_nonat
        aa = A.run_autoattack(tower, xi, yi, eps, n_classes=len(class_names),
                              bs=args.attack_bs, device=device, square=False, n_iter=n_iter,
                              targeted=bool(args.targeted))
        res["S_apgd"][tag] = aa["robust_acc"]
    print(f"[CJ]   S_apgd={res['S_apgd']} ({time.time()-t0:.0f}s)", flush=True)

    # 5. per-image Linf robust radius (PGD bisection, reused) -> per-image Spearman material
    eps_grid = args.radius_grid
    nr = min(args.radius_max_images, len(ci_a))
    ci_r = ci_a[:nr]
    radius, flipped = A.per_image_robust_radius_linf(
        tower, imgs[ci_r], labels[ci_r], eps_grid, steps=args.radius_steps,
        bs=args.attack_bs, device=device)
    res["robust_radius_mean"] = float(radius.mean().item())
    res["robust_radius_median"] = float(radius.median().item())
    # align per-image eta/L1 ratio + anisotropy to the radius images (same mapping the repo uses)
    corr_idx = torch.where(diag["correct"])[0]
    pos = {int(v): k for k, v in enumerate(corr_idx.tolist())}
    sel = torch.tensor([pos[int(j)] for j in ci_r.tolist()])
    per_image = {
        "radius_idx": ci_r.cpu(), "labels": labels[ci_r].cpu(),
        "robust_radius_linf": radius.cpu(), "flipped": flipped.cpu(),
        "ratio_l1": summ["_per_image_ratio_L1"][sel].cpu(),
        "ratio_l2": summ["_per_image_ratio_L2"][sel].cpu(),
        "anisotropy_A": aniso_per_image[sel].cpu(),
        "margin": summ["_per_image_margin"][sel].cpu(),
    }
    torch.save(per_image, os.path.join(RESULTS, f"per_image_crownjewel_{name}.pt"))
    res["radius_grid"] = list(eps_grid)
    res["seconds"] = time.time() - t0

    del tower, clip_model
    torch.cuda.empty_cache()
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--towers", nargs="+", default=DEFAULT_PANEL)
    ap.add_argument("--n_diag", type=int, default=1000, help="images for clean/SC/PC/diag")
    ap.add_argument("--n_attack", type=int, default=300, help="correct imgs for AutoAttack")
    ap.add_argument("--eps", type=float, nargs="+", default=[4/255])
    ap.add_argument("--max_shift", type=int, default=8)
    ap.add_argument("--sc_max_images", type=int, default=800)
    ap.add_argument("--pc_max_images", type=int, default=800)
    ap.add_argument("--bs", type=int, default=128)
    ap.add_argument("--diag_bs", type=int, default=32)
    ap.add_argument("--attack_bs", type=int, default=16)
    ap.add_argument("--apgd_iters_at", type=int, default=100)
    ap.add_argument("--apgd_iters_nonat", type=int, default=50)
    ap.add_argument("--targeted", type=int, default=1,
                    help="1=APGD-CE+targeted-APGD (RobustBench-grade); 0=APGD-CE only (faster, "
                         "valid robust-acc upper bound; used for the v0 pilot on robust L/14 towers)")
    ap.add_argument("--radius_grid", type=float, nargs="+",
                    default=[0.25/255, 0.5/255, 1/255, 2/255, 3/255, 4/255, 6/255, 8/255])
    ap.add_argument("--radius_steps", type=int, default=20)
    ap.add_argument("--radius_max_images", type=int, default=200)
    ap.add_argument("--tag", type=str, default="v0")
    args = ap.parse_args()

    device = "cuda"
    class_names = data.get_class_names()
    imgs, labels = data.load_val(n=args.n_diag, seed=0, cache_path=CACHE)
    print(f"[CJ] loaded {len(labels)} val images @{imgs.shape[-1]}px; panel={args.towers}",
          flush=True)
    print(f"[CJ] reference template = {REFERENCE_TEMPLATE!r}; "
          f"{len(PARAPHRASE_TEMPLATES)} paraphrase templates", flush=True)

    all_res = []
    out_path = os.path.join(RESULTS, f"crownjewel_{args.tag}.json")
    for name in args.towers:
        print(f"[CJ] === tower {name} ===", flush=True)
        r = run_tower(name, imgs, labels, class_names, args, device)
        print(f"[CJ] {name}: clean={r['clean_acc']:.3f} SC={r['sc_pred']:.4f} PC={r['pc']:.4f} "
              f"eta/L1={r['eta_over_L1']:.5f} A={r['anisotropy_A']:.2f} "
              f"S={r['S_apgd']} rad_mean={r['robust_radius_mean']:.5f} ({r['seconds']:.0f}s)",
              flush=True)
        all_res.append(r)
        with open(out_path, "w") as f:
            json.dump({"args": vars(args),
                       "reference_template": REFERENCE_TEMPLATE,
                       "paraphrase_templates": PARAPHRASE_TEMPLATES,
                       "results": all_res}, f, indent=2, default=str)
    print(f"[CJ] DONE -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
