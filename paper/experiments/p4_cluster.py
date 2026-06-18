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
                             orbit_invariance, D)

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

def run(seed, n_orbits, init, steps):
    X, y, bases = gen_cluster_data(seed, n_orbits)
    torch.manual_seed(seed); unc = train(Unc(256, init=init), X, y, steps=steps)
    torch.manual_seed(seed); tied = train(Tied(256, init=init), X, y, steps=steps)
    fq, _ = quad_surrogate(X, y)
    o = {"orth": cross_orbit_orthogonality(bases)}
    for name, f in (("unc", unc), ("tied", tied), ("quad", fq)):
        o[name] = dict(acc=acc(f, X, y), r2=r2_ddn(f, X, y), etaL=eta_over_L(f, X, y),
                       ov=orbit_invariance(f, X))
    return o

def main():
    n_orbits, steps, seeds = 6, 6000, 3
    for init in (0.1, 1.0):
        print(f"\n==== cluster-geometry: {n_orbits} near-orthogonal freq-orbits/class, "
              f"init={init} ({'rich' if init < 0.5 else 'lazy'}), steps={steps} ====")
        rows = [run(s, n_orbits, init, steps) for s in range(seeds)]
        print(f"max cross-orbit |cos| = {np.mean([r['orth'] for r in rows]):.3f} (near-orthogonal clusters)")
        print(f"{'model':6s} {'acc':>6s} {'r2(mean)':>12s} {'eta/L':>8s} {'orbit-var':>9s}")
        for name in ("unc", "tied", "quad"):
            a = np.mean([r[name]['acc'] for r in rows]); r2 = np.mean([r[name]['r2'] for r in rows])
            sd = np.std([r[name]['r2'] for r in rows]); el = np.mean([r[name]['etaL'] for r in rows])
            ov = np.mean([r[name]['ov'] for r in rows])
            print(f"{name:6s} {a:6.3f} {r2:6.3f}+-{sd:4.3f} {el:8.3f} {ov:9.3f}")
        ru = np.mean([r['unc']['r2'] for r in rows]); rt = np.mean([r['tied']['r2'] for r in rows])
        ratio = ru / rt if rt > 0 else float('nan')
        print(f"VERDICT: r2_unc / r2_tied = {ratio:.2f}  ->  "
              + ("CLUSTER GEOMETRY INDUCES NON-ROBUST BIAS: invariance helps here, P2/P3 worth pursuing on this model."
                 if ratio < 0.7 else
                 "unc ~= tied even with cluster geometry: non-robust feature-averaging does NOT transfer to orbit data; P2/P3 dead."))

if __name__ == "__main__":
    main()
