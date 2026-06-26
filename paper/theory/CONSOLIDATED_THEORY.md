# Consolidated Theory v2 — When Shift-Invariance and L_p Robustness Co-Exist
### (corrected after adversarial red-team; supersedes v1)

**Provenance:** three independent Opus derivations (`attempt_1/3/4.md`) converged on a core theory; a hostile red-team then found 3 real issues (1 verified firsthand against Kamath). This v2 keeps what survives a hostile referee and fixes the rest. Full proofs live in the attempt files; corrections below override them where noted. Writing is provisional; correctness first.

## 0. What the red-team changed (read this first)
- **Master criterion is `Sep_inv / L` (margin-to-Lipschitz η/L), NOT `Sep_inv > 0`.** [VERIFIED firsthand against Kamath p.4] Kamath's label coordinate x₀ is *fixed by their shift* (invariant) and carries the label, so Sep_inv > 0 there (Prop 1: 97% clean acc invariantly) — yet they prove a trade-off (Thm 2) because x₀'s margin is O(1/√d). So "Sep_inv>0" cannot be the co-existence condition; the right scalar is η/L.
- **The exact `a/√2` orthogonal-frequency radius is a TOY**, not a quantitative reconciliation of Ge. [VERIFIED: Ge §5.2 p.9 defines each class as the *span of all odd (resp. even) frequencies* — a multi-frequency subspace, a cloud in power-spectrum space — not the orbit of one frequency.] The *qualitative* mechanism survives (DC=0; power-spectrum supports disjoint ⇒ Sep_PS>0 ⇒ invariant model can separate where linear FC has margin 0); the exact number does not.
- **Hull-shrinkage:** the achievable invariant margin is `γ = ½·dist(conv Φ(M₊), conv Φ(M₋))`, which equals `Δ_Φ/2` only for single-orbit-per-class; for multi-modal classes `γ < Δ_Φ/2` (can be 0 if hulls intersect). Make `γ = ½dist(conv,conv)` the primitive; `Δ_Φ` is only an upper proxy.
- **Factor-2 honesty:** half-margin `γ_inv = 1/√d`; Ge's one-sided gap = `2γ_inv = 2/√d`. State once; never write "recovers 2/√d exactly" next to the ½ formula.
- **Theorem C is demoted to a corollary** (it is the standard Lipschitz-margin implication for *any* feature map; the invariance-specific content is SC=1 + the power-spectrum span lemma, not C itself).

## 1. Setting
Inputs `x∈R^d`; cyclic group `G=Z_d`, `(S_s x)_i=x_{(i−s) mod d}`, each `S_s` orthogonal. Classes orbit-closed. `V_inv={v:S_s v=v ∀s}=span(1_d)` (DC line); `V_orb=1_d^⊥` (AC). `Π_inv=(1/d)1_d1_d^T`. `f_dc(x)=(1/√d)Σx_i`. Robust radius `r_p(f,x)=inf{‖δ‖_p: sign f(x+δ)≠y}`; for linear f, `=y·f(x)/‖w‖_q`. `SC(f)=Pr_{x,s}[sign f(S_sx)=sign f(x)]`.

## 2. SURVIVING CORE (passes hostile referee)

