# Decisive mechanism experiments: WHY diffusion data buys SMOOTHNESS, not margin

**Goal.** The pilot (`diff_pilot_v2.py`) established the verified finding: adding EDM synthetic AT data
raises AutoAttack and the DDN L2 radius while the local input-gradient norm `L = ||grad_x M||` drops MORE
than the margin `M` (the radius gain lives entirely in the scale-invariant `eta/L`). `THEORY_mechanism.md`
ranks six candidate explanations (H-A..H-F). This note specifies the **3-4 most decisive measurements**
that tell them apart, and ships the measurement code (`mech_measure.py`) that runs each as one command on
the checkpoints the next full GPU run will produce.

**The hypotheses (one line each):**
- **H-A (TOP)** PGD-AT is implicit input-gradient regularization; synthetic data DENSIFIES the manifold
  vicinity where that penalty is enforced -> globally flatter function near the data, `L` down everywhere.
- **H-B** The smoothness is the ABSENCE of robust-overfitting: the late-training input-sharpening the
  real-only model acquires after the LR decay is simply not present.
- **H-C** Input-space CURVATURE reduction (the 2nd-order reading of A).
- **H-D** The flatness lives in WEIGHT space, not input space (input-`L` is a downstream correlate).
- **H-E** Manifold coverage suppresses OFF-manifold gradient components (anisotropic shrink).
- **H-F** Randomized-smoothing-like averaging over near-duplicate synthetic images (weakest).

---

## 0. BLOCKER the main process must fix first: checkpoints

`diff_pilot_v2.py` saves only metrics JSON (`results/partial/*.json`), **never the model weights**
(verified: the partial files have no `state_dict`). Every measurement here loads a TRAINED model, so the
next full run must save checkpoints. Two saves are needed:

- **Final per-(arm,seed) checkpoint** -> M1/M2/M3/M4/M5 (one snapshot per arm).
- **Per-epoch checkpoints for 2 arms (+0 and +1M), >=1 seed** -> M6 (the trajectory test).

**Exact patch for `diff_pilot_v2.py`** (the main process applies this; I did not edit the file). Format
that `mech_measure.load_ckpt` already expects: `{"state_dict":..., "arm","width","n_syn","seed","epoch"}`.

1) Add two CLI args next to the other `ap.add_argument` lines in `main()`:
```python
    ap.add_argument("--save_ckpt", action="store_true", help="save final per-cell model weights -> ckpts/")
    ap.add_argument("--save_ckpt_every", type=int, default=0, help="also save every K epochs (M6 trajectory)")
```
2) Thread them into the `A = dict(...)` recipe dict:
```python
             aa_seeds=args.aa_seeds, synth_seed=args.synth_seed, tag=args.tag,
             save_ckpt=args.save_ckpt, save_ckpt_every=args.save_ckpt_every)
```
3) Per-epoch save: in `adv_train_mixed(...)`, after `sched.step()` inside the epoch loop, add
   (pass `A`/`cell` through, or capture via closure):
```python
        if A.get("save_ckpt_every") and ((ep + 1) % A["save_ckpt_every"] == 0):
            ck = os.path.join(HERE, "ckpts"); os.makedirs(ck, exist_ok=True)
            torch.save(dict(state_dict=model.state_dict(), arm=A["arm"], width=A["width"],
                            n_syn=int(n_syn), seed=int(seed), epoch=ep + 1),
                       os.path.join(ck, f"{A['tag']}_traj_syn{n_syn}_s{seed}_ep{ep+1}.pt"))
```
4) Final save: in `run_cell(...)`, right after `model = adv_train_mixed(...)`:
```python
    if A.get("save_ckpt"):
        ck = os.path.join(HERE, "ckpts"); os.makedirs(ck, exist_ok=True)
        torch.save(dict(state_dict=model.state_dict(), arm=A["arm"], width=A["width"],
                        n_syn=int(n_syn), seed=int(seed), epoch=A["epochs"]),
                   os.path.join(ck, f"{A['tag']}_syn{n_syn}_s{seed}_e{A['epochs']}.pt"))
```
(`n_syn`, `seed`, `A`, `cell` are all in scope at those points. Each checkpoint is ~43 MB
(11.17 M params); the per-epoch save for 2 arms x 40 ep x 1 seed is ~3.4 GB -- save every 2-4 epochs to
halve that.)

