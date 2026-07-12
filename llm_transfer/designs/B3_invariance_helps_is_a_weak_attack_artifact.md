# Invariance Helps Only Under Weak Attacks: An Adaptive-Attack Audit of Consistency-Trained LLM Safety

## Transferable element (from our paper)
- (e) The "invariance-helps-robustness" reports are a weak-attack artifact: the ordering reproduces under a weak
  attack (FGSM) and vanishes under a strong one (AutoAttack). In the vision paper this is shown by retraining the
  contrary-literature operators (TIPS, rotation-equivariant nets) under their own recipe.
- The mechanism: imposing exact invariance collapses the decision margin; robustness that survives a strong attack
  is ordered by the threat-matched η/L, not by the imposed invariance / consistency level.
- The diagnostic-not-target corollary: driving invariance/consistency to the maximum degenerates toward the
  constant classifier (here: over-refusal), our Lemma ratiodegen.

LLM instantiation. Imposing invariance to jailbreak wrappers via CONSISTENCY TRAINING is the live "invariance helps
safety-robustness" claim. Audit it under a threat-matched ADAPTIVE attack and read the surviving order off the
refusal margin, not the imposed invariance.

## Literature gap (specific papers checked + why open)
- DeepMind "Consistency Training Helps Stop Sycophancy and Jailbreaks" (Oct 2025, arXiv:2510.27062): trains models
  to answer identically across jailbreak wrappers/sycophancy cues (output-level BCT, activation-level ACT); reports
  ASR reductions — BUT evaluates on FIXED jailbreak patterns, runs NO adaptive attack targeting the consistency
  objective, no GCG/embedding attack, and reports no margin/Lipschitz. This is exactly the FGSM-only regime our
  paper dissects.
- Jain et al. "Baseline Defenses" (arXiv:2309.00614): paraphrase defense (imposed paraphrase invariance) works vs
  non-adaptive GCG and is BROKEN by adaptive attacks — a prior data point for the artifact, but not framed as a
  margin-governed weak-vs-strong law.
- ChatBug (AAAI 2025, arXiv:2406.12935): format-invariance adversarial training mitigates but with large helpfulness
  cost (margin collapse analog) — trade-off noted, not a margin law.
- Logit-Gap Steering (arXiv:2506.24056): refusal margin predicts jailbreak outcome — gives the numerator η but no
  Lipschitz, no invariance dissociation.
No paper tests whether consistency/invariance-imposed safety survives a threat-matched adaptive attack, nor whether
the surviving order is set by the refusal-margin-to-embedding-sensitivity ratio. Open, with a live claim to refute.

## Hypothesis (falsifiable)
On one base aligned model with an increasing "invariance dose" (consistency-LoRA strength imposing wrapper-invariant
refusal):
- H1 (weak-attack ordering, reproduce the claim): under the NON-ADAPTIVE attacks the consistency-training paper uses
  (fixed template jailbreaks, non-adaptive paraphrase attack ≈ FGSM), higher invariance dose LOWERS ASR — invariance
  appears to help.
- H2 (strong-attack collapse): under a THREAT-MATCHED strong attack (GCG + embedding-space attack, and an ADAPTIVE
  attack that co-optimizes the wrapper against the consistency objective ≈ AutoAttack), the advantage over the base
  model shrinks toward zero / inverts; the highest-dose (most wrapper-invariant) model is not the most robust.
- H3 (margin law): across doses, the threat-matched ratio η/L (refusal-affirmation logit gap ÷ embedding-space
  ∥∇gap∥₂) predicts strong-attack robust rate (Pearson ≥ +0.7), while the imposed consistency level anti-predicts or
  is uninformative; higher dose collapses the refusal margin η (the mechanism).
- H4 (degeneracy): pushing the dose to the maximum drives over-refusal (benign-refusal rate ↑, helpfulness ↓) —
  the constant-classifier degeneracy — with no strong-attack robustness gain.
Kill: if the consistency advantage SURVIVES the adaptive threat-matched attack at the highest dose, the weak-attack-
artifact transfer fails and consistency training is genuinely robust (also a clean, publishable result).

## Protocol (model, dataset/benchmark, attack/eval incl. STRONG attack, metrics, exact steps)
- Model (local): `Meta-Llama-3-8B-Instruct` (primary; `Qwen2.5-7B-Instruct` and `Ministral-8B-Instruct-2410` as
  appendix cross-points, not a sweep).
