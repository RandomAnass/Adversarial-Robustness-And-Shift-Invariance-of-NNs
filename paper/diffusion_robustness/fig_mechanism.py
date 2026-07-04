#!/usr/bin/env python3
"""
Mechanism figure for the diffusion data intervention (two panels):
  A  Robust-overfitting delay: robust-test accuracy vs epoch for real-only (peaks early, then decays as it
     robustly overfits) versus +1M synthetic (keeps improving). The added data postpones the memorization
     phase, so the best-robust checkpoint is higher.
  B  The gain is coverage-gated, not a mixing artifact: best-checkpoint AutoAttack vs synthetic-pool size at
     the 70%-synthetic mixing (main sweep) with the 10k/100k control points at 30% synthetic overlaid, and
     the real-only baseline. 10k gives no gain at EITHER mixing; >=100k helps at both -> a coverage threshold.
Run: PYTHONNOUSERSITE=1 ../env/cenv/bin/python fig_mechanism.py
"""
import os, glob, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "report", "figures"); os.makedirs(FIG, exist_ok=True)


def load_diversity_salvage():
    """The v2firm salvage that includes the low-diversity doses (1k,10k) -> the 6-dose diversity sweep."""
    best = None
    for p in glob.glob(os.path.join(HERE, "results/salvage_earlystop_v2firm_*.json")):
        d = json.load(open(p)); doses = {r["n_syn"] for r in d.get("per_seed", [])}
        if {1000, 10000} <= doses:
            best = d  # the diversity run (has 1k & 10k)
    return best


def mean_aa(per, n):
    v = [r["aa"] for r in per if r["n_syn"] == n]
    return (np.mean(v), np.std(v)) if v else (np.nan, 0.0)


def main():
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.2))

    # --- Panel A: robust-overfitting delay (single-seed trajectory, illustrative) ---
    tj = sorted(glob.glob(os.path.join(HERE, "results/mech/mech_trajectory_*.json")))
    curve = json.load(open(tj[-1]))["result"]["curve"]
    for n, c, lab in [(0, "#444444", "real-only"), (1000000, "#d62728", "+1M synthetic")]:
        s = sorted([r for r in curve if r["n_syn"] == n], key=lambda r: r["epoch"])
        ep = [r["epoch"] for r in s]; rte = [r["robust_test"] for r in s]
        ax[0].plot(ep, rte, marker="o", ms=3, color=c, lw=1.8, label=lab)
        pk = max(s, key=lambda r: r["robust_test"])
        ax[0].scatter([pk["epoch"]], [pk["robust_test"]], s=90, facecolors="none", edgecolors=c, lw=1.8, zorder=5)
    ax[0].annotate("peak, then\nrobustly overfits", xy=(20, 0.42), xytext=(24, 0.35),
                   fontsize=8.5, color="#444444", arrowprops=dict(arrowstyle="->", color="#444444"))
    ax[0].set_xlabel("epoch"); ax[0].set_ylabel("robust-test accuracy (PGD $\\ell_\\infty$)")
    ax[0].set_title("Synthetic data delays robust overfitting", fontsize=11)
    ax[0].legend(fontsize=9, loc="lower right"); ax[0].grid(alpha=.25)

    # --- Panel B: coverage threshold, robust to mixing fraction ---
    div = load_diversity_salvage()
    doses = [0, 1000, 10000, 100000, 500000, 1000000]
    x = np.arange(len(doses)); xt = ["0", "1k", "10k", "100k", "500k", "1M"]
    m70 = [mean_aa(div["per_seed"], n) for n in doses]
    ax[1].errorbar(x, [a[0] for a in m70], yerr=[a[1] for a in m70], marker="o", color="#1f77b4",
                   lw=2, capsize=3, label="70% synthetic (main sweep)")
    # 30% synthetic control (10k, 100k)
    ctrl = sorted(glob.glob(os.path.join(HERE, "results/salvage_earlystop_v2ctrl_*.json")))
    if ctrl:
        cd = json.load(open(ctrl[-1]))
        cx = {10000: 2, 100000: 3}
        for n in (10000, 100000):
            a = mean_aa(cd["per_seed"], n)
            ax[1].errorbar([cx[n]], [a[0]], yerr=[a[1]], marker="s", color="#2ca02c", ms=9, capsize=3,
                           label="30% synthetic (control)" if n == 10000 else None)
    base = mean_aa(div["per_seed"], 0)[0]
    ax[1].axhline(base, color="0.5", ls="--", lw=1.2, label="real-only baseline")
    ax[1].axvspan(-0.3, 1.6, color="#d62728", alpha=0.06)
    ax[1].text(0.65, ax[1].get_ylim()[0], "no gain\n(low coverage)", fontsize=8, color="#a33", ha="center", va="bottom")
    ax[1].set_xticks(x); ax[1].set_xticklabels(xt)
    ax[1].set_xlabel("unique synthetic images (pool diversity)")
    ax[1].set_ylabel("best-checkpoint AutoAttack acc")
    ax[1].set_title("The gain is coverage-gated, not a mixing artifact", fontsize=11)
    ax[1].legend(fontsize=8.3, loc="lower right"); ax[1].grid(alpha=.25)

    fig.suptitle("Mechanism: diffusion data delays robust overfitting, given sufficient coverage", fontsize=12, y=1.02)
    fig.tight_layout()
    out = os.path.join(FIG, "diffusion_mechanism.pdf")
    fig.savefig(out, bbox_inches="tight"); fig.savefig(out.replace(".pdf", ".png"), dpi=150, bbox_inches="tight")
    print("# wrote", out, "| baseline AA=%.3f" % base)


if __name__ == "__main__":
    main()
