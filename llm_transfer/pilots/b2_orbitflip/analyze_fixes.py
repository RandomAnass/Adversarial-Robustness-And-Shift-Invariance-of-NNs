#!/usr/bin/env python
"""B2 verifier fixes 1 & 2 (verify/B2_verification.md). CPU only.

FIX 1 (§3c): the eta/L axis was mis-specified (refusal margin on non-refusal tasks). Recomputed
  with the TASK-CLASS margin in fix_etaL.py -> results/etaL_taskmargin.jsonl. Here we (a) show the
  margin is now sane (M>0 ~ base accuracy, not 96-100% negative), and (b) recompute
  Spearman(R2_taskmargin, rho_G) per-family and pooled to REPLACE the meaningless -0.11.

FIX 2 (table row 3): decompose the pooled orbit-flip rate 0.564 PER FAMILY and per EDIT-TYPE, so
  the constant-classifier degeneracy (NLI = P(gold=entailment); safety near-constant refuse) is
  separated from genuine excessive invariance (sentiment antonym), and the sentiment negation
  subset (unreliable oracle, §2) is split from the clean antonym subset.

Out: results/fixes_report.txt (+ results/fixes.json). Run:
  /home/students/.conda/envs/llmtransfer/bin/python analyze_fixes.py
"""
import os, sys, json, math
import numpy as np
from scipy import stats
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
DOSE0 = "0.0"


