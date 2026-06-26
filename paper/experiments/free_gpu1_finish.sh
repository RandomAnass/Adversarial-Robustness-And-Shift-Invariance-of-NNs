#!/usr/bin/env bash
# Free GPU 1 the moment cifar-l2 finishes (zero waste: we let it complete), then run the REMAINING
# core C1 work on GPU 0 ONLY so GPU 1 stays free for the user. Detached (setsid) -> survives session
# teardown. Supersedes the old final_runs_queue.sh (which would relaunch MNIST on 2 GPUs) and the old
# post_phaseb_chain.sh (which would grab GPU 1 for the re-eval).
#   wait cifar-l2 JSON -> kill old queue+chain+any 2-GPU MNIST -> pin CVD=0 ->
#   MNIST, Fashion full10k (--gpus 1, progressive-save/resume) -> final_runs_done.marker ->
#   ResNet AA-10k re-eval (smoke + --driver --ngpu 1) -> all_gpu_done.marker
# DEFERRED per user (NOT run here): Phase C npower10k, experiment #3 (Lipschitz-AT method).
set -u
cd "/home/students/code/Anas/adversarial-robustness-shift-invariance"
export PYTHONNOUSERSITE=1
PY=paper/env/cenv/bin/python
LOG=paper/results/free_gpu1_finish.log
say(){ echo "[gpu1] $(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
halt(){ say "HALT: $*"; echo "$*" > paper/results/CHAIN_HALT.marker; exit 1; }

say "START (pid $$); waiting for cifar-l2 JSON, then free GPU1 + finish on GPU0"
while ! ls paper/results/at_cifar_l2_full10k_*.json >/dev/null 2>&1; do sleep 30; done
say "cifar-l2 done -> taking over; killing old queue/chain + any running MNIST/Fashion to release GPU1"
pkill -f final_runs_queue.sh 2>/dev/null || true
pkill -f post_phaseb_chain.sh 2>/dev/null || true
pkill -f "cifar_at.py --dataset mnist"   2>/dev/null || true
pkill -f "cifar_at.py --dataset fashion" 2>/dev/null || true
sleep 5
export CUDA_VISIBLE_DEVICES=0      # everything below sees only physical GPU0; GPU1 is free
say "pinned CUDA_VISIBLE_DEVICES=0; GPU1 released"

# --- remaining Phase B conditions on GPU0 (progressive save -> resumes anything already done) ---
say "MNIST full10k on GPU0"
$PY paper/experiments/cifar_at.py --dataset mnist --norm linf --aa_n 10000 --tag full10k --gpus 1 \
    >> paper/results/run_full10k_mnist.log 2>&1
ls paper/results/at_mnist_linf_full10k_*.json >/dev/null 2>&1 || halt "MNIST produced no JSON"
say "Fashion full10k on GPU0"
$PY paper/experiments/cifar_at.py --dataset fashion --norm linf --aa_n 10000 --tag full10k --gpus 1 \
    >> paper/results/run_full10k_fashion.log 2>&1
ls paper/results/at_fashion_linf_full10k_*.json >/dev/null 2>&1 || halt "Fashion produced no JSON"
echo done > paper/results/final_runs_done.marker
say "Phase B complete (all 4 conditions full10k); GPU1 stayed free"

# --- ResNet AA-10k Linf re-eval on GPU0 (smoke gate, then driver ngpu=1) ---
say "ResNet AA re-eval SMOKE (c10at_standard_s0) on GPU0"
$PY paper/experiments/resnet_scale/resnet_reeval_aa.py --cell c10at_standard_s0 --gpu 0 \
    >> paper/results/post_phaseb_chain.log 2>&1
$PY - <<'PYEOF' >> paper/results/post_phaseb_chain.log 2>&1
import json, sys
r=json.load(open("paper/results/resnet_scale/c10at_standard_s0.json"))
v=r.get("aa_Linf_8_255"); n=r.get("aa_Linf_n")
sys.exit(0 if (n==10000 and isinstance(v,(int,float)) and 0.0<=v<=1.0) else 4)
PYEOF
[ $? -eq 0 ] || halt "ResNet re-eval smoke failed"
say "smoke OK; ResNet AA re-eval driver on GPU0 (ngpu=1, 27 remaining cells)"
$PY paper/experiments/resnet_scale/resnet_reeval_aa.py --driver --ngpu 1 \
    >> paper/results/post_phaseb_chain.log 2>&1
[ -f paper/results/resnet_scale/REEVAL_AA_DONE.marker ] || halt "ResNet re-eval driver wrote no marker"
say "ResNet AA re-eval complete"

echo done > paper/results/all_gpu_done.marker
say "ALL_GPU_DONE on GPU0; GPU1 free throughout. DEFERRED (await user 'go'): Phase C npower10k + experiment #3."
