#!/usr/bin/env python3
"""
Experiment #3 -- turning the F2 observation into a prescription. F2 found that adversarial training
INVERTS the within-cell margin<->sensitivity coupling (it buys margin partly by RAISING input
sensitivity, so eta/L is self-limiting). Prediction: adding an explicit input-gradient (Lipschitz)
penalty on top of AT should raise eta/L -- and should help the exactly-invariant (circular) arm MORE
than the standard arm, because circular starts with the margin deficit (Ge collapse) and AT's coupling
caps how much eta/L it can recover on its own.

Test: AT (PGD-linf 8/255) + lambda * mean||grad_x CE||_2 (input-gradient regularization; Ross &
Doshi-Velez 2018, Finlay & Oberman 2019), for arms {standard, circular} over a small lambda sweep,
two widths, two seeds. Report, per arm, how eta/L and AutoAttack robust accuracy move as lambda grows,
and whether the circular arm's gains exceed the standard arm's (the predicted ordering).

Reproducibility: reuses build / pgd_linf / the eval + AutoAttack wiring from the validated modules; the
ONLY new piece is the gradient-penalty term in the training loop. Progressive per-job save + resume,
and the same OOM-robust 6-worker pool as cifar_at_parallel.py.

Usage: PYTHONNOUSERSITE=1 paper/env/cenv/bin/python exp3_lipschitz_at.py --gpus 2 --workers_per_gpu 3
"""
import argparse, os, json, time, numpy as np, torch, torch.nn.functional as F
import torch.multiprocessing as mp
from itertools import product
from cifar_dissection import (build, load_data, dataset_stats, in_channels, accuracy, correct_mask,
                              shift_consistency, robust_radius_l2, etaL_decomposition, autoattack_acc,
                              pgd_acc, nparams)
from cifar_at import pgd_linf

RESDIR = os.path.join(os.path.dirname(__file__), "..", "results")
PARTDIR = os.path.join(RESDIR, "at_partial", "exp3_lipschitz")

def _jf(arm, w, lam, seed):
    return os.path.join(PARTDIR, f"{arm}_w{w}_lam{lam}_s{seed}.json")

def _save(out):
    os.makedirs(PARTDIR, exist_ok=True)
    p = _jf(out["arm"], out["w"], out["lam"], out["seed"]); tmp = p + ".tmp"
    json.dump(out, open(tmp, "w"), default=float); os.replace(tmp, p)

def train_lip_at(model, X, y, dev, epochs, seed, eps, alpha, steps, lam, bs=128, lr=0.1, wd=5e-4,
                 aug=True, shift_aug=False):
    """PGD-AT outer min on x_adv + lambda * mean ||grad_x CE(x)||_2 input-gradient penalty (double
    backprop). lam=0 reduces to the plain PGD-AT baseline (identical recipe to cifar_at.adv_train)."""
    torch.manual_seed(seed); model = model.to(dev).train()
    opt = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9, weight_decay=wd, nesterov=True)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    X, y = X.to(dev), y.to(dev); n = len(X)
    from cifar_dissection import circular_roll
    for ep in range(epochs):
        perm = torch.randperm(n, device=dev)
        for i in range(0, n, bs):
            idx = perm[i:i + bs]; xb = X[idx]; yb = y[idx]
            if aug:
                flip = torch.rand(xb.size(0), device=dev) < 0.5
                xb = torch.where(flip[:, None, None, None], xb.flip(-1), xb)
            if shift_aug: xb = circular_roll(xb, 4)
            x_adv = pgd_linf(model, xb, yb, eps, alpha, steps)
            opt.zero_grad(set_to_none=True)
            loss = F.cross_entropy(model(x_adv), yb)
            if lam > 0:                                  # input-gradient (Lipschitz) penalty on clean x
                xc = xb.clone().detach().requires_grad_(True)
                ce = F.cross_entropy(model(xc), yb)
                gx, = torch.autograd.grad(ce, xc, create_graph=True)
                loss = loss + lam * gx.flatten(1).norm(dim=1).mean()
            loss.backward(); opt.step()
        sched.step()
    return model.eval()

