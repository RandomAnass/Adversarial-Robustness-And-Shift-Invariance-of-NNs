# LLM/VLM campaign — literature synthesis + paper framing (2026-07-12)

Consolidates the three background literature scoop-hunts (C1/VLM, B2/text, unified thesis), my
source-verification of their load-bearing citations, and the impact of the T-DISS negative. This is
the input to the paper draft. Every scope claim below is either agent-quoted-verbatim or checked by
me against the arXiv abstract (noted).

---

## 0. The three pilots, verified status

| pilot | what it tests | verdict | role in paper |
|---|---|---|---|
| **C1 (VLM)** | η/L through frozen CLIP/RobustVLM/DINOv2 towers ranks AutoAttack robustness (tower + per-image); shift-consistency doesn't | **STRONG POSITIVE, verified, confound-broken (n=11)** | **load-bearing second leg / headline of the new work** |
| **B2 (text)** | ρ_G orbit-flip radius; η/L⊥ρ_G; constant-classifier degeneracy | **MIXED: A (radius) + B (orthogonality) GO; C (degeneracy) demote to a lens** | the text leg (excessive-invariance side) |
| **T-DISS (text)** | η/L (first-token refuse margin) predicts L2 jailbreak radius; consistency doesn't | **NEGATIVE / INCONCLUSIVE** (primary partial −0.067, needed >+0.15; gauge-invariance mechanism holds but predictor fails) | honest negative OR re-run with matched margin; NOT a positive leg |

**Key correction vs the inherited plan:** the text leg is NOT "η/L predicts jailbreak robustness like
it predicts VLM robustness" (that is T-DISS, which FAILED). The text leg is B2's **orthogonality**
(η/L ⊥ ρ_G) + **excessive-invariance** (ρ_G radius, degeneracy). See §3.

---

## 1. Scoop verdicts per claim (agent findings + my source checks)

### C1 / VLM — NOT SCOOPED (headline-able)
Novelty intact: {frozen VLM/foundation towers} × {threat-matched η/L = margin / dual-norm input-grad}
× {both cross-tower AutoAttack ranking AND per-image certified-radius ordering} × {paired
shift-consistency null that fails}. Nearest neighbors, all confirmed to miss on ≥1 decisive axis:
- **GREAT Score (2304.09875, ICLR 2023)** — *verified by me (abstract)*. Closest attack-free ranker,
  but generative-manifold confidence margin, plain RobustBench classifiers, no VLM towers, no null.
- **MaCS (2603.05812, 2026)** — *verified by me (abstract)*. Keyword-collision: margin + "consistency"
  + margin-to-sensitivity **ratio with a radius bound**, BUT a training regularizer, noise/blur KL
  (not shift), supervised CNN/ViT (no frozen towers). Referees will raise it → distinguish on 3 axes.
- **RDI (2504.18556)** — attack-free feature-cluster ranker on plain classifiers.
- **Ngnawe margin-consistency (2406.18451)** — within-one-model per-sample bare-margin (no L) detector.
- **Singla-Ge (2103.02695)** — motivation for the null (shift invariance reduces L∞ robustness).
Must-cite+distinguish: 2304.09875, 2603.05812, 2504.18556, 2406.18451, 2103.02695.

### B2-A / ρ_G radius + certificate — NOT SCOOPED (headline-able)
The certificate direction is **inverted** vs all certified-NLP work: CERT-ED (2408.00728),
RS-Del (2302.01757), Text-CRS (2307.16630) certify **prediction-UNCHANGED within radius = good
(meaning-preserving)**; ρ_G certifies the **meaning-CHANGING invariance as a failure** and proves
ρ_G ≥ oracle-robust-radius. Nearest threat "Small Edits, Big Consequences" (2507.15868): same
benign-vs-meaning-critical intuition in generative LLMs but pass-rate not radius, no certificate.
Must-cite+distinguish: 2507.15868, 2408.00728, 2302.01757, 2307.16630, 2002.04599, 2511.13494.

### B2-B / η/L ⊥ ρ_G orthogonality — NOT SCOOPED (headline-able)
No prior work computes a per-item Spearman between an adversarial-margin ratio and a
meaning-changing-invariance radius in LLMs. Distinguish from **Tramèr 2020 (2002.04599)**: that proves
a population-level *tradeoff* (negative dependence) between sensitivity- and invariance-type attacks;
B2 reports **measured per-item orthogonality (≈0)**, a different and more specific object.
Must-cite: 2002.04599, 2605.06458 (invariant-features, computes no such correlation), 2101.00010.

### B2-C / constant-classifier degeneracy — DEMOTE to a lens (NOT a standalone discovery)
**The empirical fact and the lemma are each already published — verified:**
- Negation-blindness of LLMs incl. Llama-3-family: **Naysayers (2306.08189)** *"insensitivity to the
  presence of negation … outputs tend to be similar with or without negation"* (agent read full PDF);
  **EMNLP-2025 "Identical Replies" (2025.emnlp-main.1088)** on **LLaMA-3.1-8B** (agent read full PDF);
  **ScoNe (2305.19426, ACL 2023)** *verified by me it is real & about LLM negation reasoning* — but
  its specific "negation-ignoring baseline matches the model" quote is UNCONFIRMED at abstract level,
  so lean on Naysayers + Identical-Replies, not ScoNe, for the constant-classifier point.
- Ratio-degeneracy lemma (constant classifier ⇒ ∞ margin-ratio, 0 real robustness): **ACR-is-a-Poor-
  Metric (2410.06895)** *verified by me (abstract): "a trivial classifier can have arbitrarily large
  ACR"* — already proven, for randomized smoothing / image classifiers.
- Over-refusal rates: XSTest (2308.01263), OR-Bench (2405.20947) — heavily benchmarked.

