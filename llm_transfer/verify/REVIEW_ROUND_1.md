# Review round 1 — reckoning (2026-07-13)

Three reviewers (main-track referee, first-time-reader, numbers-auditor) on the 8pp draft, plus my
own statistical tests of the referee's top challenges. Verdict: **the draft is a main-track Reject as
framed, and two headline claims do not survive scrutiny.** This is the honest state; the per-image VLM
result is the one solidly-powered positive.

## What my recomputation found (the decisive part)

| referee concern | my test | result | implication |
|---|---|---|---|
| W1: tower partial underpowered | partial(η/L, S \| is-AT), n=11, ALL methods + perm | Pearson-partial **+0.51 (perm p=0.15)**; Spearman-partial **+0.31 (perm p=0.39)** | **NEITHER is significant.** The stored/paper +0.51 is the raw-Pearson partial; the rank partial is +0.31; both p>0.15. Tower-level AT-controlled claim is underpowered — W1 is decisive. |
| W1: AT-only ranking | Spearman(η/L,S) among 4 AT towers | +0.80 @2/255, **+0.40 @4/255** | unstable across ε, n=4 |
| W2: per-image real? | paired bootstrap on Spearman(η/L,rad) − Spearman(SC,rad) per tower | fare2 +0.41[.33,.51], fare4 +0.37[.27,.47], tecoa2 +0.53[.44,.63] **all SIG** | **The per-image superiority is significant.** This is the solid leg. |
| W3: orthogonality real? | Spearman(η/L,ρ_G) per family | pooled −0.03; **sentiment +0.15 [+0.05,+0.24] SIG**; nli +0.00; safety −0.10 | **Orthogonality is a degeneracy artifact.** On the clean (sentiment) subset the axes are weakly POSITIVELY correlated, not orthogonal. |

## Referee (main-track) — Reject, leaning borderline. TMLR as-is.
- W1 tower panel n=11, robustness in 4 towers (2 hyperparam pairs of 2 methods); partial has no CI → my test confirms n.s.
- W2 per-image is "both predict, ours better" not a clean dissociation → but my test shows the superiority IS significant, so this is defensible if reframed as "orders it more than twice as strongly, significantly."
- W3 LLM leg is a grab-bag: Prop 1 (ρ_G certificate) is a TAUTOLOGY (ρ_G is defined as the min flipping edit); orthogonality is a null over mostly-degenerate data → my test confirms.
- W4 weak-attack is a single-paper rebuttal; "null under AA" is vacuous (all zeros, no variance to correlate).
- W5 novelty is a combination delta. W6 T-DISS reads as "doesn't transfer"; r2-stability unverified (masking crashed). W7 reproducibility + "AutoAttack" should be "APGD ensemble".
- 3 fixes: (1) fix power on the headline — expand to ≥6–8 independently robust towers OR commit fully to the per-image axis and retitle; (2) make the LLM leg ONE coherent claim (orthogonality on non-degenerate subset, demote Prop 1 to a definition, front the constant-classifier finding) or cut; (3) turn weak-attack into a phenomenon (find a setting where robustness VARIES) or fold into related work.

## First-reader — writing/clarity (all fixable)
- **Numeric error (K4): first-token jailbreak is −0.205, matched −0.167; the body prints BOTH as "−0.17". Fix first-token to −0.21.**
- η/L has two silent meanings (per-image ratio vs per-model ratio-of-means) — disambiguate (C4).
- ρ_G has 3 names (orbit-flip / excessive-invariance / oracle-robust); "orbit" never defined (C2).
- Pooled per-image +0.76 lives only in the Fig-2 caption, not the text (K2).
- One AI-tell: "It is worth asking" (S1). Define "arm", "oracle", "dual norm", "tower" at first use.
- No em-dashes, no "win". Structure/flow good. Abstract under-claims the negative (name it).

