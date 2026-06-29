#!/usr/bin/env python3
"""
PILOT: decompose the adversarial-robustness gain from EDM diffusion-generated training data into a
MARGIN term vs a local-LIPSCHITZ/sensitivity term, using the team's certified-radius tooling.

We train PreActResNet-18 under Linf 8/255 PGD-AT on CIFAR-10, varying the AMOUNT of Wang-2023 EDM
synthetic data mixed into the 50k real images. Per arm we run the SAME decomposition the paper uses
(etaL_decomposition: mean margin, mean local input-gradient norm L1/L2, eta/L), the DDN L2 robust
RADIUS, AutoAttack/PGD robust accuracy at the RobustBench Linf 8/255 threshold (gradient-masking
check AA<=PGD), and circular-shift consistency. The key analysis decomposes WHERE the robustness gain
comes from: d log(radius) ~= d log(margin) - d log(L).

DESIGN (controlled, compute-matched): every arm runs the SAME number of epochs and the SAME number of
gradient steps per epoch (steps_per_epoch = ceil(50000/bs)); optimizer is identical. The ONLY thing
that changes across arms is the size of the synthetic pool each mixed batch is sampled from
(real:synthetic ~= 30:70 per batch when synthetic is present; the 0 arm is pure real). So "more
synthetic data" = more diversity/coverage drawn from at FIXED optimization budget. This isolates the
data-amount mechanism (and differs from literature recipes that also scale the step count with data;
flagged as a limitation). One seed -> a pilot; seed noise is real (flagged in the report).

Recipe matches paper/experiments/cifar_at.py (cifar,linf): eps=8/255, alpha=2/255, PGD-7 inner,
SGD(lr=0.1, mom=0.9, nesterov, wd=5e-4), cosine LR, random horizontal flip. Reuses cifar_dissection /
cifar_at / resnet_scale.models so numbers are comparable and the decomposition is the SAME tool.

Run (Stage 1, calibration): diff_pilot.py --synth 0 1000000 --epochs 40 --tag stage1
Run (Stage 2, full sweep):  diff_pilot.py --synth 0 100000 500000 1000000 --epochs 40 --tag stage2
"""
import argparse, os, sys, json, time, math
import numpy as np, torch, torch.nn.functional as F
import torch.multiprocessing as mp

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.normpath(os.path.join(HERE, "..", "experiments"))
RS = os.path.join(EXP, "resnet_scale")
for p in (EXP, RS):
    if p not in sys.path:
        sys.path.insert(0, p)

import cifar_dissection as CD          # load_cifar, accuracy, correct_mask, shift_consistency,
import cifar_at as CAT                 # pgd_linf (Linf PGD-AT inner attack), pgd_l2
import models as M                     # PreActResNet-18 build / nparams

DATA_NPZ = os.path.join(HERE, "data", "1m.npz")
RESDIR = os.path.join(HERE, "results")
PARTDIR = os.path.join(RESDIR, "partial")

# ---- enable TF32 (perf only; matmul/conv precision unchanged enough not to affect the decomposition)
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True
torch.backends.cudnn.benchmark = True

# cifar / linf PGD-AT recipe (identical to cifar_at.py RECIPE[("cifar","linf")])
EPS, ALPHA, PGD_STEPS = 8 / 255, 2 / 255, 7
LR, MOM, WD = 0.1, 0.9, 5e-4


# ----------------------------------------------------------------------------- synthetic data pool
def load_synth(n_syn, seed=0):
    """Load n_syn EDM synthetic CIFAR-10 images as a uint8 tensor (n,3,32,32) + long labels.
    Subsample is a fixed seeded random subset so smaller arms are random subsets of the 1M pool."""
    z = np.load(DATA_NPZ)
    img, lab = z["image"], z["label"]            # (N,32,32,3) uint8, (N,) int
    N = len(img)
    n_syn = min(n_syn, N)
    rng = np.random.default_rng(seed)
    idx = rng.permutation(N)[:n_syn]
    idx.sort()                                   # sorted gather is faster on the mmap'd array
    xs = torch.from_numpy(np.ascontiguousarray(img[idx])).permute(0, 3, 1, 2).contiguous()  # uint8 (n,3,32,32)
    ys = torch.from_numpy(np.ascontiguousarray(lab[idx])).long()
    return xs, ys


