#!/usr/bin/env python3
"""
Adversarial-training (PGD-AT, Madry) version of the capacity-matched CIFAR-10 dissection, so
AutoAttack at the standard threshold ($\\ell_\\infty=8/255$) is informative. Tests whether the
standard-training decomposition story survives robustification: does anti-aliasing still act on
the Lipschitz term and exact invariance still cost margin, once models are PGD-AT robustified?

Same four capacity-matched arms as cifar_dissection.py; only the training loop changes (each
batch is replaced by its $\\ell_\\infty$ PGD adversarial before the weight update). Reuses the
validated models, DDN robust radius, eta/L decomposition, and AutoAttack wiring.

Run:    paper/env/cenv/bin/python paper/experiments/cifar_at.py --tag at
Smoke:  paper/env/cenv/bin/python paper/experiments/cifar_at.py --smoke
"""
import argparse, os, json, time, numpy as np, torch, torch.nn.functional as F
import torch.multiprocessing as mp
from itertools import product
from cifar_dissection import (build, load_cifar, load_data, dataset_stats, in_channels,
                              accuracy, correct_mask, shift_consistency,
                              robust_radius_l2, etaL_decomposition, autoattack_acc, pgd_acc,
                              circular_roll, nparams, ARMS)

RESDIR = os.path.join(os.path.dirname(__file__), "..", "results")

# ---------------- progressive (per-job) save + resume ----------------
# Each finished job is written atomically to its own file the moment it completes, so a kill/crash
# never loses completed work (the all-or-nothing aggregate JSON was the failure mode). A re-run skips
# jobs whose file already exists and re-assembles the aggregate from disk.
def _partial_dir(A):
    return os.path.join(RESDIR, "at_partial", f"{A['dataset']}_{A['norm']}_{A.get('tag','at')}")
def _job_file(A, arm, w, seed):
    return os.path.join(_partial_dir(A), f"{arm}_w{w}_s{seed}.json")
def _save_job(A, out):
    d = _partial_dir(A); os.makedirs(d, exist_ok=True)
    p = _job_file(A, out["arm"], out["w"], out["seed"]); tmp = p + ".tmp"
    json.dump(out, open(tmp, "w"), default=float); os.replace(tmp, p)   # atomic publish

# ---------------- PGD-AT (Madry): replace each batch by its Linf PGD adversarial ----------------
def pgd_linf(model, x, y, eps, alpha, steps):
    delta = torch.zeros_like(x).uniform_(-eps, eps)
    delta = (torch.clamp(x + delta, 0, 1) - x)
    for _ in range(steps):
        delta.requires_grad_(True)
        loss = F.cross_entropy(model(torch.clamp(x + delta, 0, 1)), y)
        g, = torch.autograd.grad(loss, delta)
        delta = (delta + alpha * g.sign()).clamp(-eps, eps).detach()
        delta = (torch.clamp(x + delta, 0, 1) - x).detach()
    return torch.clamp(x + delta, 0, 1).detach()

def pgd_l2(model, x, y, eps, alpha, steps):
    # normalized-gradient L2 PGD with random init in the ball (torchattacks / MadryLab convention)
    delta = torch.zeros_like(x).normal_()
    dn = delta.flatten(1).norm(dim=1).clamp_min(1e-12)
    r = torch.rand(len(x), device=x.device)
    delta = (delta / dn[:, None, None, None] * (r * eps)[:, None, None, None])
    delta = (torch.clamp(x + delta, 0, 1) - x)
    for _ in range(steps):
        delta.requires_grad_(True)
        loss = F.cross_entropy(model(torch.clamp(x + delta, 0, 1)), y)
        g, = torch.autograd.grad(loss, delta)
        gn = g / g.flatten(1).norm(dim=1).clamp_min(1e-12)[:, None, None, None]
        delta = (delta + alpha * gn).detach()
        nrm = delta.flatten(1).norm(dim=1).clamp_min(1e-12)
        delta = (delta * (eps / nrm).clamp(max=1.0)[:, None, None, None]).detach()
        delta = (torch.clamp(x + delta, 0, 1) - x).detach()
    return torch.clamp(x + delta, 0, 1).detach()

def adv_train(model, X, y, dev, epochs=30, bs=128, lr=0.1, wd=5e-4, seed=0,
              eps=8/255, alpha=2/255, steps=7, norm="linf", aug=True, shift_aug=False):
    attack = pgd_linf if norm == "linf" else pgd_l2
    torch.manual_seed(seed)
    model = model.to(dev).train()
    opt = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9, weight_decay=wd, nesterov=True)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    X, y = X.to(dev), y.to(dev); n = len(X)
    for ep in range(epochs):
        perm = torch.randperm(n, device=dev)
        for i in range(0, n, bs):
            idx = perm[i:i + bs]; xb = X[idx]; yb = y[idx]
            if aug:
                flip = torch.rand(xb.size(0), device=dev) < 0.5
                xb = torch.where(flip[:, None, None, None], xb.flip(-1), xb)
            if shift_aug:
                xb = circular_roll(xb, 4)
            x_adv = attack(model, xb, yb, eps, alpha, steps)   # inner max (linf or l2)
            opt.zero_grad(set_to_none=True)
            F.cross_entropy(model(x_adv), yb).backward(); opt.step()  # outer min
        sched.step()
    return model.eval()

