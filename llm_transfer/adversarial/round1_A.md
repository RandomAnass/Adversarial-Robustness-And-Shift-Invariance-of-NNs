# Literature Adversary — Round 1, Lens A (text-side LLM adversarial robustness)

Auditor pass over the three lens-A pilot designs (A1, A2, A3). Goal: kill or fix on paper
before compute. Every load-bearing prior below was downloaded to `pdfs/` and read
end-to-end at the cited sections (not from abstract). Verdicts are deliberately skeptical.

**PDFs downloaded + read** (`llm_transfer/adversarial/pdfs/`):
2506.24056 (Logit-Gap Steering), 2403.00867 (Gradient Cuff), 2412.06748 (Refusal Tokens),
2402.09063 (Schwinn embedding attack), 2406.11717 (Arditi refusal direction),
2510.09023 (Attacker Moves Second), 2502.10487 (Fast Proxies), 2602.06256 (Steering Off a Cliff).
Abstract-level cross-checks (WebFetch/WebSearch): 2510.27062, 2503.01345, 2512.12066,
2601.19487, 2604.12817, 2505.16947.

---

## CROSS-CUTTING FINDING THAT HITS ALL THREE DESIGNS (must fix)

**The Schwinn embedding attack (2402.09063) is UNCONSTRAINED and APPEND-BASED, not an
"L2-ball perturbation of the prompt embeddings."** Read directly from §3 of the paper:

- The attack **explicitly imposes no norm constraint**: *"As we are generally interested in
  the worst-case output behavior of the model, we do not put any constraints on the generation
  of embedding space attacks, such as restricting the magnitude of the perturbation."*
- The update is signed-gradient ascent `e^{t+1} = e^t − α·sign(∇L)` with **no projection and
  no ε ball** (Fig. 1–2, method text). Fast Proxies (2502.10487, App. B) runs it as an
  **appended suffix** initialised `"x x x x x"` scaled by the mean vocab-embedding L2 norm —
  i.e. a fresh soft-prompt block concatenated to the instruction, `<instruction><adv embedding>`.
- Therefore the ground-truth strong attack **appends new embedding vectors** and leaves the
  prompt's own token embeddings `e(x)` intact.

Two consequences the current designs get wrong:

1. **Every claim that Schwinn "constrains to an L2 ball with an explicit budget" is false.**
   (Appears in A1 line 61, A2 lines 18/47/50, and the litsweep line 51.) The designs need to
   **introduce their own projected/PGD-style embedding attack** (add a per-step projection onto
   an L2 or L∞ ball of the prompt-token perturbation) and must attribute the norm ball to
   themselves, not to Schwinn. This is a legitimate protocol choice but currently mis-cited; a
   referee who has read Schwinn will flag it immediately and it undermines the "threat model" claim.

2. **Certificate/label threat-model mismatch (most dangerous for A2).** The attack-free
   certificate `R_q(x)=M(x)/‖∂M/∂e(x)‖_q` is a first-order radius for perturbing the *prompt's
   own* token embeddings. The default Schwinn label comes from *appending* an adversarial block.
   These are different threat models: `R_q` lower-bounds robustness to prompt-embedding
   perturbation, but the label measures susceptibility to an appended soft prompt. The A2 count
   law `ASR(ε)=CF(ε)` can fail purely from this mismatch, not from any breakdown of local
   affinity. **Fix: define the strong attack as a projected perturbation of the SAME prompt
   embeddings the gradient is taken on** (L2/L∞-ball PGD on `e(x)`), so certificate and label
   share one threat model. Keep the appended-suffix Schwinn attack only as a secondary
   "does the ordering survive a different threat model" cross-check, explicitly out of the count law.

This single fix is prerequisite for A1's threat-matching arm, A2's entire headline, and A3's
strong-attack column to mean what the designs say they mean.

---

## A1 — gauge-free ratio vs consistency  (`A1_gaugefree_ratio_vs_consistency.md`)

### VERDICT: needs-fix (survives; do not kill)

The core novelty — forming the *ratio* M/L_q as a per-prompt, gauge-free, threat-matched LLM
robustness object — is genuinely open. A dedicated search for any LLM margin-over-gradient-norm
ratio returned only Gradient Cuff (gradient-norm-alone detector) and vision Lipschitz-margin
work. No LLM paper forms the ratio, proves its gauge-invariance, threat-matches, or runs the
consistency dissociation. But three load-bearing statements are mischaracterised and the T2
"consistency" gap is more contested than the design admits.

