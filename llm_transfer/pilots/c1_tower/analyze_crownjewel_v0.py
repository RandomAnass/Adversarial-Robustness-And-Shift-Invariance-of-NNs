"""Crown-Jewel v0 analysis + figure.

Reads results/c1_tower/crownjewel_v0.json (per-tower scalars) and per_image_crownjewel_*.pt,
and produces:
  1. Two-axis saturation table (SC and PC across encoders: mean +/- sd, min/max).
  2. Dissociation: cross-tower Spearman(SC, S), Spearman(PC, S), Spearman(SC, radius),
     Spearman(PC, radius), each with bootstrap 95% CI. Prediction: Spearman(eta/L1, radius) +,
     and among ROBUST towers Spearman(anisotropy A, radius) -. One headline recomputed two ways.
  3. Bonus: Spearman(SC, PC).
  4. Figure -> llm_transfer/paper/figures/crownjewel_v0.pdf.

Cross-tower stats have small n (panel size), so CIs are wide by construction; we report them
honestly. Per-image pooled dissociation (radius vs eta/L1 ratio) over robust towers gives a
powered check that sidesteps the small cross-tower n.
"""
import os, json, argparse
import numpy as np
import torch
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS = "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower"
FIGDIR = "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/paper/figures"
ROBUST = {"fare2", "fare4", "tecoa2", "tecoa4", "fare4_b32", "fare4_b16",
          "tecoa4_b32", "tecoa4_b16", "fare4_cnxt", "tecoa4_cnxt"}


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3:
        return float("nan")
    return float(stats.spearmanr(x[m], y[m]).correlation)


def boot_ci(fn, *arrays, n=5000, seed=0):
    rng = np.random.default_rng(seed)
    arrays = [np.asarray(a, float) for a in arrays]
    m = len(arrays[0])
    out = []
    for _ in range(n):
        idx = rng.integers(0, m, m)
        v = fn(*[a[idx] for a in arrays])
        if np.isfinite(v):
            out.append(v)
    if not out:
        return (float("nan"), float("nan"))
    return (float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)))


