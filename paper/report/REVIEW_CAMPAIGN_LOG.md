# Paper review campaign — progress log

**Paper:** `paper/report/main.tex` — *When Does Shift-Invariance Permit Adversarial Robustness? A Threat-Matched Margin-to-Lipschitz Theory, from Architecture to Data* (single author: Anass Al Ammiri). Venue: NeurIPS 2026 style. Currently 26 pp, compiles.

**Goal:** drive to submission-ready. Sequential review rounds, each a strong subagent that *verifies and modifies* the paper; author (me) verifies/reconciles between rounds (theory checked firsthand); end with a parallel NeurIPS-style panel. Do not stop between rounds. This log is the durable state — updated with progress + decisions so the campaign can run without pausing for check-ins.

**Resources**
- OpenReview calibration corpus: `paper/review_calibration/reviews/` (+ `fetch_calibration_reviews.py`) — for the final NeurIPS-style panel.
- Comparator papers (genre = ~2 headline theorems, proofs in appendix): `literature/comparison_4papers/`, `literature/foundational/`, `literature/invariants/`.
- Bib: `paper/report/references.bib` (57 entries) — literature round downloads/reads each.
- Diffusion working area + results: `paper/diffusion_robustness/`.

**Standing constraints:** commit as RandomAnass <anass.al-ammiri@tum.de>, no co-author/AI trailers, never touch global git config; never push without explicit request; keep the paper a clean scientific doc; honest scoped claims, no jargon-stacks/glued-words/em-dashes/"win", plain language, captions match figures; subagents unreliable for theory → author verifies proofs firsthand; keep one GPU free.

---

## Round plan + status

| # | Round | What it does | Status |
|---|-------|--------------|--------|
| R0 | §5 mechanism integration | Analyze coverage-vs-mixing control (#33), write the "dynamical + coverage-gated" paragraph + figure calibrated to it, recompile | 🔄 in progress (control done) |
| R1 | Coherence & cohesion | Whole-paper read after all the patching; fix narrative flow, drop weak parts/figures, add missing parts/figures/analysis | pending |
| R2 | Theory review | Verify the detailed theory AND its integration into paper+appendices vs comparator examples; author re-checks proofs firsthand | pending |
| R3 | Novelty & bookkeeping | No overclaims; proper citations; standard terms not invented names; claim-by-claim support check | pending |
| R4 | Literature | Go over every reference: download, read the relevant part (full paper if <20pp), fix each citation's accuracy, add missing citations | pending |
| R5 | First-time reader | Readability/understandability/flow for a fresh reader; interpretations clear | pending |
| R6 | NeurIPS-style panel | Multiple parallel calibrated reviewers (OpenReview corpus); synthesize scores + address | pending |

Between each round: I verify the subagent's edits (compile, spot-check claims/proofs), reconcile, and log decisions before starting the next.

---

## Results so far (diffusion direction, all committed)
- NQ1: diffusion obeys threat-matched η/L law (multi-seed +0.85 matched / −0.71 mismatched). In paper §5 + fig:diffusion.
- NQ2 / proper candidate: robust-overfitting delay (peak epoch Spearman +0.94; η/L collapse 0.48 baseline → ≤0.20 synthetic). To be written in R0.
- NQ3: τ (gradient conditioning) invariant → not the lever.
- NQ4: coverage threshold — synthetic hurts below ~100k unique (AA 0.35/0.36 < baseline 0.38). Being verified by control #33.
- Paper: title generalized; abstract+contributions+§5 paragraph+figure; full vicinal appendix (caveated). 26 pp.

---

## Decisions log (append-only)
- (init) Campaign launched. R0 gated on control #33 (10k/100k at 30% synth) to settle coverage-vs-mixing before writing the threshold claim.
- (R0) Control #33 result: benefit is coverage-gated and robust to mixing fraction (10k gives no gain at 30% *or* 70% synth: AA 0.382/0.364 ≈ baseline 0.383; 100k helps at both: 0.442/0.447). The sub-baseline *harm* is a mixing artifact (10k only < baseline at 70% synth). **Decision:** §5 claims "benefit requires sufficient vicinal coverage (robust to mixing)"; over-mixing harm noted as a fraction-specific corner. Do NOT claim "synthetic data hurts robustness" (overclaim). Proper candidate (robust-overfitting delay: peak epoch +0.94, η/L collapse 0.48→≤0.20) written as the leaned-on mechanism; vicinal appendix = its coverage-side candidate ingredient.
