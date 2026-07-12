# The Orbit-Flip Radius: Excessive Invariance as a Measurable Adversarial Surface in Language Models

## Transferable element (from our paper)
- (d) The excessive-invariance failure mode and the orbit-flip radius ρ_G: an imposed invariance is safe at budget ε
  only if ε < ρ_G, the smallest transformation that CHANGES the oracle label yet the invariant model treats as
  within-orbit (Proposition rhoG). A budget admits a robust invariant classifier only if ε ≤ η/L (score stability)
  AND ε < ρ_G (the invariance does not cross the oracle boundary).
- The two-quantity picture: sensitivity attacks are bounded by η/L, invariance attacks by ρ_G; more sensitivity-
  robustness trades against invariance-robustness (the Tramèr trade-off our criterion formalizes).

LLM instantiation. Define, for an instruction-tuned model, a TEXT orbit-flip radius: the minimal semantic edit
distance of a MEANING-CHANGING edit (negation insertion, antonym swap, quantifier/scope change, harmful↔benign
rewrite, entity swap) that the model is INVARIANT to (keeps its prediction / refusal while the human-oracle label
flips). Measure how ρ_G trades against the model's measured paraphrase/format/word-order invariance.

## Literature gap (specific papers checked + why open)
- Jacobsen et al. (ICLR 2019, arXiv:1811.00401) and Tramèr et al. (ICML 2020, arXiv:2002.04599) prove excessive
  invariance → adversarial vulnerability and an invariance/sensitivity trade-off, but ONLY in vision; no text/LLM
  instantiation and no ρ_G.
- "UnNatural Language Inference" (Sinha et al., ACL 2021, arXiv:2101.00010): NLI models invariant to word-order
  permutations — a measured excessive invariance, but never turned into an orbit-flip radius or a trade-off curve.
- Negation insensitivity (Thunder-NUBench; arXiv:2601.21433; arXiv:2305.14785) and over-refusal (XSTest, NAACL
  2024; OR-Bench 2025; arXiv:2510.08158) document invariance to meaning/intent-changing edits piecemeal; none
  unifies them as an orbit-flip radius or relates ρ_G to measured input-invariance.
- Contrast sets (Gardner et al.) provide oracle-labeled minimal edits but are used for accuracy, not invariance
  attacks or a trade-off.
No paper measures a ρ_G for LLMs or shows that raising paraphrase/format/safety invariance shrinks it. Open.

## Hypothesis (falsifiable)
Across a set of comparison points that vary MEASURED input-invariance (differently safety-/consistency-tuned
checkpoints of one family, and one base model under increasing imposed-invariance doses — decoding-level paraphrase
marginalization, then a consistency LoRA):
- H1 (trade-off): the invariance-attack success rate (fraction of minimal meaning-flipping edits the model is
  invariant to) INCREASES, and the orbit-flip radius ρ_G DECREASES, as measured paraphrase/word-order invariance
  increases — a negative ρ_G-vs-invariance slope (Spearman ≤ −0.6), the Tramèr trade-off instantiated.
- H2 (budget law): points are oracle-robust at edit budget ε only when ε < ρ_G; the observed oracle-robust radius
  is upper-bounded by the measured ρ_G on ≥ 95% of items (Proposition rhoG holds empirically).
- H3 (safety instance): as refusal-invariance to benign keyword contexts rises (over-refusal), ρ_G on the
  benign→benign axis falls — over-refusal is the constant-classifier degeneracy of our Lemma ratiodegen.
Kill: if ρ_G is flat or rises with measured invariance, the excessive-invariance transfer fails.

## Protocol (model, dataset/benchmark, attack/eval incl. STRONG attack, metrics, exact steps)
- Model (local): `Meta-Llama-3-8B-Instruct` (primary) and `Qwen2.5-7B-Instruct` (family cross-point). One primary
  model reported; extra checkpoints are invariance comparison points, not a statistical model sweep.
