# ResNet-scale dissection — experimental design

Status: DRAFT (recipe + metrics confirmed; arm-construction and architecture sections finalized after literature verification). Authored 2026-06-20 for the weekend run.

## 0. One-line purpose
Test whether the small-net findings (shift-consistency does **not** predict the robust radius while **η/L does**; under adversarial training shift-consistency **anti-predicts** AutoAttack robustness and the **threat-matched η/L predicts** it; exact invariance loses robustness through reduced margin) **survive at realistic scale** on a PreActResNet-18, the standard CIFAR adversarial-training backbone. This is the single referee question the small-net study cannot answer ("does it hold at scale").

## 1. Research questions
- **RQ1 (standard training).** Across capacity-matched arms differing only in the shift-invariance operator, does η/L predict the ℓ₂ robust radius (as on the small net, Pearson ≈0.998) while shift-consistency does not, at ResNet scale?
- **RQ2 (adversarial training, the headline).** Under L∞ PGD-AT, does shift-consistency anti-predict AutoAttack robust accuracy and the threat-matched ratio η/‖∇M‖₁ predict it, at ResNet scale?
- **RQ3 (mechanism).** Does the margin/Lipschitz decomposition reproduce: anti-aliasing acts on the Lipschitz term, exact invariance costs margin?
- **RQ4 (generality).** Do RQ1–RQ3 hold on a harder dataset (CIFAR-100)?

## 2. Hypotheses (pre-registered predictions from the theory)
- H1: η/L vs robust radius — strong positive (CI excludes 0); consistency vs radius — near zero / not significant (standard training).
- H2: consistency vs AutoAttack (AT) — negative; threat-matched η/‖∇M‖₁ vs AutoAttack — positive, exceeding the mismatched ℓ₂ ratio.
- H3: exact-cyclic arm — highest consistency, lowest robust accuracy, Δlog margin < 0 vs standard.
- H4: same signs on CIFAR-100 (possibly weaker magnitudes).
- **Falsifiers stated up front:** if consistency turns *positive* vs AT robustness at scale, or η/L fails to predict the radius, the small-net story does not generalize and we report that.

## 3. Factors
**Variable (the only thing that changes across arms):** the shift-invariance operator → 4 arms (see §5).
Other variables: width multiplier (for the standard-training η/L–radius scatter we want several cells), seed, dataset (CIFAR-10 / CIFAR-100), training mode (standard / L∞-AT).

**Fixed across all arms (to avoid confounds):** backbone (PreActResNet-18), depth, channel schedule and parameter count (capacity-matched by construction — blur/APS kernels are non-learned), optimizer, LR schedule, epochs, weight decay, batch size, augmentation, normalization (folded into the model), PGD-AT recipe, seed handling, and the entire evaluation protocol. Identical training for all arms; only the operator differs.

## 4. Backbone & capacity matching
PreActResNet-18 for CIFAR (3×3 stem, 4 stages × 2 pre-activation basic blocks, channels [64,128,256,512]×width, downsample ×2 at the first block of stages 2/3/4, BN-ReLU-GAP-FC head). [Layer table + downsampling sites: finalized from the architecture reading.] Width-1 ≈ 11M params. Capacity matched: all four arms share the channel schedule; the invariance operators (blur kernel / APS selection / circular padding) add **no learnable parameters**, so parameter counts are identical at each width. (FLOPs differ; we control parameters, the established protocol, and report the FLOP note honestly.)

