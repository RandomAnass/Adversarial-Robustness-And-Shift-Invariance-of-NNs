"""Reviewer-requested strengthening of the RobustBench anisotropy result.
Addresses: (1) model-size / architecture-family confound; (2) within-family ranking;
(3) held-out predictive validity of A beyond eta/L1 (falsifies "free constant C is unfalsifiable");
(4) deficit-law C stability across random splits.
Uses OFFICIAL AutoAttack accuracy (from official.json) as the robustness target where available,
which also answers the in-house-vs-official-AA concern. No GPU. Firsthand, reproducible."""
import json, os, re
import numpy as np
from scipy import stats

R = os.path.dirname(os.path.abspath(__file__))
res = json.load(open(os.path.join(R, "results.json")))
off = json.load(open(os.path.join(R, "official.json")))

def parse_arch(name, arch_str):
    """Return (family, depth, width, param_proxy). param_proxy ~ depth*width^2 for WRN."""
    s = (arch_str or "") + " " + name
    m = re.search(r'(\d+)[_-](\d+)', name)  # e.g. WRN70_16, 28_10
    if re.search(r'WideResNet|WRN', s, re.I) or (m and int(m.group(1)) >= 28):
        if m:
            d, w = int(m.group(1)), int(m.group(2))
        else:
            d, w = 28, 10  # RobustBench default WRN-28-10
        return ("WRN", d, w, d * w * w)
    if re.search(r'PreActResNet-?18|ResNet-?18|RN18|R18', s, re.I):
        return ("RN18", 18, 1, 18 * 1 * 1 * 40)  # ~ small; scaled so it ranks below WRNs
    if re.search(r'ResNet-?50|RN50', s, re.I):
        return ("RN50", 50, 1, 50 * 40)
    # default assume WRN-28-10 (most common RobustBench Linf CIFAR-10 arch)
    return ("WRN?", 28, 10, 28 * 100)

rows = []
for name, v in res.items():
    o = off.get(name, {})
    arch = o.get("architecture")
    aa = o.get("autoattack_acc")  # official AA robust acc (percentage or fraction?)
    fam, d, w, psize = parse_arch(name, arch)
    rows.append(dict(name=name, A=v["A"], etaL1=v["eta_over_L1"], clean=v["clean_acc"],
                     rob_inhouse=v["robust_acc"], rob_off=aa, arch=arch, fam=fam,
                     depth=d, width=w, psize=psize))

# normalize official AA to fraction if it looks like a percentage
offvals = [r["rob_off"] for r in rows if r["rob_off"] is not None]
if offvals and max(offvals) > 1.5:
    for r in rows:
        if r["rob_off"] is not None:
            r["rob_off"] = r["rob_off"] / 100.0
print(f"n models = {len(rows)}; with official AA = {sum(r['rob_off'] is not None for r in rows)}")
print("families:", {f: sum(r['fam']==f for r in rows) for f in set(r['fam'] for r in rows)})

# robustness target: prefer official AA, fall back to in-house
for r in rows:
    r["rob"] = r["rob_off"] if r["rob_off"] is not None else r["rob_inhouse"]

def arr(key, subset=None):
    return np.array([r[key] for r in (subset or rows)])

def partial_spearman(x, y, controls):
    """Spearman partial correlation of x,y controlling for columns in controls (rank-residual method)."""
    from numpy.linalg import lstsq
    rx = stats.rankdata(x); ry = stats.rankdata(y)
    Z = np.column_stack([stats.rankdata(c) for c in controls] + [np.ones(len(x))])
    rxr = rx - Z @ lstsq(Z, rx, rcond=None)[0]
    ryr = ry - Z @ lstsq(Z, ry, rcond=None)[0]
    r, _ = stats.pearsonr(rxr, ryr)
    n, k = len(x), len(controls)
    # p via t-approx
    if abs(r) < 1:
        t = r*np.sqrt((n-2-k)/(1-r*r)); p = 2*stats.t.sf(abs(t), n-2-k)
    else: p = 0.0
    return r, p

# ---- FULL PANEL (n=30, includes Standard) ----
A_all, rob_all, clean_all, eta_all, sz_all = arr("A"), arr("rob"), arr("clean"), arr("etaL1"), np.log(arr("psize"))
print("\n== FULL PANEL (n=30, official AA target) ==")
print(f"  Spearman(A, robust)                 = {stats.spearmanr(A_all, rob_all).correlation:+.3f}")
print(f"  partial(A, robust | clean)          = {partial_spearman(A_all, rob_all, [clean_all])[0]:+.3f}  p={partial_spearman(A_all, rob_all, [clean_all])[1]:.1e}")
print(f"  partial(A, robust | clean, size)    = {partial_spearman(A_all, rob_all, [clean_all, sz_all])[0]:+.3f}  p={partial_spearman(A_all, rob_all, [clean_all, sz_all])[1]:.1e}")
print(f"  partial(A, robust | clean, etaL1)   = {partial_spearman(A_all, rob_all, [clean_all, eta_all])[0]:+.3f}")
print(f"  partial(A, robust | clean,size,eta) = {partial_spearman(A_all, rob_all, [clean_all, sz_all, eta_all])[0]:+.3f}")
print(f"  (control) Spearman(size, robust)    = {stats.spearmanr(sz_all, rob_all).correlation:+.3f}")
print(f"  (control) Spearman(A, size)         = {stats.spearmanr(A_all, sz_all).correlation:+.3f}")

