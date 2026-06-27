# Review — "When Does Shift-Invariance Permit Adversarial Robustness? A Margin-Preservation Theory"

**Venue / scale assumed:** ICLR-style, rating **1–10** (8 = accept, 6 = marginally above threshold, 5 = marginally below, 3 = reject). Calibrated against the supplied corpus, with closest comparators: the competing NeurIPS-2025 spotlight *Bridging Symmetry and Robustness* (xDxskDUvte), the ICLR-2024 *Lipschitz-Variance-Margin* poster (C36v8541Ns), the *honest-but-rejected* NeurIPS-2023 *AT without Perturbing all Examples* (aS2Yl8s5OG), and the *narrow-analysis-rejected* ICLR-2025 *ACR is a Poor Metric* (KX5hd1RhYP).

---

## Summary

The paper reconciles two opposing claims in the literature — that shift-invariance *reduces* adversarial robustness (Ge et al. 2021) and that anti-aliasing/invariance *improves* it (Zhang 2019; Grabinski 2022; Saha 2024; and the competing Wang 2025) — by arguing both are regimes of a single scalar: the margin-to-Lipschitz ratio η/L of the discriminative signal that survives projection onto the invariant subspace. Contributions are: (1) a structural theory — an exact identity for the invariant *linear* margin as DC/group-projection separation (Thm 1–2), recovering Ge's 1/√d collapse; a Lipschitz–margin certificate r₂ ≥ η/L completed to a two-sided bracket η/L ≤ r₂ ≤ η/α under a co-Lipschitz condition (Prop "sandwich"); a power-spectrum span lemma; and interpretive reconciliations of Ge and Kamath 2021; (2) an optimization section that pins down orbit rank, proves a margin-free result on orbit-closed data, and proves a lazy/NTK cluster advantage (Thm 4), while leaving the rich-regime trajectory open; (3) an empirical dissection (training-free, then capacity-matched on MNIST/Fashion/CIFAR-10, then PGD-AT across two threats, scaling to PreActResNet-18) arguing that shift-consistency does **not** predict robustness — and anti-predicts it under AT — whereas a threat-matched η/L does, plus a **new graded anti-aliasing control at matched clean accuracy** (Fig. 6).

The proofs I checked (Prop 2 orbit-flip; Thm 4 lazy-cluster; Thm 1; the toy model Thm "toy") are correct. Thm 4 is an honest, correctly-caveated application of Elesedy 2021's projection result to the min-norm interpolant. The gradient-masking diligence (AutoAttack ≤ matched PGD reported in every condition, including the non-differentiable adaptive-polyphase arm) is exactly the box the corpus shows defense papers must tick, and the authors tick it.

---

## Strengths

1. **A genuinely coherent organizing idea, clearly post-Ge.** Theorem 1 recovers Ge's collapse as one corner and the anti-aliasing line as another, on the single η/L axis. This is the "golden thread" the strong-accept Boolean-function paper (xaWO6bAY0xM) was praised for, and it is the paper's best feature. The framing directly engages the competing Wang-2025 spotlight rather than ignoring it (§Related work; §Discussion), positioning shift-consistency as "necessary but not sufficient."

2. **The central empirical dissociation is real and somewhat counter-intuitive.** That shift-consistency carries essentially no information about the robust radius under standard training (Spearman −0.31 / 0.00; 24-cell CI [−0.68,+0.09]) and *anti*-predicts AutoAttack robust accuracy under AT (Pearson −0.88 on CIFAR, −0.81 on ResNet, persisting at partial-corr −0.82 controlling for clean accuracy) is a useful corrective to the anti-aliasing narrative. The exact-cyclic arm with consistency 1.0 and lowest robustness is a clean illustration (Tables 2–4, Fig. 3/5).

