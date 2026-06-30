#!/usr/bin/env python3
"""
NQ3: does diffusion data change the gradient GEOMETRY (the tangential / data-condition-number factor tau)?

Main paper Sec.3.6 splits the margin gradient into a radial floor and a tangential factor. Operationally,
for a sample x the radial derivative is <grad M, x>/||x||, and the tangential amplification is
    tau(x) = ||grad M||_2 / |<grad M, x>/||x||| = ||grad M||_2 * ||x|| / |<grad M, x>|  (= sec angle(grad,x) >= 1).
tau=1 means a purely radial (well-conditioned) gradient; large tau means the gradient points mostly
off the data ray. Question: does synthetic data lower tau (more radial / better conditioned gradients,
cf. off-manifold-gradient non-robustness, Melamed 2023), or leave it unchanged? Uses the existing final
checkpoints (ckpts/v2ckpt_syn*_s0_e40.pt). Margin = true_logit - max_other, grad w.r.t. [0,1] input,
correct points only -- identical to cifar_dissection.etaL_decomposition.
Run: PYTHONNOUSERSITE=1 ../env/cenv/bin/python nq3_tau.py --gpu 0
"""
import argparse, os, glob, json, time
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
import diff_pilot_v2 as DV
CD, M = DV.CD, DV.M
RESDIR = os.path.join(HERE, "results"); os.makedirs(RESDIR, exist_ok=True)


def load_model(path, dev):
    blob = torch.load(path, map_location="cpu")
    sd = blob["state_dict"] if isinstance(blob, dict) and "state_dict" in blob else blob
    model = M.build("stdzero", width=1.0); model.load_state_dict(sd)
    return model.to(dev).eval()


def tau_stats(model, X, y, dev, n_max=1000, bs=128):
    cm = CD.correct_mask(model, X, y, dev)
    Xc, yc = X[cm][:n_max], y[cm][:n_max]
    taus, radial, gnorm = [], [], []
    for i in range(0, len(Xc), bs):
        xb = Xc[i:i + bs].to(dev).requires_grad_(True); yb = yc[i:i + bs].to(dev)
        logits = model(xb)
        true = logits.gather(1, yb[:, None]).squeeze(1)
        other = logits.clone().scatter_(1, yb[:, None], -1e9).max(1).values
        margin = true - other
        g, = torch.autograd.grad(margin.sum(), xb)
        gf = g.flatten(1).detach(); xf = xb.detach().flatten(1)
        gn = gf.norm(dim=1); xn = xf.norm(dim=1)
        dot = (gf * xf).sum(1).abs()                       # |<grad, x>|
        rad = dot / xn.clamp_min(1e-12)                    # radial component magnitude
        tau = gn * xn / dot.clamp_min(1e-12)               # sec angle(grad, x) >= 1
        taus.append(tau.cpu()); radial.append(rad.cpu()); gnorm.append(gn.cpu())
    tau = torch.cat(taus); rad = torch.cat(radial); gn = torch.cat(gnorm)
    return dict(tau_mean=float(tau.mean()), tau_median=float(tau.median()),
                radial_mean=float(rad.mean()), gnorm_mean=float(gn.mean()), n=len(tau))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--doses", type=int, nargs="+", default=[0, 100000, 500000, 1000000])
    ap.add_argument("--n_max", type=int, default=1000)
    args = ap.parse_args()
    dev = f"cuda:{args.gpu}" if torch.cuda.is_available() else "cpu"
    if dev.startswith("cuda"):
        torch.cuda.set_device(args.gpu)
    _, _, Xte, yte = CD.load_cifar(50000, 10000, seed=0)
    print(f"[nq3-tau] dev={dev}  doses={args.doses}\n", flush=True)

    rows = []
    for n in args.doses:
        ck = os.path.join(HERE, f"ckpts/v2ckpt_syn{n}_s0_e40.pt")
        if not os.path.exists(ck):
            print(f"[skip] syn{n}: no final ckpt", flush=True); continue
        s = tau_stats(load_model(ck, dev), Xte, yte, dev, n_max=args.n_max)
        s["n_syn"] = n; rows.append(s)
        lab = "0" if n == 0 else (f"{n//1000}k" if n < 1_000_000 else "1M")
        print(f"[syn{lab}] tau_mean {s['tau_mean']:.3f}  tau_median {s['tau_median']:.3f}  "
              f"radial {s['radial_mean']:.4f}  ||grad|| {s['gnorm_mean']:.3f}", flush=True)

    stamp = time.strftime("%Y%m%d_%H%M%S")
    fn = os.path.join(RESDIR, f"nq3_tau_{stamp}.json")
    json.dump(dict(rows=rows), open(fn, "w"), indent=2, default=float)
    print(f"\nsaved {fn}", flush=True)
    if rows:
        b = rows[0]
        print("\nREAD: tau ~ const across doses -> gain is NOT a gradient-conditioning effect; "
              "tau falls -> synthetic data makes gradients more radial (better conditioned).", flush=True)
        for r in rows[1:]:
            lab = f"{r['n_syn']//1000}k" if r["n_syn"] < 1_000_000 else "1M"
            print(f"  +{lab}: tau {b['tau_mean']:.3f} -> {r['tau_mean']:.3f} ({r['tau_mean']-b['tau_mean']:+.3f})", flush=True)


if __name__ == "__main__":
    main()
