# Prompt Consistency Is Not Robustness: A Threat-Matched Margin-to-Sensitivity Law for LLMs

## Transferable element (from our paper)
- (a) The dissociation: an invariance metric (shift-consistency) does NOT order adversarial robustness and can
  anti-predict it; the exactly invariant operator has perfect consistency yet the lowest robustness via margin
  collapse.
- (b) The gauge-free threat-matched ratio η/L (margin ÷ sensitivity measured in the attack's dual norm) predicts
  robustness instead.
- (c) Theorem 1 form: the invariant margin is the separation of representations projected onto the invariant
  subspace via the group-average projector — here the paraphrase/format/order ORBIT-AVERAGE.

LLM instantiation. Fix ONE base model. Build a panel of prompt "operators" = semantically-equivalent transformations
of the same task input (FormatSpread-style format variants; option-order permutations; paraphrase rewrites), i.e.
different points/aggregations on the transformation orbit. For each operator measure (i) an INVARIANCE metric
(agreement across the orbit), (ii) adversarial robustness under a STRONG attack, and (iii) the threat-matched
margin-to-sensitivity ratio η/L. Test which of (i) or (iii) orders (ii).

## Literature gap (specific papers checked + why open)
- FormatSpread (Sclar et al., ICLR 2024, arXiv:2310.11324) measures format sensitivity (up to 76-pt spread) but
  treats it as evaluation noise, never as a robustness predictor and never against an adversarial axis.
- "LLMs Are Not Robust MC Selectors" (Zheng et al., ICLR 2024, arXiv:2309.03882) and "Mind Your Format" (Voronov
  et al., 2024, arXiv:2401.06766) quantify order/template invariance and even do orbit-averaging (PriDe, template
  ensembles) but never correlate with adversarial robustness.
- "Automated Consistency Analysis" (arXiv:2502.07036) states semantic consistency ⊥ accuracy — the dissociation
  logic — but has no adversarial axis and no margin.
- Logit-Gap Steering (arXiv:2506.24056) defines and validates the refusal/answer logit-gap margin as a forward-pass
  predictor, but never adds a Lipschitz denominator, never threat-matches, and never touches the invariance axis.
- Soft-Prompt/embedding attacks (Schwinn et al., NeurIPS 2024, arXiv:2402.09063) give the differentiable threat but
  are used only to attack safety, never to compute a margin-to-Lipschitz predictor across invariance operators.
- Kim et al. (ICML 2021, arXiv:2006.04710): global self-attention Lipschitz is undefined → we must and do use the
  local per-input embedding-gradient norm, matching our paper's practice.
None of these cross an invariance metric with adversarial robustness on shared models under a margin-to-sensitivity
law. Open.

## Hypothesis (falsifiable)
Across the operator panel on one model, at fixed clean task accuracy:
- H1 (null of the field): prompt/format/order/paraphrase CONSISTENCY does NOT rank adversarial robustness
  (|Pearson| < 0.4, CI crossing 0); and the maximally-invariant operator (orbit-marginalized / consistency-tuned)
  is among the LEAST robust.
- H2 (our law): the threat-matched ratio η/L₂ᵉᵐᵇ = (answer/refusal logit margin) ÷ (embedding-space ∥∇margin∥₂)
  ranks per-operator adversarial robustness with Pearson ≥ +0.7, and per-PROMPT η/L predicts per-prompt attack
  radius (Spearman ≥ +0.7), mirroring the +0.998/per-sample results in the vision paper.
Kill: if consistency already ranks robustness ≥ +0.7, the dissociation does not transfer.

## Protocol (model, dataset/benchmark, attack/eval incl. STRONG attack, metrics, exact steps)
- Model (local cache): `Qwen2.5-7B-Instruct` (primary; also present: `Meta-Llama-3-8B-Instruct`,
  `Ministral-8B-Instruct-2410` for an appendix cross-check — NOT a sweep, one primary model reported).
- Task benchmark (FULL, local): `cais/mmlu` (all 14k test items) as the discriminative task, plus `sst2` and
  `rotten_tomatoes` (local) as binary-margin tasks where the logit margin is cleanest. Adversarial-prompt attack
  suite from PromptBench (arXiv:2306.04528) protocol for task-accuracy attacks.
- Operators (the "arms", all on ONE model, no weight change except the one imposed-invariance arm):
  1. canonical template; 2–4. FormatSpread format variants; 5. option-order-permuted (MCQ) / paraphrased input;
  6. ORBIT-MARGINALIZED operator (majority-vote / logit-average over the whole format+order orbit = the
     group-average projector, the "exactly invariant" analog, à la template-ensemble / PriDe);
  7. (optional strengthening) a LoRA fine-tuned for output-consistency across the orbit (imposed invariance, the
     truest "exact-invariant" arm) — one short LoRA, not a sweep.
- Invariance metric per operator: agreement rate of the prediction across the orbit (1 − FormatSpread spread);
  for the marginalized/LoRA arms, invariance = 1 by construction (the perfect-consistency, least-robust prediction).
- STRONG attack (threat, per operator): (a) embedding-space attack (Schwinn et al.) — differentiable, budgeted
  ∥δ∥₂ on input embeddings, report per-prompt minimum-norm flip radius r (our r₂ analog) via a DDN-style search;
  (b) GCG discrete suffix (arXiv:2307.15043) on a 200-item subset as the discrete cross-check (AutoAttack analog);
  (c) PromptBench word/char attacks for the task-accuracy operators. Report attack success at matched budget AND
  per-prompt radius; verify no "masking" (embedding radius vs GCG agreement, à la our DDN-vs-AutoAttack check).
- Margin/sensitivity: M(x) = correct-class logit − max wrong-class logit (tasks) or refusal−affirmation gap
  (safety appendix); η = E[M]; L = E∥∇_emb M∥₂ (threat-matched to the embedding attack), plus ∥∇_emb M∥₁ for a
  mismatched control. η/L is the predictor; gauge-free (temperature-invariant) — verify by rescaling logits.
- Metrics: Pearson/Spearman of {consistency, η/L, clean-acc} vs {attack radius, ASR} over operators (bootstrap CIs
  over prompts); per-prompt Spearman of η/L vs radius; partial correlation of η/L vs robustness controlling for
  clean accuracy (the "beyond clean accuracy" test).
- Judge: none needed for tasks (exact-match). Safety appendix uses local HarmBench classifier / DeBERTa-zeroshot.
  No paid API anywhere.

## Compute estimate (GPU-hours on A6000s)
Embedding attacks: ~0.5–2 s/prompt × ~15k prompts × ~6 operators ≈ heavy but parallel over 2 GPUs ≈ 20–30 h.
GCG subset (200 items × few operators, ~2–5 min each) ≈ 15–25 h. Forward-pass margin/consistency over full MMLU ≈
5 h. Optional consistency LoRA ≈ 3–5 h. Total ≈ 45–65 GPU-h; core result (embedding attack + margins, no GCG) ≈ 30 h.

## Why standalone top-tier (what a reviewer would call the contribution)
First demonstration that the invariance/consistency metrics the entire prompt-robustness field reports
(FormatSpread, order-bias, template spread) are ORTHOGONAL-to-ANTI-correlated with true adversarial robustness of
LLMs, and that a single gauge-free, attack-free forward-pass diagnostic (threat-matched margin ÷ embedding-gradient)
predicts it — including out-of-sample and beyond clean accuracy. It reframes "prompt consistency" from a robustness
proxy to a robustness NON-signal, and hands practitioners a cheap selection rule. Clean, surprising, and
mechanistic; not an addendum (it stands on the LLM logit-gap/embedding-attack literature, citing our theory only for
the η/L framing).

## Risks / kill criteria
- Risk: on discriminative TASKS the "refusal margin" analog is just the class-logit gap; fine, but a reviewer may
  want the safety domain — keep safety as an appendix (fully covered by B3).
- Risk: embedding-attack radius could correlate with clean accuracy, confounding η/L. Mitigate with the partial
  correlation (our paper's fix) and the constant-clean-accuracy operator design (all operators share the base
  model's accuracy up to format effects).
- Kill: if consistency ranks robustness ≥ +0.7 with tight CI (dissociation fails), OR if η/L is a pure restatement
  of clean accuracy (partial correlation → 0). Report either honestly; the null on consistency is itself publishable
  given the field's assumption to the contrary.
