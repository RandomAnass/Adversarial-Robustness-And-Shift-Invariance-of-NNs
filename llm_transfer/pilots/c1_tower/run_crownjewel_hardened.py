"""Crown-Jewel HARDENED pilot: pre-registered 2x2 (modality x perturbation-type) dissociation.

Extends run_crownjewel_v0.py with the ONE genuinely new cell -- TEXT-ADVERSARIAL robustness
S_text = frac images correct under ALL K meaning-preserving templates (worst-case-over-paraphrases,
the exact discrete sibling of average-case paraphrase-consistency PC) -- and hardens the panel:

  * PANEL = 16 encoders: 4 non-robust + 12 robust (10 FARE/TeCoA via load_clip_tower +
    simclip4, simclip2 via load_vision_injected_tower). Runner DISPATCHES to the correct loader.
  * IMAGE-adversarial = FULL targeted AutoAttack (APGD-CE + APGD-T, n_iter=100, 3 targets,
    square=False), Linf eps=4/255, on n_attack=400 correct-under-reference images per tower;
    per-image Linf robust radius (PGD bisection) on the first 200. NO silent APGD-CE-only fallback.
  * n_diag = 2000; reference head "a photo of a {}."; population = ref-correct images.
  * K = 11 curated templates (v0 set, so average PC and worst-case S_text share the SAME family),
    PLUS a pre-registered K=20 sensitivity variant (S_text_k20).

Reuses verbatim: diagnostics.margin_and_grad / eta_L_summary / shift_consistency,
attacks.run_autoattack / per_image_robust_radius_linf, towers.load_vision_injected_tower,
and run_crownjewel_v0.{load_tower_with_reference_head, build_single_template_features,
paraphrase_consistency, PARAPHRASE_TEMPLATES, REFERENCE_TEMPLATE}. The worst-case-over-paraphrases
logic mirrors the verified smoke_text_adv.py exactly.

GPU 1 ONLY (CUDA_VISIBLE_DEVICES=1). Shared GPU: one tower at a time, small attack_bs, del +
empty_cache between towers, and a pre-tower free-memory guard so we never OOM a co-tenant job.
Per-tower JSON checkpoint after every tower (resumable).
"""
import os, json, time, argparse, subprocess, signal
import torch
import torch.nn.functional as F


class _AATimeout(Exception):
    pass


def _alarm_handler(signum, frame):
    raise _AATimeout()

import data, towers
import diagnostics as D
import attacks as A
import run_crownjewel_v0 as CJ
from run_crownjewel_v0 import (REFERENCE_TEMPLATE, PARAPHRASE_TEMPLATES,
                               build_single_template_features, paraphrase_consistency)

RESULTS = CJ.RESULTS
CACHE = CJ.CACHE

# K=11 headline set == v0's average-case PC set (average and worst-case share the SAME family).
TEMPLATES_K11 = PARAPHRASE_TEMPLATES

# K=20 pre-registered SENSITIVITY set: the 11 above + 9 more neutral rewordings, ALL drawn from
# the standard OpenAI 80-template ensemble (open_clip.OPENAI_IMAGENET_TEMPLATES). These are pure
# article/definiteness variants of the neutral "here is a {class}" family (NOT medium/quantity/
# size/quality/degradation distribution-shift templates), so meaning-preservation is preserved.
TEMPLATES_K20 = TEMPLATES_K11 + [
    "a cropped photo of the {}.",     # 8
    "a close-up photo of the {}.",    # 38
    "a good photo of the {}.",        # 33
    "a bright photo of the {}.",      # 26
    "itap of the {}.",                # 59
    "a photo of my {}.",              # 17
    "a bad photo of the {}.",         # 7
    "a photo of one {}.",             # 36  (duplicate-safe; dedup below)
    "itap of my {}.",                 # 76
]
# dedup while preserving order (a photo of one {}. is already in K11)
_seen = set()
TEMPLATES_K20 = [t for t in TEMPLATES_K20 if not (t in _seen or _seen.add(t))]

