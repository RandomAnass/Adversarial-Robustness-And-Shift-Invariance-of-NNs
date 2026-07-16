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

---

## ANISOTROPY THEORY + NOVELTY (2026-07-14, agent + I verified by running the scripts)
**Provable? Conditionally YES, unconditionally NO.** On a quadratic margin M(δ)=M0+w^T δ+½δ^T H δ, the
L∞ attack's 2nd-order term is Q=½ sign(w)^T H sign(w) — depends on H and the SIGN of w only, NOT on the
gradient magnitudes, so NOT on anisotropy A=||w||_1/||w||_2 in general.
- **Naked claim FALSE**: generic H makes radius INCREASE with A (counterexample, verified verify_counterexample.py);
  isotropic H=-cI makes radius FLAT in A (verify_quadratic T3) -> the mechanism is NOT dimensional.
- **Conditional PROPOSITION TRUE**: if curvature is concave AND gradient-aligned (H=-c hat w hat w^T), then
  Q=-c/2 A^2 and r_inf = (eta/L1)(1 - c/2 (eta/L1)^2 A^2), strictly decreasing in A; looseness
  kappa_inf-1 propto A^2. Verified numerically to 4 decimals (verify_quadratic T2). **The empirical sign
  (-0.65, higher A -> less robust) is itself evidence robust CLIP encoders sit in the aligned-concave regime**
  (generic curvature reverses the sign).
**Novel? YES.** Nearest: Simon-Gabriel 2019 (||grad||_1~sqrt(d)||grad||_2, but dimension-vs-vulnerability,
not fixed-margin ranking), Chalasani 2020 (AT->sparse gradients, converse direction), GradDiv (opposite,
ensemble dispersion), Ross-Doshi (gradient MAGNITUDE reg). The fixed-eta/L residual-ranker framing is new.
**REAL-DATA MECHANISM: WEAK/UNCONFIRMED.** On the 10 robust encoders, Spearman(A, looseness eta/L1/r) =
+0.28 (n.s.); mean looseness ~1 (not >1 as concave curvature needs; radius grid is coarse). So the
anisotropy RANKING is solid (-0.65, jackknife-robust) but the curvature-looseness MECHANISM is not yet
confirmed on real encoders. **Definitive test still needed: HVP measure sign(grad M)^T H sign(grad M) per
encoder** (is it concave + gradient-aligned?). Honest paper framing: empirical finding + conditional
proposition (proven) + sign consistent with alignment; direct curvature-alignment confirmation = future work.

## CURVATURE-ALIGNMENT MECHANISM TEST (2026-07-14, run_curv_align.py per-tower, all 10 robust)
Measured curvature along the ATTACK direction q_align = sign(grad M)^T H sign(grad M) / ||grad M||_1.
- ALL 10 encoders CONCAVE along the attack (frac q<0 = 1.00, mean -55.5) -- the qualitative condition holds.
- BUT the mechanism is REFUTED: Spearman(q_align, S_apgd)=+0.03 (null) -- concavity does NOT rank robustness;
  Spearman(anisotropy A, q_align)=+0.53 (WRONG SIGN, theory predicted <0). The aligned-concave-curvature
  proposition does NOT manifest on real encoders.
- Anisotropy ranking SURVIVES the backbone confound: partial(A,S|is-L/14)=-0.62; within-backbone L/14 -0.40,
  non-L/14 -0.71. So the empirical A->robustness ranking is REAL (survives method + eta/L + backbone + jackknife)
  but its MECHANISM is OPEN (curvature story refuted; why anisotropy ranks robustness is unexplained).
- HONEST paper framing: gradient anisotropy is a cheap attack-free predictor that ranks robust encoders where
  eta/L cannot (robust empirical finding); the curvature proposition is a valid clean-case candidate but is NOT
  the real-encoder mechanism -> present as empirical + open mechanism, do NOT claim the theory explains it.

---

## PART 2 MECHANISM — RESOLVED (2026-07-15). "Why anisotropy ranks robustness" is no longer open.

