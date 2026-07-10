#!/bin/bash
# Post-run pipeline: waits for the main run (phase1+phase2) to finish, then runs the gauge sweep,
# gradient-masking battery, GCG cross-check, validations, analysis, summary, and figures.
# GPU 0 only. Safe to launch immediately after run_tdiss.py -- it blocks on the main PID.
set -u
cd "$(dirname "$0")"
PY=/home/students/.conda/envs/llmtransfer/bin/python
export CUDA_VISIBLE_DEVICES=0
LOG=logs/post.log
echo "[post] waiting for main run to finish $(date)" | tee -a $LOG

# wait until run_tdiss.py is no longer running
while pgrep -f "run_tdiss.py" >/dev/null; do sleep 60; done
echo "[post] main run finished, starting post pipeline $(date)" | tee -a $LOG

echo "[post] gauge sweep" | tee -a $LOG
$PY -u gauge_sweep.py >> $LOG 2>&1
echo "[post] masking battery" | tee -a $LOG
$PY -u masking_battery.py >> $LOG 2>&1
echo "[post] GCG cross-check (128 prompts)" | tee -a $LOG
$PY -u gcg_check.py --n 128 --steps 250 >> $LOG 2>&1
echo "[post] validations (anchor, judge, paraphrase)" | tee -a $LOG
$PY -u validations.py --what all >> $LOG 2>&1
echo "[post] analysis + summary + figures" | tee -a $LOG
$PY -u analyze.py >> $LOG 2>&1
$PY -u summarize.py >> $LOG 2>&1
$PY -u make_figures.py >> $LOG 2>&1
echo "[post] DONE $(date)" | tee -a $LOG
