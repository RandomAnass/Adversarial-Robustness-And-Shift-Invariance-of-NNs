"""C1 analysis: turn per-tower + per-image results into the headline statistics.

Produces (to results/c1_tower/c1_analysis_<tag>.json and stdout):
  - Per-tower table (clean acc, SC, eta/L1, eta/L2, S_apgd at each eps, masking audit)
  - Cross-tower rank correlations: {SC, eta/L1, eta/L2, clean_acc} vs S_apgd
      Pearson + Spearman with bootstrap CIs (resampling towers)
  - Partial correlation of eta/L1 vs S controlling clean acc (load-bearing)
  - Per-image Spearman(eta/L1, robust radius) and Spearman(SC_per_image, radius) with CIs
  - Selection-rule regret table (pick by eta/L1 / SC / clean vs oracle)
  - Gradient-masking verdict (APGD <= PGD-40 <= FGSM per tower; Square gap)
  - KILL-criterion evaluation
"""
import os, sys, json, argparse
import numpy as np
import torch
from scipy import stats

RESULTS = "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower"


def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3:
        return float("nan")
    return float(stats.spearmanr(x, y).correlation)


def partial_corr(x, y, z):
    """Partial correlation of x,y controlling z (all 1D)."""
    x, y, z = map(lambda a: np.asarray(a, float), (x, y, z))
    def resid(a, c):
        c1 = np.c_[np.ones_like(c), c]
        beta, *_ = np.linalg.lstsq(c1, a, rcond=None)
        return a - c1 @ beta
    rx, ry = resid(x, z), resid(y, z)
    return pearson(rx, ry)


def boot_ci(fn, *arrays, n=5000, seed=0, paired=True):
    rng = np.random.default_rng(seed)
    arrays = [np.asarray(a, float) for a in arrays]
    m = len(arrays[0])
    stats_ = []
    for _ in range(n):
        idx = rng.integers(0, m, m)
        stats_.append(fn(*[a[idx] for a in arrays]))
    stats_ = np.array([s for s in stats_ if np.isfinite(s)])
    if len(stats_) == 0:
        return (float("nan"), float("nan"))
    return (float(np.percentile(stats_, 2.5)), float(np.percentile(stats_, 97.5)))


