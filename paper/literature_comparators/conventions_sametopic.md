# Writing / Organization Conventions — Same-Topic Comparators

Extracted to guide restructuring of our theory+empirical shift-invariance robustness paper.
These two are the same-topic anchors: **Ge2021** is the paper we extend; **Wang2025** is the closest competitor.

PDFs saved and confirmed in this directory:
- `wang2025.pdf` — Wang et al., "Bridging Symmetry and Robustness: On the Role of Equivariance in Enhancing Adversarial Robustness", NeurIPS 2025, arXiv:2510.16171 (28 pages).
- `ge2021.pdf` — Singla, Ge, Basri, Jacobs, "Shift Invariance Can Reduce Adversarial Robustness", NeurIPS 2021, arXiv:2103.02695 (18 pages).

---

## PAPER 1 — Ge2021 (the paper we extend)

### Document layout
- 18 pages total. **Main body pages 1–10** (Sec 1–6). **References pages 11–14** (~120 refs, standard, not self-citation-heavy). **Supplementary Material pages 15–18** (Sec 7 = Proof of Thm 1; Sec 8 = Proof of Thm 2 + Lemma 1).
- Appendix is *small and proof-only* (≈4 pages). No NeurIPS checklist printed in this PDF version.
- Section order: Intro → Related Work → **Theory (Sec 3, 4)** → **Experiments (Sec 5)** → Conclusion. Theory precedes experiments. The motivating toy example (Fig 1) is shown in the **Introduction, before any theory**.

### COUNTS (formal environments)
| Environment | Main body | Appendix/Supp | Total |
|---|---|---|---|
| Theorem | 2 (Thm 1 Sec 3, Thm 2 Sec 4) | 0 (only their proofs) | 2 |
| Proposition | 0 | 0 | 0 |
| Lemma | 0 | 1 (Lemma 1, Sec 8) | 1 |
| Corollary | 2 (Cor 1 Sec 3, Cor 2 Sec 4) | 0 | 2 |
| Remark | 0 | 0 | 0 |
| Note | 1 (Note 1, Sec 5.1.3) | 0 | 1 |
| Definition | **0 formal** (all defns inline in prose) | 0 | 0 |

Notable: **no Propositions, no Remarks, and zero numbered Definition environments.** Quantities like `f_dc(x)` ("DC component") and "shift invariant linear classifier" are defined inline in running text, not as `Definition` blocks.

### NAMING semantics
- **Theorem** = a genuinely new, headline result that carries a full proof. The 2 Theorems ARE the two headline contributions (Thm 1: shift-invariant linear-classifier margin depends only on DC components; Thm 2: NTK vs CNTK-GAP decision boundaries).
- **Corollary** = the concrete instantiation / worked numbers of a theorem. Cor 1 gives the exact margins (`2` vs `2/√d`) for the black/white-dot toy example; Cor 2 specializes Thm 2 to an antipodal pair. Corollaries connect theory to the figure.
- **Lemma** = a small technical helper used *inside* a proof (Lemma 1 = a positive-definite-kernel classification fact, used only to prove Thm 2). Lives in the appendix where it is used.
- **Note** = a restatement of conditions derived from prior work (Note 1 lists when a real CNN satisfies shift-invariance, "easy to derive from (Cohen & Welling, 2016)"). Used to flag imported/derived facts without dressing them as theorems.

### Main Theorem statement style (quote, Thm 1)
> "**Theorem 1.** Let S1 and S2 denote the sets of all shifts of X1 and X2, as described above. They are linearly separable **if and only if** max_{x1∈S1} f_dc(x1) < min_{x2∈S2} f_dc(x2) or max_{x2∈S2} f_dc(x2) < min_{x1∈S1} f_dc(x1). Furthermore, if the two classes are linearly separable then, if the first inequality holds, the margin is min_{x2∈S2} f_dc(x2) − max_{x1∈S1} f_dc(x1) ... Furthermore, the max margin separating hyperplane has a normal of w̄."

