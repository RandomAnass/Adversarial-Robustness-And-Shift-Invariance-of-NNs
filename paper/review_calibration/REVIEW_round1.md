# Review — "When Does Shift-Invariance Permit Adversarial Robustness? A Margin-Preservation Theory"

**Scale used:** ICLR 1–10 (values 1,3,5,6,8,10; 6 = marginal accept, 5 = marginal reject, 8 = accept), with Soundness / Presentation / Contribution on the 1–4 NeurIPS/ICLR scale. Decision string at the end.

---

## Summary

The paper argues that two apparently opposite findings — Ge et al. 2021 (shift-invariance can *reduce* adversarial robustness) and the anti-aliasing line (better shift-invariance *improves* robustness) — are two regimes of a single quantity: the margin-to-Lipschitz ratio η/L of the invariant feature. It develops three threads. (1) A structural theory: a shift-invariant linear classifier reads the data only through its DC projection, so its margin equals the separation of the DC-projected classes (Thm 1), generalized to any finite group (Thm 2); a convolution+quadratic-pool layer computes power-spectrum features that can separate signal linear invariance discards (Lemma 1); the Lipschitz-margin certificate r₂ ≥ η/L is "completed" to a two-sided bracket η/L ≤ r₂ ≤ η/α with κ = L/α (Prop 2); and Ge 2021 and Kamath 2021 are recovered/reconciled as the small-η/L corner. (2) An optimization thread: the rank of a shift orbit (Lemma 3), a proof that invariance is "margin-free" on orbit-closed data, a demonstration that the two canonical orbit constructions are degenerate testbeds (Prop 5), and a lazy/NTK result that on cluster data the invariant architecture reaches a larger η/L. (3) Experiments: a training-free separation test, a capacity-matched architectural dissection on MNIST/Fashion/CIFAR-10, and PGD-AT experiments scaling to PreActResNet-18, with the headline claims that a threat-matched η/L predicts the robust radius / AutoAttack accuracy (Pearson up to ~0.9–0.998) while shift-consistency does not and, under AT, *anti*-predicts it; plus per-sample certificate and an "AT inverts the margin–sensitivity coupling" observation.

The author states explicitly (end of §1) that "this is a consolidation document in a technical-report register," and several proofs of *claimed contributions* are deferred to a "companion technical report."

## Strengths

1. **The reconciliation framing is useful and the question is real.** Placing Ge 2021 and the anti-aliasing results on a common axis (does invariance preserve discriminative margin relative to sensitivity?) is a clean way to organize a genuinely confusing literature, and §5 (Related work, "the two regimes") states it crisply.

2. **The capacity-matched dissection is a good experimental design.** Holding the parameter count fixed across four arms that differ only in the shift-invariance operator (standard / anti-aliased / exact-cyclic / shift-augmented; Table 3) is exactly the controlled comparison the field usually skips, and the margin/Lipschitz decomposition in Fig. 3 (anti-aliasing lowers L at fixed margin; exact-cyclic shrinks margin) is the most informative single result in the paper.

3. **Unusual and welcome honesty.** The paper repeatedly scopes its claims (η/L "is a lower-bound certificate with no general converse"; the rich-regime trajectory "remains open"; Kamath reconciliation is "an interpretation… a self-contained restatement would be needed to make it a theorem"; the exact-cyclic clean-accuracy confound is disclosed). This register matches accepted papers in the calibration set far better than typical overclaiming.

4. **Gradient-masking controls are present.** Reporting AutoAttack ≤ matched PGD throughout, validating DDN radii against a closed-form linear radius, and cross-checking r₂ against AutoAttack at small ε (mean abs. gap 0.014, §"Capacity-matched CIFAR-10 dissection") is the right diligence and pre-empts the most obvious attack on the radius metric.

## Weaknesses (most to least serious)

### 1. The headline theory either overlaps prior work or is not in the paper. (Soundness / Contribution)