The earlier "mechanism OPEN" note above is SUPERSEDED. Two results close it:

### (i) RobustBench n=30 replication — independent model family, strong signal
`llm_transfer/pilots/c1_tower/robustbench_val/{results.json,FINAL_REPORT.txt}`. On 30 OFFICIAL
RobustBench CIFAR-10 Linf models (ResNets/WRNs, not ViTs), with A=‖∇M‖₁/‖∇M‖₂ and APGD robust acc:
- **Spearman(A, robust) = −0.791 (p=2e-7)** over all 30; **−0.768 over the 29-model robust panel**
  (excluding the single non-robust `Standard` model — the fair "ranking-among-robust" number).
- Validity: my-APGD vs official-AutoAttack Spearman = +0.960. partial(A,robust|clean) = −0.766;
  partial(A,robust|η/L₁) = −0.647. Bootstrap 95% CI [−0.915,−0.562]; jackknife [−0.843,−0.768].
- η/L₁ control: +0.61/+0.57 (detects, ranks weakly) — exactly the "size detects, shape ranks" split.
- FIGURE for deck/paper: `paper/pitch/figures/robustbench_aniso.pdf` (real data, 2-panel).

### (ii) Mechanism = effective-dimension whole-ball margin deficit (verified firsthand, 4 scripts)
Verified by running `/tmp/.../scratchpad/aniso/step{6,7,9,10}.py` (numbers reproduced exactly):
- **Law: r ≈ (η/L₁)/(1+C·A)**, C≈2.65. The first-order certificate η/L₁ is only the leading term;
  a real attack additionally harvests the gradient's per-coordinate variation, collecting a deficit
  that scales like A=√(effective active dims) at matched per-coord fluctuation.
- step6: GAP vs m log-log slope **0.531** (√m=A law), Pearson(A,GAP)=0.99997; GAP linear in field-std
  (slope 1.03). step7: matched η/L₁ + matched energy, **Spearman(A, robust_radius) = −1.0**.
- step9: single-step ≈ multi-step deficit (Pearson(A,·)=0.9998 both) → the deficit is STATIC, collected
  in one gradient read; the "multi-step efficiency" hypothesis is DOWNGRADED.
- step10: Spearman(A,deficit)=+1.0 but **A-vs-q_align NULL (−0.03)** and q_align-vs-deficit NULL →
  the deficit is a TRANSVERSE effect (spread over A² coords), NOT the on-direction curvature. This
  REPRODUCES the real-encoder curvature refutation (q_align does not rank robustness) and explains
  why curvature was refuted yet A works.

### (iii) NOVELTY (answers "is that novel??") — YES, on three counts
1. Empirical: "gradient anisotropy A ranks adversarial robustness among already-robust models
   (negatively), on two independent families (CLIP + RobustBench), surviving clean-acc/η/L/backbone
   controls" — not in the literature (lit-scout found nothing).
2. Mechanism = RELAXATION of Simon-Gabriel et al. 1802.01421 (vulnerability ∝ ‖∇‖·√d under an
   equal-variance-per-coordinate assumption that FIXES A∝√d). We let A vary at fixed d and show it
   tracks robustness — the deficit is the beyond-first-order term their assumption suppresses.
3. Refutes the curvature/CURE (Moosavi-Dezfooli 2019) story as the RANKER: transverse magnitude-spread,
   not on-direction curvature. Metric collision to cite (different use): arXiv:2505.02360 (participation
   ratio PR₁~A² for catastrophic-overfitting DETECTION during training, not cross-model ranking).
HONEST CAVEAT: the synthetic separable-Gaussian-field model is a self-consistent stand-alone (bakes in
per-coordinate independence), NOT a first-principles derivation from CLIP geometry. Strong signal is
BETWEEN-encoder (C is a model-level property); within-encoder per-image partials are weak. Present the
mechanism as "proposed, internally consistent, refutes curvature" — not "proven from the architecture."

