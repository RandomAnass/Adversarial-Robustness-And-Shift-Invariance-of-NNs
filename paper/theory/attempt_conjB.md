# Attack on Conjecture B (penalty-path lockstep / no first-order decoupling)

**Target.** Conjecture B of `coupling_conjectures.tex` (`conj:lockstep`). For the regularized
objective `L(θ)+λR(θ)` with `R(θ)=E‖∇_x M‖_q`, with `θ_λ` the minimizer (or the
gradient-flow path in `λ`), write `η(λ)=E[M]` and `L(λ)=E‖∇_x M‖_q = R(θ_λ)`. The
conjecture asserts a `c>0` with `dη/d(logL) ≥ cη`, read as: the margin falls in
lockstep with the sensitivity, so the certified ratio `η/L` is (to first order)
stationary and **no penalty of this form raises certified robustness**.

**One-line verdict (details in §5).** **REFUTED as literally stated**, with an exact
closed-form linear counterexample in which `η/L` is *monotonically non-decreasing*
along the penalty path (the inequality that holds is the exact reverse of the
conjecture). The conjecture survives as a **PARTIAL** theorem under one extra
hypothesis — that the penalty moves `θ` only along the output-scale direction, or
equivalently that the operating point is already a critical point of the ratio —
which is exactly the regime an adversarially pre-trained network sits in, and which
explains the paper's empirical lockstep without supporting the universal claim.

---

## 1. Variational / implicit-function setup (precise)

Assume `Φ_λ(θ) = L(θ) + λ R(θ)` is `C²` near an isolated minimizer `θ_λ` with
`H_λ := ∇²Φ_λ(θ_λ) = ∇²L + λ∇²R ≻ 0` (nondegenerate strict local min), so the
implicit function theorem applies and `λ ↦ θ_λ` is `C¹`. Throughout, `∇`, `∇²`
are in `θ`; `g_R := ∇_θ R(θ_λ)`, `g_η := ∇_θ η(θ_λ)`; recall the conjecture sets the
measured sensitivity equal to the penalty, `L(λ) = R(θ_λ)`, so `∇_θ L(λ) = g_R`.

**Stationarity.** `∇L(θ_λ) + λ g_R = 0.`

**Differentiate in λ** (`˙ = d/dλ`):
`∇²L·θ̇ + g_R + λ∇²R·θ̇ = 0  ⟹  θ̇_λ = −H_λ^{-1} g_R.`   (★)

**Sensitivity always falls.** Since `H_λ ≻ 0`,
```
dL/dλ = ⟨g_R, θ̇⟩ = −⟨g_R, H_λ^{-1} g_R⟩ ≤ 0.
```
So `L` is non-increasing in `λ`: the premise "the penalty reduces sensitivity" is
solid and unconditional. This is the *one* half of the conjecture that is true for
free.

**Margin change (sign free).**
```
dη/dλ = ⟨g_η, θ̇⟩ = −⟨g_η, H_λ^{-1} g_R⟩.
```
Its sign depends entirely on the `H^{-1}`-alignment of `g_η` and `g_R`; nothing in
the structure pins it.

