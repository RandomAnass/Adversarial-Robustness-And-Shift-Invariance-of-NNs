# Novelty triage of the technical-report results

Source read in full: `paper/report/theory_full_checked_v2.tex` (931 lines), especially its results
(Theorems/Lemmas/Propositions/Corollaries/Conjectures) and its existing
"Literature-grounded novelty audit" (§ `sec:novelty-audit`, lines 787-816) and "Status table"
(lines 754-776). Cross-checked against the base/gap papers read for `MOTIVATION.md` and against
`literature/RELATED_WORK_COMPARISON.md`, `DOCUMENTATION.md`, and the report's own bibliography.

**Headline verdict.** Of the ~21 formal results, **most are not novel** — they are standard
facts, clean rephrasings, or low-level realization lemmas. The report itself already says so
(its audit: "The novelty assessment should be conservative... several ingredients are
established... The phrase 'new robustness quantity' should not be used for `eta/L`"). The triage
agrees and is decisive:

- **MAIN PAPER (medium-strength, at most): 5 results** — the two-sided bracket / conditional
  converse (`thm:sandwich` + `cor:linear-exact` + `prop:computable-bracket` as one contribution),
  the finite-group projected-hull invariant margin (`thm:finite-group-margin`), the
  self-symmetrization margin-free theorem (`thm:selfsym`), the lazy-regime cluster theorem
  (`thm:lazy-cluster`), and the empirical capacity-matched `eta/L` decomposition (the executed
  CIFAR/AutoAttack study). Plus the bispectrum separation (`prop:bispectrum`) as a one-result
  "richer invariant" vignette if space allows (borderline).
- **APPENDIX / TR-ONLY: everything else (~15 results)** — setup lemmas, the bare `eta/L` lower
  bound, the no-converse counterexample, power-spectrum span/Lipschitz, the toy radius, the
  orbit-gradient lemma, the orbit-flip bound, the orbit-bundle identity, the orbit-rank lemma and
  single-orbit correction, the KKT systems, and the open conjectures (kept as stated open problems).

The honest framing (already adopted in `2pagers` and `DOCUMENTATION.md`): the contribution is
**an exact projection-margin accounting of what survives an invariance + an empirical
margin/Lipschitz decomposition validated under AutoAttack**, not a new robustness quantity.

---

## Triage table (one row per formal result)

Columns: **Result** (label + one-line statement) | **Novelty verdict** | **Cite if known/reproved**
| **Route**.

Verdict vocabulary: *novel candidate* (medium at best) / *clean rephrasing* / *known-and-reproved*
/ *low-level-or-too-narrow*.

| Result | One-line statement | Novelty verdict | Cite | Route |
|---|---|---|---|---|
| `lem:cyclic-fixed` (Fixed subspace for cyclic shifts) | `V_inv = span{1}`, `P_inv = ee^T`, shifts DFT-diagonalized so `|x_k|^2` invariant. | **Known-and-reproved.** Standard Fourier/circulant linear algebra; Ge use it explicitly. | Standard; Ge 2021. | **APPENDIX** (setup). |
| `thm:finite-group-margin` (Invariant linear margin, finite orthogonal group) | Max invariant `L2` margin = `(1/2) dist(conv P_G X+, conv P_G X-)`. | **Novel candidate (modest).** Ge prove the cyclic/DC special case; group averaging is standard rep theory. New only as the clean general-group + convex-hull-normalization statement. | Ge 2021 (cyclic case). | **MAIN** (the structural anchor; present as a clean generalization, *not* a new phenomenon). |
| `cor:cyclic-margin` (Correct cyclic DC formula) | Cyclic specialization: `(1/2)dist(I+,I-)` of DC intervals. | **Known-and-reproved** (corrects orientation bug). | Ge 2021. | **APPENDIX** (corollary of the above). |
| `cor:projection-cannot-increase` (`gamma_inv <= gamma_full`) | Projecting onto the fixed subspace cannot raise the linear max-margin. | **Low-level.** Immediate from non-expansiveness of projection / class restriction. | — | **APPENDIX** (diagnostic consequence). |
| `prop:lipschitz-margin` (Lipschitz-margin certificate) | `r2 >= eta/L` for an invariant feature classifier. | **Known-and-reproved.** Textbook Lipschitz-margin bound. The report itself says the inequality is not the contribution. | Hein-Andriushchenko 2017; Tsuzuku 2018; Sokolic 2016; Bartlett 2017. | **APPENDIX** (the new angle = apply *after* identifying invariant features, which lives in the MAIN empirical decomposition). |
| `prop:no-converse` (No universal converse for `eta/L`) | `Psi_n(x)=t^(2n+1)` gives `r2 / (eta/L) = 2n+1`, unbounded. | **Low-level / useful clarification.** Elementary counterexample; prevents overclaiming. | — | **APPENDIX** (keep as the honesty caveat; one sentence in MAIN). |
| `thm:sandwich` (Two-sided robust-radius bracket; conditional converse) | `mu/L <= r2 <= mu/alpha`, `kappa=L/alpha`; co-Lipschitz `alpha` closes the upper arm. | **Best novel candidate.** Completes the missing upper arm of Tsuzuku Eq. 5 (whose top inequality they state cannot be guaranteed, measure as 1.8-2.4x gap); prior upper bounds were only empirical (attack-based). | Tsuzuku 2018 (Eq. 5, the arm completed); Croce-Hein FAB 2020 (empirical upper bound it replaces); Dontchev-Rockafellar 2009 (metric subregularity). | **MAIN** (lead theoretical result; medium — it is a conditional bracket, not an unconditional radius formula). |
| `cor:linear-exact` (Linear invariant features: converse exact) | For `g=w^T x`, `kappa=1`, `r2 = mu/||w||` exactly. | **Known-and-reproved.** Classic point-to-hyperplane SVM distance; here a sanity-check that the bracket is tight. | Hein-Andriushchenko 2017; Cristianini-Shawe-Taylor 2000. | **MAIN** (bundle with `thm:sandwich` as its `kappa=1` corollary). |
| `rem:counter-kappa` (No-converse is a large-`kappa` instance) | Reconciles `prop:no-converse` with the bracket: `kappa=2n+1`. | **Low-level** (reconciling remark). | — | **APPENDIX** (or a footnote to `thm:sandwich`). |
| `prop:computable-bracket` (Computable bracket for the power-spectrum surrogate) | Explicit `eta_Q/2B <= r2 <= eta_Q/alpha`; verified, `kappa ~ 1.6-2.4`. | **Novel candidate (narrow).** First two-sided radius statement for an invariant-feature model; but only for the toy quadratic surrogate. | — (instantiates `thm:sandwich`). | **MAIN** (one short paragraph as the concrete instance of the bracket) **or APPENDIX** if space tight. |
| `lem:ps-corrected` (Corrected power-spectrum span) | conv-square-GAP computes `sum |w_k|^2 |x_k|^2`; real filters span conjugate-pair power coords. | **Known-and-reproved (low-level).** Power spectra / autocorrelation / scattering are classical; corrects a DFT-normalization + real-filter bug. | Bruna-Mallat 2012 (scattering); standard DFT. | **APPENDIX** (realization lemma). |
| `cor:ps-lip` (Lipschitz of power-spectrum features on a ball) | `||Q(x)-Q(y)|| <= 2B||x-y||`; scalar score `<= 2B||a||_inf`. | **Low-level.** Elementary quadratic-feature bound. | — | **APPENDIX** (makes the certificate computable). |
| `thm:toy-radius` (Exact nonlinear toy radius) | `f=||P_U x||^2 - ||P_V x||^2` gives exact `r2 = a/sqrt(2)`; linear class fails. | **Low-level / too-narrow.** Likely original as a didactic calculation, but a two-frequency toy. | — | **APPENDIX** (didactic example). |
| `lem:bispectrum` (Bispectrum = degree-3 shift invariant) | `B(x)=x_{k1}x_{k2}conj(x_{k1+k2})` is shift-invariant, conv-realizable, `O(B^2)`-Lipschitz. | **Known-and-reproved.** Classical invariant; reconstruction completeness is Kakarala's. | Kakarala 2012; Bruna-Mallat 2012. | **APPENDIX**. |
| `prop:bispectrum` (Bispectrum separates phase-coded classes the power spectrum cannot) | Separates Ge dot `+/-e_j` (identical power spectra) with margin `d^(-3/2)`, at a larger `L`. | **Novel candidate (borderline, narrow).** The *application* — defeating the exact Ge forced-trade-off corner with a higher-order invariant, quantifying the margin-vs-Lipschitz cost — is a fresh angle; the bispectrum itself is not new. | Kakarala 2012 (completeness); Ge 2021 (the dot it defeats). | **MAIN** *only* as a short "richer invariant feature" vignette if space allows; otherwise **APPENDIX**. Do not claim bispectrum invariants as new. |
| `thm:quadratic-two-orbit` (Two-orbit quadratic surrogate; P1) | Closed-form invariant max-margin `eta_Q = (1/2)||q+ - q-||` for power-spectrum features. | **Low-level / too-narrow.** Solves only the quadratic surrogate, explicitly not the ReLU case. | — | **APPENDIX** (the "P1" instance; supports the open-problem section). |
| `lem:continuous-gradient` (Continuous orbit-gradient suppression) | If `g` invariant then `<grad g(x), Ax> = 0` along the continuous orbit. | **Known-and-reproved.** Standard differentiation of an invariant along a Lie-group orbit; the report flags it is *not* a discrete-threat theorem. | — | **APPENDIX** (intuition only; carries an explicit caveat). |
| `prop:oracle-flip` (Invariance-based attack bound; Tramer formalization) | Oracle-robust radius of an invariant classifier `<= rho_G(x)` (orbit-flip radius). | **Clean rephrasing.** The excessive-invariance / invariance-attack concept is Jacobsen-Tramer; novelty is only the notation + unification with the projection-margin picture. | Jacobsen 2019; Tramer 2020. | **APPENDIX** (or one sentence in MAIN to scope the `rho_G` vs `eta/L` split). |
| `cor:` (Co-existence condition for a threat budget) | `eps < rho_G` and `eps <= mu/L` jointly. | **Low-level** (corollary of the two bounds). | — | **APPENDIX**. |
| `lem:bundle-corrected` (Orbit-bundle equivalence) | conv+global-pool = a two-layer net with hidden weights tied into shift orbits. | **Known-and-reproved.** Standard "convolution = weight sharing over translated filters"; group-conv formalizes it. | Cohen-Welling 2016. | **APPENDIX** (used to connect architecture to implicit bias; load-bearing for `thm:selfsym`). |
| `lem:orbit-rank` (Rank of a cyclic orbit) | `rank C(u) = #{k : u_k != 0}`. | **Known-and-reproved.** Standard circulant-matrix fact; important because it corrects the earlier false degeneracy claim. | Standard. | **APPENDIX**. |
| `prop:single-orbit-correction` (Corrected single-orbit statement) | Generic single orbits are full-rank and power-spectrum-separable (kills the old "rank-deficiency" claim). | **Low-level (a correction).** Necessary internal fix, not a contribution. | — | **APPENDIX**. |
| `prop:p1-quadratic` (P1 for quadratic surrogate) | Restates `thm:quadratic-two-orbit` in checklist notation. | **Low-level** (restatement). | — | **APPENDIX** (open-problem scaffolding). |
| `prop:kkt-systems` (KKT systems for the ReLU models) | Stationarity conditions for unconstrained vs tied-invariant two-layer ReLU. | **Low-level / setup.** Correct P1 starting point; does not identify which KKT point GD selects. | Lyu-Li 2020; Ji-Telgarsky 2020 (the KKT framework). | **APPENDIX** (scaffolding for the open conjecture). |
| `prop:p2-not-transfer` (P2 does not follow from feature-averaging theorems) | Orbit data violates the near-orthogonal-cluster premise of Frei/Li, so their non-robustness does not transfer. | **Useful clarification.** A negative/structural observation, not a theorem. | Frei 2023; Li 2024. | **APPENDIX** (frames the open problem honestly). |
| `cor:conditional-p3` (Conditional P3) | *If* P2 holds then weight sharing re-points the bias to larger certified radius. | **Low-level** (conditional implication). | — | **APPENDIX**. |
| `thm:selfsym` (Invariance is margin-free on orbit-closed data) | On orbit-closed data the invariant and unconstrained two-layer-ReLU max-margin values coincide (orbit-average = invariant solution of equal min-norm). | **Novel candidate (medium).** The nonlinear-ReLU, orbit-closed analogue of the linear steerable/augmentation equivalence; explains the generic-orbit experiment. | Chen-Zhu 2023 (linear steerable/augmentation equivalence it extends). | **MAIN** (the proven positive optimization result; honest scope = orbit-closed only). |
| `conj:cluster` / `conj:opt` (Invariance helps on cluster geometry) | On near-orthogonal cluster orbit data, tied GF reaches strictly larger `eta/L`; open in the rich/ReLU regime. | **Open conjecture (not a result).** Empirically supported (20-60%, lazy-strongest); the trajectory-level theorem is the frontier. | Frei 2023; Min-Vidal 2024 (architectural lever conjecture). | **MAIN** as a clearly-labeled *open problem / conjecture* (it is the paper's stated future-work hook), full development **TR-ONLY**. |
| `thm:lazy-cluster` (Invariance lowers Lipschitz in the lazy regime) | In the lazy/NTK smooth-activation regime, orbit-averaging is a non-expansive RKHS projection, so the invariant interpolant has weakly smaller norm/Lipschitz at equal margin; gap = orbit-variance. | **Novel candidate (medium).** Proves `conj:cluster` in the lazy smooth-activation regime via Elesedy's RKHS orbit-averaging projection; ReLU-NTK non-Lipschitz caveat (Bietti-Mairal) leaves rich/bare-ReLU open. | Jacot 2018; Chizat 2018 (lazy/NTK); Elesedy 2021 (orbit-averaging projection); Bietti-Mairal 2019 (smooth-vs-ReLU caveat); Haasdonk-Burkhardt 2007 (invariant kernels); Bridging-Sym-Robust 2025 (neighboring finite-net result). | **MAIN** (the second proven positive optimization result, with the explicit smooth-activation scope). |
| Executed capacity-matched CIFAR/AutoAttack `eta/L` decomposition (§ `sec:cifar-plan`) | At matched capacity, `eta/L` vs robust radius Pearson 0.998; consistency anti-predicts (-0.55 to -0.88); anti-aliasing moves `L`, exact cyclic moves `eta`; threat-matched `eta/||grad M||_1` predicts AutoAttack (0.90). | **Best empirical candidate.** Not "does invariance help" but "when capacity is controlled, which term — margin, Lipschitz, or ratio — moves." Differentiated from TIPS (no AutoAttack), Huang 2023 / RobArch (no consistency axis), Bridging (rotation/scale, no AutoAttack). | AutoAttack 2020; RobustBench 2020; RobArch 2023 (capacity control); Zhang 2019 (anti-aliasing arm); Galloway 2019 (BN control); Saha-Gokhale TIPS 2024 (the correlation it stress-tests). | **MAIN** (the empirical headline that ties the theory to a standardized benchmark). |

---

## Routing summary

**MAIN PAPER (keep in main text; medium-strength at best):**
1. `thm:finite-group-margin` — exact invariant-margin identity (clean general-group rephrasing of Ge).
2. `thm:sandwich` (+ `cor:linear-exact`, optionally `prop:computable-bracket`) — the conditional
   two-sided bracket completing the Tsuzuku certificate chain (the lead theoretical result).
3. `thm:selfsym` — margin-free on orbit-closed data (proven positive optimization result).
4. `thm:lazy-cluster` — lazy-regime cluster theorem (second proven positive result, scoped).
5. The executed capacity-matched CIFAR/AutoAttack `eta/L` decomposition (empirical headline).
- Borderline-MAIN: `prop:bispectrum` (richer-invariant vignette) and `conj:cluster` (as a labeled
  open problem / future-work hook). Include only if they earn their space.

**APPENDIX / TECHNICAL-REPORT-ONLY (kept, not main contributions):** all setup lemmas
(`lem:cyclic-fixed`, `lem:bundle-corrected`, `lem:orbit-rank`), the bare `eta/L` lower bound
(`prop:lipschitz-margin`) and its no-converse caveat (`prop:no-converse`, `rem:counter-kappa`),
the power-spectrum span/Lipschitz lemmas (`lem:ps-corrected`, `cor:ps-lip`), the toy radius
(`thm:toy-radius`), the bispectrum lemma (`lem:bispectrum`), the two-orbit surrogate
(`thm:quadratic-two-orbit`, `prop:p1-quadratic`), the orbit-gradient lemma
(`lem:continuous-gradient`), the orbit-flip bound and budget corollary (`prop:oracle-flip` + cor.),
the single-orbit correction (`prop:single-orbit-correction`), and all the open-problem scaffolding
(`prop:kkt-systems`, `prop:p2-not-transfer`, `cor:conditional-p3`, `cor:projection-cannot-increase`,
`cor:cyclic-margin`).

**Cleanup actions implied for the technical report:**
- Keep the existing § `sec:novelty-audit` and § "Status table" — they are exactly this triage and
  should *stay* in the TR as the self-audit; the present file is their paper-facing routing.
- In the *paper* main text, present the five MAIN results with honestly-scoped claims and do NOT use
  "new robustness quantity" for `eta/L` (the report's own instruction).
- Demote everything in the APPENDIX list to a clearly-marked "Supporting lemmas and corrections"
  appendix section; group the open-problem propositions under the conjecture so the reader sees them
  as scaffolding, not contributions.
- The corrections (`prop:single-orbit-correction`, the orientation fixes in `cor:cyclic-margin`,
  the DFT-normalization fix in `lem:ps-corrected`) are internal hygiene — keep in the TR, omit from
  the paper except where a one-line "the cyclic case recovers Ge" is useful.
