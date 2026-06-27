#!/usr/bin/env python3
"""
Threat-Matched Margin-Lipschitz Regularization (TM-MLR) -- turning the paper's DIAGNOSTIC into a
METHOD. The dissection shows that (a) the THREAT-MATCHED ratio eta/||grad M||_q (q = the dual norm of
the attack; q=1 for an ell_inf threat) predicts adversarial robustness while the mismatched ell_2 ratio
does not, and (b) under AT margin and input-sensitivity rise together, so eta/L is self-limiting. TM-MLR
adds, on top of PGD-AT, an explicit penalty on the THREAT-MATCHED MARGIN gradient ||grad_x M(x)||_1 to
push eta/L up directly instead of waiting for AT to do it (which it caps).

The decisive CONTROLLED comparison (what makes this theory-validated, not a generic gradient penalty):
  penalty="none"      : vanilla PGD-AT                                   (lam ignored)
  penalty="ce_l2"     : lam * mean ||grad_x CE(x)||_2                    (Finlay-Oberman / Ross-Doshi-Velez; == exp3)
  penalty="margin_l2" : lam * mean ||grad_x M(x)||_2                     (mismatched-norm ablation)
  penalty="margin_l1" : lam * mean ||grad_x M(x)||_1                     (THE METHOD: threat-matched for ell_inf)
Theory predicts in AutoAttack ell_inf robust accuracy:  margin_l1  >  margin_l2 ~ ce_l2  >  none.

This is a strict GENERALIZATION of exp3_lipschitz_at.train_lip_at: with penalty="none"/lam=0 it is the
vanilla PGD-AT baseline; with penalty="ce_l2" its penalty block is byte-identical to exp3's. The margin
penalties keep exp3's reduction convention (gradient of the batch-MEAN scalar, then per-sample norm, then
mean) so ce_l2 and margin_l2 differ ONLY in loss-gradient vs margin-gradient, and margin_l2 vs margin_l1
differ ONLY in the q-norm -- isolating the two effects the theory cares about.

Reuses build / load_data / accuracy / correct_mask / shift_consistency / robust_radius_l2 /
etaL_decomposition / autoattack_acc / pgd_acc / dataset_stats / in_channels / nparams from
cifar_dissection, and pgd_linf from cifar_at. ONLY the selectable penalty term is new. Progressive
per-cell save + resume, and exp3's OOM-robust per-GPU worker pool (AA_BS env honored).

Run (full sweep -- user chooses configs):
  PYTHONNOUSERSITE=1 paper/env/cenv/bin/python exp_tmreg.py \
      --configs none:0 ce_l2:0.05 margin_l2:0.05 margin_l1:0.1 \
      --widths 32 48 --seeds 2 --aa_n 2000 --gpus 2 --workers_per_gpu 2
"""
import argparse, os, json, time, numpy as np, torch, torch.nn.functional as F
import torch.multiprocessing as mp
from cifar_dissection import (build, load_data, dataset_stats, in_channels, accuracy, correct_mask,
                              shift_consistency, robust_radius_l2, etaL_decomposition, autoattack_acc,
                              pgd_acc, nparams)
from cifar_at import pgd_linf

RESDIR = os.path.join(os.path.dirname(__file__), "..", "results")
PARTDIR = os.path.join(RESDIR, "at_partial", "tmreg")
PENALTIES = ("none", "ce_l2", "margin_l2", "margin_l1")

def _lamstr(lam): return f"{float(lam):g}"
def _jf(penalty, lam, w, seed):
    return os.path.join(PARTDIR, f"{penalty}_l{_lamstr(lam)}_w{w}_s{seed}.json")
def _save(out):
    os.makedirs(PARTDIR, exist_ok=True)
    p = _jf(out["penalty"], out["lam"], out["w"], out["seed"]); tmp = p + ".tmp"
    json.dump(out, open(tmp, "w"), default=float); os.replace(tmp, p)        # atomic publish