### Theorem A — exact invariant linear max-margin  [CORRECT, verified numerically]
A linear `g(x)=wᵀx+b` is shift-invariant ⟺ `w∈span(1_d)` ⟺ `g=c·f_dc+b`. Hence the invariant L2 max-margin is exactly
```
   γ_inv = ½( min_{x∈X_+} f_dc(x) − max_{x∈X_-} f_dc(x) )_+ = Sep(Π_inv·X),
```
optimal direction `w̄=1_d/√d`. **Holds for ANY finite separable dataset** (not just Ge's single-dot/antipodal) — this is where it genuinely beats Ge. Trade-off ratio `κ = Sep(Π_inv)/Sep(Id) ∈[0,1]`.
- **Ge recovery (honest):** single dot → `f_dc=±1/√d` → `γ_inv=1/√d`; Ge's one-sided gap `=2γ_inv=2/√d`; `κ=1/√d→0` (worst corner). Convention stated once.

### Lemma (power-spectrum span) — the real engine  [CORRECT, verified via Parseval]
Conv (circular) + ReLU/quadratic + GAP computes invariant nonlinear features; with quadratic activation, `Φ_{w,sq}(x)=(1/d)Σ_s((w⋆x)_s)² = (1/d)Σ_k|ŵ_k|²|x̂_k|²` (unitary DFT). The conv-GAP-quadratic family **spans exactly the power-spectrum features `{|x̂_k|²}`** (second-order invariants; phase/bispectrum unreachable). These live on `V_orb` for k≠0 — so a *nonlinear* invariant can separate classes whose signal the *linear* invariant (DC) discards.

### Corollary C (demoted) — conditional robust radius
For an invariant feature map `Ψ` with achievable head margin `γ=½dist(conv Ψ(M₊),conv Ψ(M₋))` and Lipschitz `L`: `r_2 ≥ γ/L` and `SC=1`. (Standard Lipschitz-margin; true for any feature map. Invariance-specific content = SC=1 and the span lemma above, not this bound.)

### Orbit-gradient suppression (scoped)  [CORRECT for continuous group]
For the *continuous* shift generator `Gx`, an invariant g has `⟨∇g,Gx⟩=0` (verified ≈1e-9). **Caveat (attempt 3, correct):** the discrete shift `Sx−x` is a finite secant, not the tangent; `⟨∇g,Sx−x⟩≠0` in general. So this certifies first-order insensitivity along the *continuous* orbit, which is not exactly the discrete threat direction. State as first-order, continuous-scoped.

### Additions from attempt 2 (all 4 attempts now converged; all 4 shared the Kamath blind spot)
- **Two-sided bound (cleaner than v1):** `Δ_Φ/(2L_Φ) ≤ ρ_inv* ≤ ½·dist(orbit(S₊),orbit(S₋))`. Lower = invariant-feature floor; upper = orbit-distance ceiling.
- **κ/λ decomposition (useful framing):** a data-only **ceiling** `κ = d_orbit/d_raw` sets whether co-existence is *possible*; a model-feature **floor** `λ_Φ = Δ_Φ/(L_Φ·d_raw)` sets whether it is *realized*. Both computable by FFT cross-correlation + nearest-neighbor, no training. (Ge freq win = high κ + high λ_ps; Ge dot = high κ but λ_dc~1/√d; this matches the η/L criterion.)
- **Power spectrum is sign/phase-blind:** `Δ_PS = 0` for the single dot (±e_a have identical power spectra), so the dot collapse holds *even nonlinearly* — separating it needs a phase-sensitive complete invariant (bispectrum), whose Lipschitz budget is uncontrolled. (Strengthens §2: the nonlinear escape works for *frequency*-coded signal, not *localized/phase*-coded signal.)
- Attempt 2 also mis-stated Kamath as "low-κ / small invariant separation" → **4/4 attempts wrong identically**; the firsthand correction (§0, x₀ shift-fixed ⇒ Sep_inv>0, small η) stands.

## 3. Master criterion (CORRECTED)
> Shift-invariance and L_p robustness co-exist when the inter-class signal is carried by a shift-invariant feature the architecture can compute **with a large margin-to-Lipschitz ratio `Sep_inv/L` (= η/L)**; they trade off when `Sep_inv/L` is small — whether because the invariant projection collapses separation (Ge single-dot, Sep_inv→0) **or because the surviving invariant feature has tiny margin** (Kamath, Sep_inv>0 but η=O(1/√d)). The measurable predictor is **Sep_inv/L, not shift-consistency, and not Sep_inv alone.**

## 4. Reconciliations (CORRECTED)
- **Ge (2021):** Thm A recovers the single-dot collapse exactly (κ→0 corner, convention noted). The orthogonal-frequency *reversal* is recovered **qualitatively** (DC=0 but Sep_PS>0 via the span lemma ⇒ invariant beats linear-FC-margin-0); the exact a/√2 is a toy illustration on single-frequency classes, dropped as a quantitative claim on Ge's multi-frequency data.
- **Kamath (2021):** [CORRECTED] their x₀ is shift-fixed (invariant) with margin O(1/√d); their Thm 2 trade-off is an **instance of our small-η/L corner**, NOT a "no invariant feature separates" case. Their impossibility is consistent with — indeed a special case of — our criterion once it is stated as η/L. (This is both correct to the source and a stronger reconciliation.)
- **Frei/Melamed (2023):** the orthogonal optimization layer (see §5).

## 5. The open gap (the novel target) — now with TWO parts
(a) **Optimization/implicit-bias [primary, all attempts agree]:** the theory characterizes the *function class* (which architectures *can* be both), not what GD *selects* (Frei: GD may pick the non-robust KKT point even when robust solutions exist). Target theorem: GD under a shift-invariance constraint converges to the large-η/L solution (Min&Vidal left the analog a conjecture).
(b) **Structural conditionals [surfaced by red-team]:** Corollary C's (γ,L) are hypotheses, not derived for a trained net; γ uses conv-hull distance (hull-shrinkage), so co-existence is `Sep_inv/L large`, an architecture+data property we must *measure*, not assume. These are not "minor" — they mean even the structural claim is conditional on measured η/L.

## 6. Empirical predictions (define the harness; CORRECTED)
- **P1 (headline):** measured robust radius is monotone in **Sep_inv/L** and predicts robustness better than shift-consistency AND better than Sep_inv alone (regression R²). Compute Sep via hard-margin SVM on (i) raw data, (ii) DC-projected data, (iii) power-spectrum features; estimate L via Jacobian norm.
- **P2:** Ge's two datasets — dot: Sep(Π_inv)=Θ(1/√d); odd/even-frequency *spans*: Sep(Π_inv)≈0 but Sep_PS>0 ⇒ invariant model more robust than *linear* FC. (Use Ge's real multi-frequency data, not single-frequency.)
- **P3 (margin sweep, NEW — tests the Kamath correction):** hold Sep_inv>0 fixed but shrink the invariant feature's margin η → robustness should fall even though consistency stays 1 and Sep_inv>0. This directly validates that η/L (not Sep_inv) is the governing scalar.
- **P4 (orbit-gradient):** invariant nets have small continuous-orbit-tangent gradient component; note the discrete caveat.
- **P5 (consistency/robustness decoupling):** SC governed by invariance defect; robustness by η/L — separately manipulable; Ge's padding "more invariant ⇒ less robust" trend should reverse on a large-Sep_PS dataset.
- **P6 (matched capacity):** across depth/kernel/pooling/dense, Sep_inv/L beats SC at predicting robust radius.

