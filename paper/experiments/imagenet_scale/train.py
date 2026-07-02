#!/usr/bin/env python3
"""
Fast adversarial training (Wong et al. 2020, FGSM-RS) for the ImageNet-100 arms at 160px.

Recipe: Linf eps=4/255 (ImageNet RobustBench standard), single-step FGSM with uniform random init,
alpha=1.25*eps, cyclic (triangular) LR peaking mid-run (np.interp [0, T/2, T] -> [0, lr_max, 0], as
in locuslab/fast_adversarial), SGD 0.9 / wd 5e-4, batch 256, 15 epochs, bf16 autocast fwd/bwd,
channels_last. House conventions kept from experiments/resnet_scale/resnet_train.py: attack crafted
in eval mode (frozen BN), update in train mode; normalization folded into the model so the attack
operates in [0,1]; augmentation = RandomCrop(160, zero-pad 8) + hflip (GPU-side), the `aug` arm
additionally gets random circular shifts +-16px BEFORE the crop (CIFAR _AugDS order, scaled 4/32 ->
16/160); early selection = best val-robust (PGD-10) checkpoint, final checkpoint also saved.

Catastrophic-overfitting guard: per-epoch PGD-10 robust acc on the 1000-image val holdout; a run is
declared collapsed if val-robust falls > 20 points below its best AND under 5%. On collapse the arm
restarts from scratch: attempt 1 -> alpha=1.0*eps, attempt 2 -> alpha=1.0*eps + linear eps-warmup
over 5 epochs. Attempts are recorded in the output JSON.
"""
import argparse, json, math, os, subprocess, time
import numpy as np, torch, torch.nn.functional as F

from models import ImageNet100ResNet18, ARMS
from data import load_data, DATA

RESULTS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "..", "..", "results", "imagenet_scale"))
CKPTS = os.path.join(DATA, "ckpts")


def set_seed(seed):
    np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True

def env_stamp():
    try: sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception: sha = "unknown"
    return {"git_sha": sha, "torch": torch.__version__, "cuda": torch.version.cuda,
            "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"}

# ---------------- GPU-side augmentation on [0,1] float batches ----------------
def _gather2d(x, rows, cols):
    """out[b,c,i,j] = x[b,c,rows[b,i],cols[b,j]] via two take_along_dim gathers."""
    B, C, H, W = x.shape
    x = torch.take_along_dim(x, rows[:, None, :, None].expand(B, C, rows.shape[1], W), dim=2)
    return torch.take_along_dim(x, cols[:, None, None, :].expand(B, C, rows.shape[1], cols.shape[1]), dim=3)

def augment(x, pad=8, roll=0):
    """Optional per-image circular shift (+-roll) THEN RandomCrop(zero-pad `pad`) + hflip."""
    B, C, H, W = x.shape; dev = x.device
    if roll:
        sy = torch.randint(-roll, roll + 1, (B, 1), device=dev)
        sx = torch.randint(-roll, roll + 1, (B, 1), device=dev)
        x = _gather2d(x, (torch.arange(H, device=dev)[None] + sy) % H,
                         (torch.arange(W, device=dev)[None] + sx) % W)
    xp = F.pad(x, (pad,) * 4)                                  # zero pad, as CIFAR RandomCrop
    iy = torch.randint(0, 2 * pad + 1, (B, 1), device=dev)
    ix = torch.randint(0, 2 * pad + 1, (B, 1), device=dev)
    x = _gather2d(xp, torch.arange(H, device=dev)[None] + iy, torch.arange(W, device=dev)[None] + ix)
    flip = torch.rand(B, device=dev) < 0.5
    x[flip] = x[flip].flip(-1)
    return x

def batches(X, y, bs, seed, dev, epoch):
    g = torch.Generator().manual_seed(seed * 10000 + epoch)
    perm = torch.randperm(len(X), generator=g)
    for i in range(0, len(X), bs):
        idx = perm[i:i + bs]
        xb = X[idx].to(dev, non_blocking=True).float().div_(255)
        yield xb.contiguous(memory_format=torch.channels_last), y[idx].to(dev, non_blocking=True)

# ---------------- attacks (eval-mode crafting, bf16; [0,1] box) ----------------
def fgsm_rs(model, x, y, eps, alpha):
    model.eval()
    delta = torch.empty_like(x).uniform_(-eps, eps)
    delta = (torch.clamp(x + delta, 0, 1) - x).requires_grad_(True)
    with torch.autocast("cuda", dtype=torch.bfloat16):
        loss = F.cross_entropy(model(x + delta), y)
    g, = torch.autograd.grad(loss, delta)
    delta = (delta + alpha * g.sign()).clamp(-eps, eps).detach()
    return torch.clamp(x + delta, 0, 1).detach()

def pgd_linf(model, x, y, eps, alpha, steps):
    model.eval()
    delta = torch.empty_like(x).uniform_(-eps, eps)
    delta = (torch.clamp(x + delta, 0, 1) - x).detach()
    for _ in range(steps):
        delta.requires_grad_(True)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            loss = F.cross_entropy(model(torch.clamp(x + delta, 0, 1)), y)
        g, = torch.autograd.grad(loss, delta)
        delta = (delta + alpha * g.sign()).clamp(-eps, eps).detach()
        delta = (torch.clamp(x + delta, 0, 1) - x).detach()
    return torch.clamp(x + delta, 0, 1).detach()

@torch.no_grad()
def acc(model, X, y, dev, bs=256):
    model.eval(); c = 0
    for i in range(0, len(X), bs):
        xb = X[i:i + bs].to(dev).float().div_(255)
        c += (model(xb).argmax(1) == y[i:i + bs].to(dev)).sum().item()
    return c / len(X)

