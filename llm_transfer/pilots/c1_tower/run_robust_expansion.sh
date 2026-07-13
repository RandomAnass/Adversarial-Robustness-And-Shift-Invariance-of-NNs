#!/bin/bash
# Robust-panel expansion (review round 1 W1 fix): run 6 new robust encoders (FARE4/TeCoA4 at
# B/32, B/16, ConvNeXt) -> c1_results_robustexp.json + per_image_*_ext.pt. Robust panel 4 -> 10.
# Run when a GPU frees:  bash run_robust_expansion.sh <gpu_id>
set -e
GPU=${1:-0}
cd "$(dirname "$0")"
PY=/home/students/.conda/envs/llmtransfer/bin/python
CUDA_VISIBLE_DEVICES=$GPU $PY run_c1_extended.py \
  --towers fare4_b32 tecoa4_b32 fare4_b16 tecoa4_b16 fare4_cnxt tecoa4_cnxt \
  --tag robustexp --eps 0.00784313725490196 0.01568627450980392 \
  2>&1 | grep -vE "Loading|past_key|Warning|warn"
echo "=== expansion done -> c1_results_robustexp.json ==="
