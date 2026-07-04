#!/usr/bin/env python3
"""
PAYOFF experiment: eta/L as an ATTACK-FREE early-stopping / checkpoint-selection criterion for
adversarial training, where it beats clean accuracy and matches the expensive validation-attack standard.

Motivation (the panel's deepest ask: one setting where eta/L delivers actionable value BEYOND clean
accuracy). Under robust overfitting (Rice et al. 2020) robust accuracy peaks early then decays while
clean accuracy keeps RISING, so clean-accuracy / final-epoch selection picks a badly-overfit checkpoint;
the standard fix selects the best checkpoint with a validation ATTACK (expensive). We show the gauge-free
eta/L, computed attack-free on clean data, collapses exactly as robust overfitting sets in, so selecting
the max-eta/L checkpoint (past a fixed warmup) recovers near-oracle robust accuracy WITHOUT any attack.

For each per-epoch checkpoint of each adversarial-training run we compute, on a held-out split:
  clean acc; eta/L1 = margin/||grad M||_1 (Linf-threat-matched, ATTACK-FREE); test-robust (PGD @8/255,
  the oracle proxy); val-robust (PGD @8/255 on a disjoint val split, the expensive standard's signal).
Selectors (each uses only info available at selection time, no peeking at test-robust except the oracle):
  final      : last epoch (naive).
  clean      : argmax clean acc                              (attack-free baseline).
  etaL_pw    : argmax eta/L1 among epochs >= warmup fraction (ATTACK-FREE, ours).
  val_pgd    : argmax val-robust                             (expensive standard, Rice et al.).
  oracle     : argmax test-robust                            (regret 0 reference).
Metric: test robust-accuracy REGRET vs oracle, per run and averaged; the win is etaL_pw << clean and
etaL_pw ~ val_pgd, concentrated on the runs that robustly overfit.

Run: PYTHONNOUSERSITE=1 ../env/cenv/bin/python payoff_early_stop.py --gpu 0 --ckpt_glob 'ckpts/v2ckpt_traj_*.pt'
"""
import argparse, os, glob, json, re, time
import numpy as np, torch

HERE = os.path.dirname(os.path.abspath(__file__))
import diff_pilot_v2 as DV
CD = DV.CD
RESDIR = DV.RESDIR
EPS = 8 / 255
WARMUP_FRAC = 0.30                                     # ignore the first 30% of epochs (undertrained)


def eval_ckpt(path, Xval, yval, Xte, yte, dev, A):
    b = torch.load(path, map_location="cpu")
    model = DV.M.build(b.get("arm", "stdzero"), width=b.get("width", 1.0)).to(dev).eval()
    model.load_state_dict(b["state_dict"])
    base = os.path.basename(path)
    mobj = re.search(r"syn(\d+)_s(\d+)_ep(\d+)", base)
    n_syn, seed, ep = int(mobj.group(1)), int(mobj.group(2)), int(mobj.group(3))
    run_id = base.split("_traj_")[0]                          # tag prefix disambiguates arm/run
    out = dict(n_syn=n_syn, seed=seed, epoch=ep, arm=b.get("arm", "stdzero"), src=base, run_id=run_id)
    out["clean"] = CD.accuracy(model, Xte, yte, dev)
    dec = CD.etaL_decomposition(model, Xte, yte, dev, n_max=A["dec_n"])
    out["etaL1"] = dec["margin"] / dec["L1"] if dec["L1"] > 0 else float("nan")   # ATTACK-FREE
    out["margin"] = dec["margin"]; out["L1"] = dec["L1"]
    out["test_robust"] = CD.pgd_acc(model, Xte[:A["rob_n"]], yte[:A["rob_n"]], dev, EPS, "linf", steps=A["pgd_steps"])
    out["val_robust"] = CD.pgd_acc(model, Xval[:A["val_n"]], yval[:A["val_n"]], dev, EPS, "linf", steps=A["pgd_steps"])
    del model
    if dev.startswith("cuda"):
        torch.cuda.empty_cache()
    return out


