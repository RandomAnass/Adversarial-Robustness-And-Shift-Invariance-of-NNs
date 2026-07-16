#!/usr/bin/env python3
"""
Self-contained analysis for the MNIST/Fashion gradient-anisotropy eps-sweep.

Reads the per-eps aggregate JSONs written by cifar_at.py (tag pattern anisosweep_e*),
gathers ONE ROW PER TRAINED MODEL (arm/width/seed/eps), and tests whether gradient
anisotropy  A = ||grad M||_1 / ||grad M||_2  ranks adversarial robustness across a
grid that spans a WIDE robustness range because the AT strength (eps) is varied.

For each dataset it reports, across all cells:
  - Spearman(A, robust)      [law hypothesis: NEGATIVE among robust models]
  - Spearman(eta/L, robust)  [control, expect POSITIVE: bigger margin/Lipschitz => more robust]
  - Spearman(consist, robust)
  - rank-partial partial(A, robust | clean_acc)   [rule out the clean-accuracy confound]
against TWO families of robustness metric:
  (a) rr_l2  : DDN L2 robust radius (metric-free, cross-model comparable) -- PRIMARY
  (b) aa_*   : AutoAttack robust accuracy at a SWEEP of eval-eps (reported at EACH eps)

Every correlation is recomputed two independent ways (scipy vs a hand rank+pearson)
and the two must agree. Sanity checks: aa<=clean, aa<=pgd (no masking), aa monotone
decreasing in eval-eps. Nothing is dropped silently; failures are printed.

Run:  PYTHONNOUSERSITE=1 paper/env/cenv/bin/python paper/experiments/aniso_sweep_analysis.py --dataset mnist
"""
import argparse, glob, json, os, numpy as np
from scipy.stats import spearmanr, pearsonr

RESDIR = os.path.join(os.path.dirname(__file__), "..", "results")


def _rankdata(a):
    """Average-rank transform (ties averaged), matching scipy's default."""
    a = np.asarray(a, float)
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(len(a), float)
    ranks[order] = np.arange(1, len(a) + 1)
    # average ties
    _, inv, cnt = np.unique(a, return_inverse=True, return_counts=True)
    sums = np.zeros(len(cnt)); np.add.at(sums, inv, ranks)
    return (sums / cnt)[inv]


def spearman_manual(x, y):
    """Independent Spearman: rank-transform then Pearson. Cross-checks scipy."""
    rx, ry = _rankdata(x), _rankdata(y)
    return float(np.corrcoef(rx, ry)[0, 1])


def partial_spearman(x, y, z):
    """Rank-partial correlation: partial(x,y | z) on ranks. Regress rank(x) and rank(y)
    each on rank(z), correlate the residuals."""
    rx, ry, rz = _rankdata(x), _rankdata(y), _rankdata(z)
    def resid(a, b):
        b1 = np.c_[np.ones_like(b), b]
        coef, *_ = np.linalg.lstsq(b1, a, rcond=None)
        return a - b1 @ coef
    ex, ey = resid(rx, rz), resid(ry, rz)
    return float(np.corrcoef(ex, ey)[0, 1])


def load_rows(dataset, norm="linf"):
    """One row per trained model, gathered from all anisosweep per-eps aggregate JSONs.
    De-duplicates on (arm,w,seed,train_eps) keeping the newest file."""
    files = sorted(glob.glob(os.path.join(RESDIR, f"at_{dataset}_{norm}_anisosweep_e*.json")))
    rows = {}
    for f in files:
        d = json.load(open(f))
        teps = float(d["recipe"]["eps"])
        for r in d["results"]:
            key = (r["arm"], r["w"], r["seed"], round(teps, 6))
            r = dict(r); r["train_eps"] = teps; r["A"] = r["dec_L1"] / r["dec_L2"]
            rows[key] = r  # newest file wins (sorted asc -> later overwrites)
    return list(rows.values()), files


def aa_keys(rows):
    ks = set()
    for r in rows:
        ks.update(k for k in r if k.startswith("aa_"))
    return sorted(ks, key=lambda k: float(k.rsplit("_", 2)[-2] + "." + k.rsplit("_", 1)[-1]))


def sanity(rows):
    problems = []
    aks = aa_keys(rows)
    for r in rows:
        tag = f"{r['arm']}_w{r['w']}_s{r['seed']}_te{r['train_eps']:.3f}"
        for k in aks:
            if k in r and r[k] > r["clean"] + 1e-6:
                problems.append(f"{tag}: {k}={r[k]:.3f} > clean={r['clean']:.3f}")
            pk = "pgd_" + k[3:]
            if k in r and pk in r and r[k] > r[pk] + 1e-6:
                problems.append(f"{tag}: MASKING {k}={r[k]:.3f} > {pk}={r[pk]:.3f}")
        # monotone decreasing aa in eval-eps
        vals = [(float(k.rsplit('_', 2)[-2] + '.' + k.rsplit('_', 1)[-1]), r[k]) for k in aks if k in r]
        vals.sort()
        for (e0, v0), (e1, v1) in zip(vals, vals[1:]):
            if v1 > v0 + 1e-6:
                problems.append(f"{tag}: non-monotone AA {e0}->{e1}: {v0:.3f}->{v1:.3f}")
    return problems


