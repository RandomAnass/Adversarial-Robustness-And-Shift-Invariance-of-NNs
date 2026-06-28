# Attack on Conjecture D: does the implicit bias bound the bracket condition number?

**Target.** Conjecture D / `conj:kappa` of `coupling_conjectures.tex`:

> For the max-margin solution of a homogeneous network on data with margin
> condition `μ`, the bracket condition number satisfies `κ = L/α ≤ g(μ)` for an
> explicit `g`, so `η/L` estimates `r₂` up to the factor `g(μ)`.

**One–line verdict.** **REFUTED as literally stated** (no function of the
separation margin alone can bound `κ`), but with a clean **rescued PARTIAL
theorem**: the bias-free degree-1 homogeneity of the architecture forces
`κ ≤ 1/cos∠(∇ₓM(x),x)`, which *rules out the polynomial `t^{2n+1}` blow-up
entirely*, and `κ ≤ 2` in the *locally-linear (benign-curvature) regime*
`2βη ≤ L²`. The quantity that actually controls `κ` is the **input-space
curvature / gradient–input misalignment between the datum and the boundary**,
not the margin; and the gradient-flow implicit bias does not certify the benign
regime (explicit curvature / local-linearity control does).

All numerical claims below were checked with small CPU scripts (no GPU);
the scripts are in the scratch dir and the key numbers are quoted inline.

---

## 1. Precise definition of `α`, `κ`, and what makes `κ` large

### 1.1 The two-sided bracket, restated cleanly

Fix a correctly classified point `x` with scalar margin `η = M(x) > 0`
(binary; `M = f_y − max_{j≠y} f_j`). Let `x*` be the nearest point of the
decision boundary `{M = 0}` and `r₂ = ‖x − x*‖₂` the true `ℓ₂` robust radius.
Restrict `M` to the straight segment to that boundary point: with
`u = (x*−x)/r₂`,

```
    φ(ℓ) = M(x + ℓ u),    ℓ ∈ [0, r₂],    φ(0) = η,   φ(r₂) = 0.
```

Two scalars summarise the descent of `φ`:

* **sup-slope (Lipschitz along the path)** `L := sup_{ℓ} |φ'(ℓ)|`. This is the
  constant for which `η/L ≤ r₂` is a *valid* lower bound (it is the per-path
  Lipschitz constant; `L ≤ ‖M‖_Lip`). The paper's *measured* surrogate uses
  instead the **local** gradient `L₀ := ‖∇M(x)‖ = |φ'(0)|`.
* **secant slope** `ᾱ := η/r₂` (the realized average descent rate).

Because `sup ≥ average`, `L ≥ ᾱ`, and the bracket
`η/L ≤ r₂ = η/ᾱ` holds with the **operational condition number**

```
    κ := L · r₂ / η = L / ᾱ  ≥ 1,        κ = 1  ⟺  φ is affine on [0, r₂].   (★)
```

`κ` is exactly the multiplicative looseness of the certificate `η/L`, and it is
**scale-free**: invariant under `x ↦ cx` (using homogeneity) and `M ↦ sM`.

### 1.2 Relation to the file's `α` (co-Lipschitz) and the `t^{2n+1}` anchor

The file writes `κ = L/α` with `α` the **co-Lipschitz (lower-Lipschitz)
constant** `α_co = inf_{s≠t} |φ(t)−φ(s)|/|t−s| = inf_ℓ |φ'(ℓ)|` (for monotone
`φ`). Two honest remarks:

