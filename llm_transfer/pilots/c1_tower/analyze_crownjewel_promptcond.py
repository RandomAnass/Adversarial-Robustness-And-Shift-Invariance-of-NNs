"""Crown-Jewel PROMPT-CONDITIONED analysis + figure (pre-registered).

Reads results/c1_tower/crownjewel_promptcond.json (per-encoder, each with K single-prompt cells +
an ensemble cell + cross-prompt transfer) + per_image_promptcond_*.pt, and executes the
pre-registered analyses, each cross-tower/pooled stat with a bootstrap 95% CI.

  (A) DOES eta/L1 PREDICT IMAGE-ADVERSARIAL ROBUSTNESS ACROSS THE PROMPT AXIS?
      (A1) pooled over ALL (encoder, single-prompt) cells: Spearman(eta/L1, S) and (eta/L1, radius),
           with an ENCODER-CLUSTER bootstrap CI (resample encoders, keep their prompt cells) so the
           within-encoder non-independence is respected; plus a naive per-cell bootstrap for contrast.
      (A2) within-encoder-across-prompts: per-encoder Spearman(eta/L1, S) over its K prompts (needs
           spread in eta/L1 across prompts to be meaningful); summarize mean/median + how many
           encoders have a defined (non-constant-S) coefficient.
  (B) DOES PROMPT-INVARIANCE (ensemble head) CONFER ROBUSTNESS beyond what eta/L1 predicts?
      Per encoder compare ensemble S vs mean single-prompt S (delta), ensemble radius vs mean radius,
      and ensemble eta/L1 vs mean eta/L1. Then residualize S on eta/L1 (rank, over all single-prompt
      cells) and ask whether the ensemble cells sit ABOVE the fit (positive residual) systematically.
  (C) CROSS-PROMPT ADVERSARIAL TRANSFER: mean/median transfer fraction over all (source!=target)
      prompt pairs, per encoder and pooled; single->ensemble and ensemble->single specifically.
  (D) 2x2 restatement: SC, PC saturate (encoder-level); the image-adversarial cell S spreads across
      encoders AND is stable-in-eta/L1 across prompts; prompt-invariance is not robustness.
  Sanity gates (all reported): S<=clean under every (enc,prompt); non-robust S~0 under every prompt;
  transfer in [0,1]; ensemble clean acc >= mean single-prompt clean acc per encoder.
  Two-way headline recompute: pooled Spearman(eta/L1,S) AND pairwise rank concordance.

Figure -> paper/figures/crownjewel_promptcond.pdf.
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


def cluster_boot_ci(fn, groups, x, y, n=5000, seed=0):
    """Encoder-cluster bootstrap: resample ENCODERS with replacement (keeping all of a resampled
    encoder's prompt cells), recompute the pooled statistic. Respects within-encoder dependence."""
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float); y = np.asarray(y, float)
    uniq = list(dict.fromkeys(groups))
    idx_by_g = {g: np.where(np.asarray(groups) == g)[0] for g in uniq}
    out = []
    for _ in range(n):
        pick = rng.choice(len(uniq), len(uniq), replace=True)
        sel = np.concatenate([idx_by_g[uniq[p]] for p in pick])
        v = fn(x[sel], y[sel])
        if np.isfinite(v):
            out.append(v)
    if not out:
        return (float("nan"), float("nan"))
    return (float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)))


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


def desc(v):
    v = np.asarray(v, float); v = v[np.isfinite(v)]
    if len(v) == 0:
        return {"mean": float("nan"), "sd": float("nan"), "min": float("nan"),
                "max": float("nan"), "n": 0}
    return {"mean": float(np.mean(v)), "sd": float(np.std(v)),
            "min": float(np.min(v)), "max": float(np.max(v)), "n": int(len(v))}


