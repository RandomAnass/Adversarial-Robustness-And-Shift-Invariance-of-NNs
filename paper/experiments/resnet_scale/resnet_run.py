#!/usr/bin/env python3
"""
ResNet-scale dissection runner. One cell = (dataset, mode, arm, width, seed).
Per cell: build -> train (resnet_train.train_cell) -> full eval (reusing the validated small-net
harness) -> gradient-masking audit -> save JSON + per-epoch curves + per-sample radii/margins (npz)
+ best checkpoint + config + env stamp + val split. Resumable (.done markers); the driver reruns a
failed cell and never stops the campaign. A sanity gate halts NEW launches if the first AT cell is
wildly off-recipe (so a broken recipe cannot silently burn the whole budget).

Usage (always with the venv python + PYTHONNOUSERSITE=1):
  list:   PYTHONNOUSERSITE=1 paper/env/cenv/bin/python resnet_run.py --list
  cell:   PYTHONNOUSERSITE=1 paper/env/cenv/bin/python resnet_run.py --cell <name> --gpu 0
  driver: PYTHONNOUSERSITE=1 paper/env/cenv/bin/python resnet_run.py --driver
"""
import os, sys, json, time, argparse, subprocess, numpy as np, torch
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import build, nparams, ARMS, ALL_ARMS, GRADED_ARMS
from resnet_train import load_data, train_cell, pgd_linf, set_seed, env_stamp
from cifar_dissection import shift_consistency, pgd_acc, autoattack_acc, accuracy, correct_mask

RESDIR = os.path.join(os.path.dirname(__file__), "..", "..", "results", "resnet_scale")
CKPTDIR = os.path.join(RESDIR, "ckpt"); os.makedirs(CKPTDIR, exist_ok=True)
EPS = 8 / 255; ALPHA = 2 / 255

# ---------------- per-sample eval (arrays, for the detailed analysis) ----------------
def ddn_radii(model, X, y, dev, steps=300, gamma=0.05, eps0=1.0, bs=256):
    """Per-sample min-||delta||_2 (DDN); same algorithm/params as the validated small-net function.
    Returns per-sample best-norm (inf for points never flipped within `steps`; caller must mask)."""
    model.eval(); X, y = X.to(dev), y.to(dev); N = len(X); best = torch.full((N,), float("inf"), device=dev)
    for i in range(0, N, bs):
        xb, yb = X[i:i + bs], y[i:i + bs]; delta = torch.zeros_like(xb)
        eps = torch.full((len(xb),), float(eps0), device=dev); bnorm = torch.full((len(xb),), float("inf"), device=dev)
        for k in range(steps):
            a = 0.01 + 0.99 * (1 + np.cos(np.pi * k / steps)) / 2; delta.requires_grad_(True)
            logits = model(torch.clamp(xb + delta, 0, 1))
            true = logits.gather(1, yb[:, None]).squeeze(1)
            other = logits.clone().scatter_(1, yb[:, None], -1e9).max(1).values
            g, = torch.autograd.grad((other - true).sum(), delta)
            with torch.no_grad():
                adv = logits.argmax(1) != yb; nrm = delta.flatten(1).norm(dim=1)
                upd = adv & (nrm < bnorm); bnorm[upd] = nrm[upd]
                eps = torch.where(adv, eps * (1 - gamma), eps * (1 + gamma))
                gn = g / g.flatten(1).norm(dim=1).clamp_min(1e-12)[:, None, None, None]
                delta = delta + a * gn
                dn = delta.flatten(1).norm(dim=1).clamp_min(1e-12)
                delta = torch.clamp(xb + delta / dn[:, None, None, None] * eps[:, None, None, None], 0, 1) - xb
        best[i:i + len(xb)] = bnorm
    return best.cpu().numpy()

