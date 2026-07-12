# A gauge-free, threat-matched refusal margin-to-sensitivity ratio predicts per-prompt jailbreak vulnerability where the raw logit gap and paraphrase-consistency do not

## Transferable element (from our paper)
- **eta/L, the gauge-free threat-matched ratio** (core). Text analog: per prompt x, margin
  M(x) = (refusal-token logit) - (affirmation-token logit) at the first generated position
  (the "Sure"/"I" gap of Logit-Gap Steering); sensitivity L_q(x) = || d M / d e(x) ||_q, the
  gradient of that margin w.r.t. the input token embeddings e(x), in the dual norm q of the
  embedding-space attack. The diagnostic is the ratio R_q(x) = M(x) / L_q(x).
- **Gauge-freeness** (Lemma ratiodegen). Rescaling the logits f -> c f (equivalently a temperature
  change or a uniform logit-bias scaling) multiplies M and L_q together, leaving R_q invariant.
  The raw margin M is gauge-dependent; the ratio is not.
- **The dissociation (a)**: an *invariance* metric (here paraphrase / format consistency) fails or
  anti-predicts robustness while eta/L predicts it.
- **Per-sample certificate**: R_q(x) is a first-order lower bound on the embedding-space robust
  radius of prompt x, read per prompt (our per-sample section).

## Literature gap (specific papers checked + why open)
- **Logit-Gap Steering (arXiv:2506.24056)** already uses the *raw* refusal-affirmation logit gap to
  predict per-prompt jailbreak success and rank models. It does NOT normalize by a sensitivity term,
  does NOT flag gauge/temperature dependence, does NOT threat-match, and does NOT test paraphrase
  invariance. It is our "margin-alone" baseline, and its own stated open problems (does the gap
  generalize across temperature/families and under adversarial inputs?) are exactly what the gauge-free
  ratio resolves.
- **Refusal Tokens (arXiv:2412.06748)** shows the logit gap is *movable by logit bias* with no model
  change -> direct evidence the raw margin is gauge-dependent and a ratio is needed. No ratio/theory.
- **Gradient Cuff (arXiv:2403.00867) / GradSafe** use the refusal-loss gradient norm *alone* as a
  per-input jailbreak *detector* (adversarial vs benign), not a per-prompt vulnerability predictor over
  clean harmful prompts, and never combine it with a margin into a gauge-free ratio or threat-match it.
- **Fast Proxies (arXiv:2502.10487)** predicts robustness with *attack-based* proxies (direct prompting,
  embedding attacks), not an attack-free forward+one-backward diagnostic, and does not threat-match or
  discuss gauge.
- **Flip-Flop Consistency (arXiv:2510.14242) / Paraphrase-Induced Collapse (arXiv:2605.04665)** define
  paraphrase/format consistency but never relate it to jailbreak vulnerability. Whether consistency
  predicts or anti-predicts adversarial robustness is untested — the flagship open gap (T2).
- No LLM paper forms the gauge-free ratio, proves/【tests】 its gauge-invariance, threat-matches the
  sensitivity to the attack norm, or runs the consistency-vs-ratio dissociation. OPEN.

## Hypothesis (falsifiable)
On one safety-aligned model over a full harmful-prompt benchmark, per prompt:
1. The gauge-free ratio R_q(x) predicts whether a *strong* embedding-space attack succeeds on x
   (AUROC materially above 0.5, and above the raw margin M and above L_q alone).
2. **Gauge test**: apply a logit-scale/temperature transform g (and a refusal-token logit bias, the
   Refusal-Tokens knob). The raw-margin predictor's ranking/threshold shifts (its AUROC or calibrated
   threshold moves with g), while the ratio's ranking is invariant to g. This is the load-bearing claim
   that distinguishes the ratio from Logit-Gap Steering.
3. **Dissociation**: per-prompt paraphrase/format consistency C(x) does NOT predict attack success
   (AUROC ~ 0.5) or anti-predicts it; R_q(x) does. (High-consistency prompts are not the safe ones.)
4. **Threat-matching**: R_2 (L2-dual) predicts the L2-ball embedding attack better than R_inf, and vice
   versa; the mismatched ratio degrades. (Shared with A2 but here as a within-A1 control.)
Kill: if raw M predicts as well as R_q AND is gauge-invariant in practice (2 fails), the ratio adds
nothing; if consistency predicts attack success as well as R_q (3 fails), the dissociation is absent.

