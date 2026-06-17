#!/usr/bin/env python3
"""
Controlled architectural dissection (empirical core). GPU + vectorized + multi-GPU parallel.
Knobs at ~matched capacity: conv depth, kernel, pooling (max/avg/gap), +dense, BN on/off,
plus the BN 2x2 {conv,fc}x{bn,no-bn} control (Galloway). Datasets: MNIST / Fashion-MNIST.

Per model: clean acc; two-random-shift CONSISTENCY (vectorized group-roll); robust acc under
L2-PGD and Linf-PGD (batched, on GPU); eta/L proxy = mean|logit-margin| / mean||grad_x margin||.
Tests P1/P6 (does eta/L predict robustness better than consistency?) and P5 (decoupling).

Efficiency: config x seed jobs are distributed across all available GPUs (spawn pool, one
process per GPU); the consistency metric is vectorized (<=(2s+1)^2 group rolls, no per-sample
loop); attacks are batched. --gpus caps GPU use (shared-box etiquette). --serial forces 1 proc.

Run:   paper/env/cenv/bin/python paper/experiments/dissection.py --dataset mnist
Smoke: paper/env/cenv/bin/python paper/experiments/dissection.py --smoke
"""
import argparse, os, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
import torch.multiprocessing as mp
from itertools import product
from torchvision import datasets, transforms

ROOT = os.path.join(os.path.dirname(__file__), "..", "data")

# ---------------- data (cached; each worker loads its own subset, no big pickling) ----------------
def load(dataset, n_train, n_test, seed=0):
    tf = transforms.ToTensor()
    D = datasets.MNIST if dataset == "mnist" else datasets.FashionMNIST
    tr = D(ROOT, train=True, download=True, transform=tf)
    te = D(ROOT, train=False, download=True, transform=tf)
    g = torch.Generator().manual_seed(seed)
    itr = torch.randperm(len(tr), generator=g)[:n_train]
    ite = torch.randperm(len(te), generator=g)[:n_test]
    Xtr = tr.data[itr].float().div(255.0); ytr = tr.targets[itr]
    Xte = te.data[ite].float().div(255.0); yte = te.targets[ite]
    return Xtr, ytr, Xte, yte

# ---------------- models ----------------
def circ_pad(x, p): return F.pad(x, (p, p, p, p), mode="circular")

class ConvGAP(nn.Module):
    def __init__(self, depth=1, kernel=5, pool="gap", dense=False, bn=False, h=128, ncls=10):
        super().__init__()
        self.pad = kernel // 2; self.pool = pool
        layers = []; cin = 1
        for _ in range(depth):
            layers.append(nn.Conv2d(cin, h, kernel))
            if bn: layers.append(nn.BatchNorm2d(h))
            layers.append(nn.ReLU())
            if pool != "gap":
                layers.append(nn.MaxPool2d(2) if pool == "max" else nn.AvgPool2d(2))
            cin = h
        self.feat = nn.ModuleList(layers)
        self.dense = nn.LazyLinear(128) if dense else None
        self.head = nn.LazyLinear(ncls)
    def forward(self, x):
        z = x.unsqueeze(1)
        for m in self.feat:
            z = m(circ_pad(z, self.pad)) if isinstance(m, nn.Conv2d) else m(z)
        z = z.mean(dim=(2, 3)) if self.pool == "gap" else z.flatten(1)
        if self.dense is not None: z = F.relu(self.dense(z))
        return self.head(z)

class FC(nn.Module):
    def __init__(self, depth=2, h=256, bn=False, ncls=10):
        super().__init__()
        layers = [nn.Flatten()]; cin = 28*28
        for _ in range(depth):
            layers.append(nn.Linear(cin, h))
            if bn: layers.append(nn.BatchNorm1d(h))
            layers.append(nn.ReLU()); cin = h
        layers.append(nn.Linear(h, ncls)); self.net = nn.Sequential(*layers)
    def forward(self, x): return self.net(x)