def run_job(task):
    gpu, arm, w, lam, seed, A = task
    dev = f"cuda:{gpu}" if (gpu is not None and torch.cuda.is_available()) else "cpu"
    if dev.startswith("cuda"): torch.cuda.set_device(gpu)
    ds = "cifar"; Xtr, ytr, Xte, yte = load_data(ds, A["n"], A["ntest"], seed=0)
    nmean, nstd = dataset_stats(ds)
    model = train_lip_at(build(arm, w, in_ch=in_channels(ds), norm_mean=nmean, norm_std=nstd),
                         Xtr, ytr, dev, epochs=A["epochs"], seed=seed, eps=8/255, alpha=2/255,
                         steps=7, lam=lam, aug=True, shift_aug=(arm == "aug"))
    out = dict(arm=arm, w=w, lam=lam, seed=seed, params=nparams(model))
    out["clean"] = accuracy(model, Xte, yte, dev)
    out["consist"] = shift_consistency(model, Xte, dev)
    cm = correct_mask(model, Xte, yte, dev); Xc, yc = Xte[cm], yte[cm]
    out["rr_l2"] = robust_radius_l2(model, Xc[:A["rad_n"]], yc[:A["rad_n"]], dev)
    out.update({("dec_" + k): v for k, v in etaL_decomposition(model, Xte, yte, dev).items()})
    out["pgd_Linf_8_255"] = pgd_acc(model, Xte[:A["aa_n"]], yte[:A["aa_n"]], dev, 8/255, "linf", steps=20)
    out["aa_Linf_8_255"] = autoattack_acc(model, Xte, yte, dev, 8/255, "Linf", n=A["aa_n"], version="standard")
    _save(out); return out

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
        arm, w, lam, seed = item
        try: run_job((gpu, arm, w, lam, seed, A))
        except Exception as e:
            print(f"[w{wid} gpu{gpu}] {(arm,w,lam,seed)} FAILED: {type(e).__name__}: {e}", flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", default=["standard", "circular"])
    ap.add_argument("--lams", type=float, nargs="+", default=[0.0, 0.05, 0.2])
    ap.add_argument("--widths", type=int, nargs="+", default=[32, 64])
    ap.add_argument("--seeds", type=int, default=2); ap.add_argument("--epochs", type=int, default=25)
    ap.add_argument("--n", type=int, default=50000); ap.add_argument("--ntest", type=int, default=10000)
    ap.add_argument("--rad_n", type=int, default=1000); ap.add_argument("--aa_n", type=int, default=10000)
    ap.add_argument("--gpus", type=int, default=2); ap.add_argument("--workers_per_gpu", type=int, default=3)
    a = ap.parse_args()
    A = dict(n=a.n, ntest=a.ntest, epochs=a.epochs, rad_n=a.rad_n, aa_n=a.aa_n)
    ng = min(a.gpus, torch.cuda.device_count()) if torch.cuda.is_available() else 0
    K = max(1, a.workers_per_gpu)
    _maxw = max(a.widths)                          # memory-aware cap (CIFAR, heavy AA): see cifar_at_parallel
    if _maxw >= 96: K = min(K, 1)
    elif _maxw >= 64: K = min(K, 2)
    nw = max(1, ng * K) if ng > 0 else 1
    load_data("cifar", 10, 10)
    jobs = sorted(product(a.arms, a.widths, a.lams, range(a.seeds)),
                  key=lambda j: (16 if j[0] == "circular" else 1) * j[1] * j[1], reverse=True)
    pending = [j for j in jobs if not os.path.exists(_jf(*j))]
    print(f"exp3 Lipschitz-AT: {len(jobs)} jobs ({len(jobs)-len(pending)} resumed), {len(pending)} to run "
          f"over {ng} GPU x {K} workers; arms={a.arms} lams={a.lams} widths={a.widths} seeds={a.seeds}\n", flush=True)
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
    fn = os.path.join(RESDIR, f"exp3_lipschitz_at_{stamp}.json")
    json.dump(dict(args=vars(a), results=results, missing=miss), open(fn, "w"), indent=2, default=float)
    print(f"\nwall {time.time()-t0:.0f}s; {len(results)}/{len(jobs)} done; saved {fn}", flush=True)
    if miss: print(f"WARNING missing {len(miss)}: {miss} -- re-run to resume", flush=True)

if __name__ == "__main__":
    main()
