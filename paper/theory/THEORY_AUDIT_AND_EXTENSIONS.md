# Theory audit and extensions

Reviewer pass over the theory of `report/main.tex` (Structural theory, Optimization,
App. `app:envelope`, App. `app:bracket-lazy`) and the companion note
`theory/coupling_conjectures.tex` (A', the complexity envelope, the ReLU corollary,
the counterexample, B', C', D, and the achieved-margin theorem `thm:ib`).

Method: each Proposition/Theorem was re-derived by hand from its stated hypotheses;
the bibliography (`report/references.bib`) was checked for the load-bearing
attributions. I do **not** write final proofs here — I scope, give a path with known
results (arXiv IDs), estimate difficulty, and flag what I could not check. Numerical
constants quoted in the text (e.g. `kappa ~ 1.6-2.4`, `tau ~ 26`, the empirical
correlations) are taken on trust; see the honesty section.

---

## 1. Correctness pass (per-result verdict)

All formal results re-derived correctly. **No mathematical error found.** Details:

| Result | Verdict | Note |
|---|---|---|
| `prop:euler` (Euler floor, note) | verified | standard; `eta/L <= sup_i ||x_i||` uses `M>=0` on correct points |
| `lem:scale` / `lem:ratiodegen` (scale degeneracy) | verified | standard (Tsuzuku App. G.2) |
| `prop:Aprime` / `prop:split` (radial–tangential split) | verified | exact polar identity for 1-homogeneous `M`; `tau = sec∠(∇M,x)` checked |
| `thm:A` (invariant linear margin) | verified | optimal `w` lies in `V_inv`; interval/hull form consistent (`||Π_inv x − Π_inv x'|| = |f_dc(x)−f_dc(x')|`) |
| `thm:finite-group` (group-average projector) | verified | `P_G` orthogonal projector; optimal normal in `V^G` |
| `prop:linear` (linear max-margin `kappa = ||x||/γ`) | verified, sharp | SVM norm–margin duality |
| `thm:complexity` / `cor:relu` | verified | homogeneous norm–margin duality; AM–GM step and `B_i=√2` checked |
| `prop:counter` (no universal constant) | verified | `w* = (1,A)`, `||∇_S log m(e1)|| = A → ∞`, `kappa = √(1+A²)=||x||/γ` |
| `prop:Bprime` / `prop:Bift` (lockstep, IFT) | verified | ridge identity `dlogη/dlogL = m_2²/(m_1 m_3) ≤ 1` re-derived exactly via Cauchy–Schwarz |
| `prop:Cprime` (local noisy-pair ceiling) | verified | FTC + Cauchy–Schwarz + endpoint control |
| `prop:D` P1 (`kappa_br ≤ sec∠`) | verified | radial reaching-path of length `||x||`, `M` exactly linear on it |
| `prop:D` P2 (curvature, `kappa_br ≤ 2`) | verified | solve `½β t² − Lt + η = 0`; `kappa_br ≤ 2/(1+√(1−2βη/L²))` |
| `prop:sandwich` (two-sided bracket) | verified | correct; hypothesis stronger than proof uses (see C1) |
| `lem:ps` / `lem:ps-lip` (power-spectrum span, `2B`-Lipschitz) | verified | Parseval; real filter weights conjugate pairs |
| `thm:toy` (two-subspace exact radius `a/√2`) | verified | minimize `(a−r)²+r²` at `r=a/2` |
| `thm:lazy-cluster` (lazy cluster advantage) | verified | (i)-(iii) sound; **certified, not realized, Lipschitz** (see C2) |
| `thm:ib` / `prop:ib-envelope` (achieved-margin envelope) | verified | algebra correct; conceptual fix, not a hard theorem (C3) |
| Bispectrum claim in `sec:recover` (margin `d^{-3/2}`) | verified | bispectrum of `±e_j` is `±d^{-3/2}`, shift-invariant |

