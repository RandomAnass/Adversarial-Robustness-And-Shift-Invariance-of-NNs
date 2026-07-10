"""Attack-free clean-image diagnostics for a frozen tower + zero-shot head.

Definitions (verbatim from paper/report/main.tex sec:coupling / sec:exp):
  Signed logit margin:  M(x) = f_y(x) - max_{j != y} f_j(x)
  eta = E[M]   over correctly-classified clean images
  L_q = E|| grad_x M ||_q   with q the DUAL norm of the attack
        (q=1 for an Linf attack -> THREAT-MATCHED; q=2 for L2 -> mismatched control here)
  eta/L_q = threat-matched margin-to-Lipschitz ratio (the diagnostic).

Shift-consistency (paper eq): SC(f) = Pr_{x,s}[ argmax f(S_s x) == argmax f(x) ],
  S_s = integer circular pixel shift; we sweep a patch-grid phase set of offsets.
  Also report pooled-embedding cosine-consistency under the same shifts.

All computed on CLEAN images only; no attack is run for these.
"""
import torch
import torch.nn.functional as F


@torch.no_grad()
def predict(tower, images, bs=128, device="cuda"):
    preds, logits_max = [], []
    for i in range(0, len(images), bs):
        xb = images[i:i + bs].to(device)
        lg = tower(xb)
        preds.append(lg.argmax(1).cpu())
    return torch.cat(preds)


def margin_and_grad(tower, images, labels, q_list=(1, 2), bs=64, device="cuda",
                    correct_only=True):
    """Compute per-image signed margin M and ||grad_x M||_q for each q in q_list.

    Returns dict with per-image tensors: margin [K], gradnorm{q}: [K], correct mask,
    and the indices used. K = number of images (optionally restricted to correct).
    """
    tower.eval()
    all_M, all_g = [], {q: [] for q in q_list}
    all_correct, all_pred = [], []
    for i in range(0, len(images), bs):
        xb = images[i:i + bs].to(device).clone().requires_grad_(True)
        yb = labels[i:i + bs].to(device)
        logits = tower(xb)
        pred = logits.argmax(1)
        # signed margin: correct-class minus max over other classes
        true_logit = logits.gather(1, yb[:, None]).squeeze(1)
        masked = logits.clone()
        masked.scatter_(1, yb[:, None], float("-inf"))
        runner = masked.max(1).values
        M = true_logit - runner  # [B]
        # grad of sum(M) wrt input -> per-image grad (independent rows)
        grad = torch.autograd.grad(M.sum(), xb, create_graph=False)[0]  # [B,3,H,W]
        gflat = grad.reshape(grad.shape[0], -1)
        for q in q_list:
            gn = gflat.norm(p=q, dim=1)
            all_g[q].append(gn.detach().cpu())
        all_M.append(M.detach().cpu())
        all_correct.append((pred == yb).cpu())
        all_pred.append(pred.cpu())
    out = {
        "margin": torch.cat(all_M),
        "correct": torch.cat(all_correct),
        "pred": torch.cat(all_pred),
    }
    for q in q_list:
        out[f"gradnorm_l{q}"] = torch.cat(all_g[q])
    if correct_only:
        m = out["correct"]
        for k in list(out.keys()):
            if k != "correct":
                out[f"{k}_correctonly"] = out[k][m]
    return out


def eta_L_summary(diag, q_list=(1, 2)):
    """Aggregate per-image diagnostics into eta, L_q, eta/L_q over CORRECT images.

    eta = mean active margin over correctly-classified images (margin>0 by construction
    on correct images). L_q = mean ||grad M||_q over the same set.
    """
    mask = diag["correct"]
    M = diag["margin"][mask]
    eta = M.mean().item()
    res = {"eta": eta, "n_correct": int(mask.sum().item())}
    for q in q_list:
        Lq = diag[f"gradnorm_l{q}"][mask].mean().item()
        res[f"L{q}"] = Lq
        res[f"eta_over_L{q}"] = eta / Lq if Lq > 0 else float("nan")
    # per-image ratio (for per-image Spearman vs per-image robust radius)
    res["_per_image_correct_mask"] = mask
    for q in q_list:
        res[f"_per_image_ratio_L{q}"] = M / diag[f"gradnorm_l{q}"][mask].clamp_min(1e-12)
    res["_per_image_margin"] = M
    return res


def circular_shift(x, dy, dx):
    """Integer circular pixel shift of a [B,3,H,W] batch by (dy,dx)."""
    return torch.roll(x, shifts=(dy, dx), dims=(2, 3))


@torch.no_grad()
def shift_consistency(tower, images, labels, offsets, bs=128, device="cuda",
                      base_correct_mask=None):
    """SC = mean over images and shifts of 1[argmax f(S_s x) == argmax f(x)].

    Also pooled-embedding cosine-consistency: mean cos(emb(S_s x), emb(x)).
    Computed on the same correct-only subset when base_correct_mask is given
    (round2_C fix 5: SC on the same population as eta/L and S).

    offsets: list of (dy,dx) integer shifts (excluding (0,0)).
    Returns dict: sc_pred (label-agreement), sc_cos (embedding cosine).
    """
    tower.eval()
    if base_correct_mask is not None:
        idx = torch.where(base_correct_mask)[0]
        images = images[idx]
    N = len(images)
    # reference predictions and embeddings
    ref_pred = torch.empty(N, dtype=torch.long)
    has_encode = hasattr(tower, "encode")
    ref_emb = [] if has_encode else None
    for i in range(0, N, bs):
        xb = images[i:i + bs].to(device)
        ref_pred[i:i + bs] = tower(xb).argmax(1).cpu()
        if has_encode:
            ref_emb.append(F.normalize(tower.encode(xb), dim=-1).cpu())
    if has_encode:
        ref_emb = torch.cat(ref_emb)
    agree_sum = torch.zeros(N)
    cos_sum = torch.zeros(N)
    for (dy, dx) in offsets:
        for i in range(0, N, bs):
            xb = images[i:i + bs].to(device)
            xs = circular_shift(xb, dy, dx)
            ps = tower(xs).argmax(1).cpu()
            agree_sum[i:i + bs] += (ps == ref_pred[i:i + bs]).float()
            if has_encode:
                es = F.normalize(tower.encode(xs), dim=-1).cpu()
                cos_sum[i:i + bs] += (es * ref_emb[i:i + bs]).sum(1)
    n_off = len(offsets)
    sc_pred = (agree_sum / n_off).mean().item()
    sc_cos = (cos_sum / n_off).mean().item() if has_encode else float("nan")
    return {"sc_pred": sc_pred, "sc_cos": sc_cos,
            "sc_pred_per_image": (agree_sum / n_off),
            "n_images": N, "n_offsets": n_off}


def patch_grid_offsets(max_shift=8, step=1):
    """Patch-grid phase sweep offsets: (dy,dx) for dy,dx in +-1..+-max_shift on axes and
    a few diagonals, excluding (0,0). Integer circular shifts (paper's S_s)."""
    offs = []
    for d in range(step, max_shift + 1, step):
        offs += [(d, 0), (-d, 0), (0, d), (0, -d), (d, d), (-d, -d)]
    return offs
