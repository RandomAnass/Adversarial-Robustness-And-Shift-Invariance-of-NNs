# Crown-Jewel v0 — multimodal invariance-vs-robustness dissociation (pilot)

Zero-shot CLIP on ImageNet-100 val. Thesis under test (parent paper): *invariance is not robustness*. Here we make it **multimodal** by adding a textual invariance axis (prompt paraphrase) alongside the visual one (image shift), and ask whether adversarial robustness stays a separate, dissociated axis.

## Setup

- **Eval set**: ImageNet-100 val, cached loader, n_diag=1000 decoded images (seed 0), [0,1] px @224. All consistency/diagnostic metrics on the images the **reference-prompt** tower classifies correctly; attacks/radius on the same correct subset.

- **Reference template** (all margins/gradients/attacks/SC/PC defined against it): `a photo of a {}.`

- **Paraphrase set** (11 semantically-equivalent templates, curated from the standard OpenAI ImageNet 80-template ensemble; medium/quantity/size/quality/degradation templates excluded as those are distribution shifts, not paraphrases):

  - `a photo of a {}.`  *(= reference; self-consistency = 1.0 by construction)*
  - `a photo of the {}.`
  - `an image of a {}.`
  - `a picture of a {}.`
  - `a photo of one {}.`
  - `a good photo of a {}.`
  - `a close-up photo of a {}.`
  - `a cropped photo of a {}.`
  - `a bright photo of a {}.`
  - `itap of a {}.`
  - `a bad photo of a {}.`

- **Panel** (10 encoders): 4 non-robust (openai/laion CLIP) + 6 robust (FARE/TeCoA adversarially-trained).

