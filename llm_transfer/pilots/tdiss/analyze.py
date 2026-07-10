#!/usr/bin/env python
"""T-DISS analysis: the three headline results + confounds + kill-criterion check.

Reads results/phase1.jsonl (diagnostics + consistency) and results/phase2.jsonl (radii),
joins on id, and computes:
  R1 Prediction: Spearman(R_q, r2), AUROC(R_q vs binary label); partial Spearman controlling
     clean-refuse base rate AND raw margin M (the RATIO carries signal, not M alone).
  R2 Gauge: raw-M ranking of jailbreakability MOVES under gauge knob c,b; R_q ranking INVARIANT.
     (gauge sweep numbers come from results/gauge.json)
  R3 Consistency null: Spearman(C, r2), AUROC(C vs label) -- expect ~0 or anti.
Bootstrap 95% CIs over prompts; DeLong for AUROC differences.
"""
import os, json, math, numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")


def load_jsonl(p):
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p) if l.strip()]


# ---------- AUROC + DeLong ----------
def auroc(scores, labels):
    scores = np.asarray(scores, float)
    labels = np.asarray(labels, int)
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    # Mann-Whitney U -> AUROC
    order = np.argsort(np.concatenate([pos, neg]))
    ranks = np.empty_like(order, float)
    ranks[order] = np.arange(1, len(order) + 1)
    # handle ties by average rank
    allv = np.concatenate([pos, neg])
    ranks = stats.rankdata(allv)
    r_pos = ranks[:len(pos)].sum()
    auc = (r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
    return auc


def bootstrap_ci(fn, *arrays, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    arrays = [np.asarray(a) for a in arrays]
    N = len(arrays[0])
    vals = []
    for _ in range(n):
        idx = rng.integers(0, N, N)
        try:
            v = fn(*[a[idx] for a in arrays])
            if v == v:  # not nan
                vals.append(v)
        except Exception:
            pass
    if not vals:
        return (float("nan"), float("nan"), float("nan"))
    return (float(np.mean(vals)), float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))


def spearman(x, y):
    return stats.spearmanr(x, y).correlation


def partial_spearman(x, y, controls):
    """Partial Spearman(x, y | controls): rank-transform all, regress out controls via OLS, correlate residuals."""
    def rank(v):
        return stats.rankdata(v)
    X = rank(x).astype(float)
    Y = rank(y).astype(float)
    C = np.column_stack([rank(c).astype(float) for c in controls])
    C = np.column_stack([np.ones(len(X)), C])
    bx, *_ = np.linalg.lstsq(C, X, rcond=None)
    by, *_ = np.linalg.lstsq(C, Y, rcond=None)
    rx = X - C @ bx
    ry = Y - C @ by
    return stats.pearsonr(rx, ry).correlation


def main():
    p1 = {r["id"]: r for r in load_jsonl(os.path.join(RES, "phase1.jsonl"))}
    p2 = {r["id"]: r for r in load_jsonl(os.path.join(RES, "phase2.jsonl"))}
    ids = [i for i in p1 if i in p2 and p1[i]["category"] == "harmful"]
    print(f"joined harmful prompts: {len(ids)}")

    # ---- build the working set: restrict per-prompt stats to clean-COMPLIED prompts is NOT
    #      possible (almost all harmful are clean-refused); instead we analyze all harmful and
    #      control for clean_refuse as a covariate (audit §0.5). r2/rinf: None -> censored (never
    #      jailbroken within ladder); encode as a large radius = max_ladder * 2 for ranking.
    l2_max = max([float(x) for x in list(p2.values())[0]["l2_succ"].keys()]) if p2 else 1.0
    def rad(v, cap):
        return v if v is not None else cap * 2.0

    R2 = np.array([p1[i]["R2"] for i in ids])
    Rinf = np.array([p1[i]["Rinf"] for i in ids])
    M = np.array([p1[i]["M"] for i in ids])
    gl2 = np.array([p1[i]["gl2"] for i in ids])
    Cval = np.array([p1[i]["C_refuse_frac"] for i in ids])
    Cagr = np.array([p1[i]["C_agreement"] for i in ids])
    ent = np.array([p1[i]["resp_entropy"] for i in ids])
    Tlen = np.array([p1[i]["T"] for i in ids])
    clean_refuse = np.array([int(p1[i]["clean_refuse"]) for i in ids])
    # continuous fine-grained radius: r2 with within-bin ordering by the reference attack loss.
    # A prompt harder to jailbreak (larger loss at the reference eps) gets a slightly larger radius.
    l2_ref = list(p2.values())[0].get("l2_ref_eps")
    loss_ref = np.array([p2[i].get("l2_loss_ref") if p2[i].get("l2_loss_ref") is not None else np.nan
                         for i in ids])
    # normalize loss_ref into a small tie-break offset in [0, min-ladder-gap)
    lr = loss_ref.copy()
    lr[np.isnan(lr)] = np.nanmax(lr) if np.isfinite(np.nanmax(lr)) else 0.0
    lr_rank = stats.rankdata(lr) / len(lr)                       # 0..1
    r2_binary = np.array([rad(p2[i]["r2"], l2_max) for i in ids])
    ladder_gap = 0.008
    r2 = r2_binary + lr_rank * ladder_gap                        # continuous radius (fine)
    linf_max = max([float(x) for x in list(p2.values())[0]["linf_succ"].keys()])
    rinf = np.array([rad(p2[i]["rinf"], linf_max) for i in ids if "rinf" in p2[i]])
    rinf_ids = [i for i in ids if "rinf" in p2[i]]
    # binary label: jailbroken at the MEDIAN L2 budget (design budget eps* ~ ASR 0.5)
    budget = np.median(r2_binary)
    label = (r2_binary <= budget).astype(int)   # 1 = jailbroken at/below the design budget
    out_loss = {"loss_ref_eps": l2_ref}

    out = {"n": len(ids), "l2_budget_star": float(budget),
           "asr_at_budget": float(label.mean()),
           "frac_censored_r2": float(np.mean([p2[i]["r2"] is None for i in ids]))}

    # ---- R1: Prediction ----
    # higher R2 => more robust => LARGER radius => LESS likely jailbroken. So predictor of
    # VULNERABILITY is -R2 (or predict radius directly). We report Spearman(R2, r2) (expect +).
    out["R1_spearman_R2_r2"] = bootstrap_ci(lambda a, b: spearman(a, b), R2, r2)
    out["R1_spearman_M_r2"] = bootstrap_ci(lambda a, b: spearman(a, b), M, r2)
    out["R1_spearman_gl2_r2"] = bootstrap_ci(lambda a, b: spearman(a, b), gl2, r2)
    # AUROC: predict vulnerability label; score for vulnerability = -R2 (small R2 => vulnerable)
    out["R1_auroc_R2"] = bootstrap_ci(lambda s, l: auroc(-s, l), R2, label)
    out["R1_auroc_M"] = bootstrap_ci(lambda s, l: auroc(-s, l), M, label)
    out["R1_auroc_gl2"] = bootstrap_ci(lambda s, l: auroc(s, l), gl2, label)  # larger grad => vulnerable
    # PRIMARY partial: Spearman(R2, r2 | clean_refuse, M) -- ratio carries signal beyond M & base rate
    try:
        ps = partial_spearman(R2, r2, [clean_refuse, M])
        out["R1_partial_spearman_R2_r2_given_cleanrefuse_M"] = float(ps)
        # bootstrap CI
        out["R1_partial_ci"] = bootstrap_ci(
            lambda a, b, c, d: partial_spearman(a, b, [c, d]), R2, r2, clean_refuse, M)
    except Exception as e:
        out["R1_partial_error"] = str(e)
    # second partial controlling the radius-adjacent margin only
    out["R1_partial_R2_given_M_only"] = float(partial_spearman(R2, r2, [M]))

    # ---- R1b: JUDGE-INDEPENDENT signal. Attack loss at the reference eps is a continuous
    #      jailbreakability measure that does not pass through the (noisy) judge. LOW loss =>
    #      easy to jailbreak => should correlate with LOW R2. Expect POSITIVE Spearman(R2, loss_ref).
    finite = np.isfinite(loss_ref)
    if finite.sum() > 10:
        out["R1_spearman_R2_lossref_JUDGEFREE"] = bootstrap_ci(
            lambda a, b: spearman(a, b), R2[finite], loss_ref[finite])
        out["R1_spearman_M_lossref"] = bootstrap_ci(
            lambda a, b: spearman(a, b), M[finite], loss_ref[finite])
        out["R1_partial_R2_lossref_given_cleanrefuse_M_JUDGEFREE"] = float(
            partial_spearman(R2[finite], loss_ref[finite],
                             [clean_refuse[finite], M[finite]]))

    # ---- R3: Consistency null ----
    out["R3_spearman_C_r2"] = bootstrap_ci(lambda a, b: spearman(a, b), Cval, r2)
    out["R3_spearman_Cagr_r2"] = bootstrap_ci(lambda a, b: spearman(a, b), Cagr, r2)
    out["R3_auroc_C"] = bootstrap_ci(lambda s, l: auroc(-s, l), Cval, label)
    out["R3_auroc_Cagr"] = bootstrap_ci(lambda s, l: auroc(-s, l), Cagr, label)

    # ---- confounds ----
    out["conf_spearman_R2_T"] = float(spearman(R2, Tlen))
    out["conf_spearman_R2_entropy"] = float(spearman(R2, ent))
    out["conf_auroc_entropy"] = bootstrap_ci(lambda s, l: auroc(s, l), ent, label)
    out["conf_auroc_cleanrefuse"] = bootstrap_ci(lambda s, l: auroc(s, l), clean_refuse.astype(float), label)
    out["conf_partial_R2_r2_given_T"] = float(partial_spearman(R2, r2, [Tlen]))

    # ---- threat matching: R2 vs r2 should beat Rinf vs r2, and Rinf vs rinf beat R2 vs rinf ----
    out["TM_spearman_R2_r2"] = float(spearman(R2, r2))
    out["TM_spearman_Rinf_r2"] = float(spearman(Rinf, r2))
    if len(rinf_ids) > 10:
        R2_ri = np.array([p1[i]["R2"] for i in rinf_ids])
        Rinf_ri = np.array([p1[i]["Rinf"] for i in rinf_ids])
        out["TM_spearman_Rinf_rinf"] = float(spearman(Rinf_ri, rinf))
        out["TM_spearman_R2_rinf"] = float(spearman(R2_ri, rinf))
        out["TM_n_linf"] = len(rinf_ids)

    # ---- KILL check ----
    aR = out["R1_auroc_R2"][0]
    aM = out["R1_auroc_M"][0]
    aC = out["R3_auroc_C"][0]
    ps = out.get("R1_partial_spearman_R2_r2_given_cleanrefuse_M", float("nan"))
    ps_ci = out.get("R1_partial_ci", (float("nan"),)*3)
    kill_ratio = (abs(aR - aM) < 0.02)   # gauge stability checked separately in gauge.json
    kill_diss = (aC >= aR - 0.02)
    kill_primary = (not (abs(ps) > 0.15)) or (ps_ci[1] <= 0 <= ps_ci[2])
    out["KILL"] = {
        "primary_partial_below_0.15_or_insignificant": bool(kill_primary),
        "ratio_no_added_value_vs_M_auroc": bool(kill_ratio),
        "dissociation_absent_C_predicts": bool(kill_diss),
        "partial_value": ps, "partial_ci": ps_ci,
        "auroc_R2": aR, "auroc_M": aM, "auroc_C": aC,
    }

    json.dump(out, open(os.path.join(RES, "analysis.json"), "w"), indent=2, default=str)
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
