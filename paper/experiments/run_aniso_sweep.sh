#!/usr/bin/env bash
# AT-strength eps-sweep for the gradient-anisotropy generalization test (MNIST + Fashion).
# GPU 0 ONLY. Each eps trains a separate model grid (arm=standard, widths {32,64}, seeds {0,1})
# and is tagged anisosweep_e<eps> so progressive-save partials (keyed arm/w/seed) never collide.
# Resume-safe: cifar_at.py skips cells whose partial file already exists.
set -euo pipefail
cd "$(dirname "$0")/../.."   # repo root
PY="paper/env/cenv/bin/python"
export PYTHONNOUSERSITE=1 CUDA_VISIBLE_DEVICES=0 AA_BS=256

# aa_version=custom -> APGD-CE + APGD-T (deterministic, strong, ranking-grade; preserves aa<=pgd
# masking check). AutoAttack "standard" (adds FAB-T + Square) is ~4x slower and unnecessary for a
# ranking study; rr_l2 (DDN radius) is the metric-free PRIMARY metric anyway.
COMMON="--arms standard --widths 32 64 --seeds 2 --n 50000 --ntest 10000 --epochs 30 \
        --rad_n 1000 --aa_n 1000 --aa_version custom --pgd_steps 40 --serial --gpus 1"

run() {  # dataset eps "aa_eps_list"
  local ds="$1" eps="$2" aaeps="$3"
  local tag="anisosweep_e$(echo "$eps" | tr '.' 'p')"
  echo "=== $ds eps=$eps tag=$tag aa_eps=$aaeps ==="
  $PY paper/experiments/cifar_at.py --dataset "$ds" --norm linf --eps "$eps" \
      --aa_eps $aaeps --tag "$tag" $COMMON
}

for eps in 0.05 0.1 0.15 0.2 0.3 0.4; do
  run mnist "$eps" "0.1 0.2 0.3"
done
for eps in 0.02 0.05 0.1 0.15 0.2 0.3; do
  run fashion "$eps" "0.05 0.1 0.15"
done
echo "ALL_SWEEP_CELLS_DONE"
