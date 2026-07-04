#!/usr/bin/env python3
"""
Analysis for the attack-free early-stopping payoff experiment. Reads the per-checkpoint eval cache
(payoff_es_evals.json: clean, etaL1, test_robust, val_robust per epoch) and compares checkpoint-selection
criteria by the test-robust accuracy they DELIVER and their regret vs the oracle.

Selectors (each uses only info available without a test attack, except oracle/val for reference):
  final          : last epoch                                   (naive; = what you get with no early stop).
  clean          : argmax clean acc                             (attack-free baseline the panel flagged).
  etaL_argmax    : argmax eta/L1 past a warmup fraction         (attack-free, naive form).
  etaL_turnover  : stop when smoothed eta/L1 drops >delta below its post-warmup running max; take the
                   running-max epoch                            (attack-free, ours -- eta/L is the gauge-free
                                                                 robust-overfitting signal, so its turnover
                                                                 marks the robust peak).
  val_pgd        : argmax val-robust (PGD on a val split)       (the EXPENSIVE standard, Rice et al. 2020).
  oracle         : argmax test-robust                           (regret 0 reference).
The claim: under robust overfitting etaL_turnover >> clean/final and ~ val_pgd, at NO attack cost;
with no overfitting it never triggers, so it ties final (does no harm).

Run: PYTHONNOUSERSITE=1 ../env/cenv/bin/python payoff_analyze.py [cache.json]
"""
import sys, os, json
import numpy as np
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
WARMUP_FRAC = 0.30
DELTA = 0.05                                              # turnover: 5% drop below running max
SMOOTH = 3                                                # moving-average window on eta/L1


def _smooth(v, k):
    if k <= 1 or len(v) < k:
        return list(v)
    out = []
    for i in range(len(v)):
        lo = max(0, i - k // 2); hi = min(len(v), i + k // 2 + 1)
        out.append(float(np.mean(v[lo:hi])))
    return out


def selectors(traj):
    traj = sorted(traj, key=lambda r: r["epoch"])
    ep = [r["epoch"] for r in traj]
    emax = max(ep)
    warm_i = [i for i, e in enumerate(ep) if e >= WARMUP_FRAC * emax] or list(range(len(ep)))
    eta = _smooth([r["etaL1"] for r in traj], SMOOTH)
    # smoothed robust trajectory for a noise-robust oracle (raw PGD-20 on 2k pts bounces ~0.01);
    # delivered robustness of a *selected* checkpoint is still its own raw test_robust.
    trob_s = _smooth([r["test_robust"] for r in traj], SMOOTH)
    for i, r in enumerate(traj):
        r["_trob_s"] = trob_s[i]

    # turnover: walk post-warmup, track running max; stop the first time eta drops >delta below it
    run_max_i = warm_i[0]
    stop_i = len(traj) - 1                                # default: no trigger -> final epoch
    for i in warm_i:
        if eta[i] >= eta[run_max_i]:
            run_max_i = i
        elif eta[i] < (1 - DELTA) * eta[run_max_i]:
            stop_i = run_max_i                            # take the peak epoch, not the trigger epoch
            break

    picks = {
        "final":         len(traj) - 1,
        "clean":         int(np.argmax([r["clean"] for r in traj])),
        "etaL_argmax":   warm_i[int(np.argmax([eta[i] for i in warm_i]))],
        "etaL_turnover": stop_i,
        "val_pgd":       int(np.argmax([r["val_robust"] for r in traj])),
        "oracle":        int(np.argmax(trob_s)),                  # noise-robust oracle (smoothed)
    }
    return {k: traj[i] for k, i in picks.items()}, traj


def main():
    cache = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results", "payoff_es_evals.json")
    rows = json.load(open(cache))
    runs = defaultdict(list)
    for r in rows:
        runs[(r.get("run_id", "v2ckpt"), r.get("arm", "stdzero"), r["n_syn"], r["seed"])].append(r)

    SEL = ["final", "clean", "etaL_argmax", "etaL_turnover", "val_pgd"]
    reg = {k: [] for k in SEL}; reg_of = {k: [] for k in SEL}
    deliv = {k: [] for k in SEL}; deliv_of = {k: [] for k in SEL}
    print(f"warmup={WARMUP_FRAC} delta={DELTA} smooth={SMOOTH} | {len(runs)} runs\n")
    hdr = f"{'run (arm,syn,seed)':>24} {'ofit':>6} |" + "".join(f"{k:>14}" for k in SEL)
    print(hdr); print("-" * len(hdr))
    for key, traj in sorted(runs.items()):
        picks, tr = selectors(traj)
        oracle = picks["oracle"]["test_robust"]
        ofit = oracle - picks["final"]["test_robust"]
        line = f"{str(key[1:]):>24} {ofit:>+6.3f} |"
        for k in SEL:
            r = oracle - picks[k]["test_robust"]
            reg[k].append(r); deliv[k].append(picks[k]["test_robust"])
            if ofit > 0.015:
                reg_of[k].append(r); deliv_of[k].append(picks[k]["test_robust"])
            line += f"  ep{picks[k]['epoch']:>2} {r:>+5.3f}"
        print(line)

    def ci(v):
        v = np.array(v, float); m = v.mean()
        if len(v) < 2: return m, 0.0
        bs = [np.random.default_rng(s).choice(v, len(v)).mean() for s in range(3000)]
        return m, (np.percentile(bs, 97.5) - np.percentile(bs, 2.5)) / 2

    print(f"\n== mean REGRET vs oracle (all {len(runs)} runs) ==")
    for k in SEL:
        m, h = ci(reg[k]); print(f"   {k:>14}: {m:+.3f} +/- {h:.3f}   (delivered robust acc {np.mean(deliv[k]):.3f})")
    nof = len(reg_of["final"])
    print(f"\n== mean REGRET on the {nof} runs that robustly overfit (oracle-final > 0.015) ==")
    for k in SEL:
        m, h = ci(reg_of[k]); print(f"   {k:>14}: {m:+.3f} +/- {h:.3f}   (delivered {np.mean(deliv_of[k]):.3f})")
    if nof >= 1:
        print(f"\n== HEADLINE: delivered-robustness GAIN of attack-free eta/L over baselines, "
              f"on the {nof} overfitting runs (paired, no oracle needed) ==")
        gain_clean = np.array(deliv_of["etaL_turnover"]) - np.array(deliv_of["clean"])
        gain_final = np.array(deliv_of["etaL_turnover"]) - np.array(deliv_of["final"])
        vs_val = np.array(deliv_of["etaL_turnover"]) - np.array(deliv_of["val_pgd"])
        for lab, g in [("eta/L_turnover - clean", gain_clean), ("eta/L_turnover - final", gain_final),
                       ("eta/L_turnover - val_pgd(expensive)", vs_val)]:
            m, h = ci(g); print(f"   {lab:>36}: {m:+.3f} +/- {h:.3f}")


if __name__ == "__main__":
    main()