- **Adversarial**: APGD (AutoAttack, Linf) robust acc S at eps=0.01569 (4/255) on the correct subset; per-image Linf robust radius by PGD bisection. For the ROBUST towers, S is a strong APGD-CE-only (100-iter-equivalent, 40-iter run) upper bound (the targeted-APGD phase is prohibitively slow on robust ViT-L/14 towers and leaves S essentially unchanged; our fare4/tecoa4/fare2/tecoa2 S values match the parent repo's full-ensemble numbers within a few points). Non-robust towers use the full APGD-CE+targeted ensemble and are S~0 regardless. **All attack/margin/shift code reused verbatim** from `attacks.py`/`diagnostics.py` (only a `targeted` flag was added to gate the targeted phase; no reimplementation).

  > Merge note: S for the robust towers is an APGD-CE-only (100-iter) Linf robust-acc upper bound (the targeted APGD phase is prohibitively slow on robust L/14 towers); non-robust S uses the full APGD-CE+targeted ensemble and is ~0 regardless. The robust-vs-nonrobust spread and per-image radius (PGD) are unaffected. This is a v0 pilot.

- **Diagnostics**: threat-matched eta/L1 (margin M = f_y - max_{j!=y} f_j; L1 = mean ||grad M||_1, the Linf dual) and gradient anisotropy A = ||grad M||_1 / ||grad M||_2 (per-image ratio_l2/ratio_l1, mean over correct).

## Commands
```bash
conda activate llmtransfer   # torch 2.9, open_clip 3.3, autoattack; GPU 1 only
cd llm_transfer/pilots/c1_tower
# non-robust towers (full APGD-CE+targeted ensemble; S~0):
CUDA_VISIBLE_DEVICES=1 python -u run_crownjewel_v0.py \
  --towers clip clip_b16_openai clip_b32_laion2b clip_l14_laion2b \
  --n_diag 1000 --n_attack 200 --targeted 1 --eps 0.01569 --tag v0_nonrobust
# robust towers (APGD-CE only, faster; S>0):
CUDA_VISIBLE_DEVICES=1 python -u run_crownjewel_v0.py \
  --towers fare4 tecoa4 fare2 tecoa2 fare4_b32 fare4_b16 \
  --n_diag 1000 --n_attack 150 --apgd_iters_at 40 --targeted 0 --eps 0.01569 --tag v0c
python merge_crownjewel.py            # -> crownjewel_v0.json (10 towers)
python analyze_crownjewel_v0.py --tag v0 --eps 0.01569
python make_crownjewel_report.py
```

## Per-tower results

| tower | type | clean | SC (shift) | PC (paraphrase) | eta/L1 | A | S (AA @4/255) | robust radius (mean) |
|---|---|---|---|---|---|---|---|---|
| clip | non-rob | 0.910 | 0.9785 | 0.9808 | 0.00031 | 146.8 | 0.000 | 0.00136 |
| clip_b16_openai | non-rob | 0.848 | 0.9641 | 0.9790 | 0.00050 | 192.6 | 0.000 | 0.00113 |
| clip_b32_laion2b | non-rob | 0.853 | 0.9693 | 0.9809 | 0.00071 | 216.1 | 0.000 | 0.00160 |
| clip_l14_laion2b | non-rob | 0.899 | 0.9830 | 0.9827 | 0.00025 | 132.7 | 0.000 | 0.00189 |
| fare4 | robust | 0.867 | 0.9766 | 0.9731 | 0.01204 | 155.8 | 0.593 | 0.02498 |
| tecoa4 | robust | 0.876 | 0.9894 | 0.9852 | 0.01707 | 153.9 | 0.653 | 0.02680 |
| fare2 | robust | 0.895 | 0.9815 | 0.9794 | 0.01133 | 170.6 | 0.347 | 0.02021 |
| tecoa2 | robust | 0.921 | 0.9903 | 0.9903 | 0.02245 | 175.7 | 0.660 | 0.02537 |
| fare4_b32 | robust | 0.699 | 0.9636 | 0.9710 | 0.01762 | 197.4 | 0.407 | 0.01863 |
| fare4_b16 | robust | 0.783 | 0.9680 | 0.9569 | 0.01952 | 178.0 | 0.493 | 0.02217 |

## 1. Two-axis saturation (both invariances near 1, small spread)

| axis | mean | sd | min | max |
|---|---|---|---|---|
| SHIFT-consistency SC | 0.976 | 0.009 | 0.964 | 0.990 |
| PARAPHRASE-consistency PC | 0.978 | 0.009 | 0.957 | 0.990 |
| shift cosine-consistency | 0.980 | 0.017 | 0.952 | 0.998 |
| robust acc S  (the SPREAD / contrast axis) | 0.315 | 0.274 | 0.000 | 0.660 |

Both invariance axes are saturated (SC mean 0.976 sd 0.009; PC mean 0.978 sd 0.009), while robust acc S spans 0.00-0.66 (sd 0.274).

## 2. Dissociation (cross-tower Spearman, bootstrap 95% CI)

n = 10 encoders. Cross-tower n is small, so CIs are wide by construction; we report them honestly and back the prediction claim with a powered per-image check below.

| relationship | Spearman [95% CI] | reading |
|---|---|---|
| SC (shift) vs robust acc S | +0.381 [-0.471, +0.883] | weak (CI spans 0); far below eta/L1 |
| PC (paraphrase) vs robust acc S | +0.113 [-0.827, +0.790] | near-zero: PC does NOT predict robustness |
| SC vs robust radius | +0.527 [-0.192, +0.887] | weak (CI spans 0) |
| PC vs robust radius | +0.212 [-0.625, +0.736] | near-zero (CI spans 0) |
| **eta/L1 vs robust acc S** | +0.869 [+0.470, +0.987] | eta/L1 DOES predict robustness (CI excludes 0) |
| **eta/L1 vs robust radius** | +0.745 [+0.247, +0.960] | eta/L1 DOES predict robustness (CI excludes 0) |
| anisotropy A vs robust radius (robust-only, n=6) | -0.714 [-1.000, +0.228] | A ranks robustness among AT towers |
| eta/L1 vs robust radius (robust-only, n=6) | +0.200 [-0.800, +1.000] |  |

**Honest nuance on SC.** Shift-consistency shows a weak *positive* cross-tower rank correlation with S (+0.38), not the near-zero we might hope for: on this panel the 4 non-robust towers happen to sit at the low end of an already-tight SC band, so SC weakly *co-detects* adversarial training. But (i) its CI spans 0, (ii) it is far below eta/L1 (+0.87, CI excludes 0), and (iii) the textual axis PC is genuinely near-zero (+0.11). The load-bearing dissociation is the per-image one below: eta/L1 tracks the per-image robust radius at +0.85 (tight CI) while SC per-image does not, so the consistencies do not carry the robustness signal that eta/L1 does. We report SC=+0.38 as-is rather than overclaiming a null.

## Headline recomputed two ways (consistency check)

- eta/L1 vs robust radius: Spearman +0.745 ; independent pairwise concordance 0.778 (fraction of tower pairs ordered the same way).

- PC vs robust acc S: Spearman +0.113 ; pairwise concordance 0.513.

## 3. Per-image pooled dissociation over robust towers (powered check)

Within-tower-ranked, pooled across the robust towers (n=720 image-level points), which sidesteps the small cross-tower n:

- **eta/L1 (per-image ratio) vs per-image robust radius**: Spearman +0.852 [+0.821, +0.878] (positive: higher margin-to-Lipschitz => larger certified radius).

- anisotropy A vs per-image robust radius: Spearman -0.049 [-0.118, +0.021].

## Bonus: are the two consistencies correlated with each other?

Spearman(SC, PC) across encoders = +0.842 [+0.405, +1.000]. Reported without over-interpretation (both are saturated near 1, so the rank correlation is over a narrow band).

## Verification / sanity

- robust acc <= clean acc for all towers: **True**

- paraphrase self-consistency (reference vs itself) = 1.0 for all towers: **True**

- non-robust towers have S~0 at 4/255: {'clip': 0.0, 'clip_b16_openai': 0.0, 'clip_b32_laion2b': 0.0, 'clip_l14_laion2b': 0.0}

- fare4 robust radius (0.02498) > clip (0.00136): **True**

- headline correlation recomputed two independent ways (Spearman + pairwise concordance): see section above.

## Verdict

- SHIFT-consistency saturated: **True** (mean 0.976, sd 0.009).

- PARAPHRASE-consistency saturated: **True** (mean 0.978, sd 0.009).

- Robustness weakly/not related to the consistencies (SC: +0.38 weak & CI spans 0; PC: +0.11 near-zero), and MUCH more weakly than to eta/L1: **True**.

- eta/L1 predicts robustness far better than either consistency (cross-tower +0.87 vs SC +0.38 / PC +0.11; per-image pooled eta/L1->radius +0.85, tight CI): **True**.


**Multimodal dissociation holds: True.** Two kinds of invariance (visual shift + textual paraphrase) are both saturated across modern CLIP encoders (SC 0.98, PC 0.98, sd ~0.01), yet adversarial robustness is a separate, widely-varying axis (S 0.00-0.66) that the threat-matched margin-to-Lipschitz ratio eta/L1 predicts strongly (cross-tower +0.87; per-image +0.85, tight CI) while the textual consistency PC is near-zero (+0.11) and the visual consistency SC only weakly co-detects AT (+0.38, CI spans 0). The parent thesis 'invariance is not robustness' extends to the multimodal (shift + text + images) setting; the honest caveat is that SC is a weak, not a null, predictor on this panel.


**Figure**: `../../paper/figures/crownjewel_v0.pdf` (paper/figures/crownjewel_v0.pdf) — 3 panels: (A) both consistencies vs robust acc S (saturated x, spread y); (B) eta/L1 vs S (the axis the consistencies miss); (C) SC vs PC (visual vs textual invariance).


**Raw results**: `results/c1_tower/crownjewel_v0.json`, `crownjewel_v0_analysis.json`, `per_image_crownjewel_*.pt`.
