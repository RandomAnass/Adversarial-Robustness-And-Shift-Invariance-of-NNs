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

def load(path=None):
    if path is None:
        # prefer the uncapped full-10k AutoAttack eval (the figure in the paper, matched Pearson +0.88);
        # earlier 512-sample runs are superseded and give a slightly different value.
        cands = sorted(glob.glob(os.path.join(RESDIR, "at_cifar_linf_full10k_*.json")))
        if not cands:
            cands = sorted(glob.glob(os.path.join(RESDIR, "at_*.json")) +
                           glob.glob(os.path.join(RESDIR, "cifar_at_*_*.json")))
        if not cands: sys.exit("no AT JSON found")
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

def fig_predict(results, celld, fn, aakey, matchkey, matchlab, aalab):
    fig, ax = plt.subplots(1, 2, figsize=(8.2, 3.6))
    for xi, (key, lab) in enumerate([(matchkey, matchlab), ("consist", "shift-consistency")]):
        for r in results:
            ax[xi].scatter(r.get(key, np.nan), r.get(aakey, np.nan), s=14, alpha=0.30,
                           color=ARM_COLOR[r["arm"]], marker=W_MARKER.get(r["w"], "o"), linewidths=0)
        xs, ys = [], []
        for d in celld.values():
            ax[xi].scatter(d[key], d[aakey], s=70, color=ARM_COLOR[d["arm"]],
                           marker=W_MARKER.get(d["w"], "o"), edgecolor="k", linewidths=0.6, zorder=3)
            xs.append(d[key]); ys.append(d[aakey])
        p, s = corr(xs, ys)
        ax[xi].set_xlabel(lab); ax[xi].set_ylabel(aalab)
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
    prim = aa_specs[0]; aakey = "aa_" + prim[0]; pnorm = prim[1]          # primary (threat-matched) AA spec
    matchdual = "dec_L1" if pnorm == "Linf" else "dec_L2"                 # dual norm of the training threat
    missdual  = "dec_L2" if pnorm == "Linf" else "dec_L1"
    for r in results:
        r["match"] = (r["dec_margin"] / r[matchdual]) if r.get(matchdual) else float("nan")
        r["miss"]  = (r["dec_margin"] / r[missdual]) if r.get(missdual) else float("nan")
    celld = agg(results); cm = list(celld.values()); os.makedirs(FIGDIR, exist_ok=True)
    aa_names = [s[0] for s in aa_specs]
    rec = data.get("recipe", {}); tag = f"{rec.get('dataset','cifar')}_{rec.get('norm','linf')}"
    nsym = r"\ell_\infty" if pnorm == "Linf" else r"\ell_2"
    dn = r"\|\nabla M\|_1" if pnorm == "Linf" else r"\|\nabla M\|_2"
    dno = r"\|\nabla M\|_2" if pnorm == "Linf" else r"\|\nabla M\|_1"
    aalab = f"AutoAttack robust acc (${nsym}={prim[2]:.3g}$)"; matchlab = f"matched ratio $\\eta/{dn}$"
    print(f"# {tag}: primary AA = {prim[0]} ({pnorm}); threat-matched ratio = eta/{dn}")

    print("\n## Correlations (per-seed) vs primary AutoAttack:")
    for key, lab in [("match", f"MATCHED eta/{dn}"), ("miss", f"mismatched eta/{dno}"),
                     ("rr_l2", "robust radius L2"), ("consist", "consistency")]:
        p, s = corr([r.get(key, np.nan) for r in results], [r.get(aakey, np.nan) for r in results])
        print(f"  {lab:30s} vs AA : Pearson {p:+.3f}  Spearman {s:+.3f}")

    print("\n## Gradient-masking check (AutoAttack must be <= PGD):")
    for d in cm:
        for n in aa_names:
            pg, aa = d.get("pgd_" + n), d.get("aa_" + n)
            if pg is not None and aa is not None and np.isfinite(aa) and np.isfinite(pg):
                flag = "" if aa <= pg + 1e-6 else "  <-- AA>PGD (suspicious)"
                print(f"  {d['arm']:9s} w{d['w']} {n:11s}: PGD {pg:.3f}  AA {aa:.3f}{flag}")

    print("\n## Within-width decomposition vs standard:")
    for w in sorted({d["w"] for d in cm}):
        base = celld[("standard", w)]
        for a in ["blurpool", "circular", "aug"]:
            d = celld[(a, w)]
            dm = np.log(d["dec_margin"] / base["dec_margin"]); dL = np.log(d["dec_L2"] / base["dec_L2"])
            print(f"  w={w} {a:9s}: Dlog margin {dm:+.3f}  Dlog L {dL:+.3f}  Dlog(eta/L) {dm-dL:+.3f}  "
                  f"(AA {d.get(aakey, float('nan')):.3f} vs {base.get(aakey, float('nan')):.3f})")

    predict_name = "cifar_at_predict.pdf" if tag == "cifar_linf" else f"at_predict_{tag}.pdf"
    fig_predict(results, celld, os.path.join(FIGDIR, predict_name), aakey, "match", matchlab, aalab)
    fig_decomp(celld, os.path.join(FIGDIR, f"at_decomp_{tag}.pdf"))

    widths = sorted({d["w"] for d in cm}); arms = ["standard", "blurpool", "circular", "aug"]
    aacols = " & ".join("AA(" + n.replace("_", " ") + ")" for n in aa_names)
    L = [r"\begin{tabular}{ll cc " + "c" * len(aa_names) + r" ccc}", r"\toprule",
         r"arm & $w$ & clean & consist. & " + aacols + r" & $r_2$ & $\eta$ & $\eta/L_2$ \\", r"\midrule"]
    for w in widths:
        for a in arms:
            d = celld[(a, w)]
            aav = " & ".join(f"{d.get('aa_'+n, float('nan')):.3f}" for n in aa_names)
            L.append(f"{ARM_LABEL[a]} & {w} & {d['clean']:.3f} & {d['consist']:.3f} & {aav} & "
                     f"{d['rr_l2']:.3f} & {d['dec_margin']:.3f} & {d['dec_etaL']:.3f} \\\\")
        L.append(r"\midrule")
    L[-1] = r"\bottomrule"; L.append(r"\end{tabular}")
    open(os.path.join(RESDIR, f"at_table_{tag}.tex"), "w").write("\n".join(L))
    print(f"\n## LaTeX table -> results/at_table_{tag}.tex\n"); print("\n".join(L))

if __name__ == "__main__":
    main()
