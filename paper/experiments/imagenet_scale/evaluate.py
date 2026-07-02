#!/usr/bin/env python3
"""
Evaluation for the ImageNet-100 S2 check (best val-robust checkpoint per arm), fp32 throughout.

Metrics (ports of experiments/cifar_dissection.py, adapted to 160px / eps=4/255):
  clean       : accuracy on the full 5000-image test split (official ImageNet-100 val)
  consist     : circular-shift consistency, two independent random rolls per image, shifts
                uniform in [-16, 16]^2 (10% of 160px, matching the CIFAR 4/32 ratio), all 5000
  dec_*       : etaL_decomposition -- margin (true logit - max other), ||grad M||_1, ||grad M||_2,
                etaL2 = mean margin / mean L2, etaL1 = mean margin / mean L1 (threat-matched
                surrogate for Linf: dual norm of Linf is L1), per-point rho variants; computed on
                the first ~1000 clean-correct points of the full test set (CIFAR protocol)
  pgd40       : margin-loss PGD-40 Linf 4/255 (alpha=eps/4) on the fixed 1000-image subsample
  aa          : AutoAttack Linf 4/255, version='standard', same 1000 images (RobustBench-style)
  masking chk : aa <= pgd40 (AA is the ground truth; PGD above AA indicates no gradient masking)

The 1000-image subsample is a SEEDED random permutation of the test set shared by all arms
(the parquet val split is class-ordered, so a head-slice would cover only 20 of 100 classes).
"""
import argparse, glob, json, os, time
import torch, torch.nn.functional as F

from models import ImageNet100ResNet18, ARMS
from data import load_data, DATA

RESULTS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "..", "..", "results", "imagenet_scale"))
CKPTS = os.path.join(DATA, "ckpts")
EPS = 4 / 255


@torch.no_grad()
def accuracy(model, X, y, dev, bs=256):
    c = 0
    for i in range(0, len(X), bs):
        xb = X[i:i + bs].to(dev).float().div_(255)
        c += (model(xb).argmax(1) == y[i:i + bs].to(dev)).sum().item()
    return c / len(X)

@torch.no_grad()
def shift_consistency(model, X, dev, max_shift=16, bs=128, seed=0):
    """P[argmax f(roll_a x) == argmax f(roll_b x)] for two independent random circular shifts."""
    g = torch.Generator().manual_seed(seed)
    N = len(X); same = 0
    for i in range(0, N, bs):
        xb = X[i:i + bs].to(dev).float().div_(255)
        preds = []
        for _ in range(2):
            sh = torch.randint(-max_shift, max_shift + 1, (len(xb), 2), generator=g)
            out = torch.empty(len(xb), dtype=torch.long, device=dev)
            key = (sh[:, 0] + max_shift) * (2 * max_shift + 1) + (sh[:, 1] + max_shift)
            for k in key.unique():
                m = key == k
                s0, s1 = int(sh[m][0, 0]), int(sh[m][0, 1])
                out[m.to(dev)] = model(torch.roll(xb[m.to(dev)], (s0, s1), dims=(2, 3))).argmax(1)
            preds.append(out)
        same += (preds[0] == preds[1]).sum().item()
    return same / N

@torch.no_grad()
def correct_mask(model, X, y, dev, bs=256):
    out = []
    for i in range(0, len(X), bs):
        xb = X[i:i + bs].to(dev).float().div_(255)
        out.append((model(xb).argmax(1) == y[i:i + bs].to(dev)).cpu())
    return torch.cat(out)

def etaL_decomposition(model, X, y, dev, n_max=1000, bs=32):
    """Port of cifar_dissection.etaL_decomposition + threat-matched etaL1. Correct points only."""
    cm = correct_mask(model, X, y, dev)
    Xc, yc = X[cm][:n_max], y[cm][:n_max]
    if len(Xc) == 0:
        return dict(margin=float("nan"), L2=float("nan"), L1=float("nan"), etaL2=float("nan"),
                    etaL1=float("nan"), rho2=float("nan"), rho1=float("nan"), n_pts=0)
    ms, g2s, g1s, r2s, r1s = [], [], [], [], []
    for i in range(0, len(Xc), bs):
        xb = Xc[i:i + bs].to(dev).float().div_(255).requires_grad_(True)
        yb = yc[i:i + bs].to(dev)
        logits = model(xb)
        true = logits.gather(1, yb[:, None]).squeeze(1)
        other = logits.clone().scatter_(1, yb[:, None], -1e9).max(1).values
        margin = true - other
        g, = torch.autograd.grad(margin.sum(), xb)
        gf = g.flatten(1)
        m = margin.detach().cpu(); n2 = gf.norm(dim=1).detach().cpu(); n1 = gf.abs().sum(1).detach().cpu()
        ms.append(m); g2s.append(n2); g1s.append(n1)
        r2s.append(m / n2.clamp_min(1e-12)); r1s.append(m / n1.clamp_min(1e-12))
    m = torch.cat(ms); g2 = torch.cat(g2s); g1 = torch.cat(g1s)
    r2 = torch.cat(r2s); r1 = torch.cat(r1s)
    return dict(margin=float(m.mean()), L2=float(g2.mean()), L1=float(g1.mean()),
                etaL2=float(m.mean() / (g2.mean() + 1e-12)),
                etaL1=float(m.mean() / (g1.mean() + 1e-12)),
                rho2=float(r2.mean()), rho1=float(r1.mean()), n_pts=len(m))

