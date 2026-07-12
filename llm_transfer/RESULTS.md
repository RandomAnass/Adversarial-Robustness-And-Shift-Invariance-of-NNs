# LLM-transfer campaign — pilot results

## C1 (VLM tower diagnostic) — COMPLETE + VERIFIED + EXTENDED, strong PASS (verify/C1_verification.md)
Frozen open_clip tower panel, zero-shot ImageNet-100, clean attack-free eta/L + shift-consistency vs
AutoAttack (APGD-CE + APGD-T ensemble) robustness. **Extended to n=11 towers = 4 AT (FARE2/4, TeCoA2/4)
+ 7 non-AT (base CLIP, DINOv2, + 5 CLIP variants over corpus/patch/capacity)**; metaclip dropped (11 not 12).
The verifier demoted the original +0.91 tower number (was partly an AT-detector at n=6), re-scoped the
headline to the powered PER-IMAGE axis, then the extended run broke the confound outright:
- **Tower axis (n=11): eta/L1 vs robustness Pearson +0.953** [0.92,1.0], perm-p 0.0009. **Survives partialling
  out the AT indicator: partial(eta/L1, S | is-AT) = +0.51, | clean&is-AT = +0.56.** Cosine-consistency's
  +0.81 **collapses to +0.15** under the same control (it was the AT co-detector). SC_pred (fair null) n.s. +0.37.
- **HEADLINE — per-image dissociation:** Spearman(per-image eta/L1, robust radius) = **+0.78** [0.75,0.81] pooled
  over AT towers, and **+0.54 … +0.79 WITHIN each non-AT CLIP tower** (finer grid gave them radius spread) —
  vs shift-consistency **+0.12 / ≈0**. The dissociation is NOT an AT artifact; holds on AT and non-AT towers.
- **Selection rule (n=11):** eta/L1 -> 5-pt regret (near-oracle); SC_pred -> 88-pt; clean-acc -> 88-pt.
- **Bonus cross-domain confirmation:** the main paper's weak-attack artifact replicates in VLMs — every non-AT
  CLIP tower has S_fgsm 0.16–0.46 but S_apgd = S_pgd40 = 0.0 (FGSM shows "robustness" AutoAttack erases).
- **No gradient masking** (APGD<=PGD40<=FGSM, Square>=APGD). Implementation verified line-by-line; no sign flips.
- VERDICT: **GO, confound-controlled.** eta/L is a near-oracle attack-free encoder-selection rule; shift-consistency
  (prediction-agreement) and clean accuracy fail; cosine-consistency only "works" by co-detecting AT (dissolved by partials).

## T-DISS (text ratio vs consistency) — MAIN RUN DONE 2026-07-12 14:04 (phase2 920/920). Post-pipeline
##   (gauge sweep -> masking battery -> GCG 128x250 -> validations -> analyze -> summary -> figures) NOW RUNNING
##   on GPU 0 (run_post.sh, PID 630390). Was deadlocked on a self-matching-pgrep monitor; fixed 2026-07-12.
##   Adversarial verification queued for when results/SUMMARY.json lands.
## B2 (orbit-flip radius rho_G) — DONE + VERIFIED + CORRECTED (see verdict below). Fixes still queued.

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
- B2 FIXES DONE 2026-07-12 (fix_etaL.py + analyze_fixes.py; results/etaL_taskmargin.jsonl, fixes.json):
  (1) eta/L recomputed with TASK-CLASS margin -> M>0 now == base acc per family (was 97-100% negative on
      sentiment/NLI). Pooled Spearman(eta/L, rho_G_emb) = -0.025 [-0.09,+0.04], a CLEAN NULL. The old -0.11
      "decoupling" was a mis-specified-margin artifact, RETRACTED. New claim (upgraded NO-GO->GO): eta/L and
      rho_G are ORTHOGONAL axes (sensitivity-robustness ⊥ excessive-invariance radius).
  (2) 0.564 DECOMPOSED: sentiment 0.67 among-correct (GENUINE excessive invariance; clean-antonym subset 0.673,
      survives the negation-oracle caveat) vs NLI 1.00 & safety 0.62 (CONSTANT-CLASSIFIER degeneracy: model says
      'entailment' on 100%, 'refuse' on 97%). NLI flip == P(gold=entailment) exactly. Never report pooled.
  (3) graded-edit budget test + fair invariance intervention: STILL DEFERRED (needs new corpus design; budget-law
      + trade-off remain NO-GO). Defensible B2 paper parts now: rho_G radius (prop:rhoG theorem) + orthogonality
      + sentiment genuine-invariance + NLI/safety constant-classifier degeneracy (model-dependent).
