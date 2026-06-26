#!/usr/bin/env python3
"""
Paper-ready report for the full-10k adversarial-training re-run (the C1 fix). For every
at_<dataset>_<norm>_full10k_*.json that exists, recompute, on the now-uncapped (n=10000)
AutoAttack numbers:
  - per-(arm,width) cell table: clean, consistency, rr_l2, eta, L1/L2, eta/L1, eta/L2, AA(primary), AA(secondary)
  - the three across-cell correlations the paper reports against the PRIMARY (threat-matched) AA:
        matched   eta/||grad M||_q   (q = dual of the training norm: Linf->L1, L2->L2)
        mismatched eta/||grad M||_q' (the other norm)
        shift-consistency
    each with a cluster bootstrap 95% CI (resampling (arm,width) cells) and a permutation p-value,
    computed both over the 8 cell-means and over the 16 individual per-seed runs (the small-net protocol).

This supersedes the 512-based AutoAttack columns of tab:cifar-at and tab:at-general; clean / consistency /
eta / L are sample-size-independent and unchanged. Prints a comparison hook (the paper's prior values) so
the shift is visible. CPU-only, reads JSON only.

Usage:  PYTHONNOUSERSITE=1 paper/env/cenv/bin/python at_full10k_report.py
"""
import os, glob, json, numpy as np
from scipy.stats import pearsonr, spearmanr

RESDIR = os.path.join(os.path.dirname(__file__), "..", "results")
RNG = np.random.default_rng(0)
# paper's PRIOR (512-based) primary-AA correlations, for a visible before/after (consist, matched, mismatched)
PRIOR = {("cifar", "linf"): (-0.88, +0.90, +0.62), ("cifar", "l2"): (-0.77, +0.87, +0.91),
         ("mnist", "linf"): (None, None, None),    ("fashion", "linf"): (-0.86, +0.79, +0.64)}

def cluster_ci(cellkeys, groups, xs, ys, B=10000):
    """Pearson over individual runs + cluster bootstrap (resample cells) CI + permutation p."""
    X, Y = np.array(xs, float), np.array(ys, float)
    m = np.isfinite(X) & np.isfinite(Y); X, Y = X[m], Y[m]
    if len(X) < 3: return float("nan"), (float("nan"), float("nan")), float("nan")
    pe = pearsonr(X, Y)[0]; nc = len(cellkeys)
    bs = []
    for _ in range(B):
        pts = [p for k in (cellkeys[i] for i in RNG.integers(0, nc, nc)) for p in groups[k]]
        bx = np.array([p[0] for p in pts]); by = np.array([p[1] for p in pts])
        if np.std(bx) > 1e-9 and np.std(by) > 1e-9: bs.append(pearsonr(bx, by)[0])
    lo, hi = np.percentile(bs, [2.5, 97.5]) if bs else (float("nan"),) * 2
    perm = np.array([pearsonr(X, RNG.permutation(Y))[0] for _ in range(B)])
    p = (np.sum(np.abs(perm) >= abs(pe)) + 1) / (B + 1)
    return pe, (lo, hi), p

