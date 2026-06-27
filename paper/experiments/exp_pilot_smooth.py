#!/usr/bin/env python3
"""
PILOT: does a SMOOTH activation break PGD-AT's self-limiting margin<->sensitivity coupling?

The host paper's finding (resnet_persample.py Q-C / cifar_at.py decomposition): under PGD adversarial
training a ReLU network buys classification margin by SHARPENING -- it raises the input-gradient
sensitivity ||grad_x M(x)||_2 at the same time, so per-sample margin M and per-sample sensitivity are
POSITIVELY coupled (Spearman ~ +0.5 for ReLU AT). That coupling is self-limiting: AT cannot push the
threat-matched ratio eta/L up indefinitely because raising the margin drags the gradient norm up with it.

HYPOTHESIS. A smooth activation (SiLU/GELU/softplus-beta10) cannot create the sharp, piecewise-linear
kinks ReLU uses to sharpen, so it should (a) WEAKEN the per-sample margin<->sensitivity coupling and
(b) let margin grow with less sensitivity, improving AutoAttack robust accuracy at matched everything
else. This pilot tests BOTH halves at matched capacity (activations add NO parameters, so the parameter
count is identical across activations by construction -- asserted in build_smooth).

ONE controlled knob: the activation. The backbone (CIFARNet arm="standard"), the PGD-AT recipe
(cifar_at.adv_train VERBATIM: CIFAR Linf eps=8/255, 7 steps, alpha=2/255, cosine SGD, horizontal-flip
aug, 30 epochs), the data, and every evaluation are held fixed. Per cell we report clean acc, AutoAttack
Linf 8/255 (ground truth) + matched PGD (gradient-masking check: AA must be <= PGD), the eta/L
decomposition, the DDN L2 robust radius, and -- the key diagnostic -- the per-sample coupling Spearman.

Reuses build / load_data / dataset_stats / in_channels / accuracy / correct_mask / shift_consistency /
robust_radius_l2 / etaL_decomposition / autoattack_acc / pgd_acc / nparams from cifar_dissection, and
adv_train (the PGD-AT recipe) VERBATIM from cifar_at. Only the activation swap + the coupling metric are
new. Progressive per-cell save + resume; exp3/tmreg-style OOM-robust per-GPU worker pool; AA_BS honored.

Smoke:  PYTHONNOUSERSITE=1 ../env/cenv/bin/python exp_pilot_smooth.py --smoke
Full:   PYTHONNOUSERSITE=1 AA_BS=500 ../env/cenv/bin/python exp_pilot_smooth.py \
            --acts relu silu gelu --widths 48 --seeds 2 --aa_n 2000 --gpus 2 --workers_per_gpu 2
"""
import argparse, os, json, time, numpy as np, torch, torch.nn as nn
import torch.multiprocessing as mp
from scipy.stats import spearmanr
from cifar_dissection import (build, load_data, dataset_stats, in_channels, accuracy, correct_mask,
                              shift_consistency, robust_radius_l2, etaL_decomposition, autoattack_acc,
                              pgd_acc, nparams, CIFAR_MEAN, CIFAR_STD)
from cifar_at import adv_train

RESDIR = os.path.join(os.path.dirname(__file__), "..", "results")
PARTDIR = os.path.join(RESDIR, "at_partial", "pilot_smooth")

# Activation factories. ReLU is the baseline (the backbone is built with nn.ReLU(inplace=True)); the
# smooth alternatives carry NO learnable parameters, so swapping them in cannot change the param count.
# softplus(beta=10) is a near-ReLU but everywhere-smooth control (limit beta->inf recovers ReLU).
ACTS = {
    "relu":     lambda: nn.ReLU(inplace=True),
    "silu":     lambda: nn.SiLU(),
    "gelu":     lambda: nn.GELU(),
    "softplus": lambda: nn.Softplus(beta=10),
}

# ---------------- activation swap (recursive, in-place) ----------------
def _swap_relu(module, factory):
    """Recursively replace EVERY nn.ReLU submodule (in-place) with factory(). Works through
    nn.Sequential (whose children are string-indexed) since nn.Module.__setattr__ re-registers."""
    for name, child in module.named_children():
        if isinstance(child, nn.ReLU):
            setattr(module, name, factory())
        else:
            _swap_relu(child, factory)

def count_relu(model):
    return sum(isinstance(m, nn.ReLU) for m in model.modules())

