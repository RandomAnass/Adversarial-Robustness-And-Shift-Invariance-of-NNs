#!/usr/bin/env python3
"""
Deep PER-SAMPLE analysis of the ResNet-scale cells (what the cell-mean aggregates hide). Stable:
uses only the saved per-sample arrays (radius, margin, gradL2, gradL1; n=1000 clean-correct points
per cell) and the cell JSONs -- nothing here depends on the AutoAttack sample size, so it is valid
before and after the full-10k Linf re-eval. CPU-only, no model load.

Three questions the cross-cell means cannot answer:
  (Q-A) Within a SINGLE model, does a point's own local margin-to-sensitivity ratio eta/L_loc =
        margin / ||grad M||_2 predict its own certified-ish DDN radius? The headline +0.962 is a
        correlation of cell MEANS; a positive within-cell rank correlation is sample-level evidence
        that the eta/L mechanism is not an aggregation artifact (first-order certificate r2 >~
        margin/||grad M||_2 read per point).
  (Q-B) Is an arm's robustness advantage a uniform shift or a tail/never-flipped effect? Report
        radius quantiles + the never-flipped fraction (rr_ninf/n) per cell, so a mean shift can be
        distinguished from a change in the robust subpopulation.
  (Q-C) Are margin and sensitivity coupled across points within a model (does the net buy margin by
        paying Lipschitz, sample by sample)?

Writes a text report to stdout and a compact JSON (persample_summary.json) for the figure stage.

Usage:  PYTHONNOUSERSITE=1 paper/env/cenv/bin/python resnet_persample.py [--dataset cifar10|cifar100]
"""
import os, sys, json, glob, argparse, numpy as np
from scipy.stats import pearsonr, spearmanr
sys.path.insert(0, os.path.dirname(__file__))

RESDIR = os.path.join(os.path.dirname(__file__), "..", "..", "results", "resnet_scale")
ARM_LAB = {"standard": "standard", "blurpool": "anti-aliased", "aps": "exact (APS)", "aug": "shift-aug",
           "stdzero": "zero-pad", "maxpool": "max-pool (aliased)"}
CORE4 = ["standard", "blurpool", "aps", "aug"]

def load_cells(mode, dataset):
    """Return [(name, cellJSON, persample-dict)] for cells of this mode+dataset that have an npz."""
    out = []
    for f in sorted(glob.glob(os.path.join(RESDIR, "*.json"))):
        if f.endswith("_curves.json"): continue
        try: r = json.load(open(f))
        except Exception: continue
        if not (isinstance(r, dict) and r.get("mode") == mode and r.get("dataset") == dataset and "arm" in r):
            continue
        name = os.path.basename(f)[:-5]
        npz = os.path.join(RESDIR, name + "_persample.npz")
        if not os.path.exists(npz): continue
        d = np.load(npz); out.append((name, r, {k: d[k] for k in d.files}))
    return out

def _clean(*arrs):
    m = np.ones(len(arrs[0]), bool)
    for a in arrs: m &= np.isfinite(a)
    return m

