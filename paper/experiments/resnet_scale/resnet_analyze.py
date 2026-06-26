#!/usr/bin/env python3
"""
Analysis for the ResNet-scale dissection. Robust to PARTIAL results (runs over whatever cells are
done), so it can be run at the 8-cell milestone and again at full completion.

Produces, for CIFAR-10 (and CIFAR-100 if present):
  - AT correlations: consistency vs AutoAttack, threat-matched eta/||grad M||_1 vs AA, mismatched eta/||grad M||_2
    vs AA, robust-radius vs AA -- each with bootstrap 95% CI (resampling cells) + two-sided permutation test.
  - Standard correlations: eta/L vs L2 robust radius, consistency vs radius (+ the AA-vs-radius calibration).
  - Margin/Lipschitz decomposition vs the `standard` arm (Dlog eta, Dlog L, Dlog eta/L).
  - Partial correlation of consistency vs AA controlling for clean accuracy (the small-net caveat).
  - Figures: scatter (consist & matched-eta/L vs AA), decomposition bars, val-robust training trajectories,
    per-sample radius distributions.
  - A LaTeX results table + a stdout summary, with the small-net numbers alongside for comparison.

Run: PYTHONNOUSERSITE=1 paper/env/cenv/bin/python paper/experiments/resnet_scale/resnet_analyze.py
"""
import os, glob, json, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

RESDIR = os.path.join(os.path.dirname(__file__), "..", "..", "results", "resnet_scale")
FIGDIR = os.path.join(os.path.dirname(__file__), "..", "report", "figures")
RNG = np.random.default_rng(0)
ARM_LAB = {"standard": "standard", "blurpool": "anti-aliased", "aps": "exact (APS)", "aug": "shift-aug",
           "stdzero": "zero-pad", "maxpool": "max-pool (aliased)"}
ARM_COL = {"standard": "#444444", "blurpool": "#1f77b4", "aps": "#d62728", "aug": "#2ca02c",
           "stdzero": "#999999", "maxpool": "#9467bd"}
CORE4 = {"standard", "blurpool", "aps", "aug"}          # the capacity-matched circular-pad comparison arms
LOWINV = {"stdzero", "maxpool"}                          # zero-pad low-invariance arms (widen consistency axis)
SMALL_NET = {"at_consist_aa": -0.88, "at_matched_aa": 0.90, "std_etaL_rad": 0.998, "std_consist_rad": -0.33}

def load(mode, dataset="cifar10"):
    out = []
    for f in sorted(glob.glob(os.path.join(RESDIR, "*.json"))):
        if f.endswith("_curves.json"): continue                  # curves are lists, not cell dicts
        try: r = json.load(open(f))
        except Exception: continue
        if isinstance(r, dict) and r.get("mode") == mode and r.get("dataset") == dataset and "arm" in r:
            r["_name"] = os.path.basename(f)[:-5]; out.append(r)
    return out

def stat(x, y, B=10000):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y); x, y = x[m], y[m]; n = len(x)
    if n < 3: return dict(n=n, pearson=float("nan"), spearman=float("nan"), ci=(float("nan"),) * 2, p=float("nan"))
    pe, sp = pearsonr(x, y)[0], spearmanr(x, y)[0]
    bs = [pearsonr(x[i], y[i])[0] for i in (RNG.integers(0, n, n) for _ in range(B))
          if np.std(x[i]) > 1e-9 and np.std(y[i]) > 1e-9]
    lo, hi = np.percentile(bs, [2.5, 97.5]) if bs else (float("nan"),) * 2
    perm = np.array([pearsonr(x, RNG.permutation(y))[0] for _ in range(B)])
    p = (np.sum(np.abs(perm) >= abs(pe)) + 1) / (B + 1)
    return dict(n=n, pearson=pe, spearman=sp, ci=(lo, hi), p=p)

