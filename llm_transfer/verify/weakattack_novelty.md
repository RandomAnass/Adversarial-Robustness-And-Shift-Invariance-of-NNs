# Weak-attack-artifact in frozen VLM encoders — novelty verification + section plan

Agent scoop-hunt (~30 searches, ~15 full-text reads across 3 agents) + my source-verification of the
debunk target. The user's directive: promote this from a "bonus" to a proper section, but verify
novelty first, then write in rounds.

## Verdict: PROMOTABLE to a full section — but ONLY as a targeted debunk, not a discovery

Each COMPONENT fact is prior art:
- "frozen/clean CLIP → ~0 robust accuracy under AutoAttack" — established: FARE (2402.12336, ICML24)
  *"On adversarial inputs, CLIP breaks completely at both radii."*; PMG-AFT (2401.04350, CVPR24)
  *"robust accuracy dropping from 17.38% to 1.74%"* PGD-10→AutoAttack on zero-shot CLIP.
- "weak-attack robustness is a masking artifact erased by strong attacks" — Athalye-Carlini-Wagner
  Obfuscated Gradients (1802.00420): *"One-step attacks perform better than iterative attacks … it is
  likely that the iterative attack is becoming stuck at a local minimum."* + Carlini eval checklist
  (1902.06705): *"Do not use Fast Gradient Sign (exclusively)."*
- "invariance/equivariance causes robustness" — the debunk TARGET, VERIFIED by me at arXiv:
  **2510.16171 (Wang et al., "Bridging Symmetry and Robustness")**: claims robustness *"without
  requiring adversarial training"*, evaluates *"under both FGSM and PGD attacks"*, uses **no
  AutoAttack** (grep autoattack = 0), attributes it to *"regularize gradients"* / smoother boundaries
  — i.e. the textbook gradient-masking mechanism.
- "invariance REDUCES robustness" — Singla-Ge (2103.02695) (opposite sign; pre-empt the referee).

**NOT FOUND after ~30 searches + ~15 reads:** any paper that measures the invariance→robustness
CORRELATION itself, shows it holds under FGSM, and demonstrates it VANISHES under AutoAttack — least
of all on frozen foundation-model encoders. That specific composite is unoccupied.

## Defensible novelty sentence (use ~verbatim)
Recent work argues architectural invariance/equivariance confers adversarial robustness *without
adversarial training* but evaluates the claim only with FGSM and PGD (e.g. Wang et al. 2510.16171,
no AutoAttack, robustness attributed to gradient smoothing). We show that on frozen, non-
adversarially-trained CLIP/VLM vision towers the apparent invariance→robustness correlation is a
weak-attack (FGSM) artifact: it exhibits the Athalye-Carlini-Wagner gradient-masking signatures and
is erased to 0.0 robust accuracy under the APGD-CE+APGD-T AutoAttack ensemble, across pretraining
corpora, patch sizes, and capacities.

## Must-cite (arXiv): 2510.16171 (target), 1802.00420, 1902.06705, 2003.01690 (AutoAttack),
2402.12336 (FARE), 2401.04350 (PMG-AFT), 2103.02695 (Singla-Ge, pre-empt), 2307.09804 + 2204.00491
(anti-aliasing counter-lit; note ASAP's own admission native anti-aliased robustness fails at 4/255).

## Two honesty flags from the agent (heeded)
1. It caught TWO fabricated quotes in an earlier search summary (a "36%/95% FGSM-vs-AA CLIP table"
   and a "24.63→0.41" figure) — the papers do not contain them. NONE of these entered our docs; all
   our C1 numbers (FGSM 0.16–0.46, APGD/PGD40 = 0.0) are from our own data. Do not cite those numbers.
2. Strongest reviewer risk: "invariance already known to hurt robustness (Singla-Ge)" — position
   strictly against the PRO-invariance claimants (2510.16171 / any FGSM-PGD-only eval), not as
   discovering either half. Second risk: "isn't this Obfuscated Gradients again?" — yes as mechanism,
   but never applied to the invariance-robustness correlation on frozen VLM towers (the novel object).

## The experiment that makes it a section (run_weakattack.py — armed for a free GPU)
1. **PGD-k monotonicity** per tower: robust acc at k=1(FGSM),2,5,10,20,40, AutoAttack, Square. ACW:
   robust acc decays monotonically, one-step must not beat iterative; AT towers do NOT collapse
   (contrast); Square ≥ APGD (no masking on AT).
2. **Correlation decay** (the killer figure): Pearson(shift-consistency, robust_acc) ACROSS towers as
   a function of attack strength — positive/large under FGSM, ~null under AutoAttack.
3. (queued extensions if a referee pushes) unbounded-eps sweep 2→32/255 (FGSM success saturates <100%
   = masking); per-tower input-gradient-norm / loss-landscape diagnostic tying the masking to
   2510.16171's own "gradient smoothing" mechanism; EOT to rule out stochastic masking.

## Writing rounds (user asked for multiple)
- Round 1 (done): §5 of main.tex reframed as a targeted debunk with the defensible sentence + ACW.
- Round 2 (after run_weakattack.py): fold in the PGD-k monotonicity table + correlation-decay figure.
- Round 3: reviewer pre-empts (Singla-Ge, Obfuscated-Gradients-again, confounds via partial corr).