PANEL_NONROBUST = ["clip", "clip_b16_openai", "clip_b32_laion2b", "clip_l14_laion2b"]
PANEL_ROBUST = ["fare4", "tecoa4", "fare2", "tecoa2", "fare4_b32", "fare4_b16",
                "tecoa4_b32", "tecoa4_b16", "fare4_cnxt", "tecoa4_cnxt",
                "simclip4", "simclip2"]
DEFAULT_PANEL = PANEL_NONROBUST + PANEL_ROBUST


def _phys_gpu_index():
    """PHYSICAL nvidia-smi index of the GPU we are actually using. nvidia-smi -i uses PHYSICAL
    indices regardless of CUDA_VISIBLE_DEVICES, so map through CUDA_VISIBLE_DEVICES (e.g. "1")."""
    cvd = os.environ.get("CUDA_VISIBLE_DEVICES", "").strip()
    if cvd:
        return int(cvd.split(",")[0])
    return 0


def gpu_free_mib(device_index=None):
    """Free memory (MiB) on our PHYSICAL GPU (honoring CUDA_VISIBLE_DEVICES)."""
    if device_index is None:
        device_index = _phys_gpu_index()
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits",
             "-i", str(device_index)], text=True)
        return int(out.strip().split("\n")[0])
    except Exception as e:
        print(f"[CJ-H] gpu_free_mib failed ({e}); assuming OK", flush=True)
        return 999999


def wait_for_gpu(min_free_mib=6000, poll_s=30, max_wait_s=3600):
    """Shared-GPU etiquette: wait until free memory >= min_free_mib before loading a tower."""
    waited = 0
    dev = _phys_gpu_index()
    while True:
        free = gpu_free_mib(dev)  # our PHYSICAL GPU (CUDA_VISIBLE_DEVICES-aware)
        if free >= min_free_mib:
            print(f"[CJ-H] GPU free={free}MiB >= {min_free_mib}MiB; proceeding", flush=True)
            return
        if waited >= max_wait_s:
            print(f"[CJ-H] WARN: waited {waited}s, free={free}MiB still < {min_free_mib}MiB; "
                  f"proceeding cautiously", flush=True)
            return
        print(f"[CJ-H] GPU free={free}MiB < {min_free_mib}MiB; waiting {poll_s}s "
              f"(do not OOM co-tenant)", flush=True)
        time.sleep(poll_s)
        waited += poll_s


# ---------------------------------------------------------------------------
# Tower loading dispatch (standard vs vision-injected) that ALSO returns the raw
# clip_model + tokenizer so we can build the paraphrase heads for every tower.
# ---------------------------------------------------------------------------
def load_tower_dispatch(name, class_names, device):
    """Return (tower_with_reference_head, clip_model, tokenizer) for ANY panel member.

    - standard open_clip towers  -> CJ.load_tower_with_reference_head (reference single-template head)
    - vision-injected (simclip*) -> open_clip base (openai) + robust visual state_dict, then the
      SAME reference single-template head, matching load_clip_tower head construction.
    """
    if name == "leaf_L_text":
        # STRETCH: LEAF robust-TEXT tower. Uses its OWN hardened vision+text towers (transformers
        # CLIPModel, recipe C). Wrapped to expose the SAME encode_text/tokenizer contract so the
        # PC and S_text code paths are reused verbatim.
        import leaf_tower as LT
        tower, model, tok = LT.load_leaf_text_tower(class_names, device, template=REFERENCE_TEMPLATE)
        model, tok = LT.wrap_leaf_for_reuse(model, tok)
        return tower, model, tok
    if name in towers.HARDENED_NEW_ROBUST_SPEC:
        from huggingface_hub import hf_hub_download
        repo, fname, arch, kind, note = towers.HARDENED_NEW_ROBUST_SPEC[name]
        model, _, _ = towers.open_clip.create_model_and_transforms(arch, pretrained="openai")
        tokenizer = towers.open_clip.get_tokenizer(arch)
        sd = torch.load(hf_hub_download(repo, fname), map_location="cpu")
        sd = sd.get("state_dict", sd)
        sd = {(k[7:] if k.startswith("module.") else k): v for k, v in sd.items()}
        if kind == "clip_visual":
            sd = {k[len("visual."):]: v for k, v in sd.items() if k.startswith("visual.")}
        missing, unexpected = model.visual.load_state_dict(sd, strict=False)
        print(f"[CJ-H] {name}: injected robust visual ({note}); "
              f"missing={len(missing)} unexpected={len(unexpected)}", flush=True)
        model = model.to(device).eval()
        for p in model.parameters():
            p.requires_grad_(False)
        ref_tf = build_single_template_features(model, tokenizer, class_names,
                                                REFERENCE_TEMPLATE, device)
        tower = towers.ClipZeroShot(model, ref_tf, towers.CLIP_MEAN, towers.CLIP_STD).to(device).eval()
        for p in tower.parameters():
            p.requires_grad_(False)
        return tower, model, tokenizer
    # standard path
    return CJ.load_tower_with_reference_head(name, class_names, device)


