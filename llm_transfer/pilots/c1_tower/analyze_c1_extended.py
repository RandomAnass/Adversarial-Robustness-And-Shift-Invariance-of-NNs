"""C1 EXTENDED analysis (adversarial-verifier hardening).

Merges the original 6-tower panel (c1_results_main.json) with the 6 non-AT wideners
(c1_results_ext.json) into one >=12-tower panel and recomputes the load-bearing statistics
with the confound breakdowns the verifier requires:

  1. Cross-tower Pearson/Spearman of {SC_pred, SC_cos, eta/L1, eta/L2, clean} vs S_apgd, with
     bootstrap CIs + permutation p, on: (a) the FULL panel, (b) AT-only (the 4 AT towers),
     (c) non-AT-only (all non-robust towers). The AT-only block is the "is it just an AT
     detector?" test; the non-AT-only block tests whether eta/L / SC_cos vary meaningfully
     among towers that are all S~0.
  2. Partial correlation eta/L1 vs S | clean (+ | clean, is-AT indicator) on the full panel.
  3. Per-image dissociation (the powered claim that sidesteps n): pooled within-tower-ranked
     Spearman(eta/L1 ratio, robust radius) vs Spearman(SC, radius) across the AT towers, with
     bootstrap CIs; per-tower table with radius-degeneracy (floor fraction) flagged.
  4. Selection regret on the full panel.
  5. Both consistency metrics head-to-head (SC_pred vs SC_cos) with the honest range note.
"""
import os, json, argparse
import numpy as np
import torch
from scipy import stats

RESULTS = "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower"
AT_TOWERS = {"fare2", "fare4", "tecoa2", "tecoa4"}


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


def boot_ci(fn, *arrays, n=5000, seed=0):
    rng = np.random.default_rng(seed)
    arrays = [np.asarray(a, float) for a in arrays]
    m = len(arrays[0])
    out = []
    for _ in range(n):
        idx = rng.integers(0, m, m)
        out.append(fn(*[a[idx] for a in arrays]))
    out = np.array([s for s in out if np.isfinite(s)])
    if len(out) == 0:
        return (float("nan"), float("nan"))
    return (float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)))


def perm_test(fn, x, y, n=10000, seed=0):
    rng = np.random.default_rng(seed)
    x, y = np.asarray(x, float), np.asarray(y, float)
    obs = fn(x, y)
    cnt = sum(abs(fn(x, rng.permutation(y))) >= abs(obs) for _ in range(n))
    return obs, (cnt + 1) / (n + 1)


def partial_corr(x, y, z):
    x, y = np.asarray(x, float), np.asarray(y, float)
    Z = np.asarray(z, float)
    if Z.ndim == 1:
        Z = Z[:, None]

    def resid(a):
        C = np.c_[np.ones(len(a)), Z]
        beta, *_ = np.linalg.lstsq(C, a, rcond=None)
        return a - C @ beta
    return pearson(resid(x), resid(y))


def load_panel(eps_tag):
    res = []
    for fn in ["c1_results_main.json", "c1_results_ext.json"]:
        p = os.path.join(RESULTS, fn)
        if os.path.exists(p):
            res += json.load(open(p))["results"]
    rows = []
    for r in res:
        if eps_tag not in r["S_apgd"]:
            continue
        rows.append({
            "tower": r["tower"], "clean": r["clean_acc"], "sc": r["sc_pred"],
            "sc_cos": r["sc_cos"], "e1": r["eta_over_L1"], "e2": r["eta_over_L2"],
            "S": float(r["S_apgd"][eps_tag]),
            "is_at": 1.0 if r["tower"] in AT_TOWERS else 0.0,
        })
    return rows


def corr_block(x, S):
    return {"pearson": pearson(x, S), "pearson_ci95": boot_ci(pearson, x, S),
            "spearman": spearman(x, S), "spearman_ci95": boot_ci(spearman, x, S),
            "perm_p": perm_test(pearson, x, S)[1]}