## DECISION IMPLIED (needs the user, but the path to MAIN is clear)
The honest core that SURVIVES: (a) the per-image VLM superiority (significant); (b) the weak-attack
caution; (c) two honest negatives (jailbreak transfer, constant-classifier degeneracy). To reach MAIN
(user's stated target) rather than TMLR, the required work is:
1. **VLM power**: expand the robust-tower panel to ≥6–8 independently robust encoders (more AT-CLIP
   families, robust ViTs) so the TOWER-level claim has real variance and a significant partial — OR
   retitle around the per-image axis and demote the tower number. GPU.
2. **LLM leg**: the orthogonality is dead on clean data. Replace it with a REAL contribution —
   **Angle A/E (gauge confound)** is the candidate (already queued). Report the constant-classifier
   degeneracy honestly as the excessive-invariance finding, demote Prop 1 to a definition.
3. **Weak-attack**: fold into related work as a caution, or find a robustness-varies setting.
4. Fix all first-reader items (numeric error, naming, conventions).

Next: run Angle A/E (to give the LLM leg a real result), and decide with the user whether to invest
GPU in expanding the robust-tower panel for a main-track VLM claim, or re-scope.

---

## PANEL EXPANSION RESULT (2026-07-13) — the tower claim is UNFIXABLE (second reckoning)

User chose "invest for main, VLM-only, cut LLM." Executed the referee's #1 fix: expanded the robust
panel 4 → 10 (added FARE4/TeCoA4 at ViT-B/32, B/16, ConvNeXt — 6 verified encoders, real backbone +
robustness variance, S_apgd 0.71–0.84). Recomputed the tower-level correlation on the 17-tower panel:

| test | value | verdict |
|---|---|---|
| Full panel Pearson(η/L, S), n=17 | +0.931 (perm p≈0) | strong but = robust-vs-nonrobust detection |
| partial(η/L, S \| is-robust) | +0.32 Pearson / +0.33 Spearman, **perm p=0.22 / 0.21** | **STILL not significant** |
| **AMONG 10 robust: Spearman(η/L, S)** | **+0.38 (perm p=0.28)** | **not significant** |
| AMONG 10 robust: Spearman(consistency, S) | +0.32 (perm p=0.37) | ≈ η/L! |

**The expansion did NOT rescue the tower claim, and revealed it is fundamentally unfixable.** Among
robust encoders η/L (+0.38) is no better than shift-consistency (+0.32), both n.s. η/L *detects* which
encoders are robust (the +0.93 full-panel) but does not *rank* robustness among robust encoders, and
neither does consistency. Going 4→10 robust towers moved the within-robust η/L from +0.80 (n=4, lucky
small sample) to +0.38 (n=10) — adding towers made it weaker, so more won't help. **The tower-level
dissociation does not exist among robust encoders; it is a robust-detector, honestly stated.**

**Consequence:** the paper's only powered, significant dissociation is the PER-IMAGE axis (η/L orders
the per-image radius, consistency far less; significant per tower). Caveat: per-image η/L→radius is
partly definitional (η/L is the first-order certificate of the radius), so the load-bearing surprise is
that shift-consistency — the field's invariance metric — fails to order the radius (+0.33) where η/L
succeeds. The per-image η/L→radius is +0.74–0.96 across all 10 robust towers (extending the claim from
4 to 10 towers, backbone-diverse). Weak-attack debunk stands as a caution.

**HONEST venue read:** "invest for main by powering the tower" has hit a wall — the tower claim can't
be made. The defensible paper is: per-image dissociation (10 robust towers) + weak-attack caution,
which is a strong TMLR fit or a borderline main-track submission on the per-image + negative-result
framing. This needs a user decision (the main-track premise failed).

---

## STRONGER-ANGLE HUNT (2026-07-13, user: "keep hunting") — 3 angles tested, no blockbuster

1. **Tower expansion (4->10 robust)**: FAILED. Among 10 robust towers Spearman(eta/L,S)=+0.38 ~ consistency
   +0.32, both n.s. eta/L is a robust-DETECTOR not a ranker. Fundamental (adding towers made it weaker).
2. **Double dissociation (invariance->nuisance, margin->adversarial)**: FAILED. Raw pattern looked great
   (SC->nuisance +0.72, SC->adversarial +0.10, eta/L->adversarial +0.82) BUT shift-consistency is
   SATURATED (0.963-0.988 across ALL 16 towers -- almost no variance) so it can't discriminate anything;
   the SC->nuisance is a clean-acc confound (clean->nuisance +0.965; partial SC->nuisance|clean = -0.65).
   Retention metric (nuis/clean) still dominated by clean acc (+0.90). Double dissociation does not hold.
3. **Certificate tightness**: eta/L is a TIGHT first-order ESTIMATOR of the per-image radius (median
   radius/(eta/L) ~ 1.1, IQR [0.87,1.60]) -- but ratio <1 on ~30% of images, so eta/L is NOT a valid
   certificate (PGD breaks it inside the bound); it's an accurate estimate, partly the expected Taylor
   behavior at low curvature. Interesting but partly definitional.

**HONEST BOTTOM LINE.** No hidden strong positive angle. The coherent, honest paper is a DIAGNOSTIC/
CORRECTIVE contribution: (a) shift-consistency is SATURATED (~0.98) across modern CLIP encoders and
predicts neither adversarial nor (clean-controlled) nuisance robustness -- the field's invariance metric
has no discriminative power; (b) a threat-matched margin eta/L estimates per-image adversarial robustness
attack-free (+0.95, tight); (c) the "invariance improves adversarial robustness" claims are weak-attack
artifacts. Together: invariance is the wrong lens for VLM adversarial robustness, the margin is the right
one. This is a solid corrective paper (borderline main / solid TMLR); further hunting = diminishing returns.