def run_job_at(task):
    gpu, arm, w, seed, A = task
    dev = f"cuda:{gpu}" if (gpu is not None and torch.cuda.is_available()) else "cpu"
    if dev.startswith("cuda"): torch.cuda.set_device(gpu)
    ds = A["dataset"]
    Xtr, ytr, Xte, yte = load_data(ds, A["n"], A["ntest"], seed=0)
    nmean, nstd = dataset_stats(ds)
    model = adv_train(build(arm, w, in_ch=in_channels(ds), norm_mean=nmean, norm_std=nstd),
                      Xtr, ytr, dev, epochs=A["epochs"], seed=seed,
                      eps=A["eps"], alpha=A["alpha"], steps=A["steps"], norm=A["norm"],
                      aug=A["flip"], shift_aug=(arm == "aug"))
    out = dict(arm=arm, w=w, seed=seed, params=nparams(model))
    out["clean"] = accuracy(model, Xte, yte, dev)
    out["consist"] = shift_consistency(model, Xte, dev)
    cm = correct_mask(model, Xte, yte, dev); Xc, yc = Xte[cm], yte[cm]
    out["rr_l2"] = robust_radius_l2(model, Xc[:A["rad_n"]], yc[:A["rad_n"]], dev)
    out["rr_n"] = int(min(A["rad_n"], len(Xc)))
    out.update({("dec_" + k): v for k, v in etaL_decomposition(model, Xte, yte, dev).items()})
    for (nm, norm, eps) in A["aa_specs"]:                # AA is informative now -> run on ALL seeds
        out["pgd_" + nm] = pgd_acc(model, Xte[:A["aa_n"]], yte[:A["aa_n"]], dev, eps,
                                   "linf" if norm == "Linf" else "l2", steps=A["pgd_steps"])
        out["aa_" + nm] = autoattack_acc(model, Xte, yte, dev, eps, norm,
                                         n=A["aa_n"], version=A["aa_version"])
    _save_job(A, out)                                    # progressive save: publish this job before returning
    return out

