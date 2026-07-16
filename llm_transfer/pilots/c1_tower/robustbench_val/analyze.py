"""Cross-model correlation analysis for the anisotropy -> robustness hypothesis.

Reads results.json and reports:
  - per-model table sorted by robust acc
  - Spearman(A, robust_acc), Spearman(eta/L1, robust_acc), Spearman(clean, robust)
  - partial Spearman(A, robust | clean) and partial Spearman(A, robust | eta/L1)
  - jackknife drop-1 range of the main Spearman(A, robust)
Verdict: does LOWER A predict HIGHER robust acc (as on CLIP), independent of clean?
"""
import os, json, sys
import numpy as np
from scipy.stats import spearmanr, rankdata

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results.json")
OFFICIAL = os.path.join(HERE, "official.json")


def load_official():
    if os.path.exists(OFFICIAL):
        return json.load(open(OFFICIAL))
    return {}


def partial_spearman(a, b, c):
    """Spearman partial correlation of a,b controlling for c.
    Computed as Pearson correlation of the residuals of rank(a)~rank(c) and
    rank(b)~rank(c). This is the standard rank-based partial correlation."""
    ra, rb, rc = rankdata(a), rankdata(b), rankdata(c)

    def resid(y, x):
        x1 = np.column_stack([np.ones_like(x), x])
        beta, *_ = np.linalg.lstsq(x1, y, rcond=None)
        return y - x1 @ beta
    ea, eb = resid(ra, rc), resid(rb, rc)
    if ea.std() < 1e-12 or eb.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(ea, eb)[0, 1])