def _margin_loss(logits, y):
    true = logits.gather(1, y[:, None]).squeeze(1)
    other = logits.clone().scatter_(1, y[:, None], -1e9).max(1).values
    return other - true

def pgd_acc(model, X, y, dev, eps, steps=40, bs=64):
    correct = 0
    for i in range(0, len(X), bs):
        xb = X[i:i + bs].to(dev).float().div_(255); yb = y[i:i + bs].to(dev)
        delta = torch.zeros_like(xb).uniform_(-eps, eps).requires_grad_(True)
        alpha = eps / 4
        for _ in range(steps):
            loss = _margin_loss(model(torch.clamp(xb + delta, 0, 1)), yb).sum()
            g, = torch.autograd.grad(loss, delta)
            delta = (delta + alpha * g.sign()).clamp(-eps, eps).detach()
            delta = (torch.clamp(xb + delta, 0, 1) - xb).detach().requires_grad_(True)
        with torch.no_grad():
            correct += (model(torch.clamp(xb + delta, 0, 1)).argmax(1) == yb).sum().item()
    return correct / len(X)

def autoattack_acc(model, X, y, dev, eps, n=1000, version="standard", bs=128):
    from autoattack import AutoAttack
    Xa = X[:n].to(dev).float().div_(255); ya = y[:n].to(dev)
    adv = AutoAttack(model, norm="Linf", eps=eps, version=version, device=dev, verbose=True)
    adv.seed = 0
    x_adv = adv.run_standard_evaluation(Xa, ya, bs=bs)
    with torch.no_grad():
        return (model(x_adv).argmax(1) == ya).float().mean().item()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=ARMS)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--ckpt", default=None, help="default: <ckpts>/<arm>_seed<seed>_best.pt")
    ap.add_argument("--n-attack", type=int, default=1000)
    ap.add_argument("--aa-version", default="standard")
    args = ap.parse_args()
    dev = "cuda:0"; torch.backends.cuda.matmul.allow_tf32 = False   # fp32 eval fidelity
    tag = f"{args.arm}_seed{args.seed}"
    ckpt = args.ckpt or os.path.join(CKPTS, f"{tag}_best.pt")
    model = ImageNet100ResNet18(args.arm).to(dev)
    model.load_state_dict(torch.load(ckpt, map_location=dev)); model.eval()

    data = load_data(val_size=1000, seed=0)
    Xte, yte = data["Xte"], data["yte"]
    g = torch.Generator().manual_seed(0)                       # fixed subsample shared across arms
    sub = torch.randperm(len(Xte), generator=g)[:args.n_attack]
    Xs, ys = Xte[sub], yte[sub]

    out = dict(exp="imagenet100_fastat_eval", arm=args.arm, seed=args.seed, ckpt=ckpt,
               eps=EPS, n_attack=len(sub), ts=time.strftime("%Y%m%d_%H%M%S"))
    t0 = time.time()
    out["clean"] = accuracy(model, Xte, yte, dev)
    out["consist"] = shift_consistency(model, Xte, dev, max_shift=16)
    # CIFAR protocol: decomposition on the first ~1000 clean-correct points of the FULL test set
    out.update({("dec_" + k): v for k, v in etaL_decomposition(model, Xte, yte, dev).items()})
    print(f"[{tag}] clean={out['clean']:.4f} consist={out['consist']:.4f} "
          f"etaL1={out['dec_etaL1']:.6f} etaL2={out['dec_etaL2']:.4f} ({time.time()-t0:.0f}s)", flush=True)
    out["pgd40"] = pgd_acc(model, Xs, ys, dev, EPS, steps=40)
    print(f"[{tag}] pgd40={out['pgd40']:.4f} ({time.time()-t0:.0f}s)", flush=True)
    out["aa"] = autoattack_acc(model, Xs, ys, dev, EPS, n=args.n_attack, version=args.aa_version)
    out["masking_ok"] = bool(out["aa"] <= out["pgd40"] + 0.005)
    out["eval_sec"] = round(time.time() - t0, 1)
    print(f"[{tag}] aa={out['aa']:.4f} masking_ok={out['masking_ok']} ({out['eval_sec']}s)", flush=True)

    os.makedirs(RESULTS, exist_ok=True)
    p = os.path.join(RESULTS, f"imagenet100_fastat_{tag}_{out['ts']}.json")
    with open(p, "w") as f: json.dump(out, f, indent=1)
    print(f"saved {p}", flush=True)


if __name__ == "__main__":
    main()
