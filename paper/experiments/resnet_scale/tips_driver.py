#!/usr/bin/env python3
"""
S1a TIPS head-to-head driver. GPU 0 ONLY (GPU 1 left free), strictly sequential, resumable.
Runs the `tips` arm through the EXISTING pipeline (resnet_run.run_cell = train+eval+save; then
resnet_reeval_aa.reeval_cell = full-10k Linf AutoAttack re-eval), in value-order so the head-to-head
verdict lands as early as possible:

  1. c10std_tips_s0        (fast std cell: validates end-to-end + trained clean/consistency)
  2. c10at_tips_s0         (w1.0 s0 PGD-AT -- headline scatter point A)
  3. c10at_tips_w0.5_s0    (w0.5 s0 PGD-AT -- headline scatter point B)
  4. c10std_tips_w0.5_s0   (fast std cell, second width, for the weak-attack regime)
  5. reeval c10at_tips_s0        -> full-10k Linf AA (match the other cells' reported number)
  6. reeval c10at_tips_w0.5_s0   -> full-10k Linf AA
  7. c10at_tips_s1 / s2 / w0.5_s1  (extra seeds for CIs)
  8. reeval those seed cells -> full-10k Linf AA

Each step skips if already complete (.done marker / aa_Linf_n==10000). Never proceeds on GPU 1.

Usage: PYTHONNOUSERSITE=1 paper/env/cenv/bin/python tips_driver.py --gpu 0
"""
import os, sys, json, time, argparse, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
RESDIR = os.path.join(HERE, "..", "..", "results", "resnet_scale")
PY = sys.executable

TRAIN = "train"; REEVAL = "reeval"; WEAK = "weak"
# (kind, cell) in execution order
TASKS = [
    (TRAIN,  "c10std_tips_s0"),
    (TRAIN,  "c10at_tips_s0"),
    (TRAIN,  "c10at_tips_w0.5_s0"),
    (TRAIN,  "c10std_tips_w0.5_s0"),
    (WEAK,   "1.0"),                     # FGSM/PGD-small-eps vs AutoAttack, std-trained arms, w1.0
    (WEAK,   "0.5"),
    (REEVAL, "c10at_tips_s0"),
    (REEVAL, "c10at_tips_w0.5_s0"),
    (TRAIN,  "c10at_tips_s1"),
    (TRAIN,  "c10at_tips_s2"),
    (TRAIN,  "c10at_tips_w0.5_s1"),
    (REEVAL, "c10at_tips_s1"),
    (REEVAL, "c10at_tips_s2"),
    (REEVAL, "c10at_tips_w0.5_s1"),
]

def train_done(cell):
    return os.path.exists(os.path.join(RESDIR, cell + ".done"))

def reeval_done(cell):
    try:
        return json.load(open(os.path.join(RESDIR, cell + ".json"))).get("aa_Linf_n") == 10000
    except Exception:
        return False

def weak_done(width):
    return os.path.exists(os.path.join(RESDIR, f"tips_weakattack_w{width}.json"))

def run(kind, cell, gpu):
    # Pin to the ONE physical GPU: mask everything else, then the child's --gpu 0 == physical `gpu`.
    env = dict(os.environ, PYTHONNOUSERSITE="1", CUDA_VISIBLE_DEVICES=str(gpu))
    if kind == TRAIN:
        if train_done(cell):
            print(f"[tips_driver] SKIP train {cell} (already .done)", flush=True); return True
        argv = [os.path.join(HERE, "resnet_run.py"), "--cell", cell, "--gpu", "0"]
        logf = os.path.join(RESDIR, cell + ".log")
    elif kind == WEAK:
        width = cell
        # weak-attack needs the tips std ckpt at this width; skip quietly if not trained yet.
        if not train_done(f"c10std_tips{'' if width=='1.0' else '_w'+width}_s0"):
            print(f"[tips_driver] WAIT weak w{width}: std tips ckpt not ready", flush=True); return False
        argv = [os.path.join(HERE, "tips_weakattack.py"), "--gpu", "0", "--width", width]
        logf = os.path.join(RESDIR, f"tips_weakattack_w{width}.log")
    else:  # REEVAL
        if not train_done(cell):
            print(f"[tips_driver] WAIT reeval {cell}: train not done yet, skipping for now", flush=True); return False
        if reeval_done(cell):
            print(f"[tips_driver] SKIP reeval {cell} (aa_Linf_n==10000)", flush=True); return True
        argv = [os.path.join(HERE, "resnet_reeval_aa.py"), "--cell", cell, "--gpu", "0"]
        logf = os.path.join(RESDIR, cell + ".reeval.log")
    t0 = time.time()
    print(f"[tips_driver] START {kind} {cell} gpu{gpu}  ({time.strftime('%H:%M:%S')})", flush=True)
    with open(logf, "a") as lf:
        p = subprocess.run([PY] + argv, stdout=lf, stderr=subprocess.STDOUT, env=env)
    ok = {TRAIN: train_done, REEVAL: reeval_done, WEAK: weak_done}[kind](cell)
    print(f"[tips_driver] END   {kind} {cell} rc={p.returncode} ok={ok} {(time.time()-t0)/60:.1f}min", flush=True)
    return ok

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--gpu", type=int, default=0); a = ap.parse_args()
    print(f"[tips_driver] starting on GPU {a.gpu} only; {len(TASKS)} tasks", flush=True)
    for kind, cell in TASKS:
        try:
            run(kind, cell, a.gpu)
        except Exception as e:
            print(f"[tips_driver] EXC {kind} {cell}: {e}", flush=True)
    open(os.path.join(RESDIR, "TIPS_DRIVER_DONE.marker"), "w").write("done " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print("[tips_driver] all tasks processed; wrote TIPS_DRIVER_DONE.marker", flush=True)

if __name__ == "__main__":
    main()
