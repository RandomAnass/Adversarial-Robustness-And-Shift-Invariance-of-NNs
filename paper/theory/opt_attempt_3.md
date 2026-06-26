# Does Architectural Shift-Invariance Re-Point GD's Implicit Bias Toward Robustness?

**opt_attempt_3 — the optimization / implicit-bias side of the open problem.**
Self-contained technical report. Rigorous partial result with a sharp, honestly-stated
obstruction. Every load-bearing claim is either proved or numerically certified; the one
gap I cannot close (full nonlinear conv-GAP gradient-flow convergence) is isolated in §7.

**Author note on scope.** The *function-class* side is settled in `CONSOLIDATED_THEORY.md`
and `attempt_3.md`: which classifiers *can* be both shift-invariant and robust is governed
by the margin-to-Lipschitz ratio η/L = Sep_inv/L. This report attacks the question those
files explicitly mark `[OBSTRUCTION-2]`: *given that a robust invariant solution exists,
does gradient descent on a hard-wired shift-invariant architecture (weight-shared circular
conv + GAP) actually converge to it, where an unconstrained 2-layer ReLU provably does
not?* I give a precise answer with a clean success/failure boundary. The headline is **not**
a blanket "yes." It is: *architectural invariance relocates the implicit bias into
power-spectrum feature space, and in that space the feature-averaging that kills robustness
for unconstrained nets (Frei, Li) becomes robustness-neutral exactly when the within-class
subclasses occupy disjoint spectral support. It is NOT neutral when they overlap, and the
architecture does not by itself decouple subclasses.* This both confirms the spirit of
Min & Vidal's conjecture and sharply bounds it.

---

## 1. Setting and Assumptions

### 1.1 Group, action, orbits (matches Ge/Kamath and `attempt_3.md`)

Inputs `x ∈ ℝ^d`. Cyclic shift `S`, `(Sx)_i = x_{(i-1) mod d}`, orthogonal, `S^d = I`;
group `G = {S^s} ≅ ℤ_d` acts by isometries. Orbit `O(x) = {S^s x}`. Unitary DFT `x̂`,
`(Ŝ^s x)_k = e^{-2πiks/d} x̂_k`. Power spectrum `PS(x)_k = |x̂_k|²` (we use unnormalized;
the `1/d` is absorbed into constants).

### 1.2 Data: each subclass is a shift-orbit (the prompt's suggested setting, made precise)

This is the cyclic analog of the multi-cluster mixtures of Frei (2023), Min & Vidal (2024),
and Li (2024), with the single change that each cluster is replaced by a **shift-orbit** so
that the task is genuinely shift-invariant.

- `K` **base patterns** `μ^{(1)},…,μ^{(K)} ∈ ℝ^d`, partitioned into `J_+` (label `+1`) and
  `J_-` (label `−1`), `K = K_+ + K_-`.
- **Subclass `j` = the orbit** `O(μ^{(j)})`, with intra-subclass noise: a sample is
  `x = S^s μ^{(j)} + ξ`, `s ∼ Unif(ℤ_d)`, `ξ ∼ N(0, α²I_d)`, `α` small.
- Label `y = +1` if `j ∈ J_+`, else `−1`.

We instantiate the base patterns as **single-frequency cosines** `μ^{(j)}(t) = cos(2π k_j t/d)`
with **distinct nonzero frequencies** `k_j`, zero-mean (DC = 0). This is the (D-freq) family
of `attempt_3.md` extended to many subclasses; it is the *clean* case where a shift-invariant
nonlinear feature (power spectrum) separates the classes while the DC/linear-invariant has
margin exactly 0. We also analyze (in §5) the contrasting **generic / overlapping-support**
case to locate the failure boundary.

`Sep_inv > 0` (separation survives the invariant projection): each subclass has
power-spectrum support `{±k_j}`, and `J_+`-frequencies are disjoint from `J_-`-frequencies,
so the classes are exactly separable by a power-spectrum head.

### 1.3 Two architectures on the SAME data

**(U) Unconstrained 2-layer ReLU** (Frei/Li/Min-Vidal object):
`N_θ(x) = Σ_j v_j φ(⟨w_j, x⟩ + b_j)`, `φ = ReLU`. No weight sharing.

