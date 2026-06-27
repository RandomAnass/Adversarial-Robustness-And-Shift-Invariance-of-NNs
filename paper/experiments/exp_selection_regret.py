#!/usr/bin/env python3
"""
eta/L as an attack-free operator-SELECTION rule (vs shift-consistency vs clean accuracy).

For each condition (MNIST/Fashion/CIFAR-10 l_inf, CIFAR-10 l_2, the 6-arm graded sweep), rank
the invariance operators by an attack-free criterion and report the AutoAttack regret of the
selected operator against the oracle (best arm). eta/L = threat-matched margin / dual-norm
input-gradient. Reads the same full-10k AT JSONs the tables use + the graded partials.
Run: paper/env/cenv/bin/python paper/experiments/exp_selection_regret.py
"""
import json, glob, collections, os
import numpy as np

RES = os.path.join(os.path.dirname(__file__), "..", "results")


def load_full10k(path):
    d = json.load(open(path)); aakey = "aa_" + d["aa_specs"][0][0]; norm = d["aa_specs"][0][1]
    Ldual = "dec_L1" if norm == "Linf" else "dec_L2"
    by = collections.defaultdict(list)
    for r in d["results"]:
        by[r["arm"]].append(r)
    out = {}
    for a, rs in by.items():
        m = lambda k: np.mean([x[k] for x in rs if x.get(k) is not None])
        out[a] = dict(etaL=m("dec_margin") / m(Ldual), consist=m("consist"), clean=m("clean"), aa=m(aakey))
    return out


def load_graded():
    gr = collections.defaultdict(list)
    for f in glob.glob(os.path.join(RES, "at_partial", "graded_antialias", "*.json")):
        r = json.load(open(f)); gr[r["arm"]].append(r)
    return {a: dict(etaL=np.mean([x["dec_margin"] for x in rs]) / np.mean([x["dec_L1"] for x in rs]),
                    consist=np.mean([x["consist"] for x in rs]), clean=np.mean([x["clean"] for x in rs]),
                    aa=np.mean([x["aa_Linf_8_255"] for x in rs])) for a, rs in gr.items()}


def regret(arms, crit):
    best = max(a["aa"] for a in arms.values())
    pick = max(arms.values(), key=lambda a: a[crit])
    return best - pick["aa"]


def main():
    DS = {
        "MNIST (Linf)": "at_mnist_linf_full10k_20260625_043653.json",
        "Fashion (Linf)": "at_fashion_linf_full10k_20260625_160748.json",
        "CIFAR-10 (L2)": "at_cifar_l2_full10k_20260624_111942.json",
        "CIFAR-10 (Linf)": "at_cifar_linf_full10k_20260623_185505.json",
    }
    conds = {k: load_full10k(os.path.join(RES, v)) for k, v in DS.items()}
    conds["CIFAR-10 graded (6 ops)"] = load_graded()
    tot = collections.defaultdict(list)
    print(f"{'condition':24s} {'#ops':>4} | regret: {'eta/L':>7} {'consist':>8} {'clean':>7}")
    for name, arms in conds.items():
        line = f"{name:24s} {len(arms):>4d} | "
        for crit in ("etaL", "consist", "clean"):
            r = regret(arms, crit); tot[crit].append(r)
            line += f"        {r:>6.3f}" if crit == "etaL" else (f"{r:>9.3f}" if crit == "consist" else f"{r:>8.3f}")
        print(line)
    print("\nmean AutoAttack selection regret (lower = better attack-free selector):")
    for crit in ("etaL", "consist", "clean"):
        print(f"  select by {crit:8s}: {np.mean(tot[crit]):+.4f}")


if __name__ == "__main__":
    main()
