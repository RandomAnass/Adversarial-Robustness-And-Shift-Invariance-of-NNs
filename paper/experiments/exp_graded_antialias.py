#!/usr/bin/env python3
"""
GRADED anti-aliasing adversarial-training experiment (supplementary to cifar_at.py).

WHY. The paper's headline -- "shift-consistency anti-predicts robustness under adversarial
training" -- is partly confounded: the exactly-invariant `circular` arm also UNDER-FITS (low clean
accuracy), so consistency and clean accuracy move together and the consistency effect cannot be
read off cleanly. Anti-aliased BlurPool with WIDER low-pass filters (Zhang 2019) raises
shift-consistency at little clean-accuracy cost. A graded sweep over filter WIDTH therefore varies
consistency AT (roughly) MATCHED CLEAN ACCURACY, decoupling the consistency effect from clean
accuracy. The decisive question, asked WITHIN this matched-accuracy graded family: does the
threat-matched eta/L (margin / ||grad M||_1 for an Linf adversary) predict robustness (it should),
and does plain shift-consistency track within the family but stop being the unifying axis once the
`circular` reference endpoint is included (eta/L is)?

Graded blur family (1-D taps, separable, fixed/non-learnable -> ZERO added parameters):
  blur2 : Rect-2 [1,1]              (mild low-pass)
  blur3 : Tri-3  [1,2,1]            (== the paper's `blurpool` arm, numerically identical)
  blur5 : Bin-5  [1,4,6,4,1]
  blur7 : Bin-7  [1,6,15,20,15,6,1] (strong low-pass; highest consistency)
plus the two PAPER reference arms, reused VERBATIM from cifar_dissection.CIFARNet:
  standard : MaxPool(2) aliased baseline      (lowest consistency)
  circular : exact cyclic-shift invariance    (consistency ~1, the reference endpoint)

Because the blur filters are fixed buffers and MaxPool/Identity carry no parameters, ALL six arms
have IDENTICAL parameter counts (capacity matched; asserted in --smoke).

Recipe is cifar_at.py's CIFAR Linf PGD-AT VERBATIM (eps=8/255, 7 steps, alpha=2/255, flip aug,
cosine SGD): the training loop (`adv_train`) and every evaluator (AutoAttack, DDN L2 radius, eta/L
decomposition, PGD masking check) are IMPORTED, not reimplemented. This file changes only (a) the
downsample operator -> a graded BlurPoolG, via build_graded, and (b) the partial-save directory ->
results/at_partial/graded_antialias/ . cifar_dissection.py / cifar_at.py / cifar_at_parallel.py are
left untouched.

Smoke (CPU/1-GPU, no full sweep):
  PYTHONNOUSERSITE=1 ../env/cenv/bin/python exp_graded_antialias.py --smoke
Full sweep is printed by --smoke and is meant to be launched by the user with GPU scheduling.
"""
import argparse, os, json, time, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
import torch.multiprocessing as mp
from itertools import product

# Reuse the validated backbone + every evaluator/trainer VERBATIM (do NOT reimplement).
from cifar_dissection import (CIFARNet, build, train as plain_train, accuracy, correct_mask,
                              shift_consistency, robust_radius_l2, etaL_decomposition,
                              autoattack_acc, pgd_acc, nparams, load_cifar, circular_roll,
                              CIFAR_MEAN, CIFAR_STD)
from cifar_at import adv_train

RESDIR = os.path.join(os.path.dirname(__file__), "..", "results")

# ---------------- graded 1-D tap families (separable low-pass) ----------------
TAPS = {
    "blur2": [1., 1.],                       # Rect-2
    "blur3": [1., 2., 1.],                   # Tri-3  (== paper blurpool)
    "blur5": [1., 4., 6., 4., 1.],           # Bin-5
    "blur7": [1., 6., 15., 20., 15., 6., 1.],  # Bin-7
}
BLUR_ARMS = ["blur2", "blur3", "blur5", "blur7"]
REF_ARMS = ["standard", "circular"]
ARMS = BLUR_ARMS + REF_ARMS

def arm_taps(arm):
    """Tap descriptor stored in each partial JSON (a list for blur arms; a label otherwise)."""
    if arm in TAPS: return list(TAPS[arm])
    return "maxpool" if arm == "standard" else "identity"