### Load-bearing priors — read and verified

- **Logit-Gap Steering (2506.24056)** — READ §1–3, §5, App. G/I. Confirmed: uses the *raw*
  refusal−affirmation logit gap at position 1; **no gradient/Lipschitz normalization, no ratio,
  no threat-matching, no paraphrase-invariance test.** Confirmed it never discusses
  temperature/scale as a gauge issue ("temperature" appears only as a generation param; the one
  "calibrated predictor" mention is about an unrelated token-ranking heuristic, their Eq. 6).
  **CORRECTION (load-bearing misread):** the design says Logit-Gap "already uses the raw gap to
  predict per-prompt jailbreak success." The paper is *explicit that it does NOT validate this*:
  *"median gap closure co-varies with True-ASR ... **This is an internal consistency check, not
  an independent predictor, since the method optimizes gap closure**"* (§1 contributions, §5).
  So the raw gap is even *less* established as an independent per-prompt predictor than A1 states.
  This helps A1's novelty but the current wording overstates the baseline; a referee will catch it.
  Reframe the baseline as: "the raw gap has been *proposed* as a margin but never validated as an
  attack-free independent per-prompt predictor; we test whether it is one, and show the *ratio*
  is the object that predicts."

- **Gradient Cuff (2403.00867)** — READ §3, §4. Confirmed as denominator-only prior: gradient
  norm of the **refusal loss** `1−P(refuse)` w.r.t. the **mean-pooled sentence embedding**,
  estimated **zeroth-order** (Gaussian finite differences), used as a per-INPUT detector on
  already-adversarial vs benign inputs. Does not form a margin/ratio, does not threat-match, no
  gauge. **Sharpening available:** A1's denominator is the *exact analytic* gradient of the
  *logit margin* w.r.t. *per-token* embeddings — distinct from Gradient Cuff's zeroth-order
  refusal-loss gradient on a pooled embedding. State this; it widens the gap.

- **Refusal Tokens (2412.06748)** — READ §1, §2. **CORRECTION (load-bearing misread):** the
  design (line 24, and A1 hypothesis 2 "the Refusal-Tokens knob") treats it as an off-the-shelf
  logit-bias gauge knob on Llama-3. It is **not**: the mechanism requires *training* a `[refuse]`
  token prepended during alignment, then *thresholding its softmax prob* at inference. You cannot
  apply the Refusal-Tokens method to stock Llama-3-8B-Instruct. What *is* available is a **generic
  logit bias on refusal tokens** — the paper mentions this in passing (§ "adding a logit bias")
  but its actual contribution is the trained-token thresholding. **Fix:** run the gauge test with
  a plain refusal-token logit bias / temperature scaling that you define, and cite Refusal Tokens
  only as evidence that "refusal rate is a movable knob," not as the knob you turn.

- **Schwinn (2402.09063)** — see cross-cutting finding. A1's "strong attack" must become a
  projected prompt-embedding attack; the L2-ball attribution to Schwinn is wrong.

- **Fast Proxies (2502.10487)** — READ full. Confirmed: attack-based proxies (embedding ASR,
  prefilling, direct), no margin/Lipschitz diagnostic, no threat-match, no gauge, no
  budget-norm — **but operates at MODEL-RANKING granularity (33 models), not per-prompt.**
  A1 is per-prompt on one model. **Fix the framing:** the gap over Fast Proxies is *both*
  attack-free-vs-attack-based *and* per-prompt-vs-model-ranking. Say so; otherwise a reviewer
  reads Fast Proxies (Pearson 0.87 with embedding ASR) as "already predicts robustness cheaply."

### Missing papers the designer never saw (bear on the T2 "consistency" gap — the flagship claim)

- **Consistency Training Helps Stop Sycophancy and Jailbreaks (2510.27062)** — MISSING, and it
  cuts against A1's T2. It *trains* for consistency across prompt augmentations (incl. jailbreak
  text) and reports this *reduces* jailbreaks (BCT/ACT). A1 claims consistency *anti-predicts*
  robustness. These are reconcilable (trained-in invariance vs observed per-prompt consistency on
  a fixed model) but the design does not make the distinction, and a referee will pit them against
  each other. **Fix:** scope T2 explicitly to a *per-prompt observational* consistency metric on a
  *fixed, un-consistency-trained* model, and pre-empt 2510.27062 by name.