def report_condition(f):
    d = json.load(open(f)); a = d["args"]; ds, norm = a["dataset"], a["norm"]
    specs = d["aa_specs"]; prim, sec = specs[0], (specs[1] if len(specs) > 1 else None)
    pname, pnorm = prim[0], prim[1]; aakey = "aa_" + pname
    dualq = "L1" if pnorm == "Linf" else "L2"; otherq = "L2" if pnorm == "Linf" else "L1"
    res = d["results"]                                  # 16 per-seed runs
    print(f"\n{'='*100}\n{ds.upper()} {norm}-AT  full-10k  ({f.split('/')[-1]})   "
          f"aa_n={a['aa_n']} seeds={a['seeds']} widths={a['widths']}  primary AA={pname}\n{'='*100}")
    # per-seed points for matched/mismatched/consistency vs primary AA
    groups = {}
    for r in res:
        match = r["dec_margin"] / r["dec_" + dualq]; mism = r["dec_margin"] / r["dec_" + otherq]
        groups.setdefault((r["arm"], r["w"]), []).append(
            dict(match=match, mism=mism, consist=r["consist"], aa=r[aakey],
                 clean=r["clean"], rr=r["rr_l2"], eta=r["dec_margin"], L1=r["dec_L1"], L2=r["dec_L2"]))
    keys = sorted(groups, key=lambda k: (k[1], k[0]))
    # cell means table
    print(f"{'arm':9s} {'w':>3s} {'clean':>6s} {'consist':>7s} {'rr_L2':>6s} {'eta':>6s} {'L1':>7s} {'L2':>6s} "
          f"{'eta/L1':>6s} {'eta/L2':>6s} {'AA_'+pname:>10s}" + (f" {'AA_'+sec[0]:>10s}" if sec else ""))
    cellmean = {}
    for k in keys:
        g = groups[k]; mu = lambda key: float(np.mean([x[key] for x in g]))
        aap = mu("aa"); etaL1 = mu("eta") / mu("L1"); etaL2 = mu("eta") / mu("L2")
        cellmean[k] = dict(consist=mu("consist"), match=mu("eta")/(mu("L1") if pnorm=="Linf" else mu("L2")),
                           mism=mu("eta")/(mu("L2") if pnorm=="Linf" else mu("L1")), aa=aap)
        sec_s = ""
        if sec:
            sa = float(np.mean([r["aa_" + sec[0]] for r in res if r["arm"]==k[0] and r["w"]==k[1]])); sec_s = f" {sa:10.4f}"
        print(f"{k[0]:9s} {k[1]:3d} {mu('clean'):6.3f} {mu('consist'):7.3f} {mu('rr'):6.3f} {mu('eta'):6.2f} "
              f"{mu('L1'):7.1f} {mu('L2'):6.2f} {etaL1:6.3f} {etaL2:6.3f} {aap:10.4f}{sec_s}")
    # correlations: over 8 cell means AND over 16 runs (cluster bootstrap)
    def runs_xy(sel): return [x[sel] for k in keys for x in groups[k]], [x["aa"] for k in keys for x in groups[k]]
    print(f"\nAcross-cell correlations vs AA_{pname} (matched=eta/{dualq}):")
    prior = PRIOR.get((ds, norm), (None, None, None))
    for lab, sel, pr in [("consistency", "consist", prior[0]), (f"matched eta/{dualq}", "match", prior[1]),
                         (f"mismatched eta/{otherq}", "mism", prior[2])]:
        cm_x = [cellmean[k][sel] for k in keys]; cm_y = [cellmean[k]["aa"] for k in keys]
        pe_cm = pearsonr(cm_x, cm_y)[0]
        xs, ys = runs_xy(sel); gg = {k: [(x[sel], x["aa"]) for x in groups[k]] for k in keys}
        pe_r, ci, p = cluster_ci(keys, gg, xs, ys)
        prtxt = f"  [paper/512: {pr:+.2f}]" if isinstance(pr, (int, float)) else ""
        print(f"  {lab:24s}  cell-mean(n={len(keys)}) {pe_cm:+.3f}   per-run(n={len(xs)}) {pe_r:+.3f} "
              f"CI[{ci[0]:+.2f},{ci[1]:+.2f}] p={p:.3f}{prtxt}")

if __name__ == "__main__":
    files = {}
    for f in sorted(glob.glob(os.path.join(RESDIR, "at_*_full10k_*.json"))):
        d = json.load(open(f)); files[(d["args"]["dataset"], d["args"]["norm"])] = f   # keep latest
    if not files:
        print("no full10k AT files yet"); raise SystemExit
    print(f"found {len(files)} full-10k AT condition(s): {sorted(files)}")
    for k in sorted(files): report_condition(files[k])