# ---------------------------------------------------------------------------
# The NEW cell: worst-case-over-paraphrases (S_text). Mirrors smoke_text_adv.py EXACTLY.
# ---------------------------------------------------------------------------
@torch.no_grad()
def worst_case_over_paraphrases(tower, clip_model, tokenizer, class_names, images, labels,
                                device, templates, ref_template, bs=128):
    """Text-adversarial cell. For each template t, single-template head h_t predicts pred_t(x).

      a_ref  = mean_x 1[pred_ref(x)==y]              (reference-template acc; ==1 on ref-correct set)
      a_avg  = mean_x mean_t 1[pred_t(x)==y]         (average per-template acc == PC-implied acc)
      S_text = mean_x min_t 1[pred_t(x)==y]          (worst-case: correct under ALL K templates)

    Also returns per-image worst-template MARGIN (signed logit margin under the template that
    minimizes it) for the NEW cross-modal per-image coupling test (worst_margin_text vs radius).
    Ordering S_text <= a_avg <= a_ref <= 1 is asserted.
    """
    logit_scale = tower.logit_scale
    # embed images ONCE; every single-template head reuses the same image embeddings
    embs = []
    for i in range(0, len(images), bs):
        embs.append(tower.encode(images[i:i + bs].to(device)))
    emb = torch.cat(embs)                       # [N,d]
    y = labels.to(device)
    N = len(y)
    K = len(templates)

    correct_kt = torch.zeros((K, N), dtype=torch.bool, device=device)
    # per-image signed margin M = f_y - max_{j!=y} f_j under each template; track the WORST (min)
    worst_margin = torch.full((N,), float("inf"), device=device)
    ref_idx = templates.index(ref_template)
    per_template_acc = {}
    for k, t in enumerate(templates):
        tf = build_single_template_features(clip_model, tokenizer, class_names, t, device)  # [C,d]
        logits = logit_scale * emb @ tf.t()     # [N,C]
        pred = logits.argmax(1)
        correct_kt[k] = (pred == y)
        per_template_acc[t] = correct_kt[k].float().mean().item()
        true_logit = logits.gather(1, y[:, None]).squeeze(1)
        masked = logits.clone()
        masked.scatter_(1, y[:, None], float("-inf"))
        M = true_logit - masked.max(1).values   # [N]
        worst_margin = torch.minimum(worst_margin, M)

    a_ref = per_template_acc[ref_template]
    a_avg = correct_kt.float().mean().item()
    survives_all = correct_kt.all(dim=0)         # [N]
    S_text = survives_all.float().mean().item()
    n_flipped = int((~survives_all).sum().item())

    assert a_ref >= a_avg - 1e-9, f"a_ref {a_ref} < a_avg {a_avg}"
    assert a_avg >= S_text - 1e-9, f"a_avg {a_avg} < S_text {S_text}"
    assert 0.0 <= S_text <= 1.0
    worst_t = min(per_template_acc, key=per_template_acc.get)
    return {
        "a_ref": a_ref, "a_avg": a_avg, "S_text": S_text,
        "n_images": N, "n_templates": K, "n_flipped_by_some_reword": n_flipped,
        "per_template_acc": per_template_acc, "worst_template": worst_t,
        "worst_margin_per_image": worst_margin.cpu(),      # [N], aligned to `images` order
        "survives_all": survives_all.cpu(),
    }


