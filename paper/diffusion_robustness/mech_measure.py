#!/usr/bin/env python3
"""
MECHANISM measurements for "diffusion data buys SMOOTHNESS, not margin".

The pilot (diff_pilot_v2.py) established the FINDING: adding EDM synthetic AT data raises AutoAttack and
the DDN L2 radius while the local input-gradient norm L = ||grad_x M|| drops MORE than the margin M.
This module measures the QUANTITIES that adjudicate WHY (hypotheses H-A..H-F in THEORY_mechanism.md).
It does NOT train the main models -- it loads CHECKPOINTS produced by the next full GPU run and runs
cheap, mostly inference-time probes on them. See MECHANISM_EXPERIMENTS.md for the ranked protocols and
which hypothesis each measurement kills/confirms.

TASKS (each = one decisive measurement; --task picks one or 'all'):
  manifold   M1+M2  L = ||grad_x M|| measured separately on REAL / SYNTHETIC / on-manifold INTERPOLATION /
                    off-manifold (gauss-jitter, uniform) point sets, PLUS the on-/off-manifold split of the
                    gradient (local-PCA tangent projection). Adjudicates H-A (isotropic, drops everywhere &
                    most on vicinity) vs H-E (drop concentrated OFF-manifold) vs H-F (drop only near synth).
  curvature  M3     per-sample top input-Hessian eigenvalue |lambda_max(d^2 M/dx^2)| via batched power
                    iteration. Genuine 2nd-order flattening (H-C) vs pure 1st-order logit-rescale (scale
                    artifact, THEORY sec.2): if L falls but curvature does not -> rescale, not flattening.
  weightsharp M4    weight-space sharpness: clean/robust loss increase under a small (i) filter-normalized
                    RANDOM and (ii) worst-case 1-step (SAM rho) weight perturbation. H-D = smoothness lives
                    in WEIGHT space; refuted if input-L drops while weight-sharpness is flat.
  calib      M5     temperature-calibrated (Guo 2017) + logit-norm-normalized margins. Decides how much of
                    the margin-down is a confidence/scale artifact vs real class-separation loss (THEORY 2).
  trajectory M6     consumes a DIRECTORY of per-epoch checkpoints -> L(epoch) and train-test robust-acc gap
                    (epoch) for +0 vs +synth. The robust-overfitting test (H-B): late-training L SHARPENS in
                    +0 but stays flat in +synth -> B; +synth already-lower-L early -> A/C, B refuted.

CHECKPOINTS. The pilot harness saves only metrics JSON, NOT model weights. The main process must add a
--save_ckpt to the next full run (exact patch in MECHANISM_EXPERIMENTS.md). Expected format:
    torch.save({"state_dict": model.state_dict(), "arm":"stdzero", "width":1.0,
                "n_syn":N, "seed":s, "epoch":E}, path)
load_ckpt also accepts a bare state_dict.

Smoke (CPU only, no GPU, fabricates a tiny checkpoint and runs every task):
    PYTHONNOUSERSITE=1 .../cenv/bin/python mech_measure.py --smoke
Full (after the GPU frees; example, see MECHANISM_EXPERIMENTS.md for all commands):
    PYTHONNOUSERSITE=1 .../cenv/bin/python mech_measure.py --task all \
        --ckpts ckpts/v2_syn0_s0.pt ckpts/v2_syn1000000_s0.pt --synth_npz data/1m.npz --gpu 0
"""
import argparse, os, sys, json, time, math
import numpy as np, torch, torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.normpath(os.path.join(HERE, "..", "experiments"))
RS = os.path.join(EXP, "resnet_scale")
for p in (EXP, RS):
    if p not in sys.path:
        sys.path.insert(0, p)

import cifar_dissection as CD          # load_cifar, correct_mask, pgd_acc, _margin_loss
import cifar_at as CAT                 # pgd_linf (Linf PGD-AT inner attack)
import models as M                     # PreActResNet-18 build / nparams

DATA_NPZ = os.path.join(HERE, "data", "1m.npz")
MECHDIR = os.path.join(HERE, "results", "mech")

# cifar / linf PGD-AT recipe (identical to diff_pilot_v2.py)
EPS, ALPHA, PGD_STEPS = 8 / 255, 2 / 255, 7


# ----------------------------------------------------------------------------- model / checkpoint io
def build_model():
    return M.build("stdzero", width=1.0)          # canonical zero-pad stride-2 PreActResNet-18


