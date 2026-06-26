#!/usr/bin/env python3
"""
ResNet-scale Linf AutoAttack re-eval on the FULL test set (C1 integrity fix). Eval-only.

Why this exists. The cell runner reported the Linf AutoAttack robust accuracy from only the
first 512 test images: eval_cell (resnet_run.py) calls
    audit = masking_audit(model, Xte, yte, dev, n=min(n_aa, 512), ...)
    out["aa_Linf_8_255"] = audit["autoattack"]
so the n_aa=10000 bump never reached the Linf number. The L2 AutoAttack (aa_L2_0_5) was already
computed on all 10000 images; only the Linf reported quantities were capped.

What this does. For every AT cell with a saved checkpoint, it reloads the best-robust checkpoint
and recomputes, on the full 10000-image test set, the SAME quantities the cap shrank:
    aa_Linf_8_255  = AutoAttack(norm="Linf", eps=8/255, version="standard")   # the reported robust acc
    pgd_Linf_8_255 = PGD-20 (Linf, eps=8/255)                                  # the reported PGD acc
The original JSON is backed up to <cell>.json.bak512; the two fields are replaced in place; the
prior 512 values are kept as aa_Linf_8_255_n512 / pgd_Linf_8_255_n512 and provenance is stamped
(aa_Linf_n, aa_Linf_version). The 512-image masking-audit dict ("audit") is LEFT UNTOUCHED: it is
the gradient-masking diagnostic (it already passed for every cell), not a reported robust accuracy.
After this runs, aa_Linf_8_255 is a strictly larger-sample number; audit["autoattack"] stays the
512-subset diagnostic.

No retraining, no change to radii / margins / consistency / L2 numbers. Idempotent (skips cells
already at aa_Linf_n == 10000).

Usage (venv python + PYTHONNOUSERSITE=1, always):
  list:    PYTHONNOUSERSITE=1 paper/env/cenv/bin/python resnet_reeval_aa.py --list
  driver:  PYTHONNOUSERSITE=1 paper/env/cenv/bin/python resnet_reeval_aa.py --driver
  one:     PYTHONNOUSERSITE=1 paper/env/cenv/bin/python resnet_reeval_aa.py --cell c10at_aps_s0 --gpu 0
"""
import os, sys, json, time, argparse, shutil, subprocess, torch
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import build, nparams
from resnet_train import load_data, set_seed
from cifar_dissection import pgd_acc, autoattack_acc

RESDIR = os.path.join(os.path.dirname(__file__), "..", "..", "results", "resnet_scale")
CKPTDIR = os.path.join(RESDIR, "ckpt")
EPS = 8 / 255
N_FULL = 10000

def at_cells():
    """Every AT cell (mode=='at') that has both a results JSON and a checkpoint."""
    out = []
    for fn in sorted(os.listdir(RESDIR)):
        if not fn.endswith(".json") or fn.endswith("_curves.json"): continue
        name = fn[:-5]
        try: r = json.load(open(os.path.join(RESDIR, fn)))
        except Exception: continue
        if r.get("mode") == "at" and os.path.exists(os.path.join(CKPTDIR, name + ".pt")):
            out.append(name)
    return out

def _needs(name):
    try: return json.load(open(os.path.join(RESDIR, name + ".json"))).get("aa_Linf_n") != N_FULL
    except Exception: return True

