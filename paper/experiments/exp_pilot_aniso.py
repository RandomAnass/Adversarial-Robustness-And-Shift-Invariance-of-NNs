#!/usr/bin/env python3
"""
PILOT: an ANISOTROPIC, LOCAL, DEFICIT-TARGETED margin-sensitivity regularizer that tries to thread the
needle the host paper's two prior attempts both missed.

WHAT FAILED BEFORE (host paper, exp_tmreg.py).
  (1) TM-MLR  pen = lam * mean ||grad_x M(x)||_1   (penalty="margin_l1"): raised the threat-matched ratio
      eta/L1 on paper but NOT AutoAttack robustness, because under PGD-AT the per-sample margin M and the
      input-sensitivity ||grad M|| are POSITIVELY coupled (the "self-limiting coupling"): a global,
      isotropic gradient penalty flattens the margin in LOCKSTEP with the gradient, so the certified
      radius r = M/||grad M||_1 barely moves. It pays a capacity tax everywhere and buys nothing.
  (2) RATIO   pen = lam * mean ( ||grad_x M(x)||_1 / M(x) )  (penalty="margin_norm_l1"): tried to break the
      coupling by dividing by the (LIVE) margin, but the optimiser games it the cheap way -- shrink M
      toward zero EVERYWHERE -> the ratio's denominator collapses, the model degenerates to a near-constant
      classifier (clean acc -> chance). Letting the margin appear in the DENOMINATOR with gradient is the trap.

THE OPEN SEAM (literature). Every clean "margin without sharpening" method caps the Lipschitz constant
GLOBALLY + ISOTROPICALLY (spectral-norm / Lipschitz nets, Tsuzuku, Cohen RS) and pays a capacity tax.
But the robustness certificate r_i = M_i / ||grad_x M_i||_q only needs sensitivity controlled LOCALLY (near
the data), ANISOTROPICALLY (in the runner-up / margin direction, captured by the threat-matched dual norm
q=1 for Linf), and ONLY WHERE robustness is DEFICIENT (r_i below a target). Spend capacity only on the
under-robust tail; leave already-robust points alone.

THE FIX (this file).
  PRIMARY  variant="hinge"  (hinge-to-target, on CLEAN x):
        pen = mean( relu( ||grad_x M(x)||_1  -  M_detach / r_target ) )
     The per-sample certified Linf radius is r_i = M_i/||grad M_i||_1, so the hinge is active EXACTLY for
     points with r_i < r_target (the under-robust tail) and is identically zero -- no gradient, no capacity
     tax -- for already-robust points. The crucial fix vs failure (2): the margin enters only through
     M_detach, a DETACHED CONSTANT target M_i/r_target. The penalty therefore CANNOT be gamed by shrinking
     the margin (doing so does not lower a constant target), so it pushes ||grad M||_1 DOWN on the deficient
     tail without the ratio-collapse. And vs failure (1): robust points are untouched, so the margin is not
     globally flattened in lockstep.
  ABLATION variant="directional" (on the PGD ADVERSARIAL point x_adv):
        pen = mean( ||grad_x M(x_adv)||_1 )
     Same threat-matched margin-gradient penalty as TM-MLR but evaluated ON THE THREAT BALL (at x_adv)
     instead of at clean x. Tests whether LOCATING the sensitivity control on the threat ball (where the
     certificate must hold) -- rather than at clean x -- is what TM-MLR was missing. It deliberately keeps
     the plain mean form (no hinge) so the ONLY change vs margin_l1 is the evaluation point.
  BASELINE variant="vanilla": the host's none/relu PGD-AT (cifar_at.adv_train VERBATIM).

The per-sample margin M(x) = logit_y - max_{j!=y} logit_j (differentiable a.e.). The penalty gradient uses
create_graph=True (double backprop into the weights), reusing the exact mechanism in exp_tmreg.py /
exp3_lipschitz_at.py. Per-sample gradients g_i = grad_x M_i are read off from grad(M.sum()) (BN cross-sample
coupling ignored during training, same convention as exp_tmreg.margin_norm_l1; at EVAL the model is in
eval-mode so the reported per-sample radii are exact).

Recipe pieces are reused VERBATIM from cifar_at.adv_train (CIFAR Linf eps=8/255, 7 steps, alpha=2/255,
cosine SGD, horizontal-flip aug, 30 epochs) and cifar_at.pgd_linf; build/eval (accuracy, autoattack_acc,
pgd_acc, etaL_decomposition, robust_radius_l2, load_data, ...) come from cifar_dissection; the per-sample
coupling Spearman is imported VERBATIM from exp_pilot_smooth. Standard arm only. Progressive per-cell save
+ resume; the tmreg/exp3-style OOM-robust per-GPU worker pool; AA_BS honored.

MASKING CHECK: AutoAttack must be <= matched PGD. A variant whose PGD >> AA is gradient-masking and is
flagged FAILED (mask_ok=false), not a win.

Smoke:    PYTHONNOUSERSITE=1 ../env/cenv/bin/python exp_pilot_aniso.py --smoke
HP scan:  PYTHONNOUSERSITE=1 ../env/cenv/bin/python exp_pilot_aniso.py --hpscan --gpus 2 --workers_per_gpu 2
Full:     PYTHONNOUSERSITE=1 AA_BS=500 ../env/cenv/bin/python exp_pilot_aniso.py \
              --variants vanilla hinge directional --hinge_rt 0.05 --hinge_lam 1.0 --dir_lam 1.0 \
              --widths 32 48 --seeds 2 --aa_n 2000 --gpus 2 --workers_per_gpu 2
"""
import argparse, os, json, time, numpy as np, torch, torch.nn.functional as F
import torch.multiprocessing as mp
from cifar_dissection import (build, load_data, dataset_stats, in_channels, accuracy, correct_mask,
                              shift_consistency, robust_radius_l2, etaL_decomposition, autoattack_acc,
                              pgd_acc, nparams, circular_roll)