def load(tag):
    with open(os.path.join(RESULTS, f"crownjewel_{tag}.json")) as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="v0")
    ap.add_argument("--eps", type=float, default=4/255)
    args = ap.parse_args()
    eps_tag = f"{args.eps:.5f}"
    d = load(args.tag)
    rows = d["results"]

    towers = [r["tower"] for r in rows]
    is_robust = np.array([r["tower"] in ROBUST for r in rows])
    SC = np.array([r["sc_pred"] for r in rows])
    SCcos = np.array([r["sc_cos"] for r in rows])
    PC = np.array([r["pc"] for r in rows])
    S = np.array([r["S_apgd"].get(eps_tag, float("nan")) for r in rows])
    etaL1 = np.array([r["eta_over_L1"] for r in rows])
    A = np.array([r["anisotropy_A"] for r in rows])
    rad = np.array([r["robust_radius_mean"] for r in rows])
    clean = np.array([r["clean_acc"] for r in rows])

    report = {"eps": eps_tag, "towers": towers, "n_towers": len(towers)}

    # -------- 1. two-axis saturation --------
    def desc(v):
        return {"mean": float(np.mean(v)), "sd": float(np.std(v)),
                "min": float(np.min(v)), "max": float(np.max(v))}
    report["saturation"] = {
        "shift_consistency_SC": desc(SC),
        "paraphrase_consistency_PC": desc(PC),
        "shift_cos_SCcos": desc(SCcos),
        "robust_acc_S": desc(S),  # the SPREAD axis (contrast)
    }

    # -------- 2. dissociation (cross-tower) --------
    def block(x, y):
        return {"spearman": spearman(x, y), "ci95": boot_ci(spearman, x, y)}
    report["dissociation_crosstower"] = {
        "SC_vs_S": block(SC, S),
        "PC_vs_S": block(PC, S),
        "SC_vs_radius": block(SC, rad),
        "PC_vs_radius": block(PC, rad),
        # PREDICTION (parent finding): eta/L1 predicts robustness; consistencies do not.
        "etaL1_vs_S": block(etaL1, S),
        "etaL1_vs_radius": block(etaL1, rad),
    }
    # anisotropy A ranks robustness AMONG THE ROBUST towers (parent finding, A negative)
    rob = is_robust
    if rob.sum() >= 3:
        report["dissociation_crosstower"]["A_vs_radius_robustonly"] = block(A[rob], rad[rob])
        report["dissociation_crosstower"]["A_vs_S_robustonly"] = block(A[rob], S[rob])
        report["dissociation_crosstower"]["etaL1_vs_radius_robustonly"] = block(etaL1[rob], rad[rob])
        report["dissociation_crosstower"]["n_robust"] = int(rob.sum())

    # -------- headline recomputed two ways: Spearman AND rank-agreement of orderings --------
    def rank_agree(x, y):
        rx = stats.rankdata(x); ry = stats.rankdata(y)
        # fraction of pairs concordant (Kendall-style), independent of Spearman
        n = len(x); conc = 0; tot = 0
        for i in range(n):
            for j in range(i + 1, n):
                if x[i] == x[j] or y[i] == y[j]:
                    continue
                tot += 1
                conc += ((x[i] - x[j]) * (y[i] - y[j]) > 0)
        return conc / tot if tot else float("nan")
    report["headline_two_ways"] = {
        "etaL1_vs_radius_spearman": spearman(etaL1, rad),
        "etaL1_vs_radius_pair_concordance": rank_agree(etaL1, rad),
        "PC_vs_S_spearman": spearman(PC, S),
        "PC_vs_S_pair_concordance": rank_agree(PC, S),
    }

    # -------- 3. bonus: are the two consistencies correlated? --------
    report["bonus_SC_vs_PC"] = block(SC, PC)

    # -------- per-image pooled dissociation over robust towers (powered check) --------
    ratio_ranks, rad_ranks, aniso_ranks = [], [], []
    per_tower_pi = {}
    for r in rows:
        t = r["tower"]
        p = os.path.join(RESULTS, f"per_image_crownjewel_{t}.pt")
        if not os.path.exists(p):
            continue
        pi = torch.load(p, map_location="cpu")
        radp = pi["robust_radius_linf"].numpy()
        r1 = pi["ratio_l1"].numpy()
        aA = pi["anisotropy_A"].numpy()
        per_tower_pi[t] = {
            "n": len(radp),
            "spearman_ratioL1_radius": spearman(r1, radp),
            "spearman_ratioL1_radius_ci95": boot_ci(spearman, r1, radp),
            "floor_frac": float((radp == radp.min()).mean()),
            "radius_uniq": int(len(np.unique(radp))),
        }
        if t in ROBUST:
            ratio_ranks.append(stats.rankdata(r1) / len(r1))
            rad_ranks.append(stats.rankdata(radp) / len(radp))
            aniso_ranks.append(stats.rankdata(aA) / len(aA))
    report["per_image"] = {"per_tower": per_tower_pi}
    if ratio_ranks:
        rr = np.concatenate(ratio_ranks); dd = np.concatenate(rad_ranks)
        aa = np.concatenate(aniso_ranks)
        report["per_image"]["pooled_robust"] = {
            "n": len(rr),
            "spearman_ratioL1_radius": spearman(rr, dd),
            "spearman_ratioL1_radius_ci95": boot_ci(spearman, rr, dd),
            "spearman_anisotropyA_radius": spearman(aa, dd),
            "spearman_anisotropyA_radius_ci95": boot_ci(spearman, aa, dd),
        }

    # -------- sanity checks --------
    report["sanity"] = {
        "robust_acc_le_clean_all": bool(np.all(S <= clean + 1e-9)),
        "pc_self_check_all_one": bool(all(abs(r["pc_self_check"] - 1.0) < 1e-6 for r in rows)),
        "nonrobust_S_near_zero": {r["tower"]: r["S_apgd"].get(eps_tag)
                                  for r in rows if r["tower"] not in ROBUST},
        "fare4_radius_gt_clip": None,
    }
    if "fare4" in towers and "clip" in towers:
        rf = rows[towers.index("fare4")]["robust_radius_mean"]
        rc = rows[towers.index("clip")]["robust_radius_mean"]
        report["sanity"]["fare4_radius_gt_clip"] = bool(rf > rc)
        report["sanity"]["fare4_radius"] = rf
        report["sanity"]["clip_radius"] = rc

    out_path = os.path.join(RESULTS, f"crownjewel_{args.tag}_analysis.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[CJ-analysis] wrote {out_path}")

    # =========================== FIGURE ===========================
    make_figure(towers, is_robust, SC, PC, S, etaL1, A, rad, eps_tag, report)
    print("[CJ-analysis] figure written")
    # console summary
    print("\n== two-axis saturation ==")
    print(f"  SC : mean {SC.mean():.3f} sd {SC.std():.3f}  range [{SC.min():.3f},{SC.max():.3f}]")
    print(f"  PC : mean {PC.mean():.3f} sd {PC.std():.3f}  range [{PC.min():.3f},{PC.max():.3f}]")
    print(f"  S  : mean {S.mean():.3f} sd {S.std():.3f}  range [{S.min():.3f},{S.max():.3f}]  (the SPREAD axis)")
    print("\n== dissociation (cross-tower Spearman [95% CI]) ==")
    for k in ["SC_vs_S", "PC_vs_S", "SC_vs_radius", "PC_vs_radius", "etaL1_vs_S", "etaL1_vs_radius"]:
        b = report["dissociation_crosstower"][k]
        print(f"  {k:18s}: {b['spearman']:+.3f}  CI[{b['ci95'][0]:+.3f},{b['ci95'][1]:+.3f}]")
    if "A_vs_radius_robustonly" in report["dissociation_crosstower"]:
        b = report["dissociation_crosstower"]["A_vs_radius_robustonly"]
        print(f"  {'A_vs_radius(robust)':18s}: {b['spearman']:+.3f}  CI[{b['ci95'][0]:+.3f},{b['ci95'][1]:+.3f}]")
    if "pooled_robust" in report["per_image"]:
        pr = report["per_image"]["pooled_robust"]
        print(f"\n== per-image pooled over robust towers (n={pr['n']}) ==")
        print(f"  ratioL1 vs radius : {pr['spearman_ratioL1_radius']:+.3f} "
              f"CI[{pr['spearman_ratioL1_radius_ci95'][0]:+.3f},{pr['spearman_ratioL1_radius_ci95'][1]:+.3f}]")
        print(f"  anisotropyA vs radius: {pr['spearman_anisotropyA_radius']:+.3f} "
              f"CI[{pr['spearman_anisotropyA_radius_ci95'][0]:+.3f},{pr['spearman_anisotropyA_radius_ci95'][1]:+.3f}]")
    print("\n== sanity ==")
    for k, v in report["sanity"].items():
        print(f"  {k}: {v}")


