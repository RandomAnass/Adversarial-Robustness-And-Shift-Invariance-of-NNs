#!/usr/bin/env python3
"""
Capacity-matched CIFAR-10 dissection along the SHIFT-INVARIANCE axis, with AutoAttack and an
eta/L -> (margin eta, Lipschitz L) decomposition. GPU + multi-GPU spawn pool.

Arms (IDENTICAL channel schedule -> identical parameter count by construction; only the
shift-invariance operator differs, so capacity is matched exactly):
  standard : zero-pad convs, MaxPool2d(2) downsampling, GAP head      (aliased, approx invariant)
  blurpool : zero-pad convs, anti-aliased BlurPool(2) downsampling     (Zhang 2019; more consistent)
  circular : circular-pad convs, stride-1 (NO subsample), GAP head     (EXACTLY cyclic-shift invariant)
  aug      : == standard architecture, trained with random circular-shift augmentation
                                                                       (LEARNED, not architectural, invariance)

Per model: clean acc; circular-shift CONSISTENCY (vectorized group-roll, ~1.0 for `circular`);
per-sample min-flip L2 robust RADIUS (rr_L2, dataset-comparable, PRIMARY); eta/L and its
decomposition into mean margin and mean local Lipschitz (L2 and Linf duals); AutoAttack robust
accuracy (L2, Linf) + matched PGD for a gradient-masking check.

Normalization is a fixed layer INSIDE the model, so AutoAttack/PGD perturb the true [0,1] image.

Run:    paper/env/cenv/bin/python paper/experiments/cifar_dissection.py
Smoke:  paper/env/cenv/bin/python paper/experiments/cifar_dissection.py --smoke
"""
import argparse, os, json, time, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
import torch.multiprocessing as mp
from itertools import product
from torchvision import datasets, transforms

ROOT = os.path.join(os.path.dirname(__file__), "..", "data")
RESDIR = os.path.join(os.path.dirname(__file__), "..", "results")
CIFAR_MEAN = (0.4914, 0.4822, 0.4465); CIFAR_STD = (0.2470, 0.2435, 0.2616)

# ---------------- data ([0,1] tensors; normalization is a model layer) ----------------
def load_cifar(n_train, n_test, seed=0):
    tf = transforms.ToTensor()
    tr = datasets.CIFAR10(ROOT, train=True, download=True, transform=tf)
    te = datasets.CIFAR10(ROOT, train=False, download=True, transform=tf)
    Xtr = torch.tensor(tr.data, dtype=torch.float32).permute(0, 3, 1, 2).div(255.0)
    ytr = torch.tensor(tr.targets, dtype=torch.long)
    Xte = torch.tensor(te.data, dtype=torch.float32).permute(0, 3, 1, 2).div(255.0)
    yte = torch.tensor(te.targets, dtype=torch.long)
    g = torch.Generator().manual_seed(seed)
    if n_train < len(Xtr):
        itr = torch.randperm(len(Xtr), generator=g)[:n_train]; Xtr, ytr = Xtr[itr], ytr[itr]
    if n_test < len(Xte):
        ite = torch.randperm(len(Xte), generator=g)[:n_test]; Xte, yte = Xte[ite], yte[ite]
    return Xtr, ytr, Xte, yte

# ---------------- blur (anti-aliasing) pool, Zhang 2019 ----------------
class BlurPool2d(nn.Module):
    def __init__(self, ch, stride=2):
        super().__init__()
        a = torch.tensor([1., 2., 1.]); k = (a[:, None] * a[None, :]); k = k / k.sum()
        self.register_buffer("filt", k[None, None].repeat(ch, 1, 1, 1))
        self.ch = ch; self.stride = stride
    def forward(self, x):
        x = F.pad(x, (1, 1, 1, 1), mode="reflect")
        return F.conv2d(x, self.filt, stride=self.stride, groups=self.ch)

class Normalize(nn.Module):
    def __init__(self, mean, std):
        super().__init__()
        self.register_buffer("m", torch.tensor(mean)[None, :, None, None])
        self.register_buffer("s", torch.tensor(std)[None, :, None, None])
    def forward(self, x): return (x - self.m) / self.s

