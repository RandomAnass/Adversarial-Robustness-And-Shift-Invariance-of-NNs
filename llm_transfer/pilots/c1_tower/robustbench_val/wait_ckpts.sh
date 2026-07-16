#!/bin/bash
cd /home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/pilots/c1_tower/robustbench_val
TARGET="${1:-12}"
while true; do
  N=$(ls rb_models/cifar10/Linf/*.pt 2>/dev/null | grep -vc '.part')
  if [ "$N" -ge "$TARGET" ] || grep -q "DOWNLOADER FINISHED" downloader.log; then
    echo "WAIT_DONE: $N checkpoints at $(date)" > wait_result.txt
    break
  fi
  sleep 60
done
