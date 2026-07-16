# DESIGN: MNIST/Fashion gradient-anisotropy eps-sweep

## Question
Does the empirical law "among already-robust models, LOWER gradient anisotropy
A = ||grad M||_1 / ||grad M||_2 => MORE robust" generalize to a third, LOW-DIMENSIONAL
model family (MNIST + Fashion-MNIST small CNNs), when the models span a WIDE robustness
range driven by varying adversarial-training strength (eps)?

The law already replicated on CLIP encoders (Spearman ~ -0.65/-0.76) and RobustBench
CIFAR-10 (Spearman -0.791). A pilot on the EXISTING single-eps MNIST/Fashion AT grids
found A NULL (+0.035 / -0.044), but those grids vary only arm/width/seed at ONE eps, so
the robustness axis is narrow and A barely moves. That grid cannot test the law fairly.
This experiment gives it a fair test by making eps the driver.

## Grid (per dataset)
- arm = standard only (so variation is driven by AT strength, not architecture)
- widths = {32, 64}
- seeds = {0, 1}
- MNIST  Linf eps in {0.05, 0.1, 0.15, 0.2, 0.3, 0.4}
- Fashion Linf eps in {0.02, 0.05, 0.1, 0.15, 0.2, 0.3}
=> 4 cells x 6 eps = 24 model cells per dataset.

Recipe matches the repo's MNIST/Fashion Linf AT recipe: 30 epochs, n=50000, PGD-AT with
steps=10, alpha=2.5*eps/steps (per-eps), flip=False. Each eps runs as a SEPARATE invocation
with its own tag `anisosweep_e<eps>` so the progressive-save partial files (keyed by
arm/w/seed, NOT eps) do not collide.

## Robustness metrics (comparable across models -> no cherry-picked eval-eps)
(a) rr_l2  : DDN L2 robust radius (per-sample min-norm distance to boundary). Metric-free,
    cross-model comparable. PRIMARY.
(b) aa_*   : AutoAttack robust accuracy at a FIXED sweep of eval-eps applied IDENTICALLY to
    every model (via new additive `--aa_eps` flag in cifar_at.py). Reported at EACH eval-eps.
    MNIST eval-eps {0.1, 0.2, 0.3}; Fashion eval-eps {0.05, 0.1, 0.15}.
    aa_n = 1000 test points (per-sample robust acc; enough to rank), rad_n = 1000.

## Measurements per cell (already logged by cifar_at.py)
A = dec_L1/dec_L2, eta/L = dec_etaL, consist, clean, rr_l2, dec_margin, dec_L1, dec_L2,
pgd_* and aa_* at each eval-eps.

## Analysis (aniso_sweep_analysis.py, self-contained)
Across all 24 cells per dataset:
- Spearman(A, robust)          [hypothesis NEGATIVE]
- Spearman(eta/L, robust)      [control, expect POSITIVE]
- Spearman(consist, robust)
- partial(A, robust | clean)   [rank-partial, rules out clean-acc confound]
- A range and robust range (is the axis wide enough?)
Every correlation recomputed two independent ways (scipy vs manual rank+pearson), must agree.
Mechanism probes: Spearman(train_eps, A), Spearman(A, rr - margin/L1) (effective-dim gap).

## Sanity / rigor
- aa <= clean, aa <= pgd (no gradient masking), aa monotone decreasing in eval-eps -- checked.
- No cell dropped silently; failures printed.
- git SHA, full commands, seeds, configs logged in the report.

## Honest outcomes (all reportable)
1. A ranks robustness negatively over the wide eps-sweep -> law generalizes to low-dim.
2. A still does not rank -> law has a boundary condition (needs high d / arch diversity,
   not just AT strength). Honest limitation.
3. Mixed -> report exactly what holds.
