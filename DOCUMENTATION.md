# Shift-Invariance and Adversarial Robustness — Project Documentation

One consolidated document for collaborators. It replaces the scattered progress/notes
markdowns. Covers: what the project is, what is proven, what was measured, what is uncertain,
and where to go next. Companion documents: `paper/main.pdf` (the paper) and
`technical_report/technical_report.pdf` (standalone theory with all definitions and full proofs).

---

## 1. One-paragraph summary

Whether shift-invariance helps or hurts adversarial robustness is contested (Ge et al. 2021:
invariance *reduces* robustness; anti-aliasing work: invariance *helps*). We organise both
regimes around one quantity, the margin-to-Lipschitz ratio **η/L** of the data in the invariant
feature space: a shift-invariant linear classifier separates classes only through their
projection onto the invariant subspace (exact margin identity); a conv+square+pool layer computes
the power spectrum; a degree-3 bispectrum invariant separates even the localized/phase-coded case.
η/L is a Lipschitz–margin **certificate** (no general converse) that also **predicts** trained-model
robustness. Empirically (training-free + MNIST/Fashion + capacity-matched CIFAR-10 + PGD
adversarial training), **η/L predicts the robust radius/accuracy while shift-consistency does
not** (it anti-predicts). The decomposition attributes mechanism: anti-aliasing acts on the
Lipschitz term, exact invariance costs margin. On optimization we **prove invariance is
margin-free on orbit-closed data** (so gradient descent self-symmetrizes) and find it **does help
on cluster-geometry data**; the trajectory-level selection theorem there is open.

---

## 2. Theory: what is proven (full statements + proofs in the technical report)

- **Invariant linear margin (Theorem, finite group).** The max invariant ℓ2 margin is
  ½·dist(conv P_G X₊, conv P_G X₋), the distance between the group-average-projected class hulls;
  cyclic case = the DC-interval distance. (Corrected from the earlier one-sided DC gap.)
- **η/L is a certificate, not a characterization.** r₂ ≥ η/L (Lipschitz–margin), but there is
  **no general converse**: for Ψ(x)=tⁿ on the DC line, the true radius exceeds η/L by an unbounded
  factor (verified: 3×, 7×, 21×).
- **Power-spectrum span.** conv+square+GAP computes Σ|ŵ_k|²|x̂_k|²; real filters span the
  conjugate-pair power coordinates (not arbitrary single frequencies).
- **Bispectrum (positive, constructive).** The degree-3 bispectrum is shift-invariant and
  **separates phase-coded classes the power spectrum cannot** — e.g. the Ge dot ±e_j (identical
  power spectra, B₀₀ = ±d^−3/2), at the cost of a larger Lipschitz constant.
- **Orbit-rank lemma.** rank of a cyclic orbit = #nonzero Fourier coefficients; generic
  single-orbit data is full-rank and power-spectrum-separable (corrects an earlier false
  "rank-deficiency" claim).
- **Self-symmetrization (positive, proven).** On orbit-closed data, shift-invariance is
  **margin-free**: the invariant (tied) and unconstrained two-layer-ReLU max-margin values
  coincide (orbit-average → invariant solution of equal minimum norm, via per-neuron 2|a|‖w‖
  balancing). Verified numerically to machine precision. Explains the generic-orbit experiment.
- **Orbit-flip bound (Tramèr formalization).** ρ_G(x) upper-bounds the oracle-robust radius of an
  invariant classifier; η/L controls sensitivity-based attacks, ρ_G the invariance-based ones.
- **Recoveries.** Ge collapse recovered (γ_inv=1/√d; the "margin 1" is the two-image protocol,
  orbit-closed gives 1/√d too). Kamath stated as a conditional small-η/L instance.

**Open / conjectured.** (i) Cluster-geometry selection theorem (Conjecture: on near-orthogonal
cluster-geometry orbit data, tied GF reaches larger η/L than unconstrained — empirically true,
20–60%, lazy-strongest). (ii) Bispectrum certified-radius construction. (iii) A trajectory-level
implicit-bias theorem identifying *which* KKT solution GD selects on cluster data.

---

## 3. Experiments and results

