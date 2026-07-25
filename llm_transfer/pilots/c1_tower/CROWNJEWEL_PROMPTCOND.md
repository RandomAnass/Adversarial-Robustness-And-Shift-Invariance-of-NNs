# Crown-Jewel PROMPT-CONDITIONED — RESULTS

_Image-adversarial robustness measured ACROSS a set of meaning-preserving TEXT PROMPTS, in parallel
("an image attack run against text prompts in parallel"). Strong version of the multimodal
crown-jewel: no text attack; the attack stays on the image (where the spread lives) but is run
against K different meaning-preserving zero-shot heads._

Raw: `results/c1_tower/crownjewel_promptcond.json` (+ `_analysis.json`); per-image
`per_image_promptcond_{encoder}_{pid}.pt`; figure `paper/figures/crownjewel_promptcond.pdf`.

## Design actually run

- **Panel:** _(filled after run)_ non-robust + robust CLIP encoders (incl ViT-L/14 robust towers
  fare4/tecoa4/fare2/simclip; B/16 + convnext for backbone diversity; 3 AT families FARE/TeCoA/Sim-CLIP).
- **Prompts (K=6, meaning-preserving):** `a photo of a {}.` (reference), `a photo of the {}.`,
  `an image of a {}.`, `a picture of a {}.`, `a cropped photo of a {}.`, `itap of a {}.`
  PLUS an ENSEMBLE head (mean of the 6 text embeddings, renormalized = standard CLIP prompt ensemble).
- **Per (encoder, prompt) [and ensemble]:** clean acc under that prompt's head; full targeted
  AutoAttack (APGD-CE + APGD-T, n_iter=100, 3 targets, Linf eps=4/255) robust acc on n_attack images
  correct-under-that-prompt; per-image Linf robust radius (PGD bisection); threat-matched eta/L1 and
  anisotropy A on the margin gradient of that prompt's head.
- **Per encoder (prompt-independent / prompt-set):** shift-consistency SC; paraphrase-consistency PC.
- **Cross-prompt transfer:** advs crafted under each prompt evaluated under every other prompt's head.

## (Table) per (encoder x prompt) — filled after run

## Pre-registered analyses — filled after run

- (A) does eta/L1 predict image-adversarial robustness across the prompt axis?
- (B) does prompt-invariance (ensemble) confer robustness beyond eta/L1?
- (C) cross-prompt adversarial transfer.
- (D) 2x2 restatement.

## Sanity gates — filled after run

## Verdict — filled after run