## 5. The four arms (finalized)
All arms share the PreActResNet-18 channel schedule and parameter count; the invariance operators add **no learnable parameters** (blur kernels fixed; APS selection has no weights). The only difference is the downsampling at the 3 sites (stage2/3/4 block1: strided main 3×3 + strided 1×1 shortcut).
- **standard** — circular padding, standard stride-2 downsampling at both the main 3×3 conv and the 1×1 shortcut. The non-anti-aliased baseline (exact only on the cumulative-stride shift subgroup). [Revised to circular padding in review round 1 to remove the padding confound; see changelog. Zero-pad version kept as the `stdzero` ablation.]
- **anti-aliased** — circular padding; replace each stride-2 op by stride-1 conv + BlurPool (low-pass blur then subsample; Zhang 2019), shared blur on main and shortcut so they stay aligned. Approximately shift-invariant (consistency < 1, ReLU defeats exactness). Kernel = Triangle-3 [1,2,1]² (Binomial-5 as a fallback), fixed/non-learned.
- **exact (APS)** — circular padding; replace each stride-2 op by stride-1 conv + Adaptive Polyphase Sampling (Chaman & Dokmanić 2021): form the s²=4 polyphase components, select by argmax ℓ∞-norm, compute the index once and share it across main and shortcut. **Exactly invariant to all integer circular shifts (consistency = 1.0, exact through ReLU), 0 params, ~1.46× wall-clock.** This is the scale-appropriate analogue of the small-net "exact cyclic" arm (which used circular-pad + stride-1 + GAP — infeasible at ResNet depth). [Design upgrade from the originally-chosen "subgroup-exact"; APS is exact to ALL shifts at modest cost, vs subgroup-exact's 1/64.] Public ref: github achaman2/truly_shift_invariant_cnns.
- **shift-aug** — `standard` architecture (circular padding, stride-2) trained with random circular-shift augmentation (learned, not architectural, invariance).

**Optional 5th arm if budget allows:** subgroup-exact = standard + circular padding (exact on the 8Z×8Z shift subgroup only) — to dissect subgroup-exact vs all-shift-exact. Not in the core grid.

**APS gradient-masking guard (mandatory):** APS's argmax selection is non-differentiable, a known potential gradient-masking source (Carlini 2019). For the APS arm specifically, the robustness numbers are accepted only after: AutoAttack black-box Square ≤ white-box APGD; unbounded attack → 0% robust; doubling PGD steps does not further reduce robust acc; and a BPDA-style check (straight-through the selection) does not lower robust acc. If any fails, the APS robustness is masked, not real, and reported as such.

## 6. Training recipes
### Standard (RQ1)
SGD(momentum 0.9, wd 5e-4), batch 128, random crop(pad 4)+hflip, per-channel normalization folded into the model, [0,1] inputs. Epochs/schedule sized by the smoke-test timing (target the same η/L–radius scatter as the small net; standard training is cheap).

### L∞ PGD-AT (RQ2, RQ3) — Rice 2020 recipe (verified)
- Optimizer SGD(momentum 0.9, **wd 5e-4**), batch **128**.
- LR **0.1**, piecewise ÷10 at epochs **100, 150**, total **200** (early-terminated, see below).
- Training attack: **L∞, ε=8/255, 10 PGD steps, α=2/255, random uniform start**, projected to the ε-ball and clamped to **[0,1]** (normalization inside the model; attack in pixel space — never in normalized space). CE loss for inner max and outer min.
- **Robust overfitting fix (critical):** hold out **1000 training images**; each epoch evaluate PGD robust accuracy on the holdout; **select the best-robust-validation checkpoint**, not the final epoch. Robust overfitting costs ~8% otherwise. Add **early termination**: stop once val-robust has not improved for a patience window past the epoch-100 decay (the best-robust point sits right after the first decay), saving budget without changing the selected checkpoint.
- No label smoothing / EMA / gradient clipping / mixup. Standard CIFAR augmentation only.
- **Sanity target:** early-stopped PreActResNet-18 ≈ 86–89% clean, 52–57% PGD-robust at 8/255. The first completed AT cell is gated against this before the rest of the queue proceeds.

## 7. Metrics (reuse the validated small-net harness for direct comparability)
- **clean accuracy.**
- **shift-consistency** — fraction of test points whose prediction is unchanged under two random shifts (existing `shift_consistency`; measured on the invariant shift set for the exact arm and on general shifts for all).
- **ℓ₂ robust radius r₂** — per-sample DDN min-norm (existing `robust_radius_l2`, validated to 0.8% vs analytic), on clean-correct points only. PRIMARY for RQ1.
- **η/L decomposition** — mean margin η, mean ‖∇M‖₂ (=L), mean ‖∇M‖₁, η/L (existing `etaL_decomposition`). M = active logit margin. PRIMARY mechanism metric.
- **AutoAttack robust accuracy** — standard version, L∞ 8/255 (and L2 0.5 as the mismatched check), on a fixed test subset (existing `autoattack_acc`, fixed seed). PRIMARY for RQ2.
- **PGD robust accuracy** — for the gradient-masking check (AA ≤ PGD must hold).
- **Per-sample** radii and margins are saved (not just means) for the detailed analysis.
- Extra metrics to add if useful: per-class robust accuracy; empirical local Lipschitz (Huang 2021 perturbation-stability); robustness-vs-ε curve.

## 8. Evaluation rigor / gradient-masking checks [checklist finalized after eval-rigor reading]
For every cell assert: AutoAttack ≤ PGD (no masking); unbounded/large-ε attack drives robust acc →0; more PGD steps do not further reduce robust acc materially. The exact-cyclic arm uses a possibly non-differentiable selection (if APS) — explicitly check it does not cause masking (BPDA-style sanity / compare to transfer attack). AutoAttack "standard" (deterministic model) on a fixed N-point test subset; report N.

## 9. Run plan — value-ordered, checkpointed, logged
- **Order (so the headline lands first and we degrade gracefully):**
  1. CIFAR-10, L∞-AT, 4 arms × seed 0 (the RQ2/RQ3 headline) — full picture by ~hour 20.
  2. CIFAR-10, standard, arms × several widths × seed 0 (RQ1 scatter) — cheap.
  3. CIFAR-10, L∞-AT, seeds 1–2 (CIs).
  4. CIFAR-100, L∞-AT, 4 arms × seed 0 (RQ4), then a second seed if time.
- **Smoke test first:** 1 epoch per arm to (a) confirm correctness (forward/backward, attack in [0,1], consistency==1 for exact arm, no NaNs) and (b) **measure real per-epoch wall-time on these GPUs**, then size epochs/seeds to fit the budget.
- **Checkpointing:** save model + optimizer + RNG state every few epochs and at every best-val-robust improvement; runs are **resumable**. A crash or the time-wall leaves complete cells.
- **Two GPUs:** one model per GPU, dispatched from a value-ordered queue; never thrash.
- **Mid-run sanity gate:** stop after the first AT cell, verify the sanity target + no masking, before releasing the rest.
- **Failure policy:** monitor; on a mid-run failure, correct and **rerun the failed cell**, do not stop the campaign.

## 10. Reproducibility & logging (no data hoarding)
Saved per run: seed, data-loading indices (train/val/test split), full config (all hyperparameters), **git SHA**, library versions, **per-epoch curves** (train/val clean+robust loss and accuracy), **checkpoints** (best + last + resume state), **per-sample** robust radii and margins, attack settings, wall-time. NOT saved: the CIFAR tensors themselves (redownloadable; we save the loader script + indices). One JSON of aggregate results per cell + a per-cell `curves.json`/`.npz` for the trajectory analysis.

## 11. Analysis plan (the process, not just final numbers)
Beyond the aggregate correlation table: (a) per-sample radius/margin distributions per arm (not just means); (b) training trajectories — when does robust overfitting start per arm, does the exact arm overfit differently; (c) the η/L decomposition per arm with CIs and the margin-vs-Lipschitz split; (d) the consistency↔robustness scatter with bootstrap CIs + permutation test; (e) per-class effects; (f) compare ResNet vs small-net (does the law's slope/sign carry over). Dedicated analysis script feeds the paper integration.

## 12. Threats to validity
- Capacity is param-matched, not FLOP-matched (stated). - Robust overfitting handled by early stopping; report best-val checkpoint. - AutoAttack on a subset (report N + masking checks). - Exact-arm non-differentiable selection (masking check). - Single backbone/family this run (WideResNet / ImageNet are future, larger runs — noted as the multi-tier plan). - CIFAR-100 gets fewer seeds (report n honestly; treat as supportive not primary).

## 13. Budget
2× RTX A6000 (48 GB), committed ~40–50 h, no hard stop. Grid sized after the timing smoke test. Floor commitment, not a ceiling (7/10/14-day runs available later if warranted).

---
## Review-round-1 revisions (2026-06-20, applied after two strong objective reviews; each finding verified firsthand)

DESIGN review (verified, applied):
- **Padding confound (HIGH) FIXED.** All four comparison arms now use **circular padding** so the only variable is the downsampling operator. `standard` = circular-pad + stride-2 (exact only on the cumulative-stride shift subgroup), `blurpool` = circular + BlurPool, `aps` = circular + APS (exact all shifts), `aug` = circular + stride-2 + circular-roll aug. Added a **`stdzero`** ablation arm (zero-pad + stride-2) to isolate the padding effect. Verified empirically: standard shift(8,8)=1e-8 / shift(3,5)=1e-2 (subgroup-exact); aps=7e-9 both; stdzero=6.6e-3 even on the subgroup (zero-pad breaks it).
- **Statistical power (HIGH) FIXED.** AT grid is now 4 arms x **2 widths {1.0,0.5}** x seeds {0,1(,2)} -> the 8-cell seed-0 AT scatter (matching the small-net 8-cell AT) gives spread along the eta/L axis, not just seed replicates. Report per-seed points + bootstrap CI (resampling cells) + permutation test (same protocol as the small net).
- **APS masking audit (HIGH) STRENGTHENED.** Added white-box APGD vs black-box Square comparison (`square >= apgd - 0.03`); the bundled AA<=PGD and unbounded->0 checks remain. Transfer attack (standard->APS) deferred to the analysis stage (checkpoints saved). Note (reviewer): masking would *inflate* APS robustness while we claim it is *low*, so the headline is the conservative direction; the audit defends the number regardless.
- **Value-ordering (MED) FIXED.** Cheap std scatter interleaved with the expensive AT headline (one per GPU) so RQ1 completes early; CIFAR-100 demoted to supportive (Phase 6), seed-2 last (Phase 7).
- **Std calibration (MED) ADDED.** Standard cells now run small-eps AutoAttack-L2 vs radius-fraction calibration (eps 0.05/0.10/0.15/0.25), reproducing the small-net "radius not inflated by masking" evidence at scale.
- **Sanity gate (LOW) CODED.** Driver halts NEW launches if the first AT cell is off-recipe (clean<0.6, AA<0.20, or masking fails), writing SANITY_FAIL.marker.
- Clean-accuracy confound for the exact arm: report partial correlation of consistency-vs-robustness controlling for clean accuracy (analysis stage).

IMPLEMENTATION review (verified, applied):
- **rr_l2 inf-poisoning (HIGH) FIXED.** ddn_radii returns inf for never-flipped points; eval_cell now masks finite before the mean (and logs rr_ninf). Was the validated small-net behavior; had been dropped.
- **Interpreter/CUDA/autoattack (HIGH) FIXED.** run_cell now does a fail-fast `import autoattack` + `assert torch.cuda.is_available()`; the driver launches children with the venv `sys.executable` and PYTHONNOUSERSITE=1. (A user-site torch+cu130 shadows the venv torch+cu124 and breaks CUDA; PYTHONNOUSERSITE=1 selects the working venv torch.)
- **Early-stop floor (MED) FIXED.** patience=15, min_epochs=milestones[0]+patience -> with decay at 50, trains >=65 epochs (>=15 past the decay) so the post-decay robust peak is captured.
- **Split indices saved (MED) FIXED.** val_idx + seed + n_train written to each cell JSON.
- **cuDNN determinism (MED) DECISION.** benchmark=True + tf32 for speed (fixed input sizes); reruns are statistically, not bit-, reproducible -> the exact trained models are preserved as checkpoints. Documented honestly.
- **CIFAR_STD typo (LOW) FIXED.** aligned to (0.2470, 0.2435, 0.2616), matching the small-net harness for cross-scale comparability.

PERFORMANCE: bf16 mixed precision for training (eval stays fp32 for radius/gradient precision); AT schedule shortened to decay 50/75 / cap 100 / early-stop (~65-85 effective epochs) -- the claim is the *correlations*, not SOTA robustness, and the best-robust point sits just after the first decay. Timing (old design): zero-pad-standard 69s/ep, circular-APS 255s/ep. Re-timed with AMP + all-circular to size the grid.
