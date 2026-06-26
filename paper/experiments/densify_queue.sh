#!/usr/bin/env bash
# Densify the three still-underpowered (n=8) AT regressions to 12-cell grids with bootstrap-CI support,
# mirroring the CIFAR-Linf n-power run. Targets: MNIST-Linf-AT, Fashion-Linf-AT, CIFAR-L2-AT
# (each currently 4 arms x widths{32,64} x 2 seeds = 8 cells).
# WAITS for the ResNet-scale run to release both GPUs (DRIVER_DONE.marker) -> never interrupts it.
# Recipe (eps/steps/alpha) is auto-selected per (dataset,norm) inside cifar_at.py, so the new points
# are directly comparable to the existing 8-cell results.
set -u
cd "/home/students/code/Anas/adversarial-robustness-shift-invariance"
export PYTHONNOUSERSITE=1
E=paper/env/cenv/bin/python
LOG=paper/results
WIDTHS="16 24 32 48 64 96"      # 6 widths x 2 seeds = 12 cells per condition (spread along the eta/L axis)

echo "[densify] waiting for ResNet DRIVER_DONE..." >> $LOG/run_densify.log
while [ ! -f paper/results/resnet_scale/DRIVER_DONE.marker ]; do sleep 120; done
echo "[densify] ResNet done; starting at $(date -u +%FT%TZ)" >> $LOG/run_densify.log

$E paper/experiments/cifar_at.py --dataset mnist   --norm linf --widths $WIDTHS --seeds 2 --tag npow2 >> $LOG/run_densify_mnist.log   2>&1
echo "[densify] mnist done $(date -u +%FT%TZ)" >> $LOG/run_densify.log
$E paper/experiments/cifar_at.py --dataset fashion --norm linf --widths $WIDTHS --seeds 2 --tag npow2 >> $LOG/run_densify_fashion.log 2>&1
echo "[densify] fashion done $(date -u +%FT%TZ)" >> $LOG/run_densify.log
$E paper/experiments/cifar_at.py --dataset cifar   --norm l2   --widths $WIDTHS --seeds 2 --tag npow2 >> $LOG/run_densify_cifarl2.log 2>&1
echo "[densify] cifar-l2 done $(date -u +%FT%TZ)" >> $LOG/run_densify.log

echo done > $LOG/densify_done.marker
echo "[densify] ALL DONE $(date -u +%FT%TZ)" >> $LOG/run_densify.log
