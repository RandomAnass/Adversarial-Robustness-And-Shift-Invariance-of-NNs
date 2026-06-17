#!/usr/bin/env python3
"""
Validate the DDN robust RADIUS against AutoAttack at the relevant (small) eps, on the actual
trained CNNs -- the gradient-masking guard that the standard-eps AutoAttack (which floors to 0)
cannot provide. For each arm we compare, on the SAME correct points:
    AutoAttack-L2 robust accuracy at eps   vs   fraction of DDN radii > eps.
If these track each other, the DDN radius is not gradient-masking-inflated.

Run: paper/env/cenv/bin/python paper/experiments/cifar_aa_calibration.py
"""
import os, json, time, numpy as np, torch
from cifar_dissection import (build, train, load_cifar, correct_mask, _margin_loss,
                              autoattack_acc, ARMS)

RESDIR = os.path.join(os.path.dirname(__file__), "..", "results")

def ddn_persample(model, X, y, dev, steps=300, gamma=0.05, eps0=1.0, a0=1.0, bs=256):
    X = X.to(dev); y = y.to(dev); N = len(X); best = torch.full((N,), float("inf"), device=dev)
    for i in range(0, N, bs):
        xb = X[i:i+bs]; yb = y[i:i+bs]; delta = torch.zeros_like(xb)
        eps = torch.full((len(xb),), float(eps0), device=dev); bnorm = torch.full((len(xb),), float("inf"), device=dev)
        for k in range(steps):
            alpha = 0.01 + (a0-0.01)*(1+np.cos(np.pi*k/steps))/2
            delta.requires_grad_(True)
            logits = model(torch.clamp(xb+delta, 0, 1))
            g, = torch.autograd.grad(_margin_loss(logits, yb).sum(), delta)
            with torch.no_grad():
                adv = logits.argmax(1) != yb; nrm = delta.flatten(1).norm(dim=1)
                upd = adv & (nrm < bnorm); bnorm[upd] = nrm[upd]
                eps = torch.where(adv, eps*(1-gamma), eps*(1+gamma))
                gn = g/g.flatten(1).norm(dim=1).clamp_min(1e-12)[:,None,None,None]
                delta = delta + alpha*gn
                dn = delta.flatten(1).norm(dim=1).clamp_min(1e-12)
                delta = delta/dn[:,None,None,None]*eps[:,None,None,None]
                delta = torch.clamp(xb+delta, 0, 1) - xb
        best[i:i+len(xb)] = bnorm
    return best.cpu()

def main():
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    if dev.startswith("cuda"): torch.cuda.set_device(0)
    W, EPOCHS, N, SEED = 32, 40, 512, 0
    EPS = [0.05, 0.1, 0.15, 0.25, 0.5]
    Xtr, ytr, Xte, yte = load_cifar(50000, 10000, seed=0)
    out = {}
    for arm in ARMS:
        t0 = time.time()
        model = train(build(arm, W), Xtr, ytr, dev, epochs=EPOCHS, seed=SEED,
                      aug=True, shift_aug=(arm == "aug"))
        cm = correct_mask(model, Xte, yte, dev); Xc, yc = Xte[cm][:N], yte[cm][:N]
        rad = ddn_persample(model, Xc, yc, dev)                 # per-sample DDN radius
        rec = {"mean_radius": float(rad.mean()), "eps": EPS, "aa_acc": [], "ddn_acc": []}
        for e in EPS:
            aa = autoattack_acc(model, Xc, yc, dev, e, "L2", n=N, version="standard")
            ddn_acc = float((rad > e).float().mean())           # radius-implied robust acc
            rec["aa_acc"].append(aa); rec["ddn_acc"].append(ddn_acc)
        out[arm] = rec
        print(f"[{arm:9s}] {time.time()-t0:.0f}s  mean_radius={rec['mean_radius']:.3f}")
        for e, aa, dd in zip(EPS, rec["aa_acc"], rec["ddn_acc"]):
            gap = aa - dd
            flag = "  <-- AA>DDN-implied (radius may be optimistic)" if gap > 0.03 else ""
            print(f"    eps={e:.2f}  AutoAttack_acc={aa:.3f}  DDN_radius>eps={dd:.3f}  gap={gap:+.3f}{flag}")
    stamp = time.strftime("%Y%m%d_%H%M%S")
    json.dump(out, open(os.path.join(RESDIR, f"cifar_aa_calibration_{stamp}.json"), "w"), indent=2)
    print(f"\nsaved cifar_aa_calibration_{stamp}.json")
    # overall agreement
    allgap = [abs(aa-dd) for r in out.values() for aa, dd in zip(r["aa_acc"], r["ddn_acc"])]
    print(f"mean |AA - DDN-implied| over all (arm,eps) = {np.mean(allgap):.4f}  max = {np.max(allgap):.4f}")

if __name__ == "__main__":
    main()
