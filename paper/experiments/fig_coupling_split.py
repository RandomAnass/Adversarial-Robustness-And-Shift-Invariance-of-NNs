#!/usr/bin/env python3
"""
Figure for Proposition (radial--tangential split of the margin gradient).

Two panels, both purely from the exact identity (no fitted data, so nothing to go
stale): (left) the polar decomposition of the margin gradient at a data point,
grad M = m(u) u + grad_S m(u), with the angle theta to the data ray; (right) the
resulting band kappa = ||grad M|| / (M/||x||) = sec(theta) = sqrt(1 + ||grad_S log m||^2),
marking the tight linear/invariant end (kappa=1) and the large operating-point factor
the trained networks realize.

Writes report/figures/coupling_split.pdf (+ .png preview).
Run: paper/env/cenv/bin/python paper/experiments/fig_coupling_split.py
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, FancyArrowPatch

FIG = os.path.join(os.path.dirname(__file__), "..", "report", "figures")
RADIAL = "#1f77b4"   # blue
TANG = "#d62728"     # red
GRADC = "#2ca02c"    # green (resultant)
OPER = 26.0          # measured ||grad M||_2 / (M/||x||) on the trained nets


def panel_geometry(ax):
    # unit-sphere cross-section
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(th), np.sin(th), color="0.8", lw=1.2, zorder=1)
    ax.scatter([0], [0], color="0.3", s=14, zorder=3)
    ax.annotate("O", (0, 0), textcoords="offset points", xytext=(-10, -10), color="0.3")

    # data ray x -> direction u on the circle
    ang = np.deg2rad(38)
    u = np.array([np.cos(ang), np.sin(ang)])
    ax.add_patch(FancyArrowPatch((0, 0), tuple(u), arrowstyle="-|>", mutation_scale=16,
                                 color="0.45", lw=1.8, zorder=2))
    ax.annotate(r"$x$ (data ray $u$)", tuple(u * 0.5),
                textcoords="offset points", xytext=(8, -14), color="0.35", fontsize=10)

    # gradient = radial (along u) + tangential (perp to u)
    tang_dir = np.array([-u[1], u[0]])     # +90 deg, tangent to sphere
    m_rad = 0.62                           # radial length  = m(u) = M/||x||
    g_tan = 0.62                           # tangential length = ||grad_S m||
    base = u                               # attach the decomposition at the data point
    rad_v = m_rad * u
    tan_v = g_tan * tang_dir
    grad_v = rad_v + tan_v

    # radial component
    ax.add_patch(FancyArrowPatch(tuple(base), tuple(base + rad_v), arrowstyle="-|>",
                                 mutation_scale=14, color=RADIAL, lw=2.2, zorder=4))
    ax.annotate(r"radial $=\dfrac{M(x)}{\|x\|}$" + "\n(Euler floor)", tuple(base + rad_v),
                textcoords="offset points", xytext=(8, -26), color=RADIAL, fontsize=9.5)
    # tangential component
    ax.add_patch(FancyArrowPatch(tuple(base), tuple(base + tan_v), arrowstyle="-|>",
                                 mutation_scale=14, color=TANG, lw=2.2, zorder=4))
    ax.annotate(r"tangential $=\nabla_{\mathbb{S}}\,m(u)$", tuple(base + tan_v),
                textcoords="offset points", xytext=(-8, 8), color=TANG, fontsize=9.5, ha="right")
    # resultant gradient
    ax.add_patch(FancyArrowPatch(tuple(base), tuple(base + grad_v), arrowstyle="-|>",
                                 mutation_scale=16, color=GRADC, lw=2.6, zorder=5))
    ax.annotate(r"$\nabla M(x)$", tuple(base + grad_v),
                textcoords="offset points", xytext=(6, -2), color=GRADC, fontsize=11)

    # dashed parallelogram guides
    ax.plot(*zip(base + rad_v, base + grad_v), ls=(0, (3, 3)), color="0.6", lw=1)
    ax.plot(*zip(base + tan_v, base + grad_v), ls=(0, (3, 3)), color="0.6", lw=1)

    # angle theta between x-direction (radial) and grad
    a0 = np.rad2deg(np.arctan2(rad_v[1], rad_v[0]))
    a1 = np.rad2deg(np.arctan2(grad_v[1], grad_v[0]))
    ax.add_patch(Arc(tuple(base), 0.34, 0.34, angle=0, theta1=a0, theta2=a1,
                     color="0.25", lw=1.4))
    midang = np.deg2rad((a0 + a1) / 2)
    ax.annotate(r"$\theta$", base + 0.27 * np.array([np.cos(midang), np.sin(midang)]),
                color="0.2", fontsize=12, ha="center", va="center")

    ax.text(-1.18, -1.28,
            r"$\|\nabla M(x)\|=\dfrac{M(x)}{\|x\|}\,\sqrt{1+\|\nabla_{\mathbb{S}}\log m(u)\|^2}"
            r"=\dfrac{M(x)}{\|x\|}\,\sec\theta$",
            fontsize=10.5)
    ax.set_xlim(-1.35, 1.6); ax.set_ylim(-1.45, 1.55)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(r"Polar split of the margin gradient", fontsize=11)


def panel_band(ax):
    t = np.linspace(0, 30, 400)               # tangential factor ||grad_S log m|| = tan(theta)
    tau = np.sqrt(1 + t ** 2)                  # = sec(theta)
    ax.plot(t, tau, color=GRADC, lw=2.4, zorder=3,
            label=r"$\tau=\sqrt{1+\|\nabla_{\mathbb{S}}\log m\|^2}$")
    # floor end: gradient purely radial
    ax.scatter([0], [1], color=RADIAL, s=42, zorder=4)
    ax.annotate("purely radial gradient\n"
                r"($\nabla_{\mathbb{S}}\log m=0$): floor",
                (0, 1), textcoords="offset points", xytext=(14, 6),
                color=RADIAL, fontsize=9.5)
    # operating region: trained nets AND linear max-margin both sit at ||x||/gamma
    ax.axhspan(OPER - 3, OPER + 3, color=TANG, alpha=0.12, zorder=1)
    ax.axhline(OPER, color=TANG, ls="--", lw=1.6, zorder=2)
    ax.annotate("trained nets & linear max-margin:\n"
                r"$\tau=\|x\|/\gamma\approx %d$" % int(OPER),
                (18, OPER), textcoords="offset points", xytext=(-2, 8),
                color=TANG, fontsize=9.5, ha="right")
    ax.set_xlabel(r"tangential factor $\|\nabla_{\mathbb{S}}\log m(u)\|=\tan\theta$", fontsize=10.5)
    ax.set_ylabel(r"$\tau=\dfrac{\|\nabla M\|}{M/\|x\|}$", fontsize=11)
    ax.set_title(r"The envelope is set by the tangential factor", fontsize=11)
    ax.set_xlim(-1, 30); ax.set_ylim(0, 33)
    ax.grid(alpha=0.25)
    ax.legend(loc="upper left", fontsize=9)


def main():
    fig, ax = plt.subplots(1, 2, figsize=(10.2, 4.3))
    panel_geometry(ax[0])
    panel_band(ax[1])
    fig.tight_layout()
    os.makedirs(FIG, exist_ok=True)
    out = os.path.join(FIG, "coupling_split.pdf")
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.replace(".pdf", ".png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("# wrote", out)


if __name__ == "__main__":
    main()