def build_smooth(act, w, in_ch=3, norm_mean=CIFAR_MEAN, norm_std=CIFAR_STD):
    """Build CIFARNet(arm='standard', w) and swap every ReLU for `act`. Asserts the swap leaves the
    parameter count IDENTICAL to the relu backbone (capacity is matched by construction)."""
    assert act in ACTS, f"act must be one of {list(ACTS)}; got {act!r}"
    model = build("standard", w, in_ch=in_ch, norm_mean=norm_mean, norm_std=norm_std)
    if act != "relu":
        _swap_relu(model, ACTS[act])
        assert count_relu(model) == 0, f"{act} model still contains {count_relu(model)} nn.ReLU module(s)"
    ref = build("standard", w, in_ch=in_ch, norm_mean=norm_mean, norm_std=norm_std)   # relu reference
    assert nparams(model) == nparams(ref), \
        f"param count changed under {act}: {nparams(model)} != relu {nparams(ref)}"
    return model

# ---------------- the key diagnostic: per-sample margin<->sensitivity coupling ----------------
def coupling_spearman(model, X, y, dev, n_max=3000, bs=128):
    """Host-paper SELF-LIMITING COUPLING metric. Spearman correlation, across CORRECTLY-CLASSIFIED test
    points, between the per-sample active-logit margin M(x) = logit_y - max_{j!=y} logit_j and the
    per-sample input-gradient L2 norm ||grad_x M(x)||_2. Convention is byte-identical to
    resnet_run.margin_stats and cifar_dissection.etaL_decomposition (grad of M.sum(), per-sample
    flatten-then-L2). Expected ~ +0.5 for ReLU PGD-AT; the hypothesis is that a smooth activation
    weakens (lowers) it."""
    cm = correct_mask(model, X, y, dev)
    Xc, yc = X[cm][:n_max], y[cm][:n_max]
    ms, g2s = [], []
    for i in range(0, len(Xc), bs):
        xb = Xc[i:i + bs].to(dev).requires_grad_(True); yb = yc[i:i + bs].to(dev)
        logits = model(xb)
        true = logits.gather(1, yb[:, None]).squeeze(1)
        other = logits.clone().scatter_(1, yb[:, None], -1e9).max(1).values
        m = true - other
        g, = torch.autograd.grad(m.sum(), xb); gf = g.flatten(1)
        ms.append(m.detach().cpu().numpy()); g2s.append(gf.norm(dim=1).detach().cpu().numpy())
    M = np.concatenate(ms); G2 = np.concatenate(g2s)
    fin = np.isfinite(M) & np.isfinite(G2)
    if fin.sum() < 10:
        return float("nan")
    return float(spearmanr(M[fin], G2[fin])[0])

# ---------------- progressive per-cell save + resume ----------------
def _jf(act, w, seed):
    return os.path.join(PARTDIR, f"{act}_w{w}_s{seed}.json")
def _save(out):
    os.makedirs(PARTDIR, exist_ok=True)
    p = _jf(out["act"], out["w"], out["seed"]); tmp = p + ".tmp"
    json.dump(out, open(tmp, "w"), default=float); os.replace(tmp, p)        # atomic publish