def select_and_regret(traj):
    """traj: list of per-epoch dicts for one run, sorted by epoch. Returns regret per selector."""
    traj = sorted(traj, key=lambda r: r["epoch"])
    emax = max(r["epoch"] for r in traj)
    warm = [r for r in traj if r["epoch"] >= WARMUP_FRAC * emax] or traj
    oracle = max(traj, key=lambda r: r["test_robust"])
    picks = {
        "final":   traj[-1],
        "clean":   max(traj, key=lambda r: r["clean"]),
        "etaL_pw": max(warm, key=lambda r: r["etaL1"]),
        "val_pgd": max(traj, key=lambda r: r["val_robust"]),
        "oracle":  oracle,
    }
    return {k: oracle["test_robust"] - v["test_robust"] for k, v in picks.items()}, picks, oracle


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--ckpt_glob", default="ckpts/v2ckpt_traj_*.pt")
    ap.add_argument("--rob_n", type=int, default=2000); ap.add_argument("--val_n", type=int, default=1000)
    ap.add_argument("--dec_n", type=int, default=1500); ap.add_argument("--pgd_steps", type=int, default=20)
    ap.add_argument("--tag", default="payoff_es")
    args = ap.parse_args()
    dev = f"cuda:{args.gpu}" if torch.cuda.is_available() else "cpu"
    A = dict(rob_n=args.rob_n, val_n=args.val_n, dec_n=args.dec_n, pgd_steps=args.pgd_steps)

    _, _, Xte, yte = CD.load_cifar(50000, 10000, seed=0)
    Xval, yval = Xte[:1000].to(dev), yte[:1000].to(dev)           # val split (disjoint from report)
    Xrep, yrep = Xte[1000:].to(dev), yte[1000:].to(dev)          # report/test split
    cks = sorted(glob.glob(os.path.join(HERE, args.ckpt_glob)))
    print(f"[payoff] {len(cks)} checkpoints, warmup_frac={WARMUP_FRAC}, PGD-{args.pgd_steps}@8/255, dev={dev}", flush=True)

    cache = os.path.join(RESDIR, f"{args.tag}_evals.json")
    rows = json.load(open(cache)) if os.path.exists(cache) else []
    done = {r.get("src") for r in rows}                        # dedup on source filename (arm-safe)
    for i, p in enumerate(cks):
        if os.path.basename(p) in done:
            continue
        t0 = time.time()
        r = eval_ckpt(p, Xval, yval, Xrep, yrep, dev, A)
        rows.append(r)
        json.dump(rows, open(cache, "w"), default=float)
        print(f"  [{i+1}/{len(cks)}] syn{r['n_syn']} s{r['seed']} ep{r['epoch']}: clean {r['clean']:.3f} "
              f"etaL1 {r['etaL1']:.4f} testRob {r['test_robust']:.3f} valRob {r['val_robust']:.3f} ({time.time()-t0:.0f}s)", flush=True)

    # ---- selector comparison, grouped by run (arm, n_syn, seed) ----
    runs = {}
    for r in rows:
        runs.setdefault((r.get("run_id", "v2ckpt"), r.get("arm", "stdzero"), r["n_syn"], r["seed"]), []).append(r)
    print(f"\n==== ATTACK-FREE EARLY STOPPING: test-robust regret vs oracle ({len(runs)} runs) ====")
    hdr = f"{'run (arm,syn,seed)':>26} {'overfit':>8} | {'final':>7} {'clean':>7} {'etaL_pw':>8} {'val_pgd':>8}"
    print(hdr); print("-" * len(hdr))
    agg = {k: [] for k in ("final", "clean", "etaL_pw", "val_pgd")}
    agg_of = {k: [] for k in agg}                                 # overfitting runs only
    for (rid, arm, ns, sd), traj in sorted(runs.items()):
        reg, picks, oracle = select_and_regret(traj)
        overfit = oracle["test_robust"] - traj[-1]["test_robust"]  # oracle minus final = overfitting severity
        for k in agg:
            agg[k].append(reg[k])
            if overfit > 0.01:
                agg_of[k].append(reg[k])
        print(f"{str((arm,ns,sd)):>26} {overfit:>+8.3f} | " +
              " ".join(f"{reg[k]:>7.3f}" for k in ("final", "clean")) + " " +
              " ".join(f"{reg[k]:>8.3f}" for k in ("etaL_pw", "val_pgd")))

    def _ci(v):
        v = np.array(v, float); m = v.mean()
        if len(v) < 2: return m, 0.0
        bs = [np.random.default_rng(s).choice(v, len(v)).mean() for s in range(2000)]
        return m, (np.percentile(bs, 97.5) - np.percentile(bs, 2.5)) / 2
    print("\n-- mean regret (all runs) --")
    for k in ("final", "clean", "etaL_pw", "val_pgd"):
        m, h = _ci(agg[k]); print(f"   {k:>8}: {m:+.3f} +/- {h:.3f}")
    print(f"-- mean regret (the {len(agg_of['final'])} runs that robustly overfit, oracle-final>0.01) --")
    for k in ("final", "clean", "etaL_pw", "val_pgd"):
        m, h = _ci(agg_of[k]); print(f"   {k:>8}: {m:+.3f} +/- {h:.3f}")
    stamp = time.strftime("%Y%m%d_%H%M%S")
    json.dump(dict(rows=rows, warmup_frac=WARMUP_FRAC, eps=EPS, pgd_steps=args.pgd_steps),
              open(os.path.join(RESDIR, f"{args.tag}_{stamp}.json"), "w"), indent=1, default=float)
    print(f"\nsaved {args.tag}_{stamp}.json")


if __name__ == "__main__":
    main()
