#!/usr/bin/env python3
"""
Cleanest test of the consolidated theory (prediction P2), in the exact 1-D
cyclic setting the theory is stated in.

Two datasets, each class = a full shift-orbit:
  - DOT:  class +1 = all circular shifts of +e_j ; class -1 = all shifts of -e_j
          (signal in the AC/orbit subspace -> Sep(Pi_inv) ~ 1/sqrt(d) tiny)
  - FREQ: class +1 = shifts (phases) of cos at freq k1 ; class -1 = freq k2
          (DC/linear margin 0, but power-spectrum supports disjoint -> Sep_Psi = Theta(1))

Two models (matched-ish capacity):
  - ConvGAP : Conv1d (circular pad) + ReLU + global average pool + linear  (shift-invariant)
  - FC      : flatten + linear + ReLU + linear                              (not invariant)

Theory predicts (P2):
  - DOT  : ConvGAP LESS robust than FC (Ge 2/sqrt(d) collapse)
  - FREQ : ConvGAP MORE robust than FC (FC linear margin ~0; invariant power-spectrum separates)

Robustness = accuracy under L2-PGD over an epsilon sweep (untargeted), plus a
mean min-flip-epsilon estimate (robust-radius proxy). No [0,1] clamp (synthetic data).
Run with the isolated env:
  paper/env/cenv/bin/python paper/experiments/synthetic_1d.py
"""
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F

torch.manual_seed(0); np.random.seed(0)
DEV = "cuda" if torch.cuda.is_available() else "cpu"
d = 64          # signal length
H = 64          # hidden width
EPOCHS = 300

# ---------------- datasets (each class is a full shift orbit) ----------------
def shifts(v):                       # all d circular shifts of vector v (length d)
    return np.stack([np.roll(v, s) for s in range(d)], 0)

def dot_dataset():
    base_p = np.zeros(d); base_p[0] = 1.0      # white dot
    base_n = np.zeros(d); base_n[0] = -1.0     # black dot
    Xp, Xn = shifts(base_p), shifts(base_n)
    X = np.concatenate([Xp, Xn], 0); y = np.array([1]*d + [0]*d)
    return X, y

def freq_dataset(k1=3, k2=7, n_phase=64, amp=(0.7, 1.3)):
    t = np.arange(d)
    rows, ys = [], []
    rng = np.random.RandomState(1)
    for k, lab in [(k1, 1), (k2, 0)]:
        for _ in range(n_phase):
            ph = rng.uniform(0, 2*np.pi); a = rng.uniform(*amp)
            rows.append(a*np.cos(2*np.pi*k*t/d + ph)); ys.append(lab)
    return np.stack(rows, 0), np.array(ys)