- **Same Question, Different Words: Latent Adversarial Paraphrasing (2503.01345)** — MISSING.
  Shows worst-case paraphrases "drift in embedding space" and trains against it. Reinforces that
  paraphrase-robustness and embedding robustness are entangled — which makes A1's clean
  "consistency does NOT predict" outcome *less* a priori obvious. Cite it; treat as the reason the
  dissociation is a real empirical question, not a foregone conclusion.
- **Instability of Safety under seeds/temperature (2512.12066)** — MISSING and partially
  undercuts A1's motivation. It already shows 18–28% of refusals flip across temperature/seed and
  SSI drops 0.977→0.942 at T=1.0. So "the raw refusal decision is scale/temperature-fragile" is
  *already published*. A1's gauge point survives (they treat temperature as sampling noise and
  form no scale-invariant metric), but A1 must cite it and pitch novelty precisely: *a
  scale-INVARIANT logit-margin ratio*, not "refusal is temperature-fragile" (taken).

### Corrections summary (A1)

- (a) **Framing:** gap over Fast Proxies is per-prompt AND attack-free; gap over Logit-Gap is the
  *ratio + validated independent prediction*, not "they predict, we normalize."
- (b) **Load-bearing:** drop "Logit-Gap predicts per-prompt success" (they disclaim it); drop
  "Schwinn L2 ball" (unconstrained, append-based); drop "Refusal-Tokens knob on Llama-3"
  (needs training) → use a self-defined refusal logit-bias/temperature gauge.
- (c) **Gap:** T2 must be scoped to observational per-prompt consistency on a fixed model and must
  pre-empt 2510.27062 / 2503.01345; otherwise the "consistency is the wrong signal" headline is
  attackable as already-refuted-by-consistency-training.
- (d) **Protocol:** strong attack = projected (L2/L∞-ball) PGD on the *same* prompt embeddings the
  gradient uses; keep append-suffix Schwinn as a secondary threat-model cross-check. Keep the
  gauge stress-test (logit bias/temperature) as the headline — it is the cleanest thing the raw
  gap cannot survive and the ratio can.

---

## A2 — certified fraction = attack-free ASR curve  (`A2_certified_fraction_attackfree_ASR_curve.md`)

### VERDICT: needs-fix (highest risk of the three; fixable but the count law is fragile)

The measurement-theory contribution (ASR(ε)=CF(ε), budget-normalized collapse, dual-norm
matching) is open in LLM-land. But A2 inherits the full weight of the Schwinn mismatch, and the
count law is exact only in a locally-affine regime that is far shakier for transformers than for
the paper's ReLU-CNN cells.

### Load-bearing priors — read and verified

- **Schwinn (2402.09063)** — the count law's ground-truth ASR side is built on this. As above, it
  is unconstrained and append-based. **A2 cannot state "ASR(ε) = certified fraction" unless the
  attack is a projected perturbation of the prompt embeddings at each ε on the ladder, on the same
  vectors the certificate differentiates.** Otherwise ASR(ε) and CF(ε) are measuring two threat
  models and any agreement/disagreement is uninterpretable. This is the make-or-break fix.
- **Fast Proxies (2502.10487)** — confirmed does not budget-normalize or threat-match; A2's
  cross-budget/dual-norm geometry is not covered. Good. But A2's "attack-free" advantage is weaker
  than A1's because A2 *still runs the full attack ladder to validate the law* — the payoff is only
  realised *after* the law is validated, and the paper's own vision count-law was validated, not
  used to replace attacks. Frame A2 as *establishing the law*, and the cheap-proxy payoff as a
  consequence, not as the deliverable of this single run.
- **Kim et al., Lipschitz of Self-Attention (2006.04710)** — the design already caveats that a
  global transformer Lipschitz constant does not exist and uses the *local* gradient norm. Correct
  and necessary; keep it.

### The count-law premise is the real kill risk (be honest about it up front)