# ---------------- graded BlurPool: BlurPool2d generalized to arbitrary tap length ----------------
class BlurPoolG(nn.Module):
    """Anti-aliased downsample with an arbitrary separable low-pass tap vector `taps` (Zhang 2019).
    Fixed (non-learnable) buffer -> adds NO parameters. Reflect-padded so that stride-`stride` output
    spatial size is ceil(H/stride) for ANY tap length L:
        pad_left = (L-1)//2 , pad_right = L//2
    (even L like Rect-2 -> asymmetric (0,1); odd L -> symmetric). For stride 2 and L taps the padded
    size is H+L-1, and conv(kernel L, stride 2, no pad) -> floor((H-1)/2)+1 = ceil(H/2). For L=[1,2,1]
    this is byte-for-byte cifar_dissection.BlurPool2d (reflect pad (1,1,1,1))."""
    def __init__(self, ch, stride=2, taps=(1., 2., 1.)):
        super().__init__()
        a = torch.tensor(list(taps), dtype=torch.float32)
        k = a[:, None] * a[None, :]; k = k / k.sum()       # separable 2-D kernel, normalized to sum 1
        self.register_buffer("filt", k[None, None].repeat(ch, 1, 1, 1))
        self.ch = ch; self.stride = stride
        L = len(a); self.padL = (L - 1) // 2; self.padR = L // 2
    def forward(self, x):
        x = F.pad(x, (self.padL, self.padR, self.padL, self.padR), mode="reflect")
        return F.conv2d(x, self.filt, stride=self.stride, groups=self.ch)

# ---------------- graded model: paper CIFARNet backbone, graded downsample at stages 0,1 ----------------
def build_graded(arm, w):
    """Dispatch. `standard`/`circular` reuse the paper's CIFARNet EXACTLY (so the two endpoints are
    identical to the paper's arms). Blur arms reuse the SAME zero-pad backbone as the paper's
    `blurpool` arm and only swap the two downsample ops for a graded BlurPoolG -> identical params."""
    if arm in REF_ARMS:
        return build(arm, w)                               # paper arm, untouched
    if arm not in TAPS:
        raise ValueError(f"unknown arm {arm!r}; expected one of {ARMS}")
    m = CIFARNet(arm="blurpool", w=w)                      # zero-pad backbone + BlurPool downs (params identical)
    chs = [3, w, 2 * w, 4 * w]
    for s in (0, 1):                                        # downsample after stages 0,1 only (paper layout)
        m.downs[s] = BlurPoolG(chs[s + 1], stride=2, taps=TAPS[arm])
    m.arm = arm
    return m

# ---------------- feature-level shift-stability (low-noise architectural companion to consistency) ----
@torch.no_grad()
def gap_features(model, x):
    """Penultimate GAP feature vector (the shift-invariant readout fed to the linear head), recomputed
    from the model's own layers (no forbidden-file edits, no forward hook)."""
    z = model.norm(x)
    for stage, down in zip(model.stages, model.downs):
        z = down(stage(z))
    return z.mean(dim=(2, 3))

@torch.no_grad()
def feature_shift_instability(model, X, dev, max_shift=4, reps=4, n_max=2000, bs=256):
    """Mean COSINE distance 1 - cos(phi(x), phi(roll(x))) of the GAP feature under random circular
    shifts. Scale-free (per-sample cosine), so unlike a relative-L2 measure it is NOT confounded by the
    low-pass energy drop. LOWER = more shift-stable; exactly 0 for the `circular` arm. A continuous,
    low-variance architectural axis that tracks anti-aliasing more cleanly than the (argmax-agreement,
    higher-variance) decision-level shift-consistency, especially below full training scale."""
    model = model.eval(); X = X[:n_max].to(dev); tot = []
    for r in range(reps):
        for i in range(0, len(X), bs):
            xb = X[i:i + bs]
            torch.manual_seed(10007 * r + i)               # reproducible per-sample shift draw
            xs = circular_roll(xb, max_shift)
            z0 = gap_features(model, xb); z1 = gap_features(model, xs)
            tot.append(1.0 - F.cosine_similarity(z0, z1, dim=1))
    return float(torch.cat(tot).mean())

# ---------------- progressive (per-cell) save + resume, own subdir ----------------
def _partial_dir():
    return os.path.join(RESDIR, "at_partial", "graded_antialias")
def _job_file(arm, w, seed):
    return os.path.join(_partial_dir(), f"{arm}_w{w}_s{seed}.json")
def _save_job(out):
    d = _partial_dir(); os.makedirs(d, exist_ok=True)
    p = _job_file(out["arm"], out["w"], out["seed"]); tmp = p + ".tmp"
    json.dump(out, open(tmp, "w"), default=float); os.replace(tmp, p)   # atomic publish

