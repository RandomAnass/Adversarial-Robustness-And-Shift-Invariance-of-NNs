#!/usr/bin/env python3
"""
S3: WIDE-BAND threat-matched eta/L1 law via an ADVERSARIAL-TRAINING-STRENGTH (eps) sweep.

The paper's diffusion data-axis (diff_pilot_v2.py) traces the threat-matched eta/L1 = margin/||grad M||_1
(Linf-dual) vs AutoAttack law over only 4 doses at a FIXED eps=8/255, so eta/L1 spans a NARROW band
(~0.041-0.044) and Pearson ~ +0.85 only "confirms the direction". Reviewers called this underpowered.

This script traces the SAME law over a WIDE eta/L1 band by sweeping the AT strength eps in
{2,4,8,16}/255. Varying eps produces PreActResNet-18 models at very different first-order radii
(eta/L1) and very different robustness. CRITICALLY, each model is evaluated THREAT-MATCHED: AutoAttack
and the PGD masking-check are run at the SAME Linf eps the model was trained on, and eta/L1 stays
margin/||grad M||_1 (the Linf-dual, threat-matched ratio).

Per cell (eps, dose, seed) we ALSO do fair best-robust EARLY STOPPING (val PGD robust acc, in-loop)
and report the TRAIN-TEST ROBUST GAP (robust-train-acc - robust-test-acc at the best checkpoint) so the
data-axis OFFSET above the architecture arms can be characterized as robust generalization or not.

This is a COPY of the diff_pilot_v2 harness (reuses its infra via `import diff_pilot_v2 as DV`) with:
  * a per-cell Linf eps (numerator/255); ALPHA = eps/4 (4x ratio kept); PGD_STEPS = 7 (unchanged).
  * AutoAttack + PGD evaluated THREAT-MATCHED at the training eps (not fixed 8/255).
  * in-loop best-robust early stopping + a real-train vs test robust-generalization gap.
Default --eps 8 reproduces the v2 8/255 recipe (alpha 2/255), so the 8/255 behavior is unchanged.

Grid (S3): eps in {2,4,8,16}/255  x  dose in {0, 1000000}  x  2 seeds, 40 epochs, real_frac=0.3.
Launch (GPU 1 ONLY; we set CUDA_VISIBLE_DEVICES=1 so cuda:0 == physical GPU1):
    CUDA_VISIBLE_DEVICES=1 PYTHONNOUSERSITE=1 ../env/cenv/bin/python diff_pilot_s3.py \
        --eps 2 8 --doses 0 1000000 --seeds 2 --epochs 40 --tag s3eps --gpu 0
Smoke (CPU, tiny):
    PYTHONNOUSERSITE=1 ../env/cenv/bin/python diff_pilot_s3.py --smoke
"""
import argparse, os, sys, json, time, math, copy
import numpy as np, torch, torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
import diff_pilot_v2 as DV                 # reuses sys.path setup + CD/CAT/M + radius/logit-scale/synth
CD, CAT, M = DV.CD, DV.CAT, DV.M
RESDIR = DV.RESDIR
PARTDIR = DV.PARTDIR

LR, MOM, WD = DV.LR, DV.MOM, DV.WD
PGD_STEPS = DV.PGD_STEPS                    # 7 (unchanged training inner steps)


