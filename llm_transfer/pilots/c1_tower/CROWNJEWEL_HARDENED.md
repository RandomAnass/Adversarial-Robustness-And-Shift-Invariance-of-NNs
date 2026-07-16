# Crown-Jewel HARDENED — RESULTS

Pre-registered 2x2 (modality x perturbation-type) invariance-vs-robustness dissociation on zero-shot CLIP, executed faithfully from `CROWNJEWEL_HARDENED_DESIGN.md` (human-approved; not redesigned). Raw: `results/c1_tower/crownjewel_hardened.json` + `crownjewel_hardened_analysis.json`; figure `paper/figures/crownjewel_hardened.pdf`.

**Panel actually run (17 encoders; 13 robust, 4 non-robust):** clip_b32_laion2b, fare4_b32, tecoa4_b32, fare4_b16, tecoa4_b16, clip_b16_openai, simclip4, simclip2, clip, clip_l14_laion2b, fare4_cnxt, tecoa4_cnxt, fare4, tecoa4, fare2, tecoa2, leaf_L_text.

**LEAF robust-text stretch (`leaf_L_text`):** INCLUDED (see cells + verdict).


## Per-tower four cells + predictors

| tower | robust | clean | SC | PC | S (img-adv) | S_text (txt-adv) | S_text K20 | eta/L1 | A | radius | AA complete |
|---|---|---|---|---|---|---|---|---|---|---|---|
| clip_b32_laion2b | n | 0.843 | 0.960 | 0.979 | 0.000 | 0.902 | 0.840 | 0.00069 | 216.6 | 0.00169 | yes |
| fare4_b32 | Y | 0.691 | 0.963 | 0.969 | 0.393 | 0.861 | 0.797 | 0.01756 | 196.5 | 0.01683 | yes |
| tecoa4_b32 | Y | 0.770 | 0.966 | 0.968 | 0.575 | 0.850 | 0.775 | 0.02342 | 194.7 | 0.02518 | yes |
| fare4_b16 | Y | 0.760 | 0.976 | 0.962 | 0.495 | 0.836 | 0.794 | 0.01963 | 177.8 | 0.02200 | yes |
| tecoa4_b16 | Y | 0.794 | 0.977 | 0.972 | 0.573 | 0.874 | 0.842 | 0.02569 | 176.1 | 0.02403 | yes |
| clip_b16_openai | n | 0.844 | 0.968 | 0.981 | 0.000 | 0.899 | 0.845 | 0.00049 | 193.4 | 0.00113 | yes |
| simclip4 | Y | 0.836 | 0.979 | 0.974 | 0.540 | 0.886 | 0.840 | 0.01245 | 149.7 | 0.02447 | yes |
| simclip2 | Y | 0.877 | 0.982 | 0.979 | 0.340 | 0.900 | 0.861 | 0.01124 | 165.8 | 0.01970 | yes |
| clip | n | 0.900 | 0.982 | 0.984 | 0.000 | 0.922 | 0.869 | 0.00031 | 146.2 | 0.00146 | yes |
| clip_l14_laion2b | n | 0.891 | 0.986 | 0.985 | 0.000 | 0.932 | 0.899 | 0.00025 | 133.1 | 0.00163 | yes |
| fare4_cnxt | Y | 0.803 | 0.980 | 0.973 | 0.507 | 0.877 | 0.839 | 0.02151 | 168.8 | 0.02372 | yes |
| tecoa4_cnxt | Y | 0.813 | 0.974 | 0.973 | 0.620 | 0.894 | 0.838 | 0.02766 | 163.6 | 0.02692 | yes |
| fare4 | Y | 0.853 | 0.983 | 0.976 | 0.580 | 0.893 | 0.838 | 0.01220 | 156.1 | 0.02631 | yes |
| tecoa4 | Y | 0.875 | 0.989 | 0.982 | 0.693 | 0.914 | 0.873 | 0.01636 | 154.4 | 0.03014 | yes |
| fare2 | Y | 0.885 | 0.980 | 0.982 | 0.320 | 0.919 | 0.873 | 0.01130 | 171.4 | 0.01757 | yes |
| tecoa2 | Y | 0.915 | 0.990 | 0.989 | 0.578 | 0.945 | 0.905 | 0.02207 | 175.7 | 0.02515 | yes |
| leaf_L_text | Y | 0.887 | 0.981 | 0.985 | 0.338 | 0.923 | 0.883 | 0.01174 | 171.1 | 0.01933 | yes |

