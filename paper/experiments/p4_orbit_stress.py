#!/usr/bin/env python3
"""
P4 stress test (the decisive check before proving P1-P3).

Question: on NONDEGENERATE full-rank orbit data, does unconstrained gradient descent reach a
NON-robust solution (small eta/L, small robust radius) even though a robust invariant solution
EXISTS?  If yes, the Frei/Li feature-averaging premise plausibly transfers and P1-P3 are worth
proving.  If no (unconstrained GD already reaches the robust solution), the trajectory conjecture
must be weakened or moved to multi-orbit cluster-geometry data.

Data: two (or more) base patterns u,v ~ N(0,I) normalized to unit norm (generically all Fourier
coefficients nonzero -> full-rank orbits, distinct power spectra -> power-spectrum separable, as
the theory's sec:opt-open specifies).  Each class is the cyclic orbit of its base(s).

Models (all homogeneous, no bias):
  unconstrained : f(x) = a^T relu(W x)                              (sees 2d distinct points)
  tied-invariant: f(x) = a^T mean_s relu(corr(w_r, x))             (exactly shift-invariant)
  quad-surrogate: f(x) = a*^T Q(x) + b*  (closed-form max-margin in power-spectrum space; the
                  robust reference, also verifies Theorem thm:quadratic-two-orbit)

Metrics per model: train acc, mean L2 robust radius r2 (DDN min-norm, no box), eta/L (mean
first-order distance to boundary on correct points), shift-consistency, and weight-frequency
diagnostics.  Verdict compares r2_unc against the robust references r2_tied / r2_quad.

Run: paper/env/cenv/bin/python paper/experiments/p4_orbit_stress.py
"""
import argparse, numpy as np, torch, torch.nn as nn, torch.nn.functional as F

D = 64

def gen_orbit_data(seed, n_orbits=1, d=D):
    g = torch.Generator().manual_seed(seed)
    Xs, ys, bases = [], [], {1: [], -1: []}
    for lab in (1.0, -1.0):
        for _ in range(n_orbits):
            u = torch.randn(d, generator=g); u = u / u.norm()
            bases[int(lab)].append(u)
            orb = torch.stack([torch.roll(u, s) for s in range(d)])   # full cyclic orbit
            Xs.append(orb); ys.append(torch.full((d,), lab))
    return torch.cat(Xs), torch.cat(ys), bases

def full_support(u, d=D):
    return int((torch.fft.rfft(u).abs() > 1e-9).sum())

class Unc(nn.Module):
    def __init__(self, m, d=D, init=0.1):
        super().__init__()
        self.W = nn.Parameter(torch.randn(m, d) * init / np.sqrt(d))
        self.a = nn.Parameter(torch.randn(m) * init)
    def forward(self, x): return F.relu(x @ self.W.T) @ self.a

class Tied(nn.Module):
    """Exactly shift-invariant: per filter, circular correlation -> ReLU -> global average pool."""
    def __init__(self, m, d=D, init=0.1):
        super().__init__()
        self.W = nn.Parameter(torch.randn(m, d) * init / np.sqrt(d))
        self.a = nn.Parameter(torch.randn(m) * init); self.d = d
    def forward(self, x):
        Xf = torch.fft.rfft(x, dim=1)                         # (N, d/2+1)
        Wf = torch.fft.rfft(self.W, dim=1)                    # (m, d/2+1)
        corr = torch.fft.irfft(Xf[:, None, :] * Wf.conj()[None, :, :], n=self.d, dim=2)  # (N,m,d)
        return F.relu(corr).mean(dim=2) @ self.a             # GAP over shifts -> invariant