def load_ckpt(path, dev):
    """Load a checkpoint dict {'state_dict':..., meta...} OR a bare state_dict. Returns (model.eval, meta)."""
    blob = torch.load(path, map_location=dev)
    if isinstance(blob, dict) and "state_dict" in blob:
        sd = blob["state_dict"]; meta = {k: v for k, v in blob.items() if k != "state_dict"}
    else:
        sd = blob; meta = {}
    model = build_model().to(dev)
    model.load_state_dict(sd)
    return model.eval(), meta


# ----------------------------------------------------------------------------- core: margin + grad
def margin_grad(model, xb):
    """Per-sample margin M = z_true - max_other and grad_x M. xb must already be on the device and
    requires_grad is handled here. Returns (margin[B] detached, grad[B,C,H,W] detached)."""
    xb = xb.clone().requires_grad_(True)
    logits = model(xb)
    # label = current prediction is NOT what etaL uses; etaL uses the TRUE label on correct pts. For point
    # sets without trusted labels (interp / off-manifold) we use the model's OWN argmax as the "true" class
    # so M is the prediction margin (top-1 vs runner-up), which is exactly the sensitivity L probes.
    y = logits.argmax(1)
    true = logits.gather(1, y[:, None]).squeeze(1)
    other = logits.clone().scatter_(1, y[:, None], -1e9).max(1).values
    margin = true - other
    g, = torch.autograd.grad(margin.sum(), xb)
    return margin.detach(), g.detach()


def L_stats(model, X, dev, bs=128):
    """Mean margin, mean ||grad M||_2 (=L2), mean ||grad M||_1 (=L1), and L1/L2, over X (model-argmax
    margins). This is the same sensitivity L the pilot decomposes, evaluated on an ARBITRARY point set."""
    ms, n2s, n1s = [], [], []
    for i in range(0, len(X), bs):
        m, g = margin_grad(model, X[i:i + bs].to(dev))
        gf = g.flatten(1)
        ms.append(m.cpu()); n2s.append(gf.norm(dim=1).cpu()); n1s.append(gf.abs().sum(1).cpu())
    m = torch.cat(ms); n2 = torch.cat(n2s); n1 = torch.cat(n1s)
    L2, L1 = float(n2.mean()), float(n1.mean())
    return dict(margin=float(m.mean()), L2=L2, L1=L1, L1_over_L2=(L1 / L2 if L2 > 0 else float("nan")),
                L2_median=float(n2.median()), n=len(m))


# ----------------------------------------------------------------------------- point-set builders
def load_synth_pts(npz, n, seed=0):
    """n EDM synthetic CIFAR-10 images as [0,1] float (n,3,32,32). Mirrors diff_pilot.load_synth."""
    z = np.load(npz)
    img = z["image"]; N = len(img); n = min(n, N)
    idx = np.sort(np.random.default_rng(seed).permutation(N)[:n])
    xs = torch.from_numpy(np.ascontiguousarray(img[idx])).permute(0, 3, 1, 2).contiguous().float().div_(255.0)
    return xs


def make_interp(Xr, yr, n, seed=0, same_class=True):
    """On-manifold-ish convex interpolations alpha*x_i+(1-alpha)*x_j, alpha~U(0.3,0.7) (mid-segment, the
    region the extra data newly constrains). same_class=True keeps both endpoints in one class (stays near
    the manifold); same_class=False is cross-class (probes the decision-boundary vicinity)."""
    g = torch.Generator().manual_seed(seed)
    N = len(Xr); out = []
    tries = 0
    while len(out) < n and tries < 50 * n:
        i, j = int(torch.randint(0, N, (1,), generator=g)), int(torch.randint(0, N, (1,), generator=g))
        tries += 1
        if i == j:
            continue
        if same_class and (yr[i] != yr[j]):
            continue
        if (not same_class) and (yr[i] == yr[j]):
            continue
        a = 0.3 + 0.4 * float(torch.rand(1, generator=g))
        out.append((a * Xr[i] + (1 - a) * Xr[j]).clamp(0, 1))
    return torch.stack(out) if out else torch.empty(0, *Xr.shape[1:])


