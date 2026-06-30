#!/usr/bin/env python3
"""
NQ1 figure: the diffusion arms OBEY the threat-matched eta/L law.

At fair best-checkpoint comparison (salvage_earlystop), the Linf-threat-matched ratio eta/L1=M/||grad||_1
predicts AutoAttack(Linf) robust accuracy (monotone, Pearson ~+0.96), while the MIS-matched L2 ratio
eta/L2 anti-predicts it (~-0.75) -- a clean demonstration of the main paper's threat-matching requirement,
now extended to a data (not architecture) intervention. Panel C shows robust overfitting as an eta/L
collapse over training (baseline eta/L falls late; synthetic arms hold).
Run: PYTHONNOUSERSITE=1 ../env/cenv/bin/python fig_etaL_law.py
"""
import os, glob, json, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures"); os.makedirs(FIG, exist_ok=True)
DOSE_C = {0: "#444444", 100000: "#1f77b4", 500000: "#2ca02c", 1000000: "#d62728"}
DOSE_L = {0: "real-only", 100000: "+100k", 500000: "+500k", 1000000: "+1M"}


def pear(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _load():
    """Prefer the multi-seed v2firm salvage JSON (per_seed + aggregate); fall back to single-seed 'rows'."""
    cand = sorted(glob.glob(os.path.join(HERE, "results/salvage_earlystop_v2firm_*.json")))
    if cand:
        d = json.load(open(cand[-1])); per = d["per_seed"]
        for r in per:
            r.setdefault("etaL1", r["margin"] / r["L1"])
        return per, d.get("aggregate"), f"v2firm multi-seed ({d['pearson']['n_points']} dose$\\times$seed pts)"
    sp = sorted(glob.glob(os.path.join(HERE, "results/salvage_earlystop_*.json")))[-1]
    rows = json.load(open(sp))["rows"]
    for r in rows:
        r.setdefault("etaL1", r["margin"] / r["L1"])
    return rows, None, "single seed"


def main():
    per, aggregate, srclab = _load()
    per.sort(key=lambda r: r["n_syn"])
    aa = [r["aa"] for r in per]
    etaL1 = [r["etaL1"] for r in per]
    etaL2 = [r["etaL"] for r in per]
    ns = [r["n_syn"] for r in per]
    doses = sorted(set(ns))

    def dmean(key, dose):
        v = [r[key] for r in per if r["n_syn"] == dose]
        return float(np.mean(v)), float(np.std(v))

    fig, ax = plt.subplots(1, 3, figsize=(14.5, 4.3))

    # Panel A: matched -- eta/L1 vs AA(Linf), per-seed scatter + per-dose mean+/-std
    seen = set()
    for x, y, n in zip(etaL1, aa, ns):
        lab = DOSE_L[n] if n not in seen else None; seen.add(n)
        ax[0].scatter(x, y, s=55, color=DOSE_C[n], alpha=0.55, zorder=2, label=lab)
    mx = [dmean("etaL1", n) for n in doses]; my = [dmean("aa", n) for n in doses]
    ax[0].errorbar([m[0] for m in mx], [m[0] for m in my], xerr=[m[1] for m in mx], yerr=[m[1] for m in my],
                   fmt="-", color="0.3", lw=1.4, capsize=3, zorder=3)
    ax[0].set_xlabel("$\\eta/L_1$  (Linf-threat-matched ratio)")
    ax[0].set_ylabel("AutoAttack robust acc (Linf 8/255)")
    ax[0].set_title(f"Threat-MATCHED: predicts AA\nPearson $={pear(etaL1, aa):+.2f}$", fontsize=10.5)
    ax[0].legend(fontsize=8.5, loc="lower right"); ax[0].grid(alpha=.25)

    # Panel B: mismatched -- eta/L2 vs AA(Linf)
    for x, y, n in zip(etaL2, aa, ns):
        ax[1].scatter(x, y, s=55, color=DOSE_C[n], alpha=0.55, zorder=2)
    mx2 = [dmean("etaL", n) for n in doses]
    order = np.argsort([m[0] for m in mx2])
    ax[1].plot(np.array([m[0] for m in mx2])[order], np.array([m[0] for m in my])[order],
               color="0.6", lw=1.2, zorder=1)
    ax[1].set_xlabel("$\\eta/L_2$  (L2 ratio -- MIS-matched to Linf attack)")
    ax[1].set_ylabel("AutoAttack robust acc (Linf 8/255)")
    ax[1].set_title(f"Threat-MISMATCHED: anti-predicts\nPearson $={pear(etaL2, aa):+.2f}$", fontsize=10.5)
    ax[1].grid(alpha=.25)

    # Panel C: robust overfitting as an eta/L collapse (trajectory)
    tp = sorted(glob.glob(os.path.join(HERE, "results/etaL_trajectory_*.json")))
    if tp:
        traj = json.load(open(tp[-1]))
        for n in (0, 1000000):
            s = sorted(traj[str(n)], key=lambda r: r["epoch"])
            s = [r for r in s if r["epoch"] >= 8]                 # drop noisy warmup
            ep = [r["epoch"] for r in s]; e = [r["etaL"] for r in s]
            ax[2].plot(ep, e, marker="o", ms=3, color=DOSE_C[n], lw=1.8, label=DOSE_L[n])
        ax[2].set_xlabel("epoch"); ax[2].set_ylabel("$\\eta/L_2$")
        ax[2].set_title("Robust overfitting = $\\eta/L$ collapse\n(baseline falls late; +1M holds)", fontsize=10.5)
        ax[2].legend(fontsize=8.5, loc="upper right"); ax[2].grid(alpha=.25)

    fig.suptitle("Diffusion data obeys the threat-matched $\\eta/L$ law (fair best-checkpoint comparison)",
                 fontsize=12, y=1.02)
    fig.tight_layout()
    out = os.path.join(FIG, "etaL_law.pdf")
    fig.savefig(out, bbox_inches="tight"); fig.savefig(out.replace(".pdf", ".png"), dpi=150, bbox_inches="tight")
    print("# wrote", out, "| matched r=%.3f mismatched r=%.3f" % (pear(etaL1, aa), pear(etaL2, aa)))


if __name__ == "__main__":
    main()
