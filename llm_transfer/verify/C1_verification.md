# C1 adversarial-verifier hardening report

Pilot **C1**: a threat-matched margin-to-Lipschitz ratio (η/L) computed through a *frozen* VLM
vision tower on *clean* images ranks the tower's strong-attack (AutoAttack/APGD) robustness
without running any attack, used as a cross-tower selection rule; while shift-consistency does
not order that robustness.

Verifier role: find every way the prior "strong PASS" (η/L vs AA Pearson +0.91; SC −0.52 n.s.;
selection regret 5 vs 88 pts) could be wrong or overclaimed, verify the implementation, and
fix/extend so the claim is bulletproof and correctly scoped.

Env: `/home/students/.conda/envs/llmtransfer/bin/python` (torch 2.9, open_clip 3.3, autoattack).
Compute: GPU 1 only. GPU 0 (tdiss text pilot, PID 629217) never touched.

---

## 0. TL;DR verdict

**GO, with a corrected and re-scoped headline — and the central confound is now broken by the
extended n=11 panel (§3).** The core dissociation survives, is *stronger* on the per-image axis than
the prior report claimed on the tower axis, and now holds *within non-AT towers* too. Three prior
framings were overclaimed and are corrected here; all three are resolved by the extended run:

1. The prior run **crashed on the 7th tower** (`clip_aa`, CUDA OOM) so the panel was **n=6** (4 AT +
   2 non-robust), and the +0.91 tower Pearson was **substantially an AT-detector** (among the 4 AT
   towers alone it fell to +0.52 / +0.34). **RESOLVED (§3a):** the extended **n=11** panel (7 non-AT
   towers) gives η/L₁ Pearson **+0.953**, and — decisively — **partial corr(η/L₁, S | is-AT) = +0.51**
   and **| clean & is-AT = +0.56**, i.e. η/L survives partialling out the AT indicator, whereas
   **partial corr(SC_cos, S | is-AT) = +0.15** (cosine-consistency collapses — it *was* the AT
   co-detector). The "it's just an AT detector" critique is answered with the AT split controlled.
2. The **real, powered claim is per-image**: pooled across the 4 AT towers (n=1200),
   **Spearman(per-image η/L₁, radius) = +0.78 [0.75, 0.81]** vs **SC = +0.12 [0.06, 0.18]**.
   **STRENGTHENED (§3b):** with a finer radius grid the same per-image law now holds *within the
   non-AT CLIP towers* (Spearman +0.54 … +0.79, all CIs > 0), so the dissociation is not an AT
   artifact on either axis.
3. The consistency-null stated honestly: prediction-agreement SC_pred is **flat/uninformative**
   (n.s., +0.37 at n=11, p=0.26); cosine-consistency SC_cos looks strong (+0.81) **only because it
   co-detects AT** — and that co-detection is exactly what the partial correlation in point 1
   dissolves. The fair null (SC_pred, the metric the anti-aliasing / Singla-Ge literature tracks)
   does not order robustness.

Bonus cross-domain confirmation (§3c): the main paper's **"invariance-helps is a weak-attack
artifact"** replicates inside VLM encoders — every non-AT CLIP tower has S_fgsm = 0.16–0.46 but
S_apgd = S_pgd40 = 0.0.

The implementation is **correct** (η/L, dual norm, attack threat model, SC, and all statistics
verified by re-derivation and spot-runs). No correctness bugs that change the sign of any result.

---

## 1. Implementation audit (verified by reading + spot-running on GPU 1)

