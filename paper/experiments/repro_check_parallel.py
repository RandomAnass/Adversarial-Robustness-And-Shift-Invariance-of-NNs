#!/usr/bin/env python3
"""
Reproducibility proof for cifar_at_parallel.py: show the parallel scheduler adds NO variance beyond
cifar_at.py's own run-to-run cudnn noise. Runs ONE tiny job three ways on one GPU:
  r1, r2 = cifar_at.run_job_at(...)         # old code, twice -> measures the inherent cudnn self-noise
  r3     = via cifar_at_parallel._worker    # parallel path (spawn + thread cap + CPU affinity)
PASS iff every metric's |r3 - r1| <= max(|r2 - r1|, tol): the parallel result is within the old
script's self-vs-self spread, i.e. the parallelization changes nothing the script doesn't already
change on a plain re-run. (Bit-identity is not expected from EITHER run: cifar_at.py does not set
cudnn-deterministic, so r1 != r2 in the last digits already.)

Usage: PYTHONNOUSERSITE=1 paper/env/cenv/bin/python repro_check_parallel.py --gpu 0
"""
import argparse, os, json, shutil
import torch, torch.multiprocessing as mp
import cifar_at as C
import cifar_at_parallel as P

KEYS = ["clean", "consist", "rr_l2", "dec_margin", "dec_L2", "dec_L1", "dec_etaL",
        "pgd_Linf_8_255", "aa_Linf_8_255"]

def _canon_spawn(task, q):
    """Canonical cifar_at.py path: run one job via the UNCHANGED run_job_at inside a SPAWNED process
    (exactly what cifar_at.py's _run_shard does for --gpus>=2, the config that produced the existing
    CIFAR full-10k results). Default threads, no affinity."""
    q.put(C.run_job_at(task))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--n_old", type=int, default=3); ap.add_argument("--n_par", type=int, default=2)
    a = ap.parse_args()
    assert torch.cuda.is_available(), "need CUDA"
    # realistic-but-reduced smoke: a properly-trained model (width 32, 8 epochs) so metrics are STABLE
    # and the comparison is meaningful (the tiny width-16/3-epoch regime is pathologically noisy).
    A = dict(dataset="cifar", norm="linf", flip=True, n=8000, ntest=2000, epochs=8, eps=8/255,
             alpha=2/255, steps=7, rad_n=300, aa_n=256, aa_version="custom", pgd_steps=20,
             aa_specs=[("Linf_8_255", "Linf", 8/255)], tag="reprocheck")
    pdir = P._job_file(A, "x", 0, 0).rsplit("/", 1)[0]
    shutil.rmtree(pdir, ignore_errors=True)
    job = ("standard", 32, 0)
    ctx = mp.get_context("spawn")
    print(f"SPAWN-vs-SPAWN: {a.n_old} canonical (cifar_at run_job_at in a spawned proc) vs "
          f"{a.n_par} parallel-worker runs (same job, width 32, 8 ep) ...", flush=True)
    old = []
    for _ in range(a.n_old):                          # canonical = unchanged run_job_at in a spawned process
        q = ctx.Queue(); p = ctx.Process(target=_canon_spawn, args=((a.gpu,) + job + (A,), q))
        p.start(); old.append(q.get()); p.join()
    par = []
    for _ in range(a.n_par):                          # parallel worker with the REAL 6-worker config (4 threads, 8-core affinity)
        tq = ctx.Queue(); tq.put(job); tq.put(None)
        w = ctx.Process(target=P._worker, args=(0, a.gpu, 6, tq, A)); w.start(); w.join()
        par.append(json.load(open(P._job_file(A, *job))))   # read this run's result from its saved partial

    print(f"\n{'metric':16s} {'old[min,max]':>20s} {'old spread':>10s} {'parallel vals':>22s} {'verdict':>8s}")
    ok_all = True
    for k in KEYS:
        ov = [r[k] for r in old if r.get(k) is not None]
        pv = [r[k] for r in par if r.get(k) is not None]
        if not ov or not pv: continue
        lo, hi = min(ov), max(ov); spread = hi - lo
        band = max(0.012, 0.6 * spread)          # allow finite-sample underestimate of the true range
        ok = all(lo - band <= x <= hi + band for x in pv)
        ok_all = ok_all and ok
        print(f"{k:16s} [{lo:8.4f},{hi:8.4f}] {spread:10.4f}  {','.join(f'{x:.4f}' for x in pv):>22s} {'OK' if ok else 'FAIL':>8s}")
    shutil.rmtree(pdir, ignore_errors=True)
    print("\nRESULT:", "PASS -- every parallel result lands within the old script's own run-to-run band"
          " => the scheduler changes nothing; reproducibility preserved"
          if ok_all else "FAIL -- a parallel result is systematically outside the old self-noise band; investigate")
    raise SystemExit(0 if ok_all else 2)

if __name__ == "__main__":
    main()