def margin_stats(model, X, y, dev, bs=128):
    """Per-sample active logit margin M and ||grad M||_2, ||grad M||_1 (on the given, clean-correct pts)."""
    model.eval(); ms, g2s, g1s = [], [], []
    for i in range(0, len(X), bs):
        xb = X[i:i + bs].to(dev).requires_grad_(True); yb = y[i:i + bs].to(dev)
        logits = model(xb)
        true = logits.gather(1, yb[:, None]).squeeze(1)
        other = logits.clone().scatter_(1, yb[:, None], -1e9).max(1).values
        m = true - other; g, = torch.autograd.grad(m.sum(), xb); gf = g.flatten(1)
        ms.append(m.detach().cpu().numpy()); g2s.append(gf.norm(dim=1).detach().cpu().numpy())
        g1s.append(gf.abs().sum(1).detach().cpu().numpy())
    return np.concatenate(ms), np.concatenate(g2s), np.concatenate(g1s)

# ---------------- gradient-masking audit (Carlini2019; critical for the non-differentiable APS arm) ----------------
def _aa_component(model, X, y, dev, eps, attacks, norm="Linf", n=512, bs=256):
    from autoattack import AutoAttack
    Xa, ya = X[:n].to(dev), y[:n].to(dev)
    adv = AutoAttack(model, norm=norm, eps=eps, version="custom", device=dev, verbose=False)
    adv.seed = 0; adv.attacks_to_run = attacks
    xadv = adv.run_standard_evaluation(Xa, ya, bs=bs)
    with torch.no_grad(): return (model(xadv).argmax(1) == ya).float().mean().item()

def masking_audit(model, X, y, dev, eps=EPS, n=512, full=False):
    Xa, ya = X[:n], y[:n]
    pgd20 = pgd_acc(model, Xa, ya, dev, eps, norm="linf", steps=20)
    pgd100 = pgd_acc(model, Xa, ya, dev, eps, norm="linf", steps=100)
    aa = autoattack_acc(model, Xa, ya, dev, eps, norm="Linf", n=n, version="standard")
    unbounded = pgd_acc(model, Xa, ya, dev, eps=1.0, norm="linf", steps=50)         # large-eps -> must ~0
    res = {"pgd20": pgd20, "pgd100": pgd100, "autoattack": aa, "unbounded_robacc": unbounded}
    # tolerances at the eval noise floor (binomial SE ~2.2% at n=512): a sub-noise PGD100>PGD20 or
    # AA>PGD difference is Monte Carlo noise, not masking. The decisive checks are AA<=PGD (the strong
    # ensemble incl. black-box Square must not be weaker) and unbounded->0.
    ok = aa <= pgd20 + 0.02 and pgd100 <= pgd20 + 0.03 and unbounded < 0.05
    if full:                                       # extra white-box-vs-black-box probe (APS arm: non-diff selection)
        apgd = _aa_component(model, X, y, dev, eps, ["apgd-ce", "apgd-t"], n=n)
        square = _aa_component(model, X, y, dev, eps, ["square"], n=n)
        res.update(apgd_white=apgd, square_black=square); ok = ok and square >= apgd - 0.03
    res["masking_ok"] = bool(ok)
    return res

# ---------------- one cell ----------------
def eval_cell(model, data, dev, mode, arm="standard", n_rad=1000, n_aa=10000):   # full test set (C1 fix)
    Xte, yte = data["Xte"], data["yte"]
    out = {"clean": accuracy(model, Xte, yte, dev), "consist": shift_consistency(model, Xte, dev)}
    cm = correct_mask(model, Xte, yte, dev); Xc, yc = Xte[cm], yte[cm]
    rad = ddn_radii(model, Xc[:n_rad], yc[:n_rad], dev); fin = np.isfinite(rad)   # drop never-flipped from mean
    m, g2, g1 = margin_stats(model, Xc[:n_rad], yc[:n_rad], dev)
    out.update(rr_l2=float(rad[fin].mean()) if fin.any() else float("nan"),
               rr_n=int(fin.sum()), rr_ninf=int((~fin).sum()),
               dec_margin=float(np.mean(m)), dec_L2=float(np.mean(g2)), dec_L1=float(np.mean(g1)),
               dec_etaL=float(np.mean(m) / (np.mean(g2) + 1e-12)))
    persample = {"radius": rad, "margin": m, "gradL2": g2, "gradL1": g1}
    if mode == "at":
        audit = masking_audit(model, Xte, yte, dev, n=min(n_aa, 512), full=(arm in ("aps", "tips")))
        out.update(aa_Linf_8_255=audit["autoattack"], pgd_Linf_8_255=audit["pgd20"], audit=audit)
        out["aa_L2_0_5"] = autoattack_acc(model, Xte, yte, dev, eps=0.5, norm="L2", n=n_aa, version="standard")
        out["pgd_L2_0_5"] = pgd_acc(model, Xte[:n_aa], yte[:n_aa], dev, eps=0.5, norm="l2", steps=20)
    else:                                       # standard: small-eps AA-vs-radius calibration (masking check)
        cal = {}
        for e in (0.05, 0.10, 0.15, 0.25):
            cal[f"aa_L2_{e}"] = autoattack_acc(model, Xte, yte, dev, eps=e, norm="L2", n=512, version="custom")
            cal[f"radfrac_{e}"] = float((rad[fin] > e).mean()) if fin.any() else float("nan")
        out["calibration"] = cal
    return out, persample

