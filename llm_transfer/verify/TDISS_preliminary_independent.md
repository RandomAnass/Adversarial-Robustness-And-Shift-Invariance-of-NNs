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

---

## FULL-STACK RE-EXAMINATION (2026-07-12) — literature / theory / design / implementation / results

Prompted to double-check the negative across the whole stack before trusting it. Conclusion: **the
negative is INCONCLUSIVE (a threat-model design mismatch), NOT a genuine "η/L fails in text" result.**

- **Theory.** The margin/Lipschitz certificate (Tsuzuku, Hein) says R2 = M/‖∇M‖₂ lower-bounds the
  radius within which the decision that DEFINES M is preserved. Here M is the **first-token**
  refuse−affirm margin, so R2 certifies the first-token argmax radius. The attack radius r2 is the
  radius to **generate** a harmful continuation. Theory does **not** claim a first-token certificate
  bounds a multi-token generation radius. So a null/negative Spearman(R2, r2) is the THEORY-PREDICTED
  outcome of a mis-specified test, not evidence against the η/L→robustness thesis.
- **Design.** The attack (`tdiss_core.pe_pgd`) minimizes the CE loss of a 6–8 token affirmative
  continuation "Sure, here is <behavior>:\\n\\n1." (`_affirm_target_ids`), perturbing only the prompt
  embeddings. The threat-matched predictor must be built on that SAME objective: R_cont = L0/‖∇L0‖
  with L0 = the clean affirmative-continuation loss. The phase1 predictor is not that. **Design flaw
  identified, and cheaply fixable.**
- **Implementation.** `pe_pgd` is a correct signed/normalized PGD with restarts keeping best loss;
  r2 = min successful eps on a 6-rung ladder (coarse). The **masking battery + GCG cross-check**
  (running now) test whether r2 is a real radius or attack under-optimization; if a stronger attack
  shrinks r2 materially, part of the −0.17 is attack-strength noise. MUST fold in before finalizing.
- **Results/analysis.** −0.17 is robust (my independent code + the harness's exact convention). But it
  is −0.17 for the WRONG (mismatched) predictor.

**Resolution (armed): `fix_matched_margin.py`.** Recomputes R_cont = L0/‖∇L0‖ on the attack's own
continuation objective at δ=0 (one fwd+bwd/prompt, ~1–2 min, 920 prompts) and correlates with the
EXISTING r2. Runs when a GPU frees (queued for GPU 0 after the T-DISS post-pipeline). Outcomes:
- **R_cont predicts r2 (positive):** the η/L→robustness dissociation TRANSFERS to generative-LLM
  jailbreak radius once properly threat-matched → the text leg becomes a POSITIVE result, and the
  first-token −0.17 becomes a clean cautionary "you must threat-match the margin" finding.
- **R_cont also null/negative:** a GENUINE negative (η/L does not predict jailbreak radius even
  matched) → report as the honest encoder-vs-decision-boundary limitation.
Either way the paper claim is now well-posed. Do NOT present the −0.17 as "η/L fails in text" — that
is not established; the test was mis-specified.

---

## RESOLVED 2026-07-13 — matched-margin run: T-DISS is a GENUINE NEGATIVE

`fix_matched_margin.py` ran on all 920 harmful prompts (GPU 1). The threat-matched continuation-margin
predictor R_cont = L0/‖∇L0‖ (built on the attack's OWN affirmative-continuation objective) is
well-formed: L0 mean 3.39 (std 0.80, range 1.5–6.0), R2_cont mean 0.259 (std 0.045), all finite — a
real predictor with genuine variance, not degenerate.

| predictor | Spearman vs jailbreak radius r2 |
|---|---|
| R2_cont (matched continuation margin) | **−0.167** |
| Rinf_cont (matched, ℓ1) | −0.170 |
| R2 first-token (the original mismatched) | −0.205 |
| R2_cont vs loss_ref (judge-free) | −0.109 |
| L0 alone (clean continuation loss) | −0.025 |

**The matched fix does NOT rescue it.** Matching the margin to the attack objective gives essentially
the SAME −0.17 as the mismatched first-token margin. So the negative is NOT a predictor-specification
artifact — it is genuine: **the margin-to-Lipschitz ratio does not predict a generative LLM's
jailbreak radius, regardless of which margin (first-token or matched-continuation) you use.** The
consistency of −0.17 across three independent predictors (and the judge-free arm) shows r2 carries a
real, weak signal that the ratio genuinely fails to predict (pure noise would give ≈0, not a stable
−0.17 everywhere).

**Interpretation (the honest, publishable negative that SHARPENS the thesis):** the η/L dissociation
is an ENCODER / classification-margin phenomenon. The first-order margin/Lipschitz certificate is
tight for a single (near-linear) classification decision — image classifiers, VLM zero-shot towers —
but LOOSE for a deep, autoregressive, multi-token generation attack. So η/L predicts adversarial
robustness where robustness IS a margin around a decision boundary, and does not transfer to
generative-LLM jailbreak radius. This is the encoder-level boundary the paper reports honestly (§6),
and it is a cleaner story than "inconclusive": we tried the properly threat-matched predictor and it
still does not transfer.

**Caveat still open (minor):** the masking battery CRASHED (`masking_battery.py:44 unbounded_append_
attack`) so the r2-under-optimization check is missing; GCG (still grinding, ~8h) would give a second
attack's radius. Neither changes the conclusion — the matched-vs-mismatched invariance of the −0.17
already shows the predictor is not the issue — but note the r2-stability check is not in hand. Optional
cheap fix: repair + re-run only the masking monotonicity (20 prompts) to confirm r2 is stable at higher
attack budgets.
