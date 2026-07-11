# B2 (orbit-flip radius ρ_G) — Adversarial Verification

**Verifier role:** adversarial audit of the B2 pilot toward a standalone paper. NO GPU used
(code + design + literature audit; all per-item checks run CPU-only on the cached
`results/peritem.jsonl`, 1600 items). Scope: implementation bugs, oracle non-circularity,
whether the positive claims AND the pre-registered KILL are correct, and the honest defensible
standalone claim.

**One-line verdict.** The oracle is genuinely non-circular and ρ_G is a real, measurable object,
but **the headline "budget-law ε<ρ_G holds on 100%" is a DEFINITIONAL ARTIFACT, not a finding**,
and the pooled orbit-flip rate (0.564) mixes genuine excessive invariance with a
constant-classifier artifact. The KILL is correctly computed but fired because the invariance
dose knob is a broken manipulation (it jailbreaks safety and does nothing to NLI), so it is
weak evidence against the trade-off hypothesis. **GO** on ρ_G-as-a-radius + the degeneracy
characterization + oracle framing; **NO-GO** on the budget law as an empirical result and on
the trade-off transfer (either direction) as currently instrumented; **FIX** the η/L axis.

---

## 1. IMPLEMENTATION audit

### 1a. Is the budget-law "ε<ρ_G on 100% of flipping items" a real measurement or a definitional artifact? — **DEFINITIONAL ARTIFACT (the single most important finding).**

**Verdict: definitional for 94% of items; non-vacuous on only 8 items out of 1600.**

The construction: each corpus item carries a list of candidate meaning-changing edits; ρ_G(x)
is defined (`run_b2.py:144`) as `min(flip_dists_emb)` over the edits that flip. The budget-law
"holds" test (`analyze.py:258`) is
```python
ok = all((not fl) or (e >= rho - 1e-6) for e, fl in zip(embs, ef))
```
i.e. "no flipping edit has size below rho." Since `rho = min` over the *flipping* edits, this is
**true by construction** whenever there is ≥1 flip.

Measured on the cached data:
- **1511 / 1600 items have exactly ONE candidate edit.** For a single-edit item, `rho_G` **is**
  that edit's size, so the loop tests one edit whose size equals `rho` — trivially `e >= rho`.
  The 100% is arithmetic, not empirical.
- Only **89 items have 2 edits**; of these **63 flip**; and only **8 items** have a genuinely
  non-vacuous test (a *smaller, non-flipping* edit exists below rho_G, so "no flip below rho_G"
  says something). All 8 are sentiment items where the small antonym edit (‖Δe‖≈0.6–0.9) did NOT
  flip and the larger negation edit (‖Δe‖≈1.8–3.1) DID — i.e. rho_G sits at the *larger* edit.

The "invariant ASR(ε) curve" (`summary.json` R3) is likewise the CDF of ρ_G over flipping items,
a legitimate distribution to *report*; but its stated load-bearing property — "ASR = 0 for
ε < min ρ_G, so no flip occurs below ρ_G" — is the tautology "no orbit-flip has ρ_G below the
minimum ρ_G over orbit-flips." Verified independently: `P(ρ≤0.471)=0` only because
`min ρ over flips = 0.594`.

**Why the design cannot test the budget law.** prop:rhoG (`main.tex:112`) states ρ_G is an
*upper bound* on the oracle-robust radius, and the budget law is ε<ρ_G. A real empirical test
needs a **graded family of edits of increasing size per item** and must show flips appear only
above ρ_G. With 1 (occasionally 2) edits per item there is nothing below ρ_G to falsify against.
As written, "100% budget-law" should be **deleted as a result** and replaced with the honest
statement: ρ_G is *defined* as the minimal flipping edit, and we *report its distribution*; the
certificate ρ_G ≥ oracle-robust-radius holds by prop:rhoG (a theorem, not an experiment).

### 1b. Is ρ_G measured correctly (model-answer-unchanged, label extraction, edit-size metric)?

- **"Model answer unchanged":** measured by comparing the marginalized answer on the edit vs on
  x (`run_b2.py:135`, `is_flip = correct and (aj == a0) and (aj != e["y_edit"])`). The answer is
  a majority vote over `1 + round(dose·K)` variants (`marg_answer`). At dose 0 this is a single
  greedy/argmax label — correct. **Decoding is greedy** for sentiment/NLI (first-token argmax,
  `_score_binary`) and greedy generate for safety (`do_sample=False`). Sound.
