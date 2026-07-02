#!/usr/bin/env python3
"""
S1a head-to-head analysis: rerun the shift-invariance dissociation WITH the `tips` arm added, and
place TIPS on the consistency / eta-L axes. Reuses the exact load/stat/partial-corr machinery of
resnet_analyze.py (same bootstrap-CI + permutation-test protocol), so tips is scored identically to
the other arms. Reports, for CIFAR-10 adversarial training, over three arm sets:
    core4       = {standard, blurpool, aps, aug}                 (the capacity-matched comparison arms)
    core4+tips  = core4 + tips                                    (the head-to-head)
    all+tips    = core4 + {stdzero, maxpool} + tips              (full consistency axis)
the correlations consistency-vs-AA and matched eta/||grad M||_1-vs-AA (Pearson + bootstrap CI +
permutation p), plus the partial correlations controlling for clean accuracy. Also prints where TIPS
sits (per width/seed) and the weak-attack (FGSM/PGD) vs AutoAttack contrast for standard-trained TIPS.

Run: PYTHONNOUSERSITE=1 paper/env/cenv/bin/python tips_analyze.py
"""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from resnet_analyze import load, stat, cells, partial_corr, stat_cluster, RESDIR, ARM_LAB, SMALL_NET

CORE4 = ["standard", "blurpool", "aps", "aug"]
SETS = {"core4": CORE4, "core4+tips": CORE4 + ["tips"],
        "all+tips": CORE4 + ["stdzero", "maxpool", "tips"]}

def add_ratios(res):
    for r in res:
        r["matched"] = r["dec_margin"] / r["dec_L1"] if r.get("dec_L1") else float("nan")
        r["mismatched"] = r["dec_margin"] / r["dec_L2"] if r.get("dec_L2") else float("nan")
    return res

def analyze(ds="cifar10"):
    res = add_ratios(load("at", ds))
    if not res:
        print(f"[{ds}] no AT cells yet"); return
    have = sorted({r["arm"] for r in res})
    print(f"=== {ds} AT head-to-head ({len(res)} runs; arms present: {have}) ===")
    if "tips" not in have:
        print("  (tips AT cells not complete yet -- showing what exists)")
    c_all = cells(res, ["consist", "matched", "mismatched", "rr_l2", "aa_Linf_8_255", "clean", "dec_etaL", "dec_margin", "dec_L1"])
    for setname, arms in SETS.items():
        c = [d for d in c_all if d["arm"] in arms]
        if len(c) < 3:
            print(f"\n-- {setname}: only {len(c)} (arm,width) cells, skip --"); continue
        aa = [d["aa_Linf_8_255"] for d in c]
        s_con = stat([d["consist"] for d in c], aa, B=5000)
        s_mat = stat([d["matched"] for d in c], aa, B=5000)
        pc_con = partial_corr([d["consist"] for d in c], aa, [d["clean"] for d in c])
        pc_mat = partial_corr([d["matched"] for d in c], aa, [d["clean"] for d in c])
        print(f"\n-- {setname}  ({len(c)} arm/width cells) --")
        print(f"   consistency   vs AA : Pearson {s_con['pearson']:+.3f}  CI[{s_con['ci'][0]:+.3f},{s_con['ci'][1]:+.3f}]  Spear {s_con['spearman']:+.3f}  p={s_con['p']:.4f}   [small-net {SMALL_NET['at_consist_aa']:+.2f}]")
        print(f"   matched eta/L1 vs AA : Pearson {s_mat['pearson']:+.3f}  CI[{s_mat['ci'][0]:+.3f},{s_mat['ci'][1]:+.3f}]  Spear {s_mat['spearman']:+.3f}  p={s_mat['p']:.4f}   [small-net {SMALL_NET['at_matched_aa']:+.2f}]")
        print(f"   partial (control clean acc):  consist~AA {pc_con:+.3f}   matched~AA {pc_mat:+.3f}")
        # per-run cluster bootstrap for the head-to-head set
        if setname == "core4+tips" and len(res) > len(c):
            rr = [r for r in res if r["arm"] in arms]
            sc = stat_cluster(rr, "consist", lambda r: r.get("aa_Linf_8_255"))
            sm = stat_cluster(rr, "matched", lambda r: r.get("aa_Linf_8_255"))
            print(f"   [per-run cluster bootstrap] consist vs AA n={sc['n']}/{sc['ncell']}c Pearson {sc['pearson']:+.3f} CI[{sc['ci'][0]:+.3f},{sc['ci'][1]:+.3f}] p={sc['p']:.4f}")
            print(f"                               matched vs AA n={sm['n']}/{sm['ncell']}c Pearson {sm['pearson']:+.3f} CI[{sm['ci'][0]:+.3f},{sm['ci'][1]:+.3f}] p={sm['p']:.4f}")
    # per-cell table incl tips
    print("\n  per-cell (sorted by consistency):")
    for d in sorted(c_all, key=lambda d: -d["consist"]):
        star = " <== TIPS" if d["arm"] == "tips" else ""
        print(f"    {ARM_LAB.get(d['arm'], d['arm']):16s} w{d['w']:<4} consist {d['consist']:.4f}  AA {d['aa_Linf_8_255']:.4f}  rr {d['rr_l2']:.3f}  matchedEtaL1 {d['matched']:.4f}  clean {d['clean']:.3f}{star}")
    # raw tips runs (per seed)
    tips = [r for r in res if r["arm"] == "tips"]
    if tips:
        print("\n  TIPS raw runs (per seed):")
        for r in sorted(tips, key=lambda r: (r["w"], r["seed"])):
            print(f"    w{r['w']} s{r['seed']}: clean {r['clean']:.3f}  consist {r['consist']:.4f}  AA {r.get('aa_Linf_8_255',float('nan')):.4f}"
                  f"  PGD {r.get('pgd_Linf_8_255',float('nan')):.4f}  rr {r['rr_l2']:.3f}  matchedEtaL1 {r['matched']:.4f}"
                  f"  aa_n={r.get('aa_Linf_n','512?')}  maskOK={r.get('audit',{}).get('masking_ok')}")