# ---------------- backbone: identical params across arms ----------------
class CIFARNet(nn.Module):
    """3 stages x 2 conv-BN-ReLU; channels [w,2w,4w]; GAP head. Only padding mode + the
    downsampling operator change across arms, none of which add learnable parameters, so all
    arms have identical parameter counts."""
    def __init__(self, arm="standard", w=32, ncls=10):
        super().__init__()
        self.arm = arm
        self.pad_mode = "circular" if arm == "circular" else "zeros"
        self.norm = Normalize(CIFAR_MEAN, CIFAR_STD)
        chs = [3, w, 2 * w, 4 * w]
        self.stages = nn.ModuleList()
        self.downs = nn.ModuleList()
        for s in range(3):
            blocks = []
            cin = chs[s]
            for _ in range(2):
                blocks += [nn.Conv2d(cin, chs[s + 1], 3, padding=1, padding_mode=self.pad_mode, bias=False),
                           nn.BatchNorm2d(chs[s + 1]), nn.ReLU(inplace=True)]
                cin = chs[s + 1]
            self.stages.append(nn.Sequential(*blocks))
            # downsample after stages 0 and 1 (not the last); `circular` keeps full resolution.
            if s < 2 and arm != "circular":
                self.downs.append(nn.MaxPool2d(2) if arm in ("standard", "aug") else BlurPool2d(chs[s + 1], 2))
            else:
                self.downs.append(nn.Identity())
        self.head = nn.Linear(4 * w, ncls)
    def forward(self, x):
        z = self.norm(x)
        for stage, down in zip(self.stages, self.downs):
            z = down(stage(z))
        z = z.mean(dim=(2, 3))           # global average pool -> shift-invariant readout
        return self.head(z)

ARMS = ["standard", "blurpool", "circular", "aug"]
def build(arm, w): return CIFARNet(arm=arm, w=w)
def nparams(m): return sum(p.numel() for p in m.parameters())

# ---------------- train ----------------
def circular_roll(x, max_shift):
    """Per-SAMPLE random circular shift (grouped roll, no per-sample loop)."""
    N = x.size(0); S = 2 * max_shift + 1
    sx = torch.randint(-max_shift, max_shift + 1, (N,))
    sy = torch.randint(-max_shift, max_shift + 1, (N,))
    key = (sx + max_shift) * S + (sy + max_shift)
    out = torch.empty_like(x)
    for k in key.unique():
        m = key == k
        out[m] = torch.roll(x[m], shifts=(int(sx[m][0]), int(sy[m][0])), dims=(2, 3))
    return out

def train(model, X, y, dev, epochs=40, bs=128, lr=0.1, wd=5e-4, seed=0, aug=False, shift_aug=False):
    torch.manual_seed(seed)
    model = model.to(dev).train()
    opt = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9, weight_decay=wd, nesterov=True)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    X, y = X.to(dev), y.to(dev); n = len(X)
    for ep in range(epochs):
        perm = torch.randperm(n, device=dev)
        for i in range(0, n, bs):
            idx = perm[i:i + bs]
            xb = X[idx]; yb = y[idx]
            if aug:                                   # random horizontal flip (all arms)
                flip = torch.rand(xb.size(0), device=dev) < 0.5
                xb = torch.where(flip[:, None, None, None], xb.flip(-1), xb)
            if shift_aug:                             # circular-shift aug (the `aug` arm only)
                xb = circular_roll(xb, 4)
            opt.zero_grad(set_to_none=True)
            F.cross_entropy(model(xb), yb).backward(); opt.step()
        sched.step()
    return model.eval()

@torch.no_grad()
def accuracy(model, X, y, dev, bs=1024):
    c = 0
    for i in range(0, len(X), bs):
        c += (model(X[i:i + bs].to(dev)).argmax(1) == y[i:i + bs].to(dev)).sum().item()
    return c / len(X)

@torch.no_grad()
def correct_mask(model, X, y, dev, bs=1024):
    out = []
    for i in range(0, len(X), bs):
        out.append((model(X[i:i + bs].to(dev)).argmax(1) == y[i:i + bs].to(dev)).cpu())
    return torch.cat(out)

