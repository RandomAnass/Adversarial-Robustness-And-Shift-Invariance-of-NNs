#!/usr/bin/env python
"""Cross-checkpoint (SECONDARY) trade-off test: two genuinely different models (Llama-3-8B vs
Qwen2.5-7B) at their base (dose 0) give two points that differ in MEASURED paraphrase-invariance
WITHOUT the synthetic-dose confound. Tests: does the more paraphrase-invariant model have the
larger orbit-flip rate / smaller rho_G? (a clean between-model instantiation of the trade-off).

Also reports both models' rho_G distribution, orbit-flip rate, budget-law fraction, and the
decoupling, so the appendix cross-point stands on its own. Reads results/peritem.jsonl (Llama)
and results/peritem_qwen.jsonl (Qwen). Writes results/cross_model.json.
"""
import os, json, math
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")


def load(path):
    return [json.loads(l) for l in open(path) if "per_dose" in json.loads(l)]


def stats_for(rows, d="0.0"):
    flips = [r["per_dose"][d]["orbit_flip"] for r in rows]
    rate = float(np.mean(flips))
    rho = [r["per_dose"][d]["rho_G_emb"] for r in rows if r["per_dose"][d]["orbit_flip"]
           and math.isfinite(r["per_dose"][d]["rho_G_emb"])]
    minv = float(np.mean([r["per_dose"][d]["measured_invariance"] for r in rows]))
    acc = float(np.mean([r["per_dose"][d]["correct"] for r in rows]))
    # budget law
    hold, tot = 0, 0
    for r in rows:
        if not r["per_dose"][d]["orbit_flip"]:
            continue
        rr = r["per_dose"][d]["rho_G_emb"]
        if not math.isfinite(rr):
            continue
        tot += 1
        ok = all((not fl) or (e >= rr - 1e-6) for e, fl in zip(r["emb_disps"], r["per_dose"][d]["edit_flip"]))
        hold += int(ok)
    return {"n": len(rows), "orbit_flip_rate": rate, "rho_emb_median": float(np.median(rho)) if rho else None,
            "rho_emb_mean": float(np.mean(rho)) if rho else None, "measured_invariance": minv,
            "base_acc": acc, "budget_law_fraction": (hold / tot) if tot else None, "n_flip": int(sum(flips))}


def per_family(rows, d="0.0"):
    out = {}
    for fam in sorted({r["family"] for r in rows}):
        fr = [r for r in rows if r["family"] == fam]
        out[fam] = {"n": len(fr), "flip": float(np.mean([r["per_dose"][d]["orbit_flip"] for r in fr])),
                    "measured_inv": float(np.mean([r["per_dose"][d]["measured_invariance"] for r in fr]))}
    return out


def main():
    llama = load(os.path.join(RES, "peritem.jsonl"))
    qpath = os.path.join(RES, "peritem_qwen.jsonl")
    if not os.path.exists(qpath):
        print("Qwen results not found; run the Qwen arm first."); return
    qwen = load(qpath)

    L = stats_for(llama); Q = stats_for(qwen)
    print("=== Cross-checkpoint (base, dose 0) ===")
    for name, S in [("Llama-3-8B", L), ("Qwen2.5-7B", Q)]:
        print(f"  {name:12s}: flip {S['orbit_flip_rate']:.3f}  measured-inv {S['measured_invariance']:.3f}  "
              f"rho_emb med {S['rho_emb_median']}  base-acc {S['base_acc']:.3f}  budget-law {S['budget_law_fraction']}")
    print("\n  Between-model trade-off point:")
    hi, lo = (L, Q) if L["measured_invariance"] >= Q["measured_invariance"] else (Q, L)
    hi_name = "Llama" if hi is L else "Qwen"; lo_name = "Qwen" if hi is L else "Llama"
    print(f"    more paraphrase-invariant model = {hi_name} (minv {hi['measured_invariance']:.3f} vs "
          f"{lo['measured_invariance']:.3f})")
    print(f"    its orbit-flip rate = {hi['orbit_flip_rate']:.3f} vs {lo['orbit_flip_rate']:.3f} "
          f"({'HIGHER -> trade-off holds between models' if hi['orbit_flip_rate']>lo['orbit_flip_rate'] else 'not higher -> trade-off absent between these two'})")

    print("\n=== Per-family (dose 0) ===")
    LF = per_family(llama); QF = per_family(qwen)
    for fam in sorted(LF):
        print(f"  {fam:10s}: Llama flip {LF[fam]['flip']:.3f} (minv {LF[fam]['measured_inv']:.3f}) | "
              f"Qwen flip {QF[fam]['flip']:.3f} (minv {QF[fam]['measured_inv']:.3f})")

    out = {"llama": L, "qwen": Q, "llama_per_family": LF, "qwen_per_family": QF,
           "between_model_tradeoff": {
               "more_invariant_model": hi_name,
               "more_invariant_minv": hi["measured_invariance"], "less_invariant_minv": lo["measured_invariance"],
               "more_invariant_flip": hi["orbit_flip_rate"], "less_invariant_flip": lo["orbit_flip_rate"],
               "tradeoff_holds": bool(hi["orbit_flip_rate"] > lo["orbit_flip_rate"])}}
    with open(os.path.join(RES, "cross_model.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote", os.path.join(RES, "cross_model.json"))


if __name__ == "__main__":
    main()
