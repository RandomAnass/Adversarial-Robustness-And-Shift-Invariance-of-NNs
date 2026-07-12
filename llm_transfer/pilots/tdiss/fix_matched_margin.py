#!/usr/bin/env python
"""T-DISS FIX: the THREAT-MATCHED continuation margin (resolves the preliminary negative).

DIAGNOSIS (verify/TDISS_preliminary_independent.md + code read of tdiss_core.pe_pgd): the primary
predictor M in phase1 is the FIRST-TOKEN refuse-affirm anchor margin, but the attack r2 is the
minimum radius to make the model GENERATE a harmful continuation -- it minimizes the CE loss of a
6-8 token affirmative target "Sure, here is <behavior>:\\n\\n1." (tdiss_core._affirm_target_ids,
pe_pgd line 189), gradient w.r.t. the prompt embeddings only. A first-token certificate R2=M/||grad||
does NOT bound a multi-token generation radius, so the observed Spearman(R2, r2) = -0.17 is EXPECTED
under theory: the predictor was not threat-matched to the attack.

THIS SCRIPT computes the THREAT-MATCHED predictor, on the attack's OWN objective at delta=0:
  L0(x)      = CE loss of the affirmative continuation target given the CLEAN prompt embeddings
               (high L0 = far from jailbreak = robust)
  ||grad||   = ||d L0 / d e(x)||_2   (local sensitivity of that loss to the prompt embedding)
  R_cont     = L0 / ||grad||_2       (first-order radius to drive the loss to ~0 = jailbreak;
                                       higher R_cont => larger jailbreak radius => more robust)
Then correlate R_cont with the EXISTING r2 (reused from phase2.jsonl). Expect POSITIVE if the
threat-matched ratio predicts jailbreakability. Cheap: one fwd+bwd per prompt (~1-2 min, 920 items).

Run when a GPU is free (uses CUDA_VISIBLE_DEVICES):
  CUDA_VISIBLE_DEVICES=0 /home/students/.conda/envs/llmtransfer/bin/python fix_matched_margin.py
Out: results/matched_margin.jsonl  (+ prints the correlations vs r2, in the harness convention).
"""
import os, sys, json, time, argparse, math
import torch
import torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
sys.path.insert(0, HERE)
from tdiss_core import TDiss


@torch.enable_grad()
def cont_margin(T, behavior):
    ids = T.build_ids(behavior)                                  # [1,T] chat-templated
    e0 = T.embeds_of(ids).detach().clone().requires_grad_(True)  # [1,T,d]
    tgt = torch.tensor(T._affirm_target_ids(behavior), device=T.device)  # [L]
    tgt_e = T.embed(tgt.unsqueeze(0)).detach()                   # [1,L,d]
    Ln = tgt.shape[0]
    full_e = torch.cat([e0, tgt_e], dim=1)                       # [1,T+L,d]  (no perturbation)
    out = T.model(inputs_embeds=full_e)
    logits = out.logits[0, ids.shape[1] - 1: ids.shape[1] - 1 + Ln, :]  # [L,V] predict tgt[0..L-1]
    loss = F.cross_entropy(logits.float(), tgt)                  # L0: affirmative-continuation loss
    g, = torch.autograd.grad(loss, e0)
    gl2 = g[0].float().norm(p=2).item()
    gl1 = g[0].float().abs().sum().item()
    L0 = float(loss.item())
    return {"L0": L0, "gl2_cont": gl2, "gl1_cont": gl1,
            "R2_cont": L0 / gl2 if gl2 > 0 else float("inf"),
            "Rinf_cont": L0 / gl1 if gl1 > 0 else float("inf")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="meta-llama/Meta-Llama-3-8B-Instruct")
    ap.add_argument("--out", default=os.path.join(RES, "matched_margin.jsonl"))
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    p1 = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(RES, "phase1.jsonl"))}
    p2 = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(RES, "phase2.jsonl"))}
    ids = [i for i in p1 if i in p2 and p1[i]["category"] == "harmful"]
    if args.limit:
        ids = ids[:args.limit]
    print(f"[{time.strftime('%H:%M:%S')}] loading {args.model}; {len(ids)} harmful prompts")
    T = TDiss(model_id=args.model)

    t0 = time.time()
    with open(args.out, "w") as f:
        for k, i in enumerate(ids):
            try:
                d = cont_margin(T, p1[i]["behavior"])
                row = {"id": i, **d}
            except Exception as e:
                row = {"id": i, "error": str(e)[:120]}
            f.write(json.dumps(row) + "\n"); f.flush()
            if (k + 1) % 100 == 0:
                r = (k + 1) / (time.time() - t0)
                print(f"[{time.strftime('%H:%M:%S')}] {k+1}/{len(ids)} {r:.1f} it/s")
    print(f"[{time.strftime('%H:%M:%S')}] DONE -> {args.out}")

    # ---- correlate matched R_cont with the existing r2 (harness convention: expect POSITIVE) ----
    try:
        import numpy as np
        from scipy import stats
        mm = {json.loads(l)["id"]: json.loads(l) for l in open(args.out)}
        l2_max = max(float(x) for x in list(p2.values())[0]["l2_succ"].keys())
        def rad(v, cap): return v if v is not None else cap * 2.0
        keep = [i for i in ids if "R2_cont" in mm.get(i, {})]
        R2c = np.array([mm[i]["R2_cont"] for i in keep])
        Rinfc = np.array([mm[i]["Rinf_cont"] for i in keep])
        L0 = np.array([mm[i]["L0"] for i in keep])
        r2 = np.array([rad(p2[i]["r2"], l2_max) for i in keep])
        R2_first = np.array([p1[i]["R2"] for i in keep])
        loss_ref = np.array([p2[i].get("l2_loss_ref", np.nan) for i in keep])
        def sp(x, y):
            m = np.isfinite(x) & np.isfinite(y)
            return round(float(stats.spearmanr(x[m], y[m]).correlation), 4), int(m.sum())
        print("\n==== MATCHED-MARGIN RESULT (expect POSITIVE if eta/L transfers to text jailbreak) ====")
        print(f"  Spearman(R2_cont , r2)        = {sp(R2c, r2)}   [MATCHED predictor vs radius]")
        print(f"  Spearman(Rinf_cont, r2)       = {sp(Rinfc, r2)}")
        print(f"  Spearman(L0 , r2)             = {sp(L0, r2)}   [clean continuation loss alone]")
        print(f"  Spearman(R2_cont , loss_ref)  = {sp(R2c, loss_ref)}   [judge-free]")
        print(f"  [ref] Spearman(R2_firsttoken, r2) = {sp(R2_first, r2)}   [the MIS-MATCHED -0.17]")
    except Exception as e:
        print("correlation step failed:", str(e)[:200])


if __name__ == "__main__":
    main()
