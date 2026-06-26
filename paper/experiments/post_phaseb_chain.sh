#!/usr/bin/env bash
# Detached orchestrator that survives Claude session teardowns (launch with setsid+nohup). It advances
# ONLY the GPU work after Phase B, self-verifying at each step; all analysis / paper edits are left to
# the agent. It HALTS (writes CHAIN_HALT.marker) rather than proceed on incomplete/!sane data.
#   Phase B (already running, not launched here)  -- wait for + verify completeness
#   -> ResNet AA-10k Linf re-eval (smoke 1 cell, gate, then full 28-cell driver)   [eval-only, mandated C1]
#   -> Phase C: npower Linf-AT grid at aa_n=10000 (the last 512-based AT AA)        [standing "all AT on 10k"]
#   -> all_gpu_done.marker
set -u
cd "/home/students/code/Anas/adversarial-robustness-shift-invariance"
export PYTHONNOUSERSITE=1
PY=paper/env/cenv/bin/python
LOG=paper/results/post_phaseb_chain.log
say(){ echo "[chain] $(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
halt(){ say "HALT: $*"; echo "$*" > paper/results/CHAIN_HALT.marker; exit 1; }

say "START (pid $$); waiting for Phase B marker"
while [ ! -f paper/results/final_runs_done.marker ]; do sleep 120; done
say "final_runs_done.marker present; verifying Phase B completeness (4 conditions, 16 jobs, aa_n=10000)"

$PY - <<'PYEOF' >> "$LOG" 2>&1
import json, glob, sys
need=[("cifar","linf"),("cifar","l2"),("mnist","linf"),("fashion","linf")]
ok=True
for ds,norm in need:
    fs=sorted(glob.glob(f"paper/results/at_{ds}_{norm}_full10k_*.json"))
    if not fs: print(f"  MISSING {ds} {norm}"); ok=False; continue
    d=json.load(open(fs[-1])); n=len(d["results"]); an=d["args"]["aa_n"]
    flag="OK" if (n>=16 and an==10000) else "INCOMPLETE"
    print(f"  {flag} {ds} {norm}: jobs={n} aa_n={an}")
    ok = ok and flag=="OK"
sys.exit(0 if ok else 3)
PYEOF
[ $? -eq 0 ] || halt "Phase B incomplete -- not proceeding to re-eval"
say "Phase B verified complete"

# --- ResNet AA-10k re-eval: smoke one cell, gate on sane output, then full driver ---
say "ResNet AA re-eval SMOKE: c10at_standard_s0"
$PY paper/experiments/resnet_scale/resnet_reeval_aa.py --cell c10at_standard_s0 --gpu 0 >> "$LOG" 2>&1
$PY - <<'PYEOF' >> "$LOG" 2>&1
import json, sys
r=json.load(open("paper/results/resnet_scale/c10at_standard_s0.json"))
v=r.get("aa_Linf_8_255"); n=r.get("aa_Linf_n"); v0=r.get("aa_Linf_8_255_n512")
ok = (n==10000) and isinstance(v,(int,float)) and (0.0<=v<=1.0)
print(f"  smoke: aa_Linf 512={v0} -> 10k={v} (n={n}) ok={ok}")
sys.exit(0 if ok else 4)
PYEOF
[ $? -eq 0 ] || halt "ResNet re-eval smoke failed -- not running full driver"
say "smoke OK; running full ResNet AA re-eval driver (27 remaining cells, 2 GPUs)"
$PY paper/experiments/resnet_scale/resnet_reeval_aa.py --driver >> "$LOG" 2>&1
[ -f paper/results/resnet_scale/REEVAL_AA_DONE.marker ] || halt "ResNet re-eval driver did not write REEVAL_AA_DONE.marker"
say "ResNet AA re-eval complete"

# --- Phase C: npower Linf-AT grid at full 10k (the last 512-based AT AutoAttack) ---
say "Phase C: npower Linf-AT 10k (widths 24 48 96, 3 seeds)"
$PY paper/experiments/cifar_at.py --dataset cifar --norm linf --widths 24 48 96 --seeds 3 \
    --aa_n 10000 --tag npower10k >> paper/results/run_npower10k.log 2>&1
NPF=$(ls -t paper/results/at_cifar_linf_npower10k_*.json 2>/dev/null | head -1)
[ -n "$NPF" ] || halt "Phase C npower10k produced no JSON"
say "Phase C npower10k done -> $(basename "$NPF")"

echo done > paper/results/all_gpu_done.marker
say "ALL_GPU_DONE -- ResNet AA re-eval + Phase C complete; analysis/integration left to agent"
