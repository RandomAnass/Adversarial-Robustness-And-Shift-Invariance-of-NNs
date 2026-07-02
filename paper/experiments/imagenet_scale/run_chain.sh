#!/bin/bash
# S2 ImageNet-100 chain: wait for a FULLY FREE GPU (prefer 1; GPU 0 additionally requires our
# tips_driver queue to be finished), then: GPU smoke -> per-arm Fast-AT train + eval (seed 0)
# -> analysis -> seed 1 -> analysis. Never queues onto a GPU that has ANY running process
# (ours or anyone else's); double-checks 60s apart to avoid grabbing brief inter-job gaps.
# Idempotent: arms with an existing eval JSON (or active lock) are skipped, so multiple chain
# instances may run concurrently (one per free GPU) without duplicating work.
set -u
BASE=/home/students/code/Anas/adversarial-robustness-shift-invariance/paper
EXP=$BASE/experiments/imagenet_scale
RES=$BASE/results/imagenet_scale
PYBIN=$BASE/env/cenv/bin/python
LOG=$RES/run_chain.log
mkdir -p "$RES"
cd "$EXP" || exit 1
log(){ echo "[$(date +%F_%T)] $*" >> "$LOG"; }

free_gpu(){                    # echo index of a usable fully-free GPU; rc 1 if none
  local idx uuid pids
  for idx in 1 0; do
    uuid=$(nvidia-smi --query-gpu=index,uuid --format=csv,noheader | awk -F', ' -v i="$idx" '$1==i{print $2}')
    pids=$(nvidia-smi --query-compute-apps=gpu_uuid,pid --format=csv,noheader | awk -F', ' -v u="$uuid" '$1==u{print $2}')
    [ -n "$pids" ] && continue
    if [ "$idx" = "0" ] && pgrep -f "tips_driver.py" >/dev/null 2>&1; then continue; fi
    echo "$idx"; return 0
  done
  return 1
}

wait_gpu(){                    # block until a GPU is free on two checks 60s apart
  local g g2 n=0
  while true; do
    if g=$(free_gpu); then
      sleep 60
      if g2=$(free_gpu) && [ "$g2" = "$g" ]; then echo "$g"; return 0; fi
    fi
    n=$((n+1)); [ $((n % 10)) -eq 0 ] && log "still waiting for a free GPU (poll $n)"
    sleep 120
  done
}

run_py(){                      # run_py <desc> <script+args...> on the next free GPU
  local desc=$1; shift
  local g; g=$(wait_gpu)
  log "START $desc on GPU $g"
  if CUDA_VISIBLE_DEVICES=$g PYTHONNOUSERSITE=1 "$PYBIN" "$@" >> "$LOG" 2>&1; then
    log "DONE  $desc"; return 0
  else
    log "FAIL  $desc"; return 1
  fi
}

log "=== chain start (pid $$) ==="
if [ ! -f "$RES/.smoke_ok" ]; then
  run_py "smoke" smoke.py || { log "ABORT: smoke failed"; exit 1; }
  tail -50 "$LOG" | grep -q SMOKE_OK || { log "ABORT: SMOKE_OK missing"; exit 1; }
  touch "$RES/.smoke_ok"
fi

for seed in 0 1; do
  for arm in standard blurpool aps aug; do
    if ls "$RES"/imagenet100_fastat_"${arm}"_seed"${seed}"_*.json >/dev/null 2>&1; then
      log "skip $arm seed$seed (eval JSON exists)"; continue
    fi
    lock=$RES/.lock_${arm}_seed${seed}
    if ! mkdir "$lock" 2>/dev/null; then log "skip $arm seed$seed (locked)"; continue; fi
    run_py "train $arm seed$seed" train.py --arm "$arm" --seed "$seed" || { rmdir "$lock"; continue; }
    run_py "eval  $arm seed$seed" evaluate.py --arm "$arm" --seed "$seed" || log "WARN eval failed $arm seed$seed"
    rmdir "$lock"
  done
  PYTHONNOUSERSITE=1 "$PYBIN" analyze.py >> "$LOG" 2>&1
  log "analysis after seed $seed written (imagenet100_summary.json)"
done
touch "$RES/chain_done.marker"
log "=== CHAIN COMPLETE ==="
