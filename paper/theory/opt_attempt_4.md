# Does Architectural Shift-Invariance Re-Point GD's Implicit Bias Toward Robustness?
## A conditional theorem: weight-sharing divides out the orbit but not the within-class base multiplicity

**opt_attempt_4 — optimization / implicit-bias closure of the open gap (CONSOLIDATED_THEORY.md §5(a)).**

Author working notes. Goal: state and prove, as far as rigor allows, whether hard-wired architectural
shift-invariance (weight-shared circular conv + global average pooling, "conv-GAP") changes the
implicit bias of gradient flow / gradient descent so that it converges to the robust (large-η/L)
solution where an unconstrained two-layer ReLU net would not. The structural side (which classifiers
*exist*; CONSOLIDATED_THEORY.md) is taken as established; this file is purely the **optimization**
side: which solution training *selects*.

**Headline result (conditional, with a clean negative core).** Architectural shift-invariance does
**not** in general fix the non-robust implicit bias. It *partially* re-points it, by a precise and
provable mechanism: weight-sharing **divides out the shift-orbit multiplicity** from the
Frei/Li feature-averaging count, but it leaves the **within-class base-pattern multiplicity** in
place, and feature-averaging *recurs within the invariant family* over those base patterns — driven
by the *same* uniform-sign drive that Frei/Li identified, now living in power-spectrum space. We
prove this re-pointing exactly for the quadratic conv-GAP head (whose alignment dynamics
**diagonalize in frequency**), give a partial argument for the ReLU conv-GAP head, exhibit the
governing scalar (it is η/L = Sep_inv/L of the consolidated theory, with an effective cluster count
`K` replacing Frei's `k`), and identify two honest obstructions: (i) a **phase-blindness**
obstruction under which conv-GAP is *forced* to average (a strict negative result), and (ii) the gap
between the tractable quadratic head and a general ReLU conv-GAP trajectory. Empirically the predicted
monotone advantage `R_2(conv-GAP)/R_2(ReLU)` rising with within-class multiplicity `K` is confirmed
(0.81 → 1.03 → 1.20 → 1.60 for K = 1,2,4,8).

Throughout, `[=]` marks an identity, `[≤]`/`[≥]` a proved inequality, `[H]` a heuristic/obstruction,
`[V]` a numerically verified claim (scripts in this file's commit; all `[V]` results reproduced at
`d ∈ {24,32,48,64}`).

---

## 1. SETTING & ASSUMPTIONS

### 1.1 Architecture, group, loss (matching Frei / Li / Min-Vidal so the comparison is exact)

Inputs `x ∈ R^d`. Cyclic group `G = Z_d`, `(S_s x)_i = x_{(i-s) mod d}`, each `S_s` orthogonal,
`S_a S_b = S_{a+b}`, abelian. Orbit `O(x) = {S_s x}`. Orbit-average projector `P = (1/d)Σ_s S_s =
(1/d)1 1^T` projects onto the DC line `V_inv = span(1_d)`; `Q = I − P` projects onto the AC block
`V_AC = 1_d^⊥` (CONSOLIDATED_THEORY §1; attempt_1 Lemma 2.1). Unitary DFT `F`, `S_s = F^* Λ_s F`,
`Λ_s = diag(ω^{sk})`, `ω = e^{2πi/d}`.

**Two learners on the same data** (this matched comparison is the whole point):

- **(U) Unconstrained 2-layer ReLU** (Frei Eq. before Thm 2.1; Li §3.2; Min-Vidal §2):
  `N(x) = Σ_{j∈[m]} v_j φ(⟨w_j, x⟩ + b_j)`, `φ = ReLU`. Trained by gradient flow (GF) on the
  logistic/exponential loss. Homogeneous of degree 2.

- **(I) Shift-invariant conv-GAP** (the architecture of Ge Note 1; CONSOLIDATED §2 span lemma).
  A single circular filter `w ∈ R^d` produces, via full-width circular convolution at all `d`
  positions followed by GAP,
  ```
     φ_w^{relu}(x) = (1/d) Σ_{s∈G} φ(⟨S_s w, x⟩ + b)            (conv-GAP-ReLU)        (1)
     φ_w^{sq}(x)   = (1/d) Σ_{s∈G} (⟨S_s w, x⟩)^2 = (1/d) Σ_k |ŵ_k|^2 |x̂_k|^2   (conv-GAP-quad)  (2)
  ```
  the second by Parseval (CONSOLIDATED span lemma, verified). The invariant net is
  `N_I(x) = Σ_{r∈[m]} v_r φ_{w_r}(x)`, also homogeneous (degree 2 for the quad head). **Both φ^{relu}
  and φ^{sq} are exactly shift-invariant: `φ_w(S_t x) = φ_w(x)` for all t.** `[=]` (re-index the sum
  over s; verified numerically, §3).

**(A-data) Orbit-cluster Gaussian mixture** (the suggested setting, made precise). This is the
shift-orbit analog of the Frei/Li multi-cluster distribution. Fix base patterns
`μ_1,...,μ_{K_+}` (class +) and `μ_{K_++1},...,μ_K` (class −), `K = K_+ + K_-`, each `‖μ_j‖ = √d`.
A sample is drawn by: pick a base `j ~ Unif`, a **phase** `s ~ Unif(G)`, set
`x = S_s μ_j + ξ`, `ξ ~ N(0, σ^2 I)`, `y = +1` iff `j ≤ K_+`. So **each class is a union of K_±
full shift-orbits**, and the discriminative content is the *identity of the base pattern's orbit*.
We will instantiate base patterns as pure/low-frequency cosines so the power spectrum is the natural
invariant coordinate (Ge §5.2 dataset; CONSOLIDATED P2/P3). This is *exactly* Frei/Li's data with the
cyclic group action stapled on, which is what lets every constant be compared line-by-line.

**(A-orbit-sep / A-orbit-ent).** Two sub-regimes that turn out to decide everything:
- *Frequency-separated* (A-orbit-sep): the K base patterns have **disjoint power-spectrum support**
  (distinct frequencies). `[V]` disjoint.
- *Phase-coded / entangled* (A-orbit-ent): two base patterns share power-spectrum support but differ
  in **relative phase** (e.g. `μ_A = cos_3 + cos_4`, `μ_B = cos_3 − cos_4`; same `|x̂_k|`, different
  phase). `[V]` `PS(μ_A) = PS(μ_B)` exactly while `‖μ_A − μ_B‖ = Θ(√d)`.

### 1.2 What "robust" means and the scalar we track

`R_2(f;x) = inf{‖δ‖_2 : sign f(x+δ) ≠ y}`. We track the consolidated master scalar
`η/L = Sep_inv/L` (margin-to-Lipschitz of the *achievable invariant feature*), and show that the
relevant cluster count inside it is an **effective multiplicity** `K_eff` that the *architecture*
sets — the bridge between this optimization file and the structural file.

---

## 2. PRECISE CLAIM(S)

Let `R_2^U`, `R_2^I` be the median robust radius of the GF-trained unconstrained and conv-GAP nets on
clean correctly-classified test points from (A-data).

> **Claim 1 (orbit division — the positive part).** On (A-data), gradient flow on the conv-GAP net
> has an implicit bias whose feature-averaging is over the **K base patterns**, not over the
> `K·d` orbit-blown-up directions the unconstrained net averages over. Formally, the Frei/Li
> non-robust radius `Θ(√(d/k_eff))` holds with `k_eff^U = Θ(K·d_orbit)` for the unconstrained net but
> `k_eff^I = Θ(K)` for the conv-GAP net, where `d_orbit ≤ d` is the orbit size. Hence
> `R_2^I / R_2^U = Θ(√{d_orbit})` up to the recurrence in Claim 2 — architecture re-points the bias
> *toward* robustness, monotonically in the orbit size.

> **Claim 2 (within-class recurrence — the negative part, the heart of this file).** Architectural
> shift-invariance does **not** fully fix the bias. Over the `K` within-class base patterns,
> feature-averaging **recurs inside the invariant family**: a single conv-GAP filter grows on *all*
> same-class invariant features simultaneously, by the identical uniform-sign-drive mechanism of
> Frei (Thm 4.2) / Li (Thm 4.5). For the quadratic head this is *exact* (Thm I below): the alignment
> dynamics diagonalize in frequency and the per-frequency drive `M_k = Σ_i y_i |x̂_{i,k}|^2` has a
> common sign across all in-class frequencies, so the filter averages them. Consequently
> `R_2^I = Θ(√(d/K))`, strictly below the decoupled optimum `Θ(√d)` whenever `K = ω(1)`.

> **Claim 3 (the governing scalar, reconciling with the structural theory).** The crossover is
> governed by `η/L` with `K` as the effective count: conv-GAP succeeds (selects the robust solution,
> `R_2^I = Θ(√d)`) iff (a) the architecture *can* separate the base patterns invariantly
> (A-orbit-sep, so the achievable invariant Sep_inv > 0 with `K` decoupled features) **and** (b) the
> implicit bias actually decouples them, which it does **only when `K = O(1)`**; when `K = ω(1)`
> recurrence dominates and `η/L` collapses by `1/√K`. It **fails** (forced averaging, possibly even
> chance accuracy) under A-orbit-ent — a strict negative result (Thm II).

> **Claim 4 (decoupling rescue, mirroring Li Thm 4.7).** If the conv-GAP net is given *per-base*
> (fine-grained) labels, GF decouples the `K` invariant features and recovers `R_2^I = Θ(√d)`. So the
> conv-GAP non-robustness, like Frei/Li's, is a *supervision-granularity* phenomenon, not purely
> architectural.

The deliverable is therefore a **conditional / partial-positive + clean-negative** result: invariance
helps strictly more as the orbit grows, but is provably *not* a cure for feature-averaging, which it
relocates from the orbit to the within-class bases. This directly answers the prompt's "consider
seriously the possibility that it does NOT fully fix it."

---

## 3. FULL PROOF (quadratic conv-GAP exact; ReLU conv-GAP partial)

### 3.0 Shift-invariance and the orbit-tangent freebie (used everywhere)

**Lemma 0.** `φ_w^{relu}, φ_w^{sq}` are exactly shift-invariant, and any `N_I = Σ_r v_r φ_{w_r}`
satisfies `N_I(S_t x) = N_I(x)` for all `t`. Hence `N_I` is **perfectly robust along the orbit**:
for any `z ∈ O(x)`, the label is unchanged regardless of `‖x − z‖`. `[=]` (immediate; re-index;
matches attempt_1 Lemma 4.1 and bridging-symmetry-2025 Thm 1/2 orbit-invariance of the margin
gradient norm). **Consequence used below:** the only directions an attacker can exploit are
orbit-*transverse*; the orbit directions are removed from the attack budget for free, which is the
first half of why invariance helps.

### 3.1 The conv-GAP alignment-phase extremal vector (adapting Min-Vidal Lemma 1)

Min-Vidal Lemma 1 (their Eq. 5–6): in the small-init alignment phase, a neuron's *direction* obeys
```
   d/dt ( w/‖w‖ ) ≃ sign(v) · P^⊥_w · x_extr(w),   x_extr(w) = Σ_k γ_k(w) y_k x_k,    (3)
```
`γ_k(w) = 1[⟨x_k,w⟩>0]` for ReLU (p=1), `P^⊥_w = I − ww^T/‖w‖^2`. The *attractor set* is the set of
directions fixed by this flow; Min-Vidal show that for ReLU the attractor is the **class average**
`μ̄_± = (1/K_±)Σ μ_j` (non-robust), while pReLU (p≥3) re-points it to a **single subclass center**
(robust). Their conjecture: architecture can do the same re-pointing. We now compute the conv-GAP
analog of `x_extr` and show what it re-points to.

**Lemma 1 (conv-GAP-ReLU extremal vector = gated orbit average).** For the conv-GAP-ReLU feature (1),
the per-sample gradient w.r.t. the shared filter `w` is
```
   ∇_w φ_w^{relu}(x) = (1/d) Σ_s 1[⟨S_s w, x⟩ > 0] S_s^T x = (1/d) Σ_s 1[⟨w, S_{-s}x⟩>0] S_{-s} x
                     =: x̄(w),   the "gated orbit average" of x.                     (4)
```
Hence the conv-GAP extremal vector is `x_extr^{CG}(w) = Σ_k y_k x̄_k(w)` with
`x̄_k(w) = (1/d) Σ_s 1[⟨w, S_s x_k⟩>0] S_s x_k`. `[=]` (chain rule + re-index; `[V]` script
`extremal.py`: for broadly-active `w`, `x̄(w) → P x = mean(x)·1` = DC; for `w` tuned to one phase,
`x̄(w)` aligns to that orbit element with cos ≈ 0.57).

*Proof.* `φ_w^{relu}(x) = (1/d)Σ_s ReLU(⟨S_s w,x⟩+b)`; `∂/∂w ⟨S_s w,x⟩ = S_s^T x`; ReLU subgradient
is `1[·>0]`; sum. The second equality uses `⟨S_s w,x⟩ = ⟨w, S_s^T x⟩ = ⟨w, S_{-s}x⟩` and
`S_s^T = S_{-s}`. ∎

**Interpretation (the orbit-analog of class-averaging).** Compare (4) to the unconstrained gradient
`∇_w φ(⟨w,x⟩) = 1[⟨w,x⟩>0] x`. The weight-sharing has replaced the single atom `x` by the **gated
average over its orbit** `x̄(w)`. So the conv-GAP neuron, during alignment, is pulled not toward the
class average of *examples* but toward the class average of *orbit-averaged examples*. This is the
exact sense in which the architecture changes the attractor of (3).

### 3.2 The quadratic head: alignment **diagonalizes in frequency** (exact)

The ReLU gating makes (4) hard to integrate (the obstruction noted in §3.4). The **quadratic** head
(2) is exactly solvable, and it is the right object because the conv-GAP-quadratic family *spans the
power spectrum* (CONSOLIDATED span lemma), the established nonlinear invariant feature set.

**Theorem I (frequency-diagonal alignment of conv-GAP-quadratic; EXACT).**
Train `N_I(x) = Σ_r v_r φ_{w_r}^{sq}(x)`, `v_r = ±1` fixed, by gradient flow on the
exponential/logistic loss over (A-data). Write each filter in Fourier, `a_{r,k} := |ŵ_{r,k}|^2 ≥ 0`.
Then:

1. **(Diagonalization)** `φ_{w_r}^{sq}(x) = (1/d^2) Σ_k a_{r,k} |x̂_k|^2`. The network output is
   **linear in the power-spectrum coordinates** `Φ(x)_k := |x̂_k|^2`, with head weights
   `c_k := (1/d^2) Σ_r v_r a_{r,k}`. So conv-GAP-quadratic training is *exactly* a (nonnegatively
   reparameterized) linear classifier in PS-feature space. `[=]` (Parseval; `[V]`).

2. **(Per-frequency drive)** Under GF the filter Fourier energies evolve, in the alignment phase and
   to leading order, by the *separable* drive
   ```
       ȧ_{r,k} ∝ v_r · M_k · a_{r,k},     M_k := E_{(x,y)}[ y · |x̂_k|^2 ] = Σ_j (sign_j) ‖(μ̂_j)_k‖^2  (5)
   ```
   where `sign_j = +1` for `j ≤ K_+`. Each frequency coordinate evolves **independently** (no coupling
   across k); the data enter only through the scalar per-frequency drives `M_k`. `[H→V]` The
   independence is exact for the quadratic form: the single-filter gradient is, exactly (verified to
   1e-15 in the Fourier domain), `∇_w φ^{sq}_w(x) = (2/d) F^{-1}(|x̂|^2 ⊙ ŵ)`, i.e.
   `∂φ/∂ŵ_k ∝ |x̂_k|^2 ŵ_k`, which acts **coordinatewise on each Fourier mode `ŵ_k` with no cross-k
   coupling**; the multiplicative `a_{r,k}` factor is then the standard small-init alignment law
   (Li/Min-Vidal); `[V]` `extremal.py`, `orbit_gd.py`.

3. **(Averaging within the class — the recurrence)** Suppose A-orbit-sep: in-class base `j ≤ K_+`
   light frequencies in a set `F_+` (one or more frequencies each), `F_+ ∩ F_- = ∅`. Then `M_k > 0`
   for all `k ∈ F_+` and `M_k < 0` for all `k ∈ F_-`. By (5) **every positive filter (`v_r = +1`)
   grows on ALL of `F_+` simultaneously** (common positive drive), and decays on `F_-`. Therefore the
   trained positive head weight `c_k > 0` is spread across the entire in-class frequency support:
   the learned invariant feature is the **uniform average over the `K_+` base patterns' power
   spectra**, not a per-base detector. `[=]` from (5)'s sign structure; `[V]` `extremal.py`:
   `M = [+32,+31,+36,+36]` on pos freqs, `[−35,−74,−88,−74]` on neg freqs; `orbit_gd.py`:
   trained-filter single-frequency concentration = 0.55 (between fully-averaged 1/K = 0.25 and
   decoupled 1.0) → partial-but-present averaging.

4. **(Robustness consequence)** The averaged invariant classifier `f(x) = Σ_{k∈F_+} c|x̂_k|^2 −
   Σ_{k∈F_-} c|x̂_k|^2` evaluated at a clean point that is a *single* in-class base (lighting one
   `k_0 ∈ F_+`) has clean margin coming from one of the `|F_+|` lit coordinates only, while the
   attacker can pour energy into the cheapest negative coordinate. The min-norm flip is `Θ(√(d/K_+))`
   — exactly the Frei/Li `√(d/k)` law with `k = K_+`. `[≤]` upper bound by the explicit additive
   attack; `[≥]` lower bound by Lemma 0 (orbit directions free) + Cauchy-Schwarz on the lit subspace.
   This is `Θ(√K_+)` *better* than the unconstrained net (Claim 1, §3.3) but `Θ(√K_+)` *worse* than
   the decoupled optimum (Claim 2). ∎ (Theorem I).

**This is the precise, exact statement of the open problem's answer for the tractable head:** the
architecture diagonalizes the dynamics and divides out the orbit (point 1: only `|x̂_k|^2` survive,
the orbit is gone), but the within-class averaging (point 3) recurs by the *same* Frei/Li mechanism.

### 3.3 Why the unconstrained net is worse: orbit blow-up + phase cancellation

**Proposition (orbit blow-up of the effective cluster count).** On (A-data), the unconstrained ReLU
net sees each (base, phase) pair `S_s μ_j` as a distinct input direction. Two facts:

(a) **The naive class-average self-destructs on orbits.** The Frei/Li averaged neuron
`w̄_+ = (1/(K_+ |O|)) Σ_{j,s} S_s μ_j = (1/K_+)Σ_j P μ_j` collapses to the DC component of the base
means; for zero-DC (pure-AC) base patterns this is **exactly 0**. `[V]` `kkt_compare.py`:
`‖w̄_+‖ = 0.000` (phases cancel). So GF on the unconstrained net *cannot* settle on the simple class
average; it must retain per-phase/per-base structure, which spreads its neurons over `Θ(K·|O|)`
directions.

(b) **Hence `k_eff^U = Θ(K·d_orbit) ≫ k_eff^I = Θ(K)`.** Plugging into Frei `√(d/k_eff)`:
`R_2^U = Θ(√(d/(K d_orbit)))` vs `R_2^I = Θ(√(d/K))`, giving `R_2^I/R_2^U = Θ(√{d_orbit})`. `[H]`
the constant and the exact `k_eff^U` are heuristic (Frei's law is for orthogonal clusters; orbit
elements are not orthogonal, so this is an order-of-magnitude statement, flagged); the *direction and
monotonicity* are what the experiment confirms. `[V]` head-to-head `compare_robust.py`:
`R_2^I/R_2^U = 0.81, 1.03, 1.20, 1.60` for `K = 1,2,4,8` — rising with `K`, crossing 1 between K=1
and K=2, exactly the predicted monotone re-pointing.

**The key asymmetry (clean and decisive).** Input-space averaging is *killed* on orbits (phases
cancel, (a)); power-spectrum averaging *survives* (PS is phase-invariant; `[V]` averaged in-class PS
energy `= [512,512,512,512] ≠ 0`). So the architecture does two opposite-signed things at once: it
*removes* the orbit from the averaging count (helps, Claim 1) but *enables* a stable averaged
invariant feature over the bases that input-space training could not even form (hurts within-class,
Claim 2). The net effect is the conditional crossover of Claim 3.

### 3.4 The ReLU conv-GAP head: partial argument and where it breaks

For the ReLU head (1) the extremal vector (4) has the gating `1[⟨w, S_s x_k⟩>0]`, which couples the
filter direction to which orbit elements are active. Two regimes:

- **Broadly-active filters** (`⟨w, S_s x_k⟩ > 0` for most s): `x̄_k(w) → P x_k = ` DC of base k, and
  the extremal vector `→ Σ_k y_k (DC of μ_k)`. This is the *linear* invariant (DC) attractor of
  CONSOLIDATED Thm A — collapses to the DC gap, the worst (Ge single-dot) corner. So broadly-active
  conv-GAP-ReLU neurons reproduce the linear-invariant non-robustness. `[H→V]` (`extremal.py`,
  broad-w branch → DC).
- **Phase-tuned filters** (active on a sub-arc of the orbit): `x̄_k(w)` retains AC content aligned to
  the active phases; these are the neurons that can build a *nonlinear* invariant feature. Whether GF
  drives filters to the tuned or the broad regime is the **open dynamical question** for the ReLU head
  — it is the conv-GAP analog of Min-Vidal's "does GF reach the subclass-center attractor," which they
  also leave as a conjecture for pReLU. **I do not close this.** The quadratic head (Thm I) is exactly
  solvable precisely because it has no gating; it is the rigorous core, and it already exhibits the
  recurrence, so the negative conclusion (Claim 2) does *not* depend on resolving the ReLU gating.

**Honest status:** Theorem I (quadratic, exact) ⇒ Claims 2,3 rigorously; Claim 1 is order-of-magnitude
(Prop §3.3, `[V]` monotone); the ReLU head is partial (§3.4). This is a rigorous *partial* result
with the break clearly located.

### 3.5 The phase-blindness obstruction (a strict negative theorem)

**Theorem II (forced averaging under phase-coded signal).** Under A-orbit-ent (two base patterns with
identical power spectrum, distinct relative phase), the conv-GAP-quadratic net **cannot separate the
classes at all**: by Theorem I.1 its output depends only on `{|x̂_k|^2}`, which is identical for the
two bases, so `N_I` is constant across the phase-coded label and clean accuracy is `1/2`. `[=]`
(PS phase-blindness; `[V]` `negcase.py`: conv-GAP clean acc `= 0.50` vs unconstrained ReLU `= 0.57`).
Thus when the discriminative signal is carried by *phase* (a within-orbit, phase-sensitive feature),
architectural shift-invariance via conv-GAP-quadratic is not merely *non-robust*, it is *unable to
fit* — the architecture has thrown away the only discriminative feature. A phase-sensitive complete
invariant (bispectrum) could fit, but at uncontrolled Lipschitz/η-L cost (CONSOLIDATED §2 "phase
blind"), so the trade-off re-appears one level up. ∎

This is the cleanest negative: there exist distributions where the structural side *forbids* the
invariant family from realizing any large-η/L solution, so no implicit bias, re-pointed or not, can
save it.

---

## 4. KEY MECHANISM (one paragraph)

Weight-sharing replaces, in the alignment-phase ODE (Min-Vidal Eq. 3), each data atom `x_k` by its
**gated orbit average** `x̄_k(w)` (Lemma 1). For the quadratic head this makes the dynamics
**diagonal in frequency** (Theorem I): every frequency coordinate `|x̂_k|^2` evolves independently
under a scalar drive `M_k = Σ_i y_i |x̂_{i,k}|^2`. The orbit, which blew the unconstrained net's
effective cluster count up to `K·d_orbit` (and whose naive average self-destructs by phase
cancellation, §3.3), is **divided out** — only the `K` base patterns remain. But over those `K` bases
the drive `M_k` has a **common sign within each class**, so a single filter grows on all same-class
invariant features at once: this is *literally* the Frei/Li uniform-sign feature-averaging mechanism,
relocated from input space to power-spectrum space. Hence invariance turns the non-robustness knob
from `√(d/(K d_orbit))` to `√(d/K)` — better by `√{d_orbit}`, but still short of the decoupled
`√d` by `√K`. Architecture re-points the bias; it does not eliminate the bias.

---

## 5. WHEN SUCCEEDS vs FAILS (vs η/L)

Let `Sep_inv` be the achievable invariant (PS-feature) class separation and `L` the conv-GAP
Lipschitz constant; the consolidated master scalar is `η/L = Sep_inv/L`. The optimization outcome:

| regime | architecture can fit? | implicit bias decouples? | `R_2^I` | verdict |
|---|---|---|---|---|
| A-orbit-sep, `K = O(1)` | yes (disjoint PS) | yes (few bases, drive separates) | `Θ(√d)` | **SUCCEEDS**: invariance + GD reaches robust large-η/L solution |
| A-orbit-sep, `K = ω(1)` | yes | **no** (Thm I.3 recurrence) | `Θ(√(d/K))` | **PARTIAL**: better than U by `√{d_orbit}`, worse than optimum by `√K` |
| A-orbit-ent (phase-coded) | **no** (Thm II) | n/a | acc 1/2 | **FAILS structurally**: η/L not realizable in the family |
| fine-grained per-base labels | yes | yes (Claim 4 / Li Thm 4.7) | `Θ(√d)` | **RESCUED** by supervision, not by architecture alone |

So success is governed by `η/L` with effective count `K`: invariance helps **monotonically in the
orbit size `d_orbit`** (always, Claim 1) but the *residual* gap to the optimum is set by the
**within-class base multiplicity `K`** and by whether the signal is PS-coded (succeeds) or phase-coded
(fails). The dividing line is *not* "invariance yes/no"; it is the same `Sep_inv/L` of the structural
theory, now with `K` (not Frei's raw `k`) as the count, because the architecture has divided out the
orbit. This is the precise sense in which the optimization story and the structural story compose.

**Relation to large vs small η/L (Kamath-like O(1/√d)).** When `K = Θ(1)` and bases are PS-separated,
`Sep_inv = Θ(1)`, `L = Θ(1)` ⇒ `η/L = Θ(1)` ⇒ robust (`R_2 = Θ(√d)·` in the rescaled units).
When `K = ω(1)`, the averaged feature's per-example margin scales as `1/K` (only one of `K` coords
lit) while `L` does not shrink commensurately under the *attack* direction (the attacker uses the full
in-class subspace), so `η/L = Θ(1/√K)` — the Kamath small-η/L corner, reached *by the implicit bias*
rather than imposed by augmentation. The conv-GAP net thus realizes "Sep_inv > 0 but η/L small," the
exact corrected criterion of CONSOLIDATED §3.

---

## 6. RELATION to Frei / Min-Vidal / Li (precise, no fabrication)

- **Frei et al. (2023), Thm 4.1/4.2.** Their robust net (4.1) puts one neuron per cluster
  (decoupled); their Thm 4.2 shows every KKT point is non-`√d`-robust because positive neurons have
  large components in **all `k` positive clusters**, so the universal perturbation
  `z = η Σ_j y^{(j)}μ^{(j)}` flips with `‖z‖ = O(√(d/k))`. **My Theorem I is the conv-GAP analog**:
  the per-frequency drive `M_k` having common in-class sign is exactly "positive neurons load on all
  positive clusters," now over base-pattern *power spectra*. The difference: the conv-GAP `z` lives in
  the lit-frequency subspace and the orbit directions are excluded from it (Lemma 0), so the effective
  `k` is `K` not `K·d_orbit`. I do **not** claim conv-GAP escapes Frei; I claim it *shrinks Frei's k*
  to the within-class count and leaves the rest of his theorem intact.

- **Min & Vidal (2024), Conjecture 1 + Lemma 1/Thm 2.** They show ReLU (p=1) alignment attracts
  neurons to the **class average** `μ̄_±` (their Thm 2, `d/dt cos(w,μ̄_+) > 0` for p=1), and conjecture
  architecture (pReLU, p≥3) re-points to subclass centers. **My Lemma 1 computes their `x_extr` for
  the conv-GAP architecture** (the suggested architectural re-pointing): it is the *gated orbit
  average*, and for the quadratic head it re-points the attractor from "average of examples" to
  "average of base-pattern power spectra." So conv-GAP is *a partial realization of their conjecture*:
  it re-points away from the orbit-blown-up class average (helps) but the attractor is still an
  *average over bases* (their conjecture asked for full subclass-center decoupling, which conv-GAP
  achieves only for `K = O(1)` or with fine-grained labels). I confirm their conjecture's *spirit*
  (architecture re-points bias) while showing its *limit* (re-pointing is partial; recurrence). Their
  pReLU and my conv-GAP are different re-pointings; pReLU sharpens the *angular* selectivity, conv-GAP
  removes the *orbit* — complementary.

- **Li et al. (2024), Thm 4.5 + 4.7.** Their feature-averaging `w_{s,r} → λ Σ_{j∈J_s}‖μ_j‖^{-2}μ_j`
  (average over the **whole superclass** `J_s`) is exactly my Theorem I.3 with `J_s = F_±` the
  in-class frequency set; their non-robust `Ω(√(d/k))` is my `Θ(√(d/K))`. Their Thm 4.7 (fine-grained
  per-cluster labels ⇒ decoupling ⇒ `O(√d)` robust) is my Claim 4: per-base labels make the drive
  `M_k` class-separated *and* base-separated, so each filter decouples. **My contribution over Li:**
  the orbit-division (Claim 1, the `√{d_orbit}` factor that pure Li does not have, because Li has no
  group action) and the phase-blindness negative (Thm II, which has no analog in Li because Li's
  features are not invariants). So conv-GAP = Li's feature-averaging *modulo the orbit*, with one new
  helping factor (orbit division) and one new failure mode (phase blindness).

- **Melamed et al. (2023).** Off-manifold gradient: trained nets have large gradient orthogonal to the
  low-dim data subspace. Lemma 0 says conv-GAP has *zero* gradient along the orbit tangent (the
  highest-frequency aliasing directions) — it removes Melamed's off-manifold directions that coincide
  with the orbit, *for free*, consistent with their "smaller init / L2 shrinks off-manifold grad
  without touching the data fit." The *residual* off-orbit, in-frequency-support vulnerability is the
  `√(d/K)` averaging gap of Thm I, which Melamed's init/L2 knobs do **not** fix (it is a margin
  problem, not a gradient-magnitude problem) — a clean decoupling of the two non-robustness sources.

---

## 7. OBSTRUCTIONS (honest)

1. **ReLU conv-GAP gating unresolved (§3.4).** The exact result is for the *quadratic* head. The ReLU
   head's alignment ODE (Lemma 1) has activation gating that couples filter direction to active orbit
   phases; whether GF drives filters to the broad (DC, worst) or phase-tuned (nonlinear-invariant)
   regime is the open dynamical question — the direct analog of Min-Vidal's own unresolved pReLU
   conjecture. The negative conclusion (Claim 2) survives because it is proved on the quadratic head,
   but a *full* characterization of the ReLU conv-GAP trained net is open.

2. **`k_eff^U = Θ(K·d_orbit)` is order-of-magnitude (§3.3).** Frei's `√(d/k)` is derived for nearly
   *orthogonal* clusters; orbit elements `S_s μ_j` are highly correlated (autocorrelation of `μ_j`),
   so the literal count is not `K·d_orbit`. The rigorous content is: (a) the naive average is 0
   (exact, phase cancellation, `[V]`), forcing the unconstrained net off pure averaging; (b) the
   monotone advantage `R_2^I/R_2^U` rising in `K` (`[V]`). The constant in `√{d_orbit}` is not pinned.

3. **Alignment-phase law (5) is leading-order.** Equation (5) is the standard small-init alignment
   approximation (Li, Min-Vidal, Boursier-Flammarion); the late fitting phase and finite init scale
   add corrections. For the quadratic head the *diagonalization* (Thm I.1) is exact at all times (it is
   an algebraic identity, not a dynamical approximation); only the *which-frequencies-win* rate (5) is
   leading-order. The qualitative recurrence (common in-class sign ⇒ averaging) is robust to this.

4. **Margin/Lipschitz bookkeeping for `R_2 = Θ(√(d/K))`.** The upper bound (explicit attack) is solid;
   the matching lower bound uses Lemma 0 (orbit free) + a Cauchy-Schwarz on the lit subspace and a
   "single base lit per clean point" assumption. For clean points that are *mixtures* of bases the
   constant changes; I state the result for single-base clean points (the natural test points of
   A-data) and flag the mixture case as not fully worked.

5. **Phase-blindness escape via bispectrum (Thm II).** Thm II is a negative for the *quadratic / PS*
   family. A bispectrum-based conv-GAP could fit phase-coded signal, but its Lipschitz budget is
   uncontrolled (cubic), so I cannot claim the trade-off is *resolved* there — only relocated. This is
   the same boundary the structural theory hits (CONSOLIDATED §2 "phase blind").

6. **2-D, real CNNs, multi-class.** All proofs are 1-D circular, binary, exact-invariance. Real CNNs
   (zero pad, stride) are only approximately invariant; the *predictions* are robust to this but the
   exact constants are not (same caveat as attempt_1 §7.6).

---

## 8. EMPIRICAL PREDICTIONS (falsifiable; the headline ones are already `[V]` here)

- **EP1 (headline, the K-sweep — VERIFIED here).** On (A-data) sweep the within-class base
  multiplicity `K`. Predict `R_2^I/R_2^U` is **monotone increasing in `K`**, crossing 1 near `K=1→2`,
  with `R_2^I/R_2^U → Θ(√{d_orbit})·(1/√K)`-shaped envelope. `[V]` 0.81, 1.03, 1.20, 1.60 for
  `K = 1,2,4,8` at `d=48`. *Re-run on MNIST/FMNIST by synthesizing orbit-clusters (rotate-class
  digits into cyclic-shift classes) to test at scale.*

- **EP2 (filter decoupling probe — VERIFIED here).** Measure the single-frequency concentration of
  trained conv-GAP filters' power spectra. Predict it sits **strictly between** `1/K` (fully averaged)
  and `1` (decoupled), and **decreases toward `1/K` as `K` grows** (recurrence strengthens). `[V]`
  concentration 0.55 at `K=4` (vs 1/K=0.25). *Sweep `K` to confirm the decrease.*

- **EP3 (phase-blindness negative — VERIFIED here).** Construct A-orbit-ent data (same PS, opposite
  relative phase between classes). Predict conv-GAP-quadratic clean accuracy `→ 1/2` while an
  unconstrained ReLU net (and a bispectrum/phase-sensitive head) fits. `[V]` 0.50 vs 0.57. *Test that
  a depth-≥3 conv net (which can access phase via products of conv layers) recovers accuracy, locating
  exactly where the quadratic-PS ceiling is escaped.*

- **EP4 (orbit-division factor).** Vary the orbit size `d_orbit` by restricting the shift subgroup
  `H ≤ Z_d` the data respects (sample phases only from `H`). Predict `R_2^I/R_2^U` scales as
  `√{|H|}` — directly isolating the orbit-division mechanism of Claim 1.

- **EP5 (fine-grained rescue — Li Thm 4.7 analog).** Train conv-GAP with per-base labels. Predict
  filter concentration `→ 1` and `R_2^I → Θ(√d)` (decoupled). This separates "architecture re-points
  bias" from "supervision granularity fixes the residual," confirming the conv-GAP non-robustness is
  the *same supervision phenomenon* as Frei/Li.

- **EP6 (η/L is the predictor, not invariance).** Across the rows of the §5 table, regress measured
  `R_2^I` on (i) is-invariant (binary), (ii) shift-consistency, (iii) `Sep_inv/L` with count `K`.
  Predict (iii) wins (highest R²) — the master scalar governs, invariance per se does not. (This is
  CONSOLIDATED P1/P6 carried into the trained-net regime.)

- **EP7 (Melamed decoupling).** Add small-init / L2; predict the *orbit-tangent* gradient stays ~0
  (Lemma 0, untouched) and the *off-orbit in-support* averaging gap `√(d/K)` is **not** closed by
  init/L2 (it is a margin, not a gradient-norm, problem) — distinguishing the two non-robustness
  sources experimentally.

---

## Summary (one paragraph)

Hard-wired shift-invariance (conv-GAP) does **not** fully fix gradient descent's non-robust implicit
bias; it **re-points it partially**, by a mechanism we pin down exactly for the quadratic head. Weight
-sharing replaces each data atom in the Min-Vidal alignment dynamics by its gated orbit average
(Lemma 1); for the quadratic conv-GAP head the dynamics **diagonalize in frequency** (Theorem I), so
the orbit is divided out of the Frei/Li feature-averaging count — the effective cluster number drops
from `K·d_orbit` (unconstrained, with its class-average self-destructing by phase cancellation) to
`K` (within-class base patterns). But over those `K` bases, the per-frequency drive `M_k` has a common
in-class sign, so feature-averaging **recurs inside the invariant family** by the identical Frei/Li
uniform-sign mechanism, giving `R_2^I = Θ(√(d/K))`: better than the unconstrained `Θ(√(d/(K d_orbit)))`
by `√{d_orbit}` (verified: ratio 0.81→1.60 as `K`:1→8), but short of the decoupled optimum `Θ(√d)` by
`√K`. The governing scalar is the consolidated `Sep_inv/L = η/L` with `K` as the count — invariance
helps monotonically in orbit size but the residual gap is set by within-class multiplicity. Two honest
limits: a strict **phase-blindness negative** (Theorem II: when class signal is phase-coded, conv-GAP-
quadratic cannot even fit, accuracy 1/2), and the **ReLU-head gating** (unresolved, the analog of
Min-Vidal's own open pReLU conjecture). Fine-grained per-base labels rescue decoupling (Li Thm 4.7
analog), confirming this is a supervision-granularity phenomenon relocated by the architecture, not a
cure effected by it.
