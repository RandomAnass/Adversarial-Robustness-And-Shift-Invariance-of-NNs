#!/usr/bin/env python
"""B2 figures: (1) rho_G distribution + orbit-flip rate, (2) the trade-off (invariance vs
rho_G / flip-rate), (3) the budget-law invariant-ASR(eps) curve, (4) two-axis rho_G vs eta/L.
Reads results/peritem.jsonl. Saves PNGs to figures/.
"""
import os, json, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)


def load():
    rows = []
    for l in open(os.path.join(RES, "peritem.jsonl")):
        r = json.loads(l)
        if "per_dose" in r and "error" not in r:
            rows.append(r)
    return rows


def doses_of(rows):
    return sorted({float(k) for k in rows[0]["per_dose"].keys()})


def rho_enc(r, d, sentinel):
    v = r["per_dose"][str(d)]["rho_G_emb"]
    return v if math.isfinite(v) else sentinel


def main():
    rows = load()
    doses = doses_of(rows)
    fams = sorted({r["family"] for r in rows})
    COL = {"sentiment": "#1f77b4", "nli": "#ff7f0e", "safety": "#2ca02c"}
    all_emb = [r["per_dose"][str(d)]["rho_G_emb"] for r in rows for d in doses
               if math.isfinite(r["per_dose"][str(d)]["rho_G_emb"])]
    SENT = (max(all_emb) * 1.5) if all_emb else 10.0

    # ---------- Fig 1: rho_G distribution (dose 0) + orbit-flip rate per family ----------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    for fam in fams:
        vals = [r["per_dose"]["0.0"]["rho_G_emb"] for r in rows
                if r["family"] == fam and r["per_dose"]["0.0"]["orbit_flip"]
                and math.isfinite(r["per_dose"]["0.0"]["rho_G_emb"])]
        if vals:
            ax1.hist(vals, bins=25, alpha=0.55, label=f"{fam} (n={len(vals)})", color=COL.get(fam))
    ax1.set_xlabel(r"$\rho_G$  (embedding displacement $\|\Delta e\|_2$)")
    ax1.set_ylabel("orbit-flipped items")
    ax1.set_title(r"(a) $\rho_G$ distribution at dose 0 (excessive-invariance failures)")
    ax1.legend(fontsize=8)
    # orbit-flip rate per family across doses
    for fam in fams:
        fr = [r for r in rows if r["family"] == fam]
        rates = [np.mean([r["per_dose"][str(d)]["orbit_flip"] for r in fr]) for d in doses]
        ax2.plot(doses, rates, "-o", label=fam, color=COL.get(fam))
    all_rates = [np.mean([r["per_dose"][str(d)]["orbit_flip"] for r in rows]) for d in doses]
    ax2.plot(doses, all_rates, "-ks", lw=2.2, label="ALL", zorder=5)
    ax2.set_xlabel("imposed invariance dose")
    ax2.set_ylabel("orbit-flip rate")
    ax2.set_title("(b) dose response is family-dependent (sentiment↑, nli flat, safety↓*)")
    ax2.legend(fontsize=8); ax2.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig1_rhoG_and_fliprate.png"), dpi=140)
    plt.close(fig)

    # ---------- Fig 2: the trade-off -- rho_G shrinks as invariance rises ----------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    # mean rho_G (inf->sentinel) vs dose (lower = smaller room = trade-off)
    for fam in fams:
        fr = [r for r in rows if r["family"] == fam]
        means = [np.mean([rho_enc(r, d, SENT) for r in fr]) for d in doses]
        ax1.plot(doses, means, "-o", label=fam, color=COL.get(fam))
    means_all = [np.mean([rho_enc(r, d, SENT) for r in rows]) for d in doses]
    ax1.plot(doses, means_all, "-ks", lw=2.2, label="ALL", zorder=5)
    ax1.set_xlabel("imposed invariance dose")
    ax1.set_ylabel(r"mean $\rho_G$  (inf $\to$ sentinel %.1f)" % SENT)
    ax1.set_title(r"(a) $\rho_G$ vs imposed invariance (family-dependent; not monotone)")
    ax1.legend(fontsize=8); ax1.grid(alpha=0.3)
    # per-item measured invariance vs rho_G (dose 0): negative slope
    minv = [r["per_dose"]["0.0"]["measured_invariance"] for r in rows]
    rho = [rho_enc(r, doses[0], SENT) for r in rows]
    ax2.scatter(minv, rho, s=6, alpha=0.25, color="#444")
    # binned means
    minv = np.array(minv); rho = np.array(rho)
    try:
        sp = stats.spearmanr(minv, rho)[0]
    except Exception:
        sp = float("nan")
    bins = np.linspace(minv.min(), minv.max(), 8)
    bc = 0.5 * (bins[:-1] + bins[1:])
    bm = [rho[(minv >= bins[i]) & (minv < bins[i + 1])].mean() if ((minv >= bins[i]) & (minv < bins[i + 1])).sum() else np.nan for i in range(len(bins) - 1)]
    ax2.plot(bc, bm, "-ro", lw=2, label=f"binned mean (Spearman={sp:+.2f})")
    ax2.set_xlabel("measured paraphrase-invariance of the model on x (dose 0)")
    ax2.set_ylabel(r"$\rho_G$ (inf$\to$sentinel)")
    ax2.set_title("(b) measured invariance vs room (saturated: weak per-item signal)")
    ax2.legend(fontsize=8); ax2.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig2_tradeoff.png"), dpi=140)
    plt.close(fig)

    # ---------- Fig 3: budget-law invariant-ASR(eps) curve ----------
    fig, ax = plt.subplots(figsize=(6, 4.4))
    for d in [doses[0], doses[-1]]:
        rhos = [r["per_dose"][str(d)]["rho_G_emb"] for r in rows
                if r["per_dose"][str(d)]["orbit_flip"] and math.isfinite(r["per_dose"][str(d)]["rho_G_emb"])]
        hi = (max(rhos) * 1.05) if rhos else 1.0
        eps = np.linspace(0, hi, 40)
        asr = [np.mean([(r["per_dose"][str(d)]["orbit_flip"]
                         and math.isfinite(r["per_dose"][str(d)]["rho_G_emb"])
                         and r["per_dose"][str(d)]["rho_G_emb"] <= e) for r in rows]) for e in eps]
        ax.plot(eps, asr, "-", lw=2, label=f"dose {d}")
    ax.set_xlabel(r"budget $\epsilon$  ($\|\Delta e\|_2$)")
    ax.set_ylabel(r"invariant orbit-flip ASR($\epsilon$) = $P(\rho_G \leq \epsilon)$")
    ax.set_title(r"(c) budget law: a flip succeeds only when $\epsilon \geq \rho_G$")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig3_budget_law.png"), dpi=140)
    plt.close(fig)

    # ---------- Fig 4: two-axis rho_G (invariance) vs eta/L R2 (sensitivity) ----------
    fig, ax = plt.subplots(figsize=(6, 5))
    for fam in fams:
        fr = [r for r in rows if r["family"] == fam and "R2" in r.get("etaL", {})]
        R2 = [abs(r["etaL"]["R2"]) for r in fr]
        rho = [rho_enc(r, doses[0], SENT) for r in fr]
        ax.scatter(R2, rho, s=10, alpha=0.4, label=fam, color=COL.get(fam))
    ax.set_xlabel(r"sensitivity axis  $|\eta/L| = |R_2|$  (score-stability radius)")
    ax.set_ylabel(r"invariance axis  $\rho_G$  (orbit-flip radius)")
    ax.set_title("(d) the two-quantity plane (prop:rhoG): room needed under BOTH")
    ax.set_xscale("log")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig4_two_axis.png"), dpi=140)
    plt.close(fig)

    print("wrote figures ->", FIG)
    for f in ["fig1_rhoG_and_fliprate.png", "fig2_tradeoff.png", "fig3_budget_law.png", "fig4_two_axis.png"]:
        print("  ", f)


if __name__ == "__main__":
    main()
