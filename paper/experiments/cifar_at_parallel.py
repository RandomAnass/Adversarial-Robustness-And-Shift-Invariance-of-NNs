#!/usr/bin/env python3
"""
PARALLEL scheduler for the capacity-matched adversarial-training sweep. This is the SAME experiment
as cifar_at.py -- it imports the per-job computation (run_job_at, adv_train, the eval, the AutoAttack
wiring, progressive save/resume) VERBATIM from cifar_at.py and changes ONLY the scheduler: instead of
one serial job per GPU, it runs K workers PER GPU pulling from a shared queue (default 2 GPUs x 3 = 6).

Reproducibility: every job's result is produced by the identical imported run_job_at, seeded by its
own (arm,w,seed) on seed-0 data; the scheduler never enters a job's computation, so the parallel run
yields the same results as cifar_at.py -- adding NO variance beyond cifar_at.py's own run-to-run cudnn
noise (proven by experiments/repro_check_parallel.py: the parallel result lands within the old script's
self-vs-self spread). cifar_at.py is left untouched so its prior results stay reproducible.

CPU-thrash avoidance: each worker caps torch threads to ~physical_cores/(n_workers) and pins its CPU
affinity to a disjoint core slice.

Usage (identical flags to cifar_at.py, plus --workers_per_gpu):
  PYTHONNOUSERSITE=1 paper/env/cenv/bin/python cifar_at_parallel.py --dataset mnist --norm linf \
      --aa_n 10000 --tag full10k --gpus 2 --workers_per_gpu 3
"""
import argparse, os, json, time, numpy as np, torch
import torch.multiprocessing as mp
from itertools import product
# import the EXACT computation + helpers from the canonical script (do NOT reimplement them)
from cifar_at import (run_job_at, _job_file, _save_job, RESDIR, ARMS)

