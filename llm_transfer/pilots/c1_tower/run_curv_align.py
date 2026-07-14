"""MECHANISM TEST for the anisotropy result: is the margin curvature CONCAVE and ALIGNED with the
gradient along the L∞-ATTACK direction (the condition under which anisotropy proxies robustness)?

Fixes the flaw in run_ranking_diag (random delta). Here we measure curvature along the ATTACK
direction s = sign(grad M) via finite difference (low memory, no double-backward):
  Q_align(x) = s^T ( grad M(x + h*s) - grad M(x) ) / h      (curvature of M along the attack ray)
  normalized: q = Q_align / ||grad M(x)||_1                  (dimensionless looseness rate)
Theory (verified synthetically): under aligned concave curvature Q<0 and r_inf falls below eta/L1 by
~ -Q; more negative q => more looseness => (at fixed eta/L) less robust. Predictions to test across
the 10 robust encoders: (1) mean q < 0 (concave along attack); (2) Spearman(q, S_apgd) > 0 (less
concave => more robust); (3) Spearman(anisotropy A, q) < 0 (higher A => more negative q, the A^2 law).
Run: CUDA_VISIBLE_DEVICES=1 python run_curv_align.py    Out: results/c1_tower/curv_align.json
"""
import os, sys, json, argparse, torch, numpy as np
import data, towers
RES="/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower"
ROBUST=["fare2","fare4","tecoa2","tecoa4","fare4_b32","tecoa4_b32","fare4_b16","tecoa4_b16","fare4_cnxt","tecoa4_cnxt"]
EPS=2/255; N=120; device="cuda"
OUTJL=os.path.join(RES,"curv_align.jsonl")


def grad_at(tw,x):
    x=x.clone().requires_grad_(True)
    lg=tw(x); y=lg.argmax(1)
    tl=lg.gather(1,y[:,None]).squeeze(1); m=lg.clone(); m.scatter_(1,y[:,None],float("-inf"))
    M=tl-m.max(1).values
    g=torch.autograd.grad(M.sum(),x)[0]
    return M.detach(), g.detach()


def analyze():
    from scipy import stats
    rows=[json.loads(l) for l in open(OUTJL)]
    q=np.array([r["q_align"] for r in rows]); A=np.array([r["anisotropy"] for r in rows]); S=np.array([r["S_apgd"] for r in rows])
    print(f"\n=== MECHANISM TEST ({len(rows)} robust encoders) ===")
    for r in sorted(rows,key=lambda r:r['S_apgd']):
        print(f"  {r['tower']:14s} q_align={r['q_align']:+.2f} anisotropy={r['anisotropy']:.1f} S={r['S_apgd']:.3f}")
    print(f"  mean q_align = {q.mean():+.2f}   frac concave (q<0) = {(q<0).mean():.2f}   (theory wants concave)")
    print(f"  Spearman(q_align, S_apgd)       = {stats.spearmanr(q,S)}   (theory: >0, less concave => more robust)")
    print(f"  Spearman(anisotropy A, q_align) = {stats.spearmanr(A,q)}   (theory: <0, higher A => more concave)")


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--tower",default=None); ap.add_argument("--analyze",action="store_true")
    args=ap.parse_args()
    if args.analyze: analyze(); return
    torch.manual_seed(0)
    cn=data.get_class_names(); imgs,labels=data.load_val(n=2000,seed=0,cache_path=os.path.join(RES,"in100val_cache.pt"))
    cache={}
    for f in ["c1_results_main.json","c1_results_ext.json","c1_results_robustexp.json"]:
        for r in json.load(open(os.path.join(RES,f)))["results"]: cache[r["tower"]]=r
    todo=[args.tower] if args.tower else ROBUST
    for name in todo:
        tw=towers.load_clip_tower(name,cn,device)
        with torch.no_grad():
            pred=torch.cat([tw(imgs[i:i+128].to(device)).argmax(1).cpu() for i in range(0,len(imgs),128)])
        ci=(pred==labels).nonzero(as_tuple=True)[0][:N]; xs=imgs[ci]
        h=EPS  # step along the attack ray, size of the L-inf budget
        qs,l1s,anis=[],[],[]
        bs=16
        for i in range(0,len(xs),bs):
            xb=xs[i:i+bs].to(device)
            M0,g0=grad_at(tw,xb)
            s=g0.sign()
            _,g1=grad_at(tw,(xb+h*s).clamp(0,1))
            gd=(g1-g0).reshape(g0.shape[0],-1)
            Q=(s.reshape(s.shape[0],-1)*gd).sum(1)/h                      # s^T H s (curvature along attack)
            g0f=g0.reshape(g0.shape[0],-1)
            l1=g0f.norm(p=1,dim=1); l2=g0f.norm(p=2,dim=1)
            qs.append((Q/l1.clamp_min(1e-9)).cpu()); l1s.append(l1.cpu()); anis.append((l1/l2.clamp_min(1e-9)).cpu())
        q=torch.cat(qs).mean().item(); A=torch.cat(anis).mean().item()
        c=cache.get(name,{})
        row={"tower":name,"q_align":q,"anisotropy":A,"S_apgd":c.get("S_apgd",{}).get("0.00784")}
        with open(OUTJL,"a") as f: f.write(json.dumps(row)+"\n")
        print(f"{name:14s} q_align={q:+.4f} anisotropy={A:.1f} S={c.get('S_apgd',{}).get('0.00784')}",flush=True)
        del tw; torch.cuda.empty_cache()


if __name__=="__main__":
    main()
