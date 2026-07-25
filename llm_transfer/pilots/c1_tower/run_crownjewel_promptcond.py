"""Crown-Jewel PROMPT-CONDITIONED pilot: image-adversarial robustness measured ACROSS a set of
meaning-preserving TEXT PROMPTS, in parallel (the "image attack x text prompts" strong design).

MOTIVATION. The hardened crown-jewel showed the image-adversarial cell S spreads (0.385+-0.236)
and threat-matched eta/L1 predicts it (+0.80 cross-tower, +0.89 per-image), while BOTH invariance
cells (shift-consistency SC, paraphrase-consistency PC) saturate (~0.977) and the text-worst-case
cell S_text is narrow (0.896+-0.029). The text-adversarial axis was too mild to carry signal.

This pilot keeps the ATTACK on the image (where the spread lives) but runs it AGAINST K different
meaning-preserving TEXT PROMPTS in parallel. For EACH (encoder, prompt) we build the zero-shot
classification head from THAT prompt's single-template text prototypes and measure, conditioned on
that head:
  * clean accuracy,
  * IMAGE-adversarial robust accuracy: threat-matched FULL targeted AutoAttack (APGD-CE + APGD-T,
    Linf eps=4/255) on n_attack images correct-under-that-prompt, AND per-image Linf robust radius
    (PGD bisection) on a sub-subset,
  * the threat-matched diagnostic eta/L1 and gradient anisotropy A on the margin gradient of THAT
    prompt's head,
and, once per ENCODER (prompt-independent / prompt-set-level):
  * shift-consistency SC (image circular shift; reference head),
  * paraphrase-consistency PC across the K-prompt set.
We ALSO build an ENSEMBLE head (mean of the K single-prompt text embeddings, L2-normalized = the
standard CLIP prompt ensemble = a form of textual invariance) and measure the SAME image-adversarial
quantities under it, for analysis (B).

For cross-prompt adversarial transfer (analysis C, "in parallel"), we SAVE the adversarial images
crafted under each prompt (and under the ensemble) and evaluate whether they still flip the label
under EVERY OTHER prompt's head. Transfer quantifies whether the vulnerability is a property of the
IMAGE ENCODER (transfers across prompts) or of the specific prompt.

REUSES verbatim: diagnostics.margin_and_grad / eta_L_summary / shift_consistency / predict,
attacks.run_autoattack / per_image_robust_radius_linf, towers.ClipZeroShot / CLIP_MEAN/STD,
run_crownjewel_v0.{build_single_template_features, paraphrase_consistency, PARAPHRASE_TEMPLATES,
REFERENCE_TEMPLATE}, run_crownjewel_hardened.{load_tower_dispatch, wait_for_gpu, _phys_gpu_index}.
No attack / margin / radius code is reimplemented; only the head is swapped per prompt.

GPU 1 ONLY (CUDA_VISIBLE_DEVICES=1). Shared GPU: one encoder at a time, small attack_bs, a
pre-encoder free-memory guard, del + empty_cache between encoders. Per-ENCODER JSON checkpoint
(each encoder writes all its (prompt) cells at once) so the run is resumable at encoder granularity.
"""
import os, json, time, argparse, signal
import torch
import torch.nn.functional as F

import data, towers
import diagnostics as D
import attacks as A
import run_crownjewel_v0 as CJ
import run_crownjewel_hardened as CJH
from run_crownjewel_v0 import (REFERENCE_TEMPLATE, build_single_template_features,
                               paraphrase_consistency)

RESULTS = CJ.RESULTS


class _AATimeout(Exception):
    pass


def _alarm_handler(signum, frame):
    raise _AATimeout()


# K=6 well-separated meaning-preserving templates (a subset of the curated PARAPHRASE set;
# reference first). Chosen to span the neutral "here is a {class}" family with distinct surface
# forms (article/definiteness/synonym/framing) while preserving meaning -- NOT distribution-shift
# templates. The reference "a photo of a {}." is prompt index 0 (so clean/margin under it match the
# hardened run's single-template reference head exactly, a cross-run consistency check).
PROMPTS_K6 = [
    "a photo of a {}.",        # 0 == reference
    "a photo of the {}.",      # 1 definiteness
    "an image of a {}.",       # 2 synonym (image)
    "a picture of a {}.",      # 3 synonym (picture)
    "a cropped photo of a {}.",# 4 framing
    "itap of a {}.",           # 5 "I took a picture of" idiom
]

