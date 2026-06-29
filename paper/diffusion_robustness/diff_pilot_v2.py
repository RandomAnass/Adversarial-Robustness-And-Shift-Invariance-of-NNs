#!/usr/bin/env python3
"""
PILOT v2 (hardened): decompose the adversarial-robustness gain from EDM diffusion-generated training
data into a MARGIN term vs a local-LIPSCHITZ/sensitivity term, with a SCALE-CONTROLLED decomposition,
multi-seed support, atomic progressive saving + resume, and live per-epoch logging.

We train PreActResNet-18 under Linf 8/255 PGD-AT on CIFAR-10, varying the AMOUNT of Wang-2023 EDM
synthetic data mixed into the 50k real images. Per (arm, seed) we run the SAME decomposition the paper
uses (etaL_decomposition: mean margin, mean local input-gradient norm L1/L2, eta/L), the DDN L2 robust
RADIUS (mean AND median), AutoAttack/PGD robust accuracy at the RobustBench Linf 8/255 threshold
(gradient-masking check AA<=PGD), and circular-shift consistency.

WHY v2 (the key scientific fix) -- LOGIT-SCALE CONTROL
-----------------------------------------------------
The margin M = z_true - max_{j != y} z_j and the local Lipschitz L = ||grad_x M|| are BOTH degree-1
homogeneous in the logits z: multiply z by a scalar c (a temperature 1/c) and M -> c*M, L -> c*L, while
M/L (the first-order radius) and the ARGMAX (hence clean acc, PGD, AA, and the DDN attack distance) are
unchanged. So a raw report like "margin down 42%, L down 51%" mixes a real geometry change with a pure
LOGIT-SCALE change (one model simply being more/less confident). The split into "margin moved" vs "L
moved" is GAUGE-DEPENDENT; only eta/L = d log M - d log L and the actual attack distance are gauge-free.

v2 therefore:
  (PRIMARY robustness)  reports the DDN L2 robust RADIUS (rr_L2, mean + MEDIAN) and AutoAttack accuracy
                        -- both scale-invariant, actual attack distances / argmax outcomes.
  (scale-controlled split)  fixes the gauge two ways and recomputes the margin-vs-L attribution:
      anchor A "logitnorm": equalize the mean centred-logit L2 norm across arms (set each arm's
            T_a = scale_a / scale_base, then margin' = margin/T, L' = L/T). RATIONALE: M and L share
            EXACTLY one scale d.o.f. (degree-1 homogeneity); matching the logit norm removes precisely
            that d.o.f. and nothing else. Deterministic, label-free, exact.
      anchor B "nll": per-arm temperature scaling (Guo et al. 2017) -- fit a single scalar T minimizing
            NLL on a held-out test slice, so every arm is calibrated to the same reference (NLL-optimal).
            Familiar calibration anchor; used as a cross-check that the verdict is anchor-robust.
  Both anchors reduce to subtracting a common  d log s  from BOTH d log margin and d log L, so the
  gauge-INVARIANT gap d log margin - d log L = d log(eta/L) is preserved while the absolute attribution
  ("margin down" vs "L down more") is reported only RELATIVE to a stated anchor. The report says whether
  the raw "margin-down / L-down-more" story SURVIVES each anchor.

DESIGN (controlled, compute-matched): every arm runs the SAME number of epochs and the SAME number of
gradient steps per epoch (steps_per_epoch = ceil(50000/bs)); optimizer is identical. The ONLY thing
that changes across arms is the size of the synthetic pool each mixed batch is sampled from
(real:synthetic ~= 30:70 per batch when synthetic is present; the 0 arm is pure real). MULTI-SEED:
--seeds N repeats each arm with seeds 0..N-1; the synthetic POOL is held fixed (synth_seed) so seeds
vary only the init + SGD/PGD/flip randomness (isolates optimization noise). Aggregation reports
mean +/- std over seeds.

Recipe matches paper/experiments/cifar_at.py (cifar,linf): eps=8/255, alpha=2/255, PGD-7 inner,
SGD(lr=0.1, mom=0.9, nesterov, wd=5e-4), cosine LR, random horizontal flip. NOTE (flagged): bs=512
here vs cifar_at.py's bs=128 -> fewer steps/epoch at the same lr; consistent ACROSS arms (the
decomposition is a within-experiment comparison) but absolute robustness runs a touch low.

Run (full sweep, multi-seed -- LAUNCH ON GPU AFTER the current diff_pilot.py run finishes):
    PYTHONNOUSERSITE=1 .../cenv/bin/python diff_pilot_v2.py --synth 0 100000 500000 1000000 \
        --epochs 40 --seeds 3 --gpus 2 --tag v2sweep
Smoke (CPU, tiny, no GPU training):
    PYTHONNOUSERSITE=1 .../cenv/bin/python diff_pilot_v2.py --smoke
"""
import argparse, os, sys, json, time, math
import numpy as np, torch, torch.nn.functional as F
import torch.multiprocessing as mp

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.normpath(os.path.join(HERE, "..", "experiments"))
RS = os.path.join(EXP, "resnet_scale")
for p in (EXP, RS):
    if p not in sys.path:
        sys.path.insert(0, p)

