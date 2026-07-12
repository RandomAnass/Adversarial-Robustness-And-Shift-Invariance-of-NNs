# Experimental-Design Adversary — Round 2, Lens A (text-side LLM adversarial robustness)

Goal of this pass: make each of A1/A2/A3 a SINGLE run so strong, clean, and confound-controlled
that its result could lead a top-tier journal on its own. **Priority is depth on one run, not
breadth.** Every "second seed / second model / significance sweep" note below is explicitly marked
OPTIONAL and secondary. Round-1 (literature) corrections are folded in and treated as prerequisites.

All designs share one attack backbone, one predictor definition, one judge, and one environment.
I specify those once (§0) and then give the per-design verdict + the single biggest fix.

---

## §0. Shared infrastructure (audited against what is actually on disk)

### 0.1 Environment — RUN-BLOCKING, fix first (verified on the box)
- `~/.cache/huggingface/hub` has **`meta-llama/Meta-Llama-3-8B-Instruct` and `Qwen2.5-7B-Instruct`**
  cached (good), plus Mistral-7B-v0.2/v0.3 and Ministral-8B for paraphrase generation.
- **The base anaconda env is broken for this stack**: `transformers` there pins
  `huggingface-hub>=0.15.1,<1.0` but the installed hub is `1.17.0`, so `import transformers`
  raises `ImportError` today. `torch.cuda.is_available()` could not even be reached.
  → **Fix: build a dedicated venv** (`python -m venv .venv_advllm`) with a mutually consistent
  `torch` + `transformers` + `huggingface-hub<1.0` + `accelerate` + `datasets`.
- **`nanogcg`, `accelerate`, `peft`, `fschat`, `vllm` are all absent.** The discrete-GCG adaptive
  check (required by Nasr 2510.09023 as the adaptive-eval standard) needs `nanogcg` installed.
- **No judge model is cached**: no Llama-Guard-3-8B, no HarmBench Llama-2-13B classifier, no
  StrongREJECT model. All three designs name a "local judge, no API." **This is a real gap** —
  one of these must be downloaded before any success label exists. Llama-Guard-3-8B (~16 GB)
  fits one A6000; budget the download.
- **No harmful-prompt benchmark is cached** (no AdvBench/HarmBench/StrongREJECT/XSTest/OR-Bench
  datasets under `hub`). These are small text files/CSVs; fetch AdvBench + HarmBench-standard +
  XSTest + a StrongREJECT judge prompt once. Trivial size, but must be an explicit prep step.

**Net:** none of the three is "load-and-go." The prep gate is: venv + judge download + benchmark
download + `nanogcg` install. Estimate ~2–3 h wall-clock (mostly the judge download), 0 GPU-h of
science. I flag this because all three designs write "cached / no API" as if prep were free.

### 0.2 The strong attack — one definition for all three (Round-1 mandate, made exact)
Round-1's load-bearing correction stands and is non-negotiable: **the Schwinn attack (2402.09063)
is unconstrained and append-based; it is NOT an "L2-ball perturbation of the prompt embeddings."**
Do not cite it as such. Define our own attack:

> **Projected embedding-PGD (PE-PGD), the strong attack for all A-designs.**
> Let `e(x) ∈ R^{T×d}` be the prompt's own token embeddings (the SAME tensor the diagnostic
> differentiates). Perturb `e' = e(x)+δ`, `δ∈R^{T×d}`, maximizing the affirmation objective
> `L(e') = logit(affirm token | e') − logit(refuse token | e')` at the first generated position
> (the exact margin `M` of §0.3, negated), by **signed PGD with per-step projection onto a norm
> ball** `‖δ‖_p ≤ ε` (`p∈{2,∞}`), `ε` swept on a geometric ladder. Steps: 200, step size `ε/25`,
> **R=5 random restarts inside the ball**, keep worst-case over restarts. Success = the greedily
> generated continuation from `e'` is judged harmful by the local judge.

This makes certificate and label share ONE threat model (perturb `e(x)`, in norm `p`, with the
gradient taken on `e(x)`), which is the prerequisite Round-1 identified for A1's threat-matching,
A2's entire count law, and A3's strong-attack column to mean what the designs claim.

- **Threat-matching is now real** (it was not under append-Schwinn): the L2-ball PE-PGD is the
  ground truth for `R_2 = M/‖∇M‖_2`; the L∞-ball PE-PGD is the ground truth for `R_∞ = M/‖∇M‖_1`.