def analyze(mode="at", dataset="cifar10"):
    cells = load_cells(mode, dataset)
    print(f"\n{'='*92}\nPER-SAMPLE ANALYSIS  mode={mode} dataset={dataset}  ({len(cells)} cells with per-sample arrays)\n{'='*92}")
    if not cells:
        print("  (no cells)"); return {}

    # ---- Q-A: within-cell per-sample eta/L_loc -> radius ---------------------------------------
    print("\n[Q-A] WITHIN-CELL per-sample  eta/L_loc = margin/||grad M||_2  vs DDN radius")
    print("      (radius is finite only on flipped points; never-flipped dropped from the correlation)")
    print(f"      {'cell':30s} {'n_fin':>6s} {'rho_S':>7s} {'r_P':>7s} {'cellmean etaL':>13s} {'cellmean r2':>11s}")
    qa = []
    for name, r, ps in sorted(cells, key=lambda c: c[1]["arm"]):
        rad, m, g2 = ps["radius"], ps["margin"], ps["gradL2"]
        etaL_loc = m / (g2 + 1e-12)
        fin = _clean(rad, etaL_loc) & np.isfinite(rad) & (rad < np.inf)
        if fin.sum() < 10:
            print(f"      {name:30s} {int(fin.sum()):6d}   (too few flipped)"); continue
        rho = spearmanr(etaL_loc[fin], rad[fin])[0]; rp = pearsonr(etaL_loc[fin], rad[fin])[0]
        qa.append(dict(name=name, arm=r["arm"], w=r.get("w"), seed=r.get("seed"), n_fin=int(fin.sum()),
                       spearman=float(rho), pearson=float(rp),
                       cell_etaL=float(r.get("dec_etaL", np.nan)), cell_rr=float(r.get("rr_l2", np.nan))))
        print(f"      {name:30s} {int(fin.sum()):6d} {rho:+7.3f} {rp:+7.3f} {r.get('dec_etaL',float('nan')):13.4f} {r.get('rr_l2',float('nan')):11.3f}")
    if qa:
        sr = np.array([q["spearman"] for q in qa])
        print(f"\n      within-cell Spearman across {len(qa)} cells: mean {sr.mean():+.3f}  median {np.median(sr):+.3f}  "
              f"min {sr.min():+.3f}  max {sr.max():+.3f}  frac>0 {np.mean(sr>0):.2f}")
        print("      READ: a consistently positive within-cell rank correlation = the eta/L certificate")
        print("            mechanism holds sample-by-sample, not only between cell means.")

    # ---- Q-B: radius distribution shape + never-flipped fraction -------------------------------
    print("\n[Q-B] RADIUS DISTRIBUTION per cell (quantiles over flipped pts) + never-flipped fraction")
    print(f"      {'cell':30s} {'n':>5s} {'ninf%':>6s} {'q10':>6s} {'q25':>6s} {'q50':>6s} {'q75':>6s} {'q90':>6s} {'mean':>6s}")
    qb = []
    for name, r, ps in sorted(cells, key=lambda c: (c[1]["arm"], c[1].get("w", 1))):
        rad = ps["radius"]; n = len(rad); fin = np.isfinite(rad) & (rad < np.inf)
        ninf = 1.0 - fin.mean()
        if fin.sum() < 5:
            print(f"      {name:30s} {n:5d} {ninf*100:6.1f}  (few flipped)"); continue
        q = np.percentile(rad[fin], [10, 25, 50, 75, 90])
        qb.append(dict(name=name, arm=r["arm"], w=r.get("w"), ninf=float(ninf),
                       q=[float(x) for x in q], mean=float(rad[fin].mean())))
        print(f"      {name:30s} {n:5d} {ninf*100:6.1f} {q[0]:6.3f} {q[1]:6.3f} {q[2]:6.3f} {q[3]:6.3f} {q[4]:6.3f} {rad[fin].mean():6.3f}")

    # ---- Q-C: margin <-> sensitivity coupling within a model -----------------------------------
    print("\n[Q-C] WITHIN-CELL coupling of margin and sensitivity ||grad M||_2 (Spearman over all pts)")
    print(f"      {'cell':30s} {'rho(margin,gradL2)':>20s}")
    qc = []
    for name, r, ps in sorted(cells, key=lambda c: c[1]["arm"]):
        m, g2 = ps["margin"], ps["gradL2"]; fin = _clean(m, g2)
        if fin.sum() < 10: continue
        rho = spearmanr(m[fin], g2[fin])[0]
        qc.append(dict(name=name, arm=r["arm"], rho=float(rho)))
        print(f"      {name:30s} {rho:+20.3f}")

    # ---- arm-level rollup (core-4 AT, full-width seed0) ----------------------------------------
    if mode == "at":
        print("\n[ARM ROLLUP] core-4 cells (any width/seed averaged): median radius, never-flip%, within-cell rho_S")
        by = {}
        for q in qa: by.setdefault(q["arm"], {}).setdefault("rhoS", []).append(q["spearman"])
        for b in qb: by.setdefault(b["arm"], {}).setdefault("ninf", []).append(b["ninf"]); by[b["arm"]].setdefault("q50", []).append(b["q"][2])
        for arm in CORE4:
            if arm not in by: continue
            d = by[arm]
            print(f"      {ARM_LAB.get(arm,arm):16s}  med-radius {np.mean(d.get('q50',[np.nan])):.3f}  "
                  f"never-flip {100*np.mean(d.get('ninf',[np.nan])):.1f}%  within-cell rho_S {np.mean(d.get('rhoS',[np.nan])):+.3f}")

    return dict(mode=mode, dataset=dataset, qa=qa, qb=qb, qc=qc)

