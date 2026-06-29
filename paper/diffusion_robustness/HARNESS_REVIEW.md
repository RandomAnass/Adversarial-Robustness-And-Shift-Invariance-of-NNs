# Harness review: `diff_pilot.py` -> `diff_pilot_v2.py`

Review + hardening of the diffusion-data PGD-AT decomposition pilot. The original `diff_pilot.py`
is **left untouched** (a multi-seed `stage2` run is using it on both GPUs as of this review). All
changes live in the new `diff_pilot_v2.py`. No GPU training was launched; only a CPU smoke test.

**The full multi-seed GPU runs are to be launched by the main process AFTER the current
`diff_pilot.py` run finishes** (suggested command at the bottom).

---

## 1. Correctness review of `diff_pilot.py` (bugs + flags)

What is **correct** and was preserved verbatim in v2 (so v2 numbers stay comparable):

- **Synthetic mixing ratio.** `real_frac=0.3` -> `nb_real=round(0.3*512)=154`, `nb_syn=358`, i.e.
  real:synth = 154:358 ~ 30:70 per batch, matching the docstring and the Gowal/Rebuffi/Wang practice.
  The `+0` arm is pure-real permutation passes. In-place `.float().div_(255.)` acts on the fresh
  `.float()` copy, so the uint8 pool is not corrupted. Correct.
- **Compute-matched design.** `steps_per_epoch = ceil(50000/bs)` and the optimizer are identical
  across arms; only the synthetic-pool size changes. Correct and faithfully kept.
- **PGD-AT recipe.** Reuses `cifar_at.pgd_linf` directly (eps=8/255, alpha=2/255, 7 steps, uniform
  random init, clamp to valid box). SGD(0.1, mom 0.9, nesterov, wd 5e-4) + cosine + hflip matches
  `cifar_at.RECIPE[("cifar","linf")]`. Correct.
- **Decomposition math.** `d log r ~= d log margin - d log L`; `eta/L2 = mean(m)/mean(L2)` is the
  first-order (linear/Tsuzuku) L2 radius, `eta/L1` is the Linf-dual (threat-matched to AA-Linf).
  `d log(eta/L)` = `d log m - d log L`. Correct.
- **Gradient-masking check.** `AA <= PGD` is the right direction (AA is at least as strong); a
  violation flags masking. Correct.

Bugs / issues found:

- **(B1) Per-seed init is NOT actually seeded (latent multi-seed bug).** In `run_arm` the model is
  built (`M.build(...)`) **before** `adv_train_mixed` calls `torch.manual_seed(seed)`. In a freshly
  `spawn`ed worker the global RNG is at its default state, so **every seed would get the same weight
  initialisation**; seeds would differ only in batch-order/flip/PGD noise. Verified:
  `M.build` with no prior seed is deterministic across processes; `manual_seed(0)` vs `manual_seed(1)`
  before build gives different `fc` weights. **Fix in v2:** `torch.manual_seed(seed)` is called at the
  very top of `run_cell`, before data load and before `M.build`, so init varies per seed. (This was a
  no-op for the original single-seed runs, which is why it went unnoticed.)
- **(B2) The `KeyError` in the final decomposition print** (seen in `results/stage1.log`:
  `KeyError: 'margin_share_of_etaL'`) was already fixed in the current `diff_pilot.py` (the print now
  recomputes `ms` locally). v2 additionally **saves the aggregate JSON before printing**, so even a
  future print-time exception cannot lose results.
- **(B3, flag) `bs=512` vs `cifar_at.py`'s `bs=128`.** With the same `lr=0.1` the larger batch does
  fewer, noisier steps/epoch; the `+0` baseline lands at clean 0.781 / AA 0.354, a bit below a
  128-batch recipe. This is **consistent across arms** (the decomposition is a within-experiment
  comparison) so it does not bias the conclusion, but absolute robustness runs low. Kept (to stay
  comparable to the running stage); `--bs` is exposed and the note is recorded in the saved recipe.
