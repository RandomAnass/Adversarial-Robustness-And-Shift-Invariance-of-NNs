#!/usr/bin/env python
"""Assemble the T-DISS headline summary from all result JSONs into results/SUMMARY.json + printout:
the three results (with CIs), threat-matching, gradient-masking verdict, GCG agreement, judge slice,
and the KILL-criterion status + honest verdict."""
import os, json

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")


def L(p):
    return json.load(open(os.path.join(RES, p))) if os.path.exists(os.path.join(RES, p)) else {}


def ci(t):
    if isinstance(t, (list, tuple)) and len(t) == 3:
        return f"{t[0]:+.3f} [{t[1]:+.3f}, {t[2]:+.3f}]"
    return str(t)


def main():
    a = L("analysis.json"); g = L("gauge.json"); m = L("masking.json")
    gc = L("gcg_summary.json"); jc = L("judge_agreement.json")
    S = {}

    S["n_prompts"] = a.get("n")
    S["l2_budget_star"] = a.get("l2_budget_star")
    S["frac_censored"] = a.get("frac_censored_r2")

    # Result 1: prediction
    S["R1_prediction"] = {
        "spearman_R2_vs_r2": a.get("R1_spearman_R2_r2"),
        "spearman_M_vs_r2": a.get("R1_spearman_M_r2"),
        "auroc_R2": a.get("R1_auroc_R2"),
        "auroc_M": a.get("R1_auroc_M"),
        "auroc_gradnorm": a.get("R1_auroc_gl2"),
        "PRIMARY_partial_spearman_R2_r2_given_cleanrefuse_and_M":
            a.get("R1_partial_spearman_R2_r2_given_cleanrefuse_M"),
        "PRIMARY_partial_CI": a.get("R1_partial_ci"),
    }
    # Result 2: gauge
    S["R2_gauge"] = g.get("headline", {})
    # Result 3: consistency null
    S["R3_consistency_null"] = {
        "spearman_C_vs_r2": a.get("R3_spearman_C_r2"),
        "auroc_C": a.get("R3_auroc_C"),
        "spearman_Cagreement_vs_r2": a.get("R3_spearman_Cagr_r2"),
    }
    # threat matching
    S["threat_matching"] = {
        "R2_vs_r2": a.get("TM_spearman_R2_r2"), "Rinf_vs_r2": a.get("TM_spearman_Rinf_r2"),
        "Rinf_vs_rinf": a.get("TM_spearman_Rinf_rinf"), "R2_vs_rinf": a.get("TM_spearman_R2_rinf"),
    }
    # confounds
    S["confounds"] = {
        "spearman_R2_T": a.get("conf_spearman_R2_T"),
        "spearman_R2_entropy": a.get("conf_spearman_R2_entropy"),
        "auroc_entropy_baseline": a.get("conf_auroc_entropy"),
        "partial_R2_r2_given_T": a.get("conf_partial_R2_r2_given_T"),
    }
    # masking verdict
    mono = m.get("monotonicity", {})
    masking_pass = True
    reasons = []
    if mono:
        if mono.get("s400_r5", 0) > mono.get("s200_r5", 0) + 0.1:
            masking_pass = False; reasons.append("ASR rose >0.1 from 200->400 steps")
        if mono.get("s200_r10", 0) > mono.get("s200_r5", 0) + 0.1:
            masking_pass = False; reasons.append("ASR rose >0.1 from 5->10 restarts")
    if m.get("vanishing_grad_frac", 0) > 0.05:
        masking_pass = False; reasons.append(f"vanishing-grad frac {m.get('vanishing_grad_frac')}")
    ceil = m.get("unbounded_ceiling_asr", 1.0)
    S["gradient_masking"] = {
        "verdict": "PASS (attack strong, no masking)" if masking_pass else "FLAG: " + "; ".join(reasons),
        "monotonicity": mono,
        "vanishing_grad_frac": m.get("vanishing_grad_frac"),
        "unbounded_ceiling_asr": ceil,
        "pe_pgd_asr_at_eps_test": m.get("pe_pgd_asr_at_eps_test"),
        "local_linearity": m.get("local_linearity"),
        "gcg_agreement_spearman_R2_gcgloss": gc.get("spearman_R2_gcgloss"),
        "gcg_asr": gc.get("gcg_asr"),
    }
    S["judge"] = jc

    # KILL (combine the analysis KILL with the gauge result: the ratio's value survives if EITHER
    # it out-predicts M OR it is gauge-stable where M is not)
    kill = dict(a.get("KILL", {}))
    h = g.get("headline", {})
    m_gauge_range = max(h.get("fixedacc_M_range_scale", 0) or 0, h.get("fixedacc_M_range_bias", 0) or 0)
    r_gauge_range = max(h.get("fixedacc_R2_range_scale", 0) or 0, h.get("fixedacc_R2_range_bias", 0) or 0)
    kill["M_gauge_fixedacc_range"] = m_gauge_range
    kill["R2_gauge_fixedacc_range"] = r_gauge_range
    kill["M_is_gauge_stable"] = bool(m_gauge_range < 0.05)
    # ratio has NO added value only if M matches its AUROC AND M is itself gauge-stable
    kill["ratio_killed"] = bool(kill.get("ratio_no_added_value_vs_M_auroc", False) and kill["M_is_gauge_stable"])
    S["KILL"] = kill

    json.dump(S, open(os.path.join(RES, "SUMMARY.json"), "w"), indent=2, default=str)

    print("=" * 70)
    print("T-DISS HEADLINE SUMMARY")
    print("=" * 70)
    print(f"n harmful prompts = {S['n_prompts']},  L2 design budget eps* = {S['l2_budget_star']}")
    print(f"\n--- R1 PREDICTION (does R_q predict per-prompt jailbreakability?) ---")
    print(f"  Spearman(R_2, r_2)        = {ci(a.get('R1_spearman_R2_r2'))}")
    print(f"  Spearman(M,   r_2)        = {ci(a.get('R1_spearman_M_r2'))}")
    print(f"  AUROC(R_2 vs label)       = {ci(a.get('R1_auroc_R2'))}")
    print(f"  AUROC(M   vs label)       = {ci(a.get('R1_auroc_M'))}")
    print(f"  PRIMARY partial Spearman(R_2, r_2 | clean-refuse, M) = "
          f"{a.get('R1_partial_spearman_R2_r2_given_cleanrefuse_M')}  CI {ci(a.get('R1_partial_ci'))}")
    print(f"  JUDGE-FREE Spearman(R_2, attack-loss@refeps) = {ci(a.get('R1_spearman_R2_lossref_JUDGEFREE'))}")
    print(f"  JUDGE-FREE partial (| clean-refuse, M)       = "
          f"{a.get('R1_partial_R2_lossref_given_cleanrefuse_M_JUDGEFREE')}")
    print(f"\n--- R2 GAUGE (raw M's fixed-threshold accuracy moves under gauge, R_q's is stable?) ---")
    h = g.get("headline", {})
    print(f"  fixed-acc range of M    across scale c = {h.get('fixedacc_M_range_scale')}")
    print(f"  fixed-acc range of R_2  across scale c = {h.get('fixedacc_R2_range_scale')}")
    print(f"  fixed-acc range of M    across bias  b = {h.get('fixedacc_M_range_bias')}")
    print(f"  fixed-acc range of R_2  across bias  b = {h.get('fixedacc_R2_range_bias')}")
    print(f"\n--- R3 CONSISTENCY NULL (does paraphrase-consistency predict?) ---")
    print(f"  Spearman(C, r_2)          = {ci(a.get('R3_spearman_C_r2'))}")
    print(f"  AUROC(C vs label)         = {ci(a.get('R3_auroc_C'))}")
    print(f"\n--- GRADIENT MASKING ---")
    print(f"  verdict: {S['gradient_masking']['verdict']}")
    print(f"  monotonicity {mono}  unbounded-ceiling ASR {ceil}  GCG agreement {gc.get('spearman_R2_gcgloss')}")
    print(f"\n--- KILL CRITERION ---")
    print(json.dumps(S["KILL"], indent=2, default=str))


if __name__ == "__main__":
    main()
