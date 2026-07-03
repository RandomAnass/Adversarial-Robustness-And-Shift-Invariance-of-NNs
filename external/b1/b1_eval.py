#!/usr/bin/env python3
"""
B1 evaluation: does Wang et al.'s no-AT "adversarial robustness" survive a strong attack?

Loads the checkpoint trained by b1_train.py (their model, their recipe) and reports, in ONE json:

  A. their protocol (verbatim):
     - clean accuracy, full test set, their normalized loader
     - their fgsm_attack / pgd_attack (extracted verbatim from their *_test.py: PGD-40,
       alpha=0.01, perturbation in NORMALIZED [-1,1] space, clamp to [0,1] -- quirk kept),
       over their eps grid, full test set. This is the number their paper reports (~52%
       PGD at eps=0.03 on CIFAR-10).

  B. pixel-space [0,1] threat model (the standard one; normalization wrapped inside the model):
     - AutoAttack 'standard' (apgd-ce, apgd-t, fab-t, square) at eps in {0.01, 0.015, 0.03},
       n=1000.  NOTE eps=0.015 pixel-space == their eps=0.03 budget (their attacks act on the
       [-1,1] normalized tensor, which has 2x the pixel scale), so 0.015 is the threat-matched
       point; 0.01/0.03 bracket it (and 0.03 pixel-space is what a reader would naively assume).
     - PGD-40 (CE, random start, alpha=eps/4) at the same eps -- the white-box masking reference:
       if AutoAttack << their-protocol PGD at the matched budget, their number was gradient
       masking / weak-attack artifact, not robustness.
     - unbounded PGD (eps=0.5, 50 steps) sanity check: robust acc must collapse to ~0
       (Carlini et al. 2019 masking audit).

Resumable: each (attack, eps) result is written to the json as soon as it is computed.

Usage (real run):  CUDA_VISIBLE_DEVICES=0 e2cnn_env/bin/python b1_eval.py --variant cascaded --seed 0
Smoke (CPU only): CUDA_VISIBLE_DEVICES="" e2cnn_env/bin/python b1_eval.py --smoke
"""
import argparse, json, os, time, torch, torch.nn as nn, torch.nn.functional as F
from b1_common import (VARIANTS, RESDIR, load_their_model_class, load_their_attacks,
                       their_loaders, pixel_testset, PixelSpaceModel, repo_sha)

THEIR_EPS_GRID = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08,
                  0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15]      # their *_test.py grid
AA_EPS = [0.01, 0.015, 0.03]        # 0.015 pixel == their 0.03 normalized budget

def their_attack_eval(model, loader, attack_fn, eps, device, max_n=None):
    """Their evaluate_under_attack loop, verbatim semantics (accuracy on adv examples)."""
    model.eval()
    correct = total = 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        adv = attack_fn(model, images, labels, eps)
        with torch.no_grad():
            pred = model(adv).argmax(1)
        total += labels.size(0); correct += (pred == labels).sum().item()
        if max_n and total >= max_n:
            break
    return 100.0 * correct / total

def clean_acc(model, loader, device, max_n=None):
    model.eval(); correct = total = 0
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            correct += (model(images).argmax(1) == labels).sum().item()
            total += labels.size(0)
            if max_n and total >= max_n:
                break
    return 100.0 * correct / total

def pgd_pixel(model, X, y, device, eps, steps=40, bs=256):
    """Reference PGD in [0,1] pixel space: CE, random start, alpha=eps/4, proper clamping."""
    model.eval(); alpha = eps / 4; correct = 0
    for i in range(0, len(X), bs):
        xb, yb = X[i:i+bs].to(device), y[i:i+bs].to(device)
        delta = torch.empty_like(xb).uniform_(-eps, eps)
        delta = (torch.clamp(xb + delta, 0, 1) - xb)
        for _ in range(steps):
            delta.requires_grad_(True)
            loss = F.cross_entropy(model(xb + delta), yb)
            g, = torch.autograd.grad(loss, delta)
            delta = (delta + alpha * g.sign()).clamp(-eps, eps).detach()
            delta = (torch.clamp(xb + delta, 0, 1) - xb).detach()
        with torch.no_grad():
            correct += (model(xb + delta).argmax(1) == yb).sum().item()
    return 100.0 * correct / len(X)

