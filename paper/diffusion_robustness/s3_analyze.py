#!/usr/bin/env python3
"""
S3 analysis: read the per-cell partial JSONs from the eps-sweep (diff_pilot_s3.py) and characterize
(1) the WIDE-BAND threat-matched eta/L1-vs-AutoAttack law and (2) the data-axis OFFSET (+1M vs real-only)
and whether it is explained by a smaller train-test robust gap. Standalone (reads results/partial/),
so it runs on partial progress too. Usage:
    PYTHONNOUSERSITE=1 ../env/cenv/bin/python s3_analyze.py --tag s3eps
"""
import argparse, os, glob, json, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PARTDIR = os.path.join(HERE, "results", "partial")
RESDIR = os.path.join(HERE, "results")


def pearson(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def spearman(a, b):
    if len(a) < 2:
        return float("nan")
    return pearson(np.argsort(np.argsort(a)), np.argsort(np.argsort(b)))


def ols(cols, y, names):
    y = np.asarray(y, float)
    Xm = np.column_stack([np.ones(len(y))] + cols)
    beta, *_ = np.linalg.lstsq(Xm, y, rcond=None)
    resid = y - Xm @ beta
    dof = max(len(y) - Xm.shape[1], 1)
    s2 = float(resid @ resid) / dof
    cov = s2 * np.linalg.pinv(Xm.T @ Xm)
    se = np.sqrt(np.clip(np.diag(cov), 0, None))
    with np.errstate(divide="ignore", invalid="ignore"):
        t = beta / np.where(se > 0, se, np.nan)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - float(resid @ resid) / ss_tot if ss_tot > 0 else float("nan")
    return dict(names=names, beta=beta.tolist(), se=se.tolist(), t=t.tolist(), dof=dof, r2=r2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="s3eps")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--bs", type=int, default=512)
    args = ap.parse_args()

    pat = os.path.join(PARTDIR, f"{args.tag}_eps*_e{args.epochs}_bs{args.bs}_*.json")
    rows = []
    for p in sorted(glob.glob(pat)):
        try:
            r = json.load(open(p))
            if r.get("aa_matched") is not None:
                rows.append(r)
        except Exception:
            pass
    if not rows:
        print(f"no cells match {pat}"); return
    rows.sort(key=lambda r: (r["eps255"], r["n_syn"], r["seed"]))

    e1 = [r["etaL1"] for r in rows]
    e2 = [r["etaL2"] for r in rows]
    aa = [r["aa_matched"] for r in rows]
    pgd = [r["pgd_matched"] for r in rows]
    eps = [r["eps"] for r in rows]
    gap = [r["rob_gap"] for r in rows]
    dose = [1.0 if r["n_syn"] > 0 else 0.0 for r in rows]
    e1_over_eps = [x / y for x, y in zip(e1, eps)]

    print(f"\n==== S3 per-cell ({len(rows)} cells) ====")
    hdr = (f"{'eps':>5} {'dose':>5} {'seed':>4} {'bep':>4} {'clean':>6} {'etaL1':>7} {'e1/eps':>7} "
           f"{'etaL2':>6} {'AA':>6} {'PGD':>6} {'AA<=PGD':>7} {'rr_L2':>6} {'robTr':>6} {'robTe':>6} {'gap':>7}")
    print(hdr); print("-" * len(hdr))
    viol = 0
    for r in rows:
        dl = "0" if r["n_syn"] == 0 else ("1M" if r["n_syn"] >= 1_000_000 else f"{r['n_syn']//1000}k")
        ok = r["aa_matched"] <= r["pgd_matched"] + 1e-9
        viol += (0 if ok else 1)
        print(f"{r['eps255']:>5g} {dl:>5} {r['seed']:>4} {r['best_ep']:>4} {r['clean']:>6.3f} "
              f"{r['etaL1']:>7.4f} {r['etaL1']/r['eps']:>7.2f} {r['etaL2']:>6.2f} {r['aa_matched']:>6.3f} "
              f"{r['pgd_matched']:>6.3f} {'OK' if ok else 'VIOL':>7} {r['rr_l2']:>6.3f} "
              f"{r['rob_train']:>6.3f} {r['rob_test']:>6.3f} {r['rob_gap']:>+7.3f}")
    print(f"masking check: {len(rows)-viol}/{len(rows)} cells AA<=PGD  ({'ALL OK' if viol==0 else str(viol)+' VIOLATIONS'})")

    # per-(eps,dose) means
    def mean(vs):
        return float(np.mean(vs)) if vs else float("nan")
    epss = sorted(set(r["eps255"] for r in rows))
    print(f"\n==== per-(eps,dose) means ====")
    print(f"{'eps':>5} {'dose':>5} {'n':>3} {'etaL1':>8} {'AA':>7} {'gap':>8} {'clean':>7}")
    cellm = {}
    for e in epss:
        for d, dl in ((0, "0"), (1, "1M")):
            sub = [r for r in rows if r["eps255"] == e and (r["n_syn"] > 0) == (d == 1)]
            if not sub:
                continue
            cellm[(e, d)] = dict(etaL1=mean([r["etaL1"] for r in sub]), aa=mean([r["aa_matched"] for r in sub]),
                                 gap=mean([r["rob_gap"] for r in sub]), clean=mean([r["clean"] for r in sub]), n=len(sub))
            m = cellm[(e, d)]
            print(f"{e:>5g} {dl:>5} {m['n']:>3} {m['etaL1']:>8.4f} {m['aa']:>7.3f} {m['gap']:>+8.3f} {m['clean']:>7.3f}")

    # paired per-eps: +1M minus real-only (matched eps) -> AA offset, etaL1 shift, gap shift
    print(f"\n==== paired per-eps (+1M) - (real-only) ====")
    print(f"{'eps':>5} {'dAA':>8} {'d_etaL1':>9} {'d_gap':>8} {'d_clean':>8}")
    dAA, dGAP = [], []
    for e in epss:
        if (e, 0) in cellm and (e, 1) in cellm:
            a0, a1 = cellm[(e, 0)], cellm[(e, 1)]
            da = a1["aa"] - a0["aa"]; de1 = a1["etaL1"] - a0["etaL1"]; dg = a1["gap"] - a0["gap"]; dc = a1["clean"] - a0["clean"]
            dAA.append(da); dGAP.append(dg)
            print(f"{e:>5g} {da:>+8.3f} {de1:>+9.4f} {dg:>+8.3f} {dc:>+8.3f}")

    an = {}
    an["n_points"] = len(rows)
    an["etaL1_range"] = [min(e1), max(e1)]
    an["etaL1_over_eps_range"] = [min(e1_over_eps), max(e1_over_eps)]
    an["AA_range"] = [min(aa), max(aa)]
    an["clean_range"] = [min(r["clean"] for r in rows), max(r["clean"] for r in rows)]
    an["etaL1_vs_AA"] = dict(pearson=pearson(e1, aa), spearman=spearman(e1, aa))
    an["etaL1_over_eps_vs_AA"] = dict(pearson=pearson(e1_over_eps, aa), spearman=spearman(e1_over_eps, aa))
    an["etaL2_vs_AA"] = dict(pearson=pearson(e2, aa), spearman=spearman(e2, aa))
    an["ols_AA_on_etaL1_dose"] = ols([e1, dose], aa, ["const", "etaL1", "dose(+1M)"])
    an["ols_AA_on_etaL1_eps_dose"] = ols([e1, eps, dose], aa, ["const", "etaL1", "eps", "dose(+1M)"])
    an["ols_gap_on_dose"] = ols([dose], gap, ["const", "dose(+1M)"])
    an["dose_vs_gap_pearson"] = pearson(dose, gap)
    an["mean_dAA_1M_minus_real"] = mean(dAA)
    an["mean_dgap_1M_minus_real"] = mean(dGAP)

    print(f"\n==== WIDE-BAND threat-matched law (all {len(rows)} cells) ====")
    print(f"  etaL1 range   : [{an['etaL1_range'][0]:.4f}, {an['etaL1_range'][1]:.4f}]  "
          f"(span x{an['etaL1_range'][1]/max(an['etaL1_range'][0],1e-9):.1f})")
    print(f"  AA range      : [{an['AA_range'][0]:.3f}, {an['AA_range'][1]:.3f}]")
    print(f"  etaL1 vs AA   : Pearson {an['etaL1_vs_AA']['pearson']:+.3f}  Spearman {an['etaL1_vs_AA']['spearman']:+.3f}"
          f"   [narrow-band ref +0.85 over etaL1 0.041-0.044]")
    print(f"  etaL1/eps vs AA: Pearson {an['etaL1_over_eps_vs_AA']['pearson']:+.3f}  "
          f"Spearman {an['etaL1_over_eps_vs_AA']['spearman']:+.3f}  (threat-normalized certificate margin)")
    print(f"  etaL2 vs AA   : Pearson {an['etaL2_vs_AA']['pearson']:+.3f}  (mismatched L2-dual)")

    print(f"\n==== OFFSET: AA regressed on etaL1 (+ eps) with a +1M dummy ====")
    for key in ("ols_AA_on_etaL1_dose", "ols_AA_on_etaL1_eps_dose"):
        o = an[key]
        print(f"  {key}  (R2={o['r2']:.3f}, dof={o['dof']}):")
        for nm, b, s, t in zip(o["names"], o["beta"], o["se"], o["t"]):
            star = "*" if (isinstance(t, float) and math.isfinite(t) and abs(t) >= 2.0) else " "
            print(f"    {nm:>12}: beta {b:+.4f}  se {s:.4f}  t {t:+.2f} {star}")
    print(f"  mean AA offset (+1M - real, matched eps): {an['mean_dAA_1M_minus_real']:+.3f}")
    print(f"\n==== is the offset robust generalization? ====")
    og = an["ols_gap_on_dose"]
    print(f"  gap ~ dose:  dose(+1M) beta {og['beta'][1]:+.4f}  se {og['se'][1]:.4f}  t {og['t'][1]:+.2f}")
    print(f"  dose vs gap Pearson: {an['dose_vs_gap_pearson']:+.3f}  (neg => +1M has SMALLER train-test robust gap)")
    print(f"  mean gap shift (+1M - real): {an['mean_dgap_1M_minus_real']:+.3f}")

    fn = os.path.join(RESDIR, f"s3_analysis_{args.tag}.json")
    json.dump(dict(n_cells=len(rows), rows=rows, analysis=an), open(fn, "w"), indent=2, default=float)
    print(f"\nsaved {fn}")


if __name__ == "__main__":
    main()
