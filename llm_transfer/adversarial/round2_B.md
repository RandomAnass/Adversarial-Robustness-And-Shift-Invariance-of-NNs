# Round 2 — Experimental-Design Adversary on lens-B designs (B1, B2, B3)

Round 1 fixed the *literature* framing. Round 2 makes each design's ONE single run as
strong and unimpeachable as possible, so its result could carry a standalone top-tier
journal paper on its own. Priority stated up front and applied throughout: **one robust,
strong, standalone run — not breadth.** Every place a second seed / significance test /
extra model would help is marked OPTIONAL or SECONDARY; the effort goes into making the
single run bulletproof, not into scale.

Method: I re-read the load-bearing PDFs whose claims the round-2 protocol rests on
(Schwinn embedding attack 2402.09063 §3-4; Nasr 2510.09023; Fast Proxies 2502.10487;
Logit-Gap 2506.24056; and the three round-1 pivots F²C 2510.14242, LGIP 2511.13494,
adaptive-attack 2605.28467, each read in full), audited the theory (`paper/report/main.tex`,
thm:A / thm:finite-group / prop:sandwich / prop:rhoG / lem:ratiodegen / the §exp
dissociation numbers), and did a disk/cache check of the actual machine. All corrections
from `round1_B.md` are incorporated.

---

## Environment audit (disk check only, no GPU used)

**Hardware:** 2× RTX A6000 (49 GB each), both mostly free; 11 TB free on `/home`.

