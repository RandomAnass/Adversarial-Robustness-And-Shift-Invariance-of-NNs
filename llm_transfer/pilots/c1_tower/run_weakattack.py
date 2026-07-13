"""Weak-attack-artifact experiment (promote the C1 bonus to a full section).

Novelty-verified (verify/weakattack_novelty.md): the COMPOSITE claim -- the invariance->robustness
CORRELATION itself is an FGSM artifact that vanishes under AutoAttack ON FROZEN VLM ENCODERS -- is
unoccupied; it must be framed as a targeted debunk of pro-invariance-no-AT claims (Wang et al.
2510.16171, FGSM/PGD-only, attributes robustness to gradient smoothing) using the Athalye-Carlini-
Wagner masking diagnostic. This script produces the two decisive figures:

  (1) PGD-k MONOTONICITY per tower: robust acc at k = 1(FGSM),2,5,10,20,40, then AutoAttack(APGD-CE+
      APGD-T) and Square(black-box). ACW signature: robust acc must decay monotonically with k and
      one-step (FGSM) must not beat iterative; Square >= APGD => no masking on the AT towers.
  (2) CORRELATION DECAY: Pearson/Spearman(shift-consistency, robust_acc_at_strength) ACROSS towers,
      as a function of attack strength. Claim: positive/large under FGSM, decays to ~null under
      AutoAttack -- the "invariance helps" correlation lives only under weak attacks.

Reuses towers.py / diagnostics.py / attacks.py and the cached in100val images. Encoder-level, one
GPU. Run when a GPU frees:  CUDA_VISIBLE_DEVICES=0 python run_weakattack.py
Out: results/c1_tower/weakattack.json  (+ prints the correlation-vs-strength table).
"""
import os, sys, json, time, argparse
import torch

import data, towers
import diagnostics as D
import attacks as A

RESULTS = "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower"
CACHE = os.path.join(RESULTS, "in100val_cache.pt")

# full 11-tower panel: 4 AT (contrast: should NOT collapse under AA) + 7 non-AT (the debunk targets)
FULL_PANEL = ["fare2", "fare4", "tecoa2", "tecoa4",
              "clip", "dinov2", "clip_l14_laion2b", "clip_l14_datacomp",
              "clip_b16_openai", "clip_b16_laion2b", "clip_b32_laion2b"]
AT_TOWERS = {"fare2", "fare4", "tecoa2", "tecoa4"}
PGD_KS = [1, 2, 5, 10, 20, 40]     # k=1 is FGSM (run separately), rest via PGD steps


def _load_cache(n_diag):
    class_names = data.get_class_names()
    imgs, labels = data.load_val(n=n_diag, seed=0, cache_path=CACHE)
    return imgs, labels, class_names


def run_tower(name, imgs, labels, class_names, args, device):
    t0 = time.time()
    tower = towers.load_clip_tower(name, class_names, device)
    pred = D.predict(tower, imgs, bs=args.bs, device=device)
    correct = (pred == labels)
    ci = correct.nonzero(as_tuple=True)[0][:args.n_attack]
    xi, yi = imgs[ci], labels[ci]
    # shift-consistency on the same correct subset
    offsets = D.patch_grid_offsets(max_shift=args.max_shift, step=1, compact=True)
    sc = D.shift_consistency(tower, imgs, labels, offsets, bs=args.bs, device=device,
                             base_correct_mask=correct, max_images=args.sc_max_images)
    res = {"tower": name, "is_AT": name in AT_TOWERS,
           "clean_acc": correct.float().mean().item(), "n_attack": int(len(yi)),
           "SC_pred": sc.get("sc_pred") if isinstance(sc, dict) else float(sc),
           "SC_cos": sc.get("sc_cos") if isinstance(sc, dict) else None,
           "robust_by_strength": {}}
    eps = args.eps
    R = res["robust_by_strength"]
    R["fgsm"] = A.run_fgsm_eval(tower, xi, yi, eps, bs=args.bs, device=device)
    for k in PGD_KS[1:]:
        R[f"pgd{k}"] = A.run_pgd_eval(tower, xi, yi, eps, steps=k, restarts=1,
                                      bs=args.bs, device=device)
    aa = A.run_autoattack(tower, xi, yi, eps, n_classes=len(class_names), bs=args.bs,
                          device=device, square=False, n_iter=args.apgd_iters)
    R["autoattack"] = aa["robust_acc"]
    try:
        sq = A.run_square_gap(tower, xi, yi, eps, bs=args.bs, device=device,
                              n_queries=args.square_queries)
        R["square"] = sq["robust_acc"] if isinstance(sq, dict) else float(sq)
    except Exception as e:
        R["square_error"] = str(e)[:80]
    print(f"[wa] {name:18s} AT={res['is_AT']} SC={res['SC_pred']:.3f} | "
          f"fgsm={R['fgsm']:.3f} pgd40={R.get('pgd40',float('nan')):.3f} AA={R['autoattack']:.3f}"
          f"  ({time.time()-t0:.0f}s)", flush=True)
    return res


