# Appendix port notes — `appendix_full.tex`

`appendix_full.tex` is a technical-report-depth appendix meant to be `\input` at
the `\appendix` point of `paper/combined/main.tex`. It ports the full proofs and
full experiment tables from the two checked source files, adapting notation to
the combined paper's macros. It does **not** edit `main.tex` and does **not**
change any number.

## How to integrate

In `main.tex`, at the `\appendix` point, replace (or follow) the current short
Appendix A/B with:

```latex
\appendix
\input{appendix_full.tex}
```

If both the current short appendix and this one are kept, rename the current
`\section{Structural theory and the bracket}\label{app:theory}` /
`\section{Additional experiments}\label{app:extra}` or drop them, because
`appendix_full.tex` supersedes them. The internal labels here are namespaced
(`app:full-theory`, `app:full-exp`, `app:ft-*`, and `*-app` on every theorem) so
they do **not** collide with `main.tex`'s `thm:A`, `prop:sandwich`,
`lem:ratiodegen`, `app:theory`, `app:extra`, `eq:deficit`.

## Compile check (passed)

Built a throwaway wrapper (`scratchpad/apptest/wrapper.tex`) that reproduces the
combined preamble macros + theorem environments, defines dummy targets for the
main-text labels the appendix `\ref`s (`thm:A`, `prop:sandwich`,
`lem:ratiodegen`, `prop:split`, `sec:saturation`, `sec:aniso`, `sec:signflip`,
`sec:etaL`), `\input`s `appendix_full.tex`, and loads the same `references.bib`
with `plainnat`. Result with `pdflatex` + `bibtex` (3 passes):

- **0 undefined references, 0 undefined citations.**
- **0 overfull hboxes** introduced by the appendix content.
- No LaTeX errors. (Only pre-existing bibtex style warning
  `can't use both volume and number fields in ross2018improving`, which is in
  the shared bib, not from this file.)

Appendix A (theory) spans ~7 pages, Appendix B (experiments) ~7 pages in the
wrapper; **~14 pages of appendix content total** (29 numbered theorem-like
environments, 8 tables).

## Macros defined here (move to the combined preamble)

The combined `main.tex` preamble lacks these; they are added at the top of
`appendix_full.tex` with `\providecommand` (so re-definition is harmless), but
the human should move them to the preamble:

`\Vac` `\Sep` `\Z` `\E` `\one` `\Piinv` `\sign` `\conv` `\dist` `\Lip` `\Orb`

All other macros used (`\R \dd \etaL \grad \Vinv \fdc \Pinv`) are already in the
combined preamble.

## Appendix A — proofs added (with source)

Ordered as the task requested. Each is a full proof, not a sketch.

| # | Result (label) | Source |
|---|---|---|
| 1 | Thm invariant linear margin = projection separation (`thm:A-app`) + Ge $1/\sqrt d$ recovery (`cor:ge-recover`) + finite-group generalization (`prop:finite-group-app`) + projection monotonicity (`cor:proj-mono`) | `report/main.tex` proof of `thm:A` (l.416); `theory_full_checked_v2.tex` `thm:finite-group-margin`, `cor:cyclic-margin`, `cor:projection-cannot-increase` |
| 2 | Two-sided bracket (`prop:sandwich-app`), linear exact $\kappa=1$ (`cor:linear-exact-app`), $t^{2n+1}$ large-$\kappa$ (`rem:tpow-app`), Tsuzuku-completion note (`rem:tsuzuku-app`), certifiable quadratic bracket (`lem:ps-colip-app`, `prop:ps-alpha-app`) | `report/main.tex` `app:bracket-lazy` proof of `prop:sandwich` (l.457), `prop:ps-alpha`; `theory_full_checked_v2.tex` `thm:sandwich`, `cor:linear-exact`, `rem:counter-kappa` |
| 3 | Scale-invariance / gauge-freeness (`lem:ratiodegen-app`) + constant-classifier corollary (`cor:ratiodegen-app`) | `report/main.tex` proof of `lem:ratiodegen` (l.450) |
| 4 | Power-spectrum span (`lem:ps-app`), conditional radius (`cor:C-app`), ball Lipschitz (`lem:ps-lip-app`), exactly-solvable nonlinear model (`prop:toy-app`) | `report/main.tex` `lem:ps-lip`, `thm:toy`; `theory_full_checked_v2.tex` `lem:ps-corrected`, `cor:ps-lip`, `thm:toy-radius` |
| 5 | Radial-tangential split (`prop:split-app`), envelope via achieved margin (`prop:ib-envelope-app`), scope remark (`rem:envelope-scope`) | `report/main.tex` proof of `prop:split` (l.446), `app:envelope` `prop:ib-envelope` |
| 6 | Lazy-regime cluster theorem (`thm:lazy-cluster-app`), ReLU caveat (`rem:lazy-relu-app`), rich-two-layer corollary (`cor:no-gap-var-app`), orbit-bundle (`lem:bundle-app`), orbit-rank (`lem:rank-app`), degeneracy props (`prop:rank-app`, `prop:generic-app`) | `report/main.tex` `app:bracket-lazy`; `theory_full_checked_v2.tex` `thm:lazy-cluster`, `rem:lazy-relu`, `cor:no-gap-var`, `lem:bundle-corrected`, `lem:orbit-rank`, `prop:single-orbit-correction` |