**What is genuinely left (the lens, not the fact):** (i) unifying negation-blindness + over-refusal as
ONE ρ_G excessive-invariance failure; (ii) the model-contrast (Llama-3-8B degenerate vs Qwen-2.5-7B
not) as a *ratio-degeneracy diagnostic* rather than an accuracy drop; (iii) importing the vision
ratio-degeneracy lemma into the LLM negation/refusal setting. **Report C as a characterization under
the ρ_G lens, cite all of the above, never as a discovery.** Must-cite: 2305.19426, 2306.08189,
2025.emnlp-main.1088, 2410.06895, 2503.22395 (counter-evidence, same models), 2004.14623 (MoNLI),
2308.01263, 2405.20947.

### Unified cross-modal thesis — NOT SCOOPED
No paper (a) makes the invariance-vs-η/L dissociation-of-predictors claim, (b) makes it across
vision+language, or (c) frames "invariance helps robustness" as a weak-attack artifact erased by
AutoAttack. Closest foil **Singla-Ge (2103.02695)**: a *causal margin* story, vision-only, no
Lipschitz, no FGSM-vs-AA, no AT, no signed correlation — our deltas are threat-matched η/L (not bare
margin), sign-flip under AT, the strong-attack artifact, and the signed correlation. The weak-attack
artifact is a specific unnamed instance of **gradient masking (Athalye 2018, 1802.00420)** — cite as
the parent phenomenon; claim novelty in *identifying invariance as the vector* + *cross-modal
generality* (foundation towers + LLMs, where Athalye's vision-preprocessing analysis is silent).

---

## 2. FRAMING DECISION — one cross-modal paper, VLM-primary (agent-recommended, I concur)

**ONE paper**, scoped honestly as **"vision + VLM primary, LLM as the generalization frontier."**
- Headline: *the invariance/η/L dissociation is a property of foundation models, not a CIFAR quirk.*
- Leg 1 (context, done): the CIFAR paper's dissociation (shift-consistency ⊥/anti robustness; η/L
  predicts; weak-attack artifact).
- **Leg 2 (load-bearing NEW): C1 VLM** — frozen-tower η/L ranks AutoAttack robustness (tower +
  per-image), consistency fails. Metric-compatible with Leg 1 (AA-radius dissociation). This is the
  strongest new leg and the reason the paper is more than a v2 of the vision paper.
- **Leg 3 (frontier): B2 text** — the dissociation survives the jump to discrete generative LLMs,
  instantiated with modality-native operators: η/L ⊥ ρ_G orthogonality (B2-B) + the ρ_G orbit-flip
  radius/certificate (B2-A), with the constant-classifier degeneracy (B2-C) reported as an honest
  boundary condition under the ρ_G lens. Do NOT oversell Leg 3 as identical to Leg 2.
- **T-DISS**: report as an honest negative/limitation — the frozen-encoder η/L→robustness transfer
  does NOT extend to generative-LLM *jailbreak radius* with a first-token margin (likely a threat-
  model mismatch, §3), which *sharpens* the thesis (the dissociation is encoder-level, and the text
  leg is about the invariance axis, not a jailbreak-radius predictor).

**Venue:** ICML/NeurIPS main (phenomenon-generality across foundation models). Fallback TMLR
(receptive to a careful cross-modal empirical phenomenon with honest boundary conditions).

**Reviewer pre-empts to build in:** (1) distinguish Singla-Ge on the 4 axes; (2) run the strongest
attack on every leg (AutoAttack for vision/VLM) so no leg is dismissible as weak-attack-only — this is
our own central mechanism; (3) state the constant-classifier degeneracy up front as a scoping
condition with model-dependence characterized.

---

## 3. The T-DISS negative — what it means and the fork

Independent replication of the harness's exact analysis (verify/TDISS_preliminary_independent.md):
Spearman(R2, r2) = −0.17, AUROC(−R2→vuln) = 0.31, **primary partial(R2, r2 | clean_refuse, M) =
−0.067** (needed >+0.15). Consistency null holds but is moot (R2 also fails). Gauge-invariance
mechanism confirmed (R2_mean exactly constant under logit scaling; fixed-threshold R2 stable while
raw-M's moves) — a valid methods point on a task where the predictor fails.

**Most likely cause = a threat-model mismatch in the harness:** the predictor M is the *first-token*
refuse−affirm anchor margin; the attack radius r2 is for making the model *generate* a harmful
completion over 48 teacher-forced tokens (Llama-Guard-judged). Different decision boundaries → R2's
first-token certificate need not bound r2.

**Fork (decide after the masking/GCG battery lands — it tests whether r2 is a real radius or attack
under-optimization):**
- If masking/GCG confirm r2 is a genuine radius → T-DISS is a real, reportable **negative**: keep it
  as the honest limitation in Leg 3 (the transfer is encoder-level, not decision-boundary-agnostic).
- Optional future run: define M on the SAME affirmative-continuation objective the attack uses
  (M_cont = −loss at δ=0; R2_cont = M_cont/‖∇M_cont‖) and re-correlate. Only then could a positive
  or a strong-negative text-jailbreak claim be earned. NOT required for the paper — Legs 2+3 stand
  without it.

---

## 4. Immediate next steps

1. T-DISS post-pipeline (masking battery → GCG 128×250 → analyze → summarize → figures) is running on
   GPU 0. When SUMMARY.json lands: confirm my numbers, fold in masking/GCG, write TDISS_verification.md.
2. Draft the paper outline from Legs 1-3 + the honest T-DISS limitation, using the must-cite lists here.
3. (Optional, GPU permitting) re-add clip_l14_metaclip to C1 (panel 11→12, not load-bearing); the
   matched-margin T-DISS re-run (only if we want a positive text-jailbreak leg).
