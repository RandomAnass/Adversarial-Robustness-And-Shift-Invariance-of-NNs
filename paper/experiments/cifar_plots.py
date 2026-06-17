#!/usr/bin/env python3
"""
Plots + analysis for the capacity-matched CIFAR-10 dissection (consumes the JSON written by
cifar_dissection.py). Produces:
  fig 1  cifar_etaL_vs_radius.pdf  -- eta/L predicts the robust radius; shift-consistency does not
  fig 2  cifar_decomposition.pdf   -- margin vs Lipschitz decomposition of the radius gap vs `standard`
  stdout -- correlations, a gradient-masking (PGD vs AutoAttack) check, and a LaTeX results table.

Run: paper/env/cenv/bin/python paper/experiments/cifar_plots.py [path/to/results.json]
"""
import sys, os, glob, json, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

RESDIR = os.path.join(os.path.dirname(__file__), "..", "results")
FIGDIR = os.path.join(os.path.dirname(__file__), "..", "report", "figures")
ARM_LABEL = {"standard": "standard", "blurpool": "anti-aliased", "circular": "exact cyclic", "aug": "shift-aug"}
ARM_COLOR = {"standard": "#444444", "blurpool": "#1f77b4", "circular": "#d62728", "aug": "#2ca02c"}
W_MARKER = {32: "o", 64: "s"}

def load(path=None):
    if path is None:
        cands = sorted(glob.glob(os.path.join(RESDIR, "cifar_dissection_full_*.json")))
        if not cands: cands = sorted(glob.glob(os.path.join(RESDIR, "cifar_dissection_*.json")))
        if not cands: sys.exit("no results JSON found")
        path = cands[-1]
    print(f"# results: {path}")
    return json.load(open(path)), path

def agg(results):
    """mean/std over seeds per (arm,w). AA averaged over the seeds that have it."""
    cells = {}
    for r in results:
        cells.setdefault((r["arm"], r["w"]), []).append(r)
    out = {}
    for key, rs in cells.items():
        d = {"arm": key[0], "w": key[1], "params": rs[0]["params"], "nseed": len(rs)}
        for k in ["clean", "consist", "rr_l2", "dec_margin", "dec_L2", "dec_L1", "dec_etaL", "dec_rho2"]:
            v = [x[k] for x in rs if k in x and x[k] is not None]
            d[k] = float(np.mean(v)) if v else float("nan")
            d[k + "_sd"] = float(np.std(v)) if len(v) > 1 else 0.0
        aakeys = set()
        for x in rs:                                # union over the cell (AA runs on seed0 only)
            aakeys |= {k for k in x if k.startswith("aa_") or k.startswith("pgd_")}
        for k in aakeys:
            v = [x[k] for x in rs if x.get(k) is not None]
            d[k] = float(np.mean(v)) if v else float("nan")
        out[key] = d
    return out

def corr(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3: return float("nan"), float("nan")
    return float(pearsonr(x[m], y[m])[0]), float(spearmanr(x[m], y[m])[0])

def fig_predictor(results, celld, fn):
    """Two panels: eta/L vs robust radius (predicts) and consistency vs robust radius (does not)."""
    fig, ax = plt.subplots(1, 2, figsize=(8.2, 3.6))
    # per-seed points (faint) + per-cell means (bold)
    for (xi, key, lab) in [(0, "dec_etaL", r"margin/Lipschitz ratio $\eta/L$"),
                           (1, "consist", "shift-consistency")]:
        for r in results:
            ax[xi].scatter(r.get(key, np.nan), r["rr_l2"], s=14, alpha=0.30,
                           color=ARM_COLOR[r["arm"]], marker=W_MARKER.get(r["w"], "o"), linewidths=0)
        xs, ys = [], []
        for d in celld.values():
            ax[xi].scatter(d[key], d["rr_l2"], s=70, color=ARM_COLOR[d["arm"]],
                           marker=W_MARKER.get(d["w"], "o"), edgecolor="k", linewidths=0.6, zorder=3)
            xs.append(d[key]); ys.append(d["rr_l2"])
        p, s = corr(xs, ys)
        ax[xi].set_xlabel(lab); ax[xi].set_ylabel(r"$\ell_2$ robust radius $r_2$")
        ax[xi].set_title(f"Pearson {p:+.2f},  Spearman {s:+.2f}", fontsize=10)
        ax[xi].grid(alpha=0.25)
    # legend
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", color="w", markerfacecolor=ARM_COLOR[a], markeredgecolor="k",
                      markersize=8, label=ARM_LABEL[a]) for a in ["standard", "blurpool", "circular", "aug"]]
    handles += [Line2D([], [], marker=W_MARKER[w], color="w", markerfacecolor="#999", markeredgecolor="k",
                       markersize=8, label=f"width {w}") for w in sorted(W_MARKER)]
    ax[0].legend(handles=handles, fontsize=7.5, loc="upper left", framealpha=0.9)
    fig.tight_layout(); fig.savefig(fn, bbox_inches="tight"); plt.close(fig)
    print(f"# wrote {fn}")