---

## 1. Ranked decisive experiments

Discriminating quantity in **bold**. "Snapshot" = final-model probe (needs the final checkpoint);
"trajectory" = needs per-epoch checkpoints. Each row says what each hypothesis PREDICTS for the
`+1M / +0` comparison (and across the `{0,100k,500k,1M}` sweep where a dose-response sharpens the test).

| # | measurement (task) | adjudicates | the call |
|---|---|---|---|
| **1** | **`manifold`** L on REAL/SYNTH/INTERP/OFF-manifold point sets + on/off-manifold gradient split | **A vs E vs F** | where in input space the smoothing lives + isotropic-vs-anisotropic |
| **2** | **`trajectory`** per-epoch L and train-test robust-acc gap, +0 vs +1M | **B vs A/C** | is the smoothness just RO-elimination (epoch axis) or present early (data axis) |
| **3** | **`curvature`** CURE finite-difference input curvature, gauge-free **curv/L** | **C vs scale-artifact** | genuine 2nd-order flattening vs pure 1st-order logit-rescale |
| **4** | **`weightsharp`** weight-space sharpness (random + SAM), vs input-L across the sweep | **D vs A/C** | input-space vs weight-space locus of the flatness |
| 5 | `calib` temperature-calibrated + logit-norm margins (run FIRST; cheap, no ckpt geometry) | cross-cutting (THEORY sec.2) | how much of the margin-down is confidence/scale vs real separation loss |

### Experiment 1 (TOP) -- `manifold`: where does the smoothing live?
**Protocol.** On a fixed set of probe points, measure `L2 = mean||grad_x M||_2` (M = top-1 vs runner-up
margin, so it needs no trusted labels off the manifold) for the +0 and +1M models on each of:
`real` (held-out test) | `synth` (EDM pool) | `interp_same` (convex combos of SAME-class real pairs,
alpha~U(0.3,0.7); on-manifold vicinity) | `interp_cross` (cross-class; decision-boundary vicinity) |
`gauss` (real + N(0,0.1^2), well outside the 8/255 budget; off-manifold) | `uniform` (pure U[0,1]; far
off-manifold). Then the on/off split of `grad_x M`: local-PCA tangent (top-30 dirs over the 64 nearest
real anchors) -> **on-manifold energy fraction** `||P_tan g||^2/||g||^2`.

**Discriminating quantity.** Per-set ratio `R_set = L2(+1M)/L2(+0)`, the shape of `R_set` across sets, the
`L1/L2` ratio, and the change in off-manifold gradient fraction.

| | H-A | H-E | H-F |
|---|---|---|---|
| `R_set` shape | `<1` on ALL sets; **largest drop on `interp_*`/vicinity** | drop **concentrated on `gauss`/`uniform`**; `real` ~unchanged | drop only where synth neighbors exist (`real`,`synth`); `gauss`/`uniform` ~unchanged |
| `L1/L2`, on/off frac | ~unchanged (isotropic) | `L1/L2` shifts; **off-manifold frac drops sharply** (anisotropic) | ~unchanged |

So a roughly uniform `R_set` with the biggest cut on interpolation points and a flat on/off split **=> A**;
an off-manifold-concentrated cut with a falling off-manifold fraction **=> E**; a cut that vanishes on
points with no nearby synthetic neighbors **=> F**. (The pilot's single-seed `L1/L2` near-constant hint
already leans A over E; this promotes it to n>1 with the explicit on/off split.)

### Experiment 2 -- `trajectory`: robust-overfitting-as-sharpening?
**Protocol.** Needs per-epoch checkpoints for +0 and +1M (>=1 seed). Per epoch: `L2` on a fixed test
subset, and the **train-test robust-accuracy gap** (PGD-Linf 8/255 on a train subset minus a test subset).

