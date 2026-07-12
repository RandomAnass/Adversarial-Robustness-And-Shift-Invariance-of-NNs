# Orthogonal novel LLM angles (beyond the demoted constant-classifier finding)

User directive: "demoting and reproducing something is not enough ... we need to search orthogonal
angles." Agent-generated 7 angles + my source-verification of the two load-bearing competitors.
Hard constraints respected: T-DISS is a negative (no "η/L predicts jailbreak radius" angle);
constant-classifier degeneracy is published (lens only); ρ_G budget-law + trade-off are retracted.

## Verified competitors (I checked these against arXiv directly)
- **Raina et al., ACL 2024 (2402.17509)** "Extreme Miscalibration and the Illusion of Adversarial
  Robustness" — VERIFIED REAL. *"miscalibrating models masks gradients ... giving rise to an apparent
  increase in robustness"*, *"illusion of robustness"*. Scope = **NLP text CLASSIFIERS** (misclassify);
  remedy = **temperature calibration procedure**. This is the serious foil for Angle A/E: the
  "miscalibration → illusion of robustness" concept is THEIRS. Our delta must foreground it: generative-
  LLM SAFETY scope + real post-training ops (RLHF/quant/merge) as the gauge source + a gauge-INVARIANT
  metric η/L (not a calibration step). Novel but narrower than first pitched.
- **Small Edits, Big Consequences (2507.15868)** — VERIFIED REAL. Studies meaning-flip invariance
  (*"only 54% react to a single quantifier flip"*), **no radius/certificate/gradient/margin/Lipschitz,
  no sycophancy/over-refusal/jailbreak prediction, only pass-rate drops**. → Angle B's novelty (ρ_G
  radius + certificate + PREDICTOR of a behavioral failure) is CLEAN vs this.

## Ranked angles

**#1 Angle B — ρ_G as a cheap, attack-free predictor of sycophancy & over-refusal. [RUN FIRST]**
Claim: the orbit-flip radius ρ_G (smallest meaning-changing edit the model wrongly ignores), from
forward passes only, predicts per-prompt sycophancy and over-refusal (small ρ_G ⇒ more
sycophantic / more over-refusing). Novelty CLEAN (2507.15868 has the phenomenon, not the radius or the
predictor; SYCON 2505.23840 is behavioral-only). Feasibility VERY HIGH (per-item ρ_G cached for Llama
+ Qwen). Main-track. Turns ρ_G from "a radius we define" into "a radius that predicts a costly-to-
measure safety behavior" — the LLM leg's real, un-demoted contribution.

**#2 Angle A/E — gauge as an unrecognized confound in LLM safety eval; η/L sees through. [RUN SECOND]**
Claim: post-training ops (RLHF/DPO, int4 quantization, model merging) shift a model's effective logit
temperature (gauge f→cf), silently moving naive robustness/confidence/ASR metrics with NO behavioral
change; gauge-invariant η/L recovers the true ordering. Killer demo (E): make behaviorally-matched
bf16/int4/merged variants of Llama-3-8B; a standard ASR/confidence leaderboard REORDERS them from the
gauge shift while η/L keeps the invariant ranking. Novelty PARTIAL — foreground Raina (2402.17509);
our delta = generative-LLM safety + post-training-as-gauge-source + invariant metric. Main-track,
methodology impact. gauge_sweep.py infra exists.

**#3 Angle C** — per-prompt η/L on the instruction-following margin predicts indirect prompt-injection
susceptibility on CLEAN contexts (vs Gradient Cuff 2403.00867 which detects incoming jailbreaks with
gradient-norm alone). Most-open predictor; medium feasibility (injection-success label risk). Main.

**#4 Angle D** — layer/head localization of the sensitivity(η/L) ⊥ excessive-invariance(ρ_G)
dissociation; ablating invariance-heads raises ρ_G without changing η/L. ICLR/interpretability.

**#5 Angle F** — cross-model attack-free η/L ranking (vs Fast Proxies 2502.10487 = stripped attacks).
Section-only, do NOT attach to jailbreak radius (T-DISS negative).

**REJECTED Angle G** — η/L predicts hallucination: SCOOPED (Grad-Detect 2606.24790, EPGS 2605.00939).
Do not run.

## To run when GPU 0 frees (queue, disjoint infra)
1. (cheap, resolves T-DISS) `fix_matched_margin.py` — matched continuation margin vs jailbreak radius.
2. (weak-attack section) `run_weakattack.py` — PGD-k monotonicity + consistency-vs-robustness decay.
3. (Angle B, primary orthogonal) `run_angleB.py` [TO BUILD] — sycophancy probe (leading-question flip
   on the 1200 sentiment/NLI items) + over-refusal (safety-family benign-edit refusal from cache);
   correlate per-item ρ_G and η/L with each target (Spearman + AUROC + partial, bootstrap CIs).
   Pre-registered kill: correlation CI includes 0 after controlling clean acc + length.
4. (Angle A/E, second orthogonal, larger) variant creation (bf16/int4/TIES-merge) + η/L invariance
   vs naive-metric reordering, with gauge_sweep.py as the synthetic-gauge control.

## Verify-before-citing (agent-flagged UNVERIFIED, none load-bearing)
2602.13289 (quant→ECE), 1905.04270 (Yu scale-invariant normalization), 2606.24790 / 2605.00939
(hallucination). Confirm by direct PDF read before any appears in the paper.