from cifar_at import pgd_linf, adv_train
from exp_pilot_smooth import coupling_spearman           # per-sample margin<->sensitivity coupling, VERBATIM

RESDIR = os.path.join(os.path.dirname(__file__), "..", "results")
PARTDIR = os.path.join(RESDIR, "at_partial", "pilot_aniso")
VARIANTS = ("vanilla", "hinge", "directional")
CHANCE = 0.1                                              # CIFAR-10 / MNIST / Fashion: 10 classes

# ---------------- the regularizer: PGD-AT + anisotropic/local/deficit-targeted margin penalty ----------------
def train_pilot(model, X, y, dev, epochs, seed, eps, alpha, steps, variant="hinge", r_target=0.05,
                lam=1.0, warmup_ep=0, bs=128, lr=0.1, wd=5e-4, aug=True, shift_aug=False):
    """PGD-AT (Linf) outer-min on x_adv plus the selected margin-gradient penalty:
        variant="hinge"       -> lam * mean relu( ||grad_x M(x)||_1 - M_detach / r_target )   on CLEAN x
        variant="directional" -> lam * mean ||grad_x M(x_adv)||_1                              on x_adv
        variant="vanilla"     -> no penalty (use cifar_at.adv_train directly instead; never reached here)
    Per-sample g_i = grad_x M_i is taken from grad(M.sum(), create_graph=True) (double backprop into the
    weights). For the hinge the margin appears ONLY as the DETACHED constant target M_detach/r_target, so
    the penalty cannot be gamed by shrinking the margin (the fix vs the ratio collapse)."""
    assert variant in ("hinge", "directional"), f"train_pilot handles hinge/directional; got {variant!r}"
    torch.manual_seed(seed); model = model.to(dev).train()
    opt = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9, weight_decay=wd, nesterov=True)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    X, y = X.to(dev), y.to(dev); n = len(X)
    for ep in range(epochs):
        # penalty WARMUP: keep it OFF for the first warmup_ep epochs so plain PGD-AT establishes a real
        # margin first (early on M~0 makes the detached target M/r_target ~0, so an immediately-on hinge
        # degenerates to a global ||grad M||_1 crush -> collapse). Off by default (warmup_ep=0).
        use_pen = (lam > 0) and (ep >= warmup_ep)
        perm = torch.randperm(n, device=dev)
        for i in range(0, n, bs):
            idx = perm[i:i + bs]; xb = X[idx]; yb = y[idx]
            if aug:
                flip = torch.rand(xb.size(0), device=dev) < 0.5
                xb = torch.where(flip[:, None, None, None], xb.flip(-1), xb)
            if shift_aug: xb = circular_roll(xb, 4)
            x_adv = pgd_linf(model, xb, yb, eps, alpha, steps)          # inner max (Linf PGD)
            opt.zero_grad(set_to_none=True)
            loss = F.cross_entropy(model(x_adv), yb)                    # outer min (AT)
            if use_pen:
                xp = (xb if variant == "hinge" else x_adv).clone().detach().requires_grad_(True)
                logits = model(xp)
                true = logits.gather(1, yb[:, None]).squeeze(1)
                other = logits.clone().scatter_(1, yb[:, None], -1e9).max(1).values
                Mps = true - other                                     # per-sample margin
                g, = torch.autograd.grad(Mps.sum(), xp, create_graph=True)
                gl1 = g.flatten(1).abs().sum(1)                        # per-sample ||grad M_i||_1 (Linf dual)
                if variant == "hinge":
                    target = Mps.detach() / r_target                   # DETACHED constant -> cannot be gamed
                    pen = F.relu(gl1 - target).mean()                  # active only where r_i < r_target
                else:                                                  # directional: plain mean L1 on threat ball
                    pen = gl1.mean()
                loss = loss + lam * pen
            loss.backward(); opt.step()
        sched.step()
    return model.eval()

