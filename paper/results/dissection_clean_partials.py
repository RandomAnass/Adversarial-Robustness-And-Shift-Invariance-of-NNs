"""Reviewer-requested clean-accuracy partial correlations for the capacity-matched dissection
(R2: the clean-acc control was done for RobustBench but not for the dissection arms).
Standard-training dissection: target = L2 robust radius rr_l2, predictor = eta/L (L2), also consistency.
Adversarial-training dissection: target = AutoAttack Linf robust acc, predictor = threat-matched
eta/L1 = margin/L1, also consistency. Partial out clean accuracy. Aggregate seeds -> arm x width
cells and report the EFFECTIVE n (cells), per R2's effective-sample-size point. No GPU."""
import json, os
import numpy as np
from scipy import stats
from collections import defaultdict

RES = os.path.dirname(os.path.abspath(__file__))

def cellmeans(results, target_key, predictor_fn, clean_key="clean", consist_key="consist"):
    """Aggregate per-seed results to (arm,width) cell means. predictor_fn(row)->eta/L value."""
    cells = defaultdict(list)
    for r in results:
        cells[(r["arm"], r["w"])].append(r)
    arms, etaL, cons, tgt, clean = [], [], [], [], []
    for (arm, w), rs in sorted(cells.items()):
        arms.append(f"{arm}-{w}")
        etaL.append(np.mean([predictor_fn(r) for r in rs]))
        cons.append(np.mean([r[consist_key] for r in rs]))
        tgt.append(np.mean([r[target_key] for r in rs]))
        clean.append(np.mean([r[clean_key] for r in rs]))
    return arms, np.array(etaL), np.array(cons), np.array(tgt), np.array(clean)

def partial(x, y, z):
    """Pearson partial corr of x,y controlling z (single control)."""
    from numpy.linalg import lstsq
    Z = np.column_stack([z, np.ones(len(z))])
    rx = x - Z @ lstsq(Z, x, rcond=None)[0]
    ry = y - Z @ lstsq(Z, y, rcond=None)[0]
    r, _ = stats.pearsonr(rx, ry)
    n = len(x); t = r*np.sqrt((n-3)/(1-r*r)) if abs(r) < 1 else np.inf
    p = 2*stats.t.sf(abs(t), n-3)
    return r, p

def report(tag, arms, etaL, cons, tgt, clean, etaL_name):
    n = len(arms)
    print(f"\n== {tag} (effective n = {n} arm×width cells; seeds aggregated) ==")
    print(f"  cells: {arms}")
    print(f"  clean-acc range across arms: [{clean.min():.3f}, {clean.max():.3f}]  (spread = {clean.max()-clean.min():.3f})")
    print(f"  Pearson({etaL_name}, target)            = {stats.pearsonr(etaL, tgt)[0]:+.3f}")
    pr, pp = partial(etaL, tgt, clean)
    print(f"  partial({etaL_name}, target | clean)    = {pr:+.3f}  p={pp:.3f}")
    print(f"  Spearman(consistency, target)         = {stats.spearmanr(cons, tgt).correlation:+.3f}")
    cr, cp = partial(cons, tgt, clean)
    print(f"  partial(consistency, target | clean)  = {cr:+.3f}  p={cp:.3f}")
    print(f"  (context) Spearman(clean, target)     = {stats.spearmanr(clean, tgt).correlation:+.3f}")

# ---- STANDARD-training dissection: target = L2 robust radius ----
d = json.load(open(os.path.join(RES, "cifar_dissection_full_20260617_102535.json")))
arms, etaL, cons, tgt, clean = cellmeans(d["results"], "rr_l2", lambda r: r["dec_etaL"])
report("STANDARD dissection: eta/L (L2) vs L2 robust radius", arms, etaL, cons, tgt, clean, "eta/L2")

# ---- ADVERSARIAL-training dissection: target = AutoAttack Linf robust acc, threat-matched eta/L1 ----
d2 = json.load(open(os.path.join(RES, "at_cifar_linf_full10k_20260623_185505.json")))
r0 = d2["results"][0]
print("\n[AT results row keys]:", [k for k in r0.keys()])
# threat-matched eta/L1 = margin / L1 ; target = AutoAttack Linf
tgt_key = "aa_Linf_8_255" if "aa_Linf_8_255" in r0 else [k for k in r0 if "aa_Linf" in k][0]
def etaL1_fn(r):
    if "dec_etaL1" in r: return r["dec_etaL1"]
    m = r.get("margin", r.get("dec_margin")); l1 = r.get("L1", r.get("dec_L1"))
    return m / l1
arms2, etaL2, cons2, tgt2, clean2 = cellmeans(d2["results"], tgt_key, etaL1_fn)
report("AT dissection: threat-matched eta/L1 vs AutoAttack Linf robust acc", arms2, etaL2, cons2, tgt2, clean2, "eta/L1")