# ----------------------------------------------------------------------------- mixed PGD-AT training
def adv_train_mixed(model, Xr, yr, Xs_u8, ys, dev, epochs, bs, real_frac, seed):
    """Linf PGD-AT. 0 arm (Xs_u8 is None): standard permutation passes over the 50k real images.
    Synthetic arms: each of steps_per_epoch batches is real_frac real + (1-real_frac) synthetic,
    both sampled with replacement from their pools; same step budget as the 0 arm."""
    torch.manual_seed(seed)
    model = model.to(dev).train()
    opt = torch.optim.SGD(model.parameters(), lr=LR, momentum=MOM, weight_decay=WD, nesterov=True)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    n_real = len(Xr)
    steps_per_epoch = math.ceil(n_real / bs)     # identical optimization budget across all arms
    nb_real = bs if Xs_u8 is None else int(round(real_frac * bs))
    nb_syn = 0 if Xs_u8 is None else bs - nb_real
    for ep in range(epochs):
        if Xs_u8 is None:
            perm = torch.randperm(n_real, device=dev)
        for it in range(steps_per_epoch):
            if Xs_u8 is None:                                  # pure real, permutation pass
                idx = perm[it * bs:(it + 1) * bs]
                xb, yb = Xr[idx], yr[idx]
            else:                                              # mixed real:synthetic batch
                ir = torch.randint(0, n_real, (nb_real,), device=dev)
                isy = torch.randint(0, len(Xs_u8), (nb_syn,), device=dev)
                xb = torch.cat([Xr[ir], Xs_u8[isy].float().div_(255.0)], 0)
                yb = torch.cat([yr[ir], ys[isy]], 0)
            flip = torch.rand(xb.size(0), device=dev) < 0.5    # random horizontal flip (matches recipe)
            xb = torch.where(flip[:, None, None, None], xb.flip(-1), xb)
            x_adv = CAT.pgd_linf(model, xb, yb, EPS, ALPHA, PGD_STEPS)   # inner max (reused infra)
            opt.zero_grad(set_to_none=True)
            F.cross_entropy(model(x_adv), yb).backward(); opt.step()     # outer min
        sched.step()
    return model.eval()


# ----------------------------------------------------------------------------- one arm (train+eval)
def run_arm(task):
    gpu, n_syn, A = task
    dev = f"cuda:{gpu}" if (gpu is not None and torch.cuda.is_available()) else "cpu"
    if dev.startswith("cuda"):
        torch.cuda.set_device(gpu)
    t0 = time.time()
    # real CIFAR-10 (same loader / split as the paper); [0,1] tensors, normalization is a model layer
    Xtr, ytr, Xte, yte = CD.load_cifar(A["n"], A["ntest"], seed=0)
    Xr, yr = Xtr.to(dev), ytr.to(dev)
    Xs_u8, ys = (None, None)
    if n_syn > 0:
        xs, ls = load_synth(n_syn, seed=A["synth_seed"])
        Xs_u8, ys = xs.to(dev), ls.to(dev)
    model = M.build("stdzero", width=1.0).to(dev)       # canonical zero-pad stride-2 PreActResNet-18
    model = adv_train_mixed(model, Xr, yr, Xs_u8, ys, dev, A["epochs"], A["bs"], A["real_frac"], A["seed"])
    del Xs_u8, ys
    if dev.startswith("cuda"):
        torch.cuda.empty_cache()

    out = dict(n_syn=int(n_syn), seed=A["seed"], epochs=A["epochs"], bs=A["bs"],
               real_frac=A["real_frac"], params=M.nparams(model))
    out["clean"] = CD.accuracy(model, Xte, yte, dev)
    out["consist"] = CD.shift_consistency(model, Xte, dev)
    cm = CD.correct_mask(model, Xte, yte, dev)          # radius / decomposition: clean-correct pts only
    Xc, yc = Xte[cm], yte[cm]
    out["rr_l2"] = CD.robust_radius_l2(model, Xc[:A["rad_n"]], yc[:A["rad_n"]], dev)
    out["rr_n"] = int(min(A["rad_n"], len(Xc)))
    out.update({("dec_" + k): v for k, v in CD.etaL_decomposition(model, Xte, yte, dev).items()})
    # threat-matched Linf 8/255: PGD (masking check) then AutoAttack (ground truth; AA<=PGD)
    out["pgd_Linf_8_255"] = CD.pgd_acc(model, Xte[:A["aa_n"]], yte[:A["aa_n"]], dev, EPS, "linf", steps=A["pgd_steps"])
    out["aa_Linf_8_255"] = CD.autoattack_acc(model, Xte, yte, dev, EPS, "Linf", n=A["aa_n"], version=A["aa_version"])
    out["wall_s"] = round(time.time() - t0, 1)

    os.makedirs(PARTDIR, exist_ok=True)
    p = os.path.join(PARTDIR, f"{A['tag']}_syn{n_syn}_s{A['seed']}_e{A['epochs']}.json")
    json.dump(out, open(p + ".tmp", "w"), default=float); os.replace(p + ".tmp", p)
    print(f"[done] +{n_syn:>8d} syn | clean {out['clean']:.3f} PGD {out['pgd_Linf_8_255']:.3f} "
          f"AA {out['aa_Linf_8_255']:.3f} | rr_L2 {out['rr_l2']:.3f} margin {out['dec_margin']:.3f} "
          f"L1 {out['dec_L1']:.2f} L2 {out['dec_L2']:.3f} | {out['wall_s']:.0f}s", flush=True)
    return out


