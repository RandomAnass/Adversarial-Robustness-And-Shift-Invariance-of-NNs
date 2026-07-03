#!/usr/bin/env bash
# =============================================================================
# B1: Wang et al. 2025 ("Bridging Symmetry and Robustness", NeurIPS 2025) steelman test.
# Trains THEIR 10-layer P4 rotation-equivariant CIFAR-10 model (CascadedGCNN, class extracted
# verbatim from their repo) with THEIR exact recipe (Adam 1e-3, StepLR(50,0.1), bs=128, no aug,
# 200 epochs, final ckpt), then evaluates:
#   their protocol      : clean + their verbatim FGSM/PGD-40 (normalized space), their eps grid
#   pixel space [0,1]   : AutoAttack standard n=1000 at eps {0.01, 0.015, 0.03}
#                         (0.015 pixel == their 0.03 normalized budget), PGD-40 reference,
#                         unbounded-PGD masking check
# Outputs -> paper/results/b1_wang/ (ckpt, train jsonl+meta, one eval json, logs). Resumable.
#
# Usage:
#   real run (GPU):  bash b1_run.sh --gpu 0
#   CPU smoke test:  bash b1_run.sh --smoke
#   options:         --variant cascaded|parallel   --seed N
# =============================================================================
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$HERE/e2cnn_env/bin/python"
RES="$HERE/../paper/results/b1_wang"
mkdir -p "$RES"

GPU=0; SMOKE=0; VARIANT=cascaded; SEED=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --gpu)     GPU="$2"; shift 2 ;;
    --smoke)   SMOKE=1; shift ;;
    --variant) VARIANT="$2"; shift 2 ;;
    --seed)    SEED="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ "$SMOKE" == 1 ]]; then
  export CUDA_VISIBLE_DEVICES=""          # hard guarantee: no GPU in smoke mode
  SM="--smoke"; TAG="${VARIANT}_s${SEED}_smoke"
else
  export CUDA_VISIBLE_DEVICES="$GPU"
  SM=""; TAG="${VARIANT}_s${SEED}"
fi
export PYTHONNOUSERSITE=1

echo "[b1_run] variant=$VARIANT seed=$SEED smoke=$SMOKE CUDA_VISIBLE_DEVICES='${CUDA_VISIBLE_DEVICES}'"
echo "[b1_run] ==== train ===="
"$PY" "$HERE/b1/b1_train.py" --variant "$VARIANT" --seed "$SEED" $SM 2>&1 | tee -a "$RES/${TAG}_train.log"
echo "[b1_run] ==== eval ===="
"$PY" "$HERE/b1/b1_eval.py"  --variant "$VARIANT" --seed "$SEED" $SM 2>&1 | tee -a "$RES/${TAG}_eval.log"
echo "[b1_run] DONE -> $RES/${TAG}_eval.json"