**Discriminating quantity.** The `L2(epoch)` and `robust_gap(epoch)` curves.
- **H-B:** in +0, `L2` and the robust gap **climb in late epochs** (after the cosine LR gets small / the
  RO regime); in +1M they **stay flat**. The smoothness is the absence of that late sharpening.
- **H-A/C:** +1M `L2` is **already lower than +0 EARLY** (by ~epoch 10-15, before the +0 gap opens), i.e.
  the effect is present on the data axis from the start, not an end-of-training divergence -> B refuted.
- Live preview from the running sweep (`results/v2sweep.log`, ep36): +0 `robust_train_acc=0.92` vs
  +100k `=0.72` -- the +0 arm is memorizing the adversarial train set hard, so a late `L` climb in +0 is
  plausible; the L-trajectory decides whether that memorization shows up as input-sharpening (B) or whether
  +1M was already smoother early (A/C). Caveat: 40 epochs may be short for full RO; extend a couple of runs
  to ~80-100 ep if the curves are still separating at ep40.

### Experiment 3 -- `curvature`: real flattening vs logit rescale?
**Protocol.** PreActResNet-18 (ReLU + eval-mode affine BN) is **piecewise-linear in the input**, so the
pointwise margin-Hessian is ~0 a.e. (verified; the exact-HVP power iteration returns 0.00e+00). Curvature
for ReLU nets lives at the linear-region BOUNDARIES and is measured by **finite differences of the
gradient** -- exactly CURE (1811.09716): `nu = ||grad M(x + h z) - grad M(x)||_2 / h` for z = unit
gradient direction (and a random-direction average), `h` an L2 step of order the radius (default 0.25).

**Discriminating quantity.** The **gauge-free `curv/L`** ratio. Under a pure logit rescale `f -> f/T`, both
the curvature and `L` scale by `1/T`, so `curv/L` is invariant; a genuine geometric flattening (H-C)
lowers `curv/L`, a pure 1st-order rescale leaves it flat.
- **H-C (genuine flattening):** `curv` falls and `curv/L` **drops**, tracking `L` across the sweep.
- **Scale-artifact (THEORY sec.2):** `curv/L` stays **flat** -- the surface is no flatter at 2nd order,
  the logits just shrank. This cleanly separates "real smoothing" (A/C) from "shrunk logits."

### Experiment 4 -- `weightsharp`: input space vs weight space?
**Protocol.** Per arm, weight-space sharpness = loss increase under (i) a filter-normalized RANDOM weight
perturbation `eps_p = rho*||p||*z/||z||` (mean over trials) and (ii) a worst-case 1-step SAM ascent
`w += rho*g/||g||` (`rho=0.05`). Use `--adv` to make the loss the ROBUST (PGD) loss, which is the
AWP-relevant quantity. Correlate against input-`L` across `{0,100k,500k,1M}`.

**Discriminating quantity.** Whether weight-sharpness tracks input-`L` across the sweep.
- **H-D (weight-space locus):** weight-sharpness **drops with synthetic data AND tracks input-`L`**.
- **H-A/C (input-space locus):** input-`L` drops while weight-sharpness is **flat / uncorrelated** -> D
  refuted; the smoothness is an input-space phenomenon. AWP itself provides NO theoretical bridge from
  weight-flatness to input-`L`, so this is a genuine separation, not a restatement.

### Experiment 5 (run FIRST; cheap) -- `calib`: is the margin-down just confidence?
**Protocol.** Per arm: raw margin `M`, temperature-calibrated margin `M/T` (T by NLL, Guo 2017), and the
scale-free logit-norm margin `M/||z_centred||`, on clean-correct points. Report `dlog margin` vs the +0
baseline under each gauge.
- **Confidence/scale story (THEORY sec.2.1):** the raw `dlog margin` (~-0.42 in the pilot) **shrinks toward
  0** after calibration and under the logit-norm gauge -> the margin-down was largely over-confidence, while
  `eta/L`, the DDN radius and AA (all scale-invariant) are unchanged. The strongest form of the headline:
  the only real effect is smoothness.
