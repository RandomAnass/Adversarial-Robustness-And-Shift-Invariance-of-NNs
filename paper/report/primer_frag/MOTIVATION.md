# Motivation: where the research questions actually come from

This file is the motivation front-matter for the primer. The primer currently teaches the
concepts (robustness, Lipschitz certificates, margins, implicit bias, NTK) beautifully but then
states the research questions "from the sky." This document builds the real chain that produced
those questions, so an undergraduate can see *why* the project asks what it asks. Every claim is
tagged with the file it came from.

The chain in one breath: a TUM practical course reproduced and extended a NeurIPS paper, found
that the paper's clean "more shift-invariance -> less robustness" story broke in places it could
not explain and built a quadrant diagnostic it could not justify -> the supervisor named four base
papers that, read together, openly *contradict each other* on whether invariance helps or hurts
robustness -> the wider literature confirms the contradiction is real and, crucially, that **no
result ties translation-invariance to an Lp robust radius** -> therefore the project's questions are
exactly the ones needed to resolve the contradiction with one measurable quantity.

---

## Part 0 — Sources actually read for this document

Old project (the practical course this grew from):
- `Report_2C.pdf` (9 pp, Aug 2023) — the practical-course **extension report**, read end to end.
- `README.md` — old-project description, reproduction + extension phases, GSIAR figures.
- `paper original code/README.md` — confirms `paper original code/` is *Ge et al.'s own* released
  code (toy/, 5_1_1..5_1_5, 5_2), not the students' work.
- `functions/extension_models.py`, `functions/Extension_utils.py` — the extension's model zoo
  (`simple_FC`, `simple_Conv` with circular padding, kernel/pooling/depth/dense knobs) and plotting.
- `scripts/` listing (e.g. `pooling_and_layers*.py`, `best_model_mnist.py`, `consistency_and_training_data.py`)
  — what the extension actually swept.