Style: crisp `iff` characterization, fully quantified, exact margin formula, exact separating direction. These are real theorems with real proofs.

### PROOF PLACEMENT
- 100% of theorem proofs are in the Supplementary (Sec 7 = Thm 1; Sec 8 = Thm 2 + Lemma 1). Main body gives **intuition only**: "The proof of this theorem is in the supplemental material. Here we will give an intuitive explanation for this result"; "This theorem is proven in the supplemental material. Here we provide some intuition to explain the results."
- Corollary 1 has **no separate proof** — "it is straightforward to show" + the numbers. Sketch-in-main / full-in-appendix is the rule for the Theorems; Corollaries are stated as immediate consequences.

### THEORY ↔ EMPIRICAL INTEGRATION (this is Ge's signature strength — copy this)
- One toy example (Fig 1, the black/white-dot binary problem) is threaded through the *entire* paper: it appears in the Intro, drives Sec 3 ("the two classes shown in Figure 1"), drives Sec 4 ("consistent with our results in Figure 1"), and Cor 2 "follows directly from Thm 1 **which explains the results in Figure 1**."
- The strongest device: **the theoretical prediction is overlaid on the empirical curve in the same plot.** Fig 1 caption:
  > "The curve labeled CNN shows results for a real trained network, while CNTK shows the theoretically derived prediction of 1/√d for an infinitely wide network."
- Experiments are explicitly framed as testing the theory's generality:
  > "We have shown theoretically that shift invariance can reduce adversarial robustness. In this section we describe experiments that indicate that this does occur with real datasets and network architectures."
- Honest scope handoff theory→experiment:
  > "Our proof uses these kernels, and applies when the assumptions of this prior work hold. However, the results in Figure 1 are produced with real networks that do not satisfy these assumptions, suggesting that our results are more general."

### CLAIM STRENGTH / HEDGING
- "Prove" reserved for the proven theorems: "We prove that for a shift invariant linear classifier the margin will depend only on differences in the DC components"; "we prove that shift invariance in neural networks produces adversarial examples for the simple case of two classes."
- "Show empirically" for the data results: "we show empirically that with real datasets and realistic architectures, shift invariance reduces adversarial robustness."
- The **title itself is hedged**: "Shift Invariance *Can* Reduce Adversarial Robustness" (not "does").
- Bold one-sentence contribution statement: "**The main contribution of our paper is to show theoretically that shift invariance can undermine adversarial robustness, and to show experimentally that this is indeed the case on real-world networks.**"
- Synthetic-data conclusions explicitly flagged tentative: "Our tentative answer to these questions is yes, based on experiments with simple datasets. But these are questions that surely deserve greater attention."
- Limitations handled **inline** (no dedicated section in this version), e.g. the assumptions-may-not-hold caveat above; societal-impact in a short "Potential Negative Societal Impacts" paragraph in Sec 5.2.

### CITING STANDARD RESULTS
- Known kernels (NTK/CNTK, Jacot et al. 2018; Arora et al. 2019; Li et al. 2019; FC-NTK formula attributed to Bietti & Mairal 2019) are **cited as known and re-defined in the supplementary for self-containedness**, NOT renumbered as the authors' own theorems. They are *used inside* the proof of Thm 2.
- Their own new helper (general positive-definite-kernel fact) is a properly-proved Lemma 1, not borrowed.
- Net rule: import known machinery with citations *inside proofs*; keep numbered Theorems for genuinely new results.

---

## PAPER 2 — Wang2025 (closest competitor — position against precisely)

