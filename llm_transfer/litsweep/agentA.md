# Agent A literature sweep — text-side adversarial robustness of LLMs

Lens: jailbreaks / prompt attacks, embedding-space perturbations, certified robustness for
text, margin / Lipschitz diagnostics on logits, representation-space robustness (RepE, LoRRA,
circuit breakers, refusal direction).

Our paper's core, restated for transfer:
- **eta/L**: threat-matched margin-to-Lipschitz ratio = margin / dual-norm gradient. Gauge-free
  (invariant to logit rescaling). Predicts adversarial robustness.
- (a) **dissociation**: an *invariance* metric (shift-consistency) fails / anti-predicts robustness
  while eta/L predicts it.
- (b) **exact certificate count**: in the locally-affine regime robust accuracy = certified fraction
  (the per-sample first-order radius clears the budget).
- (c) **"invariance helps robustness" is a weak-attack artifact**: FGSM survives, AutoAttack kills.
- (d) **diagnostic, not a trainable target**: gauge degeneracy (scale-invariance -> constant classifier);
  margin collapse under first-order attempts to raise the ratio.
- (e) **budget-normalized eta/(L*eps)** collapses robustness across attack budgets.

## Candidate transfers (labels used in the table below)
- **T1** gauge-free threat-matched refusal margin-to-sensitivity ratio M/L_q as a robustness diagnostic
  (margin = refusal-vs-affirmation logit gap; L_q = embedding-space gradient norm in the attack's dual norm).
- **T2** the dissociation: an *invariance* metric (paraphrase / format consistency) fails/anti-predicts
  jailbreak robustness while M/L_q predicts it.
- **T3** certified-fraction = ASR law; attack-free ASR-vs-budget curve from the per-prompt first-order
  certificate; budget-normalization collapse.
- **T4** threat-matching (dual norm) for LLM embedding-space attacks (L2 vs Linf ball).
- **T5** representation / "invariance" defenses (circuit breakers, RepE, equivariance-style) look robust
  under weak attacks, collapse under strong/adaptive attacks (the (c) transfer).
- **T6** M/L_q is a diagnostic, NOT a steerable/trainable target: gauge degeneracy => the over-refuser
  is the "constant classifier"; steering the refusal margin up buys over-refusal not robustness.
- **T7** per-prompt coupling (margin vs input/embedding-gradient norm) and its inversion under
  refusal-feature adversarial training.

Verdict codes per paper: BLOCKS / PARTIAL (covers a piece, sharpens novelty) / OPEN (leaves transfer open)
/ ENABLES (tool or benchmark we can build on).

---

## A. Strong attacks (define the "AutoAttack" analog for text)

**Zou et al. 2023, "Universal and Transferable Adversarial Attacks on Aligned Language Models" (GCG),
arXiv:2307.15043.** White-box greedy-coordinate-gradient discrete suffix attack; breaks aligned
LLMs, transfers. -> ENABLES the strong-attack per-prompt outcome; the discrete-token analog of a
strong Lp attack. T3/T4: discrete, so a clean norm-ball certificate is awkward on it (use as
cross-check, not the primary metric).

**Schwinn, Dobre, Xhonneux, Gidel, Gunnemann 2024, "Soft Prompt Threats: Attacking Safety Alignment
and Unlearning through the Embedding Space", NeurIPS 2024, arXiv:2402.09063 (code SchwinnL/
LLM_Embedding_Attack).** Continuous embedding-space attack: signed GD, ~100 steps, constrained to an
L2 ball; far more efficient than discrete; ~8.8 fwd/bwd to trigger on average. -> ENABLES the
*continuous* strong attack with an explicit L2 budget — this is the clean "threat model" for T1/T3/T4
(a real norm ball in embedding space, so the certificate M/L_q >= eps is well-posed). Does NOT define
a margin/Lipschitz diagnostic. OPEN for T1/T3/T4.

**Andriushchenko, Croce, Flammarion 2024, "Jailbreaking Leading Safety-Aligned LLMs with Simple
Adaptive Attacks", ICLR 2025, arXiv:2404.02151 (tml-epfl/llm-adaptive-attacks).** Adaptive random
search on a suffix maximizing logprob of "Sure"; 100% ASR across many models; argues defenses must be
evaluated against *adaptive* attackers, not static/weak ones. -> Directly the (c) methodology point
(weak vs strong). PARTIAL BLOCK for T5 as a bare "defenses collapse" claim — that is now established.
Our T5 must add the *predictive diagnostic*, not re-demonstrate collapse.

