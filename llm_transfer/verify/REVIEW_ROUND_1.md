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