def run_cell(name, gpu):
    import autoattack  # fail fast if the wrong interpreter is used (no autoattack / broken CUDA)
    assert torch.cuda.is_available(), "CUDA unavailable -- use the venv python with PYTHONNOUSERSITE=1"
    cfg = CELLS[name]; done = os.path.join(RESDIR, name + ".done")
    if os.path.exists(done):
        print(f"[{name}] already done, skipping", flush=True); return
    dev = f"cuda:{gpu}"; torch.cuda.set_device(gpu); t0 = time.time(); set_seed(cfg["seed"])
    data = load_data(cfg["dataset"], seed=cfg["seed"])
    model = build(cfg["arm"], width=cfg["width"], num_classes=data["n_classes"])
    ckpt = os.path.join(CKPTDIR, name + ".pt")
    best_state, curves, best_ep = train_cell(
        model, data, dev, mode=cfg["mode"], arm=cfg["arm"], seed=cfg["seed"],
        epochs=cfg["epochs"], milestones=cfg["milestones"], patience=cfg["patience"], ckpt_path=ckpt,
        log_cb=lambda r: print(f"[{name}] ep{r['epoch']} loss{r['train_loss']:.3f} "
                               f"vc{r['val_clean']:.3f} vr{r['val_robust']:.3f}", flush=True))
    model.load_state_dict(best_state); model.to(dev).eval()
    res, persample = eval_cell(model, data, dev, cfg["mode"], arm=cfg["arm"])
    res.update(arm=cfg["arm"], w=cfg["width"], seed=cfg["seed"], dataset=cfg["dataset"], mode=cfg["mode"],
               params=nparams(model), best_epoch=best_ep, n_epochs_run=len(curves),
               wall_s=time.time() - t0, env=env_stamp(), config=dict(cfg),
               val_idx=data["val_idx"], n_train=len(data["Xtr"]))
    json.dump(res, open(os.path.join(RESDIR, name + ".json"), "w"), indent=1, default=float)
    json.dump(curves, open(os.path.join(RESDIR, name + "_curves.json"), "w"))
    np.savez_compressed(os.path.join(RESDIR, name + "_persample.npz"), **persample)
    open(done, "w").write(f"{time.time()-t0:.0f}s best_ep={best_ep}")
    print(f"[{name}] DONE {res['wall_s']/60:.1f}min clean={res['clean']:.3f} consist={res['consist']:.3f} "
          f"rr={res['rr_l2']:.3f} etaL={res['dec_etaL']:.4f} "
          f"{'aa='+format(res.get('aa_Linf_8_255',float('nan')),'.3f')+' maskOK='+str(res.get('audit',{}).get('masking_ok')) if cfg['mode']=='at' else ''}", flush=True)

# ---------------- value-ordered cell registry ----------------
AT_SCHED = dict(epochs=100, milestones=(50, 75), patience=15)      # ~65-85 effective epochs (early-stop)
STD_SCHED = dict(epochs=80, milestones=(40, 60), patience=15)
CELLS = {}
def _wt(w): return "" if w == 1.0 else f"_w{w}"
def _add(name, dataset, mode, arm, width, seed, sched):
    CELLS[name] = dict(dataset=dataset, mode=mode, arm=arm, width=width, seed=seed, **sched)
    return name

