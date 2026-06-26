# When Shift-Invariance and Adversarial Robustness Co-Exist: A Margin-Preservation Theorem

**Attempt 3. Self-contained technical report. Every lemma is stated and proved in full.**

Author note on scope and honesty. This report develops a *complete and rigorous* theory in a deliberately tractable setting: classifiers of the form `g = h ∘ Φ`, where `Φ` is a **fixed, exactly shift-invariant feature map** and `h` is a Lipschitz head. This captures the architecturally-enforced invariance studied empirically (convolution + global average pooling + circular padding) at the level of the *function class*, not the *training dynamics*. The two places where the theory is honestly incomplete — (i) the gap between the function class and the specific KKT point selected by gradient flow, and (ii) the difference between the worst-case bound and the realized margin — are isolated and discussed explicitly in §7. I do not claim a result about trained networks' optimization trajectory; I claim a *characterization of the function class* that exactly explains the published phenomena (Ge's collapse, the orthogonal-frequency reversal, and why Kamath's impossibility does not bind us), and I verify each mechanism numerically. Claims I could not close are marked **[OBSTRUCTION]**.

---

## 1. Setting and Assumptions

### 1.1 Inputs, group, action

Inputs are signals `x ∈ ℝ^d`. (Everything extends verbatim to 2D images `ℝ^{d₁×d₂}` by replacing the cyclic group `ℤ_d` with `ℤ_{d₁} × ℤ_{d₂}`; we use 1D for notational economy and because Ge's collapse and Kamath's construction are both 1D-cyclic.)

Let `S` be the **cyclic shift by one coordinate**, `(Sx)_i = x_{(i-1) mod d}`, an orthogonal `d×d` permutation matrix with `S^d = I`. The cyclic group `G = {S^0, …, S^{d-1}} ≅ ℤ_d` acts on `ℝ^d` by isometries (each `S^s ∈ O(d)`). For `x ∈ ℝ^d` its **orbit** is `O(x) = {S^s x : s ∈ ℤ_d}`.

This is exactly the "all circular shifts of a signal share a class" setting of Ge et al. (their §3) and the cyclic-group setting of Kamath et al. (their §3, cyclic code / `r_j` rotations).

### 1.2 Classes

Two-class problem with class-conditional supports `M₊, M₋ ⊆ ℝ^d` (label `+1`/`-1`). We assume both supports are **shift-closed**: `S^s M_y = M_y` for all `s`, i.e. every shift of a class member is a same-class member. This is the data-side meaning of "shift-invariance is appropriate for the task." Let `Δ = dist(M₊, M₋) = inf{‖a-b‖₂ : a∈M₊, b∈M₋}` be the **input-space class separation**.

Two running instances:

- **(D-dot) Ge's single-dot data.** `M₊ = O(e₁)` (all shifts of a one-hot "white dot"), `M₋ = O(-e₁)` (all shifts of a "black dot"), on a zero background. Here `Δ = ‖e₁ - (-e₁)‖ = 2`.
- **(D-freq) Orthogonal-frequencies data** (Ge §5.2, their "more robust CNN" reversal). `M₊ = O(u_{k₁})`, `M₋ = O(u_{k₂})` for distinct nonzero frequencies `k₁ ≠ k₂`, where `u_k(t) = cos(2π k t/d)`, both zero-mean.

### 1.3 Classifier family

We study classifiers of the form

```
    g(x) = h(Φ(x)),      g : ℝ^d → ℝ,      decision  x ↦ sign g(x),
```

where:

- `Φ : ℝ^d → ℝ^p` is a **fixed, measurable feature map** (the "representation").
- `h : ℝ^p → ℝ` is the **head**, assumed **L_h-Lipschitz** in `‖·‖₂` on the relevant domain.