def robust_acc(model, X, y, dev, eps, alpha, steps, bs=256):
    model.eval(); c = 0
    for i in range(0, len(X), bs):
        xb = X[i:i + bs].to(dev).float().div_(255); yb = y[i:i + bs].to(dev)
        xa = pgd_linf(model, xb, yb, eps, alpha, steps)
        with torch.no_grad(): c += (model(xa).argmax(1) == yb).sum().item()
    return c / len(X)

# ---------------- one training attempt ----------------
def train_attempt(arm, data, dev, seed, epochs, bs, lr_max, wd, eps, alpha, warmup_epochs, log):
    set_seed(seed)
    model = ImageNet100ResNet18(arm).to(dev).to(memory_format=torch.channels_last)
    opt = torch.optim.SGD(model.parameters(), lr=lr_max, momentum=0.9, weight_decay=wd)
    n_iters = math.ceil(len(data["Xtr"]) / bs); total = epochs * n_iters
    curves, best, best_state, best_epoch, collapsed = [], -1.0, None, -1, False
    step = 0
    for ep in range(epochs):
        ep_eps = eps * min(1.0, (ep + 1) / warmup_epochs) if warmup_epochs else eps
        ep_alpha = alpha * (ep_eps / eps)
        t0 = time.time(); tl = 0.0; nseen = 0
        for xb, yb in batches(data["Xtr"], data["ytr"], bs, seed, dev, ep):
            lr = float(np.interp(step, [0, total / 2, total], [0, lr_max, 0]))
            for gp in opt.param_groups: gp["lr"] = lr
            xb = augment(xb, pad=8, roll=(16 if arm == "aug" else 0))
            xa = fgsm_rs(model, xb, yb, ep_eps, ep_alpha)
            model.train(); opt.zero_grad(set_to_none=True)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                loss = F.cross_entropy(model(xa), yb)
            loss.backward(); opt.step()
            tl += loss.item() * len(yb); nseen += len(yb); step += 1
        vca = acc(model, data["Xval"], data["yval"], dev)
        vra = robust_acc(model, data["Xval"], data["yval"], dev, eps, eps / 4, 10)
        rec = {"epoch": ep, "eps": ep_eps, "lr_last": lr, "train_loss": tl / nseen,
               "val_clean": vca, "val_robust": vra, "sec": round(time.time() - t0, 1)}
        curves.append(rec); log(f"  {json.dumps(rec)}")
        if vra > best + 1e-4:
            best, best_epoch = vra, ep
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        if best - vra > 0.20 and vra < 0.05:                    # catastrophic overfitting
            collapsed = True; log(f"  COLLAPSE detected at epoch {ep} (best {best:.3f} -> {vra:.3f})")
            break
    final_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    return dict(curves=curves, best_val_robust=best, best_epoch=best_epoch,
                collapsed=collapsed), best_state, final_state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=ARMS)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--bs", type=int, default=256)
    ap.add_argument("--lr-max", type=float, default=0.2)
    ap.add_argument("--wd", type=float, default=5e-4)
    ap.add_argument("--eps", type=float, default=4 / 255)
    args = ap.parse_args()
    os.makedirs(RESULTS, exist_ok=True); os.makedirs(CKPTS, exist_ok=True)
    dev = "cuda:0"
    ts = time.strftime("%Y%m%d_%H%M%S")
    tag = f"{args.arm}_seed{args.seed}"
    logf = open(os.path.join(RESULTS, f"train_{tag}.log"), "a")
    def log(s): print(s, flush=True); logf.write(s + "\n"); logf.flush()

    data = load_data(val_size=1000, seed=0)
    log(f"[{ts}] train {tag}: {len(data['Xtr'])} train / {len(data['Xval'])} val, eps={args.eps:.5f}")
    attempts_cfg = [dict(alpha=1.25 * args.eps, warmup_epochs=0),
                    dict(alpha=1.00 * args.eps, warmup_epochs=0),
                    dict(alpha=1.00 * args.eps, warmup_epochs=5)]
    attempts = []
    for k, cfg in enumerate(attempts_cfg):
        log(f"attempt {k}: alpha={cfg['alpha']:.5f} warmup={cfg['warmup_epochs']}")
        res, best_state, final_state = train_attempt(
            args.arm, data, dev, seed=args.seed + 1000 * k, epochs=args.epochs, bs=args.bs,
            lr_max=args.lr_max, wd=args.wd, eps=args.eps, log=log, **cfg)
        attempts.append({**cfg, **res})
        if not res["collapsed"]:
            break
    torch.save(best_state, os.path.join(CKPTS, f"{tag}_best.pt"))
    torch.save(final_state, os.path.join(CKPTS, f"{tag}_final.pt"))
    out = dict(exp="imagenet100_fastat_train", arm=args.arm, seed=args.seed, ts=ts,
               config=dict(epochs=args.epochs, bs=args.bs, lr_max=args.lr_max, wd=args.wd,
                           eps=args.eps, recipe="FGSM-RS (Wong2020), cyclic LR, eval-mode attack",
                           img=160, aug="crop(pad8)+hflip" + ("+roll16" if args.arm == "aug" else "")),
               attempts=attempts, n_restarts=len(attempts) - 1,
               best_val_robust=attempts[-1]["best_val_robust"], best_epoch=attempts[-1]["best_epoch"],
               ckpt_best=os.path.join(CKPTS, f"{tag}_best.pt"),
               ckpt_final=os.path.join(CKPTS, f"{tag}_final.pt"), env=env_stamp())
    p = os.path.join(RESULTS, f"train_{tag}_{ts}.json")
    with open(p, "w") as f: json.dump(out, f, indent=1)
    log(f"saved {p}")


if __name__ == "__main__":
    main()