# ---------------- one (arm,width,seed) cell: train PGD-AT, then evaluate ----------------
# Mirrors cifar_at.run_job_at body EXACTLY, differing only in (i) build -> build_graded (graded
# downsample) and (ii) the partial-save subdir. adv_train + all evaluators are the imported originals,
# so the recipe is byte-identical to cifar_at.py. (run_job_at could not be imported as-is because it
# hardwires build(); replicating the 12-line body is the minimal change.)
def run_job_graded(task):
    gpu, arm, w, seed, A = task
    dev = f"cuda:{gpu}" if (gpu is not None and torch.cuda.is_available()) else "cpu"
    if dev.startswith("cuda"): torch.cuda.set_device(gpu)
    Xtr, ytr, Xte, yte = load_cifar(A["n"], A["ntest"], seed=0)
    model = build_graded(arm, w)
    model = adv_train(model, Xtr, ytr, dev, epochs=A["epochs"], seed=seed,
                      eps=A["eps"], alpha=A["alpha"], steps=A["steps"], norm="linf",
                      aug=A["flip"], shift_aug=False)
    out = dict(arm=arm, w=w, seed=seed, params=nparams(model), taps=arm_taps(arm))
    out["clean"] = accuracy(model, Xte, yte, dev)
    out["consist"] = shift_consistency(model, Xte, dev)                  # decision-level (argmax agreement)
    out["feat_instab"] = feature_shift_instability(model, Xte, dev)      # feature-level (lower=more stable)
    cm = correct_mask(model, Xte, yte, dev); Xc, yc = Xte[cm], yte[cm]   # radius defined on clean-correct only
    out["rr_l2"] = robust_radius_l2(model, Xc[:A["rad_n"]], yc[:A["rad_n"]], dev)
    out["rr_n"] = int(min(A["rad_n"], len(Xc)))
    out.update({("dec_" + k): v for k, v in etaL_decomposition(model, Xte, yte, dev).items()})
    for (nm, norm, eps) in A["aa_specs"]:
        out["pgd_" + nm] = pgd_acc(model, Xte[:A["aa_n"]], yte[:A["aa_n"]], dev, eps,
                                   "linf" if norm == "Linf" else "l2", steps=A["pgd_steps"])
        out["aa_" + nm] = autoattack_acc(model, Xte, yte, dev, eps, norm,
                                         n=A["aa_n"], version=A["aa_version"])
    _save_job(out)                                          # publish this cell before returning
    return out

# ---------------- parallel worker (CPU-affinity-pinned), mirrors cifar_at_parallel ----------------
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
        arm, w, seed = item
        try:
            run_job_graded((gpu, arm, w, seed, A))         # saves to disk; parent reads from disk
        except Exception as e:
            print(f"[worker {wid} gpu{gpu}] {(arm,w,seed)} FAILED: {type(e).__name__}: {e}", flush=True)

def _schedule(pending, ng, nw, A):
    """Run a list of (arm,w,seed) over ng GPUs x (nw/ng) workers via a shared queue (disk = source of
    truth; an OOM'd worker just leaves its cell for the next resume)."""
    if not pending: return
    if ng <= 0:
        for (arm, w, s) in pending:
            run_job_graded((None, arm, w, s, A))
        return
    ctx = mp.get_context("spawn"); task_q = ctx.Queue()
    for t in pending: task_q.put(t)
    for _ in range(nw): task_q.put(None)
    procs = [ctx.Process(target=_worker, args=(wid, wid % ng, nw, task_q, A)) for wid in range(nw)]
    for p in procs: p.start()
    for p in procs: p.join()

# ---------------- self-checks (sizes + capacity match) ----------------
def verify_sizes():
    """Stride-2 output of BlurPoolG must be (.,.,16,16) on a (1,ch,32,32) input for EVERY tap length."""
    print("BlurPoolG stride-2 output sizes (expect 16x16 for all tap lengths):")
    ok = True
    for arm in BLUR_ARMS:
        bp = BlurPoolG(8, stride=2, taps=TAPS[arm]).eval()
        y = bp(torch.randn(1, 8, 32, 32))
        good = tuple(y.shape[-2:]) == (16, 16)
        ok &= good
        print(f"  {arm:6s} taps={str(TAPS[arm]):28s} padL,padR=({bp.padL},{bp.padR}) -> {tuple(y.shape)}  {'OK' if good else 'BAD'}")
    assert ok, "BlurPoolG produced a wrong stride-2 output size"
    return ok

