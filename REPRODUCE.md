# Reproduce the results

Code and raw results are on git branch **`cifar-dissection`** of
`RandomAnass/Adversarial-Robustness-And-Shift-Invariance-of-NNs` (not in this ZIP, to keep it to
paper materials). Environment: an isolated conda env with PyTorch 2.6 + CUDA 12.4, `autoattack`,
`torchvision`, `scikit-learn`, `matplotlib` (built at `paper/env/cenv`). Two RTX A6000 used.

## Script → result/figure map (all under `paper/experiments/`)

| script | produces | paper element |
|---|---|---|
| `structural_margins.py` | training-free SVM margins Sep(Id)/Sep(DC)/Sep(PS) | Table 1 (structural test) |
| `dissection.py` | MNIST / Fashion-MNIST sweep; η/L vs robust radius, shift-consistency | Table 2; `results/dissection_radius.log` |
| `cifar_dissection.py` | capacity-matched CIFAR-10 (4 arms × 2 widths × 3 seeds): clean, consistency, DDN robust radius, η/L margin/Lipschitz decomposition, AutoAttack | Table 3; `results/cifar_dissection_full_*.json` |
| `cifar_plots.py` | the two CIFAR figures + the LaTeX table + correlations + masking check | `figures/cifar_etaL_vs_radius.pdf`, `figures/cifar_decomposition.pdf` |
| `cifar_aa_calibration.py` | DDN-radius vs AutoAttack-L2 calibration at small ε (gradient-masking check) | "mean gap 0.014" sentence; `results/cifar_aa_calibration_*.json` |
| `cifar_at.py` | PGD-adversarial-training arm (Linf 8/255) + AutoAttack + threat-matched η/L | Table 4; `results/cifar_at_at_*.json` |
| `cifar_at_plots.py` | AT figure (η/‖∇M‖₁ vs AutoAttack) + table | `figures/cifar_at_predict.pdf` |
| `p4_orbit_stress.py` | P4: unconstrained vs tied ReLU on generic orbit data (rich/lazy, 1/4 orbits) | §opt generic-orbit (margin-free) finding; `results/p4_orbit_stress.log` |
| `p4_cluster.py` | P4: cluster-geometry orbit data | §opt cluster-geometry positive finding; `results/p4_cluster.log` |

## Typical invocations
```
ENV=paper/env/cenv/bin/python
$ENV paper/experiments/cifar_dissection.py            # standard-training CIFAR dissection
$ENV paper/experiments/cifar_plots.py <results.json>  # figures + table
$ENV paper/experiments/cifar_at.py --tag at           # adversarial-training arm
$ENV paper/experiments/p4_orbit_stress.py --seeds 3 --steps 8000
$ENV paper/experiments/p4_cluster.py
```
The smoke flag (`--smoke`) on the dissection/AT scripts runs a fast tiny version end-to-end.

## Documents (in this ZIP)
- `paper/main.tex` → `paper/main.pdf` (bibtex on `references.bib`, `neurips_2026.sty`).
- `technical_report/technical_report.tex` → `technical_report.pdf` (self-contained `\thebibliography`).
- `twopager/` → the 2-page summary.
Compile with `latexmk -pdf`. In Overleaf, set the main document to `paper/main.tex`
(switch to `technical_report/technical_report.tex` to build the theory report).

## Notes
- Robust radius is estimated with DDN (min-norm L2), validated against the analytic linear radius
  to 0.8% and against AutoAttack to a mean gap of 0.014.
- Capacity is matched by construction: all CIFAR arms share one channel schedule, so parameter
  counts are identical per width.
- A slow dataset mirror was worked around with parallel range downloads (see commit history).
