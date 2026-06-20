#!/usr/bin/env bash
# n=8 statistical-power queue. Waits for the AT chain to free the GPUs, then runs:
#   (1) dense-width STANDARD dissection  -> tight within-condition consistency<->robustness (n=24 cells, 4 seeds)
#   (2) denser L_inf-AT grid             -> tighten the headline AT correlations beyond the 8-cell grid
# Cheap poll; touches only the two local A6000s already used by this project.
set -u
cd "/home/students/code/Anas/adversarial-robustness-shift-invariance"
E=paper/env/cenv/bin/python
LOG=paper/results

echo "[npower] waiting for AT chain marker..." >> $LOG/run_npower.log
while [ ! -f $LOG/at_chain_done.marker ]; do sleep 120; done
echo "[npower] chain done; starting dense-standard at $(date -u +%FT%TZ)" >> $LOG/run_npower.log

# (1) dense-width standard dissection: widths {16,24,32,48,64,96} x 4 seeds = 24 cells, 96 models
$E paper/experiments/cifar_dissection.py --widths 16 24 32 48 64 96 --seeds 4 \
   --aa_seeds 1 --tag npower >> $LOG/run_npower_std.log 2>&1
echo "[npower] dense-standard done at $(date -u +%FT%TZ)" >> $LOG/run_npower.log

# (2) denser L_inf-AT: widths {24,48,96} x 3 seeds = 12 cells, 36 models (overnight)
$E paper/experiments/cifar_at.py --norm linf --widths 24 48 96 --seeds 3 \
   --tag npower >> $LOG/run_npower_atlinf.log 2>&1
echo "[npower] denser-AT done at $(date -u +%FT%TZ)" >> $LOG/run_npower.log

echo done > $LOG/npower_done.marker
echo "[npower] ALL DONE at $(date -u +%FT%TZ)" >> $LOG/run_npower.log