- Imposed-invariance arms (doses on ONE base model): dose 0 = base; doses 1–3 = consistency-LoRA (reproduce a
  lightweight BCT: SFT the model to emit the base model's CLEAN-prompt refusal on wrapper-augmented harmful prompts),
  trained at increasing consistency weight / wrapper coverage. One short LoRA per dose (~3 arms), not a model sweep.
- Full jailbreak benchmark: HarmBench standard behaviors (download; ~400 behaviors) and/or AdvBench harmful
  behaviors; safety-preference stress from local `PKU-Alignment/PKU-SafeRLHF`. Helpfulness/over-refusal:
  XSTest (download) + a benign instruction set for the degeneracy check.
- WEAK attacks (reproduce the claim): fixed template jailbreaks (curated jailbreak template set), non-adaptive
  paraphrase attack, sycophancy-cue wrappers — the regime of arXiv:2510.27062.
- STRONG / threat-matched attacks: (a) GCG suffix (arXiv:2307.15043) on the full behavior set (or the HarmBench
  standard subset for cost); (b) embedding-space attack (Schwinn et al., arXiv:2402.09063) — differentiable, gives a
  per-prompt minimum-norm jailbreak radius (r₂ analog); (c) ADAPTIVE attack: co-optimize the wrapper text against
  the CONSISTENCY objective (the AutoAttack-of-this-defense), the piece the DeepMind eval omits. Masking check:
  embedding radius vs GCG success agreement (our DDN-vs-AutoAttack check).
- Margin/sensitivity: η = E[refusal−affirmation logit gap] (Logit-Gap Steering definition; also project onto the
  Arditi refusal direction as a low-D margin); L = E∥∇_emb (gap)∥₂ threat-matched to the embedding attack, ∥·∥₁ as
  mismatched control. η/L gauge-free (temperature-invariant) — verified by logit rescaling.
- Local judge (no paid API): HarmBench Llama-2-13B classifier (open weight) for attack success; refusal detection by
  string+classifier ensemble; over-refusal by XSTest rubric with `deberta-v3-large-zeroshot-v2.0`.
- Metrics: per-dose ASR under each attack; weak-vs-strong ordering inversion; Pearson(η/L, strong-ASR) vs
  Pearson(consistency-dose, strong-ASR); per-prompt Spearman(η/L, embedding jailbreak radius); benign-refusal rate
  and helpfulness vs dose (degeneracy); confirm GCG ≤ embedding-attack success (no masking).

## Compute estimate (GPU-hours on A6000s)
Consistency LoRAs: ~3 doses × 3–5 h ≈ 10–15 h. GCG on HarmBench subset × 4 arms (~2–5 min/behavior) ≈ 40–70 h
(the dominant cost; cap behaviors/steps to fit). Embedding + adaptive attacks (cheap, differentiable) over full set
× 4 arms ≈ 15–25 h. Forward-pass margins + judging ≈ 8 h. Total ≈ 75–110 GPU-h; a GCG-light core (embedding +
adaptive only) ≈ 40 h.

## Why standalone top-tier (what a reviewer would call the contribution)
A rigorous adaptive-attack refutation of the emerging "consistency/invariance training makes LLMs safe" narrative:
imposed input-invariance buys robustness only against the non-adaptive attacks it is evaluated on, collapses under a
threat-matched adaptive attack that targets the invariance objective, and the surviving robustness is governed by a
forward-pass refusal-margin-to-sensitivity ratio — with maximal invariance degenerating into over-refusal. It
directly engages a live 2025 result (arXiv:2510.27062) and the paraphrase-defense/ChatBug line, and gives the safety
community a cheap margin diagnostic plus an adaptive-eval protocol. Mirrors our AutoAttack-collapse story in the
safety domain; stands on the jailbreak literature, borrowing our theory only for the η/L framing.

## Risks / kill criteria
- Risk: reproducing consistency training faithfully. Mitigate by using the simplest published variant (output-level
  BCT: match clean-prompt behavior on wrapped prompts) and reporting it as a lightweight reproduction, with the dose
  knob making the trend the claim rather than any single checkpoint.
- Risk: GCG cost. Mitigate by capping to the HarmBench standard subset and shifting weight to the cheap
  differentiable embedding + adaptive attacks, which already deliver the strong-attack ordering.
- Risk: the base model is already near-0 ASR under strong attacks (floor), hiding ordering. Mitigate by reporting
  per-prompt jailbreak RADIUS (continuous, our r₂ analog) not just ASR at one budget — the exact fix the vision
  paper uses when AutoAttack floors to zero.
- Kill: consistency advantage survives the adaptive threat-matched attack at the top dose with η/L NOT predicting →
  the weak-attack-artifact transfer fails; report as such (still a strong, calibrating result for the field).