def build(cfg):
    if cfg["kind"] == "fc":
        return FC(depth=cfg.get("depth", 2), h=cfg.get("h", 256), bn=cfg.get("bn", False))
    return ConvGAP(depth=cfg.get("depth", 1), kernel=cfg.get("kernel", 5), pool=cfg.get("pool", "gap"),
                   dense=cfg.get("dense", False), bn=cfg.get("bn", False), h=cfg.get("h", 128))

def nparams(m): return sum(p.numel() for p in m.parameters())

# ---------------- train (GPU, mini-batch) ----------------
def train(model, X, y, dev, epochs=15, bs=128, lr=1e-3, seed=0):
    torch.manual_seed(seed)
    model = model.to(dev).train()
    _ = model(X[:2].to(dev))  # init LazyLinear
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    X, y = X.to(dev), y.to(dev); n = len(X)
    for _ in range(epochs):
        perm = torch.randperm(n, device=dev)
        for i in range(0, n, bs):
            idx = perm[i:i+bs]
            opt.zero_grad(set_to_none=True)
            F.cross_entropy(model(X[idx]), y[idx]).backward(); opt.step()
    return model.eval()

@torch.no_grad()
def accuracy(model, X, y, dev, bs=1024):
    c = 0
    for i in range(0, len(X), bs):
        c += (model(X[i:i+bs].to(dev)).argmax(1) == y[i:i+bs].to(dev)).sum().item()
    return c / len(X)

# ---------------- vectorized two-shift consistency (group-roll, no per-sample loop) ----------------
@torch.no_grad()
def shift_consistency(model, X, dev, max_shift=4, bs=1024):
    X = X.to(dev); N = len(X); S = 2*max_shift+1
    def roll_batch(Z):
        sx = torch.randint(-max_shift, max_shift+1, (N,))
        sy = torch.randint(-max_shift, max_shift+1, (N,))
        key = (sx+max_shift)*S + (sy+max_shift)
        out = torch.empty_like(Z)
        for k in key.unique():                    # <= S*S groups, each rolled in one op
            m = key == k
            out[m] = torch.roll(Z[m], shifts=(int(sx[m][0]), int(sy[m][0])), dims=(1, 2))
        return out
    A, B = roll_batch(X), roll_batch(X)
    same = 0
    for i in range(0, N, bs):
        same += (model(A[i:i+bs]).argmax(1) == model(B[i:i+bs]).argmax(1)).sum().item()
    return same / N

# ---------------- batched PGD (clamp [0,1]) ----------------
def pgd(model, X, y, dev, eps, norm="linf", steps=20, bs=512):
    correct = 0
    for i in range(0, len(X), bs):
        xb = X[i:i+bs].to(dev); yb = y[i:i+bs].to(dev)
        delta = (torch.zeros_like(xb).uniform_(-eps, eps) if norm == "linf" else torch.zeros_like(xb)).requires_grad_(True)
        alpha = eps/4
        for _ in range(steps):
            loss = F.cross_entropy(model(torch.clamp(xb+delta, 0, 1)), yb)
            g, = torch.autograd.grad(loss, delta)
            if norm == "linf":
                delta = (delta + alpha*g.sign()).clamp(-eps, eps).detach()
            else:
                gn = g/(g.flatten(1).norm(dim=1).clamp_min(1e-12)[:, None, None])
                delta = (delta + alpha*gn).detach()
                dn = delta.flatten(1).norm(dim=1).clamp_min(1e-12)
                delta = delta*(eps/dn).clamp(max=1.0)[:, None, None]
            delta = (torch.clamp(xb+delta, 0, 1)-xb).detach().requires_grad_(True)
        with torch.no_grad():
            correct += (model(torch.clamp(xb+delta, 0, 1)).argmax(1) == yb).sum().item()
    return correct/len(X)

