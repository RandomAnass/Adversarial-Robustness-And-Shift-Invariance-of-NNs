# Main paper — full status snapshot (2026-06-29)

**Title:** *When Does Shift-Invariance Permit Adversarial Robustness? A Margin-Preservation Theory*
(single author: Anass Al Ammiri / RandomAnass; supervisor Mahalakshmi Sabanayagam).
**File:** `paper/report/main.tex` — 23 pp, compiles clean. **Latest commit:** `b5e406e` (local, NOT pushed; pushes are gated on explicit request). **Status:** submission-ready honest analysis paper at a calibrated **soft-5/6** ("accept-if-championed"), TMLR-profile.

## One-line thesis
Whether making a CNN more shift-invariant helps or harms adversarial robustness is governed by ONE quantity: the margin-to-Lipschitz ratio `eta/L` of the discriminative signal that survives projection onto the invariant feature space. Large surviving ratio -> invariance and robustness coexist; small surviving margin -> they trade off.

## Theory (exactly 2 Theorems, rest Proposition/Lemma/Corollary, genre-matched)
- **Thm A** (`thm:A`): invariant linear max-margin = separation of DC-projected data; recovers Ge 2021's `1/sqrt(d)` collapse. **Thm lazy-cluster** (`thm:lazy-cluster`, appendix): in the lazy/NTK regime, orbit-averaging is an orthogonal RKHS projection, so the invariant interpolant has a smaller CERTIFIED Lipschitz at equal margin (gap = orbit-variance).
- Two-sided bracket `eta/L <= r2 <= eta/alpha` (`prop:sandwich`); power-spectrum escape lemma (`lem:ps`); Ge/Kamath reconciliation; the **exact radial-tangential (polar) split** of the margin gradient `||grad M|| = (M/||x||) sqrt(1 + ||grad_S log m||^2)` (`prop:split`) with the tangential factor `tau` = data condition number `||x||/gamma` (distinct from the bracket `kappa = L/alpha`); the **achieved-margin envelope** `prop:ib-envelope` (uses gamma_IB, the margin GD actually reaches, not the global max-margin — closes the implicit-bias gap honestly).
- §4 optimization: orbit-rank lemmas; **margin-free** on orbit-closed data (GD self-symmetrizes); lazy-cluster theorem; rich-regime trajectory open.

## Empirical (the actual strength)
- **Dissociation (headline):** shift-consistency ANTI-predicts adversarial robustness; threat-matched `eta/L` predicts it. Capacity-matched dissection on MNIST / Fashion / CIFAR-10 (+ CIFAR-100 at ResNet scale).
- Under PGD-AT, both laws hold across 3 datasets, 2 threat models, and a PreActResNet-18 backbone; per-sample certificate holds.
- **Graded anti-aliasing** improves robustness at matched clean accuracy via the margin; exact invariance hurts (margin collapse).
- **Selection rule:** picking the invariance operator by highest `eta/L` (attack-free) gives ~0 AutoAttack regret (ON PAR WITH CLEAN ACCURACY); shift-consistency picks the worst (+8.8pp regret).
- **Four interventions** confirm `eta/L` is a diagnostic, NOT a trainable target (every attempt to raise it collapses the margin) — appendix.

## Review calibration (3 independent fresh-agent rounds, corpus-calibrated)
Rounds 7/8/9 all **5/10**; all verified the theorems sound (re-derived) and attributions accurate; no false positives; credited honesty + breadth + stat-hygiene above corpus median. **Ceiling = contribution category, not error**: `eta/L` offers no positive lever beating a free baseline (ties clean-acc as selector; untrainable). Reviews at `paper/review_calibration/REVIEW_round{7,8,9}.md` + `COHERENCE_AUDIT.md` + `REGRESSION_CHECK.md`.

## Done recently
De-bloat to 2 Theorems; full coherence pass (kappa/tau disambiguation, abstract restructure, CIFAR-100 scoping, dedup); gamma_IB envelope integrated; foundational implicit-bias lit added (Lyu-Li, Ji-Telgarsky, Soudry, Vardi-Shamir-Srebro). Comparator-paper study in `paper/literature_comparators/`.

## Theory to-dos for the author (from the audit)
`paper/theory/THEORY_AUDIT_AND_EXTENSIONS.md` — no math errors found; 6 scope/clarity corrections (C1 sandwich novelty/hypothesis; C2 say "certified" Lipschitz; C3 thm:ib doesn't itself bound gamma_IB; C4 margin-free holds in rich regime too so only L/selection is open; C5 Bubeck-Sellke paraphrase; C6 add Chizat-Bach + Wei et al. cites) and 5 ranked extensions (E1 rich-regime strict cluster gap; E2 gamma_IB vs gamma_C; E3 multiclass envelope [easy]; E4 explicit alpha; E5 bispectrum tradeoff). The full worked theory is in `paper/theory/coupling_conjectures.tex`.

## Settled side-results (NOT in the paper)
- `paper/method_exploration/SUMMARY.md` — the eta/L-free METHOD search: 3 candidates (learnable anti-aliasing / margin recipe / spectral branch) all tie-or-lose vs a fixed-anti-aliasing AT baseline. Documented null; confirms bounded-levers thesis.

## Export
`adv_shift_invariance_overleaf_20260629.zip` (repo root) — Overleaf-ready (main doc = `report/main.tex`).

## HARD RULES (carry forward)
Commit as RandomAnass <anass.al-ammiri@tum.de>, no co-author/AI trailers; never push without explicit request; never touch the finance sub-paper; paper stays a clean scientific doc (no process/version/audit narration); agents are unreliable for theory (author proves, agents suggest paths + I verify firsthand); `PYTHONNOUSERSITE=1` for the venv; shared-GPU etiquette (never touch hannah/philip jobs).

---
## NEW DIRECTION (active, separate from this paper): diffusion-data robustness MECHANISM
**Finding (Stage-1 pilot, PRN-18, 1 seed, VERIFIED):** EDM synthetic data lifts AutoAttack +12.1pt (0.354->0.475), but the MARGIN DECREASES (4.46->2.57); the gain is entirely a SMOOTHNESS / lower-input-sensitivity effect (L2 5.11->2.51, falls faster than the margin), so eta/L and the DDN radius rise. **"Diffusion data buys smoothness, not margin"** — opposite of intuition, unframed by prior work (FID/robust-overfit/representation-geometry). New-paper seed. Work dir `paper/diffusion_robustness/` (data `data/1m.npz` = 1M EDM CIFAR-10, verified). Stage-2 sweep running. Caveats: 1-seed; logit-scale (must control temperature); compute-matched design. See the ledger memory for full detail.
