# Crown-Jewel HARDENED — DESIGN (for human review; NOT yet run)

A hardened, pre-registered version of the multimodal invariance-vs-robustness dissociation.
The goal is a clean **2×2 factorial (modality × perturbation-type)** that makes
*"invariance is not robustness"* a **modality-general** phenomenon.

|                        | INVARIANCE (average-case, natural)     | ADVERSARIAL (worst-case)                          |
|------------------------|----------------------------------------|---------------------------------------------------|
| **IMAGE** (fixed text) | shift-consistency over pixel shifts    | Linf/L2 attack on pixels (robust acc S + radius)  |
| **TEXT** (fixed image) | paraphrase-consistency over rewordings | **worst-case over meaning-preserving rewordings** |

**Thesis (pre-registered).** The two INVARIANCE cells (left column) are *saturated* across
encoders (small spread near 1); the two ADVERSARIAL cells (right column) have *wide spread*; and
the threat-matched margin-to-Lipschitz ratio η/L (plus gradient anisotropy A) predict the
adversarial cells while the consistencies do not. v0 already established three of the four cells
(both invariances saturated: SC 0.976±0.010, PC 0.978±0.009; image-adversarial spans 0–0.66; η/L1
predicts it at cross-tower +0.87 / per-image +0.85; paraphrase-consistency is a clean null at
+0.11). **The one genuinely new cell is TEXT-ADVERSARIAL (bottom-right).** This document justifies
that cell against the literature, expands the encoder panel to power the tower axis, upgrades the
image-attack protocol to full targeted AutoAttack, and pre-registers the analysis and figure.

This is a **design proposal**: the new mechanism is smoke-tested (see §4) and 2 new robust
encoders are download-verified and wired into `towers.py`, but the full evaluation is **not run**.

---

## 1. The new cell — TEXT-ADVERSARIAL (worst-case over meaning-preserving paraphrases)

### 1.1 Definition (the worst-case sibling of average-case paraphrase-consistency)

Zero-shot CLIP classifies image `x` (true label `y`) by comparing the image embedding to
per-class text prototypes built from a prompt template `t`. Fix a set of **K meaning-preserving
templates** `T = {t_1,…,t_K}` — the SAME curated family used for average-case
paraphrase-consistency (v0). Let `pred_t(x)` be the top-1 under the single-template head `h_t`.

- **Average-case (v0, invariance cell):** paraphrase-consistency `PC = mean_x mean_t 1[pred_t(x) = pred_ref(x)]` — how *often* a reword leaves the label put. Textual accuracy implied by it: `a_avg = mean_x mean_t 1[pred_t(x) = y]`.
- **Worst-case (new, adversarial cell):** **adversarial-paraphrase robust accuracy**
  `S_text = mean_x  min_t 1[pred_t(x) = y] = mean_x 1[ pred_t(x) = y  ∀ t ∈ T ]`.
  An image is "text-robust" iff **no** meaning-preserving reword in the set flips it off the true
  label. This is a discrete `min` over a semantically-null perturbation family — the exact textual
  analog of the image cell's *average shift-consistency* (SC) vs *worst-case ε-ball* (AutoAttack S).

By construction `S_text ≤ a_avg ≤ a_ref ≤ 1` (worst ≤ average ≤ reference-clean; smoke-verified §4).

### 1.2 Why THIS is the right, clean choice for zero-shot CLIP (literature)

The natural-language adversarial-robustness literature warns that automated word-substitution
attacks *do not reliably preserve meaning*, which is fatal for a benchmark whose whole point is a
**semantically-null** perturbation family (so that any label flip is a model failure, not a
content change).

