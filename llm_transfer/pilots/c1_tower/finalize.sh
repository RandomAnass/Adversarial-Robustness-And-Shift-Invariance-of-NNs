#!/bin/bash
# Wait for the C1 main run to finish, then run analysis + figures + commit.
# Idempotent; safe to launch with nohup. GPU 1 only (analysis is CPU; figures are CPU).
set -u
ROOT=/home/students/code/Anas/adversarial-robustness-shift-invariance
PILOT=$ROOT/llm_transfer/pilots/c1_tower
LOG=$ROOT/llm_transfer/results/c1_tower/logs/run_main.log
PY=/home/students/.conda/envs/llmtransfer/bin/python
export PYTHONWARNINGS=ignore CUDA_VISIBLE_DEVICES=1

# 1. wait for DONE or a hard error
while true; do
  if grep -qE "DONE ->" "$LOG" 2>/dev/null; then echo "[finalize] run DONE"; break; fi
  if grep -qE "Traceback|CUDA error|RuntimeError" "$LOG" 2>/dev/null; then
    echo "[finalize] run ERROR detected; finalizing partial"; break; fi
  sleep 30
done

cd "$PILOT"
# 2. analysis at headline eps=4/255 and also 2/255
$PY analyze_c1.py --tag main --eps 0.01568627451 > "$ROOT/llm_transfer/results/c1_tower/logs/analysis_eps4.log" 2>&1
$PY analyze_c1.py --tag main --eps 0.00784313725 > "$ROOT/llm_transfer/results/c1_tower/logs/analysis_eps2.log" 2>&1
# rename the eps2 analysis so it is not overwritten
cp "$ROOT/llm_transfer/results/c1_tower/c1_analysis_main.json" \
   "$ROOT/llm_transfer/results/c1_tower/c1_analysis_main_eps4.json" 2>/dev/null
# 3. figures (headline eps)
$PY figures_c1.py --tag main --eps 0.01568627451 > "$ROOT/llm_transfer/results/c1_tower/logs/figures.log" 2>&1
echo "[finalize] analysis + figures done"

# 4. commit results
cd "$ROOT"
git config user.name "RandomAnass"
git config user.email "anass.al-ammiri@tum.de"
git add -f llm_transfer/results/c1_tower/c1_results_main.json \
   llm_transfer/results/c1_tower/c1_analysis_main.json \
   llm_transfer/results/c1_tower/c1_analysis_main_eps4.json \
   llm_transfer/results/c1_tower/figures/*.png 2>/dev/null
git commit -q -m "C1 results: tower-panel eta/L vs shift-consistency vs AutoAttack robustness

ImageNet-100 zero-shot, 7 frozen towers at 224px, encoder-level AutoAttack.
Includes per-tower table, cross-tower + per-image rank correlations with bootstrap
CIs, partial correlation vs clean acc, selection-rule regret, gradient-masking
audit (FGSM>=PGD40>=APGD + Square gap), and KILL-criterion evaluation." && echo "[finalize] committed"
echo "[finalize] ALL DONE"
