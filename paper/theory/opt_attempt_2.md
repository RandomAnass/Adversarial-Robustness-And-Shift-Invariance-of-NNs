# Does Architectural Shift-Invariance Re-point Gradient Descent's Implicit Bias Toward Robust Solutions?

> ## ⚠ POST-RED-TEAM CORRECTION (read first; supersedes the original bottom line below)
>
> An adversarial review (verified by me firsthand, `/tmp/verify_redteam.py`) found a
> **fatal load-bearing flaw** in the original "implicit-bias re-pointing" headline of
> this attempt. The flaw is the *same 4/4 blind spot* the structural theory had:
> **the Frei/Li non-robustness reduction does not hold on shift-orbit data, and the
> very fact that powers the positive "GAP kills the threat" mechanism is what voids
> the negative "the baseline is non-robust" premise.** Concretely, verified:
> 1. **A single cosine-frequency orbit is rank-2** (a circle in `R^d`), not `d`
>    near-orthogonal clusters. Frei (Asm 2.2) / Li (Asm 3.2: *exactly* orthogonal,
>    `d = Ω(k^10)`) require the opposite. Orbit Gram off-diagonal `= d` (e.g. 16 at
>    `d=32`), Frei's bound demands `≤ 0.1·‖μ‖²`: **violated by ≥10×, growing with `d`.**
>    So Frei Thm 4.2 / Li Thm 4.5 **do not apply** to the D-freq data used for the
>    positive result.
> 2. **Frei's universal attack `z = (1/d)Σ y_q μ_q` is identically zero** on the
>    cosine orbit (`‖z‖ = 2e-16`: shifts of a cosine sum to zero). The original
>    attempt *celebrated* this vanishing as the positive mechanism — but the same
>    `z→0` means Frei Thm 4.2's *non-robustness conclusion (carried by `z`) has no
>    content here*. You cannot use `z→0` as the win and invoke the theorem whose
>    loss is `z`. The "FC non-robust vs conv-GAP robust along the same `z`" contrast
>    is **self-cancelling**.
> 3. **No single base pattern makes both halves true.** Cosine-orbit: `Δ_PS>0`
>    (conv-GAP can separate) but rank-2 (Frei N/A). Single-dot orbit: orthonormal,
>    Frei genuinely applies, but `Δ_PS = 0` (conv-GAP-quadratic is phase-blind, gets
>    chance accuracy — the attempt's own Prop 4 / Theorem II).
> 4. The empirical "1.57× / 1.3–1.6× / non-overlapping-restarts" headline is, per
>    the red-team's fair-baseline re-run, substantially a **weak-FC-baseline +
>    linearized-radius-on-training-points artifact** (FC under-trained, conv-GAP head
>    is the matched power-spectrum model for cosine data; with a matched FC budget
>    the K-sweep ratios collapse to ≈0.86–1.16). I could not re-confirm a fair
>    baseline this session (torch env broke), so I now treat the empirical advantage
>    as **unconfirmed**, not as evidence.
>
> **Corrected verdict: the OPTIMIZATION / implicit-bias problem is NOT closed by this
> attempt.** Every trajectory-level statement either hits the same wall as
> Frei/Min&Vidal/Li (trainable ReLU head: OPEN) or is structural Theorem A restated
> in min-norm language. **What genuinely survives is structural, not optimization**
> (see the revised Section 9 "What survives"). The sections below are kept *as
> written originally* for the record, with this correction governing; treat their
> "PROVED / verified" labels on any *contrast* or *implicit-bias* claim as
> **retracted** unless re-affirmed in §9.

**Optimization-side attempt 2.** Target: the open gap §5(a) of `CONSOLIDATED_THEORY.md`.
The structural theory (Theorems A/B/C) settles *which* invariant classifiers
**exist**; it is silent on *which one gradient descent selects*. Frei et al.
(NeurIPS'23) show GF on an unconstrained 2-layer ReLU net selects a **non-robust**
KKT point of the max-margin program even though robust ones exist; Min & Vidal
(2024) **conjecture** that the right architecture re-points this bias toward
robustness but cannot prove it; Li et al. (2024) prove the non-robust selection is
**feature averaging** and that *fine-grained supervision* fixes it.

**This document asks and partially answers:** does the hard-wired architectural
constraint of weight-shared circular convolution + global average pooling (conv-GAP)
play the role Min & Vidal's conjecture and Li's fine-grained supervision play —
forcing the *implicit bias itself* onto the robust large-η/L solution — when the
class signal is a **shift orbit**?

**Bottom line (honest).** I prove a clean **structural re-parameterization lemma**
(conv-GAP = a 2-layer ReLU net whose neurons are forced into *tied shift-orbit
bundles*), and from it a **partial implicit-bias theorem**: under the conv-GAP
parameterization the max-margin/min-norm program (the Lyu–Li/Ji–Telgarsky implicit-bias
limit) **cannot feature-average across the orbit**, because the orbit is collapsed
into a *single* parameter atom whose cost is amortized over all `d` shifts.
On orbit-structured data with positive *invariant* margin (large η/L, e.g. Ge's
orthogonal-frequency data) this provably blocks the Frei/Li 1/√k collapse **at the
global min-norm solution**, and I verify numerically that the *whole distribution*
of GD-found KKT points is shifted toward robustness (not seed-luck). The argument
**does not** upgrade to Frei's strength ("*every* KKT point is robust"): I identify
exactly the obstruction (Section 7) — a residual feature-averaging channel *within
the head v* survives, and a separate failure mode when the invariant margin is zero
(phase-coded signal, Δ_PS = 0), where conv-GAP gives no advantage, confirmed
numerically. So the answer is: **yes, conditionally on η/L large, and only for the
orbit-tangent averaging direction; no for phase-coded signal and not at the
"every-KKT-point" strength of Frei.**

All experiments below were run (CPU, torch 2.12); raw scripts in `/tmp/*.py`,
numbers reproduced in Section 8.

---

## 1. Setting and assumptions

### 1.1 Data: orbit-structured Gaussian mixture (Frei/Li, made cyclic)

We use the orthogonal-cluster mixture of Frei et al. (2023, Assumption 2.2) and Li
et al. (2024, Def 3.1/Assumption 3.2), specialized so the cluster set is a **shift
orbit**, which is the object the structural theory is about.

* Cyclic group `G = Z_d`, shift `(T_s x)_i = x_{(i-s) mod d}`, each `T_s ∈ O(d)`
  (Fact 1.1 of consolidated theory).
* Two **base patterns** `p_+, p_- ∈ R^d`. Class `+1` is the orbit
  `M_+ = {T_s p_+ : s ∈ G}`; class `−1` is `M_- = {T_s p_- : s ∈ G}`. Optionally
  add Gaussian noise `N(0, σ² I)`, `σ ≤ 1`, as in Frei. Each class is therefore
  `k = d` clusters (one per shift); the **cluster set is closed under the group and
  labels are shift-pure** (Assumption A2 of the consolidated theory holds by
  construction).
* **Equinorm/orthogonality (Frei A2.2 / Li A3.2).** Pick `p_±` so that all `2d`
  cluster centers `{T_s p_±}` are equinorm and pairwise near-orthogonal. This is
  the exact regime where Frei/Li prove non-robustness for the **unconstrained**
  net. Two canonical instances we use:
  - **(D-freq) orthogonal-frequency** (Ge §5.2 style, *high* invariant margin):
    `p_+ = cos(2π·a·/d)`, `p_- = cos(2π·b·/d)`, `a ≠ b`. The orbit of a pure
    frequency = its phase shifts; distinct frequencies are exactly orthogonal across
    the orbit. The discriminating feature ("which frequency is on") is a
    **power-spectrum** feature: shift-invariant with `Θ(1)` margin (large η/L).
  - **(D-dot) single-dot / phase-coded** (Ge single-dot, *zero* invariant margin):
    `p_+ = e_0`, `p_- = −e_0` (antipodal). Orbits = signed standard basis (exactly
    Frei's `k = d` orthonormal clusters). Power spectra are identical (flat); the
    classes differ only in **sign/phase**, so `Δ_PS = 0` (small/zero η/L).

The two instances bracket the η/L axis and let me test *when the mechanism succeeds
vs fails*.

### 1.2 The two learners (identical data, identical loss, identical width budget)

Logistic/exponential loss, gradient flow (GF) / Adam-GD to interpolation.

* **Unconstrained 2-layer ReLU** (`Nθ`, Frei/Li/Min-Vidal):
  `Nθ(x) = Σ_{j=1}^m v_j φ(w_j^T x + b_j)`, `φ = ReLU`, all parameters free,
  2-homogeneous.

* **Conv-GAP net** (fully shift-invariant): `C` circular filters `K_ch ∈ R^d`,
  biases `b_ch`, head `v_ch`,
  ```
  f(x) = Σ_{ch=1}^C v_ch · (1/d) Σ_{p=0}^{d-1} φ( (K_ch ⋆ x)_p + b_ch ),
  ```
  where `(K ⋆ x)_p = Σ_k K_k x_{(p-k) mod d}` is circular convolution and the
  `(1/d) Σ_p` is GAP. `f(T_s x) = f(x)` exactly (GAP over the full orbit of
  positions). Also 2-homogeneous in `θ = {K_ch, b_ch, v_ch}`.

Both classes are 2-homogeneous, so Lyu–Li (2020) / Ji–Telgarsky (2020) apply: if GF
drives the loss below the interpolation threshold, the **normalized parameters
converge in direction to a KKT point of the margin-maximization problem**
```
  (P_arch)   min  ½‖θ‖²   s.t.   y_i f(θ; x_i) ≥ 1  ∀i,                         (1)
```
where `f` ranges over the architecture's realizable functions and `‖θ‖²` is the
sum of squared parameters **in that architecture's parameterization**. The two
architectures induce *different* programs (1) because the constraint set and the
norm differ. This is the lever.

### 1.3 Robustness measure

`L_2` robust radius `ρ_f(x) = inf{‖δ‖_2 : sign f(x+δ) ≠ sign f(x)}` (consolidated
theory §1.2). We also use the scale-free **linearized radius**
`ρ_f^lin(x) = |f(x)| / ‖∇f(x)‖` (exact first-order radius; scale-invariant for
homogeneous `f`, hence the right quantity to compare across architectures whose
output scale differs). Frei's `√d`-robust target vs `≪√d` non-robust collapse is a
statement about how `ρ` scales with `d` (= `k`).

---

## 2. Precise claims

> **Claim 1 (Structural re-parameterization — PROVED, verified exactly).**
> A conv-GAP net with `C` filters is *identically equal* (as a function) to a
> 2-layer ReLU net with `C·d` hidden neurons that come in **tied shift-orbit
> bundles**: for each filter `ch`, all `d` shifts `{T_p K_ch}_{p}` are present as
> hidden neurons, **sharing one bias `b_ch` and one output weight `v_ch/d`**.
> Conversely the unconstrained net may choose all `m` neurons' `(w_j, b_j, v_j)`
> independently. (Lemma 1, §4.1.)

> **Claim 2 (Orbit-detection is amortized — PROVED).**
> To realize a "one-detector-per-cluster" robust classifier on an orbit of `d`
> clusters, the unconstrained net must pay `Θ(d)` independent neurons (parameter
> norm `Θ(d)`), whereas conv-GAP pays **one filter** (parameter norm `Θ(1)` in the
> filter, the head re-scaling is absorbed). Hence under the *same* margin
> constraint the conv-GAP program (1) can reach the robust per-cluster function at
> `O(1)` parameter cost while the unconstrained program reaches it only at `Θ(d)`
> cost, so the unconstrained min-norm optimum **prefers the cheaper averaged
> function** whereas the conv-GAP min-norm optimum does **not pay to average**.
> (Lemma 2 + Prop 3, §4.2–4.3; verified on D-freq: at margin 1, min‖θ‖² is *equal*
> for the two — `11.86` vs `12.18` — yet the conv-GAP min-norm solution uses just
> **2 active `O(1)`-norm filters** (one per class) and has linearized radius
> `0.999` vs FC's `0.636`, §8.)

> **Claim 3 (Conditional implicit-bias re-pointing — PARTIAL).**
> On orbit-structured data with **positive invariant margin** `Δ_PS = Ω(1)`
> (large η/L; D-freq), the *global* solution of the conv-GAP program (1) is the
> robust invariant classifier with radius `Ω(1)` (no `1/√k` collapse), while the
> unconstrained program's KKT points are non-robust with radius `O(√(d/k)) = O(1)`
> here but governed by the averaging direction and strictly smaller at matched
> margin/norm (Frei Thm 4.2 mechanism). Empirically the *entire distribution* of
> GD-found conv-GAP KKT points (8 random seeds) is robust, not just the global
> optimum. (Prop 3 + §8.)
>
> **It does NOT upgrade to "every KKT point is robust"** (Frei's strength): a
> residual averaging channel survives inside the head `v` (Obstruction O1, §7).

> **Claim 4 (Failure when invariant margin is zero — PROVED + verified).**
> On phase-coded data with `Δ_PS = 0` (D-dot antipodal; small η/L), the
> conv-GAP advantage **vanishes**: conv-GAP and FC have equal robustness
> (ratio `1.01`, §8). The re-pointing only helps where the consolidated theory
> says co-existence is *possible* (η/L large); it cannot manufacture an invariant
> margin that the data does not have. (Prop 4, §5.)

These four claims map cleanly onto the η/L master criterion: **architectural
shift-invariance re-points GD's implicit bias toward the robust solution exactly in
the large-η/L regime, and is powerless in the small-η/L regime** — the optimization
story inherits the same governing scalar as the function-class story.

---

## 3. Background facts used (cited precisely, no fabrication)

**(F1) Lyu–Li / Ji–Telgarsky implicit bias.** For 2-homogeneous nets with
exponential/logistic loss, if GF reaches loss `< 1/n` then normalized parameters
converge in direction to a KKT point of (1) [Frei §2, Thm 2.1, citing Lyu&Li 2020,
Ji&Telgarsky 2020]. **Used for both architectures** (both are 2-homogeneous).

**(F2) Frei Thm 4.1 (robust net exists).** On `Dclusters` (`k` orthogonal means,
norm `√d`, σ≤1), there is a width-`k` ReLU net, one neuron per cluster
`w_j = 4μ^(j)/d`, `b_j = −2`, that is `√d`-robust: exactly one neuron is active on
each input, so `‖∇N(x)‖ = O(1/√d)`, forcing flips to need `Ω(√d)`
[Frei §4.1.1, p.9]. **This is the localized-detector / robust target.**

**(F3) Frei Thm 4.2 (GD-found net is non-robust).** Every KKT point of (1) for the
unconstrained net behaves, near a test point, like the linear model
`w = (1/d) Σ_q y^(q) μ^(q)` (the **average of the cluster means**): `‖w‖ = Ω(√(k/d))`,
so a universal perturbation of size `O(√(d/k)) ≪ √d` flips the sign [Frei §4.1.2,
p.9–10; Thm 4.2]. **This is the feature-averaging direction.** It is non-robust
once `k = ω(1)`.

**(F4) Li Thm 4.5 (averaging on the GD trajectory).** Standard GD on the
unconstrained ReLU net **provably** converges to the feature-averaging solution:
each neuron's weight → a weighted average of the cluster features with ratios → 1;
the solution is non-robust by a factor `Θ(√k)` vs the optimal `Θ(√d)` radius [Li
Thm 4.5, resolving Min&Vidal]. Li Thm 4.7: *per-cluster (fine-grained) supervision*
recovers the localized detectors and optimal `Θ(√d)` radius.

**(F5) Min–Vidal alignment + conjecture.** ReLU's early-alignment phase collapses
neurons to the **average class centers** `μ̄_±` (= normalized sum of subclass
centers) → the non-robust `F` with critical radius `O(1/√K)`; a polynomial-ReLU
`p ≥ 2` activation re-points alignment to **individual subclass centers** → robust
`F^(p)` with `O(1)` radius. They **prove** the function-class robustness (Thm 1)
and the ReLU alignment bias (Thm 2) but only **conjecture** (Conjecture 1) that GF
on the new architecture *finds* `F^(p)` [Min&Vidal §3–4]. **Their conjecture is the
architecture-re-points-the-bias claim — exactly our target, with the lever being
the *activation*; ours is the *spatial weight-sharing+GAP*.**

**(F6) Power-spectrum span (consolidated theory, Lemma).** conv + pointwise + GAP
computes shift-invariant features; the conv-square-GAP family spans the power
spectrum `{|x̂_k|²}`; phase is unreachable at second order. So the *invariant
margin* a one-hidden-layer conv-GAP net can use is (at the quadratic level) the
power-spectrum separation `Δ_PS`. This is the η in η/L for this architecture.

---

## 4. Full proofs and the key mechanism

### 4.1 Lemma 1 (the re-parameterization) — PROVED

**Statement.** Fix `d`. For any filters `{K_ch}`, biases `{b_ch}`, head `{v_ch}`,
the conv-GAP function equals a 2-layer ReLU net with neurons indexed by
`(p, ch) ∈ G × [C]`:
```
  f(x) = Σ_{ch} Σ_{p∈G} (v_ch/d) · φ( ⟨ w_{p,ch}, x⟩ + b_ch ),
  with  (w_{p,ch})_i = (K_ch)_{(p-i) mod d}   (= the p-shift of the reversed filter).
```
The map `K_ch ↦ {w_{p,ch}}_p` sends one filter to its **entire orbit of `d`
neurons**, all sharing `(b_ch, v_ch/d)`.

**Proof.** `(K_ch ⋆ x)_p = Σ_k (K_ch)_k x_{(p-k) mod d} = Σ_i (K_ch)_{(p-i) mod d} x_i
= ⟨w_{p,ch}, x⟩` with `(w_{p,ch})_i = (K_ch)_{(p-i) mod d}`. Substituting into `f`
and pulling the GAP factor `1/d` into the output weight gives the displayed sum. ∎

**Verified exactly** (`/tmp/equiv.py`, `d=8, C=3`, 5 random inputs, agreement to
`< 1e-9`).

**Two corollaries of the structure that drive everything:**

* **(L1a) Weight-tying.** The `d` neurons `{w_{p,ch}}_p` are *not* free: they are
  the cyclic shifts of one vector `K_ch`, and they share one bias and one output
  weight. The unconstrained net has no such tie.
* **(L1b) Orbit-equivariant activation pattern.** Because `w_{p+1,ch} = T_1 w_{p,ch}`,
  the activation mask `1[⟨w_{p,ch}, x⟩ + b_ch > 0]` is shift-equivariant in `x`:
  shifting `x` permutes which of the `d` tied neurons fire, but never changes *how
  many* or their shared weight. (This is the discrete analogue of Theorem C's
  continuous orbit-equivariance.)

### 4.2 Lemma 2 (linear conv-GAP collapses to DC) — PROVED, verified

A *linear* conv-GAP net (`φ = id`) computes
`f(x) = Σ_ch v_ch (1/d) Σ_p (K_ch ⋆ x)_p = (Σ_ch v_ch (Σ_k (K_ch)_k)) · (1/d)Σ_i x_i
= c · mean(x)`,
i.e. **exactly the DC functional** (Theorem A of the consolidated theory). So the
nonlinearity is *necessary* for the re-pointing; a purely linear invariant net
inherits the `1/√d` DC bottleneck. (Verified `/tmp/analytic_core.py`: linear
conv+GAP value `= (Σ_k K_k)·mean(x)` to machine precision.) This is why the
mechanism lives entirely in how ReLU + tying shapes the *nonlinear* invariant
features (F6).

### 4.3 Proposition 3 (amortization blocks orbit feature-averaging) — the KEY MECHANISM

This is the heart. I argue at the level of the min-norm program (1), the
implicit-bias limit (F1).

**Setup.** Consider the robust "one-detector-per-cluster" target function on the
orbit data: for class `+`, a detector that fires (with margin 1) on each of the `d`
shifts `T_s p_+` and is off on `M_-`, and symmetrically for `−`. By (F2) this is
the `√d`-robust Frei construction; on the orbit data it is `T_s`-equivariant.

**Cost in the unconstrained parameterization.** The `d` cluster centers `T_s p_+`
are (near-)orthogonal, so a single ReLU neuron cannot be simultaneously active with
margin 1 on all `d` of them without being active on `M_-` too (orthogonality ⇒ a
direction correlated with all `d` shifts is the *average* `(1/d)Σ_s T_s p_+`, whose
correlation with each individual `T_s p_+` is only `‖p_+‖²/d = O(1/d)`, i.e. the
margin per cluster collapses by `1/d`). Therefore realizing the *robust per-cluster*
function needs `Θ(d)` separate neurons, parameter norm `Θ(d)`. The *averaged* single
neuron is `Θ(1)` cost but non-robust (this is precisely Frei F3 / Li F4: the cheap
min-norm interpolant is the average direction). **So in the unconstrained program,
min-norm strictly prefers the non-robust averaged solution: cost `Θ(1)` (average)
≪ `Θ(d)` (robust per-cluster).** This re-derives the Frei/Li collapse as a
norm-minimization preference.

**Cost in the conv-GAP parameterization.** By Lemma 1, choosing **one filter**
`K = p_+` (the matched detector) *automatically instantiates all `d` shifted
detectors* `{T_p p_+}`, with shared `(b, v/d)`. So the robust per-cluster function
costs **one filter**: parameter norm `‖K‖² + b² + v²`. There are two regimes for
how the head weight `v` must scale, and the *verified* one is the clean case:

*Regime (i) — extended/frequency matched filter (the verified case).* If the base
pattern is extended (e.g. a cosine, D-freq), the matched filter `K = p_+` is itself
extended, the conv response `(K ⋆ x)_p` is `Θ(1)` at *every* position when `x` is on
the orbit, GAP gives `Θ(1)` output, and margin 1 needs `v = O(1)`. **Verified
directly** (`param_inspect.py`): the min-norm conv-GAP solution uses exactly **2
active filters**, `‖K‖ ≈ 1.1`, `|v| ≈ 1.0`, all `O(1)`; the other 38 available
filters vanish. So the robust per-cluster function costs `O(1)` parameter norm —
not `Θ(d)` — and the gradient `∇f(x) = (v/d) Σ_p 1[active] T_p(rev K)` has norm
`O(1)`, giving a `d`-independent linearized radius. **No collapse.** (This is why
min`‖θ‖²` came out *equal* to FC, `11.86` vs `12.18`, while the radius was `1.57×`
larger: same budget, robust direction.)

*Regime (ii) — localized matched filter (the subtle case, not the verified one).*
If the base pattern is *localized* (a dot/bump, D-dot), the matched filter is
localized, the conv response is `Θ(1)` at only `Θ(1)` positions and ~0 elsewhere,
so GAP output `= Θ(1/d)` and margin 1 *does* require `v = Θ(d)`, naively
`Θ(d²)` filter contribution. **But the gradient is divided by the same GAP `1/d`:**
`‖∇f(x)‖ = (v/d)·Θ(1)·‖K‖ = (Θ(d)/d)·Θ(1) = Θ(1)`, so the linearized radius
`|f|/‖∇f‖ = Θ(1)` is still `d`-independent. The `v = Θ(d)` cost *is* a real
norm penalty in regime (ii); whether the min-norm program still prefers this over
averaging in the localized case is **not** verified here (it interacts with O1).
The clean, verified amortization is regime (i).

Contrast the unconstrained averaged solution: there `f(x) = ⟨w_avg, x⟩`-like with
`w_avg = (1/d)Σ_s T_s p_+`, `‖w_avg‖ = Θ(1/√d)·‖p_+‖`... but normalized to margin 1
the *gradient* is `Θ(√k/√d) = Θ(1)` here yet the **signal-to-gradient ratio** is
worse because the averaged direction spends its norm budget on a direction
correlated `O(1/√d)` with each cluster (Frei F3: radius `O(√(d/k))`, here `k=d` so
`O(1)`, but strictly smaller at matched margin — confirmed: `0.636` vs `0.999`).

**The mechanism in one sentence.** *Weight-sharing makes "detect this pattern at
every shift" a single cheap parameter atom, so the min-norm bias no longer has to
average distinct shifts into one fragile direction to save parameters; GAP then
reads off only the active shift, keeping the per-input gradient `Θ(1)` while the
unconstrained averaged solution pays its margin in a direction weakly aligned with
each cluster.* This is the spatial-weight-sharing analogue of Min–Vidal's
activation lever (F5) and of Li's fine-grained supervision (F4): all three change
*what is cheap*, so that the robust per-cluster (per-subclass / per-shift) solution
becomes the min-norm preferred one.

**Verified (the decisive numbers, §8):** at margin ≥ 1 on D-freq, min`‖θ‖²` is
*equal* for the two architectures (`11.86` conv-GAP vs `12.18` FC — amortization
exactly cancels the `v=Θ(d)` cost), yet the conv-GAP min-norm solution has
linearized radius `0.999` vs FC's `0.636`. And across 8 random GD restarts the
*whole* conv-GAP radius distribution is shifted up (Section 8), so this is the
implicit-bias limit, not a hand-built optimum.

### 4.4 Why this is exactly Theorem C at the discrete level

Lemma 1's L1b says the conv-GAP gradient is
`∇f(x) = (v/d) Σ_p 1[active at p] T_p(rev K)`, a sum over the *orbit of the
filter*, masked by the (shift-equivariant) activation. On an orbit input, the
active positions are the ones where the filter aligns with the localized pattern, a
`T_s`-equivariant set. The *orbit-tangent* component of `∇f` — the direction that
mimics a small shift of `x` — is suppressed because shifting `x` only permutes the
active set without changing the summed direction's projection onto `span{T_{±1}x−x}`
to first order (the discrete analogue of `⟨∇f, Ax⟩ = 0`, Theorem C.i). So the
gradient's energy is concentrated *off* the orbit-tangent, exactly where Theorem C
(continuous, first-order) predicted, and the discrete tying makes it hold for the
finite orbit too — a partial closure of Limitation 1 (the discrete-chord gap) of
the consolidated theory, *specifically for the conv-GAP function class* (not for
arbitrary invariant `f`). I verified gradient localization directly: a matched
ReLU filter on input `p_0` has gradient with only ~3 nonzero coordinates,
concentrated at the active position, and shift-equivariant across orbit inputs
(`/tmp/analytic_core.py`).

---

## 5. When it succeeds vs fails (vs η/L)

The four claims partition the (data, architecture) space by the invariant margin η
(= `Δ_PS` for conv-square-GAP, `Δ_dc` for linear) over Lipschitz `L`:

| regime | η/L | data example | conv-GAP vs FC | mechanism |
|---|---|---|---|---|
| **large η/L** | `Ω(1)` | D-freq (orthogonal frequencies) | conv-GAP **more robust** (ratio 1.3–1.6×, slope-flat in `d`) | amortization blocks orbit averaging (Prop 3) |
| **zero η/L (phase)** | `0` (Δ_PS=0) | D-dot antipodal (single dot) | **no advantage** (ratio ≈1.0) | power-spectrum blind to sign/phase (F6); no invariant margin to exploit (Prop 4) |
| **zero η/L (DC only)** | `0` (Δ_dc=0) | signal in AC subspace, no PS gap | linear conv-GAP collapses to DC (Lemma 2); ReLU conv-GAP limited | Theorem A bottleneck, optimization inherits it |
| **intermediate** | small `>0` | gap-coded dots (Δ_PS>0 small) | partial advantage, grows with Δ_PS | Prop 3 with small margin |

**Proposition 4 (failure at η = 0) — PROVED + verified.** If `Δ_PS = 0` (the two
orbits have identical power spectra, e.g. antipodal single dot), then at the
quadratic level conv-square-GAP cannot separate the classes invariantly (F6), so
the conv-GAP net must use the **bias/ReLU asymmetry** (a first-order DC-like term)
or fail; either way it has *no* invariant margin advantage over FC and the
re-pointing of Prop 3 is vacuous (there is no robust invariant target to be
re-pointed toward). **Verified:** D-dot antipodal gives conv-GAP/FC radius ratio
`1.01` (no advantage), vs `1.32` on the power-spectrum-separated `phase_gap` data
(§8). *Nuance (honest):* a single **ReLU** layer is slightly richer than pure
power spectrum — on a "true_phase" pair with `Δ_PS = 0` but distinct *rectified*
statistics, conv-GAP still reached 100% accuracy where FC stalled at 88% (§8). So
"power-spectrum blind ⇒ fails" is the *quadratic-idealization* statement; the real
ReLU conv-GAP has a thin extra channel. The *robustness* advantage, however, still
requires a genuine invariant margin, which antipodal data lacks.

**The governing scalar is η/L, identically to the structural theory.** The
optimization question does not introduce a new axis: architectural shift-invariance
re-points the implicit bias **iff** the data carries a shift-invariant feature with
large margin that the architecture can compute — the same condition under which the
function class *contains* a robust invariant classifier.

---

## 6. Relation to Frei / Min–Vidal / Li — is Min–Vidal's conjecture provable here?

* **Frei (Thm 4.1 vs 4.2).** We reproduce the dichotomy structurally: Frei's robust
  net (F2) = our matched filter (one filter spawns the `k=d` localized detectors);
  Frei's non-robust KKT point (F3) = the averaged direction the *unconstrained*
  min-norm program prefers (Prop 3). **The new content:** the conv-GAP
  parameterization makes Frei's robust construction the *cheap* one, inverting the
  min-norm preference. We do **not** match Frei's "*every* KKT point is non-robust"
  in the positive direction (Obstruction O1).

* **Min–Vidal (Conjecture 1).** Their conjecture is precisely "architecture
  re-points the implicit bias toward the robust solution." **Under the shift
  constraint we give a partial proof of an analogous statement** with the
  *spatial weight-sharing+GAP* as the lever instead of their pReLU activation: the
  re-pointing holds at the *global* min-norm solution (Prop 3) and empirically over
  the GD-found-KKT distribution (§8), conditioned on η/L large. Their lever
  (activation) and ours (weight-sharing) are *complementary*: both change which
  function is cheap. **Min–Vidal's conjecture is therefore provable in the
  restricted sense "the architecturally-cheapest interpolant is robust" — but the
  full conjecture "GF converges to it from random init" remains open for the same
  reason theirs does (the early-alignment-phase dynamics are not closed).** We
  reduce it, under the shift constraint, to a *single* open dynamical question
  (O2).

* **Li (Thm 4.5 / 4.7).** Li proved the averaging *on the trajectory* (closing
  Min–Vidal's averaging conjecture for FC) and that **fine-grained supervision**
  recovers robustness. **Our claim is that conv-GAP supplies the same robustifying
  information as fine-grained supervision, but through the architecture rather than
  the labels:** weight-sharing tells the net "the same detector applies at every
  shift," which is exactly the per-shift structure that per-cluster labels would
  reveal. This is a concrete, testable bridge between Li's *label-side* fix and an
  *architecture-side* fix. We do **not** have Li's trajectory-level proof for
  conv-GAP (O2).

---

## 7. Obstructions (explicit, honest)

**O1 — No "every KKT point is robust" (the residual averaging channel).** Prop 3
controls the *global* min-norm solution and the empirical KKT distribution, but
*not every* KKT point of the conv-GAP program (1). The hole: Lemma 1 ties the
*hidden* layer into orbit bundles, but the **head `v_ch`** is still free, and a
conv-GAP net with *many* filters can still form an averaged decision by combining
filters with mismatched `v_ch` — re-introducing a weak feature-averaging channel
through the head. Frei's power was a *universal* statement over KKT points; I cannot
match it because the conv-GAP KKT set is not as tightly characterized (the tying is
in `K`, the averaging freedom migrates to `v`). Closing this needs a KKT analysis
of (1) under the conv-GAP constraint analogous to Frei §4.1.2 — not done here.

**O2 — Trajectory, not just the optimum (the Min–Vidal/Li gap, inherited).** F1
guarantees GF converges to *a* KKT point; Prop 3 + §8 show the reachable ones are
robust *empirically*, but I have **no trajectory-level proof** (à la Li Thm 4.5)
that GF on conv-GAP from small init lands on the robust filter rather than a head-
averaged KKT point. This is exactly the open dynamical step in Min–Vidal's
Conjecture 1 and in Li's program; the shift constraint reduces it but does not
remove it. The early-alignment-phase analysis (Min–Vidal Thm 2) would have to be
redone for the tied-orbit parameterization.

**O3 — Quadratic idealization of the invariant features.** Prop 3/4 treat the
conv-GAP invariant margin as the power-spectrum separation `Δ_PS` (F6). A real
one-hidden-layer ReLU conv-GAP net has a thin extra (rectified, bias-driven)
channel beyond pure power spectrum, shown by the `true_phase` experiment (§8). So
the "fails iff `Δ_PS = 0`" boundary is the idealized-feature statement; the exact
boundary for ReLU conv-GAP is slightly softer and I did not characterize it.

**O4 — Orthogonality / equinorm and noise.** The amortization argument (Prop 3)
uses near-orthogonality of the `d` shifted clusters (Frei/Li A2.2/A3.2). For a
*localized* base pattern at large `d` the shifts are orthogonal; for a *non-localized*
base pattern (broadband) they are not, and the "single matched filter detects the
whole orbit" step weakens. I did not quantify the degradation with the orbit's
auto-correlation spread. Noise `σ > 0` is handled by Frei/Li at the level of their
theorems but I only ran the `σ = 0` (clean orbit) experiments.

**O5 — Factor constants, not asymptotics.** My experiments are at `d ≤ 256` (the
per-input autograd radius loop is `O(nd)` and CPU-bound); the *slope* of
`log radius` vs `log d` is the asymptotic claim (FC `< 0`, conv-GAP `≈ 0`), reported
in §8, but the constants and the largest `d` are modest. A clean `√d`-vs-`O(1)`
separation at `d = 10^3`–`10^4` was not run.

**O6 — One hidden layer.** Everything is depth-2. Deep conv-GAP nets (the practical
object) compose many tied layers; whether the amortization argument telescopes
through depth (or whether deep heads re-open the averaging channel O1 worse) is
open and is the natural next target.

---

## 8. Empirical predictions and the measurements actually run

All scripts in `/tmp/` (`equiv.py`, `analytic_core.py`, `failure_regime.py`,
`kkt_norm.py`, `decisive.py`, `kkt_restarts.py`), torch 2.12 CPU.

**Measured (this attempt):**

1. **Structural lemma exact** (`equiv.py`): conv-GAP(`C`) ≡ tied-orbit 2-layer ReLU
   (`C·d` neurons), agreement `< 1e-9`. ✅ (Lemma 1.)

2. **Linear conv-GAP = DC** (`analytic_core.py`): `f(x) = (Σ_k K_k)·mean(x)`,
   machine precision; ReLU conv-GAP gradient is localized (~3 nonzero comps) and
   shift-equivariant. ✅ (Lemma 2, §4.4.)

3. **Min-norm at matched margin** (`kkt_norm.py`, D-freq, `d=12`): min`‖θ‖²` =
   **11.86 (conv-GAP) vs 12.18 (FC)** — essentially equal (amortization cancels the
   `v=Θ(d)` cost); min-norm-solution linearized radius =
   **0.999 (conv-GAP) vs 0.636 (FC)**, a **1.57×** robustness gain at matched
   margin *and* matched parameter norm. ✅ (Prop 3 — the decisive number.)

4. **Failure regime** (`failure_regime.py`, `d=24`):
   - `phase_gap` (Δ_PS = 9.8): conv-GAP/FC radius ratio **1.32** (advantage).
   - `antipodal_dot` (Δ_PS = 0): ratio **1.01** (no advantage). ✅ (Prop 4.)
   - `true_phase` (Δ_PS = 0 but rectified-stats differ): conv-GAP acc **1.00** vs
     FC **0.88** — the thin extra ReLU channel (O3 nuance).

5. **Radius vs `d` scaling** (`scaling_jac.py`, D-freq, vmap-jacobian radius):
   `d=16: FC 2.43, CG 2.83, ratio 1.17`; `d=32: 2.91, 3.99, 1.37`;
   `d=64: 3.42, 5.57, 1.63`. The **conv-GAP/FC robustness ratio grows monotonically
   with `d`** (1.17 → 1.37 → 1.63). Both radii grow (here `k = d`, so neither is the
   fixed-`k` Frei collapse — see the honest caveat below), but conv-GAP grows
   strictly faster: the *advantage compounds with dimension*. ✅ (Claim 3.)

   **Filter structure of the min-norm conv-GAP solution** (`param_inspect.py`,
   D-freq, `d=24`, 40 filters available): the solution uses **exactly 2 active
   filters** (one per class), with `‖K‖ ≈ 1.1`, `|v| ≈ 1.0` — *all `O(1)`*, the
   other 38 filters decay to zero. This *directly confirms the amortization
   mechanism*: one `O(1)` filter per class detects the whole `d`-shift orbit via
   GAP, at `O(1)` parameter cost. (It also *corrects* a naive sub-argument: for an
   *extended* matched filter like a cosine, no `v = Θ(d)` head inflation is needed —
   the `v = Θ(d)` accounting is only the *localized-pattern* sub-case; see the
   corrected Prop 3.) ✅

   **Honest caveat on the Frei-collapse asymptotic.** The cleanest Frei/Li collapse
   (`FC radius ∼ d^{-1/2}`) is the *fixed-`k`, growing-`d`* regime. **This regime is
   structurally awkward to realize *with shift symmetry*:** a shift orbit has exactly
   `d` elements, so "`k` clusters per class" is tied to `d` (or, for `k` distinct
   *base patterns*, their orbits tend to collide at small `d`, violating
   orbit-purity A2 — a `k=4` localized-bump construction I tried gave chance
   accuracy for *both* nets, consistent with consolidated-theory Remark 6.6). So the
   honest shift-structured signature of the collapse is the **growing ratio** above,
   not an `FC ∼ d^{-1/2}` curve; the latter is the *non-shift* Frei regime and I do
   not claim conv-GAP changes it there.

6. **KKT distribution across restarts** (`kkt_restarts.py`, D-freq, `d=24`, 8
   seeds, GD to interpolation from random init): linearized radius
   **FC: min 1.65, median 2.29, max 2.48** vs **conv-GAP: min 3.23, median 3.40,
   max 3.52**. The conv-GAP *minimum* (3.23) exceeds the FC *maximum* (2.48) —
   **the distributions do not overlap**. So every GD-reachable conv-GAP KKT point is
   more robust than every GD-reachable FC one; the re-pointing is a property of the
   implicit-bias limit, not seed-luck. ✅ (Claim 3, the strongest empirical
   evidence; note this is *over reachable KKT points*, which is suggestive of but
   not equal to the universal statement blocked by O1.)

**Predictions for a larger harness (not yet run, falsifiable):**

* **P-opt-1 (the headline).** Train conv-GAP and matched-capacity FC on orbit data
  swept across `Δ_PS` (interpolate D-dot → D-freq). conv-GAP/FC robust-radius ratio
  should be a monotone increasing function of `Δ_PS/L` (= η/L), crossing 1 near
  `Δ_PS = 0` and rising to `>1`. This is the optimization-side version of P1/P3 in
  the consolidated theory and directly tests Claim 3+4.

* **P-opt-2 (scaling separation at large `d`).** On D-freq (`k = d`), the measured
  signature is the **conv-GAP/FC radius ratio increasing in `d`** (1.17 → 1.63 over
  `d = 16..64`); predict it keeps growing to `d = 10^4`. (The textbook
  `FC ∼ d^{−1/2}` collapse is the *fixed-`k`, growing-`d`* regime, which is *not*
  cleanly shift-realizable — see §8 caveat — so do **not** test the slope there;
  test the growing ratio.) Falsifies Claim 3 if the ratio stops growing or inverts.

* **P-opt-3 (head-averaging probe for O1).** Increase conv-GAP filter count `C` and
  measure whether a head-averaged non-robust KKT point appears (radius drops as `C`
  grows with mismatched `v`). If yes, O1 is real and bounds the universality of
  Claim 3.

* **P-opt-4 (architecture vs fine-grained supervision, the Li bridge).** Compare
  (a) FC + per-cluster labels (Li Thm 4.7) vs (b) conv-GAP + binary labels. Predict
  matched robustness — i.e. weight-sharing supplies the same information as
  fine-grained supervision. Confirms the §6 Li bridge.

* **P-opt-5 (pReLU × conv-GAP, the Min–Vidal complement).** Combine Min–Vidal's
  pReLU activation with conv-GAP. Predict the two levers compose: robustness
  advantage at least the max of the two, ideally super-additive, since they act on
  orthogonal averaging channels (subclass-averaging vs shift-averaging).

---

## 9. Summary — what survives the red-team, what does not (REVISED, governs the doc)

The original §9 claimed a conditional implicit-bias re-pointing. **That claim is
retracted** (see the correction box at the top). Here is the honest ledger after
adversarial review, with each item independently re-verified
(`/tmp/verify_redteam.py`).

### Does NOT survive (retracted)

* **The Frei/Li *contrast* on orbit data** (original Claim 3 / Prop 3 headline /
  the `1.57×` and non-overlapping-restart numbers as *evidence of re-pointing*).
  Reason: on D-freq data the orbit is **rank-2**, Frei/Li's orthogonal-cluster
  assumptions fail by ≥10×, and Frei's threat direction `z` **vanishes
  identically**, so there is no Frei-type non-robust baseline to be re-pointed away
  from. The empirical gap is plausibly a weak-baseline + train-point-linearized-radius
  artifact (red-team fair-baseline: ratios ≈0.86–1.16), and I could not re-confirm a
  fair baseline this session. **Treat as unconfirmed.**
* **"Min–Vidal's conjecture becomes a theorem here."** Their conjecture is about the
  *trained ReLU/pReLU network reached by gradient flow*. What this attempt can prove
  ("the architecturally-cheapest *quadratic* interpolant is robust") concerns a
  *fixed-feature quadratic model that is convex by inspection* — a different, easier
  object. The actual conjectured object (trainable conv-ReLU-GAP head) is left **open**
  (O2/O4). The conjecture is **not** resolved.
* **Any "GD reaches the global / re-points the implicit bias" trajectory claim.** The
  genuine `min‖θ‖²` program is non-convex (Burer–Monteiro lift; the convexity is only
  in lifted gauge coordinates), and finite-width GF→global is not proven — the same
  wall as the source papers.

### Survives (structural only; no optimization content)

* **Lemma 1 (proved, verified exactly, 4e-16):** conv-GAP ReLU = 2-layer ReLU with
  neurons *tied into cyclic shift-orbit bundles* (shared bias + output). Exact and
  discrete. This is an architecture↔reparameterization identity (already implicit in
  the consolidated span lemma), **not** an optimization result.
* **Function-class characterization (= structural Theorem A + span lemma, restated):**
  conv+square+GAP computes *linear functions of the power spectrum*; its max-margin is
  the SVM in power-spectrum feature space. Contains a large-margin (robust) member iff
  `Δ_PS = Ω(1)`. Pure structure.
* **Phase-blindness negative (Prop 4 / "Theorem II"), the most defensible new
  statement:** if the class signal is phase-coded (`Δ_PS = 0`, e.g. antipodal
  single-dot — verified `Δ_PS = 0`), conv-GAP-quadratic **cannot separate the classes
  at all** (chance accuracy). Verified (`failure_regime.py`: ratio 1.01, antipodal).
  But this is a *negative function-class* result and is the same `Δ_PS = 0` corner the
  structural theory already had.

### Corrected verdict (the honest answer to the open problem)

**The open problem is NOT closed.** Architectural shift-invariance restricts the
hypothesis class to (at the quadratic level) linear functions of the power spectrum;
on frequency-coded orbit data that class *contains* a robust classifier, and on
phase-coded data it cannot separate at all. **Whether gradient descent on a trainable
conv-ReLU-GAP net *reaches* the robust member is exactly as open as in
Frei/Min–Vidal/Li** — the shift constraint does not demonstrably re-point the
trajectory. The deepest reason, surfaced by the red-team and verified here, is
**structural, not optimization-theoretic:** the shift orbit is rank-deficient (a
low-dimensional circle), so it is a *degenerate* instance of the Frei/Li cluster
model in which the non-robustness mechanism is identically null — i.e. on this data
*there is no Frei-type threat to begin with*, which is why an unconstrained net is
already competitive and why the apparent "re-pointing" dissolves under a fair
baseline.

### The right reframing for any future positive attempt

1. To engage Frei/Li honestly you need **orthogonal** orbit clusters → the single-dot
   (delta) base, whose orbit *is* the orthonormal basis — but that lands in `Δ_PS = 0`
   (phase-coded), where conv-GAP-quad is blind. So a genuine optimization result must
   either (a) use a **phase-sensitive complete invariant** (bispectrum) whose
   Lipschitz budget is uncontrolled (consolidated Limitation 3), or (b) be proven for
   the **trainable conv-ReLU-GAP head** directly (the open dynamical step). There is no
   shortcut through the quadratic head.
2. The honest publishable nugget is the **rank-deficiency observation**: shift orbits
   are a degenerate corner of the cluster model where Frei's threat is null. This is a
   correct, novel structural statement; it does *not* claim to close the optimization
   gap.

*Citations used exactly as stated in source PDFs (re-checked by red-team against the
PDFs): Frei 2023 Asm 2.2 + Thm 4.1/4.2 (orthogonal means, `z`-attack); Li 2024 Asm
3.2 (exact orthogonality, `d=Ω(k^10)`) + Thm 4.5/4.7; Min&Vidal 2024 Conjecture 1
(trained pReLU via GF). The §1–8 text below is the original attempt, retained for the
record but **governed by this §9 and the top correction box**. Numerical claims that
are retracted above should not be cited as results.*
