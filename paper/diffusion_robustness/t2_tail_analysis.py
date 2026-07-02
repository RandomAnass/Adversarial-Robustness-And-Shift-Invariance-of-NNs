#!/usr/bin/env python3
"""
T2(i) + T1 shape-check: is the data-axis offset a TAIL effect, and is r1 a scale family?

From the 16 saved S3 best checkpoints (ckpts/s3eps_eps{E}_syn{N}_s{S}_best.pt), compute the per-sample
first-order Linf radius r1(x) = M(x)/||grad M(x)||_1 on the report split (test[1000:], matching the
harness's val/report split), n_pts points per model. Then:
  (1) certified fraction  CF(eps) = P(r1 >= training eps  &  correct)   [T1's population count]
  (2) OLS: AA ~ CF + dose  and  AA ~ mean-ratio/eps + dose  -- if the dose beta shrinks toward 0 under
      CF but not under the mean ratio, the +0.10 offset is a tail effect (T2 conjecture).
  (3) scale-family shape check: per-model r1 quantiles normalized by the model median; if shapes
      overlay across cells, r1 ~ mu * Z with model-independent Z (T1 scale-family conjecture).
CPU-only (keeps the one-GPU rule; GPU 1 is running S2). Progressive save to results/t2_tail.json.
Run: PYTHONNOUSERSITE=1 ../env/cenv/bin/python t2_tail_analysis.py
"""
import os, glob, json, re, time
import numpy as np, torch

HERE = os.path.dirname(os.path.abspath(__file__))
import diff_pilot_v2 as DV
CD, M = DV.CD, DV.M
OUT = os.path.join(HERE, "results", "t2_tail.json")
N_PTS, BS = 1500, 64
torch.set_num_threads(min(16, os.cpu_count() or 8))


def per_sample_r1(model, X, y, dev="cpu", n=N_PTS, bs=BS):
    """r1_i = M(x_i)/||grad M(x_i)||_1 with M = true - max other; also return correctness mask."""
    r1s, ok = [], []
    for i in range(0, min(n, len(X)), bs):
        xb = X[i:i + bs].clone().to(dev).requires_grad_(True); yb = y[i:i + bs].to(dev)
        logits = model(xb)
        true = logits.gather(1, yb[:, None]).squeeze(1)
        other = logits.clone().scatter_(1, yb[:, None], -1e9).max(1).values
        margin = true - other
        g, = torch.autograd.grad(margin.sum(), xb)
        l1 = g.flatten(1).abs().sum(1).detach()
        r1s.append((margin.detach() / l1.clamp_min(1e-12)).cpu())
        ok.append((margin.detach() > 0).cpu())
    return torch.cat(r1s).numpy(), torch.cat(ok).numpy()


def main():
    _, _, Xte, yte = CD.load_cifar(50000, 10000, seed=0)
    Xrep, yrep = Xte[1000:], yte[1000:]                      # report split (harness val_n=1000)
    cks = sorted(glob.glob(os.path.join(HERE, "ckpts", "s3eps_eps*_best.pt")))
    print(f"[t2] {len(cks)} checkpoints, {N_PTS} pts each, CPU", flush=True)
    res = json.load(open(OUT))["cells"] if os.path.exists(OUT) else {}
    for p in cks:
        key = os.path.basename(p)
        if key in res:
            continue
        mobj = re.search(r"eps([\d.]+)_syn(\d+)_s(\d+)", key)
        eps255, n_syn, seed = float(mobj.group(1)), int(mobj.group(2)), int(mobj.group(3))
        blob = torch.load(p, map_location="cpu")
        model = M.build(blob.get("arm", "stdzero"), width=blob.get("width", 1.0))
        model.load_state_dict(blob["state_dict"]); model.eval()
        t0 = time.time()
        r1, ok = per_sample_r1(model, Xrep, yrep)
        eps = eps255 / 255.0
        cf = float(np.mean((r1 >= eps) & ok))                       # certified fraction at training eps
        q = np.quantile(r1[ok], [0.05, 0.1, 0.25, 0.5, 0.75, 0.9]).tolist()
        res[key] = dict(eps255=eps255, n_syn=n_syn, seed=seed, cert_frac=cf,
                        r1_mean=float(r1[ok].mean()), r1_median=float(np.median(r1[ok])),
                        r1_q=q, acc=float(ok.mean()), n=int(len(r1)))
        json.dump(dict(cells=res), open(OUT + ".tmp", "w"), indent=1); os.replace(OUT + ".tmp", OUT)
        print(f"  {key}: CF={cf:.3f} median_r1={np.median(r1[ok]):.4f} ({time.time()-t0:.0f}s)", flush=True)

    # ---- analysis: join with the AA numbers from the s3 partials ----
    cells = []
    for p in glob.glob(os.path.join(HERE, "results/partial/s3eps_*.json")):
        d = json.load(open(p))
        key = f"s3eps_eps{d['eps255']:g}_syn{d['n_syn']}_s{d['seed']}_best.pt"
        if key in res:
            cells.append(dict(res[key], aa=d["aa_matched"], etaL1=d["etaL1"], eps=d["eps"]))
    if len(cells) < 8:
        print("not enough joined cells yet"); return
    aa = np.array([c["aa"] for c in cells]); cf = np.array([c["cert_frac"] for c in cells])
    dose = np.array([1.0 if c["n_syn"] > 0 else 0.0 for c in cells])
    mre = np.array([c["etaL1"] / c["eps"] for c in cells])

    def ols(cols, y):
        Xm = np.column_stack([np.ones(len(y))] + cols)
        beta, *_ = np.linalg.lstsq(Xm, y, rcond=None)
        resid = y - Xm @ beta
        s2 = float(resid @ resid) / max(len(y) - Xm.shape[1], 1)
        se = np.sqrt(np.clip(np.diag(s2 * np.linalg.pinv(Xm.T @ Xm)), 0, None))
        return beta, se, beta / np.where(se > 0, se, np.nan)

    print(f"\n==== T2: does the certified fraction absorb the dose offset? (n={len(cells)}) ====")
    for name, x in [("mean-ratio/eps", mre), ("certified fraction", cf)]:
        b, s, t = ols([x, dose], aa)
        print(f"  AA ~ {name} + dose:  {name} beta {b[1]:+.3f} (t {t[1]:+.1f})   "
              f"DOSE beta {b[2]:+.4f} (t {t[2]:+.2f})")
    print(f"  corr(CF, AA) = {np.corrcoef(cf, aa)[0,1]:+.3f}   corr(mean-ratio/eps, AA) = {np.corrcoef(mre, aa)[0,1]:+.3f}")

    print("\n==== T1: scale-family shape check (r1 quantiles / median) ====")
    print(f"{'cell':>26}  " + "  ".join(f"q{int(100*qq)}" for qq in (0.05, 0.1, 0.25, 0.5, 0.75, 0.9)))
    for c in sorted(cells, key=lambda c: (c["eps255"], c["n_syn"], c["seed"])):
        norm = [q / c["r1_median"] for q in c["r1_q"]]
        lab = f"eps{c['eps255']:g}_{'1M' if c['n_syn'] else '0'}_s{c['seed']}"
        print(f"{lab:>26}  " + "  ".join(f"{v:.2f}" for v in norm))
    print("(shape-invariance = rows approximately equal; heavier lower tail = smaller q5/q10 entries)")


if __name__ == "__main__":
    main()
