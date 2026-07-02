#!/usr/bin/env python3
"""
S2 analysis: per-arm table + directional correlations (n=4 arms -> report as directional evidence,
not significance). Laws under test at ImageNet-100 scale:
  (1) threat-matched eta/L1 (margin / ||grad M||_1) predicts AutoAttack robust accuracy;
  (2) shift consistency does not (anti-predicts under AT).
Uses the newest eval JSON per (arm, seed); correlations across arms per seed and on seed-means.
"""
import glob, json, os, math
import numpy as np

RESULTS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "..", "..", "results", "imagenet_scale"))
ARMS = ["standard", "blurpool", "aps", "aug"]

def pearson(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a - a.mean(), b - b.mean()
    d = math.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else float("nan")

def spearman(a, b):
    r = lambda v: np.argsort(np.argsort(v)).astype(float)
    return pearson(r(np.asarray(a)), r(np.asarray(b)))

def latest(arm, seed):
    fs = sorted(glob.glob(os.path.join(RESULTS, f"imagenet100_fastat_{arm}_seed{seed}_*.json")))
    return json.load(open(fs[-1])) if fs else None

def main():
    rows, seeds_found = {}, set()
    for seed in range(4):
        got = {a: latest(a, seed) for a in ARMS}
        if all(v is not None for v in got.values()):
            rows[seed] = got; seeds_found.add(seed)
    if not rows:
        print("no complete seed found"); return
    summary = {"exp": "imagenet100_fastat_analysis", "seeds": sorted(seeds_found), "per_seed": {}}
    hdr = f"{'arm':9s} {'clean':>7s} {'consist':>8s} {'etaL1':>9s} {'etaL2':>8s} {'pgd40':>7s} {'aa':>7s} {'mask':>5s}"
    for seed, got in rows.items():
        print(f"\n=== seed {seed} ===\n{hdr}")
        tab = []
        for a in ARMS:
            r = got[a]
            tab.append(dict(arm=a, clean=r["clean"], consist=r["consist"], etaL1=r["dec_etaL1"],
                            etaL2=r["dec_etaL2"], pgd40=r["pgd40"], aa=r["aa"],
                            masking_ok=r["masking_ok"]))
            print(f"{a:9s} {r['clean']:7.4f} {r['consist']:8.4f} {r['dec_etaL1']:9.6f} "
                  f"{r['dec_etaL2']:8.4f} {r['pgd40']:7.4f} {r['aa']:7.4f} {str(r['masking_ok']):>5s}")
        aa = [t["aa"] for t in tab]
        cors = {f"{k}_vs_aa": dict(pearson=pearson([t[k] for t in tab], aa),
                                   spearman=spearman([t[k] for t in tab], aa))
                for k in ("consist", "etaL1", "etaL2", "clean")}
        for k, v in cors.items():
            print(f"  {k:15s}: pearson={v['pearson']:+.3f}  spearman={v['spearman']:+.3f}")
        summary["per_seed"][seed] = dict(table=tab, correlations=cors)
    with open(os.path.join(RESULTS, "imagenet100_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(f"\nsaved {os.path.join(RESULTS, 'imagenet100_summary.json')}")
    print("(n=4 arms per seed: correlations are DIRECTIONAL, not significance-tested)")

if __name__ == "__main__":
    main()
