#!/usr/bin/env python3
"""
Unified-law figure: the SAME threat-matched eta/L1 -> AutoAttack relationship holds across two DIFFERENT
interventions on the identical CIFAR-10 Linf-8/255 PreActResNet-18 adversarial-training setup:
  (A) ARCHITECTURE axis: the six shift-invariance arms x two widths (resnet_scale AT cells).
  (D) DATA axis: diffusion-augmented AT at four+ doses x three seeds (v2firm early-stopped salvage).
If the data points fall on the architecture line, the "narrow-band" data axis is not a separate weak
result but the same law extended to a data intervention -> answers the reviewers' "n=4 narrow band" point.
Writes ../report/figures/unified_law.pdf.
Run: PYTHONNOUSERSITE=1 ../../env/cenv/bin/python fig_unified_law.py
"""
import os, glob, json, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resnet_analyze as RA

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "..", "..", "report", "figures")
DIFFDIR = os.path.join(HERE, "..", "..", "diffusion_robustness", "results")


def arch_points():
    res = RA.load("at", "cifar10")
    for r in res:
        r["matched"] = r["dec_margin"] / r["dec_L1"] if r.get("dec_L1") else float("nan")
    c = RA.cells(res, ["matched", "aa_Linf_8_255", "arm"])
    xs = [(d["matched"], d["aa_Linf_8_255"]) for d in c if np.isfinite(d["matched"]) and np.isfinite(d["aa_Linf_8_255"])]
    return np.array(xs)


def data_points():
    cand = [p for p in glob.glob(os.path.join(DIFFDIR, "salvage_earlystop_v2firm_*.json"))
            if {1000, 10000} <= {r["n_syn"] for r in json.load(open(p))["per_seed"]}]
    per = json.load(open(sorted(cand)[-1]))["per_seed"]
    # helping doses (>=100k) sit in the architecture eta/L1 band; include all for honesty, mark low-diversity
    xs = [(r["etaL1"], r["aa"], r["n_syn"]) for r in per]
    return np.array([(a, b) for a, b, n in xs]), np.array([n for _, _, n in xs])


def main():
    A = arch_points()
    D, Dn = data_points()
    # combined correlation on the helping-dose data (>=100k, the in-band regime) + all architecture
    Dhelp = D[Dn >= 100000]
    both = np.vstack([A, Dhelp])
    r_arch = pearsonr(A[:, 0], A[:, 1])[0]
    r_data = pearsonr(Dhelp[:, 0], Dhelp[:, 1])[0]
    r_both = pearsonr(both[:, 0], both[:, 1])[0]

    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    ax.scatter(A[:, 0], A[:, 1], s=80, facecolors="none", edgecolors="#1f77b4", linewidths=1.6,
               label=f"architecture arms (n={len(A)})", zorder=3)
    ax.scatter(Dhelp[:, 0], Dhelp[:, 1], s=55, color="#d62728", alpha=0.8,
               label=f"diffusion-data doses (n={len(Dhelp)})", zorder=3)
    # low-diversity data points (no gain) shown faint for honesty
    Dlow = D[Dn < 100000]
    if len(Dlow):
        ax.scatter(Dlow[:, 0], Dlow[:, 1], s=45, color="#d62728", alpha=0.25, marker="x",
                   label="low-diversity (no gain)", zorder=2)
    # combined trend line
    b, a = np.polyfit(both[:, 0], both[:, 1], 1)
    xx = np.linspace(both[:, 0].min(), both[:, 0].max(), 50)
    ax.plot(xx, b * xx + a, color="0.4", lw=1.4, ls="--", zorder=1,
            label=f"combined fit (Pearson ${r_both:+.2f}$)")
    ax.set_xlabel("threat-matched ratio $\\eta/\\|\\nabla M\\|_1$")
    ax.set_ylabel("AutoAttack robust accuracy (Linf $8/255$)")
    ax.set_title("One law across interventions: architecture and data\n"
                 f"(same CIFAR-10 Linf-$8/255$ PreActResNet-18 AT setup)", fontsize=11)
    ax.legend(fontsize=8.5, loc="lower right"); ax.grid(alpha=.25)
    fig.tight_layout()
    out = os.path.join(FIGDIR, "unified_law.pdf")
    fig.savefig(out, bbox_inches="tight"); fig.savefig(out.replace(".pdf", ".png"), dpi=150, bbox_inches="tight")
    print(f"# wrote {out}")
    print(f"Pearson eta/L1 vs AA:  architecture {r_arch:+.3f} (n={len(A)}) | data {r_data:+.3f} (n={len(Dhelp)}) "
          f"| COMBINED {r_both:+.3f} (n={len(both)})")
    print(f"combined eta/L1 range [{both[:,0].min():.4f}, {both[:,0].max():.4f}] "
          f"(vs data-alone [{Dhelp[:,0].min():.4f}, {Dhelp[:,0].max():.4f}])")


if __name__ == "__main__":
    main()
