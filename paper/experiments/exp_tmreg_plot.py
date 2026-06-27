#!/usr/bin/env python3
"""
Figure for the TM-MLR controlled intervention (exp_tmreg.py output): regularizing the
threat-matched margin gradient during AT RAISES eta/L exactly as the criterion predicts
(and only the matched l1 norm does), but the higher eta/L does NOT buy AutoAttack
robustness -- the self-limiting coupling (penalizing the gradient also shrinks the margin)
means eta/L is a faithful diagnostic but a poor training objective.

Two panels share the penalty-strength axis: (left) eta/L vs lambda for the matched l1 and
mismatched l2 margin penalties; (right) AutoAttack robust accuracy vs lambda for the same.
Writes report/figures/tmreg.pdf and prints the numbers.
Run: paper/env/cenv/bin/python paper/experiments/exp_tmreg_plot.py
"""
import os, json, glob, collections
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

PD = os.path.join(os.path.dirname(__file__), "..", "results", "at_partial", "tmreg")
FIG = os.path.join(os.path.dirname(__file__), "..", "report", "figures")
AAK = "aa_Linf_8_255"


def main():
    rows = [json.load(open(f)) for f in glob.glob(PD + "/*.json")]
    by = collections.defaultdict(list)
    for r in rows:
        by[(r["penalty"], float(r["lam"]))].append(r)

    def m(key, k):
        rs = by[key]
        v = [x[k] for x in rs if x.get(k) is not None and np.isfinite(x[k])]
        return np.mean(v) if v else np.nan

    def etaL(key):
        return m(key, "dec_margin") / m(key, "dec_L1")

    lams = [0.0, 0.2, 0.5]
    # build series for matched (margin_l1) and mismatched (margin_l2); lam=0 is the shared vanilla point
    def series(pen, k):
        ys = []
        for l in lams:
            key = ("none", 0.0) if l == 0.0 else (pen, l)
            ys.append(etaL(key) if k == "etaL" else m(key, k))
        return ys

    fig, ax = plt.subplots(1, 2, figsize=(8.0, 3.4))
    COL = {"margin_l1": "#d62728", "margin_l2": "#1f77b4"}
    LAB = {"margin_l1": r"matched $\ell_1$ (threat-matched)", "margin_l2": r"mismatched $\ell_2$"}
    for pen in ("margin_l1", "margin_l2"):
        ax[0].plot(lams, series(pen, "etaL"), "-o", color=COL[pen], label=LAB[pen])
        ax[1].plot(lams, series(pen, AAK), "-o", color=COL[pen], label=LAB[pen])
    # Finlay-Oberman reference point at lam=0.2
    ax[0].plot(0.2, etaL(("ce_l2", 0.2)), "s", color="0.45", label=r"$\ell_2$ loss-grad (F.-O.)")
    ax[1].plot(0.2, m(("ce_l2", 0.2), AAK), "s", color="0.45", label=r"$\ell_2$ loss-grad (F.-O.)")
    ax[0].set_xlabel(r"penalty strength $\lambda$"); ax[0].set_ylabel(r"threat-matched $\eta/L$")
    ax[0].set_title("the intervention raises $\\eta/L$\n(only the matched norm)", fontsize=9.5)
    ax[1].set_xlabel(r"penalty strength $\lambda$"); ax[1].set_ylabel(r"AutoAttack robust acc")
    ax[1].set_title("but robustness does not follow", fontsize=9.5)
    for a in ax:
        a.grid(alpha=.25); a.legend(fontsize=7, loc="best")
    fig.tight_layout()
    os.makedirs(FIG, exist_ok=True)
    fn = os.path.join(FIG, "tmreg.pdf")
    fig.savefig(fn, bbox_inches="tight"); plt.close(fig)
    print(f"# wrote {fn}")
    for pen in ("none", "ce_l2", "margin_l2", "margin_l1"):
        for l in sorted({k[1] for k in by if k[0] == pen}):
            print(f"  {pen}:{l}  etaL={etaL((pen,l)):.4f}  AA={m((pen,l),AAK):.3f}  clean={m((pen,l),'clean'):.3f}")


if __name__ == "__main__":
    main()