import cifar_dissection as CD          # load_cifar, accuracy, correct_mask, shift_consistency,
import cifar_at as CAT                 # pgd_linf (Linf PGD-AT inner attack), pgd_l2
import models as M                     # PreActResNet-18 build / nparams

DATA_NPZ = os.path.join(HERE, "data", "1m.npz")
RESDIR = os.path.join(HERE, "results")
PARTDIR = os.path.join(RESDIR, "partial")

# ---- enable TF32 (perf only; matmul/conv precision unchanged enough not to affect the decomposition)
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True
torch.backends.cudnn.benchmark = True

# cifar / linf PGD-AT recipe (identical to cifar_at.py RECIPE[("cifar","linf")])
EPS, ALPHA, PGD_STEPS = 8 / 255, 2 / 255, 7
LR, MOM, WD = 0.1, 0.9, 5e-4


# ----------------------------------------------------------------------------- synthetic data pool
def load_synth(n_syn, seed=0):
    """Load n_syn EDM synthetic CIFAR-10 images as a uint8 tensor (n,3,32,32) + long labels.
    Subsample is a fixed seeded random subset so smaller arms are random subsets of the 1M pool.
    The pool seed is INDEPENDENT of the training seed: across training seeds the pool is identical,
    so multi-seed isolates optimization/init noise (not data-subset noise)."""
    z = np.load(DATA_NPZ)
    img, lab = z["image"], z["label"]            # (N,32,32,3) uint8, (N,) int
    N = len(img)
    n_syn = min(n_syn, N)
    rng = np.random.default_rng(seed)
    idx = rng.permutation(N)[:n_syn]
    idx.sort()                                   # sorted gather is faster on the mmap'd array
    xs = torch.from_numpy(np.ascontiguousarray(img[idx])).permute(0, 3, 1, 2).contiguous()  # uint8 (n,3,32,32)
    ys = torch.from_numpy(np.ascontiguousarray(lab[idx])).long()
    return xs, ys


# ----------------------------------------------------------------------------- mixed PGD-AT training
def adv_train_mixed(model, Xr, yr, Xs_u8, ys, dev, epochs, bs, real_frac, cell, A=None, n_syn=None, seed=None):
    """Linf PGD-AT. 0 arm (Xs_u8 is None): standard permutation passes over the 50k real images.
    Synthetic arms: each of steps_per_epoch batches is real_frac real + (1-real_frac) synthetic, both
    sampled with replacement from their pools; same step budget as the 0 arm. Training math is IDENTICAL
    to diff_pilot.py so v2 numbers are directly comparable. Logs per-epoch loss + robust-train-acc.

    NOTE: the caller seeds the RNG BEFORE building the model, so per-seed init differs (v2 fix); we do
    NOT re-seed here (a single RNG stream covers init + SGD + PGD + flip)."""
    model = model.to(dev).train()
    opt = torch.optim.SGD(model.parameters(), lr=LR, momentum=MOM, weight_decay=WD, nesterov=True)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    n_real = len(Xr)
    steps_per_epoch = math.ceil(n_real / bs)     # identical optimization budget across all arms
    nb_real = bs if Xs_u8 is None else int(round(real_frac * bs))
    nb_syn = 0 if Xs_u8 is None else bs - nb_real
    for ep in range(epochs):
        if Xs_u8 is None:
            perm = torch.randperm(n_real, device=dev)
        ep_loss, ep_correct, ep_seen = 0.0, 0, 0
        for it in range(steps_per_epoch):
            if Xs_u8 is None:                                  # pure real, permutation pass
                idx = perm[it * bs:(it + 1) * bs]
                xb, yb = Xr[idx], yr[idx]
            else:                                              # mixed real:synthetic batch
                ir = torch.randint(0, n_real, (nb_real,), device=dev)
                isy = torch.randint(0, len(Xs_u8), (nb_syn,), device=dev)
                xb = torch.cat([Xr[ir], Xs_u8[isy].float().div_(255.0)], 0)
                yb = torch.cat([yr[ir], ys[isy]], 0)
            flip = torch.rand(xb.size(0), device=dev) < 0.5    # random horizontal flip (matches recipe)
            xb = torch.where(flip[:, None, None, None], xb.flip(-1), xb)
            x_adv = CAT.pgd_linf(model, xb, yb, EPS, ALPHA, PGD_STEPS)   # inner max (reused infra)
            opt.zero_grad(set_to_none=True)
            logits = model(x_adv)                              # outer min
            loss = F.cross_entropy(logits, yb)
            loss.backward(); opt.step()
            with torch.no_grad():
                ep_loss += float(loss) * yb.size(0)
                ep_correct += int((logits.argmax(1) == yb).sum()); ep_seen += yb.size(0)
        sched.step()
        if A is not None and A.get("save_ckpt_every") and ((ep + 1) % A["save_ckpt_every"] == 0):
            ck = os.path.join(HERE, "ckpts"); os.makedirs(ck, exist_ok=True)
            torch.save(dict(state_dict=model.state_dict(), arm=A["arm"], width=A["width"],
                            n_syn=int(n_syn), seed=int(seed), epoch=ep + 1),
                       os.path.join(ck, f"{A['tag']}_traj_syn{n_syn}_s{seed}_ep{ep+1}.pt"))
        print(f"  [{cell}] epoch {ep + 1:>3d}/{epochs}  loss {ep_loss / max(ep_seen, 1):.4f}  "
              f"robust_train_acc {ep_correct / max(ep_seen, 1):.4f}  lr {sched.get_last_lr()[0]:.4f}",
              flush=True)
    return model.eval()


