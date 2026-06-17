#!/usr/bin/env python3
"""
Structural test of the corrected theory (training-free). Theory-aligned margins:
  Sep(Id)     : unconstrained linear margin in INPUT space  (raw hard-margin SVM, 1/||w||)
  Sep(Pi_inv) : invariant LINEAR margin via Theorem A closed form
                = 1/2 * gap of f_dc,  f_dc(x) = (1/sqrt d) sum_i x_i      (input space)
  Sep(Psi)    : power-spectrum invariant margin eta_Psi (SVM in |FFT|^2 space),
                report eta_Psi/L_Psi as input-space robust-radius proxy.
Degenerate/non-separable features return 0 (e.g. dot power spectrum: |FFT|^2 is
sign/phase-blind so +e0 and -e0 are identical -> Sep(Psi)=0).

Corrected-theory predictions:
  DOT (base task +e0 vs -e0):  Sep(Id)=1 (FC advantage), Sep(Pi_inv)=1/sqrt(d)~0.125
       (linear-invariant collapse, Ge 2/sqrt(d) as 2*gamma_inv), Sep(Psi)=0 (PS sign-blind).
  FREQ-SPANS (Ge real odd/even):  Sep(Id)~0 and Sep(Pi_inv)~0 (zero-mean, orthogonal
       subspaces, not linearly separable), Sep(Psi)>0 (disjoint power-spectrum supports)
       -> only the power-spectrum (quadratic) invariant separates.  => "the RIGHT invariant
       feature, not invariance per se."
Run: paper/env/cenv/bin/python paper/experiments/structural_margins.py
"""
import numpy as np
from sklearn.svm import SVC

rng = np.random.RandomState(0)
d = 64
SQ = np.sqrt(d)

def shifts(v): return np.stack([np.roll(v, s) for s in range(d)], 0)

# ---------- datasets ----------
def ds_dot():
    e = np.zeros(d); e[0] = 1.0
    X = np.stack([e, -e], 0); y = np.array([1, 0])   # base task (2 images), like Ge
    return X, y, "DOT (+e0 / -e0)"

def ds_freq_single(k1=3, k2=7, n=64):
    t = np.arange(d); rows, ys = [], []
    for k, lab in [(k1,1),(k2,0)]:
        for _ in range(n):
            ph = rng.uniform(0,2*np.pi); a = rng.uniform(0.7,1.3)
            rows.append(a*np.cos(2*np.pi*k*t/d+ph)); ys.append(lab)
    return np.stack(rows,0), np.array(ys), f"FREQ-SINGLE (k={k1}/{k2})"

def ds_freq_spans(n=128):
    """Ge sec5.2 real: class+ = random combo of ODD freqs, class- = EVEN freqs."""
    t = np.arange(d); rows, ys = [], []
    odd = [k for k in range(1, d//2) if k % 2 == 1]
    even= [k for k in range(1, d//2) if k % 2 == 0]
    for ks, lab in [(odd,1),(even,0)]:
        for _ in range(n):
            x = np.zeros(d)
            for k in ks:
                x += rng.randn()*np.cos(2*np.pi*k*t/d) + rng.randn()*np.sin(2*np.pi*k*t/d)
            x /= (np.linalg.norm(x)+1e-12)
            rows.append(x); ys.append(lab)
    return np.stack(rows,0), np.array(ys), "FREQ-SPANS (odd/even, Ge real)"

# ---------- margins ----------
def svm_margin(F, y):
    """raw hard-margin geometric margin 1/||w||; 0 if degenerate or not (linearly) separable."""
    F = np.asarray(F, float)
    if F.shape[0] < 2 or np.allclose(F.std(0), 0):
        return 0.0
    clf = SVC(kernel="linear", C=1e6, max_iter=100000).fit(F, y)
    if clf.score(F, y) < 0.999:
        return 0.0
    return 1.0 / (np.linalg.norm(clf.coef_.ravel()) + 1e-12)

def sep_dc(X, y):
    """Theorem A: invariant linear input-space margin = 1/2 * gap of f_dc between classes."""
    fdc = X.sum(1) / SQ
    a, b = fdc[y == 1], fdc[y == 0]
    gap = max(a.min() - b.max(), b.min() - a.max())   # whichever orientation separates
    return max(gap, 0.0) / 2.0

def feat_ps(X): return np.abs(np.fft.rfft(X, axis=1))**2

def lipschitz_ps(X, trials=200):
    L = 0.0
    for _ in range(trials):
        x = X[rng.randint(len(X))]; v = rng.randn(d); v /= np.linalg.norm(v); eps = 1e-3
        L = max(L, np.linalg.norm(feat_ps((x+eps*v)[None])[0]-feat_ps(x[None])[0])/eps)
    return L

# ---------- run ----------
if __name__ == "__main__":
    print(f"d={d}  (1/sqrt(d)={1/SQ:.4f})\n")
    hdr = f"{'dataset':30s} {'Sep(Id)':>9s} {'Sep(Pi_inv=DC)':>15s} {'eta_Psi(PS)':>12s} {'L_Psi':>8s} {'etaPS/L':>9s}"
    print(hdr); print("-"*len(hdr))
    for ds in (ds_dot, ds_freq_single, ds_freq_spans):
        X, y, name = ds()
        s_id = svm_margin(X, y)
        s_dc = sep_dc(X, y)
        eta_ps = svm_margin(feat_ps(X), y)
        Lps = lipschitz_ps(X) if eta_ps > 0 else float("nan")
        ratio = (eta_ps/Lps) if eta_ps > 0 else 0.0
        print(f"{name:30s} {s_id:9.4f} {s_dc:15.4f} {eta_ps:12.4f} {Lps:8.2f} {ratio:9.4f}")
    print("\nExpected: DOT -> Sep(Id)=1, Sep(DC)~0.125 (=1/sqrt d), Sep(PS)=0 (sign-blind).")
    print("          FREQ -> Sep(Id)~0, Sep(DC)~0, Sep(PS)>0 (only power-spectrum invariant separates).")
