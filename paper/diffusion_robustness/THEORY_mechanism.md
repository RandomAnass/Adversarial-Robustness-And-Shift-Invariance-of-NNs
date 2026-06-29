# Why does diffusion data buy SMOOTHNESS, not margin? — candidate theoretical mechanisms

**Scope.** This is a theory-scoping note for the pilot finding "diffusion data buys smoothness, not
margin." It gives the author a *ranked* set of candidate explanations for **why adding diffusion/EDM
synthetic training data lowers the local input-gradient norm / Lipschitz `L` of an adversarially-trained
network even as the logit margin `M` shrinks**. Each candidate has: the mechanism, firsthand literature
(arXiv ID + quote, read 2026-06-29 via ar5iv/arXiv), and a *distinguishing* testable prediction runnable
with the team's existing `etaL_decomposition` / `robust_radius_l2` / consistency tooling. The author
proves/tests; this note only proposes grounded paths and flags what is unverified.

**Status of the literature on this exact question.** Open. A novelty search (2026-06-29) found no paper
that decomposes the synthetic-data robustness gain into margin vs. local-Lipschitz factors. Wang 2023
(`2302.04638`), Gowal 2021 (`2110.09468`), and Rice 2020 (`2002.11569`) — the three papers whose
mechanism claims are most load-bearing here — **contain no measurement of margin, input-gradient norm,
Lipschitz, smoothness, or input-space flatness** (verified firsthand below). So the smoothness-vs-margin
split is genuinely the team's open lane; the candidates below are explanations to *test*, not settled.

---

## 0. The numbers to explain (1-seed pilot, PreActResNet-18, CIFAR-10, Linf PGD-AT, 40 ep, fixed budget)

From `results/partial/stage1_syn{0,1000000}_s0_e40.json` (real:synth = 30:70, only the synthetic-pool
size changes; identical epochs/steps/optimizer):

| metric | +0 real-only | +1M EDM | change | meaning |
|---|---|---|---|---|
| AutoAttack (Linf 8/255) | 0.354 | 0.475 | **+12.1 pt** | ground-truth robust acc |
| PGD-40 (Linf 8/255) | 0.365 | 0.508 | +14.3 pt | `AA ≤ PGD` holds (no masking) |
| clean acc | 0.781 | 0.843 | +6.2 pt | also improves |
| DDN L2 radius `r` | 0.781 | 0.868 | **+11%** | certified-radius ground truth |
| margin `M = f_y − max_other` | 4.455 | 2.573 | **−42%** | numerator, logit units |
| `L2 = ‖∇_x M‖₂` (DDN-matched) | 5.107 | 2.513 | **−51%** | denominator, L2-dual |
| `L1 = ‖∇_x M‖₁` (AA/Linf-matched) | 128.77 | 59.81 | **−54%** | denominator, Linf-dual |
| `η/L₂ = M / L2` (radius proxy) | 0.872 | 1.024 | **+17%** | the scale-invariant radius driver |
| shift-consistency | 0.707 | 0.831 | **+0.124** | model also gets more shift-invariant |

**The decomposition arithmetic (the headline, made exact).** With `r ≈ M / L`,
`Δ log r = Δ log M − Δ log L`. Here `Δ log M = log(2.573/4.455) = −0.55` and
`Δ log L₂ = log(2.513/5.107) = −0.71`. Net `Δ log(η/L) = −0.55 − (−0.71) = +0.16 = log(1.17)`, matching
the observed `η/L₂` move (+17%) and the actual DDN radius (+11%). So the margin term *subtracts* 0.55
from log-radius and the sensitivity term *adds* 0.71; the gain is the sensitivity term overwhelming the
margin loss. **Smoothness more than pays for the lost margin.** This is true in BOTH threat norms: `L1`
(the AA-Linf-matched Lipschitz) drops even harder (−54%) than the margin (−42%), so the radius rises
under the AA-matched norm too.

