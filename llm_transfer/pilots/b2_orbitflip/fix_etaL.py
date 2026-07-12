#!/usr/bin/env python
"""B2 FIX 1 (verify/B2_verification.md §3c): recompute eta/L with the TASK-CLASS margin.

The cached peritem.jsonl etaL reused tdiss_core.diagnostics, whose M is the *refusal* margin
(refuse - affirm). That is a reasonable proxy for the safety family but semantically empty for
sentiment/NLI (1200/1600 items: M<0 on 96% sentiment, 100% NLI, since these prompts elicit no
refusal). So the reported Spearman(R2, rho_G) = -0.11 was dominated by a mis-specified margin.

This recomputes, per item, the theory margin M(x) = f_y - max_{j != y} f_j on the SAME head the
task answer uses, signed toward the ORACLE-correct label (so M>0 when the model is correct):
  sentiment : logit(' positive') - logit(' negative')   (flip sign if y=negative)
  nli       : logit(' yes')      - logit(' no')          ('yes'->entailment; flip if y=neutral)
  safety    : refuse - comply  == the existing anchor margin  (reuse T.diagnostics; already correct)
Gradient wrt the input embeddings gives ||grad||_{2,1}; R2=M/||g||_2, Rinf=M/||g||_1 are the
gauge-invariant ratios. logit_scale=1, refuse_bias=0 for Llama, so these are raw-logit margins.

Out: results/etaL_taskmargin.jsonl  (id, family, y, M, gl2, gl1, R2, Rinf, grad_near_zero, model_pred).
Run: CUDA_VISIBLE_DEVICES=1 /home/students/.conda/envs/llmtransfer/bin/python fix_etaL.py
"""
import os, sys, json, time, argparse, torch

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
sys.path.insert(0, HERE)
from b2_model import B2Model


def log(*a):
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)


@torch.enable_grad()
def task_margin_diag(B, item):
    """Task-class-margin eta/L for one item. Returns dict {M,gl2,gl1,R2,Rinf,grad_near_zero,pred}."""
    fam = item["family"]
    if fam == "safety":
        # refuse - comply == refuse - affirm anchor margin; already the correct task-class margin.
        d = B.T.diagnostics(item["x"])
        d["model_pred"] = None  # answer comes from generation elsewhere; margin sign = refuse-lean
        return d

    if fam == "sentiment":
        user = B._sentiment_prompt(item["x"])
        pos_id, neg_id = B._id[" positive"], B._id[" negative"]   # ' positive' vs ' negative'
        cor, oth = (pos_id, neg_id) if item["y"] == "positive" else (neg_id, pos_id)
    elif fam == "nli":
        user = B._nli_prompt(item["premise"], item["x"])
        pos_id, neg_id = B._id[" yes"], B._id[" no"]              # ' yes'->entailment, ' no'->neutral
        cor, oth = (pos_id, neg_id) if item["y"] == "entailment" else (neg_id, pos_id)
    else:
        raise ValueError(fam)

    ids = B._chat_ids(user)                                    # [1, T] chat-templated, gen prompt
    e = B.embed(ids).detach().clone().requires_grad_(True)     # [1, T, d]
    out = B.model(inputs_embeds=e)
    logits1 = out.logits[0, -1, :]
    Mv = logits1[cor] - logits1[oth]                          # f_y - f_{other} (signed to oracle)
    g, = torch.autograd.grad(Mv, e)
    g = g[0].float()
    gl2 = g.norm(p=2).item()
    gl1 = g.abs().sum().item()
    m = float(Mv.item())
    # model's own predicted label from the two answer-head logits (base-correctness cross-check)
    hi = pos_id if float(logits1[pos_id]) >= float(logits1[neg_id]) else neg_id
    pred = {pos_id: ("positive" if fam == "sentiment" else "entailment"),
            neg_id: ("negative" if fam == "sentiment" else "neutral")}[hi]
    return {"M": m, "gl2": gl2, "gl1": gl1,
            "R2": m / gl2 if gl2 > 0 else float("inf"),
            "Rinf": m / gl1 if gl1 > 0 else float("inf"),
            "grad_near_zero": bool(gl2 < 1e-6), "model_pred": pred}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=os.path.join(HERE, "data", "corpus.jsonl"))
    ap.add_argument("--out", default=os.path.join(RES, "etaL_taskmargin.jsonl"))
    ap.add_argument("--model", default="meta-llama/Meta-Llama-3-8B-Instruct")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.corpus)]
    if args.limit:
        rows = rows[:args.limit]
    log(f"loading {args.model} ...")
    B = B2Model(model_id=args.model)
    log(f"loaded; {len(rows)} items")

    t0 = time.time()
    with open(args.out, "w") as f:
        for i, item in enumerate(rows):
            try:
                d = task_margin_diag(B, item)
                out = {"id": item["id"], "family": item["family"], "y": item["y"], **d}
            except Exception as e:
                out = {"id": item["id"], "family": item["family"], "y": item["y"],
                       "error": str(e)[:120]}
            f.write(json.dumps(out) + "\n")
            f.flush()
            if (i + 1) % 100 == 0:
                r = (i + 1) / (time.time() - t0)
                log(f"{i+1}/{len(rows)}  {r:.1f} it/s  ETA {(len(rows)-i-1)/r/60:.0f} min")
    log(f"DONE {len(rows)} items in {(time.time()-t0)/60:.1f} min -> {args.out}")


if __name__ == "__main__":
    main()