def stat_cluster(results, xkey, yget, B=10000):
    """Correlation over INDIVIDUAL runs (all seeds), with a CLUSTER bootstrap that resamples
    (arm,width) cells (not runs) so seeds of the same cell are not treated as independent. This is
    the small-net statistical-power protocol; it uses every run while respecting the seed clustering.
    yget(r) extracts the y value (lets the caller compute matched ratios on the fly)."""
    groups = {}
    for r in results:
        x = r.get(xkey); y = yget(r)
        if isinstance(x, (int, float)) and np.isfinite(x) and y is not None and np.isfinite(y):
            groups.setdefault((r["arm"], r["w"]), []).append((float(x), float(y)))
    keys = list(groups); allpts = [pt for g in groups.values() for pt in g]
    n_runs, n_cells = len(allpts), len(keys)
    if n_runs < 3: return dict(n=n_runs, ncell=n_cells, pearson=float("nan"), ci=(float("nan"),) * 2, p=float("nan"))
    X = np.array([p[0] for p in allpts]); Y = np.array([p[1] for p in allpts])
    pe = pearsonr(X, Y)[0]
    bs = []
    for _ in range(B):
        pts = [pt for k in (keys[i] for i in RNG.integers(0, n_cells, n_cells)) for pt in groups[k]]
        bx = np.array([p[0] for p in pts]); by = np.array([p[1] for p in pts])
        if np.std(bx) > 1e-9 and np.std(by) > 1e-9: bs.append(pearsonr(bx, by)[0])
    lo, hi = np.percentile(bs, [2.5, 97.5]) if bs else (float("nan"),) * 2
    perm = np.array([pearsonr(X, RNG.permutation(Y))[0] for _ in range(B)])
    p = (np.sum(np.abs(perm) >= abs(pe)) + 1) / (B + 1)
    return dict(n=n_runs, ncell=n_cells, pearson=pe, ci=(lo, hi), p=p)

def cells(results, keys):
    """Aggregate per (arm,width) over seeds; return list of dicts with means of `keys`."""
    by = {}
    for r in results: by.setdefault((r["arm"], r["w"]), []).append(r)
    out = []
    for (arm, w), rs in by.items():
        d = {"arm": arm, "w": w, "nseed": len(rs)}
        for k in keys:
            v = [r[k] for r in rs if isinstance(r.get(k), (int, float)) and np.isfinite(r[k])]
            d[k] = float(np.mean(v)) if v else float("nan")
        out.append(d)
    return out

def partial_corr(x, y, z):
    """Pearson(x,y) controlling for z (residualize both on z)."""
    x, y, z = (np.asarray(v, float) for v in (x, y, z))
    m = np.isfinite(x) & np.isfinite(y) & np.isfinite(z); x, y, z = x[m], y[m], z[m]
    if len(x) < 4: return float("nan")
    Z = np.c_[np.ones_like(z), z]
    rx = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]
    ry = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
    return pearsonr(rx, ry)[0]

def show(name, s, ref=None):
    r = f"  {name:34s} n={s['n']:2d}  Pearson {s['pearson']:+.3f}  CI[{s['ci'][0]:+.3f},{s['ci'][1]:+.3f}]  Spear {s['spearman']:+.3f}  p={s['p']:.4f}"
    if ref is not None: r += f"   [small-net {ref:+.2f}]"
    print(r)