def autoattack_pixel(model, X, y, device, eps, n, bs=256, smoke=False):
    from autoattack import AutoAttack
    Xa, ya = X[:n].to(device), y[:n].to(device)
    if smoke:
        adv = AutoAttack(model, norm="Linf", eps=eps, version="custom", device=device, verbose=False)
        adv.attacks_to_run = ["apgd-ce"]; adv.apgd.n_iter = 10
    else:
        adv = AutoAttack(model, norm="Linf", eps=eps, version="standard", device=device, verbose=True)
    adv.seed = 0
    xadv = adv.run_standard_evaluation(Xa, ya, bs=bs)
    with torch.no_grad():
        return 100.0 * (model(xadv).argmax(1) == ya).float().mean().item()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="cascaded", choices=list(VARIANTS))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--ckpt", default=None, help="checkpoint path (default: RESDIR/<variant>_s<seed>.pth)")
    ap.add_argument("--n_aa", type=int, default=1000)
    ap.add_argument("--n_pgd_ref", type=int, default=1000)
    ap.add_argument("--their_eps", default=None, help="comma list; default = their full grid")
    ap.add_argument("--aa_eps", default=None, help="comma list; default = 0.01,0.015,0.03")
    ap.add_argument("--smoke", action="store_true", help="CPU plumbing test: tiny n, 1 eps, apgd-ce only")
    a = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tag = f"{a.variant}_s{a.seed}" + ("_smoke" if a.smoke else "")
    ckpt = a.ckpt or str(RESDIR / f"{tag}.pth")
    out_path = RESDIR / f"{tag}_eval.json"

    their_eps = [float(x) for x in a.their_eps.split(",")] if a.their_eps else THEIR_EPS_GRID
    aa_eps = [float(x) for x in a.aa_eps.split(",")] if a.aa_eps else AA_EPS
    if a.smoke:
        their_eps, aa_eps = [0.03], [0.015]

    Model, _ = load_their_model_class(a.variant, device)
    model = Model().to(device)
    state = torch.load(ckpt, map_location=device)
    # Their test file loads with strict=False because e2cnn R2Conv registers `filter` /
    # `expanded_bias` buffers that a train-mode checkpoint does not contain (they are
    # deterministically recomputed from the weights on .eval()). We do the same but VERIFY
    # that these auto-recomputed buffers are the ONLY tolerated mismatch (their blanket
    # strict=False could silently mask real architecture mismatches).
    model.train()
    missing, unexpected = model.load_state_dict(state, strict=False)
    allowed = {n for n, _ in model.named_buffers() if n.endswith(("filter", "expanded_bias"))}
    assert not unexpected and set(missing) <= allowed, \
        f"checkpoint mismatch beyond e2cnn buffers: missing={missing} unexpected={unexpected}"
    model.eval()                                  # triggers e2cnn filter re-expansion from loaded weights
    criterion = nn.CrossEntropyLoss()
    fgsm_attack, pgd_attack = load_their_attacks(a.variant, device, criterion)
    wrapped = PixelSpaceModel(model).to(device).eval()

    res = json.load(open(out_path)) if out_path.exists() else {}
    res.setdefault("meta", {"tag": tag, "ckpt": ckpt, "their_repo_sha": repo_sha(),
        "torch": torch.__version__, "n_aa": a.n_aa, "n_pgd_ref": a.n_pgd_ref,
        "note": ("their attacks: NORMALIZED [-1,1] space, clamp[0,1] quirk kept verbatim; "
                 "pixel-space eps*2 = their normalized eps (their 0.03 == pixel 0.015)")})
    res.setdefault("their_protocol", {}); res.setdefault("pixel_space", {})
    def save():
        json.dump(res, open(out_path, "w"), indent=1)

    smoke_n = 32 if a.smoke else None
    _, te_norm = their_loaders(train=False, smoke_n=smoke_n or 0)
    Xp, yp = pixel_testset(n=smoke_n or max(a.n_aa, a.n_pgd_ref))

    # ---- A. their protocol ----
    if "clean" not in res["their_protocol"]:
        res["their_protocol"]["clean"] = clean_acc(model, te_norm, device)
        print(f"[b1_eval] clean (their loader) = {res['their_protocol']['clean']:.2f}%", flush=True)
        save()
    for eps in their_eps:
        for att_name, att in (("fgsm", fgsm_attack), ("pgd40", pgd_attack)):
            k = f"{att_name}_{eps}"
            if k in res["their_protocol"]:
                continue
            t0 = time.time()
            res["their_protocol"][k] = their_attack_eval(model, te_norm, att, eps, device)
            print(f"[b1_eval] THEIR {att_name} eps={eps}: {res['their_protocol'][k]:.2f}% "
                  f"({time.time()-t0:.0f}s)", flush=True)
            save()

    # ---- B. pixel space ----
    if "clean_n" not in res["pixel_space"]:
        with torch.no_grad():
            cc = sum((wrapped(Xp[i:i+256].to(device)).argmax(1) == yp[i:i+256].to(device)).sum().item()
                     for i in range(0, len(Xp), 256))
        res["pixel_space"]["clean_n"] = 100.0 * cc / len(Xp)
        save()
    for eps in aa_eps:
        k = f"pgdref40_{eps}"
        if k not in res["pixel_space"]:
            t0 = time.time()
            res["pixel_space"][k] = pgd_pixel(wrapped, Xp[:a.n_pgd_ref], yp[:a.n_pgd_ref], device, eps,
                                              steps=5 if a.smoke else 40)
            print(f"[b1_eval] PIXEL pgd-ref eps={eps}: {res['pixel_space'][k]:.2f}% "
                  f"({time.time()-t0:.0f}s)", flush=True)
            save()
    if "unbounded_pgd" not in res["pixel_space"] and not a.smoke:
        res["pixel_space"]["unbounded_pgd"] = pgd_pixel(wrapped, Xp[:a.n_pgd_ref], yp[:a.n_pgd_ref],
                                                        device, eps=0.5, steps=50)
        print(f"[b1_eval] unbounded PGD (eps=0.5) = {res['pixel_space']['unbounded_pgd']:.2f}% "
              f"(masking check: must be ~0)", flush=True)
        save()
    for eps in aa_eps:
        k = f"aa_{eps}"
        if k not in res["pixel_space"]:
            t0 = time.time()
            n = 16 if a.smoke else a.n_aa
            res["pixel_space"][k] = autoattack_pixel(wrapped, Xp, yp, device, eps, n, smoke=a.smoke)
            print(f"[b1_eval] AUTOATTACK eps={eps} n={n}: {res['pixel_space'][k]:.2f}% "
                  f"({time.time()-t0:.0f}s)", flush=True)
            save()

    print(f"[b1_eval] DONE -> {out_path}", flush=True)
    print(json.dumps(res, indent=1))

if __name__ == "__main__":
    main()