# ---------------- vectorized circular-shift consistency ----------------
@torch.no_grad()
def shift_consistency(model, X, dev, max_shift=4, bs=512):
    X = X.to(dev); N = len(X); S = 2 * max_shift + 1
    def roll_batch():
        sx = torch.randint(-max_shift, max_shift + 1, (N,))
        sy = torch.randint(-max_shift, max_shift + 1, (N,))
        key = (sx + max_shift) * S + (sy + max_shift)
        out = torch.empty_like(X)
        for k in key.unique():
            m = key == k
            out[m] = torch.roll(X[m], shifts=(int(sx[m][0]), int(sy[m][0])), dims=(2, 3))
        return out
    A, B = roll_batch(), roll_batch()
    same = 0
    for i in range(0, N, bs):
        same += (model(A[i:i + bs]).argmax(1) == model(B[i:i + bs]).argmax(1)).sum().item()
    return same / N

# ---------------- margin (CW) loss: stronger than CE for min-norm / robustness ----------------
def _margin_loss(logits, y):
    true = logits.gather(1, y[:, None]).squeeze(1)
    other = logits.clone().scatter_(1, y[:, None], -1e9).max(1).values
    return other - true                      # >0 <=> misclassified; the adversary maximizes this

# ---------------- batched margin-PGD robust accuracy (clamp [0,1]); masking check ----------------
def pgd_acc(model, X, y, dev, eps, norm="linf", steps=40, bs=256):
    correct = 0
    for i in range(0, len(X), bs):
        xb = X[i:i + bs].to(dev); yb = y[i:i + bs].to(dev)
        delta = (torch.zeros_like(xb).uniform_(-eps, eps) if norm == "linf" else torch.zeros_like(xb)).requires_grad_(True)
        alpha = eps / 4
        for _ in range(steps):
            loss = _margin_loss(model(torch.clamp(xb + delta, 0, 1)), yb).sum()
            g, = torch.autograd.grad(loss, delta)
            if norm == "linf":
                delta = (delta + alpha * g.sign()).clamp(-eps, eps).detach()
            else:
                gn = g / (g.flatten(1).norm(dim=1).clamp_min(1e-12)[:, None, None, None])
                delta = (delta + alpha * gn).detach()
                dn = delta.flatten(1).norm(dim=1).clamp_min(1e-12)
                delta = delta * (eps / dn).clamp(max=1.0)[:, None, None, None]
            delta = (torch.clamp(xb + delta, 0, 1) - xb).detach().requires_grad_(True)
        with torch.no_grad():
            correct += (model(torch.clamp(xb + delta, 0, 1)).argmax(1) == yb).sum().item()
    return correct / len(X)

# ---------------- per-sample min-norm L2 robust radius via DDN (PRIMARY metric) ----------------
# DDN (Rony et al., CVPR 2019): decoupled direction/norm min-L2 attack. Verified to recover the
# analytic linear-model radius to ~0.8% mean (0.06% median) error, vs a fixed-eps-ball PGD grid
# which over-estimates by ~25%. Box-constrained to [0,1], so it returns the true min-||delta||_2
# over valid images. CALL ONLY ON CLEAN-CORRECT POINTS (radius is defined there).
def robust_radius_l2(model, X, y, dev, steps=300, gamma=0.05, eps0=1.0, a0=1.0, bs=256):
    X = X.to(dev); y = y.to(dev); N = len(X)
    best = torch.full((N,), float('inf'), device=dev)
    for i in range(0, N, bs):
        xb = X[i:i + bs]; yb = y[i:i + bs]
        delta = torch.zeros_like(xb)
        eps = torch.full((len(xb),), float(eps0), device=dev)
        bnorm = torch.full((len(xb),), float('inf'), device=dev)
        for k in range(steps):
            alpha = 0.01 + (a0 - 0.01) * (1 + np.cos(np.pi * k / steps)) / 2
            delta.requires_grad_(True)
            xadv = torch.clamp(xb + delta, 0, 1)
            logits = model(xadv)
            g, = torch.autograd.grad(_margin_loss(logits, yb).sum(), delta)
            with torch.no_grad():
                adv = logits.argmax(1) != yb
                nrm = delta.flatten(1).norm(dim=1)
                upd = adv & (nrm < bnorm); bnorm[upd] = nrm[upd]
                eps = torch.where(adv, eps * (1 - gamma), eps * (1 + gamma))
                gn = g / g.flatten(1).norm(dim=1).clamp_min(1e-12)[:, None, None, None]
                delta = delta + alpha * gn
                dn = delta.flatten(1).norm(dim=1).clamp_min(1e-12)
                delta = delta / dn[:, None, None, None] * eps[:, None, None, None]
                delta = torch.clamp(xb + delta, 0, 1) - xb
        best[i:i + len(xb)] = bnorm
    finite = torch.isfinite(best)
    return float(best[finite].mean().item()) if finite.any() else float('nan')