**Models cached (weights present, verified 4 shards + configs each, ~15 GB):**
`Qwen2.5-7B-Instruct`, `Meta-Llama-3-8B-Instruct`, `Ministral-8B-Instruct-2410`;
`MoritzLaurer/deberta-v3-large-zeroshot-v2.0` (841 MB). Also present and relevant:
`Qwen2.5-32B-Instruct`, `Qwen3-8B`, `Mistral-7B-Instruct-v0.3`.
**NOT cached: `Qwen2.5-3B-Instruct`** (F²C's model — see B1).

**Datasets cached:** `cais/mmlu`, `stanfordnlp/sst2`, `rotten_tomatoes`, `ag_news`,
`PKU-Alignment/PKU-SafeRLHF`, `gsm8k`. 
**NOT cached (must download): HarmBench behaviors + HarmBench-Llama-2-13b-cls classifier
(~26 GB), AdvBench, XSTest, MoNLI/Thunder-NUBench, OR-Bench.**

**Tooling gaps (install before running — all pip/HF, no GPU):**
- `transformers==4.32.1` is **too old** for Qwen2.5 / Llama-3 chat templates and the
  Ministral architecture. **Bump to ≥4.45** (F²C itself used 4.56.1). This is the single
  most likely silent-failure source; pin it first.
- **No `peft`, `trl`, `accelerate`, `sentencepiece`, `bitsandbytes`** — required for any
  LoRA arm (B1 arm 7, B2 dose arm, B3 consistency-LoRA). Install `peft`/`trl`/`accelerate`.
- **No `nanogcg`** (or `llm-attacks`) — required for the GCG cross-check (B1, B3). Install
  `nanogcg` (maintained, single-file, works with HF models).
- **NLTK WordNet corpus not downloaded** — needed for B2 antonym edits (`nltk.download('wordnet')`, tiny).
- No dedicated paraphraser cached (only `t5-base/small`). For B1/B2 meaning-preserving
  orbits, prefer **few-shot paraphrasing by the target model itself** (or a held-out 7B),
  filtered by bidirectional NLI, over a weak T5 paraphraser.

None of these is a blocker; all are setup. Budget ~0.5 day of setup + download before the
run. GPU-hour estimates below assume both A6000s in use.

---

## Cross-cutting protocol law (applies to all three; learned from the vision paper's own experience)

The vision paper's §exp is explicit that **at ~6-8 architecture/dose "cells" the per-cell
correlation has wide CIs** — matched-vs-mismatched η/L CIs *overlap* at 8 cells and only
separate on the denser **12-cell** grid (matched +0.83, CI [+0.49, +0.93]). The headline
+0.998 that carries the paper is the **per-sample** correlation over thousands of points,
not the ~8-cell one. **Transfer rule for B1/B2/B3:** do NOT rest the standalone claim on a
correlation over ~6 operators/doses. Put the statistical weight on the **per-prompt**
Spearman of η/L (or ρ_G) vs the per-prompt attack radius over **≥1,000 prompts** with
bootstrap CIs; report the per-operator/per-dose correlation as the *coarse* confirmation.
This is what makes each single run significant rather than n=6 anecdote.

Second cross-cutting rule (Nasr 2510.09023, verified: "the best way to run a strong adaptive
attack ... was for a human"; "we generally recommend attacks that operate in text space"):
the embedding-space attack alone will draw the "you did not run a strong adaptive attack"
referee comment. **GCG stays load-bearing, not optional**, on a subset, and the
**embedding-radius-vs-GCG agreement is the anti-gradient-masking audit** — the LLM analog
of the vision paper's "AutoAttack ≤ matched PGD, radius-vs-AA gap ≤ 0.025" masking check.

Third: the Schwinn embedding attack (2402.09063 §3, verified) is **unconstrained by
default** ("we do not put any constraints on the magnitude of the perturbation") and
optimizes `ē^{t+1} = ē^t − α·sign(∇ CE(F(e‖ē), y_target))` on all attacked token embeddings
simultaneously. To get a **radius** (the r₂ analog η/L predicts), you must wrap it in a
**minimum-norm search** (budget bisection / DDN-style projected variant): binary-search the
smallest ‖δ‖₂ that flips the answer / elicits the target. Specify this explicitly; the raw
Schwinn attack gives an ASR-at-budget, not a radius.

---

## DESIGN B1 — "Prompt Consistency Is Not Robustness"

**VERDICT: RUN-READY after two required fixes (F²C re-scope + per-prompt statistics).**
Strongest of the three; the dissociation is genuinely un-run on LLMs and the ingredients
are all local.

### What round-2 verification changed

I read F²C (2510.14242) in full. **Round-1's "use published F²C as the group-average /
perfect-consistency operator" needs correction**, because F²C is not that:
- F²C is a **LoRA training method**, not an inference-time projector. It is a
  confidence-gated majority-consensus regularizer (Consensus Cross-Entropy + a KL/JSD
  representation-alignment "flip" loss), trained only over a **benign PromptSource template
  orbit**. It **raises** consistency (+11.62% agreement, +8.94% F1) — it does **not saturate
  it to 1**, and it deliberately does *not* do uniform orbit-averaging (it beats swarm
  distillation precisely by pulling only toward the confident majority).
- It is fine-tuned on **`Qwen2.5-3B-Instruct` only** (NOT 7B, NOT Llama-3), under a
  non-commercial license, no checkpoints released, code on GitHub (URL not printed in PDF).
- It **never** measures adversarial robustness, margin, or Lipschitz — confirmed. That is
  exactly the untested gap.

**Consequence for the protocol.** The *literal* "exactly invariant, consistency = 1"
operator (the group-average projector = P_G of thm:finite-group, the analog of the vision
paper's exact-cyclic arm with consistency 1.0 and lowest robust radius) is the
**orbit-marginalized / majority-vote INFERENCE operator (arm 6)** — this is the one whose
consistency is 1 by construction and whose margin-collapse is the paper's sharpest point.
F²C belongs as a **realistic published high-consistency TRAINING arm** (arm 7), not as "the
exact invariant operator." Two clean choices, pick one and state it:
- **(preferred) Match F²C's model:** run the whole B1 panel on **`Qwen2.5-3B-Instruct`**
  (download; small), so the F²C arm is the authors' own released recipe on the authors' own
  model — zero "you re-implemented it wrong" surface. 3B is *fine* for a standalone
  mechanistic paper; the vision paper's headline is on 288k-param nets.
- **(alternative) Keep Qwen2.5-7B-Instruct as primary** and reproduce the F²C *recipe*
  (their loss, LoRA r=16 α=32) on it as arm 7, citing 2510.14242, and footnote that F²C's
  own checkpoint is 3B. This keeps the flagship at 7B but adds a re-implementation surface.

Either is defensible. I recommend the first (Qwen2.5-3B primary): it makes the "perfect
consistency yet least robust" arm the *published* F²C model, which is the most
adversarially-clean version of the claim.

### Exact protocol (single run)

- **Model:** `Qwen2.5-3B-Instruct` (primary, to host the released F²C arm) — OR
  `Qwen2.5-7B-Instruct` if you prefer 7B and reproduce the F²C recipe. Report ONE model.
  Llama-3-8B / Ministral-8B in an appendix cross-check only (NOT a sweep).
- **Task:** `cais/mmlu` (discriminative, class-logit-gap margin is clean) as primary; plus
  `sst2` + `rotten_tomatoes` as the binary-margin tasks where M(x) is cleanest. Exact-match
  scoring, no judge. Use a fixed ≥1,000-item evaluation subset (stratified across MMLU
  subjects) so the per-prompt statistics have power and the compute is bounded.
- **Operators (arms), all on one model, no weight change except arm 7:**
  1. canonical template; 2-4. three FormatSpread format variants (separators, casing,
     option markers); 5. option-order permutation (MCQ) / paraphrase (binary tasks);
  6. **orbit-marginalized inference operator** = majority-vote / logit-average over the
     full format+order orbit (= P_G, the literal exact-invariant arm, consistency ≡ 1);
  7. **F²C arm** = the published F²C LoRA (or its recipe) — the realistic high-consistency
     training arm.
  Six-to-seven arms. This is the *coarse* axis; the per-prompt axis (below) carries significance.
- **Invariance metric per arm:** agreement rate across the orbit (1 − FormatSpread spread);
  arms 6-7 have invariance ≈ 1 by construction (arm 6 exactly, arm 7 empirically highest).
- **STRONG attack (per arm):**
  - (a) **Embedding-space attack (Schwinn 2402.09063), wrapped in a minimum-norm search:**
    signed-gradient CE toward the wrong-class / flipped-answer target on the input-token
    embeddings, all attacked tokens simultaneously; **binary-search ‖δ‖₂ to the smallest
    label-flipping radius r₂ per prompt** (the r₂ analog). Config: α (step) tuned so the
    unconstrained attack reaches ~100% flip (Schwinn's regime), 100-500 steps, signed
    gradient (they report it most stable); then bisect the norm bound. Attack the last
    N̄ input tokens (fix N̄ across arms for fairness).
  - (b) **GCG (nanogcg) on a 200-item subset** as the discrete text-space cross-check
    (Nasr's recommended axis). **Report embedding-r₂ vs GCG-success agreement = the
    anti-masking audit.** Load-bearing, not optional.
  - (c) PromptBench word/char attacks for the task-accuracy operators (secondary).
- **Predictor:** M(x) = correct-class logit − max wrong-class logit; η = E[M];
  L = E‖∇_emb M‖₂ (threat-matched to the embedding attack); ‖∇_emb M‖₁ as the mismatched
  control. η/L is the predictor. **Gauge-free check:** rescale logits by c, verify η/L
  unchanged (lem:ratiodegen — this is the differentiator from Logit-Gap and Fast-Proxies).
- **Metrics (statistics as per the cross-cutting law):**
  - PRIMARY: per-prompt Spearman(η/L, r₂) over ≥1,000 prompts, bootstrap 95% CI. Target ≥ +0.7.
  - PRIMARY: per-prompt **partial** Spearman(η/L, r₂ | clean-correctness) — the
    "beyond clean accuracy" test, elevated to primary because Logit-Gap (2506.24056)
    explicitly warns the gap is "an internal consistency check, not an independent
    predictor" (verified quote). And a **second partial** controlling for the embedding
    radius itself must stay > 0 (round-1's near-tautology kill).
  - COARSE: Pearson/Spearman of {consistency, η/L, clean-acc} vs {r₂, ASR} over the 6-7 arms.
  - The single figure: η/L tracks r₂; consistency does not; arm 6 (marginalized) has
    consistency 1 and among the smallest r₂ — the LLM twin of the vision paper's Fig. cifar-pred.
- **Citations to position against (round-1, all verified):** LAP 2503.01345
  (embedding-drift↔paraphrase, but a training method, no margin/dissociation), Fast Proxies
  2502.10487 (cheap proxy predicts robustness rp=0.87/rs=0.94 — so B1's novelty is the
  *dissociation*, NOT the proxy), F²C 2510.14242 (the consistency operator), Logit-Gap
  2506.24056 (η numerator + the self-caveat).

### Confounds controlled
Clean accuracy (partial correlation + arms share the base model's accuracy up to format
effects); prompt length (fix N̄ attacked tokens; report length as covariate); gauge
(rescaling check); masking (embedding-vs-GCG agreement).

### KILL criterion (pre-registered)
Two kills, both honest-negative-publishable:
1. If consistency ranks robustness ≥ +0.7 with tight CI → the dissociation does not
   transfer (still publishable: it would overturn the vision-paper claim for LLMs).
2. If η/L is a pure restatement of clean accuracy (partial → 0) OR a near-tautology of the
   embedding radius (partial controlling for radius → 0) → η/L is not an independent
   predictor. Report either honestly.

### GPU-hours (2× A6000)
On 3B (or 7B): embedding min-norm search ~1-3 s/prompt × 1,000 prompts × 6 arms, parallel
over 2 GPUs ≈ **8-14 h** (3B) / **15-25 h** (7B). GCG 200-item × 3 arms (~2-4 min/item) ≈
**12-20 h**. Forward-pass margins/consistency over the 1,000-item set ≈ **2-4 h**. F²C LoRA
(one arm) ≈ **3-5 h**. **Total ≈ 25-45 GPU-h; GCG-light core ≈ 15-25 h.**

### One-line headline (if it works)
"On a fixed LLM, the prompt-consistency metrics the whole prompt-robustness field reports
are orthogonal-to-anti-correlated with adversarial robustness — the exactly consistent
orbit-marginalized operator is the least robust — while a single gauge-free forward-pass
ratio (threat-matched margin ÷ embedding-gradient norm) predicts per-prompt robustness at
Spearman +0.7, beyond clean accuracy and beyond the attack radius itself."

---

## DESIGN B2 — "The Orbit-Flip Radius: Excessive Invariance in LLMs"

**VERDICT: RUN-READY after two required fixes (de-circularize the oracle + make the dose
axis primary). Cheapest, highest-novelty-per-GPU-hour of the three.**

### What round-2 verification changed
I read LGIP (2511.13494) in full. **B2's novelty is intact.** LGIP probes only nine frozen
dual-encoder image-text VLMs (zero generative LLMs); its metrics are a mean |Δcosine|
invariance error and a positive-rate / gap — **rates and mean magnitudes, never a radius**;
its "strength-aware" flips are an *input stratification covariate*, not an output
minimal-distance-to-flip; it has **no budget law, no theory, no negation, no refusal**, and
names "instruction-tuned and generative VL models" and "negation" only as **future work**.
So B2's four load-bearing pillars are uncontested: (a) a **radius** ρ_G = minimal
distance-to-flip, (b) the **budget law** ε < ρ_G (prop:rhoG), (c) **generative
instruction-tuned LLMs at generation level**, (d) unifying word-order / negation /
over-refusal. **Required framing fix:** drop "first quantitative measure of excessive
invariance in language models" (LGIP did that for VLMs — SigLIP scores flipped captions
above human captions, sub-chance PR); claim only (a)-(d) and cite LGIP as concurrent prior.

### Exact protocol (single run)

- **Model:** `Meta-Llama-3-8B-Instruct` (primary). Report one model; `Qwen2.5-7B-Instruct`
  as an appendix family cross-point, NOT a statistical sweep. (Both cached.)
- **The invariance AXIS — make the within-model dose the PRIMARY axis** (round-1 fix, to
  avoid a between-checkpoint confound): sweep an **imposed-invariance dose** on ONE model
  via decoding-level paraphrase-marginalization strength (0 = greedy on canonical; higher =
  average the answer distribution over more of the paraphrase orbit) as a continuous knob,
  giving a clean within-model ρ_G(dose) curve. Cross-checkpoint points (base vs a
  consistency-LoRA / F²C-recipe point) are SECONDARY confirmation only.
- **Oracle (the single biggest risk — de-circularized, round-1 fix):** ρ_G is anchored
  **only on DETERMINISTIC oracle flips** where the label change is definitional:
  - negation insertion (rule-based; build from `sst2`/`rotten_tomatoes` + MoNLI-style
    negation of the hypothesis; download MoNLI or construct);
  - antonym swap (WordNet, `nltk.download('wordnet')`);
  - harmful↔benign minimal rewrite (from `PKU-SafeRLHF` pairs);
  - quantifier/entity swap where truth-conditionally decisive.
  The NLI model (`deberta-v3-large-zeroshot-v2.0`, cached) is used **ONLY as a
  paraphrase-validity filter on the invariance side** (bidirectional entailment to keep
  "paraphrases" meaning-preserving) — **never as the flip oracle** (an NLI model is itself
  excessively invariant, so using it as the oracle is exactly the circularity round-1
  flagged). State this separation explicitly; it is the difference between a credible ρ_G
  and a contaminated one.
- **STRONG invariance attack (the ρ_G search):** for each item, over the deterministic
  meaning-CHANGING edit set, find the **minimal-distance edit that flips the oracle label
  yet leaves the model's prediction/refusal unchanged.** Report distance in BOTH token edit
  distance AND embedding displacement ‖Δemb‖₂ (same geometry as B1's η/L, so ρ_G and η/L
  land on one plot). ρ_G(x) = min such distance; invariance-attack ASR = fraction of items
  with any invariant meaning-flip within a budget.
- **Sensitivity side (the trade-off):** reuse the B1 embedding-attack radius / η/L on the
  same items, so ρ_G-vs-(η/L) and ρ_G-vs-invariance are on one figure — the Tramèr
  two-quantity picture (prop:rhoG: a budget admits a robust invariant classifier only if
  ε ≤ η/L AND ε < ρ_G).
- **Metrics:**
  - H1 (trade-off): Spearman(ρ_G, dose) ≤ −0.6 — as imposed invariance rises, ρ_G falls.
    PRIMARY curve = within-model ρ_G(dose) over ≥1,000 items, bootstrap CI.
  - H2 (budget law = the certificate contribution, prop:rhoG): fraction of items where the
    oracle-robust radius ≤ ρ_G ≥ 95%. This is what LGIP cannot claim — keep it front-and-center.
  - H3 (safety degeneracy): as benign-context refusal-invariance (over-refusal) rises, ρ_G
    on the benign→benign axis falls (lem:ratiodegen constant-classifier degeneracy).
- **Judge:** deterministic oracle for the flip axis; NLI only as paraphrase filter;
  HarmBench classifier (download) for the safety-refusal axis, or a string+DeBERTa ensemble
  if avoiding the 26 GB download. No paid API.

### Confounds controlled
Paraphrase validity (bidirectional-NLI filter, drop non-equivalent "paraphrases");
between-model confound (within-model dose axis primary); oracle circularity (deterministic
flips only); geometry (report both token-edit and embedding distance).

### KILL criterion (pre-registered)
If ρ_G is flat or RISES with measured invariance (trade-off absent), OR the oracle-robust
radius routinely exceeds ρ_G (prop:rhoG fails empirically) → negative transfer of the
excessive-invariance mechanism. Publishable as a bound on when Tramèr transfers to LLMs.

### GPU-hours (2× A6000)
Mostly forward-pass generation + NLI filtering + a small embedding-displacement search over
~1-2k items × a handful of edit candidates. **≈ 12-25 GPU-h.** Optional consistency-LoRA
cross-point ≈ +3-5 h. This is the cheapest of the three.

### One-line headline (if it works)
"Generative instruction-tuned LLMs have a measurable orbit-flip radius ρ_G — the minimal
meaning-changing edit (negation, antonym, harmful→benign) they stay invariant to — and
raising a model's paraphrase/refusal invariance provably shrinks ρ_G, so the Tramèr
sensitivity/invariance trade-off governs LLMs with a budget law ε < ρ_G that holds on ≥95%
of items."

---

## DESIGN B3 — "η/L Explains Survival: A White-Box Adaptive-Attack Audit of Consistency-Trained LLM Safety"

**VERDICT: FIX-THEN-RUN (hard re-aim, but the fix is clean and the target model is
cached). Highest-risk, highest-compute of the three; the re-aim below makes it a distinct,
top-venue paper that ENGAGES rather than re-runs 2605.28467.**

### What round-2 verification changed (I read 2605.28467 in full, 24 pp)

Round-1's re-aim was right in direction; round-2 tightens the exact boundary and fixes one
conflation. What the paper already did, and what it leaves open:

- **It runs an adaptive attack, but a BLACK-BOX RL one** — a per-target GRPO suffix attacker
  (a small LoRA'd Qwen that emits a natural-language suffix), against a **frozen** target,
  reward = StrongReject/oracle scalar, **no gradient access to the target**. So the
  white-box / gradient / embedding-space adaptive attack is **fully open** — and the authors
  say so verbatim (Limitations, p.9): *"neither defense can achieve 100% security and may be
  evaded by attacks not tested in our threat model, such as **white-box attacks with direct
  gradient access**."* Quote this sentence; it is B3's open door named by the target paper.
- **Two tracks with very different numbers — do NOT conflate (round-1 did, slightly):**
  - *Jailbreak* adaptive attack (Table 6): ACT drives ASR to near-zero on **4/5**
    (GPT-OSS-20B 1%, Qwen3-8B 0%, Phi-4-reasoning 0%, Qwen3-1.7B 14%); **Gemma-4-E4B-it
    fails (33%)**. BCT degrades substantially (Qwen3-8B 30%, Gemma 57%).
  - *Prompt-injection* adaptive attack (Table 2): ACT wins only **37-63%** (ASR 37-63%),
    beating BCT on 4/5 but far from near-100%; **Gemma collapses (ACT ASR 96%, win ~4%)**.
  So "ACT largely survives the RL adaptive attack" is TRUE for jailbreak, GRADED for PI.
  B3's H2 ("advantage shrinks toward zero / inverts") is **likely FALSE for ACT-jailbreak**
  and must be re-scoped (below).
- **No margin, no Lipschitz, no η/L, no certified radius, no gradient-norm anywhere** —
  confirmed by full-text search. B3's forward-pass η/L predictor is **untouched**.
- **No consistency-dose sweep** — exactly one ACT + one BCT checkpoint per model, selected
  by validation loss. B3's dose axis is **open**.
- **BUT they OWN two things B3 must NOT claim as novel:** (i) a **linear refusal direction**
  d_ACT at the assistant-turn boundary, bidirectional (add→refuse, subtract→comply),
  clean on 2/5 models, partial on 3/5 (Sec 6.2, Table 9); and (ii) the **over-refusal /
  universal-refusal degeneracy guard** (CleanTask_any, Table 3), so "collapse to universal
  refusal" is already discussed and controlled. B3's H4 degeneracy claim is therefore NOT
  novel as a phenomenon — it must be recast as the *quantitative lem:ratiodegen* link
  (η/L → 0 as dose → max via margin collapse), building on their d_ACT selectivity numbers,
  not re-discovering over-refusal.
- **Models:** their 5 defended targets are Qwen3-1.7B, Qwen3-8B, Phi-4-reasoning,
  GPT-OSS-20B, Gemma-4-E4B-it. **`Qwen3-8B` and `gpt-oss-20b` are CACHED locally.**
  Qwen2.5-7B is only their *attacker*; Llama-3-8B is absent from the paper.

### The re-aim (the single biggest experimental fix)
**Stop claiming the adaptive-attack gap; claim the WHITE-BOX threat-matched attack + the
η/L predictor + the dose mechanism, and frame the headline as "η/L EXPLAINS survival" so the
result holds whether or not the advantage inverts.** Concretely, per round-1's directive:
the win is not "consistency training collapses" (it largely does not, under the RL attacker);
the win is that **a forward-pass margin-to-sensitivity ratio η/L predicts WHICH
consistency-trained checkpoint survives WHICH attack, and the consistency dose anti-predicts
survival via margin collapse.** If ACT survives *because* it preserves a large threat-matched
refusal margin (consistent with their d_ACT result), that is a POSITIVE confirmation of the
η/L law, not a refutation — which is exactly what makes the single run robust to either
outcome and neutralizes the coin-flip kill criterion.

### Exact protocol (single run)
- **Model (decisive choice): `Qwen3-8B` as the primary DEFENDED target** — it is one of the
  paper's own five targets AND is cached. Running the white-box arm on the *same model* they
  defend makes "we add the gradient attack they left open" airtight: same model, same ACT/BCT
  recipe, new threat. `gpt-oss-20b` (also cached, also their target) as an appendix
  cross-point. Do NOT switch to Llama-3-8B (untouched by the paper = weaker engagement).
  Report ONE model.
- **Defense arms (doses on the ONE base model):** dose 0 = base Qwen3-8B; then reproduce
  **ACT** (activation-consistency, Eq. 1 of 2605.28467: L2 between wrapped and stop-grad
  clean hidden states over layers × shared-suffix positions, LoRA) and **BCT** (output-level
  CE to the clean-prompt completion) at **increasing consistency strength** (LoRA
  perturbation size / λ / wrapper coverage) → ~3-4 doses. This dose sweep is the piece the
  paper explicitly lacks. Requires `peft`/`trl`/`accelerate` (install).
- **Benchmarks:** HarmBench standard behaviors (**download**) + AdvBench for jailbreak;
  a prompt-injection set (their OPI-style, or AdvBench-injection) for the PI track;
  helpfulness/over-refusal via **XSTest (download)** + a benign instruction set + MMLU
  (cached) for utility; guard against universal-refusal defense with their CleanTask_any
  logic (report benign-refusal rate alongside ASR).
- **WEAK attacks (reproduce the "invariance helps" claim, ≈ FGSM):** fixed template
  jailbreaks + non-adaptive paraphrase + sycophancy wrappers — the 2510.27062 regime. Expect
  higher dose ⇒ lower ASR here.
- **STRONG / threat-matched attacks (the contribution):**
  - (a) **Embedding-space attack (Schwinn 2402.09063) wrapped in a minimum-norm search** →
    per-prompt jailbreak **radius** r₂ (the r₂ analog; use radius not ASR to beat the
    near-0-ASR floor, exactly the vision-paper fix). Signed-gradient CE toward an affirmative
    target, all attacked tokens simultaneously, then bisect ‖δ‖₂.
  - (b) **GCG (nanogcg) on the HarmBench standard subset × the dose arms** — load-bearing
    text-space cross-check (Nasr). **Embedding-r₂ vs GCG agreement = anti-masking audit.**
  - (c) **White-box ADAPTIVE arm (the open door):** co-optimize the attack against the
    **consistency objective itself** — i.e., a gradient/embedding attack that directly
    targets the ACT hidden-state-agreement / BCT output-matching loss, not just the refusal
    output. This is the "AutoAttack-of-this-defense" the RL attacker cannot express and the
    authors flag as untested.
- **Predictor:** η = E[refusal − affirmation logit gap] (Logit-Gap 2506.24056 definition;
  also project onto the Arditi/d_ACT refusal direction as a low-D margin — building on their
  Sec 6.2, not claiming it); L = E‖∇_emb(gap)‖₂ threat-matched to the embedding attack, ‖·‖₁
  mismatched control. η/L gauge-free (verify by logit rescaling, lem:ratiodegen).
- **Metrics (statistics per the cross-cutting law — the per-prompt axis carries significance):**
  - PRIMARY: per-prompt Spearman(η/L, embedding jailbreak radius) over ≥1,000 prompts,
    bootstrap CI. Target ≥ +0.7.
  - PRIMARY: across doses × attacks, does η/L order the surviving robust rate while the
    consistency dose does NOT (or anti-predicts)? Report Pearson(η/L, strong-robust-rate)
    vs Pearson(dose, strong-robust-rate).
  - H4 recast (lem:ratiodegen, NOT novel-phenomenon): highest dose ⇒ η collapses ⇒ over-refusal
    (benign-refusal↑, CleanTask_any↓) with no strong-robust gain. Relate η to d_ACT selectivity.
  - Masking: GCG ≤ embedding-attack success throughout.
- **Judge:** HarmBench-Llama-2-13b-cls (**download ~26 GB**) for attack success; string +
  DeBERTa-zeroshot (cached) ensemble for refusal/over-refusal. No paid API.

### Confounds controlled
Base refusal rate (report dose-0 baseline ASR/refusal explicitly); clean accuracy /
helpfulness (MMLU + CleanTask_any per dose); universal-refusal degeneracy (benign-refusal
rate, the paper's own guard); floor effects (per-prompt radius, not ASR-at-budget); gauge
(rescaling); masking (embedding-vs-GCG).

### KILL criterion (pre-registered, re-scoped so it is NOT a coin flip)
The paper is robust to both outcomes because the claim is "η/L explains survival," not
"consistency collapses." Kill only if: **η/L fails to predict strong-attack robust rate
(per-prompt Spearman CI crosses 0) AND the dose is as good a predictor as η/L.** In that
case the forward-pass margin law does not transfer to consistency-trained safety — a clean,
calibrating negative for the field. (The old kill — "consistency survives the adaptive
attack" — is NOT a kill anymore, because survival-via-preserved-margin confirms the law.)

### GPU-hours (2× A6000)
ACT+BCT dose LoRAs (~6-8 checkpoints on Qwen3-8B) ≈ **15-25 h**. GCG on HarmBench subset ×
arms (dominant cost, ~2-5 min/behavior) ≈ **40-70 h** (cap behaviors/steps). Embedding +
white-box-adaptive attacks (differentiable, cheaper) over the set × arms ≈ **15-25 h**.
Forward-pass margins + HarmBench-classifier judging ≈ **8-12 h**. **Total ≈ 80-130 GPU-h;
GCG-light core (embedding + white-box-adaptive only, GCG on a 100-behavior subset) ≈ 45-60 h.**
This is the most expensive design; if compute is tight, run B1 or B2 first.

### One-line headline (if it works)
"On the very models 2605.28467 defends, a forward-pass threat-matched margin-to-sensitivity
ratio η/L predicts which consistency-trained (ACT/BCT) checkpoint survives which attack —
including the white-box gradient attack the authors flag as untested — while the consistency
DOSE anti-predicts survival by collapsing the refusal margin toward over-refusal: consistency
training helps safety only insofar as it preserves margin, and η/L, not the consistency
level, is what governs robustness."

---

## Three verdicts + each design's single biggest experimental fix

- **B1 — RUN-READY** (after fix). Biggest fix: **re-scope the F²C arm and move statistics to
  the per-prompt axis.** F²C is a LoRA *training* recipe on Qwen2.5-**3B** that only *raises*
  consistency — it is NOT the "exact invariant / perfect-consistency operator." Make the
  literal consistency=1 arm the orbit-marginalized *inference* operator (= P_G), keep F²C as
  a realistic published high-consistency training arm (run the panel on Qwen2.5-3B to host
  F²C's own released model), and rest significance on per-prompt Spearman(η/L, r₂) over
  ≥1,000 prompts + partial correlations, not the ~6-arm correlation.

- **B2 — RUN-READY** (after fix). Biggest fix: **de-circularize the oracle and make the
  within-model dose the primary invariance axis.** Anchor ρ_G ONLY on deterministic oracle
  flips (negation/antonym/harmful↔benign); use the NLI model solely as a paraphrase-validity
  filter, never as the flip oracle; sweep a within-model imposed-invariance dose for the
  ρ_G(dose) curve (cross-checkpoint points secondary). Novelty confirmed intact vs LGIP
  (radius + budget law + generative LLMs + generation-level refusal — none of which LGIP has).

- **B3 — FIX-THEN-RUN** (hard re-aim). Biggest fix: **pivot the headline from "consistency
  collapses under adaptive attack" (false for ACT-jailbreak; 2605.28467 already ran a
  black-box RL adaptive attack) to "η/L EXPLAINS survival," and run the WHITE-BOX
  threat-matched attack the authors explicitly flag as untested, on Qwen3-8B (their own
  cached target), with a consistency-dose sweep.** Do NOT re-claim the linear-refusal-direction
  mechanism or the over-refusal phenomenon (they own both); B3's differentiators are the
  margin/Lipschitz (η/L) quantification, the white-box gradient attack, and the dose sweep.

### Priority (restated)
The goal is ONE bulletproof standalone run, not breadth. **B2 is the cheapest and lowest-risk
(~12-25 GPU-h, novelty clean, no LoRA/GCG strictly required); B1 is the strongest single
result and moderate cost (~15-45 GPU-h); B3 is the highest-impact but highest-risk and
highest-cost (~45-130 GPU-h) and needs the re-aim before compute.** For every design, the
extra model / second seed / extra dose is SECONDARY — the single run is made bulletproof by
the per-prompt statistics (≥1,000 prompts, bootstrap CIs), the partial correlations, and the
embedding-vs-GCG anti-masking audit, not by adding scale.