**A structural hint already in the data.** The gradient's *shape* barely changes:
`L1/L2 = 25.2` (+0) → `23.8` (+1M). A near-constant `L1/L2` ratio means the whole gradient vector
shrank roughly **uniformly in magnitude** rather than collapsing along a specific subspace. This is a
soft early discriminator (n=1 seed, 1000 points) that favors a *broad input-space smoothing* story
(Mechanisms A/B/C) over a *purely off-manifold-directional* story (Mechanism E), which would predict the
ratio to shift as off-manifold components are selectively suppressed. The rising shift-consistency
(0.707→0.831) — the function varies less under input transformations — points the same way.

---

## 1. Ranked candidate mechanisms

Ranking criterion: (i) explains BOTH radius-up AND margin-down, (ii) decisiveness of its distinguishing
test, (iii) grounding strength. Mechanisms A–C are the front-runners and partly nested (zeroth/first/
second-order views of the same "denser data → flatter function" idea); D–F are competitors with clean
falsifiers. Read all distinguishing tests together — several share measurements that triangulate.

### A — Adversarial training is implicit input-gradient regularization; synthetic data densifies the vicinity where that penalty is enforced ★ TOP

**Mechanism.** PGD-AT is, to first order, a penalty on the input-gradient norm: minimizing
`max_{‖δ‖≤ε} ℓ(x+δ)` ≈ minimizing `ℓ(x) + ε‖∇_x ℓ(x)‖_*` (dual norm). So AT already pushes `L` down — but
**only at the data points it sees**. Between sample points the function is unconstrained. Empirical risk
is a sum of deltas at the 50k real points; adding 1M EDM samples replaces those deltas with a *denser,
diversity-weighted* measure over the vicinity of the manifold (vicinal risk minimization, Chapelle et al.
2000; the augmentation-as-regularization view). The implicit gradient penalty is then interpolated over
many more anchor points, so the only way to keep all of them robust at fixed capacity is to make the
function *globally flatter* near the manifold → uniform drop in `L` (consistent with the near-constant
`L1/L2` and the rising shift-consistency). Lower confidence/margin is the expected side effect of a
stronger effective regularizer (see §2).

**Literature (firsthand).**
- Finlay & Oberman, *Scaleable input gradient regularization* — **`1905.11468`**: Prop. 3.1 — the
  adversarial value is "*bounded above by `min_w E_{x∼P}[ℓ(x;w) + (λ/2)‖∇_x ℓ(x)‖²_*]`*", i.e. AT ≈
  input-gradient regularization. "*input gradient regularization is competitive with adversarial
  training*." This is the formal bridge that makes `L` the quantity AT controls.
- Ross & Doshi-Velez — **`1711.09404`**: objective `argmin_θ H(y,ŷ) + λ‖∇_x H(y,ŷ)‖²₂`; "*By training a
  model to have smooth input gradients with fewer extreme values, it will … be more resistant to
  adversarial examples.*" Directly equates small input-gradient norm with smoothness + robustness.
- Hoffman, Roberts, Yaida, *Jacobian Regularization* — **`1908.02729`**: "*the larger the components of
  the Jacobian are, the more unstable the model prediction is with respect to input perturbations*";
  penalize `‖J(x)‖_F²`. The `L` the team measures *is* this input-output Jacobian/sensitivity norm.
- Supporting (search-surfaced, not fully fetched): "*Characterizing Model Robustness via Natural Input
  Gradients*" `2409.20139` and "*Data-Driven Lipschitz Continuity*" `2406.19622` both report
  gradient-norm/Lipschitz control reproducing much of AT's robustness — corroborating that `L`, not `M`,
  is the lever. (Cite as support only; verify before quoting.)

**Consistent with both observations?** Yes. Radius-up = `L` collapses (the regularized quantity).
Margin-down = a stronger effective regularizer trades confidence for smoothness (§2). The uniform
`L1/L2` shrinkage and shift-consistency rise are exactly the *global* flattening this predicts.