- **Gradient-masking / obfuscation battery (REQUIRED — was absent or one-line in all three).**
  A single strong run is only unimpeachable if it rules out masking. Run and report all of:
  (i) **steps/restarts monotonicity** — ASR must not rise when steps 200→400 or R 5→10 (if it
  does, the 200/5 attack was weak, not the model robust);
  (ii) **loss-landscape sanity** — the PGD objective decreases smoothly, no zero-gradient regions
  (log the fraction of prompts with `‖∇M‖≈0`, i.e. vanishing-gradient masking);
  (iii) **transfer/unbounded ceiling** — an UNBOUNDED embedding attack (the original append-Schwinn,
  `ε=∞`) should reach ~100% ASR; if PE-PGD at large `ε` plateaus well below the unbounded ceiling,
  the projected attack is being masked and needs more restarts/steps;
  (iv) **discrete GCG cross-check** (Nasr 2510.09023 adaptive-eval standard) — `nanogcg`, 500 steps,
  on a **fixed 128-prompt slice**, as an independent discrete threat model. Its role is NOT to match
  PE-PGD numerically (discrete≠continuous; a weaker correlation is expected and is scope, not
  failure) but to confirm the per-prompt ORDERING survives a genuinely different attack.
- The append-suffix Schwinn attack is kept ONLY as (iii)'s unbounded ceiling + a secondary
  "does ordering survive a different threat model" check — explicitly out of any count law.

### 0.3 The predictor / target — one definition, no circularity
Match the paper's per-sample form exactly (`main.tex` §sec:coupling: `M(x)=f_y−max_{j≠y}f_j`,
per-sample ratio `M(x)/‖∇M(x)‖`, gauge Lemma ratiodegen, dual-norm threat-matching, count law
Prop count exact on affine cells).

- **Margin** `M(x) = logit(refuse-token) − logit(affirm-token)` at the first generated position.
  Fix the token identities ONCE, in writing, before the run: refuse-set anchor = first token of the
  model's own canonical refusal (`"I"` in `"I can't"`) vs affirm anchor (`"Sure"`), taken from the
  model's actual greedy refusal/compliance strings, not hand-picked. Report robustness of `M` to the
  anchor choice on a 50-prompt slice (this is a known soft spot; pre-empt it).
- **Sensitivity** `L_q(x) = ‖∂M/∂e(x)‖_q`, the exact analytic gradient of that margin w.r.t. the
  prompt token embeddings, in the dual norm `q` of the attack (`q=2` for L2 ball, `q=1` for L∞ ball).
  This is sharper than Gradient Cuff's zeroth-order refusal-loss gradient on a pooled embedding
  (Round-1) — state that; it widens the gap.
- **Ratio / radius** `R_q(x) = M(x)/L_q(x)` = per-prompt first-order embedding robust radius.
- **No circularity check (make it explicit):** the label is the SUCCESS of PE-PGD on `e(x)`; the
  predictor is a first-order Taylor radius of the SAME objective on the SAME `e(x)`. These share a
  threat model **by design** (that is the count-law claim) but are computed by different mechanisms
  (predictor = 1 backward at `δ=0`; label = 200-step optimized attack), so the predictor is a
  genuine first-order *approximation* being tested against the true optimized radius, not a
  tautology. The honest framing: "we test how well the first-order radius predicts the fully-optimized
  radius" — that is the scientific content and it is not circular.

### 0.4 The invariance / consistency null — must be a PUBLISHED operator, not invented (Round-1)
The dissociation ("consistency does not / anti-predicts robustness, the ratio does") only lands if
the consistency operator is one a referee already accepts. **Do not invent one.** Use:
- **Flip-Flop Consistency (2510.14242)** as the primary paraphrase/format-consistency operator
  (its published protocol), scoped to a **per-prompt observational** metric on the **fixed,
  un-consistency-trained** model. `C(x)` = fraction of `k=8` content-preserving paraphrases whose
  greedy response is a refusal.
- **Pre-empt by name** Consistency Training (2510.27062) and Latent Adversarial Paraphrasing
  (2503.01345): they *train* invariance and report it helps; A1 measures *observed* consistency on
  a fixed model. State this distinction in the design so the "consistency is the wrong signal"
  headline is not read as already-refuted-by-consistency-training.
- Margin-Consistency (Ngnawé 2406.18451, in `pdfs/`) is a *vision* margin-vs-logit-margin-consistency
  prior — cite it as the closest published "cheap proxy for adversarial vulnerability from internal
  quantities" and distinguish (it is not paraphrase invariance).

