#!/usr/bin/env bash
# Parametrized auto-restart guard: $1=GPU  $2=tag  $3..=encoders
# --resume=1 (default) + per-cell checkpointing => a restart loses at most the in-flight cell.
set -u
cd /home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/pilots/c1_tower
GPU="$1"; TAG="$2"; shift 2; ENCS="$*"
PY=/home/students/.conda/envs/llmtransfer/bin/python
LOG="logs_promptcond_${TAG}.log"
MAX=8
for i in $(seq 1 $MAX); do
  echo "=== [guard $TAG gpu$GPU] attempt $i/$MAX start $(date -u +%H:%M:%SZ) enc=$ENCS ===" >> "$LOG"
  CUDA_VISIBLE_DEVICES="$GPU" "$PY" -u run_crownjewel_promptcond.py \
      --encoders $ENCS --tag "$TAG" \
      --apgd_iters 50 --radius_max_images 80 --aa_time_cap_s 1800 >> "$LOG" 2>&1
  rc=$?
  if [ $rc -eq 0 ]; then
    echo "=== [guard $TAG] COMPLETED rc=0 attempt $i $(date -u +%H:%M:%SZ) ===" >> "$LOG"; exit 0
  fi
  echo "=== [guard $TAG] exited rc=$rc attempt $i $(date -u +%H:%M:%SZ); resume in 30s ===" >> "$LOG"
  sleep 30
done
echo "=== [guard $TAG] GAVE UP after $MAX $(date -u +%H:%M:%SZ) ===" >> "$LOG"
exit 1