## 7. Minimal claim set that survives a hostile referee
1. Theorem A (linear, exact, any finite separable dataset; projection-operator framing beats Ge). ✅
2. Power-spectrum span lemma (the engine). ✅
3. κ→0 recovers Ge single-dot collapse (convention stated once). ✅
4. Corollary C (demoted; honest γ=½dist(conv,conv)). ✅
5. Continuous orbit-gradient=0, first-order, scoped. ✅
6. Corrected master criterion η/L; Kamath = its small-η/L instance. ✅
**Drop/qualify:** exact a/√2 as Ge reconciliation; "recovers 2/√d exactly" next to ½; "Sep_inv>0 suffices"; any ✅ on a nonlinear projection *equality* (it's ≤).

### Verification ledger (post red-team)
| step | status |
|---|---|
| Thm A formula + linear-invariant⟺w∈span(1) | ✅ verified numerically |
| Ge 2/√d (as 2·γ_inv, convention noted) | ✅ verified |
| power-spectrum span = Σ|ŵ|²|x̂|² (Parseval) | ✅ verified |
| Corollary C r≥γ/L (γ=½dist(conv,conv)) | ✅ correct but conditional (η,L hypotheses) |
| orbit-gradient=0 (continuous only) | ✅ verified; discrete caveat noted |
| a/√2 on Ge freq data | ❌ toy only (Ge data = multi-freq spans) |
| Kamath = small-η/L corner (not Sep→0) | ✅ verified firsthand (x₀ shift-fixed, p.4) |
| co-existence needs η/L large (not Sep_inv>0) | ✅ corrected |
| optimization/implicit-bias closure | ❌ OPEN (primary target) |

**Next:** incorporate attempt 2 if it adds anything; build the corrected experiment harness (structural SVM margins for P1/P2/P3 + min-norm attack + matched objects); then MNIST/FMNIST dissection. The η/L correction tightens what P1/P3 must measure.
