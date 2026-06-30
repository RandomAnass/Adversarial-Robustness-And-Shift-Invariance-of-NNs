#!/usr/bin/env python3
"""
eta/L TRAJECTORY: is robust overfitting an eta/L-collapse?

The trajectory measurement gave L_2 and robust-test accuracy per epoch but never the margin or the
eta/L ratio. This computes margin / L_1 / L_2 / eta/L / logit-scale at every saved trajectory checkpoint
(ckpts/v2ckpt_traj_syn*_s0_ep*.pt), for all arms. The question: does the real-only baseline's eta/L
*collapse* in the late (robust-overfitting) phase while the synthetic arms hold a high eta/L? If so,
robust overfitting is, in this lens, an eta/L collapse, and synthetic data prevents it -- a dynamical
statement to set beside the static vicinal-coverage path result.

Decomposition only (no attacks) -> fast. Pair the output with the per-epoch L_2 / rob_test already in
results/mech/mech_trajectory_*.json. Writes results/etaL_trajectory_<stamp>.json.
Run: PYTHONNOUSERSITE=1 ../env/cenv/bin/python etaL_trajectory.py --gpu 0
"""
import argparse, os, glob, json, time, re
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
import diff_pilot_v2 as DV
CD, M = DV.CD, DV.M
RESDIR = os.path.join(HERE, "results"); os.makedirs(RESDIR, exist_ok=True)


def load_model(path, dev):
    blob = torch.load(path, map_location="cpu")
    sd = blob["state_dict"] if isinstance(blob, dict) and "state_dict" in blob else blob
    arm = blob.get("arm", "stdzero") if isinstance(blob, dict) else "stdzero"
    width = blob.get("width", 1.0) if isinstance(blob, dict) else 1.0
    model = M.build(arm, width=width); model.load_state_dict(sd)
    return model.to(dev).eval()


def epoch_of(p):
    m = re.search(r"_ep(\d+)\.pt$", p); return int(m.group(1)) if m else -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--doses", type=int, nargs="+", default=[0, 100000, 500000, 1000000])
    ap.add_argument("--dec_n", type=int, default=1000)
    args = ap.parse_args()
    dev = f"cuda:{args.gpu}" if torch.cuda.is_available() else "cpu"
    if dev.startswith("cuda"):
        torch.cuda.set_device(args.gpu)
    Xtr, ytr, Xte, yte = CD.load_cifar(50000, 10000, seed=0)
    print(f"[etaL-traj] dev={dev}  doses={args.doses}\n", flush=True)

    out = {}
    for n in args.doses:
        cks = sorted(glob.glob(os.path.join(HERE, f"ckpts/v2ckpt_traj_syn{n}_s0_ep*.pt")), key=epoch_of)
        series = []
        for p in cks:
            ep = epoch_of(p); mdl = load_model(p, dev)
            dec = CD.etaL_decomposition(mdl, Xte, yte, dev, n_max=args.dec_n)
            ls = DV.mean_logit_scale(mdl, Xte, yte, dev, n_max=args.dec_n)
            series.append(dict(epoch=ep, margin=dec["margin"], L1=dec["L1"], L2=dec["L2"],
                               etaL=dec["etaL"], logit_scale=ls))
            print(f"[syn{n}] ep{ep:>2}  margin {dec['margin']:.3f}  L2 {dec['L2']:.3f}  "
                  f"eta/L {dec['etaL']:.3f}  logit_scale {ls:.3f}", flush=True)
            del mdl
            if dev.startswith("cuda"): torch.cuda.empty_cache()
        out[str(n)] = sorted(series, key=lambda r: r["epoch"])

    stamp = time.strftime("%Y%m%d_%H%M%S")
    fn = os.path.join(RESDIR, f"etaL_trajectory_{stamp}.json")
    json.dump(out, open(fn, "w"), indent=2, default=float)
    print(f"\nsaved {fn}", flush=True)

    # quick read: peak eta/L vs final eta/L per arm (collapse = peak well above final)
    print("\n==== eta/L: peak vs final (collapse = peak >> final) ====", flush=True)
    for n in args.doses:
        s = out[str(n)]
        if not s: continue
        peak = max(s, key=lambda r: r["etaL"]); fin = s[-1]
        lab = "0" if n == 0 else (f"{n//1000}k" if n < 1_000_000 else "1M")
        print(f"  syn{lab:>4}: peak eta/L {peak['etaL']:.3f} @ ep{peak['epoch']}  ->  final {fin['etaL']:.3f} "
              f"(drop {peak['etaL']-fin['etaL']:+.3f})", flush=True)


if __name__ == "__main__":
    main()