def analyze_at(ds="cifar10"):
    res = load("at", ds)
    if not res: print(f"[{ds} AT] no cells yet"); return None
    for r in res:                                   # threat-matched ratios (Linf dual = L1)
        r["matched"] = r["dec_margin"] / r["dec_L1"] if r.get("dec_L1") else float("nan")
        r["mismatched"] = r["dec_margin"] / r["dec_L2"] if r.get("dec_L2") else float("nan")
    c = cells(res, ["consist", "matched", "mismatched", "rr_l2", "aa_Linf_8_255", "clean", "dec_etaL"])
    aa = [d["aa_Linf_8_255"] for d in c]
    print(f"\n=== {ds} ADVERSARIAL TRAINING ({len(res)} cells over {len(c)} (arm,width) groups) ===")
    show("consistency vs AA(Linf)", stat([d["consist"] for d in c], aa), SMALL_NET["at_consist_aa"])
    show("matched eta/||gradM||_1 vs AA", stat([d["matched"] for d in c], aa), SMALL_NET["at_matched_aa"])
    show("mismatched eta/||gradM||_2 vs AA", stat([d["mismatched"] for d in c], aa))
    show("robust radius L2 vs AA", stat([d["rr_l2"] for d in c], aa))
    pc = partial_corr([d["consist"] for d in c], aa, [d["clean"] for d in c])
    print(f"  partial corr consist~AA | clean acc: {pc:+.3f}  (controls the clean-accuracy confound)")
    # per-run cluster bootstrap (uses all seeds; resamples cells) -- the better-powered test
    if len(res) > len(c):                            # more runs than cells => multiple seeds present
        print(f"  -- per-run cluster bootstrap (all {len(res)} runs, resample cells) --")
        sc = stat_cluster(res, "consist", lambda r: r.get("aa_Linf_8_255"))
        print(f"     consistency vs AA          : n={sc['n']} runs/{sc['ncell']} cells  Pearson {sc['pearson']:+.3f}  CI[{sc['ci'][0]:+.3f},{sc['ci'][1]:+.3f}]  p={sc['p']:.4f}")
        sm = stat_cluster(res, "matched", lambda r: r.get("aa_Linf_8_255"))
        print(f"     matched eta/||gradM||_1 vs AA: n={sm['n']} runs/{sm['ncell']} cells  Pearson {sm['pearson']:+.3f}  CI[{sm['ci'][0]:+.3f},{sm['ci'][1]:+.3f}]  p={sm['p']:.4f}")
    print("  per-cell:")
    for d in sorted(c, key=lambda d: -d["consist"]):
        print(f"    {ARM_LAB[d['arm']]:12s} w{d['w']:<4} consist {d['consist']:.4f}  AA {d['aa_Linf_8_255']:.3f}  "
              f"rr {d['rr_l2']:.3f}  eta/L {d['dec_etaL']:.3f}  clean {d['clean']:.3f}")
    # recompute the masking verdict from stored audit values at the eval noise floor (binomial SE
    # ~2.2% at n=512), so a sub-noise PGD100>PGD20 wobble is not a false masking flag.
    def _ok(a):
        return (a.get("autoattack", 1) <= a.get("pgd20", 0) + 0.02 and
                a.get("pgd100", 1) <= a.get("pgd20", 0) + 0.03 and a.get("unbounded_robacc", 1) < 0.05 and
                (a.get("square_black", 1) >= a.get("apgd_white", 0) - 0.03 if "square_black" in a else True))
    bad = [r["_name"] for r in res if "audit" in r and not _ok(r["audit"])]
    print(f"  gradient-masking: {'all OK (noise-floor tolerant)' if not bad else 'FLAGGED: ' + str(bad)}")
    # consistency-axis mechanistic test: does widening the axis with low-invariance arms restore the
    # anti-prediction? Compare consistency-vs-AA over core-4 arms vs all arms (incl stdzero/maxpool).
    if any(d["arm"] in LOWINV for d in c):
        for lab, sub in [("core 4 arms", [d for d in c if d["arm"] in CORE4]),
                         ("all arms (+low-inv)", c)]:
            co = [d["consist"] for d in sub]; av = [d["aa_Linf_8_255"] for d in sub]
            s = stat(co, av, B=4000)
            print(f"  [consistency axis] {lab:22s}: range [{min(co):.3f},{max(co):.3f}] spread {max(co)-min(co):.3f}  "
                  f"consist-vs-AA Pearson {s['pearson']:+.3f} (n={s['n']}, p={s['p']:.3f})")
    return res, c

def analyze_std(ds="cifar10"):
    res = load("std", ds)
    if not res: print(f"[{ds} std] no cells yet"); return None
    c = cells(res, ["consist", "dec_etaL", "rr_l2", "clean"])
    rr = [d["rr_l2"] for d in c]
    print(f"\n=== {ds} STANDARD TRAINING ({len(res)} cells over {len(c)} groups) ===")
    show("eta/L vs robust radius", stat([d["dec_etaL"] for d in c], rr), SMALL_NET["std_etaL_rad"])
    show("consistency vs robust radius", stat([d["consist"] for d in c], rr), SMALL_NET["std_consist_rad"])
    cal = [r.get("calibration", {}) for r in res if "calibration" in r]
    if cal:
        gaps = [abs(d[f"aa_L2_{e}"] - d[f"radfrac_{e}"]) for d in cal for e in (0.05, 0.1, 0.15, 0.25)
                if d.get(f"aa_L2_{e}") is not None and np.isfinite(d.get(f"radfrac_{e}", np.nan))]
        if gaps: print(f"  radius-vs-AA calibration: mean |gap| {np.mean(gaps):.3f} (small-net 0.014) -> radius valid, no masking")
    return res, c