# ---------------- per-sample certified-radius diagnostic (under-robust tail) ----------------
def persample_radius(model, X, y, dev, n_max=2000, bs=128):
    """On clean-CORRECT points (eval mode -> per-sample gradients are exact), return numpy arrays
    M (margin), L1 (||grad_x M||_1) and r = M/L1 (the per-sample local Linf certified radius)."""
    cm = correct_mask(model, X, y, dev)
    Xc, yc = X[cm][:n_max], y[cm][:n_max]
    Ms, L1s = [], []
    for i in range(0, len(Xc), bs):
        xb = Xc[i:i + bs].to(dev).requires_grad_(True); yb = yc[i:i + bs].to(dev)
        logits = model(xb)
        true = logits.gather(1, yb[:, None]).squeeze(1)
        other = logits.clone().scatter_(1, yb[:, None], -1e9).max(1).values
        m = true - other
        g, = torch.autograd.grad(m.sum(), xb)
        Ms.append(m.detach().cpu().numpy()); L1s.append(g.flatten(1).abs().sum(1).detach().cpu().numpy())
    M = np.concatenate(Ms) if Ms else np.array([]); L1 = np.concatenate(L1s) if L1s else np.array([])
    r = M / np.clip(L1, 1e-12, None)
    return M, L1, r

def tail_stats(model, X, y, dev, r_target, n_max=2000):
    """Mean ||grad M||_1 and count for the UNDER-ROBUST tail (per-sample radius r_i < r_target).
    The whole point of the hinge is to lower exactly this number relative to vanilla."""
    M, L1, r = persample_radius(model, X, y, dev, n_max=n_max)
    if len(r) == 0: return dict(frac_under=float("nan"), tail_L1=float("nan"), med_r=float("nan"), n=0)
    under = r < r_target
    return dict(frac_under=float(under.mean()),
                tail_L1=float(L1[under].mean()) if under.any() else 0.0,
                med_r=float(np.median(r)), n=int(len(r)))

# ---------------- progressive per-cell save + resume ----------------
# The canonical job tuple is (variant, r_target, lam, warmup, w, seed); the filename encodes all of them so
# warmup / non-warmup cells never collide. _jf(*job) is the single source of truth for resume + reload.
def _g(x): return f"{float(x):g}"
def _hp(variant, r_target, lam, warmup):
    if variant == "vanilla":     s = "base"
    elif variant == "hinge":     s = f"rt{_g(r_target)}_l{_g(lam)}"
    else:                        s = f"l{_g(lam)}"        # directional
    return s + (f"_wu{int(warmup)}" if warmup else "")