# ---------------- one cell: PGD-AT (verbatim recipe) + full eval ----------------
def run_job(task):
    gpu, act, w, seed, A = task
    dev = f"cuda:{gpu}" if (gpu is not None and torch.cuda.is_available()) else "cpu"
    if dev.startswith("cuda"): torch.cuda.set_device(gpu)
    ds = A["dataset"]
    Xtr, ytr, Xte, yte = load_data(ds, A["n"], A["ntest"], seed=0)
    nmean, nstd = dataset_stats(ds)
    model = build_smooth(act, w, in_ch=in_channels(ds), norm_mean=nmean, norm_std=nstd)
    # PGD-AT, recipe VERBATIM from cifar_at.adv_train (Linf): eps=8/255, 7 steps, alpha=2/255,
    # cosine SGD, horizontal-flip aug, 30 epochs. arm='standard' -> shift_aug=False.
    model = adv_train(model, Xtr, ytr, dev, epochs=A["epochs"], seed=seed,
                      eps=A["eps"], alpha=A["alpha"], steps=A["steps"], norm="linf",
                      aug=A["flip"], shift_aug=False)
    out = dict(act=act, arm="standard", w=w, seed=seed, dataset=ds, params=nparams(model),
               eps=A["eps"], alpha=A["alpha"], steps=A["steps"], epochs=A["epochs"], n=A["n"])
    out["clean"] = accuracy(model, Xte, yte, dev)
    out["consist"] = shift_consistency(model, Xte, dev)
    cm = correct_mask(model, Xte, yte, dev); Xc, yc = Xte[cm], yte[cm]
    out["rr_l2"] = robust_radius_l2(model, Xc[:A["rad_n"]], yc[:A["rad_n"]], dev)
    out["rr_n"] = int(min(A["rad_n"], len(Xc)))
    out.update({("dec_" + k): v for k, v in etaL_decomposition(model, Xte, yte, dev).items()})
    out["coupling_spearman"] = coupling_spearman(model, Xte, yte, dev, n_max=A["coupling_n"])
    if A["aa_n"] > 0:
        # matched PGD (gradient-masking check: AA <= PGD must hold) + AutoAttack ground truth, Linf 8/255
        out["pgd_Linf_8_255"] = pgd_acc(model, Xte[:A["aa_n"]], yte[:A["aa_n"]], dev, A["eval_eps"],
                                        "linf", steps=A["pgd_steps"])
        out["aa_Linf_8_255"] = autoattack_acc(model, Xte, yte, dev, A["eval_eps"], "Linf",
                                              n=A["aa_n"], version=A["aa_version"])
    _save(out)
    return out

# ---------------- tmreg/exp3-style per-GPU worker pool (OOM-robust; saves to disk) ----------------
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
        act, w, seed = item
        try:
            run_job((gpu, act, w, seed, A))
        except Exception as e:
            print(f"[w{wid} gpu{gpu}] {(act, w, seed)} FAILED: {type(e).__name__}: {e}", flush=True)