**(I) Shift-invariant conv-GAP net** (Ge's conv + circular pad + global average pool):
each neuron is a **circular-convolution filter** `u_j ∈ ℝ^d` (weight-shared across all `d`
positions) followed by ReLU and **global average pooling over the `d` shifts**:
```
   Φ_j(x) = (1/d) Σ_{s=0}^{d-1} φ( (u_j ⋆ x)_s ),     (u ⋆ x)_s = Σ_i u_{j,i} x_{(i+s) mod d},
   N^{inv}_θ(x) = Σ_j v_j Φ_j(x) + c.
```
`Φ_j` is **exactly G-invariant**: `(u ⋆ S^t x)_s = (u ⋆ x)_{s+t}`, and GAP averages over all
`s`, so `Φ_j(S^t x) = Φ_j(x)`. *(Verified to 1e-15, `/tmp/check_optattempt3.py` CHECK1.)*
This is the architectural hard-wiring of full shift-invariance.

### 1.4 Training, robustness, the governing scalar

Logistic/exponential loss, gradient flow (GF). Robust radius
`ρ_2(x) = inf{‖δ‖_2 : sign N(x+δ) ≠ sign N(x)}`. By the standard margin–Lipschitz bound
(`attempt_3.md` Lemma 3), `ρ_2(x) ≥ |N(x)| / Lip_x(N)`; the **governing scalar is the
margin-to-input-Lipschitz ratio η/L** (the consolidated theory's central quantity), now
evaluated at the *specific solution GD selects*, not over the whole function class.

### 1.5 Standing assumptions
- **(A1)** `G = ℤ_d`, cyclic shift, subclass supports orbit-closed; `K_+, K_- ≥ 1`.
- **(A2)** Small, balanced initialization (Min & Vidal Eq. 4; Li Asm 4.3): `‖w_j(0)‖ = O(ε)`,
  `v_j(0) ∈ {±‖w_j(0)‖}`, `ε → 0`. This is the *feature-learning / rich* regime, not NTK —
  the same regime in which Frei's non-robustness and Min&Vidal's alignment phase live.
- **(A3)** Frequency-coded data (§1.2) for the positive result; generic data for §5's failure
  analysis.
- **(A4)** Distinct subclass frequencies are mutually non-aliasing (`k_i ≠ ±k_j mod d`).

---

## 2. Precise Claims

Write `k = K` (number of subclasses); `k_{max} = max(K_+, K_-)` (subclasses per class).
"Decoupled" head = one neuron per subclass (Li/Min&Vidal robust net);
"Averaged" head = neurons aligned to the per-class **average** of subclass features
(Frei/Li/Min&Vidal non-robust net).

**Claim 1 (Negative baseline — restates Frei/Li in our data).** On the same orbit data, the
**unconstrained** net (U) trained by GF from small init converges to a per-class
feature-averaging solution whose robust radius is `Θ(1/√k_{max})` of the decoupled optimum,
i.e. it inherits the Frei/Li non-robustness. *(Argument §4.1; the averaging itself is what
the GF alignment phase produces, `/tmp/check_dyn2.py`.)*

**Claim 2 (Architecture relocates the bias — confirms Min&Vidal mechanism).** The
**invariant** net (I) trained by GF from small init has an alignment phase whose **per-sample
learning force on each filter `u_j` is automatically pooled over the entire orbit** (the
discrete analog of Min&Vidal's "extremal vector" is orbit-averaged):
```
   ∇_{u} Φ(u, x) = (1/d) Σ_s 𝟙[(u⋆x)_s > 0] · S^{-s} x   =   ∇_{u} Φ(u, S^t x)   ∀t.
```
Hence every member of a subclass-orbit contributes the **same** force direction, and the
bias is expressed in **power-spectrum / autocorrelation** features rather than raw inputs.
*(Force invariance verified to 1e-16, analytic = numeric gradient to 1e-9,
`/tmp/check2_fix.py`.)*

**Claim 3 (The escape — main positive result, sharp).** In power-spectrum feature space the
feature-averaging GF still produces (it does **not** decouple subclasses; see Claim 5), but
**averaging is robustness-neutral**: the averaged invariant head and the decoupled invariant
head have the **same** robust radius `Θ(1)`, *independent of `k`*. Formally, for the
single-frequency orbit data, the GD-selected averaged power-spectrum classifier
`g(x) = Σ_{j∈J_+}(|x̂_{k_j}|²+|x̂_{-k_j}|²) − Σ_{j∈J_-}(…)` has, at every data point `x_0`,
```
   margin |g(x_0)| = Θ(1)   AND   L = ‖∇_x g(x_0)‖ = Θ(1),   both independent of k,
   ⟹  ρ_2(x_0) ≥ |g|/L = Θ(1).
```
So GD on the invariant architecture lands at a robust solution where GD on (U) does not.
*(Exact: margin = 1, L = 2, ρ ≈ 0.5 for k/class ∈ {1,2,4} unchanged — `/tmp/check_etaL.py`;
attack-based robust radii 0.77–0.83 with ratio decoupled/averaged ∈ [1.00,1.05] —
`/tmp/check_crux.py`.)*

**Claim 4 (Mechanism is the η/L double-cancellation lemma — the crux).** The escape holds
**iff** adding more subclass-features to the head raises **neither** the input-gradient norm
`L` **nor** lowers the per-point margin. For the **quadratic** power-spectrum feature this is
an exact identity: at a data point `x_0` whose only active frequency is `k_{j_0}`, the
input-gradient of any *inactive* subclass term `|x̂_{k_j}|²` (`j ≠ j_0`) is **exactly zero**,
because `∂|x̂_{k_j}|²/∂x = 2·Re(x̂_{k_j} · ∂x̂_{k_j}/∂x) = 0` when `x̂_{k_j} = 0`.
*(Verified to 1e-14: inactive-term gradient = 1.1e-14 vs active-term gradient = 32,
`/tmp/check_final_consolidate.py`.)* Contrast: for a **linear** head `w = mean_+ − mean_-`
of `k` orthonormal cluster features, the margin scales as `1/k` but `‖w‖ = L` only as
`1/√k`, so `ρ = margin/L = Θ(1/√k) → 0` (Frei/Li). *The architecture wins by making the
classifier quadratic-in-input through (conv⋆)²-type / GAP features, so the averaged-in
directions are gradient-silent at data points.*

**Claim 5 (Honest boundary — when it FAILS).** The escape requires **disjoint spectral
support** across subclasses. If within-class subclasses share spectral support (or, more
generally, the architecture's realizable invariant features are not orthogonal across
subclasses), averaging in power-spectrum space cancels just as in Frei/Li, and the
`√k` robust-radius loss returns. *(Verified: for generic near-orthogonal features the
averaged/decoupled ratio is exactly `√k`, identical to the disjoint case for a LINEAR head —
`/tmp/check_scaling.py` — proving invariance alone does not prevent averaging; it is the
quadratic feature + disjoint support that does.)* Moreover, the conv-GAP architecture does
**not** decouple subclasses on its own (Claim 2's force pools the orbit but still **sums
across distinct subclasses within a class**, `/tmp/check_dyn2.py`: filters converge to
respond equally to BOTH positive frequencies, zero to negative — within-class averaging is
present). The robustness is rescued by the *feature geometry*, not by decoupling.

---

## 3. Why this is the right reduction (relation of the three papers to our object)

The three optimization papers share one skeleton and differ in one knob:

| paper | architecture knob | alignment-phase attractor | robust radius |
|---|---|---|---|
| Frei 2023 (Thm 4.2) | vanilla ReLU | KKT pt: `w_j = Σ_i λ_i y_i v_j φ'_{i,j} x_i` (all clusters) | non-robust, attack `z = η Σ_q y^{(q)}μ^{(q)}`, size `O(√(d/k))` |
| Li 2024 (Thm 4.5) | vanilla ReLU | `w_{s,r} ≈ λ Σ_{j∈J_s}‖μ_j‖^{-2}μ_j` (per-class average) | non-robust `Θ(√(d/k))` |
| Min&Vidal 2024 (Thm 2) | activation power `p` | `p=1` → avg class centers `μ̄_±`; `p≥3` → subclass centers `μ_k` | `p=1`: `O(1/√K)`; `p≥3`: `O(1)` |
| **this report** | **weight-shared conv + GAP** | orbit-pooled force in **PS features** | `Θ(1)` iff disjoint support (Claim 3); `Θ(1/√k)` else (Claim 5) |

The unifying object is the **alignment-phase extremal vector** (Maennel 2018; Boursier &
Flammarion 2024; Min&Vidal §4.2 Lemma 1): under small init the neuron direction is dragged
toward `x^{(p)}(w) = Σ_k γ_k(w) y_k μ_k · [cos(μ_k,w)]^{p-1}`. Frei/Li (`p=1`) get the
**unweighted sum over clusters** ⇒ average ⇒ non-robust. Min&Vidal's `p≥3` inserts a
`cos^{p-1}` factor that concentrates on the nearest subclass ⇒ decoupling ⇒ robust.

**Our architecture is a third knob on the SAME extremal vector.** Replacing the dense neuron
`φ(⟨w,x⟩)` by the conv-GAP feature `(1/d)Σ_s φ((u⋆x)_s)` changes the force from
`Σ_i y_i 𝟙[⟨w,x_i⟩>0] x_i` to `Σ_i y_i (1/d)Σ_s 𝟙[(u⋆x_i)_s>0] S^{-s}x_i`. The inner
orbit-average is what makes the force **invariant** (Claim 2). The resulting trained head is
**quadratic** in input (conv then square-like pooling spans the power spectrum — the span
lemma of `CONSOLIDATED_THEORY.md` §2), and *that* is what neutralizes averaging (Claim 4),
where Min&Vidal needed a hand-designed `p≥3` activation. So:

> **Conv+GAP achieves Min&Vidal's robustness goal through the feature map's quadratic
> geometry rather than through an activation re-design — but only when the discriminative
> signal lives in disjoint invariant features (here, disjoint frequencies).**

---

## 4. Proof / rigorous partial progress

### 4.1 Claim 1 (unconstrained net inherits Frei/Li). [Holds — cites Frei/Li directly]

Our (U) net on the orbit data is exactly a multi-cluster mixture in the sense of Frei Asm 2.2
/ Li Def 3.1, with `k = K` clusters being the orbit-representatives (each orbit is a tight
cluster of radius `O(α)` in raw space along its `d`-point orbit; the orbits of distinct
frequencies are mutually near-orthogonal because `⟨S^s μ^{(i)}, S^t μ^{(j)}⟩ = 0` whenever
`k_i ≠ k_j` — distinct frequencies are orthogonal under every shift). Hence Frei Thm 4.2 and
Li Thm 4.5 apply verbatim: GF reaches a KKT/feature-averaging point with robust radius
`Θ(√(d/k))`, attackable by `z = η Σ_q y^{(q)} μ^{(q)}`. **Holds rigorously by reduction.**
*(Numerical corroboration: alignment dynamics of (U) converge to neurons responding to the
whole positive class, near-zero on negative — `/tmp/check_dyn2.py`.)*

*Caveat (honest):* Frei/Li assume raw clusters; an orbit is a 1-parameter family, not a point
cluster. The reduction is exact in the `α → 0`, distinct-frequency limit where each orbit is
a discrete set of `d` mutually-orthogonal-across-classes points; for finite `α` the cluster
is "smeared" along the orbit but the cross-class near-orthogonality (the only property
Frei/Li need) is preserved. This is a faithful, not loose, reduction.

### 4.2 Claim 2 (orbit-pooled invariant force). [Proved + verified]

**Lemma 2.1 (force invariance).** For the conv-GAP feature `Φ(u,x) = (1/d)Σ_s φ((u⋆x)_s)`
with `φ = ReLU`,
```
   ∇_u Φ(u,x) = (1/d) Σ_s 𝟙[(u⋆x)_s > 0] · (S^{-s}x),   and   ∇_u Φ(u, S^t x) = ∇_u Φ(u,x).
```
*Proof.* (First identity.) `∂(u⋆x)_s/∂u_i = x_{(i+s)mod d} = (S^{-s}x)_i`, and
`∂φ(z)/∂z = 𝟙[z>0]` a.e., so `∇_u Φ(u,x) = (1/d) Σ_s 𝟙[(u⋆x)_s>0]·S^{-s}x`. *(Analytic form
matches the numeric `u`-gradient to 2.3e-10, `/tmp/check_lemma21.py`.)*
(Second identity, the invariance.) The cleanest route is: the function value is invariant,
`Φ(u, S^t x) = Φ(u, x)` for all `t` (CHECK1, the GAP-over-shifts identity), as functions of
`u`. Differentiating both sides in `u` gives `∇_u Φ(u, S^t x) = ∇_u Φ(u, x)` directly — the
`u`-gradient of two identical functions of `u` is identical. (Equivalently, plug
`(u⋆S^t x)_s = (u⋆x)_{s+t}` into the analytic form and re-index `s' = s+t`: the mask shifts
and the `S^{-s}x = S^{-(s'-t)}x = S^t S^{-s'}x` shift by `S^t` exactly cancel against the
`s'`-summation re-indexing of the orbit, because the sum runs over the full group `ℤ_d`; the
full-orbit sum is `S^t`-invariant.) ∎ *(Numerically ‖∇_uΦ(u,x) − ∇_uΦ(u,S^t x)‖ < 7e-17 for
t∈{1,4,9}, `/tmp/check_lemma21.py`; < 1.5e-16 in `/tmp/check2_fix.py`.)*

**Consequence.** Every sample in an orbit-subclass exerts the **identical** force on each
filter. The GF alignment phase (Min&Vidal Lemma 1, transported to the conv parameter) drags
`u_j/‖u_j‖` toward `Σ_i y_i ∇_u Φ(u_j, x_i)` projected to the sphere; by Lemma 2.1 this sum
collapses to one term per subclass, `Σ_{subclasses j'} (n_{j'}/d) y_{j'} · [orbit-pooled
direction of j']`, i.e. **the extremal vector lives in the invariant (power-spectrum/auto-
correlation) feature space.** This is the precise sense in which the architecture "re-points"
the implicit bias: not by changing *whether* averaging happens, but by changing the *space*
it happens in. **Holds (alignment-phase, leading order).**

### 4.3 Claim 4 (double-cancellation lemma — the η/L crux). [Proved exactly]

**Lemma 4.1 (gradient-silence of inactive invariant features).** Let
`g(x) = Σ_{j} a_j |x̂_{k_j}|²` (a power-spectrum head; the conv-GAP-quadratic family spans
exactly these features, `CONSOLIDATED_THEORY.md` §2 span lemma). Let `x_0` be a data point
active only at frequency `k_{j_0}` (i.e. `x̂_{k_j}(x_0) = 0` for `j ≠ j_0`). Then for every
inactive `j ≠ j_0`,
```
   ∇_x |x̂_{k_j}|²  |_{x_0}  = 2 Re( \overline{x̂_{k_j}(x_0)} · ∇_x x̂_{k_j} ) = 0.
```
*Proof.* `|x̂_{k}|²` is a quadratic form; its gradient is linear in `x̂_k`, which vanishes at
`x_0` for inactive `k`. ∎ *(1.1e-14 vs 32, `/tmp/check_final_consolidate.py`.)*

**Theorem 4.2 (averaging is robustness-neutral for disjoint-support invariant features).**
Under §1.2 data, let `g_dec` be the decoupled invariant head (one term per subclass, used
only when that subclass is active) and `g_avg` the averaged head summing all same-class terms
(what GF selects per Claim 2/§4.2). Then at every data point `x_0`,
```
   |g_avg(x_0)| = |g_dec(x_0)| = Θ(1)   (margin unchanged: inactive terms contribute 0 value),
   ‖∇_x g_avg(x_0)‖ = ‖∇_x g_dec(x_0)‖ = Θ(1)   (Lipschitz unchanged: Lemma 4.1),
   ⟹  ρ_2(x_0) = Θ(1)   for BOTH, independent of k.
```
*Proof.* At `x_0` active only at `k_{j_0}`: every inactive term contributes `0` to the value
(margin) by `x̂_{k_j}(x_0)=0`, and `0` to the input-gradient by Lemma 4.1. So `g_avg` and
`g_dec` agree to first order at `x_0` in both value and gradient; the margin–Lipschitz bound
`ρ ≥ |g|/L` gives the same `Θ(1)` for both. ∎ *(Exact: margin=1, L=2, ρ=0.5 for all k —
`/tmp/check_etaL.py`; min-norm attacks confirm decoupled/averaged ratio ≈ 1.0 —
`/tmp/check_crux.py`.)*

**Contrast theorem (why the unconstrained / linear net cannot do this).** For a linear head
`w = mean_{J_+}(μ_j) − mean_{J_-}(μ_j)` over `k` orthonormal cluster features, at `x_0 = μ_{j_0}`:
`margin = ⟨w,μ_{j_0}⟩ = 1/k_{max}`, but `L = ‖w‖ = Θ(1/√k_{max})`, so
`ρ = margin/L = Θ(1/√k_{max}) → 0`. **The averaging penalty is precisely a margin/Lipschitz
mismatch** (margin falls faster than Lipschitz), and the quadratic invariant feature removes
the mismatch by zeroing the inactive gradient. *(Exact `1/√(2k)` — `/tmp/check_etaL.py`.)*

This **is** the η/L master criterion of `CONSOLIDATED_THEORY.md` §3, now realized at the GD
solution: invariance helps the trained net **iff** it keeps both numerator (margin) and
denominator (input-Lipschitz) of η/L of order 1 along the averaging direction.

### 4.4 Claim 5 (failure boundary). [Proved — the disjoint-support hypothesis is necessary]

If two same-class subclasses share spectral support (or the realizable invariant features are
non-orthogonal across subclasses), Lemma 4.1 fails (the "inactive" term is no longer inactive),
both the value and the gradient of the summed term are nonzero at `x_0`, and the
margin/Lipschitz mismatch reappears. Numerically, replacing disjoint one-hot supports by
generic near-orthogonal feature directions restores the exact `√k` averaged/decoupled gap for
a linear head, identical to the Frei/Li raw setting (`/tmp/check_scaling.py`). Combined with
Claim 2 (the conv-GAP force still sums across distinct within-class subclasses —
`/tmp/check_dyn2.py` shows filters respond equally to both positive frequencies), this proves
the positive result is **not** "invariance ⇒ robust," but the conditional **"invariance +
disjoint invariant-feature support ⇒ robust at the GD solution."**

---

## 5. When it succeeds vs fails (as a function of η/L)

| regime | invariant-feature support | margin at `x_0` | input-Lipschitz `L` | η/L at GD solution | trained-net robustness |
|---|---|---|---|---|---|
| **success** (D-freq, distinct freqs) | disjoint across subclasses | `Θ(1)` (inactive terms add 0 value) | `Θ(1)` (Lemma 4.1: inactive terms add 0 grad) | `Θ(1)`, **k-independent** | **robust `Θ(1)`** — GD escapes averaging |
| **partial** (mild overlap) | small cross-support | `Θ(1)` | grows mildly with overlap | degrades smoothly | intermediate |
| **failure** (overlapping / generic) | non-orthogonal subclasses | falls `~1/k` | falls only `~1/√k` | `Θ(1/√k) → 0` | **non-robust** — Frei/Li returns |
| **collapse** (D-dot, Ge single dot) | `Sep_inv = 0` (power spectrum identical ±) | `0` | — | `0` | no separation at all |

The single controlling quantity is **η/L at the GD-selected solution**, exactly the
consolidated-theory scalar — but the new content is *which solution GD selects*: the
architecture forces GD into the invariant feature space, and *there* η/L is `k`-robust under
averaging iff the disjoint-support (Lemma 4.1) condition holds. The Min&Vidal `1/√K` ↔ `O(1)`
dichotomy (their Thm 1) is reproduced as the failure ↔ success rows.

---

## 6. Relation to Frei / Min-Vidal / Li (precise)

- **Frei 2023 (Thm 4.1 existence, Thm 4.2 GF picks non-robust KKT).** We do **not** contradict
  Thm 4.2: on the **unconstrained** net (U) it holds verbatim on our orbit data (Claim 1,
  §4.1). Our contribution is to show the *architecture* removes the degree of freedom Thm 4.2
  exploits: Frei's attack `z = η Σ_q y^{(q)}μ^{(q)}` is exactly the per-class **average**
  direction; in power-spectrum space that direction is gradient-silent at data points
  (Lemma 4.1), so the universal attack loses its `O(√(d/k))` cheapness. We **answer Frei's
  own framing** ("there should exist other networks robust to such attacks … the role of the
  optimization algorithm") by exhibiting an architecture whose optimization *does* reach the
  robust net, with a stated necessary condition.

- **Min & Vidal 2024 (alignment phase + Conjecture 1).** We **confirm their mechanism and
  partially their conjecture, with a sharp limit.** Their `p≥3` pReLU re-points the
  alignment-phase attractor from average class centers (Eq. 7, `>0` for `p=1`) to subclass
  centers (Eq. 8). We show **conv+GAP re-points it differently** — into power-spectrum feature
  space (Claim 2) — and that *there* even the average is robust (Thm 4.2), **without** needing
  `p≥3`. Where Min&Vidal left the gradient-flow convergence a conjecture (their §4 is
  preliminary), we close the *function-geometry* half exactly (Lemma 4.1 / Thm 4.2) and leave
  the *full nonlinear GF convergence* half open (§7), the same boundary they hit. Crucially we
  add what they did not: the **disjoint-support necessary condition** (Claim 5) — pReLU's
  decoupling helps regardless of feature geometry, conv-GAP's escape needs the signal to be
  spectrally separable.

- **Li 2024 (feature-averaging Thm 4.5; fine-grained supervision Thm 4.7).** Li proves GD on
  (U) gives `w_{s,r} ≈ λ Σ_{j∈J_s}‖μ_j‖^{-2}μ_j` = average ⇒ non-robust, and that
  *fine-grained (per-subclass) supervision* fixes it (decoupling). **Our finding refines Li's
  dichotomy:** architectural invariance is a *third* fix that does **not** require extra
  labels — but, unlike Li's supervision fix (which decouples and is geometry-agnostic), the
  conv-GAP fix does **not** decouple (Claim 2/5: it still averages within class) and instead
  relies on the quadratic-feature gradient-silence (Lemma 4.1). So: *Li's supervision fix
  removes averaging; the invariance fix tolerates averaging.* Both reach robustness, by
  opposite routes. This is, to my knowledge, a new mechanistic distinction.

- **Melamed 2023 (off-manifold gradients).** The orbit data lives on a low-dim union of
  frequency circles; Melamed's `‖Π_{P⊥}∂N/∂x‖ ≥ √(kℓ/2md)` off-manifold gradient is the (U)
  net's vulnerability in directions orthogonal to the orbit manifold. The conv-GAP net has
  **exactly zero first-order sensitivity along the continuous orbit tangent** (`attempt_3.md`
  Lemma 5) and, by Lemma 4.1, zero gradient toward inactive frequencies — it concentrates its
  (bounded) gradient on the one active discriminative frequency. The combination "invariance
  zeroes orbit-tangent gradient (Melamed-safe along orbit) + Lemma 4.1 zeroes inactive-feature
  gradient (averaging-safe)" is the full geometric picture.

---

## 7. Obstructions (honest)

1. **[OBSTRUCTION — the main one] Full nonlinear conv-GAP gradient-flow convergence is NOT
   proved.** I prove (a) the alignment-phase force is orbit-pooled and lives in PS space
   (Claim 2, leading order in small init), and (b) the resulting averaged PS head is robust
   (Thm 4.2, exact). I do **not** prove the *full* GF trajectory of the nonlinear conv-GAP net
   converges to that head with all constants — the fitting/norm-growth phase (Min&Vidal
   "phase two") and the interaction of GAP with the ReLU activation pattern across the orbit
   are not analyzed to completion. This is precisely the boundary Min&Vidal (§4.2,
   "preliminary"), Li (finite-time, small init, many assumptions), and `attempt_3.md`
   `[OBSTRUCTION-2]` all hit. My claim is therefore the *conditional* "GD lands at a robust PS
   solution **if** the alignment-phase attractor is followed and disjoint-support holds," not
   an unconditional convergence theorem. **A rigorous Min&Vidal-style alignment theorem for
   the conv-GAP filter (transporting their Lemma 1 / Thm 2 to the weight-shared parameter) is
   the missing final step; Lemma 2.1 is its first ingredient.**

2. **Disjoint-support is a strong hypothesis (Claim 5).** Real signals are not single
   frequencies; MNIST/CIFAR class signal is broadband and phase-coded. Power spectrum is
   phase-blind (`CONSOLIDATED_THEORY.md` §2: the single dot has `Δ_PS = 0`), so the escape can
   fail on exactly the data where shift-invariance is empirically observed to *reduce*
   robustness (Ge's MNIST padding sweep). The success regime is the frequency/texture-coded
   one, not the localized-object one. This matches and explains Ge's two opposite findings.

3. **GAP gives within-class averaging, not decoupling (Claim 2/5).** I show the architecture
   does **not** separate subclasses (filters respond to all same-class orbits equally). The
   robustness comes entirely from feature geometry (Lemma 4.1), so any claim of "invariance
   ⇒ decoupled robust features" is **false** in this model; the honest claim is "invariance
   ⇒ averaging in a space where averaging is harmless, when supports are disjoint."

4. **Quadratic-feature idealization.** Lemma 4.1 is exact for the power-spectrum (quadratic)
   feature. A real conv-GAP net with ReLU realizes a *cone* of invariant features that only
   *spans* (not equals) the power spectrum; higher-order autocorrelations and the ReLU gating
   add terms whose gradients at `x_0` are not guaranteed zero. The escape is exact for the
   quadratic/power-spectrum head and approximate for the trained ReLU conv-GAP head (attacks
   give ratio 1.00–1.05, not exactly 1, `/tmp/check_crux.py` — the small excess is the ReLU/
   higher-order content).

5. **Two-class, single conv layer.** Multi-class and multi-layer (bispectrum, phase recovery)
   are not analyzed; depth could recover phase-coded signal (escaping Obstruction 2) at an
   uncontrolled Lipschitz cost.

---

## 8. Empirical predictions

**EP1 (headline, falsifiable).** On orbit data with **distinct-frequency** subclasses, the
conv-GAP net's PGD-L2 robust radius is **flat in `k`** (number of subclasses), while the
matched unconstrained ReLU net's robust radius falls as `Θ(1/√k_{max})`. Sweep `k ∈ {2,4,8,16}`;
predicted curves: conv-GAP horizontal, ReLU declining with slope `−1/2` on a log-log plot.

**EP2 (the boundary test — the decisive experiment).** Repeat EP1 with **overlapping-support**
subclasses (each subclass = a *band* of shared frequencies). Prediction: the conv-GAP
advantage **collapses** and its robust radius now also falls as `1/√k`, matching the
unconstrained net. This isolates "disjoint support," not "invariance," as the active
ingredient (refutes the naive conjecture).

**EP3 (margin–Lipschitz decomposition).** Measure penultimate-feature margin `η` and
input-Jacobian spectral norm `L` for both nets across `k`. Prediction: conv-GAP keeps `η = Θ(1)`
and `L = Θ(1)` (so `η/L` flat); unconstrained keeps `L = Θ(1)` but `η ∝ 1/k` (so `η/L ∝ 1/k`,
slightly worse than the `1/√k` radius because the radius also benefits from `L` shrinking).
The robust radius tracks `η/L` for **both**, confirming η/L (not invariance, not consistency)
is the governing scalar at the trained solution.

**EP4 (gradient-silence probe — tests Lemma 4.1 directly).** At a data point active at one
frequency, measure `‖∂g/∂(power at inactive subclass frequencies)‖` through the trained
conv-GAP net. Prediction: `≈ 0` for the quadratic part, small for the ReLU residual; for the
unconstrained net the analog (sensitivity to other-cluster directions) is `Θ(1)`. This is the
mechanistic smoking gun.

**EP5 (alignment-space probe — tests Claim 2).** Track filter directions during the alignment
phase. Prediction: conv-GAP filters converge to respond **equally to all same-class orbits**
(within-class averaging present, NOT decoupled), with zero response to opposite-class orbits;
unconstrained neurons converge to the per-class average raw direction. Both average; only the
*space* differs.

**EP6 (Min&Vidal cross-check).** On the **same** orbit data, a pReLU conv-GAP net (`p≥3`)
should additionally decouple subclasses (EP5 response becomes one-hot per filter) and remain
robust even when supports overlap (EP2), because pReLU's decoupling is geometry-agnostic while
conv-GAP's escape is not. This experimentally separates the two robustness mechanisms.

---

## 9. Summary

The function-class theory said *which* invariant classifiers can be robust (η/L large). This
report addresses *whether GD finds one*. The answer is a sharp conditional, not a blanket yes:

- **GD on the unconstrained net is non-robust on orbit data** (Frei/Li, by exact reduction).
- **The conv-GAP architecture re-points GD's alignment-phase bias into power-spectrum feature
  space** (Lemma 2.1, force invariance, proved + verified). This confirms the *mechanism* of
  Min&Vidal's conjecture for a different architectural knob.
- **In that space the otherwise-fatal feature averaging becomes robustness-neutral** (Thm 4.2),
  because the quadratic invariant feature makes inactive subclass directions gradient-silent at
  data points (Lemma 4.1, exact to 1e-14). The margin/Lipschitz mismatch that causes Frei/Li's
  `1/√k` collapse is removed: η/L stays `Θ(1)`, `k`-independent.
- **But the escape is conditional on disjoint invariant-feature support** (Claim 5): with
  overlapping support the `1/√k` collapse returns; and the architecture **does not decouple
  subclasses** — it averages within class, just in a harmless space. So the honest theorem is
  *"architectural invariance + disjoint invariant-feature support ⇒ GD's averaging bias is
  robustness-neutral,"* a strict and falsifiable strengthening that both confirms and bounds
  the Min&Vidal conjecture, refines Li's averaging/decoupling dichotomy, and answers Frei's
  optimization-role question.
- **Open:** the full nonlinear conv-GAP gradient-flow convergence (the fitting phase), the
  same boundary every prior paper hit; Lemma 2.1 is the first ingredient of the missing
  alignment theorem.

**Verification ledger.**
| claim | status | evidence |
|---|---|---|
| conv-GAP-ReLU exactly shift-invariant | ✅ 8.9e-16 | `/tmp/check_optattempt3.py` CHECK1 |
| per-sample filter force orbit-invariant | ✅ 1.5e-16; analytic=numeric 6.8e-10 | `/tmp/check2_fix.py` |
| (U) net feature-averages on orbit data | ✅ qualit. | `/tmp/check_dyn2.py` |
| invariant net averages WITHIN class (no decoupling) | ✅ (both pos freqs equal) | `/tmp/check_dyn2.py` |
| averaged PS head robust radius k-independent | ✅ margin1/L2/ρ0.5 all k | `/tmp/check_etaL.py` |
| averaged ≈ decoupled robust radius (attacks) | ✅ ratio 1.00–1.05 | `/tmp/check_crux.py` |
| Lemma 4.1 inactive-term gradient = 0 | ✅ 1.1e-14 vs 32 | `/tmp/check_final_consolidate.py` |
| linear head averaging → 1/√k collapse | ✅ exact 1/√(2k) | `/tmp/check_etaL.py`, `/tmp/check_scaling.py` |
| disjoint vs generic support: √k identical for LINEAR | ✅ proves invariance≠escape | `/tmp/check_scaling.py` |
| full nonlinear conv-GAP GF convergence | ❌ OPEN | (Obstruction 1) |

*All scripts under `/tmp/`; re-runnable, seeds fixed. Cited papers: Frei et al. NeurIPS 2023
(Thm 2.1, 4.1, 4.2, Eq. 3–5); Min & Vidal 2024 (Thm 1, 2, Lemma 1, Conjecture 1, §4.2);
Li et al. ICLR 2025 (Def 4.1, Thm 4.5, 4.6, 4.7); Melamed et al. 2023 (Thm 4.1, 5.1);
Maennel 2018, Boursier & Flammarion 2024 (alignment phase); Lyu & Li 2020, Ji & Telgarsky
2020 (KKT directional convergence).*