# ---------------- eta/L decomposition (margin and local Lipschitz, on CORRECT points) ----------------
def etaL_decomposition(model, X, y, dev, n_max=1000, bs=128):
    """Returns mean margin, mean ||grad M||_2, mean ||grad M||_1, eta/L (=mean m / mean ||g||_2),
    and rho2 = mean(m/||g||_2). Computed on correctly classified points only (radius is defined there)."""
    cm = correct_mask(model, X, y, dev)
    Xc, yc = X[cm][:n_max], y[cm][:n_max]
    ms, g2s, g1s, rho2s = [], [], [], []
    for i in range(0, len(Xc), bs):
        xb = Xc[i:i + bs].to(dev).requires_grad_(True); yb = yc[i:i + bs].to(dev)
        logits = model(xb)
        true = logits.gather(1, yb[:, None]).squeeze(1)
        other = logits.clone().scatter_(1, yb[:, None], -1e9).max(1).values
        margin = true - other
        g, = torch.autograd.grad(margin.sum(), xb)
        gf = g.flatten(1)
        m = margin.detach(); n2 = gf.norm(dim=1).detach(); n1 = gf.abs().sum(1).detach()
        ms.append(m.cpu()); g2s.append(n2.cpu()); g1s.append(n1.cpu())
        rho2s.append((m / n2.clamp_min(1e-12)).cpu())
    m = torch.cat(ms); g2 = torch.cat(g2s); g1 = torch.cat(g1s); rho2 = torch.cat(rho2s)
    return dict(margin=float(m.mean()), L2=float(g2.mean()), L1=float(g1.mean()),
                etaL=float(m.mean() / (g2.mean() + 1e-12)),
                rho2=float(rho2.mean()), n_pts=len(m))

# ---------------- AutoAttack robust accuracy ----------------
def autoattack_acc(model, X, y, dev, eps, norm="Linf", n=512, version="standard", bs=256):
    from autoattack import AutoAttack
    Xa = X[:n].to(dev); ya = y[:n].to(dev)
    adv = AutoAttack(model, norm=norm, eps=eps, version=version, device=dev, verbose=False)
    adv.seed = 0                                   # fix the (randomized) Square attack for reproducibility
    if version == "custom":                       # fast, deterministic subset (smoke / quick checks)
        adv.attacks_to_run = ["apgd-ce", "apgd-t"]
    x_adv = adv.run_standard_evaluation(Xa, ya, bs=bs)
    with torch.no_grad():
        acc = (model(x_adv).argmax(1) == ya).float().mean().item()
    return acc

