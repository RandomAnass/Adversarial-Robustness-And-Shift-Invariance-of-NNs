#!/usr/bin/env bash
# Detached orchestrator (setsid) for the FAST 2-GPU x K-worker finish of the whole campaign. Each stage
# uses the reproducibility-proven cifar_at_parallel.py / exp3 / parallel re-eval. Every stage is run,
# then RE-RUN once (resume any worker-died job), then completeness-checked by counting saved per-job
# partials; HALTS (CHAIN_HALT.marker) rather than proceed on a short grid. Leaves analysis/paper to agent.
#   MNIST + Fashion full10k -> final_runs_done -> ResNet AA-10k re-eval -> Phase C npower10k
#   -> Experiment #3 (Lipschitz-AT) -> all_gpu_done.marker
set -u
cd "/home/students/code/Anas/adversarial-robustness-shift-invariance"
export PYTHONNOUSERSITE=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True      # reduce fragmentation across concurrent workers
PY=paper/env/cenv/bin/python
PEXP=paper/experiments
RES=paper/results
LOG=$RES/fast_finish.log
K=3
say(){ echo "[fast] $(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
halt(){ say "HALT: $*"; echo "$*" > $RES/CHAIN_HALT.marker; exit 1; }
# count saved partials in a dir; $1=dir $2=expected $3=label ; halts if short after the (already-run) stage
need(){ n=$(ls "$1" 2>/dev/null | grep -c '\.json$'); say "$3: $n/$2 partials"; [ "$n" -ge "$2" ] || return 1; return 0; }

say "START (pid $$) 2 GPU x $K workers"

# ---- MNIST full10k (parallel) : 16 jobs ----
PD=$RES/at_partial/mnist_linf_full10k
say "MNIST full10k (run 1)"
$PY $PEXP/cifar_at_parallel.py --dataset mnist --norm linf --aa_n 10000 --tag full10k --gpus 2 --workers_per_gpu $K >> $RES/run_full10k_mnist.log 2>&1
if ! need "$PD" 16 "MNIST"; then say "MNIST resume (run 2)"; $PY $PEXP/cifar_at_parallel.py --dataset mnist --norm linf --aa_n 10000 --tag full10k --gpus 2 --workers_per_gpu $K >> $RES/run_full10k_mnist.log 2>&1; fi
need "$PD" 16 "MNIST" || halt "MNIST incomplete"
say "MNIST done"

# ---- Fashion full10k (parallel) : 16 jobs ----
PD=$RES/at_partial/fashion_linf_full10k
say "Fashion full10k (run 1)"
$PY $PEXP/cifar_at_parallel.py --dataset fashion --norm linf --aa_n 10000 --tag full10k --gpus 2 --workers_per_gpu $K >> $RES/run_full10k_fashion.log 2>&1
if ! need "$PD" 16 "Fashion"; then say "Fashion resume (run 2)"; $PY $PEXP/cifar_at_parallel.py --dataset fashion --norm linf --aa_n 10000 --tag full10k --gpus 2 --workers_per_gpu $K >> $RES/run_full10k_fashion.log 2>&1; fi
need "$PD" 16 "Fashion" || halt "Fashion incomplete"
say "Fashion done"
echo done > $RES/final_runs_done.marker
say "Phase B complete (all 4 conditions full10k)"

# ---- ResNet AA-10k Linf re-eval (parallel, smoke gate) : 28 cells ----
say "ResNet re-eval SMOKE (c10at_standard_s0)"
$PY $PEXP/resnet_scale/resnet_reeval_aa.py --cell c10at_standard_s0 --gpu 0 >> $RES/reeval_driver.log 2>&1
$PY -c "import json,sys; r=json.load(open('$RES/resnet_scale/c10at_standard_s0.json')); sys.exit(0 if (r.get('aa_Linf_n')==10000 and 0<=r.get('aa_Linf_8_255',-1)<=1) else 4)" || halt "ResNet re-eval smoke fail"
say "ResNet re-eval driver (2 GPU x 2)"
$PY $PEXP/resnet_scale/resnet_reeval_aa.py --driver --ngpu 2 --workers_per_gpu 2 >> $RES/reeval_driver.log 2>&1
[ -f $RES/resnet_scale/REEVAL_AA_DONE.marker ] || halt "ResNet re-eval no marker"
say "ResNet re-eval done"

# ---- Phase C: npower10k (parallel) : 4 arms x 3 widths x 3 seeds = 36 ----
PD=$RES/at_partial/cifar_linf_npower10k
say "Phase C npower10k (run 1)"
$PY $PEXP/cifar_at_parallel.py --dataset cifar --norm linf --widths 24 48 96 --seeds 3 --aa_n 10000 --tag npower10k --gpus 2 --workers_per_gpu $K >> $RES/run_npower10k.log 2>&1
if ! need "$PD" 36 "PhaseC"; then say "PhaseC resume (run 2)"; $PY $PEXP/cifar_at_parallel.py --dataset cifar --norm linf --widths 24 48 96 --seeds 3 --aa_n 10000 --tag npower10k --gpus 2 --workers_per_gpu $K >> $RES/run_npower10k.log 2>&1; fi
need "$PD" 36 "PhaseC" || halt "Phase C incomplete"
say "Phase C done"

# ---- Experiment #3: Lipschitz-AT (parallel) : 2 arms x 3 lams x 2 widths x 2 seeds = 24 ----
PD=$RES/at_partial/exp3_lipschitz
say "Experiment #3 (run 1)"
$PY $PEXP/exp3_lipschitz_at.py --gpus 2 --workers_per_gpu $K >> $RES/exp3.log 2>&1
if ! need "$PD" 24 "Exp3"; then say "Exp3 resume (run 2)"; $PY $PEXP/exp3_lipschitz_at.py --gpus 2 --workers_per_gpu $K >> $RES/exp3.log 2>&1; fi
need "$PD" 24 "Exp3" || halt "Experiment #3 incomplete"
say "Experiment #3 done"

echo done > $RES/all_gpu_done.marker
say "ALL_GPU_DONE -- MNIST+Fashion+reeval+PhaseC+Exp3 complete on 2 GPUs. Analysis/paper integration -> agent."
