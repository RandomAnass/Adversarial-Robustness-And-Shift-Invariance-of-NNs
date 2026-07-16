# Crown-Jewel v0 — DESIGN note

Goal: on a single clean zero-shot CLIP task, show that **two** kinds of invariance —
visual (image shift) and textual (prompt paraphrase) — are BOTH saturated across modern
CLIP encoders, yet **adversarial robustness is a separate, dissociated axis** that the
threat-matched margin-to-Lipschitz ratio `eta/L1` and gradient anisotropy `A` predict while
neither consistency does. This makes the parent thesis ("invariance is not robustness")
*multimodal*: shift + text + images.

## What already exists (reused verbatim, not reinvented)
- `towers.py` — `CLIP_TOWERS`, `load_clip_tower(name, class_names, device)`, `build_text_features`,
  `OPENAI_TEMPLATES` (the 10-template zero-shot head ensemble used by the reference towers).
- `data.py` — ImageNet-100 val loader (cached at `results/c1_tower/in100val_cache.pt`), [0,1] px @224.
- `diagnostics.py` — `margin_and_grad` (signed margin `M=f_y-max_{j!=y}f_j`, `||grad M||_q`),
  `eta_L_summary` (eta, L1, L2, eta/L1, per-image ratios), `shift_consistency` (SC = frac top-1
  unchanged under a patch-grid phase sweep of integer circular shifts), `patch_grid_offsets`.
- `attacks.py` — `run_autoattack` (APGD-CE + APGD-t, Linf, [0,1] px), `per_image_robust_radius_linf`
  (PGD bisection over an eps grid), `run_pgd_eval`, `robust_acc`.

## The one NEW axis — PARAPHRASE-CONSISTENCY (textual analog of shift-consistency)
Zero-shot CLIP classifies by comparing an image embedding to per-class text prototypes built
from a prompt template. The reference head uses the **reference template** `"a photo of a {}."`.

- Standard OpenAI ImageNet ensemble = 80 templates (pulled from `open_clip.OPENAI_IMAGENET_TEMPLATES`).
- We curate a set of **semantically-equivalent paraphrases**: templates that all say *"here is a
  {class}"* in different words, WITHOUT changing the depicted content or its attributes. We therefore
  KEEP neutral rephrasings of "a photo of a {}" and EXCLUDE templates that change semantics:
  rendering/medium changes (sculpture, tattoo, drawing, painting, origami, cartoon, plushie, toy,
  video game, graffiti, embroidered, doodle, sketch), quantity ("many", "one"), size/quality
  attributes ("large", "small", "weird", "dirty", "hard to see", "cool", "nice"), and degradations
  ("blurry", "pixelated", "jpeg corrupted", "low resolution", "black and white") — those are
  distribution shifts, not paraphrases.

  Curated paraphrase set (11 templates, all article/word variants of "here is a {class}"):
    - `a photo of a {}.`               (also the reference template)
    - `a photo of the {}.`
    - `an image of a {}.`
    - `a picture of a {}.`
    - `a photo of one {}.`
    - `a good photo of a {}.`          (neutral positive, no attribute change)
    - `a close-up photo of a {}.`      (framing only, same object)
    - `a cropped photo of a {}.`       (framing only, same object)
    - `a bright photo of a {}.`        (lighting only, kept as a mild-neutral paraphrase)
    - `itap of a {}.`                  ("I took a photo of a", reddit convention, same meaning)
    - `a bad photo of a {}.`           (same object, quality word only)

  We report the result honestly whether or not paraphrase-consistency is saturated. The
  reference-vs-itself template gives consistency = 1.0 by construction (sanity check).

**PARAPHRASE-CONSISTENCY per image** = fraction of the paraphrase templates under which the
top-1 predicted class is UNCHANGED relative to the reference template `"a photo of a {}."`.
Each template's per-class prototype is a SINGLE-template text feature (not the 10-template
ensemble), so we isolate the effect of the wording. Aggregate to per-model mean over correct images.

