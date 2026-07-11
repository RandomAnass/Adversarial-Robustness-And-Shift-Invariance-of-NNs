# B2 — The Orbit-Flip Radius ρ_G: Excessive Invariance as a Measurable Adversarial Axis in Generative LLMs

Standalone pilot instantiating the paper's `prop:rhoG` (orbit-flip radius) and the Tramèr
sensitivity/invariance trade-off in a generative instruction-tuned LLM, with the budget law
ε < ρ_G. Model: **Meta-Llama-3-8B-Instruct**. GPU 1 only.

## The object (theory: `paper/report/main.tex`, prop:rhoG, lem:ratiodegen)
For an item x with a **deterministic oracle label** y(x), an **orbit-flip** is a
meaning-changing edit x→x' with y(x')≠y(x) that the model is INVARIANT to: the model's answer
stays y(x) while the oracle flipped. ρ_G(x) = the minimal distance of such an invariant flip
(≈∞ if the model tracks every flip). A budget ε admits a robust invariant classifier only if
ε ≤ η/L (score stability) **and** ε < ρ_G (the invariance does not cross the oracle boundary).

## De-circularization (round1_B / round2_B, MANDATORY)
- The **flip oracle is DETERMINISTIC** in every family (rule-based; the label change is
  definitional). It is NEVER a model.
- The **NLI model** (`deberta-v3-large-zeroshot-v2.0`) is used ONLY as a paraphrase-validity
  FILTER on the invariance side and as an independent oracle SANITY-CHECK (`validate_oracle.py`).
  It never labels a flip. (Using an NLI model as the flip oracle would be circular — an NLI model
  is itself excessively invariant.)

## Families (all deterministic oracle flips, minimal edits)
| family | task | oracle | edit that flips it | source |
|---|---|---|---|---|
| sentiment | positive/negative | SST-2 / RT gold label | WordNet antonym swap (1 tok) or copula negation | sst2 + rotten_tomatoes |
| nli | entailment/neutral | MoNLI gold (monotonicity) | single lexical substitution under (negated) context | MoNLI |
| safety | refuse/comply | construction (harmful vs benign twin) | harmful→benign minimal object/verb swap | PKU-SafeRLHF |

Corpus: 1600 items (700 sentiment, 500 nli, 400 safety); median token-edit-distance = 1.

## Primary axis (round-2 fix): within-model imposed-invariance DOSE
A continuous knob d∈{0,…,1} raising the model's paraphrase invariance WITHOUT changing weights:
(a) a consistency-encouraging system prompt (on for d>0), (b) paraphrase-marginalization —
majority vote over round(d·K) self-paraphrases. This gives a clean within-model ρ_G(dose) curve,
avoiding a between-checkpoint confound.

## Two geometries for ρ_G
- token edit distance (Levenshtein), and
- embedding displacement ‖e(x')−e(x)‖₂ in the model's input-embedding space (the same geometry
  as the η/L embedding attack), so ρ_G and η/L land on one plot.

## Sensitivity axis (reused, read-only, from the sibling T-DISS module)
η/L via `tdiss_core.TDiss.diagnostics`: margin M, ‖∇M‖₂, ‖∇M‖₁, R₂=M/‖∇M‖₂, R∞=M/‖∇M‖₁.

## Files
- `corpus.py` — builds the deterministic oracle corpus → `data/corpus.jsonl`.
- `b2_model.py` — model engine (task heads, orbit-flip, ρ_G, dose knob, emb displacement, η/L reuse).
- `run_b2.py` — main harness → `results/peritem.jsonl` (per item, all doses).
- `analyze.py` — ρ_G distribution, orbit-flip rate, trade-off (bootstrap CIs), budget law, KILL check → `results/summary.json`.
- `make_figures.py` — figures → `figures/`.
- `validate_oracle.py` + `dump_paraphrases.py` — NLI paraphrase filter + oracle sanity check → `results/oracle_audit.json`.

## Results (per-item, ≥1,000 items, bootstrap CIs)
1. **ρ_G measurable & non-trivial** — distribution over items + real orbit-flip rate.
2. **Trade-off** — higher imposed/measured invariance ⇒ smaller ρ_G (negative correlation, CI).
3. **Budget law** — an invariant flip of size ε succeeds only when ε ≥ ρ_G (prop:rhoG fraction).

## Pre-registered KILL
KILL iff ρ_G does not fall with invariance (trade-off absent) OR orbit-flip rate ≈ 0. The honest
negative is the result — reported, never fabricated.

## Novelty vs LGIP (arXiv:2511.13494, cite on page 1)
LGIP measures an invariance-error RATE for frozen dual-encoder VLMs. B2 is uncontested on:
(a) a metric **radius** ρ_G (not a rate), (b) the **budget law** ε<ρ_G, (c) **generative
instruction-tuned LLMs** at generation level, (d) unifying word-order / negation / over-refusal.