def make_figure(towers, is_robust, SC, PC, S, etaL1, A, rad, eps_tag, report):
    os.makedirs(FIGDIR, exist_ok=True)
    c_rob, c_non = "#c0392b", "#2c6fbb"
    fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.3))

    # Panel A: two saturated consistency axes vs the spread-out robustness (S).
    for arr, color, lab, mk in [(SC, "#1b7837", "shift-consistency", "o"),
                                (PC, "#762a83", "paraphrase-consistency", "s")]:
        ax[0].scatter(arr, S, c=color, marker=mk, s=70, alpha=0.85, edgecolor="k",
                      linewidth=0.4, label=lab)
    ax[0].set_xlabel("consistency (top-1 unchanged)")
    ax[0].set_ylabel(f"robust acc S (APGD Linf eps={eps_tag})")
    ax[0].set_xlim(0.90, 1.005)
    ax[0].set_title("A. Both invariances saturated;\nrobustness dissociated", fontsize=10)
    d = report["dissociation_crosstower"]
    ax[0].text(0.03, 0.97,
               f"Spearman(SC,S)={d['SC_vs_S']['spearman']:+.2f}\n"
               f"Spearman(PC,S)={d['PC_vs_S']['spearman']:+.2f}",
               transform=ax[0].transAxes, va="top", ha="left", fontsize=8.5,
               bbox=dict(boxstyle="round", fc="w", ec="0.7", alpha=0.9))
    ax[0].legend(fontsize=8, loc="center left")
    ax[0].grid(alpha=0.25)

    # Panel B: eta/L1 DOES predict robustness (the axis the consistencies miss).
    for m, color, lab in [(~is_robust, c_non, "non-robust"), (is_robust, c_rob, "robust (AT)")]:
        ax[1].scatter(etaL1[m], S[m], c=color, s=70, alpha=0.85, edgecolor="k",
                      linewidth=0.4, label=lab)
    ax[1].set_xlabel(r"$\eta/L_1$ (threat-matched, Linf)")
    ax[1].set_ylabel(f"robust acc S (eps={eps_tag})")
    ax[1].set_title("B. $\\eta/L_1$ predicts robustness\n(what the consistencies miss)", fontsize=10)
    ax[1].text(0.03, 0.97,
               f"Spearman($\\eta/L_1$,S)={d['etaL1_vs_S']['spearman']:+.2f}\n"
               f"Spearman($\\eta/L_1$,rad)={d['etaL1_vs_radius']['spearman']:+.2f}",
               transform=ax[1].transAxes, va="top", ha="left", fontsize=8.5,
               bbox=dict(boxstyle="round", fc="w", ec="0.7", alpha=0.9))
    ax[1].legend(fontsize=8, loc="lower right")
    ax[1].grid(alpha=0.25)

    # Panel C: the two consistencies against each other (bonus) + per-tower labels.
    for m, color, lab in [(~is_robust, c_non, "non-robust"), (is_robust, c_rob, "robust (AT)")]:
        ax[2].scatter(SC[m], PC[m], c=color, s=70, alpha=0.85, edgecolor="k",
                      linewidth=0.4, label=lab)
    ax[2].set_xlabel("shift-consistency SC")
    ax[2].set_ylabel("paraphrase-consistency PC")
    ax[2].set_title("C. Visual vs textual invariance\n(both near 1)", fontsize=10)
    b = report["bonus_SC_vs_PC"]
    ax[2].text(0.03, 0.05, f"Spearman(SC,PC)={b['spearman']:+.2f}",
               transform=ax[2].transAxes, va="bottom", ha="left", fontsize=8.5,
               bbox=dict(boxstyle="round", fc="w", ec="0.7", alpha=0.9))
    ax[2].legend(fontsize=8, loc="upper left")
    ax[2].grid(alpha=0.25)

    fig.suptitle("Crown-Jewel v0: visual (shift) and textual (paraphrase) invariance are BOTH "
                 "saturated across zero-shot CLIP encoders,\nyet adversarial robustness is a "
                 "separate axis that $\\eta/L_1$ predicts and neither consistency does "
                 "(ImageNet-100, per-tower points)", fontsize=9.5, y=1.02)
    fig.tight_layout()
    out = os.path.join(FIGDIR, "crownjewel_v0.pdf")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
