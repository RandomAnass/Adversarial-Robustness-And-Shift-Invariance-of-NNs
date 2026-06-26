#!/usr/bin/env python3
"""
Data + training (standard and PGD-AT) for the ResNet-scale dissection.
Recipe: Rice/Wong/Kolter 2020 (PreActResNet-18, SGD 0.9 / wd 5e-4, batch 128, LR 0.1 ->/10 @100/150,
PGD Linf eps=8/255 10-step alpha=2/255 random start in [0,1], RandomCrop(pad4)+hflip per image,
normalization folded into the model). Robust-overfitting fix: hold out 1000 train images, select the
best-robust-val checkpoint, early-TERMINATE once val-robust has not improved for `patience` epochs.
Per-image augmentation via a seeded DataLoader; full per-epoch curves + checkpoints + seeds + indices
are saved (reproducibility, no data hoarding).
"""
import os, subprocess, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
import torchvision as tv, torchvision.transforms as T
from torch.utils.data import Dataset, DataLoader

# ---------------- reproducibility ----------------
def set_seed(seed):
    np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = True            # speed (fixed input sizes); reruns are statistically,
    torch.backends.cuda.matmul.allow_tf32 = True     # not bit-, reproducible -> exact models saved as ckpts

def env_stamp():
    try: sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception: sha = "unknown"
    return {"git_sha": sha, "torch": torch.__version__, "cuda": torch.version.cuda,
            "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"}

# ---------------- data: CIFAR-10/100 in [0,1], seeded 1000-image val holdout ----------------
_DATA = os.path.join(os.path.dirname(__file__), "..", "..", "data")
def load_data(dataset="cifar10", seed=0, val_size=1000):
    ds = {"cifar10": tv.datasets.CIFAR10, "cifar100": tv.datasets.CIFAR100}[dataset]
    tr = ds(_DATA, train=True, download=True); te = ds(_DATA, train=False, download=True)
    Xtr = torch.tensor(tr.data, dtype=torch.float32).permute(0, 3, 1, 2) / 255.0
    ytr = torch.tensor(tr.targets, dtype=torch.long)
    Xte = torch.tensor(te.data, dtype=torch.float32).permute(0, 3, 1, 2) / 255.0
    yte = torch.tensor(te.targets, dtype=torch.long)
    g = torch.Generator().manual_seed(seed); perm = torch.randperm(len(Xtr), generator=g)
    val_idx, tr_idx = perm[:val_size], perm[val_size:]
    return {"Xtr": Xtr[tr_idx], "ytr": ytr[tr_idx], "Xval": Xtr[val_idx], "yval": ytr[val_idx],
            "Xte": Xte, "yte": yte, "tr_idx": tr_idx.tolist(), "val_idx": val_idx.tolist(),
            "n_classes": 100 if dataset == "cifar100" else 10}

class _AugDS(Dataset):
    """Per-image augmentation on [0,1] CHW tensors: optional circular shift (the `aug` arm) then
    RandomCrop(32, pad 4, zero-pad) + RandomHorizontalFlip. No normalization (folded into the model)."""
    def __init__(self, X, y, shift_aug=False):
        self.X, self.y, self.shift_aug = X, y, shift_aug
        self.tf = T.Compose([T.RandomCrop(32, padding=4), T.RandomHorizontalFlip()])
    def __len__(self): return len(self.X)
    def __getitem__(self, i):
        x = self.X[i]
        if self.shift_aug:
            sx, sy = int(torch.randint(-4, 5, (1,))), int(torch.randint(-4, 5, (1,)))
            x = torch.roll(x, shifts=(sx, sy), dims=(1, 2))
        return self.tf(x), self.y[i]

def _loader(X, y, bs, seed, shift_aug):
    g = torch.Generator().manual_seed(seed)
    return DataLoader(_AugDS(X, y, shift_aug), batch_size=bs, shuffle=True, num_workers=4,
                      pin_memory=True, drop_last=False, generator=g,
                      worker_init_fn=lambda wid: np.random.seed(seed * 1000 + wid))