3. **Honest scoping.** Open problems are stated plainly (rich-regime trajectory; no universal converse; normalization-dependent Lipschitz; Kamath reconciliation explicitly "an interpretation, not a theorem"). The corpus rewards this (Frame Averaging demoted a vacuous theorem; SAT and the invariance-reg accept both leaned on honest scoping). The gradient-masking checks and the radius-vs-AutoAttack agreement table (mean gap 0.014) are the kind of diligence the DUCAT *reject* (sBpYRQOrMn) failed to provide and the Robustness-Reprogramming *spotlight* (SuH5SdOXpe) provided.

4. **Capacity-matched controls.** Identical parameter counts per width across arms, three seeds, two widths, two threats, plus denser bootstrap grids (24-cell standard, 12-cell AT) with permutation p-values. This is more careful than most of the borderline-accept corpus.

---

## Weaknesses (ranked most-to-least serious)

### W1 — Net contribution is thin for a top venue: classical-core theory + a method-free analysis. *(Abstract; §3.2; §Related "What we add"; §4)*
By the authors' own (commendable) admissions, the load-bearing certificate r₂ ≥ η/L is classical (Hein 2017; Tsuzuku 2018) — "our contribution is not the bound." The genuinely new theory is then: Thm 1 (an elementary projection-separation restatement/generalization of Ge), the two-sided bracket (a co-Lipschitz upper arm that is essentially "if g actually decreases at rate ≥ α along some path, the boundary is within η/α" — the hard part, α, is *assumed*, never established for any realistic network), and Thm 4 (a direct corollary of Elesedy-2021 projection applied to min-norm interpolation). None of these is striking on its own, and the paper proposes **no new method, no new defense, and no SOTA improvement**. The two closest pure-analysis comparators in the corpus — SAT (aS2Yl8s5OG: 5/5/5/7/7, soundness/presentation 4/4) and ACR-is-a-poor-metric (KX5hd1RhYP) — were **both rejected** precisely on "interesting but marginal / narrow contribution, no champion / belongs in a workshop," despite being technically sound. This submission is better-executed and broader than ACR, but it is in the same category and must clear the same bar. The "so what does a practitioner do with η/L?" question (the exact question the SAT AC and ACR reviewer SA4J used to reject) is not answered: η/L is offered as a predictor, never turned into a training objective or selection rule.

### W2 — The NEW graded experiment (Fig. 6) concedes the confound it was built to remove, and rests on a small, unquantified effect. *(§Exp "A graded anti-aliasing control"; Fig. 6)*
This is the headline new piece, so I weight it heavily. It does add something real: across the anti-aliasing family (Rect-2…Bin-7) clean accuracy is matched to within one point (0.729–0.740) while robust accuracy rises and so does η, which is a legitimate control showing invariance *can* help at fixed fitting. But (a) the robustness gain over the matched family is **0.389→0.407 — 1.8 points — across n=2 seeds with no CI or significance test**, while the paper supplies bootstrap CIs and permutation p-values everywhere else (§"Statistical power"); within-family this is not shown to exceed seed noise. (b) For the *decisive* comparison — exact-cyclic vs the rest, i.e. the actual trade-off regime — the authors state plainly that "clean accuracy predicts robustness as strongly as η/L does." The resolution offered ("margin is the upstream quantity both depend on") is an **interpretation, not an intervention**: the experiment that would establish causal mediation (vary margin at fixed clean accuracy *and* fixed invariance for the cyclic contrast) is not run. So in the one regime where the reconciliation has to do work, η/L is not shown to add predictive value over the trivial clean-accuracy baseline. The framing is honest, but it concedes enough that a skeptical reader is left unconvinced that η/L is *the* upstream quantity rather than co-moving with clean accuracy.

### W3 — The most eye-catching numbers are partly tautological, by the authors' own statement. *(§Exp "Statistical power"; Fig. 3; Tables 2–3)*
The η/L–radius Pearson 0.998 is "high by construction" — η/L is a first-order lower bound on r₂ and the models are near-locally-linear, so the correlation "is the across-cell face of the per-sample certificate rather than a separate finding." That is the correct caveat, but it means the abstract's and figures' most prominent statistic is not evidence for the thesis; the actual load-bearing content is the *dissociation* (consistency ⟂ radius). The paper should foreground the dissociation and de-emphasize 0.998, which currently reads as a strong result and is not one.