# ------------------------------------------------------------------- per-sample DDN L2 robust radius
# Faithful copy of cifar_dissection.robust_radius_l2 internals, but returns the PER-SAMPLE radius tensor
# so we can report the MEDIAN (more robust to the heavy right tail than the mean). cifar_dissection.py
# is outside this directory and must not be modified, hence the local copy.
def robust_radius_l2_per_sample(model, X, y, dev, steps=300, gamma=0.05, eps0=1.0, a0=1.0, bs=256):
    X = X.to(dev); y = y.to(dev); N = len(X)
    best = torch.full((N,), float('inf'), device=dev)
    for i in range(0, N, bs):
        xb = X[i:i + bs]; yb = y[i:i + bs]
        delta = torch.zeros_like(xb)
        eps = torch.full((len(xb),), float(eps0), device=dev)
        bnorm = torch.full((len(xb),), float('inf'), device=dev)
        for k in range(steps):
            alpha = 0.01 + (a0 - 0.01) * (1 + np.cos(np.pi * k / steps)) / 2
            delta.requires_grad_(True)
            xadv = torch.clamp(xb + delta, 0, 1)
            logits = model(xadv)
            g, = torch.autograd.grad(CD._margin_loss(logits, yb).sum(), delta)
            with torch.no_grad():
                adv = logits.argmax(1) != yb
                nrm = delta.flatten(1).norm(dim=1)
                upd = adv & (nrm < bnorm); bnorm[upd] = nrm[upd]
                eps = torch.where(adv, eps * (1 - gamma), eps * (1 + gamma))
                gn = g / g.flatten(1).norm(dim=1).clamp_min(1e-12)[:, None, None, None]
                delta = delta + alpha * gn
                dn = delta.flatten(1).norm(dim=1).clamp_min(1e-12)
                delta = delta / dn[:, None, None, None] * eps[:, None, None, None]
                delta = torch.clamp(xb + delta, 0, 1) - xb
        best[i:i + len(xb)] = bnorm
    return best.detach().cpu()                       # per-sample min-||delta||_2 (inf where never flipped)


# ------------------------------------------------------------- logit scale + NLL temperature (gauge)
@torch.no_grad()
def mean_logit_scale(model, X, y, dev, n_max=1000, bs=256):
    """Mean centred-logit L2 norm  mean_i || z_i - mean_c z_{i,c} ||_2  on clean-correct points (the
    SAME selection etaL_decomposition uses). Centring removes the additive-constant gauge (which does
    not affect M or L); the norm captures the degree-1 logit scale that DOES scale both M and L."""
    cm = CD.correct_mask(model, X, y, dev)
    Xc = X[cm][:n_max]
    tot, n = 0.0, 0
    for i in range(0, len(Xc), bs):
        z = model(Xc[i:i + bs].to(dev))
        zc = z - z.mean(1, keepdim=True)
        tot += float(zc.norm(dim=1).sum()); n += len(z)
    return tot / max(n, 1)