# ---------------- PGD attack in [0,1] (Linf) ----------------
def pgd_linf(model, x, y, eps, alpha, steps, random_start=True):
    delta = torch.zeros_like(x)
    if random_start:
        delta.uniform_(-eps, eps); delta = torch.clamp(x + delta, 0, 1) - x
    for _ in range(steps):
        delta.requires_grad_(True)
        loss = F.cross_entropy(model(torch.clamp(x + delta, 0, 1)), y)
        g, = torch.autograd.grad(loss, delta)
        delta = (delta + alpha * g.sign()).clamp(-eps, eps).detach()
        delta = (torch.clamp(x + delta, 0, 1) - x).detach()
    return torch.clamp(x + delta, 0, 1).detach()

@torch.no_grad()
def _acc(model, X, y, dev, bs=512):
    model.eval(); c = 0
    for i in range(0, len(X), bs):
        c += (model(X[i:i + bs].to(dev)).argmax(1) == y[i:i + bs].to(dev)).sum().item()
    return c / len(X)

def _robust_acc(model, X, y, dev, eps, alpha, steps, bs=256):
    model.eval(); c = 0
    for i in range(0, len(X), bs):
        xb, yb = X[i:i + bs].to(dev), y[i:i + bs].to(dev)
        xa = pgd_linf(model, xb, yb, eps, alpha, steps)
        with torch.no_grad(): c += (model(xa).argmax(1) == yb).sum().item()
    return c / len(X)

# ---------------- train one cell ----------------
def train_cell(model, data, dev, mode="at", arm="standard", seed=0,
               epochs=200, bs=128, lr=0.1, momentum=0.9, wd=5e-4,
               milestones=(100, 150), eps=8/255, alpha=2/255, pgd_steps=10,
               val_steps=10, patience=12, min_epochs=None, ckpt_path=None, log_cb=None):
    """Train standard (mode='std') or PGD-AT (mode='at'). Returns (best_state, curves, best_epoch).
    Attack is crafted in eval mode (frozen BN, reproducible); the SGD update is in train mode.
    Early stopping on val-robust (AT) / val-clean (std); terminate after `patience` no-improve epochs,
    not before `min_epochs` (default first milestone + patience)."""
    set_seed(seed); model = model.to(dev)
    opt = torch.optim.SGD(model.parameters(), lr=lr, momentum=momentum, weight_decay=wd)
    sched = torch.optim.lr_scheduler.MultiStepLR(opt, milestones=list(milestones), gamma=0.1)
    loader = _loader(data["Xtr"], data["ytr"], bs, seed, shift_aug=(arm == "aug"))
    Xval, yval = data["Xval"], data["yval"]
    curves = []; best_metric = -1.0; best_state = None; best_epoch = -1; bad = 0
    if min_epochs is None: min_epochs = milestones[0] + patience
    for ep in range(epochs):
        nseen = 0; tl = 0.0
        for xb, yb in loader:
            xb, yb = xb.to(dev, non_blocking=True), yb.to(dev, non_blocking=True)
            if mode == "at":
                model.eval()
                with torch.autocast("cuda", dtype=torch.bfloat16):       # bf16 attack (no GradScaler needed)
                    xb = pgd_linf(model, xb, yb, eps, alpha, pgd_steps)
            model.train(); opt.zero_grad()
            with torch.autocast("cuda", dtype=torch.bfloat16):           # bf16 fwd; BN stays fp32 under autocast
                loss = F.cross_entropy(model(xb), yb)
            loss.backward(); opt.step()
            tl += loss.item() * len(yb); nseen += len(yb)
        sched.step()
        vca = _acc(model, Xval, yval, dev)
        vra = _robust_acc(model, Xval, yval, dev, eps, alpha, val_steps) if mode == "at" else float("nan")
        metric = vra if mode == "at" else vca
        rec = {"epoch": ep, "lr": opt.param_groups[0]["lr"], "train_loss": tl / nseen,
               "val_clean": vca, "val_robust": vra}
        curves.append(rec)
        if log_cb: log_cb(rec)
        if metric > best_metric + 1e-4:
            best_metric, best_epoch, bad = metric, ep, 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            if ckpt_path: torch.save({"state": best_state, "epoch": ep, "metric": metric}, ckpt_path)
        else:
            bad += 1
        if ep + 1 >= min_epochs and bad >= patience:
            break
    return best_state, curves, best_epoch