**Distinguishing prediction.** `L` should fall **monotonically with synthetic diversity at fixed
optimization budget** — i.e. a clean dose-response over the planned `{0, 100k, 500k, 1M}` sweep — and the
flattening should be *largest at points BETWEEN real samples* (interpolated / vicinity points), not only
at the training points. Concretely: measure `L` on (a) held-out real points, (b) synthetic points, (c)
convex interpolations `αx_i+(1−α)x_j` of real pairs and small off-sample jitters. Mechanism A predicts
`L` drops everywhere and **most** on the interpolation/vicinity points (that is the region the extra data
newly constrains). This separates A from B (which predicts the drop is tied to the *training epoch* axis,
not the data-amount axis) and from E (which predicts the drop concentrates in off-manifold directions).

### B — The smoothness is the ABSENCE of robust-overfitting (no late-training sharpening) ★

**Mechanism.** Robust overfitting (Rice 2020): after the first LR decay, robust *test* accuracy degrades
while robust *train* accuracy keeps rising — the model memorizes the adversarial training set. A natural
mechanism for that memorization is carving **sharp, high-curvature decision boundaries** (high `L`,
high input-Hessian) that fit train adversarial points but generalize badly. Wang 2023 reports EDM data
"*eliminates robust overfitting*." If memorization = input-space sharpening, then preventing it = keeping
`L` low. On this reading the "+1M smoothness" is not a new smoothing force but the *removal* of the
sharpening that the +0 model would otherwise acquire late in training.

**Literature (firsthand).**
- Rice, Wong, Kolter — **`2002.11569`**: "*overfitting to the training set does in fact harm robust
  performance to a very large degree*"; the degradation "*appears to be closely linked with the first
  drop in the scheduled learning rate decay.*" Crucially, the paper offers **no input-gradient /
  Lipschitz / sharpness characterization** of robust overfitting — so "RO = input-sharpening" is an
  open hypothesis, not an established fact.
- Wang et al. — **`2302.04638`** (abstract + §5.2): "*data generated by EDM eliminates robust overfitting
  and reduces the generalization gap between clean and robust accuracy*"; "*the generalization gap
  between train and test robust accuracy is nearly 60%*"; "*Generated data can help to close the
  generalization gap.*" No margin/Lipschitz/flatness measurement anywhere (verified).

**Consistent with both?** Radius-up: yes (no late sharpening → `L` stays low). Margin-down: yes —
memorization typically inflates *train* margins/confidence; suppressing it lowers the mean margin.

**Distinguishing prediction (an epoch-axis test, not a data-axis test).** Track `L` and the
**train−test robust-accuracy gap** *over the course of training* for +0 vs +1M. B predicts: in the +0
arm, `L` (and the robust gap) **climb in late epochs**; in the +1M arm they **stay flat**. If instead `L`
is already lower for +1M *early* (before any overfitting could occur, e.g. by epoch 10–15 when the +0 gap
is still ~0), then the effect is not RO-elimination and B is refuted in favor of A/C. Caveat for the
current pilot: 40 epochs may be too short for the +0 arm to have entered the RO regime, so this test
needs the per-epoch `L` curve, ideally to a longer horizon.

### C — Input-space CURVATURE reduction (second-order companion to A) 

**Mechanism.** The first-order view (A) says `‖∇_x M‖` falls; the second-order view says the input-space
**Hessian / curvature** falls, flattening the decision surface. Moosavi-Dezfooli et al. (CURE) show AT
itself reduces input curvature and that explicitly regularizing curvature reproduces most of AT's
robustness, with robust radius scaling inversely with the top Hessian eigenvalue. Diffusion data would be
pushing this same curvature down further. This is not a rival to A so much as the curvature reading of the
same flattening — but it has a *distinct, decisive measurement* (the input-Hessian spectrum) that the
gradient-norm `L` does not capture, so it earns its own slot.

**Literature (firsthand).**
- Moosavi-Dezfooli, Fawzi, Uesato, Frossard, *Robustness via Curvature Regularization* — **`1811.09716`**:
  "*adversarial training leads to a significant decrease in the curvature of the loss surface with
  respect to inputs*"; "*small curvature is beneficial to obtain classifiers with higher robustness*";
  the regularizer "*leads to adversarial robustness that is on par with adversarial training*"; Thm 1:
  robustness bounds "*decrease with increasing curvature ν*" where `ν = λ_max(H)`.

