# Diffusion-Data Adversarial Robustness — Feasibility & Recipe Scoping

Scope: determine what is realistically runnable on **2x RTX A6000 (48 GB each)** so the team
can pilot a NOVEL hypothesis about *why/which* diffusion-generated data helps adversarial
training, without reproducing SOTA absolute numbers and without training a diffusion model
from scratch. Compiled 2026-06-29 from firsthand fetches of arXiv, the Wang-2023 GitHub repo,
HuggingFace, NVlabs/edm, and DeepMind's release, plus local disk/env checks.

TL;DR
- **Do NOT train a diffusion model.** Pre-generated EDM CIFAR-10 data is a direct download.
- **Smallest config that still shows a clear benefit:** WRN-28-10 + TRADES + **1M EDM** synthetic
  images. Wang-2023 Table 2 (WRN-28-10, Linf 8/255 AutoAttack): **0 synthetic = 60.73%,
  1M = 63.35%** (a clean +2.6 pt jump), 20M = 67.31%, 50M = 67.17%.
- **Full 1M/400-epoch WRN-28-10 recipe on 2x A6000 ≈ 3.5–4.7 days.** Too long for a pilot.
- **Minimal <1-day pilot:** PreActResNet-18 + 1M EDM, ~100–150 epochs, run the with/without-synthetic
  arms (and a data-selection arm) at a *fixed compute budget*. Gives clear signal in ~6–15 h.
- Local env (`paper/env/cenv`) already has torch 2.6.0+cu124, torchvision, autoattack, robustbench,
  torchattacks. **One gotcha:** a stray `~/.local` torch 2.12.1+cu130 shadows it and breaks CUDA —
  run everything with `PYTHONNOUSERSITE=1`.
- Disk: 11 TB free on `/home`. 1M set = 3.08 GB; 50M set = ~154 GB. No disk concern.

---

## 1. Public pre-generated synthetic CIFAR-10 data (download, do NOT generate)

### 1a. Wang et al. 2023, "Better Diffusion Models Further Improve Adversarial Training" (ICML 2023) — EDM data
Hosted on HuggingFace dataset repo **`P2333/DM-Improves-AT`**. Files are plain (uncompressed)
`.npz`, ~3.08 GB per 1M images (so they store raw `uint8`, not `savez_compressed`).

Verified `Content-Length` (HEAD requests, 2026-06-29):

| Set  | URL (prefix `https://huggingface.co/datasets/P2333/DM-Improves-AT/resolve/main/cifar10/`) | Size |
|------|--------------------------------------------------------------------------------------------|------|
| 1M   | `1m.npz`                              | **3.08 GB** |
| 5M   | `5m.npz`                              | 15.4 GB |
| 10M  | `10m.npz`                             | 30.8 GB |
| 20M  | `20m_part1.npz`, `20m_part2.npz`      | 30.8 GB x2 = **61.6 GB** |
| 50M  | `50m_part1.npz` … `50m_part4.npz`     | ~38.5 GB x4 ≈ **154 GB** |

`.npz` layout (NumPy): keys `image` → `(N, 32, 32, 3)` `uint8`, `label` → `(N,)` `int`.
(Verify once after download: `python -c "import numpy as np; d=np.load('1m.npz'); print(d.files, d['image'].shape, d['image'].dtype)"`.)

Download command (only the 1M set needed for the pilot):
```bash
cd /home/students/code/Anas/adversarial-robustness-shift-invariance/paper/diffusion_robustness
mkdir -p edm_data/cifar10
# robust resumable download
wget -c -O edm_data/cifar10/1m.npz \
  https://huggingface.co/datasets/P2333/DM-Improves-AT/resolve/main/cifar10/1m.npz
# (optional larger sets, same prefix: 5m.npz, 10m.npz, 20m_part{1,2}.npz, 50m_part{1..4}.npz)
```
HuggingFace `resolve/main/...` links are public (no token). The repo also documents that 20M/50M
are split "into several parts" purely for upload size; concatenate the arrays after loading.