# ---- ROBUST-ONLY (drop Standard / non-robust) ----
robust_rows = [r for r in rows if r["rob"] > 0.05]
Ar, robr, cleanr, szr = arr("A", robust_rows), arr("rob", robust_rows), arr("clean", robust_rows), np.log(arr("psize", robust_rows))
print(f"\n== ROBUST-ONLY (n={len(robust_rows)}) ==")
print(f"  Spearman(A, robust)               = {stats.spearmanr(Ar, robr).correlation:+.3f}")
print(f"  partial(A, robust | clean)        = {partial_spearman(Ar, robr, [cleanr])[0]:+.3f}")
print(f"  partial(A, robust | clean, size)  = {partial_spearman(Ar, robr, [cleanr, szr])[0]:+.3f}")

# ---- WITHIN-FAMILY (WRN only) ----
wrn = [r for r in rows if r["fam"].startswith("WRN") and r["rob"] > 0.05]
Aw, robw = arr("A", wrn), arr("rob", wrn)
print(f"\n== WITHIN-FAMILY WRN (n={len(wrn)}) ==")
print(f"  Spearman(A, robust)               = {stats.spearmanr(Aw, robw).correlation:+.3f}  p={stats.spearmanr(Aw, robw).pvalue:.1e}")
print(f"  partial(A, robust | width)        = {partial_spearman(Aw, robw, [arr('width', wrn)])[0]:+.3f}")

# ---- HELD-OUT PREDICTIVE VALIDITY: does A improve robust prediction beyond eta/L1? (LOO) ----
# rank-linear model on robust-only panel
from numpy.linalg import lstsq
def loo_rank_pred(feat_keys, panel):
    y = stats.rankdata(arr("rob", panel)); n = len(panel)
    X = np.column_stack([stats.rankdata(arr(k, panel)) for k in feat_keys] + [np.ones(n)])
    preds = np.zeros(n)
    for i in range(n):
        tr = [j for j in range(n) if j != i]
        beta = lstsq(X[tr], y[tr], rcond=None)[0]
        preds[i] = X[i] @ beta
    return stats.spearmanr(preds, y).correlation, np.mean((preds - y)**2)
sp_eta, mse_eta = loo_rank_pred(["etaL1"], robust_rows)
sp_both, mse_both = loo_rank_pred(["etaL1", "A"], robust_rows)
print(f"\n== HELD-OUT (LOO) PREDICTION of robust acc, ROBUST-ONLY (n={len(robust_rows)}) ==")
print(f"  features [eta/L1]     : LOO Spearman(pred,true)={sp_eta:+.3f}  MSE={mse_eta:.2f}")
print(f"  features [eta/L1, A]  : LOO Spearman(pred,true)={sp_both:+.3f}  MSE={mse_both:.2f}")
print(f"  -> adding A changes LOO MSE by {100*(mse_both-mse_eta)/mse_eta:+.1f}%  (negative = A helps out-of-sample)")

# ---- DEFICIT-LAW C STABILITY across random splits ----
# fit rob_proxy ~ (etaL1)/(1+C*A). Use robust-only; robustness proxy = rob (monotone in radius).
# 1-param fit of C on each random half, report stability.
rng = np.random.RandomState(0)
def fit_C(idx):
    e, a, y = arr("etaL1", [robust_rows[i] for i in idx]), arr("A", [robust_rows[i] for i in idx]), arr("rob", [robust_rows[i] for i in idx])
    # minimize sum( (y - k*e/(1+C*a))^2 ) over k>0,C>0 ; grid then report C
    best = (1e9, None, None)
    for C in np.linspace(0.01, 2.0, 200):
        pred = e / (1 + C*a)
        k = np.dot(pred, y)/np.dot(pred, pred)  # closed-form scale
        r = np.sum((y - k*pred)**2)
        if r < best[0]: best = (r, C, k)
    return best[1]
n = len(robust_rows); Cs = []
for _ in range(200):
    idx = rng.choice(n, n//2, replace=False)
    Cs.append(fit_C(idx))
Cs = np.array(Cs)
print(f"\n== DEFICIT-LAW C STABILITY (fit on random halves, robust-only) ==")
print(f"  C = {Cs.mean():.2f} +/- {Cs.std():.2f}  (CV = {Cs.std()/Cs.mean():.2f})  [stable => not an overfit free knob]")
print(f"  full-panel C = {fit_C(list(range(n))):.2f}")