Base papers (the supervisor's four, plus the anti-aliasing foil):
- `literature/comparison_4papers/ge2021_shift_invariance_reduces_robustness.pdf` — Ge et al.,
  NeurIPS 2021 (the base result).
- `literature/comparison_4papers/kamath2020_invariance_vs_robustness_openreview.pdf` — Kamath et al.,
  ICLR 2020 (empirical trade-off).
- `literature/comparison_4papers/kamath2021_can_we_have_it_all_spatial_vs_adv.pdf` — Kamath et al.,
  NeurIPS 2021 (trade-off proved + CuSP).
- `literature/comparison_4papers/galloway2019_batchnorm_cause_adv_vulnerability.pdf` — Galloway et al.,
  ICML 2019 wksp (BN as a robustness cause).
- `literature/foundational/zhang2019_making_convnets_shift_invariant_again.pdf` — Zhang 2019
  (BlurPool/anti-aliasing; the "invariance helps" foil).

Wider literature (the gaps):
- `literature/round2_gapcheck/tramer2020_fundamental_tradeoffs_invariance_sensitivity.pdf`
- `literature/post2023_citing/frei2023_double_edged_sword_implicit_bias.pdf`
- `literature/round2_gapcheck/li2024_feature_averaging_implicit_bias_nonrobust.pdf`
- `literature/round2_gapcheck/can_implicit_bias_imply_adversarial_robustness_2024.pdf` (Min & Vidal)
- `literature/round2_gapcheck/bridging_symmetry_robustness_equivariance_2025.pdf`
- `literature/post2023_citing/rajput2024_translation_invariant_polyphase_shift.pdf`
  (**actually** Saha & Gokhale, TIPS, WACV 2024 — slug is wrong)
- `literature/implicit_bias_equivariance/chenzhu2023_implicit_bias_equivariant_steerable.pdf`
- `literature/implicit_bias_equivariance/lawrence2021_implicit_bias_linear_equivariant.pdf`

Project synthesis docs (cross-checked against, not the primary evidence):
- `literature/INDEX.md`, `literature/RELATED_WORK_COMPARISON.md`, `DOCUMENTATION.md`,
  `2pagers/Shift_Invariance_Robustness_Project_Summary_Anass_Al_Ammiri.tex`.

---

## Part 1 — The old project and the seeds it left unresolved

The project began as a TUM practical course, *Analysis of new phenomena in machine/deep learning*,
under the Theoretical Foundations of AI chair (`README.md`; `Report_2C.pdf` p.1). It had two phases.

**Reproduction.** The students re-implemented Ge et al. 2021 ("Shift Invariance Can Reduce
Adversarial Robustness"). The released code in `paper original code/` is Ge et al.'s own
(`paper original code/README.md`); the students' reproduction lives in the notebooks and in
`paper refactored code/`. The reproduction recovered Ge's headline ordering: across their MNIST and
Fashion-MNIST model families, **higher shift-consistency went with lower adversarial robustness**
(`Report_2C.pdf` p.1-2: "The paper's hypothesis of higher consistency scores indicating lower
invariance held true in most cases").

**Extension.** Building on the reproduction, the students swept *standard architecture knobs*
on `simple_Conv`/`simple_FC` models (`functions/extension_models.py`): model **depth**
(number of conv layers), **pooling** (max vs average, and global vs `2x2`), **kernel size**
(3 vs 10, later 6 sizes), and **adding a dense layer** before the output. They attacked with
PGD `L2` and `Linf` at varied epsilon (100 iterations, via ART) and measured shift-consistency on
each model (`Report_2C.pdf` p.2-3; `scripts/pooling_and_layers*.py`). The extension findings
(`Report_2C.pdf` p.3-5):
- **Depth** generally *increased* adversarial robustness, for both datasets, and did so *without*
  necessarily reducing shift-invariance — "adding more layers doesn't necessarily mean being less
  shift invariant."
- **Pooling**: max pooling helped robustness for single-layer models; average pooling was better for
  multi-layer models. Pooling did not much affect shift-consistency.
- **Kernel size**: smaller kernels generally gave better robustness *and* higher shift-invariance,
  but "the relationship is more nuanced" and "not always true." Very large kernels make the conv
  model behave like an FC model.
- **Dense layer**: adding one often improved robustness "without significantly impacting shift
  invariance" (but a large dense layer pushes the model toward FC behavior).
- **Noteworthy models**: several CNNs reached robustness "comparable to or even surpassing FC
  models" while keeping decent consistency (`Report_2C.pdf` p.5).

**What it hinted at but could not resolve — the seeds of the new questions:**

1. **The clean monotone story broke, and the report could not say why.** Even in reproduction, the
   *observed* robustness ordering "deviates slightly from the hypothetical order," with specific
   models (`simple_Conv_max`, `simple_Conv_2`) showing "unexpected behaviors in both datasets"
   (`Report_2C.pdf` p.1-2). The report could only note the deviation. *Seed:* consistency is not
   the right axis; some other quantity orders robustness — but the report had no candidate.

2. **A quadrant diagnostic with no theory behind it.** To pick models that are both robust *and*
   shift-invariant, the students invented **GSIAR** (Graph Shift-Invariance-Adversarial-Robustness):
   plot every model with shift-consistency on one axis and robust accuracy on the other, divide into
   four zones using the FC model as the reference point, and target the top-right "Goal Zone"
   (`Report_2C.pdf` p.5-6, Fig. 10). They proposed a *select-then-adversarially-train* recipe: pick
   a Goal-Zone model on a small dataset, then fully train and adversarially train it
   (`Report_2C.pdf` p.6-7, Fig. 11). *Seed:* GSIAR is a screening heuristic with no principle saying
   *why* a model lands where it lands, or whether the zones survive a stronger attack or scale.

3. **An explicit "no theory yet" hole.** The report's appendix literally reads "B Theorems and
   Proofs [TO DO]" (`Report_2C.pdf` p.7). The whole analysis is empirical, on small images, with
   PGD only — no certificate, no AutoAttack, no margin measurement. *Seed:* the project needs a
   *theory* that explains the deviations and a *standardized strong attack* to trust the numbers.

4. **Other architectures left on the table.** They discussed but dropped RNNs/Transformers and
   attack transferability, choosing to focus on "robustness parameters" (`Report_2C.pdf` p.1).
   *Seed:* the design space is large; a controlled, capacity-matched dissection is the missing rigor.

So the old project ended with a working but unexplained empirical picture and a diagnostic it could
not justify. The natural next questions: *what quantity actually orders robustness (if not
consistency)? why? and does it hold under a strong attack and matched capacity?*

---

## Part 2 — What the base papers actually claim (the four the supervisor named, plus the foil)

The supervisor's framing asked the project to compare its findings against four papers
(`2pagers/...tex` Sec. 7; `RELATED_WORK_COMPARISON.md` header). Read precisely, they do not agree.

**Ge et al. 2021 — invariance can *reduce* robustness (the base result).**
A shift-invariant *linear* classifier must put all circular shifts of a signal in one class, which
forces its margin to depend **only on the DC (mean) component** of the signals; all non-DC structure
is discarded (Ge Thm 1: linearly separable iff the DC components separate, and the max margin equals
the DC gap, with normal `(1/sqrt(d)) 1_d`). For the black/white dot example the unconstrained max
margin is **2** but the shift-invariant max margin is **2/sqrt(d)** (Ge Cor. 1) — robustness decays
as `1/sqrt(d)` in image size. The same collapse shows up in the infinite-width kernels: CNTK-with-GAP
inherits the DC-only `2/sqrt(d)` margin while the FC-NTK keeps a constant margin (Ge Thm 2, Cor. 2).
**But Ge's own crucial nuance** (Ge §5.2, Table 3): on an *orthogonal-frequencies* dataset where
shifts do *not* raise the effective dimension, the **CNN is more robust than the FC net**
(e.g. n=50: FC 0.129 vs CNN 0.272; n=200: FC 0.103 vs CNN 0.326). Ge conclude that invariance hurts
**only when it increases effective dimension and thereby shrinks the margin**, and state outright that
"the linear margin predicts robustness better than the dimension of the data" (Ge Table 4 discussion).
*This nuance is the hinge of the whole project: Ge themselves point at margin, not consistency.*

**Kamath et al. 2020 and 2021 — a *trade-off* between spatial and adversarial robustness.**
The 2020 paper shows empirically that training a model to be invariant to larger rotations *shrinks
the average distance to the decision boundary*, hurting `Linf` robustness, and vice versa (Kamath2020
§3.1, Fig. 8; boundary distance falls and PGD accuracy drops from ~85% to ~30% as rotation range
grows to 180 deg). The 2021 NeurIPS paper *proves* the trade-off on a synthetic distribution built
from a **cyclic error-correcting code** where a 90-deg rotation is modeled as a cyclic shift of `d/4`
coordinates (Kamath2021 §3, Thm 2: high adversarial accuracy forces low spatial accuracy and
conversely). Their **CuSP** curriculum reaches a better Pareto point but does *not* beat the
single-objective baseline on the adversarial axis (Kamath2021 Table 1: pure PGD ~45% adversarial /
~33% spatial; CuSP ~36-38% adversarial / ~53-62% spatial). Two facts matter for us: their "rate of
invariance" `Pr(f(TX)=f(X))` is *structurally the same as the consistency metric the old project
used*, and **neither Kamath paper cites Ge** — so the project sits at the intersection of two
independent lines (verified: Ge absent from both reference lists).

**Galloway et al. 2019 — a specific architecture choice (BN) *causes* vulnerability.**
Batch normalization fixes every neuron's first two moments at init, destroying the input-space
distances that confer robustness, consistent with a mean-field exploding-gradients analysis
(Galloway §2, §5). The effect is large: adding BN drops PGD robustness by 17-20% on SVHN (Galloway
Table 1), ~17% on CIFAR-10 VGG (Table 2), and 8.5-11% top-5 on ImageNet (Table 5) — *the same
magnitude as the architecture effects the old project reported*. Substituting `L2` weight decay for
BN removes both the vulnerability and the apparent `~sqrt(d)` scaling (Galloway §4, Tables 6-7).
*Implication for us: any cross-architecture robustness comparison is confoundable as a BN effect
unless BN is controlled — a methodology demand, not a contradiction.*

**Zhang 2019 — anti-aliasing makes invariance *help* (the foil).**
Standard downsampling (max-pool, strided conv) aliases and breaks shift-equivariance; inserting a
blur/low-pass filter before subsampling ("BlurPool") restores it (Zhang §3.2). BlurPool *improves*
shift-consistency, *and surprisingly improves clean ImageNet accuracy* (+0.7-0.9%), *and improves
average-case corruption robustness* (ImageNet-C/-P, Zhang §4.4). Critically, Zhang **never makes an
adversarial-`Lp` claim** — adversarial robustness is listed only as future work (Zhang §5). This is
the natural "invariance helps" counter-voice to Ge, but on *average-case* (corruption/shift)
robustness, not worst-case `Lp`.

**The contradiction, stated plainly.** Same word, "invariance," opposite conclusions:
Ge says (conditional) it *hurts* worst-case `Lp` robustness; the anti-aliasing line (Zhang, and
later TIPS) reports it *helps*; Kamath proves a *trade-off* on a cyclic-shift construction. None of
the three reconciles with the others, and two of them do not even cite the base result.

---

## Part 3 — What the wider literature settles, and the gap it leaves open

The downloaded literature confirms the contradiction is real and sharpens exactly what is missing.

**The "invariance/implicit-bias hurts" camp (theory, but not about shift).**
- *Tramer et al. 2020* prove that defending against `Lp` sensitivity forces *excessive invariance*,
  which raises a distinct invariance-based failure (an attack that changes the true label while the
  prediction stays fixed). But their "invariance" is over-invariance to an `Lp` ball, *not group/shift
  invariance*, and the experiments are MNIST-only. It shows invariance *can* hurt, not that *shift*
  invariance changes the `Lp` radius.
- *Frei et al. 2023* prove that for two-layer ReLU nets, the implicit max-margin bias of gradient
  descent reaches solutions that generalize but are **provably non-robust**, *even though robust nets
  fitting the data exist* (Frei Thms 4.1, 4.2). *Li et al. 2024* identify the mechanism as **feature
  averaging** and show finer supervision recovers the robust solution. *Min & Vidal 2024* show that
  swapping the activation (polynomial ReLU) flips the implicit bias from non-robust to robust. All
  three are about the *optimizer's implicit bias on synthetic near-orthogonal clusters with no group
  symmetry and `L2` only* — they say the obstacle to robustness is the optimizer's bias (which
  architecture *can* re-point), but none connects that lever to *translation* invariance.

**The "symmetry helps" camp (empirical, or linear, or the wrong group).**
- *Saha & Gokhale (TIPS) 2024* state verbatim that "better shift invariance is generally correlated
  with better adversarial robustness" (TIPS §6.4) and show that quadrupling parameters barely moves
  consistency (+1.71%) while their pooling operator moves it from 87.4% to 98.7% at ~5% more params
  (TIPS Table 6) — i.e. shift-invariance is architectural, not a capacity artifact. But it is a *pure
  empirical correlation, no theory linking shift-invariance to any `Lp` radius*, attacks are PGD/FGSM
  only (no AutoAttack, so possibly gradient-masked), one backbone, no causal/ablation isolation of
  invariance. **This is the result that preempts a naive "we discover co-existence" claim**
  (`RELATED_WORK_COMPARISON.md` TL;DR).
- *Wang et al. 2025 (Bridging Symmetry and Robustness)* report that *rotation/scale* equivariance
  improves robustness without adversarial training — but it is the *wrong group* (CNNs are already
  translation-equivariant), enforced not emergent, FGSM/PGD-only (no AutoAttack), and the "theory"
  is a contraction/CLEVER-bound argument with no theorem tying the group to an `Lp` radius.
- *Chen & Zhu 2023* prove linear equivariant steerable nets reach a *wider margin* than non-invariant
  ones (and that this equals training on the augmented dataset); *Lawrence et al. 2021* characterize
  the Fourier/Schatten-norm implicit bias of linear equivariant nets. Both are **linear-only and stop
  at margin/generalization — neither states an `Lp` robust radius**.

**The gap, distilled.** Putting the two camps side by side:

| | claims | but its limit is |
|---|---|---|
| Ge 2021 | invariance hurts (conditional on margin) | single GAP layer; never sweeps depth/pooling/kernel; the margin nuance is left as a remark |
| Kamath 2020/21 | trade-off, proven | along the *augmentation-strength* axis on synthetic binary data; rotation, not emergent shift; does not cite Ge |
| TIPS 2024 | shift-invariance helps | empirical correlation only; PGD/FGSM, no AutoAttack; no theory; no causal isolation |
| Bridging 2025 | equivariance helps | rotation/scale not translation; enforced; no AutoAttack; no `Lp` theorem |
| Chen-Zhu / Lawrence | symmetry widens margin / shapes bias | **linear only**; margin/generalization, never an `Lp` radius |
| Frei / Li / Min-Vidal | implicit bias is non-robust, but re-pointable | synthetic clusters, no group symmetry, `L2`; architecture lever is activation/supervision, not shift |

The shared, unfilled hole across *all* of them: **no result says what discriminative signal survives
a given (translation) invariance, turns that into an `Lp` robustness certificate, and validates it
under a standardized strong attack (AutoAttack) at matched capacity.** The "helps" side is empirical
or linear or the wrong group; the "hurts" side is about `Lp`-ball over-invariance or optimizer bias
on symmetry-free clusters. That is precisely the seam the old project stumbled into when its monotone
consistency story broke.

---

## Part 4 — Therefore: the questions and contributions the project pursues

The chain forces a specific set of questions. Each one answers a seed from Part 1 and closes a gap
from Part 3.

**Q1 (the ordering question — from seed 1 + Ge's own nuance).** If shift-consistency does *not*
order adversarial robustness, what single measurable quantity does? **Answer pursued:** the
**margin-to-Lipschitz ratio `eta/L`** of the data *in the invariant feature space* — Ge's "linear
margin predicts robustness better than dimension," made into an operational quantity. The project
shows `eta/L` predicts the robust radius (Pearson 0.998 on capacity-matched CIFAR-10) while
shift-consistency anti-predicts it (`DOCUMENTATION.md` §3; `2pagers` Sec. 3). This directly explains
the old report's "unexpected" models: they had high consistency but small invariant margin.

**Q2 (the structural question — closes the "what survives invariance" gap).** Exactly what signal
does a given invariance keep? **Answer pursued:** an *exact* invariant-margin identity — a shift-
invariant linear classifier sees data only through the group-average projector `P_G`, with margin
`(1/2) dist(conv P_G X+, conv P_G X-)` (cyclic case = the DC interval distance, recovering Ge); a
conv-square-pool layer instead realizes *power-spectrum* features; and a degree-3 *bispectrum*
invariant separates the localized/phase-coded case (the Ge dot `+/-e_j`) that the power spectrum
cannot (`DOCUMENTATION.md` §2).

**Q3 (the certificate question — closes the "tie invariance to an `Lp` radius" gap).** Does
`eta/L` actually certify the radius? **Answer pursued:** `r2 >= eta/L` is a Lipschitz-margin
certificate with *no general converse* (so it is a certificate and predictor, not a
characterization), plus a companion orbit-flip radius `rho_G` that formalizes Tramer's
excessive-invariance side (`DOCUMENTATION.md` §2). This is the link from translation invariance to an
`Lp` radius that no prior paper supplied.

**Q4 (the trust + control question — from seeds 3 and 4).** Do the findings survive a strong attack
and matched capacity? **Answer pursued:** a **capacity-matched dissection** (standard / anti-aliased
/ exact-cyclic / shift-augmented, identical parameter counts) on MNIST, Fashion-MNIST and CIFAR-10,
with the robust radius measured by a min-norm attack (DDN) and validated against **AutoAttack** to
rule out gradient masking, under both standard and PGD adversarial training; the BN confound is
controlled per Galloway (`DOCUMENTATION.md` §3, §4). The margin/Lipschitz decomposition then
*attributes mechanism*: anti-aliasing moves the Lipschitz term `L`, exact cyclic invariance moves
the margin `eta` (the real-data form of the Ge collapse).

**Q5 (the GSIAR-justification question — from seed 2).** Why does a model land where it lands on the
consistency-vs-robustness plane, and can the diagnostic be principled? **Answer pursued:** the
optimization story — on orbit-closed data shift-invariance is provably *margin-free* (so gradient
descent self-symmetrizes and GSIAR's "Goal Zone" is reachable for free there), while on
near-orthogonal cluster-geometry data invariance *does* help `eta/L` (the trajectory-level selection
theorem there is the open frontier) (`DOCUMENTATION.md` §2, §5).

**The one-line contribution.** The project replaces the old project's unexplained quadrant heuristic
and the literature's contradictory verbicide with a single organizing quantity, `eta/L` in the
invariant feature space, that (i) says what survives an invariance, (ii) certifies and predicts the
`Lp` radius, and (iii) is validated under AutoAttack at matched capacity — turning "does invariance
help or hurt?" into "which term, margin or Lipschitz, does this particular invariance move?"
(`2pagers/...tex` abstract; `DOCUMENTATION.md` §1).

---

*Framing note for the primer.* This document is the "find the questions" front-matter: the primer's
concept sections (robustness, Lipschitz/`eta/L`, margins, implicit bias, NTK) are exactly the tools
Q1-Q5 need, so the motivation should precede them and each concept section can point back to the
question it serves.