### 1b. Gowal/Rebuffi 2021 (DeepMind), "Improving Robustness using Generated Data" — DDPM data
A 1M-image **DDPM**-generated CIFAR-10 set is still live on Google Cloud Storage:
```bash
wget -c https://storage.googleapis.com/dm-adversarial-robustness/cifar10_ddpm.npz   # 3.076 GB
```
Same `.npz` layout (`image` / `label`). Useful as a *second generator* arm — DDPM vs EDM data
quality is itself a clean mechanism comparison. DeepMind also ships matching **pretrained robust
checkpoints** (PyTorch + JAX), e.g.:
- WRN-28-10 (DDPM, 100M aug): `…/cifar10_linf_wrn28-10_ddpm_100m.pt` — clean 87.50 / robust 63.44
- WRN-70-16 (DDPM+cutmix): `…/cifar10_linf_wrn70-16_cutmix_ddpm_100m.pt` — clean 88.74 / robust 66.11
- ResNet-18 (DDPM): `…/cifar10_linf_resnet18_ddpm_100m.pt` — clean 87.35 / robust 58.63
  (prefix `https://storage.googleapis.com/dm-adversarial-robustness/`)

These give a ready ResNet-18 robust baseline to attack/probe without any training.

### 1c. If custom generation is unavoidable: pretrained EDM (Karras 2022, NVlabs/edm)
Pretrained CIFAR-10 EDM checkpoints (no diffusion training needed):
```
https://nvlabs-fi-cdn.nvidia.com/edm/pretrained/edm-cifar10-32x32-cond-vp.pkl   # class-conditional
https://nvlabs-fi-cdn.nvidia.com/edm/pretrained/edm-cifar10-32x32-uncond-vp.pkl # unconditional
```
Sampling cost: deterministic Heun sampler, **18 steps = NFE 35 per image**, FID 1.79 (cond) /
1.97 (uncond). Generating a *custom* 1M set with the conditional model is roughly a few GPU-hours
on the 2x A6000 (order ~1–3 h, sampler/batch dependent); generating 20–50M would be ~hundreds of
GPU-hours — **not worth it, download instead.** Only generate if the novel hypothesis *requires*
a modified sampler / custom labels.

---

## 2. SOTA recipe (Wang 2023, from the repo's `train-wa.py` + paper Table 2 / App.)

Canonical training command (1M config, from `wzekai99/DM-Improves-AT` README):
```bash
python train-wa.py --data-dir 'dataset-data' --log-dir 'trained_models' \
  --desc 'WRN28-10Swish_cifar10s_lr0p2_TRADES5_epoch400_bs512_fraction0p7_ls0p1' \
  --data cifar10s --model wrn-28-10-swish \
  --batch-size 512 --num-adv-epochs 400 --lr 0.2 \
  --beta 5.0 --unsup-fraction 0.7 \
  --aux-data-filename 'edm_data/cifar10/1m.npz' --ls 0.1
```

| Knob | Value |
|------|-------|
| Architecture | **WRN-28-10-Swish** (small) / WRN-70-16-Swish (large) |
| Loss | **TRADES**, β = 5.0 |
| Inner attack | **PGD-10**, ε = 8/255 (Linf), step α = 2/255 |
| Real:synthetic per batch | `unsup-fraction 0.7` → **30% real / 70% generated** ("original-to-generated ratio 0.3"; 0.2 when >1M generated) |
| Weight averaging | **EMA**, decay τ = 0.995 (the "-wa" in train-wa) |
| Label smoothing | 0.1 |
| LR | 0.2, cosine schedule |
| 1M config | batch 512, **400 epochs** |
| 20M config | batch 2048, 2400 epochs |
| 50M config | batch 2048, 1600 epochs |
| L2 variant | ε = 128/255 |