ORDER = []
# Phase 1+2 interleaved: headline CIFAR-10 AT (w1.0,s0) overlapped with the cheap standard scatter,
# so RQ1 completes early on one GPU while the expensive AT headline runs on the other.
for arm in ["aps", "blurpool", "standard", "aug"]:                                   # aps first (slowest)
    ORDER.append(_add(f"c10at_{arm}_s0", "cifar10", "at", arm, 1.0, 0, AT_SCHED))
    ORDER.append(_add(f"c10std_{arm}_s0", "cifar10", "std", arm, 1.0, 0, STD_SCHED))
for arm in ARMS:
    ORDER.append(_add(f"c10std_{arm}_w0.5_s0", "cifar10", "std", arm, 0.5, 0, STD_SCHED))
# Phase 3: complete the 8-cell AT scatter (second width) for seed0
for arm in ARMS:
    ORDER.append(_add(f"c10at_{arm}_w0.5_s0", "cifar10", "at", arm, 0.5, 0, AT_SCHED))
# Phase 4: AT confidence intervals (seed 1, both widths)
for w in (1.0, 0.5):
    for arm in ARMS:
        ORDER.append(_add(f"c10at_{arm}{_wt(w)}_s1", "cifar10", "at", arm, w, 1, AT_SCHED))
# Phase 5: padding-confound ablation (zero-pad standard), std + 1 AT
ORDER.append(_add("c10std_stdzero_s0", "cifar10", "std", "stdzero", 1.0, 0, STD_SCHED))
ORDER.append(_add("c10at_stdzero_s0", "cifar10", "at", "stdzero", 1.0, 0, AT_SCHED))
# Phase 6: CIFAR-100 (supportive, fewer seeds), w1.0 s0
for arm in ARMS:
    ORDER.append(_add(f"c100at_{arm}_s0", "cifar100", "at", arm, 1.0, 0, AT_SCHED))
# Phase 7 (if time): AT seed 2 for tighter CIs
for arm in ARMS:
    ORDER.append(_add(f"c10at_{arm}_s2", "cifar10", "at", arm, 1.0, 2, AT_SCHED))

# Low-invariance arms to widen the shift-consistency axis (the mechanistic test of why the
# consistency anti-prediction is weak at ResNet scale). Registered but kept OUT of ORDER so the
# already-running driver ignores them; run post-main via --cell. stdzero w0.5 + maxpool both widths,
# std + AT, seed 0 -> 4 new low-consistency AT points + their std counterparts.
EXTRA_LOWINV = []
for arm in ["stdzero", "maxpool"]:
    for w in (1.0, 0.5):
        for mode, sch in (("std", STD_SCHED), ("at", AT_SCHED)):
            nm = f"c10{mode}_{arm}{_wt(w)}_s0"
            if nm not in CELLS:
                _add(nm, "cifar10", mode, arm, w, 0, sch)
            EXTRA_LOWINV.append(nm)

# S1a head-to-head: TIPS (Saha&Gokhale WACV2025) as arm `tips`, capacity-comparable to the core arms,
# run through OUR pipeline. Registered but kept OUT of ORDER (the main driver ignores them; run
# post-main via --cell). AT grid mirrors the core-4: w{1.0} seeds{0,1,2} + w{0.5} seeds{0,1}; std for
# the weak-attack (FGSM/PGD-small-eps) regime at both widths seed0.
TIPS_CELLS = []
for (w, seed) in [(1.0, 0), (1.0, 1), (1.0, 2), (0.5, 0), (0.5, 1)]:
    nm = _add(f"c10at_tips{_wt(w)}_s{seed}", "cifar10", "at", "tips", w, seed, AT_SCHED); TIPS_CELLS.append(nm)
for w in (1.0, 0.5):
    nm = _add(f"c10std_tips{_wt(w)}_s0", "cifar10", "std", "tips", w, 0, STD_SCHED); TIPS_CELLS.append(nm)

# A5-opt: seed-1 replicate of the weak-attack regime (tips_weakattack.py --seed 1 needs std-trained
# ckpts at seed 1). Registered but kept OUT of ORDER (run via --cell from external/b1_batch.sh).
WEAK_S1_CELLS = []
for arm in ["standard", "blurpool", "aps", "aug", "tips"]:
    nm = f"c10std_{arm}_s1"
    if nm not in CELLS:
        _add(nm, "cifar10", "std", arm, 1.0, 1, STD_SCHED)
    WEAK_S1_CELLS.append(nm)