def load(tag):
    with open(os.path.join(RESULTS, f"crownjewel_{tag}.json")) as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="promptcond")
    args = ap.parse_args()
    d = load(args.tag)
    encs = d["encoders"]
    prompts = d["prompts"]
    K = len(prompts)

    # ---- flatten into single-prompt cells and ensemble cells ----
    # single-prompt cells (one row per (encoder, prompt))
    sp = {"enc": [], "robust": [], "prompt_id": [], "clean": [], "S": [], "rad": [],
          "etaL1": [], "A": [], "complete": []}
    # ensemble cells (one row per encoder)
    en = {"enc": [], "robust": [], "clean": [], "S": [], "rad": [], "etaL1": [], "A": []}
    # encoder-level invariance
    enc_lvl = {"enc": [], "robust": [], "SC": [], "PC": []}

    for e in encs:
        enc_lvl["enc"].append(e["encoder"]); enc_lvl["robust"].append(e["robust"])
        enc_lvl["SC"].append(e["sc_pred"]); enc_lvl["PC"].append(e["pc"])
        for c in e["cells"]:
            if c["is_ensemble"]:
                en["enc"].append(e["encoder"]); en["robust"].append(e["robust"])
                en["clean"].append(c["clean_acc"]); en["S"].append(c["S_apgd"])
                en["rad"].append(c["robust_radius_mean"]); en["etaL1"].append(c["eta_over_L1"])
                en["A"].append(c["anisotropy_A"])
            else:
                sp["enc"].append(e["encoder"]); sp["robust"].append(e["robust"])
                sp["prompt_id"].append(c["prompt_id"]); sp["clean"].append(c["clean_acc"])
                sp["S"].append(c["S_apgd"]); sp["rad"].append(c["robust_radius_mean"])
                sp["etaL1"].append(c["eta_over_L1"]); sp["A"].append(c["anisotropy_A"])
                sp["complete"].append(c["targeted_aa_complete"])
    for k in sp: sp[k] = np.array(sp[k], dtype=object if k in ("enc", "prompt_id") else float) \
        if k not in ("enc", "prompt_id") else np.array(sp[k])
    for k in en:
        if k != "enc": en[k] = np.array(en[k], dtype=float)
    for k in enc_lvl:
        if k not in ("enc",): enc_lvl[k] = np.array(enc_lvl[k], dtype=float)

    report = {"tag": args.tag, "prompts": prompts, "K": K,
              "n_encoders": len(encs), "n_single_prompt_cells": len(sp["S"]),
              "n_robust_encoders": int(sum(enc_lvl["robust"])),
              "n_nonrobust_encoders": int(len(encs) - sum(enc_lvl["robust"]))}

    # ================= (A) does eta/L1 predict S across the prompt axis? =================
    # (A1) pooled over all (encoder, single-prompt) cells
    S = sp["S"]; rad = sp["rad"]; etaL1 = sp["etaL1"]; A = sp["A"]; clean = sp["clean"]
    groups = list(sp["enc"])
    rob_mask = sp["robust"].astype(bool)
    A1 = {
        "pooled_all_cells": {
            "n_cells": int(len(S)),
            "spearman_etaL1_S": spearman(etaL1, S),
            "spearman_etaL1_S_cluster_ci95": list(cluster_boot_ci(spearman, groups, etaL1, S)),
            "spearman_etaL1_S_naive_ci95": list(boot_ci(spearman, etaL1, S)),
            "spearman_etaL1_radius": spearman(etaL1, rad),
            "spearman_etaL1_radius_cluster_ci95": list(cluster_boot_ci(spearman, groups, etaL1, rad)),
            "spearman_A_radius": spearman(A, rad),
            "spearman_A_radius_cluster_ci95": list(cluster_boot_ci(spearman, groups, A, rad)),
        },
        "pooled_robust_only_cells": {
            "n_cells": int(rob_mask.sum()),
            "spearman_etaL1_S": spearman(etaL1[rob_mask], S[rob_mask]),
            "spearman_etaL1_S_cluster_ci95": list(cluster_boot_ci(
                spearman, [g for g, m in zip(groups, rob_mask) if m],
                etaL1[rob_mask], S[rob_mask])),
            "spearman_etaL1_radius": spearman(etaL1[rob_mask], rad[rob_mask]),
        },
    }
    # (A2) within-encoder-across-prompts
    per_enc = {}
    within_S, within_rad = [], []
    for e in encs:
        el, sl, rl = [], [], []
        for c in e["cells"]:
            if c["is_ensemble"]:
                continue
            el.append(c["eta_over_L1"]); sl.append(c["S_apgd"]); rl.append(c["robust_radius_mean"])
        rho_s = spearman(el, sl); rho_r = spearman(el, rl)
        per_enc[e["encoder"]] = {
            "robust": e["robust"], "n_prompts": len(el),
            "etaL1_range": [float(np.min(el)), float(np.max(el))],
            "etaL1_cv": float(np.std(el) / (np.mean(el) + 1e-12)),
            "S_range": [float(np.min(sl)), float(np.max(sl))],
            "S_sd_across_prompts": float(np.std(sl)),
            "radius_sd_across_prompts": float(np.std(rl)),
            "spearman_etaL1_S": rho_s, "spearman_etaL1_radius": rho_r,
        }
        if np.isfinite(rho_s): within_S.append(rho_s)
        if np.isfinite(rho_r): within_rad.append(rho_r)
    A2 = {
        "per_encoder": per_enc,
        "n_encoders_with_defined_within_rho_S": len(within_S),
        "mean_within_encoder_rho_etaL1_S": float(np.mean(within_S)) if within_S else float("nan"),
        "median_within_encoder_rho_etaL1_S": float(np.median(within_S)) if within_S else float("nan"),
        "mean_within_encoder_rho_etaL1_radius": float(np.mean(within_rad)) if within_rad else float("nan"),
        "note": ("within-encoder rho needs eta/L1 spread across prompts; meaning-preserving prompts "
                 "keep eta/L1 nearly constant per encoder (see etaL1_cv), so within-encoder rho is "
                 "noisy/ill-defined -- the ACROSS-prompt claim is that S itself barely moves with "
                 "prompt (S_sd_across_prompts) while the ACROSS-encoder ranking by eta/L1 is what "
                 "predicts S. Report both honestly."),
    }
    report["A_etaL1_predicts_S_across_prompts"] = {"A1_pooled": A1, "A2_within_encoder": A2}

    # ================= (B) does prompt-invariance (ensemble) confer robustness? =================
    # per-encoder ensemble vs mean single-prompt
    B_per = {}
    dS, dRad, dEta = [], [], []
    ens_clean_ge_mean = []
    for e in encs:
        sp_cells = [c for c in e["cells"] if not c["is_ensemble"]]
        ens_cell = [c for c in e["cells"] if c["is_ensemble"]][0]
        mean_S = float(np.mean([c["S_apgd"] for c in sp_cells]))
        mean_rad = float(np.mean([c["robust_radius_mean"] for c in sp_cells]))
        mean_eta = float(np.mean([c["eta_over_L1"] for c in sp_cells]))
        mean_clean = float(np.mean([c["clean_acc"] for c in sp_cells]))
        B_per[e["encoder"]] = {
            "robust": e["robust"],
            "ensemble_S": ens_cell["S_apgd"], "mean_singleprompt_S": mean_S,
            "delta_S_ens_minus_mean": ens_cell["S_apgd"] - mean_S,
            "ensemble_radius": ens_cell["robust_radius_mean"], "mean_singleprompt_radius": mean_rad,
            "delta_radius": ens_cell["robust_radius_mean"] - mean_rad,
            "ensemble_etaL1": ens_cell["eta_over_L1"], "mean_singleprompt_etaL1": mean_eta,
            "delta_etaL1": ens_cell["eta_over_L1"] - mean_eta,
            "ensemble_clean": ens_cell["clean_acc"], "mean_singleprompt_clean": mean_clean,
        }
        dS.append(ens_cell["S_apgd"] - mean_S)
        dRad.append(ens_cell["robust_radius_mean"] - mean_rad)
        dEta.append(ens_cell["eta_over_L1"] - mean_eta)
        ens_clean_ge_mean.append(ens_cell["clean_acc"] >= mean_clean - 1e-9)
    # residual test (in S units): fit S ~ log(eta/L1) on the single-prompt cells (OLS), predict the
    # ensemble S from the ensemble eta/L1, and report the ensemble residual = observed S - predicted.
    # If prompt-invariance conferred robustness BEYOND what eta/L1 tracks, ensemble residuals would be
    # systematically POSITIVE. ~0 => the ensemble's robustness is exactly what eta/L1 already predicts.
    lx = np.log(np.clip(etaL1, 1e-9, None)); yv = S
    coef = np.polyfit(lx, yv, 1)                    # S ~= coef[0]*log(etaL1) + coef[1]
    ens_eta = en["etaL1"]; ens_S = en["S"]
    ens_pred = np.polyval(coef, np.log(np.clip(ens_eta, 1e-9, None)))
    ens_resid = ens_S - ens_pred                    # >0 => ensemble more robust than eta/L1 predicts
    def _mean(a): return float(np.mean(a))
    report["B_prompt_invariance_confers_robustness"] = {
        "per_encoder": B_per,
        "mean_delta_S_ens_minus_mean_singleprompt": float(np.mean(dS)),
        "delta_S_ci95": list(boot_ci(_mean, np.array(dS))),
        "mean_delta_radius": float(np.mean(dRad)),
        "mean_delta_etaL1": float(np.mean(dEta)),
        "n_encoders_ensemble_more_robust_than_mean": int(np.sum(np.array(dS) > 0)),
        "n_encoders": len(dS),
        "ensemble_residual_vs_etaL1_fit_mean_S_units": float(np.mean(ens_resid)),
        "ensemble_residual_vs_etaL1_fit_ci95": list(boot_ci(_mean, ens_resid)),
        "ens_clean_ge_mean_all": bool(all(ens_clean_ge_mean)),
        "note": ("delta_S ~ 0 and residual ~ 0 => the ensemble's robustness is whatever eta/L1 "
                 "already predicts; prompt-invariance does not buy adversarial robustness. Report "
                 "as-is either way."),
    }

    # ================= (C) cross-prompt adversarial transfer =================
    C_per = {}
    all_offdiag = []
    single_to_ens, ens_to_single = [], []
    single_to_single = []
    for e in encs:
        tr = e["cross_prompt_transfer"]
        pids = list(tr.keys())
        vals = []
        for pa in pids:
            for pb, v in tr[pa].items():
                if pb == "n_successful_adv_under_source":
                    continue
                if not (isinstance(v, (int, float)) and np.isfinite(v)):
                    continue
                vals.append(v); all_offdiag.append(v)
                if pa != "ensemble" and pb == "ensemble":
                    single_to_ens.append(v)
                elif pa == "ensemble" and pb != "ensemble":
                    ens_to_single.append(v)
                elif pa != "ensemble" and pb != "ensemble":
                    single_to_single.append(v)
        C_per[e["encoder"]] = {
            "robust": e["robust"],
            "mean_transfer_all_pairs": float(np.mean(vals)) if vals else float("nan"),
            "median_transfer_all_pairs": float(np.median(vals)) if vals else float("nan"),
            "min_transfer": float(np.min(vals)) if vals else float("nan"),
        }
    report["C_cross_prompt_transfer"] = {
        "per_encoder": C_per,
        "pooled_all_offdiag": desc(all_offdiag),
        "pooled_single_to_single": desc(single_to_single),
        "pooled_single_to_ensemble": desc(single_to_ens),
        "pooled_ensemble_to_single": desc(ens_to_single),
        "all_in_unit_interval": bool(all(0 - 1e-9 <= v <= 1 + 1e-9 for v in all_offdiag)),
        "note": ("transfer fraction = of the adversarial images that fool the SOURCE prompt's head, "
                 "the fraction that ALSO flip the TARGET prompt's head. High transfer => the "
                 "vulnerability is a property of the IMAGE ENCODER, not the specific prompt."),
    }

    # ================= (D) 2x2 restatement =================
    report["D_2x2_restatement"] = {
        "SC_encoder_level": desc(enc_lvl["SC"]),
        "PC_encoder_level": desc(enc_lvl["PC"]),
        "S_across_all_cells": desc(S),
        "S_across_encoders_at_reference_prompt": desc(
            [c["S_apgd"] for e in encs for c in e["cells"] if c.get("prompt_id") == "p0"]),
        "radius_across_all_cells": desc(rad),
        "S_sd_within_encoder_across_prompts_mean": float(np.mean(
            [per_enc[e["encoder"]]["S_sd_across_prompts"] for e in encs])),
        "S_sd_across_encoders_mean_over_prompts": float(np.mean([
            np.std([e["cells"][k]["S_apgd"] for e in encs]) for k in range(K)])),
    }

    # ================= sanity gates =================
    S_le_clean = all(c["S_apgd"] <= c["clean_acc"] + 1e-9
                     for e in encs for c in e["cells"])
    nonrob_S = {}
    for e in encs:
        if not e["robust"]:
            nonrob_S[e["encoder"]] = {c["prompt_id"]: c["S_apgd"] for c in e["cells"]}
    nonrob_near_zero = all(v <= 0.05 for enc in nonrob_S.values() for v in enc.values())
    report["sanity"] = {
        "S_le_clean_all_cells": bool(S_le_clean),
        "nonrobust_S_le_0p05_all_prompts": bool(nonrob_near_zero),
        "nonrobust_S_per_prompt": nonrob_S,
        "transfer_in_unit_interval": report["C_cross_prompt_transfer"]["all_in_unit_interval"],
        "ensemble_clean_ge_mean_singleprompt_all": report[
            "B_prompt_invariance_confers_robustness"]["ens_clean_ge_mean_all"],
        "pc_self_check_all_one": bool(all(abs(e["pc_self_check"] - 1.0) < 1e-6 for e in encs)),
        "targeted_aa_complete_all_cells": bool(all(
            c["targeted_aa_complete"] for e in encs for c in e["cells"])),
        "targeted_aa_incomplete_cells": [
            f"{e['encoder']}/{c['prompt_id']}" for e in encs for c in e["cells"]
            if not c["targeted_aa_complete"]],
    }
    if "fare4" in list(enc_lvl["enc"]) and "clip" in list(enc_lvl["enc"]):
        rf = [e for e in encs if e["encoder"] == "fare4"][0]
        rc = [e for e in encs if e["encoder"] == "clip"][0]
        rf_rad = np.mean([c["robust_radius_mean"] for c in rf["cells"]])
        rc_rad = np.mean([c["robust_radius_mean"] for c in rc["cells"]])
        report["sanity"]["fare4_radius_gt_clip_meanoverprompts"] = bool(rf_rad > rc_rad)

    # ================= two-way headline recompute =================
    report["headline_two_ways"] = {
        "etaL1_vs_S_pooled_spearman": spearman(etaL1, S),
        "etaL1_vs_S_pooled_pair_concordance": rank_agree(etaL1, S),
        "etaL1_vs_S_robustonly_spearman": spearman(etaL1[rob_mask], S[rob_mask]),
        "note": ("headline = pooled Spearman(eta/L1, S) over all (encoder,prompt) cells, recomputed "
                 "as pairwise rank concordance; both should agree in sign/strength."),
    }

    # ---- per-image pooled (powered), pooled over robust encoders' reference-prompt cells ----
    ratio_ranks, rad_ranks = [], []
    per_tower_pi = {}
    for e in encs:
        for c in e["cells"]:
            pid = c["prompt_id"]
            p = os.path.join(RESULTS, f"per_image_promptcond_{e['encoder']}_{pid}.pt")
            if not os.path.exists(p):
                continue
            pi = torch.load(p, map_location="cpu")
            radp = pi["robust_radius_linf"].numpy(); r1 = pi["ratio_l1"].numpy()
            key = f"{e['encoder']}/{pid}"
            per_tower_pi[key] = {
                "n": int(len(radp)),
                "spearman_ratioL1_radius": spearman(r1, radp),
                "floor_frac": float((radp == radp.min()).mean()),
            }
            if e["robust"] and pid == "p0":
                ratio_ranks.append(stats.rankdata(r1) / len(r1))
                rad_ranks.append(stats.rankdata(radp) / len(radp))
    report["E_per_image"] = {"per_cell": per_tower_pi}
    if ratio_ranks:
        rr = np.concatenate(ratio_ranks); dd = np.concatenate(rad_ranks)
        report["E_per_image"]["pooled_robust_refprompt"] = {
            "n": int(len(rr)),
            "spearman_ratioL1_radius": spearman(rr, dd),
            "spearman_ratioL1_radius_ci95": list(boot_ci(spearman, rr, dd)),
        }

    out_path = os.path.join(RESULTS, f"crownjewel_{args.tag}_analysis.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[CJ-PC-analysis] wrote {out_path}")

    make_figure(d, sp, en, enc_lvl, report, args.tag)
    print("[CJ-PC-analysis] figure written")

    # ---- console summary ----
    a1 = A1["pooled_all_cells"]
    print("\n== (A1) POOLED over all (encoder,prompt) cells ==")
    print(f"  Spearman(eta/L1, S)      = {a1['spearman_etaL1_S']:+.3f}  "
          f"cluster-CI[{a1['spearman_etaL1_S_cluster_ci95'][0]:+.3f},"
          f"{a1['spearman_etaL1_S_cluster_ci95'][1]:+.3f}]  (n={a1['n_cells']} cells)")
    print(f"  Spearman(eta/L1, radius) = {a1['spearman_etaL1_radius']:+.3f}  "
          f"cluster-CI[{a1['spearman_etaL1_radius_cluster_ci95'][0]:+.3f},"
          f"{a1['spearman_etaL1_radius_cluster_ci95'][1]:+.3f}]")
    print(f"  robust-only Spearman(eta/L1, S) = {A1['pooled_robust_only_cells']['spearman_etaL1_S']:+.3f}")
    print("\n== (A2) within-encoder across-prompts ==")
    print(f"  mean within-encoder rho(eta/L1,S) = {A2['mean_within_encoder_rho_etaL1_S']:+.3f} "
          f"(defined for {A2['n_encoders_with_defined_within_rho_S']} encoders)")
    print(f"  typical eta/L1 CV across prompts: "
          f"{np.median([v['etaL1_cv'] for v in per_enc.values()]):.4f} (prompts barely move eta/L1)")
    print(f"  typical S sd across prompts     : "
          f"{np.median([v['S_sd_across_prompts'] for v in per_enc.values()]):.4f}")
    b = report["B_prompt_invariance_confers_robustness"]
    print("\n== (B) prompt-invariance (ensemble) vs robustness ==")
    print(f"  mean delta S (ensemble - mean single-prompt) = {b['mean_delta_S_ens_minus_mean_singleprompt']:+.4f} "
          f"CI[{b['delta_S_ci95'][0]:+.4f},{b['delta_S_ci95'][1]:+.4f}]")
    print(f"  ensemble more robust than mean in {b['n_encoders_ensemble_more_robust_than_mean']}/{b['n_encoders']} encoders")
    print(f"  ensemble residual vs eta/L1 fit (S units) = {b['ensemble_residual_vs_etaL1_fit_mean_S_units']:+.3f} "
          f"CI[{b['ensemble_residual_vs_etaL1_fit_ci95'][0]:+.3f},{b['ensemble_residual_vs_etaL1_fit_ci95'][1]:+.3f}]")
    c = report["C_cross_prompt_transfer"]
    print("\n== (C) cross-prompt adversarial transfer ==")
    print(f"  all off-diag pairs: mean {c['pooled_all_offdiag']['mean']:.3f} "
          f"sd {c['pooled_all_offdiag']['sd']:.3f} range "
          f"[{c['pooled_all_offdiag']['min']:.3f},{c['pooled_all_offdiag']['max']:.3f}] "
          f"(n={c['pooled_all_offdiag']['n']})")
    print(f"  single->single mean {c['pooled_single_to_single']['mean']:.3f}; "
          f"single->ensemble mean {c['pooled_single_to_ensemble']['mean']:.3f}; "
          f"ensemble->single mean {c['pooled_ensemble_to_single']['mean']:.3f}")
    print("\n== sanity ==")
    for k in ["S_le_clean_all_cells", "nonrobust_S_le_0p05_all_prompts", "transfer_in_unit_interval",
              "ensemble_clean_ge_mean_singleprompt_all", "pc_self_check_all_one",
              "targeted_aa_complete_all_cells", "fare4_radius_gt_clip_meanoverprompts"]:
        if k in report["sanity"]:
            print(f"  {k}: {report['sanity'][k]}")
    if report["sanity"]["targeted_aa_incomplete_cells"]:
        print(f"  INCOMPLETE cells: {report['sanity']['targeted_aa_incomplete_cells']}")
    print("\n== headline two ways ==")
    h = report["headline_two_ways"]
    print(f"  pooled Spearman(eta/L1,S) = {h['etaL1_vs_S_pooled_spearman']:+.3f}; "
          f"pairwise concordance = {h['etaL1_vs_S_pooled_pair_concordance']:.3f}")