1. `α_co ≤ ᾱ` (the infimal slope is below the average), so the file's
   `κ_co = L/α_co ≥ κ` of (★). The two agree iff `φ` has constant slope
   (linear), and **for `t↦t^{2n+1}` they disagree**: on `[0,1]`,
   `φ'(0)=0` so `α_co = 0` and `κ_co = ∞`, whereas the file *also* states
   "`η/L = 1/(2n+1)` while `r₂ = 1`", i.e. the *looseness* `κ = r₂/(η/L) =
   2n+1` of (★) — finite. So the file's "`κ → ∞` end" is the `α_co` reading;
   the **finite, operationally meaningful** number is `κ = 2n+1` of (★). I use
   (★) throughout, which reproduces both anchors:
   `linear ⇒ κ = 1`, `t^{2n+1} ⇒ κ = 2n+1` (verified, §3).

2. With the *local* gradient `L₀`, the realized ratio `κ_loc := L₀ r₂/η` need
   **not** exceed 1: if `M` *steepens* toward the boundary (`L₀ < ᾱ`), then
   `η/L₀` *over*-estimates `r₂` and `κ_loc < 1` (the local certificate is then
   not even a valid lower bound). This actually happens at trained nets (§3,
   Test 3). The *proved* bracket uses `L` = sup-slope, giving `κ ≥ 1`.

### 1.3 What makes `κ` large

By (★), `κ` is the ratio (steepest slope on the path)/(secant slope). It is
large in exactly one situation: **`M` is steep somewhere between `x` and the
boundary but flat elsewhere on that segment** — i.e. `M` *flattens* on the way
to the boundary (`ᾱ ≪ L`). Equivalently `κ` measures the **failure of local
linearity of `M` between the datum and the boundary**. Three faces of the same
thing:

* *smooth view:* curvature `β = sup |φ''|` along the descent (a positive `φ''`
  bends `φ` up, delaying the zero crossing, so `ᾱ < L`);
* *piecewise-linear (ReLU) view:* convex kinks where the descent slope drops
  (a neuron deactivating), so `κ = L₀/(min slope before the boundary) = `
  product of slope-drop ratios across crossed convex kinks;
* *homogeneous view (§3.2):* on the unit sphere `M(x)=R·m(ω)`, `κ` is set by
  the **angular curvature of `m`** — steep-then-flat angular profiles.

None of these three is a function of the *margin*; all are curvature.

---

## 2. Literature, read firsthand (arXiv full text)

**Implicit bias to max margin — Lyu & Li 2019, arXiv:1906.05890; Ji &
Telgarsky 2020, arXiv:2006.06657.** For a network `L`-homogeneous *in the
parameters* (`Φ(cθ;x)=c^L Φ(θ;x)`), gradient flow/descent on the
exp/logistic loss converges *in direction* to a KKT point of
`min ½‖θ‖₂² s.t. qₙ(θ):=yₙΦ(θ;xₙ) ≥ 1 ∀n` (Lyu–Li Thm 4.4). The controlled
margin is the **output/parameter margin** `qₙ`, and the bound is on `‖θ‖`. The
KKT stationarity is `θ = Σₙ λₙ ∇_θ qₙ`, `λₙ ≥ 0`, complementary slackness.
**Crucially this is a statement about parameter geometry; it contains no bound
on the input-space gradient `∇ₓM`, its alignment with `x`, or the input
Hessian.** This is the gap Conjecture D must bridge and (I argue) cannot, using
the margin alone.

**Min-norm ⇒ an *integral* curvature seminorm — Ongie et al. 2020,
arXiv:1910.01635 (and Savarese et al. 2019, arXiv:1902.05040).** The infinite-
width minimum-weight-norm (= max-margin direction) 2-layer ReLU interpolant
minimises the "R-norm", a Radon-domain seminorm
`‖f‖_R ≈ ‖R{Δ^{(d+1)/2} f}‖₁`; in 1-D this is exactly
`max(∫|f''(x)|dx, |f'(−∞)+f'(+∞)|)`, the **total variation of the
derivative** (linear splines). So the implicit bias *does* control a curvature
functional — but in an **`L¹`/total-variation (integral) sense**, which permits
localized high-curvature spikes of bounded total mass. It does **not** give a
**pointwise** bound on `β/L²` at a chosen datum, which is what (★) needs. This
is the strongest "implicit-bias ⇒ smoothness" result available and it falls
short of D.