The vision count law `robust acc = certified fraction` is exact *on affine cells* of a piecewise-
linear ReLU network. Transformers have **softmax attention and (for Llama) SiLU/GELU** — smooth,
curved, not piecewise-affine — so "locally-affine cell" is an approximation whose validity radius
may be far below any interesting attack budget. The design's own kill line ("gap > 0.1 even at
smallest budgets") is right, but the *prior probability of that kill* is high and the design
undersells it. **Corrections:**
- Report the count law as a *small-budget expansion* and make the "curvature edge" (budget at
  which the gap exceeds 0.05) the primary finding, not a fallback. That is a publishable
  measurement result even if the equality holds only in a thin regime.
- Add a **local-linearity diagnostic** (e.g. relative gap between M(x+δ) and its first-order
  Taylor prediction along the attack direction, vs ‖δ‖) so the affine-regime claim is *measured*,
  not assumed. Without this the headline equality is one referee question away from collapse.

### Missing papers

- **MIXAT (2505.16947)** and **Understanding/Improving Continuous AT for LLMs (2604.12817)** —
  MISSING. Continuous/embedding adversarial-training work: relevant because a model that has *seen*
  embedding attacks in training will have a very different local geometry (flatter, more affine),
  which is exactly where the count law would hold best. If A2 wants the count law to succeed,
  running it on a *continuously-adversarially-trained* checkpoint (not just stock Llama-3) is the
  higher-probability-of-success variant, and these papers give the recipe. Consider it.
- **StrongREJECT (2402.10260, in litsweep)** — already noted; ensure the local judge is
  StrongREJECT/HarmBench-classifier and report judge agreement, because ASR(ε) noise directly
  caps the achievable |ASR−CF| gap and the target is <0.05.

### Corrections summary (A2)

- (a) **Framing:** headline = "we establish the count law / the right axis," cheap-proxy payoff is
  downstream, not this run's product; per-prompt scatter (R_q vs measured min radius) is the
  robust fallback if the distributional equality is only thin-regime.
- (b) **Load-bearing:** remove "Schwinn L2 ball at each budget"; the attack must be your own
  projected prompt-embedding PGD, sharing the certificate's threat model and its differentiation
  variable.
- (c) **Gap:** the affine-regime equality is genuinely open but *fragile* for transformers; state
  the curvature edge as the result and add a measured local-linearity check.
- (d) **Protocol:** consider a continuously-AT'd checkpoint as the count-law-favourable arm; keep
  the masking check (more steps/restarts don't raise ASR); dual-norm matching only means something
  once the attack is a genuine L2-ball vs L∞-ball *projected* attack.

---

## A3 — refusal margin is not a target / over-refusal  (`A3_refusal_margin_not_a_target_overrefusal.md`)

### VERDICT: needs-fix (survives, but a 2026 paper substantially overlaps the headline — reposition)

The transferred idea (raising the refusal margin is a gauge move whose maximizer is the
over-refuser = constant classifier; only genuine AT buys robustness) is a clean and reviewer-
legible reframing. But a paper the designer never cited already shows the empirical half of A3's
claim in mirror image, and two 2026 steering-tradeoff papers crowd the space. A3 must reposition
around the *gauge-degeneracy explanation + the gauge-free ratio correctly reporting no gain*,
which the prior work lacks.

### Load-bearing priors — read and verified

- **Arditi (2406.11717)** — READ §3. Confirmed: mean-difference refusal direction; **adding** it
  induces refusal on harmless prompts (Figs 3–4). Valid ENABLE for A3's steering knob and the
  over-refusal mechanism. A3's characterization (Arditi studies inducing/removing, not the
  scaling-vs-robustness tradeoff or its gauge status) is accurate.
- **Attacker Moves Second (2510.09023)** — READ §1, §4–5. Confirmed: **none of 12 defenses across
  4 techniques survives strong adaptive attacks** (incl. Circuit Breakers). This BLOCKS any bare
  "steering looks robust under weak attacks but collapses under strong ones" as a novel claim — it
  is established. A3's contribution must be the *predictive/explanatory* gauge angle, not the
  collapse demonstration. The design already knows this (T5 dropped); keep it dropped and cite
  2510.09023 as the reason.
- **Refusal Tokens (2412.06748)** — same correction as A1: the "pure-gauge logit-bias knob" is a
  *generic* refusal-token logit bias you define, not the Refusal-Tokens trained-token method. The
  A3 logit-bias arm (its cleanest gauge test) is fine — just don't attribute the mechanism to that
  paper.
