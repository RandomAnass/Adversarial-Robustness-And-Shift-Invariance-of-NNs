#!/usr/bin/env python3
"""
S1a supporting eval: reproduce TIPS's OWN "shift-invariance helps adversarial robustness" regime
(STANDARD-trained nets, small Linf eps, FGSM / few-step PGD -- the weak, single-/few-step attacks
TIPS used via Foolbox) and then contrast it with AutoAttack (the strong ensemble) at the SAME eps.

For each standard-trained arm (standard, blurpool, aps, aug, tips) at a given width, on a fixed test
subset, we report at eps in {1,2,4,8}/255:
    fgsm  = 1-step FGSM robust acc (CE, sign-gradient, no random start)   [weak]
    pgd   = k-step PGD robust acc (margin loss, alpha=eps/4)              [weak/medium]
    aa    = AutoAttack "standard" robust acc                             [strong ground truth]
plus clean acc and shift-consistency. Writes tips_weakattack_w{W}.json. Resumable per (arm,eps).

The head-to-head prediction: across arms, in the WEAK regime shift-consistency may positively track
FGSM/PGD robustness (TIPS's story), while under AutoAttack that apparent advantage shrinks/flips --
i.e. the weak-attack signal is not the strong-attack truth.

Usage: PYTHONNOUSERSITE=1 paper/env/cenv/bin/python tips_weakattack.py --gpu 0 --width 1.0
"""
import os, sys, json, time, argparse, numpy as np, torch, torch.nn.functional as F
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import build, nparams
from resnet_train import load_data, set_seed
from cifar_dissection import pgd_acc, autoattack_acc, accuracy, shift_consistency

RESDIR = os.path.join(os.path.dirname(__file__), "..", "..", "results", "resnet_scale")
CKPTDIR = os.path.join(RESDIR, "ckpt")
ARMS = ["standard", "blurpool", "aps", "aug", "tips"]
EPS_LIST = [1/255, 2/255, 4/255, 8/255]
AA_EPS = [2/255, 4/255, 8/255]           # AutoAttack only at these (it is the expensive attack)

def fgsm_acc(model, X, y, dev, eps, bs=256):
    """1-step FGSM robust accuracy (CE loss, no random start), clamped to [0,1]."""
    correct = 0
    for i in range(0, len(X), bs):
        xb = X[i:i+bs].to(dev); yb = y[i:i+bs].to(dev)
        xb.requires_grad_(True)
        loss = F.cross_entropy(model(xb), yb)
        g, = torch.autograd.grad(loss, xb)
        xa = torch.clamp(xb + eps * g.sign(), 0, 1).detach()
        with torch.no_grad():
            correct += (model(xa).argmax(1) == yb).sum().item()
    return correct / len(X)

def load_std(arm, width, seed=0):
    tag = "" if width == 1.0 else f"_w{width}"
    name = f"c10std_{arm}{tag}_s{seed}"
    jp = os.path.join(RESDIR, name + ".json"); cp = os.path.join(CKPTDIR, name + ".pt")
    if not (os.path.exists(jp) and os.path.exists(cp)): return None, None
    r = json.load(open(jp)); cfg = r["config"]
    m = build(cfg["arm"], width=cfg["width"], num_classes=10)
    m.load_state_dict(torch.load(cp, map_location="cpu")["state"])
    assert nparams(m) == r["params"], f"{name}: param mismatch"
    return m, name

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--width", type=float, default=1.0)
    ap.add_argument("--n", type=int, default=1000, help="#pts for FGSM/PGD + clean/consist")
    ap.add_argument("--n_aa", type=int, default=512, help="#pts for AutoAttack")
    ap.add_argument("--pgd_steps", type=int, default=10); a = ap.parse_args()
    dev = f"cuda:{a.gpu}"; torch.cuda.set_device(a.gpu)
    set_seed(0); data = load_data("cifar10", seed=0); Xte, yte = data["Xte"], data["yte"]
    out_path = os.path.join(RESDIR, f"tips_weakattack_w{a.width}.json")
    out = json.load(open(out_path)) if os.path.exists(out_path) else {"width": a.width, "n": a.n,
          "n_aa": a.n_aa, "pgd_steps": a.pgd_steps, "eps_255": [1,2,4,8], "arms": {}}
    for arm in ARMS:
        m, name = load_std(arm, a.width)
        if m is None: print(f"[weak] SKIP {arm} (no std ckpt at w{a.width})", flush=True); continue
        m.to(dev).eval()
        rec = out["arms"].get(arm, {})
        if "clean" not in rec:
            rec["clean"] = accuracy(m, Xte, yte, dev)
            rec["consist"] = shift_consistency(m, Xte, dev)
            rec["params"] = nparams(m); rec["ckpt"] = name
        for eps in EPS_LIST:
            k = f"{round(eps*255)}"
            if rec.get(f"fgsm_{k}") is None:
                t0 = time.time()
                rec[f"fgsm_{k}"] = fgsm_acc(m, Xte[:a.n], yte[:a.n], dev, eps)
                rec[f"pgd_{k}"] = pgd_acc(m, Xte[:a.n], yte[:a.n], dev, eps, "linf", steps=a.pgd_steps)
                print(f"[weak] {arm:9s} eps{k}/255 fgsm={rec[f'fgsm_{k}']:.3f} pgd={rec[f'pgd_{k}']:.3f} ({time.time()-t0:.0f}s)", flush=True)
            if eps in AA_EPS and rec.get(f"aa_{k}") is None:
                t0 = time.time()
                rec[f"aa_{k}"] = autoattack_acc(m, Xte, yte, dev, eps=eps, norm="Linf", n=a.n_aa, version="standard")
                print(f"[weak] {arm:9s} eps{k}/255 AA={rec[f'aa_{k}']:.3f} ({time.time()-t0:.0f}s)", flush=True)
            out["arms"][arm] = rec
            json.dump(out, open(out_path, "w"), indent=1, default=float)   # checkpoint after each eps
        print(f"[weak] {arm:9s} clean={rec['clean']:.3f} consist={rec['consist']:.4f} DONE", flush=True)
    json.dump(out, open(out_path, "w"), indent=1, default=float)
    print(f"[weak] wrote {out_path}", flush=True)

if __name__ == "__main__":
    main()
