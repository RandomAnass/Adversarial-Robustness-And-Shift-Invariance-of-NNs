#!/usr/bin/env python3
"""
PROPER candidate mechanism (multi-seed): diffusion data delays robust overfitting.

The verified, gauge-free effect is dynamical, not the (confounded) static 'smoothness' story. Candidate:
synthetic data enlarges the effective adversarial training set, so the productive pre-memorization phase
lengthens -- the robust-test-accuracy peak moves later, the train/test robust gap at the peak shrinks, and
the late eta/L collapse of robust overfitting is prevented. Three falsifiable, gauge-free predictions,
checked over seeds from the v2firm trajectory checkpoints:
  (a) peak robust-test epoch INCREASES with synthetic dose,
  (b) train-test robust gap at the peak DECREASES with dose,
  (c) eta/L collapse (peak-to-final) DECREASES with dose.
For each (dose,seed) it walks the trajectory checkpoints, computing PGD robust-train / robust-test and the
eta/L decomposition per epoch, then aggregates over seeds. Writes results/proper_candidate_<stamp>.json.
Run: PYTHONNOUSERSITE=1 ../env/cenv/bin/python proper_candidate.py --gpu 0 --tag v2firm --seeds 0 1 2
"""
import argparse, os, glob, json, time, re, collections, statistics as st
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
import diff_pilot_v2 as DV
CD, M = DV.CD, DV.M
RESDIR = os.path.join(HERE, "results"); os.makedirs(RESDIR, exist_ok=True)


def load_model(path, dev):
    blob = torch.load(path, map_location="cpu")
    sd = blob["state_dict"] if isinstance(blob, dict) and "state_dict" in blob else blob
    m = M.build("stdzero", width=1.0); m.load_state_dict(sd)
    return m.to(dev).eval()


def epoch_of(p):
    g = re.search(r"_ep(\d+)\.pt$", p); return int(g.group(1)) if g else -1


def spearman(a, b):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i]); r = [0]*len(v)
        for i, idx in enumerate(order): r[idx] = i
        return r
    ra, rb = rank(a), rank(b); n = len(a)
    if n < 2: return float("nan")
    dd = sum((ra[i]-rb[i])**2 for i in range(n))
    return 1 - 6*dd/(n*(n*n-1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--tag", default="v2firm")
    ap.add_argument("--doses", type=int, nargs="+", default=[0, 100000, 500000, 1000000])
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--pgd_steps", type=int, default=20)
    ap.add_argument("--n_eval", type=int, default=2000)
    ap.add_argument("--dec_n", type=int, default=1000)
    args = ap.parse_args()
    dev = f"cuda:{args.gpu}" if torch.cuda.is_available() else "cpu"
    if dev.startswith("cuda"): torch.cuda.set_device(args.gpu)
    Xtr, ytr, Xte, yte = CD.load_cifar(50000, 10000, seed=0)
    Xtr_e, ytr_e = Xtr[:args.n_eval], ytr[:args.n_eval]          # real-train subset (memorization side)
    Xte_e, yte_e = Xte[:args.n_eval], yte[:args.n_eval]
    print(f"[proper] dev={dev} tag={args.tag} doses={args.doses} seeds={args.seeds}\n", flush=True)

    per = collections.defaultdict(list)   # dose -> list of per-seed (peak_ep, gap@peak, etaL_collapse, peak_robtest)
    for n in args.doses:
        for sd in args.seeds:
            cks = sorted(glob.glob(os.path.join(HERE, f"ckpts/{args.tag}_traj_syn{n}_s{sd}_ep*.pt")), key=epoch_of)
            if not cks:
                print(f"[skip] syn{n} s{sd}", flush=True); continue
            curve = []
            for p in cks:
                ep = epoch_of(p); mdl = load_model(p, dev)
                rtr = CD.pgd_acc(mdl, Xtr_e, ytr_e, dev, DV.EPS, "linf", steps=args.pgd_steps)
                rte = CD.pgd_acc(mdl, Xte_e, yte_e, dev, DV.EPS, "linf", steps=args.pgd_steps)
                dec = CD.etaL_decomposition(mdl, Xte_e, yte_e, dev, n_max=args.dec_n)
                curve.append(dict(epoch=ep, rtr=rtr, rte=rte, gap=rtr-rte, etaL=dec["etaL"]))
                del mdl
                if dev.startswith("cuda"): torch.cuda.empty_cache()
            pk = max(curve, key=lambda r: r["rte"]); fin = curve[-1]
            etaL_pk = max(curve, key=lambda r: r["etaL"])["etaL"]
            rec = dict(peak_ep=pk["epoch"], gap_at_peak=pk["gap"], peak_rte=pk["rte"],
                       etaL_collapse=etaL_pk - fin["etaL"], final_rte=fin["rte"])
            per[n].append(rec)
            print(f"[syn{n} s{sd}] peak ep {pk['epoch']} rte {pk['rte']:.3f} gap {pk['gap']:.3f} "
                  f"etaL_collapse {rec['etaL_collapse']:+.3f}", flush=True)

    def agg(n, k):
        v = [r[k] for r in per[n]]
        return (st.mean(v), (st.pstdev(v) if len(v) > 1 else 0.0)) if v else (float("nan"), 0.0)
    doses = sorted([n for n in per if per[n]])
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = {str(n): {k: agg(n, k) for k in ("peak_ep", "gap_at_peak", "etaL_collapse", "peak_rte")} for n in doses}
    fn = os.path.join(RESDIR, f"proper_candidate_{args.tag}_{stamp}.json")
    json.dump(dict(args=vars(args), per_seed={str(n): per[n] for n in doses}, aggregate=out), open(fn, "w"), indent=2, default=float)
    print(f"\nsaved {fn}", flush=True)

    print(f"\n==== PROPER CANDIDATE: robust-overfitting delay (mean+/-std over seeds) ====")
    print(f"{'dose':>6} {'peak_ep':>14} {'gap@peak':>14} {'etaL_collapse':>16}")
    pe, ga, ec = [], [], []
    for n in doses:
        a, b, c = agg(n, "peak_ep"), agg(n, "gap_at_peak"), agg(n, "etaL_collapse")
        pe.append(a[0]); ga.append(b[0]); ec.append(c[0])
        lab = "0" if n == 0 else (f"{n//1000}k" if n < 1_000_000 else "1M")
        print(f"{lab:>6} {a[0]:>7.1f}+-{a[1]:<5.1f} {b[0]:>7.3f}+-{b[1]:<5.3f} {c[0]:>8.3f}+-{c[1]:<6.3f}")
    print(f"\nSpearman vs dose:  peak_ep {spearman(doses, pe):+.2f} (predict +)  "
          f"gap@peak {spearman(doses, ga):+.2f} (predict -)  etaL_collapse {spearman(doses, ec):+.2f} (predict -)")


if __name__ == "__main__":
    main()