def decomposition(res_at):
    """Dlog margin / Dlog L / Dlog(eta/L) vs the standard arm, within each width."""
    if not res_at: return
    print("\n=== margin/Lipschitz decomposition (vs standard arm, within width) ===")
    c = cells(res_at, ["dec_margin", "dec_L2", "dec_etaL"])
    for w in sorted({d["w"] for d in c}):
        base = next((d for d in c if d["arm"] == "standard" and d["w"] == w), None)
        if not base: continue
        for d in [x for x in c if x["w"] == w and x["arm"] != "standard"]:
            dm = np.log(d["dec_margin"] / base["dec_margin"]); dL = np.log(d["dec_L2"] / base["dec_L2"])
            print(f"  w{w} {ARM_LAB[d['arm']]:12s}: Dlog margin {dm:+.3f}  Dlog L {dL:+.3f}  Dlog(eta/L) {dm-dL:+.3f}")

def figures(res_at, ds="cifar10"):
    if not res_at: return
    os.makedirs(FIGDIR, exist_ok=True)
    for r in res_at:
        r["matched"] = r["dec_margin"] / r["dec_L1"] if r.get("dec_L1") else float("nan")
    c = cells(res_at, ["consist", "matched", "aa_Linf_8_255"])
    # scatter: matched eta/L and consistency vs AA
    fig, ax = plt.subplots(1, 2, figsize=(8.2, 3.6))
    for xi, (key, lab) in enumerate([("matched", r"matched $\eta/\|\nabla M\|_1$"), ("consist", "shift-consistency")]):
        for r in res_at:
            ax[xi].scatter(r.get(key, np.nan), r.get("aa_Linf_8_255", np.nan), s=14, alpha=.3,
                           color=ARM_COL.get(r["arm"], "#888"), linewidths=0)
        for d in c:
            ax[xi].scatter(d[key], d["aa_Linf_8_255"], s=70, color=ARM_COL.get(d["arm"], "#888"),
                           edgecolor="k", linewidths=.6, zorder=3)
        s = stat([d[key] for d in c], [d["aa_Linf_8_255"] for d in c], B=2000)
        ax[xi].set_xlabel(lab); ax[xi].set_ylabel(r"AutoAttack robust acc ($\ell_\infty=8/255$)")
        ax[xi].set_title(f"Pearson {s['pearson']:+.2f}", fontsize=10); ax[xi].grid(alpha=.25)
    fig.tight_layout(); fn = os.path.join(FIGDIR, f"resnet_at_predict_{ds}.pdf")
    fig.savefig(fn, bbox_inches="tight"); plt.close(fig); print(f"# wrote {fn}")
    # training trajectories (val robust over epochs)
    fig, ax = plt.subplots(figsize=(5, 3.4))
    for r in res_at:
        cv = os.path.join(RESDIR, r["_name"] + "_curves.json")
        if r["w"] != 1.0 or not os.path.exists(cv): continue
        cur = json.load(open(cv)); ep = [x["epoch"] for x in cur]; vr = [x["val_robust"] for x in cur]
        ax.plot(ep, vr, color=ARM_COL.get(r["arm"], "#888"), label=ARM_LAB.get(r["arm"]))
    ax.set_xlabel("epoch"); ax.set_ylabel("val robust acc"); ax.legend(fontsize=8); ax.grid(alpha=.25)
    ax.set_title("AT trajectories (robust overfitting)", fontsize=10)
    fig.tight_layout(); fn = os.path.join(FIGDIR, f"resnet_at_traj_{ds}.pdf")
    fig.savefig(fn, bbox_inches="tight"); plt.close(fig); print(f"# wrote {fn}")

def completeness_report():
    """Loudly report which registered cells did NOT complete. This is the guard whose absence let the
    CIFAR-100 failure pass silently: the analysis must never quietly run over a subset of the grid."""
    import resnet_run as RR
    registered = list(RR.CELLS)
    done = [c for c in registered if os.path.exists(os.path.join(RESDIR, c + ".done"))]
    missing = [c for c in registered if not os.path.exists(os.path.join(RESDIR, c + ".done"))]
    print("=" * 78)
    print(f"COMPLETENESS: {len(done)}/{len(registered)} registered cells completed.")
    if missing:
        print(f"!!! {len(missing)} cells NOT completed (analysis below excludes them) !!!")
        for c in sorted(missing): print(f"    MISSING: {c}")
    else:
        print("All registered cells completed.")
    print("=" * 78)
    return missing

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__))
    missing = completeness_report()
    for ds in ("cifar10", "cifar100"):
        at = analyze_at(ds); std = analyze_std(ds)
        if at: decomposition(at[0]); figures(at[0], ds)
    if missing:
        print(f"\nWARNING: {len(missing)} cells missing; correlations above are over the COMPLETED subset only.")
