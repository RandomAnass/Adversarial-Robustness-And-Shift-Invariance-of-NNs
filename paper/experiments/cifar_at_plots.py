#!/usr/bin/env python3
"""
Plots + analysis for the PGD-AT CIFAR-10 dissection (consumes the JSON from cifar_at.py).
Under adversarial training AutoAttack at the standard threshold (Linf 8/255) is informative, so
it becomes the robustness ground truth. Produces:
  fig 1  cifar_at_predict.pdf  -- eta/L (and the robust radius) vs AutoAttack@8/255 robust accuracy
  fig 2  cifar_at_decomp.pdf   -- margin/Lipschitz decomposition vs the standard AT baseline
  stdout -- correlations, the gradient-masking (PGD vs AA) check, and a LaTeX results table.

Run: paper/env/cenv/bin/python paper/experiments/cifar_at_plots.py [path/to/cifar_at_*.json]
"""
import sys, os, glob, json, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

RESDIR = os.path.join(os.path.dirname(__file__), "..", "results")
FIGDIR = os.path.join(os.path.dirname(__file__), "..", "report", "figures")
ARM_LABEL = {"standard": "standard", "blurpool": "anti-aliased", "circular": "exact cyclic", "aug": "shift-aug"}
ARM_COLOR = {"standard": "#444444", "blurpool": "#1f77b4", "circular": "#d62728", "aug": "#2ca02c"}
W_MARKER = {32: "o", 64: "s"}
AA = "aa_Linf_8_255"   # the informative robustness axis under AT

def load(path=None):
    if path is None:
        cands = sorted(glob.glob(os.path.join(RESDIR, "cifar_at_*_*.json")))
        if not cands: sys.exit("no cifar_at JSON found")
        path = cands[-1]
    print(f"# results: {path}")
    return json.load(open(path)), path

def agg(results):
    cells = {}
    for r in results:
        cells.setdefault((r["arm"], r["w"]), []).append(r)
    out = {}
    for key, rs in cells.items():
        d = {"arm": key[0], "w": int(key[1]), "nseed": len(rs)}
        keys = set()
        for x in rs:
            keys |= set(k for k in x if isinstance(x[k], (int, float))
                        and k not in ("w", "seed", "params", "nseed"))
        for k in keys:
            v = [x[k] for x in rs if x.get(k) is not None]
            d[k] = float(np.mean(v)) if v else float("nan")
            d[k + "_sd"] = float(np.std(v)) if len(v) > 1 else 0.0
        out[key] = d
    return out

def corr(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3: return float("nan"), float("nan")
    return float(pearsonr(x[m], y[m])[0]), float(spearmanr(x[m], y[m])[0])

def fig_predict(results, celld, fn):
    fig, ax = plt.subplots(1, 2, figsize=(8.2, 3.6))
    for xi, (key, lab) in enumerate([("etaLinf", r"$\ell_\infty$-matched ratio $\eta/\|\nabla M\|_1$"),
                                     ("consist", "shift-consistency")]):
        for r in results:
            ax[xi].scatter(r.get(key, np.nan), r.get(AA, np.nan), s=14, alpha=0.30,
                           color=ARM_COLOR[r["arm"]], marker=W_MARKER.get(r["w"], "o"), linewidths=0)
        xs, ys = [], []
        for d in celld.values():
            ax[xi].scatter(d[key], d[AA], s=70, color=ARM_COLOR[d["arm"]],
                           marker=W_MARKER.get(d["w"], "o"), edgecolor="k", linewidths=0.6, zorder=3)
            xs.append(d[key]); ys.append(d[AA])
        p, s = corr(xs, ys)
        ax[xi].set_xlabel(lab); ax[xi].set_ylabel(r"AutoAttack robust acc ($\ell_\infty=8/255$)")
        ax[xi].set_title(f"Pearson {p:+.2f},  Spearman {s:+.2f}", fontsize=10); ax[xi].grid(alpha=0.25)
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", color="w", markerfacecolor=ARM_COLOR[a], markeredgecolor="k",
                      markersize=8, label=ARM_LABEL[a]) for a in ["standard", "blurpool", "circular", "aug"]]
    handles += [Line2D([], [], marker=W_MARKER[w], color="w", markerfacecolor="#999", markeredgecolor="k",
                       markersize=8, label=f"width {w}") for w in sorted(W_MARKER)]
    ax[0].legend(handles=handles, fontsize=7.5, loc="best", framealpha=0.9)
    fig.tight_layout(); fig.savefig(fn, bbox_inches="tight"); plt.close(fig); print(f"# wrote {fn}")