### Document layout
- 28 pages total. **Main body pages 1–10** (Sec 1–7, Conclusion ends p.10). **References pages 11–18** (113 refs, **heavily self-citation-padded** — refs [13]–[86] are largely the same author cluster). **Appendix pages 19–28**: A (proofs of Thm 1, Thm 2) p.19–20; B Limitations p.21; C architectural designs p.21–22; D fully-equivariant experiments p.23; E comparison-with-AT p.23–24; F perturbation viz + ablation p.24–25; G compute resources p.25; **NeurIPS Checklist p.26–28**.
- Appendix is *large and mostly experimental/scaffolding* (≈10 pages), unlike Ge's lean proof-only appendix.
- Section order: Intro → Related Works → **Definitions (Sec 3)** → **Theory (Sec 4)** → Architectures (Sec 5) → Experiments (Sec 6) → Conclusion. Theory precedes architecture and experiments. No motivating toy figure.

### COUNTS (formal environments)
| Environment | Main body | Appendix | Total |
|---|---|---|---|
| Theorem | 2 (Thm 1 Sec 4.3, Thm 2 Sec 4.4) | 0 (only proofs A.1, A.2) | 2 |
| Proposition | 0 | 0 | 0 |
| Lemma | 5 (Lemmas 1–5, Sec 4.2–4.4) | 0 | 5 |
| Corollary | 0 | 0 | 0 |
| Remark | 0 | 0 | 0 |
| Definition | **13** (Def 1–13, Sec 3.1–4.4) | 0 | 13 |

Notable: **no Propositions, no Corollaries, no Remarks.** Very **Definition-heavy** (13) — the opposite of Ge's 0.

### NAMING semantics
- **Theorem** = the 2 claimed-original headline results: Thm 1 "Orbit-Invariance of Margin Gradient Norm", Thm 2 "Directional Suppression of Off-Orbit Perturbations". These have **no citation bracket** in their titles (signalling "ours").
- **Lemma** = an **imported prior result, restated as a numbered Lemma with a citation in the title**. All 5 Lemmas carry a citation: Lemma 1 (Jacobian Norm Invariance **[108]**), Lemma 2 (Transformation of Margins under Group Equivariance **[109]**), Lemma 3 (Gradient Transformation of Margin Function **[108]**), Lemma 4 ([110]), Lemma 5 (Smoothing via Orbit Averaging **[109]**). [108/109/110] = Anselmi/Rosasco/Poggio. **None of the Lemmas are proved** — they are borrowed.
- **Definition** = setup/scaffolding (equivariance, margin, Lipschitz, orbit, CLEVER, Jacobian, orbit-averaged gradient). Def 5 even renumbers a known quantity: "Definition 5 (CLEVER Bound **[107]**)".

### Main Theorem statement style (quote, Thm 1)
> "**Theorem 1** (Orbit-Invariance of Margin Gradient Norm). If both ρ(g) and Dg^{-1} are norm-preserving (e.g., orthogonal matrices), then for all g ∈ G, ‖∇g_{c,j}(g·x)‖_q = ‖∇g_{c,j}(x)‖_q. As a result, the Lipschitz constant of the margin function is invariant across the group orbit: L_q^{(j)} = sup_{x'∈B_p([x]_G,r)} ‖∇g_{c,j}(x')‖_q."

Style: "If [orthogonality assumption] then [equality]". A named theorem with formal-looking statement.

### EXACT LIST of Wang's theory claims (titles + one-line content + proved? + regime)
**Theorems (claimed original):**
1. **Theorem 1 — Orbit-Invariance of Margin Gradient Norm.** Under norm-preserving ρ(g) and Dg^{-1}, the margin-gradient norm (hence local Lipschitz constant) is constant along a group orbit. **Proved** in App A.1 — but the proof additionally **assumes ρ(g) is diagonal** ("Assuming ρ(g) is diagonal ... reduces to f_i(g·x)=ρ_ii(g)f_i(x)") and ρ_cc,ρ_jj ∈ {+1,−1}. **Regime:** compact group with *orthogonal/isometric* representation (rotations, reflections). **Explicitly excludes scale** (Sec 4.5: "scale transformations alter the norm ... violating the orthogonality condition required in Lemma 1 and Theorem 1").
2. **Theorem 2 — Directional Suppression of Off-Orbit Perturbations.** For an equivariant f under compact G, perturbations along the orbit tangent change the gradient much less than off-orbit perturbations: "‖∇f(x+δ⊥)−∇f(x)‖ ≫ ‖∇f(x+δ_G)−∇f(x)‖". **"Proved"** in App A.2, **but the proof is heuristic**: it uses "∇f(x') ≈ ∇f(x)", "‖∇f(x+δ_G)−∇f(x)‖ ≈ 0", and Case 2 "is not bounded by symmetry and may vary substantially" — i.e. ≈/≫ with no rates or quantifiers. **Regime:** compact G, orthogonal ρ(g) and Dg^{-1}, perturbation split δ = δ_G + δ⊥.

