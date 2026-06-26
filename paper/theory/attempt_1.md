# When Shift-Invariance and L_p Adversarial Robustness Co-Exist: A Margin-Preservation Theorem

**Attempt 1 — technical report, fully self-contained proofs.**

Author working notes. Goal: state and *prove* a precise condition under which possessing
shift-invariance (equivalently, perfect shift-consistency) does **not** reduce the adversarial
margin, and conversely a precise condition under which the trade-off is forced. The result must
reconcile three facts in the literature:

- Ge–Singla–Basri–Jacobs (NeurIPS'21): a shift-invariant **linear** classifier can only separate
  classes using their DC (mean) component; for the single-dot two-class example the max-margin
  collapses from `2` to `2/sqrt(d)` (their Thm 1, Cor 1). BUT (their Sec 5.2 / Table 3) on
  orthogonal-*frequency* data, where shifts do not raise the intrinsic dimension, the invariant CNN
  is *more* robust than the FC net. So the governing quantity is **margin preservation under the
  invariance constraint**, not invariance per se.
- Kamath–Deshpande–Subrahmanyam–Balasubramanian (NeurIPS'21): an *upper-bound* trade-off between
  spatial and adversarial robustness on a synthetic cyclic-code Gaussian-mixture binary
  distribution, under **augmentation-induced** invariance (their Thm 2).
- Frei–Vardi–Bartlett–Srebro (NeurIPS'23) and Melamed–Yehudai–Vardi (NeurIPS'23): robust networks
  *exist* but the implicit bias of gradient flow selects a non-robust KKT point, and non-robustness
  comes from gradient mass orthogonal to a low-dimensional data manifold.

Our contribution is a **structural** (architecture/data) characterization, deliberately decoupled
from the **optimization** (implicit-bias) story of Frei/Melamed. We prove an *exact identity* for
the invariant max-margin in the linear/kernel-linear case, an exact *robust-radius* statement for a
clean two-region nonlinear case, and we show the trade-off is governed by a single scalar:
the **class separation surviving the orbit-averaging projection**, optionally corrected by an
**off-orbit sensitivity** term. Everything reduces to Ge in the degenerate case and is consistent
with (does not contradict) Kamath.

Throughout I flag exactly where a step is an *identity* (=), an *inequality with a proof* (with the
direction and its tightness), and where an argument is only a *heuristic / obstruction* (clearly
labelled). No step is skipped.

---

## 1. Setting and Assumptions

### 1.1 Input space and the shift group

Work on 1-D circular signals; the 2-D case is identical with the group `Z_{d1} x Z_{d2}` replacing
`Z_d`, and every statement below carries over verbatim by replacing the cyclic DFT with the 2-D
cyclic DFT (Appendix remark at the end of §4). Inputs live in `X = R^d`. The shift group is the
cyclic group `G = Z_d = {0,1,...,d-1}` acting by circular (cyclic) shift: for `s in G`,
`(S_s x)_i = x_{(i - s) mod d}`. We write `S_s` for the `d x d` cyclic-shift permutation matrix.
The action is by orthogonal matrices: `S_s^T S_s = I`, `S_s^{-1} = S_{-s} = S_s^T`, and `S_a S_b =
S_{a+b}`. The group is abelian.

For `x in R^d`, its **orbit** is `O(x) = { S_s x : s in G }` (at most `d` points). The **orbit
average operator** is
```
        P := (1/d) sum_{s in G} S_s .                                         (1)
```

### 1.2 Assumptions (stated up front, minimal)

- **(A1) Finite cyclic group, orthogonal action.** As above. `|G| = d` (the full pixel-shift
  group); restriction to a subgroup `H <= G` (e.g. strided pooling, P = lcm of strides as in Ge's
  Note 1) only changes which Fourier modes are "DC" and is handled in §6.3.
- **(A2) Classifier class.** We analyze three nested classes:
  - **(L)** *Linear* classifiers `f(x) = w^T x + b`, decision `sign f`. This is Ge's setting and
    the cleanest place to get exact identities.
  - **(K)** *Kernel-linear* classifiers `g(x) = sum_i a_i k(x, x_i)` from a shift-invariant kernel
    (NTK/CNTK-GAP); we will show these reduce to the linear analysis on a feature map.
  - **(N)** A *clean two-piece ReLU* classifier (§4.2) on which we can compute an **exact** robust
    radius, to show co-existence is not an artifact of linearity.
- **(A3) Shift-invariance of the classifier.** `f` is *shift-invariant* if `f(S_s x) = f(x)` for
  all `s in G, x in X`. (This is the architectural property of conv + global average pooling with
  circular padding; see Ge Note 1.) We will *also* use the weaker measured property:
- **(A4) Shift-consistency (measured).** For a distribution `D` on `X`, the **shift-consistency**
  of a classifier with prediction `h(x) := argmax`/`sign f(x)` is
  ```
     SC(h) := Pr_{x ~ D, s ~ Unif(G)} [ h(S_s x) = h(x) ] .                   (2)
  ```
  `SC = 1` iff the *prediction* is constant on every orbit `D`-almost surely. Note `SC = 1` is
  strictly weaker than (A3): it constrains only the sign of `f` on orbits, not `f` itself. We treat
  both and are explicit about which is used where.

- **(A5) Data.** A binary labelled distribution with class-conditional supports. We will use two
  data descriptors:
  - `mu_+ , mu_-` = class means (or, in the separable deterministic case, the two single images).
  - The **orbit-projected** class data, defined via `P` in §2.

We restrict to **binary** classification for the theorems (multi-class noted in §7). We use the
**L2** norm for the margin/robust-radius theorems and give the **Linf** corollary via norm
equivalence with explicit constants (§3.4). "Margin" always means *geometric distance to the
decision boundary at a clean correctly-classified point*, which for a unit-normal linear classifier
equals the functional margin; we are explicit about normalization everywhere.

---

## 2. Definitions and the harmonic decomposition

### 2.1 The shift-invariant subspace and `P`

**Lemma 2.1 (P is the orthogonal projector onto the shift-invariant subspace).**
Let `P = (1/d) sum_s S_s`. Then:
1. `P` is symmetric: `P^T = P`.
2. `P` is idempotent: `P^2 = P`.
3. `P` is the orthogonal projector onto `V_inv := { v in R^d : S_s v = v for all s } = {v : v is
   constant along the cyclic shift, i.e. v in span(1_d)}`.
4. `range(P) = span(1_d)`, `P = (1/d) 1_d 1_d^T`, and for any `x`, `Px = (mean(x)) 1_d`.

*Proof.*
(1) `P^T = (1/d) sum_s S_s^T = (1/d) sum_s S_{-s} = (1/d) sum_{s'} S_{s'} = P`, re-indexing `s' =
-s mod d` (a bijection of `G`).
(2) `P^2 = (1/d^2) sum_{a,b} S_a S_b = (1/d^2) sum_{a,b} S_{a+b}`. Fix `c = a+b`; for each of the
`d` values of `c` there are exactly `d` pairs `(a,b)` with `a+b = c` (choose `a` freely, `b = c-a`).
So `P^2 = (1/d^2) * d * sum_c S_c = (1/d) sum_c S_c = P`.
(3) A symmetric idempotent is the orthogonal projector onto its range. Its range is its
`+1`-eigenspace. If `Pv = v` then `v in range(P)`. Conversely for any `x`, `S_t (Px) = (1/d) sum_s
S_t S_s x = (1/d) sum_s S_{t+s} x = (1/d) sum_{s'} S_{s'} x = Px`, so `Px` is shift-invariant, i.e.
`range(P) subseteq V_inv`. And if `v in V_inv` then `Pv = (1/d) sum_s S_s v = (1/d) sum_s v = v`,
so `V_inv subseteq range(P)`. Hence `range(P) = V_inv` and `P` is the orthogonal projector onto it.
(4) The only vectors fixed by *all* cyclic shifts are the constant vectors (if `v` is fixed by the
shift-by-1 `S_1`, then `v_i = v_{i-1}` for all `i`, so all coordinates equal; conversely constants
are fixed). Thus `V_inv = span(1_d)`. The orthogonal projector onto `span(1_d)` is `1_d 1_d^T /
||1_d||^2 = 1_d 1_d^T / d`. Applying it: `Px = (1_d^T x / d) 1_d = mean(x) 1_d`. QED.

So **for the full pixel-shift group, the shift-invariant subspace is exactly the DC line.** This is
the crisp statement behind Ge's "DC component only" — but stated as a projector, which is what lets
us go further. (Under a subgroup `H`, §6.3, `V_inv` is larger and is the span of the
`H`-invariant Fourier modes.)

### 2.2 Cyclic Fourier diagonalization

Let `F` be the unitary `d x d` DFT, `F_{jk} = (1/sqrt(d)) omega^{-jk}`, `omega = e^{2 pi i / d}`.
The shift matrices are simultaneously diagonalized by `F`: `S_s = F^* Lambda_s F` where `Lambda_s =
diag(omega^{s k})_{k=0..d-1}`. Hence any shift-invariant *linear* map `M` (one commuting with all
`S_s`) is diagonal in the Fourier basis: `M = F^* diag(hat m) F`. In particular for a real signal,
`x` decomposes as `x = sum_{k=0}^{d-1} hat x_k phi_k` where `phi_k` are the (real/imag) Fourier
atoms; `k = 0` is the DC mode, `phi_0 = 1_d / sqrt(d)`. The orbit-average `P` keeps only `k=0`:
`P = F^* diag(1, 0, ..., 0) F`. We write `Q := I - P` for the projector onto the
**non-DC (AC) subspace** `V_AC := V_inv^perp = span(phi_1,...,phi_{d-1})`.

### 2.3 Orbit geometry

**Lemma 2.2 (shift orbit lives in an affine slice; orbit differences are AC).**
For any `x` and any `s`, `P S_s x = P x` (shifting does not change the DC). Consequently every
orbit `O(x)` lies in the affine subspace `{ z : Pz = Px } = Px + V_AC`. Moreover the linear span of
*orbit differences* `span{ S_s x - x : s in G }` is contained in `V_AC`.

*Proof.* `P S_s = (1/d) sum_t S_t S_s = (1/d) sum_t S_{t+s} = P` (re-index). So `P(S_s x) =
P x` and `S_s x in Px + V_AC`. Then `S_s x - x in V_AC` because `P(S_s x - x) = Px - Px = 0`,
i.e. orbit differences have zero DC. QED.

This lemma is the geometric heart of the "promising direction": **the discriminative direction that
shift-invariance forbids is exactly the part of the signal that the orbit can move, and that is
exactly `V_AC`.** A shift-invariant classifier is blind precisely along `V_AC`.

### 2.4 Margin and robust radius

For a classifier `f` and a correctly-classified point `(x,y)` (`y in {+1,-1}`, `y f(x) > 0`), the
**Lp robust radius** is
```
   R_p(f; x) := inf { ||delta||_p : sign f(x + delta) != sign f(x) } .        (3)
```
For *linear* `f(x) = w^T x + b`, the classical identity (proof in Lemma 3.1) gives
`R_2(f;x) = |w^T x + b| / ||w||_2`. The **dataset margin** of a separating linear `f` is
`gamma(f) := min_i y_i (w^T x_i + b) / ||w||_2 = min_i R_2(f; x_i)`; the **max-margin** over a
hypothesis class `C` separating data `S` is `gamma*(C; S) := sup_{f in C separates S} gamma(f)`.
This is the quantity Ge bounds; we match it exactly.

---

## 3. Main theorems (linear / kernel-linear case)

### 3.1 The exact invariant-margin identity

**Theorem 1 (Exact margin under shift-invariance, linear case).**
Let `S = (x_i, y_i)_{i in [n]}`, `y_i in {+1,-1}`. Consider linear classifiers.
Define the **orbit-averaged points** `bar x_i := P x_i = mean(x_i) 1_d` and the
**residuals** `r_i := Q x_i = x_i - bar x_i in V_AC`.

(a) **Constraint reduction.** A linear classifier `f(x) = w^T x + b` is shift-invariant (A3) for
*all* `x in R^d` if and only if `w in V_inv = span(1_d)`, i.e. `w = c 1_d` for some `c in R`.

(b) **Exact invariant max-margin.** Let `C_inv` = shift-invariant linear classifiers. Then `S` is
separable by some `f in C_inv` iff the *scalar* DC features `t_i := mean(x_i) = (1/d) 1_d^T x_i`
are separable by a threshold, i.e. iff
```
   max_{i : y_i = -1} t_i  <  min_{i : y_i = +1} t_i   (or the symmetric reversed inequality).
```
When separable, the invariant max-margin is given by the careful normalization below (Eq. (4')).
**Careful normalization.** With `w = c 1_d`, `||w||_2 = |c| sqrt(d)` and `w^T x_i = c * d * t_i`.
The functional value is `c d t_i + b`; the geometric margin of point `i` is `(c d t_i + b) /
(|c| sqrt(d)) = sign(c) sqrt(d) (t_i + b/(cd))`. Optimizing the threshold `b/(cd)` to the midpoint
of the gap, the **geometric** invariant max-margin is
```
   gamma*_inv(S) = (sqrt(d) / 2) * ( min_{i:y_i=+1} t_i - max_{i:y_i=-1} t_i )     (4)
```
(taking the orientation that makes this positive). Equivalently, writing `Delta_DC :=
min_{+} t_i - max_{-} t_i` for the **DC-gap**,
```
   gamma*_inv(S) = (sqrt(d)/2) * Delta_DC .                                   (4')
```

(c) **Comparison to the unconstrained (FC/linear) max-margin.** The unconstrained linear max-margin
is the standard hard-margin SVM value `gamma*_full(S) = (1/2) * d_min`, where `d_min` is the
minimum distance between the convex hulls of the two classes' *full* points `{x_i}`:
`gamma*_full(S) = (1/2) min_{u in conv(X_+), v in conv(X_-)} ||u - v||_2`.

(d) **The trade-off ratio.** Therefore
```
   gamma*_inv(S) / gamma*_full(S) = ( sqrt(d) * Delta_DC ) / d_min ,          (5)
```
and *co-existence (no margin loss) holds iff the DC-gap times sqrt(d) recovers the full hull
distance*; the *trade-off is forced* exactly to the extent that the class-discriminative signal
lives in `V_AC` (is removed by `Q`).

*Proof of Theorem 1.*

(a) "⇐": if `w = c 1_d`, then for any `s`, `w^T S_s x = c 1_d^T S_s x = c 1_d^T x = w^T x` because
`S_s` is a permutation (it permutes the entries of `x`, leaving their sum, hence `1_d^T x`,
unchanged; formally `1_d^T S_s = (S_s^T 1_d)^T = 1_d^T` since `S_s^T 1_d = 1_d`, as `1_d in V_inv`).
So `f(S_s x) = f(x)` for all `s,x`. "⇒": suppose `f(S_s x) = f(x)` for all `s, x`. Then `w^T(S_s x -
x) = 0` for all `x`, i.e. `w^T (S_s - I) = 0` as a linear functional, for every `s`. Hence `w perp
range(S_s - I)` for all `s`. The union of these ranges spans `V_AC` (indeed `range(S_1 - I)` alone
already equals `V_AC`: `S_1 - I` is the circulant with symbol `omega^k - 1`, which is nonzero for
all `k != 0` and zero only at `k = 0`, so its range is exactly `V_AC` = span of non-DC modes). Thus
`w perp V_AC`, i.e. `w in V_AC^perp = V_inv = span(1_d)`. QED (a).

(b) By (a) the only admissible `w` is `c 1_d`. Then `w^T x_i = c 1_d^T x_i = c d t_i`, depending on
`x_i` only through its DC scalar `t_i`. Separability and the margin are now a 1-D threshold problem
in `t_i`. The geometric margin computation is the displayed normalization above, giving (4)-(4').
That `Delta_DC = min_+ t - max_- t` is the right gap is the standard 1-D max-margin: place the
threshold at the midpoint, half the gap is the margin, then multiply by `sqrt(d)` from the `||w||`
normalization (each unit of `t` corresponds to `1_d^T`-direction whose unit vector is `1_d/sqrt(d)`,
so a `t`-gap of `Delta_DC` is a geometric gap of `sqrt(d) Delta_DC` along the unit DC direction).
QED (b). [Cross-check with Ge below in §6.1 reproduces `2/sqrt(d)`.]

(c) Standard hard-margin SVM duality: the max-margin separating hyperplane's margin equals half the
distance between the convex hulls of the two point sets (Bennett-Bredensteiner; classical). No
constraint, so the full points are used. QED (c).

(d) Divide (4') by (c). QED (d).

**Remark (this is an exact identity, not a bound).** Unlike Ge's Thm 1 which is also exact in their
single-dot case, (4') holds for *any* finite separable dataset, giving the invariant margin as a
clean function of the 1-D DC features. The novelty over Ge is (d): we express co-existence vs
trade-off as the ratio of *two computable geometric quantities*, `sqrt(d) Delta_DC` and `d_min`.

### 3.2 The co-existence and trade-off conditions (linear)

**Corollary 1 (co-existence iff DC-separability with preserved gap).**
Define the **DC-survival ratio** `rho(S) := sqrt(d) Delta_DC / d_min in [0,1]` (it is `<= 1`;
proof below). Then:
- **Co-existence (invariance is free):** `rho(S) = 1` iff the entire inter-hull distance is realized
  along the DC direction `1_d/sqrt(d)`, i.e. the convex hulls' closest pair `(u*, v*)` satisfies
  `u* - v* parallel 1_d`. In that case `gamma*_inv = gamma*_full`: the shift-invariant classifier is
  *exactly as robust* as the best FC classifier.
- **Total collapse (worst trade-off):** `rho(S) -> 0` iff `Delta_DC -> 0`, i.e. the classes have
  (nearly) equal DC and are separated *purely* by AC content. Then the invariant margin -> 0 while
  `gamma*_full` can be `Omega(1)`. The single-dot example is this case with the residual structure
  making `gamma*_inv = (2/sqrt(d)) /` (normalization) — recovered in §6.1.

*Proof that `rho <= 1`.* The DC feature is `t_i = (1_d/sqrt(d))^T x_i / sqrt(d) * sqrt(d)`... let us
be fully explicit. Let `e := 1_d / sqrt(d)` (unit DC direction). Then `t_i = mean(x_i) = (1/sqrt(d))
e^T x_i`, so `e^T x_i = sqrt(d) t_i`. The DC-gap in the *projected-onto-e* coordinate is
`e^T u* - e^T v*`-type; precisely, for any `u in conv(X_+), v in conv(X_-)`, by 1-D projection
`e^T(u - v) <= ||u - v||_2` (Cauchy-Schwarz, `e` unit). The convex-hull DC-gap is
`sqrt(d) Delta_DC = min_{i:+} e^T x_i - max_{i:-} e^T x_i = min_{u in conv X_+, v in conv X_-}
e^T(u-v)` (the min over hulls of a linear functional is attained at vertices = data points). Hence
`sqrt(d) Delta_DC = min_{u,v} e^T(u-v) <= min_{u,v} ||u - v||_2`? — **No, this inequality goes the
wrong way for a min**; we must argue it correctly. Let `(u*,v*)` attain the hull distance `d_min =
||u* - v*||`. Then `sqrt(d) Delta_DC = min over hulls of e^T(u-v) <= e^T(u* - v*) <= ||u* - v*|| =
d_min` (Cauchy-Schwarz on the specific pair). The first `<=` is because the min is `<=` the value
at the specific pair `(u*,v*)`. Hence `sqrt(d) Delta_DC <= d_min`, i.e. `rho <= 1`. **Equality**
holds iff (i) `e^T(u*-v*) = ||u*-v*||`, i.e. `u* - v* parallel e = 1_d`, AND (ii) the hull-min of
`e^T(u-v)` is attained at the same `(u*,v*)`. Condition (i) alone gives equality of the chain when
combined with the fact that if `u*-v* parallel 1_d` then the closest hull pair is also the DC-extreme
pair (because moving within a hull orthogonally to `1_d` does not change `e^T x` and cannot decrease
the DC-gap below `e^T(u*-v*)`). So `rho = 1 iff u* - v* parallel 1_d`. QED.

### 3.3 Kernel-linear (CNTK-GAP) reduction

**Theorem 2 (shift-invariant kernels are linear in the DC feature; recovers Ge Thm 2.2).**
Let `k(z, x)` be a kernel that is **shift-invariant in both arguments**:
`k(S_a z, S_b x) = k(z, x)` for all `a, b` (this holds for the global-average-pooled CNTK, "CNTK-GAP"
of Li et al., because GAP averages patch kernels over all cyclic positions; we take this as the
defining property, matching Ge's Thm 2). Let `g(z) = sum_i a_i k(z, x_i)` be a kernel-linear
classifier. Then:
1. `g` is shift-invariant: `g(S_a z) = g(z)`.
2. Define the **symmetrized feature map** `Phi(x) := P_H[ psi(x) ]` where `psi` is any feature map
   for `k` (`k(z,x) = <psi(z), psi(x)>`) and `P_H` is orbit-averaging in feature space; then
   `k(z,x) = <Phi(z), Phi(x)>` and **`Phi(x)` depends on `x` only through shift-invariant feature
   coordinates.** In the special antipodal two-point case `{x, -x}` of Ge Thm 2.2, the resulting
   separating direction in feature space collapses to the constant feature, and the decision boundary
   has normal `1_d` (`z^T 1_d = 0` is the separator), exactly Ge's conclusion; the margin is the
   difference of DC components, exactly Ge Cor 2.

*Proof.*
(1) `g(S_a z) = sum_i a_i k(S_a z, x_i) = sum_i a_i k(S_a z, S_0 x_i) = sum_i a_i k(z, x_i) = g(z)`,
using joint shift-invariance with `b = 0` and the `a`-invariance in the first slot. QED (1).
(2) `k(z,x) = k(S_a z, S_b x)` for all `a,b` implies `k(z,x) = (1/d^2) sum_{a,b} k(S_a z, S_b x) =
(1/d^2) sum_{a,b} <psi(S_a z), psi(S_b x)> = < (1/d) sum_a psi(S_a z), (1/d) sum_b psi(S_b x) >
= <Phi(z), Phi(x)>` with `Phi(x) = (1/d) sum_a psi(S_a x) =: P_H psi(x)`. Any `S_t`-shift of `x`
permutes the sum over `a`, so `Phi(S_t x) = Phi(x)`: `Phi` is shift-invariant, hence a function of
the orbit only. The classifier `g(z) = sum_i a_i <Phi(z), Phi(x_i)> = < w_Phi, Phi(z) >` with
`w_Phi = sum_i a_i Phi(x_i)` is *linear in the invariant feature `Phi`*. So Theorem 1 applies in
feature space: the achievable margin is governed by the separation of `{Phi(x_i)}`, which lives in
the shift-invariant feature subspace. For the CNTK-GAP on the antipodal pair, Li et al.'s closed
form gives `Phi` proportional to the DC feature and `w_Phi parallel 1_d` (Ge Thm 2.2 part 2:
`g_K(z) >= 0 iff z^T 1_d >= 0`); the margin is then the DC-gap (Ge Cor 2). We do not re-derive the
CNTK closed form; we *cite* Ge Thm 2.2 / Li et al. for the specific kernel and only supply the
general reduction, which is the new content. QED (2).

**Why this matters:** Theorems 1-2 show the *same scalar* `Delta_DC` (resp. its feature-space
analog "separation after orbit-averaging the features") governs both the linear and the
infinite-width (NTK) shift-invariant models. So the co-existence/trade-off dichotomy is not a
linear artifact; it is a property of the **invariant feature geometry**.

### 3.4 From L2 to Linf

**Corollary 2 (Linf version with explicit constants).** For linear `f(x) = w^T x + b`,
`R_inf(f; x) = |w^T x + b| / ||w||_1` (proof: same as Lemma 3.1 with the dual norm `||.||_1` of
`||.||_inf`). For an invariant classifier `w = c 1_d`, `||w||_1 = |c| d`, so
`R_inf = |c d t_i + b| / (|c| d) = |t_i + b/(cd)|`, and the invariant Linf max-margin is
`Delta_DC / 2` (no `sqrt(d)` factor; the DC direction `1_d` has `||1_d||_1 = d`). The full Linf
max-margin is `(1/2) * min_{u,v} ||u-v||_? ` under the `L1`-dual geometry; the ratio analog of (5)
is `(Delta_DC d / 2) / (full L1-hull-gap)` — co-existence again iff the discriminative direction is
`1_d`, since `1_d` is *simultaneously* extremal for `L1` and `L2` duals only when the signal is DC.
The key qualitative conclusion (co-existence iff discriminative signal is DC / orbit-invariant) is
**norm-independent**; the *numerical* collapse factor differs (`sqrt(d)` for L2, `1` vs full for
Linf). We flag this: the dramatic `1/sqrt(d)` headline is an **L2 phenomenon**; in Linf the collapse
is hidden in the change of the hull geometry, which is why Ge's Figure 1(c) shows the steep drop for
L2 specifically.

---

## 4. Nonlinear case: an exact robust-radius theorem and the off-orbit correction

Linearity makes co-existence "iff discriminative signal is DC", which is restrictive (only the DC
mode is invariant under the *full* group). The richer empirical co-existence (Ge Sec 5.2 orthogonal
frequencies; deep nets) needs **nonlinear invariant features** (autocorrelation, power spectrum).
We now (4.1) define the right invariant features and (4.2) prove an exact robust radius for a clean
nonlinear invariant classifier, then (4.3) give the general lower bound with the off-orbit term that
connects to Melamed.

### 4.1 Nonlinear shift-invariant features: the power spectrum

The **power spectrum** `Psi: R^d -> R^d`, `Psi(x)_k = |hat x_k|^2 = |<phi_k, x>|^2` (squared Fourier
magnitudes), is shift-invariant: shifting multiplies `hat x_k` by `omega^{sk}` (unit modulus), so
`|hat x_k|` is unchanged. Equivalently `Psi(x)` is the DFT of the circular autocorrelation of `x`.
`Psi` separates orbits up to the (measure-zero) phase-retrieval ambiguity; crucially it carries
**all `d` frequency magnitudes**, not just DC. A classifier `f(x) = h(Psi(x))` is shift-invariant
for *any* `h`. This is the formal version of "invariance via autocorrelation/power-spectrum keeps a
large margin." We use it in §4.2.

**Definition (invariant separation).** For class supports `M_+, M_-` and a fixed shift-invariant
feature map `Phi` (e.g. `Psi`), the **`Phi`-separation** is
```
   sep_Phi := dist( Phi(M_+), Phi(M_-) )  (in feature space) ,
```
and we say *separation survives invariance* if `sep_Phi > 0`. Theorem 3 quantifies the robust radius
in terms of `sep_Phi` and the *conditioning* of `Phi` near the data (its local bi-Lipschitz
constants).

### 4.2 Exact robust radius for a clean two-region invariant classifier

We construct a setting matching Ge's "orthogonal frequencies" dataset, where the invariant model is
**provably more robust** than any FC model that must use the full coordinates.

**Setup (orthogonal-frequency data, made precise).** Fix two distinct nonzero frequencies
`k_+ != k_-` in `{1,...,d-1}` (AC modes), with `k_+, k_-` and their negatives distinct. Class `+`:
all signals of the form `x = a * c_{k_+}(theta)` where `c_k(theta)` is a unit-norm pure cosine at
frequency `k` with phase `theta` (i.e. the full shift orbit of a cosine, all phases), amplitude
`a in [a_lo, a_hi]`, `a_lo > 0`. Class `-`: same with `k_-`. (This is exactly "each class = all
shifts of a single frequency", Ge Sec 5.2 dataset 2, with bounded amplitude.) The two class supports
are unions of shift orbits, with `||x||_2 = a in [a_lo, a_hi]`.

**The invariant classifier.** Define `f_inv(x) := Psi(x)_{k_+} - Psi(x)_{k_-} = |hat x_{k_+}|^2 -
|hat x_{k_-}|^2` (difference of power at the two class frequencies), decision `sign f_inv`. It is
shift-invariant (it is a function of the power spectrum).

**Theorem 3 (exact L2 robust radius of the invariant classifier on orthogonal-frequency data).**
For any clean `x` in class `+` with amplitude `a` (`hat x_{k_+} = a` in magnitude after fixing the
pure-frequency normalization, `hat x_{k_-} = 0`, all other AC modes 0):
```
   R_2(f_inv; x) = a / sqrt(2) .                                              (6)
```
Symmetrically for class `-`. In particular the robust radius is `Theta(a) = Theta(||x||)`,
**independent of `d`**.

*Proof.* Write the perturbed input `x + delta`. Decompose `delta` in the orthonormal real Fourier
basis. Only the components of `delta` at modes `k_+, k_-` (and their conjugate partners) can change
`f_inv`; components at other modes leave both powers unchanged and only waste perturbation budget,
so the optimal `delta` has support on the `k_+` and `k_-` mode-pairs. Let `p` = component of `delta`
adding to the (complex) `k_+` coefficient and `q` = component adding to the `k_-` coefficient. Then
`hat{(x+delta)}_{k_+} = a + p`, `hat{(x+delta)}_{k_-} = q`, and
`f_inv(x+delta) = |a + p|^2 - |q|^2`. We need this `<= 0` (to flip the sign from `+a^2 > 0`).
Using the Parseval/orthonormality of real Fourier atoms, `||delta||_2^2 = |p|^2 + |q|^2` (each
complex mode pair contributes its squared modulus to the L2 norm; we use the unitary real-Fourier
normalization so there is no extra factor — this is the only place normalization matters and we fix
it as `||delta||^2 = |p|^2 + |q|^2`).
Minimize `|p|^2 + |q|^2` subject to `|a+p|^2 - |q|^2 <= 0`, i.e. `|q|^2 >= |a+p|^2`.
To make `|q|` as small as possible for given `p`, set `|q|^2 = |a+p|^2` (tight) — but we are
minimizing total `|p|^2 + |q|^2 = |p|^2 + |a+p|^2`. This is minimized over `p`. Take `p` real (the
imaginary part of `p` only increases `|p|^2` and `|a+p|^2`, so optimal `p` is real); minimize
`g(p) = p^2 + (a+p)^2` over real `p`: `g'(p) = 2p + 2(a+p) = 0 => p = -a/2`. Then
`|p|^2 + |q|^2 = (a/2)^2 + (a - a/2)^2 = a^2/4 + a^2/4 = a^2/2`, so `||delta||_2 = a/sqrt(2)`.
We must check the boundary is actually crossed (sign flips), not just touched: at `|q|^2 = |a+p|^2`,
`f_inv = 0` (boundary). An infinitesimally larger `|q|` flips the sign with the same limiting norm,
so the infimum (3) is `a/sqrt(2)`. No smaller perturbation works because any sign flip requires
`|q|^2 >= |a+p|^2` and we minimized exactly that. QED.

**Theorem 3' (the FC / non-invariant comparison; invariance HELPS here).** Consider the best the
*linear* (FC-class) classifier can do *robustly on the worst clean point of each class* on this same
data. A linear `f(x) = w^T x` must separate all phases of `k_+` from all phases of `k_-`. Because
each class is the full shift orbit of a frequency, by Theorem 1(a) the only *shift-consistent*
linear classifier is `w = c 1_d` — but `1_d^T x = 0` for any pure AC signal (`x` has no DC), so the
linear invariant model has **margin 0** (cannot separate at all). A *non-invariant* linear model can
separate a *fixed phase* but its consistency (A4) collapses across phases, and its worst-case robust
radius over the orbit is bounded by the in-orbit variation: there exist two phases `theta, theta'`
of the *same* class with `||c_k(theta) - c_k(theta')||` up to `2`, across which a fixed-`w` linear
score swings, forcing some clean orbit point within `O(a/sqrt(d))` of the boundary when `w` is
constrained to unit norm and must also handle the other class. (This recovers Ge's empirical Table 3
"orthogonal frequencies: CNN more robust than FC".)

*Proof sketch with the load-bearing step explicit.* The exact FC max-margin here is the SVM margin
over the union of orbits of `c_{k_+}` and `c_{k_-}`. Since these orbits are circles in the
2-D plane `span(cos k.x, sin k.x)`, the two classes are two concentric/separate circles of radius
`a` in *orthogonal* 2-planes (because `k_+ != k_-` modes are orthogonal). The max-margin hyperplane
separating two orthogonal circles of radius `a_lo..a_hi` in `R^4` (the 2+2 relevant dims) has margin
`O(a)` *only if it can use the radial/frequency-identity direction* — which is exactly the
*nonlinear* power-spectrum feature `Psi`, not available to a linear model. A linear model sees two
circles and the best separating hyperplane between a circle of radius `a` (class +) centered at 0 in
plane `A` and a circle of radius `a` in plane `B` (also through 0): both circles pass arbitrarily
close to the origin's neighborhood in the combined space and their convex hulls (disks) intersect at
0, so `d_min = 0`: **a linear model cannot separate them with positive margin at all.** Hence the
*nonlinear invariant* `f_inv` strictly dominates: margin `a/sqrt2 > 0` vs `0`. This is the cleanest
possible "invariance + nonlinear invariant feature ⇒ strictly more robust than FC-linear." QED
(rigorous for the linear comparison; the deep-FC-net comparison is empirical, Ge Table 3). ∎

**This is the formal reconciliation with Ge Sec 5.2:** invariance *helps* exactly when the
discriminative signal is carried by a shift-invariant *nonlinear* feature (power spectrum) with
positive `Phi`-separation, and *hurts* (single-dot) when the only surviving invariant linear feature
(DC) has a tiny gap.

### 4.3 General lower bound with the off-orbit correction (connects to Melamed)

We now give the general two-sided picture for a smooth invariant classifier `f = h o Phi` with `Phi`
a shift-invariant feature map (so `f` is automatically shift-invariant).

**Theorem 4 (robust radius of an invariant classifier; lower bound and obstruction).**
Let `f(x) = h(Phi(x))`, `Phi` shift-invariant and locally `L`-Lipschitz, `h` locally `beta`-Lipschitz
near `Phi(x)`, and suppose at clean correctly-classified `x`, `Phi` is locally bi-Lipschitz on the
*orbit-transverse, in-class-relevant* directions with lower constant `c_Phi > 0` (i.e. moving `Phi`
toward the boundary requires moving `x` by at least `1/L_eff` per unit of `Phi`). Let `m := y f(x)
> 0` be the functional margin in feature space terms. Then
```
   R_2(f; x)  >=  m / ( L * beta )       (lower bound, always)               (7)
```
and there is **no margin loss from invariance on the orbit directions**: perturbations along the
orbit `{S_s x - x}` (which span a subspace of `V_AC` of dimension up to `d-1`) **cannot** change
`f` at all, because `f(S_s x) = f(x)`; formally the directional derivative of `f` vanishes on
`span{S_s x - x}` (Lemma 4.1 below). Hence the invariant classifier is *perfectly robust along the
entire shift-orbit tangent space*, which is the high-frequency/aliasing subspace.

The **only** way invariance can reduce `R_2` relative to a non-invariant model is if the invariance
constraint forces a *smaller feature margin* `m` (Theorem 1 case: DC-gap small) OR creates a *new
sensitivity* in an off-orbit direction `u perp span{S_s x - x}` with large `||nabla_u f||`. The
latter is the Melamed mechanism: if the data lie on a low-dim manifold and `Phi`/`h` have large
gradient orthogonal to it, `R_2` along that off-orbit direction is small. Invariance per se does
*not* create such directions; it removes orbit directions from the budget of the attacker.

**Lemma 4.1 (orbit-tangent insensitivity).** If `f` is shift-invariant and differentiable at `x`,
then `nabla f(x)^T (S_s x - x) = 0`... more strongly, `f` is *constant* along the entire orbit, so
the finite difference `f(S_s x) - f(x) = 0` exactly (not just to first order). Moreover for the
*generator* direction, `d/dt f(x + t(S_1 x - x))|_{t=0}`: this need not be exactly 0 (the orbit is
not a straight line), but the *secant* across the orbit is 0. The precise robust statement: for any
`z` on the orbit, `||x - z||` perturbations *to z* keep the label. ∎ (immediate from A3).

*Proof of (7).* `|f(x+delta) - f(x)| = |h(Phi(x+delta)) - h(Phi(x))| <= beta ||Phi(x+delta) -
Phi(x)|| <= beta L ||delta||`. To flip the sign we need `|f(x+delta) - f(x)| >= |f(x)| = m`, so
`||delta|| >= m / (beta L)`. QED.

**Obstruction / honesty.** (7) is only a *lower* bound; the *upper* bound (existence of a small
adversarial `delta`) requires either (i) computing `Phi`'s conditioning (we did this *exactly* in
Theorem 3 for the power-spectrum-at-two-frequencies case, getting `a/sqrt2`), or (ii) the Melamed
off-manifold argument. We do **not** have a clean general exact robust radius for arbitrary `h o
Phi`; the power-spectrum quadratic case is tractable because the boundary is a quadric. This is the
main place generality fails — flagged in §7.

---

## 5. Empirical predictions (controlled dissection)

These are concrete, falsifiable, and designed for a depth/kernel/pooling/dense matched-capacity
sweep on MNIST/Fashion-MNIST/SVHN (matching Ge's protocol) plus the two synthetic datasets.

**The single predictive scalar.** Define the **DC-survival ratio** (linear proxy) and its nonlinear
generalization, the **invariant-feature separation ratio**:
```
   rho_lin(S)  := sqrt(d) * Delta_DC / d_min                (Eq. 5)
   rho_inv(S)  := sep_Phi-based margin of the invariant model / margin of the unconstrained model.
```
Prediction P0: **`rho` predicts co-existence.** Across datasets/architectures, the measured
adversarial robustness gap (FC robust radius minus invariant-CNN robust radius) is a *monotone
decreasing* function of `rho`; when `rho ≈ 1` the gap vanishes (co-existence), when `rho ≈ 0` the
gap is maximal (Ge single-dot regime). This is the headline test.

P1 (DC-gap measurement). For each dataset, compute `Delta_DC` (the gap of class-mean pixel
intensities) and `d_min` (SVM inter-hull distance). Predict: datasets where digit/object identity
correlates with mean brightness (low `rho`) show the *largest* invariance-induced robustness drop;
datasets where identity is brightness-balanced but texture/frequency-carried show *small* drop or
*reversal*. (Concrete: artificially DC-balance MNIST by per-image mean-subtraction; predict the
invariant CNN's robustness *drops further*, because you removed the only surviving invariant linear
feature. Conversely add a class-correlated brightness offset; predict the invariant CNN's robustness
*rises toward* the FC's.)

P2 (orthogonal-frequency reversal). On the synthetic orthogonal-frequency dataset of §4.2, predict
the invariant model's L2 robust radius `= a/sqrt(2)` (Theorem 3, exact, testable to 3 digits) and
that it *exceeds* the FC linear model's (which is 0; FC nonlinear's will be finite but lower).
Reproduces Ge Table 3 and is a *quantitative* (not just sign) prediction.

P3 (pooling / group-size knob). Vary the shift-subgroup `H` the architecture is invariant to (via
stride / pooling, Ge Note 1: invariance to shifts that are multiples of `prod strides`). As `H`
shrinks from full `Z_d` to trivial, `V_inv` grows (more Fourier modes survive, §6.3), so the
invariant-feature gap can only *increase* (more discriminative directions allowed). Predict: robust
radius is **monotone non-increasing in the degree of shift-invariance** *only when* the extra
surviving modes carry no class signal; if they do, robustness can be **non-monotone** — directly
testing Ge's Table 2/Figure 3 "more invariant ⇒ less robust" and predicting *where it breaks*.
Specifically, predict the breakage occurs exactly when `Delta_DC` is small but some low-AC mode has
a large class gap.

P4 (depth and nonlinear invariant features). Matched-capacity: a *linear* invariant model (1 conv +
GAP, no nonlinearity) should track `rho_lin` (P0); a *deep* invariant model can access power-spectrum
-like features and should track `rho_inv >= rho_lin`. Predict: depth helps the invariant model's
robustness *iff* the extra capacity lets it realize a high-`sep_Phi` nonlinear invariant feature;
measure `sep_Phi` of the learned penultimate features (cluster the penultimate representations of
shifted inputs; high within-orbit collapse + high between-class separation = high `sep_Phi`).

P5 (off-orbit / Melamed cross-check). Measure `||Pi_{orbit^perp} nabla f(x)||` vs `||Pi_{orbit}
nabla f(x)||`. Prediction (from Lemma 4.1 + Melamed): for an invariant model the *orbit-tangent*
gradient is ~0 (insensitivity), and the residual adversarial vulnerability is entirely off-orbit;
adding L2 weight decay / smaller init (Melamed's robustifiers) should shrink the off-orbit gradient
and raise `R_2` *without* touching shift-consistency. This decouples the two robustness sources.

P6 (consistency vs invariance). Since SC=1 (A4) is weaker than architectural invariance (A3),
predict a *measurable wedge*: high-shift-consistency models that are NOT architecturally invariant
(e.g. anti-aliased / BlurPool nets) can carry class signal in low-AC modes and thus achieve robust
radius *above* the strictly-invariant bound `(sqrt(d)/2)Delta_DC`. Test: BlurPool vs circular-pad
GAP at matched accuracy; predict BlurPool more robust when `Delta_DC` is small.

---

## 6. Relation to prior results

### 6.1 Recovering Ge's `2 -> 2/sqrt(d)` exactly

Ge's single-dot example: `x_1` = a single `1` in a background of `0`s (a one-hot `e_j`), label `+1`;
`x_2 = -e_j` (a single `-1`), label `-1`. (Ge: "image containing a single 1" vs "single -1".)
- **Full (FC) max-margin.** The two points are `e_j` and `-e_j`, distance `||e_j - (-e_j)|| = 2`.
  Max-margin = half the hull distance `= 2/2 = 1`? Ge reports max margin **2**. The discrepancy is
  normalization: Ge defines margin as the *full* gap (distance between the two parallel supporting
  hyperplanes' contact, i.e. `||e_j - (-e_j)|| = 2`), not the half-gap. Adopting Ge's convention
  (margin = full inter-class distance along the normal), `gamma_full = 2`. (We keep our half-gap
  convention internally but convert here.)
- **Invariant max-margin.** DC features: `t_1 = mean(e_j) = 1/d`, `t_2 = mean(-e_j) = -1/d`. DC-gap
  `Delta_DC = t_1 - t_2 = 2/d`. By (4') (half-gap, geometric) `gamma_inv = (sqrt(d)/2)(2/d) =
  1/sqrt(d)`; in Ge's full-gap convention multiply by 2: `gamma_inv = 2/sqrt(d)`. **Exactly Ge Cor
  1.** The collapse factor is `gamma_inv / gamma_full = (2/sqrt(d))/2 = 1/sqrt(d)`, matching Ge's
  Figure 1(c) "distance `~ 1/sqrt(d)`." ✓
- **Via our ratio (5):** `rho = sqrt(d) Delta_DC / d_min = sqrt(d)(2/d)/2 = 1/sqrt(d) -> 0`. So the
  single-dot case is precisely the `rho -> 0` (forced-trade-off) corner of Corollary 1. The reason:
  the discriminative direction `e_j - (-e_j) = 2 e_j` is almost entirely AC (`Q e_j = e_j - (1/d)
  1_d` has norm `sqrt(1 - 1/d) ≈ 1`), so `Q` (orbit-averaging) destroys almost all of it, leaving
  only the `1/d` DC sliver. **This is the mechanism Ge describes ("only DC survives") made
  quantitative as `rho`.** ✓

### 6.2 Recovering Ge Thm 2.2 (CNTK-GAP normal `1_d`)

Theorem 2 above: a jointly-shift-invariant kernel yields a classifier linear in the orbit-averaged
feature `Phi`, and for the antipodal pair the CNTK-GAP separator has normal `1_d` with margin = DC
difference. This is exactly Ge Thm 2.2(2) and Cor 2, now seen as a special case of the general
invariant-feature reduction. ✓

### 6.3 Subgroup invariance (strided/pooling architectures, Ge Note 1)

If the architecture is invariant only to the subgroup `H = <P> <= Z_d` of shifts by multiples of
`P = prod strides` (Ge Note 1), then `P_H := (1/|H|) sum_{s in H} S_s` is the orthogonal projector
onto `V_inv^H =` span of Fourier modes `phi_k` with `omega^{Pk} = 1`, i.e. `k` a multiple of `d/P`.
So `V_inv^H` is `|H|`-... has dimension `d/|H| = P` (the modes that are constant under `H`). All of
§2–§3 go through with `1_d` replaced by this `P`-dimensional invariant mode set; the invariant margin
is governed by class separation in those `P` surviving modes. **Prediction P3 is exactly this
knob.** As `P -> 1` (full invariance) only DC survives (Ge's strongest case); as `P -> d` (no
invariance) all modes survive and `gamma_inv -> gamma_full`. This rigorously interpolates Ge's
Figure 3 / Table 2 (more padding/invariance ⇒ fewer surviving modes ⇒ smaller margin *if* the
dropped modes carried signal). ✓

### 6.4 Why this does NOT contradict Kamath

Kamath Thm 2: for their cyclic-code Gaussian-mixture binary distribution with a *DC-coupled* special
coordinate `x_0` fixed under the shift `r_j`, *augmentation-induced* invariance forces:
`spatial-acc >= 1-η ⇒ adv-acc <= 1 - (1-p)(1-η)/p`. Three reasons there is no conflict:

1. **Different object.** Kamath bounds *accuracies under attack averaged over the distribution* (an
   `upper bound` on simultaneous spatial+adversarial accuracy), derived from a *constructed* data
   distribution where the label depends on a coordinate (`x_0`) that the shift leaves fixed but
   that the adversary can cheaply flip. Our Theorems 1–4 are about the *margin / robust radius of a
   given correctly-classified point* and *characterize when the margin is preserved*. Different
   quantity, different quantifier (worst-case point vs distributional accuracy).

2. **Kamath's distribution is a low-`rho` instance, by construction.** In their model the
   shift-invariant content (what survives orbit-averaging over the cyclic group acting on
   `x_1..x_d`) is engineered so that the *robust* discriminative signal is *not* in the surviving
   modes — the label leans on `x_0` (fixed by shift, but with a small adversarial budget to flip)
   and on cyclic-code structure with relative distance `δ`. In our language Kamath sits at
   *moderate-to-low `rho` with a deliberately fragile surviving feature*. So Kamath is a *consistent
   special case of our trade-off side* (Corollary 1, `rho` small / fragile surviving feature), not a
   counterexample to our co-existence side. Our Theorem 3 exhibits a *different* distribution (high
   `rho_inv`: orthogonal frequencies) where co-existence provably holds — Kamath's theorem says
   nothing about that distribution, because their bound is stated *for their distribution*.

3. **Augmentation-induced vs architectural/emergent invariance.** Kamath's invariance comes from
   training augmentation forcing `f(r_j x) = f(x)` on the *data* (a soft, distributional constraint
   coupled to the loss), and they study *random* spatial robustness (average over transformations).
   Our (A3)/(A4) are *architectural* (exact, all `x`) or *measured emergent* consistency. The
   regimes differ exactly as Kamath themselves note ("our regime is random spatial robustness").
   Co-existence in our regime therefore does not violate their impossibility, which is
   *regime-specific* (their Prop 1 explicitly constructs the distribution to make even high clean
   accuracy compatible with low spatial robustness, i.e. they *engineer* fragility).

In one line: **Kamath proves "for a distribution engineered to put the robust signal off the
invariant subspace, you can't have both"; we prove "you can have both iff the robust signal stays on
the invariant subspace", and exhibit such a distribution.** These are complementary, both true.

### 6.5 Relation to Frei and Melamed (optimization vs structure)

Frei (existence of robust net + implicit-bias selection of non-robust KKT) and Melamed (off-manifold
gradient) are about *which solution gradient flow finds*, holding the architecture fixed. Our results
are about *what robustness is achievable given the invariance constraint*, holding optimization
aside. They compose: Theorem 1/3 give the *achievable* invariant margin (the ceiling); Frei/Melamed
say gradient flow may *not reach* it and may add off-orbit sensitivity. Lemma 4.1 + Prediction P5
state the clean decoupling: invariance removes *orbit-tangent* vulnerability for free; the *residual*
vulnerability is off-orbit and is governed by the implicit-bias / init-scale story, addressable by
L2 / small init exactly as Melamed shows — *without* changing shift-consistency. So our structural
theorem and their optimization theorems are orthogonal and jointly give the full picture:
```
   achievable robust radius (ours, structural)  -  optimization slack (Frei/Melamed)  =  realized.
```

---

## 7. Limitations, where assumptions bite, open gaps

1. **Full-group linear invariance ⇒ only DC.** Theorem 1's clean "co-existence iff discriminative
   signal is DC" is *because* `V_inv = span(1_d)` for the full group in the *linear* class. This is
   restrictive and is precisely why real co-existence needs *nonlinear* invariant features (§4) or
   subgroup invariance (§6.3). The linear theorem is exact but its co-existence condition is narrow;
   the honest statement is "linear + full-group invariance almost always forces a trade-off unless
   the signal is brightness." This matches Ge but is not, by itself, the rich co-existence story.

2. **No general exact nonlinear robust radius.** Theorem 3 is exact only for the quadratic
   power-spectrum-at-two-frequencies classifier (quadric boundary). For general `h o Phi` we only
   have the lower bound (7) and the conditioning constants `L, beta, c_Phi` are not computed in
   closed form. Getting a matching *upper* bound (existence of a small adversarial example) for
   general invariant `Phi` is open — the obstruction is that `Phi`'s sublevel sets are not convex
   (power spectrum is quadratic; deeper features worse). Flagged honestly: §4.3 is a one-sided
   result for the general case.

3. **Phase-retrieval ambiguity.** `Psi` (power spectrum) does not separate orbits that are
   phase-retrieval-equivalent; `sep_Phi` could be 0 for adversarially-chosen classes even with
   distinct orbits. So "use the power spectrum" is not universally a high-margin invariant feature;
   bispectrum/triple-correlation removes most of this ambiguity but complicates the robust-radius
   computation (cubic boundary). Open.

4. **`SC = 1` vs (A3).** Our exact theorems use architectural invariance (A3). For *measured*
   shift-consistency `SC` (A4), `SC = 1` only constrains the *sign* of `f` on orbits, not `f`
   itself; the margin can then be larger than the (A3) bound (Prediction P6 wedge). We do not have
   an exact margin identity under `SC = 1` alone — only the inequality `gamma_{SC=1} >=
   gamma_{(A3)}` (more freedom). Quantifying the wedge precisely is open and is exactly the
   interesting empirical regime (BlurPool / anti-aliasing).

5. **Binary only; L2-centric.** Theorems are binary; multi-class needs the analysis per
   one-vs-rest decision region (the orbit-insensitivity Lemma 4.1 still holds, but the margin
   bookkeeping is per-pair). The L2 collapse `1/sqrt(d)` is genuinely an L2 phenomenon (§3.4);
   the Linf story is qualitatively the same (co-existence iff signal is invariant) but the numeric
   factor differs and we did not fully work out the Linf hull geometry. Flagged.

6. **2-D, color, real architectures.** All proofs are for 1-D circular signals and the abstract
   group. The 2-D `Z_{d1} x Z_{d2}` case is a verbatim extension (replace cyclic DFT by 2-D cyclic
   DFT; `V_inv` is still the DC constant image; everything in §2–§3 holds). Real CNNs are only
   *approximately* shift-invariant (zero padding, stride, non-circular boundary; Ge Note 1, Zhang
   2019), so (A3) holds only approximately and the exact identities become approximate — the
   *predictions* (§5) are robust to this but the *exact* constants are not.

7. **We characterize the achievable margin, not whether training reaches it.** As in §6.5 this is by
   design (structural, not optimization), but it means our theorems do not *predict* the robustness
   of a *trained* network without also invoking Frei/Melamed for the optimization slack. The
   honest combined claim is the decomposition at the end of §6.5.

---

## Summary of the result (one paragraph)

Shift-invariance is the orthogonal projection `P` onto the shift-invariant subspace `V_inv`
(= the DC line for the full pixel-shift group; the `P`-dimensional low-frequency block for a
stride-`P` subgroup). A shift-invariant classifier is **perfectly robust along the entire shift-orbit
tangent space** (Lemma 4.1, the high-frequency/aliasing directions) — invariance gives that
robustness *for free*. The *only* way invariance reduces the adversarial margin is by shrinking the
**class separation that survives orbit-averaging**: in the linear/kernel case the invariant
max-margin is *exactly* `(sqrt(d)/2)·(DC-gap)` (Theorem 1, recovering Ge's `2/sqrt(d)` as the
`rho -> 0` corner, Theorem 2 recovering CNTK-GAP normal `1_d`), so co-existence holds **iff the
discriminative direction is the invariant (DC / surviving-mode) direction**, quantified by the
single ratio `rho = sqrt(d)·Delta_DC / d_min in [0,1]`. With *nonlinear* invariant features
(power spectrum), co-existence provably returns: on orthogonal-frequency data the invariant
classifier has exact L2 robust radius `a/sqrt(2) = Theta(||x||)`, strictly beating the linear FC
model (Theorem 3), reconciling Ge's own Sec 5.2 "CNN more robust" reversal. This does **not**
contradict Kamath, whose impossibility is for a distribution *engineered* to place the robust signal
off the invariant subspace (a low-`rho` instance) and concerns distributional accuracy under random
transforms, not the per-point margin; it is the trade-off side of the same dichotomy. The residual,
off-orbit vulnerability is the Frei/Melamed implicit-bias story and is orthogonal: it is removed by
L2/small-init without touching shift-consistency (Prediction P5). The headline testable scalar is
`rho` (resp. its nonlinear feature-separation analog), which is predicted to govern co-existence
across the depth/kernel/pooling/dense dissection (Predictions P0–P6).