# ---------------- training: PGD-AT + selectable threat-matched gradient penalty ----------------
def train_tmreg(model, X, y, dev, epochs, seed, eps, alpha, steps, penalty="none", lam=0.0,
                bs=128, lr=0.1, wd=5e-4, aug=True, shift_aug=False):
    """PGD-AT (Linf) outer-min on x_adv plus an optional input-gradient penalty on CLEAN x:
        penalty="none"      -> no penalty (lam ignored)  == vanilla PGD-AT (cifar_at.adv_train, Linf)
        penalty="ce_l2"     -> lam * mean ||grad_x CE(x)||_2   (byte-identical to exp3.train_lip_at)
        penalty="margin_l2" -> lam * mean ||grad_x M(x)||_2    (mismatched-norm ablation)
        penalty="margin_l1" -> lam * mean ||grad_x M(x)||_1    (threat-matched, the method)
    where the per-sample margin M(x) = logit_{y} - max_{j!=y} logit_j (differentiable a.e.). The inner
    grad uses create_graph=True so the penalty backprops into the weights (double backprop)."""
    assert penalty in PENALTIES, f"penalty must be one of {PENALTIES}"
    torch.manual_seed(seed); model = model.to(dev).train()
    opt = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9, weight_decay=wd, nesterov=True)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    X, y = X.to(dev), y.to(dev); n = len(X)
    from cifar_dissection import circular_roll
    use_pen = (penalty != "none") and (lam > 0)
    for ep in range(epochs):
        perm = torch.randperm(n, device=dev)
        for i in range(0, n, bs):
            idx = perm[i:i + bs]; xb = X[idx]; yb = y[idx]
            if aug:
                flip = torch.rand(xb.size(0), device=dev) < 0.5
                xb = torch.where(flip[:, None, None, None], xb.flip(-1), xb)
            if shift_aug: xb = circular_roll(xb, 4)
            x_adv = pgd_linf(model, xb, yb, eps, alpha, steps)        # inner max (Linf PGD)
            opt.zero_grad(set_to_none=True)
            loss = F.cross_entropy(model(x_adv), yb)                  # outer min (AT)
            if use_pen:                                              # input-gradient penalty on clean x
                xc = xb.clone().detach().requires_grad_(True)
                if penalty == "ce_l2":                              # Finlay-Oberman: grad of mean CE (== exp3)
                    s = F.cross_entropy(model(xc), yb)
                    g, = torch.autograd.grad(s, xc, create_graph=True)
                    pen = g.flatten(1).norm(dim=1).mean()
                else:                                              # margin gradient: same mean-reduction as ce_l2
                    logits = model(xc)
                    true = logits.gather(1, yb[:, None]).squeeze(1)
                    other = logits.clone().scatter_(1, yb[:, None], -1e9).max(1).values
                    m = (true - other).mean()
                    g, = torch.autograd.grad(m, xc, create_graph=True)
                    gf = g.flatten(1)
                    pen = gf.norm(dim=1).mean() if penalty == "margin_l2" else gf.abs().sum(1).mean()
                loss = loss + lam * pen
            loss.backward(); opt.step()
        sched.step()
    return model.eval()