## Evaluation set (matches the repo's shift-consistency convention)
- ImageNet-100 val, cached loader, `n_diag = 1000` decoded images (seed 0).
- Keep only images the **reference-prompt tower** (single template `"a photo of a {}."`)
  classifies correctly — this is the SC/paraphrase population (top-1 unchanged is only meaningful
  relative to a correct reference). Attacks/radius run on the same correct subset.

## Panel (diverse: >=3 non-robust openai + >=4 robust FARE/TeCoA)
Non-robust (openai / laion, S~0 expected):
  `clip` (ViT-L/14 openai), `clip_b16_openai` (ViT-B/16 openai), `clip_b32_laion2b`,
  `clip_l14_laion2b`  (4 non-robust; >=3 satisfied, >=1 openai family beyond L/14).
Robust FARE/TeCoA (S>0 expected, eps=4/255-trained):
  `fare4`, `tecoa4`, `fare2`, `tecoa2` (L/14 base), plus `fare4_b32`, `fare4_b16` if time permits.
  (>=4 robust satisfied by fare4/tecoa4/fare2/tecoa2.)

## Per-model measurements
(a) SHIFT-consistency `sc_pred` (reuse `shift_consistency` + `patch_grid_offsets(max_shift=8,
    compact=True)`, the repo's exact shift set), on the correct subset. Also `sc_cos`.
(b) PARAPHRASE-consistency `pc` (new; single-template heads; reference = `"a photo of a {}."`).
(c) ADVERSARIAL robustness: threat-matched Linf. `run_autoattack` (APGD-CE+APGD-t) robust acc
    `S` at eps=4/255 on the correct subset, and per-image Linf robust radius (`per_image_robust_radius_linf`).
    Non-AT towers -> S~0 (expected, part of the dissociation).
(d) `eta/L1` (threat-matched) + anisotropy `A = ||grad M||_1 / ||grad M||_2` (= per-image
    `ratio_l2 / ratio_l1`, aggregated as mean over correct images), via `margin_and_grad` /
    `eta_L_summary`. These reuse the exact per-image code.

Note: (a)-(d) all use the SAME reference single-template head so the panel is internally
consistent (margins/gradients/attacks/SC/PC all defined against `"a photo of a {}."`).

## Headline analysis
1. Two-axis saturation table: mean+/-sd of SC and PC across the panel; both near 1.0, small spread.
2. Dissociation: Spearman(SC, S) and Spearman(PC, S) across encoders, with bootstrap 95% CIs
   (near-zero / negative expected). Also vs per-image mean robust radius.
3. Prediction: Spearman(eta/L1, robust radius) positive; among ROBUST towers, Spearman(A, radius)
   negative (parent finding), while neither consistency ranks robustness. Recompute >=1 headline
   correlation two ways (per-tower Spearman AND rank-agreement) as a check.
4. Bonus: Spearman(SC, PC) — are visually-invariant encoders also paraphrase-invariant? Report, no over-interpret.

## Figure (one clean PDF -> paper/figures/crownjewel_v0.pdf)
Scatter/panel: x = a consistency axis (SC and PC, both saturated near 1), y = robust acc S
(spread 0..~0.7), points = encoders colored by robust/non-robust; a side panel showing eta/L1
DOES track S while the consistencies do not. Caption states exactly what is shown, no overclaim.

## Rigor / verification
- Reuse verified attack/margin/shift code (no reimplementation).
- Sanity: robust_acc <= clean_acc; PC(reference vs reference) = 1.0; a non-robust tower has S~0;
  fare4 has clearly higher robust radius than clip. Recompute one headline corr two ways.
- Memory: one tower at a time, `del tower; torch.cuda.empty_cache()`; attack/grad bs<=16-48.
- Save raw per-model JSON -> `results/c1_tower/crownjewel_v0.json`; per-image .pt as needed.
- GPU 1 ONLY (`CUDA_VISIBLE_DEVICES=1`). v0 pilot: establish the dissociation cleanly + honestly.
