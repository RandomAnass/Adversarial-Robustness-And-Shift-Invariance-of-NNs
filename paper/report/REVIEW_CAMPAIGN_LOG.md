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
| R0 | §5 mechanism integration | Analyze coverage-vs-mixing control (#33), write the "dynamical + coverage-gated" paragraph + figure calibrated to it, recompile | ✅ done (commit 2008582) |
| R1 | Coherence & cohesion | Whole-paper read after all the patching; fix narrative flow, drop weak parts/figures, add missing parts/figures/analysis | ✅ done (commit f42061b), verified |
| R2 | Theory review | Verify the detailed theory AND its integration into paper+appendices vs comparator examples; author re-checks proofs firsthand | ✅ done (commit 6d6eec8), author-verified |
| R3 | Novelty & bookkeeping | No overclaims; proper citations; standard terms not invented names; claim-by-claim support check | 🔄 in progress |
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
- (R1) Coherence pass done + verified (compile 27pp clean; de-dups confirmed non-destructive). **Deferred author's-call items from R1:**
  - [→R3] §6 Related work omits the synthetic-data-for-AT line (Wang2023/Gowal2021 used in body but not placed in related work). ADD a short paragraph (known: synthetic helps AT; ours: η/L accounting). **required**
  - [→R5] Abstract is one ~400-word block; the data-axis payoff lands only in the last 2 sentences — consider a light restructure for legibility.
  - [→R5/optional] MNIST-saturation caveat appears ~3x (§5 generality, §5 stat-power, App A.3) — consider consolidating.
  - [optional] fig:mechanism right panel (coverage threshold) could move to App A.5 if space gets tight; left panel (overfitting delay) stays in body. Keeping in body for now (27pp, appendix unlimited).
  - [noted] "diagnostic, not a trainable target" in ~6 places, each with a distinct role — keep.
- (R2) Theory audit clean (agent found no math error; author re-derived the load-bearing variation-norm no-gap firsthand — correct, about the max-margin *value* not the GD trajectory, so no overclaim). Actions: prop:split overfull fixed; **added Corollary cor:no-gap-var** (formalizes "provably margin-free"); bracket independent-α honesty clause; A.5 L-notation clause. 4 concerns closed. Concern #4 (numerical constants κ≈1.6–2.4, τ≈26, Pearson/Spearman) taken from committed scripts — not re-run this round; a numbers-audit could re-verify but low risk.
  - [→R3] Verify the newly-added cor:no-gap-var citations (lyu2020gradient, ji2020directional) are apt for "directional limit = min-variation-norm max-margin"; check the §4 "provably" reads honestly now.
- (R3) Novelty & bookkeeping pass done + verified (compile 27pp clean, no undefined/overfull). **Edits made:** (1) contributions bullet softened — "gradient descent self-symmetrizes" moved out from under "prove that" and reframed as observed-in-synthetic-test, since cor:no-gap-var proves only the max-margin *value* equality, not that GD selects the invariant optimum in the non-strictly-convex variation-norm case; (2) §5 data paragraph — added a one-line honesty clause scoping the diffusion axis: 4 doses span a narrow η/L band, so it confirms the *direction* of the threat-matched law, not a wide-range trace (title "from architecture to data" now honestly scoped in body); (3) terminology — unified the undefined "orbit-complete" (7×) to the Preliminaries-defined "orbit-closed"; (4) **CLOSED the R1-deferred related-work gap** — added a "Synthetic data for adversarial training" paragraph to §6 (gowal2021/rebuffi2021fixing/wang2023), framed as: known that generated data helps AT + reduces robust overfitting, ours = the η/L accounting + gauge/robust-overfitting confound demos, not a new method; added rebuffi2021fixing to bib. **Verified OK (no change):** cor:no-gap-var citations lyu2020gradient+ji2020directional are apt at claim level for "directional limit = max-margin" (the variation-norm identification is the corollary's own convex-norm/Jensen bridge — soft R4 flag); "provably margin-free" reads honestly (value-level, trajectory left open); "η/L not trainable" scoped as empirical+first-order (not an impossibility thm); vicinal App stays caveated. Kept coined-but-defined terms: threat-matched, gauge, margin-free, self-symmetrization, gradient-floor slack (τ≠data-cond-number in general), coverage-gated, vicinal. **[→R4] flags:** bispectrum "determines signal up to shift"/margin d^{-3/2} (line ~125) is uncited — add Kakarala/Bendory (PDFs in literature/invariants) + verify the d^{-3/2} number; "constant-function degeneracy flagged by tsuzuku2018lipschitz" (ratiodegen proof) — verify Tsuzuku actually flags this; variation-norm=directional-limit identification may want Chizat-Bach.
