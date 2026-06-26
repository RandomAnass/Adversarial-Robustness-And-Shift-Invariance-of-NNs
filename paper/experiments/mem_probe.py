#!/usr/bin/env python3
"""Measure the peak GPU memory of ONE full-10k AutoAttack-standard job (worst case: MNIST eps=0.3,
width 64) so we can choose K = workers-per-GPU without OOM on the 48GB card. Trains a quick model
(few epochs -- AA memory is set by batch size + model, not by how well trained), then runs the real
autoattack_acc(...,n=10000,version='standard') and reports torch.cuda.max_memory_allocated/reserved.
Usage: PYTHONNOUSERSITE=1 paper/env/cenv/bin/python mem_probe.py --gpu 1"""
import argparse, torch
from cifar_at import run_job_at  # reuse the exact compute; but we want only the AA-memory peak

import cifar_at as C

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--gpu", type=int, default=1); a = ap.parse_args()
    dev = f"cuda:{a.gpu}"; torch.cuda.set_device(a.gpu)
    ds = "mnist"
    Xtr, ytr, Xte, yte = C.load_data(ds, 60000, 10000, seed=0)
    nmean, nstd = C.dataset_stats(ds)
    print("training a quick width-64 model (2 epochs) just to have something to attack ...", flush=True)
    model = C.adv_train(C.build("circular", 64, in_ch=C.in_channels(ds), norm_mean=nmean, norm_std=nstd),
                        Xtr, ytr, dev, epochs=2, seed=0, eps=0.3, alpha=2.5*0.3/10, steps=10, norm="linf", aug=False)
    torch.cuda.reset_peak_memory_stats(a.gpu)
    print("running full AA-standard on 10000 (this is the memory-heavy phase) ...", flush=True)
    acc = C.autoattack_acc(model, Xte, yte, dev, eps=0.3, norm="Linf", n=10000, version="standard")
    peak_alloc = torch.cuda.max_memory_allocated(a.gpu) / 1024**3
    peak_resv = torch.cuda.max_memory_reserved(a.gpu) / 1024**3
    print(f"\nAA-standard-10k peak: allocated {peak_alloc:.1f} GiB, reserved {peak_resv:.1f} GiB (robacc={acc:.3f})")
    free_gb = 47.0
    for K in (2, 3, 4):
        fits = K * peak_resv < free_gb
        print(f"  K={K} workers/GPU: {K*peak_resv:.1f} GiB reserved -> {'FITS' if fits else 'OOM RISK'} (48GB card)")

if __name__ == "__main__":
    main()