Bibliography spot-check: **no mis-attributions.** `soudry2018implicit` = JMLR 2018
*Implicit Bias of GD on Separable Data* (arXiv:1710.10345) — correct. `elesedy2021provably`
= arXiv:2106.02346 *Provably Strict Generalisation Benefit for Invariance in Kernel
Methods* — exactly the right Elesedy paper for the RKHS orbit-projection / orbit-variance
machinery (the *kernel* one, not the linear-model 2102.10333). `bietti2019inductive`
(1905.12173) correctly carries the ReLU-NTK non-Lipschitz caveat. The note's provenance
paragraph is accurate.

---

## 2. Corrections (over-claims, loose hypotheses, scope)

These are scope/clarity fixes, not errors. Ordered by how much they affect the reading.

**C1 — `prop:sandwich` upper arm is near-definitional; scope the novelty and weaken the
hypothesis.** The proof uses only the single secant inequality at the boundary-hitting
point, `|g(x) − g(γ(T))| ≥ α||γ(T) − x||`, not a co-Lipschitz (lower-Lipschitz) bound
along the whole path as stated. Two consequences: (a) state the hypothesis as the weaker
"there exists a reaching path whose endpoint satisfies the secant lower bound," which is
what is actually needed; (b) be honest that taking `α` = secant slope along the *true*
minimal path makes `r_2 = η/α` an identity, so the content is only when `α` is
certifiable a priori (from injectivity/co-Lipschitz structure of the feature, or a
quasi-convexity of sub-level sets). Recommend reframing as "the bracket is exact for
linear features and becomes a genuine *a priori* upper bound whenever a reaching path
with certifiable slope `α` exists," and explicitly contrasting with the trivial choice.
This is reachable to make rigorous for the invariant features (see E4) and is the single
place a referee will push.