@torch.no_grad()
def _collect_logits(model, X, dev, bs=512):
    out = []
    for i in range(0, len(X), bs):
        out.append(model(X[i:i + bs].to(dev)).cpu())
    return torch.cat(out)


def fit_temperature_nll(model, Xho, yho, dev):
    """Temperature scaling (Guo et al. 2017): fit a single scalar T>0 minimizing NLL of logits/T on a
    held-out split. Returns T (the calibration temperature). Dividing logits by T calibrates the arm to
    the same NLL-optimal reference, removing per-arm over/under-confidence (a logit-scale d.o.f.)."""
    logits = _collect_logits(model, Xho, dev).double()
    labels = yho.cpu()
    logT = torch.zeros(1, requires_grad=True, dtype=torch.double)
    opt = torch.optim.LBFGS([logT], lr=0.1, max_iter=80, line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad()
        loss = F.cross_entropy(logits / logT.exp(), labels)
        loss.backward(); return loss
    opt.step(closure)
    T = float(logT.exp().item())
    if not (math.isfinite(T) and T > 0):
        return 1.0
    return float(min(max(T, 0.05), 20.0))           # clamp: trained nets give T~0.5-3; guard flat-NLL runaway


# ----------------------------------------------------------------------------- partial-save / resume
def cell_key(A, n_syn, seed):
    """Partial-file key. Includes arm, width, n_syn, seed, epochs AND bs/real_frac so two runs that
    differ in any recipe knob never collide (the width/scale collision bug class)."""
    rf = f"{A['real_frac']:.3f}".rstrip("0").rstrip(".")
    return (f"{A['tag']}_arm-{A['arm']}_w{A['width']:g}_syn{n_syn}_s{seed}"
            f"_e{A['epochs']}_bs{A['bs']}_rf{rf}")


def cell_path(A, n_syn, seed):
    return os.path.join(PARTDIR, cell_key(A, n_syn, seed) + ".json")


def save_cell_atomic(A, out):
    os.makedirs(PARTDIR, exist_ok=True)
    p = cell_path(A, out["n_syn"], out["seed"]); tmp = p + ".tmp"
    json.dump(out, open(tmp, "w"), default=float); os.replace(tmp, p)   # atomic publish


# ----------------------------------------------------------------------------- one cell (train+eval)
def run_cell(task):
    gpu, n_syn, seed, A = task
    dev = f"cuda:{gpu}" if (gpu is not None and torch.cuda.is_available()) else "cpu"
    if dev.startswith("cuda"):
        torch.cuda.set_device(gpu)
    cell = f"syn{n_syn}_s{seed}"
    t0 = time.time()
    print(f"[start] {cell} | arm={A['arm']} w={A['width']} epochs={A['epochs']} bs={A['bs']} "
          f"real_frac={A['real_frac']} dev={dev}", flush=True)

    torch.manual_seed(seed)                         # v2 FIX: seed BEFORE build so per-seed INIT differs
    # real CIFAR-10 (same loader / split as the paper); [0,1] tensors, normalization is a model layer
    Xtr, ytr, Xte, yte = CD.load_cifar(A["n"], A["ntest"], seed=0)
    Xr, yr = Xtr.to(dev), ytr.to(dev)
    Xs_u8, ys = (None, None)
    if n_syn > 0:
        xs, ls = load_synth(n_syn, seed=A["synth_seed"])
        Xs_u8, ys = xs.to(dev), ls.to(dev)
    model = M.build(A["arm"], width=A["width"]).to(dev)   # canonical zero-pad stride-2 PreActResNet-18
    model = adv_train_mixed(model, Xr, yr, Xs_u8, ys, dev, A["epochs"], A["bs"], A["real_frac"], cell,
                            A=A, n_syn=n_syn, seed=seed)
    if A.get("save_ckpt"):
        ck = os.path.join(HERE, "ckpts"); os.makedirs(ck, exist_ok=True)
        torch.save(dict(state_dict=model.state_dict(), arm=A["arm"], width=A["width"],
                        n_syn=int(n_syn), seed=int(seed), epoch=A["epochs"]),
                   os.path.join(ck, f"{A['tag']}_syn{n_syn}_s{seed}_e{A['epochs']}.pt"))
    del Xs_u8, ys
    if dev.startswith("cuda"):
        torch.cuda.empty_cache()

    out = dict(n_syn=int(n_syn), seed=int(seed), epochs=A["epochs"], bs=A["bs"], arm=A["arm"],
               width=A["width"], real_frac=A["real_frac"], params=M.nparams(model))
    out["clean"] = CD.accuracy(model, Xte, yte, dev)
    out["consist"] = CD.shift_consistency(model, Xte, dev)
    cm = CD.correct_mask(model, Xte, yte, dev)          # radius / decomposition: clean-correct pts only
    Xc, yc = Xte[cm], yte[cm]
    rr = robust_radius_l2_per_sample(model, Xc[:A["rad_n"]], yc[:A["rad_n"]], dev, steps=A["rad_steps"])
    fin = torch.isfinite(rr)
    out["rr_l2"] = float(rr[fin].mean()) if fin.any() else float("nan")          # mean (paper-comparable)
    out["rr_l2_median"] = float(rr[fin].median()) if fin.any() else float("nan") # median (robust to tail)
    out["rr_n"] = int(min(A["rad_n"], len(Xc)))
    out.update({("dec_" + k): v for k, v in
                CD.etaL_decomposition(model, Xte, yte, dev, n_max=A["dec_n"]).items()})
    # logit-scale gauge measures (for the scale-controlled decomposition)
    out["dec_logit_scale"] = mean_logit_scale(model, Xte, yte, dev, n_max=A["dec_n"])
    out["temp_nll"] = fit_temperature_nll(model, Xte[-A["temp_n"]:], yte[-A["temp_n"]:], dev)
    # threat-matched Linf 8/255: PGD (masking check) then AutoAttack (ground truth; AA<=PGD)
    out["pgd_Linf_8_255"] = CD.pgd_acc(model, Xte[:A["aa_n"]], yte[:A["aa_n"]], dev, EPS, "linf", steps=A["pgd_steps"])
    if seed < A["aa_seeds"]:
        out["aa_Linf_8_255"] = CD.autoattack_acc(model, Xte, yte, dev, EPS, "Linf", n=A["aa_n"], version=A["aa_version"])
    else:
        out["aa_Linf_8_255"] = None
    out["wall_s"] = round(time.time() - t0, 1)

    save_cell_atomic(A, out)
    aa_s = "n/a" if out["aa_Linf_8_255"] is None else f"{out['aa_Linf_8_255']:.3f}"
    print(f"[done] {cell} | clean {out['clean']:.3f} PGD {out['pgd_Linf_8_255']:.3f} AA {aa_s} | "
          f"rr_L2 {out['rr_l2']:.3f} (med {out['rr_l2_median']:.3f}) margin {out['dec_margin']:.3f} "
          f"L1 {out['dec_L1']:.2f} L2 {out['dec_L2']:.3f} logit_scale {out['dec_logit_scale']:.3f} "
          f"T_nll {out['temp_nll']:.3f} | {out['wall_s']:.0f}s", flush=True)
    return out


def _run_shard(shard, q):
    for t in shard:
        q.put(run_cell(t))


# ----------------------------------------------------------------------------- aggregation over seeds
def _mean(vs):
    vs = [v for v in vs if v is not None and (not isinstance(v, float) or math.isfinite(v))]
    return float(np.mean(vs)) if vs else float("nan")


def _std(vs):
    vs = [v for v in vs if v is not None and (not isinstance(v, float) or math.isfinite(v))]
    return float(np.std(vs)) if len(vs) > 1 else 0.0


AGG_KEYS = ["clean", "consist", "rr_l2", "rr_l2_median", "pgd_Linf_8_255", "aa_Linf_8_255",
            "dec_margin", "dec_L1", "dec_L2", "dec_etaL", "dec_rho2", "dec_logit_scale", "temp_nll"]


def aggregate(rows):
    """Group cells by n_syn; return {n_syn: {key: (mean, std), 'nseed': k}} over seeds."""
    by = {}
    for r in rows:
        by.setdefault(r["n_syn"], []).append(r)
    agg = {}
    for ns, rs in by.items():
        a = {"nseed": len(rs)}
        for k in AGG_KEYS:
            a[k] = (_mean([r.get(k) for r in rs]), _std([r.get(k) for r in rs]))
        agg[ns] = a
    return agg


# ----------------------------------------------------------------------------- decomposition report
def _safe_log(a, b):
    return math.log(a / b) if (a is not None and b is not None and a > 0 and b > 0) else float("nan")


def decompose(agg):
    """Per-arm-mean decomposition vs the 0 (real-only) baseline.

    RAW (gauge-dependent):     d log margin, d log L1, d log L2, and d log(eta/L) = d log m - d log L.
    GAUGE-INVARIANT (robust):  d log(eta/L1|L2), d log rr_L2 (mean & median), d AA.
    SCALE-CONTROLLED split:    for each anchor (logitnorm via d log s = d log logit_scale; nll via
                               d log s = d log T), margin_ctrl = d log m - d log s, L_ctrl = d log L - d log s.
                               The gap margin_ctrl - L_ctrl == d log(eta/L) is anchor-invariant; the SIGN
                               of margin_ctrl / which term "moved more" is what the anchor decides. We flag
                               whether the raw 'margin-down & L-down-more' attribution SURVIVES each anchor.
    """
    m = lambda d, k: d[k][0]
    base = agg[0]
    out = []
    for ns in sorted(agg):
        if ns == 0:
            continue
        r = agg[ns]
        dlm = _safe_log(m(r, "dec_margin"), m(base, "dec_margin"))
        dl1 = _safe_log(m(r, "dec_L1"), m(base, "dec_L1"))
        dl2 = _safe_log(m(r, "dec_L2"), m(base, "dec_L2"))
        rec = dict(n_syn=ns, nseed=r["nseed"],
                   dlog_margin=dlm, dlog_L1=dl1, dlog_L2=dl2,
                   dlog_etaL2=dlm - dl2, dlog_etaL1=dlm - dl1,
                   dlog_rr_l2=_safe_log(m(r, "rr_l2"), m(base, "rr_l2")),
                   dlog_rr_l2_median=_safe_log(m(r, "rr_l2_median"), m(base, "rr_l2_median")),
                   dAA=(m(r, "aa_Linf_8_255") - m(base, "aa_Linf_8_255"))
                       if math.isfinite(m(r, "aa_Linf_8_255")) and math.isfinite(m(base, "aa_Linf_8_255"))
                       else float("nan"))
        raw_margin_down = dlm < 0
        raw_L_down_more = (dl2 < dlm)                      # L2 more negative than margin
        for anc, ds in (("logitnorm", _safe_log(m(r, "dec_logit_scale"), m(base, "dec_logit_scale"))),
                        ("nll", _safe_log(m(r, "temp_nll"), m(base, "temp_nll")))):
            mc, l2c, l1c = dlm - ds, dl2 - ds, dl1 - ds
            survives = bool((mc < 0) and (l2c < mc) and raw_margin_down and raw_L_down_more)
            rec[f"dlog_s_{anc}"] = ds
            rec[f"margin_ctrl_{anc}"] = mc
            rec[f"L2_ctrl_{anc}"] = l2c
            rec[f"L1_ctrl_{anc}"] = l1c
            rec[f"survives_{anc}"] = survives
        out.append(rec)
    return base, out


def fmt_ms(pair, w=6, p=3):
    mu, sd = pair
    return f"{mu:>{w}.{p}f}+-{sd:.{p}f}"


def print_report(agg, decomp_base, decomp_lines, recipe):
    m = lambda d, k: d[k][0]
    sd = lambda d, k: d[k][1]
    print("\n==== results (mean +- std over seeds) ====", flush=True)
    hdr = f"{'+synth':>9s} {'nseed':>5s} {'clean':>14s} {'PGD':>14s} {'AA':>14s} {'rr_L2':>14s} {'rr_med':>14s} {'eta/L':>14s} {'consist':>14s}"
    print(hdr); print("-" * len(hdr))
    for ns in sorted(agg):
        r = agg[ns]
        print(f"{ns:>9d} {r['nseed']:>5d} {fmt_ms(r['clean'])} {fmt_ms(r['pgd_Linf_8_255'])} "
              f"{fmt_ms(r['aa_Linf_8_255'])} {fmt_ms(r['rr_l2'])} {fmt_ms(r['rr_l2_median'])} "
              f"{fmt_ms(r['dec_etaL'])} {fmt_ms(r['consist'])}")

    print("\n---- raw decomposition quantities (margin/L are GAUGE-DEPENDENT) ----")
    hdr2 = f"{'+synth':>9s} {'margin':>14s} {'L1':>16s} {'L2':>14s} {'logit_scale':>14s} {'T_nll':>14s}"
    print(hdr2); print("-" * len(hdr2))
    for ns in sorted(agg):
        r = agg[ns]
        print(f"{ns:>9d} {fmt_ms(r['dec_margin'])} {fmt_ms(r['dec_L1'], 8, 2)} {fmt_ms(r['dec_L2'])} "
              f"{fmt_ms(r['dec_logit_scale'])} {fmt_ms(r['temp_nll'])}")

    print("\n==== gradient-masking check (must hold: AA <= PGD) ====")
    for ns in sorted(agg):
        r = agg[ns]
        aa, pgd = m(r, "aa_Linf_8_255"), m(r, "pgd_Linf_8_255")
        if math.isfinite(aa):
            ok = "OK" if aa <= pgd + 1e-9 else "VIOLATED"
            print(f"  +{ns:>8d}: AA {aa:.3f} <= PGD {pgd:.3f}  [{ok}]")
        else:
            print(f"  +{ns:>8d}: AA n/a (seed >= aa_seeds)  PGD {pgd:.3f}")

    if decomp_lines:
        print("\n==== decomposition vs +0 (real-only) baseline ====")
        print("GAUGE-INVARIANT robustness (the actual conclusions):")
        print(f"  base(+0): rr_L2 {m(decomp_base,'rr_l2'):.3f} (med {m(decomp_base,'rr_l2_median'):.3f})  "
              f"eta/L {m(decomp_base,'dec_etaL'):.3f}  AA {m(decomp_base,'aa_Linf_8_255'):.3f}")
        for l in decomp_lines:
            print(f"  +{l['n_syn']:>8d}: dlog(eta/L2) {l['dlog_etaL2']:+.3f}  dlog(eta/L1) {l['dlog_etaL1']:+.3f}  "
                  f"dlog rr_L2 {l['dlog_rr_l2']:+.3f} (med {l['dlog_rr_l2_median']:+.3f})  dAA {l['dAA']:+.3f}")
        print("\nRAW margin-vs-L split (CONFOUNDED by logit scale -- do not interpret alone):")
        for l in decomp_lines:
            print(f"  +{l['n_syn']:>8d}: dlog margin {l['dlog_margin']:+.3f}  dlog L1 {l['dlog_L1']:+.3f}  "
                  f"dlog L2 {l['dlog_L2']:+.3f}")
        print("\nSCALE-CONTROLLED margin-vs-L split (margin_ctrl = dlog m - dlog s ; L_ctrl = dlog L - dlog s):")
        for anc in ("logitnorm", "nll"):
            print(f"  anchor = {anc}:")
            for l in decomp_lines:
                print(f"    +{l['n_syn']:>8d}: dlog s {l[f'dlog_s_{anc}']:+.3f} | "
                      f"margin_ctrl {l[f'margin_ctrl_{anc}']:+.3f}  L2_ctrl {l[f'L2_ctrl_{anc}']:+.3f}  "
                      f"L1_ctrl {l[f'L1_ctrl_{anc}']:+.3f} | raw 'margin-down & L-down-more' survives: "
                      f"{l[f'survives_{anc}']}")
        print("\nVERDICT: eta/L, rr_L2 and AA are scale-invariant and define the robustness gain; the raw "
              "margin-vs-L attribution is gauge-dependent and is reported only relative to a stated anchor.")


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--synth", type=int, nargs="+", default=[0, 1000000], help="synthetic-pool sizes (arms)")
    ap.add_argument("--seeds", type=int, default=1, help="repeat each arm with seeds 0..N-1")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--bs", type=int, default=512)
    ap.add_argument("--real_frac", type=float, default=0.3, help="real fraction per mixed batch (synth arms)")
    ap.add_argument("--arm", default="stdzero", help="models.py arm (default canonical zero-pad stride-2)")
    ap.add_argument("--width", type=float, default=1.0)
    ap.add_argument("--n", type=int, default=50000); ap.add_argument("--ntest", type=int, default=10000)
    ap.add_argument("--rad_n", type=int, default=1000); ap.add_argument("--rad_steps", type=int, default=300)
    ap.add_argument("--dec_n", type=int, default=1000); ap.add_argument("--temp_n", type=int, default=2000)
    ap.add_argument("--aa_n", type=int, default=512)
    ap.add_argument("--aa_version", default="standard"); ap.add_argument("--pgd_steps", type=int, default=40)
    ap.add_argument("--aa_seeds", type=int, default=99, help="#seeds (per arm) that get AutoAttack (default: all)")
    ap.add_argument("--synth_seed", type=int, default=0)
    ap.add_argument("--gpus", type=int, default=99); ap.add_argument("--serial", action="store_true")
    ap.add_argument("--cpu", action="store_true", help="force CPU (no GPU)")
    ap.add_argument("--smoke", action="store_true", help="tiny CPU end-to-end check (no GPU training)")
    ap.add_argument("--tag", default="stage")
    ap.add_argument("--save_ckpt", action="store_true", help="save final per-cell model weights -> ckpts/")
    ap.add_argument("--save_ckpt_every", type=int, default=0, help="also save every K epochs (M6 trajectory)")
    args = ap.parse_args()

    if args.smoke:                                   # tiny end-to-end on CPU (NOT the full pilot)
        args.cpu = True
        args.n, args.ntest, args.epochs, args.seeds = 256, 512, 1, 2
        args.synth = [0, 256] if args.synth == [0, 1000000] else args.synth
        args.bs = 128
        args.rad_n, args.rad_steps, args.dec_n, args.temp_n = 24, 25, 64, 128
        args.aa_n, args.aa_version, args.pgd_steps = 16, "custom", 5
        torch.set_num_threads(min(8, os.cpu_count() or 4))   # be a good neighbour on a busy box

    A = dict(n=args.n, ntest=args.ntest, epochs=args.epochs, bs=args.bs, real_frac=args.real_frac,
             arm=args.arm, width=args.width, rad_n=args.rad_n, rad_steps=args.rad_steps, dec_n=args.dec_n,
             temp_n=args.temp_n, aa_n=args.aa_n, aa_version=args.aa_version, pgd_steps=args.pgd_steps,
             aa_seeds=args.aa_seeds, synth_seed=args.synth_seed, tag=args.tag,
             save_ckpt=args.save_ckpt, save_ckpt_every=args.save_ckpt_every)
    ng = 0 if args.cpu else (min(args.gpus, torch.cuda.device_count()) if torch.cuda.is_available() else 0)
    CD.load_cifar(10, 10)                                  # trigger the torchvision download once

    # full grid = arms x seeds; resume from disk (atomic per-cell save), then run the rest
    arms = sorted(set(args.synth))
    grid = [(ns, s) for ns in arms for s in range(args.seeds)]
    done, pending = [], []
    for (ns, s) in grid:
        p = cell_path(A, ns, s)
        if os.path.exists(p):
            try:
                done.append(json.load(open(p))); continue
            except Exception:
                pass
        pending.append((ns, s))
    tasks = [((i % ng) if ng > 0 else None, ns, s, A) for i, (ns, s) in enumerate(pending)]
    print(f"PILOT v2 diffusion-AT: arms(synth)={arms} seeds={args.seeds} epochs={args.epochs} bs={args.bs} "
          f"real_frac={args.real_frac} | {len(done)} cell(s) resumed, {len(tasks)} to run over "
          f"{ng or 'CPU'} GPU(s)\n", flush=True)

    t0 = time.time()
    computed = []
    if tasks:
        if args.serial or ng <= 1:
            computed = [run_cell(t) for t in tasks]
        else:
            ctx = mp.get_context("spawn")
            shards = [[t for t in tasks if t[0] == g] for g in range(ng)]
            q = ctx.Queue()
            procs = [ctx.Process(target=_run_shard, args=(shards[g], q)) for g in range(ng) if shards[g]]
            for pr in procs:
                pr.start()
            computed = [q.get() for _ in range(len(tasks))]
            for pr in procs:
                pr.join()
    rows = done + computed
    print(f"\nwall {time.time() - t0:.0f}s ({len(rows)} cells total)", flush=True)

    # aggregate over seeds, decompose
    agg = aggregate(rows)
    decomp_base, decomp_lines = (None, [])
    if 0 in agg and any(ns > 0 for ns in agg):
        decomp_base, decomp_lines = decompose(agg)

    # ---- SAVE the aggregate JSON BEFORE printing, so a print failure never loses results ----
    os.makedirs(RESDIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    recipe = dict(arch=f"PreActResNet-18 ({args.arm}, width={args.width})", eps=EPS, alpha=ALPHA,
                  pgd_steps=PGD_STEPS, lr=LR, mom=MOM, wd=WD, sched="cosine", aug="hflip",
                  real_frac=args.real_frac, bs=args.bs, epochs=args.epochs, seeds=args.seeds,
                  scale_control="logit-norm match (primary) + NLL temperature (cross-check); margin/L are "
                  "degree-1 homogeneous in logits, so only eta/L and the DDN radius are gauge-free",
                  note="compute-matched: same steps_per_epoch=ceil(50000/bs) across arms; arms differ only "
                       "in synthetic-pool size; bs=512 (cifar_at.py uses 128) flagged")
    agg_json = {str(ns): {k: (list(v) if isinstance(v, tuple) else v) for k, v in a.items()}
                for ns, a in agg.items()}
    fn = os.path.join(RESDIR, f"diff_pilot_v2_{args.tag}_{stamp}.json")
    json.dump(dict(args=vars(args), recipe=recipe, rows=rows, aggregate=agg_json,
                   decomposition=decomp_lines), open(fn, "w"), indent=2, default=float)
    print(f"saved {fn}", flush=True)

    # ---- print report (after save) ----
    print_report(agg, decomp_base, decomp_lines, recipe)


if __name__ == "__main__":
    main()