# POWER grid: graded anti-aliasing arms (blur2=Rect-2, blur5=Bin-5, blur7=Bin-7) densify the invariance
# axis so the threat-matched dissection reaches n>=20 cells with tighter, better-separated CIs. AT, both
# widths, 3 seeds. Registered but kept OUT of ORDER (run post-main via --cell).
GRADED_CELLS = []
for arm in GRADED_ARMS:
    for w in (1.0, 0.5):
        for seed in (0, 1, 2):
            nm = _add(f"c10at_{arm}{_wt(w)}_s{seed}", "cifar10", "at", arm, w, seed, AT_SCHED)
            GRADED_CELLS.append(nm)

# ---------------- driver ----------------
def _sanity_fail():
    """After the first CIFAR-10 AT headline cell finishes, check it is not wildly off-recipe.
    Gate on the .done marker (written last) and guard against a mid-write JSON read."""
    if not os.path.exists(os.path.join(RESDIR, "c10at_aps_s0.done")): return False
    try: r = json.load(open(os.path.join(RESDIR, "c10at_aps_s0.json")))
    except Exception: return False
    # integrity gate: a MISSING field defaults toward "flag", not "accept" (the audit lesson).
    bad = (r.get("clean", 0) < 0.6 or r.get("aa_Linf_8_255", 0) < 0.20
           or not r.get("audit", {}).get("masking_ok", False))
    if bad: open(os.path.join(RESDIR, "SANITY_FAIL.marker"), "w").write(json.dumps(
        {k: r.get(k) for k in ("clean", "aa_Linf_8_255", "pgd_Linf_8_255")} | {"audit": r.get("audit")}))
    return bad

def driver(ngpu=2, max_reruns=1):
    pending = [c for c in ORDER if not os.path.exists(os.path.join(RESDIR, c + ".done"))]
    print(f"[driver] {len(pending)}/{len(ORDER)} cells pending on {ngpu} GPU(s)", flush=True)
    running = {}; reruns = {}; free = list(range(ngpu)); gated = False
    def launch(cell, gpu):
        env = dict(os.environ, PYTHONNOUSERSITE="1")
        logf = open(os.path.join(RESDIR, cell + ".log"), "a")
        p = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--cell", cell, "--gpu", str(gpu)],
                             stdout=logf, stderr=subprocess.STDOUT, env=env)
        running[gpu] = (cell, p, logf); print(f"[driver] launch {cell} gpu{gpu}", flush=True)
    while pending or running:
        while free and pending and not gated:
            launch(pending.pop(0), free.pop(0))
        time.sleep(15)
        for gpu, (cell, p, logf) in list(running.items()):
            if p.poll() is None: continue
            logf.close(); ok = os.path.exists(os.path.join(RESDIR, cell + ".done"))
            if not ok and reruns.get(cell, 0) < max_reruns:
                reruns[cell] = reruns.get(cell, 0) + 1; pending.append(cell)
                print(f"[driver] {cell} FAILED rc={p.returncode}, rerun {reruns[cell]}/{max_reruns}", flush=True)
            elif not ok:
                print(f"[driver] {cell} FAILED permanently rc={p.returncode}; continuing", flush=True)
            else:
                print(f"[driver] {cell} done", flush=True)
            del running[gpu]; free.append(gpu)
        if not gated and _sanity_fail():
            gated = True; print("[driver] SANITY_FAIL on first AT cell -- halting NEW launches; "
                                "letting running finish. Inspect SANITY_FAIL.marker.", flush=True)
        if gated and not running:
            print("[driver] gated and all running cells finished; exiting.", flush=True); break
    print("[driver] all cells processed", flush=True)
    open(os.path.join(RESDIR, "DRIVER_DONE.marker"), "w").write("done")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell"); ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--driver", action="store_true"); ap.add_argument("--list", action="store_true")
    ap.add_argument("--ngpu", type=int, default=2); a = ap.parse_args()
    if a.list:
        for i, c in enumerate(ORDER): print(f"{i:2d} {c:26s} {CELLS[c]}")
        print(f"total {len(ORDER)} cells")
    elif a.driver: driver(a.ngpu)
    elif a.cell: run_cell(a.cell, a.gpu)
    else: ap.print_help()