def fig_decomp(celld, fn):
    widths = sorted({d["w"] for d in celld.values()}); arms = ["blurpool", "circular", "aug"]
    fig, axes = plt.subplots(1, len(widths), figsize=(4.2 * len(widths), 3.6), squeeze=False)
    for wi, w in enumerate(widths):
        ax = axes[0][wi]; base = celld[("standard", w)]
        dm = [np.log(celld[(a, w)]["dec_margin"] / base["dec_margin"]) for a in arms]
        dL = [np.log(celld[(a, w)]["dec_L2"] / base["dec_L2"]) for a in arms]
        x = np.arange(len(arms)); bw = 0.27
        ax.bar(x - bw, dm, bw, label=r"$\Delta\log$ margin $\eta$", color="#2ca02c")
        ax.bar(x, [-v for v in dL], bw, label=r"$-\Delta\log$ Lipschitz $L$", color="#1f77b4")
        ax.bar(x + bw, [m - l for m, l in zip(dm, dL)], bw, label=r"$\Delta\log(\eta/L)$", color="#d62728")
        ax.axhline(0, color="k", lw=0.8); ax.set_xticks(x)
        ax.set_xticklabels([ARM_LABEL[a] for a in arms], fontsize=9)
        ax.set_title(f"width {w} (AT)", fontsize=10); ax.grid(alpha=0.25, axis="y")
        if wi == 0: ax.set_ylabel("log-ratio vs standard\n(higher = more robust)")
    axes[0][0].legend(fontsize=8, loc="best")
    fig.tight_layout(); fig.savefig(fn, bbox_inches="tight"); plt.close(fig); print(f"# wrote {fn}")

def main():
    data, path = load(sys.argv[1] if len(sys.argv) > 1 else None)
    results, aa_specs = data["results"], data["aa_specs"]
    for r in results:                              # Linf-matched ratio: margin / ||grad M||_1 (Linf dual)
        r["etaLinf"] = (r["dec_margin"] / r["dec_L1"]) if r.get("dec_L1") else float("nan")
    celld = agg(results); cm = list(celld.values()); os.makedirs(FIGDIR, exist_ok=True)
    aa_names = [s[0] for s in aa_specs]

    print("\n## Correlations (across all per-seed points):")
    for key, lab in [("etaLinf", "eta/L_inf (matched)"), ("dec_etaL", "eta/L_2"), ("rr_l2", "robust radius (L2)"), ("consist", "consistency")]:
        p, s = corr([r.get(key, np.nan) for r in results], [r.get(AA, np.nan) for r in results])
        print(f"  {lab:20s} vs AA@8/255 : Pearson {p:+.3f}  Spearman {s:+.3f}")
    p, s = corr([r.get("dec_etaL", np.nan) for r in results], [r["rr_l2"] for r in results])
    print(f"  eta/L            vs rr_L2    : Pearson {p:+.3f}  Spearman {s:+.3f}")

    print("\n## Gradient-masking check (robust acc; AutoAttack must be <= PGD):")
    for d in cm:
        for n in aa_names:
            pg, aa = d.get("pgd_" + n), d.get("aa_" + n)
            if pg is not None and aa is not None and np.isfinite(aa) and np.isfinite(pg):
                flag = "" if aa <= pg + 1e-6 else "  <-- AA>PGD (suspicious)"
                print(f"  {d['arm']:9s} w{d['w']} {n:11s}: PGD {pg:.3f}  AA {aa:.3f}{flag}")

    print("\n## Within-width decomposition vs standard (AT):")
    for w in sorted({d["w"] for d in cm}):
        base = celld[("standard", w)]
        for a in ["blurpool", "circular", "aug"]:
            d = celld[(a, w)]
            dm = np.log(d["dec_margin"] / base["dec_margin"]); dL = np.log(d["dec_L2"] / base["dec_L2"])
            print(f"  w={w} {a:9s}: Dlog margin {dm:+.3f}  Dlog L {dL:+.3f}  Dlog(eta/L) {dm-dL:+.3f}  "
                  f"(AA {d.get(AA, float('nan')):.3f} vs {base.get(AA, float('nan')):.3f}; rr {d['rr_l2']:.3f})")

    fig_predict(results, celld, os.path.join(FIGDIR, "cifar_at_predict.pdf"))
    fig_decomp(celld, os.path.join(FIGDIR, "cifar_at_decomp.pdf"))

    # LaTeX table
    widths = sorted({d["w"] for d in cm}); arms = ["standard", "blurpool", "circular", "aug"]
    L = [r"\begin{tabular}{ll cccc ccc}", r"\toprule",
         r"arm & $w$ & clean & consist. & AA$_{\infty}$ & AA$_{2}$ & $r_2$ & $\eta$ & $\eta/L$ \\", r"\midrule"]
    for w in widths:
        for a in arms:
            d = celld[(a, w)]
            L.append(f"{ARM_LABEL[a]} & {w} & {d['clean']:.3f} & {d['consist']:.3f} & "
                     f"{d.get('aa_Linf_8_255', float('nan')):.3f} & {d.get('aa_L2_0_5', float('nan')):.3f} & "
                     f"{d['rr_l2']:.3f} & {d['dec_margin']:.3f} & {d['dec_etaL']:.3f} \\\\")
        L.append(r"\midrule")
    L[-1] = r"\bottomrule"; L.append(r"\end{tabular}")
    open(os.path.join(RESDIR, "cifar_at_table.tex"), "w").write("\n".join(L))
    print("\n## LaTeX table -> results/cifar_at_table.tex\n"); print("\n".join(L))

if __name__ == "__main__":
    main()