### W4 — The predictive claim depends on per-threat norm engineering, and effect sizes are moderate with wide CIs. *(§Exp "Under adversarial training"; "Generality"; Table 5)*
"Threat-matched η/L predicts robustness" requires picking the dual-norm gradient per threat: under ℓ∞-AT the ℓ₂ ratio fails (0.55) and only the ℓ₁-gradient ratio works (0.88); under ℓ₂ the matched and mismatched are comparable and the **mismatched is marginally higher** (matched 0.88 vs mismatched 0.91). On MNIST the matched ratio (0.92) barely beats mismatched (0.90). So the "matched beats mismatched" law holds cleanly only in some ℓ∞ conditions, and the predictor is somewhat engineered after the fact. The supporting correlations rest on 8–16 cells with wide CIs (12-cell AT grid: consistency −0.75, CI [−0.92, −0.02]; matched +0.83, CI [+0.49, +0.93]) — suggestive, not decisive.

### W5 — The consistency anti-prediction is fragile and depends on hand-added low-invariance arms. *(§Exp "Scaling to a ResNet backbone"; §"A mechanism…")*
Over the four capacity-matched arms on PreActResNet-18 the consistency anti-correlation is −0.43 (n.s.) and "washes out"; it only reaches −0.81 once two extra low-invariance arms (zero-pad, aliased max-pool) widen the consistency axis. The authors argue "this is the point," and there is a defensible reading (consistency saturates on strong backbones). But a reviewer can equally read it as: the headline anti-correlation is carried by arm selection, and on the realistic architecture family it is not significant. CIFAR-100 is "underpowered at four cells" (Spearman 1.0 over 4 points is not strong evidence). No ImageNet — acceptable for a theory paper per the corpus (Group Downsampling, equivariance spotlight both stayed sub-ImageNet), but it caps the empirical weight.

### W6 — §4 (optimization) is heavy machinery that concludes "open." *(§4; Lemmas bundle/rank; Props rank/generic; Thm 4)*
Four lemmas/propositions and a theorem are deployed to establish that the two canonical orbit constructions are degenerate and that the implicit-bias question "remains open, on the same wall as Frei/Min/Li." This is honest, but the section under-delivers relative to its length and dilutes the thread; much of its payload is offloaded to "a companion technical report." A reader finishes §4 unsure what it added beyond "the obvious testbeds don't work and we couldn't resolve the main question."

### W7 — Minor overclaims and presentation. *(Abstract; §3.3–3.4; Table 1)*
- The abstract says a conv-plus-pool layer "computes power-spectrum features that escape" the Ge collapse, but §3.4 shows the power spectrum is *sign-blind and cannot* separate Ge's canonical ±e_j dot — only the bispectrum can, at an even weaker certified η/L. The "escape" holds for the orthogonal-frequency-span construction, not Ge's headline example; the abstract conflates them.
- "A corrected reconciliation of Kamath" (abstract/intro) is, per §3.4, an interpretation requiring a restatement of their distribution to become a theorem. "Corrected reconciliation" overclaims slightly.
- Number-wall paragraphs ("Generality," "Statistical power," "Scaling to a ResNet") cram many Pearson/Spearman/CI/p values inline; the corpus penalized exactly this density (Lipschitz-Variance-Margin reviewers). Table 1's raw separation 361.9 is uninterpretable without scale.
- The abstract is a single ~300-word block.

---

## Questions for the authors

