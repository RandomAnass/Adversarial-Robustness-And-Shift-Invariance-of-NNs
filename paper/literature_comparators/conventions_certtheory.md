# Writing & Organization Conventions: Certified-Robustness Theory Papers

Two published comparators, read end to end (main body + all appendices). This catalogues **how they present and organize results**, not the math. Use it as a template for restructuring a theory+empirical adversarial-robustness paper.

PDFs saved in this folder:
- `cohen2019.pdf` — Cohen, Rosenfeld, Kolter, "Certified Adversarial Robustness via Randomized Smoothing", ICML 2019 (arXiv:1902.02918v2). 36 pages.
- `tsuzuku2018.pdf` — Tsuzuku, Sato, Sugiyama, "Lipschitz-Margin Training: Scalable Certification of Perturbation Invariance for Deep Neural Networks", NeurIPS 2018 (arXiv:1802.04034v3). 18 pages.

---

## Paper 1 — Cohen et al. 2019 (Randomized Smoothing)

### COUNTS (main body vs appendix)

Document structure: main body = pp. 1-8 (Intro, Related Work, §3 Randomized smoothing, §4 Experiments, §5 Conclusion); acknowledgements + references pp. 8-12; **Appendices A-J = pp. 13-36 (24 pages, 3x the main body).**

| Result type | Main body | Appendix | Notes |
|---|---|---|---|
| Theorem | **2** (Thm 1, Thm 2) | 1 new (Thm 6, App D) + Thm 1 & 2 *restated* (App A) | "Thm 1 (binary case)" is a restatement in main for the sketch |
| Proposition | **2** (Prop 1, Prop 2) | 5 new (Prop 3-6 App B, Prop 7 App G) + Prop 1 & 2 *restated* (App C) | |
| Lemma | 0 | **3** (Lemma 3, 4, 5) | all in appendix |
| Corollary | 0 | 0 | none anywhere |
| Remark | 0 | 1 ("Remark: connection to statistical hypothesis testing", App A) | unnumbered |
| Definition | 0 numbered | 0 numbered | `g` defined inline as Eq (1) |
| Claim | 0 | 4 (deferred-algebra claims, App A) | unnumbered "Claim." |

Counter quirk worth copying: **Theorem and Lemma share one counter** (Thm 1, Thm 2, Lemma 3, Lemma 4, Lemma 5, Thm 6 — continuous 1-6), while **Proposition has its own counter** (Prop 1-7). This is the standard amsthm `\newtheorem{lemma}[theorem]` setup.

### NAMING — what is a Theorem vs Prop vs Lemma