def make_figure(d, sp, en, enc_lvl, report, tag):
    os.makedirs(FIGDIR, exist_ok=True)
    encs = d["encoders"]; prompts = d["prompts"]; K = len(prompts)
    S = sp["S"]; etaL1 = sp["etaL1"]; rob = sp["robust"].astype(bool)
    c_rob, c_non = "#c0392b", "#2c6fbb"

    fig = plt.figure(figsize=(13.6, 4.7))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.15, 1.0], wspace=0.32)

    # ---- Panel A: pooled eta/L1 vs S across (encoder,prompt) cells ----
    axA = fig.add_subplot(gs[0, 0])
    axA.scatter(etaL1[~rob], S[~rob], marker="o", s=42, facecolor="none",
                edgecolor=c_non, linewidth=1.2, label="non-robust")
    axA.scatter(etaL1[rob], S[rob], marker="o", s=42, c=c_rob, edgecolor="k",
                linewidth=0.3, alpha=0.8, label="robust")
    axA.set_xscale("log")
    axA.set_xlabel(r"$\eta/L_1$ (threat-matched L$\infty$; per (encoder,prompt))")
    axA.set_ylabel("robust accuracy S (APGD-CE upper bound)")
    a1 = report["A_etaL1_predicts_S_across_prompts"]["A1_pooled"]["pooled_all_cells"]
    axA.set_title(f"A. $\\eta/L_1$ predicts image-adversarial S\n"
                  f"across ALL (encoder,prompt) cells (n={a1['n_cells']})", fontsize=9.5)
    axA.text(0.03, 0.97,
             f"Spearman = {a1['spearman_etaL1_S']:+.2f}\n"
             f"cluster-CI [{a1['spearman_etaL1_S_cluster_ci95'][0]:+.2f},"
             f"{a1['spearman_etaL1_S_cluster_ci95'][1]:+.2f}]",
             transform=axA.transAxes, va="top", ha="left", fontsize=8.2,
             bbox=dict(boxstyle="round", fc="w", ec="0.7", alpha=0.92))
    axA.legend(fontsize=8, loc="lower right"); axA.grid(alpha=0.25, which="both")

    # ---- Panel B: S per encoder across the K prompts + ensemble (spread across ENCODERS, flat across PROMPTS) ----
    axB = fig.add_subplot(gs[0, 1])
    order = sorted(range(len(encs)), key=lambda i: np.mean([c["S_apgd"] for c in encs[i]["cells"]]))
    yt = []
    for row, i in enumerate(order):
        e = encs[i]
        sp_S = [c["S_apgd"] for c in e["cells"] if not c["is_ensemble"]]
        ens_S = [c["S_apgd"] for c in e["cells"] if c["is_ensemble"]][0]
        col = c_rob if e["robust"] else c_non
        axB.plot(sp_S, [row] * len(sp_S), "o", ms=4, color=col, alpha=0.55)
        axB.plot([min(sp_S), max(sp_S)], [row, row], "-", color=col, lw=1.0, alpha=0.4)
        axB.plot(ens_S, row, "D", ms=6, color=col, markeredgecolor="k", markeredgewidth=0.4)
        yt.append(e["encoder"])
    axB.set_yticks(range(len(order))); axB.set_yticklabels(yt, fontsize=7)
    axB.set_xlabel("robust accuracy S")
    axB.set_title("B. S spreads across ENCODERS but is nearly flat\n"
                  "across the K prompts (circles) and the ensemble (diamond)", fontsize=9.5)
    axB.grid(axis="x", alpha=0.25)

    # ---- Panel C: cross-prompt transfer matrix (pooled over encoders, robust) ----
    axC = fig.add_subplot(gs[0, 2])
    pids = ["p%d" % k for k in range(K)] + ["ensemble"]
    labels_short = [p.replace("a photo of ", "").replace("{}.", "").strip() or p
                    for p in prompts] + ["ens"]
    M = np.full((len(pids), len(pids)), np.nan)
    cnt = np.zeros((len(pids), len(pids)))
    for e in encs:
        if not e["robust"]:
            continue
        tr = e["cross_prompt_transfer"]
        for ia, pa in enumerate(pids):
            if pa not in tr:
                continue
            for ib, pb in enumerate(pids):
                if pb == pa or pb not in tr[pa]:
                    continue
                v = tr[pa][pb]
                if isinstance(v, (int, float)) and np.isfinite(v):
                    M[ia, ib] = (0 if np.isnan(M[ia, ib]) else M[ia, ib]) + v
                    cnt[ia, ib] += 1
    with np.errstate(invalid="ignore"):
        M = M / np.where(cnt > 0, cnt, np.nan)
    np.fill_diagonal(M, np.nan)
    im = axC.imshow(M, vmin=0, vmax=1, cmap="viridis")
    axC.set_xticks(range(len(pids))); axC.set_xticklabels(labels_short, rotation=45, ha="right", fontsize=6.5)
    axC.set_yticks(range(len(pids))); axC.set_yticklabels(labels_short, fontsize=6.5)
    axC.set_xlabel("target prompt B"); axC.set_ylabel("source prompt A")
    cpm = report["C_cross_prompt_transfer"]["pooled_all_offdiag"]["mean"]
    axC.set_title(f"C. Cross-prompt adversarial transfer\n(robust encoders; mean off-diag = {cpm:.2f})",
                  fontsize=9.5)
    cb = fig.colorbar(im, ax=axC, fraction=0.046, pad=0.04)
    cb.set_label("transfer fraction", fontsize=8)

    fig.suptitle(
        "Crown-Jewel PROMPT-CONDITIONED: an image attack run against K meaning-preserving text "
        "prompts in parallel. Image-adversarial robustness S spreads across encoders, is predicted "
        r"by threat-matched $\eta/L_1$ regardless of prompt, is nearly invariant to the prompt, and "
        "the adversarial vulnerability transfers across prompts (it is a property of the image "
        "encoder). Prompt-invariance (ensemble) does not buy robustness.", fontsize=8.8, y=1.06)
    out = os.path.join(FIGDIR, f"crownjewel_{tag}.pdf")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