- **Label extraction:** sentiment/NLI use constrained first-token scoring
  (logit(' positive') vs logit(' negative'); logit(' yes') vs logit(' no')). This is robust and
  cheap. Safety uses substring refusal-marker matching on 32–40 generated tokens
  (`is_refusal`, 40+ markers). Refusal detection by keyword is the standard-but-imperfect method;
  a polite non-refusing deflection could be mis-scored, but this is an accepted approximation and
  the safety base accuracy (0.973 at dose 0) is sane.
- **Edit-size metric:** token edit distance is word-level Levenshtein (correct). Embedding
  displacement `emb_displacement` (`b2_model.py:232`) computes ‖e(x_edit)−e(x)‖₂ over the aligned
  common prefix plus full norm of the length-changed tail. **Caveat:** this geometry is coarse and
  heavily quantized — e.g. the safety swap "…drugs…"→"…vitamins…" produces ‖Δe‖=0.839024 on 120
  distinct items, and the *median* ρ_G_emb is byte-identical (0.8390237092971802) at every one of
  the 6 doses. That constant median is not a bug (it is the modal single-token swap), but it means
  the embedding radius carries little per-item information beyond the discrete edit type; ρ_G is
  effectively a re-encoding of "which swap template," not a continuous radius.

### 1c. Orbit-flip rate numerator/denominator.

Denominator = **all items** (not just base-correct). Numerator requires `correct` on x, so the
flip rate is bounded by base accuracy. This is a defensible convention (an item the model gets
wrong cannot exhibit "invariance to a flip it never tracked"), **but it couples the flip rate to
base accuracy**, which is what makes the safety dose knob look like a trade-off (see §3). Overall
flip rate 0.564 = 0.714 among base-correct items × 0.79 base accuracy. Correctly computed;
interpretation caveat below.

### 1d. Dose knob and McNemar/trade-off stats.

The stats are **correctly implemented and correctly signed** (verified every branch of the KILL
booleans against `summary.json`). McNemar uses a binomial test on discordant pairs (fine). The
per-item dose→flip Spearman, paired bootstrap, and partials are standard. No stat bug.

The **dose knob itself is the problem**, not the stats (§3).

---

## 2. ORACLE non-circularity — **VERDICT: CLEAN. No model decision leaks into the flip label.**

- The flip oracle `y_edit` is set **only** by construction in `corpus.py` (antonym→y_flip;
  copula-negation→y_flip; MoNLI `gold_label`; harmful→"comply"). Grep confirms
  `run_b2.py / b2_model.py / analyze.py / corpus.py / cross_model.py` **never import or call the
  NLI/deberta model**. The NLI model appears only in `validate_oracle.py` and `dump_paraphrases.py`.
- The NLI model's roles are exactly the two permitted ones: (i) a *diagnostic* meaning-change
  sanity check on the deterministic edits (reports `frac_meaning_changed` = 96/98.7/99.3% per
  family — high, as required, so the deterministic flips are genuine meaning changes), and (ii) a
  paraphrase-validity filter pass-rate (0.82) on the *invariance* side. Neither feeds a label.
  This is precisely the de-circularization round1_B/round2_B mandated. **The 96–99% oracle-validity
  claim is real** (independent NLI diagnostic, not the oracle).

**Minor oracle-quality concerns (not circularity, but noise in the deterministic oracle):**
- **Sentiment copula-negation is linguistically unreliable.** "the film itself is small and
  shriveled" (negative) → "…is **not** small and shriveled" is labeled **positive**, but "not
  small and shriveled" is closer to neutral/ambiguous than positive. **206/700 sentiment items are
  negation-only** (rely entirely on this rule), and 295 sentiment negation edits exist total. The
  NLI diagnostic flags these as "changed" (it only checks *non-equivalence*, which is satisfied),
  so the 96% validity number does NOT catch the polarity-assignment error. This is a real
  few-to-29%-level contaminant on the sentiment negation subset. Antonym edits (494) are clean.
- NLI regex substitution can produce ungrammatical edits ("a instrument" for "an instrument").
  Cosmetic; MoNLI gold is the oracle, defensible.

---

## 3. RESULT-CORRECTNESS audit

### 3a. Is the KILL real, or an artifact of a weak/broken dose knob? — **The KILL is a MANIPULATION-WEAKNESS artifact. It is NOT clean evidence the trade-off hypothesis is false.**