def _jf(variant, r_target, lam, warmup, w, seed):
    return os.path.join(PARTDIR, f"{variant}_{_hp(variant, r_target, lam, warmup)}_w{w}_s{seed}.json")
def _save(out):
    os.makedirs(PARTDIR, exist_ok=True)
    p = _jf(out["variant"], out["r_target"], out["lam"], out["warmup_ep"], out["w"], out["seed"])
    tmp = p + ".tmp"
    json.dump(out, open(tmp, "w"), default=float); os.replace(tmp, p)        # atomic publish

# ---------------- one cell: PGD-AT (+optional penalty) + full eval ----------------
def run_job(task):
    gpu, variant, r_target, lam, warmup, w, seed, A = task
    dev = f"cuda:{gpu}" if (gpu is not None and torch.cuda.is_available()) else "cpu"
    if dev.startswith("cuda"): torch.cuda.set_device(gpu)
    ds = A["dataset"]
    Xtr, ytr, Xte, yte = load_data(ds, A["n"], A["ntest"], seed=0)
    nmean, nstd = dataset_stats(ds)
    net = build("standard", w, in_ch=in_channels(ds), norm_mean=nmean, norm_std=nstd)
    if variant == "vanilla":            # host's none/relu PGD-AT, recipe VERBATIM
        model = adv_train(net, Xtr, ytr, dev, epochs=A["epochs"], seed=seed, eps=A["eps"],
                          alpha=A["alpha"], steps=A["steps"], norm="linf", aug=A["flip"], shift_aug=False)
    else:
        model = train_pilot(net, Xtr, ytr, dev, epochs=A["epochs"], seed=seed, eps=A["eps"],
                            alpha=A["alpha"], steps=A["steps"], variant=variant, r_target=r_target,
                            lam=lam, warmup_ep=warmup, aug=A["flip"], shift_aug=False)
    out = dict(variant=variant, arm="standard", r_target=float(r_target), lam=float(lam),
               warmup_ep=int(warmup), w=w, seed=seed, dataset=ds, params=nparams(model),
               eps=A["eps"], alpha=A["alpha"], steps=A["steps"], epochs=A["epochs"], n=A["n"])
    out["clean"] = accuracy(model, Xte, yte, dev)
    out["consist"] = shift_consistency(model, Xte, dev)
    cm = correct_mask(model, Xte, yte, dev); Xc, yc = Xte[cm], yte[cm]
    out["rr_l2"] = robust_radius_l2(model, Xc[:A["rad_n"]], yc[:A["rad_n"]], dev)
    out["rr_n"] = int(min(A["rad_n"], len(Xc)))
    out.update({("dec_" + k): v for k, v in etaL_decomposition(model, Xte, yte, dev).items()})
    out["dec_etaL_matched"] = out["dec_margin"] / (out["dec_L1"] + 1e-12)    # threat-matched ratio (Linf->L1)
    out["coupling_spearman"] = coupling_spearman(model, Xte, yte, dev, n_max=A["coupling_n"])
    # under-robust-tail diagnostic: was the gradient actually lowered on the deficient tail?
    rt_diag = r_target if variant == "hinge" else A.get("diag_rt", 0.05)
    out.update({("tail_" + k): v for k, v in tail_stats(model, Xte, yte, dev, rt_diag,
                                                        n_max=A["coupling_n"]).items()})
    if A["aa_n"] > 0:
        out["pgd_Linf_8_255"] = pgd_acc(model, Xte[:A["aa_n"]], yte[:A["aa_n"]], dev, A["eval_eps"],
                                        "linf", steps=A["pgd_steps"])
        out["aa_Linf_8_255"] = autoattack_acc(model, Xte, yte, dev, A["eval_eps"], "Linf",
                                              n=A["aa_n"], version=A["aa_version"])
        out["mask_ok"] = bool(out["aa_Linf_8_255"] <= out["pgd_Linf_8_255"] + 0.02)   # AA must be <= PGD
    _save(out); return out