**Consistent with both?** Radius-up: yes (lower `λ_max(H_x)` → larger radius, CURE Thm 1, and a flatter
function naturally has smaller `‖∇M‖`). Margin-down: curvature reduction does not *predict* margin-down by
itself — that comes from A/§2 — so C is best read as the mechanistic *depth* behind A rather than a
standalone margin explanation.

**Distinguishing prediction.** The input-Hessian top eigenvalue(s) `λ_max(∇²_x M)` (or the loss-Hessian,
via a few Hutchinson/power-iteration steps on the clean-correct points the team already uses) should drop
with synthetic data, and the drop should **track the `L` drop across the `{0,100k,500k,1M}` sweep**. If
`L` falls but curvature does NOT (the surface stays bumpy at second order while the gradient magnitude
shrinks), then the effect is a pure first-order rescaling (points to §2 logit-scale) rather than genuine
geometric flattening — a clean separation of "real smoothing" from "shrunk logits."

### D — Weight-loss-landscape flatness (the smoothness lives in WEIGHT space, not input space)

**Mechanism.** A competing locus: maybe synthetic data finds a **flatter minimum in weight space**, which
AWP ties to a smaller robust generalization gap; the input-`L` drop would then be a downstream
correlate of weight-flatness rather than the primary effect. This matters because it changes the story
("diffusion data flattens the *optimization* landscape") and the prescription. Importantly, AWP **does
not** theoretically connect weight-flatness to input-gradient norm (verified), so D is a genuinely
distinct hypothesis, not a restatement of A.

**Literature (firsthand).**
- Wu, Xia, Wang, *Adversarial Weight Perturbation* — **`2004.05884`**: "*identify a clear correlation
  between the flatness of weight loss landscape and robust generalization gap*"; "*the robust
  generalization gap is bounded by … the flatness of weight loss landscape.*" But the paper does **not**
  link weight-space flatness to input-space smoothness/`L` — it treats input and weight perturbations as
  complementary, and notably finds AWP **outperforms** standard data augmentation, so "augmentation
  flattens weights" is not something AWP asserts.

**Consistent with both?** Radius-up: indirectly (via robust generalization), but D does not *mechanically*
produce a lower input-`L` — that link is exactly what is unproven. Margin-down: not predicted by D.

**Distinguishing prediction.** Measure **weight-space sharpness** (SAM-style `ρ`-sharpness: worst-case
loss increase under a small weight perturbation, or `λ_max` of the weight-Hessian) for +0 vs +1M, and
correlate it against input-`L`. D is supported only if weight-sharpness drops AND that drop *explains*
the input-`L` drop (e.g. they move together across the data sweep). If input-`L` falls while
weight-sharpness is unchanged, the smoothness is an input-space phenomenon (A/C) and D is refuted. This
is the cleanest "input space vs weight space" decider.

### E — Manifold coverage suppresses OFF-manifold gradients

**Mechanism.** Because data lives on a low-dimensional manifold inside a high-dimensional input space, the
dimension gap leaves many off-manifold directions in which the network's gradient is large and
*unconstrained by the training data* — the textbook source of adversarial directions. Synthetic data that
densely covers the *vicinity* of the manifold supplies constraints in (some of) those directions,
shrinking the off-manifold gradient components → lower `L`. On-manifold robustness then improves simply as
better generalization (Stutz), consistent with clean acc also rising.

**Literature (firsthand).**
- Stutz, Hein, Schiele, *Disentangling Adversarial Robustness and Generalization* — **`1812.00740`**
  (NOTE: the brief gave `1910.09338`, which is a different paper; correct ID is `1812.00740`, CVPR 2019):
  "*regular adversarial examples leave the manifold*"; "*on-manifold robustness is nothing different than
  generalization*"; "*better generalization, i.e., using more training images N, also reduces on-manifold
  success rate.*" The last quote is the direct "more data → manifold robustness" link.
