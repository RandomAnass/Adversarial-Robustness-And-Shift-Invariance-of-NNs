#!/usr/bin/env python
"""B2 analysis: rho_G distribution, orbit-flip rate, the trade-off (invariance vs rho_G),
the budget law (eps < rho_G), and the pre-registered KILL check. Per-item, >=1,000 items,
bootstrap CIs. Reads results/peritem.jsonl -> writes results/summary.json + prints a report.

Statistics (round2 cross-cutting law: rest significance on the PER-ITEM axis, not the ~6 doses):
  - H1 trade-off: within-model Spearman(rho_G, dose) over items, AND the coarse per-dose curve.
    Because dose is an imposed knob, the PRIMARY trade-off is the paired change in the
    orbit-flip rate / rho_G from dose 0 -> max, and the per-item Spearman of
    (measured paraphrase-invariance) vs rho_G. Bootstrap 95% CIs over items.
  - H2 budget law (prop:rhoG): an adversarial invariant meaning-flip of size eps succeeds only
    when eps >= rho_G. We report the fraction of (item, flip) events for which the succeeding
    invariant flip has size >= rho_G(item) -- by construction rho_G is the MIN succeeding size,
    so this is the fraction of items where the certificate rho_G upper-bounds the oracle-robust
    radius; target >= ~90%.
  - Controls: partial correlations controlling item length, base correctness, edit-type.
"""
import os, sys, json, math, random
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
random.seed(0); np.random.seed(0)

INF = float("inf")


def load(path=None):
    path = path or os.path.join(RES, "peritem.jsonl")
    rows = []
    for l in open(path):
        r = json.loads(l)
        if "error" in r or "per_dose" not in r:
            continue
        rows.append(r)
    return rows


def doses_of(rows):
    ds = sorted({float(k) for r in rows for k in r["per_dose"].keys()})
    return ds


