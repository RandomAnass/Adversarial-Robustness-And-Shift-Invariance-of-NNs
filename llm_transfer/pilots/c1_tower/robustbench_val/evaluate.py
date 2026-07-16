"""Evaluate each available RobustBench Linf model:
  clean acc (on N test images), anisotropy A, eta/L_1, and Linf robust acc
  (APGD-CE, eps=8/255) on ~n_correct correctly-classified images.

Resumable: per-model results cached in results.json. Only evaluates models whose
checkpoint already exists and validates. Safe to re-run while the downloader adds
more checkpoints.
"""
import os, sys, json, time, argparse
import torch

import rb_common as RC
from rb_attack import apgd_robust_correct

HERE = os.path.dirname(os.path.abspath(__file__))
CKPT_DIR = os.path.join(HERE, "rb_models", "cifar10", "Linf")
RESULTS = os.path.join(HERE, "results.json")


def available_models():
    if not os.path.isdir(CKPT_DIR):
        return []
    out = []
    for fn in sorted(os.listdir(CKPT_DIR)):
        if fn.endswith(".pt") and not fn.endswith(".part"):
            out.append(fn[:-3])
    return out


def load_results():
    if os.path.exists(RESULTS):
        with open(RESULTS) as f:
            return json.load(f)
    return {}


def save_results(r):
    tmp = RESULTS + ".tmp"
    with open(tmp, "w") as f:
        json.dump(r, f, indent=2)
    os.replace(tmp, RESULTS)


def evaluate_model(name, x, y, n_correct=500, eps=8/255, n_iter=100,
                   device="cuda"):
    t0 = time.time()
    model = RC.load_model(name).to(device).eval()
    # clean predictions on all provided images
    pred = RC.predict(model, x.to(device)).cpu()
    correct_mask = (pred == y)
    clean_acc = float(correct_mask.float().mean())
    xc = x[correct_mask][:n_correct]
    yc = y[correct_mask][:n_correct]

    stats = RC.compute_anisotropy_and_eta(model, xc, yc, device=device)

    surv = apgd_robust_correct(model, xc, yc, eps=eps, n_iter=n_iter,
                               bs=128, device=device)
    # robust acc among the correctly-classified subset that we attacked
    robust_acc_on_correct = float(surv.float().mean())
    # robust acc over the full N test set:
    #   images misclassified clean are already 'broken'; among the n_correct we
    #   attacked, surv survive. Extrapolate the survival rate over ALL correct
    #   images to get standard robust accuracy = clean_acc * survival_rate.
    robust_acc = clean_acc * robust_acc_on_correct

    res = {
        "name": name,
        "clean_acc": clean_acc,
        "robust_acc": robust_acc,
        "robust_acc_on_correct": robust_acc_on_correct,
        "n_correct_attacked": int(xc.shape[0]),
        "n_total_eval": int(x.shape[0]),
        "eps": eps, "apgd_iters": n_iter,
        "A": stats["A"], "A_std": stats["A_std"],
        "eta_over_L1": stats["eta_over_L1"],
        "mean_margin": stats["mean_margin"], "mean_l1": stats["mean_l1"],
        "sqrt_d": stats["sqrt_d"],
        "eval_time_s": round(time.time() - t0, 1),
    }
    del model
    torch.cuda.empty_cache()
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_eval", type=int, default=1000,
                    help="test images to load / compute clean acc on")
    ap.add_argument("--n_correct", type=int, default=500,
                    help="correctly-classified images to attack & measure A on")
    ap.add_argument("--n_iter", type=int, default=100)
    ap.add_argument("--force", action="store_true",
                    help="re-evaluate even if already in results.json")
    args = ap.parse_args()

    device = "cuda"
    x, y = RC.load_data(n_examples=args.n_eval)
    print(f"loaded {x.shape[0]} test images", flush=True)

    results = load_results()
    models = available_models()
    print(f"{len(models)} checkpoints available: {models}", flush=True)

    for name in models:
        if (name in results) and (not args.force):
            print(f"skip (cached) {name}: robust={results[name]['robust_acc']:.3f} "
                  f"A={results[name]['A']:.3f}", flush=True)
            continue
        try:
            res = evaluate_model(name, x, y, n_correct=args.n_correct,
                                 n_iter=args.n_iter, device=device)
            results[name] = res
            save_results(results)
            print(f"OK {name}: clean={res['clean_acc']:.3f} "
                  f"robust={res['robust_acc']:.3f} A={res['A']:.3f} "
                  f"eta/L1={res['eta_over_L1']:.4f} ({res['eval_time_s']}s)",
                  flush=True)
        except Exception as e:
            import traceback
            print(f"FAIL {name}: {repr(e)[:160]}", flush=True)
            traceback.print_exc()
            torch.cuda.empty_cache()

    print(f"\nEvaluated {len(results)} models total.", flush=True)


if __name__ == "__main__":
    main()
