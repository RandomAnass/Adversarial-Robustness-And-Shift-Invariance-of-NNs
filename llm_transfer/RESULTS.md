# LLM-transfer campaign — pilot results

## C1 (VLM tower diagnostic) — COMPLETE, strong PASS (commit fdb6249)
Frozen open_clip tower panel (base CLIP, FARE2/4 + TeCoA2/4 robust, DINOv2 widener), zero-shot ImageNet-100,
clean attack-free eta/L + shift-consistency vs AutoAttack (APGD-CE+DLR, +Square) robustness. 6 towers
(7th anti-aliased-stem widener OOM'd on GPU — dropped, not core).
- **eta/L1 vs AutoAttack robustness: Pearson +0.91, Spearman +0.93 (perm-p 0.014).**
- **shift-consistency vs robustness: -0.31 / -0.52 (perm-p 0.49, n.s.)** — the field's invariance metric does NOT order robustness; DINOv2 has the HIGHEST consistency (0.989) yet ZERO robustness (the VLM analog of our exactly-invariant arm).
- **partial corr eta/L | clean-acc = +0.95** (not a clean-accuracy proxy; clean-acc itself anti-predicts -0.75).
- **Selection rule:** pick tower by eta/L -> 5-pt robustness regret (near-oracle); by shift-consistency -> 88-pt regret (picks the zero-robust DINOv2). Same catastrophic 88-pt for clean-acc.
- **No gradient masking** (APGD<=PGD40<=FGSM, Square>=APGD, all towers/eps). **KILL not triggered.**
- Nuance: a cosine-embedding consistency variant DOES correlate (+0.94) — but the standard prediction-agreement shift-consistency the literature uses fails. Handle in writeup.
- VERDICT: the eta/L-vs-shift-consistency dissociation transfers to VLM vision towers cleanly; eta/L is a near-perfect attack-free encoder-selection rule where shift-consistency (and clean accuracy) fail catastrophically.

## T-DISS (text ratio vs consistency) — RUNNING (GPU 0, phase2 ~380/920 radius search, ~1 day)
## B2 (orbit-flip radius rho_G) — RUNNING (GPU 1, ~12-25 GPU-h)