**Lemmas (all imported, none proved):**
3. **Lemma 1 — Jacobian Norm Invariance [108].** If ρ(g), Dg^{-1} orthogonal then ‖J_f(g·x)‖₂ = ‖J_f(x)‖₂. Assumed (cited).
4. **Lemma 2 — Transformation of Margins under Group Equivariance [109].** g_{c,j}(g·x) = ρ_cc f_c − ρ_jj f_j. Assumed.
5. **Lemma 3 — Gradient Transformation of Margin Function [108].** ∇g_{c,j}(g·x) = ρ(g)∇g_{c,j}(x)Dg^{-1}. Assumed.
6. **Lemma 4 — Gradient Transformation under Group Equivariance [110].** ∇f(g·x) = ρ(g)·∇f(x)·Dg^{-1}. Assumed.
7. **Lemma 5 — Smoothing via Orbit Averaging [109].** "‖φ̄_j(x)−φ_j(x)‖ ≪ ‖φ_j(x+δ)−φ_j(x)‖, especially when δ is orthogonal to the group orbit." Assumed; **uses ≪ with no quantification** (informal even though it is a Lemma).

**Scale equivariance (Sec 4.5):** *no* certified guarantee — explicitly only a "regularization" / gradient-variance-reduction heuristic, because scale breaks the orthogonality assumption. Stated in prose, not a theorem.

### PROOF PLACEMENT
- Only the 2 Theorems are proved, **entirely in the appendix** (A.1, A.2); main body gives surrounding intuition + "Detailed proof is provided in Appendix A.1 / A.2."
- The 5 Lemmas and 13 Definitions are not proved. So the *proved fraction* of numbered environments is 2 / 20.
- Caveat for positioning: even the appendix proofs lean on ≈ / ≪ / ≫ and added hidden assumptions (diagonal ρ(g)).

### THEORY ↔ EMPIRICAL INTEGRATION (weak — our opening to beat them)
- **The theory and the experiments run on separate tracks and never meet quantitatively.** Theory (Sec 3–4) is about CLEVER certified bounds, Lipschitz constants, and gradient-variance; experiments (Sec 6) report **FGSM/PGD accuracy curves and CIFAR-10C corruption accuracy**. There is **no "we verify Theorem 1/2 in Figure/Table X"**, no plot of a CLEVER bound, no measurement of orbit-gradient-invariance.
- The only nod to theory in experiments is a generic mention of the "maximum invariant perturbation metric [112]" used for a qualitative perturbation-tolerance figure (App F).
- The abstract *claims* tight certified-bound improvements ("yield tighter certified robustness bounds under the CLEVER ... framework") but nothing in the experiments measures a CLEVER bound. This claim–evidence gap is the clearest weakness to position against.

### CLAIM STRENGTH / HEDGING
- Strong "demonstrate" framing for theory: "Theoretically, we demonstrate that such models reduce hypothesis space complexity, regularize gradients, and yield tighter certified robustness bounds under the CLEVER ... framework."
- "We present a theoretical analysis **demonstrating** that equivariant architectures contract the hypothesis space, regularize gradient behavior, and admit tighter certified robustness bounds."
- Formal environments themselves are **under-hedged given their rigor**: Lemma 5 and Thm 2 use ≪/≫ as if proven facts.
- Limitations: a **dedicated Appendix B** paragraph, honest about scope: "First, the theoretical framework focuses solely on local Lipschitz bounds (e.g., CLEVER), which may not capture broader robustness phenomena ... Second, empirical evaluations are limited to small-scale datasets and common ℓp-norm attacks ... Finally, the integration of equivariant layers is confined to early stages of the network, and the computational trade-offs of group convolutions remain unquantified."

