"""
Counterexample check: a FIXED generic (non-aligned) H that depends only on sign structure.
At fixed M0, ||w||_1, sign(w), varying anisotropy A, the second-order radius depends on H only
through Q = 0.5 sign(w)^T H sign(w), which is CONSTANT across A (same sign pattern).
So the true radius should be ~constant in A => anisotropy does NOT predict the gap. FALSIFIES the
naked claim. Also test a random SPD-ish fixed H (not sign-structured) to see true radius spread.
"""
import numpy as np
rng = np.random.default_rng(1)

def inner_min(eps, M0, w, H, ns=60, it=400):
    d=w.shape[0]; best=np.inf; lr=eps*0.5
    cands=[-eps*np.sign(w)]+[rng.uniform(-eps,eps,d) for _ in range(ns)]+[eps*rng.choice([-1.,1.],d) for _ in range(ns//2)]
    for x0 in cands:
        x=np.clip(x0,-eps,eps).copy()
        for _ in range(it):
            g=w+H@x; x=np.clip(x-lr*g,-eps,eps)
        v=M0+w@x+0.5*x@(H@x)
        if v<best: best=v
    return best

def true_radius(M0,w,H,tol=1e-4):
    hi=8.0*M0/np.linalg.norm(w,1)
    for _ in range(60):
        if inner_min(hi,M0,w,H)<=0: break
        hi*=1.7
    lo=0.0
    while hi-lo>tol*max(1.,hi):
        mid=.5*(lo+hi)
        if inner_min(mid,M0,w,H)<=0: hi=mid
        else: lo=mid
    return .5*(lo+hi)

def make_w(d,A,l1,sign):
    idx=np.arange(1,d+1)
    Aof=lambda p:(idx.astype(float)**(-p)).sum()/np.sqrt(((idx.astype(float)**(-p))**2).sum())
    lo,hi=0.,40.
    for _ in range(200):
        m=.5*(lo+hi)
        if Aof(m)>A: lo=m
        else: hi=m
    p=.5*(lo+hi); mag=idx.astype(float)**(-p); mag=mag/mag.sum()*l1
    return mag*sign

d=30; M0=1.0; l1=4.0; R1=M0/l1
sign=rng.choice([-1.,1.],d)
A_grid=np.linspace(1.5,np.sqrt(d)*0.98,6)

print("CASE A: fixed random symmetric H (generic, NOT aligned to w), same across all A")
Hr=rng.standard_normal((d,d)); Hr=0.15*(Hr+Hr.T)/2   # indefinite generic curvature, fixed
rows=[]
for A in A_grid:
    w=make_w(d,A,l1,sign); Areal=np.linalg.norm(w,1)/np.linalg.norm(w,2)
    s=-np.sign(w); Q=0.5*s@(Hr@s)
    r=true_radius(M0,w,Hr); rows.append((Areal,r,Q))
print(f"  Q (sign-only, should be constant) = {rows[0][2]:.4f}")
for Areal,r,Q in rows: print(f"  A={Areal:6.3f}  r_true={r:.4f}  r/R1={r/R1:.4f}")
rr=[x[1] for x in rows]
print(f"  radius spread/R1 = {(max(rr)-min(rr))/R1:.4f}  (small => anisotropy does NOT drive gap)\n")

print("CASE B: same but the concave direction is FIXED (v), not aligned to w")
v=rng.standard_normal(d); v/=np.linalg.norm(v); Hv=-3.0*np.outer(v,v)
rows=[]
for A in A_grid:
    w=make_w(d,A,l1,sign); Areal=np.linalg.norm(w,1)/np.linalg.norm(w,2)
    r=true_radius(M0,w,Hv); rows.append((Areal,r))
for Areal,r in rows: print(f"  A={Areal:6.3f}  r_true={r:.4f}  r/R1={r/R1:.4f}")
rr=[x[1] for x in rows]
print(f"  radius spread/R1 = {(max(rr)-min(rr))/R1:.4f}  (fixed non-aligned curvature => weak A dependence)")
