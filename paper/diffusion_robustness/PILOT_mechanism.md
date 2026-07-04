# Pilot: where does the diffusion-data robustness gain come from — margin or local Lipschitz?

**Status: DRAFT — Stage 1 (calibration) running; results tables and verdict filled in after the runs.**

One-seed pilot. A new research direction: decompose the adversarial-robustness gain from
diffusion-generated (EDM) training data into a **margin** term and a **local-Lipschitz / input-sensitivity**
term, using the team's existing certified-radius decomposition tool (`etaL_decomposition`,
`robust_radius_l2`). The certified-radius identity behind the split, for the smooth/locally-linear
regime around a clean-correct point, is

```
robust radius  r  >=  margin / L_local            (L_local = local input-gradient norm of the margin)
=>  d log r  ~=  d log(margin)  -  d log(L_local)
```

so a robustness gain can come from the **numerator** (the model pushes points further from the
decision boundary) or the **denominator** (the model becomes locally less sensitive / flatter), or both.
Prior diffusion-AT work (Gowal 2021, Rebuffi 2021, Wang 2023 "Better Diffusion Models Further Improve
Adversarial Training") reports the *accuracy* gain but does not attribute it to margin vs sensitivity.
This pilot asks that question with the same decomposition the paper already uses, so the numbers are
directly comparable.

## Recipe

- **Architecture.** PreActResNet-18, the canonical RobustBench/Wang-2023 CIFAR backbone
  (`paper/experiments/resnet_scale/models.py`, `build("stdzero", width=1.0)` = zero-padding, stride-2
  subsampling; 11,172,170 params). Input normalization is a layer **inside** the model, so all attacks
  perturb the true `[0,1]` image.
- **Adversarial training.** Linf PGD-AT (Madry), `eps = 8/255`, step `alpha = 2/255`, **7** inner PGD
  steps, identical to `paper/experiments/cifar_at.py` `RECIPE[("cifar","linf")]`. Reuses
  `cifar_at.pgd_linf` for the inner maximization, so the AT loop matches the paper's.
- **Optimizer.** SGD(lr=0.1, momentum=0.9, nesterov, weight_decay=5e-4), cosine-annealed LR, random
  horizontal flip (the paper's augmentation). Batch size 512.
- **Synthetic data.** Wang-2023 EDM synthetic CIFAR-10 (`data/1m.npz`, 1,000,000 images, 10 balanced
  classes, verified). Arms add `{0, +100k, +500k, +1M}` synthetic images to the 50k real CIFAR-10
  train images. Smaller pools are fixed seeded random subsets of the 1M.
- **Mixing.** When synthetic is present, each batch is **30% real / 70% synthetic** (standard
  Gowal/Rebuffi/Wang practice), sampled with replacement from the two pools. The `+0` arm is pure real
  (standard permutation passes).
- **Compute-matched design (important).** Every arm runs the **same** number of epochs (40 for the
  pilot) and the **same** number of gradient steps per epoch (`ceil(50000/512) = 98`), with an
  identical optimizer. The **only** thing that varies across arms is the size of the synthetic pool
  that the mixed batches are drawn from. So "more synthetic data" here is a **diversity/coverage** knob
  at fixed optimization budget — this isolates the data-amount mechanism and avoids confounding it with
  "more training steps." (Literature recipes also scale the step count with data; that is a different,
  compute-unmatched experiment. Flagged as a limitation below.)

## Measurements (per arm), all reusing the paper's tooling

| metric | tool | meaning |
|---|---|---|
| clean | `cifar_dissection.accuracy` | clean test accuracy |
| PGD | `cifar_dissection.pgd_acc` (40-step margin-PGD, Linf 8/255) | robust acc, masking-check upper bound |
| AA | `cifar_dissection.autoattack_acc` (AutoAttack standard, Linf 8/255) | robust acc ground truth (`AA <= PGD`) |
| rr_L2 | `cifar_dissection.robust_radius_l2` (DDN, 1000 clean-correct pts) | mean min-norm L2 certified radius |
| margin | `etaL_decomposition` `dec_margin` | mean margin on clean-correct points |
| L1 | `etaL_decomposition` `dec_L1` | mean `||grad margin||_1` (Linf-dual local Lipschitz) |
| L2 | `etaL_decomposition` `dec_L2` | mean `||grad margin||_2` (L2-dual local Lipschitz) |
| eta/L | `etaL_decomposition` `dec_etaL` | mean margin / mean L2 |
| consist | `cifar_dissection.shift_consistency` | circular-shift prediction consistency |

The **threat-matched** local Lipschitz for AutoAttack-Linf is **L1** (Linf dual norm); the DDN radius is
L2 so its matched Lipschitz is **L2**. The report gives both, plus `d log(eta/L)` split into the margin
share and the Lipschitz share, vs the `+0` real-only baseline.

## Results — Stage 1 (calibration, arms {0, +1M}, 40 epochs)

_TBD after run._

## Results — Stage 2 (full sweep {0, +100k, +500k, +1M}, 40 epochs)

_TBD (only if the Stage-1 gain reproduces)._

## Gradient-masking check

_TBD — require `AA <= PGD` for every arm._

## The decomposition verdict

_TBD — is the diffusion-data robustness gain margin-driven, Lipschitz-driven, or both? With numbers._

## Honesty / caveats

- **One seed.** This is a 1-seed pilot. AT robust accuracy at this scale has seed noise on the order of
  ~0.5–1 point (AA) and the margin/Lipschitz means carry comparable noise; the decomposition *direction*
  is the deliverable, not third-decimal precision. Multi-seed confirmation is the obvious follow-up.
- **Compute-matched, not step-scaled.** See the design note above. The pilot isolates synthetic-data
  *diversity at fixed budget*; it does not reproduce the literature's step-count scaling.
- **Pilot epoch count (40).** Below the 200+ epochs used for SOTA RobustBench numbers, so absolute
  robustness is lower than published; the cross-arm *comparison* and decomposition are the point.