### (iv) BOUNDARY CONDITION (MNIST/Fashion pilot, honest negative)
Reanalysis of existing MNIST/Fashion AT cells (dec_L1/dec_L2 already logged): A does NOT rank robustness
there (Spearman +0.035 MNIST, −0.044 Fashion, both null). Cause: those cells are AT at a SINGLE ε,
varying only by shift-arm+width → narrow robustness band and A compressed to [1.95,2.88]/[4.33,5.43]
(vs A∈[18,35] where the law holds). The law needs a WIDE robustness range driven by training-strength
diversity. A proper AT-strength-sweep test on MNIST/Fashion is running to settle whether low input
dimension is a hard boundary or just needs the wider axis. η/L still predicts on both (+0.5), so the
DETECTION-level story holds on all families; only the anisotropy RANKING refinement is range-dependent.

---

## CROWN-JEWEL v0 — multimodal dissociation (2026-07-15, VERIFIED firsthand)
`llm_transfer/pilots/c1_tower/CROWNJEWEL_V0.md` + `run_crownjewel_v0.py`; results
`crownjewel_v0.json` + `crownjewel_v0_analysis.json`; figure `llm_transfer/paper/figures/crownjewel_v0.pdf`.
Zero-shot CLIP on ImageNet-100 val (n=1000, 10 encoders: 4 non-robust openai/laion + 6 robust
FARE/TeCoA), eps=4/255. I INDEPENDENTLY recomputed every headline from the raw per-tower JSON — all
match the agent's analysis exactly; sanity holds (non-robust S=0.000, all S<=clean, robust radius > non-robust).

VERIFIED NUMBERS:
- **Two-axis saturation**: shift-consistency SC mean 0.976 (sd 0.010, range 0.964-0.990); paraphrase-
  consistency PC mean 0.978 (sd 0.009, range 0.957-0.990). Robust acc S spans 0.00-0.66 (sd 0.29).
  BOTH invariances saturated; robustness is the only axis with spread.
- **eta/L1 predicts robustness**: cross-tower Spearman(eta/L1, S) = +0.869 [CI 0.47,0.99]; per-image
  pooled Spearman(eta/L1, radius) = +0.852 (n=720, tight CI) — the powered headline, proper radius metric.
- **Textual invariance cleanly dissociated**: Spearman(PC, S) = +0.113 [CI -0.83,0.79] ~ null.
- **Anisotropy A ranks robust towers by radius**: Spearman(A, radius | robust) = -0.714 (reproduces
  the parent A-ranks-robust-radius law on this panel).
- SC vs PC = +0.842 (visually-invariant encoders also tend to be paraphrase-invariant).
- HONEST CAVEAT (reported, not hidden): Spearman(SC, S) = +0.381 [CI -0.47,0.88] — NOT a clean null;
  on this small panel the 4 non-robust towers happen to sit slightly low in the tight SC band, so SC
  weakly CO-DETECTS AT. But CI spans 0 (non-significant), it is far below eta/L1 (+0.87), and SC does
  NOT carry the per-image robustness signal eta/L1 does. So the dissociation holds; SC is a weak (not
  null) MODEL-LEVEL co-detector here, PC is genuinely null.
- METHOD CAVEAT: S computed APGD-CE-only (agent added a backward-compatible `targeted=True` default to
  attacks.py, used False for speed) → S is a strong UPPER BOUND, slightly overestimates robust acc but
  preserves ordering (validated vs parent full-ensemble within a few points). The per-image RADIUS
  headline uses the proper DDN/radius metric, unaffected.

VERDICT: the parent thesis "invariance is not robustness" EXTENDS to the multimodal (shift + text +
images) setting. Both visual and textual invariance saturate across CLIP encoders; adversarial
robustness is a separate axis that eta/L1 predicts (per-image, powered) and neither consistency carries
(PC cleanly, SC weakly/non-sig). For the combined paper this is the multimodal generalization of the
saturation + per-image-dissociation headline. TO STRENGTHEN for main: bigger tower panel, full targeted
AA for S, more images; consider per-image paraphrase-consistency (not just model-level).