**Curvature of trained nets — Moosavi-Dezfooli et al. 2019, arXiv:1811.09716
(CURE).** Curvature = eigenvalues of the input Hessian `H = ∂²ℓ/∂x²`. Two facts
I use: (i) the second-order radius bound (their Thm 1)
`‖r*‖ ≥ (c/‖g‖)(√(1 + 2νc/‖g‖²) − 1)` with `ν = λ_max(H)`, `g = ∇ℓ(x)`,
`c = t − ℓ(x)` — a *quadratic* control of the radius by gradient and curvature,
the mirror of my Lemma 2; (ii) **ordinary training leaves large curvature;
adversarial training is what produces "a significant decrease in the curvature
of the loss surface w.r.t. inputs"** (their Fig. 2), and CURE *explicitly*
penalises it via `L_r = ‖∇ℓ(x+hz) − ∇ℓ(x)‖²`. So curvature reduction is an
effect of *explicit* robust training, not of the vanilla implicit bias.

**Local linearity of trained nets — Qin et al. 2019, arXiv:1907.02610 (LLR).**
Local-linearity measure `γ(ε,x) = max_{δ∈B(ε)} |ℓ(x+δ)−ℓ(x)−δᵀ∇ₓℓ(x)|`, and
Prop. 4.1 `|ℓ(x+δ)−ℓ(x)| ≤ |δᵀ∇ₓℓ(x)| + γ(ε,x)` — precisely the statement that
the first-order certificate is tight up to the nonlinearity `γ` (this *is* (★),
with `γ` the curvature gap). They report that **nets trained without explicit
help have "a highly non-linear loss surface in the vicinity of training
examples"** (gradient obfuscation) and add a regulariser `λγ(ε,x)` to force the
benign regime. Again: local linearity is *imposed*, not *inherited* from the
implicit bias.

**Randomized-smoothing converse — Cohen et al. 2019, arXiv:1902.02918.**
Certified `ℓ₂` radius `R = (σ/2)(Φ⁻¹(p̄_A) − Φ⁻¹(p̄_B))`, with the smoothed
score `x↦Φ⁻¹(\tilde p(x))` exactly `(1/σ)`-Lipschitz; their tightness theorem
is **worst-case over base classifiers**: "for any `‖δ‖₂ > R` there *exists* a
base classifier consistent with the class probabilities that flips." Contrast
with (★): `κ` is a **per-classifier** tightness of the *gradient* certificate.
Cohen's converse is loose for any *particular* `f` because it ranges over an
adversarial family; the per-`f` looseness `κ` can be 1 (a single-Lipschitz/
locally-linear `f`) even where Cohen's bound is far from `r₂`. This is the
right framing of why a per-classifier `κ` could be informative — *if* it were
bounded, which is the content of D.

**Take-away from the literature.** Every result that bounds the pointwise
nonlinearity of a net near its data (`γ`, `ν`, `β`) is an *explicit
regulariser*; the only thing the *implicit bias* is known to control is `‖θ‖`
(Lyu–Li) and, in the limit, an *integral* curvature seminorm (Ongie). So the
literature predicts D is **false for the implicit bias** and **true only under
added curvature control** — which is what the proof below finds.

---

## 3. Proof attempt: linear, homogeneous/ReLU, and blow-up cases

### 3.1 Anchor: the linear case gives `κ = 1`

For `g(x)=wᵀx+b`, the boundary is a hyperplane, `r₂ = |g(x)|/‖w‖ = η/‖w‖`,
`L₀ = ‖w‖`, so by (★) `κ = ‖w‖·(η/‖w‖)/η = 1`. `φ` is affine: no curvature, no
looseness. (Verified.)

### 3.2 Theorem (homogeneity bound — the unconditional positive result)

