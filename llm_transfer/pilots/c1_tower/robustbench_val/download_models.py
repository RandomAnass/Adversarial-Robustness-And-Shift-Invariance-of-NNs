"""Resilient background downloader for RobustBench CIFAR-10 Linf checkpoints.

Google Drive rate-limits per file ('Too many users ...'), and quotas reset over
minutes-to-hours. This loops over the candidate list repeatedly with backoff,
caching each successful checkpoint permanently at rb_models/cifar10/Linf/<name>.pt
(the path robustbench.load_model reuses). Writes a live status json.

Run:  python download_models.py   (intended for background / long run)
"""
import os, sys, time, json, traceback
import torch
import gdown
import robustbench.model_zoo.cifar10 as C

HERE = os.path.dirname(os.path.abspath(__file__))
CKPT_DIR = os.path.join(HERE, "rb_models", "cifar10", "Linf")
os.makedirs(CKPT_DIR, exist_ok=True)
STATUS = os.path.join(HERE, "download_status.json")

CANDIDATES = [
    "Standard", "Wong2020Fast", "Engstrom2019Robustness",
    "Andriushchenko2020Understanding", "Ding2020MMA", "Zhang2019Theoretically",
    "Sitawarin2020Improving", "Carmon2019Unlabeled", "Sehwag2020Hydra",
    "Wang2020Improving", "Hendrycks2019Using", "Rice2020Overfitting",
    "Wu2020Adversarial", "Sehwag2021Proxy_R18", "Rade2021Helper_R18_ddpm",
    "Rebuffi2021Fixing_R18_ddpm", "Addepalli2021Towards_RN18",
    "Addepalli2022Efficient_RN18", "Gowal2021Improving_R18_ddpm_100m",
    "Cui2020Learnable_34_10", "Zhang2020Attacks", "Zhang2020Geometry",
    "Huang2020Self", "Pang2020Boosting", "Chen2021LTD_WRN34_10",
    "Sehwag2021Proxy", "Gowal2020Uncovering_28_10_extra",
    "Rebuffi2021Fixing_28_10_cutmix_ddpm", "Addepalli2022Efficient_WRN_34_10",
    "Jia2022LAS-AT_34_10", "Dai2021Parameterizing",
    # --- second wave: additional single-part Linf models (fresh quotas) ---
    "Zhang2019You", "Wu2020Adversarial_extra", "Gowal2020Uncovering_70_16",
    "Gowal2020Uncovering_70_16_extra", "Gowal2020Uncovering_34_20",
    "Sehwag2021Proxy_ResNest152", "Chen2020Efficient", "Cui2020Learnable_34_20",
    "Rebuffi2021Fixing_106_16_cutmix_ddpm", "Rebuffi2021Fixing_70_16_cutmix_ddpm",
    "Rebuffi2021Fixing_70_16_cutmix_extra", "Sridhar2021Robust",
    "Sridhar2021Robust_34_15", "Rade2021Helper_R18_extra", "Rade2021Helper_extra",
    "Rade2021Helper_ddpm", "Huang2021Exploring", "Huang2021Exploring_ema",
    "Addepalli2021Towards_WRN34", "Gowal2021Improving_70_16_ddpm_100m",
    "Gowal2021Improving_28_10_ddpm_100m", "Chen2021LTD_WRN34_20",
    "Jia2022LAS-AT_70_16", "Pang2022Robustness_WRN28_10",
    "Pang2022Robustness_WRN70_16",
]


def ckpt_path(name):
    return os.path.join(CKPT_DIR, f"{name}.pt")


def is_valid(path):
    if not os.path.exists(path) or os.path.getsize(path) < 100_000:
        return False
    with open(path, "rb") as f:
        if f.read(1) == b"<":  # html error page
            return False
    # try to actually torch.load it
    try:
        torch.load(path, map_location="cpu", weights_only=False)
        return True
    except Exception:
        return False


def try_download(name):
    gid = C.linf[name].get("gdrive_id")
    if isinstance(gid, list):
        return False, "multipart (skipped)"
    out = ckpt_path(name)
    tmp = out + ".part"
    try:
        gdown.download(id=gid, output=tmp, quiet=True)
    except Exception as e:
        if os.path.exists(tmp):
            os.remove(tmp)
        return False, repr(e).split("\n")[0][:120]
    # validate then atomically move
    if is_valid(tmp):
        os.replace(tmp, out)
        return True, "ok size=%d" % os.path.getsize(out)
    else:
        if os.path.exists(tmp):
            os.remove(tmp)
        return False, "invalid file (html/corrupt)"


def write_status(state):
    with open(STATUS, "w") as f:
        json.dump(state, f, indent=2)


def main(max_hours=6.0, spacing=60.0):
    """Gentle policy: shuffle each round, wide spacing between gdrive hits so we
    don't trip Google's per-IP abuse throttle. One attempt per file per round."""
    import random
    t_start = time.time()
    state = {"done": [], "pending": list(CANDIDATES), "last_error": {},
             "round": 0, "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    # pick up any already-valid checkpoints (resume)
    for n in list(state["pending"]):
        if is_valid(ckpt_path(n)):
            state["done"].append(n)
            state["pending"].remove(n)
    write_status(state)

    # Block-aware policy: each round we PROBE a small batch of files. If the whole
    # probe fails with quota, we are IP-blocked -> sleep a long time before the
    # next probe (do NOT keep hitting gdrive, which keeps the block warm). When a
    # probe succeeds, we opportunistically try the rest of pending at 'spacing'.
    PROBE = 4          # files to probe per round when blocked
    BLOCK_SLEEP = 1200 # 20 min quiet period after an all-fail probe
    while state["pending"] and (time.time() - t_start) < max_hours * 3600:
        state["round"] += 1
        order = list(state["pending"])
        random.shuffle(order)
        probe = order[:PROBE]
        any_ok = False
        for n in probe:
            if n not in state["pending"]:
                continue
            ok, msg = try_download(n)
            ts = time.strftime("%H:%M:%S")
            if ok:
                print(f"[{ts}] DONE  {n}: {msg}", flush=True)
                state["done"].append(n); state["pending"].remove(n)
                any_ok = True
            else:
                state["last_error"][n] = msg
                print(f"[{ts}] probe {n}: {msg[:60]}", flush=True)
            write_status(state)
            time.sleep(spacing)
        if any_ok:
            # block seems lifted: sweep the rest of pending this round
            for n in order[PROBE:]:
                if n not in state["pending"]:
                    continue
                ok, msg = try_download(n)
                ts = time.strftime("%H:%M:%S")
                if ok:
                    print(f"[{ts}] DONE  {n}: {msg}", flush=True)
                    state["done"].append(n); state["pending"].remove(n)
                else:
                    state["last_error"][n] = msg
                    print(f"[{ts}] wait  {n}: {msg[:60]}", flush=True)
                write_status(state)
                if state["pending"]:
                    time.sleep(spacing)
            print(f"--- round {state['round']} SWEEP done={len(state['done'])} "
                  f"pending={len(state['pending'])} ---", flush=True)
        else:
            print(f"--- round {state['round']} BLOCKED (probe all-fail) "
                  f"done={len(state['done'])} pending={len(state['pending'])} "
                  f"sleeping {BLOCK_SLEEP}s ---", flush=True)
            time.sleep(BLOCK_SLEEP)
    state["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    write_status(state)
    print("DOWNLOADER FINISHED. done=%d pending=%d" %
          (len(state["done"]), len(state["pending"])), flush=True)


if __name__ == "__main__":
    hrs = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
    main(max_hours=hrs)