- **CLIP prompt ensembles / the 80-template set.** Zero-shot CLIP is standardly evaluated with an
  ensemble of prompt templates; the canonical ImageNet set is **80 templates** (Radford et al.,
  CLIP, 2021), which lifts ImageNet zero-shot top-1 by ≈3.5% over the single `"a photo of a {}."`
  prompt and was hand-tuned over ≈a year. We verified in-environment that
  `open_clip.OPENAI_IMAGENET_TEMPLATES` contains **exactly 80** templates. Our K-template
  meaning-preserving set is a *curated subset* of these 80 (see §1.3), so the family is drawn from
  the community-standard prompt distribution — not invented for this paper. CLIP zero-shot accuracy
  is known to be sensitive to the *exact wording* of the prompt/class name (a documented source of
  variance; e.g. class-name swaps cause large metric swings in CLIP anomaly segmentation,
  arXiv:2505.17692), which is precisely why a worst-case-over-wordings axis is meaningful.
  Refs: CLIP paper https://arxiv.org/abs/2103.00020 ; open_clip
  https://github.com/mlfoundations/open_clip ; OpenAI prompt-engineering notebook
  https://github.com/openai/CLIP/blob/main/notebooks/Prompt_Engineering_for_ImageNet.ipynb ;
  Allingham et al. "A Simple Zero-shot Prompt Weighting Technique" https://openreview.net/pdf?id=6MU5xdrO7t .