# ---------------- tmreg/exp3-style per-GPU worker pool (OOM-robust; saves to disk) ----------------
def _worker(wid, gpu, n_workers, task_q, A):
    try:
        avail = sorted(os.sched_getaffinity(0)); per = max(1, len(avail) // n_workers)
        my = avail[wid * per:(wid + 1) * per] or avail[:per]
        os.sched_setaffinity(0, set(my)); torch.set_num_threads(max(1, len(my) // 2))
    except Exception:
        torch.set_num_threads(max(1, (os.cpu_count() or 8) // max(1, n_workers)))
    while True:
        item = task_q.get()
        if item is None: break
        variant, r_target, lam, warmup, w, seed = item
        try:
            run_job((gpu, variant, r_target, lam, warmup, w, seed, A))
        except Exception as e:
            print(f"[w{wid} gpu{gpu}] {(variant, r_target, lam, warmup, w, seed)} FAILED: "
                  f"{type(e).__name__}: {e}", flush=True)

def _run_pool(pending, A, ng, K):
    nw = max(1, ng * K) if ng > 0 else 1
    if pending and ng > 0:
        ctx = mp.get_context("spawn"); task_q = ctx.Queue()
        for t in pending: task_q.put(t)
        for _ in range(nw): task_q.put(None)
        workers = [ctx.Process(target=_worker, args=(wid, wid % ng, nw, task_q, A)) for wid in range(nw)]
        for p in workers: p.start()
        for p in workers: p.join()
    elif pending:
        for j in pending: run_job((None,) + tuple(j) + (A,))

# ---------------- mechanism check: detached-margin hinge + double-backprop reaches the weights ----------------
def _check_mechanism(dev):
    torch.manual_seed(0)
    m = build("standard", 16).to(dev).train()
    x = torch.rand(8, 3, 32, 32, device=dev); yb = torch.randint(0, 10, (8,), device=dev)
    xp = x.clone().detach().requires_grad_(True)
    logits = m(xp)
    true = logits.gather(1, yb[:, None]).squeeze(1)
    other = logits.clone().scatter_(1, yb[:, None], -1e9).max(1).values
    Mps = true - other
    g, = torch.autograd.grad(Mps.sum(), xp, create_graph=True)
    gl1 = g.flatten(1).abs().sum(1)
    target = Mps.detach() / 0.05
    assert not target.requires_grad, "detached target must be a constant (no grad)"
    pen = F.relu(gl1 - target).mean()
    assert pen.grad_fn is not None, "double-backprop graph missing on the hinge penalty"
    pen.backward()
    wgs = [p.grad for p in m.parameters() if p.grad is not None]
    assert wgs and any(float(gg.abs().sum()) > 0 for gg in wgs), "penalty does not reach the weights"
    print("mechanism check OK: detached target is constant, hinge double-backprop reaches the weights",
          flush=True)

# ---------------- smoke: mechanism check + one tiny hinge cell with AA<=PGD ----------------
def _smoke():
    print("=== SMOKE exp_pilot_aniso ===", flush=True)
    gpu = 0 if torch.cuda.is_available() else None
    dev = f"cuda:{gpu}" if gpu is not None else "cpu"
    _check_mechanism(dev)
    A = dict(dataset="cifar", flip=True, n=2000, ntest=1000, epochs=3, eps=8/255, alpha=2/255, steps=7,
             rad_n=200, aa_n=200, aa_version="custom", pgd_steps=10, coupling_n=1000, eval_eps=8/255,
             diag_rt=0.05)
    t0 = time.time()
    out = run_job((gpu, "hinge", 0.05, 1.0, 0, 16, 0, A))
    print(f"\ntrained+evaluated one hinge cell in {time.time()-t0:.0f}s; JSON -> {_jf('hinge',0.05,1.0,0,16,0)}\n",
          flush=True)
    print(json.dumps(out, indent=2, default=float), flush=True)
    # HARD asserts validate the MECHANISM (the point of the smoke): finite coupling + valid JSON +
    # the masking invariant AA<=PGD. Clean acc is NOT asserted: at this deliberately tiny 3-epoch/w16
    # toy a strong hinge can legitimately collapse the margin (that is a finding about lambda, judged at
    # proper scale in --hpscan), not a harness failure.
    assert np.isfinite(out["coupling_spearman"]), "coupling_spearman not finite"
    assert out["mask_ok"], (f"MASKING: AA {out['aa_Linf_8_255']:.3f} > PGD {out['pgd_Linf_8_255']:.3f} "
                            f"+0.02 -> gradient masking")
    if out["clean"] <= CHANCE + 0.02:
        print(f"\nNOTE: clean={out['clean']:.3f} ~ chance at the tiny toy (lam={out['lam']} is strong for a "
              f"3-epoch w16 net; early M~0 makes the hinge act globally). Judge collapse at --hpscan scale.",
              flush=True)
    print(f"\nclean={out['clean']:.3f}  margin={out['dec_margin']:.3f}  L1={out['dec_L1']:.3f}  "
          f"etaL_matched={out['dec_etaL_matched']:.4f}  AA={out['aa_Linf_8_255']:.3f} <= "
          f"PGD={out['pgd_Linf_8_255']:.3f}  coupling={out['coupling_spearman']:.3f}", flush=True)
    print("SMOKE OK (mechanism + JSON + masking validated)", flush=True)

# ---------------- hp scan: primary (hinge) over r_target x lambda, w32, short, no AA ----------------
def _hpscan(a):
    A = dict(dataset=a.dataset, flip=(a.dataset == "cifar"), n=a.scan_n, ntest=2000, epochs=a.scan_epochs,
             eps=8/255, alpha=2/255, steps=7, rad_n=400, aa_n=0, aa_version="custom", pgd_steps=10,
             coupling_n=2000, eval_eps=8/255, diag_rt=0.05)
    wu = a.scan_warmup
    jobs = [("vanilla", 0.0, 0.0, 0, a.scan_w, 0)]                              # reference baseline
    for rt in a.scan_rts:
        for lam in a.scan_lams:
            jobs.append(("hinge", rt, lam, wu, a.scan_w, 0))
    pending = [j for j in jobs if not os.path.exists(_jf(*j))]
    ng = min(a.gpus, torch.cuda.device_count()) if torch.cuda.is_available() else 0
    K = min(a.workers_per_gpu, 2)
    print(f"HP-SCAN hinge (CIFAR-like {a.dataset}, w{a.scan_w}, n={a.scan_n}, {a.scan_epochs} ep, "
          f"warmup={wu}, NO AA): {len(jobs)} cells ({len(jobs)-len(pending)} resumed), "
          f"r_target={a.scan_rts} lambda={a.scan_lams} over {ng or 'CPU'} GPU x {K} workers\n", flush=True)
    load_data(a.dataset, 10, 10)
    t0 = time.time()
    _run_pool(pending, A, ng, K)
    res = [json.load(open(_jf(*j))) for j in jobs if os.path.exists(_jf(*j))]
    by = {(r["variant"], r["r_target"], r["lam"]): r for r in res}
    base = by.get(("vanilla", 0.0, 0.0))
    hdr = (f"{'variant':10s} {'r_tgt':>5s} {'lam':>4s} {'wu':>3s} {'clean':>6s} {'margin':>7s} {'L1':>7s} "
           f"{'etaL':>6s} {'eta/L1':>7s} {'medR':>6s} {'tailL1':>7s} {'verdict':>22s}")
    print("\n" + hdr); print("-" * len(hdr))
    def row(r, verdict=""):
        rt = "-" if r["variant"] == "vanilla" else f"{r['r_target']:.2g}"
        lm = "-" if r["variant"] == "vanilla" else f"{r['lam']:.2g}"
        print(f"{r['variant']:10s} {rt:>5s} {lm:>4s} {r.get('warmup_ep',0):3d} {r['clean']:6.3f} "
              f"{r['dec_margin']:7.3f} {r['dec_L1']:7.2f} {r['dec_etaL']:6.3f} {r['dec_etaL_matched']:7.4f} "
              f"{r.get('tail_med_r', float('nan')):6.3f} {r.get('tail_tail_L1', float('nan')):7.2f} "
              f"{verdict:>22s}")
    if base: row(base, "reference")
    for j in jobs:
        r = by.get((j[0], float(j[1]), float(j[2])))
        if r is None or r["variant"] == "vanilla": continue
        v = "ok"
        if r["clean"] < 0.25 or (base and r["dec_margin"] < 0.4 * base["dec_margin"]):
            v = "MARGIN COLLAPSE"
        elif base and r["dec_L1"] > 0.97 * base["dec_L1"]:
            v = "no-op (L1 ~ vanilla)"
        elif base and r["dec_L1"] < 0.9 * base["dec_L1"]:
            v = "L1 down, margin kept"
        row(r, v)
    if base:
        print(f"\nREAD: want a cell with clean >> chance ({CHANCE}) AND dec_margin not collapsed "
              f"(vanilla margin={base['dec_margin']:.3f}) AND dec_L1 < vanilla L1={base['dec_L1']:.2f} "
              f"(esp. tailL1 down). If EVERY hinge cell is 'MARGIN COLLAPSE' or 'no-op', that is the "
              f"capacity wall: the penalty cannot lower the deficient-tail gradient without flattening "
              f"the margin.")
    stamp = time.strftime("%Y%m%d_%H%M%S")
    fn = os.path.join(RESDIR, f"exp_pilot_aniso_hpscan_{a.dataset}_{stamp}.json")
    json.dump(dict(args=vars(a), results=res), open(fn, "w"), indent=2, default=float)
    print(f"\nwall {time.time()-t0:.0f}s; {len(res)}/{len(jobs)} cells; saved {fn}", flush=True)

# ---------------- full grid ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="+", default=["vanilla", "hinge", "directional"])
    ap.add_argument("--hinge_rt", type=float, default=0.05, help="r_target for the hinge variant (full grid)")
    ap.add_argument("--hinge_lam", type=float, default=1.0)
    ap.add_argument("--warmup_ep", type=int, default=0, help="epochs of plain PGD-AT before the penalty engages (full grid)")
    ap.add_argument("--dir_lam", type=float, default=1.0, help="lambda for the directional variant")
    ap.add_argument("--widths", type=int, nargs="+", default=[32, 48])
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--dataset", default="cifar", choices=["cifar", "mnist", "fashion"])
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--n", type=int, default=50000); ap.add_argument("--ntest", type=int, default=10000)
    ap.add_argument("--rad_n", type=int, default=1000); ap.add_argument("--aa_n", type=int, default=2000)
    ap.add_argument("--coupling_n", type=int, default=3000)
    ap.add_argument("--aa_version", default="standard"); ap.add_argument("--pgd_steps", type=int, default=20)
    ap.add_argument("--gpus", type=int, default=2); ap.add_argument("--workers_per_gpu", type=int, default=2)
    # scan-only knobs
    ap.add_argument("--scan_rts", type=float, nargs="+", default=[0.02, 0.05, 0.1])
    ap.add_argument("--scan_lams", type=float, nargs="+", default=[0.5, 1.0, 2.0])
    ap.add_argument("--scan_w", type=int, default=32); ap.add_argument("--scan_n", type=int, default=8000)
    ap.add_argument("--scan_epochs", type=int, default=8); ap.add_argument("--scan_warmup", type=int, default=0)
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--hpscan", action="store_true")
    a = ap.parse_args()
    for v in a.variants:
        if v not in VARIANTS: raise SystemExit(f"bad variant '{v}'; choose from {VARIANTS}")
    if a.smoke:  _smoke(); return
    if a.hpscan: _hpscan(a); return

    A = dict(dataset=a.dataset, flip=(a.dataset == "cifar"), n=a.n, ntest=a.ntest, epochs=a.epochs,
             eps=8/255, alpha=2/255, steps=7, rad_n=a.rad_n, aa_n=a.aa_n, aa_version=a.aa_version,
             pgd_steps=a.pgd_steps, coupling_n=a.coupling_n, eval_eps=8/255, diag_rt=a.hinge_rt)
    # map each variant to its (r_target, lam, warmup); vanilla ignores penalty knobs
    def hp(v):
        if v == "vanilla":     return (0.0, 0.0, 0)
        if v == "hinge":       return (a.hinge_rt, a.hinge_lam, a.warmup_ep)
        return (0.0, a.dir_lam, a.warmup_ep)                     # directional
    jobs = sorted([(v,) + hp(v) + (w, s) for v in a.variants for w in a.widths for s in range(a.seeds)],
                  key=lambda j: j[4] * j[4], reverse=True)        # cost-sort by width^2
    pending = [j for j in jobs if not os.path.exists(_jf(*j))]
    ng = min(a.gpus, torch.cuda.device_count()) if torch.cuda.is_available() else 0
    K = max(1, a.workers_per_gpu); _maxw = max(a.widths)
    if _maxw >= 96: K = min(K, 1)
    elif a.dataset == "cifar": K = min(K, 2)
    elif _maxw >= 64: K = min(K, 2)
    print(f"PILOT aniso ({a.dataset}, arm=standard, PGD-AT Linf eps=8/255, 7 steps): {len(jobs)} cells "
          f"({len(jobs)-len(pending)} resumed), {len(pending)} to run over {ng or 'CPU'} GPU x {K} workers; "
          f"variants={a.variants} hinge(rt={a.hinge_rt},lam={a.hinge_lam}) dir(lam={a.dir_lam}) "
          f"widths={a.widths} seeds={a.seeds} aa_n={a.aa_n}\n", flush=True)
    load_data(a.dataset, 10, 10)
    t0 = time.time()
    _run_pool(pending, A, ng, K)
    results = [json.load(open(_jf(*j))) for j in jobs if os.path.exists(_jf(*j))]
    miss = [j for j in jobs if not os.path.exists(_jf(*j))]
    stamp = time.strftime("%Y%m%d_%H%M%S")
    fn = os.path.join(RESDIR, f"exp_pilot_aniso_{a.dataset}_{stamp}.json")
    json.dump(dict(args=vars(a), results=results, missing=miss), open(fn, "w"), indent=2, default=float)
    if results:
        agg = {}
        for r in results: agg.setdefault((r["variant"], r["r_target"], r["lam"]), []).append(r)
        def gg(rs, k): return float(np.mean([x[k] for x in rs if k in x and x[k] is not None]))
        hdr = (f"{'variant':11s} {'rt':>5s} {'lam':>4s} {'clean':>6s} {'margin':>7s} {'L1':>7s} "
               f"{'etaL':>6s} {'eta/L1':>7s} {'rr_L2':>6s} {'coupl':>6s} {'pgd':>6s} {'AA':>6s} {'mask':>5s}")
        print("\n" + hdr); print("-" * len(hdr))
        for key in sorted(agg, key=lambda k: (VARIANTS.index(k[0]), k[1], k[2])):
            rs = agg[key]; pgd = gg(rs, "pgd_Linf_8_255"); aa = gg(rs, "aa_Linf_8_255")
            ok = "yes" if aa <= pgd + 0.02 else "NO!"
            print(f"{key[0]:11s} {key[1]:5.2g} {key[2]:4.2g} {gg(rs,'clean'):6.3f} {gg(rs,'dec_margin'):7.3f} "
                  f"{gg(rs,'dec_L1'):7.2f} {gg(rs,'dec_etaL'):6.3f} {gg(rs,'dec_etaL_matched'):7.4f} "
                  f"{gg(rs,'rr_l2'):6.3f} {gg(rs,'coupling_spearman'):6.3f} {pgd:6.3f} {aa:6.3f} {ok:>5s}")
        print("\nREAD: a win = hinge/directional AA > vanilla AA with mask=yes. If AA does not beat "
              "vanilla despite eta/L1 rising, the self-limiting coupling / capacity wall held.")
    print(f"\nwall {time.time()-t0:.0f}s; {len(results)}/{len(jobs)} cells; saved {fn}", flush=True)
    if miss: print(f"WARNING missing {len(miss)}: {miss} -- re-run to resume", flush=True)

if __name__ == "__main__":
    main()
