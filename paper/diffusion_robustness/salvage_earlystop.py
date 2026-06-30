#!/usr/bin/env python3
"""
SALVAGE: fair early-stopped diffusion-data comparison.

The ep40 comparison is confounded by robust overfitting: the real-only baseline overfits (its L_2 blows
up and its robust-test accuracy decays late), which inflates both the headline robustness gain and the
"L drop". This script removes that confound by proper early stopping. Using the per-epoch trajectory
checkpoints already saved (ckpts/v2ckpt_traj_syn*_s0_ep*.pt), for each arm it:
  1) selects the checkpoint with the best Linf-8/255 PGD robust accuracy on a held-out VAL split, then
  2) reports clean / AutoAttack / DDN-l2 radius / eta-L decomposition on a DISJOINT TEST split.
So the cross-arm comparison is best-checkpoint vs best-checkpoint (no selection-on-test bias). The
question it answers: does the robustness gain survive fair early stopping, and at matched (best) operating
points is L actually lower for the synthetic arms, or was the ep40 "L drop" an overfitting artifact?

1 seed (s0) -- enough to settle the qualitative confound; multi-seed is a follow-up if it matters.
Run: PYTHONNOUSERSITE=1 ../env/cenv/bin/python salvage_earlystop.py --gpu 0
"""
import argparse, os, glob, json, time, re
import numpy as np, torch

HERE = os.path.dirname(os.path.abspath(__file__))
import diff_pilot_v2 as DV          # robust_radius_l2_per_sample, mean_logit_scale, EPS/ALPHA, CD/CAT/M
CD, M = DV.CD, DV.M
RESDIR = os.path.join(HERE, "results"); os.makedirs(RESDIR, exist_ok=True)


def load_model(path, dev):
    blob = torch.load(path, map_location="cpu")
    sd = blob["state_dict"] if isinstance(blob, dict) and "state_dict" in blob else blob
    arm = blob.get("arm", "stdzero") if isinstance(blob, dict) else "stdzero"
    width = blob.get("width", 1.0) if isinstance(blob, dict) else 1.0
    model = M.build(arm, width=width)
    model.load_state_dict(sd)
    return model.to(dev).eval()