# Panel: >=3 non-robust + >=6 robust CLIP encoders, incl the ViT-L/14 robust towers
# (fare4, tecoa4, fare2, tecoa2, simclip4, simclip2 are all ViT-L/14) and B/16 + convnext for
# backbone diversity. Runner dispatches standard vs vision-injected via CJH.load_tower_dispatch.
# Feasible-under-contention panel: 3 non-robust + 6 robust (>= spec minimum), maximally diverse:
#   backbones ViT-L/14 + ViT-B/16 + convnext; AT families FARE, TeCoA, Sim-CLIP; eps 2/255 & 4/255.
# Non-robust act as the S~0 anchors under every prompt (sanity gate). The FULL 4+10 panel and the
# ViT-L/14 towers remain available via --encoders for a longer run when the GPU is uncontended.
PANEL_NONROBUST = ["clip", "clip_b16_openai", "clip_b32_laion2b"]
PANEL_ROBUST = ["fare4", "tecoa4", "fare2", "simclip4", "fare4_b16", "tecoa4_cnxt"]
DEFAULT_PANEL = PANEL_NONROBUST + PANEL_ROBUST


def make_head_tower(base_tower, text_features):
    """Return a lightweight ClipZeroShot that shares base_tower's frozen VISION encoder + normalizer
    + logit_scale but uses a DIFFERENT zero-shot head (text_features). Attacks/margins/radius run
    through this exactly as through any tower (same [0,1]-pixel forward, normalization folded in)."""
    t = towers.ClipZeroShot.__new__(towers.ClipZeroShot)
    torch.nn.Module.__init__(t)
    t.visual = base_tower.visual
    t.norm = base_tower.norm
    t.register_buffer("text_features", text_features)
    t.register_buffer("logit_scale", base_tower.logit_scale.detach().clone())
    return t.to(text_features.device).eval()


def build_prompt_heads(clip_model, tokenizer, class_names, prompts, device):
    """Per-prompt single-template head [C,d] for each prompt, PLUS the ensemble head
    (mean of the K single-prompt text embeddings, L2-normalized = standard CLIP prompt ensemble)."""
    heads = []
    for p in prompts:
        tf = build_single_template_features(clip_model, tokenizer, class_names, p, device)  # [C,d]
        heads.append(tf)
    stacked = torch.stack(heads, 0)                       # [K,C,d]
    ens = F.normalize(stacked.mean(0), dim=-1)            # [C,d]  ensemble = mean then renormalize
    return heads, ens


