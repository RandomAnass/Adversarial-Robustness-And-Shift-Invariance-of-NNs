"""Shared utilities for the RobustBench anisotropy validation.

Patches robustbench 1.1.1 for torch>=2.6 (weights_only) and swaps the broken
gdrive downloader for gdown. Provides load_model, data loader, the anisotropy /
margin quantities, and an APGD-CE Linf robust-accuracy attack.
"""
import os
import torch

# ---- patches (must run before importing robustbench.utils.load_model) --------
_ORIG_TORCH_LOAD = torch.load
def _patched_load(*a, **k):
    k.setdefault("weights_only", False)
    return _ORIG_TORCH_LOAD(*a, **k)
torch.load = _patched_load

import gdown
import robustbench.utils as _U

def _download_gdrive(gdrive_id, fname_save):
    os.makedirs(os.path.dirname(fname_save), exist_ok=True)
    gdown.download(id=gdrive_id, output=fname_save, quiet=True)
    # sanity: reject html error pages
    if os.path.exists(fname_save):
        with open(fname_save, "rb") as f:
            head = f.read(1)
        if head == b"<":
            os.remove(fname_save)
            raise RuntimeError("gdrive returned HTML (quota/error) for %s" % gdrive_id)
_U.download_gdrive = _download_gdrive
_U.download_gdrive_new = _download_gdrive  # newer name if present

from robustbench.utils import load_model as _rb_load_model
from robustbench.data import load_cifar10 as _rb_load_cifar10

DATA_DIR = "/home/students/code/Anas/adversarial-robustness-shift-invariance/paper/data"
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rb_models")


def load_model(name):
    return _rb_load_model(model_name=name, dataset="cifar10",
                          threat_model="Linf", model_dir=MODEL_DIR)


def load_data(n_examples=1000):
    return _rb_load_cifar10(n_examples=n_examples, data_dir=DATA_DIR)


# ---- the quantities ----------------------------------------------------------
def margin_and_grad(model, x, y):
    """Return M(x)=f_y - max_{j!=y} f_j and grad_x M for a batch.

    x: [B,3,32,32] in [0,1], requires no grad on input coming in.
    Returns margins [B], grad [B,3,32,32].
    """
    x = x.clone().detach().requires_grad_(True)
    logits = model(x)                       # [B,C]
    B, C = logits.shape
    yl = logits.gather(1, y.view(-1, 1)).squeeze(1)      # f_y
    other = logits.clone()
    other.scatter_(1, y.view(-1, 1), float("-inf"))
    other_max = other.max(1).values                       # max_{j!=y} f_j
    margins = yl - other_max                               # [B]
    grad = torch.autograd.grad(margins.sum(), x, create_graph=False)[0]
    return margins.detach(), grad.detach()


@torch.no_grad()
def predict(model, x, bs=128):
    out = []
    for i in range(0, x.shape[0], bs):
        out.append(model(x[i:i+bs]).argmax(1))
    return torch.cat(out)


def compute_anisotropy_and_eta(model, x, y, bs=64, device="cuda"):
    """On the given (correctly classified) images compute:
      A_i = ||grad M_i||_1 / ||grad M_i||_2   (per-image), report mean
      eta/L_1 = mean(M) / mean(||grad M||_1)
    Returns dict.
    """
    ratios = []      # per-image L1/L2
    margins_all = []
    l1_all = []
    for i in range(0, x.shape[0], bs):
        xb = x[i:i+bs].to(device)
        yb = y[i:i+bs].to(device)
        m, g = margin_and_grad(model, xb, yb)
        gflat = g.reshape(g.shape[0], -1)
        l1 = gflat.abs().sum(1)
        l2 = gflat.norm(p=2, dim=1)
        ratios.append((l1 / (l2 + 1e-30)).cpu())
        margins_all.append(m.cpu())
        l1_all.append(l1.cpu())
    ratios = torch.cat(ratios)
    margins_all = torch.cat(margins_all)
    l1_all = torch.cat(l1_all)
    A = float(ratios.mean())
    eta_over_L1 = float(margins_all.mean() / (l1_all.mean() + 1e-30))
    d = x[0].numel()
    return {
        "A": A,
        "A_std": float(ratios.std()),
        "eta_over_L1": eta_over_L1,
        "mean_margin": float(margins_all.mean()),
        "mean_l1": float(l1_all.mean()),
        "d": int(d),
        "sqrt_d": float(d ** 0.5),
        "n_used": int(x.shape[0]),
    }
