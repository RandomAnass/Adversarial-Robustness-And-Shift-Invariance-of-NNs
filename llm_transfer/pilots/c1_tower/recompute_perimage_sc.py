"""Recompute per-image shift-consistency for the 6 new robust towers (the ext run didn't save it),
align to the cached per-image radius, and report the per-image dissociation across all robust towers."""
import os, sys, torch, numpy as np
from scipy import stats
import data, towers
import diagnostics as D
RES="/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower"
NEW=["fare4_b32","tecoa4_b32","fare4_b16","tecoa4_b16","fare4_cnxt","tecoa4_cnxt"]
device="cuda"
class_names=data.get_class_names()
imgs,labels=data.load_val(n=2000,seed=0,cache_path=os.path.join(RES,"in100val_cache.pt"))
offs=D.patch_grid_offsets(max_shift=8,step=1,compact=True)
for name in NEW:
    tw=towers.load_clip_tower(name,class_names,device)
    pred=D.predict(tw,imgs,bs=64,device=device); correct=(pred==labels)
    sc=D.shift_consistency(tw,imgs,labels,offs,bs=64,device=device,base_correct_mask=correct,max_images=None)
    scpi=sc["sc_pred_per_image"].numpy()  # aligned to correct-set order
    pf=torch.load(os.path.join(RES,f"per_image_{name}_ext.pt"),map_location="cpu")
    rad=pf["robust_radius_linf"].numpy(); r1=pf["ratio_l1"].numpy()
    n=min(len(rad),len(scpi)); scn=scpi[:n]; radn=rad[:n]; r1n=r1[:n]
    # save sc into the per_image file for reuse
    pf["sc_pred_per_image"]=torch.tensor(scn); torch.save(pf,os.path.join(RES,f"per_image_{name}_ext.pt"))
    re=stats.spearmanr(r1n,radn).correlation; rs=stats.spearmanr(scn,radn).correlation
    rng=np.random.default_rng(0)
    diffs=[stats.spearmanr(r1n[i],radn[i]).correlation-stats.spearmanr(scn[i],radn[i]).correlation
           for i in (rng.integers(0,n,n) for _ in range(1500))]
    dl,dh=np.nanpercentile(diffs,[2.5,97.5])
    print(f"{name:14s} n={n} eta/L={re:+.3f} SC={rs:+.3f} diff={re-rs:+.3f} [{dl:+.2f},{dh:+.2f}] {'SIG' if dl>0 else 'ns'}",flush=True)
