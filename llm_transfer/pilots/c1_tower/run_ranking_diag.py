"""PART 2: what ranks robustness AMONG robust encoders, where eta/L (point-gradient) fails?

Theory (paper prop:sandwich): eta/L = margin / POINT dual-norm-gradient is only the LOWER arm of
eta/L <= r2 <= eta/alpha. The upper arm's alpha is path-tautological for trained nets (theory audit),
so instead we measure CERTIFIABLE ball quantities the point gradient cannot see:
  L_point = mean ||grad M(x)||_1                          (current eta/L denominator)
  L_ball  = mean over x of MAX over K random delta (||delta||_inf=eps) of ||grad M(x+delta)||_1
            (local Lipschitz UPPER estimate over the eps-ball -> a curvature-aware, larger L)
  curv    = mean ||grad M(x+delta) - grad M(x)||_1 / ||delta||_inf   (finite-diff Hessian norm; CURE-style)
Ratios: R_point = eta/L_point (fails to rank, +0.38); R_ball = eta/L_ball (curvature-aware).
Hypothesis: R_ball or curv orders AutoAttack robust accuracy AMONG the 10 robust encoders where
R_point does not. If the residual ranking is curvature, R_ball >> R_point in correlation with S_apgd.

Run: CUDA_VISIBLE_DEVICES=0 python run_ranking_diag.py
Out: results/c1_tower/ranking_diag.json + printed correlations among the 10 robust encoders.
"""
import os, json, torch, numpy as np
import data, towers
RES="/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower"
ROBUST=["fare2","fare4","tecoa2","tecoa4","fare4_b32","tecoa4_b32","fare4_b16","tecoa4_b16","fare4_cnxt","tecoa4_cnxt"]
EPS=2/255; K=4; N=120; device="cuda"


def margin(tower, x):
    logits=tower(x)
    y=logits.argmax(1)  # use predicted (all are correct on the subset)
    tl=logits.gather(1,y[:,None]).squeeze(1)
    m=logits.clone(); m.scatter_(1,y[:,None],float("-inf"))
    return tl-m.max(1).values


def grad_at(tower, x):
    x=x.clone().requires_grad_(True)
    M=margin(tower,x)
    g=torch.autograd.grad(M.sum(),x)[0]
    return M.detach(), g.detach()


def main():
    torch.manual_seed(0)
    cn=data.get_class_names()
    imgs,labels=data.load_val(n=2000,seed=0,cache_path=os.path.join(RES,"in100val_cache.pt"))
    cache={}
    for f in ["c1_results_main.json","c1_results_ext.json","c1_results_robustexp.json"]:
        for r in json.load(open(os.path.join(RES,f)))["results"]: cache[r["tower"]]=r
    rows=[]
    for name in ROBUST:
        tw=towers.load_clip_tower(name,cn,device)
        # correct subset
        with torch.no_grad():
            pred=torch.cat([tw(imgs[i:i+128].to(device)).argmax(1).cpu() for i in range(0,len(imgs),128)])
        ci=(pred==labels).nonzero(as_tuple=True)[0][:N]
        xs=imgs[ci]
        Lp,Lb,cv,eta=[],[],[],[]
        bs=16
        for i in range(0,len(xs),bs):
            xb=xs[i:i+bs].to(device)
            M0,g0=grad_at(tw,xb)
            gp=g0.reshape(g0.shape[0],-1).norm(p=1,dim=1)
            eta.append(M0.cpu()); Lp.append(gp.cpu())
            gmax=gp.clone(); cvacc=torch.zeros_like(gp)
            for _ in range(K):
                delta=torch.empty_like(xb).uniform_(-EPS,EPS)
                _,gd=grad_at(tw,(xb+delta).clamp(0,1))
                gdn=gd.reshape(gd.shape[0],-1).norm(p=1,dim=1)
                gmax=torch.maximum(gmax,gdn)
                cvacc=cvacc+((gd-g0).reshape(gd.shape[0],-1).norm(p=1,dim=1)/EPS)
            Lb.append(gmax.cpu()); cv.append((cvacc/K).cpu())
        eta=torch.cat(eta).mean().item(); Lp=torch.cat(Lp).mean().item()
        Lb=torch.cat(Lb).mean().item(); cv=torch.cat(cv).mean().item()
        c=cache.get(name,{})
        rows.append({"tower":name,"eta":eta,"L_point":Lp,"L_ball":Lb,"curv":cv,
                     "R_point":eta/Lp,"R_ball":eta/Lb,"kappa_ballpoint":Lb/Lp,
                     "S_apgd":c.get("S_apgd",{}).get("0.00784"),"clean":c.get("clean_acc")})
        print(f"{name:14s} eta={eta:.3f} L_pt={Lp:.0f} L_ball={Lb:.0f} kappa={Lb/Lp:.2f} "
              f"curv={cv:.0f} R_pt={eta/Lp:.5f} R_ball={eta/Lb:.5f} S={c.get('S_apgd',{}).get('0.00784')}",flush=True)
        del tw; torch.cuda.empty_cache()
    json.dump(rows,open(os.path.join(RES,"ranking_diag.json"),"w"),indent=2)

    from scipy import stats
    def col(k): return np.array([r[k] if r[k] is not None else np.nan for r in rows],float)
    S=col("S_apgd")
    def sp(x):
        m=np.isfinite(x)&np.isfinite(S); r,p=stats.spearmanr(x[m],S[m]); return round(float(r),3),round(float(p),4)
    print("\n=== RANKING among the 10 robust encoders: Spearman(quantity, AutoAttack robust acc) ===")
    print(f"  R_point = eta/L_point  : {sp(col('R_point'))}   [the one that FAILED: was +0.38]")
    print(f"  R_ball  = eta/L_ball   : {sp(col('R_ball'))}   [curvature-aware ratio]")
    print(f"  L_ball  (local Lip)    : {sp(col('L_ball'))}")
    print(f"  curv    (curvature)    : {sp(col('curv'))}")
    print(f"  kappa   = L_ball/L_pt  : {sp(col('kappa_ballpoint'))}")
    print(f"  eta     (margin)       : {sp(col('eta'))}")


if __name__=="__main__":
    main()
