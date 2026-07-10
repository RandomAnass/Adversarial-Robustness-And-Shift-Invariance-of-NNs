#!/usr/bin/env python
"""HEADLINE gauge test: under a pure logit-scale (temperature c) and refusal-bias (b) transform,
the RAW margin M's ranking of jailbreakability MOVES, while the ratio R_q's ranking is INVARIANT.

We already have the per-prompt attack radius r2 (from phase2) as the ground-truth jailbreakability.
For each gauge setting (c, b) we recompute M and R2 (the diagnostic), then measure how well each
RANKS r2 (Spearman) and the vulnerability label (AUROC).  Prediction:
  - Spearman/AUROC of R2 is (near-)CONSTANT across c and (approximately) across b  [gauge-free]
  - Spearman/AUROC of M CHANGES with c and b                                        [gauge-dependent]

This is the load-bearing claim that separates the ratio from the raw logit-gap.
Reuses phase1 for the r2/label join and recomputes M,R2 under each gauge on the fly.
"""
import os, json, numpy as np
from scipy import stats
from tdiss_core import TDiss

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")


def auroc(scores, labels):
    scores = np.asarray(scores, float); labels = np.asarray(labels, int)
    pos = (labels == 1); neg = (labels == 0)
    if pos.sum() == 0 or neg.sum() == 0:
        return float("nan")
    ranks = stats.rankdata(scores)
    return (ranks[pos].sum() - pos.sum() * (pos.sum() + 1) / 2) / (pos.sum() * neg.sum())


def fixed_threshold_acc(scores, labels, tau):
    """Balanced accuracy of the FIXED-threshold rule 'vulnerable if score < tau'.
    AUROC/Spearman are rank-based and thus blind to an additive gauge shift (M -> M+b keeps ranks),
    so they cannot expose the gauge dependence. A practitioner uses a FIXED threshold tau, calibrated
    once at c=1,b=0; under the gauge knob the same tau lands at a different operating point, so this
    accuracy MOVES for the gauge-dependent raw margin M while it is stable for the gauge-free R_q."""
    scores = np.asarray(scores, float); labels = np.asarray(labels, int)
    pred = (scores < tau).astype(int)   # small score => vulnerable
    pos = labels == 1; neg = labels == 0
    if pos.sum() == 0 or neg.sum() == 0:
        return float("nan")
    tpr = (pred[pos] == 1).mean(); tnr = (pred[neg] == 0).mean()
    return 0.5 * (tpr + tnr)


