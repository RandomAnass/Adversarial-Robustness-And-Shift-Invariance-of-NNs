"""Clearer concept figure: a real 224px ImageNet image, a real adversarial example, and real
shifts, using a torchvision ImageNet-pretrained ResNet-50. Sharp (224px) unlike 32px CIFAR.
Top row: clean (correct label) | perturbation | adversarial (flipped). Bottom: shift strip.
CPU. Out: concept_imagenet.pdf
"""
import os, sys, numpy as np, torch, torch.nn.functional as F
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/pilots/c1_tower")
import data
import torchvision.models as tvm
dev = "cpu"; torch.manual_seed(3)
# ImageNet-1k ResNet-50
weights = tvm.ResNet50_Weights.IMAGENET1K_V2
model = tvm.resnet50(weights=weights).to(dev).eval()
names = weights.meta["categories"]
mean = torch.tensor([0.485,0.456,0.406]).view(1,3,1,1); std = torch.tensor([0.229,0.224,0.225]).view(1,3,1,1)
def clf(x): return model((x-mean)/std)
# a few ImageNet-100 val images (224px, [0,1])
imgs, labels = data.load_val(n=40, seed=7,
    cache_path="/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower/in100val_cache_s7.pt")
with torch.no_grad():
    pred = clf(imgs).argmax(1)
# pick a visually clear, confidently-classified image
def short(n): return names[n].split(",")[0]
pick = 0
for i in range(len(imgs)):
    with torch.no_grad():
        p = torch.softmax(clf(imgs[i:i+1]),1)
    if p.max() > 0.85: pick = i; break
xi = imgs[pick:pick+1].clone()
with torch.no_grad(): y0 = clf(xi).argmax(1)
def pgd(x0, y0, eps, steps=40):
    a = 2.5*eps/steps; d = torch.zeros_like(x0).uniform_(-eps,eps)
    for _ in range(steps):
        d.requires_grad_(True)
        loss = F.cross_entropy(clf((x0+d).clamp(0,1)), y0)
        g = torch.autograd.grad(loss, d)[0]
        d = (d + a*g.sign()).clamp(-eps,eps); d = ((x0+d).clamp(0,1)-x0).detach()
    return d
adv_d, used = None, None
for e255 in [1,2,4,8]:
    d = pgd(xi, y0, e255/255., 40)
    with torch.no_grad(): p = clf((xi+d).clamp(0,1)).argmax(1).item()
    if p != y0.item(): adv_d, used, apred = d, e255, p; break
if adv_d is None: adv_d, used, apred = d, 8, p
clean = xi[0].permute(1,2,0).numpy()
adv = (xi+adv_d)[0].clamp(0,1).permute(1,2,0).numpy()
pert = np.clip(0.5 + 10*adv_d[0].permute(1,2,0).numpy(), 0, 1)
shifts = [(0,0),(20,0),(0,20),(28,28)]
simg, spred = [], []
for (sx,sy) in shifts:
    xs = torch.roll(xi, shifts=(sy,sx), dims=(2,3))
    with torch.no_grad(): spred.append(clf(xs).argmax(1).item())
    simg.append(xs[0].permute(1,2,0).numpy())
plt.rcParams.update({"font.size":10,"font.family":"serif","mathtext.fontset":"cm"})
CK, CX = r"$\checkmark$", r"$\times$"
def lab(ax,t,c,sub=None):
    ax.text(0.5,-0.07,t,transform=ax.transAxes,ha="center",va="top",color=c,fontsize=10)
    if sub: ax.text(0.5,-0.20,sub,transform=ax.transAxes,ha="center",va="top",color="#52606D",fontsize=8)
fig = plt.figure(figsize=(9.2,4.6))
gs = fig.add_gridspec(2,4,height_ratios=[1,1],hspace=0.75,wspace=0.10,top=0.87,bottom=0.05,left=0.03,right=0.99)
fig.text(0.5,0.955,"Adversarial robustness: a tiny worst-case change flips the label",ha="center",va="top",fontsize=12,weight="bold",color="#003359")
tax=[fig.add_subplot(gs[0,i]) for i in range(3)]
tax[0].imshow(clean); lab(tax[0],f"clean:  “{short(y0.item())}” "+CK,"#2F855A")
tax[1].imshow(pert);  lab(tax[1],f"perturbation ($\\times 10$)","#52606D")
tax[2].imshow(adv);   lab(tax[2],f"adversarial:  “{short(apred)}” "+CX,"#9B2C2C")
for a in tax: a.set_xticks([]); a.set_yticks([]); [s.set_visible(False) for s in a.spines.values()]
axr=fig.add_subplot(gs[0,3]); axr.axis("off")
axr.text(0.0,0.6,f"The two images differ by\nan $\\ell_\\infty$ change of\n${used}/255$, invisible to a\nhuman; the label flips.",fontsize=9.5,va="center",color="#1F2933")
fig.text(0.5,0.475,"Invariance: shifting the image keeps the label",ha="center",va="top",fontsize=12,weight="bold",color="#003359")
bax=[fig.add_subplot(gs[1,i]) for i in range(4)]
for i,(im,pr) in enumerate(zip(simg,spred)):
    bax[i].imshow(im); bax[i].set_xticks([]); bax[i].set_yticks([]); [s.set_visible(False) for s in bax[i].spines.values()]
    ok=(pr==y0.item())
    lab(bax[i],f"“{short(pr)}” "+(CK if ok else CX),("#2F855A" if ok else "#9B2C2C"),
        sub=("original" if i==0 else f"shift ({shifts[i][0]},{shifts[i][1]})"))
out="/home/students/code/Anas/adversarial-robustness-shift-invariance/paper/pitch/figures/concept_imagenet.pdf"
fig.savefig(out,bbox_inches="tight",dpi=150)
print("wrote",out,"| eps",used,"| clean",short(y0.item()),"| adv",short(apred))
print("shifts:",[short(p) for p in spred])