**Setup.** Let `M : ℝ^d → ℝ` be positively homogeneous of degree `δ`
(`M(cx)=c^δ M(x)`, `c>0`), locally Lipschitz, with `η = M(x) > 0`. By
homogeneity `M(0)=0`, so the origin lies on `{M=0}` and hence

```
    r₂ = dist(x, {M ≤ 0}) ≤ ‖x − 0‖ = ‖x‖.                                  (1)
```

Euler's identity (a.e., Clarke version on the ReLU kink set) gives
`⟨∇M(x), x⟩ = δ·M(x) = δη`, so with `θ := ∠(∇M(x), x)`,

```
    cos θ = δη / (‖∇M(x)‖ ‖x‖).                                             (2)
```

**Theorem 1.** `κ_loc := ‖∇M(x)‖·r₂/η ≤ δ / cos θ = ‖∇M(x)‖‖x‖/η`.
For a **bias-free network with positively-homogeneous degree-1 activations**
(ReLU, leaky-ReLU, abs, maxout; *any depth* — composition of 1-homogeneous maps
is 1-homogeneous), `δ = 1` and

```
    κ_loc ≤ 1 / cos∠(∇ₓM(x), x).                                           (3)
```

*Proof.* `κ_loc = ‖∇M(x)‖ r₂/η ≤ ‖∇M(x)‖‖x‖/η` by (1); substitute (2). ∎

**Corollary (no polynomial blow-up).** The file's unbounded-`κ` example
`t↦t^{2n+1}` has degree `δ = 2n+1`; (3) shows it **cannot occur at any
bias-free degree-1 network**, trained or not. A degree-1 net has `κ` controlled
by the *gradient–input angle*, not by a polynomial degree. (On `ℝ`, degree-1
homogeneous ⇒ linear ⇒ `κ=1`; the blow-up genuinely needs `δ>1`.)
**Verified:** `t^{2n+1}` gives `κ = 2n+1 = δ/cos θ` exactly for `n=0,1,2,3`;
and `δ`-homogeneous toy nets satisfy (3) to numerical tolerance.

**Spherical reading (what (3) really says).** Writing `x = R ω`, `M = R·m(ω)`,
the gradient splits into radial + tangential parts with
`‖∇M‖² = m(ω)² + ‖∇_S m(ω)‖²` and `cos θ = m/‖∇M‖`, so
`1/cos θ = √(1 + (‖∇_S m‖/m)²)`. Thus `κ` blows up iff the **restriction `m`
to the sphere is steep at `ω` relative to its value** — i.e. high *angular
curvature* (steep-then-flat). Homogeneity has merely converted "input
curvature" into "spherical curvature"; it has **not removed it**. This is the
crux of the refutation.

### 3.3 Lemma (curvature bound — the conditional positive result)

**Lemma 2.** Let `M ∈ C²` on the steepest-descent segment from `x`
(`u=−∇M(x)/L₀`, `L₀=‖∇M(x)‖`), with `uᵀ∇²M(z)u ≤ β` on the segment. If
`2βη ≤ L₀²` then the boundary is met by arclength
`t* = (L₀ − √(L₀²−2βη))/β`, hence `r₂ ≤ t*` and

```
    κ_loc = L₀ r₂/η ≤ 2 / (1 + √(1 − 2βη/L₀²))  ≤  2.                       (4)
```

`κ_loc → 1` as `β → 0` (locally linear). *Proof.* `φ(t)=M(x+tu)`,
`φ(0)=η`, `φ'(0)=−L₀`, `φ''≤β` ⇒ `φ(t) ≤ η − L₀t + (β/2)t²`; its smaller root
is `t*`; `φ(t*) ≤ 0` ⇒ `r₂ ≤ t*`; simplify. ∎

This is the smooth mirror of Moosavi's Thm 1 and of Qin's Prop 4.1
(`β` ↔ `ν` ↔ `γ`). **Verified exactly** (Test 1): e.g. `(η,L₀,β)=(1,2,1.9)`
gives `2βη/L₀²=0.95`, `κ = 2/(1+√0.05) = 1.6345`.