def robust_radius_l2(model, X, y, dev, grid=None, steps=20, bs=512):
    """Mean per-sample min-flip L2 radius (theory-aligned, dataset-comparable).
    For each sample, the smallest grid eps at which L2-PGD flips it (else max grid)."""
    if grid is None:
        grid = [0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
    X = X.to(dev); y = y.to(dev); N = len(X)
    flip_at = torch.full((N,), float(grid[-1]), device=dev)
    done = torch.zeros(N, dtype=torch.bool, device=dev)
    for eps in grid:
        for i in range(0, N, bs):
            xb = X[i:i+bs]; yb = y[i:i+bs]
            delta = torch.zeros_like(xb, requires_grad=True); alpha = eps/4
            for _ in range(steps):
                loss = F.cross_entropy(model(torch.clamp(xb+delta, 0, 1)), yb)
                g, = torch.autograd.grad(loss, delta)
                gn = g/(g.flatten(1).norm(dim=1).clamp_min(1e-12)[:, None, None])
                delta = (delta + alpha*gn).detach()
                dn = delta.flatten(1).norm(dim=1).clamp_min(1e-12)
                delta = delta*(eps/dn).clamp(max=1.0)[:, None, None]
                delta = (torch.clamp(xb+delta, 0, 1)-xb).detach().requires_grad_(True)
            with torch.no_grad():
                wrong = model(torch.clamp(xb+delta, 0, 1)).argmax(1) != yb
            idx = torch.arange(i, min(i+bs, N), device=dev)
            newly = wrong & ~done[idx]
            flip_at[idx[newly]] = eps; done[idx] = done[idx] | wrong
        if done.all(): break
    return float(flip_at.mean().item())

def eta_over_L(model, X, y, dev, bs=256, nb=4):
    ms, gs = [], []
    for b in range(nb):
        xb = X[b*bs:(b+1)*bs].to(dev).requires_grad_(True)
        if len(xb) == 0: break
        logits = model(xb); yb = y[b*bs:(b+1)*bs].to(dev)
        true = logits.gather(1, yb[:, None]).squeeze(1)
        other = logits.clone().scatter_(1, yb[:, None], -1e9).max(1).values
        margin = true - other
        g, = torch.autograd.grad(margin.sum(), xb)
        ms.append(margin.detach().abs().mean().item()); gs.append(g.flatten(1).norm(dim=1).mean().item())
    return float(np.mean(ms)/(np.mean(gs)+1e-9))

# ---------------- one job (run on assigned GPU) ----------------
def run_job(task):
    gpu, cfg, seed, args = task
    dev = f"cuda:{gpu}" if (gpu is not None and torch.cuda.is_available()) else "cpu"
    if dev.startswith("cuda"): torch.cuda.set_device(gpu)
    Xtr, ytr, Xte, yte = load(args["dataset"], args["n"], args["ntest"], seed=0)
    m = train(build(cfg), Xtr, ytr, dev, epochs=args["epochs"], seed=seed)
    out = dict(name=cfg["name"], seed=seed, params=nparams(m),
               clean=accuracy(m, Xte, yte, dev),
               consist=shift_consistency(m, Xte, dev),
               rr_l2=robust_radius_l2(m, Xte, yte, dev),
               rob_l2=pgd(m, Xte, yte, dev, args["eps2"], "l2"),
               rob_linf=pgd(m, Xte, yte, dev, args["epsinf"], "linf"),
               etaL=eta_over_L(m, Xte, yte, dev))
    return out

CONFIGS = [
    {"kind":"fc","depth":2,"bn":False,"name":"FC_d2"},
    {"kind":"fc","depth":2,"bn":True ,"name":"FC_d2_BN"},
    {"kind":"conv","depth":1,"kernel":5,"pool":"gap","bn":False,"name":"conv_d1_k5_gap"},
    {"kind":"conv","depth":1,"kernel":5,"pool":"gap","bn":True ,"name":"conv_d1_k5_gap_BN"},
    {"kind":"conv","depth":2,"kernel":3,"pool":"max","bn":False,"name":"conv_d2_k3_max"},
    {"kind":"conv","depth":2,"kernel":3,"pool":"avg","bn":False,"name":"conv_d2_k3_avg"},
    {"kind":"conv","depth":2,"kernel":3,"pool":"max","dense":True,"bn":False,"name":"conv_d2_k3_max_dense"},
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="mnist", choices=["mnist", "fashion"])
    ap.add_argument("--n", type=int, default=12000); ap.add_argument("--ntest", type=int, default=3000)
    ap.add_argument("--epochs", type=int, default=15); ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--gpus", type=int, default=99, help="max #GPUs to use (etiquette cap)")
    ap.add_argument("--serial", action="store_true"); ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    configs = CONFIGS
    if args.smoke:
        args.n, args.ntest, args.epochs, args.seeds = 4000, 1000, 6, 1
        configs = [CONFIGS[0], CONFIGS[2]]
    ng = min(args.gpus, torch.cuda.device_count()) if torch.cuda.is_available() else 0
    A = dict(dataset=args.dataset, n=args.n, ntest=args.ntest, epochs=args.epochs,
             eps2=1.5, epsinf=0.2)
    load(args.dataset, 10, 10)  # ensure dataset downloaded once before forking
    tasks = [((i % ng) if ng > 0 else None, cfg, s, A)
             for i, (cfg, s) in enumerate(product(configs, range(args.seeds)))]
    print(f"{args.dataset}: {len(tasks)} jobs over {ng or 'CPU'} GPU(s); n={args.n} epochs={args.epochs} seeds={args.seeds}\n")

    if args.serial or ng <= 1:
        results = [run_job(t) for t in tasks]
    else:
        with mp.get_context("spawn").Pool(ng) as pool:
            results = pool.map(run_job, tasks)

    # aggregate over seeds
    agg = {}
    for r in results:
        agg.setdefault(r["name"], []).append(r)
    hdr = f"{'model':24s} {'params':>7s} {'clean':>6s} {'consist':>7s} {'rr_L2':>6s} {'rob_L2':>7s} {'eta/L':>7s}"
    print(hdr); print("-"*len(hdr))
    rows = []
    for name in [c["name"] for c in configs]:
        rs = agg[name]; g = lambda k: float(np.mean([x[k] for x in rs]))
        print(f"{name:24s} {rs[0]['params']:7d} {g('clean'):6.3f} {g('consist'):7.3f} "
              f"{g('rr_l2'):6.3f} {g('rob_l2'):7.3f} {g('etaL'):7.3f}")
        rows.append((g('consist'), g('rr_l2'), g('etaL'), g('rob_l2')))
    # P1/P6 — PRIMARY target is the robust RADIUS rr_l2 (dataset-comparable; eta/L is a radius lower bound).
    if len(rows) >= 3:
        a = np.array(rows)
        from scipy.stats import pearsonr, spearmanr
        def P(i, j): return float(pearsonr(a[:, i], a[:, j])[0])
        def S(i, j): return float(spearmanr(a[:, i], a[:, j])[0])
        print(f"\nP1/P6 across {len(rows)} configs (PRIMARY: robust RADIUS rr_L2):")
        print(f"  consist vs rr_L2 : Pearson {P(0,1):+.3f}  Spearman {S(0,1):+.3f}")
        print(f"  eta/L   vs rr_L2 : Pearson {P(2,1):+.3f}  Spearman {S(2,1):+.3f}")
        print(f"  (secondary, fixed-eps) consist vs rob_L2 {P(0,3):+.3f} ; eta/L vs rob_L2 {P(2,3):+.3f}")
        print("  theory P6: eta/L should track the robust radius better than shift-consistency")

if __name__ == "__main__":
    main()