- **Meaning-preserving textual attacks and why we do NOT use them.** TextFooler
  (Jin et al., AAAI 2020, https://arxiv.org/abs/1907.11932) replaces "important" words with
  embedding-nearest synonyms filtered by POS + a sentence-similarity threshold; BERT-Attack
  (Li et al., EMNLP 2020, https://arxiv.org/abs/2004.09984) substitutes via a masked-LM;
  DeepWordBug (Gao et al., 2018, https://arxiv.org/abs/1801.04354) makes character-level edits
  (swap/flip/insert/delete). **Morris et al., "Reevaluating Adversarial Examples in Natural
  Language" (EMNLP Findings 2020, https://arxiv.org/abs/2004.14174 ;
  https://aclanthology.org/2020.findings-emnlp.341/ ) show these attacks routinely break
  meaning/grammar:** TextFooler perturbations **introduce grammatical errors ≈38% of the time**,
  and when semantic + grammatical constraints are tightened to actually preserve meaning, the
  **attack success rate drops by >70 percentage points** — i.e. most of the "successful" attacks
  were relying on meaning drift. For a benchmark that must attribute every label flip to model
  brittleness (not to the prompt now describing a different thing), automated substitution is the
  wrong tool. A **human-curated discrete set guarantees meaning-preservation by construction** —
  exactly the mitigation Morris et al. advocate.

### 1.3 Alternatives considered — ruled in/out

| Alternative | Verdict | Reason |
|---|---|---|
| **(chosen) Worst-case min over a curated meaning-preserving template set** | **IN** | Meaning-preservation is guaranteed by human curation from the standard 80-template set; discrete `min` is the exact worst-case sibling of the average-case PC; no separate text-attack machinery; comparable across encoders (same K templates, all towers share the frozen OpenAI text tower). |
| (i) Synonym / word-substitution attack on the class name (TextFooler-style) | OUT | Morris et al.: ≈38% ungrammatical, meaning drift; class-name synonyms (e.g. "Doberman"→"dog") change the *label semantics*, not just the wording. Not semantically null. |
| (ii) Character-level typos / DeepWordBug | OUT | Not meaning-preserving in spirit (it tests OCR/tokenization brittleness, a different axis); "itap"-style noise would confound the clean average-vs-worst contrast. Could be a supplementary robustness axis, not the main cell. |
| (iii) Adversarial suffixes (GCG-style) | OUT | Designed for autoregressive LLM jailbreaks; appends nonsense tokens that are *not* meaning-preserving and have no natural average-case sibling. |
| (iv) Embedding-space attack on the text tower | OUT | Produces an unrealizable off-manifold text embedding with no natural-language preimage, so "meaning-preserving" is undefined; it also breaks comparability because it needs per-encoder text-tower gradients while our thesis fixes ONE shared text tower. |

**Honest asymmetry.** The image-adversarial cell is a **continuous ε-ball** worst-case; the
text-adversarial cell is a **discrete finite-set** worst-case. We do not hide this. The **unifying
axis that makes the 2×2 fair is *average-case vs worst-case over a semantically-null perturbation
family***, not the cardinality of the family. In BOTH modalities: (a) the perturbation set is
meaning/label-preserving by design (pixel shifts and ε-balls leave the depicted object unchanged;
curated rewordings leave the described object unchanged); (b) the invariance cell reports the
*average* behavior over that set and the adversarial cell reports the *worst* element of it; (c)
the same encoders and the same reference head are used throughout. The discrete text `min` is a
*lower-bound* proxy for the true worst-case-over-all-meaning-preserving-English (we can only
enumerate a finite set), which we state as a limitation; enlarging K tightens it monotonically.

### 1.4 The perturbation "budget" (K, curation, comparability)

- **Template family:** the K templates are the v0 curated set (11 templates), all article/word
  variants of *"here is a {class}"* selected from the standard OpenAI 80-template ensemble, with
  medium/quantity/size/quality/degradation templates EXCLUDED (those are distribution shifts, not
  paraphrases). `"a photo of a {}."` is the reference (self-consistency = 1.0 by construction).
- **Curation guarantee:** every template is a neutral rephrasing that does not change the depicted
  object or its attributes; this is the meaning-preservation guarantee Morris et al. require.
- **Budget K:** default **K = 11** (matches v0's average-case set exactly, so the average and
  worst-case cells are the SAME family). We pre-register a **sensitivity check at K = 20** (add
  more neutral rewordings drawn from the 80-set, e.g. `"a photo of my {}."`, `"a snapshot of a
  {}."`, `"a photograph of a {}."`) to confirm `S_text` moves monotonically down and the ranking
  across encoders is stable. K is **identical across all encoders**.
- **Comparability across encoders:** all towers use the SAME K templates and the SAME frozen
  shared OpenAI CLIP text tower (FARE/TeCoA/Sim-CLIP only fine-tune the *vision* tower), so the
  text prototypes differ across encoders ONLY through what each vision tower's embedding does —
  the axis is apples-to-apples.

---

## 2. Expanded encoder panel (power the tower axis — the v0 caveat)

v0 ran **10 encoders (4 non-robust + 6 robust)**; the cross-tower n was small (wide CIs). The
hardened panel roughly **doubles the robust side to ≥12 robust encoders** while keeping ≥4
non-robust. Sources were surveyed for *downloadable* robust CLIP checkpoints (all URLs below were
reachability-checked; the two marked **VERIFIED-LOADED** were actually downloaded and run through
the load path + a 120–200-image clean-accuracy sanity this session).

### 2.1 Already present (10; unchanged)
Non-robust (4): `clip` (ViT-L/14 openai), `clip_b16_openai`, `clip_b32_laion2b`,
`clip_l14_laion2b`.
Robust FARE/TeCoA, chs20/RobustVLM (6): `fare4`, `tecoa4`, `fare2`, `tecoa2` (ViT-L/14),
`fare4_b32`, `fare4_b16` (and `tecoa4_b32/b16/fare4_cnxt/tecoa4_cnxt` already wired in `CLIP_TOWERS`).
*Note:* the chs20 org (RobustVLM, Schlarmann et al., ICML 2024, https://arxiv.org/abs/2402.12336)
was exhaustively listed — it has **exactly** these CLIP checkpoints plus DINO/FuseLIP variants that
are NOT zero-shot CLIP; so doubling the panel requires OTHER sources.

### 2.2 NEW robust candidates (added / recommended)

Load recipe A = `hf-hub:` open_clip drop-in; B = inject `model.visual` state_dict into an open_clip
base with the shared OpenAI text head (helper `towers.load_vision_injected_tower`, added this
session); C = transformers-format `CLIPModel` → pull `.vision_model` (or convert to open_clip).

| tower key | hf repo / file | arch | method | norm/eps | recipe | status |
|---|---|---|---|---|---|---|
| **`simclip4`** | `hossainzarif19/SimCLIP` `simclip4.pt` | ViT-L-14 | **Sim-CLIP** (Siamese/stop-grad AT; new FAMILY) | Linf 4/255 | B | **VERIFIED-LOADED, clean acc 0.820** |
| **`simclip2`** | `hossainzarif19/SimCLIP` `simclip2.pt` | ViT-L-14 | Sim-CLIP | Linf 2/255 | B | **VERIFIED-LOADED, clean acc 0.875** |
| `leaf_H_fare2` | `LEAF-CLIP/OpenCLIP-ViT-H-FARE2` | ViT-H-14 | FARE | Linf 2/255 | C | reachable (transformers-format; needs convert) |
| `leaf_g_fare2` | `LEAF-CLIP/OpenCLIP-ViT-g-FARE2` | ViT-g-14 | FARE | Linf 2/255 | C | reachable |
| `leaf_L_fare2` | `LEAF-CLIP/CLIP-ViT-L-FARE2` | ViT-L-14 | FARE | Linf 2/255 | C | reachable (config.json + model.safetensors) |
| `leaf_L_text` | `LEAF-CLIP/CLIP-ViT-L-rho50-k1-constrained-FARE2` | ViT-L-14 | **LEAF** (FARE image + Levenshtein-k1 **robust TEXT tower**) | Linf 2/255 + char k=1 | C | reachable; only panel member with a robustified text tower |
| `delta_l14_vis` | `zw123/delta_clip_l14_224` `open_clip_pytorch_model.bin` | ViT-L-14-quickgelu | **Double Visual Defense** (SOTA) | Linf 4/255 | B* | **DEFERRED — flagged** |
| `delta_h14` | `zw123/delta_clip_h14_336` | ViT-H-14 (336) | Double Visual Defense | Linf 8/255 | B*/A(after config patch) | reachable |

`delta_l14_vis` was download-tested this session: injecting only its `visual.*` keys into a stock
ViT-L-14 gives ~chance accuracy (missing `ln_pre` + a QuickGELU mismatch, and DVD adversarially
trains the **text** tower too — "Double Visual Defense" — so the shared OpenAI head is the wrong
text space). It needs its OWN quickgelu text tower to be usable. It is wired in
`HARDENED_NEW_ROBUST_SPEC` **but excluded from the run list** until that is done. Similarly the
LEAF and ΔCLIP-H entries are reachability-confirmed but need a converter/config patch (recipe C or
the config-patch for the `vocab_path` issue) — recommended for the human to green-light before we
invest the conversion.

**Panel to run (proposed): 4 non-robust + 12 robust = 16 encoders.**
Robust = the 10 existing (fare/tecoa × {L14, B32, B16, cnxt}) + **`simclip4`, `simclip2`** (verified)
→ **12 robust**, hitting the target with only download-verified drop-ins. If the human approves the
conversion effort, adding `leaf_H_fare2`, `leaf_g_fare2`, `leaf_L_text` (new arch scales H/g and a
robust-text tower) and `delta_h14` pushes to ~16 robust and broadens arch/method/eps substantially.

Sources: Sim-CLIP https://arxiv.org/abs/2407.14971 (+ Sim-CLIP+ https://arxiv.org/abs/2409.07353),
checkpoints https://huggingface.co/hossainzarif19/SimCLIP ;
LEAF org https://huggingface.co/LEAF-CLIP , code https://github.com/LIONS-EPFL/LEAF ,
paper https://arxiv.org/abs/2506.03355 ;
Double Visual Defense / ΔCLIP https://arxiv.org/abs/2501.09446 ,
https://huggingface.co/collections/zw123/delta-clip-67d770f8868b5bb02ee99041 ;
RobustVLM (FARE/TeCoA) https://arxiv.org/abs/2402.12336 .
**Dead ends (no released weights):** PMG-AFT (arXiv:2401.04350, code-only), TIMA (arXiv:2405.17678).

---

## 3. The full design (pre-registered)

### 3.1 Data and population
- **n_images:** ImageNet-100 val, cached loader, **`n_diag = 2000`** decoded images (seed 0),
  [0,1] px @224. (v0 used 1000; we double it — the per-tower consistency/η-L estimates are means so
  they were already tight, but the **attack** subset and per-image radius benefit from more correct
  images, and it costs little relative to the attack. Justification: SC/PC/η-L are cheap; the extra
  images mostly widen the correct-under-reference pool the attack draws from.)
- **Reference head:** single template `"a photo of a {}."`; ALL metrics (clean, margin, gradients,
  attacks, SC, PC, S_text) defined against it, so the panel is internally consistent.
- **Population:** images the reference-prompt tower classifies correctly (top-1-unchanged /
  robust-acc are only meaningful relative to a correct reference); attacks/radius on the same subset.

### 3.2 The four cells (metrics)
| cell | metric | code |
|---|---|---|
| IMAGE-invariance | shift-consistency `SC` (frac top-1 unchanged over patch-grid circular shifts) + `SC_cos` | reuse `diagnostics.shift_consistency`, `patch_grid_offsets(max_shift=8, compact=True)` |
| TEXT-invariance | paraphrase-consistency `PC` (frac top-1 unchanged over K rewordings) | reuse `run_crownjewel_v0.paraphrase_consistency` |
| **IMAGE-adversarial** | **full targeted AutoAttack** robust acc `S` (APGD-CE + APGD-T, Linf, eps=4/255) + per-image Linf robust radius (PGD bisection) | `attacks.run_autoattack(..., targeted=True)`, `attacks.per_image_robust_radius_linf` |
| **TEXT-adversarial (NEW)** | **adversarial-paraphrase robust acc `S_text`** = frac images correct under ALL K templates; also per-image `worst_margin_text` = margin under the worst template | new: `worst_case_over_paraphrases` (smoke-tested; §4) |

Predictor diagnostics (reuse per-image code verbatim): threat-matched **η/L1** (margin
`M=f_y−max_{j≠y}f_j`, `L1 = E‖∇M‖_1`, the Linf dual) and gradient **anisotropy
A = ‖∇M‖_1/‖∇M‖_2**, via `diagnostics.margin_and_grad` / `eta_L_summary`.

### 3.3 Image-attack protocol — UPGRADE from the v0 shortcut
v0 used **APGD-CE-only** on the robust towers (a valid robust-acc upper bound, but the v0 caveat).
The hardened run uses the **FULL standard targeted AutoAttack ensemble (APGD-CE + APGD-T,
RobustBench-grade)** on **every** tower (`targeted=True`, `n_iter=100`, `n_target_classes=3`,
`square=False`). This is the honest, community-standard S.

**Cost management (this is the dominant expense).** Targeted APGD on robust ViT-L/14 towers is
slow. We bound it by:
1. **Attack subset cap:** `n_attack = 400` correct-under-reference images per tower (fixed seed 0),
   not the full 2000. AA robust acc is a mean; 400 gives a per-tower SE ≈ √(S(1−S)/400) ≤ 0.025.
2. **Per-tower time cap + checkpointing:** write per-tower JSON immediately after each tower (as v0
   does), so a slow tower can be resumed/killed without losing the panel. Small `attack_bs` (16).
3. **Radius on a sub-subset:** per-image robust radius (PGD bisection) on the first 200 of the
   attack subset (as v0), which feeds the powered per-image η/L1→radius check.
4. **GPU 1 only, one tower at a time**, `del + empty_cache` between towers.
Rough budget: ~16 towers × (targeted AA on 400 imgs @ bs16 + radius on 200) — expect the robust
L/14 towers to dominate (order tens of minutes each). We pre-commit to **not** silently downgrading
any tower to APGD-CE-only; if a tower exceeds the time cap it is reported as "targeted-AA
incomplete" with the APGD-CE upper bound flagged, not merged as if complete.

### 3.4 Pre-registered analysis (avoid post-hoc cherry-picking)
Let `is_robust` index AT towers. Report, each with **bootstrap 95% CI (5000 resamples)**:

**(A) Two-column saturation vs spread (the 2×2 headline).**
mean±sd, min, max of each cell across the panel. **Pre-registered prediction:** the two INVARIANCE
cells (SC, PC) have sd ≈ 0.01 and sit near 1; the two ADVERSARIAL cells (S, S_text) have large sd
and wide range. Report `spread_ratio = sd(adversarial cell)/sd(invariance cell)` per modality.

**(B) Dissociation (cross-tower Spearman).**
`SC vs S`, `PC vs S`, `PC vs S_text`, `SC vs S_text`, `SC vs radius`, `PC vs radius`.
**Pre-registered prediction:** all consistency→adversarial correlations are weak / CI-spans-0
(v0: PC↔S +0.11; SC↔S +0.38). The load-bearing textual claim: `PC vs S_text` — does average-case
textual invariance predict worst-case textual robustness? Reported as-is either way.

**(C) Prediction (the axis the consistencies miss).**
`η/L1 vs S`, `η/L1 vs radius`, `η/L1 vs S_text`; `A vs radius` and `A vs S_text` among robust
towers (n≥12 now). **Pre-registered prediction:** η/L1 predicts BOTH adversarial cells (positive,
CI excludes 0) while neither consistency does. This is the key new test — **does the same margin/
Lipschitz diagnostic that predicts image-adversarial robustness ALSO predict text-adversarial
robustness?** A positive η/L1↔S_text with a null PC↔S_text is the cleanest possible statement of
"invariance is not robustness, in text too."

**(D) Partial correlations.** `partial( η/L1 , S | clean_acc )` and `partial( PC , S | clean_acc )`
(and the S_text analogs), to rule out clean-accuracy as the confound behind any correlation.
Spearman partial via rank-residualization.

**(E) Per-image pooled check (powered, sidesteps small cross-tower n).** Within-tower-ranked,
pooled across robust towers: `η/L1 (per-image ratio) vs per-image robust radius` (v0: +0.85, tight
CI) and, NEW, `per-image worst-template-margin vs per-image robust radius` — is the image that is
easiest to flip *textually* also the one easiest to flip *visually*? (Cross-modal per-image
coupling; reported without over-claim.)

**(F) Two-way headline recompute (consistency check).** Recompute ≥1 headline correlation two
independent ways (Spearman AND pairwise rank-concordance), as v0 did.

**Sanity gates (must pass):** `S ≤ clean_acc` and `S_text ≤ a_avg ≤ a_ref ≤ 1` for every tower;
`PC(ref vs ref)=1.0`; non-robust towers `S≈0` at 4/255; `fare4 radius > clip radius`; the two new
Sim-CLIP towers show `S > 0` (robust) and sit in the robust cluster.

### 3.5 One figure (pre-registered)
**`paper/figures/crownjewel_hardened.pdf` — a 2×2-aligned "saturation vs spread" panel:**
- **Left (the 2×2 as a strip):** four cells as horizontal violin/strip plots of the per-tower
  values, top-to-bottom `SC, PC | S, S_text`, x-axis = metric value in [0,1]. Visually: the two
  invariance rows are tight spikes near 1; the two adversarial rows are broad. One glance = the
  thesis.
- **Right (the predictor):** scatter `η/L1` (x) vs the two adversarial cells `S` and `S_text` (y,
  two series), colored robust/non-robust, with the two Spearman values annotated; overlaid faint
  points show `PC` (x, rescaled) vs the same y to show it does NOT track. Caption states exactly
  what is shown, no overclaim, and names the honest continuous-vs-discrete asymmetry.

Analysis + figure code will mirror `analyze_crownjewel_v0.py` (extended with the S_text cell and
the partials); no new stats machinery is invented.

---

## 4. Smoke test of the NEW mechanism (text-adversarial) — RESULTS

Script: **`smoke_text_adv.py`** (reuses `run_crownjewel_v0.load_tower_with_reference_head`,
`build_single_template_features`, and the SAME `PARAPHRASE_TEMPLATES`/`REFERENCE_TEMPLATE`; no new
model or head machinery). Run on GPU 1, one non-robust tower, a handful of images.

```
CUDA_VISIBLE_DEVICES=1 python -u smoke_text_adv.py --tower clip           --n 64 --bs 64
CUDA_VISIBLE_DEVICES=1 python -u smoke_text_adv.py --tower clip_b32_laion2b --n 96 --bs 64
```

| tower | a_ref | a_avg (PC-implied) | **S_text (worst-case)** | ordering `S_text ≤ a_avg ≤ a_ref ≤ 1` | flipped by SOME reword |
|---|---|---|---|---|---|
| `clip` (ViT-L/14 openai) | 1.000 | 0.983 | **0.906** | ✅ True | **6 / 64 (9.4%)** |
| `clip_b32_laion2b` | 1.000 | 0.983 | **0.927** | ✅ True | **7 / 96 (7.3%)** |

- **(1) Ordering holds** on both towers: `S_text ≤ a_avg ≤ a_ref ≤ 1` (assertions pass).
- **(2) The axis has signal:** a non-robust CLIP is flipped off the true label by *some*
  meaning-preserving reword on ≈7–9% of images that the reference prompt gets right. The worst
  templates on `clip` were `"a photo of the {}."`, `"a good photo of a {}."`, `"itap of a {}."`
  (acc 0.969 each) — plausible neutral rephrasings, not meaning-changers. So worst-case-over-
  paraphrases is a **non-degenerate** robustness axis, distinct from the saturated average-case PC.
- **(3) It runs** on GPU 1, one tower, small batches, ≈20–37 s including model load; no attack code.

The smoke confirms the mechanism is correct and the cell is measurable. In the full run we expect
robust (AT) towers to have `S_text` closer to `a_avg` (fewer text-flips) and the pre-registered
question is whether η/L1 — not PC — ranks `S_text` across the panel.

---

## 5. Open design decisions for the human to rule on

1. **Panel size vs effort.** Run the **verified-only 16-tower panel** (4 non-robust + 12 robust,
   all download-verified drop-ins incl. the 2 new Sim-CLIP) — safe and hits ≥12 robust? Or invest
   the recipe-C conversion to also add LEAF ViT-H/g + a robust-**text** LEAF tower + ΔCLIP-H
   (broadens arch H/g, method, eps 8/255, and adds the ONE robustified-text encoder) for a ~19-tower
   panel? The robust-text LEAF tower is scientifically attractive (it is the only encoder whose text
   tower is itself hardened, a natural probe for the text-adversarial cell) but needs a converter.
2. **`delta_l14_vis` (Double Visual Defense, SOTA).** Include it by building its OWN quickgelu text
   tower from the ΔCLIP `.bin` (it trains vision+text), or leave it deferred? It is wired but
   flagged off. Adding it correctly is ~30 lines but changes the "shared frozen text tower"
   invariant for that one tower — worth discussing whether that breaks comparability.
3. **K (template budget).** Ship at **K=11** (identical to v0's average-case set, cleanest
   average-vs-worst parity) with a pre-registered K=20 sensitivity check? Or make K=20 the headline?
4. **n_attack / time cap.** Is `n_attack = 400` with full targeted AA acceptable given the robust
   L/14 cost, or should we trade to `n_attack = 300` for a faster turnaround? (SE at 400 ≤ 0.025.)
5. **n_images = 2000** vs keeping 1000 (v0). 2000 mainly widens the attack pool; confirm the extra
   decode/cache cost is fine (cache already exists).

Nothing above is run beyond the two smoke commands and the two checkpoint-load verifications; the
full evaluation awaits sign-off.