The KILL is *correctly computed* — all five trade-off signals point away from the hypothesis
(imposed flip-delta −0.045 [−0.062,−0.028]; per-item dose→flip Spearman −0.221; McNemar
gained 61 / lost 133, p=2.5e-7; minv-vs-ρ +0.051; minv-vs-flip −0.034). But *why* they point away
is a broken knob, family by family:

- **NLI (500 items): the dose does literally nothing.** 0/500 items change their answer across the
  dose grid; 1/500 changes measured invariance. NLI is a frozen constant classifier ("entailment"
  on 100% of x for Llama), so there is no invariance to *raise*.
- **Sentiment (700): the dose barely moves it.** 38/700 items change answer across doses. The
  consistency system prompt + paraphrase-marginalization leaves the argmax essentially fixed.
- **Safety (400): the dose JAILBREAKS the model.** As dose rises, P(comply on a harmful request)
  goes 2.8% → 24% and base refuse-accuracy collapses 0.973 → 0.757. Because an orbit-flip requires
  the model to be *correct* on x (refuse), the flip rate DROPS mechanically as the dose destroys
  base accuracy (safety dose→flip Spearman −0.445; McNemar +14/−99). The observed
  negative/anti-trade-off is a base-accuracy-collapse confound, exactly the report's own caveat,
  but stronger than the report states: it is not "noisy," it is a **jailbreak of x**, not an
  increase in invariance to the *edit*.

So the imposed-invariance dose (a) does nothing where the model is already saturated (NLI),
(b) barely moves the sentiment argmax, and (c) in safety raises *compliance*, which is a
different phenomenon from raising paraphrase-invariance. **The trade-off hypothesis was never
given a fair test.** The KILL is a valid pre-registered negative *on this knob*, but the honest
reading is "this dose knob cannot move invariance without confounds," not "the Tramèr trade-off
is absent in LLMs." A fairer intervention (a genuine consistency-LoRA / F²C-style operator that
raises paraphrase-agreement while holding base accuracy, or a between-model invariance contrast
with accuracy controlled) is needed before any claim — positive or negative — about the trade-off.
The cross-model arm does not rescue it either: Qwen is *more* paraphrase-invariant (0.933 vs
0.922) yet has a *lower* flip rate (0.489 vs 0.564) — the wrong sign for the trade-off — but Qwen
also has higher base accuracy (0.878 vs 0.79), so this too is accuracy-confounded, n=2.

### 3b. Constant-classifier degeneracy (100% entailment, 97% refuse) — real, or a parse bug? — **REAL model behavior, correctly detected.**

- The R0 detection in `analyze.py` is sound (dominant-answer fraction per family).
- Evidence it is **not** a label-extraction bug: (i) Qwen on the *same* corpus and *same* code
  shows NLI dominant-answer fraction 0.516, not 1.0 — a parse bug would hit both models
  identically; (ii) MoNLI hypotheses are negated sentences on which a "yes"-biased instruction
  model plausibly always answers entailment; (iii) the first-token yes/no scoring is standard.
- **Consequence for the headline flip rate:** the NLI orbit-flip rate (0.468) equals
  P(gold=entailment) exactly — it is a *pure* constant-classifier artifact (model says
  "entailment" on x and on the edit, oracle flips to neutral ⇒ guaranteed flip), NOT a measurement
  of invariance to a distinction the model *could* have drawn. Likewise safety is 97% "refuse".
  The pooled 0.564 headline therefore mixes genuine excessive invariance (sentiment antonym,
  parts of safety) with lem:ratiodegen degeneracy (all of NLI, most of safety). This is the exact
  empirical instance of lem:ratiodegen and is worth reporting **as a characterization**, but it
  must not be sold as "the model is 56% excessively invariant." The degeneracy being
  model-dependent (Llama yes, Qwen no) is itself a clean, reportable result.

### 3c. η/L ⊥ ρ_G (Spearman −0.11) — **the η/L here is NOT computed consistently with the theory; the decoupling number is largely meaningless for 75% of items.**

`b2_model.eta_L` reuses `tdiss_core.diagnostics`, which computes M as the **refusal margin**
`refuse_logit − affirm_logit` (`tdiss_core.py:68`). The theory's M (`main.tex:135`) is the
**task-class margin** M(x)=f_y − max_{j≠y} f_j. For the safety family the refusal margin is a
reasonable proxy; for **sentiment and NLI (1200/1600 items) the "refuse − affirm" margin is
semantically empty** — verified: M is negative on 96% of sentiment and 100% of NLI items (mean
−1.5 and −3.0), because these prompts elicit no refusal. So R2=M/‖∇M‖₂ is a negative
refusal-margin ratio on a non-refusal task for three-quarters of the data. The reported
Spearman(R2, ρ_G) = −0.11 is dominated by this mis-specified margin and should **not** be cited as
"η/L decouples from ρ_G." To make the two-axis claim, η/L must use the task-appropriate class
margin (positive−negative logit gap for sentiment; yes−no for NLI; refuse−comply for safety), the
same heads the flip uses. As-is, this result is a **NO-GO**.