# ---------------- models ----------------
class ConvGAP(nn.Module):            # shift-invariant: circular conv + GAP + linear
    def __init__(self, h=H, k=d):
        super().__init__()
        self.conv = nn.Conv1d(1, h, k, padding=k//2, padding_mode="circular")
        self.fc = nn.Linear(h, 2)
    def forward(self, x):            # x: (N, d)
        z = F.relu(self.conv(x.unsqueeze(1)))   # (N,h,~d)
        z = z.mean(dim=2)                        # global average pool -> (N,h)
        return self.fc(z)

class FC(nn.Module):
    def __init__(self, h=H):
        super().__init__()
        self.net = nn.Sequential(nn.Flatten(), nn.Linear(d, h), nn.ReLU(), nn.Linear(h, 2))
    def forward(self, x): return self.net(x)

def n_params(m): return sum(p.numel() for p in m.parameters())

# ---------------- train ----------------
def train(model, X, y):
    model = model.to(DEV).train()
    Xt = torch.tensor(X, dtype=torch.float32, device=DEV)
    yt = torch.tensor(y, dtype=torch.long, device=DEV)
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    for ep in range(EPOCHS):
        opt.zero_grad(); loss = F.cross_entropy(model(Xt), yt); loss.backward(); opt.step()
    model.eval()
    with torch.no_grad():
        acc = (model(Xt).argmax(1) == yt).float().mean().item()
    return model, acc

# ---------------- L2-PGD (no [0,1] clamp; synthetic data) ----------------
def pgd_l2(model, X, y, eps, steps=50, step_frac=0.2):
    Xt = torch.tensor(X, dtype=torch.float32, device=DEV)
    yt = torch.tensor(y, dtype=torch.long, device=DEV)
    delta = torch.zeros_like(Xt, requires_grad=True)
    alpha = step_frac * eps
    for _ in range(steps):
        loss = F.cross_entropy(model(Xt + delta), yt)
        g, = torch.autograd.grad(loss, delta)
        gn = g / (g.flatten(1).norm(dim=1).clamp_min(1e-12)[:, None])
        delta = (delta + alpha * gn).detach()
        dn = delta.flatten(1).norm(dim=1).clamp_min(1e-12)
        factor = (eps / dn).clamp(max=1.0)
        delta = (delta * factor[:, None]).requires_grad_(True)
    with torch.no_grad():
        acc = (model(Xt + delta).argmax(1) == yt).float().mean().item()
    return acc

def robustness_curve(model, X, y, eps_grid):
    return {round(e, 3): pgd_l2(model, X, y, e) for e in eps_grid}

def mean_flip_eps(model, X, y, eps_grid):
    """robust-radius proxy: per-sample smallest grid-eps that flips it (else max)."""
    Xt = torch.tensor(X, dtype=torch.float32, device=DEV)
    yt = torch.tensor(y, dtype=torch.long, device=DEV)
    flipped_at = np.full(len(y), eps_grid[-1])
    done = np.zeros(len(y), bool)
    for e in eps_grid:
        d_ = torch.zeros_like(Xt, requires_grad=True)
        for _ in range(50):
            loss = F.cross_entropy(model(Xt + d_), yt)
            g, = torch.autograd.grad(loss, d_)
            gn = g / (g.flatten(1).norm(dim=1).clamp_min(1e-12)[:, None])
            d_ = (d_ + 0.2*e*gn).detach()
            dn = d_.flatten(1).norm(dim=1).clamp_min(1e-12)
            d_ = (d_ * (e/dn).clamp(max=1.0)[:, None]).requires_grad_(True)
        with torch.no_grad():
            wrong = (model(Xt + d_).argmax(1) != yt).cpu().numpy()
        newly = wrong & ~done
        flipped_at[newly] = e; done |= newly
        if done.all(): break
    return float(flipped_at.mean())

# ---------------- run ----------------
if __name__ == "__main__":
    print(f"device={DEV}  d={d}  H={H}  epochs={EPOCHS}")
    print(f"params: ConvGAP={n_params(ConvGAP())}  FC={n_params(FC())}")
    for name, (X, y), eps_grid in [
        ("DOT",  dot_dataset(),  np.linspace(0.05, 1.5, 16)),
        ("FREQ", freq_dataset(), np.linspace(0.05, 1.5, 16)),
    ]:
        print(f"\n===== {name}  (N={len(y)}, ||x||~{np.linalg.norm(X,axis=1).mean():.2f}) =====")
        for mname, M in [("ConvGAP(inv)", ConvGAP), ("FC", FC)]:
            m, acc = train(M(), X, y)
            mfe = mean_flip_eps(m, X, y, eps_grid)
            curve = robustness_curve(m, X, y, [0.1, 0.25, 0.5, 1.0])
            print(f"  {mname:13s} clean={acc:.2f}  mean_flip_eps(radius proxy)={mfe:.3f}  "
                  f"robacc@{{0.1,0.25,0.5,1.0}}={[curve[k] for k in (0.1,0.25,0.5,1.0)]}")
    print("\nTheory P2: DOT -> ConvGAP radius < FC ; FREQ -> ConvGAP radius > FC")
