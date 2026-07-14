# Two-paper audit + combined-story synthesis (2026-07-14)

Four parallel agents audited Paper A (vision/CIFAR, `paper/report/main.tex`) and Paper B (VLM,
`llm_transfer/paper/main.tex`); I verified their load-bearing claims. Verdicts below.

## Paper A — THEORY (verified: agent ran verify_sandwich.py, re-derived identities, checked cites)
- **prop:sandwich (two-sided bracket η/L ≤ r₂ ≤ η/α, κ=L/α)** — VALID + genuinely (modestly) novel: a
  deterministic per-classifier converse, distinct from Tsuzuku (one-sided lower bound) and Cohen
  (worst-case-over-classifiers). **CAVEAT (load-bearing for Part 2):** α is a *path-secant* constant,
  **near-tautological for a general trained network**; an a-priori certifiable α exists only for the
  linear and power-spectrum-cone cases. The "two-sided bracket" headline is fully rigorous only there.
- **thm:lazy-cluster (no min-norm gap on orbit-closed data)** — VALID (numerically confirmed) + novel
  as a *degeneracy* result, not subsumed by the Elesedy/Tahmasebi invariance-generalization line.
  Smooth-activation only; bare-ReLU open (correctly flagged).
- **thm:A** (invariant margin = DC separation), **cor:C** (r₂≥η/L), **prop:split** identities:
  CORRECT but RE-DERIVATIONS (Ge 2021, Hein/Tsuzuku, Euler/Soudry), correctly credited by the paper.
- Bottom line: theory is honest and correct; the two novel results are **modest** (elementary converse
  + honest degeneracy lemma). The paper's weight is empirical.

## Paper A — EMPIRICAL (audited with the SAME skepticism that broke Paper B — and it applies)
- **The headline dissociation has the SAME confound as Paper B.** "Consistency anti-predicts robustness
  (−0.88)" under AT is n≈4–8; **collapses to −0.15 (NS) when the exact-cyclic arm (consistency=1.0 by
  construction, a saturated metric) is removed**; the paper itself concedes the capacity-matched-arms
  value is −0.43 (NS), and the exact-cyclic arm's low robustness is a margin/clean-accuracy collapse.
  Same saturated-metric + clean-accuracy confound as the VLM tower claim.
- **η/L vs r₂ = +0.998 is near-definitional** (first-order Taylor of the radius); paper admits it.
- **ImageNet-100** (clean acc flat, η/L predicts +0.90) is the confound-free check, BUT n=8, no CI/perm
  — underpowered, same regime as VLM n=11.
- **Weak-attack artifact** — cleanest, but LOW NOVELTY (Athalye 2018).
- **Graded anti-aliasing** (+0.013, n=40, CI) — solid, small.
- **Per-sample margin↔gradient SIGN-FLIP under AT** (−0.5 standard → +0.5 AT, across 36 models) — the
  **MOST NOVEL and best-powered** single finding, non-definitional. Underused.
- **NOVELTY THREAT: CLEVER (Weng et al. ICLR 2018)** — "first attack-independent robustness metric,"
  margin÷gradient-norm. Directly preempts the attack-free-η/L framing; must cite+distinguish in BOTH papers.
- **TWO FLAGGED NUMBERS to verify against source (in Paper A, lines 359/685):** Saha "budgets up to
  192/255" (192/255 = 0.75 is a physically odd L∞ adversarial budget; agent found no such budget in
  Saha) and the reproduction "FGSM 28.5%" of Wang's arch (agent says Wang's own FGSM is 65–85%, so
  "reproduce" may be the wrong word). I could not fetch the full Saha/Wang PDFs to confirm/refute —
  **user should check these against their own source/experiment logs; if wrong they read as fabricated.**

## Paper B — VLM (novelty + combine; correctness already audited)
- **R1 SATURATION** (SC 0.963–0.988 across 16 encoders, no predictive power beyond clean acc) —
  **the standout: genuinely new, unscooped.** Pre-empt "Lost in Translation" 2404.07153 (CLIP fails ~40%
  at *subpixel/representation-level* shifts — a different metric; our saturation is integer-pixel+top-1).
- **R2 per-image** — foundation-model instance of Paper A's per-sample certificate; partly definitional.
  (Numeric reconcile: agent recomputes median radius/(η/L) ≈ 1.57, not 1.1 — check the pipeline grid.)
- **R3 weak-attack** — same phenomenon, second domain (Paper A debunks the SAME target Wang 2510.16171).
- **R4 tower detector-not-ranker** — honest limitation, weakly novel. → this is exactly Part 2's puzzle.
- **CITATION ERRATA (verified):** (1) `towergoverns`=2407.11121 MISATTRIBUTED (it's Bhagwatkar et al.
  "Towards Adversarially Robust VLMs"); re-source the tower-governs claim to FARE 2402.12336. (2)
  `singlage` author order: **Ge first**, not Singla (2103.02695).