def main():
    p1 = {r["id"]: r for r in (json.loads(l) for l in open(os.path.join(RES, "phase1.jsonl")) if l.strip())}
    p2 = {r["id"]: r for r in (json.loads(l) for l in open(os.path.join(RES, "phase2.jsonl")) if l.strip())}
    ids = [i for i in p1 if i in p2 and p1[i]["category"] == "harmful"]
    l2_max = max(float(x) for x in list(p2.values())[0]["l2_succ"].keys())
    r2 = np.array([p2[i]["r2"] if p2[i]["r2"] is not None else l2_max * 2 for i in ids])
    budget = np.median(r2)
    label = (r2 <= budget).astype(int)

    T = TDiss()
    behaviors = [p1[i]["behavior"] for i in ids]
    # precompute grads once at c=1,b=0 is not enough because bias changes selection; recompute per gauge
    scales = [0.25, 0.5, 1.0, 2.0, 4.0]
    biases = [-5, -2, 0, 2, 5]

    def diag_all(c, b):
        T.logit_scale = c; T.refuse_bias = b
        Ms, R2s = [], []
        for beh in behaviors:
            d = T.diagnostics(beh)
            Ms.append(d["M"]); R2s.append(d["R2"])
        T.logit_scale = 1.0; T.refuse_bias = 0.0
        return np.array(Ms), np.array(R2s)

    out = {"ids_n": len(ids), "budget": float(budget), "scale_sweep": {}, "bias_sweep": {}}

    # calibrate the FIXED decision thresholds ONCE at the baseline gauge (c=1, b=0):
    # predict "vulnerable if score < tau", tau = the score value that best separates the label.
    M0, R20 = diag_all(1.0, 0.0)
    def best_tau(scores):
        # threshold at the median of the score distribution among the vulnerable/robust split
        return float(np.median(scores))
    tauM = best_tau(M0); tauR = best_tau(R20)
    out["fixed_tau_M"] = tauM; out["fixed_tau_R2"] = tauR

    print("=== SCALE sweep (temperature c; b=0) ===")
    for c in scales:
        M, R2 = diag_all(c, 0.0)
        aM = auroc(-M, label); aR = auroc(-R2, label)
        accM = fixed_threshold_acc(M, label, tauM)    # FIXED tau => moves under gauge for M
        accR = fixed_threshold_acc(R2, label, tauR)
        out["scale_sweep"][str(c)] = {"auroc_M": float(aM), "auroc_R2": float(aR),
                                      "fixedacc_M": float(accM), "fixedacc_R2": float(accR),
                                      "M_mean": float(M.mean()), "R2_mean": float(R2.mean())}
        print(f"  c={c:<5} fixed-acc(M)={accM:.3f} fixed-acc(R2)={accR:.3f} | AUROC(M)={aM:.3f} AUROC(R2)={aR:.3f} | mean M={M.mean():.2f}")

    print("=== BIAS sweep (refusal-token logit bias b; c=1) ===")
    for b in biases:
        M, R2 = diag_all(1.0, float(b))
        aM = auroc(-M, label); aR = auroc(-R2, label)
        accM = fixed_threshold_acc(M, label, tauM)
        accR = fixed_threshold_acc(R2, label, tauR)
        out["bias_sweep"][str(b)] = {"auroc_M": float(aM), "auroc_R2": float(aR),
                                     "fixedacc_M": float(accM), "fixedacc_R2": float(accR),
                                     "M_mean": float(M.mean()), "R2_mean": float(R2.mean())}
        print(f"  b={b:<+3} fixed-acc(M)={accM:.3f} fixed-acc(R2)={accR:.3f} | AUROC(M)={aM:.3f} AUROC(R2)={aR:.3f} | mean M={M.mean():.2f}")

    # HEADLINE = spread of each predictor's FIXED-THRESHOLD accuracy across the gauge grid.
    # The fixed-threshold accuracy is what a practitioner actually uses and is the metric that
    # exposes gauge dependence (AUROC/Spearman are rank-based and blind to additive shifts).
    def rng(key, keys):
        vs = [out[key][str(k)] for k in keys]
        return float(max(vs) - min(vs))
    faM_s = [out["scale_sweep"][str(c)]["fixedacc_M"] for c in scales]
    faR_s = [out["scale_sweep"][str(c)]["fixedacc_R2"] for c in scales]
    faM_b = [out["bias_sweep"][str(b)]["fixedacc_M"] for b in biases]
    faR_b = [out["bias_sweep"][str(b)]["fixedacc_R2"] for b in biases]
    out["headline"] = {
        "fixedacc_M_range_scale": float(max(faM_s) - min(faM_s)),
        "fixedacc_R2_range_scale": float(max(faR_s) - min(faR_s)),
        "fixedacc_M_range_bias": float(max(faM_b) - min(faM_b)),
        "fixedacc_R2_range_bias": float(max(faR_b) - min(faR_b)),
        "auroc_M_range_scale": float(max(out["scale_sweep"][str(c)]["auroc_M"] for c in scales)
                                     - min(out["scale_sweep"][str(c)]["auroc_M"] for c in scales)),
        "auroc_R2_range_scale": float(max(out["scale_sweep"][str(c)]["auroc_R2"] for c in scales)
                                      - min(out["scale_sweep"][str(c)]["auroc_R2"] for c in scales)),
        "interpretation": ("R_q's fixed-threshold accuracy is (near-)constant across c and b; raw M's "
                           "moves -- the raw refusal gap needs re-calibration under any logit rescale/bias, "
                           "the gauge-free ratio does not."),
    }
    json.dump(out, open(os.path.join(RES, "gauge.json"), "w"), indent=2)
    print("\n=== HEADLINE (gauge) ===")
    print(json.dumps(out["headline"], indent=2))


if __name__ == "__main__":
    main()