def assert_capacity_matched(w):
    """All six arms must have IDENTICAL parameter counts (blur filters are non-learnable buffers)."""
    counts = {arm: nparams(build_graded(arm, w)) for arm in ARMS}
    base = counts["standard"]
    print(f"\nParameter counts at w={w} (must all be equal):")
    for arm in ARMS:
        print(f"  {arm:9s}: {counts[arm]:,}  {'OK' if counts[arm] == base else 'MISMATCH'}")
    assert len(set(counts.values())) == 1, f"capacity NOT matched: {counts}"
    return base, counts

# ---------------- aggregate + cross-cell correlations (read from disk) ----------------
def aggregate_and_report(arms, widths, seeds, aa_name):
    rows = []
    for w in widths:
        for arm in arms:
            rs = []
            for s in range(seeds):
                jf = _job_file(arm, w, s)
                if os.path.exists(jf):
                    try: rs.append(json.load(open(jf)))
                    except Exception: pass
            if not rs: continue
            def g(k): return float(np.mean([x[k] for x in rs if x.get(k) is not None]))
            rows.append(dict(arm=arm, w=w, clean=g("clean"), consist=g("consist"),
                             feat_instab=g("feat_instab"), rr_l2=g("rr_l2"),
                             margin=g("dec_margin"), L1=g("dec_L1"), L2=g("dec_L2"), etaL=g("dec_etaL"),
                             aa=g("aa_" + aa_name)))
    if not rows: return rows
    hdr = (f"{'arm':9s} {'w':>3s} {'clean':>6s} {'consist':>7s} {'featInst':>8s} {'margin/L1':>9s} "
           f"{'rr_L2':>6s} {'aa_'+aa_name:>13s}")
    print("\n" + hdr); print("-" * len(hdr))
    for x in rows:
        x["match"] = x["margin"] / x["L1"] if x["L1"] else float("nan")   # Linf threat-matched eta/L
        print(f"{x['arm']:9s} {x['w']:3d} {x['clean']:6.3f} {x['consist']:7.3f} {x['feat_instab']:8.4f} "
              f"{x['match']:9.4f} {x['rr_l2']:6.3f} {x['aa']:13.3f}")
    if len(rows) >= 3:
        from scipy.stats import pearsonr, spearmanr
        aa = np.array([x["aa"] for x in rows]); mt = np.array([x["match"] for x in rows])
        cs = np.array([x["consist"] for x in rows]); fi = np.array([x["feat_instab"] for x in rows])
        blur = [x for x in rows if x["arm"] in BLUR_ARMS]
        print(f"\nAcross {len(rows)} cells [graded Linf-AT, AA={aa_name}]:")
        print(f"  MATCHED eta/L (margin/||grad M||_1) vs AA : Pearson {pearsonr(mt,aa)[0]:+.3f} Spearman {spearmanr(mt,aa)[0]:+.3f}")
        print(f"  decision shift-consistency          vs AA : Pearson {pearsonr(cs,aa)[0]:+.3f} Spearman {spearmanr(cs,aa)[0]:+.3f}")
        print(f"  feature shift-instability           vs AA : Pearson {pearsonr(fi,aa)[0]:+.3f} Spearman {spearmanr(fi,aa)[0]:+.3f}")
        if len(blur) >= 3:   # WITHIN the matched-clean-accuracy graded family (blur arms only)
            aab = np.array([x["aa"] for x in blur]); csb = np.array([x["consist"] for x in blur])
            mtb = np.array([x["match"] for x in blur]); fib = np.array([x["feat_instab"] for x in blur])
            print(f"  [blur family only] consistency vs AA : Pearson {pearsonr(csb,aab)[0]:+.3f}")
            print(f"  [blur family only] feat_instab vs AA : Pearson {pearsonr(fib,aab)[0]:+.3f}")
            print(f"  [blur family only] eta/L       vs AA : Pearson {pearsonr(mtb,aab)[0]:+.3f}")
    return rows

# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50000); ap.add_argument("--ntest", type=int, default=10000)
    ap.add_argument("--epochs", type=int, default=30); ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--widths", type=int, nargs="+", default=[32, 48])
    ap.add_argument("--arms", nargs="+", default=ARMS)
    ap.add_argument("--rad_n", type=int, default=1000); ap.add_argument("--aa_n", type=int, default=2000)
    ap.add_argument("--aa_version", default="standard"); ap.add_argument("--pgd_steps", type=int, default=40)
    ap.add_argument("--gpus", type=int, default=2); ap.add_argument("--workers_per_gpu", type=int, default=2)
    ap.add_argument("--circ_workers_per_gpu", type=int, default=1,
                    help="concurrency cap for the heavy full-res `circular` arm (avoid AA OOM)")
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--tag", default="graded")
    args = ap.parse_args()
    widths, arms = args.widths, args.arms
    # CIFAR Linf PGD-AT recipe -- VERBATIM from cifar_at.py RECIPE[("cifar","linf")].
    EPS, STEPS, ALPHA, FLIP = 8 / 255, 7, 2 / 255, True
    aa_specs = [("Linf_8_255", "Linf", 8 / 255)]            # supplementary: threat-matched AA only

    if args.smoke:
        # tiny end-to-end CPU check: trains (PGD-AT), evaluates, asserts capacity match, writes a
        # partial JSON, and shows wider blur -> higher consistency. Does NOT launch the full sweep.
        torch.set_num_threads(max(1, (os.cpu_count() or 8) // 2))
        print("=== SMOKE: BlurPoolG size check ==="); verify_sizes()
        print("\n=== SMOKE: capacity-match assertion (all six arms) ===")
        base, _ = assert_capacity_matched(16)

        # (1) END-TO-END PGD-AT cell(s): proves train -> eval (AA/radius/eta-L) -> valid partial JSON
        # on the REAL recipe. Two arms is enough for the pipeline check.
        A = dict(n=1000, ntest=500, epochs=2, eps=EPS, alpha=ALPHA, steps=STEPS, flip=FLIP,
                 rad_n=200, aa_n=200, aa_version="custom", pgd_steps=10, aa_specs=aa_specs)
        at_arms = ["blur2", "blur7"]
        print(f"\n=== SMOKE: end-to-end PGD-AT cells {at_arms} on CPU "
              f"(n={A['n']}, epochs={A['epochs']}, aa_n={A['aa_n']}) ===", flush=True)
        for arm in at_arms:
            t0 = time.time()
            out = run_job_graded((None, arm, 16, 0, A))
            print(f"  {arm:6s} clean={out['clean']:.3f} consist={out['consist']:.3f} "
                  f"margin={out['dec_margin']:.3f} L1={out['dec_L1']:.3f} "
                  f"rr_l2={out['rr_l2']:.3f} aa={out['aa_Linf_8_255']:.3f}  ({time.time()-t0:.0f}s)", flush=True)
        sample = _job_file("blur7", 16, 0)
        print(f"\n=== SMOKE: sample partial JSON ({sample}) ===")
        print(json.dumps(json.load(open(sample)), indent=2))

        # (2) SHIFT-STABILITY probe. Anti-aliasing -> more shift-stable is an ARCHITECTURAL property,
        # only resolvable on a DISCRIMINATIVE model (a 2-epoch near-chance model has collapsed/noisy
        # predictions that saturate the metric). We plain-train each arm to be discriminative (plain SGD
        # is ~steps x cheaper than PGD-AT, so this stays a fast CPU smoke) -- same build_graded
        # architecture as the AT cells -- and report BOTH the feature-level shift-instability (1-cos of
        # the GAP feature; low-variance) and the decision-level shift-consistency (argmax agreement;
        # high-variance). At this tiny scale (w=16, n=4000, 1 seed) the clean, reproducible signal is at
        # the FEATURE level: aliased `standard` is least stable, anti-aliased blur arms are more stable,
        # and `circular` is exactly invariant. The fine within-blur-WIDTH monotonicity and the
        # decision-level gradient are a few-% effect below the smoke noise floor -> they need the
        # full-scale, seed-averaged sweep.
        probe_arms = ["standard", "blur2", "blur3", "blur5", "blur7", "circular"]
        Xtr, ytr, Xte, yte = load_cifar(4000, 1000, seed=0)
        print(f"\n=== SMOKE: shift-stability probe (plain-trained discriminative models) {probe_arms} ===", flush=True)
        fi, cs = {}, {}
        for arm in probe_arms:
            t0 = time.time()
            m = plain_train(build_graded(arm, 16), Xtr, ytr, "cpu", epochs=12, seed=0, aug=True)
            fi[arm] = feature_shift_instability(m, Xte, "cpu"); cs[arm] = shift_consistency(m, Xte, "cpu")
            print(f"  {arm:9s} clean={accuracy(m, Xte, yte, 'cpu'):.3f}  feat_instab(1-cos)={fi[arm]:.4f}  "
                  f"decision_consist={cs[arm]:.3f}  ({time.time()-t0:.0f}s)", flush=True)
        blur_more_stable = all(fi[a] < fi["standard"] for a in BLUR_ARMS)
        circ_invariant = fi["circular"] < 1e-4
        print(f"\nfeature shift-instability (lower=more stable): "
              f"{ {a: round(fi[a],4) for a in probe_arms} }")
        print(f"CONFIRMED anti-aliasing -> more shift-stable: every blur arm beats aliased `standard` "
              f"({fi['standard']:.4f}): {blur_more_stable}")
        print(f"CONFIRMED `circular` exactly shift-invariant (feat_instab ~ 0): {circ_invariant}")
        print(f"(decision-level shift-consistency at this scale is within noise: "
              f"{ {a: round(cs[a],3) for a in probe_arms} } -- the within-blur-width gradient resolves at full scale)")

        # the exact full-sweep command (launched by the user with GPU scheduling)
        print("\n=== FULL SWEEP COMMAND (run with proper GPU scheduling; NOT launched here) ===")
        print("PYTHONNOUSERSITE=1 AA_BS=500 ../env/cenv/bin/python exp_graded_antialias.py "
              "--gpus 2 --workers_per_gpu 2 --circ_workers_per_gpu 1")
        return

    # ---- full sweep ----
    assert_capacity_matched(max(widths))                   # fail fast if capacity ever drifts
    A = dict(n=args.n, ntest=args.ntest, epochs=args.epochs, eps=EPS, alpha=ALPHA, steps=STEPS,
             flip=FLIP, rad_n=args.rad_n, aa_n=args.aa_n, aa_version=args.aa_version,
             pgd_steps=args.pgd_steps, aa_specs=aa_specs)
    load_cifar(10, 10)                                      # download once before forking
    ng = min(args.gpus, torch.cuda.device_count()) if torch.cuda.is_available() else 0
    K = max(1, args.workers_per_gpu); Kc = max(1, min(K, args.circ_workers_per_gpu))

    # resume: skip cells already on disk (progressive save)
    all_cells = list(product(arms, widths, range(args.seeds)))
    pending = [(a, w, s) for (a, w, s) in all_cells if not os.path.exists(_job_file(a, w, s))]
    light = sorted([c for c in pending if c[0] != "circular"], key=lambda c: c[1] * c[1], reverse=True)
    heavy = sorted([c for c in pending if c[0] == "circular"], key=lambda c: c[1] * c[1], reverse=True)
    done = len(all_cells) - len(pending)
    print(f"graded anti-alias PGD-AT (cifar linf eps=8/255, 7 steps): {len(all_cells)} cells, "
          f"{done} resumed, {len(pending)} to run over {ng or 'CPU'} GPU(s); arms={arms} widths={widths} "
          f"seeds={args.seeds} (light K={K}/gpu, circular Kc={Kc}/gpu)\n", flush=True)
    t0 = time.time()
    # phase 1: light arms (blur*, standard) at full concurrency
    _schedule(light, ng, max(1, ng * K) if ng > 0 else 1, A)
    # phase 2: heavy `circular` arm (full-res, heavy AA) at capped concurrency -> avoids OOM
    _schedule(heavy, ng, max(1, ng * Kc) if ng > 0 else 1, A)
    print(f"\nwall {time.time()-t0:.0f}s", flush=True)

    rows = aggregate_and_report(arms, widths, args.seeds, aa_specs[0][0])
    missing = [(a, w, s) for (a, w, s) in all_cells if not os.path.exists(_job_file(a, w, s))]
    if missing:
        print(f"\nWARNING: {len(missing)} cell(s) missing (worker died/OOM?): {missing} -- re-run to resume", flush=True)
    os.makedirs(RESDIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    fn = os.path.join(RESDIR, f"graded_antialias_{args.tag}_{stamp}.json")
    recipe = dict(dataset="cifar", norm="linf", eps=EPS, alpha=ALPHA, steps=STEPS, flip=FLIP,
                  taps={a: arm_taps(a) for a in arms})
    json.dump(dict(args=vars(args), recipe=recipe, aa_specs=aa_specs, rows=rows), open(fn, "w"), indent=2)
    print(f"saved {fn}", flush=True)

if __name__ == "__main__":
    main()
