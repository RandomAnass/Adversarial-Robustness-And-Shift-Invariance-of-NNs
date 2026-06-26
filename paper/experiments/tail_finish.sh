#!/usr/bin/env bash
# Replacement tail orchestrator (detached). Supersedes fast_finish.sh's reeval->PhaseC->exp3 tail so
# Phase C runs the USER-CHOSEN trimmed grid (widths 24 48 only; width-96 dropped = prohibitive full-10k
# AA). fast_finish.sh's bash is killed first (its orphaned reeval driver keeps running + writes its
# marker, so reeval is uninterrupted). This script waits for that marker, fills any reeval gaps, then:
#   Phase C npower10k widths 24 48 (K=3, fast) -> Experiment #3 -> all_gpu_done.marker
set -u
cd "/home/students/code/Anas/adversarial-robustness-shift-invariance"
export PYTHONNOUSERSITE=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY=paper/env/cenv/bin/python
PEXP=paper/experiments
RES=paper/results
LOG=$RES/tail_finish.log
say(){ echo "[tail] $(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
halt(){ say "HALT: $*"; echo "$*" > $RES/CHAIN_HALT.marker; exit 1; }
have(){ n=$(ls "$1" 2>/dev/null | grep -c '\.json$'); say "$3: $n/$2"; [ "$n" -ge "$2" ]; }

say "START (pid $$); waiting for ResNet reeval marker (orphaned driver still running)"
while [ ! -f $RES/resnet_scale/REEVAL_AA_DONE.marker ]; do sleep 30; done
say "reeval marker present; filling any dropped cells (idempotent driver, K=4)"
$PY $PEXP/resnet_scale/resnet_reeval_aa.py --driver --ngpu 2 --workers_per_gpu 4 >> $RES/reeval_driver.log 2>&1
NRE=$($PY -c "import glob,json; print(sum(json.load(open(f)).get('aa_Linf_n')==10000 for f in glob.glob('$RES/resnet_scale/*.json') if json.load(open(f)).get('mode')=='at'))" 2>/dev/null)
say "ResNet cells at full-10k: ${NRE:-?}/28"

# ---- Phase C: npower10k TRIMMED to widths 24 48 (user choice), K=3 ----
PD=$RES/at_partial/cifar_linf_npower10k
say "Phase C npower10k widths 24 48 (run 1)"
$PY $PEXP/cifar_at_parallel.py --dataset cifar --norm linf --widths 24 48 --seeds 3 --aa_n 10000 --tag npower10k --gpus 2 --workers_per_gpu 3 >> $RES/run_npower10k.log 2>&1
have "$PD" 24 "PhaseC" || { say "PhaseC resume"; $PY $PEXP/cifar_at_parallel.py --dataset cifar --norm linf --widths 24 48 --seeds 3 --aa_n 10000 --tag npower10k --gpus 2 --workers_per_gpu 3 >> $RES/run_npower10k.log 2>&1; }
have "$PD" 24 "PhaseC" || halt "Phase C incomplete"
say "Phase C done (widths 24 48, 24 cells)"

# ---- Experiment #3: Lipschitz-AT (2 arms x 3 lams x 2 widths x 2 seeds = 24) ----
PD=$RES/at_partial/exp3_lipschitz
say "Experiment #3 (run 1)"
$PY $PEXP/exp3_lipschitz_at.py --gpus 2 --workers_per_gpu 3 >> $RES/exp3.log 2>&1
have "$PD" 24 "Exp3" || { say "Exp3 resume"; $PY $PEXP/exp3_lipschitz_at.py --gpus 2 --workers_per_gpu 3 >> $RES/exp3.log 2>&1; }
have "$PD" 24 "Exp3" || halt "Experiment #3 incomplete"
say "Experiment #3 done"

echo done > $RES/all_gpu_done.marker
say "ALL_GPU_DONE (Phase C 24/48 trimmed + Exp3 complete). Analysis/paper integration -> agent."