def _run_shard(shard, q):
    for t in shard:
        q.put(run_job_at(t))

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
    ap.add_argument("--gpus", type=int, default=99); ap.add_argument("--serial", action="store_true")
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--tag", default="at")
    args = ap.parse_args()
    widths, arms = args.widths, args.arms
    # recipe by (dataset, norm). Sources: Madry MNIST Linf 0.3/PGD; Fashion-MNIST Linf 0.1; RobustBench CIFAR Linf 8/255, L2 0.5.
    # cifar/linf alpha=2/255 is the canonical Madry value (deliberately NOT 2.5*eps/steps); the others follow 2.5*eps/steps.
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
    A = dict(dataset=args.dataset, norm=args.norm, flip=flip, n=args.n, ntest=args.ntest,
             epochs=args.epochs, eps=eps, alpha=alpha, steps=steps, rad_n=args.rad_n, aa_n=args.aa_n,
             aa_version=args.aa_version, pgd_steps=args.pgd_steps, aa_specs=aa_specs, tag=args.tag)
    load_data(args.dataset, 10, 10)
    jobs = sorted(product(arms, widths, range(args.seeds)),
                  key=lambda j: (16 if j[0] == "circular" else 1) * j[1] * j[1], reverse=True)
    # resume: skip jobs already saved to disk (progressive save), re-balance the rest across GPUs
    done_results, pending = [], []
    for (arm, w, s) in jobs:
        jf = _job_file(A, arm, w, s)
        if os.path.exists(jf):
            try: done_results.append(json.load(open(jf))); continue
            except Exception: pass
        pending.append((arm, w, s))
    tasks = [((i % ng) if ng > 0 else None, arm, w, s, A) for i, (arm, w, s) in enumerate(pending)]
    print(f"{args.dataset} PGD-AT ({args.norm}, eps={eps:.4f}, {steps} steps): {len(jobs)} jobs total, "
          f"{len(done_results)} resumed from disk, {len(tasks)} to run over {ng or 'CPU'} GPU(s); "
          f"arms={arms} widths={widths} epochs={args.epochs} seeds={args.seeds}\n", flush=True)
    t0 = time.time()
    computed = []
    if tasks:
        if args.serial or ng <= 1:
            computed = [run_job_at(t) for t in tasks]
        else:
            ctx = mp.get_context("spawn")
            shards = [[t for t in tasks if t[0] == g] for g in range(ng)]
            q = ctx.Queue()
            procs = [ctx.Process(target=_run_shard, args=(shards[g], q)) for g in range(ng)]
            for p in procs: p.start()
            computed = [q.get() for _ in range(len(tasks))]
            for p in procs: p.join()
    results = done_results + computed     # full grid, re-assembled from disk + this run
    print(f"\nwall {time.time()-t0:.0f}s", flush=True)

    agg = {}
    for r in results:
        agg.setdefault((r["arm"], r["w"]), []).append(r)
    def g(rs, k): return float(np.mean([x[k] for x in rs if k in x and x[k] is not None]))
    aa_names = [s[0] for s in aa_specs]
    hdr = (f"{'arm':9s} {'w':>3s} {'clean':>6s} {'consist':>7s} {'rr_L2':>6s} {'margin':>7s} {'L2':>7s} "
           f"{'etaL':>6s} " + " ".join(f"{'aa_'+n:>12s}" for n in aa_names))
    print(hdr); print("-" * len(hdr))
    rows = []
    for w in widths:
        for arm in arms:
            rs = agg[(arm, w)]
            print(f"{arm:9s} {w:3d} {g(rs,'clean'):6.3f} {g(rs,'consist'):7.3f} {g(rs,'rr_l2'):6.3f} "
                  f"{g(rs,'dec_margin'):7.3f} {g(rs,'dec_L2'):7.3f} {g(rs,'dec_etaL'):6.3f} "
                  + " ".join(f"{g(rs,'aa_'+n):12.3f}" for n in aa_names))
            rows.append(dict(arm=arm, w=w, consist=g(rs,'consist'), rr_l2=g(rs,'rr_l2'),
                             etaL=g(rs,'dec_etaL'), margin=g(rs,'dec_margin'), L2=g(rs,'dec_L2'),
                             L1=g(rs,'dec_L1'),
                             **{('aa_'+n): g(rs,'aa_'+n) for n in aa_names}))
    pa_name, pa_norm = aa_specs[0][0], aa_specs[0][1]   # primary (threat-matched) AutoAttack spec
    aakey = "aa_" + pa_name
    # matched ratio uses the dual of the training norm (Linf->L1, L2->L2); mismatched uses the other.
    for x in rows:
        if pa_norm == "Linf":
            x["match"] = x["margin"] / x["L1"]; x["mismatch"] = x["margin"] / x["L2"]
        else:
            x["match"] = x["margin"] / x["L2"]; x["mismatch"] = x["margin"] / x["L1"]
    if len(rows) >= 3:
        from scipy.stats import pearsonr, spearmanr
        rr = np.array([x['rr_l2'] for x in rows]); mt = np.array([x['match'] for x in rows])
        mm = np.array([x['mismatch'] for x in rows]); cs = np.array([x['consist'] for x in rows])
        aa = np.array([x[aakey] for x in rows])
        dmatch = "||grad M||_1" if pa_norm == "Linf" else "||grad M||_2"
        dmiss = "||grad M||_2" if pa_norm == "Linf" else "||grad M||_1"
        print(f"\nAcross {len(rows)} cells [{A['dataset']} {A['norm']}-AT, primary AA={pa_name}]:")
        print(f"  MATCHED   eta/{dmatch} vs AA : Pearson {pearsonr(mt,aa)[0]:+.3f} Spearman {spearmanr(mt,aa)[0]:+.3f}")
        print(f"  mismatched eta/{dmiss} vs AA : Pearson {pearsonr(mm,aa)[0]:+.3f} Spearman {spearmanr(mm,aa)[0]:+.3f}")
        print(f"  consistency             vs AA : Pearson {pearsonr(cs,aa)[0]:+.3f} Spearman {spearmanr(cs,aa)[0]:+.3f}")
    print("\nWithin-width decomposition vs standard:")
    for w in widths:
        base = next(x for x in rows if x['arm'] == "standard" and x['w'] == w)
        for x in rows:
            if x['w'] != w or x['arm'] == "standard": continue
            dm = np.log(x['margin']/base['margin']); dL = np.log(x['L2']/base['L2'])
            print(f"  w={w} {x['arm']:9s}: Dlog margin {dm:+.3f}  Dlog L2 {dL:+.3f}  Dlog(eta/L) {dm-dL:+.3f}  "
                  f"(AA {x[aakey]:.3f} vs {base[aakey]:.3f})")
    os.makedirs(RESDIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    fn = os.path.join(RESDIR, f"at_{args.dataset}_{args.norm}_{args.tag}_{stamp}.json")
    recipe = dict(dataset=args.dataset, norm=args.norm, eps=eps, alpha=alpha, steps=steps, flip=flip)
    json.dump(dict(args=vars(args), recipe=recipe, aa_specs=aa_specs, results=results, rows=rows), open(fn, "w"), indent=2)
    print(f"\nsaved {fn}")

if __name__ == "__main__":
    main()