- Haldar, Xing, Song, *Effect of Ambient-Intrinsic Dimension Gap on Adversarial Vulnerability* —
  **`2403.03967`**: off-manifold attacks are "*a natural consequence of the dimension gap between the
  intrinsic and ambient dimensions*"; weights carry off-manifold "*volatile biases … independent of x*"
  that "*can be exploited by off-manifold attacks*"; "*as the dimension gap increases … the model is
  more vulnerable.*"
- Melamed et al., *Adversarial Examples Exist in Two-Layer ReLU Networks for Low Dimensional Linear
  Subspaces* — **`2303.00783`** (NeurIPS 2023; the brief's "Melamed 2305.xxxx" — corrected; read from
  abstract/OpenReview, **not** full-text-fetched, flag): gradient methods yield "*large gradients in
  directions orthogonal to the data subspace*," and "*L₂ regularization … can make the trained network
  more robust to … perturbations orthogonal to the data*" — i.e. an off-manifold-gradient story.

**Consistent with both?** Radius-up: yes (off-manifold `L` shrinks). Margin-down: not directly predicted;
E is silent on margin, so it leans on §2.

**Distinguishing prediction.** Estimate the local tangent space (e.g. local PCA of nearest neighbors, or
the EDM/data covariance) at each clean-correct point and **split `∇_x M` into on-manifold vs off-manifold
energy**. E predicts the `L` reduction is **concentrated off-manifold** (the off-manifold fraction of
gradient energy drops sharply; on-manifold component little changed). This is the strongest test against
A: A predicts a roughly *uniform/isotropic* shrinkage (consistent with the near-constant `L1/L2` already
observed), whereas E predicts an *anisotropic* shrinkage that should *change* `L1/L2` and the on/off
split. The current constant-`L1/L2` hint is mild evidence against a pure-E story but n=1; the explicit
on/off decomposition is the decider.

### F — Randomized-smoothing-like averaging over near-duplicates (weakest)

**Mechanism.** If the synthetic pool contains many near-duplicates clustered around each real image,
training on them approximates training over a smoothed/noise-augmented vicinity — an implicit
Cohen-style randomized smoothing, whose smoothed classifier has bounded sensitivity. The catch: EDM
samples are *diverse novel images*, not Gaussian-noised copies of the train set, so the near-duplicate
premise is doubtful — which is why this ranks last. It is cheap to falsify, so worth a single check.

**Literature (firsthand).**
- Cohen, Rosenfeld, Kolter, *Randomized Smoothing* — **`1902.02918`**: smoothed `g(x) = argmax_c
  P(f(x+ε)=c)`, `ε∼N(0,σ²I)`, certified `R = (σ/2)(Φ⁻¹(p_A) − Φ⁻¹(p_B))`; trained "*with Gaussian data
  augmentation at variance σ²*." Robustness comes from *averaging over a noise vicinity* — the analogy
  only holds if synthetic data plays the role of that vicinity. (Cohen does not claim a Lipschitz bound on
  `g` itself, so this is an averaging argument, not a Lipschitz one.)

**Consistent with both?** Radius-up: yes if the near-duplicate premise holds. Margin-down: yes (averaging
over a vicinity softens the decision function, lowering confidence) — but contingent on the premise.

**Distinguishing prediction.** Measure, per real image, the distance to its nearest synthetic neighbors
(is the EDM pool actually clustered around real images, or space-filling?), and test whether the local
`L` drop **scales with local synthetic density**. If `L` drops just as much in regions with *no* nearby
synthetic samples, the smoothing/near-duplicate story (F) is refuted and the effect is the global
regularization of A. Strong prior: F fails this test.

---

## 2. The margin-shrink / logit-scale subtlety (cross-cutting; read before believing any "margin loss")

The margin `M = f_y − max_other` is in **logit units, which are not scale-invariant**: rescale the
network output `f → f/T` (a temperature) and `M → M/T`, `L = ‖∇_x M‖ → L/T`, so **`η/L = M/L` is exactly
invariant** while the *reported margin* shrinks by `T`. Three consequences:

1. **A confidence drop alone would lower the margin without changing the radius.** Diffusion/diverse data
   is known to lower confidence and improve calibration (Gowal `2110.09468`: diverse generated data helps;
   the mixup analogue Thulasidasan `1905.11001`: "*mixup-trained DNNs are … less prone to over-confident
   predictions*," soft targets prevent "*the largest pre-softmax logit from becoming much larger than the
   others*"). So a large chunk of the observed `−42%` margin is plausibly a **temperature/calibration
   effect, not a loss of class separation** — the model is simply less overconfident, exactly as a
   stronger effective regularizer (Mechanism A) predicts.

2. **But temperature CANNOT explain the radius gain.** Under pure rescaling `η/L` is invariant; the pilot
   shows `η/L₂` *rose* +17% (and the DDN radius +11%). So **on top of** a confidence drop there is a
   genuine, scale-invariant geometric improvement — `L` fell by *more* than any common temperature would
   shrink `M`. The headline survives the logit-scale objection: the radius gain is real and lives in the
   scale-invariant `η/L`, while the raw margin drop is partly an artifact of the units.

3. **Why `L` falls more than `M` (the crux).** If margin-down were *only* temperature, `M` and `L` would
   fall by the same factor and `η/L` would not move. They don't: `M ×0.58`, `L₂ ×0.49`. The extra `L`
   reduction beyond the `M` reduction is the "true smoothing" — Mechanisms A/C — sitting on top of a
   confidence rescale. The clean way to separate them is to measure margins **after** matching confidence.

**Tests that isolate scale from geometry.**
- **Temperature-calibrate both models** (fit `T` on a val split to minimize NLL/ECE), then recompute the
  margin. Prediction: the `−42%` margin gap **shrinks substantially** after calibration (it was largely
  confidence), while `η/L` and the DDN radius are **unchanged** (they are scale-invariant). If the
  calibrated margin gap *closes entirely*, the margin-down is purely a confidence artifact and the only
  real effect is smoothness — the strongest form of the headline.
- **Logit-norm-normalized margin:** report `M / ‖f‖` or `M / ‖W_last‖` (a scale-free margin). If the
  normalized margin is roughly *flat* across arms while `L` still drops, smoothness is confirmed as the
  sole scale-invariant driver.
- **Note for the write-up:** the pilot recipe uses plain CE PGD-AT with **no label smoothing** (unlike
  Wang's `ls=0.1`), so the margin shrink is **not** a label-smoothing artifact — it is data-induced. Worth
  stating explicitly to preempt that objection.

---

## 3. What to measure next, ordered by how decisively it pins the mechanism

1. **`L`-vs-synthetic-amount dose-response** over `{0, 100k, 500k, 1M}` at fixed budget (already planned
   Stage 2). Monotone `L` decrease with *diversity at fixed steps* is the core prediction of A and the
   single most informative curve. Plot `M`, `L1`, `L2`, `η/L`, and `r` on the same axis. (Separates a
   data-diversity effect from a pure step-count effect; A predicts a clean monotone `L` decline.)
2. **`L` at real vs synthetic vs interpolated/off-sample points** (one extra `etaL_decomposition` pass on
   three point sets). Where the function is smoother localizes the mechanism: everywhere-and-most-on-
   interpolations ⇒ A; off-manifold-only ⇒ E; near-synthetic-clusters-only ⇒ F.
3. **On-/off-manifold split of `∇_x M`** (local-PCA tangent projection). Isotropic shrink ⇒ A; off-manifold
   concentrated ⇒ E. Directly adjudicates the two leading geometric stories and tests the constant-`L1/L2`
   hint at n>1.
4. **Temperature-calibrated + logit-norm-normalized margins** (cheap; no training). Decides how much of
   the `−42%` margin is confidence vs. real separation loss, and confirms the radius gain is scale-
   invariant. Do this early — it reframes the entire "margin-down" claim.
5. **Per-epoch `L` and train−test robust-gap trajectories, +0 vs +1M** (log `L` every few epochs; extend a
   couple of runs past 40 ep). The decisive robust-overfitting (B) test: late-training `L` climb in +0 but
   not +1M ⇒ B; +1M already-lower-`L` early ⇒ A/C.
6. **Input-Hessian top eigenvalue(s)** `λ_max(∇²_x M)` via power iteration on the clean-correct set
   (CURE/C). Confirms genuine second-order flattening vs. first-order rescaling; should track the `L`
   drop across the sweep.
7. **Weight-space sharpness** (SAM `ρ`-sharpness or weight-Hessian `λ_max`), +0 vs +1M, correlated with
   input-`L` (D). Settles input-space vs weight-space locus of the smoothness.
8. **Nearest-synthetic-neighbor density vs local `L`** (F falsifier; cheap). Confirms/kills the
   randomized-smoothing/near-duplicate reading.
9. **`L1/L2` ratio across the full sweep with seeds + CIs.** Already hints at uniform shrinkage; promote
   from a 1-seed hint to a real discriminator between isotropic (A) and anisotropic (E) flattening.
10. **Multi-seed + a second backbone (WRN-28-10) confirmation** of the *direction* of every effect above.
    The decomposition direction is the deliverable; 1 seed/40 ep cannot anchor magnitudes.

**Predicted leaderboard before running (what the author should expect if A is right):** monotone `L`
collapse with diversity (1); smoothing largest on interpolation points (2); isotropic gradient shrink (3,
9); the margin gap mostly closing under calibration (4); +1M `L` already lower *before* any overfitting
onset (5); curvature down in lockstep with `L` (6); weight-sharpness either flat or only weakly coupled to
input-`L` (7); F falsified (8). Any single deviation re-ranks the list — e.g. an off-manifold-concentrated
gradient drop (3) would promote E above A.

---

## 4. Reference list (arXiv ID — one-line firsthand basis, read 2026-06-29)

- Wang et al. 2023, *Better Diffusion Models Further Improve AT* — **`2302.04638`**: "EDM … eliminates
  robust overfitting and reduces the generalization gap"; "low FID … leads to high … robust accuracy";
  ratio 0.3 real/0.7 gen. **No margin/Lipschitz/flatness measurement (verified).**
- Gowal et al. 2021, *Improving Robustness using Generated Data* — **`2110.09468`**: "even … random data
  (generated by Gaussian sampling) can improve robustness"; 50–90% real ratios all help. No margin/
  Lipschitz analysis (verified).
- Rice, Wong, Kolter 2020, *Overfitting in Adversarially Robust DL* — **`2002.11569`**: robust overfitting
  defined/linked to first LR-decay; **no** input-gradient/Lipschitz/sharpness characterization (verified).
- Finlay & Oberman 2019, *Scaleable input gradient regularization* — **`1905.11468`**: Prop. 3.1, AT ≈
  `(λ/2)‖∇_x ℓ‖²_*` regularization; "competitive with adversarial training."
- Ross & Doshi-Velez 2017, *Regularizing Input Gradients* — **`1711.09404`**: `λ‖∇_x H‖²₂`; "smooth input
  gradients … more resistant to adversarial examples."
- Hoffman, Roberts, Yaida 2019, *Jacobian Regularization* — **`1908.02729`**: penalize `‖J(x)‖_F²`; larger
  Jacobian ⇒ more unstable to input perturbations.
- Moosavi-Dezfooli et al. 2019, *CURE: Robustness via Curvature Regularization* — **`1811.09716`**: "AT …
  decrease[s] the curvature of the loss surface w.r.t. inputs"; "small curvature is beneficial"; Thm 1
  robustness ∝ 1/`λ_max(H)`.
- Wu, Xia, Wang 2020, *Adversarial Weight Perturbation (AWP)* — **`2004.05884`**: weight-loss flatness ↔
  robust generalization gap; **does not** bridge weight-flatness to input-`L` (verified — this is why D is
  a distinct hypothesis).
- Stutz, Hein, Schiele 2019, *Disentangling Adversarial Robustness and Generalization* — **`1812.00740`**
  (brief's `1910.09338` is the wrong ID): "regular adversarial examples leave the manifold"; "on-manifold
  robustness is nothing different than generalization"; "more training images N … reduces on-manifold
  success rate."
- Haldar, Xing, Song 2024, *Ambient-Intrinsic Dimension Gap & Adversarial Vulnerability* —
  **`2403.03967`**: off-manifold attacks from the dimension gap; off-manifold "volatile biases" exploited.
- Melamed et al. 2023, *Adversarial Examples Exist in Two-Layer ReLU Nets for Low-Dim Linear Subspaces* —
  **`2303.00783`** (NeurIPS 2023; brief's "2305.xxxx" corrected; **abstract/OpenReview only, not
  full-text fetched** — flag before quoting): "large gradients in directions orthogonal to the data
  subspace"; L₂ reg improves off-manifold robustness.
- Cohen, Rosenfeld, Kolter 2019, *Randomized Smoothing* — **`1902.02918`**: `g(x)=argmax_c P(f(x+ε)=c)`;
  `R=(σ/2)(Φ⁻¹(p_A)−Φ⁻¹(p_B))`; Gaussian-augmentation training.
- Thulasidasan et al. 2019, *On Mixup Training: Improved Calibration* — **`1905.11001`**: mixup ⇒ "less
  prone to over-confident predictions"; soft targets prevent the top logit dominating (margin-shrink
  analogue).
- Tsuzuku, Sato, Sugiyama 2018, *Lipschitz-Margin Training* — **`1802.04034`**: guarded-area result
  `M ≥ √2·L·‖ε‖₂ ⇒ r ≥ M/(√2·L)`; margin = logit difference `F(x)_t − max_{i≠t} F(x)_i`. (The ar5iv
  render garbled the constant to "2"; the paper's factor is √2 from the Lipschitz of the margin operator —
  verify the exact constant against the PDF before citing.)
- Supporting, search-surfaced only (verify before quoting): *Characterizing Model Robustness via Natural
  Input Gradients* `2409.20139`; *Data-Driven Lipschitz Continuity* `2406.19622`; *Smoothness Analysis of
  Adversarial Training* `2103.01400`.

**Closest preemption (from the team's own landscape note, `landscape_gap.md`):** Huang, Chen & Lin 2026,
*Expanding the Role of Diffusion Models for Robust Classifier Training* — `2602.19931` — does mechanism
analysis of the diffusion-data gain via **representation geometry** (low-rank features, alignment/
uniformity, frequency-saliency of input gradients), **not** the margin/local-Lipschitz/certified-radius
split. It mentions "frequency-saliency of input gradients," which is adjacent to `L`; differentiate
carefully (their measure is a spectral saliency map of the gradient, not its dual-norm magnitude `L`).
This paper was not re-fetched here; verify its exact gradient measure before claiming distinctness.

---

## 5. Caveats / what is NOT verified

- **1 seed, 40 epochs, one backbone.** Every magnitude is provisional; only the *direction* (radius-up,
  margin-down, `L`-down-more) is the deliverable. The `L1/L2`-constant and shift-consistency hints are
  single-seed and should be treated as hypotheses, not evidence, until §3 items 9–10.
- **ID corrections made:** Stutz = `1812.00740` (not `1910.09338`); Melamed off-manifold = `2303.00783`
  (not `2305.xxxx`). The Tsuzuku constant should be `√2` — the auto-render returned an ambiguous "2";
  confirm against the PDF.
- **Not full-text-fetched (cite with care):** Melamed `2303.00783` (abstract/OpenReview only); Huang
  `2602.19931` (from the team's prior note); the three "supporting" search-surfaced IDs in §4.
- **Mechanisms A, B, C are partly nested**, not mutually exclusive — they are the zeroth/first/second-order
  readings of "denser data → flatter function near the manifold." The experiments in §3 are designed to
  apportion the effect among them and to separate that family from the genuine rivals D (weight-space) and
  E (off-manifold-directional), with F as the cheap falsifiable long-shot.
</content>
</invoke>
