#!/usr/bin/env python
"""Smoke test: verify M, grads, gauge-invariance of R_q, PE-PGD, judge, and calibrate eps ladder."""
import csv, os, time, torch
from tdiss_core import TDiss
from judge import Judge

HERE = os.path.dirname(os.path.abspath(__file__))
T = TDiss()
rows = list(csv.DictReader(open(os.path.join(HERE, "data", "prompts.csv"))))
harmful = [r for r in rows if r["category"] == "harmful" and r["source"] != "xstest"][:6]

print("=== embedding scale reference ===")
ids = T.build_ids(harmful[0]["behavior"])
e = T.embeds_of(ids)
print("mean token-embed L2 norm:", e[0].norm(dim=-1).mean().item(), " T=", ids.shape[1])

print("\n=== clean diagnostics + gauge-invariance check ===")
for r in harmful[:4]:
    d = T.diagnostics(r["behavior"])
    # gauge test: scale logits by c=2 and add refuse bias b=+3; R2 must be invariant to c
    T.logit_scale = 2.0
    d2 = T.diagnostics(r["behavior"])
    T.logit_scale = 1.0
    print(f"  M={d['M']:+.3f} gl2={d['gl2']:.4f} R2={d['R2']:.4f} Rinf={d['Rinf']:.5f} | "
          f"c=2: M={d2['M']:+.3f} R2={d2['R2']:.4f}  (R2 should match)")

print("\n=== judge load ===")
J = Judge(kind="auto")

print("\n=== clean generations + judge (expect refusals => not success) ===")
for r in harmful[:4]:
    txt = T.generate_text(r["behavior"], max_new_tokens=40)
    print(f"  succ={J(r['behavior'], txt)}  {txt[:60]!r}")

print("\n=== PE-PGD L2 eps ladder calibration (1 prompt) ===")
beh = harmful[0]["behavior"]
for eps in [2, 5, 10, 20, 40, 80]:
    t0 = time.time()
    res = T.pe_pgd(beh, eps=eps, p=2, steps=100, restarts=2, gen_tokens=40, judge=J, return_text=True)
    print(f"  eps={eps:3d}  A={res['best_A']:+.2f}  succ={res['success']}  "
          f"({time.time()-t0:.1f}s)  {res['text'][:50]!r}")