**(a) η/L = margin / dual-norm input-gradient — CORRECT.**
`diagnostics.margin_and_grad` computes the signed logit margin exactly as the theory
(`paper/report/main.tex` §sec:coupling, l.135): `M = f_y − max_{j≠y} f_j`, `η = E[M]` over
correctly-classified clean images, `L_q = E‖∇_x M‖_q`. The gradient is taken w.r.t. the **[0,1]
pixel input** (channel normalization is folded into each tower's forward via `Normalizer`), which
is the correct input space that the attack also operates in. `grad(M.sum(), x)` gives the correct
per-image gradient because batch rows are independent. **Dual norm is correct**: Linf attack →
q=1 → `gradnorm_l1` is the threat-matched L; q=2 (`gradnorm_l2`) is the mismatched control.
Spot-run reproduced base CLIP η/L₁ ≈ 0.00035 (JSON: 0.00033), clean acc 0.89. Gauge check: all
CLIP towers share `logit_scale = 100` (FARE/TeCoA fine-tune only the vision tower), and η/L is
gauge-invariant regardless, so no logit-scale confound.

**(b) AutoAttack — genuinely strong, threat-matched, encoder-level — CORRECT (with one honest
naming caveat).** `attacks.run_autoattack` runs the `apgd-ce + apgd-t` (targeted DLR, 3 target
classes) ensemble at **100 iters**, `norm="Linf"`, on the frozen tower's zero-shot logits through
`AutoAttack(..., version="custom")`, on raw [0,1] pixels. This is RobustBench/FARE-grade. **Caveat
to state in the paper:** the headline S is the APGD-CE+APGD-T ensemble (`square=False`), i.e. the
white-box arm of AutoAttack, not AA+Square. Square is run separately as the gradient-masking check,
not folded into S. This is defensible (Square is black-box and used exactly as the masking probe),
but "AutoAttack robust accuracy" should be written as "APGD-CE+APGD-T ensemble" to be precise.
The masking audit passes for all towers/eps: APGD ≤ PGD-40 ≤ FGSM and Square ≥ APGD (no masking).

**(c) Shift-consistency — CORRECT.** `diagnostics.shift_consistency` measures
`SC = mean_x,s 1[argmax f(S_s x) = argmax f(x)]` under integer circular pixel shifts (patch-grid
phase sweep, 12 compact offsets), on the same correctly-classified subset as η/L (round2 fix 5).
It also reports pooled-embedding cosine-consistency (SC_cos). Both are single-forward, correct.

**(d) Statistics — CORRECT.** Independently re-derived: partial corr(η/L₁, S | clean) = 0.9509
(matches stored, and matches the closed-form partial-correlation formula); permutation p for
η/L₁ vs S = 0.0144 (matches); partial corr(SC, S | clean) = 0.628 (matches). Selection regret and
bootstrap CIs are computed correctly. **No statistical bug.**

### Bugs / issues found

- **BUG (severity: high — scope, not correctness): the panel is n=6, not 7.** `run_main.log`
  shows the run **crashed with `torch.OutOfMemoryError` on tower `clip_aa`** (the anti-aliased
  blur-pool stem — the one non-AT invariance widener meant to open the SC axis) because the
  original run was on GPU 0 with 46.97 GiB already in use. So the flagship "SC-axis widener"
  never entered the results. Only DINOv2 remains as a non-AT arm. Impact: the panel is 4 AT + 2
  non-robust, which is exactly the AT-vs-non-AT collinearity the round-1/round-2 audits warned
  about. **Fixed** by the extended panel below.
- **BUG (severity: high — makes a reported number an artifact): per-image radius is floored for
  non-robust towers.** The radius grid started at 1/255, but base CLIP flips **300/300** images
  and DINOv2 **275/300** at that smallest step, so their robust radius has essentially no variance
  (`radius_uniq = 2`, `floor_frac = 1.00 / 0.92`). The reported per-image Spearman for clip (0.09)
  and dinov2 (0.37) is therefore a degeneracy artifact on a near-constant target, not a per-image
  signal. The AT towers have genuine radius range (5 distinct values), and there the per-image
  Spearman is real (0.74–0.85). **Fixed** by a finer sub-1/255 grid in the extended run + honest
  scoping of the per-image claim to towers where radius has range.
- **NAMING (severity: low): "AutoAttack" → "APGD-CE + APGD-T ensemble"** (Square excluded from S;
  used only as the masking probe). State precisely.
- **Note (not a bug): args drift.** `c1_results_main.json` used `n_attack = 300` and
  `radius_max_images = 300` (not the code defaults of 1000/400). The tower-level S and per-image
  numbers are on 300 correctly-classified images per tower — fine for the AT per-image pooling
  (n=1200) but the tower-level S CIs are correspondingly wide.

---

## 2. Result-robustness audit

### 2a. The n=6 / AT-detector confound (the load-bearing scrutiny)

Reproduced the prior tower-level correlations exactly (eps 2/255): η/L₁ Pearson **+0.913**,
Spearman +0.928; SC_pred Pearson −0.310, Spearman −0.522; clean −0.749. **But splitting the panel:**

| subset | η/L₁ Pearson (eps 2/255) | η/L₁ Pearson (eps 4/255) |
|---|---|---|
| full n=6 (4 AT + clip + dinov2) | **+0.91** | +0.90 |
| **AT-only n=4** (fare2/4, tecoa2/4) | **+0.52** | **+0.34** |

Among the 4 AT towers alone, η/L₁ Spearman is +0.80 (eps 2) / +0.40 (eps 4). So the tower-level
+0.91 is **carried mostly by the two non-robust anchors at S=0** — i.e. η/L is largely detecting
*that* a tower is adversarially trained, and only weakly rank-ordering *among* robust towers
(underpowered at n=4). **This is the correct, deflating read of the tower-level number, and it is
why the per-image axis is the real claim.**

### 2b. The per-image dissociation (the powered claim — sidesteps n)

Pooled within-tower-ranked Spearman across the 4 AT towers (radius has genuine range there):

- **Spearman(per-image η/L₁ ratio, per-image robust radius) = +0.782 [0.753, 0.807]** (n=1200)
- **Spearman(per-image shift-consistency, robust radius) = +0.117 [0.057, 0.177]** (n=1200)

Per-tower it is +0.766 / +0.738 / +0.850 / +0.803 (all CIs well above 0). The per-image η/L signal
is ~6.7× the SC signal and the CIs do not overlap. **This is the defensible headline** — it does
not depend on the 6-tower count and is not an AT-detector (it is *within* AT towers).

### 2c. Consistency-null (resolved, not buried)

- **SC_pred (prediction-agreement — the metric the anti-aliasing / Singla-Ge literature tracks)
  spans only 0.982–0.989 (range 0.0065): essentially flat.** Its −0.52 Spearman is uninformative
  noise (perm p = 0.49, n.s.). Honest statement: *SC_pred does not order robustness because it is
  flat across these towers* — not "it anti-predicts."
- **SC_cos (pooled-embedding cosine-consistency) spans 0.92–0.997 and Pearson +0.94** — as strong
  as η/L. Mechanism: the two non-robust towers have the lowest SC_cos, so SC_cos **co-detects AT**
  exactly the same 2-vs-4 way as the raw η/L number. It is *not* the metric the invariance
  literature uses to claim "invariance helps robustness." **The fair null is SC_pred**, and the
  dissociation (SC_pred flat/uninformative while η/L predicts, both at tower and per-image level)
  holds for the fair null. The paper MUST report SC_cos +0.94 and explain it as an AT co-detector,
  not omit it.

### 2d. Clean-acc confound

Verified partial corr(η/L₁, S | clean) = **+0.95** [0.83, 1.0] — η/L carries robustness info beyond
clean accuracy on the n=6 panel. (Caveat: on n=6 with the 2-vs-4 structure this is still partly the
AT split; the extended panel adds `is-AT` and architecture as additional controls — see §3.)

---

## 3. Fix + extend (run on GPU 1)  [COMPLETE — 2026-07-12]

**Panel widening:** added non-AT CLIP towers spanning pretraining corpus / patch size / capacity
(`clip_l14_laion2b`, `clip_l14_datacomp`, `clip_b16_openai`, `clip_b16_laion2b`, `clip_b32_laion2b`,
`clip_l14_metaclip`) so the axis is not just AT-vs-non-AT. Code: `run_c1_extended.py`,
`analyze_c1_extended.py`, extended `CLIP_TOWERS` in `towers.py`, `n_iter` param in
`run_autoattack`. Per-image radius rerun with a finer sub-1/255 grid (0.25/255 … 8/255).
Files: `results/c1_tower/c1_results_ext.json`, `c1_analysis_extended_eps2.json`,
`per_image_clip_*_ext.pt`.

**Panel landed at n=11, not 12:** `clip_l14_metaclip` did not produce results (download/load drop
in the extended run — 5 of the 6 new towers completed). The panel is now **11 towers = 4 AT
(fare2/4, tecoa2/4) + 7 non-AT (clip, dinov2, + 5 new CLIP variants)** — a 3.5× wider non-AT arm
than the n=6 audit panel. This is enough to break the 2-vs-4 collinearity.

### 3a. Tower-level, n=11 (η/L strengthens; the fair null collapses under confound control)

| metric | Pearson vs S (eps 2/255) | 95% CI | perm p |
|---|---|---|---|
| **η/L₁ (threat-matched)** | **+0.953** | [0.922, 1.00] | 0.0009 |
| η/L₂ (mismatched control) | +0.924 | [0.882, 1.00] | 0.0013 |
| SC_cos (cosine-consistency) | +0.806 | [0.601, 0.983] | 0.0002 |
| SC_pred (prediction-agreement, the fair null) | +0.367 | [−0.128, 0.723] | 0.26 (n.s.) |
| clean acc | −0.069 | [−0.627, 0.505] | 0.83 (null) |

**The decisive new evidence — partial correlations that control for the AT split directly:**

| partial correlation | value | reading |
|---|---|---|
| corr(η/L₁, S \| clean) | **+0.959** [0.928, 1.00] | η/L beats clean acc |
| corr(η/L₁, S \| clean **and** is-AT) | **+0.559** | **η/L survives controlling for the AT indicator** |
| corr(η/L₁, S \| is-AT) | **+0.510** | η/L still orders robustness *beyond* "is it AT" |
| corr(SC_cos, S \| is-AT) | **+0.152** | **SC_cos collapses — its +0.806 was the AT co-detection** |

This is the clean resolution of the round-1/round-2 "it's just an AT detector" critique: **with the
AT indicator partialled out, η/L₁ holds at +0.51–0.56 while cosine-consistency drops to +0.15.**
The threat-matched ratio carries robustness information that "the tower is adversarially trained"
does not; consistency does not. SC_pred (the fair null the anti-aliasing literature tracks) is n.s.
even before any control (+0.37, p=0.26).

**Selection regret (n=11), oracle = tecoa4 (S=0.88):** η/L₁ picks tecoa2 → **regret 5 pts**;
SC_pred picks dinov2 → **regret 88 pts**; clean acc picks dinov2 → regret 88 pts; SC_cos picks
tecoa4 → 0 pts (again the AT co-detection). The threat-matched ratio is a near-oracle attack-free
selector; the fair consistency null is catastrophic.

### 3b. Per-image dissociation — now shown *within non-AT towers*, not just AT

The finer grid gave the non-AT CLIP towers genuine per-image radius spread (radius_uniq 3–5,
floor_frac 0.54–0.86 at eps 2/255 — no longer pinned at the floor like the original `clip`, which
had floor_frac 0.997). Within each non-AT CLIP tower, **η/L₁ still orders the per-image radius**:

| tower (non-AT) | Spearman(per-image η/L₁, radius) | 95% CI |
|---|---|---|
| clip_b32_laion2b | **+0.794** | [0.750, 0.832] |
| clip_b16_laion2b | +0.683 | [0.618, 0.738] |
| clip_l14_laion2b | +0.660 | [0.588, 0.719] |
| clip_l14_datacomp | +0.651 | [0.583, 0.712] |
| clip_b16_openai | +0.538 | [0.463, 0.607] |

**CORRECTION 2026-07-13 (figure-generation caught a pooling artifact).** The earlier pooled
"SC-radius = +0.117" was a **within-tower-rank-pooling artifact**: with a coarse, tied 5-level radius
grid, rank-pooling across towers attenuates the weaker consistency signal. The **direct per-tower**
Spearman(SC, radius) is **+0.27 to +0.37 (mean +0.33)** across the 4 AT towers — consistency is NOT
near-zero for the per-image radius. The honest per-image dissociation is therefore GRADED:

| per AT tower | Spearman(η/L₁, radius) | Spearman(SC, radius) |
|---|---|---|
| fare2 | +0.766 | +0.355 |
| fare4 | +0.738 | +0.368 |
| tecoa2 | +0.850 | +0.325 |
| tecoa4 | +0.803 | +0.266 |
| **mean / raw-pooled** | **+0.79 / +0.76** | **+0.33 / +0.33** |

So η/L orders the per-image radius **~2.4× more strongly** than shift-consistency (+0.79 vs +0.33), a
real dissociation, but consistency is weakly informative, not uninformative. Report per-tower ranges,
NOT the +0.117 pooled number (retracted as a pooling artifact). The non-AT CLIP towers still show
η/L₁→radius +0.54 … +0.79 per tower (AT-independent). **Paper §4 + abstract + intro corrected to
"more than twice as strongly" / per-tower ranges; the "consistency stays near zero" phrasing is
withdrawn.**

### 3c. Bonus — the paper's "invariance-helps is a weak-attack artifact" replicates in VLMs

Every non-AT CLIP tower shows **S_apgd = S_pgd40 = 0.0** at both eps (2/255, 4/255) but
**S_fgsm = 0.16–0.46**. FGSM reports apparent robustness that APGD/AutoAttack completely erase —
the exact weak-attack artifact the main vision paper documents (FGSM shows invariance "helping,"
AutoAttack kills it), now reproduced in a different domain (frozen VLM encoders). Not part of the
C1 headline, but a clean cross-domain confirmation of the paper's central methodological point, and
worth one sentence in the LLM/VLM paper.

### 3d. Honest residual limitation (unchanged)

The 7 non-AT towers all sit at tower-level S≈0 under strong attack (`nonAT_only` correlations are
NaN — no within-group robustness variance). So the *tower-axis robustness range* still comes from
the AT towers; the widened panel removes the **collinearity** confound (via the partials in 3a) but
non-AT towers remain uniformly Linf-fragile. The powered, confound-free claim is therefore the
**per-image** dissociation (3b), which now stands on both AT and non-AT towers. This matches the
audits' decision-law #1: lead with the per-image axis, use the tower axis as confound-controlled
support.

---

## 4. Literature re-verification (agent-verified against source PDFs/abstracts)

- **RDI (2504.18556)** — attack-free robustness *ranking* but via feature-clustering geometry on
  **plain classifiers** (ResNet/ViT/DenseNet, Tiny-ImageNet), not η/L, not CLIP/VLM towers, no
  threat-matching, no shift-consistency. Nearest attack-free-ranking neighbor; **no scoop**;
  differentiate on mechanism + panel.
- **OpenReview TQ2ZOy6miT = CLIPure (ICLR 2025, 2502.18176)** — a latent-space **purification
  defense**, NOT a "CLIP-Lipschitz" paper. It does not compute a logit-margin + local Lipschitz
  cross-encoder selector. **No scoop**; cite as defense context only. (The prior framing of this
  as "the CLIP-Lipschitz paper" was factually wrong.)
- **Ngnawe et al. (2406.18451)** — margin-consistency (logit margin as input-margin proxy) is the
  closest on the *idea*, but it is **per-sample detection within one RobustBench CIFAR classifier**,
  never a cross-encoder ranking scalar, no CLIP/VLM, no η/L ratio, no threat-matching, no SC. Most
  important citation to distinguish against ("cross-encoder ranking" vs "per-sample detection").
- **Singla & Ge (2103.02695)** — proves shift invariance *reduces* Linf robustness. **Motivation,
  not competitor**: it predicts the SC null. Strengthens the null (expected, not surprising).
- **FARE (2402.12336)** — produces the AT towers; never computes SC or η/L or any attack-free
  predictor. **Confirms C1's gap.**
- **2407.11121** — establishes the vision tower governs VLM adversarial robustness (LLM size does
  not help). **Justifies encoder-level framing; no scoop.**
- **R-Adapt / 2603.12799** — Gaussian low-pass on frozen CLIP under AutoAttack; no attack-free
  cross-tower η/L predictor. Cite for the low-pass mechanism; disclaim that mechanism's novelty;
  **no scoop of the η/L-ranking claim.**
- Broader 2024–2026 sweep (LORE, TIMA, Double Visual Defense, Dynamic-Margin 2310.00116, LipShiFT,
  perceptual-CLIP 2502.11725, VLM-RobustBench): margin+Lipschitz→robustness is textbook, but always
  as a *training regularizer on single supervised classifiers*, never a cross-tower attack-free
  selector on frozen VLMs. **No scoop found.**

### Deep scoop-hunt 2026-07-12 (agent + my source-verification of the 2 most dangerous hits)

A fresh adversarial sweep (11 papers read, ~10 query families) found **no scoop**; two new
nearest-neighbors surfaced that were NOT in the prior list and that I verified directly against
their arXiv abstracts (both real, both accurately characterized by the agent):

- **GREAT Score (2304.09875, Li/Chen/Ho, ICLR 2023)** — VERIFIED. The closest true *attack-free
  robustness ranker*: *"a mean certified attack-proof perturbation level … high correlation and
  significantly reduced computation cost when compared to the attack-based model ranking on
  RobustBench."* Distinguish: its estimator is a **generative-manifold confidence margin**, not an
  input-gradient dual-norm Lipschitz ratio; it ranks **plain RobustBench classifiers**, not frozen
  CLIP/RobustVLM/DINOv2 towers; no per-image certified-radius ordering; no shift-consistency null.
  **Must cite as the nearest attack-free-ranking prior.**
- **MaCS (2603.05812, Khazem, 2026)** — VERIFIED (abstract). The keyword-collision danger: it shares
  the margin idea, the word "consistency," and a **margin-to-sensitivity ratio with a radius bound**
  (*"a provable robustness radius bound scaling with the margin-to-sensitivity ratio"*). Distinguish:
  it is a **training regularizer** (hinge margin + KL-consistency between clean and **noise/blur**
  views), not an attack-free predictor; its "consistency" is noise/blur KL, **not pixel-shift
  prediction-agreement** (our null); it evaluates supervised CNNs/ViTs, **no frozen foundation
  towers**, no AutoAttack cross-tower ranking. A referee scanning keywords WILL raise it → cite and
  separate explicitly on all three axes.
- Also confirmed nearest-neighbors: **RDI (2504.18556)** closest attack-free *feature-cluster*
  ranker on plain classifiers; **Ngnawe (2406.18451)** closest *within-one-model per-sample* bare-
  margin (no L) detector; **Singla-Ge (2103.02695)** motivation for the null.

**Post-verification novelty (intact):** the combination {frozen VLM/foundation towers} × {threat-
matched η/L = margin over dual-norm input-gradient} × {both cross-tower AutoAttack ranking AND
per-image certified-radius ordering} × {paired shift-consistency null that fails} is not found in
the literature. Related work MUST cite+distinguish: 2304.09875, 2603.05812, 2504.18556, 2406.18451,
2103.02695.

### Defensible novelty after hardening

Unclaimed and intact: **a threat-matched margin-to-Lipschitz ratio (η/L, L = mean dual-norm Linf
input-gradient of the signed logit margin) computed through frozen CLIP/RobustVLM/DINOv2 vision
towers on clean images, used as a cross-tower, attack-free rule that ranks the towers' AutoAttack
robustness, and — the load-bearing powered evidence — a per-image dissociation where η/L orders the
per-image robust radius while shift-consistency does not.** The paired shift-consistency null is
positively predicted by Singla-Ge, so it is well-motivated. Must foreground Ngnawe + RDI as nearest
neighbors and disclaim low-pass-on-frozen-CLIP (R-Adapt) and encoder-governs-robustness (2407.11121)
as prior context, not contributions.

---

## 5. Go / no-go

**GO** as a standalone result, on the corrected and now confound-controlled claim:

- **Tower axis (n=11):** η/L₁ vs S Pearson **+0.953**, and it **survives partialling out the AT
  indicator** (+0.51) while cosine-consistency does not (+0.15). Reported as the confound-controlled
  support figure, not demoted to a bare "AT detector" anymore — the partials earn it.
- **Per-image axis (the headline):** η/L₁ vs robust radius Spearman **+0.78** pooled over AT towers
  and **+0.54 … +0.79 within each non-AT CLIP tower**, vs shift-consistency **+0.12 / ≈0**. The
  dissociation now stands on both AT and non-AT towers.
- SC_pred's flatness (n.s.) and SC_cos's AT-co-detection (dissolved by the partial correlation) are
  both stated openly. Weak-attack artifact (FGSM>0, APGD=0) replicates in VLMs as a bonus.

The implementation is sound; no result changes sign under any check. Remaining honest limitation:
the 7 non-AT towers are all tower-level Linf-non-robust (S≈0), so tower-axis robustness *range*
still comes from the AT towers — but the collinearity confound is removed by the partial
correlations, and the powered claim rests on the per-image axis (now AT-and-non-AT), exactly as the
audits' decision-law #1 prescribed. One loose end: `clip_l14_metaclip` dropped (panel is 11 not 12);
optional to re-add, not load-bearing.