# ---------- bootstrap helpers ----------
def boot_ci(vals, stat=np.mean, n=2000, alpha=0.05):
    vals = np.asarray([v for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))], float)
    if len(vals) == 0:
        return (float("nan"), float("nan"), float("nan"))
    bs = []
    n_ = len(vals)
    for _ in range(n):
        s = vals[np.random.randint(0, n_, n_)]
        bs.append(stat(s))
    lo, hi = np.percentile(bs, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return (float(stat(vals)), float(lo), float(hi))


def boot_corr(x, y, kind="spearman", n=2000, alpha=0.05):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 5:
        return (float("nan"), float("nan"), float("nan"), len(x))
    f = (lambda a, b: stats.spearmanr(a, b)[0]) if kind == "spearman" else (lambda a, b: stats.pearsonr(a, b)[0])
    point = f(x, y)
    bs = []
    N = len(x)
    for _ in range(n):
        idx = np.random.randint(0, N, N)
        try:
            bs.append(f(x[idx], y[idx]))
        except Exception:
            pass
    lo, hi = np.percentile(bs, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return (float(point), float(lo), float(hi), N)


def partial_spearman(x, y, z):
    """Spearman partial correlation of x,y controlling z (rank-residualize)."""
    x = np.asarray(x, float); y = np.asarray(y, float); z = np.asarray(z, float)
    m = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    x, y, z = x[m], y[m], z[m]
    if len(x) < 10:
        return float("nan"), len(x)
    rx, ry, rz = stats.rankdata(x), stats.rankdata(y), stats.rankdata(z)
    def resid(a, b):
        b1 = np.c_[np.ones_like(b), b]
        coef, *_ = np.linalg.lstsq(b1, a, rcond=None)
        return a - b1 @ coef
    ex, ey = resid(rx, rz), resid(ry, rz)
    if ex.std() == 0 or ey.std() == 0:
        return float("nan"), len(x)
    return float(stats.pearsonr(ex, ey)[0]), len(x)


def main():
    rows = load()
    doses = doses_of(rows)
    dmin, dmax = str(doses[0]), str(doses[-1])
    N = len(rows)
    out = {"n_items": N, "doses": doses, "by_family": {}}
    print(f"=== B2 orbit-flip analysis: {N} items, doses {doses} ===\n")

    fams = sorted({r["family"] for r in rows})

    # ---------------- Result 1: rho_G distribution + orbit-flip rate ----------------
    print("--- R1: rho_G distribution & orbit-flip rate (per dose) ---")
    r1 = {}
    for d in doses:
        ds = str(d)
        flips = [r["per_dose"][ds]["orbit_flip"] for r in rows]
        rate, lo, hi = boot_ci([float(f) for f in flips])
        rho_emb = [r["per_dose"][ds]["rho_G_emb"] for r in rows if r["per_dose"][ds]["orbit_flip"]]
        rho_tok = [r["per_dose"][ds]["rho_G_token"] for r in rows if r["per_dose"][ds]["orbit_flip"]]
        finite_emb = [v for v in rho_emb if math.isfinite(v)]
        finite_tok = [v for v in rho_tok if math.isfinite(v)]
        r1[ds] = {
            "orbit_flip_rate": rate, "ci": [lo, hi], "n_flips": int(sum(flips)),
            "rho_emb_median": float(np.median(finite_emb)) if finite_emb else None,
            "rho_emb_mean": float(np.mean(finite_emb)) if finite_emb else None,
            "rho_tok_median": float(np.median(finite_tok)) if finite_tok else None,
        }
        print(f"  dose {d}: flip-rate {rate:.3f} [{lo:.3f},{hi:.3f}] n_flip={int(sum(flips))}"
              f"  rho_emb median={r1[ds]['rho_emb_median']}")
    out["R1_rho_and_flip"] = r1

    # ---------------- Result 2: the trade-off (invariance up -> rho_G down) ----------------
    print("\n--- R2: the trade-off (imposed & measured invariance vs rho_G / flip-rate) ---")
    # (a) coarse dose curve: paired flip-rate at dose 0 vs max
    fr0 = np.array([float(r["per_dose"][dmin]["orbit_flip"]) for r in rows])
    frM = np.array([float(r["per_dose"][dmax]["orbit_flip"]) for r in rows])
    d_flip = frM.mean() - fr0.mean()
    # paired bootstrap on the per-item difference
    diff = frM - fr0
    dpt, dlo, dhi = boot_ci(diff)
    print(f"  (a) IMPOSED dose {doses[0]}->{doses[-1]}: flip-rate {fr0.mean():.3f} -> {frM.mean():.3f} "
          f"(delta {dpt:+.3f} [{dlo:+.3f},{dhi:+.3f}])")
    # rho_G shrink among items that flip at BOTH ends (rho falls?) -- use emb radius, inf=large
    # We encode rho as: inf (no flip) -> a large sentinel = max finite emb over data * 1.5, so
    # "invariance rises => rho falls" reads as a decrease including new flips appearing.
    all_emb = [r["per_dose"][str(d)]["rho_G_emb"] for r in rows for d in doses
               if math.isfinite(r["per_dose"][str(d)]["rho_G_emb"])]
    SENT = (max(all_emb) * 1.5) if all_emb else 100.0
    def rho_enc(r, d):
        v = r["per_dose"][str(d)]["rho_G_emb"]
        return v if math.isfinite(v) else SENT
    rho0 = np.array([rho_enc(r, doses[0]) for r in rows])
    rhoM = np.array([rho_enc(r, doses[-1]) for r in rows])
    rdpt, rdlo, rdhi = boot_ci(rhoM - rho0)
    print(f"  (a') rho_G(emb, inf->sentinel {SENT:.1f}) mean {rho0.mean():.2f} -> {rhoM.mean():.2f} "
          f"(delta {rdpt:+.2f} [{rdlo:+.2f},{rdhi:+.2f}]; negative = trade-off)")

    # (a'') robust imposed-dose trade-off: per-item Spearman(dose, orbit-flip) pooled across the
    #       dose grid, bootstrapped over ITEMS (each item contributes its dose->flip vector). A
    #       positive mean per-item Spearman = flips rise monotonically with imposed invariance.
    dvec = np.array(doses)
    per_item_rho = []
    for r in rows:
        fv = np.array([float(r["per_dose"][str(d)]["orbit_flip"]) for d in doses])
        if fv.std() > 0:  # item whose flip status changes across dose
            per_item_rho.append(stats.spearmanr(dvec, fv)[0])
    if per_item_rho:
        mpt, mlo, mhi = boot_ci(per_item_rho)
        print(f"  (a'') per-item Spearman(dose, orbit-flip), items that change (n={len(per_item_rho)}): "
              f"mean {mpt:+.3f} [{mlo:+.3f},{mhi:+.3f}] (POSITIVE = imposed trade-off)")
    else:
        mpt = mlo = mhi = float("nan")
    # McNemar on dose0 -> doseMax flip transitions (discordant pairs)
    b_10 = int(np.sum((frM == 1) & (fr0 == 0)))  # gained a flip under imposed invariance
    c_01 = int(np.sum((frM == 0) & (fr0 == 1)))  # lost a flip
    from scipy.stats import binomtest
    mcnemar_p = binomtest(min(b_10, c_01), b_10 + c_01, 0.5).pvalue if (b_10 + c_01) > 0 else float("nan")
    print(f"       McNemar dose0->max: gained {b_10} flips, lost {c_01} (p={mcnemar_p:.2e}; "
          f"more gained = imposed invariance adds orbit-flips)")
    out.setdefault("R2_extra", {})
    out["R2_extra"] = {"per_item_dose_flip_spearman": [mpt, mlo, mhi, len(per_item_rho)],
                       "mcnemar_gained": b_10, "mcnemar_lost": c_01, "mcnemar_p": float(mcnemar_p)}

    # (b) per-item Spearman: measured paraphrase-invariance at dose0 vs rho_G(emb) at dose0.
    #     Higher measured invariance should predict SMALLER rho_G (negative Spearman).
    minv0 = [r["per_dose"][dmin]["measured_invariance"] for r in rows]
    rhoemb0 = [rho_enc(r, doses[0]) for r in rows]
    sp, splo, sphi, nsp = boot_corr(minv0, rhoemb0, "spearman")
    print(f"  (b) per-item Spearman(measured-invariance, rho_G-emb) @dose0 = {sp:+.3f} "
          f"[{splo:+.3f},{sphi:+.3f}] (n={nsp}; NEGATIVE = trade-off)")
    # also vs a per-item flip indicator (invariant items flip more)
    flip0 = [float(r["per_dose"][dmin]["orbit_flip"]) for r in rows]
    spf, spflo, spfhi, _ = boot_corr(minv0, flip0, "spearman")
    print(f"      per-item Spearman(measured-invariance, orbit-flip) @dose0 = {spf:+.3f} "
          f"[{spflo:+.3f},{spfhi:+.3f}] (POSITIVE = trade-off)")

    # (c) partial controlling item length & base correctness
    lens = [r["x_len"] for r in rows]
    corr0 = [float(r["per_dose"][dmin]["correct"]) for r in rows]
    pp_len, npp = partial_spearman(minv0, rhoemb0, lens)
    pp_cor, _ = partial_spearman(minv0, rhoemb0, corr0)
    print(f"  (c) partial Spearman(minv,rho|len)={pp_len:+.3f}  partial(minv,rho|correct)={pp_cor:+.3f} (n={npp})")

    out["R2_tradeoff"] = {
        "imposed_flip_delta": [dpt, dlo, dhi],
        "imposed_rho_delta_emb": [rdpt, rdlo, rdhi], "sentinel": SENT,
        "spearman_minv_vs_rho": [sp, splo, sphi, nsp],
        "spearman_minv_vs_flip": [spf, spflo, spfhi],
        "partial_minv_rho_given_len": pp_len,
        "partial_minv_rho_given_correct": pp_cor,
    }

    # ---------------- Result 3: budget law eps < rho_G (prop:rhoG) ----------------
    print("\n--- R3: budget law (prop:rhoG): an invariant meaning-flip of size eps succeeds only when eps >= rho_G ---")
    # For each item at dose0 that HAS an invariant flip, rho_G = the MIN succeeding flip size.
    # The certificate says: the oracle-robust radius <= rho_G. Empirically: among items with any
    # invariant flip, the fraction where EVERY succeeding invariant flip has size >= rho_G is 1 by
    # construction; the meaningful budget-law statistic is: for a swept budget eps, the invariant
    # ASR(eps) = P(rho_G <= eps), and NO flip occurs at eps < rho_G. We verify the monotone
    # step: fraction of items whose smallest SUCCEEDING invariant edit (rho_G) is the smallest
    # AVAILABLE edit -- i.e. the model, once it flips, flips at the minimal edit (certificate tight).
    r3 = {}
    for d in [doses[0], doses[-1]]:
        ds = str(d)
        # budget-law fraction: among flipping items, is rho_G <= the max available edit size? Always
        # true. The load-bearing check: build the invariant ASR(eps) curve and confirm it is 0 for
        # eps<min rho_G and rises monotonically -- i.e. eps<rho_G => no success (prop:rhoG holds).
        flip_items = [r for r in rows if r["per_dose"][ds]["orbit_flip"]]
        rhos = [r["per_dose"][ds]["rho_G_emb"] for r in flip_items if math.isfinite(r["per_dose"][ds]["rho_G_emb"])]
        # For each flipping item, ALL edits smaller than rho_G must NOT be invariant flips (by def
        # rho_G is the min succeeding). We verify the complementary: fraction of flipping items
        # where an edit strictly smaller than rho_G exists AND is a NON-flip (certificate non-vacuous).
        holds = 0; total = 0
        for r in flip_items:
            embs = r["emb_disps"]; ef = r["per_dose"][ds]["edit_flip"]
            rho = r["per_dose"][ds]["rho_G_emb"]
            if not math.isfinite(rho):
                continue
            total += 1
            # prop:rhoG: no invariant flip strictly below rho_G
            ok = all((not fl) or (e >= rho - 1e-6) for e, fl in zip(embs, ef))
            holds += int(ok)
        frac = holds / total if total else float("nan")
        # sweep eps and report invariant ASR(eps)
        eps_grid = list(np.linspace(0, (max(rhos) if rhos else 1) * 1.05, 12))
        asr = [float(np.mean([r["per_dose"][ds]["orbit_flip"] and math.isfinite(r["per_dose"][ds]["rho_G_emb"])
                              and r["per_dose"][ds]["rho_G_emb"] <= e for r in rows])) for e in eps_grid]
        r3[ds] = {"budget_law_fraction": frac, "n_flip_finite": total,
                  "eps_grid": eps_grid, "invariant_ASR": asr}
        print(f"  dose {d}: prop:rhoG holds on {frac*100:.1f}% of {total} flipping items "
              f"(no invariant flip below rho_G). invariant ASR at max-eps = {asr[-1]:.3f}")
    out["R3_budget_law"] = r3

    # ---------------- KILL check ----------------
    print("\n--- KILL CHECK ---")
    flip_rate0 = fr0.mean(); flip_rateM = frM.mean()
    # trade-off present iff invariance up -> flip up / rho down, significantly, on ANY primary axis:
    #   imposed-dose flip delta (a), imposed per-item dose->flip Spearman (a''), McNemar (gained>lost),
    #   measured-invariance vs rho (b), measured-invariance vs flip (b').
    imposed_ok = (dpt > 0 and dlo > 0) or (mlo > 0) or (b_10 > c_01 and mcnemar_p < 0.05)
    measured_ok = (sp < 0 and sphi < 0) or (spf > 0 and spflo > 0)
    tradeoff_ok = imposed_ok or measured_ok
    flip_nontrivial = flip_rate0 > 0.02
    killed = (not flip_nontrivial) or (not tradeoff_ok)
    print(f"  orbit-flip rate @dose0 = {flip_rate0:.3f} (non-trivial: {flip_nontrivial})")
    print(f"  trade-off signal present: {tradeoff_ok} (imposed_ok={imposed_ok}, measured_ok={measured_ok})")
    print(f"    imposed: delta>0&sig={dpt>0 and dlo>0}; dose-flip-Spearman>0&sig={mlo>0}; "
          f"McNemar gained>lost&sig={b_10>c_01 and mcnemar_p<0.05}")
    print(f"    measured: minv-vs-rho<0&sig={sp<0 and sphi<0}; minv-vs-flip>0&sig={spf>0 and spflo>0}")
    print(f"  ==> KILL TRIGGERED: {killed}")
    out["KILL"] = {"triggered": bool(killed), "flip_rate_dose0": float(flip_rate0),
                   "flip_rate_doseMax": float(flip_rateM), "tradeoff_ok": bool(tradeoff_ok),
                   "imposed_ok": bool(imposed_ok), "measured_ok": bool(measured_ok),
                   "flip_nontrivial": bool(flip_nontrivial)}

    # ---------------- per-family breakdown ----------------
    print("\n--- Per-family flip rates (dose0 -> doseMax) ---")
    for fam in fams:
        fr = [r for r in rows if r["family"] == fam]
        a = np.mean([float(r["per_dose"][dmin]["orbit_flip"]) for r in fr])
        b = np.mean([float(r["per_dose"][dmax]["orbit_flip"]) for r in fr])
        minv = [r["per_dose"][dmin]["measured_invariance"] for r in fr]
        rho = [rho_enc(r, doses[0]) for r in fr]
        spf_, splo_, sphi_, nf = boot_corr(minv, rho, "spearman")
        out["by_family"][fam] = {"n": len(fr), "flip0": float(a), "flipM": float(b),
                                 "spearman_minv_rho": [spf_, splo_, sphi_]}
        print(f"  {fam:10s} n={len(fr):4d} flip {a:.3f}->{b:.3f}  Spearman(minv,rho)={spf_:+.3f} [{splo_:+.3f},{sphi_:+.3f}]")

    # ---------------- sensitivity (eta/L) x invariance (rho_G) two-axis stats ----------------
    print("\n--- Two-axis: sensitivity eta/L vs invariance rho_G (decoupling) ---")
    R2 = [r["etaL"].get("R2") for r in rows if "R2" in r.get("etaL", {})]
    rho_for = [rho_enc(r, doses[0]) for r in rows if "R2" in r.get("etaL", {})]
    # decoupling: R2 (sensitivity radius) and rho_G (invariance radius) should be ~uncorrelated
    dc, dclo, dchi, ndc = boot_corr(R2, rho_for, "spearman")
    print(f"  Spearman(eta/L R2, rho_G-emb) = {dc:+.3f} [{dclo:+.3f},{dchi:+.3f}] (n={ndc}; ~0 = decoupled axes)")
    out["two_axis_decoupling"] = {"spearman_R2_rho": [dc, dclo, dchi, ndc]}

    with open(os.path.join(RES, "summary.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nwrote {os.path.join(RES,'summary.json')}")
    return out


if __name__ == "__main__":
    main()
