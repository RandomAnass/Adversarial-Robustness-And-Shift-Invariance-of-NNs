#!/bin/bash
# Scale-up for the attack-free early-stopping payoff: real-only (dose 0) PGD-AT across arms x 3 seeds,
# per-epoch checkpoints (save every 2), no per-cell AutoAttack. All overfit -> where eta/L beats clean.
cd /home/students/code/Anas/adversarial-robustness-shift-invariance/paper/diffusion_robustness
PY="env PYTHONNOUSERSITE=1 ../env/cenv/bin/python"
for arm in standard aps blurpool; do
  echo "[scaleup] === arm $arm START $(date +%H:%M) ==="
  $PY diff_pilot_v2.py --arm $arm --synth 0 --seeds 3 --epochs 40 \
     --save_ckpt_every 2 --aa_seeds 0 --tag poes_$arm --gpus 2 \
     > results/poes_$arm.log 2>&1
  echo "[scaleup] === arm $arm END rc=$? $(date +%H:%M) ==="
done
echo "[scaleup] ALL DONE $(date)"