def _worker(wid, gpu, n_workers, task_q, A):
    """One worker, pinned to `gpu` and a disjoint CPU-core slice. Pulls (arm,w,seed) tasks and runs the
    imported run_job_at (which atomically SAVES each result to disk via _save_job) until the None
    sentinel. Results are collected from disk by the parent -- NO result queue, so a dead/OOM'd worker
    cannot deadlock the run (its unsaved job is just re-done on the next resume)."""
    try:
        avail = sorted(os.sched_getaffinity(0))
        per = max(1, len(avail) // n_workers)
        my = avail[wid * per:(wid + 1) * per] or avail[:per]
        os.sched_setaffinity(0, set(my))
        torch.set_num_threads(max(1, len(my) // 2))     # logical->~physical; no oversubscription
    except Exception:
        torch.set_num_threads(max(1, (os.cpu_count() or 8) // max(1, n_workers)))
    while True:
        item = task_q.get()
        if item is None:
            break
        arm, w, seed = item
        try:
            run_job_at((gpu, arm, w, seed, A))          # IDENTICAL compute path as cifar_at.py; saves to disk
        except Exception as e:
            print(f"[worker {wid} gpu{gpu}] job {(arm,w,seed)} FAILED: {type(e).__name__}: {e}", flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50000); ap.add_argument("--ntest", type=int, default=10000)
    ap.add_argument("--epochs", type=int, default=30); ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--widths", type=int, nargs="+", default=[32, 64])
    ap.add_argument("--arms", nargs="+", default=ARMS)
    ap.add_argument("--dataset", default="cifar", choices=["cifar", "mnist", "fashion"])
    ap.add_argument("--norm", default="linf", choices=["linf", "l2"])
    ap.add_argument("--eps", type=float, default=None); ap.add_argument("--alpha", type=float, default=None)
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--rad_n", type=int, default=1000); ap.add_argument("--aa_n", type=int, default=512)
    ap.add_argument("--aa_version", default="standard"); ap.add_argument("--pgd_steps", type=int, default=40)
    ap.add_argument("--gpus", type=int, default=2); ap.add_argument("--workers_per_gpu", type=int, default=3)
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--tag", default="at")
    args = ap.parse_args()
    widths, arms = args.widths, args.arms
    # recipe by (dataset, norm) -- IDENTICAL to cifar_at.py (kept in sync; the compute uses A built below)
    RECIPE = {
        ("cifar", "linf"):   dict(eps=8/255, steps=7,  alpha=2/255,      aa=[("Linf_8_255", "Linf", 8/255), ("L2_0_5", "L2", 0.5)], flip=True),
        ("cifar", "l2"):     dict(eps=0.5,   steps=10, alpha=2.5*0.5/10, aa=[("L2_0_5", "L2", 0.5), ("Linf_8_255", "Linf", 8/255)], flip=True),
        ("mnist", "linf"):   dict(eps=0.3,   steps=10, alpha=2.5*0.3/10, aa=[("Linf_0_3", "Linf", 0.3)], flip=False),
        ("fashion", "linf"): dict(eps=0.1,   steps=10, alpha=2.5*0.1/10, aa=[("Linf_0_1", "Linf", 0.1)], flip=False),
    }
    rec = RECIPE[(args.dataset, args.norm)]
    eps = args.eps if args.eps is not None else rec["eps"]
    steps = args.steps if args.steps is not None else rec["steps"]
    alpha = args.alpha if args.alpha is not None else rec["alpha"]
    aa_specs = rec["aa"]; flip = rec["flip"]
    if args.smoke:
        args.n, args.ntest, args.epochs, args.seeds = 4000, 1000, 2, 1
        widths, arms = [16], ARMS
        args.rad_n, args.aa_n, args.aa_version, args.pgd_steps = 200, 128, "custom", 10
        steps = min(steps, 5)
    ng = min(args.gpus, torch.cuda.device_count()) if torch.cuda.is_available() else 0
    # memory-aware concurrency: full-10k AutoAttack on WIDE/robust models holds a lot (a single
    # width-64 robust-MNIST AA job peaked ~23 GiB), so 3 concurrent can OOM a 48 GiB card. Cap K by the
    # run's largest width. Scheduling-only -> never changes a job's result (each job still runs the
    # identical run_job_at); a smaller K is just slower. CIFAR (3-channel) is heavier than MNIST/Fashion.
    K = max(1, args.workers_per_gpu)
    _maxw = max(widths); _heavy = (args.dataset == "cifar")
    if _maxw >= 96: K = min(K, 1 if _heavy else 2)
    elif _heavy: K = min(K, 2)         # CIFAR (3-channel) AA-standard-10k is ~8 GiB/job at ANY width -> >=3 maxes a 48 GiB card
    elif _maxw >= 64: K = min(K, 2)
    A = dict(dataset=args.dataset, norm=args.norm, flip=flip, n=args.n, ntest=args.ntest,
             epochs=args.epochs, eps=eps, alpha=alpha, steps=steps, rad_n=args.rad_n, aa_n=args.aa_n,
             aa_version=args.aa_version, pgd_steps=args.pgd_steps, aa_specs=aa_specs, tag=args.tag)
    from cifar_at import load_data
    load_data(args.dataset, 10, 10)
    jobs = sorted(product(arms, widths, range(args.seeds)),
                  key=lambda j: (16 if j[0] == "circular" else 1) * j[1] * j[1], reverse=True)
    # resume: skip jobs already saved to disk (same progressive-save protocol as cifar_at.py)
    done_results, pending = [], []
    for (arm, w, s) in jobs:
        jf = _job_file(A, arm, w, s)
        if os.path.exists(jf):
            try: done_results.append(json.load(open(jf))); continue
            except Exception: pass
        pending.append((arm, w, s))
    nw = max(1, ng * K) if ng > 0 else 1
    print(f"{args.dataset} PGD-AT ({args.norm}, eps={eps:.4f}, {steps} steps) [PARALLEL]: {len(jobs)} jobs, "
          f"{len(done_results)} resumed, {len(pending)} to run over {ng} GPU(s) x {K} workers = {nw}; "
          f"arms={arms} widths={widths} epochs={args.epochs} seeds={args.seeds}\n", flush=True)
    t0 = time.time()
    if pending:
        if ng <= 0:
            for (arm, w, s) in pending: run_job_at((None, arm, w, s, A))
        else:
            ctx = mp.get_context("spawn")
            task_q = ctx.Queue()
            for t in pending: task_q.put(t)
            for _ in range(nw): task_q.put(None)               # one sentinel per worker
            workers = [ctx.Process(target=_worker, args=(wid, wid % ng, nw, task_q, A))
                       for wid in range(nw)]
            for p in workers: p.start()
            for p in workers: p.join()                          # workers save to disk; we read below
    # assemble the FULL grid from disk (robust to a worker dying); report any gaps for a resume
    results, missing = [], []
    for (arm, w, s) in jobs:
        jf = _job_file(A, arm, w, s)
        if os.path.exists(jf):
            try: results.append(json.load(open(jf))); continue
            except Exception: pass
        missing.append((arm, w, s))
    print(f"\nwall {time.time()-t0:.0f}s ({len(results)}/{len(jobs)} jobs on disk)", flush=True)
    if missing:
        print(f"WARNING: {len(missing)} job(s) missing (worker died/OOM?): {missing} -- re-run to resume", flush=True)

    # aggregate + save -- IDENTICAL JSON structure to cifar_at.py (args/recipe/aa_specs/results/rows)
    agg = {}
    for r in results: agg.setdefault((r["arm"], r["w"]), []).append(r)
    def g(rs, k): return float(np.mean([x[k] for x in rs if k in x and x[k] is not None]))
    aa_names = [s[0] for s in aa_specs]
    rows = []
    for w in widths:
        for arm in arms:
            rs = agg[(arm, w)]
            rows.append(dict(arm=arm, w=w, consist=g(rs,'consist'), rr_l2=g(rs,'rr_l2'),
                             etaL=g(rs,'dec_etaL'), margin=g(rs,'dec_margin'), L2=g(rs,'dec_L2'),
                             L1=g(rs,'dec_L1'), **{('aa_'+n): g(rs,'aa_'+n) for n in aa_names}))
    os.makedirs(RESDIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    fn = os.path.join(RESDIR, f"at_{args.dataset}_{args.norm}_{args.tag}_{stamp}.json")
    recipe = dict(dataset=args.dataset, norm=args.norm, eps=eps, alpha=alpha, steps=steps, flip=flip)
    json.dump(dict(args=vars(args), recipe=recipe, aa_specs=aa_specs, results=results, rows=rows,
                   scheduler="parallel", workers_per_gpu=K, ngpu=ng), open(fn, "w"), indent=2)
    print(f"saved {fn}", flush=True)

if __name__ == "__main__":
    main()
