"""Reviewer-requested per-image FLOOR control (R1/R2/R3): is the within-encoder per-image
eta/L1-vs-radius Spearman (+0.74..0.96) genuine fine ordering, or is it driven by fragile images whose
robust radius sits at the grid floor (near zero)? For each ROBUST encoder we recompute the per-image
Spearman(ratio_l1, robust_radius_linf) after excluding floor images (radius at the smallest grid value),
and report the floor fraction and the pooled result. No GPU."""
import glob, os
import numpy as np, torch
from scipy import stats

R = "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower"
NONROBUST = {"clip", "clip_b16_openai", "clip_b32_laion2b", "clip_l14_laion2b"}

def tower_name(f):
    return os.path.basename(f).replace("per_image_crownjewelH_", "").replace(".pt", "")

files = sorted(glob.glob(os.path.join(R, "per_image_crownjewelH_*.pt")))
robust = [f for f in files if tower_name(f) not in NONROBUST]
print(f"robust encoders: {len(robust)}")

pooled_full_x, pooled_full_y = [], []
pooled_nf_x, pooled_nf_y = [], []
print(f"\n{'encoder':22s} {'n':>4} {'floor%':>7} {'rho_full':>9} {'rho_noFloor':>12} {'n_noFloor':>10}")
for f in robust:
    d = torch.load(f, map_location="cpu", weights_only=False)
    r = np.asarray(d["robust_radius_linf"], float)
    x = np.asarray(d["ratio_l1"], float)
    m = np.isfinite(r) & np.isfinite(x)
    r, x = r[m], x[m]
    floor = r.min()                      # smallest grid value = fragile/floor
    is_floor = r <= floor + 1e-9
    nf = ~is_floor
    rho_full = stats.spearmanr(x, r).correlation
    rho_nf = stats.spearmanr(x[nf], r[nf]).correlation if nf.sum() >= 5 else float("nan")
    print(f"{tower_name(f):22s} {len(r):4d} {100*is_floor.mean():6.1f}% {rho_full:+9.3f} {rho_nf:+12.3f} {int(nf.sum()):10d}")
    pooled_full_x += list(x); pooled_full_y += list(r)
    pooled_nf_x += list(x[nf]); pooled_nf_y += list(r[nf])

pf = stats.spearmanr(pooled_full_x, pooled_full_y).correlation
pn = stats.spearmanr(pooled_nf_x, pooled_nf_y).correlation
floor_frac = 1 - len(pooled_nf_x)/len(pooled_full_x)
print(f"\n== POOLED over robust encoders ==")
print(f"  full:        rho = {pf:+.3f}  (n={len(pooled_full_x)})")
print(f"  floor {100*floor_frac:.1f}% of images at min radius")
print(f"  no-floor:    rho = {pn:+.3f}  (n={len(pooled_nf_x)})")
print(f"  => {'SURVIVES' if pn > 0.5 else 'WEAKENS'}: excluding fragile floor images, the per-image ordering {'holds' if pn>0.5 else 'drops'}.")
