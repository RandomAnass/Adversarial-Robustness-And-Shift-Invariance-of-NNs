"""Generate the paper's main figures from cached pilot results (CPU only, no GPU).
  F1: VLM tower-level dissociation (eta/L ranks robustness; consistency collapses under AT control).
  F2: VLM per-image dissociation (eta/L orders certified radius, consistency does not) -- HEADLINE.
  F5: LLM eta/L perp rho_G orthogonality scatter.
Out: paper/figures/{fig1_tower,fig2_perimage,fig5_orthogonality}.pdf
Run: PYTHONNOUSERSITE=1 /home/students/.conda/envs/llmtransfer/bin/python make_paper_figs.py
"""
import os, json
import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
C1 = "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower"
B2 = "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/pilots/b2_orbitflip/results"
OUT = os.path.join(HERE, "figures"); os.makedirs(OUT, exist_ok=True)
AT = {"fare2", "fare4", "tecoa2", "tecoa4"}
EPS = "0.00784"
BLUE, ORANGE, GREY = "#2B6CB0", "#C05621", "#8895A3"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 150})


def load_towers():
    rows = json.load(open(os.path.join(C1, "c1_results_main.json")))["results"] + \
           json.load(open(os.path.join(C1, "c1_results_ext.json")))["results"]
    out = []
    for r in rows:
        s = r.get("S_apgd", {}).get(EPS)
        out.append(dict(name=r["tower"], at=r["tower"] in AT, etaL1=r.get("eta_over_L1"),
                        sc=r.get("sc_pred"), sccos=r.get("sc_cos"), S=s))
    return [r for r in out if r["S"] is not None and r["etaL1"] is not None]


def fig1():
    T = load_towers()
    ana = json.load(open(os.path.join(C1, "c1_analysis_extended_eps2.json")))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.6))
    # panel A: eta/L1 vs robust acc
    for r in T:
        c = ORANGE if r["at"] else BLUE
        a1.scatter(r["etaL1"], r["S"], c=c, s=42, edgecolor="w", linewidth=0.6, zorder=3)
    r_all = ana["full_panel"]["eta_over_L1"]["pearson"]
    a1.set_xscale("log")
    a1.set_xlabel(r"$\eta/L_1$ (clean, attack-free)")
    a1.set_ylabel("AutoAttack robust accuracy")
    a1.set_title(f"Tower ranking: Pearson $={r_all:+.2f}$", fontsize=10)
    a1.scatter([], [], c=ORANGE, label="adv. trained"); a1.scatter([], [], c=BLUE, label="non-AT")
    a1.legend(frameon=False, fontsize=8, loc="lower right")
    # panel B: partial corr controlling is-AT
    bars = [("$\\eta/L_1$", ana["partial_etaL1_S_given_isAT"]["value"], BLUE),
            ("cos-consist.", ana["partial_SCcos_S_given_isAT"]["value"], ORANGE),
            ("pred-consist.", ana["full_panel"]["SC_pred"]["pearson"], GREY)]
    xs = np.arange(len(bars))
    a2.bar(xs, [b[1] for b in bars], color=[b[2] for b in bars], width=0.6, edgecolor="w")
    a2.axhline(0, color="k", lw=0.7)
    a2.set_xticks(xs); a2.set_xticklabels([b[0] for b in bars], fontsize=9)
    a2.set_ylabel("corr. with robustness")
    a2.set_title("Controlling for adv. training", fontsize=10)
    a2.set_ylim(-0.1, 0.75)
    for x, b in zip(xs, bars):
        a2.text(x, b[1] + 0.02, f"{b[1]:+.2f}", ha="center", fontsize=8.5)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig1_tower.pdf")); plt.close(fig)
    print("fig1_tower.pdf")


def fig2():
    ratios, radii, scs = [], [], []
    for t in ["fare2", "fare4", "tecoa2", "tecoa4"]:
        d = torch.load(os.path.join(C1, f"per_image_{t}_main.pt"), map_location="cpu")
        ratios.append(d["ratio_l1"].numpy()); radii.append(d["robust_radius_linf"].numpy())
        scs.append(d["sc_pred_per_image"].numpy())
    ratio = np.concatenate(ratios); radius = np.concatenate(radii); sc = np.concatenate(scs)
    sp_r = stats.spearmanr(ratio, radius).correlation
    sp_s = stats.spearmanr(sc, radius).correlation
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.7), sharey=True)
    a1.scatter(ratio, radius * 255, s=12, c=BLUE, alpha=0.35, edgecolor="none")
    a1.set_xlabel(r"per-image $\eta/L_1$"); a1.set_ylabel(r"certified radius ($/255$)")
    a1.set_title(f"Sensitivity ratio: Spearman $={sp_r:+.2f}$", fontsize=10)
    a2.scatter(sc, radius * 255, s=12, c=GREY, alpha=0.35, edgecolor="none")
    a2.set_xlabel("per-image shift-consistency")
    a2.set_title(f"Invariance: Spearman $={sp_s:+.2f}$", fontsize=10)
    fig.suptitle("Per-image dissociation, pooled over robust towers ($n=1200$)", fontsize=11, y=1.02)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig2_perimage.pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"fig2_perimage.pdf  (ratio {sp_r:+.2f} vs consistency {sp_s:+.2f})")


