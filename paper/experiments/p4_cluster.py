#!/usr/bin/env python3
"""
P4 final check: controlled CLUSTER-GEOMETRY orbit data -- the one structure plain orbit data
lacks. Each class is a union of many LOW-RANK orbits (single-frequency cosines), each at a
DISTINCT frequency, so the orbits are near-orthogonal "clusters"; the two classes occupy disjoint
frequency bands, so they are power-spectrum separable. This is the closest orbit-structured
analogue of the near-orthogonal multi-cluster data behind the Frei/Li non-robustness results.

If unconstrained GD becomes non-robust here (unc << tied), the trajectory conjecture holds on
cluster-geometry data and P2/P3 are worth pursuing on THAT model. If unc ~= tied again, the
non-robust feature-averaging mechanism does not transfer to orbit-structured data at all.

Run: paper/env/cenv/bin/python paper/experiments/p4_cluster.py
"""
import numpy as np, torch
from p4_orbit_stress import (Unc, Tied, quad_surrogate, train, acc, r2_ddn, eta_over_L,
                             orbit_invariance, norm_margin, D)

def gen_cluster_data(seed, n_orbits=6, d=D):
    g = torch.Generator().manual_seed(seed); t = torch.arange(d).float()
    freqs = (torch.randperm(d // 2 - 1, generator=g)[: 2 * n_orbits] + 1)   # distinct freqs
    Fp, Fm = freqs[:n_orbits], freqs[n_orbits:]                              # disjoint bands per class
    Xs, ys, bases = [], [], {1: [], -1: []}
    for lab, F in ((1.0, Fp), (-1.0, Fm)):
        for f in F:
            ph = torch.rand(1, generator=g) * 2 * np.pi
            u = torch.cos(2 * np.pi * int(f) * t / d + ph); u = u / u.norm()
            bases[int(lab)].append(u)
            orb = torch.stack([torch.roll(u, s) for s in range(d)])
            Xs.append(orb); ys.append(torch.full((d,), lab))
    return torch.cat(Xs), torch.cat(ys), bases

def cross_orbit_orthogonality(bases):
    allb = bases[1] + bases[-1]
    G = torch.stack(allb); M = (G @ G.T).abs()
    off = M - torch.diag(torch.diag(M))
    return float(off.max())   # max |cos| between distinct base patterns; ~0 = near-orthogonal clusters

def run(seed, n_orbits, init, steps, d=D):
    X, y, bases = gen_cluster_data(seed, n_orbits, d)
    torch.manual_seed(seed); unc = train(Unc(256, d=d, init=init), X, y, steps=steps)
    torch.manual_seed(seed); tied = train(Tied(256, d=d, init=init), X, y, steps=steps)
    fq, _ = quad_surrogate(X, y)
    o = {"orth": cross_orbit_orthogonality(bases)}
    for name, f, mdl in (("unc", unc, unc), ("tied", tied, tied), ("quad", fq, None)):
        o[name] = dict(acc=acc(f, X, y), r2=r2_ddn(f, X, y), etaL=eta_over_L(f, X, y),
                       ov=orbit_invariance(f, X, d),
                       nm=(norm_margin(mdl, X, y) if mdl is not None else float("nan")))
    return o

def block(init, n_orbits, d, seeds, steps):
    rows = [run(s, n_orbits, init, steps, d) for s in range(seeds)]
    reg = "rich" if init < 0.5 else "lazy"
    print(f"\n==== {n_orbits} freq-orbits/class, d={d}, init={init} ({reg}), {seeds} seeds, steps={steps} ====")
    print(f"max cross-orbit |cos| = {np.mean([r['orth'] for r in rows]):.3f} (near-orthogonal clusters)")
    print(f"{'model':6s} {'acc':>6s} {'r2(mean)':>13s} {'eta/L':>8s} {'orbit-var':>9s} {'norm-margin':>11s}")
    agg = {}
    for name in ("unc", "tied", "quad"):
        a = np.mean([r[name]['acc'] for r in rows]); r2 = np.mean([r[name]['r2'] for r in rows])
        sd = np.std([r[name]['r2'] for r in rows]); el = np.mean([r[name]['etaL'] for r in rows])
        elsd = np.std([r[name]['etaL'] for r in rows]); ov = np.mean([r[name]['ov'] for r in rows])
        nm = np.mean([r[name]['nm'] for r in rows])
        agg[name] = (el, elsd)
        print(f"{name:6s} {a:6.3f} {r2:6.3f}+-{sd:5.3f} {el:8.3f} {ov:9.3f} {nm:11.4f}")
    (elu, elusd), (elt, eltsd) = agg["unc"], agg["tied"]
    ratio = elt / elu if elu > 0 else float("nan")
    sep = (elt - eltsd) > (elu + elusd)   # tied clearly above unc by >1 sigma
    print(f"VERDICT: eta/L tied/unc = {ratio:.2f}  (tied {elt:.3f}+-{eltsd:.3f} vs unc {elu:.3f}+-{elusd:.3f}) -> "
          + ("invariance HELPS (tied>unc, separated): cluster-geometry positive holds"
             if (ratio > 1.05 and sep) else "no clear architecture gap here"))
    return ratio

def main():
    seeds, steps = 5, 6000
    print("### PRIMARY: n_orbits=6, d=64, rich vs lazy ###")
    for init in (0.3, 3.0):
        block(init, 6, 64, seeds, steps)
    print("\n### ROBUSTNESS (lazy init=3.0): vary #orbits and d ###")
    for (no, d) in [(4, 64), (8, 64), (6, 128)]:
        block(3.0, no, d, 3, steps)

if __name__ == "__main__":
    main()
