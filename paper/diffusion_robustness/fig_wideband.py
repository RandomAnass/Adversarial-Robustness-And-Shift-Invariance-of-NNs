#!/usr/bin/env python3
"""
S3 wide-band figure: the budget-normalized threat-matched law + the quantified data-axis offset.

Panel A: AutoAttack robust accuracy (evaluated at each model's own training eps) vs the
budget-normalized ratio eta/(L1*eps), over the full eps x dose sweep (16 cells). The sweep collapses
onto one monotone curve (Pearson +0.94), while the raw eta/L1 anti-correlates across budgets (-0.95):
across attack budgets the certificate must be measured in units of the budget.
Panel B: the offset mechanism: train-test robust gap per (eps, dose). The +1M arms have a uniformly
smaller gap, and both the gap and the dose gain shrink as eps grows (nothing left to overfit).
Reads results/partial/s3eps_*.json. Writes ../report/figures/wideband_law.pdf/.png.
Run: PYTHONNOUSERSITE=1 ../env/cenv/bin/python fig_wideband.py
"""
import os, glob, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "report", "figures")
EPS_C = {2: "#1f77b4", 4: "#2ca02c", 8: "#d62728", 16: "#9467bd"}


def main():
    rows = [json.load(open(p)) for p in glob.glob(os.path.join(HERE, "results/partial/s3eps_*.json"))]
    rows = [r for r in rows if r.get("aa_matched") is not None]
    e1 = np.array([r["etaL1"] for r in rows]); eps = np.array([r["eps"] for r in rows])
    aa = np.array([r["aa_matched"] for r in rows]); dose = np.array([r["n_syn"] > 0 for r in rows])
    gap = np.array([r["rob_gap"] for r in rows]); eps255 = np.array([r["eps255"] for r in rows])
    x = e1 / eps
    r_norm = pearsonr(x, aa)[0]; s_norm = spearmanr(x, aa)[0]; r_raw = pearsonr(e1, aa)[0]

    fig, ax = plt.subplots(1, 2, figsize=(11.6, 4.3))
    # --- Panel A: the collapse ---
    for e in sorted(set(eps255)):
        for d, mk, lab in [(False, "o", "real-only"), (True, "s", "+1M synthetic")]:
            m = (eps255 == e) & (dose == d)
            ax[0].scatter(x[m], aa[m], s=70, marker=mk, facecolors=("none" if not d else EPS_C[e]),
                          edgecolors=EPS_C[e], linewidths=1.6,
                          label=(f"$\\varepsilon$={int(e)}/255 {lab}" if e in (2,) else None))
    order = np.argsort(x)
    ax[0].plot(x[order], np.poly1d(np.polyfit(x, aa, 2))(x[order]), color="0.55", lw=1.3, ls="--", zorder=1)
    ax[0].set_xlabel("budget-normalized ratio $\\eta/(L_1\\varepsilon)$")
    ax[0].set_ylabel("AutoAttack robust acc at the training $\\varepsilon$")
    ax[0].set_title(f"One curve across budgets: Pearson ${r_norm:+.2f}$, Spearman ${s_norm:+.2f}$\n"
                    f"(raw $\\eta/L_1$ across budgets: ${r_raw:+.2f}$)", fontsize=10.5)
    hs, ls_ = ax[0].get_legend_handles_labels()
    ax[0].legend(hs, ["real-only (circles)", "+1M synthetic (squares)"], fontsize=8.5, loc="upper left")
    ax[0].grid(alpha=.25)
    for e in sorted(set(eps255)):
        m = eps255 == e
        ax[0].annotate(f"$\\varepsilon$={int(e)}", (x[m].mean(), aa[m].max() + 0.03),
                       color=EPS_C[e], fontsize=9, ha="center")

    # --- Panel B: the offset = robust generalization ---
    epsu = sorted(set(eps255)); xb = np.arange(len(epsu)); w = 0.36
    g0 = [gap[(eps255 == e) & (~dose)].mean() for e in epsu]
    g1 = [gap[(eps255 == e) & dose].mean() for e in epsu]
    a0 = [aa[(eps255 == e) & (~dose)].mean() for e in epsu]
    a1 = [aa[(eps255 == e) & dose].mean() for e in epsu]
    ax[1].bar(xb - w/2, g0, w, color="#888888", label="robust gap, real-only")
    ax[1].bar(xb + w/2, g1, w, color="#d62728", label="robust gap, +1M")
    for i in range(len(epsu)):
        ax[1].annotate(f"AA {a1[i]-a0[i]:+.2f}", (xb[i], max(g0[i], g1[i]) + 0.012),
                       ha="center", fontsize=8.5)
    ax[1].set_xticks(xb); ax[1].set_xticklabels([f"{int(e)}/255" for e in epsu])
    ax[1].set_xlabel("adversarial-training budget $\\varepsilon$")
    ax[1].set_ylabel("train$-$test robust gap (PGD at $\\varepsilon$)")
    ax[1].set_title("The data gain tracks the robust gap it removes\n(annotations: AA gain of +1M at that $\\varepsilon$)",
                    fontsize=10.5)
    ax[1].legend(fontsize=8.5); ax[1].grid(alpha=.25, axis="y")

    fig.tight_layout()
    out = os.path.join(FIG, "wideband_law.pdf")
    fig.savefig(out, bbox_inches="tight"); fig.savefig(out.replace(".pdf", ".png"), dpi=150, bbox_inches="tight")
    print(f"# wrote {out}")
    print(f"normalized {r_norm:+.3f}/{s_norm:+.3f} raw {r_raw:+.3f} | AA gains by eps:",
          {int(e): round(a1[i]-a0[i], 3) for i, e in enumerate(epsu)})


if __name__ == "__main__":
    main()