def attack_cell(tower_head, xi, yi, class_names, args, device, tag_prefix):
    """Linf AutoAttack on this prompt's head. Attack config is set UNIFORMLY across all encoders and
    prompts by --targeted so cross-encoder / cross-prompt comparisons stay valid:
      --targeted 1 : full targeted AutoAttack (APGD-CE + APGD-T), RobustBench-grade (expensive).
      --targeted 0 : APGD-CE-only, a strong VALID robust-accuracy UPPER BOUND (this run, chosen
                     because full targeted APGD-T on the ViT-L/14 robust towers is too heavy under
                     shared-GPU contention). Cheaper, and being uniform it preserves the cross-cell
                     ordering that every pre-registered analysis depends on. Flagged, never a silent
                     downgrade (targeted_aa_complete records the config).
    Returns (robust_acc, complete_flag, xadv_cpu, still_robust_mask). Time-capped as a safety valve."""
    eps = args.eps
    use_targeted = bool(args.targeted)
    complete = use_targeted           # 'complete' == "is this full RobustBench-grade targeted AA"
    if args.aa_time_cap_s > 0:
        signal.signal(signal.SIGALRM, _alarm_handler)
        signal.alarm(int(args.aa_time_cap_s))
    try:
        aa = A.run_autoattack(tower_head, xi, yi, eps, n_classes=len(class_names),
                              bs=args.attack_bs, device=device, square=False,
                              n_iter=args.apgd_iters, targeted=use_targeted)
        signal.alarm(0)
        xadv = aa["xadv"]
        ra = aa["robust_acc"]
    except _AATimeout:
        signal.alarm(0)
        torch.cuda.empty_cache()
        print(f"[CJ-PC]   !! targeted AA exceeded {args.aa_time_cap_s}s cap ({tag_prefix}); "
              f"falling back to APGD-CE-only upper bound, flagged INCOMPLETE", flush=True)
        # Fallback: APGD-CE-only (cheaper, still a valid robust-acc upper bound). Give it a larger
        # cap; if it ALSO times out under contention, run it uncapped. APGD-CE has a FIXED iteration
        # count so it always terminates -- the cap only bounds wall-clock. This inner guard is why a
        # single slow cell can no longer crash the whole run (previously the fallback's own alarm
        # raised _AATimeout inside this handler, propagated uncaught, and killed the run).
        try:
            if args.aa_time_cap_s > 0:
                signal.signal(signal.SIGALRM, _alarm_handler)
                signal.alarm(int(args.aa_time_cap_s) * 3)
            aa = A.run_autoattack(tower_head, xi, yi, eps, n_classes=len(class_names),
                                  bs=args.attack_bs, device=device, square=False,
                                  n_iter=args.apgd_iters, targeted=False)
            signal.alarm(0)
        except _AATimeout:
            signal.alarm(0)
            torch.cuda.empty_cache()
            print(f"[CJ-PC]   !! APGD-CE fallback also exceeded cap ({tag_prefix}); "
                  f"running uncapped (fixed-iter, guaranteed to terminate)", flush=True)
            aa = A.run_autoattack(tower_head, xi, yi, eps, n_classes=len(class_names),
                                  bs=args.attack_bs, device=device, square=False,
                                  n_iter=args.apgd_iters, targeted=False)
        xadv = aa["xadv"]
        ra = aa["robust_acc"]
        complete = False
    # per-image still-robust under this head (recompute so it is aligned to xadv order)
    with torch.no_grad():
        still = torch.zeros(len(yi), dtype=torch.bool)
        for i in range(0, len(yi), args.attack_bs):
            lg = tower_head(xadv[i:i + args.attack_bs].to(device))
            still[i:i + args.attack_bs] = (lg.argmax(1).cpu() == yi[i:i + args.attack_bs])
    return ra, complete, xadv.cpu(), still


