# Paper build plan — "Invariance is not robustness: a foundation-model dissociation"

Working title (placeholder): **The Invariance–Robustness Dissociation Generalizes to Foundation
Models.** Standalone paper; the CIFAR result is our PRIOR work, cited as the origin, not a leg to
re-run. Structure per SYNTHESIS_lit_and_framing.md §2: VLM-primary, LLM-frontier, T-DISS honest
limitation. Venue target ICML/NeurIPS main; fallback TMLR. All numbers below are from the VERIFIED
docs (verify/C1_verification.md, verify/B2_verification.md, verify/TDISS_preliminary_independent.md).

Writing rules (hard): plain language, no jargon stacks, no glued words, no "win", no em-dashes, no
AI-tells, define every term at first use, narrative flow, captions match figures, honest scoped
claims. Define η/L, shift-consistency, ρ_G, gauge, threat-matched at first use.

---

## Thesis (one sentence)
A threat-matched margin-to-Lipschitz ratio η/L predicts adversarial robustness while
invariance (shift-consistency in vision, paraphrase/orbit-invariance in language) does not — and this
dissociation, first shown on CIFAR classifiers, holds through frozen vision-language encoders and
instruction-tuned LLMs. "Invariance helps robustness" is a weak-attack artifact.

---

## §1 Introduction
- Hook: the field treats shift/format invariance as a robustness virtue; we show it does not predict
  adversarial robustness in foundation models, and a threat-matched η/L does.
- Define η/L = mean signed logit-margin M(x)=f_y−max_{j≠y}f_j over correctly-classified clean inputs,
  divided by mean dual-norm input-gradient ‖∇_x M‖_q (q=1 for L∞, q=2 for L2). Gauge-free (invariant
  under logit rescaling f→cf). Certificate reading: robust radius ≥ η/L.
- Contributions: (1) VLM: η/L is an attack-free cross-tower AND per-image robustness predictor;
  shift-consistency is not. (2) LLM: sensitivity (η/L) and invariance (ρ_G orbit-flip radius) are
  orthogonal axes; ρ_G is a certifiable radius; a model-dependent constant-classifier degeneracy is
  the excessive-invariance boundary. (3) Honest scope: the transfer is encoder-level — it does not
  extend to generative-LLM jailbreak radius with a first-token margin (T-DISS).
- Frame the weak-attack artifact as a named instance of gradient masking (Athalye 2018, 1802.00420).

## §2 Related work (must-cite + one-line distinction each — from SYNTHESIS §1)
- Attack-free robustness ranking: GREAT Score (2304.09875, generative-manifold, plain classifiers),
  RDI (2504.18556, feature-cluster). Ours: margin/Lipschitz ratio on frozen VLM towers + per-image.
- Margin/Lipschitz predictors: Ngnawe (2406.18451, within-model per-sample bare margin, no L),
  MaCS (2603.05812, training regularizer, noise/blur consistency not shift, no towers).
- Invariance vs robustness: Singla-Ge (2103.02695, causal margin story, vision, no η/L, no AT, no
  strong-attack artifact); Tramèr 2020 (2002.04599, population tradeoff, not measured orthogonality).
- Certified NLP (opposite direction): CERT-ED 2408.00728, RS-Del 2302.01757, Text-CRS 2307.16630.
- Negation-blindness / over-refusal (for the degeneracy lens): Naysayers 2306.08189, Identical-
  Replies EMNLP-2025, ScoNe 2305.19426, ACR-poor-metric 2410.06895 (ratio lemma), XSTest 2308.01263,
  OR-Bench 2405.20947, MoNLI 2004.14623.
- VLM robustness governed by tower: 2407.11121. FARE 2402.12336.

## §3 The dissociation on CIFAR (brief recap of prior work, cited)
One paragraph + one figure reused/cited: η/L predicts robustness (Pearson ~0.998 across arms),
shift-consistency anti-predicts under adversarial training (Linf −0.88), threat-matched η/L predicts
AutoAttack (+0.90); FGSM shows invariance "helping," AutoAttack erases it. Sets up the generalization.

## §4 Foundation-model vision encoders (LEG 2 — LOAD-BEARING) [LOCKED]
Claim: η/L through frozen CLIP/RobustVLM/DINOv2 vision towers is an attack-free predictor of
AutoAttack (APGD-CE+APGD-T) robustness; shift-consistency is not.
Setup: 11-tower panel (4 AT: FARE2/4, TeCoA2/4; 7 non-AT: CLIP, DINOv2, 5 CLIP variants), zero-shot
ImageNet-100, clean η/L + shift-consistency, AutoAttack radius per image.
- **Fig 1 (tower axis):** η/L vs robust acc, Pearson **+0.953** [0.92,1.0]; partial | is-AT = **+0.51**;
  cosine-consistency +0.81 collapses to **+0.15** | is-AT; SC_pred n.s. +0.37. Selection regret: η/L
  5 pts vs SC_pred/clean 88 pts.