**Ratio change — the clean master formula.** Using `∇_θ(η/L) = (1/L)(g_η − (η/L) g_R)`
(here `g_L = g_R`), the chain rule gives the exact identity
```
   d(η/L)/dλ  =  ⟨∇_θ(η/L), θ̇⟩  =  − ⟨ ∇_θ(η/L) ,  H_λ^{-1} g_R ⟩.            (B★)
```
Equivalently, in log-derivative form, with `dlogL/dλ < 0`,
```
   d log(η/L)/dλ ≤ 0   ⟺   (d log η/dλ)/(d log L/dλ) ≥ 1   ⟺   d log η/d log L ≥ 1.
```
**This `≥ 1` is the substantive content of Conjecture B** ("margin falls *at least*
as fast as sensitivity, ratio does not improve"). Note the bare existential "`∃c>0`"
in the LaTeX statement is, by itself, *vacuous*: along the path `dη/dλ<0` and
`dlogL/dλ<0`, so `dη/d(logL) = (dη/dλ)/(dlogL/dλ) > 0`, and being `> 0` it already
exceeds `cη` for some small `c>0` pointwise. The non-trivial claim is the `c≥1`
(ratio-non-increasing) reading, and that is what I test.

So (B★) reduces Conjecture B to one geometric inequality along the path:
```
   ⟨ ∇_θ(η/L) ,  H_λ^{-1} ∇_θ R ⟩  ≥  0      for all λ.                        (B-align)
```
The natural-gradient ascent direction of the penalty (`H^{-1}∇R`, in the curvature
metric) must be positively correlated with the ascent direction of the ratio. There
is no a-priori reason for this; the rest of the note shows it holds in a controlled
sub-case and fails in a clean explicit one.

---

## 2. The tractable cases, fully worked

### 2(a). Linear model `f(x)=w^T x` — exact, and it REFUTES the conjecture

Here `∇_x M = ±w` is constant, so the measured sensitivity is `L = ‖w‖_q` and the
penalty `R = ‖w‖_q` coincide *exactly* (no expectation gap). The mean margin is
`η = E[M] = w^T b` with `b := E[y x]`. Take the threat-matched `q=2` (the ℓ₂
certified radius uses `‖·‖₂`), so `L = ‖w‖₂` and the **certified ratio is purely
directional**:
```
   η/L = (w^T b)/‖w‖₂ = ŵ^T b ,     ŵ := w/‖w‖₂ .
```
This is the cleanest possible incarnation of the scale degeneracy (Lemma 1 of the
note): `η/L` depends *only on the direction* `ŵ`. A penalty that merely shrinks `‖w‖`
cannot touch it; only a *rotation* of `ŵ` can.

**Does the penalty rotate `ŵ`?** Take the squared loss `L(w)=½ E(y−w^Tx)² ` (any
strongly-convex quadratic loss gives the same conclusion); `Σ := E[xx^T]`,
`b = E[xy]`. For the conjecture's degree-1 penalty `R=‖w‖₂`, stationarity is
`(Σ − ... )`:
```
   Σ w − b + λ w/‖w‖₂ = 0  ⟹  w_λ = (Σ + t I)^{-1} b ,   t := λ/‖w_λ‖₂ ≥ 0 .
```
The squared (ridge) penalty `R=½‖w‖₂²` gives the *same path family* with `t=λ`. As
`λ` (hence `t`) increases, the direction rotates from `ŵ ∝ Σ^{-1}b` (`t=0`) to
`ŵ → b̂` (`t→∞`). **So unless `Σ ∝ I` or `b` is a `Σ`-eigenvector, the penalty does
rotate the direction, and `η/L = ŵ^T b` strictly changes.**

**Exact log-derivative.** Parametrize by `t` and set `A=Σ+tI`, `m_k := b^T A^{-k} b`
(`m_k = Σ_i c_i α_i^{-k}`, eigenvalues `α_i=λ_i(Σ)+t>0`, weights `c_i=(u_i^Tb)²≥0`).
Then `η = m_1`, `L² = m_2`, and
```
   dη/dt = −m_2 ,   d(L²)/dt = −2 m_3 ,
   d log η/d log L  =  (dlogη/dt)/(dlogL/dt)  =  (−m_2/m_1)/(−m_3/m_2)  =  m_2² /(m_1 m_3).
```
By Cauchy–Schwarz on `(√c_i α_i^{-1/2})` and `(√c_i α_i^{-3/2})`,
```
   m_2² = (Σ c_i α_i^{-2})² ≤ (Σ c_i α_i^{-1})(Σ c_i α_i^{-3}) = m_1 m_3 ,
```
with equality **iff** all active `α_i` (those with `c_i>0`) are equal, i.e. `b` lies
in a single `Σ`-eigenspace (the isotropic/degenerate case). Therefore

> **Proposition 1 (linear, exact).** Along the gradient-penalty path of a linear
> model with squared loss (equivalently any quadratic loss; both the degree-1
> penalty `‖w‖₂` and the ridge penalty `½‖w‖₂²` give the same path),
> ```
>        d log η / d log L  =  m_2²/(m_1 m_3)  ≤  1 ,
> ```
> with equality iff the data is isotropic on `span(b)`. Hence `η/L` is monotonically
> **non-decreasing** in `λ`, and **strictly increasing whenever the data is
> anisotropic**.

This is the *exact reverse* of Conjecture B, which needs `d log η/d log L ≥ 1`.
Both `η` and `L` fall (so the LaTeX phrase "the margin falls" is literally true),
but the margin falls **strictly slower** than the sensitivity, so the certified
ratio *improves*. Numerically (`conjB_check.py`, Test 1, four random anisotropic
`Σ∈R^{4×4}`): the analytic `m_2²/(m_1m_3)` ranged over `0.79–0.99 < 1`, matched the
numeric slope to `<1e-4`, and `η/L` increased monotonically (e.g. `2.565 → 2.826`,
`0.975 → 1.252`).

**Does the improved surrogate mean improved robustness?** This is where honesty
matters. The surrogate `η/L = E[M]/E‖∇M‖` (ratio of *means*) is what the conjecture
names and what increases. Whether *true* robustness increases depends on the loss:

- **Symmetric Gaussian mixture** `x = yμ + N(0,Σ)` (so `b=μ`, and least squares
  recovers the LDA/Fisher direction `Σ^{-1}μ`, which is the **accuracy- and
  robustness-optimal** direction). Here the penalty rotates *away* from `Σ^{-1}μ`
  *toward* `μ`. Test 2 (`d=3`, `Σ=diag-like(4,1,¼)`): along the path the surrogate
  `η/L = ŵ^Tμ` rose `1.385 → 1.499`, while **clean accuracy fell `0.997 → 0.974`
  and robust accuracy at `ε=0.5` fell `0.959 → 0.901`.** So the surrogate and true
  robustness move in **opposite** directions.

  This *refutes the formalization* (`η/L` is not stationary; it rises) while
  *vindicating the paper's deeper thesis*: raising the `η/L` surrogate via a penalty
  buys no real robustness — here it actively hurts. The culprit is the surrogate
  `η = E[M]` itself: as a *mean signed margin* it rewards inflating the margin of
  already-correct points and is blind to accuracy, so it can be inflated by a
  direction rotation that degrades the classifier.

- **Generic / mis-specified ERM loss.** If the unpenalized solution sits at a
  direction that is *worse* than `b̂` for robustness (e.g. ERM overfits a
  high-variance non-discriminative axis), the same rotation toward `b̂` raises both
  the surrogate *and* true robustness — a genuine "penalty helps" instance. I did
  not need to engineer this to refute the conjecture (Proposition 1 already does),
  but it shows the `c≥1` claim cannot be rescued by switching to a true-robustness
  reading without further assumptions on the loss.

**Take-away for 2(a).** For linear models the conjecture is *false on its own terms*:
the certified ratio does not fall, it rises (Prop. 1). The lockstep that *is* real is
the trivial one — pure magnitude shrinkage leaves the direction, hence `η/L`, fixed.

### 2(b). Single homogeneous ReLU neuron `f(x)=a·σ(w^T x)`

`∇_x M = a·1{w^Tx>0}·w`, so on the active set `‖∇_x M‖_q = |a|‖w‖_q`. With active
fraction `p(w)=Pr(w^Tx>0)` (a function of the *direction* of `w` only),
```
   L = E‖∇_x M‖_q = |a|‖w‖_q · p(ŵ) ,   η = a·E[(w^Tx)_+] = a‖w‖_? · (directional),
```
and the certified ratio
```
   η/L = E[(w^Tx)_+] / (‖w‖_q · p(ŵ))
```
is again **invariant to the output scale `a` and to `‖w‖`** — it is a function of the
direction `ŵ` alone. The structure is identical to the linear case:
- penalizing/scaling `a` (or `‖w‖`) gives **exact lockstep** `d log η = d log L`,
  `η/L` constant (this is the Lemma-1 scale degeneracy made dynamic);
- only a rotation of `ŵ` (driven by the off-diagonal loss curvature) changes `η/L`,
  and its sign is uncontrolled, exactly as in 2(a).

So 2(b) adds no new obstruction and no new rescue: the homogeneity that the note
relies on is precisely what makes `η/L` scale-invariant, which makes the penalty's
dominant (scale) action a perfect lockstep and pushes all the action into the
uncontrolled rotation term.

### 2(c). Diagonal / feature-aligned case

If `Σ = diag(σ_1²,…,σ_d²)` and `b = e_k` (a single feature), then `b` is a
`Σ`-eigenvector, `m_2²=m_1 m_3` exactly, `d log η/d log L = 1`, and `η/L` is exactly
constant: **the diagonal feature-aligned case is the equality case of Proposition 1**
— the only linear case where Conjecture B holds, and it holds with `c=1` (exact
stationarity), not as an inequality. Any off-diagonal coupling between the penalized
coordinate and the margin coordinate breaks it toward `η/L` increasing.

---

## 3. The general (nonlinear) attempt and the exact obstruction

The master formula (B★), `d(η/L)/dλ = −⟨∇(η/L), H_λ^{-1} ∇R⟩`, localizes the entire
question in the sign of (B-align). Two structural facts organize it.

**(i) The scale subspace gives exact lockstep.** For a bias-free 1-homogeneous
network the ratio `η/L` is invariant under the output-scaling action
`θ ↦ θ_c` with `M ↦ cM`, `∇_xM ↦ c∇_xM`. Let `s(θ)` be its generator. Then `η/L` is
degree-0 along `s`, so by Euler `⟨∇(η/L), s⟩ = 0`. Decompose the IFT velocity
`θ̇ = θ̇_∥ + θ̇_⊥` into the scale part (`∥ s`) and the ratio-tangent part. Only the
latter moves the ratio:
```
   d(η/L)/dλ = ⟨∇(η/L), θ̇_⊥⟩ ,     and along θ̇_∥ :  d log η = d log L exactly.
```
> **Proposition 2 (exact lockstep on the scale subspace).** If the penalty moves the
> parameters only along the output-scale direction — `H_λ^{-1}∇R ∥ s(θ_λ)` — then
> `d log η/dλ = d log L/dλ` and `d(η/L)/dλ = 0`: perfect lockstep, ratio exactly
> stationary (`c=1`). Verified numerically (Test 4): scaling `θ↦cθ` holds `η/L`
> constant to machine precision across `c∈{0.5,1,2,5}`.

Because the penalty `R=E‖∇_xM‖` is *itself* degree-1 in the output scale, its
gradient `∇R` has a large component along `s`; if `H_λ` (or at least the part of it
relevant through `H^{-1}`) does not mix the scale and ratio-tangent subspaces, then
`H^{-1}∇R` stays `∥ s` and Proposition 2 gives lockstep. **Decoupling is purely a
scale↔rotation mixing effect**, carried by the off-diagonal block of `H_λ^{-1}` times
the non-scale component of `∇R`. This is the precise obstruction: there is no reason
that off-diagonal block vanishes for a generic loss/data geometry, and when it does
not, (B-align) can take either sign.

**(ii) Both signs occur.** The general formula is genuinely two-sided:
- Test 1 (linear, anisotropic) realizes `⟨∇(η/L), H^{-1}∇R⟩ < 0` ⟹ ratio **rises**
  ⟹ conjecture false.
- Test 3 (a deliberately constructed 2-parameter nonlinear-ish program with a strong
  off-axis loss curvature `S=diag(1,9)`, margin functional `q^Tθ`, sensitivity `‖θ‖₂`)
  realizes `⟨∇(η/L), H^{-1}∇R⟩ > 0` ⟹ ratio **falls** (`0.706 → 0.218`,
  `d log η/d log L ∈ [1.8,2.7] > 1`) ⟹ conjecture holds there.

So no general proof of (B-align) exists; the sign is a property of the *operating
point and data geometry*, not of "penalties of this form".

**(iii) The one extra hypothesis that makes it true — and why the paper sees lockstep.**

> **Proposition 3 (no-improvement at a ratio-critical operating point).** If the
> `λ=0` solution `θ_0` is a critical point of `η/L` on the scale quotient
> (`∇(η/L)(θ_0)=0`) — in particular a local *maximizer* of the ratio, i.e. a
> robust-optimal direction — then `d(η/L)/dλ|_{0}=0`, and if the max is strict the
> ratio decreases to second order. The conjecture's spirit ("no penalty raises
> certified robustness") then holds *locally*, not because of lockstep dynamics but
> because there is nothing to gain by rotating away from an optimum.

This is the honest reconciliation with the experiments. An **adversarially
pre-trained** PreActResNet sits (approximately) at its implicit-bias / robust-optimal
direction; from there a gradient/ratio penalty has no profitable rotation available,
so its leading action is scale shrinkage → exact lockstep (Prop. 2), and the margin
collapses with the sensitivity (the observed four-intervention behaviour). Conjecture
B mistakes a property of *that operating point* (Prop. 3) for a property of *all*
first-order penalties (which Prop. 1 refutes).

---

## 4. Literature, firsthand (arXiv IDs verified)

- **Hein & Andriushchenko 2017, arXiv:1705.08475** ("Formal Guarantees on the
  Robustness of a Classifier against Adversarial Manipulation," NeurIPS 2017).
  Theorem 2.1 gives the instance bound `‖δ‖_p ≥ min_{j≠c}(f_c−f_j)/‖∇(f_c−f_j)‖_q`
  (margin / local Lipschitz) and a Cross-Lipschitz regularizer to enlarge it. They
  note output-shift invariance ("adding the same `g` to all outputs leaves loss and
  regularizer invariant"); the *scale* invariance of the ratio is implicit in the
  bound. **No lockstep/no-improvement theorem.**
- **Tsuzuku, Sato, Sugiyama 2018, arXiv:1802.04034** ("Lipschitz-Margin Training,"
  NeurIPS 2018). Prop. 1: safe radius `= margin/(√2·Lip)`. Appendix G.2 *explicitly*
  states the scale degeneracy: "if we add a scaling layer to the output ... we can
  control the Lipschitz constant ... however, this does not change its prediction."
  So the scale-invariance premise (= Lemma 1, = the `η/L` directionality used in §2)
  is established folklore. **No lockstep theorem** — their method aims to beat the
  ratio by enlarging the margin while bounding Lip.
- **Ross & Doshi-Velez 2018, arXiv:1711.09404.** Penalize `λ‖∇_x H(y,ŷ)‖₂²`; purely
  empirical, no margin analysis, **no theorem**.
- **Finlay & Oberman 2019, arXiv:1905.11468** ("Scaleable input gradient
  regularization"). Closest in spirit. Prop. 2.2 writes robustness as
  margin/input-gradient-norm. They *informally* warn of exactly this degeneracy:
  *"Shrinking the magnitude of gradients while also closing the gap `ℓ₀−ℓ(x)`
  effectively does nothing to improve adversarial robustness"* (the defensive-
  distillation/gradient-masking pitfall). But this is a caveat, **not a theorem**,
  and their thesis is the opposite — that good gradient regularization *does* improve
  the ratio.
- **Hoffman, Roberts, Yaida 2019, arXiv:1908.02729** ("Robust Learning with Jacobian
  Regularization"). Claims the *reverse* of lockstep: Jacobian regularization
  "increases classification margins." **No lockstep theorem.**
- **Tsipras et al. 2019, arXiv:1805.12152** ("Robustness May Be at Odds with
  Accuracy"). Thm 2.1 is an *accuracy-vs-robustness* tradeoff in a Gaussian model
  (robust feature `x₁=+y` w.p. `p`; `d` weak features `N(ηy,1)`): any classifier with
  `≥1−δ` standard accuracy has `≤ (p/(1−p))δ` robust accuracy at `ε≥2η`. This is a
  *different* tradeoff (accuracy vs robustness, not margin vs sensitivity) and says
  nothing about `E[M]/E‖∇M‖` or gradient penalties.

**Synthesis.** The *scale-degeneracy half* of the story is known (Tsuzuku G.2; implicit
in every margin/Lipschitz radius). The *lockstep half* — a formal theorem that a
gradient/Jacobian penalty cannot raise `E[M]/E‖∇M‖` because the margin must fall in
proportion — is **not in the literature**; where the literature commits, it points the
*other* way (Finlay-Oberman, Hoffman aim to raise the ratio). So Conjecture B is a
genuine open statement — and §2 shows it is, as written, false.

---

## 5. Verdict

**REFUTED as literally stated; TRUE only as a PARTIAL result under an explicit
operating-point hypothesis.**

1. **Refutation (linear, exact).** Proposition 1: for a linear model with quadratic
   loss and the conjecture's own penalty `R=‖w‖_q` (or ridge), `d log η/d log L =
   m_2²/(m_1m_3) ≤ 1` with strict `<1` under anisotropy. The certified ratio `η/L`
   is therefore monotonically **non-decreasing** along the penalty path — the exact
   negation of the conjectured `≥1`. The "margin falls" sub-claim is true; the
   operative "ratio does not improve / no penalty raises robustness" sub-claim is
   false. Confirmed numerically to `<1e-4` (Test 1).

2. **The conjecture's `∃c>0` form is vacuous** (it holds pointwise for trivially
   small `c`); the substantive `c≥1` form is the one refuted.

3. **Decoupling of surrogate and truth (important nuance).** In the symmetric
   Gaussian mixture the penalty *raises* the surrogate `η/L` while *lowering* clean
   and robust accuracy (Test 2). So the refutation does not hand the paper a working
   defense; instead it pinpoints that `η=E[M]` is a poor robustness surrogate. The
   paper's *empirical* conclusion ("these penalties don't buy robustness") is right;
   its *proposed mechanism* (lockstep forcing the ratio to be stationary) is wrong —
   the ratio is not stationary, it just doesn't track real robustness.

4. **Strongest TRUE version (PARTIAL).**
   - *Proposition 2*: along the output-scale direction, `d log η = d log L` exactly,
     `η/L` exactly stationary (`c=1`). Always available; it is the only lockstep that
     is unconditional.
   - *Proposition 3*: if the operating point is a ratio-critical (robust-optimal)
     direction, `d(η/L)/dλ=0` and the ratio does not increase to first order. This is
     the regime of an adversarially pre-trained network and the honest explanation of
     the experiments.
   - *Master formula (B★)*: `d(η/L)/dλ = −⟨∇(η/L), H^{-1}∇R⟩`; the conjecture holds
     iff this inner product is `≥0`, which is a data/operating-point condition, not a
     law of "penalties of this form."

   A defensible restatement that *is* a theorem: **"At a ratio-critical operating
   point, or when the penalty acts purely by output rescaling, the certified ratio is
   first-order stationary along the penalty path; in general its first-order change is
   `−⟨∇(η/L),H^{-1}∇R⟩`, whose sign is not fixed and is negative (ratio improves) for
   anisotropic linear models."**

5. **Recommendation for the note.** Downgrade `conj:lockstep` from "would close the
   impossibility" to a *characterization*: replace the universal claim with
   Propositions 1–3. The walk-back in §3 of `coupling_conjectures.tex` was right to be
   cautious; this attack shows the dynamic lockstep is not just unproven but *false*
   in the cleanest case, while the empirical regularity is explained by the
   operating-point Proposition 3 (not by a universal lockstep).

---

## 6. Adversarial self-review

- **"You used squared loss, not the adversarial loss `L_AT`."** Correct, and stated.
  Conjecture B as written ("`L(θ)+λR(θ)`, `θ_λ` minimizes it") places *no* restriction
  on `L`, so the linear-LS instance is a valid counterexample to the statement. If one
  *adds* the restriction `L=L_AT`, the start moves toward the robust-optimal direction
  and Proposition 3 applies — i.e. the only way to save the conjecture is to assume the
  operating-point hypothesis, which is exactly my PARTIAL verdict. I have not proven
  the conjecture is false *for `L_AT` specifically at the implicit-bias solution*; there
  it is plausibly true, but only via Prop. 3, not via a universal lockstep.

- **"`η/L` going up but accuracy going down — maybe `η/L` is the wrong robustness
  measure, so the conjecture about `η/L` could still be 'morally' false-positive."**
  This is precisely the point I make (item 5.3): the refutation is of the *formal
  statement about `η/L`*. The conjecture *names* `η/L` as the certified ratio, so a
  monotone increase of `η/L` refutes it on its own terms. The fact that real
  robustness doesn't follow `η/L` is an additional finding, not a hole.

- **Is `m_2²≤m_1m_3` airtight?** Yes — it is Cauchy–Schwarz on the positive measure
  `c_i δ_{α_i}`; it is also the statement that `t↦log m_k(t)` ... more simply, `(m_k)`
  is a Hausdorff/Stieltjes moment sequence in `α^{-1}`, hence log-convex in the index:
  `m_2² ≤ m_1 m_3`. Equality iff the measure is a single atom (isotropic on `span b`).
  Verified numerically to `<1e-4` against the path derivative.

- **IFT regularity / nonsmooth ReLU.** The IFT step assumes `H_λ≻0` and `C²`; for ReLU
  networks `R` is only piecewise smooth. Within an activation cell everything above is
  exact; across cells one needs a Clarke/`o(1)`-measure argument as in Thm 1 of the
  note. This does not affect the *linear* refutation (globally smooth) and only adds
  technical care to Propositions 2–3.

- **Could the off-diagonal scale↔rotation block of `H^{-1}` always have the
  conjecture-favourable sign at a *minimizer*?** No: `H_λ≻0` constrains the quadratic
  form `⟨v,H^{-1}v⟩>0` but places *no sign constraint* on the cross term
  `⟨∇(η/L),H^{-1}∇R⟩` for two non-parallel vectors. Test 1 (sign `<0`) and Test 3
  (sign `>0`) both occur at genuine strict minimizers, settling this.

- **Did I check monotonicity vs. just endpoints?** Yes — `η/L` is monotone along the
  whole path in all four Test-1 trials (`np.all(np.diff(ratio)≥0)`), and the local
  slope `d log η/d log L` stayed in `(0,1)` throughout, so the increase is not a
  boundary artifact.

**Scratch:** `/tmp/.../scratchpad/conjB_check.py` (Tests 1–4). The mathematics in §1–§3
stands without the numerics; the numerics only confirm the closed forms.
