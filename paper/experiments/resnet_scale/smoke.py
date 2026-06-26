#!/usr/bin/env python3
"""
Smoke test for the ResNet-scale harness.
  --tiny : fast plumbing check (tiny subset, 1-2 epochs, all arms) — catches crashes, checks APS consist.
  --time : measure REAL full-epoch wall-time (standard vs aps, AT) to size the run budget.
Run: PYTHONNOUSERSITE=1 python paper/experiments/resnet_scale/smoke.py --tiny --gpu 0
"""
import os, sys, time, argparse, numpy as np, torch
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import build, nparams, ARMS
from resnet_train import load_data, train_cell, pgd_linf, _acc, _robust_acc
from cifar_dissection import shift_consistency

def tiny(gpu):
    dev = f"cuda:{gpu}"; torch.cuda.set_device(gpu)
    d = load_data("cifar10", seed=0)
    # subset for speed
    sub = lambda X, n: X[:n]
    data = {"Xtr": sub(d["Xtr"], 512), "ytr": sub(d["ytr"], 512),
            "Xval": sub(d["Xval"], 128), "yval": sub(d["yval"], 128),
            "Xte": sub(d["Xte"], 256), "yte": sub(d["yte"], 256), "n_classes": 10}
    for arm in ARMS:
        m = build(arm, num_classes=10)
        t0 = time.time()
        best, curves, be = train_cell(m, data, dev, mode="at", arm=arm, seed=0, epochs=2, bs=128,
                                      milestones=(1,), patience=99, min_epochs=99, pgd_steps=5, val_steps=5)
        m.load_state_dict(best); m.to(dev).eval()
        cons = shift_consistency(m, data["Xte"], dev)
        ca = _acc(m, data["Xte"], data["yte"], dev)
        ra = _robust_acc(m, data["Xte"], data["yte"], dev, 8/255, 2/255, 10)
        nan = any(not np.isfinite(c["train_loss"]) for c in curves)
        print(f"{arm:9s} ok | {time.time()-t0:5.1f}s | clean {ca:.3f} pgd {ra:.3f} consist {cons:.3f} "
              f"| NaN={nan} | params {nparams(m)}", flush=True)
        if arm == "aps" and cons < 0.999:
            print(f"  WARNING: APS consistency {cons:.4f} < 1.0 (expected exact)", flush=True)
    print("TINY SMOKE OK", flush=True)

def timing(gpu):
    dev = f"cuda:{gpu}"; torch.cuda.set_device(gpu)
    d = load_data("cifar10", seed=0)
    for arm in ["standard", "aps"]:
        m = build(arm, num_classes=10)
        t0 = time.time()
        train_cell(m, d, dev, mode="at", arm=arm, seed=0, epochs=1, bs=128,
                   milestones=(100,), patience=999, min_epochs=999, pgd_steps=10, val_steps=10)
        dt = time.time() - t0
        # extrapolate: ~120 effective AT epochs (Rice early-terminated)
        print(f"{arm:9s}: 1 full AT epoch = {dt:.1f}s -> ~120ep approx {dt*120/3600:.2f}h/model", flush=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--tiny", action="store_true")
    ap.add_argument("--time", action="store_true"); ap.add_argument("--gpu", type=int, default=0)
    a = ap.parse_args()
    if a.time: timing(a.gpu)
    else: tiny(a.gpu)