def analyze(rows):
    import numpy as np
    from scipy import stats
    strengths = ["fgsm", "pgd2", "pgd5", "pgd10", "pgd20", "pgd40", "autoattack"]
    out = {"per_tower": rows, "correlation_vs_strength": {}}
    SC = np.array([r["SC_pred"] for r in rows])
    for s in strengths:
        ra = np.array([r["robust_by_strength"].get(s, np.nan) for r in rows])
        m = np.isfinite(SC) & np.isfinite(ra)
        if m.sum() >= 4 and np.std(ra[m]) > 1e-6:
            pr = float(stats.pearsonr(SC[m], ra[m])[0])
            sp = float(stats.spearmanr(SC[m], ra[m]).correlation)
        else:
            pr = sp = float("nan")  # no robust-acc variance (e.g. all 0 under AA) -> correlation undefined
        out["correlation_vs_strength"][s] = {"pearson_SC_robust": pr, "spearman_SC_robust": sp,
                                             "mean_robust": float(np.nanmean(ra)),
                                             "std_robust": float(np.nanstd(ra))}
    # non-AT-only view (the debunk subset)
    nonAT = [r for r in rows if not r["is_AT"]]
    out["correlation_vs_strength_nonAT"] = {}
    SCn = np.array([r["SC_pred"] for r in nonAT])
    for s in strengths:
        ra = np.array([r["robust_by_strength"].get(s, np.nan) for r in nonAT])
        m = np.isfinite(SCn) & np.isfinite(ra)
        pr = float(stats.pearsonr(SCn[m], ra[m])[0]) if m.sum() >= 4 and np.std(ra[m]) > 1e-6 else float("nan")
        out["correlation_vs_strength_nonAT"][s] = {"pearson_SC_robust": pr,
                                                   "mean_robust": float(np.nanmean(ra))}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--towers", nargs="+", default=FULL_PANEL)
    ap.add_argument("--eps", type=float, default=2/255)
    ap.add_argument("--n_attack", type=int, default=500)
    ap.add_argument("--bs", type=int, default=64)
    ap.add_argument("--max_shift", type=int, default=8)
    ap.add_argument("--sc_max_images", type=int, default=800)
    ap.add_argument("--apgd_iters", type=int, default=100)
    ap.add_argument("--square_queries", type=int, default=2000)
    ap.add_argument("--n_diag", type=int, default=2000)
    ap.add_argument("--out", default=os.path.join(RESULTS, "weakattack.json"))
    args = ap.parse_args()
    device = "cuda"
    imgs, labels, class_names = _load_cache(args.n_diag)
    print(f"[wa] cache: {len(labels)} imgs, {len(class_names)} classes; eps={args.eps:.5f} "
          f"({args.eps*255:.1f}/255); {len(args.towers)} towers", flush=True)
    rows = []
    for name in args.towers:
        try:
            rows.append(run_tower(name, imgs, labels, class_names, args, device))
        except Exception as e:
            print(f"[wa] {name} FAILED: {str(e)[:120]}", flush=True)
        torch.cuda.empty_cache()
    out = analyze(rows)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    print("\n=== CORRELATION(shift-consistency, robust acc) vs ATTACK STRENGTH (all towers) ===")
    for s, v in out["correlation_vs_strength"].items():
        print(f"  {s:11s}: Pearson={v['pearson_SC_robust']:+.3f}  mean_robust={v['mean_robust']:.3f}")
    print("  [claim: positive/large under FGSM, decays to ~null under AutoAttack]")
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
