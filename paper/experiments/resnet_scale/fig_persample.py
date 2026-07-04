#!/usr/bin/env python3
"""
Figures for the two STABLE per-sample findings (independent of the AutoAttack sample size, so safe to
build before the full-10k re-eval lands):
  F1  within-model certificate: the local first-order ratio eta/L_loc = M/||grad M||_2 predicts each
      point's own DDN l2 radius (per-sample), in every cell -- deepening the cell-mean headline.
  F2  AT inverts the margin<->sensitivity coupling: Spearman(M, ||grad M||_2) is negative under
      standard training and positive after adversarial training, in every cell.
Reads the per-sample npz + persample_summary.json; matches the house style of resnet_analyze.figures().
CPU-only. Usage:  PYTHONNOUSERSITE=1 paper/env/cenv/bin/python fig_persample.py
"""
import os, json, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

RESDIR = os.path.join(os.path.dirname(__file__), "..", "..", "results", "resnet_scale")
FIGDIR = os.path.join(os.path.dirname(__file__), "..", "..", "report", "figures")
ARM_COL = {"standard": "#444444", "blurpool": "#1f77b4", "aps": "#d62728", "aug": "#2ca02c",
           "stdzero": "#999999", "maxpool": "#9467bd", "circular": "#d62728"}
ARM_LAB = {"standard": "standard", "blurpool": "anti-aliased", "aps": "exact (APS)", "aug": "shift-aug",
           "stdzero": "zero-pad", "maxpool": "max-pool"}

def _npz(name):
    d = np.load(os.path.join(RESDIR, name + "_persample.npz")); return {k: d[k] for k in d.files}

def fig_f1():
    summ = json.load(open(os.path.join(RESDIR, "persample_summary.json")))
    fig, ax = plt.subplots(1, 2, figsize=(8.4, 3.6))
    # -- panel A: per-sample density for one representative AT cell --
    name = "c10at_standard_s0"; ps = _npz(name)
    rad, m, g2 = ps["radius"], ps["margin"], ps["gradL2"]
    etaL = m / (g2 + 1e-12); fin = np.isfinite(rad) & (rad < np.inf) & np.isfinite(etaL)
    x, y = etaL[fin], rad[fin]; rho = spearmanr(x, y)[0]
    hb = ax[0].hexbin(x, y, gridsize=34, bins="log", cmap="viridis", mincnt=1)
    lim = [0, np.percentile(np.r_[x, y], 99.5)]
    ax[0].plot(lim, lim, "--", color="0.4", lw=1, label="$y=x$ (first order)")
    ax[0].set_xlim(lim); ax[0].set_ylim(0, np.percentile(y, 99.5))
    ax[0].set_xlabel(r"local $\eta/L = M/\|\nabla M\|_2$"); ax[0].set_ylabel(r"DDN $\ell_2$ radius $r_2$")
    ax[0].set_title(rf"within one adversarially trained model: $\rho_S={rho:+.2f}$", fontsize=9.5)
    ax[0].legend(fontsize=8, loc="upper left"); ax[0].grid(alpha=.25)
    cb = fig.colorbar(hb, ax=ax[0], pad=.02); cb.set_label("points (log)", fontsize=8)
    # -- panel B: within-model rho_S for every cell, grouped std / AT-c10 / AT-c100 --
    groups = [("std_cifar10", 0, "standard\ntraining"), ("at_cifar10", 1, "adversarial\ntraining"),
              ("at_cifar100", 2, "AT\nCIFAR-100")]
    rng = np.random.default_rng(0)
    for gkey, gx, _ in groups:
        for q in summ.get(gkey, {}).get("qa", []):
            ax[1].scatter(gx + rng.uniform(-.13, .13), q["spearman"], s=42,
                          color=ARM_COL.get(q["arm"], "#888"), edgecolor="k", linewidths=.5, alpha=.9, zorder=3)
    ax[1].set_xticks([g[1] for g in groups]); ax[1].set_xticklabels([g[2] for g in groups], fontsize=8.5)
    ax[1].set_ylim(0.85, 1.0); ax[1].set_ylabel(r"within-model $\rho_S(\eta/L_{\mathrm{loc}},\, r_2)$")
    ax[1].set_title("holds in every model", fontsize=9.5); ax[1].grid(alpha=.25, axis="y")
    # arm legend
    seen = {}
    for arm in ["standard", "blurpool", "aps", "aug", "stdzero", "maxpool"]:
        seen[arm] = ax[1].scatter([], [], s=42, color=ARM_COL[arm], edgecolor="k", linewidths=.5, label=ARM_LAB[arm])
    ax[1].legend(fontsize=7, loc="lower right", ncol=2, framealpha=.9)
    fig.tight_layout(); fn = os.path.join(FIGDIR, "resnet_persample_certificate.pdf")
    fig.savefig(fn, bbox_inches="tight"); plt.close(fig); print(f"# wrote {fn}")

def fig_f2():
    summ = json.load(open(os.path.join(RESDIR, "persample_summary.json")))
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    groups = [("std_cifar10", 0, "standard\ntraining"), ("at_cifar10", 1, "adversarial\ntraining"),
              ("at_cifar100", 2, "AT\nCIFAR-100")]
    rng = np.random.default_rng(1)
    for gkey, gx, _ in groups:
        for q in summ.get(gkey, {}).get("qc", []):
            ax.scatter(gx + rng.uniform(-.14, .14), q["rho"], s=46,
                       color=ARM_COL.get(q["arm"], "#888"), edgecolor="k", linewidths=.5, alpha=.9, zorder=3)
    ax.axhline(0, color="k", lw=.9)
    ax.set_xticks([g[1] for g in groups]); ax.set_xticklabels([g[2] for g in groups], fontsize=9)
    ax.set_ylim(-0.74, 0.80); ax.set_xlim(-0.45, 2.45)
    ax.set_ylabel(r"within-model $\rho_S(M,\ \|\nabla M\|_2)$")
    ax.set_title("adversarial training inverts the\nmargin--sensitivity coupling", fontsize=10)
    ax.grid(alpha=.25, axis="y")
    # interpretation cues placed in the empty band around 0 (clear of the data clusters)
    ax.text(0, -0.24, "margin &\nrobustness\nreinforce", ha="center", va="center", fontsize=7, color="0.35")
    ax.text(1, 0.26, "margin bought by\nraising sensitivity", ha="center", va="center", fontsize=7, color="0.35")
    fig.tight_layout(); fn = os.path.join(FIGDIR, "resnet_persample_signflip.pdf")
    fig.savefig(fn, bbox_inches="tight"); plt.close(fig); print(f"# wrote {fn}")

if __name__ == "__main__":
    os.makedirs(FIGDIR, exist_ok=True)
    fig_f1(); fig_f2()
