#!/usr/bin/env python
"""B2 orbit-flip main harness. Runs the full pilot end-to-end, saving per-item rows incrementally.

Per item, per invariance dose d in DOSES:
  - model_answer(x, d), model_answer(x_edit, d)     (marginalized over round(d*k_max) paraphrases)
  - orbit_flip(x, d) = model was right on x AND stayed put when the oracle flipped
  - rho_G_token(x, d) = min token-edit-dist over invariant flips (else +inf)
  - rho_G_emb(x, d)   = min ||Delta emb||_2 over invariant flips (else +inf)
  - measured_invariance(x, d) = paraphrase-consistency of the model's answer on x (agreement over
                                 the orbit) -- the observational invariance the field reports
Once per item (dose-independent):
  - eta/L sensitivity axis (M, ||grad||_2, ||grad||_1, R2, Rinf) from the T-DISS module
  - clean correctness, item length, edit_type, family

Output: results/peritem.jsonl (one row per item, carrying all doses). Config -> results/config.json.
"""
import os, sys, json, time, argparse, torch
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
os.makedirs(RES, exist_ok=True)
sys.path.insert(0, HERE)
from b2_model import B2Model, DOSE_SYS

DOSES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
K_MAX = 6  # paraphrases at dose 1.0

CONFIG = {
    "model": "meta-llama/Meta-Llama-3-8B-Instruct",
    "doses": DOSES, "k_max_paraphrases": K_MAX,
    "orbit_flip_def": "model correct on x AND model_answer(edit)==model_answer(x) AND != oracle(edit)",
    "oracle": "DETERMINISTIC (negation/antonym/harmful->benign); NLI model is paraphrase filter ONLY",
    "distance_geometries": ["token_edit_dist (Levenshtein)", "emb_disp = ||e(x_edit)-e(x)||_2"],
    "invariance_dose_axis": "within-model: consistency system prompt (d>0) + marginalize over round(d*k_max) paraphrases",
    "measured_invariance": "paraphrase-consistency: agreement of model answer over k_max paraphrases of x",
    "sensitivity_axis": "eta/L reused from T-DISS diagnostics (M, ||grad||_{2,1}, R2, Rinf)",
    "kill_criterion": ("KILL iff rho_G does NOT fall as invariance rises (Spearman(rho_G,dose) not "
                       "<= -0.6 and not significantly negative) OR orbit-flip rate ~ 0. Honest "
                       "negative is the result -- report, do not fabricate."),
    "budget_law": "prop:rhoG: an adversarial edit of size eps succeeds (invariant flip) only when eps >= rho_G; fraction >= ~90%",
    "seed": 0,
}


def log(*a):
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)


def _surface_of(item, which):
    """Return the answerable surface for 'x' or an edit index (int)."""
    fam = item["family"]
    if which == "x":
        return item["x"]
    e = item["edits"][which]
    return e["x_edit_hyp"] if fam == "nli" else e["x_edit"]


def _answer_surface(M, item, surface, system):
    """Model answer label for a single surface string of this item's task."""
    fam = item["family"]
    if fam == "sentiment":
        return M.sentiment_answer(surface, system=system)[0]
    if fam == "nli":
        return M.nli_answer(item["premise"], surface, system=system)[0]
    return M.safety_answer(surface, system=system)[0]