# ---------------- one job ----------------
def run_job(task):
    gpu, arm, w, seed, A = task
    dev = f"cuda:{gpu}" if (gpu is not None and torch.cuda.is_available()) else "cpu"
    if dev.startswith("cuda"): torch.cuda.set_device(gpu)
    Xtr, ytr, Xte, yte = load_cifar(A["n"], A["ntest"], seed=0)
    model = build(arm, w)
    model = train(model, Xtr, ytr, dev, epochs=A["epochs"], seed=seed,
                  aug=True, shift_aug=(arm == "aug"))
    out = dict(arm=arm, w=w, seed=seed, params=nparams(model))
    out["clean"] = accuracy(model, Xte, yte, dev)
    out["consist"] = shift_consistency(model, Xte, dev)
    cm = correct_mask(model, Xte, yte, dev)          # radius is defined only on clean-correct points
    Xc, yc = Xte[cm], yte[cm]
    out["rr_l2"] = robust_radius_l2(model, Xc[:A["rad_n"]], yc[:A["rad_n"]], dev)
    out["rr_n"] = int(min(A["rad_n"], len(Xc)))
    out.update({("dec_" + k): v for k, v in etaL_decomposition(model, Xte, yte, dev).items()})
    # strong-attack ground truth + matched PGD masking check (representative seeds only: AA is the
    # trustworthy CHECK + RobustBench-standard number; the radius/decomposition use all seeds)
    if seed < A["aa_seeds"]:
        for (nm, norm, eps) in A["aa_specs"]:
            out["pgd_" + nm] = pgd_acc(model, Xte[:A["aa_n"]], yte[:A["aa_n"]], dev, eps,
                                       "linf" if norm == "Linf" else "l2", steps=A["pgd_steps"])
            out["aa_" + nm] = autoattack_acc(model, Xte, yte, dev, eps, norm,
                                             n=A["aa_n"], version=A["aa_version"])
    return out

