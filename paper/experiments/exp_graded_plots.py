#!/usr/bin/env python3
"""
Analyse + plot the graded anti-aliasing PGD-AT sweep (exp_graded_antialias.py output).

The graded BlurPool family (Rect-2 -> Bin-7) varies the anti-aliasing strength at NEARLY
FIXED clean accuracy; the exact-cyclic arm is the invariance endpoint. The figure shows the
two regimes in one controlled sweep:
  - across the matched-clean-accuracy anti-aliasing family, robust accuracy and the
    threat-matched eta/L rise together (anti-aliasing helps, through the margin term under
    l_inf AT), while shift-consistency stays ~flat;
  - the exact-cyclic arm has consistency 1.0 yet collapses margin -> eta/L and robustness,
    the harming regime, so shift-consistency is non-monotonic while eta/L tracks robustness.

Writes report/figures/graded_antialias.pdf and prints the verdict numbers.
Run: paper/env/cenv/bin/python paper/experiments/exp_graded_plots.py
"""
import os, json, glob, collections
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

PD = os.path.join(os.path.dirname(__file__), "..", "results", "at_partial", "graded_antialias")
FIG = os.path.join(os.path.dirname(__file__), "..", "report", "figures")
ORDER = ["standard", "blur2", "blur3", "blur5", "blur7", "circular"]
LAB = {"standard": "standard", "blur2": "Rect-2", "blur3": "Tri-3", "blur5": "Bin-5",
       "blur7": "Bin-7", "circular": "exact cyclic"}
# colour ramp: anti-aliasing family in a blue gradient, exact-cyclic in red
COL = {"standard": "#9ecae1", "blur2": "#6baed6", "blur3": "#3182bd", "blur5": "#08519c",
       "blur7": "#08306b", "circular": "#d62728"}


def main():
    rows = [json.load(open(f)) for f in glob.glob(PD + "/*.json")]
    aak = [k for k in rows[0] if k.startswith("aa_")][0]
    for r in rows:
        r["etaL1"] = r["dec_margin"] / r["dec_L1"] if r.get("dec_L1") else np.nan
    by = collections.defaultdict(list)
    for r in rows:
        by[r["arm"]].append(r)

    def m(rs, k):
        v = [x[k] for x in rs if x.get(k) is not None and np.isfinite(x[k])]
        return float(np.mean(v)) if v else np.nan

    fam = [r for r in rows if r["arm"] != "circular"]

    def corr(sub, xk):
        x = np.array([r[xk] for r in sub]); y = np.array([r[aak] for r in sub])
        mm = np.isfinite(x) & np.isfinite(y)
        return pearsonr(x[mm], y[mm])[0]

    print("# graded anti-aliasing verdict")
    print(f"  clean-acc spread, anti-aliasing family: "
          f"{min(m(by[a],'clean') for a in ORDER[:-1]):.3f}-{max(m(by[a],'clean') for a in ORDER[:-1]):.3f}")
    print(f"  circular clean {m(by['circular'],'clean'):.3f}  margin {m(by['circular'],'dec_margin'):.3f} "
          f"(vs standard {m(by['standard'],'dec_margin'):.3f})  AA {m(by['circular'],aak):.3f}")
    for nm, sub in [("family (matched acc)", fam), ("all arms", rows)]:
        print(f"  {nm:20s}: eta/L vs AA {corr(sub,'etaL1'):+.3f}   "
              f"consist vs AA {corr(sub,'consist'):+.3f}   clean vs AA {corr(sub,'clean'):+.3f}")

    fig, ax = plt.subplots(1, 2, figsize=(8.4, 3.7))
    # ---- panel A: eta/L vs AA (predicts) ----
    for a in ORDER:
        rs = by[a]
        ax[0].scatter([r["etaL1"] for r in rs], [r[aak] for r in rs], s=18, alpha=.35,
                      color=COL[a], linewidths=0)
        ax[0].scatter(m(rs, "etaL1"), m(rs, aak), s=95, color=COL[a], edgecolor="k",
                      linewidths=.7, zorder=3, label=LAB[a])
    pall = corr(rows, "etaL1")
    ax[0].set_xlabel(r"threat-matched $\eta/L=\eta/\|\nabla M\|_1$")
    ax[0].set_ylabel(r"AutoAttack robust acc ($\ell_\infty{=}8/255$)")
    ax[0].set_title(rf"$\eta/L$ tracks robustness (Pearson ${pall:+.2f}$)", fontsize=9.5)
    ax[0].grid(alpha=.25); ax[0].legend(fontsize=7, loc="lower right", ncol=2, framealpha=.9)
    # ---- panel B: shift-consistency vs AA (non-monotonic) ----
    for a in ORDER:
        rs = by[a]
        ax[1].scatter([r["consist"] for r in rs], [r[aak] for r in rs], s=18, alpha=.35,
                      color=COL[a], linewidths=0)
        ax[1].scatter(m(rs, "consist"), m(rs, aak), s=95, color=COL[a], edgecolor="k",
                      linewidths=.7, zorder=3)
    ax[1].annotate("anti-aliasing family\n(clean acc matched)", (0.804, 0.40), (0.70, 0.345),
                   fontsize=7, color="0.3", ha="center",
                   arrowprops=dict(arrowstyle="->", color="0.5", lw=.8))
    ax[1].annotate("exact cyclic:\nconsistency 1.0,\nmargin collapses", (1.0, 0.278), (0.86, 0.30),
                   fontsize=7, color="#d62728", ha="center",
                   arrowprops=dict(arrowstyle="->", color="#d62728", lw=.8))
    ax[1].set_xlabel(r"circular-shift consistency")
    ax[1].set_ylabel(r"AutoAttack robust acc")
    ax[1].set_title("shift-consistency does not", fontsize=9.5)
    ax[1].grid(alpha=.25)
    fig.tight_layout()
    os.makedirs(FIG, exist_ok=True)
    fn = os.path.join(FIG, "graded_antialias.pdf")
    fig.savefig(fn, bbox_inches="tight"); plt.close(fig)
    print(f"# wrote {fn}")


if __name__ == "__main__":
    main()