Clean "headline = Theorem" discipline:
- **Theorems = the 2 novel headline results.** Thm 1 = the tight robustness guarantee (the paper's whole point); Thm 2 = the matching tightness/converse. Thm 6 (appendix) = the statistical machinery to convert "approximate" to a high-probability bound — still a Theorem because it is a self-contained probabilistic statement.
- **Propositions = operational / correctness / special-case results.** Prop 1 & 2 = correctness guarantees of the Monte-Carlo `PREDICT`/`CERTIFY` algorithms; Prop 3-6 = the linear-classifier special case (illustrative); Prop 7 = resolution-scaling argument.
- **Lemmas = standard imported tools.** Lemma 3 & 4 = Neyman-Pearson restatements; Lemma 5 = an elementary Gaussian-interval monotonicity fact.

Main Theorem statement style (full quote, Thm 1):
> "**Theorem 1.** Let f : ℝ^d → Y be any deterministic or random function, and let ε ∼ N(0, σ²I). Let g be defined as in (1). Suppose c_A ∈ Y and p_A, p_B ∈ [0,1] satisfy: P(f(x+ε)=c_A) ≥ p_A ≥ p_B ≥ max_{c≠c_A} P(f(x+ε)=c). Then g(x+δ) = c_A for all ‖δ‖₂ < R, where R = (σ/2)(Φ⁻¹(p_A) − Φ⁻¹(p_B))."

Style notes: terse "Let… Suppose… Then…" template; the theorem is immediately followed by a bulleted list of plain-language "observations about Theorem 1" (e.g. "Theorem 1 assumes nothing about f. This is crucial since it is unclear which well-behavedness assumptions, if any, are satisfied by modern deep architectures.").

### PROOF PLACEMENT
**Sketch in main + full in appendix.** Explicit handoff sentence:
> "The complete proofs of Theorems 1 and 2 are in Appendix A. We now sketch the proofs in the special case when there are only two classes."

A "Theorem 1 (binary case)" with a labelled "*Proof sketch.*" (ending in a QED box) sits in the main text; the rigorous general proof (via Neyman-Pearson) is fully deferred. Roughly 100% of rigorous proofs are in the appendix; the main body carries only the 2-class sketch.

### MAIN vs APPENDIX SPLIT
- **Main (8 pp):** the 2 headline theorems (with sketch), the practical algorithms (pseudocode + Prop 1/2), and the *figures* of the experiments (Figs 5-8 + Table 1 ImageNet headline). Reads as a self-contained narrative.
- **Appendix (24 pp):** A = full proofs; B = linear-classifier analysis (Prop 3-6); C = algorithm helper details + Prop 1/2 restated proofs; D = Bernstein conversion to high-prob bound (Thm 6); **E = the full result tables (Tables 2-4) deferred out of main**; F = training-with-noise justification; G = resolution-scaling (Prop 7); H = extra baseline comparisons; I = re-derivation of prior guarantees in this paper's notation; J = experimental setup / attack details / hyperparameters.

### THEORY ↔ EMPIRICAL INTEGRATION
Strong, explicit, bidirectional:
- A dedicated **"Empirical tightness of bound"** paragraph turns a theorem into an experiment: *"When f is linear, there always exists a class-changing perturbation just beyond the certified radius. Since neural networks are not linear, we empirically assessed the tightness of our bound by subjecting an ImageNet smoothed classifier … to a projected gradient descent-style adversarial attack … We succeeded 17% of the time at radius 1.5R and 53% of the time at radius 2R."*
- **Figures cite the theorem they illustrate.** Fig 8 caption: *"Left: certified accuracies obtained using our Theorem 1 versus those obtained using the robustness guarantees derived in prior work."* Fig 9 caption: *"Illustration of the proof of Theorem 1."* Fig 5 caption references "our Theorem 1 guarantee".
- Conclusion re-anchors on the theorem: *"Theorem 2 establishes that smoothing with Gaussian noise naturally confers adversarial robustness in ℓ₂ norm…"*

### CLAIM STRENGTH / HEDGING
- Strong where proven: *"we prove the first tight robustness guarantee for randomized smoothing"*; *"We prove a tight robustness guarantee in ℓ₂ norm for smoothing with Gaussian noise."*
- Hedged for speculation: *"Our strong empirical results suggest that randomized smoothing is a promising direction for future research…"*; *"We suspect that other, as-yet-unknown noise distributions might induce robustness to other perturbation sets…"*
- Limitations get a **dedicated flagged paragraph**: *"Randomized smoothing has one major drawback. If f is a neural network, it is not possible to exactly compute the probabilities with which f classifies N(x,σ²I)…"* Assumptions are also surfaced inline as "observations" right after the theorem.

### CITING FOUNDATIONAL / STANDARD RESULTS
Mixed but principled:
- A standard result that is *used structurally in a proof* is **restated as a named, numbered Lemma with attribution**: *"**Lemma 3 (Neyman-Pearson).** …"* prefaced by *"which is essentially a restatement of the Neyman-Pearson lemma (Neyman & Pearson, 1933) from statistical hypothesis testing"*, plus an unnumbered Remark drawing the connection.
- A standard result merely *invoked* is **cited, not restated**: Clopper-Pearson interval (cited via `statsmodels`), Bernstein's inequality (*"Bernstein's inequality (Blanchard, 2007) guarantees that…"* inside the Thm 6 proof).

---

## Paper 2 — Tsuzuku et al. 2018 (Lipschitz-Margin Training)

### COUNTS (main body vs appendix)

Document structure: main body = pp. 1-8 (Intro, §2 Related work, §3 Problem formulation, §4 Calculation+enlargement of guarded area, §5 Calculation of Lipschitz constant, §6 Numerical evaluations, §7 Conclusion); references pp. 9-11; **Appendices A-G = pp. 12-18 (7 pages, slightly shorter than main).**

| Result type | Main body | Appendix | Notes |
|---|---|---|---|
| Theorem | **3** (Thm 1, 2, 3) | 0 | all theorems in main |
| Proposition | **2** (Prop 1, Prop 2) | 0 | the certification conditions |
| Corollary | **1** (Cor 1) | 0 | convolution operator-norm bound |
| Lemma | 0 | **2** (Lemma 1 App A, Lemma 2 App D) | helper lemmas only |
| Remark | 0 | 0 | none |
| Definition | 0 numbered | 0 numbered | threat model / defense goal / margin all defined inline (Eq 1, M_{F,X}) |

All numbered statements use one shared counter (Thm/Prop/Cor/Lemma interleave continuously is NOT used here; each type appears to carry its own simple numbering: Thm 1-3, Prop 1-2, Cor 1, Lemma 1-2).

### NAMING — what is a Theorem vs Prop vs Lemma (CONTRAST with Cohen)
This paper does **not** follow "headline = Theorem". Instead:
- **Propositions = the conceptual core, stated as simple implication conditions.** Prop 1 and Prop 2 are the actual certification principle (margin ≥ √2·L·‖ε‖ ⇒ no class change). They are the most-used results in the experiments, yet are Propositions because each is a short, directly-derived condition.
- **Theorems = the harder / more general technical machinery.** Thm 1 (power-iteration converges to the operator norm), Thm 2 (high-probability error bound on the estimated operator norm), Thm 3 (Lipschitz bound for concatenated pooling/activation layers). These are "Theorems" because they are technically heavier and more general, not because they are the marquee claim.
- **Corollary = direct consequence of a Theorem:** Cor 1 (convolution operator-norm ≤ √n‖W'‖) follows from Thm 3.
- **Lemmas = elementary helpers**, banished to the appendix (Lemma 1: a max-difference inequality; Lemma 2: concatenation Lipschitz bound).

Representative statement styles (terse, implication-form):
> "**Proposition 1.** (M_{F,X} ≥ √2 L_F ‖ε‖₂) ⇒ (M_{F,X+ε} ≥ 0)."

> "**Theorem 3.** Define f(Z) = (f₁(Z¹), …, f_Λ(Z^Λ)), where Z^λ ⊂ Z and ‖f_λ‖₂ ≤ L for all λ. Then, ‖f‖₂ ≤ √n L, where n := max_j |{λ | x_j ∈ Z^λ}| and x_j is the j-th element of x."

### PROOF PLACEMENT
**All proofs in appendix; each result followed by a one-line pointer to its proof location** (cleaner than Cohen — no sketches in main):
- Prop 1: *"The details of the proof are in Appendix A."*
- Thm 1: *"The proof is found in Appendix C.1."*
- Thm 2: *"The proof is in Appendix C.3, which is mostly from Friedman [10]."*
- Thm 3: *"The proof, whose idea comes from Cisse et al. [8], is found in Appendix D.1."*
- Cor 1: *"The proof of Corollary 1 is in Appendix D.2."*

### MAIN vs APPENDIX SPLIT
- **Main (8 pp):** every numbered Theorem/Prop/Corollary, the two training algorithms (Alg 1 LMT, Alg 2 operator-norm calc, shown as boxed figures), the bound-comparison figure (Fig 3), and all headline experiments (§6: tightness Fig 4, guarded-image examples Fig 5, scalability Table 1).
- **Appendix (7 pp):** A = proof of Prop 1 (+ Lemma 1); B = Lipschitz constants of composition/addition/concatenation (plain derivations, unnumbered); C = proofs of Thm 1 & 2 + normalization-layer treatment; D = proof of Thm 3, Cor 1, tighter n-counts, **Table 2 of per-activation Lipschitz constants**; E = LMT stabilization tricks; F = experimental setups/hyperparameters; G = additional discussion (relation to Parseval nets, extensions).

### THEORY ↔ EMPIRICAL INTEGRATION
Very tight — the paper's signature move is **measuring how loose each theoretical inequality is**:
- The inequality chain Eq (5): `Margin/L (A) ≤ Margin/L_global (B) ≤ Margin/L_local (C) ≤ Smallest Adversarial Perturbation (D)`, then: *"We analyzed errors in inequalities (i)–(iii)… Figure 4 shows the result. With an unregularized model, estimated error ratios in (i)–(iii) were 39.9, 1.13, and 1.82 respectively."* Each labelled inequality is empirically quantified.
- **Figures/captions cite the result they illustrate.** Fig 3 bars are literally labelled "Thm. 1, 2 / Cor. 1 / Cisse+ / Peck+". Fig 5 caption: *"On the basis of Proposition 2, any patterns of perturbations with the same or smaller magnitudes could not deceive the network trained with LMT."*
- §6 opens by mapping contributions to experiment sections: *"1. Our bounds … are tighter than previous ones (Sec. 6.1). 2. LMT effectively enlarges the provably guarded area (Secs. 6.1 and 6.2). 3. Our calculation technique … available for modern large and complex networks (Sec. 6.2)."*

### CLAIM STRENGTH / HEDGING
Consistently modest and honest:
- Abstract: *"our method showed its ability to provide a **non-trivial** guarantee and enhance robustness for even large networks."* ("non-trivial" used repeatedly instead of overclaiming).
- *"We **empirically observed** that the training procedure also improves robustness against current attack methods."*
- Limitations handled **inline at the point of the claim**, including an explicit admission of inferiority: comparing to ℓ∞ Kolter-Wong, *"Thus, in the ℓ∞-norm, our work is inferior, if we ignore their limited applicability."* Also a careful caveat that one inequality direction does not hold because *"we calculated mere lower bounds of Lipschitz constants"*, and that large c makes constant functions optimal (a failure mode), stated openly.
- Conclusion is a plain achievement list: *"We offered… We introduced… We proposed… We successfully provided non-trivial certification…"*

### CITING FOUNDATIONAL / STANDARD RESULTS
- Standard Lipschitz-composition facts (composition `L₁·L₂`, addition `L₁+L₂`, concatenation `√(L₁²+L₂²)`) are given as **plain unnumbered equations** in §5.1, with proofs in App B — not elevated to theorems.
- Per-activation Lipschitz constants are **tabulated** (Table 2: ReLU=1, sigmoid=1/4, …) as known facts, not stated as results.
- When a result builds on prior work it is **presented as the authors' own numbered result with explicit attribution in the pointer**: Thm 2 *"…which is mostly from Friedman [10]"*; Thm 3 *"whose idea comes from Cisse et al. [8]"*; Cor 1 *"This result is similar to Cisse et al. [8], but we can provide better bounds."*

---

## TEMPLATE — shared conventions distilled into a checklist

Use this to restructure the theory+empirical adversarial-robustness paper. Items marked ★ are where the two papers agree strongly; items marked ⚖ are where they differ (a design choice to make).

**Result taxonomy & naming**
- [ ] ★ Keep the count of formal main-body results small: ~2-3 Theorems, ~1-2 Propositions, 0-1 Corollaries. (Cohen: 2 Thm / 2 Prop; Tsuzuku: 3 Thm / 2 Prop / 1 Cor.)
- [ ] ⚖ Decide the naming convention up front:
  - *Cohen style:* **Theorem = the 1-2 novel headline claims**; Propositions = correctness/operational + special cases; Lemmas = imported tools.
  - *Tsuzuku style:* **Theorem = the heavier/more general technical machinery**; Propositions = the simple conceptual condition that the experiments actually use; Corollary = direct consequence; Lemmas = elementary helpers.
  - Recommendation: for a paper whose selling point is one clean guarantee, use Cohen style (headline = Theorem). For a paper whose contribution is a toolbox of bounds, Tsuzuku style is acceptable.
- [ ] ★ Corollary only for a direct one-step consequence of a stated Theorem. Lemma only for a helper; push Lemmas to the appendix.
- [ ] ★ Numbered Definitions are optional — both papers define core objects inline as displayed equations (g, the margin M, the threat model) rather than as "Definition 1".
- [ ] Theorem statements: terse "Let … Suppose … Then …" or implication form. Immediately follow the headline theorem with a short bulleted/prose list of plain-language consequences and assumptions.

**Proofs**
- [ ] ★ All rigorous proofs go to the appendix. In the main body, after each result place a **one-line pointer**: "The proof is in Appendix X." (Tsuzuku does only this; Cohen additionally gives a 2-class *proof sketch* in main for the headline theorem — include a sketch only for the single most important theorem.)
- [ ] When a proof uses a known result, restate it as a named, numbered **Lemma (with citation)** if it is structural to the argument; otherwise just **cite it inline** in the proof.

**Main vs appendix split**
- [ ] ★ Main body ≈ 8 pages: intro, related work, problem setup, the theory (with sketch + pointers), the method/algorithm (boxed), and the *figures* of the headline experiments.
- [ ] ★ Appendix carries: full proofs; special-case / illustrative results; **the full result tables** (Cohen pushes Tables 2-4 to App E); per-component constants/tables; statistical-conversion machinery; baseline re-derivations; and all hyperparameters / experimental setup.
- [ ] Appendix length is unconstrained — Cohen's appendix is 3x the main body; Tsuzuku's is ~0.9x. Either is fine.

**Theory ↔ empirical integration (do all of these)**
- [ ] ★ After each theorem, add a sentence/paragraph pointing to the experiment that verifies or illustrates it ("we verify this in §X / Fig Y").
- [ ] ★ Include an explicit **"tightness of the bound"** experiment: attack inside/outside the certified radius (Cohen: succeed 17% at 1.5R, 53% at 2R) or measure the empirical looseness ratio of each inequality (Tsuzuku: 39.9, 1.13, 1.82 for the three inequalities).
- [ ] ★ **Figure captions must cite the theorem/proposition they illustrate** (e.g. "certified accuracies using our Theorem 1", "Illustration of the proof of Theorem 1", bars labelled "Thm 1,2 / Cor 1"; "On the basis of Proposition 2, …").
- [ ] ★ Open the experiments section by mapping each numbered contribution to the section/figure that tests it.

**Claim strength / hedging**
- [ ] ★ Use strong verbs ("we prove", "we show") only for results with a proof; use "suggests", "we suspect", "we empirically observed" for speculation and empirical-only findings.
- [ ] ⚖ Limitations: Cohen uses a **dedicated flagged paragraph** ("X has one major drawback…"); Tsuzuku handles them **inline at the point of each claim**, including a frank "our work is inferior in ℓ∞". Do at least one; a dedicated limitations paragraph is the safer default, with honest inline caveats where a claim is scoped (e.g. "we computed only lower bounds, so inequality (iii) need not hold").
- [ ] State assumptions explicitly right next to the headline result (Cohen: "Theorem 1 assumes nothing about f. This is crucial since…").

**Citing standard results**
- [ ] ★ Don't dress up textbook facts as new theorems. Tabulate them (per-activation Lipschitz constants) or give them as plain unnumbered equations (composition rules).
- [ ] ★ When building on prior work, present your version as your own numbered result **with explicit attribution** ("mostly from Friedman [10]", "idea comes from Cisse et al. [8], but we provide better bounds", "essentially a restatement of Neyman-Pearson (1933)").