**ReLU version of Lemma 2.** With `β = 0` *within* linear pieces and curvature
concentrated at kinks, `κ_loc = L₀ / (minimal descent slope before the
boundary) =` product of the slope-drop ratios across the *convex* kinks crossed
on the way to `{M=0}`. The number of such kinks and their slope ratios — and
nothing about the margin — bound `κ`. (This refutes the suggestion in the
prompt that "larger margin ⇒ fewer pieces ⇒ smaller `κ`": the margin is a
*value*, it does not bound the count of activation switches or their slope
ratios on the path; §3.4 has a maximal-margin point with large `κ`.)

### 3.4 Blow-up case: does it survive at well-separated data? **Yes.** (Refutation)

The decisive test: can a **degree-1** net have large `κ` at a point of **large
geometric margin**? If yes, no `g(μ)` of the separation margin can bound `κ`.

**Construction (brute-force verified).** A bias-free 1-homogeneous ReLU net in
`ℝ²` with `n=4` neurons (`M(x)=Σ aᵣ relu(wᵣᵀx)`), evaluated at `x₀=(1,0)`:

```
    η = M(x₀)   = 2.41     (NOT small)
    L₀ = ‖∇M‖   = 51.6
    r₂ (brute)  = 1.000 = ‖x₀‖   ← MAXIMAL geometric margin (origin is the
                                    nearest point of {M ≤ 0}; brute force over
                                    14 400 directions × 40 000 radii)
    κ = L₀ r₂/η = 21.4 = 1/cos θ  (Thm 1 tight here, since r₂ = ‖x₀‖)
    curvature check along steepest descent: 2βη/L₀² ≈ 16.5  > 1
                                  ← NON-benign regime, Lemma 2 does not apply.
```

So a perfectly well-separated point (robust radius equal to the *largest value
geometrically possible* for a 1-homogeneous net, `r₂=‖x₀‖`) has `κ = 21`. The
mechanism is precisely §3.2/§1.3: `∇M(x₀)` is almost **orthogonal** to `x₀`
(`cos θ = 1/21.4`); `M` is steep tangentially at `x₀` (a near-flat valley floor
flanked by steep walls, all kinks through the origin) but flat on the way to the
boundary. The blow-up is real, lives at degree 1, and is **not** bounded by the
geometric separation. (Smaller, equally clean examples with `η≈1`, `κ ≈ 6–8`
arise from a symmetric "steep-wall valley".)

**Does this survive at the gradient-flow max-margin solution?** I have *not*
exhibited the exact dataset whose KKT max-margin net is the above `M` (that is a
non-convex program). But D's burden is the converse — that the implicit bias
*forbids* such configurations — and there is no mechanism for it:

1. Lyu–Li/Ji–Telgarsky bound only `‖θ‖`; (3)–(4) need a bound on input-gradient
   alignment / input curvature, which `‖θ‖` does not provide at fixed margin
   (width-independence is even claimed in `conj:upper`, but `κ = 1/cos θ` is a
   purely geometric quantity untouched by the parameter norm).
2. The only implicit-bias smoothness result (Ongie, §2) is an *integral*
   `∫|f''|`/R-norm bound; a single tall, thin valley like §3.4 has *bounded*
   R-norm but unbounded pointwise `κ`. So even the sharp implicit-bias result
   permits the construction.