def fig5():
    tm = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(B2, "etaL_taskmargin.jsonl"))}
    peri = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(B2, "peritem.jsonl"))}
    R2, rho = [], []
    for i in tm:
        if i not in peri: continue
        d0 = peri[i]["per_dose"]["0.0"]
        rg = d0.get("rho_G_emb")
        if not d0.get("orbit_flip") or rg in (None, float("inf")): continue
        r2 = tm[i].get("R2")
        if r2 is None or not np.isfinite(r2): continue
        R2.append(r2); rho.append(rg)
    R2, rho = np.array(R2), np.array(rho)
    sp = stats.spearmanr(R2, rho).correlation
    fig, ax = plt.subplots(figsize=(4.6, 3.7))
    ax.scatter(R2, rho, s=16, c=BLUE, alpha=0.4, edgecolor="none")
    ax.set_xlabel(r"sensitivity ratio $\eta/L$ (task margin)")
    ax.set_ylabel(r"excessive-invariance radius $\rho_G$")
    ax.set_title(f"Orthogonal axes in LLMs: Spearman $={sp:+.3f}$", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig5_orthogonality.pdf")); plt.close(fig)
    print(f"fig5_orthogonality.pdf  (n={len(R2)}, Spearman {sp:+.3f})")


def fig3():
    """Weak-attack: consistency correlates with robust acc under FGSM, vanishes under AutoAttack."""
    T = load_towers()
    non = [r for r in T if not r["at"]]
    at = [r for r in T if r["at"]]
    # need FGSM + APGD per tower
    raw = {r["tower"]: r for r in json.load(open(os.path.join(C1, "c1_results_main.json")))["results"]
           + json.load(open(os.path.join(C1, "c1_results_ext.json")))["results"]}
    def get(t, k): return raw[t["name"]].get(k, {}).get(EPS)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
    for ax, key, ttl in [(a1, "S_fgsm", "under FGSM (weak)"), (a2, "S_apgd", "under AutoAttack (strong)")]:
        for r in non:
            ax.scatter(r["sc"], get(r, key), c=BLUE, s=44, edgecolor="w", linewidth=0.6, zorder=3)
        for r in at:
            ax.scatter(r["sc"], get(r, key), c=ORANGE, s=44, edgecolor="w", linewidth=0.6, zorder=3)
        ax.set_xlabel("shift-consistency"); ax.set_title(ttl, fontsize=10)
    # correlation among non-AT
    scn = np.array([r["sc"] for r in non])
    fgsm = np.array([get(r, "S_fgsm") for r in non])
    pr = stats.pearsonr(scn, fgsm)[0]
    a1.set_ylabel("robust accuracy")
    a1.text(0.05, 0.92, f"non-AT: Pearson $={pr:+.2f}$", transform=a1.transAxes, fontsize=9, color=BLUE)
    a2.text(0.05, 0.92, "non-AT: all $=0$ (no signal)", transform=a2.transAxes, fontsize=9, color=BLUE)
    a1.scatter([], [], c=ORANGE, label="adv. trained"); a1.scatter([], [], c=BLUE, label="non-AT")
    a1.legend(frameon=False, fontsize=8, loc="center right")
    fig.suptitle("Invariance looks like robustness only under a weak attack", fontsize=11, y=1.02)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig3_weakattack.pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"fig3_weakattack.pdf (non-AT Pearson(SC,FGSM)={pr:+.2f})")


def fig4():
    """rho_G distribution (token-edit + embedding) over orbit-flip items, by family."""
    peri = [json.loads(l) for l in open(os.path.join(B2, "peritem.jsonl"))]
    fams = {"sentiment": BLUE, "nli": ORANGE, "safety": GREY}
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    for fam, c in fams.items():
        vals = [r["per_dose"]["0.0"]["rho_G_emb"] for r in peri
                if r["family"] == fam and r["per_dose"]["0.0"]["orbit_flip"]
                and np.isfinite(r["per_dose"]["0.0"]["rho_G_emb"])]
        if vals:
            ax.hist(vals, bins=25, alpha=0.55, color=c, label=f"{fam} (n={len(vals)})", density=True)
    ax.set_xlabel(r"orbit-flip radius $\rho_G$ (embedding $\ell_2$)")
    ax.set_ylabel("density"); ax.legend(frameon=False, fontsize=8)
    ax.set_title(r"Measured $\rho_G$: smallest ignored meaning-changing edit", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig4_rhoG.pdf")); plt.close(fig)
    print("fig4_rhoG.pdf")


if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig4(); fig5()
    print("all figures ->", OUT)
