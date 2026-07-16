"""Real-data figure for the pitch deck / paper: gradient anisotropy A ranks adversarial
robustness among the 30 official RobustBench CIFAR-10 Linf models. A = ||grad M||_1/||grad M||_2.
Panel (a): A vs robust acc (the ranking law). Panel (b): eta/L1 vs robust acc (the DETECTION
control that saturates among the robust models). Data: robustbench_val/results.json."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "../../../llm_transfer/pilots/c1_tower/robustbench_val/results.json")
d = json.load(open(RES))
rows = list(d.values())
name = np.array([r["name"] for r in rows])
A = np.array([r["A"] for r in rows])
rob = np.array([r["robust_acc"] for r in rows]) * 100
clean = np.array([r["clean_acc"] for r in rows]) * 100
etaL = np.array([r["eta_over_L1"] for r in rows])

# separate the single non-robust "Standard" model (rob=0) from the robust panel
is_std = rob < 1.0
rb = ~is_std  # robust panel (the ranking regime)

sA = stats.spearmanr(A[rb], rob[rb])
sE = stats.spearmanr(etaL[rb], rob[rb])

plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "font.family": "serif"})
fig, ax = plt.subplots(1, 2, figsize=(8.4, 3.5))

# ---- panel (a): anisotropy ranks the robust models ----
sc = ax[0].scatter(A[rb], rob[rb], c=clean[rb], cmap="viridis", s=46, edgecolor="k",
                   linewidth=0.4, zorder=3)
# trend line (rank-based robust fit shown as OLS for guidance)
m, b = np.polyfit(A[rb], rob[rb], 1)
xs = np.linspace(A[rb].min(), A[rb].max(), 50)
ax[0].plot(xs, m * xs + b, color="#9B2C2C", lw=1.6, ls="--", zorder=2)
ax[0].set_xlabel(r"gradient anisotropy  $A=\|\nabla M\|_1/\|\nabla M\|_2$")
ax[0].set_ylabel("AutoAttack robust acc. (%)")
ax[0].set_title(f"(a) shape ranks robust models\nSpearman $= {sA.statistic:+.2f}$  ($p={sA.pvalue:.0e}$)",
                fontsize=10.5)
cb = fig.colorbar(sc, ax=ax[0], fraction=0.046, pad=0.03)
cb.set_label("clean acc. (%)", fontsize=9)

# ---- panel (b): eta/L1 detects but saturates in ranking among robust ----
ax[1].scatter(etaL[rb], rob[rb], c=clean[rb], cmap="viridis", s=46, edgecolor="k",
              linewidth=0.4, zorder=3)
ax[1].set_xlabel(r"first-order certificate  $\eta/L_1$")
ax[1].set_ylabel("AutoAttack robust acc. (%)")
ax[1].set_title(f"(b) size detects, ranks weakly\nSpearman $= {sE.statistic:+.2f}$",
                fontsize=10.5)

fig.tight_layout()
out = os.path.join(HERE, "robustbench_aniso.pdf")
fig.savefig(out, bbox_inches="tight")
print("wrote", out)
print(f"robust-panel n={rb.sum()}  Spearman(A,rob)={sA.statistic:+.3f} p={sA.pvalue:.2e}"
      f"  Spearman(etaL,rob)={sE.statistic:+.3f}")
