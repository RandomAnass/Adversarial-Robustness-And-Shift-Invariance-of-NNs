#!/usr/bin/env python3
"""
rank_probe.py -- SECOND-ORDER ranking probe for the "eta/L detects but does not RANK"
puzzle (REVIEW_ROUND_1.md).

Empirical fact this addresses (among the 10 robust CLIP towers, S_apgd in [0.71,0.88]):
  eta/L1   ranks robust acc at Spearman +0.38 (n.s.)   <- first-order ratio saturates
  eta/L2   ranks robust acc at Spearman +0.25 (n.s.)
  eta      ranks robust acc at Spearman -0.37          <- margin alone is anti-informative
  L1/L2 anisotropy ranks at Spearman -0.64 (p=0.048)   <- a DIRECTIONAL signal already ranks

Hypothesis (prop:sandwich): eta/L is only the LOWER arm of  eta/L <= r2 <= eta/alpha.
Among robust towers the point-gradient L is saturated; what orders robustness is the
condition number kappa = L_ball / L_point (curvature over the eps-ball) and/or the
lower-Lipschitz secant alpha. This script computes, per tower, on the SAME cached
attack subset, four second-order candidates and correlates each with S_apgd.

Candidates (per correctly-classified image, then tower-mean):
  C1  L_ball   = max ||grad M(x')|| over the PGD path (local Lipschitz over the ball)
                 kappa_hat = L_ball / L_point   (>=1; the sandwich tightness)
  C2  curv     = ||grad M(x+h u) - grad M(x)|| / h   with u the FGSM/gradient direction
                 (finite-difference input curvature, CURE-style, 1811.09716)
  C3  alpha    = secant slope  M(x)/||x - x_boundary||  along the min-norm attack
                 direction (the UPPER-arm lower-Lipschitz constant); rank by eta/alpha
  C4  aniso    = ||grad M||_1 / ||grad M||_2  (cheap direction-spread control; already p=.048)

Prediction: eta/L_ball (curvature-corrected radius) and/or eta/alpha RANK S_apgd among
the 10 robust towers where eta/L_point failed. C1/C3 are the sandwich arms; C2 is the
CURE curvature proxy; C4 is the near-free control.

Run (2 GPUs, ~10-20 min total; reuses the cached in100val subset + tower loader):
  paper/env/cenv/bin/python pilots/c1_tower/rank_probe.py --towers all --n 256
"""
import argparse, json, os, time
import torch
import torch.nn.functional as F

# reuse the existing tower loader + data cache from the C1 pilot
from towers import load_clip_tower, load_dinov2_backbone  # noqa (tower API: tower(x01)->logits)
from data import load_val, get_class_names                 # cached [0,1] pixel eval subset + labels


def signed_margin(logits, y):
    """M(x) = f_y - max_{j!=y} f_j  (active logit margin)."""
    tgt = logits.gather(1, y[:, None]).squeeze(1)
    other = logits.clone()
    other.scatter_(1, y[:, None], float("-inf"))
    return tgt - other.max(1).values


def margin_grad(tower, x, y):
    """grad_x M(x) for a batch; returns (M, grad) with M detached."""
    x = x.clone().detach().requires_grad_(True)
    M = signed_margin(tower(x), y)
    g, = torch.autograd.grad(M.sum(), x)
    return M.detach(), g.detach()


@torch.no_grad()
def flatten_norm(g, p):
    return g.flatten(1).norm(p=p, dim=1)


def pgd_path_maxgrad(tower, x, y, eps, steps=20):
    """C1: run Linf-PGD; track the MAX ||grad M||_1 along the path (local Lipschitz over ball).
    Returns (L_point_1, L_ball_1) per image, both L1 (dual of Linf)."""
    x0 = x.clone().detach()
    M0, g0 = margin_grad(tower, x0, y)
    L_point = flatten_norm(g0, 1)
    L_ball = L_point.clone()
    xadv = x0.clone()
    alpha = 2.5 * eps / steps
    for _ in range(steps):
        M, g = margin_grad(tower, xadv, y)
        L_ball = torch.maximum(L_ball, flatten_norm(g, 1))
        # descend the margin (move toward the boundary) to probe the ball the attack uses
        xadv = (xadv - alpha * g.sign()).clamp(0, 1)
        xadv = torch.min(torch.max(xadv, x0 - eps), x0 + eps)
    return M0, L_point, L_ball