def quad_surrogate(X, y):
    """Closed-form (two-orbit) or hard-margin SVM (multi-orbit) max-margin head on power spectrum."""
    Q = lambda x: (torch.fft.rfft(x, dim=-1).abs() ** 2)
    qp = Q(X[y > 0]); qm = Q(X[y < 0])
    if torch.allclose(qp, qp[0]) and torch.allclose(qm, qm[0]):   # two-orbit: each class one point
        a = qp[0] - qm[0]; eta = 0.5 * a.norm(); a = a / a.norm()
        b = -0.5 * (a @ (qp[0] + qm[0]))
        return (lambda x: Q(x) @ a + b), float(eta)
    from sklearn.svm import SVC                                    # multi-orbit: SVM in Q-space
    Qx = Q(X).numpy(); svc = SVC(C=1e6, kernel="linear").fit(Qx, y.numpy())
    w = torch.tensor(svc.coef_[0], dtype=torch.float32); b0 = float(svc.intercept_[0])
    nrm = w.norm(); eta = 1.0 / float(nrm)
    return (lambda x: (Q(x) @ (w / nrm) + b0 / nrm)), eta

def train(model, X, y, steps=20000, lr=0.5, lossbased=True, lr_cap=200.0):
    """GD on the logistic loss. The Lyu-Li loss-based increasing LR (lr *= loss0/loss, capped)
    reaches the max-margin / implicit-bias regime far faster than fixed LR, whose convergence is
    only O(1/log t); see github.com/vfleaking/max-margin. Bias-free homogeneous nets."""
    opt = torch.optim.SGD(model.parameters(), lr=lr)
    with torch.no_grad():
        loss0 = float(F.softplus(-y * model(X)).mean().clamp_min(1e-6))
    for _ in range(steps):
        opt.zero_grad(set_to_none=True)
        loss = F.softplus(-y * model(X)).mean()
        loss.backward()
        if lossbased:
            f = min(loss0 / float(loss.detach().clamp_min(1e-12)), lr_cap)
            for grp in opt.param_groups:
                grp["lr"] = lr * f
        opt.step()
    return model.eval()

@torch.no_grad()
def norm_margin(model, X, y):
    """Normalized margin min_i y_i f(x_i) / ||theta||^2 (degree-2 homogeneous); a convergence
    diagnostic for the implicit bias (plateaus when the max-margin direction is reached)."""
    pn2 = sum((p ** 2).sum() for p in model.parameters()).clamp_min(1e-12)
    return float((y * model(X)).min() / pn2)

@torch.no_grad()
def acc(fmodel, X, y): return float((torch.sign(fmodel(X)) == torch.sign(y)).float().mean())

def r2_ddn(fmodel, X, y, steps=300, gamma=0.05, eps0=1.0):
    """Per-sample min-||delta||_2 to flip sign (DDN; no box, synthetic data)."""
    N = len(X); best = torch.full((N,), float("inf")); eps = torch.full((N,), float(eps0))
    delta = torch.zeros_like(X)
    for k in range(steps):
        alpha = 0.01 + (1.0 - 0.01) * (1 + np.cos(np.pi * k / steps)) / 2
        delta.requires_grad_(True)
        f = fmodel(X + delta)
        g, = torch.autograd.grad((-(y * f)).sum(), delta)         # ascend to drive y*f below 0
        with torch.no_grad():
            flipped = (y * f) < 0
            nrm = delta.norm(dim=1); upd = flipped & (nrm < best); best[upd] = nrm[upd]
            eps = torch.where(flipped, eps * (1 - gamma), eps * (1 + gamma))
            gn = g / g.norm(dim=1, keepdim=True).clamp_min(1e-12)
            delta = delta + alpha * gn
            delta = delta / delta.norm(dim=1, keepdim=True).clamp_min(1e-12) * eps[:, None]
    finite = torch.isfinite(best)
    return float(best[finite].mean()) if finite.any() else float("nan")

def eta_over_L(fmodel, X, y):
    Xr = X.clone().requires_grad_(True); f = fmodel(Xr)
    g, = torch.autograd.grad(f.sum(), Xr)
    m = (y * f).detach(); gn = g.norm(dim=1); ok = m > 0
    return float((m[ok] / gn[ok].clamp_min(1e-12)).mean())