## PART 2 — the ranking answer (what η/L misses), and it UNIFIES the papers
η/L is the **first-order (locally-linear) limit**. Among robust models it fails to rank because robust
radii are large and leave the locally-linear regime; the **input curvature over the ε-ball ≡ the
sandwich condition number κ = L_ball/L_point** is what orders them, and η/L (the *lower* arm) is provably
blind to it. This is the direct next step of Paper A's own sentence (main.tex:385: η/L is "the
small-curvature limit of the curvature-corrected bound of Moosavi-Dezfooli 2019"), and Paper A's
prop:sandwich is the object that answers it. Empirical fingerprint already in the data: among the 10
robust towers gradient anisotropy L1/L2 ranks S_apgd at **−0.64 (p=0.048)** while η/L is +0.38 (n.s.).
Novelty (verified): the curvature-vs-point-gradient idea is known in PIECES (CURE 1811.09716,
Finlay-Oberman 1905.11468, CLEVER 1801.10578, Qin 1907.02610) but **never assembled for RANKING
already-robust models, nor tied to invariance/CLIP.**

### PART 2 RESULT (run_ranking_diag.py + anisotropy check) — ANSWERED, and NOT curvature
- **Curvature hypothesis: NEGATIVE.** Random-δ ball-Lipschitz gives κ≈1.00 for the 6 new robust towers
  (gradient flat over the ε-ball in random directions), so η/L_ball (+0.26) ≈ η/L_point (+0.30), and
  L_ball / curv / κ do NOT rank (all n.s.). Caveat: this tests RANDOM directions; the PGD-path L_ball
  (agent's rank_probe.py) is untested, but the random-δ negative is suggestive that curvature-in-
  random-directions is not the answer.
- **Gradient ANISOTROPY: POSITIVE and solid.** The gradient SHAPE ‖∇M‖₁/‖∇M‖₂ (= how spread the
  margin-gradient is across input dims) ranks robustness among the 10 robust encoders:
  **Spearman(anisotropy, S_apgd) = −0.648 (p=0.043)**; survives controlling for the FARE-vs-TeCoA method
  (**partial | is-TeCoA = −0.95**); **adds beyond η/L_point (partial = −0.83)**; **jackknife drop-1 stays
  [−0.73,−0.52]** (not an outlier artifact). Lower anisotropy (concentrated gradient) ⇒ more robust —
  consistent with the L∞ threat exploiting spread gradients.
- **THE ANSWER to "detects but can't rank":** η/L uses the gradient MAGNITUDE (‖∇M‖₁) and detects
  robust-vs-non-robust; it ignores the gradient SHAPE (anisotropy ‖∇M‖₁/‖∇M‖₂), which is what ranks
  among robust encoders. Two encoders with equal η/L differ in robustness by their gradient concentration.
  Novel (agent lit-check found nothing on gradient-anisotropy ranking robust models), non-definitional
  (a gradient-shape quantity, not the margin/radius), and a clean NEW positive contribution.
- Caveat: n=10, p=0.043 borderline; jackknife-robust but a larger robust panel would strengthen it.
  Mechanism (why concentrated gradients resist L∞) needs a one-paragraph argument + a synthetic check.

## THE COMBINED MAIN-TRACK STORY (recommended)
**One paper.** Paper A (vision) is the spine — it owns the theory (η/L criterion, the two-sided bracket,
the Ge-collapse recovery, diagnostic-not-target) and the powered CIFAR/ImageNet empirics. Add:
1. A **"frozen foundation encoders"** section headlined by **R1 saturation** (the field's invariance
   metric is saturated + non-predictive on a CLIP bank — the freshest new claim, cross-domain), with
   **R2** as the per-image certificate transferring to learned representations and **R3** folded into the
   shared weak-attack section as a same-target second-domain replication. **R4** = honest limitation.
2. **PART 2 as the new theory→empirics contribution that CLOSES R4:** the **gradient anisotropy
   ‖∇M‖₁/‖∇M‖₂ ranks robust encoders** (−0.65, survives method + η/L controls, jackknife-robust) where
   η/L only detects. The through-line: **η/L uses the gradient MAGNITUDE (detects robust-vs-not); the
   gradient SHAPE / anisotropy ranks among robust models.** (The naive sandwich-κ/curvature route was
   tested and is negative in random directions — report honestly; the anisotropy is the real signal.)

Multi-contribution: (i) the invariance metric is saturated/confounded (both domains, the honest negative);
(ii) the weak-attack artifact (both domains); (iii) the two-sided bracket theory; (iv) **NEW: gradient
anisotropy ranks robust models** (η/L detects, gradient-shape ranks); (v) the per-sample sign-flip
diagnostic. That is a main-track-shaped multi-contribution paper.

## ACTION ITEMS
- Add + distinguish **CLEVER (Weng 2018)** in both papers (the attack-free-metric prior).
- **Verify/fix the two flagged Paper-A numbers (192/255, 28.5%)** against source — potential integrity issue.
- Fix VLM citation errata (2407.11121 misattribution; Ge author order).
- Promote the **per-sample sign-flip** (Paper A's most-novel finding) to a headline.
- Reconcile the per-image tightness ratio (1.1 vs 1.57).
- If Part 2's experiment confirms κ ranks robust encoders → that becomes the paper's strongest new positive.