def run_encoder(name, imgs, labels, class_names, args, device):
    t0 = time.time()
    CJH.wait_for_gpu(min_free_mib=args.min_free_mib)
    base_tower, clip_model, tokenizer = CJH.load_tower_dispatch(name, class_names, device)
    is_robust = name in towers.ROBUST_TOWERS
    print(f"[CJ-PC] === encoder {name} (robust={is_robust}) built ({time.time()-t0:.0f}s) ===",
          flush=True)

    prompts = PROMPTS_K6[:args.n_prompts]
    heads, ens_head = build_prompt_heads(clip_model, tokenizer, class_names, prompts, device)

    # ---- encoder-level (prompt-independent / prompt-set-level) invariance metrics ----
    # SHIFT-consistency: reference head (prompt 0); PARAPHRASE-consistency across the K-prompt set.
    ref_tower = make_head_tower(base_tower, heads[0])
    diag_ref = D.margin_and_grad(ref_tower, imgs, labels, q_list=(1, 2), bs=args.diag_bs,
                                 device=device, correct_only=True)
    offsets = D.patch_grid_offsets(max_shift=args.max_shift, step=1, compact=True)
    sc = D.shift_consistency(ref_tower, imgs, labels, offsets, bs=args.bs, device=device,
                             base_correct_mask=diag_ref["correct"], max_images=args.sc_max_images)
    ci_ref = torch.where(diag_ref["correct"])[0]
    xi_pc = imgs[ci_ref][:args.pc_max_images] if args.pc_max_images else imgs[ci_ref]
    pc = paraphrase_consistency(ref_tower, clip_model, tokenizer, class_names, xi_pc, device,
                                prompts, REFERENCE_TEMPLATE, bs=args.bs)
    enc_common = {
        "encoder": name, "robust": is_robust,
        "sc_pred": sc["sc_pred"], "sc_cos": sc["sc_cos"], "n_offsets": sc["n_offsets"],
        "pc": pc["pc"], "pc_per_template": pc["per_template_agreement"],
        "pc_n_images": pc["n_images"], "pc_n_templates": pc["n_templates"],
        "pc_self_check": pc["per_template_agreement"][REFERENCE_TEMPLATE],
        "prompts": prompts,
    }
    print(f"[CJ-PC]   SC={sc['sc_pred']:.4f} PC={pc['pc']:.4f} (self={enc_common['pc_self_check']:.3f}) "
          f"({time.time()-t0:.0f}s)", flush=True)
    del ref_tower

    # ---- per-(prompt) cells, PLUS the ensemble cell (prompt_id 'ensemble') ----
    cell_specs = [(f"p{k}", p, heads[k]) for k, p in enumerate(prompts)]
    cell_specs.append(("ensemble", "ENSEMBLE(mean of K prompts)", ens_head))

    # PER-CELL CHECKPOINTING (resume mid-encoder): a sidecar JSON holds the finished cells and the
    # encoder-level invariance metrics; xadv tensors are saved per cell so transfer is recomputable.
    part_path = os.path.join(RESULTS, f"promptcond_partial_{name}.json")
    cells = []
    done_pids = set()
    if args.resume and os.path.exists(part_path):
        prev = json.load(open(part_path))
        cells = prev.get("cells", [])
        done_pids = {c["prompt_id"] for c in cells}
        print(f"[CJ-PC]   resume {name}: {len(done_pids)} cells done: {sorted(done_pids)}", flush=True)

    # store xadv per prompt cell for cross-prompt transfer (only the per-prompt heads + ensemble)
    xadv_store = {}       # prompt_id -> xadv (cpu) crafted under that head
    xadv_idx_store = {}   # prompt_id -> global image indices attacked (for cross-eval alignment)
    xadv_lbl_store = {}   # prompt_id -> labels

    def _adv_path(pid):
        return os.path.join(RESULTS, f"promptcond_xadv_{name}_{pid}.pt")

    for pid, ptext, head_tf in cell_specs:
        if pid in done_pids:
            # reload xadv for the transfer step
            ad = torch.load(_adv_path(pid), map_location="cpu")
            xadv_store[pid] = ad["xadv"]; xadv_idx_store[pid] = ad["idx"]; xadv_lbl_store[pid] = ad["labels"]
            print(f"[CJ-PC]   [{pid:9s}] (resumed from checkpoint)", flush=True)
            continue
        tc0 = time.time()
        tower_h = make_head_tower(base_tower, head_tf)
        cell = {"prompt_id": pid, "prompt": ptext, "is_ensemble": pid == "ensemble"}

        # clean acc under this head
        pred = D.predict(tower_h, imgs, bs=args.bs, device=device)
        correct = (pred == labels)
        cell["clean_acc"] = correct.float().mean().item()
        ci = torch.where(correct)[0]                       # correct-under-THIS-prompt population
        cell["n_correct"] = int(len(ci))

        # margin + gradient diagnostics conditioned on THIS head -> eta, L1, L2, eta/L1, A
        diag = D.margin_and_grad(tower_h, imgs, labels, q_list=(1, 2), bs=args.diag_bs,
                                 device=device, correct_only=True)
        summ = D.eta_L_summary(diag, q_list=(1, 2))
        for k, v in summ.items():
            if not k.startswith("_"):
                cell[k] = v
        r1 = summ["_per_image_ratio_L1"]; r2 = summ["_per_image_ratio_L2"]
        aniso_pi = (r2 / r1.clamp_min(1e-12))
        cell["anisotropy_A"] = aniso_pi.mean().item()

        # choose the attack subset: images correct UNDER THIS PROMPT (threat-matched population)
        if args.n_attack and len(ci) > args.n_attack:
            g = torch.Generator().manual_seed(0)
            sel = torch.randperm(len(ci), generator=g)[:args.n_attack]
            ci_a = ci[sel]
        else:
            ci_a = ci
        xi, yi = imgs[ci_a], labels[ci_a]
        cell["n_attack"] = int(len(ci_a))

        # IMAGE-adversarial: full targeted AutoAttack, Linf eps, on this prompt's head
        ra, complete, xadv, still = attack_cell(tower_h, xi, yi, class_names, args, device,
                                                 f"{name}/{pid}")
        cell["S_apgd"] = ra
        cell["targeted_aa_complete"] = complete
        cell["attack_type"] = ("full_targeted_apgd_ce_t" if args.targeted
                               else "apgd_ce_only_upperbound")
        xadv_store[pid] = xadv
        xadv_idx_store[pid] = ci_a.cpu()
        xadv_lbl_store[pid] = yi.cpu()
        # persist xadv for the transfer step (survives a mid-encoder kill -> resumable)
        torch.save({"xadv": xadv, "idx": ci_a.cpu(), "labels": yi.cpu()}, _adv_path(pid))

        # per-image Linf robust radius (PGD bisection) on a sub-subset
        nr = min(args.radius_max_images, len(ci_a))
        ci_r = ci_a[:nr]
        radius, flipped = A.per_image_robust_radius_linf(
            tower_h, imgs[ci_r], labels[ci_r], args.radius_grid, steps=args.radius_steps,
            bs=args.attack_bs, device=device)
        cell["robust_radius_mean"] = float(radius.mean().item())
        cell["robust_radius_median"] = float(radius.median().item())

        # align per-image eta/L1 ratio + anisotropy + margin to the radius images
        corr_idx = torch.where(diag["correct"])[0]
        pos = {int(v): kk for kk, v in enumerate(corr_idx.tolist())}
        sel_pi = torch.tensor([pos[int(j)] for j in ci_r.tolist()])
        per_image = {
            "radius_idx": ci_r.cpu(), "labels": labels[ci_r].cpu(),
            "robust_radius_linf": radius.cpu(), "flipped": flipped.cpu(),
            "ratio_l1": summ["_per_image_ratio_L1"][sel_pi].cpu(),
            "ratio_l2": summ["_per_image_ratio_L2"][sel_pi].cpu(),
            "anisotropy_A": aniso_pi[sel_pi].cpu(),
            "margin": summ["_per_image_margin"][sel_pi].cpu(),
        }
        torch.save(per_image, os.path.join(
            RESULTS, f"per_image_promptcond_{name}_{pid}.pt"))
        cell["radius_grid"] = list(args.radius_grid)
        cell["seconds"] = time.time() - tc0
        cells.append(cell)
        print(f"[CJ-PC]   [{pid:9s}] clean={cell['clean_acc']:.3f} S={ra:.3f} "
              f"eta/L1={cell['eta_over_L1']:.5f} A={cell['anisotropy_A']:.2f} "
              f"rad={cell['robust_radius_mean']:.5f} complete={complete} "
              f"({cell['seconds']:.0f}s)", flush=True)
        del tower_h
        torch.cuda.empty_cache()
        # per-cell checkpoint (resume mid-encoder)
        with open(part_path, "w") as f:
            json.dump({"encoder": name, "enc_common": {k: v for k, v in enc_common.items()
                                                       if k != "cells"}, "cells": cells},
                      f, indent=2, default=str)

    # ---- cross-prompt adversarial transfer (analysis C material) ----
    # For each source prompt A, take its adversarial images (crafted under A's head) and evaluate
    # whether they FLIP the label under every target prompt B's head (B != A), among the images that
    # WERE fooled under A (i.e. successful adversarials for A). transfer[A][B] = fraction of A's
    # successful adversarials that also fool B. We embed each xadv batch ONCE per target head.
    transfer = {}
    all_pids = [c["prompt_id"] for c in cells]
    head_by_pid = {pid: h for (pid, _p, h) in cell_specs}
    for pa in all_pids:
        xadv = xadv_store[pa]; ya = xadv_lbl_store[pa]
        tower_a = make_head_tower(base_tower, head_by_pid[pa])
        with torch.no_grad():
            fooled_a = torch.zeros(len(ya), dtype=torch.bool)
            for i in range(0, len(ya), args.attack_bs):
                lg = tower_a(xadv[i:i + args.attack_bs].to(device))
                fooled_a[i:i + args.attack_bs] = (lg.argmax(1).cpu() != ya[i:i + args.attack_bs])
        del tower_a
        n_src = int(fooled_a.sum().item())
        transfer[pa] = {"n_successful_adv_under_source": n_src}
        for pb in all_pids:
            if pb == pa:
                continue
            tower_b = make_head_tower(base_tower, head_by_pid[pb])
            with torch.no_grad():
                flip_b = torch.zeros(len(ya), dtype=torch.bool)
                for i in range(0, len(ya), args.attack_bs):
                    lg = tower_b(xadv[i:i + args.attack_bs].to(device))
                    flip_b[i:i + args.attack_bs] = (lg.argmax(1).cpu() != ya[i:i + args.attack_bs])
            del tower_b
            torch.cuda.empty_cache()
            both = int((fooled_a & flip_b).sum().item())
            transfer[pa][pb] = (both / n_src) if n_src > 0 else float("nan")
        torch.cuda.empty_cache()
    enc_common["cross_prompt_transfer"] = transfer

    enc_common["cells"] = cells
    enc_common["seconds"] = time.time() - t0
    del base_tower, clip_model
    torch.cuda.empty_cache()
    print(f"[CJ-PC] encoder {name} DONE ({enc_common['seconds']:.0f}s)", flush=True)
    return enc_common


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--encoders", nargs="+", default=DEFAULT_PANEL)
    ap.add_argument("--n_diag", type=int, default=2000)
    ap.add_argument("--n_prompts", type=int, default=6,
                    help="use PROMPTS_K6[:n_prompts] single-prompt cells (+ensemble). Subset for a "
                         "cheaper full-targeted-AA validation run; default 6 = full set.")
    ap.add_argument("--n_attack", type=int, default=250)
    ap.add_argument("--eps", type=float, default=4/255)
    ap.add_argument("--targeted", type=int, default=0,
                    help="1=full targeted AA (APGD-CE+APGD-T, RobustBench-grade, expensive); "
                         "0=APGD-CE-only strong robust-acc UPPER BOUND applied UNIFORMLY (this run, "
                         "chosen for shared-GPU feasibility on ViT-L/14 robust towers; flagged).")
    ap.add_argument("--max_shift", type=int, default=8)
    ap.add_argument("--sc_max_images", type=int, default=800)
    ap.add_argument("--pc_max_images", type=int, default=800)
    ap.add_argument("--bs", type=int, default=128)
    ap.add_argument("--diag_bs", type=int, default=32)
    ap.add_argument("--attack_bs", type=int, default=12)
    ap.add_argument("--apgd_iters", type=int, default=100)
    ap.add_argument("--radius_grid", type=float, nargs="+",
                    default=[0.25/255, 0.5/255, 1/255, 2/255, 3/255, 4/255, 6/255, 8/255])
    ap.add_argument("--radius_steps", type=int, default=20)
    ap.add_argument("--radius_max_images", type=int, default=120)
    ap.add_argument("--min_free_mib", type=int, default=9000)
    ap.add_argument("--aa_time_cap_s", type=int, default=0,
                    help="per-cell wall-clock cap (s) on full targeted AA; on timeout fall back to "
                         "APGD-CE-only upper bound + flag complete=False. 0 = no cap.")
    ap.add_argument("--tag", type=str, default="promptcond")
    ap.add_argument("--resume", type=int, default=1)
    args = ap.parse_args()

    device = "cuda"
    class_names = data.get_class_names()
    imgs, labels = data.load_val(n=args.n_diag, seed=0, cache_path=CJ.CACHE)
    print(f"[CJ-PC] loaded {len(labels)} val images @{imgs.shape[-1]}px", flush=True)
    print(f"[CJ-PC] K={len(PROMPTS_K6)} prompts + ensemble; panel={args.encoders}", flush=True)
    _atk = ("FULL targeted AA (APGD-CE+APGD-T)" if args.targeted
            else "APGD-CE-only (strong robust-acc UPPER BOUND, uniform)")
    print(f"[CJ-PC] attack={_atk}, n_iter={args.apgd_iters}, eps={args.eps:.5f}, "
          f"n_attack={args.n_attack}, radius_max={args.radius_max_images}", flush=True)

    out_path = os.path.join(RESULTS, f"crownjewel_{args.tag}.json")
    all_enc, done = [], set()
    if args.resume and os.path.exists(out_path):
        prev = json.load(open(out_path))
        all_enc = prev.get("encoders", [])
        done = {e["encoder"] for e in all_enc}
        print(f"[CJ-PC] resume: {len(done)} encoders done: {sorted(done)}", flush=True)

    for name in args.encoders:
        if name in done:
            print(f"[CJ-PC] skip {name} (already done)", flush=True)
            continue
        e = run_encoder(name, imgs, labels, class_names, args, device)
        all_enc.append(e)
        with open(out_path, "w") as f:
            json.dump({"args": vars(args), "prompts": PROMPTS_K6,
                       "reference_template": REFERENCE_TEMPLATE,
                       "encoders": all_enc}, f, indent=2, default=str)
        print(f"[CJ-PC] checkpoint -> {out_path} ({len(all_enc)} encoders)", flush=True)
    print(f"[CJ-PC] DONE -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
