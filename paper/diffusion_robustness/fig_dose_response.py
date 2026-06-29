#!/usr/bin/env python3
"""
Dose-response figure for the diffusion-data MECHANISM finding: as EDM synthetic data is added,
adversarial robustness (AutoAttack, DDN L2 radius) RISES while the logit MARGIN FALLS and the
local input-sensitivity / Lipschitz L FALLS FASTER -> the certified-radius gain r ~= margin/L is
entirely a SMOOTHNESS (lower-L) effect, not a margin effect.

Reads, in order of preference: the v2 multi-seed aggregate (mean+/-std, results/diff_pilot_v2_*.json
or per-cell results/partial/v2sweep_*.json) -> error bars; else the 1-seed stage2 partials.
Writes figures/dose_response.pdf (+ .png).
Run: PYTHONNOUSERSITE=1 ../env/cenv/bin/python fig_dose_response.py
"""
import os, json, glob, math, collections
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures"); os.makedirs(FIG, exist_ok=True)
AAK = ("aa_Linf_8_255", "aa")


def aa_of(d):
    for k in AAK:
        if k in d:
            return d[k]
    return float("nan")


def load_cells():
    """Return {n_syn: {metric: [values over seeds]}} from v2 partials if present, else stage2."""
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    v2 = glob.glob(os.path.join(HERE, "results/partial/v2sweep_*.json"))
    v2_doses = {json.load(open(p))["n_syn"] for p in v2} if v2 else set()
    stage2 = glob.glob(os.path.join(HERE, "results/partial/stage2_syn*_e40.json"))
    if len(v2_doses) >= 4:                       # use v2 multi-seed only once the full sweep is in
        src, label = v2, f"v2 multi-seed (n={len(v2)//max(1,len(v2_doses))} seeds)"
    else:
        src, label = stage2, "stage-2 (1 seed; v2 multi-seed pending)"
    for p in src:
        d = json.load(open(p)); n = d["n_syn"]
        by[n]["clean"].append(d["clean"]); by[n]["aa"].append(aa_of(d))
        by[n]["rr"].append(d["rr_l2"]); by[n]["margin"].append(d["dec_margin"])
        by[n]["L2"].append(d["dec_L2"]); by[n]["L1"].append(d["dec_L1"])
        by[n]["etaL"].append(d["dec_etaL"]); by[n]["consist"].append(d["consist"])
    return by, label


def ms(by, n, k):
    v = np.array(by[n][k], float); return v.mean(), (v.std() if len(v) > 1 else 0.0)


def main():
    by, label = load_cells()
    ns = sorted(by.keys())
    x = np.arange(len(ns)); xt = [("0" if n == 0 else f"{n//1000}k" if n < 1_000_000 else f"{n//1_000_000}M") for n in ns]
    def series(k): return np.array([ms(by, n, k)[0] for n in ns]), np.array([ms(by, n, k)[1] for n in ns])

    fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.0))
    # Panel 1: robustness rises
    for k, lab, c, mk in [("aa", "AutoAttack robust acc", "#d62728", "o"), ("rr", "DDN $\\ell_2$ radius", "#1f77b4", "s")]:
        m, s = series(k); ax[0].errorbar(x, m, yerr=s, marker=mk, color=c, lw=2, capsize=3, label=lab)
    ax[0].set_title("Robustness rises with synthetic data", fontsize=11)
    ax[0].set_ylabel("robustness"); ax[0].legend(fontsize=9, loc="lower right")

    # Panel 2: margin DOWN, L DOWN more (twin axes)
    mm, ms_ = series("margin"); Lm, Ls = series("L2")
    ax[1].errorbar(x, mm, yerr=ms_, marker="o", color="#2ca02c", lw=2, capsize=3, label="margin $\\eta$")
    ax[1].errorbar(x, Lm, yerr=Ls, marker="s", color="#9467bd", lw=2, capsize=3, label="sensitivity $L_2=\\Vert\\nabla M\\Vert$")
    ax[1].set_title("Margin falls; sensitivity $L$ falls faster", fontsize=11)
    ax[1].set_ylabel("logit-space magnitude"); ax[1].legend(fontsize=9, loc="upper right")

    # Panel 3: decomposition d log r = d log margin - d log L (vs +0 baseline)
    base = {k: ms(by, ns[0], k)[0] for k in ("margin", "L2", "rr")}
    dm = [math.log(ms(by, n, "margin")[0] / base["margin"]) for n in ns]
    dL = [math.log(ms(by, n, "L2")[0] / base["L2"]) for n in ns]
    dr = [math.log(ms(by, n, "rr")[0] / base["rr"]) for n in ns]
    w = 0.38
    ax[2].bar(x - w / 2, dm, w, color="#2ca02c", label="$\\Delta\\log$ margin (numerator)")
    ax[2].bar(x + w / 2, [-v for v in dL], w, color="#9467bd", label="$-\\Delta\\log L$ (denominator)")
    ax[2].plot(x, dr, "k--o", lw=1.8, label="$\\Delta\\log$ radius (net)")
    ax[2].axhline(0, color="0.5", lw=0.8)
    ax[2].set_title("The gain is the $-\\Delta\\log L$ (smoothness) term", fontsize=11)
    ax[2].set_ylabel("$\\Delta\\log$ vs real-only"); ax[2].legend(fontsize=8.5, loc="upper left")

    for a in ax:
        a.set_xticks(x); a.set_xticklabels(xt); a.set_xlabel("synthetic images added"); a.grid(alpha=.25)
    fig.suptitle(f"Diffusion data buys smoothness, not margin  [{label}]", fontsize=12, y=1.02)
    fig.tight_layout()
    out = os.path.join(FIG, "dose_response.pdf")
    fig.savefig(out, bbox_inches="tight"); fig.savefig(out.replace(".pdf", ".png"), dpi=150, bbox_inches="tight")
    print("# wrote", out, "| source:", label, "| doses:", xt)


if __name__ == "__main__":
    main()