def main():
    with open(RESULTS) as f:
        R = json.load(f)
    off = load_official()
    rows = list(R.values())
    rows.sort(key=lambda d: d["robust_acc"])
    n = len(rows)

    name = [r["name"] for r in rows]
    clean = np.array([r["clean_acc"] for r in rows])
    robust = np.array([r["robust_acc"] for r in rows])
    A = np.array([r["A"] for r in rows])
    eta = np.array([r["eta_over_L1"] for r in rows])
    off_aa = np.array([off.get(r["name"], {}).get("autoattack_acc", np.nan) / 100.0
                       for r in rows])

    print("=" * 116)
    print(f"PER-MODEL TABLE (n={n}), sorted by Linf robust acc "
          f"(APGD-CE eps=8/255, {rows[0].get('apgd_iters','?')} iters)")
    print("=" * 116)
    hdr = (f"{'model':<36}{'clean':>8}{'robust':>9}{'offAA':>8}"
           f"{'A':>9}{'A/sqrtd':>9}{'eta/L1':>10}")
    print(hdr)
    print("-" * 116)
    for r, oa in zip(rows, off_aa):
        oa_s = f"{oa:>8.3f}" if not np.isnan(oa) else f"{'--':>8}"
        print(f"{r['name']:<36}{r['clean_acc']:>8.3f}{r['robust_acc']:>9.3f}{oa_s}"
              f"{r['A']:>9.2f}{r['A']/r['sqrt_d']:>9.3f}{r['eta_over_L1']:>10.5f}")
    print("-" * 116)
    # validity: does our APGD robust acc rank like official AutoAttack?
    mask = ~np.isnan(off_aa)
    if mask.sum() >= 4:
        s_val = spearmanr(robust[mask], off_aa[mask])[0]
        print(f"VALIDITY CHECK: Spearman(my APGD robust, official AutoAttack) "
              f"= {s_val:+.3f} over {int(mask.sum())} models "
              f"(should be ~+1 if my attack ranks correctly)")

    if n < 4:
        print(f"\nOnly {n} models — need >=4 for meaningful correlation. "
              "Waiting for more downloads.")
        return

    # main correlations
    s_A, p_A = spearmanr(A, robust)
    s_eta, p_eta = spearmanr(eta, robust)
    s_clean, p_clean = spearmanr(clean, robust)
    s_A_clean = spearmanr(A, clean)[0]

    print("\nSPEARMAN CORRELATIONS with Linf robust acc:")
    print(f"  Spearman(A,       robust) = {s_A:+.3f}  (p={p_A:.3g})   "
          f"[hypothesis: NEGATIVE]")
    print(f"  Spearman(eta/L1,  robust) = {s_eta:+.3f}  (p={p_eta:.3g})   "
          f"[control, expect POSITIVE]")
    print(f"  Spearman(clean,   robust) = {s_clean:+.3f}  (p={p_clean:.3g})")
    print(f"  Spearman(A,       clean)  = {s_A_clean:+.3f}   "
          f"[how confounded A is with clean acc]")

    # A vs OFFICIAL AutoAttack robust acc (removes any attack-strength concern)
    if mask.sum() >= 4:
        s_A_off = spearmanr(A[mask], off_aa[mask])[0]
        pc_off_clean = partial_spearman(A[mask], off_aa[mask], clean[mask])
        print(f"\nCROSS-CHECK vs OFFICIAL AutoAttack (n={int(mask.sum())}):")
        print(f"  Spearman(A, officialAA)          = {s_A_off:+.3f}")
        print(f"  partial(A, officialAA | clean)   = {pc_off_clean:+.3f}")

    # partial correlations
    pc_clean = partial_spearman(A, robust, clean)
    pc_eta = partial_spearman(A, robust, eta)
    print("\nPARTIAL (rank) CORRELATIONS:")
    print(f"  partial(A, robust | clean)  = {pc_clean:+.3f}   "
          f"[A vs robust, removing clean-acc]")
    print(f"  partial(A, robust | eta/L1) = {pc_eta:+.3f}   "
          f"[A vs robust, removing eta/L1]")

    # bootstrap 95% CI on main Spearman(A, robust)
    rng = np.random.default_rng(0)
    boots = []
    for _ in range(5000):
        idx = rng.integers(0, n, n)
        if len(np.unique(A[idx])) < 3 or len(np.unique(robust[idx])) < 3:
            continue
        boots.append(spearmanr(A[idx], robust[idx])[0])
    boots = np.array(boots)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    print(f"\nBOOTSTRAP 95% CI on Spearman(A, robust): "
          f"[{lo:+.3f}, {hi:+.3f}]  (n_boot={len(boots)})")

    # jackknife drop-1 on main Spearman(A, robust)
    jk = []
    for i in range(n):
        idx = [j for j in range(n) if j != i]
        jk.append(spearmanr(A[idx], robust[idx])[0])
    jk = np.array(jk)
    worst_i = int(np.argmax(jk))  # dropping this makes corr least negative
    print("\nJACKKNIFE drop-1 of Spearman(A, robust):")
    print(f"  range [{jk.min():+.3f}, {jk.max():+.3f}]  "
          f"(full={s_A:+.3f}, median={np.median(jk):+.3f})")
    print(f"  most influential model (dropping it weakens most): "
          f"{name[worst_i]} -> {jk[worst_i]:+.3f}")

    # verdict
    print("\n" + "=" * 104)
    holds = (s_A < 0)
    indep = (pc_clean < 0) and (not np.isnan(pc_clean))
    strong = s_A <= -0.3
    print("VERDICT:")
    direction = "LOWER A => MORE robust" if s_A < 0 else "HIGHER A => more robust (OPPOSITE of CLIP)"
    print(f"  Spearman(A,robust)={s_A:+.3f}. Direction: {direction}.")
    print(f"  CLIP reference was Spearman(A,robust) = -0.65.")
    if holds and strong and indep:
        print("  => REPLICATES: anisotropy ranks robustness (lower A = more robust), "
              "and survives control for clean accuracy.")
    elif holds and indep:
        print("  => WEAK REPLICATION: correct sign and clean-independent, "
              "but weaker than CLIP.")
    elif holds and not indep:
        print("  => PARTIAL: correct sign overall, but the A->robust signal is "
              "largely explained by clean accuracy (partial|clean not negative).")
    else:
        print("  => DOES NOT REPLICATE: sign is wrong / not negative. "
              "The CLIP finding did not transfer to CIFAR-10 RobustBench.")
    print("=" * 104)


if __name__ == "__main__":
    main()
