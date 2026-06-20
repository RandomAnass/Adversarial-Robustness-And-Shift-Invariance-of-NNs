#!/usr/bin/env python3
"""
n=8 statistical-power follow-up. Recomputes the headline correlations on the DENSE grids
(standard dissection: 24 cells x 4 seeds; Linf-AT: 12 cells x 3 seeds) with bootstrap 95% CIs
(resampling cells) and a two-sided permutation test, and checks they reproduce the original
8-cell signs/magnitudes.

Run: paper/env/cenv/bin/python paper/experiments/npower_stats.py
"""
import json, sys, numpy as np
from scipy.stats import pearsonr, spearmanr

STD = "paper/results/cifar_dissection_npower_20260619_084655.json"
AT  = "paper/results/at_cifar_linf_npower_20260619_180843.json"
RNG = np.random.default_rng(0)

def cells(results):
    by = {}
    for r in results:
        by.setdefault((r["arm"], r["w"]), []).append(r)
    out = []
    for k, rs in by.items():
        d = {"arm": k[0], "w": k[1], "n": len(rs)}
        keys = set().union(*[{kk for kk in x if isinstance(x[kk], (int, float))} for x in rs])
        for kk in keys:
            v = [x[kk] for x in rs if x.get(kk) is not None]
            d[kk] = float(np.mean(v)) if v else float("nan")
        out.append(d)
    return out

def stat(x, y, B=10000):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y); x, y = x[m], y[m]; n = len(x)
    pe = pearsonr(x, y)[0]; sp = spearmanr(x, y)[0]
    # bootstrap CI over cells
    bs = []
    for _ in range(B):
        idx = RNG.integers(0, n, n)
        if np.std(x[idx]) < 1e-12 or np.std(y[idx]) < 1e-12: continue
        bs.append(pearsonr(x[idx], y[idx])[0])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    # two-sided permutation test
    perm = np.array([pearsonr(x, RNG.permutation(y))[0] for _ in range(B)])
    p = (np.sum(np.abs(perm) >= abs(pe)) + 1) / (B + 1)
    return dict(n=n, pearson=pe, spearman=sp, ci=(lo, hi), p=p)

def show(name, s):
    print(f"  {name:34s} n={s['n']:2d}  Pearson {s['pearson']:+.3f}  "
          f"95% CI [{s['ci'][0]:+.3f}, {s['ci'][1]:+.3f}]  Spearman {s['spearman']:+.3f}  perm p={s['p']:.4f}")

print("="*96)
print("DENSE-STANDARD dissection (24 cells x 4 seeds): does eta/L predict radius, consistency not?")
c = cells(json.load(open(STD))["results"])
etaL = [d["dec_etaL"] for d in c]; rr = [d["rr_l2"] for d in c]; con = [d["consist"] for d in c]
show("eta/L vs robust radius r2", stat(etaL, rr))
show("consistency vs robust radius r2", stat(con, rr))
print(f"  [orig 8-cell was: eta/L vs r2 Pearson +0.998 ; consistency -0.55]")

print("="*96)
print("DENSE Linf-AT (12 cells x 3 seeds): consistency anti-predicts AA, threat-matched eta/L predicts")
c = cells(json.load(open(AT))["results"])
aa = [d["aa_Linf_8_255"] for d in c]; con = [d["consist"] for d in c]
matched = [d["dec_margin"]/d["dec_L1"] for d in c]      # Linf dual = L1 gradient
missd  = [d["dec_margin"]/d["dec_L2"] for d in c]
show("consistency vs AA(Linf 8/255)", stat(con, aa))
show("matched eta/||grad M||_1 vs AA", stat(matched, aa))
show("mismatched eta/||grad M||_2 vs AA", stat(missd, aa))
# gradient masking recheck
masked = [(d["arm"], d["w"]) for d in c if d.get("aa_Linf_8_255",0) > d.get("pgd_Linf_8_255",1)+1e-6]
print(f"  gradient-masking cells (AA>PGD): {masked if masked else 'none'}")
print(f"  [orig 8-cell was: consistency -0.88 ; matched +0.90 ; mismatched +0.62]")
print("="*96)