def make_gauss(Xr, n, sigma=0.1, seed=0):
    """Off-manifold jitter: real point + N(0,sigma^2) per-pixel noise, clamped to [0,1]. sigma=0.1 is far
    larger than the 8/255~=0.031 Linf / typical L2 robust radius, so these sit OFF the data manifold."""
    g = torch.Generator().manual_seed(seed)
    idx = torch.randperm(len(Xr), generator=g)[:n]
    x = Xr[idx]
    return (x + sigma * torch.randn(x.shape, generator=g)).clamp(0, 1)


def make_uniform(n, shape, seed=0):
    """Extreme off-manifold: pure U[0,1] random images (no data structure at all)."""
    g = torch.Generator().manual_seed(seed)
    return torch.rand(n, *shape, generator=g)


# ----------------------------------------------------------------------------- M2: on/off-manifold split
@torch.no_grad()
def _knn_idx(q_flat, anchors_flat, k, chunk=256):
    """Indices of the k nearest anchors (L2 in pixel space) for each query row."""
    out = []
    for i in range(0, len(q_flat), chunk):
        d = torch.cdist(q_flat[i:i + chunk], anchors_flat)          # [c, A]
        out.append(d.topk(k, largest=False).indices)
    return torch.cat(out)


def onoff_split(model, X, anchors, dev, k=64, d_tan=30, bs=64):
    """Split grad_x M into on-manifold vs off-manifold energy. The local tangent space at each query is
    estimated by local PCA of its k nearest REAL anchors (top d_tan principal directions). Returns the mean
    on-manifold energy FRACTION ||P_tan g||^2 / ||g||^2 (and 1-that off-manifold) over X.
      H-A (isotropic shrink): on/off fraction ~ same across arms.
      H-E (off-manifold suppression): off fraction DROPS sharply with synthetic data."""
    Af = anchors.flatten(1).to(dev)
    on_fr = []
    for i in range(0, len(X), bs):
        xb = X[i:i + bs].to(dev)
        _, g = margin_grad(model, xb)
        gf = g.flatten(1)                                           # [b, D]
        nn = _knn_idx(xb.flatten(1), Af, k)                        # [b, k]
        for r in range(xb.size(0)):
            nb = Af[nn[r]]                                          # [k, D]
            nb = nb - nb.mean(0, keepdim=True)
            # right singular vectors = local principal directions (tangent estimate)
            try:
                _, _, Vh = torch.linalg.svd(nb, full_matrices=False)
            except Exception:
                continue
            P = Vh[:min(d_tan, Vh.size(0))]                        # [d, D] orthonormal tangent basis
            gv = gf[r]
            on = float((P @ gv).pow(2).sum())
            tot = float(gv.pow(2).sum()) + 1e-12
            on_fr.append(on / tot)
    on_fr = torch.tensor(on_fr) if on_fr else torch.tensor([float("nan")])
    return dict(on_frac=float(on_fr.mean()), off_frac=float(1 - on_fr.mean()),
                k=k, d_tan=d_tan, n=int((~torch.isnan(on_fr)).sum()))


# ----------------------------------------------------------------------------- M3: input curvature
# IMPORTANT: PreActResNet-18 (ReLU + eval-mode affine BatchNorm) is PIECEWISE-LINEAR in the input, so the
# pointwise margin-Hessian d^2 M/dx^2 is ZERO almost everywhere (verified: exact-HVP power iteration
# returns ~0). Curvature for ReLU nets therefore lives at the linear-region BOUNDARIES and is measured by
# FINITE DIFFERENCES of the gradient -- exactly CURE's construction (1811.09716). curvature_fd is the
# decisive M3 measure; input_hessian_topeig is kept only as the documented ~0 sanity (its near-zero value
# CONFIRMS piecewise-linearity, i.e. that the FD measure is the right tool).
def curvature_fd(model, X, dev, h=0.25, n_rand=3, bs=32, seed=0):
    """CURE-style finite-difference curvature nu = ||grad M(x + h z) - grad M(x)||_2 / h (per-sample), for
    z = the (unit) GRADIENT direction (the adversarially-relevant curvature) and averaged over n_rand
    random unit directions. h is an L2 step length (default 0.25, of order the DDN L2 radius). H-C predicts
    nu DROPS with synthetic data and TRACKS the L drop; if L falls but nu is flat the effect is a 1st-order
    logit-rescale, not genuine geometric flattening (separates 'real smoothing' from 'shrunk logits')."""
    g0 = torch.Generator().manual_seed(seed)
    cg, cr = [], []
    for i in range(0, len(X), bs):
        xb = X[i:i + bs].to(dev)
        _, g = margin_grad(model, xb)
        gf = g.flatten(1)
        gdir = (g / gf.norm(dim=1).clamp_min(1e-12)[:, None, None, None])
        _, gh = margin_grad(model, (xb + h * gdir).clamp(0, 1))
        cg.append(((gh - g).flatten(1).norm(dim=1) / h).cpu())         # gradient-direction curvature
        rr = []
        for _ in range(n_rand):
            z = torch.randn(xb.shape, generator=g0).to(dev)
            z = z / z.flatten(1).norm(dim=1).clamp_min(1e-12)[:, None, None, None]
            _, gz = margin_grad(model, (xb + h * z).clamp(0, 1))
            rr.append(((gz - g).flatten(1).norm(dim=1) / h))
        cr.append(torch.stack(rr).mean(0).cpu())                       # random-direction curvature (avg)
    return torch.cat(cg), torch.cat(cr)