def process_item(M, item):
    """One item, all doses. Paraphrases are generated ONCE per surface at K_MAX (the expensive
    step) and SUBSAMPLED (first n) for lower doses, and REUSED for both the marginalized answer
    and the measured-invariance metric -- identical science, ~1/(2*n_doses) the generations."""
    fam = item["family"]
    edits = item["edits"]
    row = {"id": item["id"], "family": fam, "source": item.get("source"),
           "y": item["y"], "edit_types": [e["edit_type"] for e in edits],
           "token_dists": [e["token_edit_dist"] for e in edits],
           "x_len": len(item["x"].split())}

    # ---- embedding displacement per edit + eta/L (dose-independent) ----
    emb_disps = []
    for j in range(len(edits)):
        try:
            emb_disps.append(M.emb_displacement(item, j))
        except Exception:
            emb_disps.append(float("nan"))
    row["emb_disps"] = emb_disps
    try:
        el = M.eta_L(item)
        row["etaL"] = {"M": el["M"], "gl2": el["gl2"], "gl1": el["gl1"],
                       "R2": el["R2"], "Rinf": el["Rinf"], "grad_near_zero": el["grad_near_zero"]}
    except Exception as e:
        row["etaL"] = {"error": str(e)[:80]}

    # ---- precompute K_MAX paraphrases per surface (canonical x + each edit), ONE batched call ----
    keys = ["x"] + list(range(len(edits)))
    surfaces = {k: _surface_of(item, k) for k in keys}
    para_lists = M.paraphrases_multi([surfaces[k] for k in keys], K_MAX)
    paras = {k: para_lists[i] for i, k in enumerate(keys)}

    # ---- answer each surface + its paraphrases under BOTH system prompts, batched per surface ----
    # cache: ans[key][sysflag] = [answer(surface), answer(p1), ...]  (len 1+len(paras))
    ans = {}
    for k in keys:
        variants = [surfaces[k]] + paras[k]
        ans[k] = {
            0: M.answers_batch(item, variants, system=None),      # base
            1: M.answers_batch(item, variants, system=DOSE_SYS),  # consistency sys
        }

    def marg_answer(key, dose):
        """Majority-vote answer over 1 + round(dose*K_MAX) variants at this dose's system prompt."""
        sysflag = 1 if dose > 0 else 0
        pool = ans[key][sysflag]
        n = min(len(pool), 1 + int(round(dose * K_MAX)))
        votes = pool[:n]
        return Counter(votes).most_common(1)[0][0]

    def measured_inv(dose):
        """Paraphrase-consistency of the model answer on canonical x at this dose (agreement over
        1+K_MAX variants) -- observational invariance the field reports."""
        sysflag = 1 if dose > 0 else 0
        votes = ans["x"][sysflag]
        _, cnt = Counter(votes).most_common(1)[0]
        return cnt / len(votes)

    per_dose = {}
    for d in DOSES:
        a0 = marg_answer("x", d)
        correct = (a0 == item["y"])
        flip_dists_tok, flip_dists_emb, edit_flip = [], [], []
        any_flip = False
        for j, e in enumerate(edits):
            aj = marg_answer(j, d)
            is_flip = correct and (aj == a0) and (aj != e["y_edit"])
            edit_flip.append(bool(is_flip))
            if is_flip:
                any_flip = True
                flip_dists_tok.append(e["token_edit_dist"])
                flip_dists_emb.append(emb_disps[j])
        per_dose[str(d)] = {
            "model_answer_x": a0, "correct": bool(correct),
            "orbit_flip": bool(any_flip), "edit_flip": edit_flip,
            "rho_G_token": min(flip_dists_tok) if flip_dists_tok else float("inf"),
            "rho_G_emb": min(flip_dists_emb) if flip_dists_emb else float("inf"),
            "measured_invariance": measured_inv(d),
        }
    row["per_dose"] = per_dose
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=os.path.join(HERE, "data", "corpus.jsonl"))
    ap.add_argument("--out", default=os.path.join(RES, "peritem.jsonl"))
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    ap.add_argument("--model", default=CONFIG["model"], help="HF model id (cross-checkpoint)")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    cfg = dict(CONFIG); cfg["model"] = args.model
    cfg_name = "config.json" if os.path.basename(args.out) == "peritem.jsonl" else \
               "config_" + os.path.basename(args.out).replace(".jsonl", "") + ".json"
    with open(os.path.join(RES, cfg_name), "w") as f:
        json.dump(cfg, f, indent=2)

    rows = [json.loads(l) for l in open(args.corpus)]
    if args.limit:
        rows = rows[:args.limit]

    done = set()
    mode = "w"
    if args.resume and os.path.exists(args.out):
        for l in open(args.out):
            try:
                done.add(json.loads(l)["id"])
            except Exception:
                pass
        mode = "a"
        log(f"resume: {len(done)} items already done")

    log(f"loading model {args.model} ...")
    M = B2Model(model_id=args.model)
    log(f"model loaded, mem {torch.cuda.max_memory_allocated()/1e9:.1f}GB; {len(rows)} items")

    t0 = time.time()
    n = 0
    with open(args.out, mode) as f:
        for i, item in enumerate(rows):
            if item["id"] in done:
                continue
            try:
                row = process_item(M, item)
            except Exception as e:
                log(f"item {item['id']} FAILED: {str(e)[:120]}")
                row = {"id": item["id"], "family": item["family"], "error": str(e)[:200]}
            f.write(json.dumps(row) + "\n")
            f.flush()
            n += 1
            if n % 25 == 0:
                el = time.time() - t0
                rate = n / el
                remain = (len(rows) - len(done) - n) / rate if rate > 0 else 0
                log(f"{n} done ({i+1}/{len(rows)}), {rate:.2f} it/s, ETA {remain/60:.0f} min")
    log(f"DONE {n} items in {(time.time()-t0)/60:.1f} min -> {args.out}")


if __name__ == "__main__":
    main()