def run_tower(name, imgs, labels, class_names, args, device):
    t0 = time.time()
    wait_for_gpu(min_free_mib=args.min_free_mib)
    tower, clip_model, tokenizer = load_tower_dispatch(name, class_names, device)
    res = {"tower": name, "robust": name in towers.ROBUST_TOWERS}
    print(f"[CJ-H]   tower built ({time.time()-t0:.0f}s)", flush=True)

    # 1. clean accuracy under the REFERENCE single-template head
    pred = D.predict(tower, imgs, bs=args.bs, device=device)
    correct = (pred == labels)
    res["clean_acc"] = correct.float().mean().item()
    res["n_eval"] = int(len(labels))
    ci = torch.where(correct)[0]                 # correct-under-reference subset (the population)

    # 2. margin + gradient diagnostics (reused) -> eta, L1, L2, eta/L1, per-image ratios, A
    diag = D.margin_and_grad(tower, imgs, labels, q_list=(1, 2), bs=args.diag_bs,
                             device=device, correct_only=True)
    summ = D.eta_L_summary(diag, q_list=(1, 2))
    res.update({k: v for k, v in summ.items() if not k.startswith("_")})
    r1 = summ["_per_image_ratio_L1"]; r2 = summ["_per_image_ratio_L2"]
    aniso_per_image = (r2 / r1.clamp_min(1e-12))
    res["anisotropy_A"] = aniso_per_image.mean().item()
    print(f"[CJ-H]   clean={res['clean_acc']:.3f} eta/L1={res['eta_over_L1']:.5f} "
          f"A={res['anisotropy_A']:.2f} ({time.time()-t0:.0f}s)", flush=True)

    # 3a. IMAGE-invariance: SHIFT-consistency (reused), correct subset
    offsets = D.patch_grid_offsets(max_shift=args.max_shift, step=1, compact=True)
    sc = D.shift_consistency(tower, imgs, labels, offsets, bs=args.bs, device=device,
                             base_correct_mask=diag["correct"], max_images=args.sc_max_images)
    res["sc_pred"] = sc["sc_pred"]; res["sc_cos"] = sc["sc_cos"]; res["n_offsets"] = sc["n_offsets"]

    # 3b. TEXT-invariance: PARAPHRASE-consistency (v0), correct subset, K=11 family.
    # Text cells are computed on the FULL ref-correct pool (images are embedded ONCE, so it is
    # cheap and it guarantees the radius-image subset is fully covered for the cross-modal
    # per-image coupling in analysis (E)); pc_max_images left as a safety cap only.
    xi_all = imgs[ci]; yi_all = labels[ci]
    _cap = args.pc_max_images if args.pc_max_images else None  # 0 -> no cap
    xi_pc = xi_all if _cap is None or len(xi_all) <= _cap else xi_all[:_cap]
    pc = paraphrase_consistency(tower, clip_model, tokenizer, class_names, xi_pc, device,
                                TEMPLATES_K11, REFERENCE_TEMPLATE, bs=args.bs)
    res["pc"] = pc["pc"]; res["pc_per_template"] = pc["per_template_agreement"]
    res["pc_n_images"] = pc["n_images"]; res["pc_n_templates"] = pc["n_templates"]
    res["pc_self_check"] = pc["per_template_agreement"][REFERENCE_TEMPLATE]

    # 3c. TEXT-adversarial (NEW): worst-case-over-paraphrases S_text, K=11 (headline) and K=20.
    yi_pc = yi_all[:len(xi_pc)]
    st11 = worst_case_over_paraphrases(tower, clip_model, tokenizer, class_names, xi_pc, yi_pc,
                                       device, TEMPLATES_K11, REFERENCE_TEMPLATE, bs=args.bs)
    res["S_text"] = st11["S_text"]; res["a_avg"] = st11["a_avg"]; res["a_ref_text"] = st11["a_ref"]
    res["S_text_n_images"] = st11["n_images"]; res["S_text_n_templates"] = st11["n_templates"]
    res["S_text_n_flipped"] = st11["n_flipped_by_some_reword"]
    res["S_text_worst_template"] = st11["worst_template"]
    res["S_text_per_template_acc"] = st11["per_template_acc"]
    st20 = worst_case_over_paraphrases(tower, clip_model, tokenizer, class_names, xi_pc, yi_pc,
                                       device, TEMPLATES_K20, REFERENCE_TEMPLATE, bs=args.bs)
    res["S_text_k20"] = st20["S_text"]; res["a_avg_k20"] = st20["a_avg"]
    res["S_text_k20_n_templates"] = st20["n_templates"]
    print(f"[CJ-H]   SC={res['sc_pred']:.4f} PC={res['pc']:.4f} S_text={res['S_text']:.4f} "
          f"(a_avg={res['a_avg']:.4f} a_ref={res['a_ref_text']:.4f}; K20 S_text={res['S_text_k20']:.4f}) "
          f"({time.time()-t0:.0f}s)", flush=True)

    # 4. IMAGE-adversarial: FULL targeted AutoAttack (APGD-CE + APGD-T), Linf eps=4/255, correct subset
    if args.n_attack and len(ci) > args.n_attack:
        g = torch.Generator().manual_seed(0)
        sel = torch.randperm(len(ci), generator=g)[:args.n_attack]
        ci_a = ci[sel]
    else:
        ci_a = ci
    xi, yi = imgs[ci_a], labels[ci_a]
    res["n_attack"] = int(len(ci_a))
    res["S_apgd"] = {}
    res["targeted_aa_complete"] = {}
    # Per-tower wall-clock CAP on the full targeted AA (design 3.3: "if a tower exceeds a sane
    # time cap it is reported as targeted-AA incomplete with the APGD-CE upper bound flagged, NOT
    # merged as if complete"). On timeout we fall back to APGD-CE-only (a VALID robust-acc upper
    # bound) and flag targeted_aa_complete=False -- an honest incomplete, never a silent downgrade.
    res["S_apgd_ce_upperbound"] = {}
    for eps in args.eps:
        tag = f"{eps:.5f}"
        ta = time.time()
        did_timeout = False
        if args.aa_time_cap_s > 0:
            signal.signal(signal.SIGALRM, _alarm_handler)
            signal.alarm(int(args.aa_time_cap_s))
        try:
            aa = A.run_autoattack(tower, xi, yi, eps, n_classes=len(class_names),
                                  bs=args.attack_bs, device=device, square=False,
                                  n_iter=args.apgd_iters, targeted=True)
            signal.alarm(0)
            res["S_apgd"][tag] = aa["robust_acc"]
            res["targeted_aa_complete"][tag] = True
        except _AATimeout:
            signal.alarm(0)
            did_timeout = True
            print(f"[CJ-H]   !! targeted AA exceeded {args.aa_time_cap_s}s cap for {name} "
                  f"eps={tag}; falling back to APGD-CE-only upper bound, flagged INCOMPLETE",
                  flush=True)
            torch.cuda.empty_cache()
        except Exception as e:  # e.g. OOM; flag honestly, do NOT merge as complete
            signal.alarm(0)
            print(f"[CJ-H]   !! targeted AA FAILED for {name} eps={tag}: {e}", flush=True)
            torch.cuda.empty_cache()
            res["S_apgd"][tag] = None
            res["targeted_aa_complete"][tag] = False
            res["targeted_aa_error"] = str(e)
            print(f"[CJ-H]   AA eps={tag} S={res['S_apgd'][tag]} complete=False "
                  f"({time.time()-ta:.0f}s)", flush=True)
            continue
        if did_timeout:
            # APGD-CE-only upper bound (fast, valid S upper bound), separately time-capped
            if args.aa_time_cap_s > 0:
                signal.signal(signal.SIGALRM, _alarm_handler)
                signal.alarm(int(args.aa_time_cap_s))
            try:
                ce = A.run_autoattack(tower, xi, yi, eps, n_classes=len(class_names),
                                      bs=args.attack_bs, device=device, square=False,
                                      n_iter=args.apgd_iters, targeted=False)
                signal.alarm(0)
                res["S_apgd"][tag] = ce["robust_acc"]           # upper bound stands in for S
                res["S_apgd_ce_upperbound"][tag] = ce["robust_acc"]
                res["targeted_aa_complete"][tag] = False        # flagged: NOT full targeted AA
            except Exception as e2:
                signal.alarm(0)
                res["S_apgd"][tag] = None
                res["targeted_aa_complete"][tag] = False
                res["targeted_aa_error"] = f"timeout then CE failed: {e2}"
        print(f"[CJ-H]   AA eps={tag} S={res['S_apgd'][tag]} "
              f"complete={res['targeted_aa_complete'][tag]} "
              f"(CE_ub={res['S_apgd_ce_upperbound'].get(tag)}) ({time.time()-ta:.0f}s)", flush=True)

    # 5. per-image Linf robust radius (PGD bisection, reused), first `radius_max_images`
    eps_grid = args.radius_grid
    nr = min(args.radius_max_images, len(ci_a))
    ci_r = ci_a[:nr]
    radius, flipped = A.per_image_robust_radius_linf(
        tower, imgs[ci_r], labels[ci_r], eps_grid, steps=args.radius_steps,
        bs=args.attack_bs, device=device)
    res["robust_radius_mean"] = float(radius.mean().item())
    res["robust_radius_median"] = float(radius.median().item())

    # align per-image eta/L1 ratio + anisotropy + worst-template-margin to the radius images
    corr_idx = torch.where(diag["correct"])[0]
    pos = {int(v): k for k, v in enumerate(corr_idx.tolist())}
    sel = torch.tensor([pos[int(j)] for j in ci_r.tolist()])
    # worst_margin_text is aligned to xi_pc order (= first len(xi_pc) of ci); map radius imgs -> that
    pc_pos = {int(v): k for k, v in enumerate(ci[:len(xi_pc)].tolist())}
    wm = st11["worst_margin_per_image"]
    wm_sel = torch.tensor([pc_pos.get(int(j), -1) for j in ci_r.tolist()])
    worst_margin_aligned = torch.where(
        wm_sel >= 0, wm[wm_sel.clamp_min(0)], torch.full_like(radius, float("nan")))
    per_image = {
        "radius_idx": ci_r.cpu(), "labels": labels[ci_r].cpu(),
        "robust_radius_linf": radius.cpu(), "flipped": flipped.cpu(),
        "ratio_l1": summ["_per_image_ratio_L1"][sel].cpu(),
        "ratio_l2": summ["_per_image_ratio_L2"][sel].cpu(),
        "anisotropy_A": aniso_per_image[sel].cpu(),
        "margin": summ["_per_image_margin"][sel].cpu(),
        "worst_margin_text": worst_margin_aligned.cpu(),  # NEW: cross-modal per-image coupling
    }
    torch.save(per_image, os.path.join(RESULTS, f"per_image_crownjewelH_{name}.pt"))
    res["radius_grid"] = list(eps_grid)
    res["seconds"] = time.time() - t0

    del tower, clip_model
    torch.cuda.empty_cache()
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--towers", nargs="+", default=DEFAULT_PANEL)
    ap.add_argument("--n_diag", type=int, default=2000)
    ap.add_argument("--n_attack", type=int, default=400)
    ap.add_argument("--eps", type=float, nargs="+", default=[4/255])
    ap.add_argument("--max_shift", type=int, default=8)
    ap.add_argument("--sc_max_images", type=int, default=800)
    ap.add_argument("--pc_max_images", type=int, default=0,
                    help="0 = no cap (text cells on full ref-correct pool; cheap, embed-once)")
    ap.add_argument("--bs", type=int, default=128)
    ap.add_argument("--diag_bs", type=int, default=32)
    ap.add_argument("--attack_bs", type=int, default=16)
    ap.add_argument("--apgd_iters", type=int, default=100)
    ap.add_argument("--radius_grid", type=float, nargs="+",
                    default=[0.25/255, 0.5/255, 1/255, 2/255, 3/255, 4/255, 6/255, 8/255])
    ap.add_argument("--radius_steps", type=int, default=20)
    ap.add_argument("--radius_max_images", type=int, default=200)
    ap.add_argument("--min_free_mib", type=int, default=6000,
                    help="wait until GPU free >= this before loading a tower (shared-GPU etiquette)")
    ap.add_argument("--aa_time_cap_s", type=int, default=0,
                    help="per-tower wall-clock cap (s) on full targeted AA; on timeout fall back to "
                         "APGD-CE-only upper bound and flag targeted_aa_complete=False (design 3.3). "
                         "0 = no cap (run full targeted AA to completion).")
    ap.add_argument("--tag", type=str, default="hardened")
    ap.add_argument("--resume", type=int, default=1,
                    help="1=skip towers already in the output JSON (resumable)")
    args = ap.parse_args()

    device = "cuda"
    class_names = data.get_class_names()
    imgs, labels = data.load_val(n=args.n_diag, seed=0, cache_path=CACHE)
    print(f"[CJ-H] loaded {len(labels)} val images @{imgs.shape[-1]}px; panel={args.towers}", flush=True)
    print(f"[CJ-H] reference={REFERENCE_TEMPLATE!r}; K11={len(TEMPLATES_K11)} K20={len(TEMPLATES_K20)} "
          f"templates; FULL targeted AA (APGD-CE+APGD-T, n_iter={args.apgd_iters}), "
          f"n_attack={args.n_attack}", flush=True)

    out_path = os.path.join(RESULTS, f"crownjewel_{args.tag}.json")
    all_res, done = [], set()
    if args.resume and os.path.exists(out_path):
        prev = json.load(open(out_path))
        all_res = prev.get("results", [])
        done = {r["tower"] for r in all_res}
        print(f"[CJ-H] resume: {len(done)} towers already done: {sorted(done)}", flush=True)

    for name in args.towers:
        if name in done:
            print(f"[CJ-H] skip {name} (already done)", flush=True)
            continue
        print(f"[CJ-H] === tower {name} ===", flush=True)
        r = run_tower(name, imgs, labels, class_names, args, device)
        print(f"[CJ-H] {name}: clean={r['clean_acc']:.3f} SC={r['sc_pred']:.4f} PC={r['pc']:.4f} "
              f"S_text={r['S_text']:.4f} eta/L1={r['eta_over_L1']:.5f} A={r['anisotropy_A']:.2f} "
              f"S={r['S_apgd']} rad_mean={r['robust_radius_mean']:.5f} ({r['seconds']:.0f}s)", flush=True)
        all_res.append(r)
        with open(out_path, "w") as f:
            json.dump({"args": vars(args),
                       "reference_template": REFERENCE_TEMPLATE,
                       "templates_k11": TEMPLATES_K11,
                       "templates_k20": TEMPLATES_K20,
                       "results": all_res}, f, indent=2, default=str)
        print(f"[CJ-H] checkpoint -> {out_path} ({len(all_res)} towers)", flush=True)
    print(f"[CJ-H] DONE -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
