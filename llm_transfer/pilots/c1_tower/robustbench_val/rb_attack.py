"""Linf robust accuracy via APGD-CE (autoattack), eps=8/255, on given images.

We use the standard APGD cross-entropy attack. Robust accuracy is computed only
on the subset passed in (typically the correctly-classified images). A single
APGD-CE run at ~75-100 iters is a strong (not full-AA) lower-effort proxy that
still ranks models well; we use 100 iters + 1 restart.
"""
import torch
from autoattack.autopgd_base import APGDAttack


def apgd_robust_correct(model, x, y, eps=8/255, n_iter=100, bs=128,
                        device="cuda", seed=0):
    """Return boolean tensor [N]: True where the image survives APGD-CE.

    model: callable logits, input in [0,1] (includes its own normalization).
    x,y already assumed to be images the model classifies correctly clean.
    """
    model.eval()
    apgd = APGDAttack(model, n_iter=n_iter, norm="Linf", n_restarts=1,
                      eps=eps, seed=seed, loss="ce", eot_iter=1, rho=0.75,
                      verbose=False, device=device)
    survived = torch.zeros(x.shape[0], dtype=torch.bool)
    for i in range(0, x.shape[0], bs):
        xb = x[i:i+bs].to(device)
        yb = y[i:i+bs].to(device)
        x_adv = apgd.perturb(xb, yb)
        with torch.no_grad():
            pred = model(x_adv).argmax(1)
        survived[i:i+bs] = (pred == yb).cpu()
    return survived
