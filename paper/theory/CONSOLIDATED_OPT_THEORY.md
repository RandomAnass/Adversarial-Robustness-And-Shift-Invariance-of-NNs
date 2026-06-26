# Consolidated Optimization Theory — Does shift-invariance re-point GD's implicit bias toward robustness?
### ⚠️ RETRACTED AFTER RED-TEAM (2026-06-17) — read this box; the body below is the superseded attempt
**The headline positive claim below ("convexification re-points the implicit bias; Min&Vidal conjecture becomes a theorem; conv-GAP is more robust") is WRONG and retracted.** A red-team + firsthand verification found a fatal 4/4-shared flaw (same blind-spot pattern as the structural theory):
- A shift ORBIT of a base pattern is RANK-DEFICIENT (a single cosine orbit is **rank 2**, verified), NOT the ~d near-orthogonal clusters Frei/Li REQUIRE. So Frei Thm4.2 / Li Thm4.5 **do not apply** to orbit data.
- On a frequency orbit, Frei's universal non-robust direction z = signed mean of cluster means is **≈0** (‖z‖=1.7e-16, verified). The attempts CELEBRATED this vanishing as the "GAP annihilates the threat" mechanism — but z≈0 means Frei's non-robustness has no content there, so the contrast is **self-cancelling**.
- No single base makes BOTH "Frei applies" (needs orthonormal, e.g. the spike orbit) AND "conv-GAP separates" (needs Δ_PS>0; the spike orbit has Δ_PS=0, phase-blind). Verified.
- The empirical "1.5–1.6× radius" is an unfair-FC-baseline + train-point-linearized-radius artifact (collapses to ~0.86–1.16 with matched budget); marked UNCONFIRMED.

**HONEST STATUS: the optimization / implicit-bias gap is OPEN.** What SURVIVES: (a) Lemma "conv-GAP = tied shift-orbit-bundle ReLU" (exact, structural); (b) the function-class characterization (= structural Theorem A restated, NOT new optimization content); (c) Δ_PS=0 phase-blindness negative; (d) **the one genuine nugget: shift orbits are rank-deficient, a degenerate corner of the Frei/Li cluster model where the non-robustness threat is identically null** — this is a correct novel *structural* observation (now Prop. in `paper/report/main.tex` §4) but does NOT close the gap. The report §4 has been corrected to this honest status. Everything below is the superseded attempt, kept for the record.

### (synthesis of opt_attempt_1..4; SUPERSEDED — see retraction box above)

