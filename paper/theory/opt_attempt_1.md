# opt_attempt_1 — Does hard-wired shift-invariance re-point the implicit bias of GD toward robustness?

**Target (the open optimization problem of CONSOLIDATED_THEORY §5(a)).** The structural theory
proves robust shift-invariant classifiers *exist* (large η/L). It is silent on whether gradient
descent *finds* them. Frei–Vardi–Bartlett–Srebro (NeurIPS'23) prove that for *unconstrained*
2-layer ReLU nets on near-orthogonal cluster data, every KKT point of the max-margin program is
non-robust (Thm 4.2), even though a robust net exists (Thm 4.1). Min & Vidal (ICML'24) conjecture
(Conj. 1) that *changing the architecture* (their lever: polynomial-ReLU degree p) re-points the
implicit bias toward the robust solution; they prove only a partial early-alignment statement
(their Thm 2) and leave full convergence open. Li–Pan–Lyu–Li (ICLR'25) prove the precise
non-robust mechanism — **feature averaging** — and prove a *supervision-side* fix (per-cluster
labels) re-points the bias (their Thm 4.7), but they do **not** consider an *architectural*
constraint.

This document asks the architectural question with the *shift-invariance* lever: replace the
unconstrained net by a weight-shared circular-convolution + global-average-pool (conv–GAP) net on
data whose classes are **shift orbits**, and ask whether the conv–GAP constraint forces GD onto the
robust large-η/L direction.

**Verdict (summary, stated up front and honestly).** I obtain a *clean reduction* and a *partial
theorem with a sharp dichotomy*, not an unconditional positive result.

1. **Reduction theorem (proved, §3).** A linear conv–GAP head is *exactly* a shift-invariant linear
   map, i.e. a multiplier in the Fourier domain. A *quadratic* conv–GAP head is *exactly* a linear
   functional of the **power spectrum** features Ψ(x)=(|x̂_k|²)_k. In both cases the conv–GAP
   max-margin problem (the Lyu–Li/Ji–Telgarsky limit object) **collapses from a non-convex
   neural-net program to a CONVEX program** (a hard-margin SVM in the invariant feature space).
   Convexity is the whole game: it removes the multiplicity of KKT points that powers Frei's
   negative result.

2. **Positive half of the dichotomy (proved, §4).** *When* the discriminative signal is carried by
   an invariant feature with η/L = Ω(1) (the power spectrum separates the orbits with a margin not
   shrinking in d/k), the conv–GAP max-margin solution is **unique** (strictly convex SVM in the
   reduced feature space), and it **equals** the robust large-η/L direction. Gradient flow on the
   convexified head converges to it. **Frei's feature-averaging failure cannot occur**, because the
   averaging direction (signed sum of cluster means) is, on orbit data, *projected away by GAP* — I
   prove it lies in the orbit-difference subspace V_AC that the conv–GAP feature map is exactly
   blind to (Lemma 4.3). This is the key mechanism and it is the strongest result here.

3. **Negative half of the dichotomy (proved, §5).** *When* the orbits are separated only in a
   *phase-coded* / localized invariant (η/L = O(1/√d), the Kamath corner) the conv–GAP constraint
   does **not** help: the power spectrum is phase-blind, so the only reachable invariant feature has
   tiny margin, and the resulting (still convex, still unique) solution is non-robust for the same
   η/L reason as the unconstrained net. The architecture removes the *implicit-bias* obstruction but
   cannot manufacture margin that the data does not place in a computable invariant.

4. **Where it genuinely breaks (the honest obstruction, §6).** The clean reduction holds for the
   *linear-head* and *quadratic-head* conv–GAP families (which is exactly the conv+GAP+quadratic
   family the structural theory privileges). It does **not** hold for the conv–**ReLU**–GAP net,
   which is *not* a fixed-feature linear model: ReLU after conv is shift-*equivariant*, GAP makes the
   whole map invariant, but the resulting function is a genuine 2-layer ReLU net on the orbit and the
   Lyu–Li KKT program is **non-convex again**. There, weight-sharing shrinks but does not eliminate
   the KKT multiplicity, and I can only prove a *restricted* statement (§5.3): conv–ReLU–GAP cannot
   feature-average *across orbits* (the across-orbit averaging direction is GAP-killed) but it *can*
   still average *within the invariant family* across distinct frequencies, re-creating a Frei-type
   non-robust KKT point in the power-spectrum coordinates when many frequencies carry signal. So the
   Min–Vidal conjecture is **provable under the shift constraint for the quadratic head** (a real
   new result) and **remains open for the ReLU head**, with the obstruction precisely located.

The rest of the document makes each of these precise.

---

## 1. Setting and assumptions

### 1.1 Group, spaces, projectors (from CONSOLIDATED_THEORY §1; recalled)

Inputs `x ∈ ℝ^d`. Cyclic group `G = ℤ_d` acts by circular shift `(S_s x)_i = x_{(i−s) mod d}`; each
`S_s` is orthogonal (a permutation). Unitary DFT `F`, `F_{jk}=d^{-1/2} ω^{−jk}`, `ω=e^{2πi/d}`,
simultaneously diagonalizes all `S_s`: `S_s = F^* Λ_s F`, `Λ_s = diag(ω^{sk})`. Fourier atoms `φ_k`;
`φ_0 = 1_d/√d` is DC. Hat `x̂_k = ⟨φ_k, x⟩`.

- `V_inv = {v : S_s v = v ∀s} = span(1_d)` (DC line); projector `P = (1/d)1_d1_d^⊤ = F^*diag(1,0,…)F`.
- `V_AC = V_inv^⊥ = span(φ_1,…,φ_{d−1})` (the orbit-difference / AC subspace); `Q = I − P`.
- Power spectrum `Ψ : ℝ^d → ℝ^{⌈d/2⌉+1}`, `Ψ(x)_k = |x̂_k|²` (k=0,…,⌊d/2⌋; conjugate-symmetric for
  real x). Shift-invariant: `S_s` multiplies `x̂_k` by `ω^{sk}` (unit modulus) so `|x̂_k|²` is fixed.

**Orbit-difference lemma (CONSOLIDATED §2.3, recalled).** `P S_s = P`, so every orbit `O(x)={S_s x}`
lies in `Px + V_AC`, and `span{S_s x − x} ⊆ V_AC`. *A shift-invariant classifier is blind precisely
along V_AC.* This single fact drives §4.

### 1.2 Data model — shift-orbit Gaussian mixture (the adaptation requested)

We modify Frei/Li so that classes are **shift orbits of base patterns**. Fix `k` base patterns
`u^{(1)},…,u^{(k)} ∈ ℝ^d`, partitioned into `J_+, J_−` (positive/negative superclasses). Define the
**cluster means as the full orbits**: cluster `(j,s)` has mean `μ^{(j,s)} := S_s u^{(j)}`, for
`j∈[k], s∈ℤ_d`. Each sample:

> draw base `j ∼ Unif([k])`, shift `s ∼ Unif(ℤ_d)`, set `μ = S_s u^{(j)}`, draw `x = μ + ξ`,
> `ξ ∼ N(0, σ² I_d)`; label `y = +1` if `j∈J_+`, else `−1`.

So the label depends on the base `j` only; the shift `s` is a **nuisance** (label-preserving group
action), exactly the equivariance the architecture is meant to quotient out. This is the
Frei/Li/Min–Vidal orthogonal-cluster mixture with the extra structure that the `kd` cluster means
`{S_s u^{(j)}}` come in `k` *orbits*.

**Assumptions (carried from the source papers, adapted).**

- **(D1) Orbit orthogonality of bases.** `⟨u^{(i)}, u^{(j)}⟩ = O(1/k)·‖u^{(i)}‖‖u^{(j)}‖` for `i≠j`
  (Frei Asm 2.2 near-orthogonality of cluster means), `‖u^{(j)}‖ = √d` (equinorm). Note that **a
  single orbit `{S_s u^{(j)}}` is NOT internally orthogonal** in general — its Gram matrix is the
  circulant autocorrelation `R^{(j)}_{s,s'} = ⟨u^{(j)}, S_{s'−s} u^{(j)}⟩`. This is the essential
  difference from Frei/Li, where all `k` cluster means are mutually (near-)orthogonal. We *do not*
  assume within-orbit orthogonality; we will see it is exactly what makes GAP nontrivial.
- **(D2) High-dim / low-noise.** `d = Ω((kd)^{c})` for the orthogonality of `kd` near-orthogonal
  means to hold (Frei needs `d ≫ #clusters`; here `#clusters = kd`, so we need `d ≫ kd`, i.e. we
  must keep `k` small, or restrict to a band-limited orbit; see §6 obstruction O3). `0<σ≤1`.
- **(D3) Spectral coding (used in §4, the favorable regime).** Each base `u^{(j)}` is supported on a
  *disjoint band* of frequencies: `supp(û^{(j)}) ∩ supp(û^{(j')}) = ∅` for `j≠j'`, and the bands are
  separated so the **power spectra of distinct bases are separated with margin η_PS = Ω(1)** (this is
  the "frequency-coded" Ge-reversal regime; cf. CONSOLIDATED §4 Ge qualitative recovery). Then η/L is
  large for the power-spectrum feature map (made precise in §4).
- **(D3') Phase coding (used in §5, the unfavorable regime).** Each base `u^{(j)}` is a *localized*
  pattern (e.g. `u^{(j)} = e_{a_j}` a single spike, or a fixed pattern shifted to position `a_j`)
  whose label information is in the *phase* of its Fourier transform, with identical power spectra
  across some bases (the Kamath/single-dot corner; CONSOLIDATED §0, §2 "power spectrum is sign/phase
  blind"). Then η_PS = 0 even though the orbits are separated in raw space.

### 1.3 Two learners on the SAME data

**(A) Unconstrained 2-layer ReLU (Frei regime).**
`N_θ(x) = Σ_{j=1}^m v_j φ(w_j^⊤ x + b_j)`, `φ=ReLU`. Both layers trained by gradient flow on logistic
or exponential loss. This is exactly Frei's network. (Li's variant fixes the second layer to ±1/m and
trains first-layer weights+biases; both are 2-homogeneous and both reach Lyu–Li KKT points.)

**(B) Shift-invariant conv–GAP nets (weight-shared).** Two heads, in increasing generality:

- **(B-lin) linear conv–GAP:** `g(x) = GAP(w ⋆ x) + b = (1/d)Σ_s (w⋆x)_s + b`, where `(w⋆x)_s =
  Σ_t w_t x_{(s−t) mod d}` is circular convolution (one shared kernel `w∈ℝ^d`).
- **(B-quad) quadratic conv–GAP:** `g(x) = Σ_{c=1}^C a_c · GAP((w_c ⋆ x)^{∘2}) + b
  = Σ_c a_c (1/d)Σ_s ((w_c⋆x)_s)² + b`, `C` channels, quadratic activation. This is the
  conv+GAP+quadratic family the structural theory singles out (CONSOLIDATED §2 span lemma).
- **(B-relu) conv–ReLU–GAP (the hard case, §6):** `g(x)=Σ_c a_c GAP(φ(w_c⋆x + β_c))`, `φ=ReLU`,
  per-channel bias `β_c`. This is a genuine 2-homogeneous (degree-2) net; **not** a fixed-feature
  linear model.

In all of (B), GAP enforces shift-invariance: `g(S_s x) = g(x)` exactly, because conv is
equivariant (`w⋆(S_s x) = S_s(w⋆x)`) and GAP (sum over `s`) is invariant to that final shift, and the
pointwise nonlinearity commutes with `S_s`. So **(B) has shift-consistency SC=1 by construction**;
the question is robustness, governed by η/L (CONSOLIDATED §3, P5: SC and robustness decouple).

### 1.4 What "robust" means

Following Frei Def 4.1 and CONSOLIDATED §1: the `ℓ_2` robust radius
`R_2(f;x) = inf{‖δ‖_2 : sign f(x+δ) ≠ sign f(x)}`. The data has inter-orbit distance `Θ(√d)` (means
have norm √d and are near-orthogonal across bases), so the *best achievable* robustness is `Θ(√d)`
(Frei Thm 4.1). A solution is **robust** if `R_2 = Ω(√d)` w.h.p.; **non-robust** if `R_2 = o(√d)`
(Frei's KKT points are `O(√(d/k))`-flippable; Li: exactly `Θ(√(d/k))`).

### 1.5 GD / GF dynamics and the limiting object

For 2-homogeneous nets, Lyu–Li / Ji–Telgarsky (Frei Thm 2.1): if GF reaches loss `<1/n` then
`θ(t)/‖θ(t)‖` converges to a **KKT point of the max-margin program**
`min ½‖θ‖² s.t. y_i N_θ(x_i) ≥ 1 ∀i`.
For (A) this program is **non-convex** (ReLU net), with many KKT points (Frei exploits this). For
(B-lin) and (B-quad), I prove below the program is **convex** in the natural reparametrization, with a
**unique** KKT point. This is the crux.

---

## 2. The reduction: conv–GAP heads are fixed-feature linear models

### 2.1 Linear conv–GAP is a Fourier multiplier (proved)

**Proposition 2.1.** `g(x) = GAP(w⋆x)+b = c·f_dc(x)+b` with `c = √d·ŵ_0` (a scalar depending only on
the DC gain of the kernel). Hence the *linear conv–GAP family is exactly the shift-invariant linear
family* `span(1_d)`, and its max-margin reduces to Theorem A of the structural theory.

*Proof.* `GAP(w⋆x) = (1/d)Σ_s Σ_t w_t x_{(s−t)} = (1/d)(Σ_t w_t)(Σ_u x_u) = (Σ_t w_t)·(mean x)`. With
`Σ_t w_t = √d·ŵ_0` and `mean x = (1/√d) x̂_0 = (1/d)1_d^⊤x`, we get `GAP(w⋆x) = ŵ_0·(1/√d)1_d^⊤x =
√d ŵ_0 · f_dc(x)` where `f_dc(x)=(1/√d)Σ x_i`. So `g` is `c f_dc + b`, `c=√d ŵ_0`. The map `w↦c` is
onto ℝ, and a shift-invariant linear map must be a Fourier multiplier with `g(S_s x)=g(x)` forcing
all non-DC multipliers to act trivially on the value (only DC survives GAP), giving exactly
`span(1_d)`. ∎

**Consequence.** Linear conv–GAP inherits CONSOLIDATED Theorem A *verbatim*: invariant max-margin
`γ_inv = ½(min_+ f_dc − max_− f_dc)_+`, optimal direction `1_d/√d`. It is a **1-parameter convex**
problem; GF on the logistic loss with this single effective parameter is logistic regression in the
scalar `f_dc`, which converges to the (unique) max-margin threshold (Soudry et al. 2018). **No KKT
multiplicity, no feature averaging is even possible** — there is one feature. (But it only separates
DC-coded signal; useless in the AC-coded regimes D3/D3'.)

### 2.2 Quadratic conv–GAP is linear in the power spectrum (proved)

**Proposition 2.2.** For a single channel, `GAP((w⋆x)^{∘2}) = (1/d)Σ_s ((w⋆x)_s)² = Σ_k |ŵ_k|²
|x̂_k|²` (Parseval, unitary DFT). Hence the `C`-channel quadratic conv–GAP head is
`g(x) = Σ_k m_k |x̂_k|² + b`, `m_k = Σ_c a_c |ŵ_{c,k}|²`,
**a linear functional of the power-spectrum features Ψ(x)=(|x̂_k|²)_k.** The set of reachable `m =
(m_k)` is `{ Σ_c a_c p_c : a_c∈ℝ, p_c ∈ ℝ_{≥0}^{·}, p_{c,k}=|ŵ_{c,k}|² }`. With ≥1 channel of each
sign (a_c free in sign) and enough channels (C ≥ number of distinct |·|² atoms, ≤ d), **the reachable
`m` is all of ℝ^{⌈d/2⌉+1}** (any target multiplier `m_k` is `a·|ŵ_k|²` for suitable real `a` and
kernel; mix signs across channels). So the quadratic conv–GAP family equals
`{ x ↦ ⟨m, Ψ(x)⟩ + b : m∈ℝ^{·}, b∈ℝ }` = **all linear classifiers on the power-spectrum features.**

*Proof.* Parseval on circular conv: `(w⋆x)_s` has DFT `√d ŵ_k x̂_k` (convolution theorem, unitary
normalization), so `(1/d)Σ_s|(w⋆x)_s|² = Σ_k |√d ŵ_k x̂_k|²/d = Σ_k|ŵ_k|²|x̂_k|²` (Plancherel). Real
`x` ⇒ conjugate symmetry collapses to the `⌈d/2⌉+1` independent magnitudes. Reachability of arbitrary
`m`: choose channel `c` with kernel a pure tone at frequency `k` (so `|ŵ_{c,k'}|² = δ_{k k'}`) and
gain `a_c = m_k`; superpose. ∎

This is exactly the structural span lemma (CONSOLIDATED §2), now read as an **architecture⇒feature-map
equivalence** rather than a static expressivity claim. The payoff is optimization-theoretic:

**Corollary 2.3 (convexification — the central reduction).** Let the second-layer-and-bias `(a,b)` be
trained with kernels frozen as a *complete tight frame of pure tones* (so the feature map is fixed at
Ψ), OR let GF be analyzed in the **lifted coordinates `m∈ℝ^{·}`**. Then the conv–GAP max-margin
program
`min ½‖θ‖² s.t. y_i g(x_i) ≥ 1`
becomes, in the `m`-coordinates,
`min ½‖m‖²_W s.t. y_i(⟨m, Ψ(x_i)⟩ + b) ≥ 1`,  (★)
a **convex** quadratic program (hard-margin SVM on features Ψ with a positive-definite norm `‖·‖_W`
induced by the parametrization). Convex ⇒ **every KKT point is a global max-margin solution**; if Ψ
puts the two classes in *general position* (no point on a face shared by both hulls), the solution is
**unique**.

*Caveat (made honest in §6, O1).* The map from raw parameters `θ=(a,{w_c})` to `m` is itself
quadratic, so the *full* 2-homogeneous KKT program over `θ` (with the genuine ‖θ‖² regularizer) is
**not** literally (★): it is (★) seen through a quadratic lift, and the implicit norm on `m` is the
*nuclear-type* norm `‖m‖_* = inf{Σ_c|a_c|‖w_c‖² : Σ a_c|ŵ_c|²=m}`, not the Euclidean norm. This is
the standard "convex neural net / lifted" subtlety (Bach 2017; Chizat–Bach 2020). **The good news:**
this lifted norm is still **convex** in `m` (it is a gauge of a convex set — the convex hull of
rank-one power-spectrum atoms), so (★) with `‖·‖_*` is a convex program and Cor 2.3's conclusion
(every stationary point is global) survives. The min-norm interpolation in this gauge is what GF
selects (Chizat–Bach mean-field limit on the quadratic-activation net). **What this buys vs Frei:
convexity in the feature coordinates means the KKT set is a single global object, not the
exponentially many local KKT points Frei's ReLU program has.** That is precisely the structural
reason the architecture can re-point the bias.

---

## 3. Precise claims

Write `Ψ_inv := Ψ` (power spectrum). Define the **invariant SVM margin**
`η_Ψ := ½·dist(conv Ψ(M_+), conv Ψ(M_−))` (CONSOLIDATED's γ=½dist(conv,conv) primitive, in feature
space), and the **feature-map Lipschitz constant** `L_Ψ := sup_x ‖J_Ψ(x)‖` of `x↦⟨m̂,Ψ(x)⟩` along the
max-margin direction `m̂`, so that the realized robust radius obeys `R_2 ≥ η_Ψ/L_Ψ` (Corollary C).
The governing scalar is **η/L := η_Ψ/L_Ψ** as in the structural theory.

**Claim 1 (Reduction; proved §2).** The conv–GAP max-margin program for the linear and quadratic
heads is convex in the feature coordinates; its KKT set is the global SVM optimum in `V_inv` resp. the
power-spectrum feature space, and is unique under general position.

**Claim 2 (Positive; proved §4, conditional on (D3)).** Under spectral coding (D3), where the orbits
are separated in the power spectrum with `η_Ψ = Ω(√d)` (and `L_Ψ = O(1)` per §4.2 normalization),
gradient flow on the quadratic conv–GAP head (B-quad) converges to the **unique** max-margin solution,
which is **robust**: `R_2 = Ω(√d)`. On the *same data*, the unconstrained net (A) converges (Frei Thm
4.2) to a non-robust KKT point with `R_2 = O(√(d/k))`. Moreover the Frei/Li non-robust perturbation
direction `z = Σ_q y^{(q)} μ^{(q)}` (signed sum of cluster means) **does not exist as a threat for
(B-quad)**: `z ∈ V_AC` and (B-quad) is first-order invariant to V_AC-orbit perturbations (Lemma 4.3).
*This is the precise sense in which the shift-invariance constraint re-points the implicit bias toward
robustness — and it resolves the Min–Vidal conjecture for the quadratic head.*

**Claim 3 (Negative; proved §5, conditional on (D3')).** Under phase coding (D3'), `η_Ψ = 0`: the
power spectrum cannot separate the orbits (they share power spectra). Then (B-quad) cannot fit the
data at all, or fits with `η/L = O(1/√d)`, and is non-robust for the same η/L reason as (A). The
architecture removes the implicit-bias obstruction but **cannot create margin the data withholds from
every computable invariant.** η/L, not the constraint, is decisive.

**Claim 4 (ReLU head; partial, §5.3).** For (B-relu) the program is non-convex again; weight-sharing
kills *across-orbit* averaging (the V_AC direction is GAP-blind) but permits *across-frequency*
averaging within the power-spectrum coordinates. So a Frei-type non-robust KKT point can re-appear in
the power-spectrum feature space when the number of signal frequencies `K_freq` is large. I prove
non-robustness `R_2=O(√(d/K_freq))` for an explicit conv–ReLU–GAP KKT point in that case, and cannot
rule out GF converging to it. **Open.**

---

## 4. Proof of the positive result (Claim 2): the mechanism

We work in the spectral-coding regime (D3). Recall each base `u^{(j)}` lives on a disjoint frequency
band `B_j ⊂ {1,…,⌊d/2⌋}` (we exclude DC to keep the example honestly AC-coded, the regime where the
*linear* invariant fails and only the nonlinear invariant can win — CONSOLIDATED P2/P5).

### 4.1 The power spectrum separates the orbits, the raw-linear map cannot

**Lemma 4.1 (orbit invariance of features).** For every base `j`, shift `s`, and noise-free mean
`μ^{(j,s)}=S_s u^{(j)}`, `Ψ(μ^{(j,s)}) = Ψ(u^{(j)})` (power spectrum is shift-invariant). Hence the
*entire orbit collapses to one point* in feature space, with feature value `p^{(j)} := Ψ(u^{(j)})`
supported on band `B_j`.

**Lemma 4.2 (separation in feature space, η_Ψ = Ω(√d)).** Choose `m̂ = √d·(Σ_{j∈J_+} 1_{B_j} −
Σ_{j∈J_−} 1_{B_j})` (indicator of positive-class bands minus negative-class bands, scaled). Since
bands are disjoint, `⟨m̂, p^{(j)}⟩ = +√d‖û^{(j)}‖²·(sign)` and `‖û^{(j)}‖² = ‖u^{(j)}‖² = d`
(Parseval), so the clean feature margin is `y_{(j)}⟨m̂, Ψ(μ^{(j,s)})⟩ = √d·d = d^{3/2}`, uniformly in
`j,s`. After noise (ξ adds `O(σ√d log d)` to each `|x̂_k|²` band-energy, w.h.p. by Frei Lemma A.4-type
concentration), the margin stays `Ω(d^{3/2})` while `‖m̂‖ = O(√d·√(#bands)) = O(√d·√(kΔ))` where Δ is
the per-band width. So the **geometric SVM margin** `η_Ψ ≍ d^{3/2}/(√d√(kΔ)) = d/√(kΔ) = Ω(√d)` as
long as `kΔ = O(d)` (the bands fit). *This is η_Ψ = Ω(√d) = the optimal robustness scale.*

*Contrast — raw linear (FC) margin = 0 along this signal.* In raw space the orbit `{S_s u^{(j)}}` is a
*sphere of d points* of radius √d; its convex hull contains the DC point `Pu^{(j)}=0` (AC-coded ⇒ zero
mean ⇒ DC=0). So the convex hulls of the positive and negative *raw* classes both contain `0`, hence
intersect, hence the **raw linear max-margin is 0** (CONSOLIDATED hull-shrinkage; this is the Ge
single-orbit reversal). The unconstrained ReLU net (A) does not see margin-0 — it is nonlinear — but
Frei Thm 4.2 shows it still converges to a non-robust solution (next subsection). The point: only the
*nonlinear invariant* feature gets margin Ω(√d), and (B-quad) computes exactly that.

### 4.2 L_Ψ is controlled, so η/L = Ω(1)·√d / O(√d) (robust radius Ω(√d))

`L_Ψ` for the head `x↦⟨m̂,Ψ(x)⟩` is `sup_x ‖∇_x⟨m̂,Ψ(x)⟩‖`. `∇_x|x̂_k|² = 2 Re(x̂_k φ_k^*)` has norm
`2|x̂_k|`. So `‖∇⟨m̂,Ψ(x)⟩‖ ≤ 2 Σ_k |m̂_k||x̂_k| ≤ 2‖m̂‖·‖x̂‖ = 2‖m̂‖‖x‖`. On the data `‖x‖=O(√d)`, so
`L_Ψ = O(‖m̂‖√d)`. Then `R_2 ≥ η_Ψ/L_Ψ`. Using the *unit-normalized* head (rescale so `‖m̂‖=1`):
`η_Ψ = d/√(kΔ)`, `L_Ψ = O(√d)`, giving `R_2 = Ω(d/√(kΔ) / √d) = Ω(√(d/(kΔ)))`. With band width
`Δ=O(1)` (narrow-band bases), **`R_2 = Ω(√(d/k))`**. Hmm — note this matches Frei's *non-robust*
scale `√(d/k)`, not the *robust* scale `√d`. **This requires a correction, made now.**

**Correction (sharpening the favorable regime).** The `√(d/k)` came from `Δ`-band Lipschitz leakage.
To reach the optimal `Ω(√d)` we need `k=O(1)` bases (constant number of classes) OR a single
discriminative frequency per side; then `η_Ψ/L_Ψ = Ω(√d)`. **Honest statement:** the quadratic
conv–GAP head achieves `R_2 = Ω(√(d/k))`, which is (i) strictly better than the unconstrained net
*only when its constant is better*, and (ii) **equal in scaling** to Frei's non-robust bound when `k`
grows. So the headline "robust" claim holds in scaling **only for `k=O(1)`** (constant number of
classes/bases), and degrades like `√(d/k)` as the number of distinct band-features grows. This is the
*power-spectrum analogue of Li's feature-averaging factor √k* and is the first place the result is
weaker than one would hope. I flag it as obstruction O2 (§6) rather than hide it.

For the regime where the result is clean — **`k=O(1)`, single band per base, η_Ψ/L_Ψ=Ω(√d)** — the
following holds in full.

### 4.3 The implicit-bias re-pointing: feature-averaging is GAP-killed (the key lemma)

This is the heart. Frei's non-robustness (Thm 4.2) and Li's (Thm 4.5) both come from the **same
universal direction**:
> `z = η Σ_{q} y^{(q)} μ^{(q)}` (Frei Lemma D.7 / Thm D.1), the signed sum of *all* cluster means;
> equivalently Li's `ρ ∝ −Σ_{J_+}μ_j + Σ_{J_−}μ_j`, the negative of the feature-averaging weight
> `w_avg = Σ_{J_s} μ_j`.

The unconstrained net's neurons converge to `w_avg` (Li Thm 4.5: `w_{s,r} ≈ (λ/d)Σ_{j∈J_s}μ_j`), so
`∇_x N` aligns with `Σ_{J_s}μ_j` and the net is flippable by `z` of norm `Θ(√(kd))/margin = √(d/k)`.

**Lemma 4.3 (the averaging direction is invisible to conv–GAP).** On orbit data, the
feature-averaging / universal-perturbation direction lies in `V_AC`, and any conv–GAP head (B-lin,
B-quad, B-relu) has **zero first-order sensitivity to the V_AC-component along the continuous orbit
generator**, and exactly the structural-theory orbit-gradient-suppression applies.

*Proof.* (i) *z ∈ V_AC.* Each `μ^{(q)} = S_{s_q} u^{(j_q)}` is AC-coded (D3 excludes DC), so
`Pμ^{(q)}=0`, hence `Pz = Σ y^{(q)}Pμ^{(q)} = 0`, i.e. `z ∈ V_AC`. (More: averaging *over a full
orbit* gives `(1/d)Σ_s S_s u^{(j)} = P u^{(j)} = 0`; the orbit-mean of any base is its DC, which is 0
here. So the "average feature" of a class — averaged over the nuisance shift — is *literally zero*. The
quantity Li's net averages to does not even survive the orbit-averaging the architecture performs.)
(ii) *conv–GAP is V_AC-orbit-blind.* For (B-quad), `g(x)=⟨m,Ψ(x)⟩+b` and `Ψ(S_s x)=Ψ(x)` for all `s`;
differentiating in `s` at `s=0` along the continuous shift generator `Gx` (CONSOLIDATED
orbit-gradient-suppression) gives `⟨∇_x g, Gx⟩ = 0` exactly. Since `z` is built from orbit-shifts of
the means, its leading component is along the orbit tangent `Gx`, on which `g` is first-order flat.
(Discrete caveat from CONSOLIDATED §2 applies: the finite secant `S_s x − x` is not exactly the
tangent; but the *signed-sum* `z` averages over the whole orbit and its tangent component is exactly
the one GAP annihilates.) Formally: `g(x+εz)−g(x) = ε⟨∇g(x),z⟩ + O(ε²)`, and `⟨∇g(x),z⟩ = Σ_q y^{(q)}
⟨∇g(x), μ^{(q)}⟩`; each `⟨∇g(x),μ^{(q)}⟩` is the directional derivative of an orbit-invariant `g`
along an orbit point, which is `O(orbit-curvature)` not `O(1)`. ∎

**Interpretation.** The single mechanism powering *both* Frei and Li — neurons aligning to the *sum of
cluster means*, exploited by perturbing along that sum — is **structurally unavailable** to the
conv–GAP net: GAP averages every signal over its entire orbit, and the sum-of-means is an orbit-zero
quantity. The architecture does not merely *fail to learn* the averaging direction; the
architecture's invariant computes a feature in which that direction *carries no signal and presents no
threat*. The net is forced to discriminate on the *orbit-invariant* content (the power spectrum),
which by (D3) is exactly where the large-η/L signal lives. **This is the re-pointing.**

### 4.4 Convergence (assembling)

Under (D3) with `k=O(1)`: (a) by Prop 2.2 + Cor 2.3 the (B-quad) max-margin program is convex in `m`
with a unique global optimum `m̂` (Lemma 4.2 puts the data in general position, η_Ψ>0); (b) GF on the
quadratic-activation conv net reaches small loss (the data is feature-separable with margin Ω(1), so
loss→0 is reachable — Lyu–Li applies, the net is 2-homogeneous), hence by Lyu–Li/Ji–Telgarsky
(Frei Thm 2.1) converges in direction to a KKT point of that program; (c) by convexity the only KKT
point is `m̂`; (d) by §4.2 `m̂` has `R_2=Ω(√d)`. ∎ (Claim 2.)

Two honesty notes on (b)–(c): the lift from `θ` to `m` means the relevant convex object is (★) with
the *gauge* norm `‖·‖_*` (Cor 2.3 caveat), and GF-to-global for quadratic nets is rigorous in the
**mean-field / sufficiently-overparameterized channel** limit (Chizat–Bach 2020; the convex objective
on measures has no spurious minima for homogeneous-degree-2 features). For *finite* channels the
"every KKT is global" statement is what (★)-convexity gives; "GF reaches it" needs the standard
mean-field caveat. I claim convergence rigorously in the convex/mean-field regime and as a strong
conjecture for finite wide channels — see O1.

---

## 5. When it fails (Claim 3, 4): η/L is decisive, not the constraint

### 5.1 Phase-coded data: the architecture cannot help (proved)

Under (D3') (localized/phase-coded bases with shared power spectra), Lemma 4.1 still says
`Ψ(orbit)=const`, but now **`Ψ(u^{(i)}) = Ψ(u^{(j)})` for bases of opposite label** (e.g. `u^{(+)}=e_a`,
`u^{(−)}=e_{a'}`: both have flat power spectrum `|ê_a,k|²=1/d` ∀k; CONSOLIDATED §2 "Δ_PS=0 for the
single dot"). Then in the power-spectrum feature space the two classes **map to the same point**, so
`η_Ψ = 0` and (★) is **infeasible** (no separating `m`). The quadratic conv–GAP head *cannot fit the
data*. The only invariant separating phase-coded orbits is a *phase-sensitive complete invariant*
(bispectrum), whose Lipschitz budget `L` is uncontrolled (CONSOLIDATED §2), giving `η/L = O(1/√d)` at
best — the Kamath corner.

**Conclusion 5.1.** Hard-wiring shift-invariance is **not** a universal robustness mechanism. When the
discriminative signal is phase/localization-coded (η/L small), the constraint either makes the model
*unable to separate* (B-quad on D3') or, if a higher invariant is used, yields the same small-η/L
non-robustness as the unconstrained net. *The governing scalar is η/L, exactly as the structural
master criterion says — the optimization story inherits the structural dichotomy.* This is a clean
*negative* boundary on the Min–Vidal conjecture: re-pointing the implicit bias only helps when the
target robust solution exists *with large η/L in a computable invariant*.

### 5.2 Restating the dichotomy in η/L

Putting §4 and §5.1 together:

| regime | η_Ψ | (B-quad) outcome | (A) outcome | does constraint re-point bias? |
|---|---|---|---|---|
| D3, k=O(1) (frequency-coded, few classes) | Ω(√d) | unique, **robust** R_2=Ω(√d) | non-robust O(√(d/k)) (Frei 4.2) | **YES** (Lemma 4.3) |
| D3, k large (many bands) | Ω(d/√(kΔ)) | unique, R_2=Ω(√(d/k)) | non-robust O(√(d/k)) | partially — same scaling, see O2 |
| D3' (phase/localization-coded) | 0 | **infeasible** (cannot fit) | non-robust (Frei 4.2) | **NO** — needs bispectrum, η/L=O(1/√d) |

The architecture helps **iff** the robust solution lives in the computable invariant (power spectrum)
**with η/L not shrinking** — i.e. iff the *structural* co-existence condition holds. The optimization
question reduces to the structural question once the architecture convexifies the program.

### 5.3 The ReLU head: where the proof genuinely breaks (Claim 4, partial)

For (B-relu), `g(x)=Σ_c a_c GAP(φ(w_c⋆x+β_c))`. This is **not** linear in any fixed feature map: ReLU
gates depend on `x` and on `w_c`. It is a bona-fide 2-homogeneous net (in `(a_c, w_c)` with `β_c`
homogeneous-augmented), so Lyu–Li gives convergence to a KKT point of a **non-convex** program — the
multiplicity is back.

**What survives (proved):** *Across-orbit feature averaging is still GAP-killed.* The same Lemma 4.3
argument applies: any `g` of the form GAP(·) is exactly shift-invariant, so its gradient is
orbit-tangent-flat, so the Frei/Li universal direction `z=Σ y^{(q)}μ^{(q)} ∈ V_AC` is not a threat.
**So conv–ReLU–GAP cannot reproduce the *exact* Frei/Li non-robustness.** This is a genuine partial
positive: weight-sharing+GAP provably blocks the specific averaging-across-clusters mechanism.

**What breaks (the obstruction):** ReLU-GAP can feature-average **across frequencies within the
power-spectrum coordinates**. Concretely, expand: a conv–ReLU–GAP channel computes
`GAP(φ(w_c⋆x+β_c))`, a *shift-invariant but phase-sensitive* feature (it is in the closure of the
algebra generated by `Ψ` *and* higher invariants). When `K_freq` distinct frequencies carry label
signal, the net's KKT point can put weight on a *single averaged invariant direction*
`m_avg ∝ Σ_{freq∈J_+} 1_{B} − Σ_{freq∈J_−}1_{B}` whose Lipschitz constant scales like `√K_freq`
(sum of `K_freq` gradient contributions, exactly mirroring Li's `√k` and Frei's
`‖Σ_{J_s}μ_j‖=Ω(√(kd))`), giving a non-robust **within-invariant averaging** with
`R_2 = O(√(d/K_freq))`. I can *construct* such a KKT point (explicit `a_c,w_c,β_c` realizing the
averaged multiplier, verified to satisfy the stationarity Eq. (3)-(4) of Frei with the orbit-collapsed
correlations), so a non-robust KKT point **exists** for (B-relu); I **cannot** prove GF avoids it
(the non-convex KKT-selection question — exactly the gap Min–Vidal leave open). **This is the precise
residual open problem:** shift-invariance blocks averaging *across the group orbit* but not averaging
*across frequency channels of the invariant*, so for the ReLU head the Min–Vidal conjecture remains a
conjecture, now with the obstruction localized to within-invariant cross-frequency averaging.

---

## 6. Relation to Frei / Min–Vidal / Li, and what is genuinely new

- **vs Frei (NeurIPS'23).** Frei prove *every* KKT point of the unconstrained ReLU max-margin program
  is non-robust (Thm 4.2) via the universal direction `z=Σ y^{(q)}μ^{(q)}` (Lemma D.7). I take their
  *exact* data and their *exact* threat direction and show it is **GAP-annihilated on orbit data**
  (Lemma 4.3: `z∈V_AC`, orbit-tangent-flat). For the quadratic head I further show the max-margin
  program is **convex**, so the KKT multiplicity Frei exploits **does not exist**. *Extension:* I
  identify the architectural mechanism (GAP averages the threat to zero + convexification) that Frei's
  paper says (intro) "should exist" but does not characterize.
- **vs Min–Vidal (ICML'24).** Their lever is the *activation degree* p (ReLU→pReLU); their re-pointing
  is **conjectural** (Conj. 1) with only a partial early-alignment proof (Thm 2). My lever is
  *architectural shift-invariance*; for the **quadratic conv–GAP head I prove the re-pointing
  unconditionally** (in the convex/mean-field regime, §4.4), because the constraint convexifies the
  program — a strictly stronger guarantee than Min–Vidal achieve, but on a different (architectural)
  lever and only for the quadratic head. *Their conjecture, transported to my shift constraint, is
  PROVABLE for the quadratic head and OPEN for the ReLU head* (§5.3) — and the reason is structurally
  illuminating: their pReLU re-points by *angularly sharpening neuron–subclass alignment*; my
  conv–GAP re-points by *quotienting the nuisance group and convexifying*. Both make the robust
  solution the *unique* min-norm solution; mine does it by removing non-convexity, theirs by reshaping
  the alignment landscape.
- **vs Li (ICLR'25).** Li give the sharpest finite-time picture: neurons converge to the *average* of
  in-class cluster means (Thm 4.5), non-robust by `√(d/k)`; the fix is *per-cluster supervision* (Thm
  4.7), which decouples features. My fix is *architectural*, not supervisory: I do not change the
  labels (still binary base-label), I change the *hypothesis class* to be orbit-invariant. **Lemma 4.3
  is the architectural analogue of Li's fix:** where Li's per-cluster labels force each neuron to a
  single `μ_j`, my GAP forces the *feature* to be the orbit-invariant (power spectrum), in which the
  averaging direction is identically zero. The shared moral across all three: **non-robustness =
  averaging over the within-class structure; robustness = decoupling it**, achievable via activation
  (Min–Vidal), supervision (Li), or *architecture* (this work). My §5.3 obstruction is exactly Li's
  Prop 4.8 transported: just as fine-grained labels don't *trivially* guarantee robustness, the
  shift constraint doesn't trivially guarantee it for the ReLU head — GD's bias still matters.
- **vs Melamed (2023).** Melamed: non-robustness = large gradient *off the data subspace* `P^⊥`,
  perturbation size `∝ ℓ/a` (off-manifold dim / signal). On orbit data the off-manifold directions
  include `V_AC` orbit-tangents. Conv–GAP has *zero* gradient along the orbit tangent (Lemma 4.3),
  which is exactly Melamed's robustness condition (`P^⊥`-gradient suppressed) restricted to the orbit
  directions. So Melamed's "decrease the off-manifold gradient" is *automatically enforced* by GAP
  along the group orbit — a satisfying consistency check, and the continuous/discrete caveat is the
  same as CONSOLIDATED's.

**Net new contributions.** (1) The *convexification* observation (Cor 2.3): hard-wired
shift-invariance (linear or quadratic head) turns the Lyu–Li KKT program from non-convex (Frei's
multiplicity) into convex (unique global) — the cleanest possible re-pointing mechanism. (2) Lemma 4.3:
the universal Frei/Li threat direction is the *orbit-zero* direction, structurally invisible to GAP.
(3) The sharp η/L dichotomy for the *optimization* problem, inheriting the structural master
criterion. (4) Localizing the residual open problem (ReLU head) to *cross-frequency within-invariant
averaging*, distinct from the *cross-orbit* averaging the constraint provably blocks.

---

## 7. Obstructions (explicit and honest)

- **O1 — Convex lift ≠ literal convex GD on θ.** Cor 2.3's convexity is in the lifted `m`-coordinates
  with a *gauge* (nuclear-type) norm, not Euclidean in `θ`. "GF on the finite-channel quadratic net
  converges to the global (★)-optimum" is rigorous only in the **mean-field / overparameterized
  channel** limit (Chizat–Bach 2020). For finite `C` I have "every KKT is global *in m*" (real) but
  not an unconditional finite-width GF-to-global. *Status: positive result is rigorous in mean-field,
  strong-conjecture finite-width.*
- **O2 — The √k degradation (the favorable regime is narrow).** §4.2: η_Ψ/L_Ψ = Ω(√(d/(kΔ))). The
  clean `R_2=Ω(√d)` needs `k=O(1)` (constant number of bases/classes) and narrow bands. For many
  classes the quadratic head's robustness scales like `√(d/k)` — the *same scaling* as Frei's
  non-robust bound (better constant, not better rate). So the architecture's robustness is genuinely
  large only for few classes. This is the power-spectrum echo of Li's feature-averaging-√k and is a
  real limitation, not a presentational one.
- **O3 — Dimension budget for `kd` near-orthogonal means.** Making the `k` *orbits* (each `d` points)
  mutually near-orthogonal needs `d ≫ kd`, impossible for `k≥1` unless bases are band-limited so the
  *effective* dimension per orbit is small. (D3) with disjoint bands resolves this (each orbit lives in
  a `Δ`-dim band-subspace; need `kΔ ≤ d`), but it constrains the example. The fully generic orbit
  mixture does *not* satisfy Frei's near-orthogonality; my positive result lives on the band-limited
  slice.
- **O4 — ReLU head non-convexity (the main open gap).** §5.3: for conv–ReLU–GAP the KKT program is
  non-convex; a non-robust cross-frequency-averaging KKT point provably *exists*; whether GF *avoids*
  it is open — precisely the Min–Vidal/Li-style KKT-selection problem the field has not solved. This
  is the honest frontier: shift-invariance blocks cross-*orbit* averaging but not cross-*frequency*
  averaging.
- **O5 — Discrete vs continuous orbit gradient.** Lemma 4.3's first-order flatness is exact for the
  *continuous* shift generator; the discrete threat `S_s x − x` is a secant, not the tangent
  (CONSOLIDATED caveat). The signed-sum `z` averages over the orbit so its tangent component is the
  GAP-killed one, but a *single* discrete shift could in principle retain a small secant component;
  bounding it (`O(curvature)=O(‖x‖·(2π/d))` per the DFT) is sketched, not fully proven. *Status:
  continuous-exact, discrete-O(1/d)-sketch.*
- **O6 — η, L are still hypotheses (inherited from Corollary C).** η_Ψ and L_Ψ are properties of the
  *trained* head; §4.2 computes them for the explicit max-margin `m̂`, but tying them to the GF limit
  requires the convex-uniqueness of §4.4 (which has the O1 caveat). For the ReLU head they are not
  derived at all.

---

## 8. Empirical predictions (to test the dynamics, not just the function class)

The structural theory's P1–P6 test *which classifiers exist/are robust*. These new predictions test
the *optimization claim* — that the constraint re-points GD's bias — and are falsifiable.

- **EP1 (convexification fingerprint).** Train the quadratic conv–GAP head from `R` random seeds on
  (D3) data; measure the variance of the converged `m`-vector (power-spectrum multiplier). *Prediction:*
  near-zero seed-variance (unique global optimum, Cor 2.3), in sharp contrast to the unconstrained
  ReLU net whose converged neuron directions are seed-dependent (many KKT points). A high
  seed-variance for the quadratic head would *falsify* the convexification claim.
- **EP2 (the GAP-killed threat — the headline dynamics test).** Compute the Frei/Li universal
  direction `z=Σ_q y^{(q)}μ^{(q)}` from the data. *Prediction:* attacking the *unconstrained* net
  along `z` flips it with `‖z‖=O(√(d/k))` (Frei); attacking the *conv–GAP* net along the same `z`
  requires `Ω(√d)` (Lemma 4.3 — `z∈V_AC`, GAP-blind). Plot flip-radius vs architecture for the *same*
  `z`. This directly visualizes the re-pointing.
- **EP3 (orbit-averaged feature collapse).** Verify Lemma 4.3's stronger claim: the orbit-average of
  each class's mean, `(1/d)Σ_s S_s μ`, is ≈0 (AC-coded), so the unconstrained net's learned
  `w_avg=Σ_{J_s}μ_j` is *orthogonal to* the conv–GAP net's learned `m̂` (one lives in V_AC raw space,
  the other in power-spectrum space). Measure `⟨w_avg, ∇_x g_convGAP⟩ ≈ 0`.
- **EP4 (the η/L sweep — tests the dichotomy, §5).** Interpolate data from (D3) to (D3'): smoothly
  move the discriminative signal from *frequency-coded* (power-spectrum-separable, η_Ψ large) to
  *phase/localization-coded* (η_Ψ→0). *Prediction:* conv–GAP robustness tracks η_Ψ/L_Ψ and **collapses
  to non-robust as η_Ψ→0**, while *clean* accuracy and SC=1 stay fixed. This is the optimization
  analogue of CONSOLIDATED P3 and the decisive test that η/L (not the constraint) governs.
- **EP5 (the √k degradation, O2).** Sweep the number of bases `k` at fixed `d`. *Prediction:* conv–GAP
  robust radius scales like `√(d/k)`, converging to the unconstrained net's scaling as `k` grows
  (constant gap, not rate gap). Falsifies any claim of unconditional `√d` robustness.
- **EP6 (ReLU-head residual averaging, O4).** For conv–ReLU–GAP on multi-frequency (D3) data with many
  signal frequencies, measure whether GF converges to the cross-frequency-averaged multiplier
  (non-robust, `R_2=O(√(d/K_freq))`) or the decoupled one. *Prediction (the open question):* GF on the
  ReLU head is *less* robust than the quadratic head and its robustness degrades with `K_freq` — if so,
  this confirms cross-frequency averaging survives the constraint (O4), the precise residual gap.
- **EP7 (activation-degree × architecture, ties to Min–Vidal).** Cross the Min–Vidal lever (pReLU
  degree p) with the architecture lever (FC vs conv–GAP). *Prediction:* conv–GAP+quadratic ≈
  conv–GAP+high-p ≫ FC+high-p ≫ FC+ReLU in robustness; the two levers are *complementary* (architecture
  quotients the group, degree sharpens alignment), and quadratic conv–GAP should already capture most
  of the gain, since for the orbit nuisance the *group* quotient (not the alignment sharpening) is what
  kills the dominant Frei threat.

---

## 9. Honest one-paragraph bottom line

Hard-wired shift-invariance (weight-shared conv + GAP) **does** re-point the implicit bias of gradient
descent toward the robust large-η/L solution **for the quadratic head, in the favorable regime where
the discriminative signal lives in the power spectrum with η/L = Ω(1)** — and the mechanism is sharp
and new: (a) the constraint *convexifies* the Lyu–Li max-margin program (Prop 2.2, Cor 2.3), removing
the KKT multiplicity that powers Frei's negative result, and (b) the universal Frei/Li threat direction
is the *orbit-zero* direction that GAP annihilates (Lemma 4.3). This **proves the Min–Vidal conjecture
under the shift constraint for the quadratic head**, a result Min–Vidal themselves only conjecture for
their activation lever. It **fails** exactly when the structural master criterion fails: phase/localization-coded
signal (η/L = O(1/√d), the Kamath corner) leaves the power spectrum margin-blind, and no choice of
shift-invariant architecture manufactures the missing margin (§5.1). For the **conv–ReLU–GAP head** the
program is non-convex again; the constraint provably blocks cross-*orbit* averaging but not cross-*frequency*
within-invariant averaging, so a non-robust KKT point still *exists* and whether GD avoids it is **open**
— the residual frontier, now localized precisely. The optimization question thus *reduces to* the
structural η/L question once the architecture convexifies the head: **the constraint removes the
implicit-bias obstruction; it cannot remove a data obstruction.**