- **Theorem 1 substantially overlaps Ge et al. 2021.** The submission's central structural result — a shift-invariant linear classifier sees the data only through its DC component, and its margin equals the DC-projected separation — is, per Ge et al. 2021 themselves, what that paper already proves ("characterizes the margin between classes when a shift-invariant linear classifier is used, showing that the margin can only depend on the DC component of the signals"). The submission presents this as its own contribution (§1 bullet 1; Thm 1, §3.1) and only later (§3.4) uses Ge for the 1/√d *recovery*. The genuine delta over Ge — arbitrary finite separable datasets, the convex-hull/interval form, and the finite-group generalization (Thm 2) — is real but incremental, and the paper never delineates it against Ge's own margin characterization. As written, a reader could mistake a restatement of Ge for a new theorem.

- **Two of the paper's advertised new results have no proof in the paper.** Proposition 2 (the two-sided bracket η/L ≤ r₂ ≤ η/α — sold in the abstract and §1 as "a characterization up to a condition number" and the "matching arm" that turns Tsuzuku's one-sided certificate two-sided) ends with "The full proof is in the companion technical report." The lazy/NTK cluster theorem (§4, the only optimization result the paper calls "now a theorem") is likewise attributed to the "companion technical report." For a conference submission these are not self-contained; reviewers cannot verify the very claims that are foregrounded. Worse, Prop 2 as *stated* is under-specified: "L-Lipschitz toward the boundary" and "a co-Lipschitz constant α along a path reaching it" are not made rigorous, and the upper bound r₂ ≤ η/α requires the network to actually realize sensitivity α all the way to the nearest decision boundary — an instance-specific, generally false-or-vacuous assumption outside the linear case (where it is trivial, r₂ = η/‖w‖). Either the bracket is trivial (linear) or its hypotheses are not established. This needs to be a fully stated, fully proved theorem *in the paper* or dropped from the contributions.

### 2. The flagship empirical correlation is close to definitional. (Soundness / framing)

η/L is, by construction, a first-order *lower bound* on r₂, and the paper's own per-sample analysis shows M/‖∇M‖₂ ≈ r₂ with Spearman ≈ 0.91–0.95 because the networks are locally near-linear (§"The certificate holds per sample"). It then reports η/L vs r₂ at Pearson 0.998 across eight cells (Fig. 2) as the central finding. But if margin/gradient-norm ≈ distance-to-boundary for these models, then "η/L predicts r₂" is largely a restatement of local linearity — a long-known property of these (non-1-Lipschitz, smallish) networks — not a discovery about shift-invariance. The quantity that is *not* tautological is the **contrast**: shift-consistency does not predict, and under AT it anti-predicts. The paper should foreground that contrast and stop presenting 0.998 as if it were the result; as stated it invites the reading that the headline number is baked in. (Reviewers in the calibration set, e.g. the LVM-RS thread, were explicit that "we don't demonstrate a correlation" claims must be stated precisely.)

### 3. The genuinely novel empirical claim (consistency anti-predicts; AT sign-flip) is underpowered and confounded. (Soundness)

- **It rests on one outlier arm with a clean-accuracy confound.** In every table the "exact cyclic" arm is the single point driving the negative correlation: consistency 1.0, lowest robustness — but *also* the lowest clean accuracy by a wide margin (0.57–0.63 vs 0.69–0.78 under AT, Table 4; 0.711–0.769 vs 0.804–0.854 in Table 6). With only four arms, one of which under-fits, "consistency anti-predicts robustness" is hard to separate from "the model that fits worst is least robust." The ResNet partial correlation (−0.82 controlling for clean accuracy) and the per-arm tables help, but the core dissociation still leans on a handful of cells and a confounded extreme point. A within-arm manipulation that varies consistency *without* collapsing clean accuracy (e.g. graded anti-aliasing strength, or matched-clean-accuracy exact-invariant variants) would be far more convincing than four widely-separated arms.