def input_hessian_topeig(model, X, dev, iters=20, bs=16, seed=0):
    """Exact per-sample |lambda_max| of d^2 M/dx^2 via batched Hessian-vector power iteration. For a ReLU
    net this is ~0 a.e. (the function is piecewise-linear); reported only to CONFIRM that, so the FD
    curvature above is the meaningful number."""
    g0 = torch.Generator().manual_seed(seed)
    out = []
    for i in range(0, len(X), bs):
        xb = X[i:i + bs].to(dev)
        B = xb.size(0)
        v = torch.randn(xb.shape, generator=g0).to(dev)
        v = v / v.flatten(1).norm(dim=1).clamp_min(1e-12)[:, None, None, None]
        lam = torch.zeros(B, device=dev)
        for _ in range(iters):
            xb_ = xb.clone().requires_grad_(True)
            logits = model(xb_)
            y = logits.argmax(1)
            margin = logits.gather(1, y[:, None]).squeeze(1) - \
                logits.clone().scatter_(1, y[:, None], -1e9).max(1).values
            g1, = torch.autograd.grad(margin.sum(), xb_, create_graph=True)
            Hv, = torch.autograd.grad((g1 * v).flatten(1).sum(), xb_)   # per-sample H_i v_i
            Hv = Hv.detach()
            lam = (v * Hv).flatten(1).sum(1)                            # Rayleigh quotient (v unit-norm)
            nrm = Hv.flatten(1).norm(dim=1).clamp_min(1e-12)
            v = (Hv / nrm[:, None, None, None]).detach()
        out.append(lam.abs().detach().cpu())
    e = torch.cat(out)
    return e


# ----------------------------------------------------------------------------- M4: weight-space sharpness
def _eval_loss(model, X, y, dev, adv=False, bs=128):
    """Mean CE loss over X; adv=True evaluates on PGD-Linf-perturbed inputs (robust loss, AWP-relevant)."""
    tot, n = 0.0, 0
    for i in range(0, len(X), bs):
        xb = X[i:i + bs].to(dev); yb = y[i:i + bs].to(dev)
        if adv:
            xb = CAT.pgd_linf(model, xb, yb, EPS, ALPHA, PGD_STEPS)
        with torch.no_grad():
            tot += float(F.cross_entropy(model(xb), yb, reduction="sum")); n += len(yb)
    return tot / max(n, 1)


