#!/usr/bin/env python3
"""
A1-opt: standard-train the TIPS arm WITH TIPS's own auxiliary losses (Saha & Gokhale WACV 2025).

Steelman flank being tested: our S1a head-to-head trained the TIPS arm with the shared CE recipe
only (the OPERATOR, aux losses deliberately omitted -- see models.py TIPS docstring). A defender
could argue TIPS only delivers its robustness/invariance benefits WITH its training losses. This
script closes that flank: same arm, same std recipe (STD_SCHED, mirroring resnet_train.train_cell
mode='std' exactly), plus TIPS's auxiliary objective wired in per external/tips/train_test.py:

    loss = (1-alpha) * CE + alpha * (1/num_down) * sum_i MSE(psi_x_i, x_t_i)      [their eq.]

  * psi_x_i = ReLU(conv1(x)) inside each TIPS module (captured by forward hooks; our port already
    returns it as output[1], see models.py TIPS.forward).
  * x_t_i   = randomly shifted copy of the TIPS module INPUT (their feat_transform defaults:
    'standard' zero-fill shift, |shift| <= 2 per axis, random amount+direction), DETACHED.
    NOTE their code writes `x_t.detach()` without assignment (a no-op), so their literal code
    leaves x_t attached; their comment says "### Freeze". Default = detached (their stated
    intent); --literal_nodetach replicates their literal code instead.
  * grouping: per downsampling BLOCK, main+shortcut TIPS pairs concatenated before the MSE
    (upstream resnet.py concatenates psi_x1/psi_x2, x_t1/x_t2); num_down = 3 here
    (layer2/3/4 block-1), vs 5 in their resnet50 config.
  * alpha = 0.35 (their default); aux is OFF before epoch `--wake` (their wake_up_at /
    t_epsilon gate; their tiny-imagenet recipe wakes at 100/480 epochs ~ 21%, scaled here to
    17/80 by default).
  * loss_reg (Index_Regularize on tau) is identically ZERO in their own downstream config
    (return_soft_polyphase_indices=False), so it is not wired.
  * their trainer also clips grad-norm to 1.0; OUR std cells do not clip, so default is off
    to keep the single-difference comparison (aux loss only); --clip 1.0 matches them exactly.

Training mirrors resnet_train.train_cell(mode='std') line-for-line otherwise (SGD 0.1/0.9/5e-4,
bs 128, MultiStepLR(40,60), max 80 epochs, early stop on val-clean, patience 15, bf16 autocast,
crop+flip aug, best-val checkpoint). Eval mirrors tips_weakattack.py (clean, shift-consistency,
FGSM / PGD-10 at {1,2,4,8}/255 on n=1000, AutoAttack standard at {2,4,8}/255 on n=512) so the
result drops straight into the weak-vs-strong-attack comparison.

Writes: results/resnet_scale/c10stdaux_tips{_wW}_s{S}.json (+ _curves.json, ckpt, .done).

Usage (GPU): PYTHONNOUSERSITE=1 paper/env/cenv/bin/python tips_aux_train.py --gpu 0
CPU smoke:   CUDA_VISIBLE_DEVICES="" PYTHONNOUSERSITE=1 paper/env/cenv/bin/python tips_aux_train.py --smoke
"""
import os, sys, json, time, argparse, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from models import build, nparams, TIPS
from resnet_train import load_data, set_seed, _loader, _acc, env_stamp

RESDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "results", "resnet_scale")
CKPTDIR = os.path.join(RESDIR, "ckpt")

# ---- their feat_transform, 'standard' type, defaults (tips.py feat_transform.forward) ----
def rand_shift_standard(feat, max_h=2, max_w=2):
    sh = np.random.randint(-max_h, max_h + 1)
    sw = np.random.randint(-max_w, max_w + 1)
    f = torch.roll(feat, shifts=sh, dims=-2)
    if sh > 0:   f[:, :, :sh, :] = 0
    elif sh < 0: f[:, :, sh:, :] = 0
    f = torch.roll(f, shifts=sw, dims=-1)
    if sw > 0:   f[:, :, :, :sw] = 0
    elif sw < 0: f[:, :, :, sw:] = 0
    return f