Scope preserved verbatim: the effective-dimension deficit
`r ≈ (η/L1)/(1+CA)` is stated as a **proposed** mechanism; the rich-regime /
bare-ReLU KKT selection is stated as **open** (`rem:lazy-relu-app`).

## Appendix B — tables added (with source file)

| Table | Content | Source file(s) |
|---|---|---|
| `tab:weakattack-full` | 6-arm ResNet weak-vs-strong (FGSM/PGD/AA at 1,2,4/255), width 1.0 | `paper/results/resnet_scale/tips_weakattack_w1.0.json` (standard/blurpool/aps/aug/tips) + `c10stdaux_tips_s0.json` (tips+aux) |
| `tab:wang-weak` | Wang CascadedGCNN their-protocol + pixel-space AA | `paper/results/b1_wang/cascaded_s0_eval.json` |
| `tab:at-cifar-full` | CIFAR-10 per-arm AT: Linf 8/255 and L2 0.5 (clean, consist, robust, η, L, η/L) | `paper/results/at_cifar_linf_full10k_20260623_185505.json`, `at_cifar_l2_full10k_20260624_111942.json` |
| `tab:at-mf-full` | MNIST (Linf 0.3) + Fashion (Linf 0.1) per-arm AT | `paper/results/at_mnist_linf_full10k_20260625_043653.json`, `at_fashion_linf_full10k_20260625_160748.json` |
| `tab:robustbench-full` | 30-model RobustBench panel (clean, robust, A, A/√d, η/L1) + correlation summary | `llm_transfer/pilots/c1_tower/robustbench_val/results.json` + `FINAL_REPORT.txt` |
| `tab:crown-full` | 17-tower four-cell (SC, PC, S, S_text, η/L1) | `llm_transfer/results/c1_tower/crownjewel_hardened.json` |
| `tab:crown-corr` | Pre-registered correlations + CIs (η/L1 vs S +0.80; partial|clean +0.82; vs S_text −0.54 raw, +0.006 partial; PC vs S_text +0.98; per-image n=2600 +0.89) | `llm_transfer/results/c1_tower/crownjewel_hardened_analysis.json` |
| `tab:anisosweep-corr` | MNIST/Fashion 24-cell A-vs-robustness at each budget + partials + mismatched-L2 nuance | `paper/results/anisosweep_analysis_{mnist,fashion}_linf.json` |

Narrative ported (diffusion data-axis, four TM-regression interventions,
certificate-count `prop:count-app` + reading `rem:count-app`) from
`report/main.tex` `app:extra` / `app:count` / `app:tmreg` and `main.tex`
combined §Additional-experiments.

## Citation-key remapping (report → combined `references.bib`)

