"""Crown-Jewel HARDENED analysis + figure (pre-registered; extends analyze_crownjewel_v0.py).

Reads results/c1_tower/crownjewel_hardened.json (per-tower scalars) + per_image_crownjewelH_*.pt
and executes the pre-registered analysis (design section 3.4), each cross-tower stat with a
bootstrap 95% CI (5000 resamples):

  (A) two-column saturation-vs-spread table (mean/sd/min/max per cell; spread_ratio per modality)
  (B) dissociation: cross-tower Spearman of SC/PC/etaL1 vs S and vs S_text, + SC/PC vs radius
  (C) prediction (KEY new test): does eta/L1 predict BOTH adversarial cells (S and S_text) while
      neither consistency does? A vs radius and A vs S_text among robust towers.
  (D) partial correlations controlling clean_acc (Spearman via rank-residualization)
  (E) per-image pooled: eta/L1 (per-image) vs radius; NEW cross-modal worst-template-margin vs radius
  (F) two-way recompute of >=1 headline (Spearman AND pairwise rank concordance)

Sanity gates (all reported): S<=clean_acc; S_text<=a_avg<=a_ref<=1; PC(ref,ref)=1; non-robust S~0;
fare4 radius>clip radius; simclip4/simclip2 S>0 and cluster with robust towers.

Figure -> paper/figures/crownjewel_hardened.pdf (design 3.5): a 2x2 saturation-vs-spread strip
(SC,PC | S,S_text) + an eta/L1-vs-adversarial-cells scatter with the two Spearman values annotated.
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
          "tecoa4_b32", "tecoa4_b16", "fare4_cnxt", "tecoa4_cnxt",
          "simclip4", "simclip2", "leaf_L_text"}


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


def block(x, y):
    return {"spearman": spearman(x, y), "ci95": list(boot_ci(spearman, x, y)), "n": int(len(x))}


def partial_spearman(x, y, z):
    """Spearman partial correlation of x,y controlling z, via rank-residualization.
    Rank-transform all three, regress out z (rank) from x and y (rank), correlate residuals."""
    x, y, z = [stats.rankdata(np.asarray(a, float)) for a in (x, y, z)]
    def resid(a, b):
        b1 = np.c_[np.ones_like(b), b]
        beta = np.linalg.lstsq(b1, a, rcond=None)[0]
        return a - b1 @ beta
    rx, ry = resid(x, z), resid(y, z)
    if np.std(rx) < 1e-12 or np.std(ry) < 1e-12:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def partial_block(x, y, z):
    fn = lambda a, b, c: partial_spearman(a, b, c)
    return {"partial_spearman": partial_spearman(x, y, z),
            "ci95": list(boot_ci(fn, x, y, z)), "n": int(len(x))}


def rank_agree(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x); conc = 0; tot = 0
    for i in range(n):
        for j in range(i + 1, n):
            if x[i] == x[j] or y[i] == y[j]:
                continue
            tot += 1
            conc += ((x[i] - x[j]) * (y[i] - y[j]) > 0)
    return conc / tot if tot else float("nan")


def load(tag):
    with open(os.path.join(RESULTS, f"crownjewel_{tag}.json")) as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="hardened")
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
    S = np.array([(r["S_apgd"].get(eps_tag) if r["S_apgd"].get(eps_tag) is not None else np.nan)
                  for r in rows])
    S_text = np.array([r["S_text"] for r in rows])
    S_text_k20 = np.array([r.get("S_text_k20", np.nan) for r in rows])
    a_avg = np.array([r["a_avg"] for r in rows])
    etaL1 = np.array([r["eta_over_L1"] for r in rows])
    A = np.array([r["anisotropy_A"] for r in rows])
    rad = np.array([r["robust_radius_mean"] for r in rows])
    clean = np.array([r["clean_acc"] for r in rows])

    report = {"eps": eps_tag, "towers": towers, "n_towers": len(towers),
              "n_robust": int(is_robust.sum()), "n_nonrobust": int((~is_robust).sum())}

    # ---------- (A) two-column saturation vs spread ----------
    def desc(v):
        v = np.asarray(v, float); v = v[np.isfinite(v)]
        return {"mean": float(np.mean(v)), "sd": float(np.std(v)),
                "min": float(np.min(v)), "max": float(np.max(v)), "n": int(len(v))}
    sat = {
        "IMAGE_invariance_SC": desc(SC),
        "TEXT_invariance_PC": desc(PC),
        "IMAGE_adversarial_S": desc(S),
        "TEXT_adversarial_S_text": desc(S_text),
        "shift_cos_SCcos": desc(SCcos),
        "S_text_k20": desc(S_text_k20),
    }
    sd_SC, sd_PC = sat["IMAGE_invariance_SC"]["sd"], sat["TEXT_invariance_PC"]["sd"]
    sd_S, sd_St = sat["IMAGE_adversarial_S"]["sd"], sat["TEXT_adversarial_S_text"]["sd"]
    report["A_saturation_vs_spread"] = {
        "cells": sat,
        "spread_ratio_image_S_over_SC": (sd_S / sd_SC) if sd_SC > 0 else float("inf"),
        "spread_ratio_text_Stext_over_PC": (sd_St / sd_PC) if sd_PC > 0 else float("inf"),
    }

    # ---------- (B) dissociation (cross-tower Spearman) ----------
    report["B_dissociation"] = {
        "SC_vs_S": block(SC, S), "PC_vs_S": block(PC, S),
        "PC_vs_S_text": block(PC, S_text), "SC_vs_S_text": block(SC, S_text),
        "SC_vs_radius": block(SC, rad), "PC_vs_radius": block(PC, rad),
    }

    # ---------- (C) prediction (the KEY new test) ----------
    report["C_prediction"] = {
        "etaL1_vs_S": block(etaL1, S),
        "etaL1_vs_radius": block(etaL1, rad),
        "etaL1_vs_S_text": block(etaL1, S_text),   # <-- does eta/L1 predict TEXT-adv too?
    }
    rob = is_robust
    if rob.sum() >= 3:
        report["C_prediction"]["A_vs_radius_robustonly"] = block(A[rob], rad[rob])
        report["C_prediction"]["A_vs_S_text_robustonly"] = block(A[rob], S_text[rob])
        report["C_prediction"]["etaL1_vs_S_text_robustonly"] = block(etaL1[rob], S_text[rob])
        report["C_prediction"]["etaL1_vs_radius_robustonly"] = block(etaL1[rob], rad[rob])

    # ---------- (D) partial correlations controlling clean_acc ----------
    report["D_partial_control_clean"] = {
        "etaL1_vs_S__clean": partial_block(etaL1, S, clean),
        "PC_vs_S__clean": partial_block(PC, S, clean),
        "etaL1_vs_S_text__clean": partial_block(etaL1, S_text, clean),
        "PC_vs_S_text__clean": partial_block(PC, S_text, clean),
    }

    # ---------- (F) two-way headline recompute ----------
    report["F_headline_two_ways"] = {
        "etaL1_vs_S_text_spearman": spearman(etaL1, S_text),
        "etaL1_vs_S_text_pair_concordance": rank_agree(etaL1, S_text),
        "PC_vs_S_text_spearman": spearman(PC, S_text),
        "PC_vs_S_text_pair_concordance": rank_agree(PC, S_text),
        "etaL1_vs_S_spearman": spearman(etaL1, S),
        "etaL1_vs_S_pair_concordance": rank_agree(etaL1, S),
    }

    # ---------- K=20 sensitivity check ----------
    finite = np.isfinite(S_text_k20)
    report["K20_sensitivity"] = {
        "S_text_k11_mean": float(np.mean(S_text)),
        "S_text_k20_mean": float(np.mean(S_text_k20[finite])) if finite.any() else float("nan"),
        "monotone_down_all_towers": bool(np.all(S_text_k20[finite] <= S_text[finite] + 1e-9)),
        "n_towers_k20_le_k11": int(np.sum(S_text_k20[finite] <= S_text[finite] + 1e-9)),
        "spearman_ranking_stable_k11_k20": spearman(S_text[finite], S_text_k20[finite]),
        "per_tower": {t: {"k11": float(s11), "k20": float(s20)}
                      for t, s11, s20 in zip(towers, S_text, S_text_k20)},
    }

    # ---------- bonus ----------
    report["bonus_SC_vs_PC"] = block(SC, PC)

    # ---------- (E) per-image pooled (powered) ----------
    ratio_ranks, rad_ranks, aniso_ranks, wm_ranks = [], [], [], []
    wm_ranks_rad = []
    per_tower_pi = {}
    for r in rows:
        t = r["tower"]
        p = os.path.join(RESULTS, f"per_image_crownjewelH_{t}.pt")
        if not os.path.exists(p):
            continue
        pi = torch.load(p, map_location="cpu")
        radp = pi["robust_radius_linf"].numpy()
        r1 = pi["ratio_l1"].numpy()
        aA = pi["anisotropy_A"].numpy()
        wm = pi["worst_margin_text"].numpy() if "worst_margin_text" in pi else np.full_like(radp, np.nan)
        per_tower_pi[t] = {
            "n": int(len(radp)),
            "spearman_ratioL1_radius": spearman(r1, radp),
            "spearman_ratioL1_radius_ci95": list(boot_ci(spearman, r1, radp)),
            "spearman_worstmargintext_radius": spearman(wm, radp),
            "floor_frac": float((radp == radp.min()).mean()),
            "radius_uniq": int(len(np.unique(radp))),
        }
        if t in ROBUST:
            ratio_ranks.append(stats.rankdata(r1) / len(r1))
            rad_ranks.append(stats.rankdata(radp) / len(radp))
            aniso_ranks.append(stats.rankdata(aA) / len(aA))
            mfin = np.isfinite(wm)
            if mfin.sum() >= 3:
                wm_ranks.append(stats.rankdata(wm[mfin]) / mfin.sum())
                wm_ranks_rad.append(stats.rankdata(radp[mfin]) / mfin.sum())
    report["E_per_image"] = {"per_tower": per_tower_pi}
    if ratio_ranks:
        rr = np.concatenate(ratio_ranks); dd = np.concatenate(rad_ranks); aa = np.concatenate(aniso_ranks)
        report["E_per_image"]["pooled_robust"] = {
            "n": int(len(rr)),
            "spearman_ratioL1_radius": spearman(rr, dd),
            "spearman_ratioL1_radius_ci95": list(boot_ci(spearman, rr, dd)),
            "spearman_anisotropyA_radius": spearman(aa, dd),
            "spearman_anisotropyA_radius_ci95": list(boot_ci(spearman, aa, dd)),
        }
    if wm_ranks:
        wr = np.concatenate(wm_ranks); wd = np.concatenate(wm_ranks_rad)
        report["E_per_image"]["crossmodal_pooled_robust"] = {
            "n": int(len(wr)),
            "spearman_worstmargintext_radius": spearman(wr, wd),
            "spearman_worstmargintext_radius_ci95": list(boot_ci(spearman, wr, wd)),
            "note": "cross-modal per-image coupling (worst-template text margin vs Linf robust "
                    "radius), pooled over robust towers, within-tower rank-normalized; reported "
                    "without over-claim.",
        }

    # ---------- sanity gates ----------
    S_ok = np.array([(np.isnan(s) or s <= c + 1e-9) for s, c in zip(S, clean)])
    order_ok = {}
    for r in rows:
        order_ok[r["tower"]] = bool(
            r["S_text"] <= r["a_avg"] + 1e-9 <= r["a_ref_text"] + 1e-9 and r["a_ref_text"] <= 1 + 1e-9)
    sanity = {
        "S_le_clean_all": bool(np.all(S_ok)),
        "S_le_clean_per_tower": {t: bool(o) for t, o in zip(towers, S_ok)},
        "S_text_ordering_all": bool(all(order_ok.values())),
        "S_text_ordering_per_tower": order_ok,
        "pc_self_check_all_one": bool(all(abs(r["pc_self_check"] - 1.0) < 1e-6 for r in rows)),
        "nonrobust_S_near_zero": {r["tower"]: r["S_apgd"].get(eps_tag)
                                  for r in rows if r["tower"] not in ROBUST},
        "targeted_aa_complete": {r["tower"]: r.get("targeted_aa_complete", {}).get(eps_tag)
                                 for r in rows},
    }
    if "fare4" in towers and "clip" in towers:
        rf = rows[towers.index("fare4")]["robust_radius_mean"]
        rc = rows[towers.index("clip")]["robust_radius_mean"]
        sanity["fare4_radius_gt_clip"] = bool(rf > rc)
        sanity["fare4_radius"] = rf; sanity["clip_radius"] = rc
    for sc_t in ["simclip4", "simclip2"]:
        if sc_t in towers:
            rr = rows[towers.index(sc_t)]
            sval = rr["S_apgd"].get(eps_tag)
            sanity[f"{sc_t}_S_gt_zero"] = bool(sval is not None and sval > 0)
            sanity[f"{sc_t}_S"] = sval
    report["sanity"] = sanity

    out_path = os.path.join(RESULTS, f"crownjewel_{args.tag}_analysis.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[CJ-H-analysis] wrote {out_path}")

    make_figure(towers, is_robust, SC, PC, S, S_text, etaL1, PC, rad, eps_tag, report, args.tag)
    print("[CJ-H-analysis] figure written")

    # console summary
    print("\n== (A) saturation vs spread ==")
    for k, v in sat.items():
        print(f"  {k:26s}: mean {v['mean']:.3f} sd {v['sd']:.3f} range [{v['min']:.3f},{v['max']:.3f}]")
    print(f"  spread_ratio image (sd S / sd SC)       : "
          f"{report['A_saturation_vs_spread']['spread_ratio_image_S_over_SC']:.1f}x")
    print(f"  spread_ratio text  (sd S_text / sd PC)  : "
          f"{report['A_saturation_vs_spread']['spread_ratio_text_Stext_over_PC']:.1f}x")
    print("\n== (B) dissociation (cross-tower Spearman [95% CI]) ==")
    for k, b in report["B_dissociation"].items():
        print(f"  {k:16s}: {b['spearman']:+.3f}  CI[{b['ci95'][0]:+.3f},{b['ci95'][1]:+.3f}]")
    print("\n== (C) prediction ==")
    for k, b in report["C_prediction"].items():
        print(f"  {k:26s}: {b['spearman']:+.3f}  CI[{b['ci95'][0]:+.3f},{b['ci95'][1]:+.3f}]")
    print("\n== (D) partial (control clean_acc) ==")
    for k, b in report["D_partial_control_clean"].items():
        print(f"  {k:26s}: {b['partial_spearman']:+.3f}  CI[{b['ci95'][0]:+.3f},{b['ci95'][1]:+.3f}]")
    if "pooled_robust" in report["E_per_image"]:
        pr = report["E_per_image"]["pooled_robust"]
        print(f"\n== (E) per-image pooled over robust (n={pr['n']}) ==")
        print(f"  ratioL1 vs radius : {pr['spearman_ratioL1_radius']:+.3f} "
              f"CI[{pr['spearman_ratioL1_radius_ci95'][0]:+.3f},{pr['spearman_ratioL1_radius_ci95'][1]:+.3f}]")
    if "crossmodal_pooled_robust" in report["E_per_image"]:
        cm = report["E_per_image"]["crossmodal_pooled_robust"]
        print(f"  cross-modal worst-text-margin vs radius (n={cm['n']}): "
              f"{cm['spearman_worstmargintext_radius']:+.3f} "
              f"CI[{cm['spearman_worstmargintext_radius_ci95'][0]:+.3f},"
              f"{cm['spearman_worstmargintext_radius_ci95'][1]:+.3f}]")
    print("\n== K=20 sensitivity ==")
    ks = report["K20_sensitivity"]
    print(f"  S_text mean K11={ks['S_text_k11_mean']:.3f} K20={ks['S_text_k20_mean']:.3f}; "
          f"monotone-down all towers: {ks['monotone_down_all_towers']} "
          f"({ks['n_towers_k20_le_k11']}/{len(towers)}); ranking stability rho="
          f"{ks['spearman_ranking_stable_k11_k20']:+.3f}")
    print("\n== sanity gates ==")
    for k in ["S_le_clean_all", "S_text_ordering_all", "pc_self_check_all_one",
              "fare4_radius_gt_clip", "simclip4_S_gt_zero", "simclip2_S_gt_zero"]:
        if k in sanity:
            print(f"  {k}: {sanity[k]}")
    print(f"  nonrobust S: {sanity['nonrobust_S_near_zero']}")
    print(f"  targeted_aa_complete: {sanity['targeted_aa_complete']}")


def make_figure(towers, is_robust, SC, PC, S, S_text, etaL1, PC2, rad, eps_tag, report, tag):
    os.makedirs(FIGDIR, exist_ok=True)
    c_rob, c_non = "#c0392b", "#2c6fbb"
    fig = plt.figure(figsize=(13.2, 5.0))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1.0], wspace=0.28)

    # ---- Left: the 2x2 as a saturation-vs-spread strip (SC, PC | S, S_text) ----
    axL = fig.add_subplot(gs[0, 0])
    cells = [("SC  (image invariance)", SC, "#1b7837"),
             ("PC  (text invariance)", PC, "#762a83"),
             ("S   (image adversarial)", S, "#d95f02"),
             (r"$S_{text}$ (text adversarial)", S_text, "#7570b3")]
    ypos = [3, 2, 1, 0]
    rng = np.random.default_rng(0)
    for (lab, vals, col), y in zip(cells, ypos):
        v = np.asarray(vals, float); v = v[np.isfinite(v)]
        jit = (rng.random(len(v)) - 0.5) * 0.28
        axL.scatter(v, np.full(len(v), y) + jit, s=48, c=col, alpha=0.8,
                    edgecolor="k", linewidth=0.3, zorder=3)
        axL.plot([v.min(), v.max()], [y, y], color=col, lw=1.2, alpha=0.5, zorder=1)
        axL.text(-0.02, y, f"sd={v.std():.3f}", ha="right", va="center", fontsize=8, color="0.3")
    axL.axhspan(1.5, 3.5, color="#eef6ee", zorder=0)   # invariance band
    axL.axhspan(-0.5, 1.5, color="#fdf1ea", zorder=0)  # adversarial band
    axL.set_yticks(ypos)
    axL.set_yticklabels([c[0] for c in cells], fontsize=9)
    axL.set_xlim(-0.16, 1.03)
    axL.set_xlabel("metric value in [0,1]  (per-tower points)")
    axL.set_title("A. Both invariance cells saturate; the image-adversarial\n"
                  r"cell (S) spreads wide, the text cell ($S_{text}$) stays narrow", fontsize=10)
    sr = report["A_saturation_vs_spread"]
    axL.text(0.02, 0.02,
             f"spread ratio (image) sd(S)/sd(SC) = {sr['spread_ratio_image_S_over_SC']:.0f}x\n"
             f"spread ratio (text) sd($S_{{text}}$)/sd(PC) = {sr['spread_ratio_text_Stext_over_PC']:.0f}x",
             transform=axL.transAxes, va="bottom", ha="left", fontsize=8.2,
             bbox=dict(boxstyle="round", fc="w", ec="0.7", alpha=0.92))
    axL.grid(axis="x", alpha=0.25)

    # ---- Right: eta/L1 predicts BOTH adversarial cells; PC does not ----
    axR = fig.add_subplot(gs[0, 1])
    # S vs eta/L1
    for m, mk, lab in [(~is_robust, "o", None), (is_robust, "o", None)]:
        pass
    axR.scatter(etaL1[~is_robust], S[~is_robust], marker="o", s=60, facecolor="none",
                edgecolor=c_non, linewidth=1.3, label="S  non-robust")
    axR.scatter(etaL1[is_robust], S[is_robust], marker="o", s=60, c="#d95f02",
                edgecolor="k", linewidth=0.3, alpha=0.85, label="S  robust")
    axR.scatter(etaL1[~is_robust], S_text[~is_robust], marker="^", s=60, facecolor="none",
                edgecolor=c_non, linewidth=1.3, label=r"$S_{text}$  non-robust")
    axR.scatter(etaL1[is_robust], S_text[is_robust], marker="^", s=60, c="#7570b3",
                edgecolor="k", linewidth=0.3, alpha=0.85, label=r"$S_{text}$  robust")
    axR.set_xscale("log")
    axR.set_xlabel(r"$\eta/L_1$ (threat-matched, L$\infty$; log scale)")
    axR.set_ylabel("adversarial robust accuracy")
    axR.set_title(r"B. $\eta/L_1$ predicts the image cell (S), not the text"
                  "\n" r"cell ($S_{text}$); the consistencies predict neither", fontsize=10)
    d = report["C_prediction"]; b = report["B_dissociation"]
    axR.text(0.02, 0.97,
             f"Spearman($\\eta/L_1$, S)      = {d['etaL1_vs_S']['spearman']:+.2f}\n"
             f"Spearman($\\eta/L_1$, $S_{{text}}$) = {d['etaL1_vs_S_text']['spearman']:+.2f}\n"
             f"Spearman(PC, $S_{{text}}$)      = {b['PC_vs_S_text']['spearman']:+.2f}  (both narrow)",
             transform=axR.transAxes, va="top", ha="left", fontsize=8.2,
             bbox=dict(boxstyle="round", fc="w", ec="0.7", alpha=0.92))
    axR.legend(fontsize=7.5, loc="lower right", ncol=2)
    axR.grid(alpha=0.25, which="both")

    fig.suptitle(
        "Crown-Jewel HARDENED: a 2x2 (modality x perturbation) view on zero-shot CLIP. "
        "Visual (shift) and textual (paraphrase) invariance are both saturated across "
        f"{len(towers)} encoders.\nOnly the image-adversarial cell (S) spreads across encoders and is "
        r"predicted by $\eta/L_1$; the text worst-case $S_{text}$ stays narrow, and $\eta/L_1$ is "
        "orthogonal to it once clean accuracy is controlled.", fontsize=9.2, y=1.03)
    out = os.path.join(FIGDIR, f"crownjewel_{tag}.pdf")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