def _run_shard(shard, q):                          # one process per GPU; its tasks run sequentially
    for t in shard:
        q.put(run_job(t))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50000); ap.add_argument("--ntest", type=int, default=10000)
    ap.add_argument("--epochs", type=int, default=40); ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--widths", type=int, nargs="+", default=[32, 64])
    ap.add_argument("--arms", nargs="+", default=ARMS)
    ap.add_argument("--rad_n", type=int, default=1000, help="#test pts for the L2 robust radius")
    ap.add_argument("--aa_n", type=int, default=512, help="#test pts for AutoAttack/PGD")
    ap.add_argument("--aa_version", default="standard"); ap.add_argument("--pgd_steps", type=int, default=40)
    ap.add_argument("--aa_seeds", type=int, default=1, help="#seeds (per arm,width) that get AutoAttack")
    ap.add_argument("--gpus", type=int, default=99); ap.add_argument("--serial", action="store_true")
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--tag", default="")
    args = ap.parse_args()
    widths, arms = args.widths, args.arms
    if args.smoke:
        args.n, args.ntest, args.epochs, args.seeds = 4000, 1000, 2, 1
        widths, arms = [16], ARMS
        args.rad_n, args.aa_n, args.aa_version, args.pgd_steps = 200, 128, "custom", 10
    aa_specs = [("Linf_8_255", "Linf", 8 / 255), ("L2_0_5", "L2", 0.5)]   # RobustBench CIFAR standards
    ng = min(args.gpus, torch.cuda.device_count()) if torch.cuda.is_available() else 0
    A = dict(n=args.n, ntest=args.ntest, epochs=args.epochs, rad_n=args.rad_n, aa_n=args.aa_n,
             aa_version=args.aa_version, pgd_steps=args.pgd_steps, aa_specs=aa_specs,
             aa_seeds=args.aa_seeds)
    load_cifar(10, 10)  # download once before forking
    # cost-sort (circular keeps full resolution -> ~16x FLOPs) so round-robin balances the GPUs
    jobs = sorted(product(arms, widths, range(args.seeds)),
                  key=lambda j: (16 if j[0] == "circular" else 1) * j[1] * j[1], reverse=True)
    tasks = [((i % ng) if ng > 0 else None, arm, w, s, A) for i, (arm, w, s) in enumerate(jobs)]
    print(f"CIFAR-10: {len(tasks)} jobs over {ng or 'CPU'} GPU(s); arms={arms} widths={widths} "
          f"epochs={args.epochs} seeds={args.seeds} aa={args.aa_version}\n", flush=True)
    t0 = time.time()
    if args.serial or ng <= 1:
        results = [run_job(t) for t in tasks]
    else:
        ctx = mp.get_context("spawn")
        shards = [[t for t in tasks if t[0] == g] for g in range(ng)]   # one process pinned per GPU
        q = ctx.Queue()
        procs = [ctx.Process(target=_run_shard, args=(shards[g], q)) for g in range(ng)]
        for p in procs: p.start()
        results = [q.get() for _ in range(len(tasks))]
        for p in procs: p.join()
    print(f"\nwall {time.time()-t0:.0f}s")

    # aggregate over seeds (per arm,width)
    agg = {}
    for r in results:
        agg.setdefault((r["arm"], r["w"]), []).append(r)
    def g(rs, k): return float(np.mean([x[k] for x in rs]))
    def gs(rs, k): return float(np.std([x[k] for x in rs]))
    def gv(rs, k):                                  # average only rows that have the key (AA: seed0 only)
        v = [x[k] for x in rs if x.get(k) is not None]
        return float(np.mean(v)) if v else float("nan")

    aa_names = [s[0] for s in aa_specs]
    hdr = (f"{'arm':9s} {'w':>3s} {'params':>8s} {'clean':>6s} {'consist':>7s} {'rr_L2':>6s} "
           f"{'margin':>7s} {'L2':>7s} {'etaL':>6s} " + " ".join(f"{'aa_'+n:>12s}" for n in aa_names))
    print(hdr); print("-" * len(hdr))
    rows = []
    for w in widths:
        for arm in arms:
            rs = agg[(arm, w)]
            line = (f"{arm:9s} {w:3d} {rs[0]['params']:8d} {g(rs,'clean'):6.3f} {g(rs,'consist'):7.3f} "
                    f"{g(rs,'rr_l2'):6.3f} {g(rs,'dec_margin'):7.3f} {g(rs,'dec_L2'):7.3f} {g(rs,'dec_etaL'):6.3f} "
                    + " ".join(f"{gv(rs,'aa_'+n):12.3f}" for n in aa_names))
            print(line)
            rows.append(dict(arm=arm, w=w, consist=g(rs, 'consist'), rr_l2=g(rs, 'rr_l2'),
                             etaL=g(rs, 'dec_etaL'), margin=g(rs, 'dec_margin'), L2=g(rs, 'dec_L2')))

    # correlations across all (arm,width) cells: does eta/L predict the robust radius? consistency?
    if len(rows) >= 3:
        from scipy.stats import pearsonr, spearmanr
        rr = np.array([x['rr_l2'] for x in rows]); el = np.array([x['etaL'] for x in rows])
        cs = np.array([x['consist'] for x in rows])
        print(f"\nAcross {len(rows)} (arm,width) cells [PRIMARY: robust RADIUS rr_L2]:")
        print(f"  eta/L   vs rr_L2 : Pearson {pearsonr(el,rr)[0]:+.3f}  Spearman {spearmanr(el,rr)[0]:+.3f}")
        print(f"  consist vs rr_L2 : Pearson {pearsonr(cs,rr)[0]:+.3f}  Spearman {spearmanr(cs,rr)[0]:+.3f}")

    # within-width margin/Lipschitz decomposition vs the `standard` arm (capacity matched)
    print("\nWithin-width decomposition vs `standard` (Dlog rr = Dlog margin - Dlog L2):")
    for w in widths:
        base = next(x for x in rows if x['arm'] == "standard" and x['w'] == w)
        for x in rows:
            if x['w'] != w or x['arm'] == "standard": continue
            dlm = np.log(x['margin'] / base['margin']) if base['margin'] > 0 and x['margin'] > 0 else float('nan')
            dlL = np.log(x['L2'] / base['L2'])
            dlr = np.log(x['etaL'] / base['etaL']) if base['etaL'] > 0 and x['etaL'] > 0 else float('nan')
            print(f"  w={w} {x['arm']:9s}: Dlog margin {dlm:+.3f}  Dlog L2 {dlL:+.3f}  Dlog(eta/L) {dlr:+.3f}")

    os.makedirs(RESDIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    fn = os.path.join(RESDIR, f"cifar_dissection{('_'+args.tag) if args.tag else ''}_{stamp}.json")
    with open(fn, "w") as f:
        json.dump(dict(args=vars(args), aa_specs=aa_specs, results=results, rows=rows), f, indent=2)
    print(f"\nsaved {fn}")

if __name__ == "__main__":
    main()