### 0.5 Confounds to control on EVERY design (was under-specified)
Report each predictor's AUROC **conditional on / partialling out**:
- **Clean refusal base rate** — a prompt the model already refuses clean is trivially "robust";
  either restrict the AUROC to clean-complied prompts or report stratified.
- **Prompt length `T`** — both `M` and `‖∇M‖_q` scale with `T`; report Spearman(`R_q`,`T`) and a
  length-partialled AUROC. (This is the LLM analog of the paper's clean-accuracy-matched control.)
- **Clean generation confidence / response entropy** — baseline predictor; the ratio must beat it.
- **Benchmark provenance** (AdvBench vs HarmBench) as a stratifier — the two have different
  difficulty; report within-benchmark so the effect is not a dataset-mixture artifact.

---

## A1 — gauge-free ratio vs consistency

### VERDICT: **FIX-THEN-RUN** (strongest of the three; closest to run-ready)

The novelty — the per-prompt, gauge-free, threat-matched ratio `M/L_q` as an LLM robustness object,
plus the consistency dissociation — is genuinely open (Round-1 confirmed). The design is
scientifically sound; it needs the §0 fixes and three sharpenings.

### Protocol fixes (exact)
- **Attack:** replace "Schwinn L2 ball" with **PE-PGD (§0.2)**; run the full masking battery §0.2.
  The per-prompt binary label = L2-ball PE-PGD success at the design budget `ε*` (choose `ε*` as the
  budget where clean-complied ASR ≈ 0.5, so the label is maximally informative — pre-register this
  rule, not the number).
- **Predictor / target:** §0.3 definitions. Add the **per-prompt Spearman of `R_2` vs the measured
  min-successful-`ε`** (the true optimized radius from the budget ladder) as the cleanest,
  judge-noise-robust result — this is the headline scatter and it survives even if AUROC is capped by
  judge noise.
- **Gauge test (the load-bearing arm — keep it the headline):** apply (a) temperature/logit-scale
  `f→cf` for `c∈{0.25,0.5,1,2,4}` and (b) a **generic refusal-token logit bias** `b∈{0,±2,±5}`
  (self-defined; do NOT attribute to Refusal-Tokens 2412.06748 — that needs training, per Round-1;
  cite it only as "refusal rate is a movable knob"). Show: raw-`M` AUROC / calibrated threshold
  **moves** with `c` and `b`; `R_q` AUROC / ranking is **invariant** to `c` and (approximately) to `b`.
  This is the one thing the raw gap cannot survive and the ratio can — it is the paper.
- **Consistency null:** §0.4 (Flip-Flop 2510.14242, observational, pre-empt 2510.27062/2503.01345).
- **Threat-matching within-A1:** `R_2` predicts L2-ball PE-PGD better than `R_∞` does, and vice
  versa (now meaningful because §0.2 gives genuine L2 vs L∞ *projected* attacks).
- **Confounds:** all of §0.5. **DeLong test** for AUROC(`R_q`) > AUROC(`M`) and > AUROC(`C`),
  bootstrap 95% CIs over prompts. (These are significance ON THE SINGLE RUN, not a sweep — keep.)

### KILL criterion (pre-registered)
Kill the ratio's added value if **both**: (i) raw `M` matches `R_q`'s AUROC within CI **AND** is
empirically gauge-stable across the `c`,`b` grid (gauge arm fails); this collapses the contribution
to the theory-only gauge proof. Kill the dissociation if consistency `C` predicts PE-PGD success as
well as `R_q` (AUROC overlap). **Honest-negative outcome that is still publishable:** "the raw
refusal gap already predicts per-prompt jailbreakability and is gauge-stable in practice, so the
normalization is unnecessary for stock aligned models" — a clean, citable negative for the field's
margin-based diagnostics.

### GPU-hours (2×A6000, realistic)
Clean diagnostics 920 prompts (fwd+bwd, both norms) ~0.5 h. Paraphrase gen (8×920) ~1–2 h.
PE-PGD 200 steps × 5 restarts × 920 prompts × ~5 budgets ~**10–16 h** on one A6000 (heavier than
the design's 6–12 h because of 200 steps + 5 restarts + the masking monotonicity re-runs). GCG
cross-check 128 prompts × 500 steps ~**6–10 h** on the 2nd A6000. Judge passes + gauge sweep ~2–3 h.
**Total ~1.5–2 GPU-days across both A6000s.**

### Headline if it works
"On a stock aligned LLM, the gauge-free threat-matched ratio `M/‖∇M‖_q` predicts per-prompt
jailbreak vulnerability (AUROC ≫ 0.5), the raw refusal gap does so only until you rescale the logits,
and paraphrase-consistency does not predict it at all."

### OPTIONAL / secondary (do not turn into a sweep)
Qwen2.5-7B replication (2nd model) — mark as robustness appendix only. A second seed for the attack
restarts. Report as "generalization check," not a scaling claim.

---

## A2 — certified fraction = attack-free ASR curve

### VERDICT: **FIX-THEN-RUN, but HIGH-RISK; scope the headline down before running**

The measurement-theory contribution (`ASR(ε)=CF(ε)`, budget-normalized collapse, dual-norm
matching) is open, but two things make the *stated* headline (`|ASR−CF|<0.05`) fragile enough that
a single run could read as a failure of the design rather than a finding:

1. **The count law is exact only on affine cells** (`main.tex` Prop count). Transformers have
   softmax attention + SiLU/GELU — smooth, curved, not piecewise-affine — so the affine radius may
   sit far below any interesting `ε`. Round-1 rated the prior probability of the `gap>0.1` kill as
   **high**. I agree. A single run at stock Llama-3 that returns a 0.15 gap would look like a null.
2. Even with §0.2's shared threat model (the prerequisite that makes `ASR(ε)` and `CF(ε)` comparable
   at all), the equality is a *small-ε expansion*, not a global law.

### The reframe that makes the single run unimpeachable (this is A2's single biggest fix)
**Make the "curvature edge" the primary result, not the fallback.** The publishable object is:
the budget `ε_c` at which `|ASR(ε)−CF(ε)|` first exceeds 0.05, the measured **local-linearity
diagnostic** that explains it, and the demonstration that below `ε_c` the cheap one-backward `CF`
curve *is* the expensive ASR curve. That is a measurement result whether the affine regime is thick
or thin, and it cannot be killed by a large gap — a large gap just moves `ε_c` down and becomes the
finding. Frame the headline as "we establish the count law AND its validity regime," with the
cheap-proxy payoff downstream (Round-1: the payoff is realized only after the law is validated, and
A2 still runs the full ladder to validate it — so "attack-free" is weaker here than in A1; say so).

### Protocol fixes (exact)
- **Attack:** PE-PGD (§0.2) run **at each `ε` on the ladder, in both an L2 and an L∞ ball**, on the
  same `e(x)` the certificate differentiates. This is THE make-or-break fix (Round-1): without it
  `ASR(ε)` and `CF(ε)` measure two threat models and any agreement is uninterpretable.
- **Add a measured local-linearity check (was assumed, must be measured):** along the PE-PGD
  direction, log the relative gap between `M(x+δ)` and its first-order Taylor prediction
  `M(x)+⟨∇M,δ⟩` as a function of `‖δ‖`. Report the `‖δ‖` at which this exceeds, say, 10% — that is
  the affine radius, and it should predict `ε_c`. This turns "the affine premise" from an assumption
  into a measured quantity and pre-empts the obvious referee question.
- **Curves:** overlay `ASR_q(ε)` and `CF_q(ε)=P(R_q<ε)`; report mean-abs-gap and max-gap per budget
  and `ε_c`. Budget-normalize (`R_q/ε`) and test the single-curve collapse (paper's `+0.94`).
  Dual-norm matching: matched CF tracks matched ASR; mismatched over/under-shoots.
- **Masking battery §0.2** — especially the unbounded ceiling: if PE-PGD ASR plateaus below the
  unbounded-attack ceiling, the "non-certified fraction" comparison is contaminated by a weak attack,
  which would masquerade as a good `ASR=CF` fit for the wrong reason. This check protects the law.
- **Confounds §0.5**, judge agreement on a 100-sample hand-checked slice (judge noise directly caps
  the achievable `|ASR−CF|`, and the target is 0.05, so a noisy judge alone can kill it — report the
  judge's own error bar as a floor on the gap).

### KILL criterion (pre-registered)
If `|ASR−CF|>0.1` **even at the smallest resolvable `ε` above judge noise** AND the local-linearity
diagnostic shows the affine radius is essentially zero (curvature dominates immediately), then the
first-order certificate is only a loose lower bound for transformers → report the per-prompt scatter
(`R_q` vs measured min radius, Spearman) as the surviving result and **drop the distributional
equality headline**. The per-prompt scatter is the robust fallback and is itself reportable.

### GPU-hours (2×A6000, realistic)
Diagnostics ~0.5 h. The attack ladder is the cost driver: 920 × 200 steps × 5 restarts × ~8 budgets
× 2 norms, with warm-starting down the ladder ~**20–30 h** on one A6000 (higher than the design's
15–25 h due to restarts). Local-linearity probe ~2 h. Masking subset ~3 h. Judge ~1–2 h.
**Total ~2 GPU-days, parallelizable to ~1–1.25 days across both A6000s.**

### Headline if it works
"A single forward+backward per prompt reproduces an LLM's jailbreak-success-vs-budget curve up to a
measured curvature edge `ε_c`, below which the cheap first-order certified fraction equals the
expensive attack success rate and its budget-normalized form collapses all budgets onto one curve."

### OPTIONAL / secondary (higher-probability-of-success variant, mark clearly)
Round-1's suggestion: run the count law on a **continuously-adversarially-trained checkpoint**
(MIXAT 2505.16947 / Continuous-AT 2604.12817) where local geometry is flatter and the law should
hold best. This is a *second* run — do NOT fold it into the single stock-model run; note it as the
natural follow-up if the stock-model `ε_c` is disappointingly small.

---

## A3 — refusal margin is not a target / over-refusal

### VERDICT: **FIX-THEN-RUN, with a mandatory repositioning** (survives; must move the headline)

The transferred idea (raising the refusal margin is a gauge move whose maximizer is the over-refuser
= constant classifier; only genuine intervention buys robustness; the gauge-free ratio correctly
reports "no gain") is clean and reviewer-legible. But Round-1 found **Steering Safely or Off a Cliff
(2602.06256)** already establishes the empirical half in mirror image (steering silently trades
robustness), and **Attacker Moves Second (2510.09023)** establishes "defenses collapse under strong
adaptive attacks." So the *empirical collapse demonstration is not the contribution.*

### The single biggest fix: reposition + measure `R_q` at every strength
Move the headline from "steering the margin up doesn't buy robustness" (now partly established) to:
**"over-refusal IS the scale-degeneracy of margin maximization; the gauge-free ratio `R_q` proves it
by staying flat under the pure-gauge knob while raw `M` reports a spurious gain; only a genuine
intervention moves `R_q` without the over-refusal blow-up."** The load-bearing curve is therefore
**`R_q` measured at every steering strength** — its flatness under pure gauge and its rise only under
genuine AT is what nobody else has. Make sure the run computes `R_q` (not just `M`) at every point.

### Protocol fixes (exact)
- **Two knobs cleanly separated (the design's own good instinct — enforce it):**
  (a) **Pure-gauge arm = generic refusal-token logit bias** `b` (self-defined; §0.4 — do NOT
  attribute to Refusal-Tokens 2412.06748). This ONLY rescales/shifts logits, so `R_q` MUST be flat
  here — this is the cleanest gauge test and the cleanest evidence.
  (b) **Steering arm = Arditi (2406.11717) refusal-direction activation addition** at mid layers,
  strength `α∈{0,0.5,1,2,4,8}`. This changes the function (not pure gauge), so `M`, `‖∇M‖`, and
  `R_q` all move; the claim is that strong-attack ASR does NOT fall in proportion to `M`.
- **Attack recomputed per strength (Round-1):** under steering, `M` and `e(x)`'s geometry shift, so
  **PE-PGD (§0.2) must be re-run at each strength** on the same embeddings — you cannot reuse a
  single attack. Weak-check contrast = single-step (FGSM-analog) embedding perturbation, to show the
  weak/strong gap explicitly (but frame per 2510.09023: the collapse-under-strong-attack is expected,
  the *gauge read-out* is the novelty).
- **Constant-classifier endpoint (A3's unique asset — push to it):** at high `α`, show XSTest safe
  refusal → ~1.0, OR-Bench over-refusal → high, MMLU slice (`cais/mmlu` IS cached) → chance. This is
  the over-refuser = constant-classifier collapse, the exact analog of `main.tex`'s ratio-maximizer.
  2602.06256 does NOT go to this endpoint — it is A3's territory.
- **Genuine-intervention comparator (cheap, current — Round-1):** prefer the **inference-time
  refusal-feature ablation (compute-free)** plus, if available, one of AlphaSteer (2506.07022) /
  LLM-VA (2601.19487) over a full ReFAT fine-tune. Show it raises strong-attack robustness AND `R_q`
  WITHOUT the over-refusal blow-up — separating a real gain from a gauge move. Keep a short ReFAT/LAT
  fine-tune OPTIONAL (adds GPU-days; the ablation comparator keeps this a single run).
- **Confounds §0.5** + XSTest standard protocol + strict judge for over-refusal.

### KILL criterion (pre-registered)
If strong-attack ASR falls **monotonically with `M` all the way** and over-refusal stays low, then
the margin IS a usable robustness dial and the negative-result framing dies — **but that positive
result (a cheap robustness knob) is itself a strong, publishable finding**, so either branch is a
paper. The pre-registered decision rule: report whichever of {gauge-illusion, usable-dial} the data
selects; do not select post hoc.

### GPU-hours (2×A6000, realistic)
No training in the main arm. Per strength: PE-PGD on HarmBench-400 (200 steps × 5 restarts) ~4–6 h +
over-refusal/utility passes ~1 h. 6 steering strengths + prune the logit-bias arm to ~4 points,
reusing clean generations → ~**40–60 GPU-h**, i.e. **~1.5–2 GPU-days across both A6000s.** Ablation
comparator is compute-free; optional ReFAT/LAT fine-tune +0.5–1 GPU-day (droppable).

### Headline if it works
"Steering an aligned LLM's refusal margin upward is a gauge illusion: it inflates the raw margin and
XSTest over-refusal toward the constant-classifier (refuse-everything) endpoint while the gauge-free
ratio correctly reports no robustness gain and strong-attack success barely moves — only a genuine
refusal-feature intervention raises the ratio and real robustness together."

### OPTIONAL / secondary
Qwen2.5-7B replication; a full ReFAT fine-tune arm. Both secondary; the single Llama-3 run with the
inference-time ablation comparator is the standalone paper.

---

## Cross-design experimental notes

- **One attack implementation, one judge, one predictor module** serve all three — build PE-PGD +
  `M`/`∇M` + Llama-Guard judge once, reuse. This is why running all three is ~4–5 GPU-days total, not
  3× a design. But per the stated priority, **A1 is the strongest single standalone run** (novelty
  cleanest, kill criterion cleanest, least dependent on a fragile regime); if only one runs, run A1.
- **The masking/obfuscation battery (§0.2) is the biggest shared experimental gap** across all three
  as written — each mentioned at most a one-line "AutoAttack ≤ PGD" analog. Without the full battery
  (steps/restarts monotonicity + vanishing-gradient log + unbounded ceiling + GCG cross-check) a
  single run cannot claim its attack is strong, and the whole lens collapses to "your attack was
  weak." Make it a first-class, reported experiment, not a footnote.
- **Judge noise is the shared ceiling.** A1's AUROC, A2's 0.05 target, and A3's ASR curves are all
  capped by judge error. Report a hand-checked 100-sample judge-agreement slice on every design and
  treat that error as the floor on any gap/threshold claim.

---

## Final verdicts + each design's single biggest experimental fix

- **A1 — FIX-THEN-RUN (run this one first).** Biggest fix: make the strong attack **projected
  embedding-PGD on the prompt's own `e(x)` (§0.2)** with the full gradient-masking battery, and keep
  the **logit-scale/logit-bias gauge stress-test the headline** — it is the one thing the raw gap
  cannot survive and the ratio can. ~1.5–2 GPU-days.

- **A2 — FIX-THEN-RUN (high-risk; scope down).** Biggest fix: **reposition the headline onto the
  measured "curvature edge" `ε_c` + a measured local-linearity diagnostic**, with the attack a
  per-budget L2/L∞ PE-PGD on the same `e(x)` the certificate differentiates — so a large `ASR−CF` gap
  becomes a finding (`ε_c` moves down), not a null. ~2 GPU-days (→~1 day across both A6000s).

- **A3 — FIX-THEN-RUN (reposition mandatory).** Biggest fix: **move the headline from "steering isn't
  robustness" (partly pre-empted by 2602.06256) to the gauge-degeneracy read-out — compute `R_q` at
  every steering strength**, show it stays flat under the pure-gauge logit-bias knob and rises only
  under a genuine (inference-time ablation / AlphaSteer) intervention, and push the sweep to the
  constant-classifier over-refuser endpoint. ~1.5–2 GPU-days.

**Shared prerequisite before any run (RUN-BLOCKING):** build a clean venv (the base anaconda
`transformers`/`huggingface-hub` versions are broken), install `nanogcg`+`accelerate`, and download a
local judge (Llama-Guard-3-8B) + the benchmarks — none of these are currently on disk despite the
designs treating prep as free.