**C2 — `thm:lazy-cluster` bounds the *certified* (RKHS-norm) Lipschitz, not the realized
robust radius; localize the open part to `L`.** Steps (i)-(ii) (orbit-averaging is a
non-expansive RKHS projection, feasibility of `Π_G f_unc`) are activation-independent and
exact. Step (iii) compares `L_Φ ||f||_K`, an *upper bound* on the local Lipschitz
constant. So "`η/L_inv ≥ η/L_unc`, strict unless `f_unc` is already invariant" is a
statement about the *certificate*. The §opt narrative ("the invariant architecture
reaches a substantially larger `η/L` ... the gain is entirely a smaller Lipschitz
constant") silently blends this certified gap with the *empirical realized* `η/L`.
Recommend: keep the theorem as is (it is correct and honestly remarked), but in §opt say
"smaller **certified** Lipschitz constant," and state that whether the realized robust
radius strictly improves at equal margin is exactly extension E1.

**C3 — `thm:ib`/`prop:ib-envelope` is a conceptual fix, not a hard theorem, and is only
as informative as one's lower bound on `γ_IB`.** It is `thm:complexity` verbatim with
`γ_C → γ_IB`; the entire content is the choice of denominator (the achieved margin), which
the note already concedes. Two honesty points worth surfacing in the paper: (a) the
envelope does **not** bound `γ_IB` from below, so on its own it gives no number unless the
achieved margin is estimated or `γ_IB` is related to `γ_C` (extension E2); (b) "closes the
implicit-bias gap" should read "closes the *global-optimality* gap" — it removes the
unprovable `γ_IB = γ_C` assumption but leaves the quantitative gap `γ_IB ≤ γ_C` open.

**C4 — the "margin-free" claim is regime-independent; the rich regime is open only in
`L` and in selection, not in the margin.** The §opt sketch ("orbit-averaging an
unconstrained solution gives an invariant one of equal minimum norm") in fact holds in the
*rich / variation-norm* regime too: group-averaging is non-expansive in the `F_1`
(variation) norm because that norm is `G`-invariant and convex (orbit-averaging a network
`Σ a_j σ(w_j^T x)` yields the network with neurons `{S_{−s} w_j}` and total variation
norm `≤ Σ |a_j| ||w_j||`). So the *margin value* equality is not what is open in the rich
regime. What is open is (i) which equal-margin solution the implicit bias selects, and
(ii) the realized-Lipschitz gap. Recommend rewriting so the margin-free lemma is stated
for the variation norm (one clean line) and the open problem is correctly localized to the
`L` term and the trajectory — this also sets up E1 cleanly.

**C5 — `prop:Cprime` ↔ Bubeck–Sellke is a paraphrase; soften.** Bubeck–Sellke
(2105.12806) prove a lower bound on the global Lipschitz constant `~ √(nd/p)` under data
isoperimetry and label noise. "They state the bound needs the supremum, not the average,
of `||∇f||`" is an interpretation, not their statement. Phrase as "consistent with the
sup-Lipschitz, noise-required form of the law of robustness (Bubeck–Sellke 2105.12806)";
the average-pair `prop:Cprime` is then offered as the honest *local* analogue.

**C6 — missing-but-helpful citations for the rich-regime claims.** The rich/feature-learning
discussion cites only `chizat2019lazy` (1812.07956, the *lazy* paper). For the
rich-regime implicit bias and the rich-vs-kernel margin gap it should cite
**Chizat–Bach 2020** (2002.04486, *Implicit Bias of GD for Wide Two-Layer Nets with the
Logistic Loss*) and **Wei–Lee–Liu–Ma 2019** (1810.05369, *Regularization matters:
Generalization and optimization of neural nets vs. their induced kernel*), which is
precisely the result that the variation-norm max-margin can beat the kernel one — directly
relevant to E1.

---

## 3. Extensions worth proving (ranked by value × reachability)

### E1 — Rich-regime cluster gap in the variation norm (the explicitly-flagged open item, in its reachable form). **Highest priority.**
**Target.** On orbit-closed near-orthogonal cluster data (each class an orbit of a base
with all Fourier coefficients nonzero, so full-rank per `prop:generic`/`lem:rank`), the
min-variation-norm (= rich-regime max-margin, `F_1`/`R_2,1`) invariant interpolant
`f_inv` has variation norm `||f_inv||_{F1} = ||f_unc||_{F1} − Δ` with the *strict* gap
`Δ` equal to the variation-norm "orbit variance" `||(I − Π_G) f_unc||` (in the convex
`F_1` sense), and the induced **certified** Lipschitz (sum of `|a_j| ||w_j||`) is strictly
smaller, with equality iff `f_unc` is already shift-invariant. Then push to the *realized*
Lipschitz: show the invariant solution's local Lipschitz at the data is strictly smaller.
**Why it matters.** This is the rich-regime analogue of `thm:lazy-cluster`, the one piece
§opt and §limitations call out as open; it converts the smooth-activation lazy theorem
into the regime the experiments actually live in, and gives an exact `Δ` = orbit-variance
quantification.
**Path.** (1) Static norm gap: replay the `thm:lazy-cluster` (i)-(ii) argument with the
RKHS norm replaced by the variation norm `||·||_{F1}`; the only ingredients are convexity
and `G`-invariance of the norm (both hold) and orbit-closure for feasibility of
`Π_G f_unc`. This is **the reachable medium-difficulty core.** Key results:
Chizat–Bach 2020 (2002.04486) for the `F_1` max-margin characterization, Lyu–Li
(1906.05890) for the homogeneous margin object, Elesedy (2106.02346) for the
orthogonal-projection / orbit-variance template (adapt from Hilbert to the convex `F_1`
case via a Bregman/strong-convexity surrogate). (2) Strict realized-Lipschitz step (the
genuinely hard part): the variation-norm bound on the realized Lipschitz is loose for
ReLU, so a strict realized gap needs either a smooth activation (where E1(1) already
suffices, mirroring the remark) or a structural argument that `f_unc`'s non-invariant
component produces a localized gradient spike absent in `f_inv` — connect to
Bietti–Mairal (1905.12173) on which functions in the ReLU cone are non-Lipschitz.
**Difficulty.** Static norm/certified gap: **medium** (a clean lemma). Realized-Lipschitz
strict gap in the bare-ReLU rich regime: **hard** (same wall as Frei–Vardi et al.,
Li 2025). Recommend publishing the static result and the smooth-activation realized result
now, flagging bare-ReLU.

### E2 — Pin `γ_IB` to `γ_C` on the structured orbit/cluster data. **High priority.**
**Target.** For the orbit-closed / near-orthogonal cluster families the paper studies,
show gradient descent's directional limit achieves the *global* normalized margin,
`γ_IB = γ_C`, so the achieved-margin envelope (`thm:ib`) collapses to the global one
(`thm:complexity`) and yields an actual number. Sub-target (cleanest): the two-layer-ReLU
case on orthogonally-separable orbit data.
**Why it matters.** `thm:ib` is honest but vacuous without a handle on `γ_IB` (C3). The
global-vs-achieved margin question is *the* hard implicit-bias problem in general
(Vardi–Shamir–Srebro 2110.02732 show KKT ≠ global for ReLU), but on *structured* data it
is sometimes tractable, and this is exactly the data the paper controls.
**Path.** Linear case is already exact (Soudry 1710.10345 → GD reaches the hard-margin SVM,
so `γ_IB = γ_C`). For two-layer ReLU on near-orthogonal clusters, use the directional-
convergence machinery (Lyu–Li 1906.05890, Ji–Telgarsky 2006.06657) plus the
cluster-geometry implicit-bias analyses (Frei–Vardi–Bartlett–Srebro on benign overfitting
of two-layer nets; Li 2025 "feature averaging"; Min et al. 2024 on architecture
re-pointing) to certify that the KKT point reached is in fact global max-margin on this
data — or to produce the *negative* result (a structured orbit dataset where `γ_IB < γ_C`
strictly), which is equally publishable and would sharpen `thm:ib`'s necessity.
**Difficulty.** **Hard** in general; **medium** for the linear and the
orthogonal-cluster two-layer instances. A negative example would be **medium** and high
value.
**Key refs.** 1906.05890, 2006.06657, 2110.02732, 1710.10345, 2002.04486.

### E3 — Multiclass spherical envelope. **Do it; low cost, closes a stated restriction.**
**Target.** State `prop:split`/`thm:ib` for the genuine `k`-class margin
`M = f_y − max_{j≠y} f_j`, including the non-smooth tie set.
**Why it matters.** The paper *defines* `M` multiclass but proves `cor:relu`'s `B_i = √2`
via the binary rival `e_y − e_{j*}`. A reader expects the multiclass statement.
**Path.** The polar split holds verbatim for any 1-homogeneous `M`, so only `cor:relu`
needs the multiclass step. At a tie among rivals `J`, Clarke subgradients give
`∂_x M = J_f^T (e_y − Σ_{j∈J} λ_j e_j)` with `λ` in the simplex; the distance from `e_y`
to `conv{e_j : j≠y}` is `√2` (attained at a vertex), so `||e_y − Σ λ_j e_j||_2 ≤ √2`
and `B_i = √2` survives. Write the envelope with the Clarke subgradient and note `m(u)`
is only locally Lipschitz across tie sets.
**Difficulty.** **Easy** (a paragraph). Best treated as a closed corollary, not a
headline.
**Key refs.** Clarke subgradient calculus; for the homogeneous KKT object at ties,
Lyu–Li 1906.05890 §4.

### E4 — Make `prop:sandwich` explicit (computed `α`) for the invariant features. **Medium priority; turns C1 from a soft claim into a theorem.**
**Target.** For the linear DC feature and the power-spectrum surrogate, exhibit the
reaching path and compute the co-Lipschitz `α` (hence `κ = L/α`) in closed or
semi-closed form, so the bracket `η/L ≤ r_2 ≤ η/α` is fully a priori (no "suppose a path
exists"). Then a tightened-`κ` statement under a curvature/implicit-bias assumption.
**Why it matters.** Removes the near-definitional flavour (C1) and substantiates the
`κ ≈ 1.6-2.4` numeric with an analytic envelope; gives the paper a real two-sided
certificate for at least the features it constructs.
**Path.** Linear/DC: `α = L = ||w||`, `κ=1`, already exact (Hein–Andriushchenko
1705.08475). Power-spectrum `f_a(x) = Σ a_k |x̂_k|²`: along the radial path to a boundary
zero, `f_a` is a quadratic form, so `α` is the smallest secant slope of a 1-D quadratic on
`[0, r_2]` and is computable from the eigen-structure of `diag(a)` restricted to the
active frequencies; combine with `lem:ps-lip` (`L ≤ 2B||a||_∞`). For the tightened-`κ`
arm under curvature, port the CURE / local-linearity bound (Moosavi-Dezfooli et al. 2019,
1811.09716, the `moosavi2019robustness` already cited) — this is exactly `prop:D` P2, so
the deliverable is to connect `prop:D` P2 to the bracket `κ`, which the note leaves
implicit.
**Difficulty.** Closed-form `α` for DC and power-spectrum: **easy–medium**. General
tightened `κ` under implicit-bias-guaranteed curvature: **hard** (the note correctly says
the implicit bias does *not* certify the benign regime).
**Key refs.** 1705.08475, 1802.04034, 1811.09716.

### E5 — Higher-order-invariant margin–Lipschitz tradeoff + non-abelian finite-group power spectrum. **Medium priority, partly computational.**
**Target.** Quantify `η_Ψ / L` across the invariant hierarchy — DC (linear) ⊂ power
spectrum ⊂ bispectrum ⊂ full — on the dot, single-frequency, and Ge span data: prove the
margin grows (power spectrum is sign-blind so `η=0` on `±e_j`, bispectrum gives
`η = d^{-3/2}`, already verified) while the Lipschitz constant grows faster, giving a
monotone-decreasing certified `η/L`, and find the crossover. Then state the finite-group
version of `lem:ps`: for general finite `G`, the degree-2 invariants are the
isotypic-component energies `||Π_ρ x||²` (the "group power spectrum"), and the degree-3
invariants are the group bispectrum.
**Why it matters.** Closes the "a higher-order invariant escapes the dot but at larger
Lipschitz" remark with numbers, and generalizes `lem:ps`/`thm:finite-group` beyond cyclic
`Z_d` (which §related and §limitations gesture at).
**Path.** Bispectrum invariance/completeness and the group bispectrum: Kakarala
(group-theoretic bispectrum; *The Bispectrum as a Source of Phase-Sensitive Invariants*)
and the multireference-alignment literature (Bandeira–Chen–Singer; arXiv:1705.00641 for
sample-complexity intuition). Lipschitz growth of higher moments: extend `lem:ps-lip`
(degree-`q` invariant is `O(B^{q-1})`-Lipschitz on the ball). Mallat scattering
(1101.2286) for the stability-vs-discriminability tradeoff framing.
**Difficulty.** Margin–Lipschitz computations on the three datasets: **easy** (analytic +
a verification script). Clean non-abelian degree-2 = isotypic-energy statement:
**medium**.

---

## 4. Open questions (lower-effort, publishable-adjacent)

**Q1 — D's explicit GD dataset.** The note lists as a residual "an explicit
gradient-descent dataset realizing large `κ_br` at large geometric margin." `prop:counter`
already gives large `κ` (the gradient-floor slack `τ`) at max margin for a *linear*
solver; the open piece is a *trained* (GD, finite-time) two-layer ReLU instance where the
*bracket* `κ_br = L r_2 / η` (curvature looseness, not `τ`) is large while the margin is
large. Reachable as a small synthetic experiment + a curvature lower bound via `prop:D`
P2 run backwards. Low effort.

**Q2 — Conditions for the conditional converse (C1/E4).** Give a clean sufficient
condition under which a reaching path with certifiable `α` is *guaranteed*: e.g.
quasi-concavity of `g` toward the boundary, or star-shaped correctly-classified region
about the nearest boundary point. This is the missing hypothesis that makes `prop:sandwich`
non-vacuous. Low–medium effort; connects to level-set geometry of invariant features.

**Q3 — `prop:Cprime` in the genuine `p ≪ nd` noisy regime.** The note flags "C in the
noisy `p ≪ nd` training-point-average niche." Bridge the local pair bound to the global
Bubeck–Sellke law: under label noise and isoperimetry, bound the *number* of close
opposite-label pairs from below and turn the per-pair ceiling into a population statement,
recovering a `√(nd/p)`-type rate from `prop:Cprime`. Medium effort; cite 2105.12806.

**Q4 — Finite-group generalization specifics.** `thm:finite-group` is stated for any
finite orthogonal `G`. Two cheap follow-ups: (a) for `G = Z_d` the orbit-flip radius
`ρ_G` of `prop:rhoG` is computable in closed form (nearest shift that crosses the oracle
boundary) — do it; (b) spell out `V^G` and `P_G` for the 2-D shift group and the
dihedral/rotation groups used by `wang2025bridging`, so the structural theory lines up
with the equivariant-defense literature it cites. Low effort.

**Q5 — Within-model sign-flip (the `+0.5 ↔ −0.5` coupling) as a theorem.** The empirical
"adversarial training inverts the per-sample margin/sensitivity rank correlation" is
currently only narrated, with `prop:split`'s radial floor offered as the *structural*
reason the coupling is positive. A reachable target: in a 1-homogeneous model the floor
`||∇M|| ≥ M/||x||` forces a nonnegative *lower envelope* slope; show that adversarial
training pushes solutions toward the floor (where the coupling is `+1`) while standard
training sits in the slack (where data noise makes it negative). Connect to
`moosavi2019robustness` (curvature reduction). Medium effort; would convert a figure into
a proposition.

---

## 5. What I could not verify

- **All numerical constants** are taken on trust from the text: the bracket
  `κ ≈ 1.6-2.4` for the power-spectrum surrogate (`prop:sandwich`), `τ ≈ 26` gradient-floor
  slack (`prop:split`/Fig. coupling-split), the `λ`-sweep numbers in `app:tmreg`, and every
  reported correlation/Pearson/Spearman. I checked their *internal consistency* with the
  theory (e.g. `τ` large ⇒ slack exists ⇒ penalty can move `||∇M||` while margin falls),
  which holds, but did not re-run any experiment.
- **`prop:Bift` ridge identity beyond the displayed quantity.** I re-derived
  `dlogη/dlogL = m_2²/(m_1 m_3) ≤ 1` exactly under `η = b^T A^{-1} b`, `L = (b^T A^{-2} b)^{1/2}`;
  if the paper's `η, L` along the ridge are defined differently the constant could shift,
  though the `≤ 1` (Cauchy–Schwarz) conclusion is robust to that choice.
- **`thm:lazy-cluster` smooth-activation realizability.** I verified the projection and
  Lipschitz steps; I did *not* check that a concrete smooth-activation NTK with a
  shift-invariant kernel on the specific cluster data actually has the claimed strict
  orbit-variance gap nonzero (i.e. that `f_unc` is genuinely non-invariant there). That
  strictness is asserted "unless `f_unc` is already invariant" and is the content of E1.
- **arXiv IDs I am confident about** (cross-checked against `references.bib`): Lyu–Li
  1906.05890, Ji–Telgarsky 2006.06657, Vardi–Shamir–Srebro 2110.02732, Soudry et al.
  JMLR 2018 (1710.10345), Chizat–Oyallon–Bach 1812.07956, Elesedy 2106.02346,
  Bietti–Mairal 1905.12173, Bubeck–Sellke 2105.12806, Tsuzuku 1802.04034,
  Hein–Andriushchenko 1705.08475, Jacot et al. 1806.07572, Moosavi-Dezfooli et al.
  1811.09716. **IDs I suggest but did not verify against arXiv directly** (not in the
  current bib, recommended for E1/E2/E5): Chizat–Bach 2020 *2002.04486*, Wei–Lee–Liu–Ma
  2019 *1810.05369*, the Kakarala group-bispectrum papers, Mallat scattering *1101.2286*,
  Bandeira–Chen–Singer MRA *1705.00641*, and the exact IDs of `frei2023double`,
  `li2025feature`, `min2024can` — confirm these before citing.