@torch.no_grad()
def orbit_invariance(fmodel, X, d=D):
    """Real invariance probe: std of f across each cyclic orbit, normalized by mean |f|.
    0 = exactly invariant. (Sign-consistency is trivial here: rolling stays in the same orbit.)"""
    n = len(X) // d; vals = []
    for o in range(n):
        f = fmodel(X[o * d:(o + 1) * d])
        vals.append((f.std() / f.abs().mean().clamp_min(1e-12)).item())
    return float(np.mean(vals))

def run(seed, n_orbits, m=256, init=0.1, steps=20000):
    X, y, bases = gen_orbit_data(seed, n_orbits)
    supp = [full_support(u) for c in bases.values() for u in c]
    torch.manual_seed(seed)
    unc = train(Unc(m, init=init), X, y, steps=steps)
    torch.manual_seed(seed)
    tied = train(Tied(m, init=init), X, y, steps=steps)
    fq, eta_q = quad_surrogate(X, y)
    out = {"seed": seed, "n_orbits": n_orbits, "min_fft_support": min(supp)}
    for name, f in [("unconstrained", unc), ("tied-invariant", tied), ("quad-surrogate", fq)]:
        out[name] = dict(acc=acc(f, X, y), r2=r2_ddn(f, X, y), etaL=eta_over_L(f, X, y),
                         orbvar=orbit_invariance(f, X))
    out["eta_q"] = eta_q
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5); ap.add_argument("--steps", type=int, default=20000)
    ap.add_argument("--init", type=float, default=0.1); ap.add_argument("--m", type=int, default=256)
    args = ap.parse_args()
    for init in (0.1, 1.0):
      for n_orbits in (1, 4):
        print(f"\n======== {n_orbits} orbit(s)/class, init={init} ({'rich' if init<0.5 else 'lazy'})  (d={D}, m={args.m}, steps={args.steps}) ========")
        rows = [run(s, n_orbits, m=args.m, init=init, steps=args.steps) for s in range(args.seeds)]
        print(f"min FFT support: {min(r['min_fft_support'] for r in rows)}/{D//2+1} "
              f"(full-rank) ; quad eta_Q mean {np.mean([r['eta_q'] for r in rows]):.3f}")
        hdr = f"{'model':16s} {'train_acc':>9s} {'r2(mean)':>11s} {'eta/L':>8s} {'orbit-var':>9s}"
        print(hdr); print("-" * len(hdr))
        for name in ["unconstrained", "tied-invariant", "quad-surrogate"]:
            a = np.mean([r[name]["acc"] for r in rows]); r2 = np.mean([r[name]["r2"] for r in rows])
            el = np.mean([r[name]["etaL"] for r in rows]); ov = np.mean([r[name]["orbvar"] for r in rows])
            r2sd = np.std([r[name]["r2"] for r in rows])
            print(f"{name:16s} {a:9.3f} {r2:6.3f}+-{r2sd:4.3f} {el:8.3f} {ov:9.3f}")
        r2u = np.mean([r["unconstrained"]["r2"] for r in rows])
        r2t = np.mean([r["tied-invariant"]["r2"] for r in rows])
        r2q = np.mean([r["quad-surrogate"]["r2"] for r in rows])
        ref = max(r2t, r2q)
        ratio = r2u / ref if ref > 0 else float("nan")
        print(f"VERDICT ({n_orbits}-orbit): r2_unc/max(r2_tied,r2_quad) = {ratio:.2f}  ->  "
              + ("UNCONSTRAINED IS NON-ROBUST despite a robust solution existing: P2 plausible, prove P1-P3."
                 if ratio < 0.7 else
                 "unconstrained GD already ~robust: P2 likely FALSE here -> weaken conjecture / need multi-orbit cluster geometry."))

if __name__ == "__main__":
    main()