# --------------------------------------------------------- mixed PGD-AT with in-loop early stopping
def adv_train_earlystop(model, Xr, yr, Xs_u8, ys, Xval, yval, dev, A, cell, eps, alpha):
    """Linf PGD-AT (eps, alpha=eps/4, PGD-7) identical to DV.adv_train_mixed, BUT every A['val_every']
    epochs we score val PGD robust acc at eps and keep the best model state (fair best-robust early
    stopping in-loop, avoids saving a trajectory of checkpoints). Returns (best_state, best_ep, best_rob).
    """
    model = model.to(dev).train()
    opt = torch.optim.SGD(model.parameters(), lr=LR, momentum=MOM, weight_decay=WD, nesterov=True)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=A["epochs"])
    n_real = len(Xr)
    steps_per_epoch = math.ceil(n_real / A["bs"])
    nb_real = A["bs"] if Xs_u8 is None else int(round(A["real_frac"] * A["bs"]))
    nb_syn = 0 if Xs_u8 is None else A["bs"] - nb_real
    best_state, best_ep, best_rob = None, -1, -1.0
    for ep in range(A["epochs"]):
        if Xs_u8 is None:
            perm = torch.randperm(n_real, device=dev)
        ep_loss, ep_correct, ep_seen = 0.0, 0, 0
        for it in range(steps_per_epoch):
            if Xs_u8 is None:
                idx = perm[it * A["bs"]:(it + 1) * A["bs"]]
                xb, yb = Xr[idx], yr[idx]
            else:
                ir = torch.randint(0, n_real, (nb_real,), device=dev)
                isy = torch.randint(0, len(Xs_u8), (nb_syn,), device=dev)
                xb = torch.cat([Xr[ir], Xs_u8[isy].float().div_(255.0)], 0)
                yb = torch.cat([yr[ir], ys[isy]], 0)
            flip = torch.rand(xb.size(0), device=dev) < 0.5
            xb = torch.where(flip[:, None, None, None], xb.flip(-1), xb)
            x_adv = CAT.pgd_linf(model, xb, yb, eps, alpha, PGD_STEPS)
            opt.zero_grad(set_to_none=True)
            logits = model(x_adv)
            loss = F.cross_entropy(logits, yb)
            loss.backward(); opt.step()
            with torch.no_grad():
                ep_loss += float(loss) * yb.size(0)
                ep_correct += int((logits.argmax(1) == yb).sum()); ep_seen += yb.size(0)
        sched.step()
        # in-loop best-robust early-stop selection (cheap val PGD at the training eps)
        do_val = ((ep + 1) % A["val_every"] == 0) or (ep + 1 == A["epochs"])
        val_rob = float("nan")
        if do_val:
            model.eval()
            val_rob = CD.pgd_acc(model, Xval, yval, dev, eps, "linf", steps=A["sel_steps"])
            model.train()
            if val_rob > best_rob:
                best_rob, best_ep = val_rob, ep + 1
                best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        print(f"  [{cell}] ep {ep + 1:>3d}/{A['epochs']}  loss {ep_loss / max(ep_seen, 1):.4f}  "
              f"rob_train {ep_correct / max(ep_seen, 1):.4f}  val_rob {val_rob if do_val else float('nan'):.4f}  "
              f"lr {sched.get_last_lr()[0]:.4f}", flush=True)
    if best_state is None:                              # safety: fall back to final weights
        best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        best_ep, best_rob = A["epochs"], val_rob
    return best_state, best_ep, best_rob


# ----------------------------------------------------------------------------- partial-save / resume
def cell_key(A, eps255, n_syn, seed):
    rf = f"{A['real_frac']:.3f}".rstrip("0").rstrip(".")
    return (f"{A['tag']}_eps{eps255:g}_arm-{A['arm']}_w{A['width']:g}_syn{n_syn}_s{seed}"
            f"_e{A['epochs']}_bs{A['bs']}_rf{rf}")


def cell_path(A, eps255, n_syn, seed):
    return os.path.join(PARTDIR, cell_key(A, eps255, n_syn, seed) + ".json")


def save_cell_atomic(A, out):
    os.makedirs(PARTDIR, exist_ok=True)
    p = cell_path(A, out["eps255"], out["n_syn"], out["seed"]); tmp = p + ".tmp"
    json.dump(out, open(tmp, "w"), default=float); os.replace(tmp, p)