- **(B4, flag) Real-data sampling differs between arms.** The `+0` arm draws real images
  **without** replacement (permutation pass over all 50k); synth arms draw real **with** replacement
  (`torch.randint`), seeing ~15k real draws/epoch. This is the standard mixed-pool sampler and is the
  intended compute-matched design (same #steps, same batch size), not a bug. Kept and documented.

---

## 2. Multi-seed + progressive-save / resume design (v2)

- **`--seeds N`** runs each arm with seeds `0..N-1`. The full grid is `arms x seeds`. The **synthetic
  pool is held fixed** (`--synth_seed`, independent of the training seed), so seeds vary only
  init + SGD/PGD/flip randomness -> multi-seed isolates *optimization noise*, not data-subset noise.
- **Atomic per-cell save.** Each `(arm, n_syn, seed)` cell writes its result to its own JSON via
  `json.dump(tmp); os.replace(tmp, final)` the moment it finishes. A crash/restart loses **at most one
  in-flight cell**.
- **Collision-proof key.** The partial filename encodes
  `tag_arm-<arm>_w<width>_syn<n_syn>_s<seed>_e<epochs>_bs<bs>_rf<real_frac>` — i.e. **arm, width,
  n_syn, seed, epochs AND bs/real_frac** — so two runs differing in any recipe knob never overwrite
  each other (the width/scale collision bug class). `--arm/--width` are exposed for future arch sweeps.
- **Resume.** On start, every grid cell whose JSON exists is loaded from disk and skipped; only the
  rest are scheduled and round-robined across GPUs. The aggregate is re-assembled from disk + this run.
- **Aggregation.** Cells are grouped by `n_syn`; clean/PGD/AA, rr_L2 (mean + median), eta/L, margin,
  L1/L2, logit-scale and T_nll are reported as **mean +/- std** over seeds. The decomposition runs on
  the per-arm seed means.

---

## 3. Logit-scale control (the key scientific fix)

**Problem.** The margin `M = z_y - max_{j!=y} z_j` and the local Lipschitz `L = ||grad_x M||` are both
**degree-1 homogeneous in the logits** `z`: scaling `z -> c*z` (a temperature `1/c`) sends `M -> c*M`
and `L -> c*L`, while `M/L`, the argmax, clean acc, PGD/AA, and the DDN L2 attack distance are
**unchanged**. So the raw pilot result "margin down 42%, L down 51%" conflates a real geometry change
with a pure **logit-scale** change (the +1M model simply being less confident: its mean centred-logit
norm and both margin & L shrink together). The split of the gain into "margin moved" vs "L moved" is
**gauge-dependent**; only `eta/L = d log M - d log L` and the actual attack radius are gauge-free.

**What v2 implements.**

1. **Primary robustness = scale-invariant.** The DDN L2 robust radius `rr_L2` (now **mean AND median**,
   median is robust to the heavy right tail) and AutoAttack accuracy are the headline robustness
   numbers — neither depends on logit scale.

2. **Scale-controlled margin/L split under two anchors.** Each anchor fixes the gauge by choosing a
   per-arm scale factor `T_a` and rescaling `margin' = margin/T_a`, `L' = L/T_a`:
   - **Anchor A `logitnorm` (PRIMARY).** Equalize the **mean centred-logit L2 norm** across arms:
     `T_a = scale_a / scale_base`, where `scale = mean_i || z_i - mean_c z_{i,c} ||_2` on the
     clean-correct decomposition points. **Rationale:** `M` and `L` share *exactly one* scale d.o.f.
     (degree-1 homogeneity); matching the logit norm removes precisely that d.o.f. and nothing else.
     It is deterministic, label-free, exact, and centred so the additive-constant gauge (which does
     not affect `M`/`L`) is removed first.
   - **Anchor B `nll` (CROSS-CHECK).** Per-arm **temperature scaling** (Guo et al. 2017): fit a single
     scalar `T` minimizing NLL of `logits/T` on a held-out test slice (`--temp_n`, LBFGS, clamped to
     `[0.05, 20]`), so every arm is calibrated to the same NLL-optimal reference. Familiar calibration
     anchor; used to test whether the verdict is **anchor-robust**.

   Both anchors reduce algebraically to **subtracting a common `d log s`** from both `d log margin` and
   `d log L` (`d log s = d log scale` for A, `d log T` for B). Therefore the gauge-INVARIANT gap
   `margin_ctrl - L_ctrl == d log margin - d log L == d log(eta/L)` is **preserved exactly** (unit-tested
   to `<1e-9` for both anchors), while the absolute attribution ("is margin really down? did L move
   more?") is reported only *relative to the stated anchor*.

3. **Report.** For each arm vs the +0 baseline the report prints (a) the gauge-invariant
   `d log(eta/L1|L2)`, `d log rr_L2` (mean+median) and `dAA` as the actual conclusions; (b) the raw
   `d log margin / L1 / L2` clearly labelled CONFOUNDED; (c) the scale-controlled `margin_ctrl`,
   `L2_ctrl`, `L1_ctrl` under both anchors, plus a boolean **`survives_<anchor>`** = does the raw
   "margin-down AND L-down-more" attribution survive scale control. The chosen anchor and its rationale
   are documented in the script docstring and recorded in the saved recipe JSON.

   *Worked illustration on the Stage-1 numbers* (margin 4.455->2.573, L2 5.107->2.513, logit-scale
   shrinks): under the `logitnorm` anchor `d log s ~= -0.55 ~= d log margin`, so `margin_ctrl ~= 0`
   (the margin did **not** really move — it was logit scale) while `L2_ctrl ~= -0.16` (L genuinely
   dropped) and `d log(eta/L2) = +0.16` (= the gauge-free gain, matching `rr_L2` +0.10 / `AA` +0.12).
   The full multi-seed run will report the real per-anchor verdict.

Also added: per-sample radius **median** (`robust_radius_l2_per_sample`, a faithful copy of
`cifar_dissection.robust_radius_l2` that returns the per-sample tensor, since that file is outside this
directory and must not be edited).

---

## 4. Logging

- **`[start] syn<N>_s<seed> | arm=... epochs=... dev=...`** per cell.
- **Per-epoch** line `[cell] epoch e/E loss L robust_train_acc A lr LR`, where robust-train-acc reuses
  the outer-forward logits (no extra forward), all `flush=True` so `tail -f` shows live progress.
- **`[done] syn<N>_s<seed> | clean PGD AA | rr_L2 (med) margin L1 L2 logit_scale T_nll | wall`** per cell.
- Final **results table (mean +/- std)**, raw decomposition quantities, gradient-masking check, and the
  gauge-invariant + raw + scale-controlled decomposition. The **aggregate JSON is saved BEFORE** the
  report is printed, and each cell is saved atomically on completion, so no print/agg failure can lose
  computed results.

---

## 5. CPU smoke test (no GPU training)

Run (forces CPU, tiny sizes, AA `custom`):

```
PYTHONNOUSERSITE=1 .../cenv/bin/python diff_pilot_v2.py --smoke --serial --tag smoke
```

`--smoke` sets `n=256, ntest=512, epochs=1, seeds=2, synth=[0,256], bs=128, rad_n=24/steps25,
dec_n=64, temp_n=128, aa_n=16, aa_version=custom, pgd_steps=5` and caps CPU threads.

Result: completes end-to-end on CPU (exit 0, ~214 s for 4 cells), exercising both the pure-real and
the mixed-synthetic training paths, all eval (clean/consist/rr_L2 mean+median/decomposition/
logit_scale/T_nll/PGD/AA-custom), atomic per-cell save, seed aggregation, the masking check, and the
gauge-invariant + raw + scale-controlled decomposition. The numbers are meaningless (1 epoch on 256
images -> ~10% acc, untrained; `T_nll` pinned at the clamp 20.0 as expected for an uncalibrated model)
-- the smoke confirms the MACHINERY, not science.

Key live-output excerpts:

```
PILOT v2 diffusion-AT: arms(synth)=[0, 256] seeds=2 epochs=1 ... | 0 cell(s) resumed, 4 to run over CPU
[start] syn0_s0 | arm=stdzero w=1.0 epochs=1 bs=128 real_frac=0.3 dev=cpu
  [syn0_s0] epoch   1/1  loss 3.3412  robust_train_acc 0.0273  lr 0.0000
[done] syn0_s0 | clean 0.098 PGD 0.125 AA 0.125 | rr_L2 1.450 (med 1.310) margin 2.286 ... | 53s
  [syn0_s1] epoch   1/1  loss 3.3478  ...          <- different loss => per-seed INIT differs (B1 fix)
...
==== decomposition vs +0 (real-only) baseline ====
  +   256: dlog(eta/L2) -0.370  dlog rr_L2 +0.243 (med +0.143)  dAA +0.000
RAW:        dlog margin +0.332  dlog L1 +0.713  dlog L2 +0.702
SCALE-CONTROLLED:
  logitnorm: dlog s -0.254 | margin_ctrl +0.587  L2_ctrl +0.956  L1_ctrl +0.967 | survives: False
  nll:       dlog s +0.000 | margin_ctrl +0.332  L2_ctrl +0.702  L1_ctrl +0.713 | survives: False
```

Checks that passed:
- **Per-seed init differs** (B1 fix): seeds 0/1 produce different epoch losses (3.3412 vs 3.3478).
- **Gauge-invariance holds in the live output**: `margin_ctrl - L2_ctrl = -0.369 ~= dlog(eta/L2) = -0.370`
  under BOTH anchors (also unit-tested to `<1e-9`).
- **Gradient-masking check** prints and holds (`AA <= PGD`).
- **Save-before-print**: the aggregate JSON is written (`saved .../diff_pilot_v2_smoke_*.json`) before
  the report.
- **Full resume**: re-running the same command -> `4 cell(s) resumed, 0 to run`, `wall 0s`, report
  rebuilt from disk.
- **Partial resume** (delete one cell): `3 cell(s) resumed, 1 to run` -> only `syn0_s0` reran and
  reproduced identical numbers (clean 0.098, margin 2.286), confirming determinism and at-most-one-cell
  loss on crash.
- **Collision-proof filenames**, e.g. `smoke_arm-stdzero_w1_syn0_s0_e1_bs128_rf0.3.json`.

(The CPU-smoke partials and `diff_pilot_v2_smoke_*` result files were deleted after the test; they hold
no real science.)

---

## How to launch the full multi-seed GPU run (main process, after the current run finishes)

```
PYTHONNOUSERSITE=1 /home/students/code/Anas/adversarial-robustness-shift-invariance/paper/env/cenv/bin/python \
    paper/diffusion_robustness/diff_pilot_v2.py \
    --synth 0 100000 500000 1000000 --epochs 40 --seeds 3 --gpus 2 --tag v2sweep \
    > paper/diffusion_robustness/results/v2sweep.log 2>&1 &
```

Resumable: re-running the same command skips completed `(arm, n_syn, seed)` cells found on disk.
Do NOT start this while `diff_pilot.py` is still on the GPUs.