def input_curvature(tower, x, y, h=None):
    """C2: CURE-style finite-difference curvature in the gradient direction.
    curv = ||grad M(x + h*z) - grad M(x)|| / h,  z = sign(grad M(x)) normalized (Linf attack dir).
    (1811.09716 estimates the top Hessian curvature by exactly this FD in the grad direction.)"""
    M0, g0 = margin_grad(tower, x, y)
    z = g0.sign()
    if h is None:
        h = 4.0 / 255.0
    x2 = (x + h * z).clamp(0, 1)
    _, g2 = margin_grad(tower, x2, y)
    curv = (g2 - g0).flatten(1).norm(dim=1) / h
    return curv


def secant_alpha(tower, x, y, eps, steps=30):
    """C3: min-norm-ish Linf attack; on flipped points return alpha = M0 / ||delta||_2
    (the lower-Lipschitz secant of the UPPER sandwich arm). eta/alpha is the upper radius."""
    x0 = x.clone().detach()
    M0, _ = margin_grad(tower, x0, y)
    xadv = x0.clone()
    a = 2.5 * eps / steps
    for _ in range(steps):
        _, g = margin_grad(tower, xadv, y)
        xadv = (xadv - a * g.sign()).clamp(0, 1)
        xadv = torch.min(torch.max(xadv, x0 - eps), x0 + eps)
    with torch.no_grad():
        Madv = signed_margin(tower(xadv), y)
        flipped = Madv < 0
        dnorm = (xadv - x0).flatten(1).norm(dim=1).clamp_min(1e-8)
        alpha = M0 / dnorm  # secant slope M0/||delta|| (only meaningful where flipped)
    return alpha, flipped


def run_tower(name, tower, x, y, eps, device):
    tower.eval().to(device)
    x, y = x.to(device), y.to(device)
    with torch.no_grad():
        correct = tower(x).argmax(1) == y
    x, y = x[correct], y[correct]  # certificate quantities defined on correct points
    outs = {}
    M0, Lp1, Lb1 = pgd_path_maxgrad(tower, x, y, eps)
    curv = input_curvature(tower, x, y)
    alpha, flipped = secant_alpha(tower, x, y, eps)
    kappa = (Lb1 / Lp1.clamp_min(1e-8))
    outs["eta"] = M0.mean().item()
    outs["L_point_1"] = Lp1.mean().item()
    outs["L_ball_1"] = Lb1.mean().item()
    outs["kappa_hat"] = kappa.mean().item()
    outs["eta_over_Lpoint"] = (M0 / Lp1.clamp_min(1e-8)).mean().item()   # reproduces eta/L1
    outs["eta_over_Lball"] = (M0 / Lb1.clamp_min(1e-8)).mean().item()    # C1: curvature-corrected
    outs["curv"] = curv.mean().item()                                     # C2
    if flipped.any():
        outs["alpha_secant"] = alpha[flipped].mean().item()               # C3
        outs["eta_over_alpha"] = (M0[flipped] / alpha[flipped].clamp_min(1e-8)).mean().item()
    outs["aniso_L1_L2"] = (Lp1 / flatten_norm(margin_grad(tower, x, y)[1], 2).clamp_min(1e-8)).mean().item()
    outs["n"] = int(len(y))
    return outs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--towers", default="all")
    ap.add_argument("--n", type=int, default=256)
    ap.add_argument("--eps", type=float, default=8 / 255)
    ap.add_argument("--out", default="../../results/c1_tower/rank_probe.json")
    args = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    x, y = load_val(n=args.n)                # cached; returns [0,1] pixels + integer labels
    class_names = get_class_names()          # 100 ImageNet-100 class name strings
    ROBUST = ["fare2", "fare4", "tecoa2", "tecoa4",
              "fare4_b16", "fare4_b32", "fare4_cnxt",
              "tecoa4_b16", "tecoa4_b32", "tecoa4_cnxt"]
    names = ROBUST if args.towers == "all" else args.towers.split(",")

    results = {}
    for nm in names:
        t0 = time.time()
        tower = load_clip_tower(nm, class_names, device)  # loads the matching RobustVLM checkpoint
        results[nm] = run_tower(nm, tower, x, y, args.eps, device)
        results[nm]["seconds"] = time.time() - t0
        del tower; torch.cuda.empty_cache()
        print(nm, {k: round(v, 4) for k, v in results[nm].items() if isinstance(v, float)})

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump({"args": vars(args), "results": results}, open(args.out, "w"), indent=2)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