# ---------------- one cell ----------------
def run_job(task):
    gpu, penalty, lam, w, seed, A = task
    dev = f"cuda:{gpu}" if (gpu is not None and torch.cuda.is_available()) else "cpu"
    if dev.startswith("cuda"): torch.cuda.set_device(gpu)
    ds = A["dataset"]; arm = A["arm"]
    Xtr, ytr, Xte, yte = load_data(ds, A["n"], A["ntest"], seed=0)
    nmean, nstd = dataset_stats(ds)
    model = train_tmreg(build(arm, w, in_ch=in_channels(ds), norm_mean=nmean, norm_std=nstd),
                        Xtr, ytr, dev, epochs=A["epochs"], seed=seed, eps=A["eps"], alpha=A["alpha"],
                        steps=A["steps"], penalty=penalty, lam=lam, aug=A["flip"],
                        shift_aug=(arm == "aug"))
    out = dict(arm=arm, penalty=penalty, lam=lam, w=w, seed=seed, dataset=ds, params=nparams(model),
               eps=A["eps"], alpha=A["alpha"], steps=A["steps"], epochs=A["epochs"], n=A["n"])
    out["clean"] = accuracy(model, Xte, yte, dev)
    out["consist"] = shift_consistency(model, Xte, dev)
    cm = correct_mask(model, Xte, yte, dev); Xc, yc = Xte[cm], yte[cm]
    out["rr_l2"] = robust_radius_l2(model, Xc[:A["rad_n"]], yc[:A["rad_n"]], dev)
    out["rr_n"] = int(min(A["rad_n"], len(Xc)))
    out.update({("dec_" + k): v for k, v in etaL_decomposition(model, Xte, yte, dev).items()})
    out["dec_etaL_matched"] = out["dec_margin"] / (out["dec_L1"] + 1e-12)   # threat-matched ratio (Linf -> L1)
    if A["aa_n"] > 0:
        out["pgd_Linf_8_255"] = pgd_acc(model, Xte[:A["aa_n"]], yte[:A["aa_n"]], dev, 8/255, "linf",
                                        steps=A["pgd_steps"])                # gradient-masking check
        out["aa_Linf_8_255"] = autoattack_acc(model, Xte, yte, dev, 8/255, "Linf",
                                              n=A["aa_n"], version=A["aa_version"])
    _save(out); return out