# ---------------- smoke: one tiny cell + the structural assertions ----------------
def _smoke():
    print("=== SMOKE exp_pilot_smooth ===", flush=True)
    nmean, nstd = dataset_stats("cifar")
    relu = build_smooth("relu", 16, in_ch=3, norm_mean=nmean, norm_std=nstd)
    silu = build_smooth("silu", 16, in_ch=3, norm_mean=nmean, norm_std=nstd)
    print(f"param count  relu w16 = {nparams(relu)}   silu w16 = {nparams(silu)}   "
          f"identical={nparams(relu) == nparams(silu)}", flush=True)
    print(f"nn.ReLU modules  relu={count_relu(relu)}  silu={count_relu(silu)}  "
          f"(silu must be 0)", flush=True)
    assert nparams(relu) == nparams(silu)
    assert count_relu(silu) == 0
    A = dict(dataset="cifar", flip=True, n=2000, ntest=1000, epochs=3, eps=8/255, alpha=2/255, steps=7,
             rad_n=200, aa_n=200, aa_version="custom", pgd_steps=10, coupling_n=1000, eval_eps=8/255)
    gpu = 0 if torch.cuda.is_available() else None
    t0 = time.time()
    out = run_job((gpu, "silu", 16, 0, A))
    print(f"\ntrained+evaluated one cell in {time.time()-t0:.0f}s; partial JSON written to "
          f"{_jf('silu', 16, 0)}\n", flush=True)
    print(json.dumps(out, indent=2, default=float), flush=True)
    print(f"\ncoupling_spearman = {out['coupling_spearman']}  (finite={np.isfinite(out['coupling_spearman'])})",
          flush=True)
    assert np.isfinite(out["coupling_spearman"]), "coupling_spearman is not finite"
    print("SMOKE OK", flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--acts", nargs="+", default=["relu", "silu", "gelu"],
                    help=f"activations to compare; choose from {list(ACTS)}")
    ap.add_argument("--widths", type=int, nargs="+", default=[48])
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--dataset", default="cifar", choices=["cifar", "mnist", "fashion"])
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--n", type=int, default=50000); ap.add_argument("--ntest", type=int, default=10000)
    ap.add_argument("--eps", type=float, default=8/255); ap.add_argument("--alpha", type=float, default=2/255)
    ap.add_argument("--steps", type=int, default=7)
    ap.add_argument("--rad_n", type=int, default=1000); ap.add_argument("--aa_n", type=int, default=2000)
    ap.add_argument("--coupling_n", type=int, default=3000, help="#correct test pts for the coupling Spearman")
    ap.add_argument("--aa_version", default="standard"); ap.add_argument("--pgd_steps", type=int, default=20)
    ap.add_argument("--gpus", type=int, default=2); ap.add_argument("--workers_per_gpu", type=int, default=2)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    for act in a.acts:
        if act not in ACTS: raise SystemExit(f"bad act '{act}'; choose from {list(ACTS)}")
    if a.smoke:
        _smoke(); return
    A = dict(dataset=a.dataset, flip=(a.dataset == "cifar"), n=a.n, ntest=a.ntest, epochs=a.epochs,
             eps=a.eps, alpha=a.alpha, steps=a.steps, rad_n=a.rad_n, aa_n=a.aa_n, coupling_n=a.coupling_n,
             aa_version=a.aa_version, pgd_steps=a.pgd_steps, eval_eps=8/255)
    ng = min(a.gpus, torch.cuda.device_count()) if torch.cuda.is_available() else 0
    # memory-aware concurrency (CIFAR 3-channel + standard-AutoAttack is heavy); scheduling only, never
    # changes a cell's result (each cell still runs the identical run_job) -- smaller K is just slower.
    K = max(1, a.workers_per_gpu); _maxw = max(a.widths); _heavy = (a.dataset == "cifar")
    if _maxw >= 96: K = min(K, 1)
    elif _heavy: K = min(K, 2)
    elif _maxw >= 64: K = min(K, 2)
    nw = max(1, ng * K) if ng > 0 else 1
    load_data(a.dataset, 10, 10)                                  # download once before forking
    jobs = sorted([(act, w, s) for act in a.acts for w in a.widths for s in range(a.seeds)],
                  key=lambda j: j[1] * j[1], reverse=True)         # cost-sort by width^2 (round-robin balance)
    pending = [j for j in jobs if not os.path.exists(_jf(*j))]
    print(f"PILOT smooth-activation ({a.dataset}, arm=standard, PGD-AT Linf eps={a.eps:.4f}, {a.steps} steps): "
          f"{len(jobs)} cells ({len(jobs)-len(pending)} resumed), {len(pending)} to run over "
          f"{ng or 'CPU'} GPU x {K} workers; acts={a.acts} widths={a.widths} seeds={a.seeds} "
          f"aa_n={a.aa_n}\n", flush=True)
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
    fn = os.path.join(RESDIR, f"exp_pilot_smooth_{a.dataset}_{stamp}.json")
    json.dump(dict(args=vars(a), results=results, missing=miss), open(fn, "w"), indent=2, default=float)
    # console summary (per activation, averaged over widths+seeds)
    if results:
        agg = {}
        for r in results: agg.setdefault(r["act"], []).append(r)
        def g(rs, k): return float(np.mean([x[k] for x in rs if k in x and x[k] is not None]))
        hdr = (f"{'act':9s} {'clean':>6s} {'consist':>7s} {'margin':>7s} {'L2':>7s} {'etaL':>6s} "
               f"{'rr_L2':>6s} {'coupling':>8s} {'pgd':>6s} {'AA':>6s} {'mask_ok':>7s}")
        print("\n" + hdr); print("-" * len(hdr))
        for act in [a for a in ACTS if a in agg]:
            rs = agg[act]
            pgd = g(rs, "pgd_Linf_8_255"); aa = g(rs, "aa_Linf_8_255")
            ok = "yes" if aa <= pgd + 0.02 else "NO!"          # AA must be <= PGD (gradient-masking check)
            print(f"{act:9s} {g(rs,'clean'):6.3f} {g(rs,'consist'):7.3f} {g(rs,'dec_margin'):7.3f} "
                  f"{g(rs,'dec_L2'):7.3f} {g(rs,'dec_etaL'):6.3f} {g(rs,'rr_l2'):6.3f} "
                  f"{g(rs,'coupling_spearman'):8.3f} {pgd:6.3f} {aa:6.3f} {ok:>7s}")
        print("\nREAD: hypothesis predicts smooth acts have a LOWER coupling Spearman than relu AND a "
              "higher AA.")
    print(f"\nwall {time.time()-t0:.0f}s; {len(results)}/{len(jobs)} cells; saved {fn}", flush=True)
    if miss: print(f"WARNING missing {len(miss)}: {miss} -- re-run to resume", flush=True)

if __name__ == "__main__":
    main()
