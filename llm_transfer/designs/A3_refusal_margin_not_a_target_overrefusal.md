# The refusal margin is a gauge-dependent diagnostic, not a steerable robustness target: steering it up buys over-refusal (the constant classifier), not robustness

## Transferable element (from our paper)
- **Diagnostic, not a trainable target (d)** + **gauge degeneracy** (Lemma ratiodegen): because the ratio
  is scale-invariant, its direct maximizer is the *constant classifier* (predict one class everywhere);
  four first-order attempts to raise eta/L collapse the margin and leave robustness flat or worse.
- Text analog of the constant classifier: the **over-refuser** — a model that refuses everything has a
  huge raw refusal margin M and perfect "safety" on harmful prompts, yet is useless and no more robust in
  the meaningful sense. Raising M by steering/logit-bias is a *gauge move* the ratio R_q = M/L_q ignores.
- **Margin collapse under interventions**: the empirical core is that pushing the diagnostic up does not
  produce robustness; only a genuine adversarial-training-style intervention does.

## Literature gap (specific papers checked + why open)
- **Refusal Tokens (arXiv:2412.06748)** shows refusal rate is *tunable by logit bias / thresholding* —
  i.e. the refusal margin is a knob — but never connects this to robustness, to a gauge-free ratio, or to
  the constant-classifier degeneracy.
- **Arditi et al. (arXiv:2406.11717)** and **RepE/LoRRA (arXiv:2310.01405)** give the refusal-direction
  steering knob but study *inducing/removing* refusal, not the robustness-vs-over-refusal tradeoff of
  *scaling* the margin, nor its gauge status.
- **Over-refusal line (XSTest arXiv:2308.01263, OR-Bench, SCANS arXiv:2408.11491, SafeConstellations
  arXiv:2508.11290)** studies *reducing* over-refusal; nobody frames over-refusal as the *scale-degeneracy
  of maximizing the refusal margin*, nor shows the gauge-free ratio stays flat while the raw margin and
  over-refusal both rise.
- **Logit-Gap Steering (arXiv:2506.24056)** proposes the raw gap as a robustness diagnostic but does not
  test whether *increasing* the gap increases robustness (whether it is a target) — the falsifiable claim
  here.
- **ReFAT (arXiv:2409.20089) / LAT (arXiv:2407.15549)** are the genuine adversarial-training comparators
  (they *do* raise robustness), against which steering must be contrasted. No paper contrasts "steer the
  margin up" vs "adversarially train" through the gauge-free-ratio lens. OPEN.

## Hypothesis (falsifiable)
On one model, sweeping refusal-margin interventions of increasing strength (no training):
1. Increasing steering strength (activation addition along the refusal direction) and/or refusal-token
   logit bias raises the raw refusal margin M monotonically and lowers harmful-prompt compliance under a
   *weak* check, but the strong embedding-attack ASR does NOT fall in proportion to M (and past a point,
   strong-attack robustness is flat/worse while over-refusal explodes).
2. **Gauge flatness**: the gauge-free ratio R_q = M/L_q is approximately invariant under the pure-scaling
   part of the intervention (logit bias / uniform steering), correctly reporting "no robustness gain",
   whereas the raw margin M reports a large spurious gain.
3. **Constant-classifier degeneracy**: at high strength the model collapses to an over-refuser — XSTest
   safe-prompt refusal -> ~1.0, OR-Bench over-refusal -> high, general utility (MMLU/a small helpfulness
   set) -> chance/degraded — the exact analog of the paper's ratio-maximization collapsing to the constant
   classifier at chance accuracy.
4. **Contrast**: a genuine intervention (refusal-feature adversarial ablation at inference, the ReFAT
   direction, or a short ReFAT/LAT fine-tune if compute allows) raises strong-attack robustness *and*
   R_q without the over-refusal blow-up — separating a real robustness gain from a gauge move.
Kill: if strong-attack ASR falls monotonically with M all the way and over-refusal stays low, then the
margin *is* a usable target and the transfer fails (this would be a strong positive result either way).

