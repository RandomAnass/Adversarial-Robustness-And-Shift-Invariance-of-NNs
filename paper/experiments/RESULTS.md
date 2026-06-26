# Experiment log

## Run 1 — `synthetic_1d.py` (1-D synthetic P2 smoke test) — 2026-06-17
Env: `paper/env/cenv` (torch 2.12 CPU; **GPU unusable: driver 12080 too old for cu130 build** → CPU only for now).
Result: pipeline (PyTorch models + custom L2-PGD) works end to end. **Theory test inconclusive**, in an informative way:
- DOT: ConvGAP & FC both radius≈0.147 (grid-limited). Theory: invariant ~1/√d≈0.125, FC max-margin ~1. The trained FC did NOT reach its robust max-margin → **optimization/implicit-bias gap demonstrated** (function class ≠ trained solution).
- FREQ: both saturated ε-grid (max 1.5 ≪ ‖x‖≈5.8); and the "FC" here is 2-layer ReLU (can fit freqs), not the theory's *linear* FC → object mismatch.

## Run 2 — `structural_margins.py` (training-free structural test) — 2026-06-17  ✅ THEORY CONFIRMED
| dataset | Sep(Id) | Sep(Pi_inv=DC) | eta_Psi(PS) | eta/L |
|---|---|---|---|---|
| DOT (+e0/-e0) | 1.000 | **0.125 = 1/sqrt(d)** | **0.000** (sign-blind) | 0 |
| FREQ-single | 0.000 | 0.000 | 361.9 | 3.10 |
| FREQ-spans (Ge real odd/even) | 0.000 | 0.000 | 5.75 | 0.378 |

Confirms corrected theory exactly, no training: (1) Theorem A — invariant linear margin = 1/sqrt(d) for the dot (FC=1). (2) Power spectrum is sign/phase-blind: Sep_Psi=0 for the dot (nonlinear escape fails for localization/phase-coded signal). (3) Reversal: on frequency data NEITHER linear classifier separates (Sep(Id)=Sep(DC)=0) but the power-spectrum invariant does (eta/L>0) -> invariance helps via the RIGHT invariant feature. (Bug fixed from the stalled runs: SVC needed max_iter cap + degenerate/non-separable -> 0; Sep(Pi_inv) computed via Theorem A closed form, not standardized SVC.)

## Run 3 — `dissection.py` MNIST sweep (GPU, 7 cfg x 3 seeds, n=16k, 25ep) — 2026-06-17  ✅ P6 CONFIRMED
HEADLINE: **eta/L predicts robustness; shift-consistency does NOT.** Pearson r across 7 configs:
  consist vs rob_L2 = -0.289 ; **eta/L vs rob_L2 = +0.968** ; consist vs rob_Linf = -0.147 ; eta/L vs rob_Linf = +0.642.
Per-model: conv_d1_k5_gap has consist=1.000 but LEAST robust (rob_L2 0.044, eta/L 0.37) = cleanest "consistency != robustness". Multi-layer convs both moderately consistent (~0.49) AND robust (rob_L2 0.38-0.58), highest eta/L (1.47-1.69); +dense most robust (0.579). BN 2x2 (Galloway): BN raised clean but LOWERED rob_L2 (FC 0.063->0.049; conv-gap 0.044->0.025) = Galloway effect reproduced.
CAVEATS for the paper sweep: (1) conv_d1_k5_gap underfits (clean 0.569, only 4.6k params) — bump h to ~512 for fair clean acc (still a valid low-eta/L point). (2) params NOT matched (FC 269k vs conv_d1 4.6k vs conv_d2 211k vs dense 953k) — match capacity for the "matched-capacity" claim. (3) rob_Linf at eps=0.2 near 0 for most; L2 (eps 1.5) is the discriminating metric. TODO: matched-capacity re-run + Fashion-MNIST + AutoAttack + CIFAR (all GPU now).

### Design fixes for Run 2 (decouple structure from optimization)
1. **Structural test (tests Thm A/B/C directly, no training confound):** compute via hard-margin SVM — Sep(Id) [unconstrained], Sep(Π_inv) [DC-projected = f_dc gap], Sep_Ψ [power-spectrum features]. Verify: DOT → Sep(Π_inv)=Θ(1/√d) small; FREQ → Sep(Π_inv)≈0 but Sep_Ψ=Θ(1). This is the clean P2/P1 test.
2. **Match theory objects:** include LINEAR-invariant (conv+GAP, no ReLU) and LINEAR-FC for Thm A; nonlinear ConvGAP for Thm C.
3. **Min-norm attack** (DDN/CW-style) for a real per-sample robust radius, not a coarse ε grid; scale ε to ‖x‖.
4. **Optimization-gap study (separate):** trained-net realized radius vs achievable max-margin → quantify the gap (this is itself a finding, ties to Frei/Min&Vidal).

## Run 4 — `dissection.py` robust-RADIUS metric, MNIST + Fashion (GPU) — 2026-06-17  ✅ P6 CONFIRMED BOTH DATASETS
Switched primary metric from fixed-eps robust ACCURACY (floor artifact on FMNIST) to per-sample min-flip L2 RADIUS (rr_L2; dataset-comparable; eta/L is its lower bound). Result:
  MNIST   : eta/L vs rr_L2 Pearson +0.968 Spearman +0.964 ; consist vs rr_L2 -0.569 / -0.306
  FASHION : eta/L vs rr_L2 Pearson +0.511 Spearman +0.714 ; consist vs rr_L2 +0.103 / 0.000
=> eta/L predicts robust radius on BOTH (strong MNIST, moderate FMNIST); consistency on NEITHER. The earlier FMNIST "consistency wins" was the fixed-eps floor artifact (secondary fixed-eps line: consist vs rob_L2 +0.669). Methodology fix validated. Per-model numbers in paper/results/dissection_radius.log.
NEXT (await user word for the big push): capacity-matched configs + AutoAttack + CIFAR; decompose eta/L into margin eta vs Lipschitz L per model (does conv-GAP win by bigger margin or smaller L? is BN's penalty an L effect?).