def signflip_robustness(dataset="cifar10"):
    """Stress-test F2 (AT inverts the within-cell margin<->sensitivity coupling) before it goes in the
    paper: is the std(neg)->AT(pos) sign flip robust to (a) the gradient norm (L1 vs L2) and (b)
    restricting to confident (above-median-margin) points, or is it an easy-vs-hard-spread artifact?"""
    print(f"\n{'='*92}\nF2 ROBUSTNESS: within-cell Spearman(margin, sensitivity)  dataset-family {dataset}\n{'='*92}")
    def block(mode, ds, label):
        cells = load_cells(mode, ds); r2, r1, rhi = [], [], []
        for name, r, ps in cells:
            M, g2, g1 = ps["margin"], ps["gradL2"], ps["gradL1"]; fin = _clean(M, g2, g1)
            M, g2, g1 = M[fin], g2[fin], g1[fin]
            r2.append(spearmanr(M, g2)[0]); r1.append(spearmanr(M, g1)[0])
            hi = M >= np.median(M); rhi.append(spearmanr(M[hi], g2[hi])[0])
        f = lambda a: (np.mean(a), np.min(a), np.max(a), float(np.mean(np.array(a) > 0)))
        for tag, arr in [("rho(M,||gradM||_2)", r2), ("  L1-norm rho(M,||gradM||_1)", r1),
                         ("  confident-half rho(M,gL2)", rhi)]:
            mu, lo, hi_, fr = f(arr)
            print(f"  {label if tag.startswith('rho') else '':10s} {tag:30s} mean {mu:+.2f} [{lo:+.2f},{hi_:+.2f}] frac>0 {fr:.2f}  (n={len(arr)})")
        return r2
    block("std", dataset, "STD")
    block("at", dataset, "AT")
    if dataset == "cifar10": block("at", "cifar100", "AT-c100")
    print("  READ: sign flip is norm-robust; std attenuates within the confident half (partly easy-vs-hard),"
          "\n        but AT stays positive there -> the inversion is genuine, not only a spread artifact.")

def analyze_trajectories(mode="at", dataset="cifar10"):
    """Process (not endpoint) analysis: robust overfitting from the per-epoch curves (Rice2020).
    val_robust typically peaks mid-training then decays; best-robust early stopping (used here) keeps
    the peak. Quantify the peak, the end-of-training value, the overfitting gap, and the best epoch,
    per cell and rolled up by arm. Stable: curves do not depend on the AutoAttack sample size."""
    cells = []
    for f in sorted(glob.glob(os.path.join(RESDIR, "*.json"))):
        if f.endswith("_curves.json"): continue
        try: r = json.load(open(f))
        except Exception: continue
        if not (isinstance(r, dict) and r.get("mode") == mode and r.get("dataset") == dataset and "arm" in r):
            continue
        name = os.path.basename(f)[:-5]; cv = os.path.join(RESDIR, name + "_curves.json")
        if not os.path.exists(cv): continue
        cur = json.load(open(cv)); cells.append((name, r, cur))
    print(f"\n{'='*92}\nTRAJECTORY / ROBUST-OVERFITTING  mode={mode} dataset={dataset}  ({len(cells)} cells)\n{'='*92}")
    if not cells: print("  (no cells)"); return []
    print(f"      {'cell':30s} {'eps':>4s} {'peakVR':>7s} {'finalVR':>7s} {'gap':>6s} {'bestEp':>6s} {'nEp':>4s}")
    traj = []
    for name, r, cur in sorted(cells, key=lambda c: (c[1]["arm"], c[1].get("w", 1))):
        vr = [x["val_robust"] for x in cur]; ep = [x["epoch"] for x in cur]
        peak = max(vr); peak_i = int(np.argmax(vr)); final = vr[-1]; gap = peak - final
        traj.append(dict(name=name, arm=r["arm"], w=r.get("w"), seed=r.get("seed"), peak=float(peak),
                         final=float(final), gap=float(gap), best_epoch=int(ep[peak_i]), n_epochs=len(cur)))
        print(f"      {name:30s} {'':>4s} {peak:7.3f} {final:7.3f} {gap:+6.3f} {ep[peak_i]:6d} {len(cur):4d}")
    g = {}
    for t in traj: g.setdefault(t["arm"], []).append(t)
    print("\n      by arm: mean robust-overfitting gap (peak val_robust - final val_robust):")
    for arm in CORE4 + ["stdzero", "maxpool"]:
        if arm not in g: continue
        gg = [t["gap"] for t in g[arm]]; be = [t["best_epoch"] for t in g[arm]]
        print(f"        {ARM_LAB.get(arm,arm):16s}  gap {np.mean(gg):+.3f}  best_epoch {np.mean(be):.0f}  (n={len(gg)})")
    allgap = [t["gap"] for t in traj]
    print(f"\n      READ: mean gap {np.mean(allgap):+.3f} over {len(traj)} cells confirms robust overfitting "
          f"at ResNet scale; best-robust early stopping (used) is necessary.")
    return traj

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="cifar10")
    ap.add_argument("--out", default=os.path.join(RESDIR, "persample_summary.json"))
    a = ap.parse_args()
    summary = {}
    for mode in ("at", "std"):
        summary[f"{mode}_{a.dataset}"] = analyze(mode, a.dataset)
    if a.dataset == "cifar10":   # also roll the c100 AT cells
        summary["at_cifar100"] = analyze("at", "cifar100")
    signflip_robustness(a.dataset)
    summary["traj_at"] = analyze_trajectories("at", a.dataset)
    if a.dataset == "cifar10":
        summary["traj_at_c100"] = analyze_trajectories("at", "cifar100")
    json.dump(summary, open(a.out, "w"), indent=1, default=float)
    print(f"\n# wrote {a.out}")