def weight_sharpness(model, X, y, dev, rho=0.05, trials=5, adv=False, bs=128, seed=0):
    """Two sharpness probes (AWP / SAM style):
      random: filter-normalized random weight perturbation eps_p = rho*||p||*z/||z|| per tensor, mean loss
              increase over `trials` draws.
      worst1: one SAM ascent step w += rho * g/||g||_global, the worst-case loss increase.
    H-D supported only if these DROP with synthetic data AND track input-L. If input-L drops while these
    are flat, the smoothness is input-space (A/C), D refuted."""
    base = _eval_loss(model, X, y, dev, adv=adv, bs=bs)
    sd0 = {k: v.detach().clone() for k, v in model.state_dict().items()}
    params = [(k, v) for k, v in model.state_dict().items() if v.dtype.is_floating_point and v.dim() > 0]

    # ---- random filter-normalized ----
    g0 = torch.Generator().manual_seed(seed); rand_inc = []
    for _ in range(trials):
        with torch.no_grad():
            for k, v in params:
                z = torch.randn(v.shape, generator=g0).to(v.device)
                v.add_(rho * v.norm() * z / z.norm().clamp_min(1e-12))
        rand_inc.append(_eval_loss(model, X, y, dev, adv=adv, bs=bs) - base)
        model.load_state_dict(sd0)
    rand_inc = float(np.mean(rand_inc))

    # ---- worst-case 1-step (SAM) on a single batch's gradient ----
    xb = X[:bs].to(dev); yb = y[:bs].to(dev)
    if adv:
        xb = CAT.pgd_linf(model, xb, yb, EPS, ALPHA, PGD_STEPS)
    model.zero_grad(set_to_none=True)
    F.cross_entropy(model(xb), yb).backward()
    with torch.no_grad():
        gnorm = math.sqrt(sum(float(p.grad.pow(2).sum()) for p in model.parameters() if p.grad is not None))
        for p in model.parameters():
            if p.grad is not None:
                p.add_(rho * p.grad / (gnorm + 1e-12))
    worst_inc = _eval_loss(model, X, y, dev, adv=adv, bs=bs) - base
    model.load_state_dict(sd0); model.zero_grad(set_to_none=True)
    return dict(base_loss=base, rand_sharp=rand_inc, worst_sharp=float(worst_inc),
                rho=rho, adv=bool(adv), trials=trials)


# ----------------------------------------------------------------------------- M5: calibrated margins
@torch.no_grad()
def _logits(model, X, dev, bs=256):
    return torch.cat([model(X[i:i + bs].to(dev)).cpu() for i in range(0, len(X), bs)])


