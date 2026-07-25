"""Authentic figure for the deck's invariance-vs-robustness slide: a REAL adversarial
example and a REAL shift orbit on one CIFAR-10 image, using a downloaded RobustBench model.
Panel row: clean (correct label) | perturbation x8 | adversarial (flipped label, same eps)
Panel row: the shift orbit (circular shifts), all keeping the correct label.
Runs on CPU (one image, a few PGD steps). Out: concept_advshift.pdf
"""
import os, sys, numpy as np, torch, torch.nn.functional as F
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/pilots/c1_tower/robustbench_val")
import rb_common as RB
CLASSES = ["plane","car","bird","cat","deer","dog","frog","horse","ship","truck"]
dev = "cpu"
torch.manual_seed(0)
model = RB.load_model("Standard").to(dev).eval()   # standard-trained: small eps flips it, clean message
x, y = RB.load_data(n_examples=64)
x, y = x.to(dev), y.to(dev)
with torch.no_grad():
    pred = model(x).argmax(1)
ok = (pred == y).nonzero(as_tuple=True)[0]
# pick a visually clear image (ship/truck/horse) that is classified correctly
pick = None
for i in ok.tolist():
    if y[i].item() in (8, 9, 7, 0):  # ship, truck, horse, plane
        pick = i; break
pick = pick if pick is not None else ok[0].item()
xi = x[pick:pick+1].clone(); yi = y[pick:pick+1]

def pgd(x0, y0, eps, steps=40, alpha=None):
    alpha = alpha or 2.5 * eps / steps
    d = torch.zeros_like(x0).uniform_(-eps, eps)
    for _ in range(steps):
        d.requires_grad_(True)
        loss = F.cross_entropy(model((x0 + d).clamp(0, 1)), y0)
        g = torch.autograd.grad(loss, d)[0]
        d = (d + alpha * g.sign()).clamp(-eps, eps)
        d = (x0 + d).clamp(0, 1) - x0
        d = d.detach()
    return d

# find the smallest eps (in /255) that flips the label
adv_d, used_eps = None, None
for e255 in [1, 2, 4, 8, 12, 16]:
    d = pgd(xi, yi, e255 / 255.0, steps=50)
    with torch.no_grad():
        p = model((xi + d).clamp(0, 1)).argmax(1).item()
    if p != yi.item():
        adv_d, used_eps, adv_pred = d, e255, p; break
if adv_d is None:
    adv_d, used_eps, adv_pred = d, 16, p

clean_np = xi[0].permute(1, 2, 0).numpy()
adv_np = (xi + adv_d)[0].clamp(0, 1).permute(1, 2, 0).numpy()
pert = adv_d[0].permute(1, 2, 0).numpy()
pert_vis = np.clip(0.5 + 8 * pert, 0, 1)   # amplified x8 for visibility
# shift orbit (circular shifts), predicted labels
shifts = [(0, 0), (3, 0), (0, 3), (4, 4), (-3, 2)]
shift_imgs, shift_preds = [], []
for (sx, sy) in shifts:
    xs = torch.roll(xi, shifts=(sy, sx), dims=(2, 3))
    with torch.no_grad():
        shift_imgs.append(xs[0].permute(1, 2, 0).numpy())
        shift_preds.append(model(xs).argmax(1).item())

plt.rcParams.update({"font.size": 9, "font.family": "serif", "mathtext.fontset": "cm"})
CK, CX = r"$\checkmark$", r"$\times$"
def lab(ax, txt, color, sub=None):
    ax.text(0.5, -0.09, txt, transform=ax.transAxes, ha="center", va="top",
            color=color, fontsize=9)
    if sub: ax.text(0.5, -0.30, sub, transform=ax.transAxes, ha="center", va="top",
                    color="#52606D", fontsize=7.5)
fig = plt.figure(figsize=(8.4, 4.2))
gs = fig.add_gridspec(2, 5, height_ratios=[1, 1], hspace=0.75, wspace=0.12,
                      top=0.86, bottom=0.06, left=0.04, right=0.98)
fig.text(0.5, 0.955, "Adversarial robustness: a tiny worst-case change flips the label",
         ha="center", va="top", fontsize=11, weight="bold", color="#1F2933")
tax = [fig.add_subplot(gs[0, i]) for i in range(3)]
tax[0].imshow(clean_np); lab(tax[0], f"clean:  “{CLASSES[yi.item()]}” " + CK, "#2F855A")
tax[1].imshow(pert_vis); lab(tax[1], f"perturbation ($\\times 8$)", "#52606D")
tax[2].imshow(adv_np);   lab(tax[2], f"adversarial:  “{CLASSES[adv_pred]}” " + CX, "#9B2C2C")
for a in tax: a.set_xticks([]); a.set_yticks([]); [s.set_visible(False) for s in a.spines.values()]
axr = fig.add_subplot(gs[0, 3:]); axr.axis("off")
axr.text(0.02, 0.62, "The two images differ by an\n$\\ell_\\infty$ change of size "
         f"${used_eps}/255$,\nimperceptible to a human,\nyet the model's label flips.",
         fontsize=9, va="center", color="#1F2933")
fig.text(0.5, 0.475, "Invariance: shifting the image keeps the label", ha="center", va="top",
         fontsize=11, weight="bold", color="#1F2933")
bax = [fig.add_subplot(gs[1, i]) for i in range(5)]
for i, (im, pr) in enumerate(zip(shift_imgs, shift_preds)):
    bax[i].imshow(im); bax[i].set_xticks([]); bax[i].set_yticks([]); [s.set_visible(False) for s in bax[i].spines.values()]
    ok_lab = (pr == yi.item())
    head = "original" if i == 0 else f"shift ({shifts[i][0]},{shifts[i][1]})"
    lab(bax[i], f"“{CLASSES[pr]}” " + (CK if ok_lab else CX),
        ("#2F855A" if ok_lab else "#9B2C2C"), sub=head)
out = "/home/students/code/Anas/adversarial-robustness-shift-invariance/paper/pitch/figures/concept_advshift.pdf"
fig.savefig(out, bbox_inches="tight", dpi=150)
print("wrote", out, "| flip eps =", used_eps, "/255 | clean=", CLASSES[yi.item()], "adv=", CLASSES[adv_pred])
print("shift preds:", [CLASSES[p] for p in shift_preds])
