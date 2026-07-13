"""Stronger-angle hunt: the DOUBLE DISSOCIATION.
Does shift-invariance predict NUISANCE/CORRUPTION robustness (a continuous axis that varies across ALL
towers, unlike the bimodal adversarial axis) while the threat-matched margin eta/L predicts ADVERSARIAL
robustness? If so: invariance IS a kind of robustness (nuisance), just not the adversarial kind, which
explains why the field conflates them. Non-definitional (corruption acc is a separate measurement).

Per tower, measure clean acc and accuracy under mild common corruptions (Gaussian noise, Gaussian blur,
contrast down, brightness, large translation) -> nuisance robustness = mean corrupted acc. Then across
the 17-tower panel correlate {nuisance robustness, adversarial robustness S_apgd} with {shift-consistency,
eta/L}. Prediction: SC -> nuisance (+), eta/L -> adversarial (+), cross-terms weak = double dissociation.
Run: CUDA_VISIBLE_DEVICES=0 python run_nuisance.py
"""
import os, json, torch, numpy as np
import torch.nn.functional as F
import data, towers
import diagnostics as D

RES="/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower"
PANEL=["clip","clip_l14_laion2b","clip_l14_datacomp","clip_b16_openai","clip_b16_laion2b",
       "clip_b32_laion2b","fare2","fare4","tecoa2","tecoa4",
       "fare4_b32","tecoa4_b32","fare4_b16","tecoa4_b16","fare4_cnxt","tecoa4_cnxt"]
device="cuda"


def gaussian_blur(x, sigma=1.5, k=7):
    ax=torch.arange(k,device=x.device)-k//2
    g=torch.exp(-(ax**2)/(2*sigma**2)); g=(g/g.sum())
    ker=(g[:,None]*g[None,:])[None,None].repeat(x.shape[1],1,1,1)
    return F.conv2d(F.pad(x,(k//2,)*4,mode="reflect"),ker,groups=x.shape[1])


def corrupt(x, kind):
    if kind=="noise":   return (x+0.08*torch.randn_like(x)).clamp(0,1)
    if kind=="blur":    return gaussian_blur(x,1.5).clamp(0,1)
    if kind=="contrast":m=x.mean(dim=(2,3),keepdim=True); return ((x-m)*0.5+m).clamp(0,1)
    if kind=="bright":  return (x+0.25).clamp(0,1)
    if kind=="shift":   return torch.roll(x,shifts=(16,16),dims=(2,3))
    return x

CORR=["noise","blur","contrast","bright","shift"]


@torch.no_grad()
def acc_under(tower, imgs, labels, kind, bs=128):
    cor=0
    for i in range(0,len(imgs),bs):
        xb=imgs[i:i+bs].to(device); yb=labels[i:i+bs].to(device)
        xb=corrupt(xb,kind)
        pred=tower(xb).argmax(1)
        cor+=(pred==yb).sum().item()
    return cor/len(labels)


def main():
    torch.manual_seed(0)
    cn=data.get_class_names()
    imgs,labels=data.load_val(n=2000,seed=0,cache_path=os.path.join(RES,"in100val_cache.pt"))
    # adversarial + SC + eta/L from cached results
    cache={}
    for f in ["c1_results_main.json","c1_results_ext.json","c1_results_robustexp.json"]:
        for r in json.load(open(os.path.join(RES,f)))["results"]:
            cache[r["tower"]]=r
    rows=[]
    for name in PANEL:
        tw=towers.load_clip_tower(name,cn,device)
        clean=acc_under(tw,imgs,labels,"clean")
        cacc={k:acc_under(tw,imgs,labels,k) for k in CORR}
        nuis=float(np.mean(list(cacc.values())))
        c=cache.get(name,{})
        rows.append({"tower":name,"clean":clean,"nuisance":nuis,"corr":cacc,
                     "sc_pred":c.get("sc_pred"),"eta_over_L1":c.get("eta_over_L1"),
                     "S_apgd":c.get("S_apgd",{}).get("0.00784")})
        print(f"{name:16s} clean={clean:.3f} nuis={nuis:.3f} SC={c.get('sc_pred',0):.3f} "
              f"eta/L={c.get('eta_over_L1',0):.4f} S_adv={c.get('S_apgd',{}).get('0.00784')}",flush=True)
    json.dump(rows,open(os.path.join(RES,"nuisance.json"),"w"),indent=2)

    from scipy import stats
    def col(k): return np.array([r[k] if r[k] is not None else np.nan for r in rows],float)
    SC,eta,nuis,adv,clean=col("sc_pred"),col("eta_over_L1"),col("nuisance"),col("S_apgd"),col("clean")
    def sp(x,y):
        m=np.isfinite(x)&np.isfinite(y); r,p=stats.spearmanr(x[m],y[m]); return round(float(r),3),round(float(p),4)
    print("\n=== DOUBLE DISSOCIATION (n=%d towers) ==="%len(rows))
    print(f"  Spearman(shift-consistency, NUISANCE robustness) = {sp(SC,nuis)}   [expect + : invariance helps nuisance]")
    print(f"  Spearman(shift-consistency, ADVERSARIAL robust ) = {sp(SC,adv)}    [expect ~0 : the paper's null]")
    print(f"  Spearman(eta/L,            ADVERSARIAL robust  ) = {sp(eta,adv)}   [expect + : margin -> adversarial]")
    print(f"  Spearman(eta/L,            NUISANCE robustness ) = {sp(eta,nuis)}  [cross term]")
    print(f"  (control) Spearman(clean acc, NUISANCE) = {sp(clean,nuis)}  Spearman(clean, ADV) = {sp(clean,adv)}")
    # partial: SC->nuisance controlling clean acc (is it beyond just 'good clean model')?
    def pcorr(x,y,z):
        m=np.isfinite(x)&np.isfinite(y)&np.isfinite(z); x,y,z=x[m],y[m],z[m]
        rx,ry,rz=[stats.rankdata(a) for a in (x,y,z)]
        rxy,rxz,ryz=stats.pearsonr(rx,ry)[0],stats.pearsonr(rx,rz)[0],stats.pearsonr(ry,rz)[0]
        return round((rxy-rxz*ryz)/np.sqrt((1-rxz**2)*(1-ryz**2)),3)
    print(f"  partial Spearman(SC, nuisance | clean acc) = {pcorr(SC,nuis,clean)}")


if __name__=="__main__":
    main()