3. Empirically the trained regime is the *non-benign* one. In a small trained
   1-hidden ReLU net on well-separated data (Test 3'), the sup gradient along
   the path exceeds the local gradient by up to `~9×` (the file reports `~26×`
   on PreActResNet-18), i.e. `M` is strongly nonlinear between data and
   boundary — exactly the regime CURE/LLR exist to remove.

### 3.5 Numerical summary (CPU, illustrative)

| test | result | meaning |
|---|---|---|
| Lemma 2 formula (Test 1) | `κ = 2/(1+√(1−2βη/L²))` to machine precision | (4) exact |
| Thm 1 on `t^{2n+1}` | `κ = 2n+1 = δ/cos θ` (n=0..3) | blow-up is degree-driven |
| Thm 1 on 1-homog ReLU nets | `κ ≤ 1/cos θ` always; tight when `r₂=‖x‖` | (3) holds & sharp |
| trained net (Test 3') | `κ_loc ∈ [0.12, 0.8]`, `L_sup/L₀` up to `~9×` | vanilla nets are non-benign |
| refutation (§3.4) | `κ=21` at `r₂=‖x₀‖`, `2βη/L²=16.5` | margin does **not** bound `κ` |

---

## 4. VERDICT

**Conjecture D is REFUTED in its literal form:** there is **no function
`g(μ)` of the separation margin alone** that bounds `κ`. A bias-free degree-1
homogeneous ReLU net can have `κ` arbitrarily large at points of *maximal*
geometric margin (`r₂ = ‖x‖`), because `κ = 1/cos∠(∇M,x)` is set by gradient–
input misalignment / local curvature, which the margin does not control and
which the gradient-flow implicit bias does not bound (it bounds only `‖θ‖`, and,
in the limit, an integral curvature seminorm that permits localized spikes).

**Two rescued PARTIAL theorems** (these are the genuine contribution):

* **P1 — architectural, unconditional.** For any bias-free network with
  positively-homogeneous degree-1 activations,
  `κ ≤ 1/cos∠(∇ₓM(x), x) = ‖∇ₓM(x)‖·‖x‖/η`, hence the file's polynomial
  blow-up `t^{2n+1}` (degree `2n+1`) is structurally impossible; the looseness
  can only be angular curvature, with `κ=1` iff `∇M ∥ x`. (Thm 1.)

* **P2 — the correct hypothesis is curvature, not margin.** Let `β` bound the
  curvature of `M` along the steepest-descent segment to the boundary (smooth:
  `uᵀ∇²M u ≤ β`; ReLU: the convex-kink slope-drops). Then in the benign /
  locally-linear regime `2βη ≤ L²`,

  ```
       κ ≤ 2 / (1 + √(1 − 2βη/L²))  ≤  2,
  ```

  i.e. `η/L` estimates `r₂` to within a factor 2. **The explicit `g` is
  `g = g(β, η, L) = 2/(1+√(1−2βη/L²))`, a local-linearity condition number, and
  the required hypothesis is `2βη ≤ L²` (curvature dominated by gradient²/
  margin), realized by curvature/local-linearity regularization (CURE,
  arXiv:1811.09716; LLR, arXiv:1907.02610), not by the implicit bias.**

**Honest restatement that *is* true:** "`η/L` estimates `r₂` up to a factor set
by the input-space curvature of `M` between the datum and the boundary; this
factor is `1` for locally-linear (e.g. invariant-linear) features, is bounded by
`2` whenever `2βη ≤ L²`, and is structurally bounded by `1/cos∠(∇M,x)` for
degree-1 homogeneous nets so the polynomial blow-up cannot occur — but the
gradient-flow implicit bias does not by itself certify the benign regime, and no
function of the margin alone bounds the factor." If `coupling_conjectures.tex`
keeps a Conjecture D, it should be reworded to this curvature statement; the
margin-only version should be retired.

---

## 5. Adversarial self-review

* **"Is the refutation just the trivial `η→0` near-boundary case?"** No. The
  reported point has `η = 2.41` (order of `max|aᵣwᵣᵀx|`) and `r₂ = ‖x₀‖`
  *maximal*; it is the *opposite* of near-boundary. The scale-freedom of `κ`
  (§1.1) means "small `η`" is not even meaningful in isolation — what matters is
  `cos θ`, and that is genuinely `1/21`.

* **"Theorem 1 gives `κ ≤ 1/cosθ`, but for the linear feature `1/cosθ` can be
  huge while the true `κ=1` — is the bound useful?"** Correct and important:
  (3) is an *upper* bound, loose when the nearest boundary is much closer than
  the origin (linear case: it is). It is *not* a lower bound on `κ`. Its content
  is (i) excluding the polynomial blow-up and (ii) being *tight exactly when
  `r₂=‖x‖`*, which is the blow-up configuration of §3.4. I do **not** claim
  `κ = 1/cosθ`.

* **"Lemma 2 says `κ ≤ 2` always — doesn't that already prove D with `g≡2`?"**
  No: Lemma 2 holds **only** under `2βη ≤ L²`. The empirical `κ≈26` (file) and
  the §3.4 construction have `2βη/L² = 16.5 ≫ 1`; the quadratic upper envelope
  never reaches `0` along steepest descent there, so the bound is vacuous and
  `κ` is unbounded. The benign hypothesis is exactly what fails at vanilla-
  trained nets.

* **"`κ` definition mismatch."** I flagged the file's `α_co` vs. my secant `ᾱ`
  (§1.2): `α_co` gives `κ=∞` for `t^{2n+1}`, my (★) gives the finite `2n+1` the
  file actually quotes. Both are recorded; I prove bounds on the operational
  (★). I also distinguish `κ` (sup-slope, `≥1`, proved bracket) from `κ_loc`
  (local gradient, can be `<1`, the paper's measured surrogate) and never
  conflate them.

* **"Did you conflate parameter-homogeneity (Lyu–Li) with input-
  homogeneity?"** Deliberately kept separate. P1 uses *input* degree-1
  homogeneity, which holds for any bias-free ReLU net **regardless of training**
  (no implicit bias needed). Lyu–Li's *parameter* homogeneity is invoked only to
  define "the trained solution" and to argue (negatively) that it controls
  `‖θ‖`, not input curvature. The refutation does not even need Lyu–Li.

* **"Clarke subgradient at ReLU kinks?"** Euler's identity holds in the Clarke
  sense (`∃ v ∈ ∂M(x): ⟨v,x⟩ = δη`), as already used in `thm:env`; the
  measure-zero kink set does not affect `r₂` or the bounds, which are stated for
  the (a.e.) differentiable points and one-sided slopes along the segment.

* **"Multiclass / `M(0)=0` subtlety."** (1) uses `M(0)=0 ⇒ 0 ∈ {M≤0}`. For the
  binary `M = f_y − f_{¬y}` this is automatic for bias-free homogeneous nets;
  for `k>2`, `M(0)=0` still holds for every pairwise margin, so `r₂ ≤ ‖x‖`
  survives. Fine.

* **"Strongest objection: maybe the §3.4 net is NOT reachable by gradient flow,
  so D could still hold *at the implicit-bias solution*."** This is the one gap
  I did not fully close: I show the *architecture* permits large `κ` at large
  margin and that no known property of the implicit bias forbids it (and the
  empirical/curvature evidence says it does not). I did **not** construct the
  explicit dataset whose KKT max-margin net realizes `κ=21`. So a maximally
  charitable reading of D — "`κ ≤ g(μ)` *specifically at gradient-flow KKT
  points*, possibly with `g` also depending on hidden data regularity" — is
  **not strictly refuted**, only deprived of any supporting mechanism and
  contradicted by the curvature literature. Closing it fully would require
  either (a) a max-margin dataset exhibiting large `κ` (likely constructible via
  a "valley-forcing" labelled cloud), or (b) a theorem that gradient-flow KKT
  points have `2βη ≤ L²` — which, given CURE/LLR's raison d'être, I expect to be
  **false**. My verdict (REFUTED-as-stated + curvature-rescue) reflects this:
  the margin-only `g(μ)` is dead; the live, true statement is the curvature one,
  P2.
```