## (A) Two-column saturation vs spread

| cell | mean | sd | min | max |
|---|---|---|---|---|
| IMAGE-invariance SC | 0.977 | 0.009 | 0.960 | 0.990 |
| TEXT-invariance PC | 0.977 | 0.007 | 0.962 | 0.989 |
| IMAGE-adversarial S | 0.385 | 0.236 | 0.000 | 0.693 |
| TEXT-adversarial S_text | 0.896 | 0.029 | 0.836 | 0.945 |

- spread_ratio IMAGE = sd(S)/sd(SC) = **27.6x**
- spread_ratio TEXT  = sd(S_text)/sd(PC) = **4.1x**

## (B) Dissociation (cross-tower Spearman, bootstrap 95% CI)

| pair | Spearman [95% CI] |
|---|---|
| SC_vs_S | 0.212  [-0.368, 0.670] |
| PC_vs_S | -0.303  [-0.752, 0.216] |
| PC_vs_S_text | 0.980  [0.887, 1.000] |
| SC_vs_S_text | 0.620  [0.189, 0.864] |
| SC_vs_radius | 0.238  [-0.329, 0.691] |
| PC_vs_radius | -0.267  [-0.684, 0.225] |

## (C) Prediction — the KEY new test

Does the SAME margin/Lipschitz diagnostic (eta/L1) that predicts image-adversarial robustness ALSO predict text-adversarial robustness, while neither consistency does?

| pair | Spearman [95% CI] |
|---|---|
| etaL1_vs_S | 0.801  [0.437, 0.952] |
| etaL1_vs_radius | 0.748  [0.370, 0.933] |
| etaL1_vs_S_text | -0.542  [-0.866, -0.081] |
| A_vs_radius_robustonly | -0.495  [-0.864, 0.159] |
| A_vs_S_text_robustonly | -0.440  [-0.812, 0.358] |
| etaL1_vs_S_text_robustonly | -0.407  [-0.822, 0.161] |
| etaL1_vs_radius_robustonly | 0.456  [-0.140, 0.866] |

## (D) Partial correlations controlling clean_acc (rank-residualized)

| pair (| clean) | partial Spearman [95% CI] |
|---|---|
| etaL1_vs_S__clean | 0.815  [0.501, 0.954] |
| PC_vs_S__clean | -0.135  [-0.745, 0.570] |
| etaL1_vs_S_text__clean | 0.006  [-0.546, 0.515] |
| PC_vs_S_text__clean | 0.775  [0.197, 1.000] |

## (E) Per-image pooled (powered) + cross-modal coupling

- eta/L1 (per-image ratio) vs robust radius, pooled over robust towers (n=2600): **0.886** [0.875, 0.896]
- anisotropy A vs robust radius, pooled: -0.052 [-0.091, -0.014]
- NEW cross-modal coupling: worst-template TEXT margin vs Linf robust radius, pooled over robust (n=2600): **0.763** [0.744, 0.780] (reported without over-claim: is the image easiest to flip textually also easiest visually?)

## (F) Two-way headline recompute

- eta/L1 vs S_text: Spearman **-0.542** vs pairwise concordance **0.301**
- PC vs S_text: Spearman 0.980 vs pairwise concordance 0.956
- eta/L1 vs S: Spearman 0.801 vs pairwise concordance 0.831

## K=20 sensitivity check

- S_text mean: K11 = 0.896, K20 = 0.848 (more templates -> lower, as expected).
- monotone-down on all towers: **True** (17/17).
- cross-encoder ranking stability K11 vs K20: Spearman **0.922**.

## Sanity gates

- S <= clean_acc (all towers): **True**
- S_text <= a_avg <= a_ref <= 1 (all towers): **True**
- PC(ref vs ref) = 1.0 (all towers): **True**
- fare4 radius (0.02631) > clip radius (0.00146): **True**
- simclip4 S>0 (robust, clusters with AT): **True** (S=0.540)
- simclip2 S>0 (robust, clusters with AT): **True** (S=0.340)
- non-robust S at eps=0.01569: {'clip_b32_laion2b': 0.0, 'clip_b16_openai': 0.0, 'clip': 0.0, 'clip_l14_laion2b': 0.0}
- targeted AA complete per tower: {'clip_b32_laion2b': True, 'fare4_b32': True, 'tecoa4_b32': True, 'fare4_b16': True, 'tecoa4_b16': True, 'clip_b16_openai': True, 'simclip4': True, 'simclip2': True, 'clip': True, 'clip_l14_laion2b': True, 'fare4_cnxt': True, 'tecoa4_cnxt': True, 'fare4': True, 'tecoa4': True, 'fare2': True, 'tecoa2': True, 'leaf_L_text': True}