---

## 4. LITERATURE re-verify

Round1_B/round2_B already downloaded and read LGIP (2511.13494), Jacobsen 2019 (1811.00401),
Tramèr 2020 (2002.04599), UnNatural LI (2101.00010) in full, with verified quotes (the 98.7%
figure; SigLIP scoring flipped captions above human captions). I re-confirmed LGIP's scope
directly: its three metrics are **invariance error, semantic-sensitivity gap, positive-rate** —
all rates/mean magnitudes; **no minimal-distance radius, no ε-budget certificate, frozen
dual-encoder VLMs only (CLIP/SigLIP), no negation, no refusal**. So LGIP does not subsume B2.

**B2's DEFENSIBLE standalone contribution, given the mixed result:**
1. **ρ_G as a measurable radius** — the minimal meaning-changing edit (antonym / negation /
   harmful→benign) a *generative instruction-tuned* LLM stays invariant to, in both token-edit and
   embedding geometry. New relative to LGIP (rate, not radius) and UnNatural LI (encoder NLI).
2. **The certificate/budget framing** ρ_G ≥ oracle-robust-radius (prop:rhoG) — as a **theorem
   instantiated**, not as the tautological "100% empirical" claim. This is what LGIP cannot state.
3. **The constant-classifier degeneracy characterization** (lem:ratiodegen made empirical):
   Llama-3-8B is a constant "entailment" classifier on negated MoNLI and near-constant "refuse" on
   PKU-harmful, and this is model-dependent (Qwen is not) — a clean, honest excessive-invariance
   finding that unifies negation-blindness and over-refusal under one radius.

**NOT defensible from this run:** the invariance–sensitivity **trade-off** transfer (killed, but by
a broken knob — so neither the positive nor a strong negative claim is earned); the **budget-law
ε<ρ_G as an empirical result** (definitional); the **η/L ⊥ ρ_G decoupling** (mis-specified margin).

---

## GO / NO-GO on B2's parts as paper results

| Claim | Verdict | Reason |
|---|---|---|
| ρ_G is a real, measurable radius (distribution, both geometries) | **GO** (with caveat) | Sound measurement; embedding geometry is coarse/quantized, lead with token-edit distance |
| Oracle is deterministic & non-circular | **GO** | Clean separation verified; NLI is filter/diagnostic only |
| Orbit-flip rate 0.564 as "excessive invariance" | **GO only if decomposed** | Pool mixes genuine invariance with NLI/safety constant-classifier artifact; report per-family, not pooled headline |
| Constant-classifier degeneracy (lem:ratiodegen instance) | **GO** | Real behavior, correctly detected, model-dependent — a genuine finding |
| Budget law ε<ρ_G "holds on 100%" | **NO-GO** | Definitional artifact (1 edit/item); non-vacuous on 8/1600. Replace with prop:rhoG-as-theorem + ρ_G distribution |
| Invariance–sensitivity trade-off (transfers / KILL) | **NO-GO (re-run)** | KILL is a broken-dose-knob artifact (jailbreaks safety, no-ops NLI); needs a genuine invariance operator with accuracy control before any claim |
| η/L ⊥ ρ_G decoupling (−0.11) | **NO-GO (fix)** | η/L uses refusal margin on non-refusal tasks for 75% of items; recompute with task-class margin |
| Sentiment negation oracle | **FIX** | Polarity assignment unreliable on 206 negation-only items; restrict to antonym or hand-audit |

**Bottom line for the paper:** B2 supports a *narrower* standalone claim than "the Tramèr
trade-off with a budget law governs LLMs." It supports: *generative LLMs have a measurable
orbit-flip radius ρ_G that certifies (by prop:rhoG) an upper bound on their oracle-robust radius,
and on negation-NLI and harmful-request tasks Llama-3-8B collapses to a constant classifier
(lem:ratiodegen), a model-dependent excessive-invariance failure LGIP's rate metrics and encoder
NLI cannot express.* The trade-off and the budget law are not earned by this run.
