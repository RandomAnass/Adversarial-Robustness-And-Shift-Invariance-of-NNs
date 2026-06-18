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
from cifar_dissection import (build, load_cifar, accuracy, correct_mask, shift_consistency,
                              robust_radius_l2, etaL_decomposition, autoattack_acc, pgd_acc,
                              circular_roll, nparams, ARMS)

RESDIR = os.path.join(os.path.dirname(__file__), "..", "results")

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

def adv_train(model, X, y, dev, epochs=30, bs=128, lr=0.1, wd=5e-4, seed=0,
              eps=8/255, alpha=2/255, steps=7, aug=True, shift_aug=False):
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
            x_adv = pgd_linf(model, xb, yb, eps, alpha, steps)   # inner max
            opt.zero_grad(set_to_none=True)
            F.cross_entropy(model(x_adv), yb).backward(); opt.step()  # outer min
        sched.step()
    return model.eval()

def run_job_at(task):
    gpu, arm, w, seed, A = task
    dev = f"cuda:{gpu}" if (gpu is not None and torch.cuda.is_available()) else "cpu"
    if dev.startswith("cuda"): torch.cuda.set_device(gpu)
    Xtr, ytr, Xte, yte = load_cifar(A["n"], A["ntest"], seed=0)
    model = adv_train(build(arm, w), Xtr, ytr, dev, epochs=A["epochs"], seed=seed,
                      eps=A["eps"], alpha=A["alpha"], steps=A["steps"],
                      aug=True, shift_aug=(arm == "aug"))
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
    ap.add_argument("--eps", type=float, default=8/255); ap.add_argument("--alpha", type=float, default=2/255)
    ap.add_argument("--steps", type=int, default=7)
    ap.add_argument("--rad_n", type=int, default=1000); ap.add_argument("--aa_n", type=int, default=512)
    ap.add_argument("--aa_version", default="standard"); ap.add_argument("--pgd_steps", type=int, default=40)
    ap.add_argument("--gpus", type=int, default=99); ap.add_argument("--serial", action="store_true")
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--tag", default="at")
    args = ap.parse_args()
    widths, arms = args.widths, args.arms
    if args.smoke:
        args.n, args.ntest, args.epochs, args.seeds = 4000, 1000, 2, 1
        widths, arms = [16], ARMS
        args.rad_n, args.aa_n, args.aa_version, args.pgd_steps, args.steps = 200, 128, "custom", 10, 5
    aa_specs = [("Linf_8_255", "Linf", 8 / 255), ("L2_0_5", "L2", 0.5)]
    ng = min(args.gpus, torch.cuda.device_count()) if torch.cuda.is_available() else 0
    A = dict(n=args.n, ntest=args.ntest, epochs=args.epochs, eps=args.eps, alpha=args.alpha,
             steps=args.steps, rad_n=args.rad_n, aa_n=args.aa_n, aa_version=args.aa_version,
             pgd_steps=args.pgd_steps, aa_specs=aa_specs)
    load_cifar(10, 10)
    jobs = sorted(product(arms, widths, range(args.seeds)),
                  key=lambda j: (16 if j[0] == "circular" else 1) * j[1] * j[1], reverse=True)
    tasks = [((i % ng) if ng > 0 else None, arm, w, s, A) for i, (arm, w, s) in enumerate(jobs)]
    print(f"CIFAR-10 PGD-AT (eps={args.eps:.4f}, {args.steps} steps): {len(tasks)} jobs over "
          f"{ng or 'CPU'} GPU(s); arms={arms} widths={widths} epochs={args.epochs} seeds={args.seeds}\n", flush=True)
    t0 = time.time()
    if args.serial or ng <= 1:
        results = [run_job_at(t) for t in tasks]
    else:
        ctx = mp.get_context("spawn")
        shards = [[t for t in tasks if t[0] == g] for g in range(ng)]
        q = ctx.Queue()
        procs = [ctx.Process(target=_run_shard, args=(shards[g], q)) for g in range(ng)]
        for p in procs: p.start()
        results = [q.get() for _ in range(len(tasks))]
        for p in procs: p.join()
    print(f"\nwall {time.time()-t0:.0f}s")

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
                             **{('aa_'+n): g(rs,'aa_'+n) for n in aa_names}))
    if len(rows) >= 3:
        from scipy.stats import pearsonr, spearmanr
        rr = np.array([x['rr_l2'] for x in rows]); el = np.array([x['etaL'] for x in rows])
        cs = np.array([x['consist'] for x in rows]); aa = np.array([x['aa_Linf_8_255'] for x in rows])
        print(f"\nAcross {len(rows)} cells [AT]:")
        print(f"  eta/L vs rr_L2          : Pearson {pearsonr(el,rr)[0]:+.3f} Spearman {spearmanr(el,rr)[0]:+.3f}")
        print(f"  eta/L vs AA(Linf 8/255) : Pearson {pearsonr(el,aa)[0]:+.3f} Spearman {spearmanr(el,aa)[0]:+.3f}")
        print(f"  consist vs AA           : Pearson {pearsonr(cs,aa)[0]:+.3f} Spearman {spearmanr(cs,aa)[0]:+.3f}")
    print("\nWithin-width decomposition vs standard (Dlog rr = Dlog margin - Dlog L2):")
    for w in widths:
        base = next(x for x in rows if x['arm'] == "standard" and x['w'] == w)
        for x in rows:
            if x['w'] != w or x['arm'] == "standard": continue
            dm = np.log(x['margin']/base['margin']); dL = np.log(x['L2']/base['L2'])
            print(f"  w={w} {x['arm']:9s}: Dlog margin {dm:+.3f}  Dlog L2 {dL:+.3f}  Dlog(eta/L) {dm-dL:+.3f}  "
                  f"(AA {x['aa_Linf_8_255']:.3f} vs {base['aa_Linf_8_255']:.3f})")
    os.makedirs(RESDIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    fn = os.path.join(RESDIR, f"cifar_at_{args.tag}_{stamp}.json")
    json.dump(dict(args=vars(args), aa_specs=aa_specs, results=results, rows=rows), open(fn, "w"), indent=2)
    print(f"\nsaved {fn}")

if __name__ == "__main__":
    main()
