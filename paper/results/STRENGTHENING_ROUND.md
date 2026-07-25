# Strengthening round (reviewer-driven), 2026-07-22

All numbers verified firsthand. Scripts:
- `llm_transfer/pilots/c1_tower/robustbench_val/anisotropy_strengthening.py`
- `paper/results/dissection_clean_partials.py`
(full-AA prompt-conditioned validation still running on GPU 0, tag pcAAfull.)

## 1. Anisotropy — model-size/family confound + falsifiability (R1/R2/R3)
Target = OFFICIAL RobustBench AutoAttack acc (n=30, all present) — also answers in-house-vs-official.
- Spearman(A, robust) = **-0.791** (reproduces headline).
- partial | clean = -0.764 (p=1.4e-6).
- **partial | clean, size = -0.694 (p=4.1e-5)** — survives model-size control. (A~size = -0.64, so size IS a partial confound, but A carries robustness info beyond it.)
- partial | clean, size, eta/L1 = -0.595 — survives ALL controls.
- **Within-family WRN (n=22): Spearman(A, robust) = -0.673 (p=6.1e-4)**, partial|width -0.628 — A ranks inside one family.
- **Held-out (LOO) predictive validity** [answers "free constant C is unfalsifiable"]: predicting robust acc from [eta/L1] gives LOO Spearman +0.668; adding A -> **+0.738, LOO MSE -30.4%**. A improves OUT-OF-SAMPLE prediction => real signal, falsifiable.
- Deficit-law C refit on RobustBench is DEGENERATE (C -> grid floor) because robust *accuracy* at fixed eps is not the per-model *radius* the law concerns. DROP the C-refit; report the held-out result instead (honest).

## 2. Dissection clean-accuracy partials (R2: control done for RobustBench, not dissection)
Effective n = 8 arm×width cells (seeds aggregated) — this IS the effective-n R2 flagged.
- **STANDARD dissection** (clean spread 0.05): Pearson(eta/L2, rr_l2) +0.998; **partial|clean +0.994 (p<1e-3)**; consistency partial|clean -0.586 (n.s.).
- **AT dissection** (clean spread 0.21, the big gap R2 cited): Pearson(eta/L1, AA_Linf) +0.884; **partial|clean +0.948 (p=1e-3)**; consistency **partial|clean -0.856 (p=0.014)** — consistency anti-predicts robustness even controlling clean.
- Caveat: in the AT arms clean & AA-robust are ~rank-identical (Spearman +1.0), so partials are on residual variance; direction/sign robust, magnitudes noisy at n=8.

## Net effect on the reviews
- R1 "anisotropy free constant unfalsifiable" -> answered (held-out +30%).
- R2 "clean-acc confound in dissection" -> answered (partials survive both dissections).
- R2/R3 "size/family confound" -> answered (partial|size -0.69, within-WRN -0.67).
- R2 "in-house not official AA" -> answered (used official AA, -0.79).
- R2 "effective n" -> stated honestly (n=8 dissection cells).

## Still to integrate (text/scoping + these numbers) + pending full-AA validation.
