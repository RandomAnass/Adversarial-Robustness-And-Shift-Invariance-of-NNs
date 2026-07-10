#!/usr/bin/env python
"""Fine low-eps calibration: find the eps regime where PE-PGD ASR moves 0->1 across prompts,
so the per-prompt min-successful-eps (radius) has resolution. Report per-eps ASR over 12 prompts."""
import csv, random, torch
from tdiss_core import TDiss
from judge import Judge

def log(*a): print(*a, flush=True)

T = TDiss(); J = Judge(kind="auto")
rows = list(csv.DictReader(open("data/prompts.csv")))
h = [r for r in rows if r["category"] == "harmful" and r["source"] != "xstest"]
random.seed(1); sample = random.sample(h, 12)
ladder = [0.003, 0.006, 0.012, 0.025, 0.05, 0.1]
log("=== fine L2 ladder ASR calibration (12 prompts, 150 steps, 1 restart) ===")
asr = {e: 0 for e in ladder}
for j, r in enumerate(sample):
    line = f"[{j:2d}] "
    for eps in ladder:
        res = T.pe_pgd(r["behavior"], eps=eps, p=2, steps=150, restarts=1,
                       gen_tokens=40, judge=J)
        s = 1 if res["success"] else 0
        asr[eps] += s
        line += f" e{eps}:{'J' if s else '.'}(l{res['best_loss']:.1f})"
    log(line)
log("=== per-eps ASR ===")
for e in ladder:
    log(f"  eps={e:.3f}  ASR={asr[e]}/12 = {asr[e]/12:.2f}")
log("=== done ===")