The report's inline bib keys were remapped to the combined bib. Verified present:
`ge2021shift, hein2017formal, tsuzuku2018lipschitz, cohen2019certified,
kakarala2012bispectrum, soudry2018implicit, lyu2020gradient, ji2020directional,
vardi2022margin, jacot2018neural, chizat2019lazy, elesedy2021provably`
(= report's `Elesedy2021kernel`), `bietti2019inductive` (= report's
`BiettiMairalNTK2019`), `chizat2020implicit, frei2023double, li2025feature,
min2024can, tramer2020fundamental, ross2018improving, finlay2021scaleable,
galloway2019batchnorm, wang2025bridging, saha2024improving,
simongabriel2019adversarial, moosavi2019curvature, participation2025,
rony2019decoupling, croce2020reliable, kamath2021canwehaveitall`.

**Minor "standard fact" citations from the report that are NOT in the combined
bib were avoided** (rephrased to prose, no new bib key introduced), so nothing is
undefined: Haasdonk–Burkhardt (invariant kernels), Dontchev–Rockafellar (metric
subregularity), Cristianini–Shawe-Taylor (SVM textbook), Bartlett-2017,
Sokolic-2016, Cohen–Welling (G-CNN), Gunasekar-2018, Lawrence-2021,
Chen–Zhu-2023, Bruna–Mallat, Croce–Hein-FAB. If the human wants these cited,
add the entries to `references.bib` and re-insert the `\citep{}`s; they are
inessential to the proofs.

## Numbers reconciled / flagged

Every experimental number is traced to a source file. Reconciliations:

- **Crown-jewel image-adversarial spread S = 0.385 ± 0.244.** The analysis JSON
  reports **population** sd `0.23623` (ddof=0); the combined `main.tex` reports
  **sample** sd `0.244` (ddof=1). I used **0.244** to match the main text
  (recomputed sample sd = `0.2435`). The `27.6×` S/SC spread ratio in
  `tab:crown-full` prose is the analysis file's population-sd ratio (noted
  in-text). SC 0.009, PC 0.007, S_text 0.029 already match main text (sample sd).
- **CIFAR-10 L2 per-arm robust accuracy.** The report `app:at-tables` (2-seed)
  gives 0.581/0.594/0.464/0.570/0.609/0.628/0.511/0.613; the full-10k JSON gives
  0.5807/0.5943/0.4638/0.5705/0.6093/0.6282/0.5107/0.6128 — identical to 3 d.p.
  I used the full-10k JSON values (rounded), which match the report table.
- **MNIST/Fashion Linf per-arm AT.** Full-10k JSON values match the report
  `tab:at-perarm` exactly. Used as-is.
- **RobustBench.** `Spearman(A,robust)=-0.79`, bootstrap `[-0.92,-0.56]`, partial|clean
  `-0.77` (=`-0.766`), partial|η/L1 `-0.65` (=`-0.647`), 29-robust `-0.77`
  (jackknife-drop-Standard value `-0.768`): all from `FINAL_REPORT.txt`.
- **MNIST/Fashion anisosweep.** MNIST A vs AA: `-0.83`@0.2 / `-0.89`@0.3, partial
  `-0.75`/`-0.74`; mismatched-L2 `+0.48` raw → `+0.09` partial. Fashion `-0.61`@0.1
  / `-0.80`@0.15, partial `-0.53`/`-0.67`; mismatched-L2 `-0.74`. A-ranges
  `[2.38,16.59]` MNIST / `[3.99,13.17]` Fashion. All from the analysis JSONs.

**No unreconciled numbers.** Nothing in the vision-paper tables conflicted with a
JSON that I then had to drop; the one convention difference (population vs sample
sd for S) is resolved in favor of the main-text number and documented above.

One label note: `leaf_L_text` is `robust=False` in the raw JSON (its image-adversarial
robustness is not in the T tier), yet it is the paper's **text-hardened** tower;
`tab:crown-full` marks it `†` and counts it among the four non-image-robust
towers, exactly as the combined main text does (four non-robust, thirteen robust).
The highest raw `S_text` in the panel is `tecoa2` (0.9448); `leaf_L_text`
(0.9234) is in the top tier of paraphrase-consistency/`S_text` — the main text's
"highest ... in the panel" is read as the top tier for a text-hardened tower with
middling vision η/L1, which the data support; wording in the appendix says "among
the highest" to stay exact.