**Nasr et al. 2025 (OpenAI/Anthropic/GDM), "The Attacker Moves Second: Stronger Adaptive Attacks
Bypass Defenses Against LLM Jailbreaks and Prompt Injections", arXiv:2510.09023 (USENIX Sec'26).**
NONE of the evaluated jailbreak/prompt-injection defenses withstand strong adaptive attacks. ->
BLOCKS a bare "defense X is a weak-attack artifact" paper: the field already knows defenses collapse.
Sharpens T5 to *only* the diagnostic angle (predict, per-prompt, which apparent robustness survives).

**Mehrotra et al. 2023, "Tree of Attacks (TAP)"; Chao et al. 2023, "PAIR"; Liu et al. 2023
"AutoDAN".** Black-box / semantic jailbreaks. -> ENABLES additional attack outcomes; secondary.

## B. The margin side (refusal-vs-affirmation logit gap) — closest prior to our numerator

**"Logit-Gap Steering: A Forward-Pass Diagnostic for Alignment Robustness", arXiv:2506.24056.**
Defines the refusal-affirmation logit gap and uses it (b) to predict per-prompt jailbreak success and
(c) to rank models by robustness. Does NOT normalize by any gradient/Lipschitz term (no gauge-free
ratio); does NOT discuss temperature/scale (gauge) dependence as a limitation; does NOT threat-match;
does NOT relate to paraphrase/format invariance. -> PARTIAL for T1 (raw margin already predicts) but
this is exactly our "margin alone is gauge-dependent" baseline. Our novelty = the gauge-free ratio
M/L_q, gauge-dependence of the raw gap, threat-matching, and the invariance dissociation (T2). Their
own open questions (generalization across temperature/families, behavior under adversarial inputs) are
what the ratio answers. STRONGEST prior to differentiate against; not a blocker for the ratio.

**"Refusal Tokens: A Simple Way to Calibrate Refusals in LLMs", arXiv:2412.06748.** Refusal-token
softmax probability is a tunable confidence: thresholding / logit bias moves the refusal rate without
retraining. -> ENABLES/PARTIAL for T6 and the gauge argument: the logit gap is explicitly *movable by
logit bias* (a gauge/temperature knob) with no change to the underlying model — direct evidence that
the raw margin is gauge-dependent and the ratio is the invariant object. Does not form a ratio or a
robustness theory. OPEN for T1/T6.

**"Beyond Attack Success Rate: Temporal Logit Observability for LLM Safety Failures",
arXiv:2605.29629.** Logit-Margin Score (LMS) = compliance-refusal balance per decoding step, a passive
temporal diagnostic. -> PARTIAL for the margin definition (per-step margin exists); no ratio, no gauge,
no threat-matching. OPEN for T1.

**"The Instability of Safety: How Random Seeds and Temperature Expose Inconsistent LLM Refusal
Behavior", arXiv:2512.12066.** 18-28% of harmful prompts flip refuse/comply across sampling configs;
instability rises with temperature. -> Motivates T1/T6 (raw refusal decisions are scale/temperature
fragile) but studies *sampling* instability, not a gauge-free logit-margin ratio. OPEN.

**"Safety Instincts", arXiv:2510.01088; "From Confidence to Collapse", arXiv:2508.16267.** Aligned
LLMs are more confident (lower entropy) when refusing than when producing harmful content. -> Confidence
~ margin correlates with safety, consistent with our numerator; none forms the gauge-free ratio. OPEN.

## C. The sensitivity side (gradient norm of refusal loss) — closest prior to our denominator

**Hu, Chen, Ho et al. 2024, "Gradient Cuff: Detecting Jailbreak Attacks by Exploring Refusal Loss
Landscapes", NeurIPS 2024, arXiv:2403.00867.** Refusal loss = 1 - P(refuse). Two-step *per-input
detector*: threshold the refusal-loss value, then its gradient norm (jailbreak inputs have smaller
value, larger gradient norm). Tested on LLaMA-2-7B-Chat, Vicuna-7B vs 6 attacks. -> PARTIAL/closest
prior for the denominator L. But: it is a per-INPUT detector on (already) adversarial vs benign inputs,
NOT a per-model robustness ranking; it uses the gradient norm ALONE (no margin numerator, no ratio);
it does NOT threat-match, does NOT discuss gauge, and does NOT predict which *clean harmful* prompts an
attacker will succeed on. Our T1 (ratio over clean harmful prompts, threat-matched, gauge-free) is
distinct. Not a blocker.

**"GradSafe: Detecting Jailbreak Prompts via Safety-Critical Gradient Analysis", 2024.** Jailbreak
prompts + harmful response produce characteristic gradients on safety-critical parameters; training-free
detector. -> PARTIAL for the denominator idea (gradient signal predicts harm); parameter-space, per-input
detection, no margin/ratio/gauge/threat-matching. OPEN for T1.

