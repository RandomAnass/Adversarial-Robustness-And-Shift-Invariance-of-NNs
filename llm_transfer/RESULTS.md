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

## DIRECTION (2026-07-11, author): LLM campaign -> its OWN paper. Priority = correct literature + correct
## experimental design + correct implementation. Skip nothing. (lora_gauge dropped - not our run.)
Verification pass launched (adversarial, find-every-flaw):
- C1_verification (GPU 1): audit code (eta/L, AutoAttack, consistency, stats); resolve the n=6 / "eta/L just
  detects adversarial training" confound via the PER-IMAGE axis (>=1000 imgs) + a WIDER non-AT tower panel
  (>=10-12 towers spanning eta/L, not just AT-vs-non-AT); resolve the consistency-metric nuance (agreement
  -0.52 flat vs cosine +0.94 -> which is the fair null); lit re-verify (RDI 2504.18556, CLIP-Lipschitz). 
- B2_verification (no GPU): audit code; CRITICAL check = is "eps<rho_G on 100%" a real finding or a
  DEFINITIONAL artifact (rho_G = smallest flipping edit, so nothing flips below it trivially?); oracle
  non-circularity; is the trade-off KILL real or a weak-dose-knob artifact; label-extraction bug check on
  the 100%-entailment/97%-refusal degeneracy; lit re-verify (LGIP 2511.13494).
- T-DISS_verification: queued for when its run completes (~1 day, GPU 0).
Then: deep literature pass for the paper-candidate claims -> build the standalone LLM paper from the
VERIFIED, correctly-scoped results only.

## B2 VERIFICATION VERDICT (2026-07-11) — major honest corrections (verify/B2_verification.md)
- BUDGET-LAW "eps<rho_G 100%" = DEFINITIONAL ARTIFACT (rho_G := min flipping edit; 1511/1600 have 1 edit;
  only 8/1600 non-vacuous). DROP. A real budget test needs a graded family of increasing-size edits/item.
- TRADE-OFF KILL = BROKEN-MANIPULATION artifact (dose knob does nothing to NLI, jailbreaks safety 2.8->24%);
  the trade-off was never fairly tested -> KILL does NOT count as a negative.
- eta/L ⊥ rho_G (-0.11) MIS-SPECIFIED (reused T-DISS refusal margin on sentiment/NLI). RECOMPUTE with task-class margin.
- SURVIVES (real): rho_G as a measurable orbit-flip radius (oracle verified non-circular); the CONSTANT-
  CLASSIFIER DEGENERACY (Llama 100% entailment on MoNLI / 97% refuse; Qwen doesn't -> model-dependent) = a
  clean empirical instance of lem:ratiodegen and B2's best standalone finding.
- DEFENSIBLE CLAIM: generative LLMs have a measurable rho_G upper-bounding the oracle-robust radius
  (prop:rhoG), and Llama-3-8B shows a model-dependent constant-classifier collapse on negation-NLI + harmful
  requests (excessive-invariance failure LGIP's rate metrics can't express). Trade-off + budget-law = NO-GO.
- B2 FIXES QUEUED (need GPU, after C1 verifier frees GPU1): (1) recompute eta/L with per-task-class margin;
  (2) report flip-rate PER-FAMILY (sentiment/NLI/safety), not pooled 0.564; (3) either design a graded-edit
  family for a real budget test + a FAIR invariance intervention, or drop both and keep rho_G-dist + degeneracy.