- **Real separation loss:** the calibrated/logit-norm gap stays clearly negative.
(The pilot recipe uses plain CE with no label smoothing, so the margin-shrink is data-induced, not an
`ls` artifact -- worth stating to preempt that objection.)

---

## 2. The measurement code: `mech_measure.py`

One reusable module, `--task {manifold,curvature,weightsharp,calib,trajectory,all}`, that loads
checkpoint(s) and writes JSON to `results/mech/`. It reuses the paper tooling unchanged
(`cifar_dissection`: `load_cifar`, `correct_mask`, `pgd_acc`, `_margin_loss`; `cifar_at.pgd_linf`;
`resnet_scale.models.build`) so numbers are comparable to the pilot. It does **not** edit `diff_pilot*.py`
or anything outside this directory, and never trains the main models.

Key functions: `margin_grad` (per-sample M and grad), `L_stats` (L1/L2/margin on any point set),
`onoff_split` (local-PCA tangent projection), `curvature_fd` (CURE finite-difference) + `input_hessian_topeig`
(exact, ~0 = piecewise-linear check), `weight_sharpness` (random + SAM), `fit_temperature`/`calibrated_margins`,
and the five `task_*` dispatchers. Smoke fabricates two tiny CPU-trained checkpoints (incl. per-epoch ones
for the trajectory task) so the whole pipeline runs with no GPU and no checkpoints on hand.

### CPU smoke result (no GPU touched; `CUDA_VISIBLE_DEVICES=""`, ~15 s)
```
$ PYTHONNOUSERSITE=1 ../env/cenv/bin/python mech_measure.py --smoke
[manifold] syn0_s0:   real:L2=0.052 interp_same:L2=0.053 interp_cross:L2=0.053 gauss:L2=0.052 uniform:L2=0.054 synth:L2=0.054 | on_frac=0.002
[manifold] syn256_s0: real:L2=0.049 interp_same:L2=0.047 interp_cross:L2=0.049 gauss:L2=0.045 uniform:L2=0.047 synth:L2=0.045 | on_frac=0.003
[curvature] syn0_s0:   FD-curv grad=0.116 (med 0.101) rand=0.058 curv/L=2.122 | exact|lam_max|=0.00e+00 (~0=piecewise-linear) | L2=0.055
[curvature] syn256_s0: FD-curv grad=0.106 (med 0.090) rand=0.055 curv/L=2.202 | exact|lam_max|=0.00e+00 (~0=piecewise-linear) | L2=0.048
[weightsharp] syn0_s0:   rand=+0.0000 worst=+0.0603 (rho=0.05, adv=False) | input_L2=0.052
[weightsharp] syn256_s0: rand=-0.0014 worst=+0.0587 (rho=0.05, adv=False) | input_L2=0.049
[calib] syn0_s0:   T=1.183 raw=0.021 calib=0.018 lognorm=0.0787
[calib] syn256_s0: T=2.318 raw=0.026 calib=0.011 lognorm=0.1485
  vs base syn256_s0: dlog margin raw +0.188 -> calib -0.485  lognorm +0.635
[trajectory] ep0..2 syn0/syn256: L2, rob_train, rob_test, gap  (per-epoch curve)
[done] ['manifold','curvature','weightsharp','calib','trajectory'] in ~15s on cpu
```
(The smoke checkpoints are 2-epoch clean-trained toys -- numbers are NOT meaningful; the point is every
probe loads a checkpoint, runs end-to-end and emits finite outputs + the cross-arm comparison. The
`exact|lam_max|=0` line is the real, load-bearing finding: confirms piecewise-linearity, which is why M3
uses finite differences.)

---

## 3. Exact GPU commands for the main process (run AFTER the current `v2sweep` frees the GPUs)

`env=PYTHONNOUSERSITE=1 .../diffusion_robustness/../env/cenv/bin/python`. Both A6000s are at 100% on the
definitive `diff_pilot_v2.py --tag v2sweep` run (do not contend). When it is done:

