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

    rows = []
    for n in args.doses:
        cks = sorted(glob.glob(os.path.join(HERE, f"ckpts/v2ckpt_traj_syn{n}_s0_ep*.pt")), key=epoch_of)
        if not cks:
            print(f"[skip] syn{n}: no trajectory checkpoints", flush=True); continue
        # 1) select best checkpoint by VAL PGD robust accuracy
        sel = []
        for p in cks:
            mdl = load_model(p, dev)
            rob = CD.pgd_acc(mdl, Xval, yval, dev, DV.EPS, "linf", steps=args.sel_steps)
            sel.append((epoch_of(p), rob, p))
            del mdl
            if dev.startswith("cuda"): torch.cuda.empty_cache()
        sel.sort(key=lambda t: t[1], reverse=True)
        best_ep, best_rob, best_p = sel[0]
        traj = {e: r for e, r, _ in sel}
        # 2) report at the selected (early-stopped) checkpoint on the disjoint TEST split
        mdl = load_model(best_p, dev)
        clean = CD.accuracy(mdl, Xrep, yrep, dev)
        aa = CD.autoattack_acc(mdl, Xrep, yrep, dev, DV.EPS, "Linf", n=args.aa_n, version="standard")
        cm = CD.correct_mask(mdl, Xrep, yrep, dev); Xc, yc = Xrep[cm], yrep[cm]
        rr = DV.robust_radius_l2_per_sample(mdl, Xc[:args.rad_n], yc[:args.rad_n], dev, steps=args.rad_steps)
        fin = torch.isfinite(rr); rr_mean = float(rr[fin].mean()) if fin.any() else float("nan")
        dec = CD.etaL_decomposition(mdl, Xrep, yrep, dev, n_max=args.dec_n)
        ls = DV.mean_logit_scale(mdl, Xrep, yrep, dev, n_max=args.dec_n)
        row = dict(n_syn=int(n), best_ep=best_ep, val_rob=best_rob, ep40_val_rob=traj.get(40),
                   clean=clean, aa=aa, rr_l2=rr_mean, margin=dec["margin"], L1=dec["L1"], L2=dec["L2"],
                   etaL=dec["etaL"], logit_scale=ls)
        rows.append(row)
        print(f"[syn{n}] best ep={best_ep} (val_rob {best_rob:.3f}; ep40 val_rob {traj.get(40,float('nan')):.3f}) "
              f"| clean {clean:.3f} AA {aa:.3f} rr_l2 {rr_mean:.3f} | margin {dec['margin']:.3f} "
              f"L2 {dec['L2']:.3f} eta/L {dec['etaL']:.3f} logit_scale {ls:.3f}", flush=True)
        del mdl
        if dev.startswith("cuda"): torch.cuda.empty_cache()

    stamp = time.strftime("%Y%m%d_%H%M%S")
    fn = os.path.join(RESDIR, f"salvage_earlystop_{stamp}.json")
    json.dump(dict(args=vars(args), rows=rows), open(fn, "w"), indent=2, default=float)
    print(f"\nsaved {fn}", flush=True)

    # ---- comparison table + the decisive read ----
    if rows:
        b = rows[0]
        print("\n==== EARLY-STOPPED comparison (best-ckpt vs best-ckpt, test split) ====", flush=True)
        print(f"{'dose':>7} {'best_ep':>7} {'clean':>7} {'AA':>7} {'rr_l2':>7} {'margin':>7} {'L2':>7} {'eta/L':>7}", flush=True)
        for r in rows:
            lab = "0" if r["n_syn"] == 0 else (f"{r['n_syn']//1000}k" if r["n_syn"] < 1_000_000 else "1M")
            print(f"{lab:>7} {r['best_ep']:>7} {r['clean']:>7.3f} {r['aa']:>7.3f} {r['rr_l2']:>7.3f} "
                  f"{r['margin']:>7.3f} {r['L2']:>7.3f} {r['etaL']:>7.3f}", flush=True)
        print("\nDECISIVE READS:", flush=True)
        for r in rows[1:]:
            lab = f"{r['n_syn']//1000}k" if r["n_syn"] < 1_000_000 else "1M"
            dAA = r["aa"] - b["aa"]; dL = r["L2"] - b["L2"]
            print(f"  +{lab}: dAA {dAA:+.3f}  (ep40-confounded gain was larger)  |  L2 {b['L2']:.3f}->{r['L2']:.3f} "
                  f"({'LOWER' if dL < 0 else 'HIGHER/EQUAL'} L at matched best-ckpt)  |  eta/L {b['etaL']:.3f}->{r['etaL']:.3f}", flush=True)
        print("\nIf AA gain persists -> finding survives early stopping. If L is NOT lower at matched best-ckpt -> "
              "the ep40 'smoothness/lower-L' mechanism was a robust-overfitting artifact.", flush=True)


if __name__ == "__main__":
    main()