- **Schwinn (2402.09063)** — A3's strong-attack column must again be a projected prompt-embedding
  attack, not "Schwinn L2 ball." Under steering, the margin M shifts; the attack must be
  recomputed at each steering strength on the same embeddings.

### Missing papers — one is a serious partial preemption

- **Steering Safely or Off a Cliff? (2602.06256, Goyal & Daumé, Feb 2026)** — MISSING and the
  biggest threat to A3. Read: it introduces "robustness specificity" and shows that **all
  over-refusal steering methods reduce over-refusal without harming general ability or refusal on
  harmful queries, yet substantially INCREASE jailbreak vulnerability** — i.e. steering silently
  trades robustness. This is the mirror image of A3's claim (they steer *down* out of over-refusal;
  A3 steers *up* into it) and it already establishes the load-bearing empirical point that steering
  is not a real robustness lever. **What A3 still owns after this paper:** (i) the *gauge-degeneracy
  theory* — over-refusal as the scale-invariant maximizer / constant classifier; (ii) the
  demonstration that a *gauge-free ratio R_q correctly reports "no robustness gain"* where the raw
  margin reports a spurious gain; (iii) steering *up* to the over-refuser endpoint + utility
  collapse. 2602.06256 has none of these. **Fix:** cite it as the closest empirical prior,
  restate A3's delta as "we give the *why* (gauge degeneracy) and the *correct read-out* (the
  ratio), and complete the curve to the constant-classifier endpoint."
- **LLM-VA (2601.19487)** and **AlphaSteer (2506.07022)** — MISSING. Both frame and *resolve* the
  jailbreak-vs-overrefusal tradeoff (vector alignment / null-space steering). A3 is not a competing
  method (it's a diagnostic reframe), but reviewers will ask "why not just use AlphaSteer/LLM-VA."
  A3 must state it is a *negative/diagnostic* result about naive margin/steering, orthogonal to
  these method papers, and ideally include one of them as a "genuine intervention that raises R_q
  without over-refusal" comparator — cheaper and more current than the ReFAT fine-tune arm.
- **ReFAT (2409.20089) / LAT (2407.15549)** — already in the design as the AT comparators; keep.
  Given compute, prefer the inference-time refusal-feature ablation (compute-free) plus one of
  AlphaSteer/LLM-VA over a full ReFAT fine-tune, to keep this a single strong run.

### Corrections summary (A3)

- (a) **Framing:** move the headline from "steering the margin up doesn't buy robustness" (now
  partly established by 2602.06256) to "over-refusal *is* the scale-degeneracy of margin
  maximization, the gauge-free ratio proves it, and only a genuine intervention moves the ratio."
- (b) **Load-bearing:** fix Refusal-Tokens (generic logit bias, not their trained token); fix
  Schwinn (projected prompt-embedding attack recomputed per steering strength); keep Arditi as-is.
- (c) **Gap:** the "steering isn't robustness" empirical point is no longer fully open (2602.06256);
  the gauge-degeneracy explanation and the ratio-as-correct-readout are. Reposition accordingly.
- (d) **Protocol:** add 2602.06256's over-refusal-steering setup and at least one of
  AlphaSteer/LLM-VA as the "genuine intervention" comparator; keep the logit-bias arm as the clean
  pure-gauge test; measure R_q (the ratio) at every strength so its flatness under pure gauge and
  its rise only under genuine AT is the load-bearing curve.

---

## One-line bottom line per design

- **A1** needs-fix / survives — novelty (the ratio) is real and open; fix the three misreads
  (Logit-Gap disclaims independent prediction; Schwinn is unconstrained/append-based; Refusal-
  Tokens needs training) and pre-empt the consistency-training papers on T2.
- **A2** needs-fix / survives (highest risk) — the count law is only meaningful once the attack is
  a projected prompt-embedding PGD sharing the certificate's threat model, and the affine regime is
  fragile for transformers; make the curvature edge the result and measure local linearity.
- **A3** needs-fix / survives — reposition around gauge-degeneracy + the ratio as the correct
  read-out, because "steering isn't a robustness dial" is now partly established by
  Steering-Off-a-Cliff (2602.06256).
