#!/usr/bin/env bash
# Tail with AA_BS=64: the previous tail OOM'd on circular CIFAR AutoAttack (~22 GiB/job at batch 256,
# so two on one card exceed 48 GiB). AutoAttack robust accuracy is batch-size-independent (per-sample),
# so a smaller AA batch cuts memory ~4x with identical numbers. Resumes Phase C from saved partials,
# then runs Experiment #3, then all_gpu_done.marker.
set -u
cd "/home/students/code/Anas/adversarial-robustness-shift-invariance"
export PYTHONNOUSERSITE=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export AA_BS=64
PY=paper/env/cenv/bin/python
PEXP=paper/experiments
RES=paper/results
LOG=$RES/tail3_finish.log
say(){ echo "[tail3] $(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
halt(){ say "HALT: $*"; echo "$*" > $RES/CHAIN_HALT.marker; exit 1; }
have(){ n=$(ls "$1" 2>/dev/null | grep -c '\.json$'); say "$3: $n/$2"; [ "$n" -ge "$2" ]; }

say "START (pid $$); AA_BS=64 (result-neutral memory fix). Phase C (resume) -> Exp #3"
PD=$RES/at_partial/cifar_linf_npower10k
$PY $PEXP/cifar_at_parallel.py --dataset cifar --norm linf --widths 24 48 --seeds 3 --aa_n 10000 --tag npower10k --gpus 2 --workers_per_gpu 3 >> $RES/run_npower10k.log 2>&1
have "$PD" 24 "PhaseC" || { say "PhaseC resume"; $PY $PEXP/cifar_at_parallel.py --dataset cifar --norm linf --widths 24 48 --seeds 3 --aa_n 10000 --tag npower10k --gpus 2 --workers_per_gpu 3 >> $RES/run_npower10k.log 2>&1; }
have "$PD" 24 "PhaseC" || halt "Phase C incomplete"
say "Phase C done (widths 24 48, 24 cells)"

PD=$RES/at_partial/exp3_lipschitz
say "Experiment #3 (run 1)"
$PY $PEXP/exp3_lipschitz_at.py --gpus 2 --workers_per_gpu 3 >> $RES/exp3.log 2>&1
have "$PD" 24 "Exp3" || { say "Exp3 resume"; $PY $PEXP/exp3_lipschitz_at.py --gpus 2 --workers_per_gpu 3 >> $RES/exp3.log 2>&1; }
have "$PD" 24 "Exp3" || halt "Experiment #3 incomplete"
say "Experiment #3 done"

echo done > $RES/all_gpu_done.marker
say "ALL_GPU_DONE (Phase C 24/48 + Exp3)."