- Full benchmarks (assemble one held-out orbit-flip corpus, all from oracle-labeled minimal edits):
  - Sentiment counterfactuals: `sst2` + `rotten_tomatoes` (local) with antonym/negation edits (rule + WordNet).
  - Negation NLI: build from local resources / download MoNLI; oracle label flips deterministically under negation.
  - Safety contrast pairs: `PKU-Alignment/PKU-SafeRLHF` (local) + XSTest (download) — benign vs harmful minimal
    rewrites for the refusal axis.
  - Word-order permutations (UnNatural-LI protocol) as the permutation-orbit attack.
- INVARIANCE metric (per model/point): agreement over the MEANING-PRESERVING orbit (paraphrases via a local
  paraphraser + format variants); low spread = high invariance.
- STRONG invariance attack (the ρ_G search): for each item, search the MEANING-CHANGING edit set for the
  minimal-distance edit that (i) flips the oracle label (verified by a LOCAL judge) yet (ii) leaves the model's
  prediction/refusal unchanged. Distance = token edit distance AND embedding-space displacement ∥Δemb∥₂ (so ρ_G is
  reported in the same geometry as B1's η/L). Report ρ_G = mean minimal such distance; invariance-attack success =
  fraction of items with any such edit within a budget.
- Sensitivity side (for the trade-off): the same models' η/L / embedding-attack radius from the B1 pipeline, so the
  ρ_G-vs-(η/L) and ρ_G-vs-invariance curves are on one plot.
- LOCAL judge (no paid API): oracle labels are deterministic for negation/antonym/harmful-rewrite constructions;
  cross-check meaning-change with `MoritzLaurer/deberta-v3-large-zeroshot-v2.0` (NLI/zero-shot, local) and, for
  safety, the HarmBench classifier (open weight). Paraphrase-validity checked with the same NLI model (entailment
  both directions).
- Metrics: ρ_G distribution per model; invariance-attack ASR; Spearman(ρ_G, measured-invariance) and
  Spearman(ρ_G, η/L); fraction of items where oracle-robust radius ≤ ρ_G (Proposition check); over-refusal ρ_G vs
  benign-refusal rate.

## Compute estimate (GPU-hours on A6000s)
Mostly forward-pass generation + NLI judging over ~10–20k items × a handful of edit candidates each, plus a small
embedding-displacement search. ~15–30 GPU-h. Optional consistency-LoRA comparison point ≈ +3–5 h.

## Why standalone top-tier (what a reviewer would call the contribution)
The first quantitative, model-agnostic MEASURE of excessive invariance in LLMs — a text orbit-flip radius ρ_G — and
the first evidence that the invariance/sensitivity trade-off of Tramèr (2020) governs instruction-tuned LLMs:
pushing paraphrase/format/safety invariance measurably shrinks the room before meaning-changing edits (negation,
harmful↔benign) become invisible to the model. It unifies three separate LLM failure literatures (word-order
invariance, negation insensitivity, over-refusal) under one operator-theoretic quantity and gives a budget law
(ε < ρ_G) practitioners can measure. Not an addendum: it stands on the NLP robustness/safety literature and only
borrows our ρ_G definition.

## Risks / kill criteria
- Risk: "semantic edit distance" is fuzzy; mitigate by anchoring on DETERMINISTIC oracle flips (negation, antonym,
  harmful-rewrite) where the label change is unambiguous, and reporting both token-edit and embedding distance.
- Risk: a paraphraser that changes meaning contaminates the invariance metric; guard with bidirectional-NLI
  entailment filtering (drop non-equivalent "paraphrases").
- Risk: too few invariance comparison points for a slope. Mitigate by adding decoding-level imposed-invariance doses
  (paraphrase-marginalization strength) as a continuous knob on one base model, giving a within-model ρ_G(dose)
  curve — no extra training, no model sweep.
- Kill: ρ_G does not decrease with measured invariance (trade-off absent), or oracle-robust radius routinely exceeds
  ρ_G (Proposition fails empirically) → report as a negative transfer of the excessive-invariance mechanism.