**Kim, Papamakarios, Mnih 2021, "The Lipschitz Constant of Self-Attention", ICML, arXiv:2006.04710.**
Standard dot-product self-attention is NOT Lipschitz (softmax over scores); proposes L2-MHA. Follow-ups:
"Pay Attention to Attention Distribution: A New Local Lipschitz Bound", arXiv:2507.07814; "Certifiably
Robust Transformers with 1-Lipschitz Self-Attention". -> IMPORTANT CAVEAT: a *global* Lipschitz constant
for a transformer is not available/finite. This BLOCKS a global-Lipschitz certificate but NOT the
paper's actual quantity: our L is the *empirical local input/embedding-gradient norm* (mean ||grad M||),
which is exactly what our experiments use and is well-defined for any model. Use local gradient norm,
state the caveat.

## D. Certified / smoothing defenses for text (the "certified fraction" analog)

**Kumar et al. 2023, "Certifying LLM Safety against Adversarial Prompting" (erase-and-check),
arXiv:2309.02705 (aounon/certified-llm-safety).** Erase tokens, run a safety filter on subsequences;
verifiable guarantee up to an adversarial-suffix size. -> PARTIAL for T3: a certificate exists but it
is combinatorial over token deletions (an L0/edit budget), not a first-order margin certificate. Our
T3 in *embedding space* (continuous L2) is the missing continuous analog. OPEN for T3.

**Robey et al. 2023, "SmoothLLM", arXiv:2310.03684.** Randomized character perturbations + majority
vote; robust to GCG-style brittle suffixes. -> PARTIAL: randomized-smoothing analog; no per-prompt
first-order certificate count, no eta/L. OPEN for T3.

## E. Representation-space defenses & the refusal subspace (the "invariant subspace" analog)

**Zou et al. 2024, "Improving Alignment and Robustness with Circuit Breakers", arXiv:2406.04313.**
Reroutes harmful representations; lowers ASR of unseen single-turn attacks to ~3.8%. -> the "invariance/
representation defense helps robustness" claim. Subsequently broken: see below.

**"Revisiting the Robust Alignment of Circuit Breakers", arXiv:2407.15902; Best-of-N jailbreaking
(52% ASR on circuit breakers); "Obfuscated Activations Bypass LLM Latent-Space Defenses",
arXiv:2412.09565.** Representation-level defenses fall to stronger/adaptive attacks. -> These, with
Nasr 2025, mean T5 as "the representation defense is a weak-attack artifact" is largely COVERED. T5 is
only worth doing as a *diagnostic* claim (M/L_q predicts the collapse), else BLOCKED.

**Zou et al. 2023, "Representation Engineering (RepE)" + LoRRA, arXiv:2310.01405.** Reads/controls
concepts along representation directions; LoRRA = low-rank representation adaptation for honesty/safety.
-> the representation-direction machinery for defining the refusal subspace / margin. ENABLES A3.

**Arditi et al. 2024, "Refusal in LLMs Is Mediated by a Single Direction", NeurIPS 2024,
arXiv:2406.11717 (andyrdt/refusal_direction).** Refusal is a 1-D residual-stream direction; ablating it
removes refusal, adding it induces refusal; reproduced 1.8B-72B. -> ENABLES A3's steering knob and a
representation-space definition of the refusal margin (projection onto the refusal direction). This is
the direct "invariant subspace / projection margin" analog of Theorem A.

**"There Is More to Refusal in LLMs than a Single Direction", arXiv:2602.02132; "LLMs Encode
Harmfulness and Refusal Separately", arXiv:2507.11878.** Refinements: multiple refusal-relevant
directions; harmfulness and refusal are separate. -> CAVEAT for the 1-D framing; define the refusal
margin on the output logit gap (robust) and optionally cross-check the residual-stream projection.

**"Robust LLM Safeguarding via Refusal Feature Adversarial Training (ReFAT)", ICLR 2025,
arXiv:2409.20089.** Adversarial training that stochastically ablates the refusal feature during
training; ASR 53%->10% (Llama3-8B). -> ENABLES A3's "genuine adversarial-training" comparator and T7:
the LLM analog of PGD-AT for the refusal subspace, against which we test coupling inversion.

**Sheshadri et al. 2024, "Latent Adversarial Training (LAT/TLAT) Improves Robustness to Persistent
Harmful Behaviors", arXiv:2407.15549.** Adversarial perturbations to hidden latents during training.
-> ENABLES/T7 alternative adversarial-training axis.

## F. The invariance metric (paraphrase / format consistency) — the "shift-consistency" analog