- **Sample sizes are thin and the strong-correlation cells are few.** The AT dissections are 2 seeds × 4 arms × 2 widths; the "statistical power" paragraph adds a 24-cell standard grid and a 12-cell AT grid with bootstrap CIs, which is the right instinct, but the AT anti-prediction CI is wide ([−0.92, −0.02], p = 0.006) and the headline 0.998 lives on the standard-training side where the metric is near-definitional (point 2). CIFAR-100 is "underpowered at four cells" by the author's own admission (§"Scaling to a ResNet backbone").

- **The "AT inverts the margin–sensitivity coupling" result is not tied to shift-invariance.** The −0.5 → +0.5 Spearman flip (Fig. 6) is presented as a finding, but it is a statement about adversarial training in general, holds for all arms, and has no demonstrated connection to the shift-invariance thesis of the paper. It reads as an interesting but orphaned observation. Its relation to known AT-curvature/gradient-alignment results (Moosavi-Dezfooli 2019; Tsipras 2019), which the paper cites, should be made quantitative rather than asserted as a new "sign."

### 4. The optimization section (§4) is almost entirely negative/open and does not support the narrative. (Contribution)

Lemma 3 (orbit rank = #nonzero Fourier coeffs) and Props 4–6 are correct but modest, and their punchline is that the two textbook constructions are degenerate and *generic* orbit data is not — i.e., the section establishes that the interesting case exists but does not analyze it ("the rich-regime trajectory remains open… on the same wall reached by Frei 2023, Min 2024, Li 2025"). The one positive theorem (lazy/NTK) is deferred to the companion report (point 1). As a result §4 occupies ~20% of the paper to conclude "we don't yet know," which is honest but weakens the case for a conference contribution rather than strengthening it.

### 5. The per-sample "certificate" is largely margin-consistency, already published. (Contribution)

The claim that M(x)/‖∇M(x)‖₂ predicts a point's own robust radius is, as the paper acknowledges (citing Ngnawe et al. 2024, "ngnawe2024detecting"), margin consistency in robust classifiers — and the broader literature already notes "Lipschitz continuity of the feature extractor does not imply margin consistency." The paper is fair in citing this, but it then leans on the per-sample result as evidence for its thesis; the incremental content here is small.

### 6. Presentation: reads as a consolidation/technical report, not a focused paper. (Presentation)

- The abstract is a single ~400-word paragraph that tries to state every result at once; it is essentially unreadable as an abstract and contains no qualitative takeaway a non-expert could retain.
- The experiments section is extremely number-dense (dozens of Pearson/Spearman values, multiple thresholds, CIs) with very few sentences telling the reader what to conclude. Paragraphs such as "Generality across datasets and threats" enumerate +0.92 / −0.44 / +0.88 / +0.91 etc. without a single qualitative synthesis.
- The author's own framing ("a consolidation document in a technical-report register; full proofs are in Appendix") signals that this is a TR excerpt. Conferences want a self-contained, focused argument, not a digest with proofs elsewhere.
- Single author, single venue style file in *preprint* mode with the author's real name — fine for a TR, but for the actual submission the deferred-proof structure and external companion report will be a hard blocker on verifiability and likely on double-blind compliance.

### 7. Novelty positioning vs. the closest competitor is missing.

The mechanism the paper invokes (orbit-averaging as a non-expansive RKHS projection, off-orbit gradient suppression, Lipschitz constancy across the orbit) is precisely the machinery of *Bridging Symmetry and Robustness: On the Role of Equivariance in Enhancing Adversarial Robustness* (NeurIPS 2025 spotlight), which proves equivariant convolutions preserve the Lipschitz constant across the group orbit and suppress off-orbit gradients. That paper is not cited or distinguished. The author should position the present η/L dissection against it explicitly; right now an informed reviewer will see strong conceptual overlap on the "helps" side.

## Questions to the authors

1. State precisely what Theorem 1 adds beyond Ge et al. 2021's own DC-margin characterization. Is the delta only (i) general finite datasets, (ii) the interval/convex-hull form, and (iii) the finite-group generalization? If so, please say so in-text.
2. Please provide the full statement and proof of Proposition 2 *in the paper*, with explicit, verifiable hypotheses. Outside the linear case, when does a co-Lipschitz constant α "along a path reaching the boundary" exist, and why is r₂ ≤ η/α not vacuous? Give a non-linear, non-toy example where the upper arm is informative (κ bounded) and α is computable.
3. The 0.998 η/L–r₂ correlation under standard training: how much of it survives if you regress out the per-sample local-linearity (i.e., is η/L predictive of r₂ *beyond* M/‖∇M‖ ≈ r₂)? What is the across-arm variance of the gap r₂ − η/L?
4. Can you decouple "exact-cyclic is least robust" from "exact-cyclic under-fits"? E.g., match clean accuracy across arms (longer training / higher capacity for the invariant arm), or vary anti-aliasing strength continuously within one architecture so consistency moves without a clean-accuracy collapse.
5. Is the −0.5 → +0.5 margin–sensitivity sign flip specific to shift-invariant models, or identical across all arms and on a fully-connected baseline? If the latter, why is it in a shift-invariance paper?
6. Please position the orbit-averaging / off-orbit-gradient mechanism against the NeurIPS 2025 "Bridging Symmetry and Robustness" spotlight.

## Scores

- **Soundness: 2 (fair).** What is proved in-paper is correct, but the two foregrounded new results (two-sided bracket, lazy/NTK) are not proved here, the headline empirical correlation is near-definitional, and the novel empirical claim is confounded and thinly powered.
- **Presentation: 2 (fair).** Dense, technical-report register; a one-paragraph all-in abstract; number-heavy experiment prose with few qualitative takeaways; key proofs offloaded to an external document.
- **Contribution: 2 (fair).** The reconciliation framing and the capacity-matched decomposition are genuinely useful, but the structural theorem overlaps Ge, the certificate is classical, the optimization section is mostly open, and the per-sample result is largely published margin-consistency.

**Overall rating: 3 (reject) — a high/borderline 3, between weak-reject and reject.** The paper is honest, competently executed, and asks a good question, but its theoretical centerpiece either restates Ge or is unverifiable in-paper, its flagship empirical number is close to tautological, and the one non-obvious empirical claim rests on a confounded outlier arm at small sample size. This is the same failure mode as the calibration's NeurIPS-2023 "Subset AT" paper (interesting, honest, well-run, but contribution judged marginal and no champion → reject) compounded by self-containedness problems the field treats more harshly.

**Confidence: 4.** I am confident in the assessment of soundness, novelty overlap, and experimental design; I am less able to check the deferred proofs (they are not in the paper) and have not re-derived the lazy/NTK claim.

---

## Decision and top-3 fixes

**Decision: Reject** (for the current cycle). The core issues are structural, not rebuttal-sized: the headline theorem's overlap with Ge, the missing in-paper proofs of advertised results, and the near-definitional nature of the flagship correlation. With a focused rewrite the work could become a solid paper.

**Top-3 highest-leverage changes:**

1. **Make the theory self-contained and clearly post-Ge.** Bring the Proposition-2 bracket and the lazy/NTK theorem into the paper with full, verifiable hypotheses and proofs, or remove them from the claimed contributions. Add one explicit sentence stating exactly what Theorem 1 adds beyond Ge et al. 2021's DC-margin result. (Addresses Weaknesses 1, 4.)

2. **Reframe the empirical claim around the dissociation, not the 0.998.** Lead with "shift-consistency does not (and under AT anti-) predict robustness, whereas a threat-matched η/L does," demote the near-tautological η/L–r₂ correlation, and *show* η/L adds information beyond local linearity. (Addresses Weakness 2.)

3. **Kill the exact-cyclic confound.** Replace the four-arm, one-outlier design with a manipulation that varies shift-consistency while holding clean accuracy fixed (graded anti-aliasing, or clean-accuracy-matched invariant arms), with more seeds/cells and CIs, so the consistency anti-prediction is not attributable to under-fitting. (Addresses Weakness 3.)

Secondary: rewrite the abstract as prose with a qualitative takeaway; add qualitative synthesis sentences to the experiments; cite and distinguish the NeurIPS-2025 equivariance-robustness spotlight.