def weakattack(width=1.0):
    p = os.path.join(RESDIR, f"tips_weakattack_w{width}.json")
    if not os.path.exists(p):
        print(f"\n[weak-attack] {p} not present yet"); return
    d = json.load(open(p)); arms = d["arms"]
    print(f"\n=== weak-attack vs AutoAttack (STANDARD-trained, w{width}, n={d['n']}, n_aa={d['n_aa']}) ===")
    order = [a for a in ["standard", "blurpool", "aps", "aug", "tips"] if a in arms]
    hdr = f"  {'arm':10s} {'consist':>7s} {'clean':>6s}" + "".join(f"  fgsm{k:>2}/pgd{k:>2}/aa{k:>2}" for k in ["2","4","8"])
    print(hdr)
    for a in order:
        r = arms[a]
        row = f"  {a:10s} {r['consist']:7.4f} {r['clean']:6.3f}"
        for k in ["2", "4", "8"]:
            row += f"   {r.get('fgsm_'+k,float('nan')):.2f}/{r.get('pgd_'+k,float('nan')):.2f}/{r.get('aa_'+k,float('nan')):.2f}"
        print(row + ("   <== TIPS" if a == "tips" else ""))
    # correlation of consistency with each attack across arms (does invariance track weak but not strong?)
    from scipy.stats import pearsonr
    con = np.array([arms[a]["consist"] for a in order])
    print("  across-arm Pearson(consistency, robust-acc):")
    for k in ["2", "4", "8"]:
        for att in ["fgsm", "pgd", "aa"]:
            vals = [arms[a].get(f"{att}_{k}") for a in order]
            if all(v is not None for v in vals) and len(order) >= 3:
                r = pearsonr(con, np.array(vals, float))[0]
                print(f"    eps{k}/255 {att.upper():4s}: r(consist, robust) = {r:+.3f}", end="   ")
        print()

if __name__ == "__main__":
    analyze("cifar10")
    for w in (1.0, 0.5):
        weakattack(w)