def perm_test(fn, x, y, n=10000, seed=0):
    rng = np.random.default_rng(seed)
    x, y = np.asarray(x, float), np.asarray(y, float)
    obs = fn(x, y)
    cnt = 0
    for _ in range(n):
        cnt += abs(fn(x, rng.permutation(y))) >= abs(obs)
    return obs, (cnt + 1) / (n + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="main")
    ap.add_argument("--eps", type=float, default=4/255, help="headline eps for S")
    args = ap.parse_args()

    with open(os.path.join(RESULTS, f"c1_results_{args.tag}.json")) as f:
        blob = json.load(f)
    res = blob["results"]
    eps_tag = f"{args.eps:.5f}"

    towers = [r["tower"] for r in res]
    clean = [r["clean_acc"] for r in res]
    sc = [r["sc_pred"] for r in res]
    sc_cos = [r["sc_cos"] for r in res]
    etaL1 = [r["eta_over_L1"] for r in res]
    etaL2 = [r["eta_over_L2"] for r in res]
    S = [float(r["S_apgd"][eps_tag]) for r in res]  # AutoAttack robust acc (target)
    S_pgd = [float(r["S_pgd40"][eps_tag]) for r in res]
    S_fgsm = [float(r["S_fgsm"][eps_tag]) for r in res]
    sqgap = [float(r["S_square_gap"][eps_tag]) for r in res]

    out = {"tag": args.tag, "eps": args.eps, "towers": towers}
    out["per_tower"] = [
        {"tower": t, "clean_acc": c, "sc": s, "sc_cos": sco, "eta_over_L1": e1,
         "eta_over_L2": e2, "S_apgd": ss, "S_pgd40": sp, "S_fgsm": sf, "square_gap": sq}
        for t, c, s, sco, e1, e2, ss, sp, sf, sq in
        zip(towers, clean, sc, sc_cos, etaL1, etaL2, S, S_pgd, S_fgsm, sqgap)
    ]

    # ---- cross-tower correlations vs S (AutoAttack robust acc) ----
    def corr_block(name, x):
        pr = pearson(x, S); sp = spearman(x, S)
        pr_ci = boot_ci(pearson, x, S); sp_ci = boot_ci(spearman, x, S)
        _, pperm = perm_test(pearson, x, S)
        return {"metric": name, "pearson": pr, "pearson_ci95": pr_ci,
                "spearman": sp, "spearman_ci95": sp_ci, "perm_p": pperm}

    out["cross_tower_vs_S"] = {
        "SC": corr_block("SC", sc),
        "SC_cos": corr_block("SC_cos", sc_cos),
        "eta_over_L1": corr_block("eta_over_L1", etaL1),
        "eta_over_L2": corr_block("eta_over_L2", etaL2),
        "clean_acc": corr_block("clean_acc", clean),
    }
    # partial corr eta/L1 vs S controlling clean acc (load-bearing)
    pc = partial_corr(etaL1, S, clean)
    pc_ci = boot_ci(lambda a, b, c: partial_corr(a, b, c), etaL1, S, clean)
    out["partial_corr_etaL1_S_given_clean"] = {"value": pc, "ci95": pc_ci}
    pc_sc = partial_corr(sc, S, clean)
    out["partial_corr_SC_S_given_clean"] = {"value": pc_sc,
        "ci95": boot_ci(lambda a, b, c: partial_corr(a, b, c), sc, S, clean)}

    # ---- selection-rule regret ----
    oracle_S = max(S)
    def regret(selector_vals, higher_is_better=True):
        j = int(np.argmax(selector_vals)) if higher_is_better else int(np.argmin(selector_vals))
        return oracle_S - S[j], towers[j]
    reg_etaL1, pick_etaL1 = regret(etaL1)
    reg_sc, pick_sc = regret(sc)
    reg_clean, pick_clean = regret(clean)
    reg_etaL2, pick_etaL2 = regret(etaL2)
    out["selection_regret"] = {
        "oracle_S": oracle_S, "oracle_tower": towers[int(np.argmax(S))],
        "eta_over_L1": {"pick": pick_etaL1, "regret_pts": reg_etaL1 * 100},
        "eta_over_L2": {"pick": pick_etaL2, "regret_pts": reg_etaL2 * 100},
        "SC": {"pick": pick_sc, "regret_pts": reg_sc * 100},
        "clean_acc": {"pick": pick_clean, "regret_pts": reg_clean * 100},
    }

    # ---- per-image Spearman(eta/L1, robust radius) and (SC, radius) ----
    per_img = {}
    for r in res:
        t = r["tower"]
        p = os.path.join(RESULTS, f"per_image_{t}_{args.tag}.pt")
        if os.path.exists(p):
            per_img[t] = torch.load(p)
    out["per_image"] = {}
    # pooled per-image Spearman within each tower (radius is a per-tower attack quantity)
    for t, pi in per_img.items():
        if "robust_radius_linf" not in pi:
            continue
        rad = pi["robust_radius_linf"].numpy()
        r1 = pi["ratio_l1"].numpy()
        scpi = pi.get("sc_pred_per_image")
        scpi = scpi.numpy() if scpi is not None else None
        # only uncensored (flipped) images give a real radius ordering; keep all with rank
        sp_r1 = spearman(r1, rad)
        sp_r1_ci = boot_ci(spearman, r1, rad)
        entry = {"n": int(len(rad)), "spearman_ratioL1_radius": sp_r1,
                 "spearman_ratioL1_radius_ci95": sp_r1_ci,
                 "frac_flipped": float(pi["flipped"].float().mean())}
        if scpi is not None:
            m = np.isfinite(scpi) & np.isfinite(rad)
            if m.sum() >= 10:
                entry["spearman_SC_radius"] = spearman(scpi[m], rad[m])
                entry["spearman_SC_radius_ci95"] = boot_ci(spearman, scpi[m], rad[m])
                entry["n_sc_radius"] = int(m.sum())
        out["per_image"][t] = entry

    # ---- gradient-masking verdict ----
    # No masking iff: APGD <= PGD40 <= FGSM (white-box monotonicity) AND
    #                 Square (black-box) does not beat APGD (S_square >= S_apgd, gap >= ~0).
    masking = []
    for r in res:
        t = r["tower"]
        ok = True
        detail = {}
        for etag in r["S_apgd"]:
            aa = float(r["S_apgd"][etag]); pg = float(r["S_pgd40"][etag]); fg = float(r["S_fgsm"][etag])
            sqg = float(r["S_square_gap"][etag])  # S_square - S_apgd; >= 0 means APGD stronger
            mono = (aa <= pg + 1e-6) and (pg <= fg + 1e-6)
            square_ok = sqg >= -0.02  # Square not materially stronger than APGD (tol 2pts)
            ok = ok and mono and square_ok
            detail[etag] = {"apgd": aa, "pgd40": pg, "fgsm": fg,
                            "square": float(r["S_square"][etag]),
                            "square_minus_apgd": sqg,
                            "monotone_ok": mono, "square_ok": square_ok}
        masking.append({"tower": t, "audit_ok_all_eps": ok, "detail": detail})
    out["masking_audit"] = masking
    out["masking_verdict"] = (
        "PASS: APGD<=PGD40<=FGSM and Square>=APGD for all towers/eps (no masking)"
        if all(m["audit_ok_all_eps"] for m in masking)
        else "CHECK: monotonicity or Square<APGD violated for some tower/eps")

    # ---- KILL criterion ----
    # Kill iff SC predicts S as strongly as eta/L1 (CIs overlap in favor of SC) OR
    # partial corr(eta/L1, S | clean) < 0.5
    etaL1_pr = out["cross_tower_vs_S"]["eta_over_L1"]["pearson"]
    sc_pr = out["cross_tower_vs_S"]["SC"]["pearson"]
    kill_partial = (not np.isfinite(pc)) or (pc < 0.5)
    kill_sc = abs(sc_pr) >= abs(etaL1_pr)  # SC orders at least as well
    out["KILL"] = {
        "criterion_partial_lt_0.5": bool(kill_partial),
        "criterion_SC_predicts_as_well": bool(kill_sc),
        "triggered": bool(kill_partial or kill_sc),
        "etaL1_pearson": etaL1_pr, "SC_pearson": sc_pr,
        "partial_corr": pc,
    }

    outp = os.path.join(RESULTS, f"c1_analysis_{args.tag}.json")
    with open(outp, "w") as f:
        json.dump(out, f, indent=2, default=str)

    # ---- pretty print ----
    print("\n===== C1 PER-TOWER (eps=%.4f) =====" % args.eps)
    print(f"{'tower':8} {'clean':>6} {'SC':>7} {'SCcos':>7} {'eta/L1':>9} {'eta/L2':>9} "
          f"{'S_apgd':>7} {'S_pgd':>7} {'S_fgsm':>7} {'sqgap':>7}")
    for d in out["per_tower"]:
        print(f"{d['tower']:8} {d['clean_acc']:6.3f} {d['sc']:7.4f} {d['sc_cos']:7.4f} "
              f"{d['eta_over_L1']:9.5f} {d['eta_over_L2']:9.5f} {d['S_apgd']:7.3f} "
              f"{d['S_pgd40']:7.3f} {d['S_fgsm']:7.3f} {d['square_gap']:7.3f}")
    print("\n===== CROSS-TOWER CORR vs S_apgd =====")
    for k, v in out["cross_tower_vs_S"].items():
        print(f"{k:14} pearson={v['pearson']:+.3f} CI{tuple(round(c,2) for c in v['pearson_ci95'])} "
              f"spearman={v['spearman']:+.3f} CI{tuple(round(c,2) for c in v['spearman_ci95'])} "
              f"perm_p={v['perm_p']:.3f}")
    print(f"\nPARTIAL corr(eta/L1, S | clean) = {pc:+.3f} CI{tuple(round(c,2) for c in pc_ci)}")
    print(f"PARTIAL corr(SC,     S | clean) = {pc_sc:+.3f}")
    print("\n===== SELECTION REGRET (robust-acc pts vs oracle) =====")
    sr = out["selection_regret"]
    print(f"oracle: {sr['oracle_tower']} S={sr['oracle_S']:.3f}")
    for k in ["eta_over_L1", "eta_over_L2", "SC", "clean_acc"]:
        print(f"  pick-by-{k:12} -> {sr[k]['pick']:8} regret={sr[k]['regret_pts']:.2f} pts")
    print("\n===== PER-IMAGE Spearman(ratio/SC, radius) =====")
    for t, e in out["per_image"].items():
        line = (f"{t:8} n={e['n']:5} sp(eta/L1,rad)={e['spearman_ratioL1_radius']:+.3f} "
                f"CI{tuple(round(c,2) for c in e['spearman_ratioL1_radius_ci95'])} "
                f"flip={e['frac_flipped']:.2f}")
        if "spearman_SC_radius" in e:
            line += f"  sp(SC,rad)={e['spearman_SC_radius']:+.3f}"
        print(line)
    print("\nMASKING:", out["masking_verdict"])
    print("KILL:", out["KILL"]["triggered"], out["KILL"])
    print("\nsaved ->", outp)


if __name__ == "__main__":
    main()
