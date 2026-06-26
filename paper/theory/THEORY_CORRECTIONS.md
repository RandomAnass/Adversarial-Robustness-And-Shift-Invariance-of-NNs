# Theory corrections log (external audit, verified firsthand)

Date: 2026-06-17. An external review of `paper/report/theory_full.tex` caught real errors.
Each load-bearing correction below was re-derived/verified firsthand with a NumPy script
(d=64) before integration. Corrected doc of record: **`paper/report/theory_full_checked_v2.tex`**
(compiles, 18pp). Paper `paper/report/main.tex` updated to match (compiles, 7pp).

## Corrections (all accepted)

1. **Invariant linear margin = projected convex-hull distance, NOT one-sided DC gap.**
   The uploaded `½(min_{X+} f_dc − max_{X-} f_dc)_+` is correct only when X+ lies above X−
   in DC coordinate. Correct: `γ_inv = ½ dist(conv Π_inv X+, conv Π_inv X−) = ½ dist(I+, I−)`
   (distance between the two DC intervals; the one-sided form is a special orientation).
   Holds for any finite separable dataset, orbit-closure not required.

2. **Margin-ratio corollary had a spurious √d factor and was orientation-dependent.**
   With `e = 1/√d`, `f_dc = eᵀx`, there is no √d on the RHS. The clean statement is
   `γ_inv ≤ γ_full` by non-expansiveness of orthogonal projection.

3. **Power-spectrum lemma: real filters span conjugate-pair sums, not individual freqs.**
   A real filter has `|ŵ_k|² = |ŵ_{d−k}|²`, so it spans `|x̂_0|²`, `|x̂_{d/2}|²` (d even),
   and pair-sums `|x̂_k|² + |x̂_{d−k}|²`; since x is real these exhaust its power spectrum.
   A *complex* filter isolates a single `|x̂_k|²`. ("spans exactly {|x̂_k|²}" was an overclaim.)
   Verified: `|ŵ_k|² == |ŵ_{d−k}|²` for real w → True.

4. **η/L is a Lipschitz–margin CERTIFICATE, not a characterization — NO converse.**
   `r₂ ≥ η/L` is the standard lower bound. There is no universal converse: for the
   shift-invariant feature `Ψ_n(x) = t^{2n+1}` on the DC line (t = f_dc), η/L = 1/(2n+1)
   while true `r₂ = 1`, so `r₂ / (η/L) = 2n+1` is unbounded.
   Verified: ratios 3×, 7×, 21× for n = 1, 3, 10. Frame η/L as certificate + empirical predictor.

5. **The single-orbit "rank-deficiency" Proposition was FALSE as stated.**
   Replaced with the exact **orbit-rank lemma**: `rank{S_s u} = #{k : û_k ≠ 0}`.
   - Verified: cosine(k=5) orbit rank 2 (nonzero |FFT| = 2); spike rank 64; generic random
     base rank 64 (FULL) and power-spectrum separable (PS distance 549.5 > 0).
   - So generic single-orbit data is full-rank AND invariant-separable. The two *canonical*
     bases are degenerate in OPPOSITE ways: cosine → rank-2 + zero signed mean (premise of
     Frei/Li fails); spike → orthonormal but phase-blind PS, Sep(Ψ)=0 (separation fails).
   - The optimization gap is therefore OPEN on nondegenerate data, and NOT closed by moving
     to multi-orbit data.

6. **Ge "unconstrained margin = 1" is the two-image protocol.**
   `{e_j} vs {−e_j}` unconstrained margin = 1 (w = e_j). On the orbit-closed dataset
   `O(e_j) vs O(−e_j)` the unconstrained linear max-margin is ALSO 1/√d (= invariant margin,
   κ = 1). Verified: orbit-closed unconstrained max-margin = 0.125 = 1/√d. Do not conflate.

7. **Kamath reconciliation must be stated conditionally** (on their exact data model) unless
   the distribution is restated self-contained in our framework. Stated as interpretation.

## Still open / source-dependent
- Trajectory-level implicit-bias theorem for shift-invariant conv+pool nets on nondegenerate
  orbit data where the non-robustness premise genuinely holds. (Same wall as Frei/Min&Vidal/Li.)
- η/L predicting trained-model robustness is empirical/dataset-dependent (confirmed MNIST
  strong, Fashion moderate); to be hardened with capacity-matched CIFAR + AutoAttack and an
  η/L → (margin η, Lipschitz L) decomposition. See CIFAR plan §sec:cifar-plan in v2 tex.

## Must-not-claim
- Do NOT call η/L a "new robustness quantity"/characterization — it is a known certificate.
- Do NOT claim the cyclic/DC shift-invariance phenomenon as new (Ge 2021).
- Do NOT claim power-spectrum invariants as new (scattering / bispectrum / Fourier descriptors).
- Do NOT claim a discrete-shift robustness theorem from the continuous orbit-gradient lemma.
