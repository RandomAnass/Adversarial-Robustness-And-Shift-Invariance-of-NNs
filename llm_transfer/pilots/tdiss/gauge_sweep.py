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

    print("=== SCALE sweep (temperature c; b=0) ===")
    for c in scales:
        M, R2 = diag_all(c, 0.0)
        sM = stats.spearmanr(M, r2).correlation
        sR = stats.spearmanr(R2, r2).correlation
        aM = auroc(-M, label); aR = auroc(-R2, label)
        out["scale_sweep"][str(c)] = {"spearman_M_r2": float(sM), "spearman_R2_r2": float(sR),
                                      "auroc_M": float(aM), "auroc_R2": float(aR),
                                      "M_mean": float(M.mean()), "R2_mean": float(R2.mean())}
        print(f"  c={c:<5} Spearman(M)={sM:+.3f} Spearman(R2)={sR:+.3f} | AUROC(M)={aM:.3f} AUROC(R2)={aR:.3f} | mean M={M.mean():.2f}")

    print("=== BIAS sweep (refusal-token logit bias b; c=1) ===")
    for b in biases:
        M, R2 = diag_all(1.0, float(b))
        sM = stats.spearmanr(M, r2).correlation
        sR = stats.spearmanr(R2, r2).correlation
        aM = auroc(-M, label); aR = auroc(-R2, label)
        out["bias_sweep"][str(b)] = {"spearman_M_r2": float(sM), "spearman_R2_r2": float(sR),
                                     "auroc_M": float(aM), "auroc_R2": float(aR),
                                     "M_mean": float(M.mean()), "R2_mean": float(R2.mean())}
        print(f"  b={b:<+3} Spearman(M)={sM:+.3f} Spearman(R2)={sR:+.3f} | AUROC(M)={aM:.3f} AUROC(R2)={aR:.3f} | mean M={M.mean():.2f}")

    # spread of each predictor's AUROC across the gauge grid = the headline number
    aM_scale = [out["scale_sweep"][str(c)]["auroc_M"] for c in scales]
    aR_scale = [out["scale_sweep"][str(c)]["auroc_R2"] for c in scales]
    aM_bias = [out["bias_sweep"][str(b)]["auroc_M"] for b in biases]
    aR_bias = [out["bias_sweep"][str(b)]["auroc_R2"] for b in biases]
    out["headline"] = {
        "auroc_M_range_scale": float(max(aM_scale) - min(aM_scale)),
        "auroc_R2_range_scale": float(max(aR_scale) - min(aR_scale)),
        "auroc_M_range_bias": float(max(aM_bias) - min(aM_bias)),
        "auroc_R2_range_bias": float(max(aR_bias) - min(aR_bias)),
        "spearman_M_range_scale": float(max(out["scale_sweep"][str(c)]["spearman_M_r2"] for c in scales)
                                        - min(out["scale_sweep"][str(c)]["spearman_M_r2"] for c in scales)),
        "spearman_R2_range_scale": float(max(out["scale_sweep"][str(c)]["spearman_R2_r2"] for c in scales)
                                         - min(out["scale_sweep"][str(c)]["spearman_R2_r2"] for c in scales)),
    }
    json.dump(out, open(os.path.join(RES, "gauge.json"), "w"), indent=2)
    print("\n=== HEADLINE (gauge) ===")
    print(json.dumps(out["headline"], indent=2))


if __name__ == "__main__":
    main()
