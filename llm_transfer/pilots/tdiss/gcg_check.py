#!/usr/bin/env python
"""Discrete GCG cross-check (nanogcg) on a FIXED 128-prompt slice (Nasr adaptive-eval standard).

Role: confirm the per-prompt ORDERING from the continuous PE-PGD / R_q survives a genuinely
DIFFERENT (discrete, text-space) threat model. NOT to match numerically (discrete != continuous).
Reports: per-prompt GCG best loss + success, and the Spearman agreement between R_q (and r2) and
the GCG outcome = the anti-gradient-masking audit (if R_q disagrees with GCG, suspect masking).
"""
import os, json, random, csv, numpy as np, torch
import nanogcg
from nanogcg import GCGConfig
from scipy import stats
from tdiss_core import TDiss, MID
from judge import Judge

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")


def main(n_prompts=128, num_steps=250):
    T = TDiss()
    J = Judge(kind="auto")
    rows = list(csv.DictReader(open(os.path.join(HERE, "data", "prompts.csv"))))
    h = [r for r in rows if r["category"] == "harmful" and r["source"] != "xstest"]
    random.seed(42)
    slice_ = random.sample(h, min(n_prompts, len(h)))

    cfg = GCGConfig(num_steps=num_steps, search_width=256, topk=256, seed=0,
                    verbosity="ERROR", early_stop=True)
    out_path = os.path.join(RES, "gcg.jsonl")
    open(out_path, "w").close()
    recs = []
    for i, r in enumerate(slice_):
        beh = r["behavior"].strip().rstrip(".")
        target = f"Sure, here is {beh[0].lower() + beh[1:]}"
        messages = [{"role": "user", "content": r["behavior"] + " {optim_str}"}]
        try:
            res = nanogcg.run(T.model, T.tok, messages, target, cfg)
            best_loss = float(res.best_loss)
            adv = res.best_string
            # generate with the adversarial suffix appended, judge it
            full = r["behavior"] + " " + adv
            gen = T.generate_text(full, max_new_tokens=48)
            succ = bool(J(r["behavior"], gen))
        except Exception as e:
            best_loss = float("nan"); succ = None; adv = f"ERR:{e}"
        rec = {"id": r["id"], "gcg_best_loss": best_loss, "gcg_success": succ}
        recs.append(rec)
        with open(out_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        if i % 16 == 0:
            print(f"[gcg] {i}/{len(slice_)} loss={best_loss:.3f} succ={succ}", flush=True)

    # agreement with R_q / r2 (join phase1/phase2)
    p1 = {x["id"]: x for x in (json.loads(l) for l in open(os.path.join(RES, "phase1.jsonl")) if l.strip())} \
        if os.path.exists(os.path.join(RES, "phase1.jsonl")) else {}
    p2 = {x["id"]: x for x in (json.loads(l) for l in open(os.path.join(RES, "phase2.jsonl")) if l.strip())} \
        if os.path.exists(os.path.join(RES, "phase2.jsonl")) else {}
    summ = {"n": len(recs), "gcg_asr": float(np.mean([int(bool(x["gcg_success"])) for x in recs if x["gcg_success"] is not None]))}
    ids = [x["id"] for x in recs if x["id"] in p1 and x["id"] in p2 and x["gcg_success"] is not None]
    if len(ids) > 10:
        R2 = np.array([p1[i]["R2"] for i in ids])
        l2max = max(float(k) for k in list(p2.values())[0]["l2_succ"].keys())
        r2 = np.array([p2[i]["r2"] if p2[i]["r2"] is not None else l2max * 2 for i in ids])
        gloss = np.array([[x for x in recs if x["id"] == i][0]["gcg_best_loss"] for i in ids])
        # GCG loss LOW => easy to jailbreak => small r2 & small R2. Expect POSITIVE Spearman(R2, gloss)
        summ["spearman_R2_gcgloss"] = float(stats.spearmanr(R2, gloss).correlation)
        summ["spearman_r2_gcgloss"] = float(stats.spearmanr(r2, gloss).correlation)
        summ["n_joined"] = len(ids)
    json.dump(summ, open(os.path.join(RES, "gcg_summary.json"), "w"), indent=2)
    print("GCG summary:", json.dumps(summ, indent=2))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=128)
    ap.add_argument("--steps", type=int, default=250)
    args = ap.parse_args()
    main(args.n, args.steps)