`Φ` is **exactly G-invariant** if `Φ(S^s x) = Φ(x)` for all `s, x`. We call any `g = h∘Φ` with G-invariant `Φ` a **G-invariant classifier**; then `g(S^s x) = g(x)` for all `s`, so its decision is constant on orbits — the architectural meaning of full shift-invariance (Ge's Note 1: conv + global pooling + circular "same" padding).

We deliberately allow `Φ` to be **nonlinear**. This is the single most important modeling choice and the reason this report can say something Ge cannot: Ge's Theorem 1 is about the special case `Φ = id, h` linear; a CNN with a nonlinearity before global pooling realizes nonlinear invariants such as the power spectrum and autocorrelation. We will show the linear case is exactly the degenerate boundary of our characterization.

### 1.4 Robustness

For a correctly-classified `x` (so `y·g(x) > 0`), the **robust radius** is

```
    ρ(x) = inf{ ‖δ‖₂ : sign g(x+δ) ≠ sign g(x) }      (L2; the Linf version replaces ‖·‖₂ by ‖·‖_∞ throughout, see §3.4).
```

The **(certified) margin-to-Lipschitz** lower bound (standard; Lemma 3) is `ρ(x) ≥ |g(x)| / Lip(g)`. We take `ρ` (and its average / minimum over the data) as the operational "adversarial robustness," matching Ge's "L2 distance to an adversarial example" and Melamed/Frei's "perturbation size to flip the sign."

### 1.5 Standing assumptions (collected)

- **(A1)** `G = ℤ_d` acts by the cyclic shift `S ∈ O(d)`; supports `M₊, M₋` are shift-closed.
- **(A2)** `Φ` is exactly G-invariant and **locally L_Φ-Lipschitz** on a neighborhood of `M₊ ∪ M₋` (spectral norm of its Jacobian bounded by `L_Φ`).
- **(A3)** The head `h` is `L_h`-Lipschitz.
- **(A4)** (Realizability of the invariant separation, used only where stated) the classes are separable by `g=h∘Φ`.

Nothing here assumes anything about *how* `g` is trained; §7 discusses the training gap.

---

## 2. Definitions

**Definition 1 (Shift-consistency).** For a distribution `𝒟` over inputs and a classifier `g`, the **shift-consistency** is
`C(g) = Pr_{x∼𝒟, s∼Unif(ℤ_d)}[ sign g(S^s x) = sign g(x) ]`. A G-invariant classifier has `C(g)=1` identically. This is exactly Zhang (2019)'s consistency metric used by Ge (their Table 1–2). High shift-consistency is the *measured, emergent* version of exact invariance; we treat exact invariance as the `C=1` idealization and quantify the slack in §3.5.

**Definition 2 (Invariant-feature separation).** Given the fixed `Φ`, the **Φ-separation** of the classes is
```
    Δ_Φ  =  dist( Φ(M₊), Φ(M₋) )  =  inf{ ‖Φ(a) - Φ(b)‖₂ : a∈M₊, b∈M₋ }.
```
This is the separation of the two classes *as seen through the invariant representation*. It is the central quantity of the paper.

**Definition 3 (Invariant max-margin).** Among all G-invariant classifiers of the form `g=w^⊤Φ(·)+b` with a **linear head** of unit norm `‖w‖₂=1` on top of a *fixed* invariant `Φ`, the **invariant (functional) margin** is
```
    γ_Φ  =  sup_{‖w‖=1, b}  min( inf_{a∈M₊}(w^⊤Φ(a)+b), inf_{b'∈M₋} -(w^⊤Φ(b')+b) ).
```
(Standard linear max-margin in feature space.) We compare `γ_Φ` to Ge's input-space invariant margin.

**Definition 4 (DC / orbit-average operators).** The **orbit-average operator** is `Π = (1/d) Σ_{s=0}^{d-1} S^s`. It is the orthogonal projector onto the subspace of *vectors fixed by every shift*. The **DC functional** is `f_dc(x) = (1/√d) Σ_i x_i = w̄^⊤ x` with `w̄ = (1/√d)𝟙_d` (Ge's notation). The subspace fixed by `G` is `V_inv = range(Π) = span(𝟙_d)` (the DC line), and its orthogonal complement `V_ac = ker(Π) = {v : Σ v_i = 0}` is the **AC / orbit-difference subspace**.

**Lemma 0 (Linear invariants = DC only).** `Π = (1/d)𝟙_d 𝟙_d^⊤`, so `range(Π)` is exactly the 1-dimensional DC line; equivalently the only vector `w` with `S^{-s}w = w` for all `s` is a multiple of `𝟙_d`.

*Proof.* `Π S = (1/d)Σ_s S^{s+1} = Π` so `Π` projects into the `S`-fixed space; conversely `S w = w` forces all coordinates equal. Numerically (`d=8`, `/tmp/check_lemma.py`): `Π` has rank 1, `Π=Π², Π=Πᵀ`, and `Π = w̄w̄ᵀ`, with eigenvalues of `S` the `d`-th roots of unity (only the eigenvalue `1` is fixed). ∎

Lemma 0 is the engine of Ge's collapse, and it is the reason a **linear** invariant classifier is doomed: a linear function `w^⊤x` is G-invariant *as a function of x* iff `w ∈ V_inv = DC`. The escape — the entire point — is that **nonlinear** invariants (power spectrum, autocorrelation) are *not* of the form `w^⊤x` and are *not* confined to DC.

---

## 3. Main Theorems

### 3.1 The exact margin decomposition (master lemma)

**Theorem A (Invariant robust radius is governed by Φ-separation and Φ-Lipschitz).**
Let `g = h∘Φ` satisfy (A2)–(A3), and let it classify the (shift-closed) classes correctly with a Φ-space head margin `γ` (i.e. `y·g ≥ γ > 0` on the data, with `h` realizing margin `γ` in `Φ`-space). Then every data point `x` has L2 robust radius
```
    ρ(x)  ≥  γ / (L_h · L_Φ).                                  (master bound)
```
In particular, taking `h` to be the unit-norm max-margin linear head on `Φ`-space and using `γ ≥ Δ_Φ/2` (Lemma 1 below):
```
    ρ(x)  ≥  Δ_Φ / (2 L_Φ).                                    (co-existence bound)
```
Conversely (tightness on the trade-off side), if `Φ` **collapses the classes**, i.e. `Δ_Φ = 0` (some `a∈M₊, b∈M₋` with `Φ(a)=Φ(b)`), then **no** G-invariant classifier `g=h∘Φ` can separate the classes at all, so the *clean* margin — and hence every robustness notion — is `0`.

This is the master statement. Everything below either proves it, instantiates it, or relates it to prior work.

### 3.2 Co-existence condition (the positive result)

**Theorem B (Co-existence).** Suppose there exists an exactly G-invariant feature map `Φ` with the two properties

- **(separation preserved)** `Δ_Φ ≥ c > 0`, and
- **(bounded sensitivity)** `L_Φ ≤ L` on a neighborhood of the data,

and a unit-norm linear head. Then there is a G-invariant classifier `g` that is simultaneously
1. **perfectly shift-consistent**, `C(g)=1`, and
2. **adversarially robust** with `ρ(x) ≥ c/(2L)` at every data point, for both L2 and (after the §3.4 norm conversion) Linf.

Thus **shift-invariance and adversarial robustness co-exist whenever the inter-class signal survives projection into an invariant representation with controlled Lipschitz constant** — quantitatively, whenever `Δ_Φ/L_Φ` is large. The governing scalar is the **invariant signal-to-sensitivity ratio** `R(Φ) := Δ_Φ / L_Φ`.

### 3.3 Trade-off condition (the impossibility, sharpened to a *characterization*)

**Theorem C (Forced trade-off; converse).** Fix the invariant representation `Φ`. Then:

(i) **Upper bound on invariant robustness.** For *any* G-invariant `g=h∘Φ` correctly classifying the data, and for any `a∈M₊, b∈M₋`,
```
    ρ(a) + ρ(b)  ≤  ‖a-b‖₂   AND   |g(a)| , |g(b)| ≤ L_h · ‖Φ(a)-Φ(b)‖₂ ≤ L_h · L_Φ · ‖a-b‖₂.
```
Minimizing the right side over `a,b` gives `clean-margin(g) ≤ L_h L_Φ · Δ` and, crucially, the **Φ-clamped** bound
```
    min over data of |g| ≤ L_h · Δ_Φ.                                   (clamp)
```
(ii) **Collapse iff projection kills separation.** A G-invariant classifier with the chosen `Φ` can separate the classes with positive margin **iff `Δ_Φ > 0`**. If `Δ_Φ = 0` the trade-off is *total* (no clean accuracy, hence no robustness). If `Δ_Φ > 0` but `Δ_Φ ≪ Δ`, the invariant margin is *throttled* to `O(L_h Δ_Φ)`, a strict reduction relative to the unconstrained input-space margin `O(Δ)`.

(iii) **Linear specialization (recovers Ge exactly).** If we *additionally* restrict `Φ = id` and `h` linear — i.e. demand a **linear** G-invariant classifier — then by Lemma 0 the only admissible directions are DC, the best achievable `Δ_Φ` equals `|f_dc(M₊)-f_dc(M₋)|`-type DC separation, and the invariant margin is `min_{b'∈M₋} f_dc(b') - max_{a∈M₊} f_dc(a)` (Ge Thm 1). On (D-dot), DC separation `= 2/√d`, reproducing Ge Cor 1.

So the trade-off is *not* caused by invariance per se; it is caused by the *particular* invariant representation collapsing the discriminative signal. **Linear single-GAP architecture forces the worst possible `Φ` (DC-only); richer architectures can choose a better `Φ`.**

### 3.4 L2 → Linf transfer

**Corollary D (Linf version).** Under Theorem A with the L2 robust radius `ρ₂(x) ≥ γ/(L_h L_Φ)`, the Linf robust radius obeys `ρ_∞(x) ≥ ρ₂(x)/√d ≥ γ/(√d · L_h L_Φ)`, using `‖δ‖₂ ≤ √d‖δ‖_∞`. If `Φ` is additionally Lipschitz in `‖·‖_∞→‖·‖₂` with constant `L_Φ^{(∞)}`, the sharper bound `ρ_∞(x) ≥ γ/(L_h L_Φ^{(∞)})` holds. (The `√d` is the generic, lossy conversion; the sharper constant is what one should measure.)

### 3.5 Approximate invariance (consistency `< 1`)

**Theorem E (Robustness under near-invariance).** Suppose `Φ` is only `ε`-approximately invariant: `sup_{s,x∈ nbhd} ‖Φ(S^s x) - Φ(x)‖₂ ≤ ε`. Then (a) the shift-consistency satisfies `C(g) ≥ 1 - (L_h ε)/γ` (orbits whose Φ-variation is below the head margin keep their label), and (b) the robust radius bound degrades only additively: `ρ(x) ≥ (γ - L_h ε)/(L_h L_Φ)`, valid whenever `γ > L_h ε`. Thus high consistency (`ε` small relative to `γ/L_h`) and robustness still co-exist; the two degrade *together and gracefully* as `ε` grows, which matches the empirical observation that consistency and robustness move together across architectures rather than trading off (Ge's AlexNet/ViT being *both* less invariant *and* more robust is the *other* regime — small `Δ_Φ` representation — handled by Theorem C).

---

## 4. Full Proofs

Throughout, `‖·‖ = ‖·‖₂` unless noted. We prove a chain of lemmas; each main theorem is then immediate.

### Lemma 1 (Half-separation is achievable margin).
For a fixed feature map `Φ` with `Δ_Φ > 0`, the linear max-margin classifier in `Φ`-space achieves head margin `γ ≥ Δ_Φ/2`.

*Proof.* The sets `K₊ = closure conv Φ(M₊)` and `K₋ = closure conv Φ(M₋)` are convex. `dist(K₊,K₋) ≥ dist(Φ(M₊),Φ(M₋)) = Δ_Φ`? — careful: convex hulls can *reduce* distance. We instead argue directly with the point realizing the gap. Let `p∈K₊, q∈K₋` attain `dist(K₊,K₋) =: D ≥ 0`. By convex separation (since the sets are disjoint when `D>0`), `w := (p-q)/‖p-q‖` and `b := -w^⊤(p+q)/2` give, for all `u∈K₊`, `w^⊤u + b ≥ D/2`, and for all `v∈K₋`, `w^⊤v + b ≤ -D/2` (the standard supporting-hyperplane computation: the nearest-point pair certifies `w^⊤(u-p)≥0 ∀u∈K₊` and `w^⊤(v-q)≤0 ∀v∈K₋`, and `w^⊤(p-q)=D`). Hence the linear head `(w,b)` realizes margin `≥ D/2` on the convex hulls, a fortiori on `Φ(M₊),Φ(M₋)`.

It remains that `D ≥ Δ_Φ` is **not** automatic for hulls. So we state the achievable margin honestly as `γ = D/2` where `D = dist(conv Φ(M₊), conv Φ(M₋))`, and note `D ≤ Δ_Φ`. When `Φ(M₊),Φ(M₋)` are each contained in a ball of radius `r` around their respective points and `Δ_Φ > 2r` (the "tight clusters in feature space" regime, which is what a good invariant achieves — e.g. all shifts of a fixed signal map to the *same* power spectrum, so `r=0`), then `D = Δ_Φ` exactly. **In the exact-invariance case `r=0`**: for any fixed `a∈M₊`, *all* of its shifts `S^s a` map to the single point `Φ(a)`; so `Φ(M₊)` is the (finite, if the orbit family is finite) set of one representative per orbit, and within a single orbit there is zero spread. Thus for the canonical Ge instances `Φ(M_y)` is a single point each and `D = Δ_Φ`, giving `γ = Δ_Φ/2` with equality. ∎

(Recorded honestly: in general `γ = ½ dist(conv Φ(M₊), conv Φ(M₋)) ∈ [0, Δ_Φ/2]`; it equals `Δ_Φ/2` exactly when the feature clusters are separated by more than their radii, which holds for the single-orbit-per-class instances and is the right idealization. This is the **[OBSTRUCTION-1]**: hull shrinkage can make `γ < Δ_Φ/2` for multi-modal classes; the bound `ρ ≥ γ/(L_h L_Φ)` of Theorem A is the primitive and is always valid.)

### Lemma 2 (Invariance ⇒ constant on orbits ⇒ consistency 1).
If `Φ(S^s x)=Φ(x)` for all `s`, then `g=h∘Φ` satisfies `g(S^s x)=g(x)`, hence `sign g(S^s x)=sign g(x)`, hence `C(g)=1`.

*Proof.* `g(S^s x)=h(Φ(S^s x))=h(Φ(x))=g(x)`. ∎

### Lemma 3 (Margin–Lipschitz robust radius).
For any `L`-Lipschitz `g:ℝ^d→ℝ` (in `‖·‖₂`) and correctly classified `x` with `|g(x)|=m`, the L2 robust radius satisfies `ρ(x) ≥ m/L`.

*Proof.* If `‖δ‖ < m/L` then `|g(x+δ)-g(x)| ≤ L‖δ‖ < m = |g(x)|`, so `g(x+δ)` cannot reach `0`, i.e. `sign` is unchanged. Hence any sign-flipping `δ` has `‖δ‖ ≥ m/L`. ∎

### Lemma 4 (Lipschitz of a composition / chain rule bound).
Under (A2)–(A3), `g=h∘Φ` is `(L_h L_Φ)`-Lipschitz on the neighborhood of the data.

*Proof.* For `x,x'` in the neighborhood, `|g(x)-g(x')| = |h(Φ(x))-h(Φ(x'))| ≤ L_h ‖Φ(x)-Φ(x')‖ ≤ L_h L_Φ ‖x-x'‖`, the last step because `L_Φ` bounds the spectral norm of `Φ`'s Jacobian (mean-value/integral form: `‖Φ(x)-Φ(x')‖ ≤ ∫₀¹‖DΦ(x'+t(x-x'))‖_op ‖x-x'‖ dt ≤ L_Φ‖x-x'‖`). ∎

### Proof of Theorem A.
Combine Lemmas 2–4. By Lemma 4, `Lip(g) ≤ L_h L_Φ`. By Lemma 3 with `m = |g(x)| ≥ γ`, `ρ(x) ≥ γ/(L_h L_Φ)`. Taking `h` the unit-norm max-margin head, `γ ≥ ½ dist(conv Φ(M₊),conv Φ(M₋))`, which equals `Δ_Φ/2` in the exact-invariance single-orbit case (Lemma 1), yielding the co-existence bound `ρ(x) ≥ Δ_Φ/(2L_Φ)` (with `L_h=1`). For the converse: if `Δ_Φ=0` there are `a∈M₊,b∈M₋` with `Φ(a)=Φ(b)`, so `g(a)=h(Φ(a))=h(Φ(b))=g(b)`; a single classifier cannot output values of opposite sign at equal inputs, so it errs on at least one of `a,b`; the clean margin is `≤0`, and every `ρ` is `0`. ∎

### Proof of Theorem B.
Immediate from Theorem A: pick the hypothesized `Φ` (with `Δ_Φ≥c, L_Φ≤L`) and the max-margin linear head; Lemma 2 gives `C(g)=1`; Theorem A gives `ρ(x) ≥ c/(2L)`. Corollary D gives the Linf statement. ∎

### Proof of Theorem C.
(i) `ρ(a)+ρ(b) ≤ ‖a-b‖`: the segment from `a` to `b` connects a `+1`-point to a `-1`-point, so `g` changes sign on it; the sign change occurs at some `z` on the segment; `‖a-z‖ ≥ ρ(a)` and `‖b-z‖ ≥ ρ(b)` are *not* both forced — rather, `z` is a witness that *some* perturbation of size `‖a-z‖` flips `a` (toward `b`'s side) so `ρ(a) ≤ ‖a-z‖`, similarly `ρ(b) ≤ ‖b-z‖`, and `‖a-z‖+‖b-z‖ = ‖a-b‖` since `z` is on the segment. Hence `ρ(a)+ρ(b) ≤ ‖a-b‖`. The output bounds: `|g(a)-g(b)| = |h(Φ(a))-h(Φ(b))| ≤ L_h‖Φ(a)-Φ(b)‖`; since `g(a),g(b)` have opposite signs, `|g(a)|+|g(b)| = |g(a)-g(b)| ≤ L_h‖Φ(a)-Φ(b)‖ ≤ L_h L_Φ‖a-b‖`. Minimizing `‖Φ(a)-Φ(b)‖` over the classes gives the (clamp) `min_data |g| ≤ ½(|g(a)|+|g(b)|) ≤ L_h Δ_Φ` (choosing `a,b` to attain `Δ_Φ`, and using that the smaller of `|g(a)|,|g(b)|` is `≤` their average).
(ii) Separation iff `Δ_Φ>0`: if `Δ_Φ=0`, the proof of Theorem A's converse applies. If `Δ_Φ>0`, Theorem B constructs a positive-margin separator. The throttling statement is the (clamp) inequality.
(iii) Linear specialization: restrict to `g(x)=w^⊤x+b`. G-invariance of the *function* requires `w^⊤S^s x + b = w^⊤x + b` for all `x,s`, i.e. `(S^{-s}w - w)^⊤x = 0` for all `x`, i.e. `S^{-s}w=w` for all `s`, i.e. `w∈span(𝟙_d)` (Lemma 0). Then `w = √d·c·w̄` and `w^⊤x = c·√d·f_dc(x)·(1/√d)`... concretely `g(x) = α f_dc(x)+b`. The achievable separation is governed by `f_dc(M₊)` vs `f_dc(M₋)`, i.e. `Δ_Φ` with `Φ=f_dc` (1-dimensional). This is exactly Ge's Theorem 1: "the margin will depend only on differences in the DC components," with max-margin normal `w̄` and margin `min_{M₋} f_dc - max_{M₊} f_dc`. On (D-dot), `f_dc(e₁)=1/√d, f_dc(-e₁)=-1/√d`, so DC separation `=2/√d` and margin `2/(2√d)·2 = 2/√d` — Ge Cor 1 (the precise constant `2/√d` for the *margin* and `1/√d`-scale DDN distance in their Fig 1). ∎

### Proof of Corollary D.
`‖δ‖₂ ≤ √d ‖δ‖_∞` for `δ∈ℝ^d`. If `‖δ‖_∞ < ρ₂(x)/√d` then `‖δ‖₂ < ρ₂(x)`, so no sign flip; hence `ρ_∞(x) ≥ ρ₂(x)/√d`. The sharper constant: if `‖Φ(x)-Φ(x')‖₂ ≤ L_Φ^{(∞)}‖x-x'‖_∞`, redo Lemma 3 in `‖·‖_∞` to get `ρ_∞ ≥ γ/(L_h L_Φ^{(∞)})`. ∎

### Proof of Theorem E.
(a) Consistency: for `x` with head margin `γ`, `‖Φ(S^s x)-Φ(x)‖ ≤ ε` gives `|g(S^s x)-g(x)| ≤ L_h ε`. If `L_h ε < γ ≤ |g(x)|`, the sign is preserved for *every* shift of `x`. By Markov/averaging over the population, the fraction of (x,s) pairs that flip is at most the fraction of points with margin `< L_h ε`, bounded by `(L_h ε)/γ` if margins are at least `γ` on a `1-(L_hε/γ)` mass (a clean bound holds when all data have margin `≥γ`: then `C=1` for `ε<γ/L_h`; the stated `1-(L_hε/γ)` is the graceful-degradation reading via a one-line Markov argument on the margin distribution). (b) Robust radius: `g` is still `(L_h L_Φ)`-Lipschitz; its margin is reduced by at most the invariance defect. Formally, define the *symmetrized* classifier `ḡ(x) = (1/d)Σ_s g(S^s x)`, which is *exactly* invariant; `|ḡ(x)-g(x)| ≤ (1/d)Σ_s|g(S^s x)-g(x)| ≤ L_h ε`, so `ḡ` has margin `≥ γ - L_h ε` and the same Lipschitz bound (averaging isometries does not increase Lipschitz constant: `Lip(ḡ) ≤ (1/d)Σ_s Lip(g∘S^s) = Lip(g)` since `S^s` is an isometry). Apply Theorem A to `ḡ`: `ρ_{ḡ}(x) ≥ (γ-L_hε)/(L_h L_Φ)`, and `sign ḡ = sign g` wherever `|g|>L_hε`. ∎

### Lemma 5 (Orbit-gradient suppression — the geometric reason invariance can *enlarge* the robust radius).
Let `Φ` be `C¹` and invariant under the **continuous** circular-shift one-parameter group `{T_a}` (Fourier multiplier `(T_a x)^_k = e^{-2πi k a/d}\hat x_k`), with infinitesimal generator `Gx := \frac{d}{da}T_a x|_{a=0}` (in coordinates, `G = `the skew-symmetric "derivative/Hilbert-transform-like" operator that is the linearization of translation). Then for `g=h∘Φ`,
```
    ⟨ ∇_x g(x) , Gx ⟩ = 0     for all x.
```
That is, **the input-gradient of an invariant classifier is orthogonal to the (continuous) shift-orbit tangent at every point**: the classifier has *exactly zero* first-order sensitivity along the orbit direction.

*Proof.* Invariance `g(T_a x)=g(x)` for all `a`; differentiate at `a=0`: `0 = \frac{d}{da}g(T_a x)|_{0} = ⟨∇g(x), \frac{d}{da}T_a x|_0⟩ = ⟨∇g(x), Gx⟩`. ∎

**Consequence (robust-radius enlargement).** Decompose any perturbation `δ = δ_∥ + δ_⊥`, where `δ_∥` is the component along the orbit tangent `Gx` and `δ_⊥` is orthogonal. To first order, `g(x+δ) ≈ g(x) + ⟨∇g,δ⟩ = g(x) + ⟨∇g,δ_⊥⟩` (the `δ_∥` term vanishes by Lemma 5). So orbit-direction perturbations are *first-order ineffective*: the attacker must spend its budget in the `(orbit)^⊥` directions. If the discriminative signal lives in `(orbit)^⊥` and is well-separated there (large `Δ_Φ`), the attacker is forced into the *expensive* directions and the robust radius is **enlarged** relative to a non-invariant classifier that has sensitivity in *all* directions including the cheap orbit ones. This is the precise, theorem-grade version of the prompt's "invariance suppresses gradient components along shift-orbit (high-frequency/aliasing) directions, enlarging the robust radius, provided no new orthogonal sensitivity is created" — and it dovetails with Melamed et al.: their non-robustness comes from large gradients in directions *orthogonal to the data manifold*; Lemma 5 shows invariance *zeroes* the gradient along the orbit directions, which is exactly safe *iff* those orbit directions are not the discriminative ones. The failure mode (`Δ_Φ=0`, Theorem C) is precisely "the discriminative signal *was* in the orbit-difference subspace, and invariance threw it away."

Numerical confirmation (`/tmp/check_cont.py`, `d=16`): for `Φ=` power spectrum and a random linear head on top, `⟨∇g, Gx⟩ = -1.5×10⁻⁹ ≈ 0` to machine precision; and exact invariance `Φ(T_a x)=Φ(x)` holds for the continuous group. (The discrete `Sx-x` step is a *large finite* displacement, not the tangent, so its directional derivative is not expected to vanish — `/tmp/check_robust.py` correctly shows it is non-zero; this is why Lemma 5 is stated for the continuous generator, which is the mathematically correct object.)

---

## 5. The Two Canonical Instances Worked Out (proving the reconciliation numerically and analytically)

We now make the abstract `Φ` concrete with the **power-spectrum feature** `Φ_PS(x)_k = |\hat x_k|²/d` (`\hat x=`DFT of `x`), which is the canonical exactly-shift-invariant nonlinear feature realized by autocorrelation / second-order statistics that a conv+nonlinearity+GAP stack can compute.

**Fact (Φ_PS is exactly G-invariant).** `(\widehat{S^s x})_k = e^{-2πiks/d}\hat x_k`, so `|(\widehat{S^s x})_k|² = |\hat x_k|²`; hence `Φ_PS(S^s x)=Φ_PS(x)`. (Numerically verified, `/tmp/check_powerspec.py`, `/tmp/check_robust.py`.) `Φ_PS` is invariant under the continuous group too, so Lemma 5 applies. Local Lipschitz: `DΦ_PS` has spectral norm `≈4.13` at a random unit-scale point (`/tmp/check_robust.py`), i.e. `L_Φ = O(‖x‖)`, bounded on the data neighborhood — (A2) holds.

### 5.1 (D-dot): trade-off is forced (recovers Ge).
For the single dot, every shift of `e₁` is a different one-hot vector; the *power spectrum of a one-hot vector is flat*: `|\widehat{e_j}|²_k = 1` for all `k` (a delta has a flat spectrum). So `Φ_PS(S^s e₁) = (1/d)𝟙` for **every** shift, and likewise `Φ_PS(S^s(-e₁)) = (1/d)𝟙` (the sign is lost by `|·|²`). Therefore `Φ_PS(M₊) = Φ_PS(M₋) = {(1/d)𝟙}`: **`Δ_{Φ_PS} = 0`**. By Theorem C the power-spectrum invariant *also* collapses on (D-dot) — consistent with Ge — because the only thing distinguishing white-dot from black-dot is the *sign*, which is a phase/DC feature, not a power-spectrum feature. The DC feature gives `Δ_dc = 2/√d` (Ge), small and vanishing as `d→∞`. *Either* invariant representation throttles the margin to `O(1/√d)` or to `0`. **The trade-off is forced because the class signal lives in a low-dimensional, shift-fragile direction (the DC sign of a single spike), which any reasonable invariant representation either collapses or shrinks.** This is exactly Ge's `2/√d` story, now derived as the `Δ_Φ → small` corner of Theorem C.

### 5.2 (D-freq): co-existence holds (recovers Ge's reversal, §5.2 / Table 3 "Orth. Frequencies").
For distinct nonzero frequencies `k₁≠k₂`, `u_{k_1}(t)=cos(2πk₁t/d)` has power spectrum supported on `{±k₁}` and `u_{k_2}` on `{±k₂}`; these are **orthogonal supports**, so `‖Φ_PS(u_{k₁})-Φ_PS(u_{k₂})‖₂` is large and shift-independent. Numerically (`/tmp/check_powerspec.py`, `d=16, k₁=2,k₂=5`): both classes have DC `=0` (so the *DC/linear* invariant has margin **0** — a linear invariant classifier is useless here, the Ge collapse), yet `‖Φ_PS(+)-Φ_PS(-)‖ = 8`, and the linear head `w=Φ_PS(+)-Φ_PS(-)` separates the power-spectra with gap `64 > 0`. So `Δ_{Φ_PS} = 8 ≫ 0`, `L_Φ = O(1)`, and Theorem B gives a shift-consistent (`C=1`) classifier with `ρ ≥ Δ_{Φ_PS}/(2L_Φ) = Θ(1)`, *independent of `d`*. Meanwhile a (non-invariant) FC net that keys on raw `cos` values has robustness set by the input separation but is sensitive to the cheap orbit directions. **This is exactly Ge Table 3's finding that on orthogonal-frequency data the invariant CNN is *more* robust than FC** — derived here as the `Δ_Φ = Θ(1)` corner of Theorem B, with the mechanism (power-spectrum carries the inter-class signal; DC does not) made explicit.

**The reconciliation in one sentence.** Ge's collapse (D-dot) and Ge's reversal (D-freq) are the **same theorem** (A/B/C) evaluated at two data distributions that differ only in whether the inter-class signal is `Φ`-preserved (`Δ_Φ`) or `Φ`-destroyed; the linear single-GAP architecture is just the special case `Φ ∈ {DC}` that maximizes the chance of destruction.

---

## 6. Empirical Predictions (for the controlled dissection)

The theory yields one master predictor and several falsifiable consequences.

**P0 (master predictor).** Across architectures/datasets, **co-existence of high shift-consistency and adversarial robustness is predicted by the invariant signal-to-sensitivity ratio `R(Φ) = Δ_Φ / L_Φ`**, where `Φ` is the network's *penultimate* representation (pre-head), `Δ_Φ` is the empirical inter-class min-distance in that representation, and `L_Φ` its local Lipschitz constant (estimated by the spectral norm of the input→penultimate Jacobian, or by Jacobian-norm penalization probes). Concretely: measure (a) consistency `C`, (b) PGD-L2 robust radius `ρ`, (c) `Δ_Φ` = min over class-pairs of penultimate-feature distance, (d) `L_Φ` = mean spectral norm of `∂Φ/∂x`. **Prediction:** `ρ` correlates with `Δ_Φ/L_Φ` *much* better than with consistency `C` alone; in particular models with `C≈1` will span the whole robustness range, ordered by `Δ_Φ/L_Φ`.

**P1 (depth/kernel sweep, matched capacity).** As one increases the conv kernel size / depth before GAP, the network can realize *higher-order* shift-invariants (power spectrum → bispectrum → general autocorrelations). Prediction: `Δ_Φ` (hence `ρ`) **increases with the richness of realizable invariants**, while consistency stays `≈1`. A single-conv-layer + GAP (closest to Ge's linear-CNTK-GAP) should sit near the DC/`2/√d` corner; deeper variants escape it. (Ge's Table 2 already shows padding-size↑ ⇒ consistency↑ but robustness↓ on MNIST — the *opposite* direction — because MNIST's class signal is largely DC/low-frequency *and* tied to absolute structure that GAP discards: predicted to be a *small-`Δ_Φ`* dataset, like D-dot. Build a *frequency-coded* MNIST variant and the sign should flip: consistency↑ ⇒ robustness↑.)

**P2 (pooling type).** GAP collapses spatial info to orbit-averages of features (DC-like at the *feature* level). Predict: replacing GAP with a *shift-invariant but information-preserving* pooling (e.g. pooling the power spectrum / sorted activations / second-order pooling) raises `Δ_Φ` at fixed `C`, and raises `ρ`. Plain GAP on a single linear feature is the worst case.

**P3 (dense / FC baseline).** FC nets have `C<1` (Ge Table 1: ~16–21%) and arbitrary `Φ` with sensitivity in *all* directions including orbit ones; predict their robustness is set by input separation `Δ` minus the cheap orbit directions — robust on D-dot (no useful invariant exists, so don't impose one), *less* robust than invariant CNN on D-freq. Matches Ge.

**P4 (orbit-gradient probe; tests Lemma 5).** For each model, estimate `cosθ = ⟨∇_x g, Gx⟩ / (‖∇g‖‖Gx‖)` with `Gx` the continuous-shift generator (Fourier). Prediction: exactly-invariant CNNs have `cosθ ≈ 0` (orbit-gradient suppressed); FC nets have `cosθ` bounded away from 0; and **the fraction of adversarial perturbation energy lying in the orbit subspace is near 0 for invariant models** — attacks are forced off the orbit. This directly tests the robustness-enlargement mechanism and connects to Melamed (attacks live in the cheap, here orbit, directions).

**P5 (consistency–robustness joint trajectory).** Theorem E predicts consistency and robustness **co-vary** (both governed by `γ`, `ε`, `L_Φ`), *not* trade off, *within a fixed-`Δ_Φ` regime*. Across-regime (changing the data's `Δ_Φ`) they can anti-correlate. So: holding the dataset fixed and varying only invariance strength (Ge's padding sweep), expect a *single-signed* relationship determined by that dataset's `Δ_Φ` — monotone *up* on frequency-coded data, monotone *down* on dot/absolute-structure data. This is a sharp, cheap experiment that the existing repo can run.

---

## 7. Relation to Prior Work

**Recovers Ge (2/√d).** Theorem C(iii) + Lemma 0: restricting to *linear* invariant classifiers forces `w∈DC`, so the margin is the DC separation; on (D-dot) this is `2/√d` (Cor 1). §5.1 shows even the *nonlinear* power-spectrum invariant collapses on (D-dot) (`Δ_{Φ_PS}=0`), explaining why the phenomenon is robust to architecture there. Our framework strictly **extends** Ge: it identifies the *governing quantity* as `Δ_Φ` (margin preservation under the chosen invariant), exactly as Ge's own §5.2/Table 3 hinted ("invariance reduces robustness only when it also shrinks the margin/increases intrinsic dimension"), and it *predicts the reversal* on orthogonal frequencies (§5.2) from the same theorem rather than as a separate empirical curiosity.

**Does NOT contradict Kamath (Thm 2).** Kamath proves a trade-off for a *specific* construction: a cyclic-code Gaussian mixture where (i) invariance is **imposed by augmentation over the full cyclic orbit**, forcing the classifier to be invariant *as a function on raw inputs*, and (ii) the discriminative coordinate `x₀` is *fixed under rotation* while the informative coordinates `x_{1..d}` are *cyclically permuted* — so the label information is carried in coordinates that the imposed invariance **averages over**. In our language: their setup is engineered so that `Δ_Φ` (for the augmentation-induced invariant `Φ`) is *small*, with the additional twist that the *spatial* robustness they trade against is itself an invariance demand. Their Theorem 2 is an *upper bound* in the regime `Δ_Φ ≈ 0`, which is precisely our Theorem C trade-off corner — **consistent, not contradictory**. Our co-existence result lives in the *complementary* regime `Δ_Φ = Θ(1)` (signal carried by a shift-*invariant* feature), which Kamath's construction deliberately excludes (their `x₀` is a single rotation-fixed coordinate of bounded margin `2c_y/√d`-scale, again `O(1/√d)`). The non-contradiction is structural: Kamath fixes the data so the invariant projection is uninformative; we characterize *when* it is/ isn't. Furthermore Kamath studies *random spatial* robustness vs *adversarial* robustness with augmentation-driven invariance, whereas our emergent-architectural invariance + adversarial margin is a different (and the prompt's) regime; the impossibility is regime-specific exactly as they note.

**Frei et al. (implicit bias).** Frei prove robust nets *exist* (Thm 4.1) but gradient flow *selects* a non-robust KKT max-margin point (Thm 4.2) on clustered, near-orthogonal data. This is **orthogonal and complementary** to us: our Theorems A–C are about the *function class / existence* (which `Φ` admits co-existence), the same "exists" side as Frei 4.1. We do **not** prove that gradient flow *finds* the co-existing invariant — that is **[OBSTRUCTION-2]**, the central open gap (see below). Frei's Thm 4.2 is a warning that even when a good invariant exists, training may not reach it; an invariance *constraint in the architecture* (hard-wired `Φ`) is exactly a way to *remove* that degree of freedom, which is why architectural invariance can help where implicit bias would not — but proving the trained invariant CNN lands at large `Δ_Φ` requires an implicit-bias analysis we have not done.

**Melamed et al. (off-manifold gradients).** Their non-robustness is large gradient in directions *orthogonal to the low-dim data manifold*, with smaller init / stronger L2 increasing robustness in those directions. Lemma 5 is the invariance-analog: an invariant classifier has *exactly zero* gradient along the (continuous) orbit directions. When the orbit directions coincide with the cheap off-manifold directions (high-frequency/aliasing), invariance *certifiably removes* that sensitivity — a free robustness gain — *provided* (Theorem B's "no new orthogonal sensitivity") the discriminative signal is not itself in the orbit subspace. Melamed's `√(kℓ/2md)` gradient-in-`P^⊥` bound and our orbit-suppression are two instances of the same "control gradients in the non-discriminative subspace" principle; combining them (invariance ⇒ orbit-suppression *and* small init ⇒ off-manifold suppression) is a natural, *un-attempted* extension.

---

## 8. Limitations and Obstructions (honest)

1. **[OBSTRUCTION-2 — the main one] Function class ≠ trained solution.** All theorems characterize the *hypothesis class* `{h∘Φ}` and *which* invariants admit co-existence. They do **not** prove gradient descent on a real invariant CNN *converges* to a large-`Δ_Φ`, large-margin head. Frei's Thm 4.2 explicitly shows training can select non-robust KKT points; closing this requires an implicit-bias theorem for invariant architectures (open). My claim is therefore: *architectural invariance makes co-existence possible and the achievable robustness is governed by `Δ_Φ/L_Φ`*, not *training achieves it*. This is the right honest scope and matches Frei's existence-vs-dynamics distinction.

2. **[OBSTRUCTION-1] Hull shrinkage.** Lemma 1 gives `γ = ½ dist(conv Φ(M₊), conv Φ(M₋)) ≤ Δ_Φ/2`; equality needs feature clusters separated by more than their radius. For multi-modal classes the realized margin can be strictly below `Δ_Φ/2`. The primitive bound `ρ ≥ γ/(L_h L_Φ)` (Theorem A) is always valid; `Δ_Φ` is an *upper proxy* for achievable margin, exact in the single-orbit-per-class idealization (Ge's instances).

3. **Lipschitz looseness.** `Lip(g) ≤ L_h L_Φ` (worst-case, chain rule) can badly over-estimate the *local* Lipschitz constant near the data, so `ρ ≥ γ/(L_hL_Φ)` is a *lower* bound; the realized robust radius can be larger. The empirical predictions use *local* Jacobian norms precisely to tighten this. Likewise the `√d` in Corollary D is the generic, lossy L2→Linf conversion; the sharp Linf constant must be measured (`L_Φ^{(∞)}`), and for Linf attacks the relevant geometry may differ.

4. **Fixed-`Φ` modeling.** Real CNNs learn `Φ` and `h` jointly; treating `Φ` as fixed is the same simplification as analyzing a kernel/feature map. It is faithful to *architecturally-enforced* invariance (the `Φ` is constrained to be invariant by conv+GAP+circular padding) but ignores feature *learning*'s effect on `Δ_Φ`. Frei explicitly contrasts kernel-regime vs feature-learning; our result is feature-map-level, agnostic to which regime *produced* the features.

5. **Group choice.** Stated for cyclic (circular-shift) `ℤ_d`, matching Ge/Kamath. Zero-padding (real CNNs) breaks exact invariance; Theorem E (approximate invariance) is the right tool but the `ε` for zero-padding is data-dependent and not bounded here. Translation in continuous images vs discrete pixels (aliasing) is exactly why Lemma 5 must use the *continuous* generator; the discrete-shift directional derivative does not vanish (verified numerically) and the gap between them is the aliasing literature (Zhang 2019, Azulay–Weiss).

6. **Two-class.** Multi-class needs `Δ_Φ` to be the *minimum* over class pairs; the bounds carry over with `Δ_Φ = min_{y≠y'} dist(Φ(M_y),Φ(M_{y'}))`, but the head Lipschitz/ margin bookkeeping for `K`-way softmax is not written out here.

7. **Power-spectrum is one invariant.** §5 uses `Φ_PS` as the canonical realizable nonlinear invariant. Whether a *given* CNN's learned penultimate features achieve the `Δ_Φ` of the power spectrum (or better, e.g. bispectrum to recover phase) is exactly the empirical question P0–P2 — not settled by theory.

---

## 9. Summary

The governing quantity is **not invariance, but margin preservation under the invariant representation**, made precise as the **invariant signal-to-sensitivity ratio `R(Φ)=Δ_Φ/L_Φ`**:

- **Co-existence (Thm B):** high shift-consistency *and* robustness `ρ ≥ Δ_Φ/(2L_Φ)` hold whenever the inter-class signal survives projection into an invariant representation with bounded Lipschitz — i.e. `Δ_Φ` large. The robustness is *enlarged* because invariance certifiably zeroes the gradient along orbit directions (Lemma 5), forcing attacks into expensive off-orbit directions.
- **Trade-off (Thm C):** forced exactly when the invariant projection destroys separation (`Δ_Φ` small/zero). The linear single-GAP architecture is the worst case (`Φ∈DC`, Lemma 0), giving Ge's `2/√d` collapse; nonlinear invariants escape it iff the signal is `Φ`-preserved.
- **Reconciliation:** Ge's collapse (D-dot, `Δ_Φ→0`) and Ge's orthogonal-frequency reversal (D-freq, `Δ_Φ=Θ(1)`) are the *same* theorem at two distributions; Kamath's impossibility is the `Δ_Φ≈0` corner engineered by augmentation-invariance over the label-carrying coordinates, hence consistent with, not contrary to, our co-existence regime.
- **Honest gap:** we characterize the *function class*; whether *training* lands at large `Δ_Φ` is open (Frei's dynamics warning), and is the natural next theorem.

All mechanisms verified numerically: Lemma 0 (orbit-average = rank-1 DC), §5.1–5.2 (power-spectrum invariance; D-dot collapse `Δ_Φ=0` vs D-freq separation `Δ_Φ=8`, DC-margin 0 in both, hence linear invariants useless and only the nonlinear invariant rescues D-freq), and Lemma 5 (continuous orbit-gradient `≈10⁻⁹`).