## Protocol (model, dataset/benchmark, attack/eval incl. STRONG attack, metrics, exact steps)
- **Model**: `meta-llama/Meta-Llama-3-8B-Instruct` (in HF cache; safety-aligned, open-weight, 8B).
  Robustness cross-check on `Qwen2.5-7B-Instruct` (also cached) is optional and out of the single-run
  scope; primary result is one model.
- **Benchmark (full)**: HarmBench standard behaviors (400) + AdvBench harmful behaviors (520) = 920
  clean harmful prompts. Paraphrases: generate k=8 content-preserving paraphrases/format variants per
  prompt with the same model (or Mistral-7B, cached) at T=0 — this is data prep, not a model sweep.
- **Strong attack (defines the threat & the per-prompt label)**: Schwinn embedding-space attack
  (signed GD, 100 steps, L2 ball radius from their setup), per prompt, on the token embeddings, target
  = affirmative continuation. Success = the generated continuation is judged harmful. Cross-check on a
  256-prompt subset with GCG (nanoGCG, 250 steps) to confirm the label is not attack-specific.
- **Judge (local, no API)**: HarmBench Llama-2-13B classifier OR Llama-Guard-3-8B (download once; fits
  one A6000). Report judge-agreement on a hand-checked 100-sample slice.
- **Diagnostics per prompt (attack-free, one forward + one backward)**: M(x); L_2(x), L_inf(x) (via
  L1/L2 grad norms, dual-matched); R_2 = M/L_2, R_inf = M/L_1; consistency C(x) = fraction of the k
  paraphrases whose greedy response is a refusal (invariance metric); clean refusal indicator; response
  entropy (confidence baseline).
- **Metrics**: AUROC / average-precision of each scalar vs the binary strong-attack-success label;
  Spearman of R_q vs the per-prompt embedding-attack robust radius (the smallest successful L2 budget,
  from a budget ladder); the gauge-shift curve (AUROC vs transform strength g) for M vs R_q;
  bootstrap 95% CIs over prompts; DeLong test for AUROC differences.
- **Steps**: (1) load model + judge; (2) for all 920 prompts compute clean diagnostics (M, grads, C);
  (3) run the embedding attack per prompt at a budget ladder, record success + min successful radius;
  (4) GCG cross-check on 256; (5) apply gauge transforms and recompute predictor AUROCs; (6) correlations,
  DeLong tests, plots.

## Compute estimate (GPU-hours on A6000s)
- Clean diagnostics (fwd+bwd) 920 prompts: < 0.5 h. Paraphrase generation (8x920 gens): ~1-2 h.
- Embedding attack, 100 steps x 920 prompts x ~5 budgets: ~6-12 h on one A6000 (fwd/bwd ~0.15 s at 8B).
- GCG cross-check 256 prompts x 250 steps: ~8-16 h (secondary; can be dropped or run on the 2nd A6000).
- Judge passes + gauge sweep: ~2 h. **Total ~1.0-1.5 GPU-days on a single A6000**; well within 2xA6000.

## Why standalone top-tier (what a reviewer would call the contribution)
"The first *gauge-free* robustness diagnostic for LLMs: the refusal-affirmation logit gap alone is
temperature/logit-bias dependent and therefore not a robustness measure (contra recent logit-gap work),
but its ratio to the threat-matched embedding-gradient norm is scale-invariant and predicts per-prompt
jailbreak vulnerability attack-free — while paraphrase-consistency, an intuitive 'stability' metric,
does not." It unifies the margin line (Logit-Gap Steering) and the sensitivity line (Gradient Cuff)
into one gauge-invariant object, imports a provable invariance property, and delivers a new negative
result (consistency is the wrong signal) plus an attack-free per-prompt vulnerability score. Venue:
NeurIPS/ICLR/USENIX-Sec.

## Risks / kill criteria
- **Margin-side prior**: if the plain raw gap already matches R_q *and* is empirically gauge-stable, the
  ratio's added value is only theoretical -> reframe around the gauge proof + dissociation. Mitigate by
  making the gauge stress-test (logit bias / temperature) the headline, where the raw gap must move.
- **Discreteness**: the certificate/threat-match is cleanest in continuous embedding space; discrete GCG
  is only a cross-check, and a weaker correlation there is expected (state as scope, not failure).
- **Judge noise** could cap AUROC; mitigate with a strict judge + human-checked slice.
- **Refusal direction is not exactly 1-D** (arXiv:2602.02132): we define M on the *output logit gap*
  (robust), not a residual-stream projection, so this does not threaten the metric.