def epoch_of(path):
    m = re.search(r"_ep(\d+)\.pt$", path); return int(m.group(1)) if m else -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--doses", type=int, nargs="+", default=[0, 100000, 500000, 1000000])
    ap.add_argument("--tag", default="v2ckpt", help="ckpt tag prefix (v2ckpt=single-seed, v2firm=multi-seed)")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0], help="seeds to early-stop and aggregate over")
    ap.add_argument("--val_n", type=int, default=2000, help="held-out val pts for checkpoint selection")
    ap.add_argument("--sel_steps", type=int, default=20, help="PGD steps for val-selection (cheap)")
    ap.add_argument("--aa_n", type=int, default=512)
    ap.add_argument("--rad_n", type=int, default=1000); ap.add_argument("--rad_steps", type=int, default=300)
    ap.add_argument("--dec_n", type=int, default=1000)
    args = ap.parse_args()
    dev = f"cuda:{args.gpu}" if torch.cuda.is_available() else "cpu"
    if dev.startswith("cuda"):
        torch.cuda.set_device(args.gpu)

    # same loader/split as the harness; carve val (selection) disjoint from report (test metrics)
    Xtr, ytr, Xte, yte = CD.load_cifar(50000, 10000, seed=0)
    Xval, yval = Xte[:args.val_n], yte[:args.val_n]               # checkpoint selection (PGD robust acc)
    Xrep, yrep = Xte[args.val_n:], yte[args.val_n:]               # reporting (clean/AA/radius/decomp)
    print(f"[salvage] dev={dev}  val={len(Xval)} (selection)  report={len(Xrep)} (test)  "
          f"sel=PGD-Linf-8/255 x{args.sel_steps}\n", flush=True)

    import statistics as st, math
    per = []                                            # all (dose, seed) early-stopped rows
    for n in args.doses:
        for sd in args.seeds:
            cks = sorted(glob.glob(os.path.join(HERE, f"ckpts/{args.tag}_traj_syn{n}_s{sd}_ep*.pt")), key=epoch_of)
            if not cks:
                print(f"[skip] syn{n} s{sd}: no '{args.tag}' trajectory checkpoints", flush=True); continue
            # 1) select best checkpoint by VAL PGD robust accuracy
            sel = []
            for p in cks:
                mdl = load_model(p, dev)
                rob = CD.pgd_acc(mdl, Xval, yval, dev, DV.EPS, "linf", steps=args.sel_steps)
                sel.append((epoch_of(p), rob, p)); del mdl
                if dev.startswith("cuda"): torch.cuda.empty_cache()
            sel.sort(key=lambda t: t[1], reverse=True)
            best_ep, best_rob, best_p = sel[0]
            # 2) report at the selected (early-stopped) checkpoint on the disjoint TEST split
            mdl = load_model(best_p, dev)
            clean = CD.accuracy(mdl, Xrep, yrep, dev)
            aa = CD.autoattack_acc(mdl, Xrep, yrep, dev, DV.EPS, "Linf", n=args.aa_n, version="standard")
            cm = CD.correct_mask(mdl, Xrep, yrep, dev); Xc, yc = Xrep[cm], yrep[cm]
            rr = DV.robust_radius_l2_per_sample(mdl, Xc[:args.rad_n], yc[:args.rad_n], dev, steps=args.rad_steps)
            fin = torch.isfinite(rr); rr_mean = float(rr[fin].mean()) if fin.any() else float("nan")
            dec = CD.etaL_decomposition(mdl, Xrep, yrep, dev, n_max=args.dec_n)
            row = dict(n_syn=int(n), seed=int(sd), best_ep=best_ep, val_rob=best_rob, clean=clean, aa=aa,
                       rr_l2=rr_mean, margin=dec["margin"], L1=dec["L1"], L2=dec["L2"], etaL=dec["etaL"],
                       etaL1=dec["margin"] / dec["L1"])
            per.append(row); del mdl
            if dev.startswith("cuda"): torch.cuda.empty_cache()
            print(f"[syn{n} s{sd}] best ep={best_ep} (val_rob {best_rob:.3f}) | AA {aa:.3f} "
                  f"eta/L1 {row['etaL1']:.4f} eta/L2 {dec['etaL']:.3f} L2 {dec['L2']:.3f}", flush=True)

    doses = sorted({r["n_syn"] for r in per})

    def agg(n, k):
        v = [r[k] for r in per if r["n_syn"] == n]
        return (st.mean(v), (st.pstdev(v) if len(v) > 1 else 0.0), len(v)) if v else (float("nan"), 0.0, 0)

    def pear(a, b):
        nn = len(a)
        if nn < 2: return float("nan")
        ma, mb = sum(a) / nn, sum(b) / nn
        ca = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        va = sum((x - ma) ** 2 for x in a); vb = sum((y - mb) ** 2 for y in b)
        return ca / math.sqrt(va * vb) if va > 0 and vb > 0 else float("nan")

    AA = [r["aa"] for r in per]; E1 = [r["etaL1"] for r in per]; E2 = [r["etaL"] for r in per]
    r_match, r_mis = pear(E1, AA), pear(E2, AA)
    aggregate = {str(n): {k: agg(n, k) for k in ("aa", "etaL1", "etaL", "L1", "L2", "margin", "rr_l2", "best_ep")}
                 for n in doses}

    stamp = time.strftime("%Y%m%d_%H%M%S")
    fn = os.path.join(RESDIR, f"salvage_earlystop_{args.tag}_{stamp}.json")
    json.dump(dict(args=vars(args), per_seed=per, aggregate=aggregate,
                   pearson=dict(etaL1_vs_AA=r_match, etaL2_vs_AA=r_mis, n_points=len(per))),
              open(fn, "w"), indent=2, default=float)
    print(f"\nsaved {fn}", flush=True)

    print(f"\n==== EARLY-STOPPED, multi-seed (tag={args.tag}, seeds={args.seeds}) ====", flush=True)
    print(f"{'dose':>6} {'nseed':>5} {'AA':>14} {'eta/L1(Linf)':>17} {'eta/L2':>13} {'L2':>13}", flush=True)
    for n in doses:
        lab = "0" if n == 0 else (f"{n//1000}k" if n < 1_000_000 else "1M")
        a, e1, e2, l2 = agg(n, "aa"), agg(n, "etaL1"), agg(n, "etaL"), agg(n, "L2")
        print(f"{lab:>6} {a[2]:>5} {a[0]:>7.3f}+-{a[1]:<5.3f} {e1[0]:>10.4f}+-{e1[1]:<5.4f} "
              f"{e2[0]:>7.3f}+-{e2[1]:<4.3f} {l2[0]:>7.3f}+-{l2[1]:<4.3f}", flush=True)
    print(f"\nPearson over all {len(per)} (dose x seed) points -- the threat-matched law:", flush=True)
    print(f"  eta/L1 (Linf-matched) vs AA(Linf):  {r_match:+.3f}", flush=True)
    print(f"  eta/L2 (mismatched)   vs AA(Linf):  {r_mis:+.3f}", flush=True)


if __name__ == "__main__":
    main()