# ----------------------------------------------------------------------------- one cell (train+eval)
def run_cell(gpu, eps255, n_syn, seed, A):
    dev = f"cuda:{gpu}" if (gpu is not None and torch.cuda.is_available()) else "cpu"
    if dev.startswith("cuda"):
        torch.cuda.set_device(gpu)
    eps = eps255 / 255.0
    alpha = eps / 4.0
    cell = f"eps{eps255:g}_syn{n_syn}_s{seed}"
    t0 = time.time()
    print(f"[start] {cell} | eps={eps255}/255 alpha={eps255/4:g}/255 pgd_steps={PGD_STEPS} arm={A['arm']} "
          f"epochs={A['epochs']} bs={A['bs']} real_frac={A['real_frac']} dev={dev}", flush=True)

    torch.manual_seed(seed)
    Xtr, ytr, Xte, yte = CD.load_cifar(A["n"], A["ntest"], seed=0)
    # val (selection) disjoint from report (all reported metrics) -- no selection-on-test bias
    Xval, yval = Xte[:A["val_n"]].to(dev), yte[:A["val_n"]].to(dev)
    Xrep, yrep = Xte[A["val_n"]:], yte[A["val_n"]:]
    Xr, yr = Xtr.to(dev), ytr.to(dev)
    Xs_u8, ys = (None, None)
    if n_syn > 0:
        xs, ls = DV.load_synth(n_syn, seed=A["synth_seed"])
        Xs_u8, ys = xs.to(dev), ls.to(dev)
    model = M.build(A["arm"], width=A["width"]).to(dev)
    best_state, best_ep, best_rob = adv_train_earlystop(model, Xr, yr, Xs_u8, ys, Xval, yval, dev, A,
                                                        cell, eps, alpha)
    model.load_state_dict(best_state); model.eval()     # report at the best (early-stopped) checkpoint
    if A.get("save_ckpt"):
        ck = os.path.join(HERE, "ckpts"); os.makedirs(ck, exist_ok=True)
        torch.save(dict(state_dict=best_state, arm=A["arm"], width=A["width"], eps255=eps255,
                        n_syn=int(n_syn), seed=int(seed), epoch=int(best_ep)),
                   os.path.join(ck, f"{A['tag']}_eps{eps255:g}_syn{n_syn}_s{seed}_best.pt"))
    del Xs_u8, ys
    if dev.startswith("cuda"):
        torch.cuda.empty_cache()

    out = dict(eps255=float(eps255), eps=eps, alpha=alpha, n_syn=int(n_syn), seed=int(seed),
               epochs=A["epochs"], bs=A["bs"], arm=A["arm"], width=A["width"], real_frac=A["real_frac"],
               params=M.nparams(model), best_ep=int(best_ep), val_rob=float(best_rob))
    out["clean"] = CD.accuracy(model, Xrep, yrep, dev)
    out["consist"] = CD.shift_consistency(model, Xrep, dev)
    # DDN L2 radius on clean-correct report points (scale-free primary metric)
    cm = CD.correct_mask(model, Xrep, yrep, dev)
    Xc, yc = Xrep[cm], yrep[cm]
    rr = DV.robust_radius_l2_per_sample(model, Xc[:A["rad_n"]], yc[:A["rad_n"]], dev, steps=A["rad_steps"])
    fin = torch.isfinite(rr)
    out["rr_l2"] = float(rr[fin].mean()) if fin.any() else float("nan")
    out["rr_l2_median"] = float(rr[fin].median()) if fin.any() else float("nan")
    out["rr_n"] = int(min(A["rad_n"], len(Xc)))
    # eta/L decomposition (report split): margin, L1, L2, etaL(=eta/L2); threat-matched etaL1 = margin/L1
    dec = CD.etaL_decomposition(model, Xrep, yrep, dev, n_max=A["dec_n"])
    out.update({("dec_" + k): v for k, v in dec.items()})
    out["etaL1"] = dec["margin"] / dec["L1"] if dec["L1"] > 0 else float("nan")   # threat-matched (Linf)
    out["etaL2"] = dec["etaL"]                                                    # mismatched (L2-dual)
    out["dec_logit_scale"] = DV.mean_logit_scale(model, Xrep, yrep, dev, n_max=A["dec_n"])
    # THREAT-MATCHED strong attacks at the TRAINING eps: PGD masking-check then AutoAttack (AA <= PGD)
    out["eval_eps"] = eps
    out["pgd_matched"] = CD.pgd_acc(model, Xrep[:A["aa_n"]], yrep[:A["aa_n"]], dev, eps, "linf",
                                    steps=A["pgd_steps"])
    out["aa_matched"] = CD.autoattack_acc(model, Xrep, yrep, dev, eps, "Linf", n=A["aa_n"],
                                          version=A["aa_version"])
    # train-test ROBUST GAP at the best checkpoint: PGD robust acc on REAL train vs test (same eps/steps)
    gtr = min(A["gap_n"], len(Xtr))
    out["rob_train"] = CD.pgd_acc(model, Xtr[:gtr], ytr[:gtr], dev, eps, "linf", steps=A["pgd_steps"])
    out["rob_test"] = CD.pgd_acc(model, Xrep[:A["gap_n"]], yrep[:A["gap_n"]], dev, eps, "linf",
                                 steps=A["pgd_steps"])
    out["rob_gap"] = out["rob_train"] - out["rob_test"]
    out["wall_s"] = round(time.time() - t0, 1)

    save_cell_atomic(A, out)
    print(f"[done] {cell} | best_ep {best_ep} clean {out['clean']:.3f} | AA@eps {out['aa_matched']:.3f} "
          f"PGD@eps {out['pgd_matched']:.3f} | etaL1 {out['etaL1']:.4f} etaL2 {out['etaL2']:.3f} "
          f"rr_L2 {out['rr_l2']:.3f} | rob_gap {out['rob_gap']:+.3f} "
          f"(tr {out['rob_train']:.3f} te {out['rob_test']:.3f}) | {out['wall_s']:.0f}s", flush=True)
    return out


