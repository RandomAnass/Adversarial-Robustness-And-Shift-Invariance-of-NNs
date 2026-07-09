#!/bin/bash
# Powered dissection: train the 18 graded anti-aliasing AT cells (blur2/blur5/blur7 x 2 widths x 3 seeds)
# split across both GPUs. Same AT protocol (100ep milestones 50/75 patience15) as the existing grid.
cd /home/students/code/Anas/adversarial-robustness-shift-invariance/paper/experiments/resnet_scale
PY="env PYTHONNOUSERSITE=1 ../../env/cenv/bin/python"
G0="c10at_blur2_s0 c10at_blur2_s1 c10at_blur2_s2 c10at_blur2_w0.5_s0 c10at_blur2_w0.5_s1 c10at_blur2_w0.5_s2 c10at_blur5_s0 c10at_blur5_s1 c10at_blur5_s2"
G1="c10at_blur5_w0.5_s0 c10at_blur5_w0.5_s1 c10at_blur5_w0.5_s2 c10at_blur7_s0 c10at_blur7_s1 c10at_blur7_s2 c10at_blur7_w0.5_s0 c10at_blur7_w0.5_s1 c10at_blur7_w0.5_s2"
run_list () { local gpu=$1; shift
  for c in "$@"; do
    [ -f "../../results/resnet_scale/$c.done" ] && { echo "[g$gpu] skip $c (done)"; continue; }
    echo "[g$gpu] START $c $(date +%H:%M)"
    $PY resnet_run.py --cell $c --gpu $gpu > ../../results/resnet_scale/$c.runlog 2>&1
    echo "[g$gpu] END $c rc=$? $(date +%H:%M)"
  done
}
run_list 0 $G0 &
run_list 1 $G1 &
wait
echo "[graded_driver] ALL DONE $(date)"