def _run_shard(shard, q):
    for t in shard:
        q.put(run_arm(t))


# ----------------------------------------------------------------------------- decomposition report
def decompose(rows):
    """d log(radius) ~= d log(margin) - d log(L), each arm vs the 0 (real-only) baseline."""
    base = next(r for r in rows if r["n_syn"] == 0)
    lines = []
    for r in sorted(rows, key=lambda x: x["n_syn"]):
        if r["n_syn"] == 0:
            continue
        dlm = math.log(r["dec_margin"] / base["dec_margin"])
        dl1 = math.log(r["dec_L1"] / base["dec_L1"])
        dl2 = math.log(r["dec_L2"] / base["dec_L2"])
        d_etaL2 = dlm - dl2                                 # predicted d log(L2 radius); L2-dual L = L2
        d_etaL1 = dlm - dl1                                 # threat-matched to AA-Linf; Linf-dual L = L1
        d_rr = math.log(r["rr_l2"] / base["rr_l2"]) if base["rr_l2"] > 0 and r["rr_l2"] > 0 else float("nan")
        d_aa = r["aa_Linf_8_255"] - base["aa_Linf_8_255"]
        # additive split of each d log(eta/L) into numerator (margin) and denominator (-L) shares
        share_margin_L2 = (dlm / d_etaL2) if abs(d_etaL2) > 1e-9 else float("nan")
        share_margin_L1 = (dlm / d_etaL1) if abs(d_etaL1) > 1e-9 else float("nan")
        lines.append(dict(n_syn=r["n_syn"], dlog_margin=dlm, dlog_L1=dl1, dlog_L2=dl2,
                          dlog_etaL2=d_etaL2, dlog_etaL1=d_etaL1, dlog_rr_l2=d_rr, dAA=d_aa,
                          margin_share_of_etaL2=share_margin_L2, margin_share_of_etaL1=share_margin_L1))
    return base, lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--synth", type=int, nargs="+", default=[0, 1000000], help="synthetic-pool sizes (arms)")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--bs", type=int, default=512)
    ap.add_argument("--real_frac", type=float, default=0.3, help="real fraction per mixed batch (synth arms)")
    ap.add_argument("--n", type=int, default=50000); ap.add_argument("--ntest", type=int, default=10000)
    ap.add_argument("--rad_n", type=int, default=1000); ap.add_argument("--aa_n", type=int, default=512)
    ap.add_argument("--aa_version", default="standard"); ap.add_argument("--pgd_steps", type=int, default=40)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--synth_seed", type=int, default=0)
    ap.add_argument("--gpus", type=int, default=99); ap.add_argument("--serial", action="store_true")
    ap.add_argument("--tag", default="stage")
    args = ap.parse_args()

    A = dict(n=args.n, ntest=args.ntest, epochs=args.epochs, bs=args.bs, real_frac=args.real_frac,
             rad_n=args.rad_n, aa_n=args.aa_n, aa_version=args.aa_version, pgd_steps=args.pgd_steps,
             seed=args.seed, synth_seed=args.synth_seed, tag=args.tag)
    ng = min(args.gpus, torch.cuda.device_count()) if torch.cuda.is_available() else 0
    CD.load_cifar(10, 10)                                  # trigger the torchvision download once

    # resume from disk (progressive per-arm save), then run the rest
    arms = sorted(set(args.synth))
    done, pending = [], []
    for ns in arms:
        p = os.path.join(PARTDIR, f"{args.tag}_syn{ns}_s{args.seed}_e{args.epochs}.json")
        if os.path.exists(p):
            try: done.append(json.load(open(p))); continue
            except Exception: pass
        pending.append(ns)
    tasks = [((i % ng) if ng > 0 else None, ns, A) for i, ns in enumerate(pending)]
    print(f"PILOT diffusion-AT: arms(synth)={arms} epochs={args.epochs} bs={args.bs} real_frac={args.real_frac} "
          f"| {len(done)} resumed, {len(tasks)} to run over {ng or 'CPU'} GPU(s)\n", flush=True)

    t0 = time.time()
    computed = []
    if tasks:
        if args.serial or ng <= 1:
            computed = [run_arm(t) for t in tasks]
        else:
            ctx = mp.get_context("spawn")
            shards = [[t for t in tasks if t[0] == g] for g in range(ng)]
            q = ctx.Queue()
            procs = [ctx.Process(target=_run_shard, args=(shards[g], q)) for g in range(ng) if shards[g]]
            for pr in procs: pr.start()
            computed = [q.get() for _ in range(len(tasks))]
            for pr in procs: pr.join()
    rows = done + computed
    print(f"\nwall {time.time()-t0:.0f}s\n", flush=True)

    # ----- results table
    rows = sorted(rows, key=lambda r: r["n_syn"])
    hdr = (f"{'+synth':>9s} {'clean':>6s} {'PGD':>6s} {'AA':>6s} {'rr_L2':>6s} {'margin':>7s} "
           f"{'L1':>7s} {'L2':>7s} {'eta/L':>6s} {'consist':>7s}")
    print(hdr); print("-" * len(hdr))
    for r in rows:
        print(f"{r['n_syn']:>9d} {r['clean']:6.3f} {r['pgd_Linf_8_255']:6.3f} {r['aa_Linf_8_255']:6.3f} "
              f"{r['rr_l2']:6.3f} {r['dec_margin']:7.3f} {r['dec_L1']:7.2f} {r['dec_L2']:7.3f} "
              f"{r['dec_etaL']:6.3f} {r['consist']:7.3f}")

    # ----- gradient-masking check
    print("\nGradient-masking check (must hold: AA <= PGD):")
    for r in rows:
        ok = "OK" if r["aa_Linf_8_255"] <= r["pgd_Linf_8_255"] + 1e-9 else "VIOLATED"
        print(f"  +{r['n_syn']:>8d}: AA {r['aa_Linf_8_255']:.3f} <= PGD {r['pgd_Linf_8_255']:.3f}  [{ok}]")

    # ----- decomposition verdict
    if any(r["n_syn"] == 0 for r in rows) and any(r["n_syn"] > 0 for r in rows):
        base, lines = decompose(rows)
        print("\nDecomposition vs 0 (real-only) baseline  [d log r ~= d log margin - d log L]:")
        print(f"  base(+0): margin {base['dec_margin']:.3f} L1 {base['dec_L1']:.2f} L2 {base['dec_L2']:.3f} "
              f"rr_L2 {base['rr_l2']:.3f} AA {base['aa_Linf_8_255']:.3f}")
        for l in lines:
            ms = l['dlog_margin'] / l['dlog_etaL2'] if abs(l.get('dlog_etaL2', 0.0)) > 1e-9 else float('nan')
            print(f"  +{l['n_syn']:>8d}: dlog margin {l['dlog_margin']:+.3f}  dlog L1 {l['dlog_L1']:+.3f}  "
                  f"dlog L2 {l['dlog_L2']:+.3f}  dlog(eta/L2) {l['dlog_etaL2']:+.3f}  "
                  f"dlog rr_L2 {l['dlog_rr_l2']:+.3f}  dAA {l['dAA']:+.3f}  "
                  f"(margin share of d log(eta/L2) = {ms:+.2f})")
    else:
        lines = []

    os.makedirs(RESDIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    fn = os.path.join(RESDIR, f"diff_pilot_{args.tag}_{stamp}.json")
    recipe = dict(arch="PreActResNet-18 (stdzero: zero-pad stride-2, canonical)", eps=EPS, alpha=ALPHA,
                  pgd_steps=PGD_STEPS, lr=LR, mom=MOM, wd=WD, sched="cosine", aug="hflip",
                  real_frac=args.real_frac, bs=args.bs, epochs=args.epochs, note="compute-matched: same "
                  "steps_per_epoch=ceil(50000/bs) across arms; arms differ only in synthetic-pool size")
    json.dump(dict(args=vars(args), recipe=recipe, rows=rows, decomposition=lines), open(fn, "w"), indent=2, default=float)
    print(f"\nsaved {fn}")


if __name__ == "__main__":
    main()
