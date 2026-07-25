#!/usr/bin/env bash
# Full targeted-AA validation guard: $1=GPU $2=tag $3..=encoders
# --targeted 1 = full AutoAttack (APGD-CE + APGD-T, n_target=3). Trimmed n_attack/radius since this is
# a representative subset to test whether the prompt-conditioned eta/L1 ordering survives full AA.
set -u
cd /home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/pilots/c1_tower
GPU="$1"; TAG="$2"; shift 2; ENCS="$*"
PY=/home/students/.conda/envs/llmtransfer/bin/python
LOG="logs_promptcond_${TAG}.log"
MAX=8
for i in $(seq 1 $MAX); do
  echo "=== [guard $TAG gpu$GPU] attempt $i/$MAX start $(date -u +%H:%M:%SZ) enc=$ENCS ===" >> "$LOG"
  CUDA_VISIBLE_DEVICES="$GPU" "$PY" -u run_crownjewel_promptcond.py \
      --encoders $ENCS --tag "$TAG" --targeted 1 \
      --apgd_iters 50 --n_attack 120 --n_prompts 3 --radius_max_images 24 --aa_time_cap_s 3600 >> "$LOG" 2>&1
  rc=$?
  if [ $rc -eq 0 ]; then
    echo "=== [guard $TAG] COMPLETED rc=0 attempt $i $(date -u +%H:%M:%SZ) ===" >> "$LOG"; exit 0
  fi
  echo "=== [guard $TAG] exited rc=$rc attempt $i $(date -u +%H:%M:%SZ); resume in 30s ===" >> "$LOG"
  sleep 30
done
echo "=== [guard $TAG] GAVE UP after $MAX $(date -u +%H:%M:%SZ) ===" >> "$LOG"; exit 1