1. **Graded control (Fig. 6):** what are the per-seed values and a CI / paired test for the 0.389→0.407 matched-family robustness gain? Can you run an actual margin intervention (e.g. margin-maximizing or margin-penalizing training) at fixed clean accuracy *and* fixed invariance arm, so that "margin is upstream" becomes a causal statement rather than a co-variation observation?
2. **Actionability:** does η/L yield anything a practitioner can use — a regularizer, a model-selection rule, a defense — that improves robustness over a matched baseline? A single such result would move this from "diagnosis" to "contribution."
3. **Threat-matching:** since under ℓ₂-AT the mismatched ratio predicts marginally better and under ℓ∞-AT only the ℓ₁ ratio works, is "threat-matched η/L" a law or a post-hoc selection? Please report the matched-vs-mismatched comparison with CIs and a pre-registered rule for choosing the norm.
4. **Co-Lipschitz constant α (Prop sandwich):** can you estimate or bound α for *any* of your trained networks, so the upper arm η/α and κ are more than a hypothesis? Right now the bracket is verified only on the linear case and a power-spectrum surrogate (κ≈1.6–2.4).
5. **Consistency anti-prediction:** report it over a fixed, pre-specified arm set (not arm-selected); is it significant on the four capacity-matched ResNet arms with more seeds, or genuinely only when low-invariance arms are added?
6. Thm 4 compares *certified* Lipschitz constants L_Φ‖f‖_K with a shared L_Φ; how loose is this versus the realized local constant, and does the empirical η/L gap track the orbit-variance term the theorem predicts?

---

## Scores

- **Soundness: 3/4 (good).** Proofs I checked are correct; gradient-masking is properly excluded; controls are careful. Docked because the headline correlation is partly tautological (W3), the upper-bracket arm assumes α without establishing it (W4), and the new graded result lacks significance quantification (W2).
- **Presentation: 3/4 (good).** Coherent thread and strong figures, but dense number-wall paragraphs, a monolithic abstract, and the abstract "escape"/"corrected reconciliation" overclaims (W7).
- **Contribution: 2/4 (fair).** A real but narrow empirical dissociation and a clean organizing scalar, atop a classical certificate, with no new method and no SOTA. Same category as the corpus's two rejected pure-analysis papers, though better executed.

## Overall rating: **5 / 10 — marginally below the acceptance threshold.**
This is a genuine borderline: a sympathetic reviewer who values the reconciliation framing and the consistency anti-prediction could argue 6, and I would not contest a 6 strongly. But weighed against this corpus, where well-executed *method-free* analysis papers (SAT, ACR) were rejected for marginal/narrow contribution despite positive scores and clean rigor, and where the paper's own most-novel new experiment (Fig. 6) concedes the confound and its headline correlation is admitted to be near-tautological, I land just below the bar. A new-method or a causal margin-intervention result would move me to 6–7.

## Confidence: **4/5.** Familiar with the Lipschitz-margin / anti-aliasing / invariance-robustness literature; I checked the requested proofs (Prop 2, Thm 4) and the structural theorems line-by-line. Some empirical reruns I cannot independently verify.

---

## Decision and top-3 fixes

**Decision: weak reject (5), borderline — accept-if-championed.** No fatal flaw; the issue is contribution weight and one under-powered headline experiment, not correctness.

**Top-3 fixes (in priority order):**
1. **Turn the diagnosis into an intervention or a tool.** Either (a) run a margin intervention at fixed clean accuracy and fixed invariance arm to causally establish "margin is upstream" for the trade-off regime, or (b) derive a usable artifact from η/L (regularizer / selection rule / defense) that beats a matched baseline. This is what separates the corpus's accepted understanding papers (Boolean, equivariance) from the rejected ones (SAT, ACR).
2. **Quantify the new graded experiment.** Add seeds, CIs, and a paired significance test for the matched-family robustness gain; re-frame the exact-cyclic contrast honestly as mediation that is *demonstrated*, not asserted.
3. **De-emphasize the tautological 0.998 and the arm-selected anti-correlation; foreground the robust, load-bearing claims with CIs.** Report the consistency anti-prediction over a pre-specified arm set, fix the abstract "escape"/"corrected-reconciliation" overclaims, and break the number-wall paragraphs into qualitative takeaways with the statistics tabulated.