def boot_corr(x, y, kind="spearman", n=2000, alpha=0.05, seed=0):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 4 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan"), (float("nan"), float("nan")), len(x)
    f = (lambda a, b: stats.spearmanr(a, b)[0]) if kind == "spearman" else \
        (lambda a, b: stats.pearsonr(a, b)[0])
    r = f(x, y)
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(n):
        idx = rng.integers(0, len(x), len(x))
        bs.append(f(x[idx], y[idx]))
    lo, hi = np.nanpercentile(bs, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(r), (float(lo), float(hi)), len(x)


def main():
    peri = {json.loads(l)["id"]: json.loads(l)
            for l in open(os.path.join(RES, "peritem.jsonl"))}
    tm = {json.loads(l)["id"]: json.loads(l)
          for l in open(os.path.join(RES, "etaL_taskmargin.jsonl"))}
    ids = sorted(set(peri) & set(tm))
    rows = [peri[i] for i in ids]
    fams = ["sentiment", "nli", "safety"]
    lines, out = [], {"n": len(ids), "by_family": {}}

    def P(*a):
        s = " ".join(str(x) for x in a)
        print(s); lines.append(s)

    P(f"B2 FIXES — n={len(ids)} items joined (peritem + task-margin eta/L)\n")

    # ============ FIX 1: task-class margin sanity + R2 ⊥ rho_G recompute ============
    P("=" * 78)
    P("FIX 1 — eta/L recomputed with the TASK-CLASS margin (was: refusal margin)")
    P("=" * 78)
    P("\n(a) margin sanity: fraction of items with M>0 (old refusal margin vs new task margin)")
    P(f"    {'family':10s} {'n':>4} | {'old M>0':>8} {'new M>0':>8} | {'old meanM':>9} {'new meanM':>9}")
    for fam in fams:
        fr = [r for r in rows if r["family"] == fam]
        oldM = [r["etaL"].get("M", float("nan")) for r in fr if "etaL" in r and "M" in r["etaL"]]
        newM = [tm[r["id"]].get("M", float("nan")) for r in fr]
        o_pos = float(np.mean([m > 0 for m in oldM])) if oldM else float("nan")
        n_pos = float(np.mean([m > 0 for m in newM])) if newM else float("nan")
        P(f"    {fam:10s} {len(fr):>4} | {o_pos:>8.3f} {n_pos:>8.3f} | "
          f"{np.nanmean(oldM):>9.3f} {np.nanmean(newM):>9.3f}")

    P("\n(b) Spearman(ratio, rho_G) over items that orbit-flip at dose 0 — OLD vs NEW margin.")
    P("    rho_G_emb pairs with R2 (both L2 geometry); rho_G_token is the Levenshtein budget.")
    for geom, rk in [("rho_G_emb", "R2"), ("rho_G_token", "R2"), ("rho_G_emb", "Rinf")]:
        P(f"\n    --- ratio={rk}  vs  {geom} ---")
        P(f"    {'family':10s} {'n_flip':>6} | {'OLD r':>7} {'OLD CI':>16} | {'NEW r':>7} {'NEW CI':>16}")
        for fam in fams + ["POOLED"]:
            fr = [r for r in rows if (fam == "POOLED" or r["family"] == fam)]
            flip = [r for r in fr if r["per_dose"][DOSE0]["orbit_flip"]
                    and math.isfinite(r["per_dose"][DOSE0][geom])]
            rho = [r["per_dose"][DOSE0][geom] for r in flip]
            old = [r["etaL"].get(rk, float("nan")) for r in flip]
            new = [tm[r["id"]].get(rk, float("nan")) for r in flip]
            ro, cio, no = boot_corr(old, rho)
            rn, cin, nn = boot_corr(new, rho)
            P(f"    {fam:10s} {len(flip):>6} | {ro:>+7.3f} [{cio[0]:+.2f},{cio[1]:+.2f}] | "
              f"{rn:>+7.3f} [{cin[0]:+.2f},{cin[1]:+.2f}]")
            if geom == "rho_G_emb" and rk == "R2":
                out["by_family"].setdefault(fam, {})["R2new_vs_rhoemb"] = {
                    "r": rn, "ci": cin, "n": nn, "old_r": ro}

    # ============ FIX 2: per-family + per-edit-type flip-rate decomposition ============
    P("\n" + "=" * 78)
    P("FIX 2 — orbit-flip rate DECOMPOSED (pooled 0.564 is NOT '56% excessively invariant')")
    P("=" * 78)
    P(f"\n(a) per-family orbit-flip rate @dose0  (among ALL items, and among BASE-CORRECT)")
    P(f"    {'family':10s} {'n':>4} | {'flip/all':>8} {'flip/correct':>12} {'base_acc':>8} "
      f"{'dominant_ans':>14} {'frac_dom':>8}")
    pooled_all = []
    for fam in fams:
        fr = [r for r in rows if r["family"] == fam]
        flip_all = np.mean([float(r["per_dose"][DOSE0]["orbit_flip"]) for r in fr])
        corr = [r for r in fr if r["per_dose"][DOSE0]["correct"]]
        flip_cor = np.mean([float(r["per_dose"][DOSE0]["orbit_flip"]) for r in corr]) if corr else float("nan")
        base_acc = np.mean([float(r["per_dose"][DOSE0]["correct"]) for r in fr])
        ans = [r["per_dose"][DOSE0]["model_answer_x"] for r in fr]
        top, cnt = Counter(ans).most_common(1)[0]
        pooled_all += [float(r["per_dose"][DOSE0]["orbit_flip"]) for r in fr]
        P(f"    {fam:10s} {len(fr):>4} | {flip_all:>8.3f} {flip_cor:>12.3f} {base_acc:>8.3f} "
          f"{top:>14} {cnt/len(fr):>8.3f}")
        out["by_family"].setdefault(fam, {}).update(
            {"flip_all": float(flip_all), "flip_correct": float(flip_cor),
             "base_acc": float(base_acc), "dominant_ans": top, "frac_dominant": cnt / len(fr)})
    P(f"    {'POOLED':10s} {len(pooled_all):>4} | {np.mean(pooled_all):>8.3f}   "
      f"<- the headline 0.564 that must NOT be pooled")

    P(f"\n(b) per-EDIT-TYPE flip rate @dose0 among base-correct items (splits sentiment "
      f"antonym[clean] vs negation[unreliable oracle, §2])")
    P(f"    {'family':10s} {'edit_type':>12} {'n_edits':>8} {'flip_rate':>10}")
    et = defaultdict(lambda: [0, 0])  # (fam,type) -> [flips, total] among base-correct
    for r in rows:
        if not r["per_dose"][DOSE0]["correct"]:
            continue
        types = r.get("edit_types", [])
        ef = r["per_dose"][DOSE0]["edit_flip"]
        for t, fl in zip(types, ef):
            et[(r["family"], t)][1] += 1
            if fl:
                et[(r["family"], t)][0] += 1
    for (fam, t), (fl, tot) in sorted(et.items()):
        rate = fl / tot if tot else float("nan")
        P(f"    {fam:10s} {t:>12} {tot:>8} {rate:>10.3f}")
        out["by_family"].setdefault(fam, {}).setdefault("edit_types", {})[t] = {
            "n": tot, "flip_rate": rate}

    # (c) NLI constant-classifier identity: flip_rate == P(gold=entailment)?
    P("\n(c) NLI constant-classifier check: orbit-flip on NLI is a PURE lem:ratiodegen artifact "
      "iff flip_rate(all) == P(gold=entailment) AND model says 'entailment' on ~100% of x.")
    nli = [r for r in rows if r["family"] == "nli"]
    p_gold_ent = np.mean([r["y"] == "entailment" for r in nli])
    p_model_ent = np.mean([r["per_dose"][DOSE0]["model_answer_x"] == "entailment" for r in nli])
    nli_flip = np.mean([float(r["per_dose"][DOSE0]["orbit_flip"]) for r in nli])
    P(f"    P(gold=entailment)={p_gold_ent:.3f}  P(model=entailment on x)={p_model_ent:.3f}  "
      f"NLI flip_rate(all)={nli_flip:.3f}")
    P(f"    => {'CONFIRMED pure artifact' if abs(nli_flip - p_gold_ent) < 0.03 and p_model_ent > 0.95 else 'partial'}: "
      f"the model is a near-constant 'entailment' classifier, so every gold=neutral item flips.")
    out["nli_degeneracy"] = {"p_gold_entailment": float(p_gold_ent),
                             "p_model_entailment": float(p_model_ent),
                             "nli_flip_rate": float(nli_flip)}

    with open(os.path.join(RES, "fixes_report.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(RES, "fixes.json"), "w") as f:
        json.dump(out, f, indent=2)
    P(f"\n-> results/fixes_report.txt , results/fixes.json")


if __name__ == "__main__":
    main()