# ---------------- exp3-style per-GPU worker pool (OOM-robust; saves to disk) ----------------
def _worker(wid, gpu, n_workers, task_q, A):
    try:
        avail = sorted(os.sched_getaffinity(0)); per = max(1, len(avail) // n_workers)
        my = avail[wid * per:(wid + 1) * per] or avail[:per]
        os.sched_setaffinity(0, set(my)); torch.set_num_threads(max(1, len(my) // 2))
    except Exception:
        torch.set_num_threads(max(1, (os.cpu_count() or 8) // max(1, n_workers)))
    while True:
        item = task_q.get()
        if item is None: break
        penalty, lam, w, seed = item
        try: run_job((gpu, penalty, lam, w, seed, A))
        except Exception as e:
            print(f"[w{wid} gpu{gpu}] {(penalty,lam,w,seed)} FAILED: {type(e).__name__}: {e}", flush=True)

def _parse_configs(items):
    cfgs = []
    for s in items:
        p, _, l = s.partition(":")
        if p not in PENALTIES: raise SystemExit(f"bad penalty '{p}' in '{s}'; choose from {PENALTIES}")
        cfgs.append((p, 0.0 if p == "none" else float(l or 0.0)))
    return cfgs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", nargs="+", default=["none:0", "ce_l2:0.05", "margin_l2:0.05", "margin_l1:0.05"],
                    help="penalty:lam pairs, e.g. none:0 ce_l2:0.05 margin_l2:0.05 margin_l1:0.1")
    ap.add_argument("--arm", default="standard")
    ap.add_argument("--widths", type=int, nargs="+", default=[32, 48])
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--dataset", default="cifar", choices=["cifar", "mnist", "fashion"])
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--n", type=int, default=50000); ap.add_argument("--ntest", type=int, default=10000)
    ap.add_argument("--eps", type=float, default=8/255); ap.add_argument("--alpha", type=float, default=2/255)
    ap.add_argument("--steps", type=int, default=7)
    ap.add_argument("--rad_n", type=int, default=1000); ap.add_argument("--aa_n", type=int, default=2000)
    ap.add_argument("--aa_version", default="standard"); ap.add_argument("--pgd_steps", type=int, default=20)
    ap.add_argument("--gpus", type=int, default=2); ap.add_argument("--workers_per_gpu", type=int, default=2)
    a = ap.parse_args()
    cfgs = _parse_configs(a.configs)
    A = dict(dataset=a.dataset, arm=a.arm, flip=(a.dataset == "cifar"), n=a.n, ntest=a.ntest,
             epochs=a.epochs, eps=a.eps, alpha=a.alpha, steps=a.steps, rad_n=a.rad_n, aa_n=a.aa_n,
             aa_version=a.aa_version, pgd_steps=a.pgd_steps)
    ng = min(a.gpus, torch.cuda.device_count()) if torch.cuda.is_available() else 0
    # memory-aware concurrency (CIFAR 3-channel + AA + double-backprop is heavy); scheduling only
    K = max(1, a.workers_per_gpu); _maxw = max(a.widths); _heavy = (a.dataset == "cifar")
    if _maxw >= 96: K = min(K, 1)
    elif _heavy: K = min(K, 2)
    elif _maxw >= 64: K = min(K, 2)
    nw = max(1, ng * K) if ng > 0 else 1
    load_data(a.dataset, 10, 10)                                  # download once before forking
    jobs = sorted([(p, lam, w, s) for (p, lam) in cfgs for w in a.widths for s in range(a.seeds)],
                  key=lambda j: j[2] * j[2], reverse=True)         # cost-sort by width^2 (round-robin balance)
    pending = [j for j in jobs if not os.path.exists(_jf(*j))]
    print(f"TM-MLR ({a.dataset}, {a.arm}, eps={a.eps:.4f}, {a.steps} steps): {len(jobs)} cells "
          f"({len(jobs)-len(pending)} resumed), {len(pending)} to run over {ng or 'CPU'} GPU x {K} workers; "
          f"configs={cfgs} widths={a.widths} seeds={a.seeds} aa_n={a.aa_n}\n", flush=True)
    t0 = time.time()
    if pending and ng > 0:
        ctx = mp.get_context("spawn"); task_q = ctx.Queue()
        for t in pending: task_q.put(t)
        for _ in range(nw): task_q.put(None)
        workers = [ctx.Process(target=_worker, args=(wid, wid % ng, nw, task_q, A)) for wid in range(nw)]
        for p in workers: p.start()
        for p in workers: p.join()
    elif pending:
        for j in pending: run_job((None,) + j + (A,))
    results = [json.load(open(_jf(*j))) for j in jobs if os.path.exists(_jf(*j))]
    miss = [j for j in jobs if not os.path.exists(_jf(*j))]
    stamp = time.strftime("%Y%m%d_%H%M%S")
    fn = os.path.join(RESDIR, f"exp_tmreg_{a.dataset}_{stamp}.json")
    json.dump(dict(args=vars(a), configs=cfgs, results=results, missing=miss), open(fn, "w"),
              indent=2, default=float)
    # console summary (per config, averaged over widths+seeds)
    if results:
        agg = {}
        for r in results: agg.setdefault((r["penalty"], r["lam"]), []).append(r)
        def g(rs, k): return float(np.mean([x[k] for x in rs if k in x and x[k] is not None]))
        hdr = f"{'penalty':10s} {'lam':>5s} {'clean':>6s} {'consist':>7s} {'margin':>7s} {'L1':>7s} {'L2':>7s} {'eta/L1':>7s} {'pgd':>6s} {'AA':>6s}"
        print("\n" + hdr); print("-" * len(hdr))
        for (p, lam) in sorted(agg, key=lambda k: (PENALTIES.index(k[0]), k[1])):
            rs = agg[(p, lam)]
            print(f"{p:10s} {lam:5.3g} {g(rs,'clean'):6.3f} {g(rs,'consist'):7.3f} {g(rs,'dec_margin'):7.3f} "
                  f"{g(rs,'dec_L1'):7.3f} {g(rs,'dec_L2'):7.3f} {g(rs,'dec_etaL_matched'):7.4f} "
                  f"{g(rs,'pgd_Linf_8_255'):6.3f} {g(rs,'aa_Linf_8_255'):6.3f}")
    print(f"\nwall {time.time()-t0:.0f}s; {len(results)}/{len(jobs)} cells; saved {fn}", flush=True)
    if miss: print(f"WARNING missing {len(miss)}: {miss} -- re-run to resume", flush=True)

if __name__ == "__main__":
    main()
