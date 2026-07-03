#!/usr/bin/env bash
# =============================================================================
# Fire-on-free-GPU batch: B1 -> A1-opt -> A5-opt, strictly sequential, one GPU.
#
#   B1     Wang et al. 2025 equivariance steelman: train THEIR P4 CascadedGCNN with THEIR
#          recipe, eval their FGSM/PGD protocol + AutoAttack (n=1000, eps {0.01,0.015,0.03}
#          pixel-space; 0.015 == their 0.03 normalized budget) + masking checks.
#          -> paper/results/b1_wang/
#   A1-opt standard-train OUR tips arm WITH TIPS's auxiliary losses (alpha=0.35, wake 17/80,
#          their MSE(psi_x, x_t) objective; see tips_aux_train.py header for every choice).
#          -> paper/results/resnet_scale/c10stdaux_tips_s0.*
#   A5-opt weak-attack sweep, seed-1 replicate: first std-train the five seed-1 arms
#          (c10std_{standard,blurpool,aps,aug,tips}_s1 -- registered in resnet_run.py, OUT of
#          ORDER), then tips_weakattack.py --seed 1 -> tips_weakattack_w1.0_s1.json.
#
# Every step is resumable/skippable (done-markers / existing files); rerunning is safe.
# Usage:   bash external/b1_batch.sh --gpu <free-gpu-id>
#          nohup bash external/b1_batch.sh --gpu 0 > /dev/null 2>&1 &   (logs are per-step)
# =============================================================================
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
CENV="$ROOT/paper/env/cenv/bin/python"
RSDIR="$ROOT/paper/experiments/resnet_scale"
LOGDIR="$ROOT/paper/results/b1_wang"
mkdir -p "$LOGDIR"

GPU=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --gpu) GPU="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done
export PYTHONNOUSERSITE=1

step () {  # step <name> <logfile> <cmd...>
  local name="$1" log="$2"; shift 2
  echo "[b1_batch] ==== $name  ($(date '+%F %T'))  log=$log ===="
  if "$@" 2>&1 | tee -a "$log"; then
    echo "[b1_batch] $name OK"
  else
    echo "[b1_batch] $name FAILED (see $log) -- continuing with next step" >&2
  fi
}

# ---------------- B1 (highest value: closes the last steelman flank) ----------------
step "B1 wang-equivariance train+eval" "$LOGDIR/b1_batch_B1.log" \
  bash "$HERE/b1_run.sh" --gpu "$GPU" --variant cascaded --seed 0

# ---------------- A1-opt: tips arm + TIPS aux losses (std training) ----------------
step "A1-opt tips+aux std train" "$ROOT/paper/results/resnet_scale/c10stdaux_tips_s0.batchlog" \
  env CUDA_VISIBLE_DEVICES="$GPU" "$CENV" "$RSDIR/tips_aux_train.py" --gpu 0 --width 1.0 --seed 0

# ---------------- A5-opt: seed-1 weak-attack replicate ----------------
# (a) std-train the five seed-1 arms (skip automatically if .done exists)
for ARM in standard blurpool aps aug tips; do
  CELL="c10std_${ARM}_s1"
  step "A5-opt train $CELL" "$ROOT/paper/results/resnet_scale/${CELL}.batchlog" \
    env CUDA_VISIBLE_DEVICES="$GPU" "$CENV" "$RSDIR/resnet_run.py" --cell "$CELL" --gpu 0
done
# (b) the sweep itself (resumable per (arm,eps); eval points fixed to seed-0 subset by design)
step "A5-opt weak-attack sweep seed1" "$ROOT/paper/results/resnet_scale/tips_weakattack_w1.0_s1.batchlog" \
  env CUDA_VISIBLE_DEVICES="$GPU" "$CENV" "$RSDIR/tips_weakattack.py" --gpu 0 --width 1.0 --seed 1

echo "[b1_batch] ALL DONE ($(date '+%F %T'))"