def reeval_cell(name, gpu):
    import autoattack  # fail fast if the wrong interpreter is used (no autoattack / broken CUDA)
    assert torch.cuda.is_available(), "CUDA unavailable -- use the venv python with PYTHONNOUSERSITE=1"
    jpath = os.path.join(RESDIR, name + ".json"); r = json.load(open(jpath))
    assert r.get("mode") == "at", f"{name} is not an AT cell"
    if r.get("aa_Linf_n") == N_FULL:
        print(f"[{name}] already full-10k (aa_Linf_n={N_FULL}); skip", flush=True); return
    dev = f"cuda:{gpu}"; torch.cuda.set_device(gpu); t0 = time.time()
    cfg = r["config"]; set_seed(cfg["seed"])
    data = load_data(cfg["dataset"], seed=cfg["seed"]); Xte, yte = data["Xte"], data["yte"]
    assert len(Xte) >= N_FULL, f"{name}: test set only {len(Xte)} < {N_FULL}"
    model = build(cfg["arm"], width=cfg["width"], num_classes=data["n_classes"])
    sd = torch.load(os.path.join(CKPTDIR, name + ".pt"), map_location="cpu")["state"]  # {"state","epoch","metric"}
    model.load_state_dict(sd); model.to(dev).eval()
    assert nparams(model) == r.get("params", nparams(model)), f"{name}: param mismatch vs JSON (wrong arch)"
    # full-10k Linf robust accuracies, identical config to the (capped) originals: AA-standard + PGD-20
    aa = autoattack_acc(model, Xte, yte, dev, eps=EPS, norm="Linf", n=N_FULL, version="standard")
    pgd20 = pgd_acc(model, Xte[:N_FULL], yte[:N_FULL], dev, eps=EPS, norm="linf", steps=20)
    shutil.copy(jpath, jpath + ".bak512")                                  # audit trail: keep the 512 JSON
    r["aa_Linf_8_255_n512"] = r.get("aa_Linf_8_255"); r["pgd_Linf_8_255_n512"] = r.get("pgd_Linf_8_255")
    r["aa_Linf_8_255"] = float(aa); r["pgd_Linf_8_255"] = float(pgd20)
    r["aa_Linf_n"] = N_FULL; r["aa_Linf_version"] = "standard"; r["reeval_wall_s"] = time.time() - t0
    json.dump(r, open(jpath, "w"), indent=1, default=float)
    print(f"[{name}] DONE {(time.time()-t0)/60:.1f}min  "
          f"aa_Linf 512={r['aa_Linf_8_255_n512']:.4f} -> 10k={aa:.4f}   "
          f"pgd_Linf 512={r['pgd_Linf_8_255_n512']:.4f} -> 10k={pgd20:.4f}", flush=True)

def driver(ngpu=2, workers_per_gpu=2):
    """Run K=workers_per_gpu re-eval subprocesses PER GPU concurrently (eval-only + idempotent, so this
    only changes scheduling, never a cell's result). Slot = one concurrent subprocess pinned to a gpu."""
    cells = at_cells(); pending = [c for c in cells if _needs(c)]
    slots = [g for g in range(ngpu) for _ in range(max(1, workers_per_gpu))]   # gpu id per concurrent slot
    print(f"[driver] {len(pending)}/{len(cells)} AT cells need full-10k Linf re-eval on {ngpu} GPU(s) "
          f"x {workers_per_gpu} workers = {len(slots)} slots", flush=True)
    running = {}; free = list(slots); sid = [0]
    def launch(cell, gpu):
        env = dict(os.environ, PYTHONNOUSERSITE="1")
        logf = open(os.path.join(RESDIR, cell + ".reeval.log"), "a")
        p = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--cell", cell, "--gpu", str(gpu)],
                             stdout=logf, stderr=subprocess.STDOUT, env=env)
        running[sid[0]] = (cell, p, logf, gpu); sid[0] += 1
        print(f"[driver] launch {cell} gpu{gpu}", flush=True)
    while pending or running:
        while free and pending:
            launch(pending.pop(0), free.pop(0))
        time.sleep(15)
        for k, (cell, p, logf, gpu) in list(running.items()):
            if p.poll() is None: continue
            logf.close(); ok = not _needs(cell)
            print(f"[driver] {cell} {'done' if ok else 'FAILED'} rc={p.returncode}", flush=True)
            del running[k]; free.append(gpu)
    open(os.path.join(RESDIR, "REEVAL_AA_DONE.marker"), "w").write("done")
    print("[driver] all AT cells processed; wrote REEVAL_AA_DONE.marker", flush=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell"); ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--driver", action="store_true"); ap.add_argument("--ngpu", type=int, default=2)
    ap.add_argument("--workers_per_gpu", type=int, default=2)
    ap.add_argument("--list", action="store_true"); a = ap.parse_args()
    if a.list:
        cs = at_cells(); print("\n".join(f"{'NEEDS' if _needs(c) else ' ok  '} {c}" for c in cs))
        print(f"total {len(cs)} AT cells, {sum(_needs(c) for c in cs)} need re-eval")
    elif a.driver: driver(a.ngpu, a.workers_per_gpu)
    elif a.cell: reeval_cell(a.cell, a.gpu)
    else: ap.print_help()
