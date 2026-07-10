"""C1 figures: the dissociation plots.

Fig 1: two-panel scatter over the tower panel.
  Left:  eta/L1 (threat-matched) vs S_apgd  -> predicts (up-slope), annotate Pearson
  Right: shift-consistency SC vs S_apgd      -> does NOT order (flat/anti), annotate Pearson
Fig 2: selection-rule regret bar chart (pick-by eta/L1 / SC / clean vs oracle).
Fig 3: masking audit -- FGSM >= PGD40 >= APGD per tower (grouped bars).
"""
import os, json, argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS = "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower"
FIGDIR = os.path.join(RESULTS, "figures")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="main")
    ap.add_argument("--eps", type=float, default=4/255)
    args = ap.parse_args()
    with open(os.path.join(RESULTS, f"c1_analysis_{args.tag}.json")) as f:
        A = json.load(f)
    pt = A["per_tower"]
    towers = [d["tower"] for d in pt]
    S = np.array([d["S_apgd"] for d in pt])
    etaL1 = np.array([d["eta_over_L1"] for d in pt])
    sc = np.array([d["sc"] for d in pt])
    clean = np.array([d["clean_acc"] for d in pt])
    os.makedirs(FIGDIR, exist_ok=True)
    colors = {"clip": "tab:blue", "fare2": "tab:green", "fare4": "darkgreen",
              "tecoa2": "tab:orange", "tecoa4": "chocolate", "dinov2": "tab:purple",
              "clip_aa": "tab:red"}
    cs = [colors.get(t, "gray") for t in towers]

    # Fig 1: dissociation
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
    pr1 = A["cross_tower_vs_S"]["eta_over_L1"]["pearson"]
    prsc = A["cross_tower_vs_S"]["SC"]["pearson"]
    ax[0].scatter(etaL1, S * 100, c=cs, s=90, zorder=3)
    for t, x, y in zip(towers, etaL1, S * 100):
        ax[0].annotate(t, (x, y), fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax[0].set_xlabel(r"attack-free $\eta/L_1$ (threat-matched, clean images)")
    ax[0].set_ylabel(r"AutoAttack robust acc $S$ (%)  $\varepsilon=%.4f$" % args.eps)
    ax[0].set_title(r"$\eta/L$ predicts robustness  (Pearson $=%.2f$)" % pr1)
    ax[0].grid(alpha=0.3)
    ax[1].scatter(sc, S * 100, c=cs, s=90, zorder=3)
    for t, x, y in zip(towers, sc, S * 100):
        ax[1].annotate(t, (x, y), fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax[1].set_xlabel("shift-consistency SC (clean images)")
    ax[1].set_ylabel(r"AutoAttack robust acc $S$ (%)")
    ax[1].set_title(r"SC does NOT order robustness  (Pearson $=%.2f$)" % prsc)
    ax[1].grid(alpha=0.3)
    fig.suptitle("C1: shift-consistency vs a threat-matched margin-to-Lipschitz ratio "
                 "as attack-free robustness selectors (frozen VLM towers)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, f"c1_dissociation_{args.tag}.png"), dpi=150)
    plt.close(fig)

    # Fig 2: selection regret
    sr = A["selection_regret"]
    keys = ["eta_over_L1", "eta_over_L2", "SC", "clean_acc"]
    labels = [r"pick $\eta/L_1$", r"pick $\eta/L_2$", "pick SC", "pick clean-acc"]
    reg = [sr[k]["regret_pts"] for k in keys]
    picks = [sr[k]["pick"] for k in keys]
    fig2, a2 = plt.subplots(figsize=(6.5, 4))
    bars = a2.bar(labels, reg, color=["tab:green", "tab:olive", "tab:red", "tab:gray"])
    for b, p in zip(bars, picks):
        a2.annotate(p, (b.get_x() + b.get_width() / 2, b.get_height()),
                    ha="center", va="bottom", fontsize=8)
    a2.set_ylabel("robustness regret vs oracle (pts)")
    a2.set_title(f"Selection-rule regret (oracle={sr['oracle_tower']}, S={sr['oracle_S']:.2f})")
    a2.grid(alpha=0.3, axis="y")
    fig2.tight_layout()
    fig2.savefig(os.path.join(FIGDIR, f"c1_regret_{args.tag}.png"), dpi=150)
    plt.close(fig2)

    # Fig 3: masking audit
    fgsm = np.array([d["S_fgsm"] for d in pt]) * 100
    pgd = np.array([d["S_pgd40"] for d in pt]) * 100
    apgd = S * 100
    x = np.arange(len(towers)); w = 0.26
    fig3, a3 = plt.subplots(figsize=(9, 4))
    a3.bar(x - w, fgsm, w, label="FGSM", color="tab:blue")
    a3.bar(x, pgd, w, label="PGD-40", color="tab:orange")
    a3.bar(x + w, apgd, w, label="APGD/AutoAttack", color="tab:red")
    a3.set_xticks(x); a3.set_xticklabels(towers, rotation=30)
    a3.set_ylabel("robust acc (%)")
    a3.set_title("Gradient-masking audit: FGSM $\\geq$ PGD-40 $\\geq$ APGD (per tower)")
    a3.legend(); a3.grid(alpha=0.3, axis="y")
    fig3.tight_layout()
    fig3.savefig(os.path.join(FIGDIR, f"c1_masking_{args.tag}.png"), dpi=150)
    plt.close(fig3)
    print("figures ->", FIGDIR)


if __name__ == "__main__":
    main()