- **Fig 2 (per-image, THE headline):** Spearman(per-image η/L₁, robust radius) = **+0.78** [0.75,0.81]
  pooled AT, and **+0.54..+0.79 within each non-AT CLIP tower**; shift-consistency **+0.12 / ≈0**.
- **Fig 3 (weak-attack artifact in VLMs):** every non-AT tower S_fgsm 0.16–0.46 but S_apgd=S_pgd40=0.0.
- Honest limitation: non-AT towers all tower-level S≈0, so tower-axis range comes from AT; the
  powered claim is per-image (both AT and non-AT). No gradient masking (APGD≤PGD40≤FGSM, Square≥APGD).
Source: verify/C1_verification.md.

## §5 Instruction-tuned LLMs (LEG 3 — FRONTIER) [LOCKED except degeneracy framing]
Claim: in LLMs the sensitivity axis (η/L) and the invariance axis (ρ_G orbit-flip radius) are
orthogonal; ρ_G certifies a robust radius; excessive invariance appears as a model-dependent
constant-classifier degeneracy.
Setup: Llama-3-8B-Instruct (+ Qwen-2.5-7B contrast), 1600-item corpus (sentiment antonym/negation,
MoNLI negation-NLI, PKU harmful→benign), deterministic non-circular oracle (NLI model = filter only).
- **§5.1 ρ_G radius + certificate (B2-A):** ρ_G(x) = smallest meaning-changing edit the model stays
  invariant to (token-edit + embedding-L2). Certificate ρ_G ≥ oracle-robust-radius (prop:rhoG).
  Report the ρ_G distribution; the certificate is a theorem, not the (retracted) "100% budget-law."
- **§5.2 Orthogonality (B2-B):** Spearman(η/L task-class margin, ρ_G_emb) = **−0.025 [−0.09,+0.04]**,
  a clean null → sensitivity ⊥ invariance. (Old −0.11 was a mis-specified-margin artifact, dropped.)
- **§5.3 Excessive-invariance degeneracy (B2-C — as a LENS, not a discovery):** per-family orbit-flip
  decomposition: sentiment **0.67** genuine (clean-antonym 0.673) vs NLI **1.00** / safety 0.62
  constant-classifier degeneracy (model answers "entailment" on 100%, "refuse" on 97%; Qwen differs).
  Cast as the ratio-degeneracy lemma instance; cite the known negation-blindness/over-refusal work and
  the ACR lemma; claim only the unification + model-contrast diagnostic.
Source: verify/B2_verification.md (§3e fixes).

## §6 Where the transfer stops: generative-LLM jailbreak radius (T-DISS) [PENDING masking/GCG]
Honest negative: a first-token refuse-margin η/L does NOT predict the L2 jailbreak radius
(Spearman −0.17, primary partial −0.067; consistency also null). Gauge-invariance mechanism is
confirmed (R2_mean exactly constant under logit scaling; fixed-threshold R2 stable). Diagnose the
first-token-margin vs multi-token-attack threat-model mismatch. This sharpens the thesis: the
dissociation is encoder-level; the LLM invariance story (§5) is about the invariance axis, not a
jailbreak-radius predictor. [FINALIZE after masking/GCG confirm r2 is a real radius, not
attack-underoptimization — verify/TDISS_preliminary_independent.md §"Still pending".]

## §7 Discussion / limitations
- The dissociation is a property of the representation/encoder; decision-boundary-specific transfer
  (multi-token generation) needs a matched margin (future work).
- Constant-classifier degeneracy is model-dependent; report as scope, not a universal claim.
- Threats to validity: panel size on the tower axis (per-image is the powered claim); oracle noise on
  sentiment negation (antonym subset is clean); ρ_G embedding geometry is coarse (lead with token-edit).

## Figures/tables checklist
- [ ] F1 tower η/L-vs-robust + partial-correlation bars (C1 §3a)
- [ ] F2 per-image η/L-vs-radius, AT pooled + non-AT within-tower (C1 §3b)  ← headline figure
- [ ] F3 FGSM-vs-APGD weak-attack artifact bars (C1 §3c)
- [ ] F4 ρ_G distribution + certificate schematic (B2 §5.1)
- [ ] F5 η/L ⊥ ρ_G scatter, null (B2 §5.2)
- [ ] T1 per-family flip decomposition (B2 §5.3)
- [ ] F6 T-DISS negative: η/L-vs-jailbreak-radius null + gauge-invariance panel (§6)

## Build order
1. [after T-DISS] finalize §6 framing.
2. Draft §4 (locked) → §5 (locked) → §3 recap → §6 → §1/§2 → §7. Prose in the paper venv.
3. Generate F1–F6/T1 from the cached result JSONs (scripts already exist per pilot).
