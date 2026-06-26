#!/usr/bin/env bash
# Post-main GPU work, runs ONLY after the core ResNet-scale run frees both GPUs (DRIVER_DONE.marker).
# Phase A: low-invariance arms (stdzero w0.5 + maxpool both widths, std+AT, seed 0) to widen the
#          shift-consistency axis -> mechanistic test of the weak AT consistency anti-prediction.
# Phase B: densify the three n=8 AT regressions (MNIST-Linf, Fashion-Linf, CIFAR-L2) to 12-cell grids.
# Never interrupts the core run.
set -u
cd "/home/students/code/Anas/adversarial-robustness-shift-invariance"
export PYTHONNOUSERSITE=1
PY=paper/env/cenv/bin/python
RUN=paper/experiments/resnet_scale/resnet_run.py
RS=paper/results/resnet_scale
LOG=paper/results
WIDTHS="16 24 32 48 64 96"

echo "[postmain] waiting for ResNet DRIVER_DONE..." >> $LOG/run_postmain.log
while [ ! -f $RS/DRIVER_DONE.marker ]; do sleep 120; done
echo "[postmain] core run done; Phase A (low-invariance arms) at $(date -u +%FT%TZ)" >> $LOG/run_postmain.log

# Phase A: dispatch the new low-invariance cells two at a time (one per GPU). Skips any already .done.
CELLS="c10std_stdzero_w0.5_s0 c10at_stdzero_w0.5_s0 c10std_maxpool_s0 c10at_maxpool_s0 c10std_maxpool_w0.5_s0 c10at_maxpool_w0.5_s0"
set -- $CELLS
while [ $# -gt 0 ]; do
  c0=$1; shift
  if [ $# -gt 0 ]; then c1=$1; shift; else c1=""; fi
  $PY $RUN --cell "$c0" --gpu 0 >> $RS/$c0.log 2>&1 &
  p0=$!
  if [ -n "$c1" ]; then $PY $RUN --cell "$c1" --gpu 1 >> $RS/$c1.log 2>&1 & p1=$!; else p1=""; fi
  wait $p0; [ -n "$p1" ] && wait $p1
  echo "[postmain] done pair: $c0 $c1 at $(date -u +%FT%TZ)" >> $LOG/run_postmain.log
done
echo "[postmain] Phase A done; Phase B (densify) at $(date -u +%FT%TZ)" >> $LOG/run_postmain.log

# Phase B: densify the three underpowered AT regressions (recipe auto-selected per dataset/norm).
$PY paper/experiments/cifar_at.py --dataset mnist   --norm linf --widths $WIDTHS --seeds 2 --tag npow2 >> $LOG/run_densify_mnist.log   2>&1
echo "[postmain] mnist done $(date -u +%FT%TZ)" >> $LOG/run_postmain.log
$PY paper/experiments/cifar_at.py --dataset fashion --norm linf --widths $WIDTHS --seeds 2 --tag npow2 >> $LOG/run_densify_fashion.log 2>&1
echo "[postmain] fashion done $(date -u +%FT%TZ)" >> $LOG/run_postmain.log
$PY paper/experiments/cifar_at.py --dataset cifar   --norm l2   --widths $WIDTHS --seeds 2 --tag npow2 >> $LOG/run_densify_cifarl2.log 2>&1
echo "[postmain] cifar-l2 done $(date -u +%FT%TZ)" >> $LOG/run_postmain.log

echo done > $LOG/postmain_done.marker
echo "[postmain] ALL DONE $(date -u +%FT%TZ)" >> $LOG/run_postmain.log
