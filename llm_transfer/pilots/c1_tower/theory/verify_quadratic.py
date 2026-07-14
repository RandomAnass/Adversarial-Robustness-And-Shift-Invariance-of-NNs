"""
Verify the quadratic-margin anisotropy analysis.

M(delta) = M0 + w^T delta + 0.5 delta^T H delta   (margin at current point x0=0 is M0>0).
True Linf robust radius r_inf = smallest eps such that
   min_{||delta||_inf <= eps} M(delta) <= 0.
We compute the true radius by a fine bisection on eps, solving the inner minimization
(a nonconvex box-constrained QP) by multi-start projected gradient descent + the
first-order candidate delta=-eps sign(w). This is the "strong attack" radius.

Tests:
 (T1) COUNTEREXAMPLE: fix M0, ||w||_1, sign(w); vary anisotropy A=||w||_1/||w||_2.
      With H=0 (or H depending only on sign(w)), radius should be CONSTANT in A.
 (T2) PROPOSITION: H = -c * hatw hatw^T (aligned concave). At fixed eta/L1 and M0,
      radius should DECREASE monotonically in A, with gap ~ A^2.
 (T3) ISOTROPIC H = -c I: gap should be ~independent of A (mechanism does NOT use spread).
"""
import numpy as np

rng = np.random.default_rng(0)

def margin(delta, M0, w, H):
    return M0 + w @ delta + 0.5 * delta @ (H @ delta)

def inner_min_over_box(eps, M0, w, H, n_starts=40, iters=300, lr=None):
    """Minimize M(delta) over ||delta||_inf <= eps. Returns min value found."""
    d = w.shape[0]
    if lr is None:
        lr = eps * 0.5
    best = np.inf
    # candidate 1: first-order worst case
    cands = [-eps * np.sign(w)]
    # random starts on the box vertices and interior
    for _ in range(n_starts):
        cands.append(rng.uniform(-eps, eps, size=d))
    for _ in range(n_starts//2):
        cands.append(eps * rng.choice([-1.0, 1.0], size=d))
    for x0 in cands:
        x = np.clip(x0, -eps, eps).copy()
        for _ in range(iters):
            g = w + H @ x
            x = np.clip(x - lr * g, -eps, eps)
        val = margin(x, M0, w, H)
        if val < best:
            best = val
    return best

def true_radius_inf(M0, w, H, hi=None, tol=1e-4):
    """Smallest eps with inner_min <= 0, via bisection."""
    if hi is None:
        hi = 10.0 * M0 / np.linalg.norm(w, 1)
    # ensure hi flips
    for _ in range(60):
        if inner_min_over_box(hi, M0, w, H) <= 0:
            break
        hi *= 1.7
    lo = 0.0
    while hi - lo > tol * max(1.0, hi):
        mid = 0.5 * (lo + hi)
        if inner_min_over_box(mid, M0, w, H) <= 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)

def make_w(d, A_target, l1_target, sign_pattern):
    """Build w with given sign pattern, ||w||_1 = l1_target, and anisotropy A=||w||_1/||w||_2 = A_target.
    A in [1, sqrt(d)].  We use a two-level magnitude: k coords large, rest small, tune to hit A.
    """
    # parametrize magnitudes m_i > 0; ||w||_1 = sum m, ||w||_2 = sqrt(sum m^2), A = l1/l2.
    # Use power-law magnitudes m_i = i^{-p}; sweep p to hit A_target.
    idx = np.arange(1, d+1)
    def A_of_p(p):
        m = idx.astype(float)**(-p)
        return m.sum()/np.sqrt((m**2).sum())
    # bisection on p in [0, large]; p=0 => uniform => A=sqrt(d); large p => concentrated => A->1
    lo, hi = 0.0, 40.0
    for _ in range(200):
        mid = 0.5*(lo+hi)
        if A_of_p(mid) > A_target:  # larger p -> smaller A
            lo = mid
        else:
            hi = mid
    p = 0.5*(lo+hi)
    m = idx.astype(float)**(-p)
    m = m / m.sum() * l1_target      # scale so ||w||_1 = l1_target
    w = m * sign_pattern
    return w

d = 30
M0 = 1.0
l1 = 4.0           # ||w||_1 fixed => eta/L1 = M0/||w||_1 = 0.25 fixed
sign_pattern = rng.choice([-1.0, 1.0], size=d)
R1 = M0 / l1
print(f"d={d}, M0={M0}, ||w||_1={l1}, first-order radius eta/L1 = {R1:.4f}")
print(f"anisotropy range [1, sqrt(d)=[{np.sqrt(d):.3f}]\n")

A_grid = np.linspace(1.5, np.sqrt(d)*0.98, 7)

for label, H_of in [
    ("T1 H=0 (no curvature)",           lambda w: np.zeros((d,d))),
    ("T2 aligned concave H=-c hatw hatwT", None),   # handled below
    ("T3 isotropic concave H=-c I",     None),
]:
    print("="*70)
    print(label)
    c = 3.0
    rows = []
    for A in A_grid:
        w = make_w(d, A, l1, sign_pattern)
        A_real = np.linalg.norm(w,1)/np.linalg.norm(w,2)
        if label.startswith("T1"):
            H = np.zeros((d,d))
        elif label.startswith("T2"):
            hatw = w/np.linalg.norm(w,2)
            H = -c * np.outer(hatw, hatw)
        else:
            H = -c * np.eye(d)
        r = true_radius_inf(M0, w, H)
        # second-order prediction along s=-sign(w): a=0.5 s^T H s
        s = -np.sign(w)
        Q = 0.5 * s @ (H @ s)
        if abs(Q) < 1e-12:
            r2 = R1
        else:
            a, b, cc = Q, l1, M0
            disc = b*b - 4*a*cc
            r2 = (b - np.sqrt(disc))/(2*a) if disc >= 0 else np.nan
        rows.append((A_real, r, r2, Q))
    print(f"{'A':>8} {'r_true':>10} {'r_2nd':>10} {'r/R1':>8} {'Q':>10}")
    for A_real, r, r2, Q in rows:
        print(f"{A_real:8.3f} {r:10.4f} {r2:10.4f} {r/R1:8.4f} {Q:10.4f}")
    # monotonicity check
    rr = [x[1] for x in rows]
    print(f"  radius monotone-decreasing in A? {all(rr[i]>=rr[i+1]-1e-3 for i in range(len(rr)-1))}")
    print(f"  radius spread (max-min)/R1 = {(max(rr)-min(rr))/R1:.4f}")
