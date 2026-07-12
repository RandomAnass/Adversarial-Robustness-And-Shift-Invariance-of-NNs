"""Re-run per-image robust radius on a FINER sub-1/255 grid for the ORIGINAL panel towers,
so the non-robust towers (clip, dinov2) are not floored at the old 1/255 grid bottom. This
lets the per-image Spearman(eta/L1, radius) be measured with genuine radius range where possible.

Writes per_image_<tower>_finegrid.pt with radius + ratio_l1 aligned. GPU 1 only.
"""
import os, sys, time, argparse
import torch
sys.path.insert(0, os.path.dirname(__file__))
import data, towers, diagnostics as D, attacks as A

RESULTS = "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower"
CACHE = os.path.join(RESULTS, "in100val_cache.pt")
DINO_HEAD = os.path.join(RESULTS, "dinov2_head.pt")


def build(name, cn, dev):
    if name == "dinov2":
        bb = towers.load_dinov2_backbone(dev)
        h = torch.load(DINO_HEAD, map_location=dev)
        t = towers.LinearProbeZeroShot(bb, h["head_w"].to(dev), h["head_b"].to(dev),
                                       towers.IN_MEAN, towers.IN_STD).to(dev).eval()
        for p in t.parameters():
            p.requires_grad_(False)
        return t
    return towers.load_clip_tower(name, cn, dev)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--towers", nargs="+", default=["clip", "dinov2"])
    ap.add_argument("--n_diag", type=int, default=2000)
    ap.add_argument("--n_img", type=int, default=300)
    ap.add_argument("--grid", type=float, nargs="+",
                    default=[0.125/255, 0.25/255, 0.5/255, 1/255, 2/255, 3/255, 4/255])
    ap.add_argument("--steps", type=int, default=25)
    args = ap.parse_args()
    dev = "cuda"
    cn = data.get_class_names()
    imgs, labels = data.load_val(n=args.n_diag, seed=0, cache_path=CACHE)
    for name in args.towers:
        t0 = time.time()
        tower = build(name, cn, dev)
        pred = D.predict(tower, imgs, bs=128, device=dev)
        correct = (pred == labels)
        diag = D.margin_and_grad(tower, imgs, labels, q_list=(1, 2), bs=48, device=dev)
        summ = D.eta_L_summary(diag, q_list=(1, 2))
        ci = torch.where(correct)[0][:args.n_img]
        rad, flipped = A.per_image_robust_radius_linf(
            tower, imgs[ci], labels[ci], args.grid, steps=args.steps, bs=64, device=dev)
        corr_idx = torch.where(diag["correct"])[0]
        pos = {int(v): k for k, v in enumerate(corr_idx.tolist())}
        sel = torch.tensor([pos[int(j)] for j in ci.tolist()])
        out = {"radius_idx": ci.cpu(), "robust_radius_linf": rad.cpu(),
               "flipped": flipped.cpu(), "ratio_l1": summ["_per_image_ratio_L1"][sel].cpu(),
               "ratio_l2": summ["_per_image_ratio_L2"][sel].cpu(),
               "margin": summ["_per_image_margin"][sel].cpu()}
        torch.save(out, os.path.join(RESULTS, f"per_image_{name}_finegrid.pt"))
        uniq = torch.unique(rad)
        print(f"{name}: n={len(rad)} radius_uniq={len(uniq)} "
              f"floor_frac={(rad==rad.min()).float().mean():.2f} "
              f"({time.time()-t0:.0f}s)", flush=True)
        del tower
        torch.cuda.empty_cache()
    print("DONE-FINEGRID", flush=True)


if __name__ == "__main__":
    main()
