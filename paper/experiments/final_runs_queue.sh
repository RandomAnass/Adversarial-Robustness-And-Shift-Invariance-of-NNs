#!/usr/bin/env bash
# Final runs after the audit + the user's "full 10k" decision.
# Phase A: CIFAR-100 ResNet cells (data now downloaded+verified) -> completes the ResNet RQ4 grid.
# Phase B: re-run ALL 4 small-net AT conditions with full-10,000-image AutoAttack (C1 fix). New
#          tag full10k so the original 512-based JSONs are kept for the audit trail; we compare.
set -u
cd "/home/students/code/Anas/adversarial-robustness-shift-invariance"
export PYTHONNOUSERSITE=1
PY=paper/env/cenv/bin/python
RUN=paper/experiments/resnet_scale/resnet_run.py
RS=paper/results/resnet_scale
LOG=paper/results

echo "[final] START $(date -u +%FT%TZ)" >> $LOG/run_final.log

# ---- Phase A: CIFAR-100 ResNet cells, 2 at a time ----
echo "[final] Phase A: CIFAR-100 cells $(date -u +%FT%TZ)" >> $LOG/run_final.log
A=(c100at_standard_s0 c100at_blurpool_s0 c100at_aps_s0 c100at_aug_s0)
i=0
while [ $i -lt ${#A[@]} ]; do
  c0=${A[$i]}; c1=${A[$((i+1))]:-}
  $PY $RUN --cell "$c0" --gpu 0 >> $RS/$c0.log 2>&1 & p0=$!
  if [ -n "$c1" ]; then $PY $RUN --cell "$c1" --gpu 1 >> $RS/$c1.log 2>&1 & p1=$!; else p1=""; fi
  wait $p0; [ -n "$p1" ] && wait $p1
  echo "[final] c100 pair done: $c0 $c1 $(date -u +%FT%TZ)" >> $LOG/run_final.log
  i=$((i+2))
done

# ---- Phase B: full-10k AutoAttack re-run of the 4 small-net AT conditions ----
echo "[final] Phase B: full-10k AT re-run $(date -u +%FT%TZ)" >> $LOG/run_final.log
$PY paper/experiments/cifar_at.py --dataset cifar   --norm linf --aa_n 10000 --tag full10k >> $LOG/run_full10k_cifarlinf.log 2>&1
echo "[final] cifar-linf full10k done $(date -u +%FT%TZ)" >> $LOG/run_final.log
$PY paper/experiments/cifar_at.py --dataset cifar   --norm l2   --aa_n 10000 --tag full10k >> $LOG/run_full10k_cifarl2.log   2>&1
echo "[final] cifar-l2 full10k done $(date -u +%FT%TZ)" >> $LOG/run_final.log
$PY paper/experiments/cifar_at.py --dataset mnist   --norm linf --aa_n 10000 --tag full10k >> $LOG/run_full10k_mnist.log     2>&1
echo "[final] mnist full10k done $(date -u +%FT%TZ)" >> $LOG/run_final.log
$PY paper/experiments/cifar_at.py --dataset fashion --norm linf --aa_n 10000 --tag full10k >> $LOG/run_full10k_fashion.log   2>&1
echo "[final] fashion full10k done $(date -u +%FT%TZ)" >> $LOG/run_final.log

echo done > $LOG/final_runs_done.marker
echo "[final] ALL DONE $(date -u +%FT%TZ)" >> $LOG/run_final.log