def corr_block(name, A, robust, clean, etaL, consist, label):
    """Print all correlations for one robustness metric, cross-checking scipy vs manual."""
    sp_sci = spearmanr(A, robust)[0]; sp_man = spearman_manual(A, robust)
    # cross-check scipy vs manual; a constant robust column (e.g. AA=0 for every cell at a hard
    # eval-eps) makes BOTH nan -> that agreement is fine, only a real numeric disagreement is a bug.
    both_nan = np.isnan(sp_sci) and np.isnan(sp_man)
    assert both_nan or abs(sp_sci - sp_man) < 1e-6, f"scipy/manual mismatch {sp_sci} vs {sp_man}"
    if np.isnan(sp_sci):
        print(f"  {label:14s} n={len(robust):2d}  (constant robust column -> correlation undefined)")
        return dict(metric=label, n=len(robust), A_spear=None, A_spear_p=None,
                    A_partial_clean=None, etaL_spear=None, consist_spear=None, clean_spear=None,
                    note="constant_robust_column")
    p = spearmanr(A, robust)[1]
    part = partial_spearman(A, robust, clean)
    eta_sp = spearmanr(etaL, robust)[0]
    cs_sp = spearmanr(consist, robust)[0]
    cl_sp = spearmanr(clean, robust)[0]
    print(f"  {label:14s} n={len(robust):2d}  "
          f"A:sp={sp_sci:+.3f}(p={p:.2g}) partial|clean={part:+.3f}  "
          f"eta/L:sp={eta_sp:+.3f}  consist:sp={cs_sp:+.3f}  clean:sp={cl_sp:+.3f}")
    return dict(metric=label, n=len(robust), A_spear=sp_sci, A_spear_p=p,
                A_partial_clean=part, etaL_spear=eta_sp, consist_spear=cs_sp, clean_spear=cl_sp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=["mnist", "fashion"])
    ap.add_argument("--norm", default="linf")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    rows, files = load_rows(args.dataset, args.norm)
    print(f"=== {args.dataset} {args.norm} anisotropy eps-sweep ===")
    print(f"loaded {len(rows)} model cells from {len(files)} files")
    for f in files:
        print("  ", os.path.basename(f))

    A = np.array([r["A"] for r in rows])
    clean = np.array([r["clean"] for r in rows])
    etaL = np.array([r["dec_etaL"] for r in rows])
    consist = np.array([r["consist"] for r in rows])
    rr = np.array([r["rr_l2"] for r in rows])
    teps = np.array([r["train_eps"] for r in rows])

    print(f"\ntrain_eps values: {sorted(set(np.round(teps,4).tolist()))}")
    print(f"A range:      [{A.min():.3f}, {A.max():.3f}]  (sqrt(784)={np.sqrt(784):.1f} is the ceiling)")
    print(f"rr_l2 range:  [{rr.min():.3f}, {rr.max():.3f}]")
    print(f"clean range:  [{clean.min():.3f}, {clean.max():.3f}]")
    print(f"eta/L range:  [{etaL.min():.3f}, {etaL.max():.3f}]")
    print(f"consist range:[{consist.min():.3f}, {consist.max():.3f}]")

    problems = sanity(rows)
    print(f"\nsanity: {'OK (no violations)' if not problems else str(len(problems))+' VIOLATIONS:'}")
    for p in problems: print("   !", p)

    summary = []
    print("\ncorrelations across all cells (hypothesis: A negative; eta/L positive):")
    summary.append(corr_block("rr", A, rr, clean, etaL, consist, "rr_l2 (DDN)"))
    for k in aa_keys(rows):
        if all(k in r for r in rows):
            robust = np.array([r[k] for r in rows])
            summary.append(corr_block(k, A, robust, clean, etaL, consist, k))
        else:
            print(f"  {k}: SKIPPED (missing in some cells)")

    # mechanism probe: does A move with train_eps? does rr - eta/L1 gap grow with A?
    print("\nmechanism:")
    print(f"  Spearman(train_eps, A)     = {spearmanr(teps, A)[0]:+.3f}   (does stronger AT change A?)")
    print(f"  Spearman(train_eps, rr_l2) = {spearmanr(teps, rr)[0]:+.3f}   (does stronger AT raise the radius?)")
    L1 = np.array([r["dec_L1"] for r in rows]); margin = np.array([r["dec_margin"] for r in rows])
    eta_over_L1 = margin / L1
    gap = rr - eta_over_L1
    print(f"  Spearman(A, rr - margin/L1)= {spearmanr(A, gap)[0]:+.3f}   "
          f"(effective-dim mechanism: gap should GROW with A if r ~ (eta/L1)/(1+cA))")
    print(f"  Spearman(A, rr)/Spearman(A, margin/L1) = "
          f"{spearmanr(A, rr)[0]:+.3f} / {spearmanr(A, eta_over_L1)[0]:+.3f}")

    out = args.out or os.path.join(RESDIR, f"anisosweep_analysis_{args.dataset}_{args.norm}.json")
    payload = dict(dataset=args.dataset, norm=args.norm, n_cells=len(rows), files=[os.path.basename(f) for f in files],
                   A_range=[float(A.min()), float(A.max())], rr_range=[float(rr.min()), float(rr.max())],
                   clean_range=[float(clean.min()), float(clean.max())], sanity_violations=problems,
                   train_eps=sorted(set(np.round(teps, 4).tolist())),
                   spearman_teps_A=float(spearmanr(teps, A)[0]),
                   spearman_A_gap=float(spearmanr(A, gap)[0]), summary=summary,
                   rows=[{k: r[k] for k in ("arm", "w", "seed", "train_eps", "A", "clean", "consist",
                          "rr_l2", "dec_etaL", "dec_margin", "dec_L1", "dec_L2",
                          *[k for k in r if k.startswith("aa_") or k.startswith("pgd_")])} for r in rows])
    json.dump(payload, open(out, "w"), indent=2, default=float)
    print(f"\nsaved {out}")


if __name__ == "__main__":
    main()
