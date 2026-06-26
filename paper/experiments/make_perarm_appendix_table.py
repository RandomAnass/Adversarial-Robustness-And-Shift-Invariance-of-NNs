#!/usr/bin/env python3
"""
Build the per-arm robust-accuracy appendix table for the adversarial-training
generality conditions (MNIST/Fashion-MNIST under l_inf, CIFAR-10 under l_2).

Reads the same full-10k JSONs that cifar_at_plots.py renders the per-condition
tables from, aggregates per (arm, width) over seeds with the identical mean, and
emits one compact LaTeX table grouped by dataset:
    arm | w | clean | consist. | robust acc (threat-matched AutoAttack).
The robust accuracy is the primary AutoAttack spec (aa_specs[0]), i.e. the one
matched to the training threat. Output -> results/at_perarm_appendix.tex (+stdout).

Run: paper/env/cenv/bin/python paper/experiments/make_perarm_appendix_table.py
"""
import os, json, numpy as np

RESDIR = os.path.join(os.path.dirname(__file__), "..", "results")
ARM_LABEL = {"standard": "standard", "blurpool": "anti-aliased",
             "circular": "exact cyclic", "aug": "shift-aug"}
ARM_ORDER = ["standard", "blurpool", "circular", "aug"]

# (display name, threat label, json file)
CONDITIONS = [
    ("MNIST", r"$\ell_\infty=0.3$", "at_mnist_linf_full10k_20260625_043653.json"),
    ("Fashion-MNIST", r"$\ell_\infty=0.1$", "at_fashion_linf_full10k_20260625_160748.json"),
    ("CIFAR-10", r"$\ell_2=0.5$", "at_cifar_l2_full10k_20260624_111942.json"),
]


def agg(results):
    cells = {}
    for r in results:
        cells.setdefault((r["arm"], int(r["w"])), []).append(r)
    out = {}
    for key, rs in cells.items():
        d = {"arm": key[0], "w": key[1], "nseed": len(rs)}
        keys = set()
        for x in rs:
            keys |= {k for k in x if isinstance(x[k], (int, float))
                     and k not in ("w", "seed", "params", "nseed")}
        for k in keys:
            v = [x[k] for x in rs if x.get(k) is not None]
            d[k] = float(np.mean(v)) if v else float("nan")
        out[key] = d
    return out


def main():
    L = [r"\begin{tabular}{ll ccc}", r"\toprule",
         r"arm & $w$ & clean & consist. & robust acc. \\"]
    for disp, threat, fn in CONDITIONS:
        data = json.load(open(os.path.join(RESDIR, fn)))
        aakey = "aa_" + data["aa_specs"][0][0]   # threat-matched AutoAttack
        celld = agg(data["results"])
        widths = sorted({k[1] for k in celld})
        L.append(r"\midrule")
        L.append(r"\multicolumn{5}{l}{\emph{" + disp + r"}, " + threat + r"} \\")
        for w in widths:
            for a in ARM_ORDER:
                d = celld[(a, w)]
                L.append(f"{ARM_LABEL[a]} & {w} & {d['clean']:.3f} & "
                         f"{d['consist']:.3f} & {d[aakey]:.3f} \\\\")
    L.append(r"\bottomrule")
    L.append(r"\end{tabular}")
    out = os.path.join(RESDIR, "at_perarm_appendix.tex")
    open(out, "w").write("\n".join(L))
    print(f"# wrote {out}\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
