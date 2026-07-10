"""Fit a linear-probe head for the DINOv2 ViT-L/14 tower on ImageNet-100 train features.

DINOv2 has no CLIP text space, so it enters the panel as a non-AT high-invariance widener
via a linear probe (standard DINOv2 evaluation protocol). We fit a logistic-regression head
on frozen pooled features from a subset of ImageNet-100 train, at COMMON_RES=224 in [0,1].
Head weights saved to results/c1_tower/dinov2_head.pt.
"""
import os
import torch
import torch.nn.functional as F

import towers

TRAIN_PT = "/home/students/code/Anas/adversarial-robustness-shift-invariance/paper/data/imagenet100/cache/train.pt"
OUT = "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower/dinov2_head.pt"
RES = towers.COMMON_RES


@torch.no_grad()
def extract_features(backbone, X_uint8, mean, std, device, bs=128, per_class=None, y=None):
    """Resize 160->224, /255, normalize, pool features. Optionally class-balanced subsample."""
    if per_class is not None and y is not None:
        idx = []
        for c in range(int(y.max()) + 1):
            ci = torch.where(y == c)[0]
            g = torch.Generator().manual_seed(c)
            ci = ci[torch.randperm(len(ci), generator=g)[:per_class]]
            idx.append(ci)
        idx = torch.cat(idx)
        X_uint8 = X_uint8[idx]
        y = y[idx]
    norm = towers.Normalizer(mean, std).to(device)
    feats = []
    for i in range(0, len(X_uint8), bs):
        xb = X_uint8[i:i + bs].to(device).float() / 255.0
        xb = F.interpolate(xb, size=RES, mode="bicubic", align_corners=False).clamp(0, 1)
        f = backbone(norm(xb))
        feats.append(f.cpu())
    return torch.cat(feats), y


def main(per_class=200, epochs=60, lr=1.0, wd=1e-4, device="cuda"):
    d = torch.load(TRAIN_PT, map_location="cpu")
    X, y = d["X"], d["y"]
    backbone = towers.load_dinov2_backbone(device)
    feats, ys = extract_features(backbone, X, towers.IN_MEAN, towers.IN_STD, device,
                                 per_class=per_class, y=y)
    feats = feats.to(device)
    ys = ys.to(device)
    dfeat = feats.shape[1]
    ncls = int(ys.max()) + 1
    # standardize features for a well-conditioned linear probe
    mu = feats.mean(0, keepdim=True)
    sd = feats.std(0, keepdim=True) + 1e-6
    feats_n = (feats - mu) / sd
    W = torch.zeros(ncls, dfeat, device=device, requires_grad=True)
    b = torch.zeros(ncls, device=device, requires_grad=True)
    opt = torch.optim.LBFGS([W, b], lr=lr, max_iter=epochs, line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad()
        logits = F.linear(feats_n, W, b)
        loss = F.cross_entropy(logits, ys) + wd * (W.pow(2).sum())
        loss.backward()
        return loss

    opt.step(closure)
    with torch.no_grad():
        acc = (F.linear(feats_n, W, b).argmax(1) == ys).float().mean().item()
    print(f"DINOv2 linear-probe train acc ({per_class}/class): {acc:.3f}, dfeat={dfeat}")
    # fold the feature-standardization into the head so it acts on raw pooled features:
    # logits = ((f - mu)/sd) W^T + b = f (W/sd)^T + (b - (mu/sd) W^T)
    Weff = (W / sd)  # [ncls, dfeat]
    beff = b - (mu / sd) @ W.t()  # [1,ncls] -> [ncls]
    beff = beff.squeeze(0)
    torch.save({"head_w": Weff.detach().cpu(), "head_b": beff.detach().cpu(),
                "train_acc": acc}, OUT)
    print("saved head to", OUT)


if __name__ == "__main__":
    main()