**Step A -- apply the `--save_ckpt` patch (sec.0), then produce checkpoints.** Re-run the arms with saving
on (resume is free -- the existing `results/partial/*.json` are reused; only the weight-save is new, so
this is a fresh short pass that re-trains because no `state_dict` was kept). Final snapshots for all arms +
per-epoch for the two trajectory arms:
```bash
# final checkpoints for the dose-response (M1/M3/M4/M5)
$ENV diff_pilot_v2.py --synth 0 100000 500000 1000000 --epochs 40 --seeds 3 \
      --gpus 2 --tag v2sweep --save_ckpt
# per-epoch checkpoints for the two trajectory arms (M6); every 2 ep to keep ~1.7 GB/arm
$ENV diff_pilot_v2.py --synth 0 1000000 --epochs 40 --seeds 1 \
      --gpus 2 --tag v2traj --save_ckpt --save_ckpt_every 2
```

**Step B -- run the measurements (each one command; minutes on one GPU).**
```bash
# 5 (do first, cheapest): margin scale control
$ENV mech_measure.py --task calib  --gpu 0 --tag v2 \
     --ckpts ckpts/v2sweep_syn0_s0_e40.pt ckpts/v2sweep_syn1000000_s0_e40.pt

# 1 (TOP): where the smoothing lives + on/off split (real EDM pool for the synth set)
$ENV mech_measure.py --task manifold --gpu 0 --tag v2 --synth_npz data/1m.npz --npts 1000 \
     --ckpts ckpts/v2sweep_syn0_s0_e40.pt ckpts/v2sweep_syn1000000_s0_e40.pt

# 3: CURE finite-difference curvature, gauge-free curv/L
$ENV mech_measure.py --task curvature --gpu 0 --tag v2 --npts 1000 \
     --ckpts ckpts/v2sweep_syn0_s0_e40.pt ckpts/v2sweep_syn1000000_s0_e40.pt

# 4: weight-space sharpness on the ROBUST loss
$ENV mech_measure.py --task weightsharp --gpu 0 --tag v2 --adv --npts 512 \
     --ckpts ckpts/v2sweep_syn0_s0_e40.pt ckpts/v2sweep_syn1000000_s0_e40.pt

# 2: per-epoch trajectory (point at the per-epoch ckpt dir)
$ENV mech_measure.py --task trajectory --gpu 0 --tag v2 --adv --ckpt_dir ckpts --npts 512
```
For the dose-response versions of 1/3/4, pass all four arms' final checkpoints to `--ckpts` (the baseline
must be the `n_syn==0` one); the tasks auto-detect the `n_syn==0` arm as the comparison base via the
checkpoint metadata. Multi-seed: pass the `_s1`, `_s2` checkpoints too and average offline.

---

## 4. Caveats / design notes
- **Piecewise-linearity (load-bearing).** Verified: the exact margin-Hessian of this ReLU+BN net is ~0
  a.e., so M3 MUST use finite differences (CURE). `curv/L`, not raw curvature, is the gauge-free quantity
  (both curv and L are degree-1 in the logits).
- **Off-manifold margins.** On `gauss`/`uniform`/`interp` points there is no trusted label, so `L_stats`
  uses the model's own top-1-vs-runner-up margin -- exactly the sensitivity `L` probes. (On `real`/clean-
  correct points this coincides with the pilot's true-label margin.)
- **Manifold estimate.** The tangent is a local-PCA estimate (top-30 of 64 NN); it is a proxy, so read the
  on/off split as a direction indicator, not a calibrated dimension. Cross-check with the `L1/L2` ratio.
- **Single backbone / seeds.** Everything is the +1M vs +0 DIRECTION; magnitudes need the multi-seed sweep
  and ideally a 2nd backbone (WRN-28-10), per THEORY sec.5. The dose-response over `{0,100k,500k,1M}` is
  what makes "tracks `L`" claims (M3/M4) testable.
- **Ranking is conditional.** If M1 shows an off-manifold-concentrated cut with a falling off-manifold
  fraction, E is promoted above A and the whole leaderboard re-ranks (THEORY sec.3).