### CITING STANDARD RESULTS
- Wang **renumbers known results as its own numbered Lemmas/Definitions**, attributing only via a bracketed citation in the title (Lemmas 1–5 = Anselmi et al.; Def 5 = CLEVER/Weng et al.). This inflates the apparent theoretical contribution (5 "Lemmas" that are all borrowed). Contrast Ge, who imports the same kind of machinery *inside proofs* rather than as standalone numbered Lemmas.

---

## TEMPLATE — Shared conventions to adopt (and where to differ)

**Shared by both same-topic papers (adopt these — they are the genre norm):**
1. **Exactly 2 Theorems as the headline.** Both papers crown the contribution with two Theorems; everything else is support. Pick our 1–2 strongest results as the only Theorems.
2. **Theory section(s) before the experiments**, in the order Setup → Theorem(s) → Experiments → Conclusion.
3. **Sketch/intuition in main body, full proof in appendix**, with an explicit pointer ("The proof is in App X"; "Here we give the intuition").
4. **Neither uses "Proposition" or "Remark."** The working vocabulary is Theorem / Lemma / (Corollary) / (Definition) / (Note). Do not introduce Propositions/Remarks unless we have a reason.
5. **Hedged title + scoped claims.** Use "can"/"may" in the title; reserve "prove" strictly for proven statements and "show (empirically)" for data.
6. **A dedicated Limitations paragraph** (Wang App B; Ge inline) — NeurIPS expects it. Put one in.
7. **Bold one-sentence statement of the main contribution** (Ge does this verbatim; effective).

**Where the two diverge — choose deliberately:**
8. **Definitions:** Ge = 0 formal (inline prose); Wang = 13. The genre tolerates either extreme. For a theory+empirical paper, use a *modest* number of real Definitions only for objects you reuse; don't pad to 13.
9. **Lemmas / imported results:** Ge imports machinery *inside proofs* with citations; Wang restates borrowed results as 5 own-numbered Lemmas. **Follow Ge** — do NOT renumber known results as our own Lemmas; cite them in-proof. (If a referee compares us to Wang, this is a credibility differentiator.)
10. **Corollaries:** Ge uses them to land the abstract theorem on a concrete worked example/number. **Adopt this** — a Corollary that produces the exact toy-example margin is a clean theory→figure bridge.
11. **Appendix size/shape:** Ge = lean, proof-only (~4 pp); Wang = bloated with experiments + checklist (~10 pp). Either is fine for NeurIPS; keep proofs separate from extra experiments.

**The decisive differentiator to exploit against Wang (our closest competitor):**
12. **Tie every theorem to a measured quantity.** Ge overlays the theoretical `1/√d` prediction on the empirical curve in one figure and routes Thm→Corollary→Figure→real-data experiments as a single chain. Wang's theorems (CLEVER/Lipschitz/gradient-variance) are *never measured* — experiments only report FGSM/PGD accuracy. **Our paper should, for each theorem, show a figure/table where the theoretically predicted quantity is plotted against the measured one** (e.g., predicted radius / η/L vs. measured AA radius). This is exactly the gap Wang leaves open and Ge models well.
13. **Keep "theorem" honest.** Wang's Thm 2 / Lemma 5 use ≈/≪/≫ without rates — a reviewer-visible weakness. Our numbered Theorems should be statements we can prove with explicit constants/assumptions (the sandwich/κ bound style), and anything heuristic should be a labeled "claim"/"observation," not a Theorem.
