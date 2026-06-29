#!/usr/bin/env python3
"""
Dose-response figure for the diffusion-data robustness finding (GAUGE-HONEST version).

The v2 scale-control showed the headline gains are GAUGE-INVARIANT (eta/L, the DDN L2 certified
radius, and AutoAttack all rise, monotone, with diminishing returns), but the raw "margin falls /
L falls faster" attribution is GAUGE-DEPENDENT: it survives a logit-norm anchor yet FLIPS sign under
an NLL/temperature anchor. So the figure leads with the gauge-free conclusion and then *shows* the
attribution flipping, rather than asserting a "smoothness not margin" story that does not survive.

Panels:
  A  Robustness rises (gauge-invariant): AutoAttack, DDN l2 radius, eta/L vs synthetic count.
  B  Gains are monotone and saturate: dlog(eta/L), dlog(radius), dAA -- ~flat past 500k.
  C  The margin-vs-L split is gauge-dependent: margin_ctrl & L_ctrl under the logit-norm anchor
     (both negative, L lower) vs the NLL anchor (both positive, margin higher). Only eta/L is gauge-free.

Reads the v2 multi-seed partials (results/partial/v2sweep_*.json) for mean+/-std error bars; falls
back to the 1-seed stage2 partials. Writes figures/dose_response.pdf (+ .png).
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
        if k in d and d[k] is not None:
            return d[k]
    return float("nan")


def load_cells():
    """Return ({n_syn: {metric: [values over seeds]}}, label) from v2 partials if present, else stage2."""
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    v2 = glob.glob(os.path.join(HERE, "results/partial/v2sweep_*.json"))
    v2_doses = {json.load(open(p))["n_syn"] for p in v2} if v2 else set()
    stage2 = glob.glob(os.path.join(HERE, "results/partial/stage2_syn*_e40.json"))
    if len(v2_doses) >= 4:
        src = v2; label = f"v2 multi-seed ({len(v2)//max(1,len(v2_doses))} seeds)"
    else:
        src = stage2; label = "stage-2 (1 seed; v2 multi-seed pending)"
    for p in src:
        d = json.load(open(p)); n = d["n_syn"]
        by[n]["clean"].append(d["clean"]); by[n]["aa"].append(aa_of(d))
        by[n]["rr"].append(d["rr_l2"]); by[n]["margin"].append(d["dec_margin"])
        by[n]["L2"].append(d["dec_L2"]); by[n]["L1"].append(d["dec_L1"])
        by[n]["etaL"].append(d["dec_etaL"])
        by[n]["s_norm"].append(d.get("dec_logit_scale", float("nan")))   # logit-norm anchor scale
        by[n]["s_nll"].append(d.get("temp_nll", float("nan")))           # NLL/temperature anchor scale
    return by, label


def ms(by, n, k):
    v = np.array([x for x in by[n][k] if x is not None], float)
    return (np.nanmean(v), (np.nanstd(v) if len(v) > 1 else 0.0))


def main():
    by, label = load_cells()
    ns = sorted(by.keys())
    x = np.arange(len(ns))
    xt = [("0" if n == 0 else f"{n//1000}k" if n < 1_000_000 else f"{n//1_000_000}M") for n in ns]
    mean = lambda k: np.array([ms(by, n, k)[0] for n in ns])
    std = lambda k: np.array([ms(by, n, k)[1] for n in ns])

    fig, ax = plt.subplots(1, 3, figsize=(14.0, 4.1))

    # ---- Panel A: gauge-invariant robustness rises ----
    for k, lab, c, mk in [("aa", "AutoAttack robust acc", "#d62728", "o"),
                          ("rr", "DDN $\\ell_2$ radius", "#1f77b4", "s"),
                          ("etaL", "$\\eta/L$ (margin/Lipschitz)", "#2ca02c", "^")]:
        ax[0].errorbar(x, mean(k), yerr=std(k), marker=mk, color=c, lw=2, capsize=3, label=lab)
    ax[0].set_title("Robustness rises (gauge-invariant)", fontsize=11)
    ax[0].set_ylabel("gauge-free quantity"); ax[0].legend(fontsize=8.5, loc="lower right")

    # ---- Panel B: monotone + saturating gains (log-change vs +0 baseline) ----
    b = {k: mean(k)[0] for k in ("etaL", "rr")}
    dlog_etaL = np.array([math.log(ms(by, n, "etaL")[0] / b["etaL"]) for n in ns])
    dlog_rr = np.array([math.log(ms(by, n, "rr")[0] / b["rr"]) for n in ns])
    dAA = mean("aa") - mean("aa")[0]
    ax[1].plot(x, dlog_etaL, marker="^", color="#2ca02c", lw=2, label="$\\Delta\\log(\\eta/L)$")
    ax[1].plot(x, dlog_rr, marker="s", color="#1f77b4", lw=2, label="$\\Delta\\log$ radius")
    ax[1].plot(x, dAA, marker="o", color="#d62728", lw=2, label="$\\Delta$ AutoAttack")
    ax[1].axhline(0, color="0.5", lw=0.8)
    ax[1].set_title("Gains are monotone and saturate by 500k", fontsize=11)
    ax[1].set_ylabel("change vs real-only"); ax[1].legend(fontsize=9, loc="lower right")

    # ---- Panel C: the margin-vs-L split is gauge-dependent (flips with the anchor) ----
    # control under anchor s:  margin_ctrl = dlog margin - dlog s ;  L_ctrl = dlog L2 - dlog s
    m0, L0 = mean("margin")[0], mean("L2")[0]
    sn0, st0 = mean("s_norm")[0], mean("s_nll")[0]
    syn = [i for i, n in enumerate(ns) if n > 0]
    def ctrl(anchor):
        s0 = sn0 if anchor == "norm" else st0
        skey = "s_norm" if anchor == "norm" else "s_nll"
        out = {}
        for i in syn:
            n = ns[i]
            dlm = math.log(ms(by, n, "margin")[0] / m0); dlL = math.log(ms(by, n, "L2")[0] / L0)
            dls = math.log(ms(by, n, skey)[0] / s0)
            out[i] = (dlm - dls, dlL - dls)
        return out
    cn, ct = ctrl("norm"), ctrl("nll")
    w = 0.2; xs = np.array(syn, float)
    ax[2].bar(xs - 1.5*w, [cn[i][0] for i in syn], w, color="#2ca02c", label="margin$_{ctrl}$ (logit-norm)")
    ax[2].bar(xs - 0.5*w, [cn[i][1] for i in syn], w, color="#9467bd", label="$L_{ctrl}$ (logit-norm)")
    ax[2].bar(xs + 0.5*w, [ct[i][0] for i in syn], w, color="#2ca02c", alpha=0.45, hatch="//", label="margin$_{ctrl}$ (NLL)")
    ax[2].bar(xs + 1.5*w, [ct[i][1] for i in syn], w, color="#9467bd", alpha=0.45, hatch="//", label="$L_{ctrl}$ (NLL)")
    ax[2].axhline(0, color="0.4", lw=0.9)
    ax[2].set_title("Margin-vs-$L$ split flips with the gauge anchor", fontsize=11)
    ax[2].set_ylabel("$\\Delta\\log$ (anchored)"); ax[2].legend(fontsize=7.3, loc="lower left", ncol=2)
    ax[2].set_xticks(syn)

    for i, a in enumerate(ax):
        a.set_xticks(x); a.set_xticklabels(xt); a.set_xlabel("synthetic images added"); a.grid(alpha=.25)
    fig.suptitle(f"Diffusion data raises gauge-free robustness ($\\eta/L$, radius, AA); the margin-vs-$L$ "
                 f"attribution is gauge-dependent  [{label}]", fontsize=11.5, y=1.03)
    fig.tight_layout()
    out = os.path.join(FIG, "dose_response.pdf")
    fig.savefig(out, bbox_inches="tight"); fig.savefig(out.replace(".pdf", ".png"), dpi=150, bbox_inches="tight")
    print("# wrote", out, "| source:", label, "| doses:", xt)


if __name__ == "__main__":
    main()