def fit_temperature(model, X, y, dev):
    """Temperature scaling (Guo 2017): scalar T>0 minimizing NLL of logits/T on (X,y)."""
    logits = _logits(model, X, dev).double(); labels = y.cpu()
    logT = torch.zeros(1, requires_grad=True, dtype=torch.double)
    opt = torch.optim.LBFGS([logT], lr=0.1, max_iter=80, line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad(); loss = F.cross_entropy(logits / logT.exp(), labels); loss.backward(); return loss
    opt.step(closure)
    T = float(logT.exp().item())
    return float(min(max(T, 0.05), 20.0)) if (math.isfinite(T) and T > 0) else 1.0


def calibrated_margins(model, X, y, dev, n_max=1000):
    """Margins under three gauges on clean-correct points:
      raw           M = z_true - max_other (logit units; NOT scale-invariant).
      calibrated    M / T (T fit by NLL temperature scaling) -- removes per-model confidence/scale.
      lognorm       M / ||z_centred|| -- scale-free margin (geometry of class separation only).
    H/THEORY-2: most of the raw margin-down should be a confidence/scale effect -> the calibrated and
    lognorm margin GAPS between arms should be much smaller than the raw gap."""
    T = fit_temperature(model, X, y, dev)
    cm = CD.correct_mask(model, X, y, dev)
    Xc, yc = X[cm][:n_max], y[cm][:n_max]
    raw, lognorm = [], []
    for i in range(0, len(Xc), 256):
        z = _logits(model, Xc[i:i + 256], dev)
        yb = yc[i:i + 256]
        true = z.gather(1, yb[:, None]).squeeze(1)
        other = z.clone().scatter_(1, yb[:, None], -1e9).max(1).values
        m = true - other
        zc = z - z.mean(1, keepdim=True)
        raw.append(m); lognorm.append(m / zc.norm(dim=1).clamp_min(1e-12))
    raw = torch.cat(raw); lognorm = torch.cat(lognorm)
    return dict(T=T, margin_raw=float(raw.mean()), margin_calibrated=float(raw.mean() / T),
                margin_lognorm=float(lognorm.mean()), n=len(raw))


# ----------------------------------------------------------------------------- task dispatchers
def _save(tag, task, payload):
    os.makedirs(MECHDIR, exist_ok=True)
    fn = os.path.join(MECHDIR, f"mech_{task}_{tag}_{time.strftime('%Y%m%d_%H%M%S')}.json")
    json.dump(payload, open(fn, "w"), indent=2, default=float)
    print(f"saved {fn}", flush=True)
    return fn


def _ckpt_tag(meta, path):
    if "n_syn" in meta:
        return f"syn{meta['n_syn']}_s{meta.get('seed', 0)}"
    return os.path.splitext(os.path.basename(path))[0]


def task_manifold(args, dev, Xte, yte, Xtr, ytr):
    """M1 (L on point sets) + M2 (on/off split) per checkpoint."""
    # build the point sets ONCE (shared across checkpoints for a fair comparison)
    nps = args.npts
    sets = {
        "real":        Xte[:nps],
        "interp_same": make_interp(Xtr, ytr, nps, seed=0, same_class=True),
        "interp_cross": make_interp(Xtr, ytr, nps, seed=1, same_class=False),
        "gauss":       make_gauss(Xte, nps, sigma=args.gauss_sigma, seed=2),
        "uniform":     make_uniform(nps, Xte.shape[1:], seed=3),
    }
    if args.synth_npz and os.path.exists(args.synth_npz):
        sets["synth"] = load_synth_pts(args.synth_npz, nps, seed=4)
    elif args.smoke:
        sets["synth"] = (torch.rand(nps, *Xte.shape[1:]))            # fabricated synth for smoke
    anchors = Xtr[:args.anchors]                                     # real manifold anchors for local PCA
    res = {}
    for path in args.ckpts:
        model, meta = load_ckpt(path, dev)
        tg = _ckpt_tag(meta, path)
        per_set = {name: L_stats(model, S, dev) for name, S in sets.items()}     # L_stats moves to dev
        split = onoff_split(model, sets["real"], anchors, dev, k=args.knn, d_tan=args.dtan)
        res[tg] = dict(meta=meta, L_by_set=per_set, onoff_real=split)
        print(f"[manifold] {tg}: " +
              "  ".join(f"{n}:L2={v['L2']:.3f}" for n, v in per_set.items()) +
              f"  | on_frac={split['on_frac']:.3f}", flush=True)
    return res


def task_curvature(args, dev, Xte, yte, Xtr, ytr):
    res = {}
    for path in args.ckpts:
        model, meta = load_ckpt(path, dev)
        tg = _ckpt_tag(meta, path)
        cm = CD.correct_mask(model, Xte, yte, dev)
        Xc = Xte[cm][:args.npts]
        cg, cr = curvature_fd(model, Xc, dev, h=args.fd_h, n_rand=args.fd_rand, bs=args.hess_bs)  # primary
        eig = input_hessian_topeig(model, Xc, dev, iters=args.power_iters, bs=args.hess_bs)       # ~0 check
        Ls = L_stats(model, Xc, dev)
        # curv/L is the GAUGE-FREE 2nd-order quantity: under a pure logit rescale f->f/T both curvature and
        # L scale by 1/T, so curv/L is invariant; a genuine geometric flattening (H-C) lowers curv/L, a
        # pure 1st-order rescale leaves it flat. This is the decisive separation (THEORY sec.2).
        curv_over_L = float(cg.mean()) / Ls["L2"] if Ls["L2"] > 0 else float("nan")
        res[tg] = dict(meta=meta, curv_grad_mean=float(cg.mean()), curv_grad_median=float(cg.median()),
                       curv_rand_mean=float(cr.mean()), curv_grad_over_L2=curv_over_L,
                       hess_topeig_mean=float(eig.mean()), L2=Ls["L2"], margin=Ls["margin"],
                       fd_h=args.fd_h, n=len(cg))
        print(f"[curvature] {tg}: FD-curv grad={float(cg.mean()):.3f} (med {float(cg.median()):.3f}) "
              f"rand={float(cr.mean()):.3f} curv/L={curv_over_L:.3f} | exact|lam_max|={float(eig.mean()):.2e} "
              f"(~0=piecewise-linear) | L2={Ls['L2']:.3f}", flush=True)
    return res


def task_weightsharp(args, dev, Xte, yte, Xtr, ytr):
    res = {}
    for path in args.ckpts:
        model, meta = load_ckpt(path, dev)
        tg = _ckpt_tag(meta, path)
        ws = weight_sharpness(model, Xte[:args.npts], yte[:args.npts], dev, rho=args.rho,
                              trials=args.trials, adv=args.adv)
        Ls = L_stats(model, Xte[:args.npts], dev)
        res[tg] = dict(meta=meta, **ws, input_L2=Ls["L2"])
        print(f"[weightsharp] {tg}: rand={ws['rand_sharp']:+.4f} worst={ws['worst_sharp']:+.4f} "
              f"(rho={ws['rho']}, adv={ws['adv']}) | input_L2={Ls['L2']:.3f}", flush=True)
    return res


def task_calib(args, dev, Xte, yte, Xtr, ytr):
    res = {}
    for path in args.ckpts:
        model, meta = load_ckpt(path, dev)
        tg = _ckpt_tag(meta, path)
        cmar = calibrated_margins(model, Xte, yte, dev, n_max=args.npts)
        res[tg] = dict(meta=meta, **cmar)
        print(f"[calib] {tg}: T={cmar['T']:.3f} raw={cmar['margin_raw']:.3f} "
              f"calib={cmar['margin_calibrated']:.3f} lognorm={cmar['margin_lognorm']:.4f}", flush=True)
    # report the gap-shrink: how much of the raw margin gap survives each gauge (needs a syn0 baseline)
    base = next((v for k, v in res.items() if v["meta"].get("n_syn", -1) == 0), None)
    if base is not None:
        for tg, v in res.items():
            if v is base:
                continue
            def dlog(a, b): return math.log(a / b) if (a > 0 and b > 0) else float("nan")
            v["dlog_raw_vs_base"] = dlog(v["margin_raw"], base["margin_raw"])
            v["dlog_calib_vs_base"] = dlog(v["margin_calibrated"], base["margin_calibrated"])
            v["dlog_lognorm_vs_base"] = dlog(v["margin_lognorm"], base["margin_lognorm"])
            print(f"  vs base {tg}: dlog margin raw {v['dlog_raw_vs_base']:+.3f} -> "
                  f"calib {v['dlog_calib_vs_base']:+.3f}  lognorm {v['dlog_lognorm_vs_base']:+.3f} "
                  f"(if calib/lognorm ~0 the margin-down was confidence/scale)", flush=True)
    return res


def task_trajectory(args, dev, Xte, yte, Xtr, ytr):
    """M6: per-epoch checkpoints in --ckpt_dir (any *.pt). For each, L on a fixed test subset and the
    train-test ROBUST-acc gap. H-B: late-epoch L sharpening in +0 but not +synth."""
    import glob
    files = sorted(glob.glob(os.path.join(args.ckpt_dir, "*.pt")))
    if not files:
        print(f"[trajectory] no *.pt in {args.ckpt_dir}; needs per-epoch checkpoints (see --save_ckpt_every "
              "in MECHANISM_EXPERIMENTS.md)", flush=True)
        return {}
    Xtr_s, ytr_s = Xtr[:args.npts], ytr[:args.npts]
    Xte_s, yte_s = Xte[:args.npts], yte[:args.npts]
    curve = []
    for path in files:
        model, meta = load_ckpt(path, dev)
        ep = meta.get("epoch", -1)
        Ls = L_stats(model, Xte_s, dev)
        rtr = CD.pgd_acc(model, Xtr_s, ytr_s, dev, EPS, "linf", steps=args.pgd_steps)
        rte = CD.pgd_acc(model, Xte_s, yte_s, dev, EPS, "linf", steps=args.pgd_steps)
        row = dict(epoch=ep, n_syn=meta.get("n_syn"), seed=meta.get("seed"),
                   L2=Ls["L2"], L1=Ls["L1"], margin=Ls["margin"],
                   robust_train=rtr, robust_test=rte, robust_gap=rtr - rte, file=os.path.basename(path))
        curve.append(row)
        print(f"[trajectory] ep{ep} syn{meta.get('n_syn')}: L2={Ls['L2']:.3f} "
              f"rob_train={rtr:.3f} rob_test={rte:.3f} gap={rtr - rte:+.3f}", flush=True)
    return dict(curve=curve)


TASKS = {"manifold": task_manifold, "curvature": task_curvature, "weightsharp": task_weightsharp,
         "calib": task_calib, "trajectory": task_trajectory}


# ----------------------------------------------------------------------------- smoke checkpoint
def _make_smoke_ckpts(dev):
    """Two tiny CPU-trained checkpoints (syn0 + 'syn256') so the smoke exercises load + every probe + the
    arm comparison. A few clean SGD steps only -- enough to break symmetry, NOT a real model."""
    out = os.path.join(HERE, "results", "mech", "_smoke_ckpts")
    os.makedirs(out, exist_ok=True)
    Xtr, ytr, _, _ = CD.load_cifar(256, 64, seed=0)
    paths = []
    for n_syn in (0, 256):
        torch.manual_seed(n_syn)
        model = build_model().to(dev).train()
        opt = torch.optim.SGD(model.parameters(), lr=0.05, momentum=0.9)
        for ep in range(2):
            perm = torch.randperm(len(Xtr))
            for i in range(0, len(Xtr), 128):
                idx = perm[i:i + 128]
                opt.zero_grad(set_to_none=True)
                F.cross_entropy(model(Xtr[idx].to(dev)), ytr[idx].to(dev)).backward(); opt.step()
                # save an "epoch" ckpt for the trajectory task
                p = os.path.join(out, f"syn{n_syn}_s0_ep{ep}.pt")
                torch.save(dict(state_dict=model.state_dict(), arm="stdzero", width=1.0,
                                n_syn=n_syn, seed=0, epoch=ep), p)
        p = os.path.join(out, f"syn{n_syn}_s0_final.pt")
        torch.save(dict(state_dict=model.eval().state_dict(), arm="stdzero", width=1.0,
                        n_syn=n_syn, seed=0, epoch=2), p)
        paths.append(p)
    return paths, out


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=list(TASKS) + ["all"], default="all")
    ap.add_argument("--ckpts", nargs="+", default=[], help="checkpoint(s); first with n_syn==0 = baseline")
    ap.add_argument("--ckpt_dir", default="", help="dir of per-epoch *.pt for --task trajectory")
    ap.add_argument("--synth_npz", default=DATA_NPZ, help="EDM pool for the 'synth' point set (manifold)")
    ap.add_argument("--gpu", type=int, default=None, help="cuda index; omit/None -> CPU")
    ap.add_argument("--n", type=int, default=50000); ap.add_argument("--ntest", type=int, default=10000)
    ap.add_argument("--npts", type=int, default=512, help="#points per probe (test/curvature/sharp/calib)")
    ap.add_argument("--anchors", type=int, default=4000, help="#real anchors for local-PCA tangent")
    ap.add_argument("--knn", type=int, default=64); ap.add_argument("--dtan", type=int, default=30)
    ap.add_argument("--gauss_sigma", type=float, default=0.1)
    ap.add_argument("--fd_h", type=float, default=0.25, help="finite-diff L2 step for curvature (CURE)")
    ap.add_argument("--fd_rand", type=int, default=3, help="#random directions for FD curvature avg")
    ap.add_argument("--power_iters", type=int, default=20); ap.add_argument("--hess_bs", type=int, default=16)
    ap.add_argument("--rho", type=float, default=0.05); ap.add_argument("--trials", type=int, default=5)
    ap.add_argument("--adv", action="store_true", help="weightsharp/trajectory use robust (PGD) loss")
    ap.add_argument("--pgd_steps", type=int, default=20)
    ap.add_argument("--tag", default="run")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    if args.smoke:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""                      # never touch the GPUs in smoke
        torch.set_num_threads(min(4, os.cpu_count() or 2))
        args.gpu = None
        args.n, args.ntest, args.npts, args.anchors = 256, 256, 8, 64
        args.knn, args.dtan, args.power_iters, args.hess_bs = 16, 6, 5, 4
        args.fd_rand, args.trials, args.pgd_steps = 2, 2, 3
        args.tag = "smoke"

    dev = f"cuda:{args.gpu}" if (args.gpu is not None and torch.cuda.is_available()) else "cpu"
    Xtr, ytr, Xte, yte = CD.load_cifar(args.n, args.ntest, seed=0)

    if args.smoke and not args.ckpts:
        args.ckpts, smoke_dir = _make_smoke_ckpts(dev)
        if not args.ckpt_dir:
            args.ckpt_dir = smoke_dir
        args.synth_npz = ""                                         # fabricate synth instead of 3GB load

    tasks = list(TASKS) if args.task == "all" else [args.task]
    t0 = time.time()
    for tk in tasks:
        if tk == "trajectory" and not args.ckpt_dir:
            print("[skip] trajectory needs --ckpt_dir (per-epoch checkpoints)", flush=True); continue
        if tk != "trajectory" and not args.ckpts:
            print(f"[skip] {tk} needs --ckpts", flush=True); continue
        res = TASKS[tk](args, dev, Xte, yte, Xtr, ytr)
        _save(args.tag, tk, dict(task=tk, args=vars(args), result=res))
    print(f"\n[done] {tasks} in {time.time() - t0:.1f}s on {dev}", flush=True)


if __name__ == "__main__":
    main()