def per_image_dissociation():
    """Pooled within-tower-ranked Spearman across AT towers (the powered, n-sidestepping claim).
    Uses the EXT per-image radii (finer grid) where available, else the main per-image files."""
    out = {"per_tower": {}, "pooled_AT": {}}
    at = ["fare2", "fare4", "tecoa2", "tecoa4"]
    nonat = ["clip", "dinov2", "clip_l14_laion2b", "clip_l14_datacomp", "clip_b16_openai",
             "clip_b16_laion2b", "clip_b32_laion2b", "clip_l14_metaclip"]
    ratio_ranks, rad_ranks, sc_ranks, scrad_ranks = [], [], [], []
    for t in at + nonat:
        p_ext = os.path.join(RESULTS, f"per_image_{t}_ext.pt")
        p_main = os.path.join(RESULTS, f"per_image_{t}_main.pt")
        p = p_ext if os.path.exists(p_ext) else (p_main if os.path.exists(p_main) else None)
        if p is None:
            continue
        d = torch.load(p, map_location="cpu")
        if "robust_radius_linf" not in d or "ratio_l1" not in d:
            continue
        rad = d["robust_radius_linf"].numpy()
        r1 = d["ratio_l1"].numpy()
        floor = float((rad == rad.min()).mean())
        entry = {"n": len(rad), "radius_uniq": int(len(np.unique(rad))),
                 "floor_frac": floor, "source": os.path.basename(p),
                 "spearman_ratioL1_radius": spearman(r1, rad),
                 "spearman_ratioL1_radius_ci95": boot_ci(spearman, r1, rad)}
        sc = d.get("sc_pred_per_image")
        if sc is not None:
            sc = sc.numpy()
            m = np.isfinite(sc) & np.isfinite(rad)
            if m.sum() >= 10:
                entry["spearman_SC_radius"] = spearman(sc[m], rad[m])
        out["per_tower"][t] = entry
        if t in at:  # pool only towers with genuine radius range
            ratio_ranks.append(stats.rankdata(r1) / len(r1))
            rad_ranks.append(stats.rankdata(rad) / len(rad))
            if sc is not None:
                m = np.isfinite(sc) & np.isfinite(rad)
                sc_ranks.append(stats.rankdata(sc[m]) / m.sum())
                scrad_ranks.append(stats.rankdata(rad[m]) / m.sum())
    if ratio_ranks:
        rr = np.concatenate(ratio_ranks); dd = np.concatenate(rad_ranks)
        out["pooled_AT"]["spearman_ratioL1_radius"] = spearman(rr, dd)
        out["pooled_AT"]["spearman_ratioL1_radius_ci95"] = boot_ci(spearman, rr, dd)
        out["pooled_AT"]["n"] = len(rr)
    if sc_ranks:
        sr = np.concatenate(sc_ranks); dd2 = np.concatenate(scrad_ranks)
        out["pooled_AT"]["spearman_SC_radius"] = spearman(sr, dd2)
        out["pooled_AT"]["spearman_SC_radius_ci95"] = boot_ci(spearman, sr, dd2)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eps", type=float, default=2/255)
    args = ap.parse_args()
    eps_tag = f"{args.eps:.5f}"
    rows = load_panel(eps_tag)
    towers = [r["tower"] for r in rows]
    S = [r["S"] for r in rows]
    out = {"eps": args.eps, "n_towers": len(rows), "towers": towers}

    def block_for(subset_rows, label):
        S_ = [r["S"] for r in subset_rows]
        b = {}
        for key, name in [("sc", "SC_pred"), ("sc_cos", "SC_cos"), ("e1", "eta_over_L1"),
                          ("e2", "eta_over_L2"), ("clean", "clean_acc")]:
            b[name] = corr_block([r[key] for r in subset_rows], S_)
        b["_n"] = len(subset_rows)
        b["_towers"] = [r["tower"] for r in subset_rows]
        b["_S"] = S_
        return b

    out["full_panel"] = block_for(rows, "full")
    out["AT_only"] = block_for([r for r in rows if r["is_at"]], "AT")
    out["nonAT_only"] = block_for([r for r in rows if not r["is_at"]], "nonAT")

    # partial correlations on full panel
    e1 = [r["e1"] for r in rows]; clean = [r["clean"] for r in rows]; is_at = [r["is_at"] for r in rows]
    out["partial_etaL1_S_given_clean"] = {
        "value": partial_corr(e1, S, clean),
        "ci95": boot_ci(lambda a, b, c: partial_corr(a, b, c), np.array(e1), np.array(S), np.array(clean))}
    out["partial_etaL1_S_given_clean_and_isAT"] = {
        "value": partial_corr(e1, S, np.c_[clean, is_at])}
    sc = [r["sc"] for r in rows]; sc_cos = [r["sc_cos"] for r in rows]
    out["partial_SCcos_S_given_isAT"] = {"value": partial_corr(sc_cos, S, is_at)}
    out["partial_etaL1_S_given_isAT"] = {"value": partial_corr(e1, S, is_at)}

    # SC range note
    out["consistency_ranges"] = {
        "SC_pred_range": [min(r["sc"] for r in rows), max(r["sc"] for r in rows)],
        "SC_cos_range": [min(r["sc_cos"] for r in rows), max(r["sc_cos"] for r in rows)]}

    # selection regret (full panel)
    oracle = max(S)
    def regret(vals, hib=True):
        j = int(np.argmax(vals)) if hib else int(np.argmin(vals))
        return oracle - S[j], towers[j]
    out["selection_regret"] = {"oracle_S": oracle, "oracle_tower": towers[int(np.argmax(S))]}
    for key, name in [("e1", "eta_over_L1"), ("sc", "SC_pred"), ("sc_cos", "SC_cos"),
                      ("clean", "clean_acc")]:
        reg, pick = regret([r[key] for r in rows])
        out["selection_regret"][name] = {"pick": pick, "regret_pts": reg * 100}

    out["per_image"] = per_image_dissociation()

    outp = os.path.join(RESULTS, f"c1_analysis_extended_eps{int(round(args.eps*255))}.json")
    json.dump(out, open(outp, "w"), indent=2, default=str)

    # print
    print(f"\n===== C1 EXTENDED (eps={args.eps:.4f}, {len(rows)} towers) =====")
    print(f"{'tower':20} {'clean':>6} {'SCpred':>7} {'SCcos':>7} {'eta/L1':>9} {'S':>6}")
    for r in rows:
        print(f"{r['tower']:20} {r['clean']:6.3f} {r['sc']:7.4f} {r['sc_cos']:7.4f} "
              f"{r['e1']:9.5f} {r['S']:6.3f}")
    for blk in ["full_panel", "AT_only", "nonAT_only"]:
        b = out[blk]
        print(f"\n--- {blk} (n={b['_n']}, towers={b['_towers']}) ---")
        for name in ["SC_pred", "SC_cos", "eta_over_L1", "eta_over_L2", "clean_acc"]:
            v = b[name]
            print(f"  {name:12} pearson={v['pearson']:+.3f} "
                  f"CI({v['pearson_ci95'][0]:+.2f},{v['pearson_ci95'][1]:+.2f}) "
                  f"spearman={v['spearman']:+.3f} perm_p={v['perm_p']:.3f}")
    print(f"\nSC_pred range: {out['consistency_ranges']['SC_pred_range']}")
    print(f"SC_cos  range: {out['consistency_ranges']['SC_cos_range']}")
    print(f"\npartial(eta/L1,S|clean)      = {out['partial_etaL1_S_given_clean']['value']:+.3f}")
    print(f"partial(eta/L1,S|clean,isAT) = {out['partial_etaL1_S_given_clean_and_isAT']['value']:+.3f}")
    print(f"partial(eta/L1,S|isAT)       = {out['partial_etaL1_S_given_isAT']['value']:+.3f}")
    print(f"partial(SC_cos,S|isAT)       = {out['partial_SCcos_S_given_isAT']['value']:+.3f}")
    pi = out["per_image"]
    print("\n--- per-image (finer-grid where available) ---")
    for t, e in pi["per_tower"].items():
        line = (f"  {t:20} n={e['n']:4} uniq={e['radius_uniq']} floor={e['floor_frac']:.2f} "
                f"sp(eta/L1,rad)={e['spearman_ratioL1_radius']:+.3f}")
        if "spearman_SC_radius" in e:
            line += f" sp(SC,rad)={e['spearman_SC_radius']:+.3f}"
        print(line)
    if pi["pooled_AT"]:
        pa = pi["pooled_AT"]
        print(f"\n  POOLED AT (n={pa.get('n')}): sp(eta/L1,rad)={pa.get('spearman_ratioL1_radius'):+.3f} "
              f"CI{tuple(round(c,3) for c in pa.get('spearman_ratioL1_radius_ci95',(0,0)))}  "
              f"sp(SC,rad)={pa.get('spearman_SC_radius'):+.3f} "
              f"CI{tuple(round(c,3) for c in pa.get('spearman_SC_radius_ci95',(0,0)))}")
    sr = out["selection_regret"]
    print(f"\nSelection regret (oracle={sr['oracle_tower']} S={sr['oracle_S']:.3f}):")
    for name in ["eta_over_L1", "SC_pred", "SC_cos", "clean_acc"]:
        print(f"  pick-by-{name:12} -> {sr[name]['pick']:20} regret={sr[name]['regret_pts']:.2f} pts")
    print("\nsaved ->", outp)


if __name__ == "__main__":
    main()
