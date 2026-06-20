#!/usr/bin/env python3
"""
Numerical check of the two-sided robust-radius bracket (Theorem thm:sandwich /
Proposition prop:computable-bracket) for the power-spectrum quadratic surrogate.

For the two-orbit quadratic surrogate g on ||x||<=B we claim
        eta_Q / L  <=  r_2  <=  eta_Q / alpha ,
with L the upper Lipschitz (<= 2B analytically) and alpha = inf ||grad g|| along the
gradient path to the boundary (the co-Lipschitz constant). This script verifies the
bracket contains the DDN min-norm radius. Run:
  paper/env/cenv/bin/python paper/experiments/verify_sandwich.py
"""
import torch, numpy as np
from p4_orbit_stress import gen_orbit_data, quad_surrogate, r2_ddn, D

torch.manual_seed(0)

def gnorm(f, x):                       # ||grad g|| at rows of x
    x = x.clone().detach().requires_grad_(True)
    g, = torch.autograd.grad(f(x).sum(), x)
    return g.detach()

def path_alpha(f, x0, step=5e-3, max_steps=4000):
    """Descend g from x0 to the boundary; return (inf ||grad g|| on path, path length, end g)."""
    x = x0.clone().detach().unsqueeze(0); g0 = float(f(x)); sgn = 1.0 if g0 > 0 else -1.0
    amin, length = float("inf"), 0.0
    for _ in range(max_steps):
        gr = gnorm(f, x)[0]; amin = min(amin, float(gr.norm()))
        if sgn * float(f(x)) <= 0: break
        x = (x - sgn * step * gr / gr.norm().clamp_min(1e-12)).detach(); length += step
    return amin, length, float(f(x))

def verify(seed, d=D):
    X, y, _ = gen_orbit_data(seed, n_orbits=1, d=d)          # 1 orbit/class -> two-orbit case
    fq, eta = quad_surrogate(X, y)
    B = float(X.norm(dim=1).max())
    # upper Lipschitz: analytic bound 2B, and empirical max over data + ball samples
    z = torch.randn(4000, d); z = z / z.norm(dim=1, keepdim=True) * (B * torch.rand(4000, 1) ** (1.0 / d))
    L_emp = float(gnorm(fq, torch.cat([X, z], 0)).norm(dim=1).max())
    # co-Lipschitz alpha = min over positive points of (inf ||grad|| along path to boundary)
    Xp = X[y > 0]; alphas, lens, ends = zip(*[path_alpha(fq, xp) for xp in Xp])
    alpha = min(alphas); reached = max(abs(e) for e in ends)
    r2 = r2_ddn(fq, Xp, y[y > 0])                            # DDN min-norm radius (mean over pos pts)
    # quad_surrogate uses the NON-unitary rfft; the TR's analytic bounds use the unitary DFT
    # (|x_hat|^2_unitary = |rfft|^2 / d). Scaling g by 1/d leaves the boundary (hence r2) fixed but
    # puts eta, L, alpha in the convention where Corollary cor:ps-lip's "L <= 2B" applies.
    eta_u, L_u, alpha_u = eta / d, L_emp / d, alpha / d
    lo_anal, lo_emp, hi = eta_u / (2 * B), eta_u / L_u, eta_u / alpha_u
    ok = (lo_anal - 1e-6 <= r2) and (lo_emp - 1e-6 <= r2) and (r2 <= hi + 1e-6) and (L_u <= 2 * B + 1e-6)
    return dict(seed=seed, eta=eta_u, B=B, L_u=L_u, alpha=alpha_u, kappa=L_emp / alpha,
                r2=r2, lo_anal=lo_anal, lo_emp=lo_emp, hi=hi, twoB=2 * B,
                boundary_residual=reached, ok=ok)

if __name__ == "__main__":
    print(f"# Sandwich bracket check, power-spectrum quadratic surrogate (d={D})")
    print(f"# claim:  eta/(2B) <= eta/L_emp <= r2(DDN) <= eta/alpha\n")
    allok = True
    for s in range(5):
        r = verify(s); allok &= r["ok"]
        print(f"seed {s}: eta={r['eta']:.4f} B={r['B']:.3f} L={r['L_u']:.4f}(<=2B={r['twoB']:.1f}) "
              f"alpha={r['alpha']:.4f} kappa={r['kappa']:.2f} | "
              f"eta/2B={r['lo_anal']:.4f} <= eta/L={r['lo_emp']:.4f} <= r2={r['r2']:.4f} <= eta/alpha={r['hi']:.4f}  "
              f"{'OK' if r['ok'] else 'FAIL'}")
    print(f"\nALL SEEDS {'PASS' if allok else 'FAIL'}: DDN radius lies inside the analytic bracket.")