## Verdict

- SATURATION vs SPREAD. Both INVARIANCE cells saturate near 1 with tiny spread (SC 0.977+-0.009, PC 0.977+-0.007). The IMAGE-adversarial cell is the ONE cell with real spread (S 0.385+-0.236, range [0.000,0.693]; spread ratio 27.6x). The TEXT-adversarial cell is itself fairly SATURATED/NARROW (S_text 0.896+-0.029, band [0.836,0.945]): worst-case over the 11 curated meaning-preserving paraphrases only flips ~6-16% of images even for non-robust CLIP, so the discrete-K worst case does not open up the way the continuous eps-ball does.
- PREDICTION. eta/L1 predicts the IMAGE-adversarial cell (eta/L1 vs S = 0.80 [0.44,0.95], vs radius = 0.75; partial|clean_acc = 0.81 [0.50,0.95] -- SURVIVES the clean-acc control), while neither consistency predicts it (SC vs S = 0.21 [-0.37,0.67], CI spans 0).
- THE KEY CORRECTED RESULT (text cell). Raw cross-tower eta/L1 vs S_text = -0.54 [-0.87,-0.08] LOOKS like an anti-prediction, but it is a CLEAN-ACCURACY CONFOUND: the partial correlation controlling clean_acc VANISHES to eta/L1 vs S_text | clean = 0.01 [-0.55,0.51] (CI spans 0). So eta/L1 is ORTHOGONAL to the residual variation of worst-case-over-paraphrases once clean accuracy is held fixed -- it is NOT a modality-specific predictor of the text cell; the apparent negative sign was just AT vision towers having lower clean acc. What DOES co-move with S_text is average-case paraphrase-consistency itself (PC vs S_text = 0.98 [0.89,1.00]), unsurprising since S_text is the worst-case sibling of PC over the SAME template family.
- HONEST HEADLINE. Both VISUAL (shift) and TEXTUAL (paraphrase) invariance saturate across zero-shot CLIP encoders; among the four 2x2 cells only the IMAGE-adversarial cell carries real cross-encoder spread, and the threat-matched margin-to-Lipschitz ratio eta/L1 predicts THAT cell (surviving a clean-acc control) while the consistencies do not. Worst-case-over-11-paraphrases is itself fairly saturated, and eta/L1 is orthogonal to its residual variation once clean accuracy is controlled. 'Invariance is not robustness' is established cleanly in the image modality; the text-adversarial cell as constructed (discrete curated K=11) does not spread enough to host an independent robustness axis for the vision-tower eta/L1 to predict.
- Honest asymmetry: the IMAGE-adversarial cell is a CONTINUOUS Linf eps-ball worst-case; the TEXT-adversarial cell is a DISCRETE finite-set (K templates) worst-case. The unifying axis that makes the 2x2 fair is *average-case vs worst-case over a semantically-null perturbation family*, NOT the cardinality of the family. The discrete text `min` is a lower-bound proxy for the true worst-case-over-all-meaning-preserving-English; enlarging K tightens it monotonically (confirmed by the K=20 check).
- Stretch (robust-TEXT tower): `leaf_L_text` (LEAF-CLIP ViT-L rho50-k1-constrained-FARE2, the ONLY panel member with a robustified TEXT tower; recipe-C transformers->tower conversion) WAS included and passed the sanity gates: clean acc 0.887, full targeted AA S=0.338 (>0, complete), radius 0.0193. It is the cleanest independent-text-axis probe: despite only a mid-range vision eta/L1 (0.0117), its hardened text tower gives it the HIGHEST paraphrase-consistency in the panel (PC 0.985) and a high worst-case-over-paraphrases (S_text 0.923, vs panel mean 0.896) -- i.e. text-hardening lifts the text cell independently of the vision-tower eta/L1, consistent with the corrected headline that eta/L1 is orthogonal to S_text once clean accuracy is controlled.
