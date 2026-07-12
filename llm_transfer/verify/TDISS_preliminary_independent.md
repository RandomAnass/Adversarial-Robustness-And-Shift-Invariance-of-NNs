# T-DISS — preliminary INDEPENDENT check (before the harness post-pipeline finishes)

**Date 2026-07-12.** Computed by me directly from the completed `results/phase1.jsonl` (1170 rows)
and `results/phase2.jsonl` (920 rows, all harmful), NOT from the harness's `analyze.py` (still
running in the post-pipeline). I replicated `analyze.py`'s EXACT construction (n=920 harmful,
continuous r2 = ladder-min + loss_ref-rank tie-break, censored→2×max cap, AUROC with score=−R2,
primary partial(R2,r2|clean_refuse,M), judge-free R1b) so these numbers should match SUMMARY.json.

## The primary hypothesis FAILS (verdict: NEGATIVE / NO-GO as a positive result)

Harness convention (analyze.py:131): *higher R2 ⇒ more robust ⇒ LARGER jailbreak radius ⇒ expect
Spearman(R2, r2) POSITIVE.* The VLM analog (C1) is +0.78. Actual:

| metric | value | hypothesis | verdict |
|---|---|---|---|
| Spearman(R2, r2) | **−0.172** | expect + | wrong sign |
| Spearman(M, r2) | −0.158 | — | — |
| AUROC(−R2 → vulnerable) | **0.309** | expect >0.5 | below chance |
| **PRIMARY partial(R2, r2 \| clean_refuse, M)** | **−0.067** | kill needs **>+0.15 & sig** | **FAILS** |
| partial(R2, r2 \| M only) | −0.073 | — | — |
| Judge-free Spearman(R2, loss_ref) | −0.108 | expect + | wrong sign |
| Judge-free partial(R2, loss_ref \| clean_refuse, M) | −0.016 | — | ≈ null |
| Consistency null Spearman(C, r2) | −0.054 | expect ~0/anti | holds, but moot |
| AUROC(−C → vulnerable) | 0.354 | — | C also fails |

So R2 (the threat-matched ratio) does **not** positively predict the L2 jailbreak radius; it weakly
anti-predicts, and after controlling for M and base rate it is null-to-negative. The consistency
null holds, but there is **no positive-vs-null dissociation** because R2 itself fails.

## Most likely cause: predictor/attack THREAT-MODEL MISMATCH (design flaw, not necessarily a true negative)

- **Predictor M** (`tdiss_core.diagnostics`): the *first-token* margin logit(refuse-anchor) −
  logit(affirm-anchor) at position 1. R2 = M/‖∇M‖₂ is the certified radius for that **first-token**
  refuse/affirm decision.
- **Attack target r2** (`phase2`, PE-PGD): the minimum L2 embedding radius to make the model
  **generate a harmful completion** (48 tokens, teacher-forced affirmative continuation objective),
  success judged by Llama-Guard-3-8B over the generation.

These optimize **different objectives on different decision boundaries** (one-token margin vs
multi-token generation), so R2's certificate does not bound r2 and the ranking need not transfer.
A properly threat-matched test would define M on the **same** affirmative-continuation objective the
attack uses (M_cont = −loss of the affirmative target at δ=0; R2_cont = M_cont/‖∇M_cont‖) and
correlate R2_cont with r2. The current run does not do that.

## Consequence for the campaign

- **T-DISS does NOT yield a positive text-LLM analog of the C1 VLM result.** It is a NEGATIVE /
  INCONCLUSIVE result as instrumented.
- Honest options for the paper (decide after the full pipeline + adversarial verification):
  1. Report T-DISS as an **honest negative**: the frozen-encoder η/L→robustness transfer does not
     extend to generative-LLM *jailbreak radius* with a first-token margin — a scoped, publishable
     negative that sharpens the C1 claim (the dissociation is encoder-level, not decision-boundary-
     agnostic).
  2. Re-run with the **threat-matched continuation margin** R2_cont before making any positive OR
     strong-negative claim (a mismatch artifact cannot be ruled out with the current instrumentation).
- **The verified positive headline of the LLM/VLM paper is C1 (VLM tower dissociation), not T-DISS.**
  B2 contributes ρ_G-radius + η/L⊥ρ_G orthogonality + constant-classifier degeneracy.

## Still pending from the harness (do not preempt these — they add context even given the negative)

- **R2 Gauge test:** does the raw-M jailbreakability ranking move under the (c,b) logit gauge while
  R_q stays invariant? (gauge_sweep.py) — a methods point that stands regardless of R1's sign.
- **Masking battery** (200/400 steps, 5/10 restarts) + **GCG cross-check** (128 prompts): is r2 a
  real radius or attack-underoptimization? If a stronger attack shrinks r2 a lot, the −0.17 could
  partly be attack-strength noise. MUST check before finalizing.
- **summarize.py KILL booleans** + figures.

**Action:** when `results/SUMMARY.json` lands, confirm these numbers match, fold in gauge/masking/GCG,
then write the full adversarial `TDISS_verification.md`. Do not trust a positive summary if it
contradicts these independently-derived numbers — reconcile the sign convention first.
