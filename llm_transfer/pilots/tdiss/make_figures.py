#!/usr/bin/env python
"""T-DISS figures: (1) R_q vs r2 scatter + M vs r2 + C vs r2; (2) gauge sweep (AUROC of M vs R2
across c,b); (3) ASR(eps) & certified-fraction curves; (4) local-linearity. Saves PNGs to results/."""
import os, json, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")


def load_jsonl(p):
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


def main():
    p1 = {r["id"]: r for r in load_jsonl(os.path.join(RES, "phase1.jsonl"))}
    p2 = {r["id"]: r for r in load_jsonl(os.path.join(RES, "phase2.jsonl"))}
    ids = [i for i in p1 if i in p2 and p1[i]["category"] == "harmful"]
    l2max = max(float(x) for x in list(p2.values())[0]["l2_succ"].keys())
    r2 = np.array([p2[i]["r2"] if p2[i]["r2"] is not None else l2max * 2 for i in ids])
    R2 = np.array([p1[i]["R2"] for i in ids])
    M = np.array([p1[i]["M"] for i in ids])
    C = np.array([p1[i]["C_refuse_frac"] for i in ids])

    # Fig 1: three scatter panels
    fig, ax = plt.subplots(1, 3, figsize=(13, 4))
    for a, (v, name) in zip(ax, [(R2, "R_2 = M/||grad||_2 (ratio)"), (M, "M (raw margin)"),
                                 (C, "C (paraphrase consistency)")]):
        a.scatter(v, r2, s=12, alpha=0.4)
        rho = stats.spearmanr(v, r2).correlation
        a.set_xlabel(name); a.set_ylabel("PE-PGD L2 radius r_2")
        a.set_title(f"Spearman = {rho:+.3f}")
    fig.suptitle("T-DISS: what predicts per-prompt jailbreak radius r_2 (larger = more robust)")
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "fig1_predictors_vs_radius.png"), dpi=130)
    plt.close(fig)

    # Fig 2: gauge sweep
    g = json.load(open(os.path.join(RES, "gauge.json"))) if os.path.exists(os.path.join(RES, "gauge.json")) else None
    if g:
        fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        scales = sorted(g["scale_sweep"].keys(), key=float)
        aM = [g["scale_sweep"][c]["fixedacc_M"] for c in scales]
        aR = [g["scale_sweep"][c]["fixedacc_R2"] for c in scales]
        ax[0].plot([float(c) for c in scales], aM, "o-", label="raw M")
        ax[0].plot([float(c) for c in scales], aR, "s-", label="ratio R_2")
        ax[0].set_xscale("log"); ax[0].set_xlabel("logit scale c (temperature)")
        ax[0].set_ylabel("fixed-threshold balanced acc"); ax[0].set_title("Gauge: scale sweep")
        ax[0].legend(); ax[0].axhline(0.5, ls=":", c="gray")
        biases = sorted(g["bias_sweep"].keys(), key=float)
        bM = [g["bias_sweep"][b]["fixedacc_M"] for b in biases]
        bR = [g["bias_sweep"][b]["fixedacc_R2"] for b in biases]
        ax[1].plot([float(b) for b in biases], bM, "o-", label="raw M")
        ax[1].plot([float(b) for b in biases], bR, "s-", label="ratio R_2")
        ax[1].set_xlabel("refusal-token logit bias b"); ax[1].set_ylabel("AUROC")
        ax[1].set_title("Gauge: bias sweep"); ax[1].legend(); ax[1].axhline(0.5, ls=":", c="gray")
        fig.suptitle("Gauge test: raw M's ranking MOVES under logit rescale/bias; R_2 is invariant")
        fig.tight_layout()
        fig.savefig(os.path.join(RES, "fig2_gauge_sweep.png"), dpi=130)
        plt.close(fig)

    # Fig 3: ASR(eps) and certified fraction CF(eps)=P(R2<eps)
    ladder = sorted(float(x) for x in list(p2.values())[0]["l2_succ"].keys())
    asr = []
    for eps in ladder:
        s = [p2[i]["l2_succ"].get(str(eps)) for i in ids]
        s = [x for x in s if x is not None]
        # success is monotone-encoded: a prompt with r2<=eps counts as jailbroken
        jb = np.mean([(p2[i]["r2"] is not None and p2[i]["r2"] <= eps) for i in ids])
        asr.append(jb)
    cf = [np.mean(R2 < eps) for eps in ladder]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(ladder, asr, "o-", label="empirical ASR(eps) (PE-PGD)")
    ax.plot(ladder, cf, "s--", label="certified fraction P(R_2<eps)")
    ax.set_xlabel("L2 budget eps"); ax.set_ylabel("fraction jailbroken")
    ax.set_title("Attack-free certified fraction vs empirical ASR"); ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "fig3_asr_vs_cf.png"), dpi=130)
    plt.close(fig)

    # Fig 4: local linearity
    mk = os.path.join(RES, "masking.json")
    if os.path.exists(mk):
        m = json.load(open(mk))
        ll = m.get("local_linearity", [])
        if ll:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot([x["norm"] for x in ll], [x["mean_rel_gap"] for x in ll], "o-")
            ax.set_xlabel("||delta||_2"); ax.set_ylabel("mean rel. Taylor gap")
            ax.set_title("Local linearity of M along attack direction (small = affine, no masking)")
            fig.tight_layout()
            fig.savefig(os.path.join(RES, "fig4_local_linearity.png"), dpi=130)
            plt.close(fig)

    print("figures written to", RES)


if __name__ == "__main__":
    main()