class AuxCapture:
    """Forward hooks on every TIPS module: capture (psi_x, x_t) keyed by parent block.
    `enabled` gates the capture -- MUST be False outside training forwards (eval / attacks do
    many forwards; capturing there would leak memory by keeping autograd graphs alive)."""
    def __init__(self, model, detach_xt=True):
        self.store = {}                     # block_name -> list[(psi_x, x_t)]
        self.detach_xt = detach_xt
        self.enabled = True
        self.blocks = []
        for name, mod in model.named_modules():
            if isinstance(mod, TIPS):
                block = name.rsplit(".", 1)[0]          # e.g. 'layer2.0'
                if block not in self.blocks:
                    self.blocks.append(block)
                mod.register_forward_hook(self._hook(block))
        assert self.blocks, "no TIPS modules found -- is this the tips arm?"
    def _hook(self, block):
        def fn(mod, inputs, output):
            if not self.enabled:
                return
            x_in = inputs[0]
            psi_x = output[1]                            # models.py TIPS returns (out, psi_x, None)
            x_t = rand_shift_standard(x_in.detach() if self.detach_xt else x_in)
            self.store.setdefault(block, []).append((psi_x, x_t))
        return fn
    def clear(self):
        self.store = {}
    def aux_losses(self):
        """their per-down-layer MSE over the concatenated (main, shortcut) pair."""
        out = []
        for b in self.blocks:
            pairs = self.store.get(b, [])
            psi = torch.cat([p for p, _ in pairs], dim=1)
            xt = torch.cat([t for _, t in pairs], dim=1)
            out.append(F.mse_loss(psi, xt))
        return out                                       # len == num_down (3)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--width", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--alpha", type=float, default=0.35, help="their aux mixing weight")
    ap.add_argument("--wake", type=int, default=17, help="their wake_up_at (t_epsilon), scaled 100/480 -> 17/80")
    ap.add_argument("--clip", type=float, default=0.0, help="grad-norm clip; 0=off (ours), 1.0=theirs")
    ap.add_argument("--literal_nodetach", action="store_true",
                    help="replicate their literal no-op x_t.detach() (x_t stays in the graph)")
    ap.add_argument("--epochs", type=int, default=80)          # STD_SCHED
    ap.add_argument("--smoke", action="store_true", help="CPU plumbing test: 200 imgs, 2 epochs, no AA")
    a = ap.parse_args()

    milestones, patience = (40, 60), 15                        # STD_SCHED
    tag_w = "" if a.width == 1.0 else f"_w{a.width}"
    name = f"c10stdaux_tips{tag_w}_s{a.seed}" + ("_smoke" if a.smoke else "")
    done = os.path.join(RESDIR, name + ".done")
    if os.path.exists(done):
        print(f"[{name}] already done, skipping", flush=True); return
    os.makedirs(CKPTDIR, exist_ok=True)

    if a.smoke:
        dev = "cpu"; a.epochs = 2; a.wake = 1                  # epoch0 pre-wake, epoch1 aux on
    else:
        assert torch.cuda.is_available(), "CUDA unavailable -- use cenv python with PYTHONNOUSERSITE=1"
        dev = f"cuda:{a.gpu}"; torch.cuda.set_device(a.gpu)
    use_amp = dev != "cpu"

    t0 = time.time(); set_seed(a.seed)
    data = load_data("cifar10", seed=a.seed)
    if a.smoke:
        data["Xtr"], data["ytr"] = data["Xtr"][:200], data["ytr"][:200]
        data["Xval"], data["yval"] = data["Xval"][:100], data["yval"][:100]
    model = build("tips", width=a.width, num_classes=10).to(dev)
    cap = AuxCapture(model, detach_xt=not a.literal_nodetach)
    num_down = len(cap.blocks)
    print(f"[{name}] {nparams(model)} params, TIPS blocks: {cap.blocks} (num_down={num_down}), "
          f"alpha={a.alpha} wake={a.wake} clip={a.clip} detach={not a.literal_nodetach}", flush=True)

    # ---- training loop: train_cell(mode='std') + their aux objective ----
    opt = torch.optim.SGD(model.parameters(), lr=0.1, momentum=0.9, weight_decay=5e-4)
    sched = torch.optim.lr_scheduler.MultiStepLR(opt, milestones=list(milestones), gamma=0.1)
    loader = _loader(data["Xtr"], data["ytr"], 128, a.seed, shift_aug=False)
    ckpt = os.path.join(CKPTDIR, name + ".pt")
    curves = []; best_metric = -1.0; best_state = None; best_epoch = -1; bad = 0
    min_epochs = min(milestones[0] + patience, a.epochs)
    for ep in range(a.epochs):
        model.train(); nseen = 0; tl = tcls = taux = 0.0
        awake = ep >= a.wake
        for xb, yb in loader:
            xb, yb = xb.to(dev, non_blocking=True), yb.to(dev, non_blocking=True)
            opt.zero_grad(); cap.clear()
            ctx = torch.autocast("cuda", dtype=torch.bfloat16) if use_amp else _null()
            with ctx:
                logits = model(xb)
                loss_cls = F.cross_entropy(logits, yb)
                aux = cap.aux_losses()
                # their combination (train_test.py L456-464): pre-wake the aux weights are zeroed
                aux_w = (1.0 / num_down) if awake else 0.0
                loss = (1 - a.alpha) * loss_cls + a.alpha * aux_w * torch.stack(aux).sum()
            loss.backward()
            if a.clip > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), a.clip, norm_type=2.0)
            opt.step()
            n = len(yb); nseen += n; tl += loss.item() * n; tcls += loss_cls.item() * n
            taux += float(np.mean([x.item() for x in aux])) * n
        sched.step(); cap.clear(); cap.enabled = False       # no capture during val/eval forwards
        vca = _acc(model, data["Xval"], data["yval"], dev)
        cap.enabled = True
        rec = {"epoch": ep, "lr": opt.param_groups[0]["lr"], "train_loss": tl / nseen,
               "cls_loss": tcls / nseen, "aux_mse_mean": taux / nseen, "awake": awake, "val_clean": vca}
        curves.append(rec)
        print(f"[{name}] ep{ep} loss{rec['train_loss']:.3f} cls{rec['cls_loss']:.3f} "
              f"aux{rec['aux_mse_mean']:.4f}{'*' if awake else ' '} vc{vca:.3f}", flush=True)
        if vca > best_metric + 1e-4:
            best_metric, best_epoch, bad = vca, ep, 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            torch.save({"state": best_state, "epoch": ep, "metric": vca}, ckpt)
        else:
            bad += 1
        if ep + 1 >= min_epochs and bad >= patience:
            break

    # ---- eval: mirror tips_weakattack.py so the result is directly comparable ----
    model.load_state_dict(best_state); model.to(dev).eval()
    cap.enabled = False; cap.clear()                          # hooks off for all attack forwards
    from cifar_dissection import pgd_acc, autoattack_acc, accuracy, shift_consistency
    from tips_weakattack import fgsm_acc
    Xte, yte = data["Xte"], data["yte"]
    if a.smoke:
        Xte, yte = Xte[:200], yte[:200]
    res = {"clean": accuracy(model, Xte, yte, dev), "consist": shift_consistency(model, Xte, dev)}
    n_pt, n_aa = (100, 0) if a.smoke else (1000, 512)
    for eps in (1/255, 2/255, 4/255, 8/255):
        k = f"{round(eps*255)}"
        res[f"fgsm_{k}"] = fgsm_acc(model, Xte[:n_pt], yte[:n_pt], dev, eps)
        res[f"pgd_{k}"] = pgd_acc(model, Xte[:n_pt], yte[:n_pt], dev, eps, "linf", steps=10)
        if n_aa and eps >= 2/255:
            res[f"aa_{k}"] = autoattack_acc(model, Xte, yte, dev, eps=eps, norm="Linf", n=n_aa, version="standard")
        print(f"[{name}] eps{k}/255 fgsm={res[f'fgsm_{k}']:.3f} pgd={res[f'pgd_{k}']:.3f} "
              f"aa={res.get(f'aa_{k}', float('nan')):.3f}", flush=True)

    res.update(arm="tips+aux", w=a.width, seed=a.seed, mode="stdaux", params=nparams(model),
               best_epoch=best_epoch, n_epochs_run=len(curves), wall_s=time.time() - t0,
               config=dict(alpha=a.alpha, wake=a.wake, clip=a.clip, num_down=num_down,
                           detach_xt=not a.literal_nodetach, epochs=a.epochs,
                           milestones=list(milestones), patience=patience, smoke=a.smoke),
               env=env_stamp(), n=n_pt, n_aa=n_aa, pgd_steps=10)
    json.dump(res, open(os.path.join(RESDIR, name + ".json"), "w"), indent=1, default=float)
    json.dump(curves, open(os.path.join(RESDIR, name + "_curves.json"), "w"))
    open(done, "w").write(f"{time.time()-t0:.0f}s best_ep={best_epoch}")
    print(f"[{name}] DONE {res['wall_s']/60:.1f}min clean={res['clean']:.3f} "
          f"consist={res['consist']:.3f}", flush=True)

class _null:
    def __enter__(self): return None
    def __exit__(self, *args): return False

if __name__ == "__main__":
    main()