| regime | finding | numbers |
|---|---|---|
| Training-free structural (SVM margins) | confirms the theory exactly | dot: Sep(Id)=1, Sep(DC)=1/√d, Sep(PS)=0; freq: only PS separates |
| MNIST / Fashion dissection | η/L predicts robust **radius**; consistency does not | η/L vs rr_L2 Spearman 0.96 (MNIST) / 0.71 (Fashion); consist −0.31 / 0.00 |
| **CIFAR-10 capacity-matched** (4 arms × 2 widths × 3 seeds) | η/L predicts radius; consistency anti-predicts; mechanism split | η/L vs rr_L2 **Pearson 0.998**; consist −0.55; anti-aliasing→L↓, exact-cyclic→margin↓ |
| DDN radius validation | radius not gradient-masking-inflated | matches AutoAttack at small ε to mean gap **0.014** (max 0.025); DDN vs analytic 0.8% |
| **CIFAR-10 PGD-AT** (Linf 8/255) | AutoAttack informative; consistency anti-predicts; threat-matched η/L predicts | AA 27–41%; consist vs AA **−0.88**; η/‖∇M‖₁ vs AA **+0.90** (L2 ratio 0.62) |
| **P4 synthetic** (unconstrained vs tied ReLU) | **dichotomy** | generic orbit: unc≈tied (margin-free, proven); cluster-geometry: tied η/L 20–60% > unc, lazy-strongest |

Key methodology choices: per-sample **robust radius** (DDN min-norm) is the dataset-comparable
metric (fixed-ε accuracy floors); under AT, **match the certificate norm to the threat**
(Linf-AT → use ‖∇M‖₁, the Linf dual). Capacity is matched by construction (identical channel
schedule → identical parameter counts across arms).

---

## 4. What is uncertain / caveats (kept honest)

- The exact-cyclic arm **underfits under adversarial training** (clean 0.57–0.63 vs 0.69–0.77),
  so part of its robustness deficit is reduced capacity, not pure margin geometry. The
  consistency anti-prediction and threat-matched η/L law are not explained by clean accuracy.
- η/L is a **certificate + empirical predictor, not a tight characterization** (no converse).
- The cluster-geometry positive result is 3 seeds, one construction (single-frequency orbits);
  promising, not yet a theorem.
- The CIFAR study uses **standard and PGD-AT** at two widths only; larger backbones and
  RobustBench-scale recipes are untested.
- The Galloway "BN hurts robustness" effect reproduces under **fixed-ε accuracy** but reverses
  under the **radius** metric — i.e. it is partly a threshold artifact here.

---

## 5. Potential next experiments / avenues to explore

1. **Cluster-geometry selection theorem (highest value).** Prove the tied network reaches a
   higher-η/L KKT point on near-orthogonal cluster-geometry orbit data, using the explicit ReLU
   KKT systems (technical report) + a frequency-domain reduction; the lazy regime shows the
   largest gap, so start there. This is the open positive theorem.
2. **Bispectrum certified robustness.** Turn the bispectrum separation into a certified-radius
   construction; quantify the margin gained vs the larger (O(B²)) Lipschitz cost.
3. **Larger-scale AT.** ResNet backbones, longer PGD-AT, RobustBench submission-grade numbers;
   test whether the threat-matched η/L law and the consistency anti-prediction persist.
4. **Beyond cyclic shift.** The finite-group margin theorem is general; test rotation/scale
   groups (G-CNNs) — does the η/L law and the margin-free phenomenon carry over?
5. **Multi-orbit cluster geometry on real data.** Construct a real-data analogue of the
   cluster-geometry regime to see the invariance advantage outside synthetic data.
6. **Self-symmetrization beyond orbit-closed.** Does GD approximately self-symmetrize on
   *augmented* (not orbit-closed) data? Ties to the augmentation-vs-architecture question.

---

## 6. File map

- `paper/main.tex` — the paper (11pp); `paper/main.pdf` compiled.
- `technical_report/technical_report.tex` — standalone theory, all definitions + full proofs (25pp).
- `paper/figures/` — all figures incl. the concept schematic source (`concept.tex`) and the
  unused `cifar_at_decomp.pdf`.
- `twopager/` — 2-page project summary.
- `literature/` — 40 PDFs in subfolders + `INDEX.md` (priority-tiered, must-read first).
- `REPRODUCE.md` — how to regenerate every result (code is on git branch `cifar-dissection`).

Code and raw results live on the git branch `cifar-dissection` of the project repository
(`RandomAnass/Adversarial-Robustness-And-Shift-Invariance-of-NNs`); see `REPRODUCE.md`.