# --------------------------------------------------------------------------------- simple analysis
def _pearson(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _spearman(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    return _pearson(ra, rb)


# ----------------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eps", type=float, nargs="+", default=[8.0], help="Linf eps NUMERATORS over 255 (e.g. 2 4 8 16)")
    ap.add_argument("--doses", type=int, nargs="+", default=[0, 1000000], help="synthetic-pool sizes")
    ap.add_argument("--seeds", type=int, default=2, help="repeat each cell with seeds 0..N-1")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--bs", type=int, default=512)
    ap.add_argument("--real_frac", type=float, default=0.3)
    ap.add_argument("--arm", default="stdzero"); ap.add_argument("--width", type=float, default=1.0)
    ap.add_argument("--n", type=int, default=50000); ap.add_argument("--ntest", type=int, default=10000)
    ap.add_argument("--val_n", type=int, default=1000); ap.add_argument("--val_every", type=int, default=2)
    ap.add_argument("--sel_steps", type=int, default=10)
    ap.add_argument("--rad_n", type=int, default=1000); ap.add_argument("--rad_steps", type=int, default=300)
    ap.add_argument("--dec_n", type=int, default=1000)
    ap.add_argument("--aa_n", type=int, default=512); ap.add_argument("--aa_version", default="standard")
    ap.add_argument("--pgd_steps", type=int, default=40)
    ap.add_argument("--gap_n", type=int, default=2000, help="pts for the train/test robust-gap PGD")
    ap.add_argument("--synth_seed", type=int, default=0)
    ap.add_argument("--gpu", type=int, default=0, help="cuda index (with CUDA_VISIBLE_DEVICES=1 -> physical GPU1)")
    ap.add_argument("--cpu", action="store_true"); ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--tag", default="s3eps"); ap.add_argument("--save_ckpt", action="store_true")
    args = ap.parse_args()

    if args.smoke:
        args.cpu = True
        args.n, args.ntest, args.epochs, args.seeds = 256, 512, 2, 1
        args.eps = [4.0, 8.0]; args.doses = [0, 256]
        args.bs = 128; args.val_n, args.val_every, args.sel_steps = 64, 1, 3
        args.rad_n, args.rad_steps, args.dec_n = 24, 25, 64
        args.aa_n, args.aa_version, args.pgd_steps, args.gap_n = 16, "custom", 5, 64
        torch.set_num_threads(min(8, os.cpu_count() or 4))

    A = dict(n=args.n, ntest=args.ntest, epochs=args.epochs, bs=args.bs, real_frac=args.real_frac,
             arm=args.arm, width=args.width, val_n=args.val_n, val_every=args.val_every,
             sel_steps=args.sel_steps, rad_n=args.rad_n, rad_steps=args.rad_steps, dec_n=args.dec_n,
             aa_n=args.aa_n, aa_version=args.aa_version, pgd_steps=args.pgd_steps, gap_n=args.gap_n,
             synth_seed=args.synth_seed, tag=args.tag, save_ckpt=args.save_ckpt)
    gpu = None if args.cpu else args.gpu
    CD.load_cifar(10, 10)                                # trigger torchvision download once

    eps_list = sorted(set(args.eps)); doses = sorted(set(args.doses))
    grid = [(e, ns, s) for e in eps_list for ns in doses for s in range(args.seeds)]
    done, pending = [], []
    for (e, ns, s) in grid:
        p = cell_path(A, e, ns, s)
        if os.path.exists(p):
            try:
                done.append(json.load(open(p))); continue
            except Exception:
                pass
        pending.append((e, ns, s))
    print(f"S3 eps-sweep diffusion-AT: eps(255)={eps_list} doses={doses} seeds={args.seeds} "
          f"epochs={args.epochs} bs={args.bs} real_frac={args.real_frac} | {len(done)} resumed, "
          f"{len(pending)} to run on {'CPU' if gpu is None else f'cuda:{gpu}'}\n", flush=True)

    t0 = time.time()
    computed = []
    for (e, ns, s) in pending:
        computed.append(run_cell(gpu, e, ns, s, A))
    rows = done + computed
    print(f"\nwall {time.time() - t0:.0f}s ({len(rows)} cells total)", flush=True)

    # ---- wide-band analysis over ALL cells ----
    rows = [r for r in rows if r.get("aa_matched") is not None]
    e1 = [r["etaL1"] for r in rows]; e2 = [r["etaL2"] for r in rows]
    aa = [r["aa_matched"] for r in rows]; epsv = [r["eps"] for r in rows]
    gaps = [r["rob_gap"] for r in rows]; dose = [1.0 if r["n_syn"] > 0 else 0.0 for r in rows]
    analysis = {}
    if len(rows) >= 2:
        analysis["etaL1_vs_AA_pearson"] = _pearson(e1, aa)
        analysis["etaL1_vs_AA_spearman"] = _spearman(e1, aa)
        analysis["etaL2_vs_AA_pearson"] = _pearson(e2, aa)
        # eps-relative (threat-normalized) certificate margin: how far the first-order radius clears eps
        e1_over_eps = [x / y for x, y in zip(e1, epsv)]
        analysis["etaL1_over_eps_vs_AA_pearson"] = _pearson(e1_over_eps, aa)
        analysis["etaL1_over_eps_vs_AA_spearman"] = _spearman(e1_over_eps, aa)
        analysis["etaL1_range"] = [float(min(e1)), float(max(e1))]
        analysis["etaL1_over_eps_range"] = [float(min(e1_over_eps)), float(max(e1_over_eps))]
        analysis["AA_range"] = [float(min(aa)), float(max(aa))]
        # OFFSET: regress AA on [1, etaL1, dose_dummy] and on [1, etaL1, eps, dose_dummy]
        def ols(cols, y):
            Xm = np.column_stack([np.ones(len(y))] + cols); yv = np.asarray(y, float)
            beta, *_ = np.linalg.lstsq(Xm, yv, rcond=None)
            resid = yv - Xm @ beta
            dof = max(len(y) - Xm.shape[1], 1)
            s2 = float(resid @ resid) / dof
            cov = s2 * np.linalg.pinv(Xm.T @ Xm)
            se = np.sqrt(np.clip(np.diag(cov), 0, None))
            t = beta / np.where(se > 0, se, np.nan)
            return beta.tolist(), se.tolist(), t.tolist()
        analysis["ols_AA_on_etaL1_dose"] = dict(zip(["beta", "se", "t"], ols([e1, dose], aa)),
                                                names=["const", "etaL1", "dose(+1M)"])
        analysis["ols_AA_on_etaL1_eps_dose"] = dict(zip(["beta", "se", "t"], ols([e1, epsv, dose], aa)),
                                                    names=["const", "etaL1", "eps", "dose(+1M)"])
        analysis["dose_vs_robgap_pearson"] = _pearson(dose, gaps)
        analysis["n_points"] = len(rows)

    os.makedirs(RESDIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    recipe = dict(arch=f"PreActResNet-18 ({args.arm}, width={args.width})", eps255_sweep=eps_list,
                  alpha_ratio=0.25, pgd_steps_train=PGD_STEPS, lr=LR, mom=MOM, wd=WD, sched="cosine",
                  aug="hflip", real_frac=args.real_frac, bs=args.bs, epochs=args.epochs, seeds=args.seeds,
                  early_stop="in-loop best val Linf-PGD robust acc @ training eps (val disjoint from report)",
                  threat_match="AutoAttack + PGD masking-check run at the SAME Linf eps the model trained on;"
                               " etaL1=margin/||grad M||_1 is the Linf-dual (threat-matched) ratio")
    fn = os.path.join(RESDIR, f"diff_pilot_s3_{args.tag}_{stamp}.json")
    json.dump(dict(args=vars(args), recipe=recipe, rows=rows, analysis=analysis), open(fn, "w"),
              indent=2, default=float)
    print(f"saved {fn}", flush=True)

    # ---- report ----
    print("\n==== S3 per-cell (best-early-stopped) ====", flush=True)
    hdr = (f"{'eps':>5} {'dose':>7} {'seed':>4} {'bep':>4} {'clean':>7} {'etaL1':>8} {'etaL2':>7} "
           f"{'AA@eps':>7} {'PGD@eps':>7} {'rr_L2':>6} {'robTr':>6} {'robTe':>6} {'gap':>7}")
    print(hdr); print("-" * len(hdr))
    for r in sorted(rows, key=lambda r: (r["eps255"], r["n_syn"], r["seed"])):
        dl = "0" if r["n_syn"] == 0 else ("1M" if r["n_syn"] >= 1_000_000 else f"{r['n_syn']//1000}k")
        print(f"{r['eps255']:>5g} {dl:>7} {r['seed']:>4} {r['best_ep']:>4} {r['clean']:>7.3f} "
              f"{r['etaL1']:>8.4f} {r['etaL2']:>7.3f} {r['aa_matched']:>7.3f} {r['pgd_matched']:>7.3f} "
              f"{r['rr_l2']:>6.3f} {r['rob_train']:>6.3f} {r['rob_test']:>6.3f} {r['rob_gap']:>+7.3f}")
    if analysis:
        print("\n==== WIDE-BAND law (all cells, threat-matched) ====")
        print(f"  etaL1 range: {analysis['etaL1_range']}   AA range: {analysis['AA_range']}   n={analysis['n_points']}")
        print(f"  etaL1  vs AA@eps : Pearson {analysis['etaL1_vs_AA_pearson']:+.3f}  "
              f"Spearman {analysis['etaL1_vs_AA_spearman']:+.3f}   (narrow-band ref: +0.85)")
        print(f"  etaL1/eps vs AA  : Pearson {analysis['etaL1_over_eps_vs_AA_pearson']:+.3f}  "
              f"Spearman {analysis['etaL1_over_eps_vs_AA_spearman']:+.3f}  (threat-normalized)")
        print(f"  etaL2  vs AA@eps : Pearson {analysis['etaL2_vs_AA_pearson']:+.3f}  (mismatched)")
        print("\n==== OFFSET (data intervention) ====")
        for key in ("ols_AA_on_etaL1_dose", "ols_AA_on_etaL1_eps_dose"):
            o = analysis[key]
            print(f"  {key}:")
            for nm, b, s, t in zip(o["names"], o["beta"], o["se"], o["t"]):
                print(f"    {nm:>12}: beta {b:+.4f}  se {s:.4f}  t {t:+.2f}")
        print(f"  dose(+1M) vs robust-gap Pearson: {analysis['dose_vs_robgap_pearson']:+.3f} "
              f"(more negative => +1M has smaller train-test gap)")


if __name__ == "__main__":
    main()