Reported CIFAR-10 Linf 8/255 (AutoAttack), **WRN-28-10**, Table 2 — the key scaling:

| Generated images | Clean | AutoAttack robust |
|------------------|-------|-------------------|
| **0 (baseline)** | —     | **60.73%** |
| **1M EDM**       | —     | **63.35%**  ← smallest clear benefit (+2.6 pt) |
| 20M EDM          | 92.44%| 67.31% |
| 50M EDM          | —     | 67.17% |
| WRN-70-16, 50M   | 93.25%| **70.69%** (paper headline) |

**Smallest config with a clear diffusion-data benefit = WRN-28-10 + TRADES + 1M EDM** (63.35 vs
60.73). That +2.6 pt gap is the effect the pilot should aim to reproduce/dissect — not the 70.69.

Cost of that 1M config (authors' own numbers): WRN-28-10 trains at **3.45 min/epoch on 4x A100
SXM4-40GB** (bs 2048). 400 epochs ≈ **23 h wall on 4 A100 ≈ ~92 A100-GPU-hours**.

---

## 3. 2x A6000 feasibility

Efficiency: for AMP conv-heavy AT (PGD inner loop), one A6000 ≈ **0.45–0.55x** an A100-SXM4-40GB
(half the TF32 tensor throughput, ~half the memory bandwidth: 768 vs 1555 GB/s). Use ~0.5 midpoint.
Memory is a non-issue: WRN-28-10 TRADES at bs 512/GPU fits in 40 GB on A100, so it fits comfortably
in 48 GB (can push bs ~640–768/GPU).

Scaling the 92 A100-GPU-h figure:

| Run | Est. wall-clock on 2x A6000 | Notes |
|-----|------------------------------|-------|
| **(a) Full WRN-28-10, 1M, 400 ep, TRADES** | **~3.5–4.7 days** (≈ 82–112 h; ~13–17 min/epoch) | reaches ~63% AA; too long for a pilot |
| (a') Same but **80–100 ep** | **~18–24 h** | the with/without-synthetic *gap* is already visible by ~50–100 ep |
| **(b) PreActResNet-18, 1M, 100–150 ep** | **~6–15 h** | PRN-18 ≈ 3–4x cheaper than WRN-28-10 → ~3.5–4.5 min/epoch on 2x A6000 |
| (b') PRN-18, 100 ep, **single arm** | **~6–7.5 h** | leaves room for 2–3 arms in a day |

These are scaling estimates from the authors' per-epoch number, not measured here — **time-box the
first run to 2 epochs to calibrate min/epoch before committing.**

---

## 4. Minimal-signal pilot (<1 day on 2x A6000)

Goal: get signal on a mechanism/selection/efficiency hypothesis about the diffusion-data gain,
**not** SOTA. Recommended:

**Backbone:** PreActResNet-18 (`--model preact-resnet-18` / `resnet-18` in the repo), TRADES β=5,
PGD-10 ε=8/255, EMA τ=0.995, ~120 epochs. ~6–7 h per arm → **2–3 arms fit in <1 day.**

**Fixed-compute comparison (same epochs/steps, vary only the data):**
1. **No synthetic** (50k real only) — baseline.
2. **+1M EDM**, ratio 0.3 — should reproduce the gap (the Wang 60.73→63.35 effect, at PRN-18 scale).
3. **Selected/filtered 100k–1M** — the novel arm: pick the synthetic subset by your hypothesis
   (e.g. shift-consistency, margin/‖∇‖₁ threat-matched score, orbit-variance) and test whether a
   *small selected* set matches a *large random* set. This directly tests "which diffusion images
   carry the robustness signal," which aligns with the project's consistency / threat-matched
   η/L line and is genuinely novel vs. Wang's "more is better."

Why this gives signal fast: the with/without-synthetic AA gap opens within the first ~50 epochs;
at fixed budget, a *relative* AA difference between random-1M and selected-100k is a clean,
publishable signal even if absolute AA is ~5–8 pt below the 400-epoch SOTA. Evaluate with the
installed `autoattack` (or `robustbench`) on the 10k test set (~minutes).

Optional zero-training probes (hours, no AT run): attack the released ResNet-18/WRN-28-10 DDPM
checkpoints (§1b) and the EDM WRN-28-10 checkpoint to study the trained models directly.

---

## 5. Existing code to reuse

- **Primary:** `https://github.com/wzekai99/DM-Improves-AT` — the exact training code
  (`train-wa.py`, WRN/PRN models w/ Swish, TRADES, EMA, `cifar10s` semi-sup loader, `--aux-data-filename`
  for the `.npz`). Built on the Gowal/Rebuffi codebase. Clone and point `--aux-data-filename` at the
  downloaded `1m.npz`.
- DeepMind release (data + JAX/PyTorch robust checkpoints):
  `https://github.com/deepmind/deepmind-research/tree/master/adversarial_robustness`.
- **RobustBench** (`pip` `robustbench`, already installed) — model zoo + standardized AutoAttack eval;
  use for evaluation and to pull baseline checkpoints.
- NVlabs/edm (`https://github.com/NVlabs/edm`) — only if custom generation is needed.

### Env check (local, `paper/env/cenv`)
Already present and sufficient — no installs needed:
- `torch 2.6.0+cu124`, `torchvision 0.21.0+cu124`, `numpy 2.4.4`, `scipy`, `matplotlib`, `pillow`
- `autoattack 0.1`, `torchattacks 3.5.1`, `robustbench`

**Critical gotcha:** a user-site `~/.local/.../torch 2.12.1+cu130` shadows the cenv torch and reports
`cuda.is_available() == False` (driver 570.133.20 is CUDA 12.8, too old for the cu130 build).
Run everything with user-site disabled:
```bash
export PYTHONNOUSERSITE=1
/home/students/code/Anas/adversarial-robustness-shift-invariance/paper/env/cenv/bin/python -c \
 "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.device_count())"
# -> 2.6.0+cu124 True 2     (both A6000s visible)
```
No wandb required (the repo logs to local files/tensorboard).

---

## 6. Disk

- `/home` filesystem (holds the repo): **11 TB free** of 14 TB (`df -h`, 2026-06-29).
- Repo `paper/data` currently 825 MB.
- Storage budget: 1M = 3.08 GB, 5M = 15.4 GB, 10M = 30.8 GB, 20M = 61.6 GB, 50M ≈ 154 GB.
- Suggested location:
  `/home/students/code/Anas/adversarial-robustness-shift-invariance/paper/diffusion_robustness/edm_data/cifar10/`.
  Even the full 50M set (154 GB) fits with huge margin; the pilot only needs the 3.08 GB 1M file.

---

### Sources (firsthand)
- Wang et al. 2023, arXiv:2302.04638 (abstract + ar5iv Table 2 / training details): https://arxiv.org/abs/2302.04638 , https://ar5iv.labs.arxiv.org/abs/2302.04638
- Code/data repo: https://github.com/wzekai99/DM-Improves-AT ; data: https://huggingface.co/datasets/P2333/DM-Improves-AT
- DeepMind release (DDPM data + checkpoints): https://github.com/deepmind/deepmind-research/tree/master/adversarial_robustness ; data: https://storage.googleapis.com/dm-adversarial-robustness/cifar10_ddpm.npz
- EDM (Karras 2022): https://github.com/NVlabs/edm ; checkpoint: https://nvlabs-fi-cdn.nvidia.com/edm/pretrained/edm-cifar10-32x32-cond-vp.pkl
- RobustBench: https://github.com/RobustBench/robustbench
- Per-epoch cost / 4x A100 / batch sizes: Wang 2023 experimental setup (ar5iv, fetched above).
