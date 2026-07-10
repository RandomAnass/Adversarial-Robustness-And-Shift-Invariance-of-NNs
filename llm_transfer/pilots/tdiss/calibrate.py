#!/usr/bin/env python
"""Calibrate the L2 eps ladder: find the range where PE-PGD ASR moves 0 -> 1 (radius resolution)."""
import sys, csv, random, torch
from tdiss_core import TDiss
from judge import Judge

def log(*a):
    print(*a, flush=True)

T = TDiss()
J = Judge(kind="auto")
rows = list(csv.DictReader(open("data/prompts.csv")))
h = [r for r in rows if r["category"] == "harmful" and r["source"] != "xstest"]
random.seed(0)
sample = random.sample(h, 5)
ladder = [0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0]
log("=== L2 ladder calibration ===")
for r in sample:
    log("PROMPT:", r["behavior"][:55])
    for eps in ladder:
        res = T.pe_pgd(r["behavior"], eps=eps, p=2, steps=150, restarts=1,
                       gen_tokens=48, judge=J, return_text=True)
        flag = "JB" if res["success"] else "  "
        log(f"   eps={eps:4.2f} loss={res['best_loss']:.2f} {flag} {res['text'][:55]!r}")
log("=== done ===")
