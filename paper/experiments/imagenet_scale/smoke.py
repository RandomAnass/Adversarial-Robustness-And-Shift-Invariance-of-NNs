#!/usr/bin/env python3
"""Smoke test for the S2 pipeline: a few real train iters (timing), val-robust probe, and the whole
eval path on tiny n. Run before launching the chain. Low footprint (fits beside another job)."""
import time, torch, torch.nn.functional as F

import train as TR
import evaluate as EV
from models import ImageNet100ResNet18
from data import load_data

def main():
    dev = "cuda:0"
    t0 = time.time(); data = load_data(); print(f"data loaded {time.time()-t0:.0f}s "
        f"train={tuple(data['Xtr'].shape)} val={tuple(data['Xval'].shape)} test={tuple(data['Xte'].shape)}")
    eps = 4 / 255
    for arm, iters in [("standard", 12), ("aps", 6), ("blurpool", 6)]:
        TR.set_seed(0)
        model = ImageNet100ResNet18(arm).to(dev).to(memory_format=torch.channels_last)
        opt = torch.optim.SGD(model.parameters(), lr=0.05, momentum=0.9, weight_decay=5e-4)
        it = TR.batches(data["Xtr"], data["ytr"], 256, 0, dev, 0)
        losses = []
        for k in range(iters):
            xb, yb = next(it)
            if k == 2: torch.cuda.synchronize(); t0 = time.time()   # skip warmup
            xb = TR.augment(xb, pad=8, roll=(16 if arm == "aug" else 0))
            xa = TR.fgsm_rs(model, xb, yb, eps, 1.25 * eps)
            model.train(); opt.zero_grad(set_to_none=True)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                loss = F.cross_entropy(model(xa), yb)
            loss.backward(); opt.step(); losses.append(loss.item())
        torch.cuda.synchronize()
        dt = (time.time() - t0) / (iters - 2)
        est = dt * (len(data["Xtr"]) / 256 + 40) / 60           # + val-probe overhead margin
        print(f"{arm:9s}: {dt:.3f}s/iter -> ~{est:.1f} min/epoch, ~{est*15/60:.1f} h/15ep  "
              f"loss {losses[0]:.2f}->{losses[-1]:.2f}  mem {torch.cuda.max_memory_allocated()/2**30:.1f}G")
        torch.cuda.reset_peak_memory_stats()
        if arm == "standard":
            t0 = time.time()
            vra = TR.robust_acc(model, data["Xval"][:256], data["yval"][:256], dev, eps, eps / 4, 10)
            print(f"  val-robust probe (256 imgs, PGD-10): {vra:.3f}  {time.time()-t0:.0f}s")
            model.eval()
            t0 = time.time(); c = EV.shift_consistency(model, data["Xte"][:512], dev); tc = time.time() - t0
            t0 = time.time(); d = EV.etaL_decomposition(model, data["Xte"][:512], data["yte"][:512], dev, n_max=128); td = time.time() - t0
            t0 = time.time(); p = EV.pgd_acc(model, data["Xte"][:128], data["yte"][:128], dev, eps, steps=10); tp = time.time() - t0
            t0 = time.time(); a = EV.autoattack_acc(model, data["Xte"][:64], data["yte"][:64], dev, eps, n=64, version="custom"); ta = time.time() - t0
            print(f"  eval path: consist={c:.3f} ({tc:.0f}s/512) etaL1={d['etaL1']:.5f} n={d['n_pts']} ({td:.0f}s) "
                  f"pgd10={p:.3f} ({tp:.0f}s/128) aa_custom={a:.3f} ({ta:.0f}s/64)")
    print("SMOKE_OK")

if __name__ == "__main__":
    main()