## Protocol (model, dataset/benchmark, attack/eval incl. STRONG attack, metrics, exact steps)
- **Model**: `meta-llama/Meta-Llama-3-8B-Instruct` (cached). Refusal direction extracted by Arditi's
  mean-difference method on harmful vs harmless activation sets (data prep, single model).
- **Intervention sweep (single run, no model sweep, no training for the main arm)**: steering strength
  alpha in a grid (e.g. 0, 0.5, 1, 2, 4, 8 x the unit refusal direction added to the residual stream at
  the mid layers) and, separately, a refusal-token logit-bias grid (the pure-gauge knob). Optional extra
  arm: inference-time refusal-feature *ablation* (removes refusal) as the opposite end.
- **Strong attack**: Schwinn embedding attack (100 steps, L2 ball) on HarmBench 400 harmful prompts at
  each steering strength; success judged locally (HarmBench Llama-2-13B classifier / Llama-Guard-3-8B).
  Weak check for contrast: direct prompting / single-step embedding perturbation (the FGSM analog).
- **Over-refusal**: XSTest (250 safe + 200 unsafe) and an OR-Bench sample (e.g. 1k) at each strength;
  refusal judged by a keyword+judge combo. Utility: a small MMLU slice (cached `cais/mmlu`) and a short
  helpfulness set to detect the collapse.
- **Diagnostics per strength**: mean refusal margin M, mean L_q, gauge-free ratio R_q; strong-attack ASR;
  weak-attack ASR; XSTest over-refusal; utility.
- **Metrics**: curves of (M, R_q, strong-ASR, over-refusal, utility) vs strength; the divergence between
  M's implied robustness and actual strong-ASR; flatness of R_q under the pure-gauge (logit-bias) arm;
  the strength at which the over-refuser (constant classifier) appears.
- **Steps**: (1) extract refusal direction; (2) for each strength, generate + attack + judge over the
  benchmarks; (3) compute diagnostics; (4) plot the tradeoff; (5) ReFAT/ablation contrast arm.

## Compute estimate (GPU-hours on A6000s)
- No training in the main arm. Per strength: embedding attack on 400 prompts (~3-5 h) + over-refusal/utility
  passes (~1 h). ~6 strengths x 2 knobs -> ~50-70 GPU-h if run naively; prune the logit-bias arm to fewer
  points and reuse clean generations -> **~1.5-2 GPU-days across 2 A6000s**. Optional ReFAT/LAT short
  fine-tune arm: +0.5-1 GPU-day (can be dropped; the inference-time ablation contrast is compute-free).

## Why standalone top-tier (what a reviewer would call the contribution)
"A safety-alignment reality check: the popular idea that a larger refusal margin (or steering harder
toward refusal) means a more robust model is a gauge illusion. We show that inflating the refusal margin
is scale-degenerate — its maximizer is the over-refuser (the constant classifier) — so it raises XSTest
over-refusal and destroys utility without buying robustness against strong attacks, while a gauge-free
threat-matched ratio correctly reports no gain and a genuine adversarial intervention (ReFAT/LAT) does.
Refusal margin is a diagnostic to read, not a dial to turn." This reframes the over-refusal literature
(it is the margin-maximization degeneracy) and warns against margin/steering-based 'robustness',
grounded in a transferred scale-invariance theorem. Venue: ICLR/NeurIPS/ACL/SaTML.

## Risks / kill criteria
- **Steering may degrade coherence** before the clean degeneracy shows; mitigate with mid-layer steering
  at moderate strengths and report the utility curve so the collapse is visible, not confounded.
- **If strong-attack ASR does fall monotonically with M** (margin IS a target), the negative-result framing
  dies — but that positive result (a cheap robustness dial) would itself be publishable; either branch is
  a paper.
- **Two knobs (steering vs logit bias)** must be separated cleanly so the pure-gauge flatness of R_q is
  demonstrable; the logit-bias arm is the cleanest gauge test (it *only* rescales/shifts logits).
- **Judge/keyword over-refusal measurement noise**; use XSTest's standard protocol + a strict judge.