**"Flip-Flop Consistency: Unsupervised Training for Robustness to Prompt Perturbations",
arXiv:2510.14242.** Trains for consistency of outputs across content-preserving prompt variants;
defines a consistency metric. -> ENABLES the invariance metric for T2. Does NOT relate consistency to
adversarial/jailbreak robustness. OPEN for T2.

**"Paraphrase-Induced Output-Mode Collapse", arXiv:2605.04665.** Semantically-equivalent inputs flip
model behavior (format/mode collapse) — an invariance-failure taxonomy. -> ENABLES the invariance
metric; not linked to adversarial robustness. OPEN for T2.

**Paraphrase-as-attack and paraphrase-as-defense line (Robust Prompt Optimization arXiv:2401.17263;
paraphrase defenses).** Paraphrasing both attacks safeguards and defends against brittle suffixes. ->
Shows paraphrase-robustness and adversarial-robustness are entangled but NOBODY has tested whether a
per-prompt *paraphrase-consistency* metric predicts (or anti-predicts) jailbreak vulnerability while a
margin/sensitivity ratio predicts it. T2 OPEN — this is the flagship gap.

## G. Robustness-evaluation proxies / methodology

**Schwinn group 2025, "Fast Proxies for LLM Robustness Evaluation", arXiv:2502.10487.** Direct
prompting, prefilling, and embedding-space attacks as cheap proxies for a 6-attack ensemble; direct
prompting Spearman 0.94, embedding Pearson 0.87 across 33 models. -> PARTIAL/closest methodology prior.
Uses *attack-based* proxies, NOT a margin/Lipschitz diagnostic; explicitly does NOT threat-match, does
NOT discuss gauge invariance, does NOT budget-normalize. Their limitation (>10B untested) and their
attack-based framing are exactly what an attack-free gauge-free eta/L adds. Not a blocker for T1/T3/T4.

**Peng et al. 2024, "Navigating the Safety Landscape: Measuring Risks in Finetuning LLMs" (safety
basin, VISAGE), NeurIPS 2024, arXiv:2405.17374.** Safety is flat in a *weight-space* basin then drops
sharply; VISAGE metric. -> Related "landscape" framing but in WEIGHT space, not input/embedding space.
Leaves the input-space margin/sensitivity diagnostic OPEN; a nice contrast (weight basin vs input ratio).

**Souly et al. 2024, "A StrongREJECT for Empty Jailbreaks", arXiv:2402.10260 (dsbowen/strong_reject).**
High-quality forbidden-prompt benchmark + evaluator; existing auto-evaluators OVERSTATE jailbreak
success; local judge = finetuned Gemma-2B. -> ENABLES a LOCAL (no-API) judge and directly supports the
(c) "weak eval overstates robustness/success" theme.

**Mazeika et al. 2024, "HarmBench", ICML, arXiv:2402.04249 (centerforaisafety/HarmBench).** Standardized
red-teaming; 400 behaviors; local Llama-2-13B classifier judge; efficient adversarial-training baseline
(R2D2). -> ENABLES the benchmark + a LOCAL judge; the "standardized strong attack" venue.

**JailbreakBench (arXiv:2404.01318); AdvBench (520 behaviors, from GCG paper); XSTest (arXiv:2308.01263,
250 safe + 200 unsafe); OR-Bench (80k over-refusal prompts).** -> ENABLE benchmarks: AdvBench/HarmBench
for attack outcomes, XSTest/OR-Bench for over-refusal (A3).

---

## Bottom line for design
- **Both individual terms already exist in the LLM literature and are each gauge-dependent**: the
  refusal-affirmation logit gap (Logit-Gap Steering, LMS, Refusal Tokens) is the margin; the refusal-loss
  gradient norm (Gradient Cuff, GradSafe) is the sensitivity. NOBODY forms the gauge-free threat-matched
  RATIO, threat-matches the sensitivity to the attack norm, budget-normalizes it, or runs the invariance
  (paraphrase-consistency) dissociation. This is precisely the vision-paper situation (margin alone and
  Lipschitz alone are gauge-dependent; the ratio is the object) reproduced in text. -> T1, T2, T3, T4, T6 OPEN.
- **T5 (weak-attack artifact) is largely BLOCKED** as a bare claim by Nasr 2025 + circuit-breaker-breaking
  papers; only survives as a *diagnostic* sub-result folded into T1.
- **Global-Lipschitz certificates are BLOCKED** (self-attention not Lipschitz); use the *local empirical
  embedding-gradient norm* exactly as the vision paper uses mean ||grad M||. State the caveat.
- The 1-D refusal direction (Arditi) is the clean "invariant subspace / projection margin" analog;
  caveat it with "more than one direction" refinements by defining the margin on the output logit gap.
