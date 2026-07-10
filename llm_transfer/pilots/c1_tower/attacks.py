"""Strong-attack evaluation at the zero-shot-logit (encoder) level.

Load-bearing attack: AutoAttack ensemble (APGD-CE + APGD-DLR), Linf, on [0,1] pixels
through the frozen tower's zero-shot logits. No decoder in the graph (round2_C: encoder
level is the feasibility lever and the tower governs, 2407.11121).

Gradient-masking audit (mandatory, first-class):
  - APGD robust acc <= PGD-40 robust acc <= FGSM robust acc   (monotonicity)
  - Square Attack (black-box) gap vs APGD
All attacks share the same eval subset and threat model per tower.

Also: per-image minimum-Linf robust radius by PGD + bisection (for per-image Spearman
of eta/L vs per-image robust radius).
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------- white-box PGD / FGSM (Linf, on [0,1] pixels) ----------------
def _ce_loss(logits, y):
    return F.cross_entropy(logits, y, reduction="none")


def fgsm(tower, x, y, eps):
    x = x.clone().detach().requires_grad_(True)
    loss = _ce_loss(tower(x), y).sum()
    g = torch.autograd.grad(loss, x)[0]
    xadv = (x + eps * g.sign()).clamp(0, 1).detach()
    return xadv


def pgd_linf(tower, x, y, eps, steps=40, alpha=None, restarts=1, rand_init=True):
    """Untargeted Linf PGD on CE. Returns adversarial batch (worst-case over restarts)."""
    if alpha is None:
        alpha = 2.5 * eps / steps
    x0 = x.clone().detach()
    best_adv = x0.clone()
    # track which are already fooled
    with torch.no_grad():
        still_correct = tower(x0).argmax(1) == y
    for r in range(restarts):
        if rand_init:
            delta = (torch.rand_like(x0) * 2 - 1) * eps
        else:
            delta = torch.zeros_like(x0)
        xadv = (x0 + delta).clamp(0, 1).detach()
        for _ in range(steps):
            xadv.requires_grad_(True)
            loss = _ce_loss(tower(xadv), y).sum()
            g = torch.autograd.grad(loss, xadv)[0]
            xadv = xadv.detach() + alpha * g.sign()
            xadv = torch.min(torch.max(xadv, x0 - eps), x0 + eps).clamp(0, 1)
        with torch.no_grad():
            fooled = tower(xadv).argmax(1) != y
        newly = fooled & still_correct
        best_adv[newly] = xadv[newly]
        still_correct = still_correct & ~fooled
    return best_adv


@torch.no_grad()
def robust_acc(tower, xadv, y, bs=256, device="cuda"):
    correct = 0
    for i in range(0, len(xadv), bs):
        lg = tower(xadv[i:i + bs].to(device))
        correct += (lg.argmax(1) == y[i:i + bs].to(device)).sum().item()
    return correct / len(y)


def run_pgd_eval(tower, images, labels, eps, steps=40, restarts=1, bs=64, device="cuda"):
    advs = []
    for i in range(0, len(images), bs):
        xb = images[i:i + bs].to(device)
        yb = labels[i:i + bs].to(device)
        advs.append(pgd_linf(tower, xb, yb, eps, steps=steps, restarts=restarts).cpu())
    xadv = torch.cat(advs)
    return robust_acc(tower, xadv, labels, device=device)


def run_fgsm_eval(tower, images, labels, eps, bs=128, device="cuda"):
    advs = []
    for i in range(0, len(images), bs):
        xb = images[i:i + bs].to(device)
        yb = labels[i:i + bs].to(device)
        advs.append(fgsm(tower, xb, yb, eps).cpu())
    xadv = torch.cat(advs)
    return robust_acc(tower, xadv, labels, device=device)


# ---------------- AutoAttack (APGD-CE + APGD-DLR ensemble) ----------------
def run_autoattack(tower, images, labels, eps, n_classes, bs=64, device="cuda",
                   square=True, seed=0):
    """AutoAttack ensemble on Linf. Uses apgd-ce + apgd-t (+ optional square).

    Returns dict: robust_acc (full AA), and per-attack robust accs, plus per-image
    'still_robust' boolean over the standard (non-square) ensemble.
    """
    from autoattack import AutoAttack
    tower = tower.to(device).eval()

    class Wrap(nn.Module):
        def __init__(self, t):
            super().__init__()
            self.t = t

        def forward(self, x):
            return self.t(x)

    wrap = Wrap(tower).to(device).eval()
    attacks = ["apgd-ce", "apgd-t"]
    if square:
        attacks_full = attacks + ["square"]
    else:
        attacks_full = attacks
    adversary = AutoAttack(wrap, norm="Linf", eps=eps, version="custom",
                           attacks_to_run=attacks_full, device=device, seed=seed)
    adversary.apgd.n_restarts = 1
    adversary.apgd_targeted.n_restarts = 1
    adversary.apgd_targeted.n_target_classes = min(5, n_classes - 1)
    adversary.verbose = False
    if square:
        adversary.square.n_queries = 5000
    x = images.to(device)
    y = labels.to(device)
    xadv = adversary.run_standard_evaluation(x, y, bs=bs)
    ra = robust_acc(tower, xadv.cpu(), labels, device=device)
    return {"robust_acc": ra, "xadv": xadv.cpu()}


def run_square_gap(tower, images, labels, eps, bs=64, device="cuda", n_queries=2000, seed=0):
    """Black-box Square Attack robust acc (for the APGD-vs-Square masking gap).
    Run on the full attack subset; caller compares to APGD-only S."""
    from autoattack import AutoAttack

    class Wrap(nn.Module):
        def __init__(self, t):
            super().__init__(); self.t = t
        def forward(self, x):
            return self.t(x)

    wrap = Wrap(tower).to(device).eval()
    adv = AutoAttack(wrap, norm="Linf", eps=eps, version="custom",
                     attacks_to_run=["square"], device=device, seed=seed)
    adv.square.n_queries = n_queries
    xadv = adv.run_standard_evaluation(images.to(device), labels.to(device), bs=bs)
    return robust_acc(tower, xadv.cpu(), labels, device=device)


# ---------------- per-image minimum-Linf robust radius (bisection over PGD) ----------------
def per_image_robust_radius_linf(tower, images, labels, eps_grid, steps=40, bs=64,
                                 device="cuda"):
    """Per-image smallest eps in eps_grid at which PGD flips the label.
    Radius = first eps that fools; images never fooled get max(eps_grid)*inf-cap.
    Returns tensor [N] of radii (in Linf pixel units)."""
    N = len(images)
    radius = torch.full((N,), float(eps_grid[-1]) * 1.5)  # censored above top eps
    flipped = torch.zeros(N, dtype=torch.bool)
    for eps in eps_grid:
        for i in range(0, N, bs):
            sl = slice(i, min(i + bs, N))
            todo = ~flipped[sl]
            if todo.sum() == 0:
                continue
            xb = images[sl][todo].to(device)
            yb = labels[sl][todo].to(device)
            xadv = pgd_linf(tower, xb, yb, eps, steps=steps, restarts=1)
            with torch.no_grad():
                fooled = (tower(xadv).argmax(1) != yb).cpu()
            gidx = torch.where(~flipped[sl])[0]
            hit = gidx[fooled]
            base = i
            radius[base + hit] = eps
            flipped[base + hit] = True
    return radius, flipped