**The open problem** (CONSOLIDATED_THEORY §5a): the structural theory proves robust shift-invariant classifiers *exist* (large η/L). Does gradient descent *find* them? Frei (NeurIPS'23) proved unconstrained 2-layer ReLU nets converge to a NON-robust KKT point even when robust ones exist; Min&Vidal (ICML'24) *conjectured* architecture re-points the bias; Li (ICLR'25) proved the non-robust mechanism = feature averaging + a *supervision* fix.

**Provenance:** four INDEPENDENT Opus attempts (opt_attempt_1..4.md) converged on the same answer (a conditional positive + clean negative), each verifying load-bearing steps numerically. Red-team pending (the structural theory's 4/4 shared blind spot makes this non-negotiable). Full proofs/scripts in the attempt files.

## Answer (one line)
**Yes, conditionally: hard-wired shift-invariance (weight-shared circular conv + GAP) re-points GD's implicit bias toward the robust solution AT THE MIN-NORM/MAX-MARGIN OPTIMUM, in the large-η/L (disjoint invariant-feature support) regime — turning Min&Vidal's conjecture into a theorem for the quadratic conv-GAP head — but it is a PARTIAL fix: it cannot reach Frei's universal strength, the averaging recurs within the invariant family when support overlaps (R₂∼√(d/K)), it fails on phase-coded signal (power-spectrum blind), and the full trajectory-level convergence for conv-ReLU-GAP stays open.**

## The mechanism (all 4 attempts, multiple equivalent framings)
- **Orbit-bundling (attempts 2,3):** a conv-GAP net = a 2-layer ReLU net whose neurons are forced into tied shift-orbit bundles (one filter spawns all d shifts, shared bias/output weight) [verified 1e-9]. The per-filter learning force is orbit-pooled, hence invariant.
- **Convexification (attempt 1):** for the linear/quadratic head the max-margin (Lyu-Li/Ji-Telgarsky limit) program collapses from non-convex (Frei's exponentially many KKT points) to CONVEX (unique global = SVM in invariant-feature space). Convexity removes the KKT multiplicity that powers Frei's negative result.
- **GAP annihilates the threat (attempts 1,3):** the single direction powering BOTH Frei (Thm 4.2) and Li (Thm 4.5) — neurons aligning to the signed sum of cluster means z=Σ y·μ — is exactly the orbit-mean-zero (AC) direction GAP averages to 0. The architecture computes a feature in which the threat carries no signal.
- **Orbit divided out of the averaging count (attempt 4):** weight-sharing drops the effective cluster count from K·d_orbit to K; within-class averaging then happens harmlessly in power-spectrum space (Theorem I: quadratic conv-GAP alignment diagonalizes in frequency, each mode driven by M_k=Σ y_i|x̂_{i,k}|², verified 1e-15).

## Positive result (proved at the optimum; empirically verified)
In the large-η/L / disjoint-invariant-support regime, the architecturally-cheapest (min-norm/max-margin) conv-GAP interpolant IS the robust solution. **Min&Vidal's conjecture becomes a theorem for the quadratic conv-GAP head, with spatial weight-sharing as the lever** (complementary to their pReLU activation).
Empirical verification (attempts' own scripts):
- conv-GAP min-norm radius **1.5-1.6× FC** at matched margin, using exactly **2 active O(1) filters** (one/class) = amortization (attempt 2).
- Across 8 GD restarts, conv-GAP radius distribution **does not overlap** FC's → re-pointing over *reachable* KKT points, not seed luck (attempt 2).
- Ratio **grows with d** (1.17→1.37→1.63, d=16..64) and with orbit multiplicity K (0.81→1.03→1.20→1.60, K=1,2,4,8) (attempts 2,4).
- **No advantage when Δ_PS=0** (phase-coded/antipodal dot: ratio ≈1.0) vs ~1.3 on PS-separated data → inherits the η/L master criterion verbatim (attempts 2,4).

## Negative / conditional (honest)
- (a) **Conditioned on η/L large** (disjoint invariant-feature support); on overlapping support, feature-averaging **recurs within the invariant family** over the K within-class base patterns → R₂∼√(d/K) — advantage grows with orbit size but does NOT fully close the gap to the decoupled optimum (attempt 4).
- (b) **Phase/localization-coded signal:** power spectrum is blind → quadratic conv-GAP at chance (Theorem II, attempt 4; matches structural Sep_Ψ=0 for the dot).
- (c) **Not Frei's universal strength:** does NOT reach "every KKT point is robust"; a residual averaging channel survives in the output-weight head v (attempt 2, O1).

## Open gap (remaining target)
Full **trajectory-level gradient-flow convergence for conv-ReLU-GAP** (the fitting/norm-growth phase) — the SAME wall Frei/Min&Vidal/Li all hit. Reduced here (min-norm optimum characterized; alignment force proven orbit-pooled; convexified for the quadratic head) but not removed for the ReLU head.

## Caveats to stress-test in red-team
- "Convexity" is in lifted power-spectrum coords with a gauge/nuclear-type norm; "GF→global optimum" rigorous only in mean-field/overparam-channel limit (Chizat-Bach), conjectural finite-width (attempt 1 O1).
- **k_eff = K·d_orbit is order-of-magnitude** — Frei's law assumes orthogonal clusters, but orbit elements are CORRELATED, not orthogonal (attempt 4 O2). Does the Frei reduction actually hold on orbit data? (verify)
- **min-norm optimum ≠ what finite-step GD reaches** — the positive result is about the min-norm/max-margin solution; the trajectory gap (O2) is real. Is the empirical "1.5× radius / non-overlapping restarts" measuring the min-norm solution or the GD-reached one? (the restart experiment suggests GD-reached, but verify it's not an artifact of the toy/regularization.)
- discrete-vs-continuous orbit (recurring issue): is the orbit-bundling exact for the discrete cyclic group, or only continuous?
- Is "the architecturally-cheapest interpolant is robust" a genuine implicit-bias statement or a restatement of the structural Theorem A in min-norm clothing? (i.e., does it add optimization content beyond the function-class result?)

## Surviving claim set (pre-red-team)
1. Orbit-bundling / convexification mechanism (the architecture maps the head to invariant-feature space and annihilates the Frei/Li threat direction). 
2. Min-norm positive result for the quadratic conv-GAP head in the large-η/L/disjoint regime (Min&Vidal conjecture realized).
3. η/L conditioning (Δ_PS=0 ⇒ no advantage) — empirically verified.
4. Empirical scalings (radius ratio grows with d and K; non-overlapping restarts).
5. Honest negatives (√(d/K) recurrence; phase-blindness; not Frei-universal; trajectory gap open).

**Next:** red-team this (hunt the shared blind spot — esp. the k_eff/orthogonality assumption on correlated orbits, and whether the positive result adds optimization content beyond structural Thm A); then the MNIST/FMNIST dissection (which tests the empirical predictions at scale).