def fig_decomposition(celld, fn):
    """Per width, bars of Dlog(margin) and Dlog(L2) vs the `standard` arm (Dlog(eta/L)=Dlog m - Dlog L)."""
    widths = sorted({d["w"] for d in celld.values()})
    arms = ["blurpool", "circular", "aug"]
    fig, axes = plt.subplots(1, len(widths), figsize=(4.2 * len(widths), 3.6), squeeze=False)
    for wi, w in enumerate(widths):
        ax = axes[0][wi]
        base = celld[("standard", w)]
        dm = [np.log(celld[(a, w)]["dec_margin"] / base["dec_margin"]) for a in arms]
        dL = [np.log(celld[(a, w)]["dec_L2"] / base["dec_L2"]) for a in arms]
        dr = [m - l for m, l in zip(dm, dL)]
        x = np.arange(len(arms)); bw = 0.27
        ax.bar(x - bw, dm, bw, label=r"$\Delta\log$ margin $\eta$", color="#2ca02c")
        ax.bar(x, [-v for v in dL], bw, label=r"$-\Delta\log$ Lipschitz $L$", color="#1f77b4")
        ax.bar(x + bw, dr, bw, label=r"$\Delta\log(\eta/L)$", color="#d62728")
        ax.axhline(0, color="k", lw=0.8)
        ax.set_xticks(x); ax.set_xticklabels([ARM_LABEL[a] for a in arms], fontsize=9)
        ax.set_title(f"width {w}", fontsize=10); ax.grid(alpha=0.25, axis="y")
        if wi == 0: ax.set_ylabel("log-ratio vs standard\n(higher = more robust)")
    axes[0][0].legend(fontsize=8, loc="best")
    fig.tight_layout(); fig.savefig(fn, bbox_inches="tight"); plt.close(fig)
    print(f"# wrote {fn}")

def latex_table(celld, aa_specs):
    aa_names = [s[0] for s in aa_specs]
    widths = sorted({d["w"] for d in celld.values()})
    arms = ["standard", "blurpool", "circular", "aug"]
    lines = [r"\begin{tabular}{ll r ccc ccc " + "c" * len(aa_names) + "}", r"\toprule",
             r"arm & $w$ & params & clean & consist. & $r_2$ & margin & $L$ & $\eta/L$ & "
             + " & ".join("AA " + n.replace("_", " ") for n in aa_names) + r" \\", r"\midrule"]
    for w in widths:
        for a in arms:
            d = celld[(a, w)]
            aa = " & ".join(f"{d.get('aa_'+n, float('nan')):.3f}" for n in aa_names)
            lines.append(f"{ARM_LABEL[a]} & {w} & {d['params']} & {d['clean']:.3f} & {d['consist']:.3f} & "
                         f"{d['rr_l2']:.3f} & {d['dec_margin']:.3f} & {d['dec_L2']:.3f} & {d['dec_etaL']:.3f} & {aa} \\\\")
        lines.append(r"\midrule")
    lines[-1] = r"\bottomrule"; lines.append(r"\end{tabular}")
    return "\n".join(lines)

def main():
    data, path = load(sys.argv[1] if len(sys.argv) > 1 else None)
    results, aa_specs = data["results"], data["aa_specs"]
    celld = agg(results)
    os.makedirs(FIGDIR, exist_ok=True)

    print("\n## Correlations (across all per-seed points):")
    for key, lab in [("dec_etaL", "eta/L"), ("dec_rho2", "rho2 (per-pt certificate)"), ("consist", "consistency")]:
        p, s = corr([r.get(key, np.nan) for r in results], [r["rr_l2"] for r in results])
        print(f"  {lab:28s} vs rr_L2 : Pearson {p:+.3f}  Spearman {s:+.3f}")
    print("## Correlations (across (arm,width) cell means):")
    cm = list(celld.values())
    for key, lab in [("dec_etaL", "eta/L"), ("dec_rho2", "rho2"), ("consist", "consistency")]:
        p, s = corr([d[key] for d in cm], [d["rr_l2"] for d in cm])
        print(f"  {lab:28s} vs rr_L2 : Pearson {p:+.3f}  Spearman {s:+.3f}")

    print("\n## Gradient-masking check (robust acc; AutoAttack must be <= PGD):")
    for d in cm:
        for n in [s[0] for s in aa_specs]:
            pg, aa = d.get("pgd_" + n), d.get("aa_" + n)
            if pg is not None and aa is not None and np.isfinite(aa):
                flag = "" if aa <= pg + 1e-6 else "  <-- AA>PGD (suspicious)"
                print(f"  {d['arm']:9s} w{d['w']} {n:11s}: PGD {pg:.3f}  AA {aa:.3f}{flag}")

    print("\n## Within-width decomposition vs standard (Dlog r ~ Dlog margin - Dlog L):")
    for w in sorted({d["w"] for d in cm}):
        base = celld[("standard", w)]
        for a in ["blurpool", "circular", "aug"]:
            d = celld[(a, w)]
            dm = np.log(d["dec_margin"] / base["dec_margin"]); dL = np.log(d["dec_L2"] / base["dec_L2"])
            print(f"  w={w} {a:9s}: Dlog margin {dm:+.3f}  Dlog L {dL:+.3f}  Dlog(eta/L) {dm-dL:+.3f}  "
                  f"(rr {d['rr_l2']:.3f} vs {base['rr_l2']:.3f})")

    fig_predictor(results, celld, os.path.join(FIGDIR, "cifar_etaL_vs_radius.pdf"))
    fig_decomposition(celld, os.path.join(FIGDIR, "cifar_decomposition.pdf"))
    tex = latex_table(celld, aa_specs)
    open(os.path.join(RESDIR, "cifar_table.tex"), "w").write(tex)
    print("\n## LaTeX table -> results/cifar_table.tex\n"); print(tex)

if __name__ == "__main__":
    main()
