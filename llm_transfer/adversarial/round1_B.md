# Round 1 — Literature Adversary report on lens-B designs (B1, B2, B3)

Adversarial audit of the three lens-B pilot designs (invariance/equivariance analogs in
LLMs vs adversarial robustness) against the literature, *before* any compute is spent.
Method: every load-bearing paper was DOWNLOADED and the relevant sections READ (not just
abstracts). PDFs are in `llm_transfer/adversarial/pdfs/`. Search fan-out covered arXiv /
OpenReview / ACL / Semantic Scholar via WebSearch, targeting the specific gaps each design
claims (prompt-consistency, format-robustness, option-order bias, paraphrase defenses,
consistency-training-for-safety, excessive-invariance / negation, semantic-entropy).

Priority applied throughout: the bar is ONE robust single-model run that stands alone at a
top venue, not an addendum to the vision paper. I killed nothing outright, but B3's central
gap is materially eroded by a 2026 paper and needs a hard re-aim; B1 and B2 survive with
required re-framing and added citations.

---

## Papers downloaded and READ (1-line finding each)

Verification of CITED, load-bearing papers:

- **2510.27062** DeepMind "Consistency Training Helps Stop Sycophancy and Jailbreaks" (Irpan,
  Turner, Kurzeja, Elson, Shah; Google, Oct 2025). READ all 19 pp (8 body + 11 appendix).
  **B3's characterization is CORRECT**: jailbreak eval is on FIXED template sets (ClearHarm,
  WildguardTest; "seen + unseen" only tests template *generalization*, App. A), there is NO
  GCG, NO embedding attack, NO adaptive attack, and NO margin/Lipschitz anywhere. The paper
  *explicitly* states its method requires "no adversarial optimization" (p.2) — an
  omission by design, exactly the FGSM-only regime B3 targets. Confirmed, not a misread.
- **2506.24056** "Logit-Gap Steering" (Li & Liu, Palo Alto Networks, v2 May 2026). READ pp.1-2.
  Refusal–affirmation logit gap at first decoded token is defined and validated as claimed
  (numerator η for B1/B3). CRITICAL NUANCE the designs miss: the authors themselves call gap
  closure "an internal consistency check, since our method optimises gap closure — NOT an
  independent predictor." B1/B3's "η is an independent predictor" claim therefore *requires*
  the out-of-sample / partial-correlation controls to be defensible; cite this hedge.
- **2402.09063** Schwinn et al. "Soft Prompt Threats" (NeurIPS 2024). READ pp.1-2. Embedding-
  space attack is exactly as B1/B3 use it (continuous δ on input-token embeddings, signed-
  gradient update, cheap, open-weights). Faithful.
- **2002.04599** Tramèr et al. "Fundamental Tradeoffs..." (ICML 2020). READ pp.1-2. Verified
  precisely: defenses vs sensitivity attacks *actively harm* invariance-attack robustness;
  they break certifiably-robust models with label-flipping perturbations the model is provably
  robust to; excessive invariance arises from overly-robust features. Note their framework
  uses an oracle O with a garbage class ⊥ — B2's deterministic-flip constructions are the
  right way to instantiate that oracle in text.
- **1811.00401** Jacobsen et al. "Excessive Invariance Causes Adversarial Vulnerability"
  (ICLR 2019). READ p.1. Verified: nets "too invariant to task-relevant changes," can change
  class-specific content without changing hidden activations. B2 accurate.
- **2101.00010** Sinha et al. "UnNatural Language Inference" (ACL 2021). READ pp.1-2. Verified
  EXACT number: "almost all (98.7%) [MNLI] examples contain at least one permutation which
  elicits the gold label," models even relabel-correctly under permutation. Caveat B2 must
  carry: this is on *encoder* NLI models (RoBERTa/BERT), not generative instruction-tuned LLMs.

Missing / preemption papers found and READ:

- **2605.28467** Shah, Brinkmann, Angell (NYU / TU Clausthal), "Mitigating Adaptive Attacks
  against Reasoning Models with Activation Consistency Training" (v1 May 2026). READ pp.1-12
  (full body + appendix). **THE most important finding of this audit — directly bears on B3.**
  A direct follow-up to 2510.27062 that DOES run an adaptive attack against consistency
  training (BCT + ACT): a per-target GRPO RL suffix attacker trained against the defended
  model, explicitly citing Nasr et al.'s call for adaptive attackers. Result is the OPPOSITE
  of B3's H2 for jailbreak: ACT holds near-100% defense win-rate under adaptive attack on 4/5
  models (Fig. 6), BCT "degrades substantially under adaptive attack" but does not uniformly
  collapse; for prompt-injection the picture is graded (ACT 37–63% win vs undefended ~0%, but
  Gemma-4-E4B-it collapses to 2–4% for both). They also add a CoT-prefill and a linear-refusal-
  direction mechanistic analysis. Their own limitation: "may be evaded by attacks not tested
  in our threat model, such as **white-box attacks with direct gradient access**."
- **2510.09023** Nasr, Carlini, Sitawarin, Schulhoff, Hayes, ..., Tramèr (OpenAI/Anthropic/
  DeepMind/ETH, Oct 2025), "The Attacker Moves Second." READ pp.1-4. The flagship "adaptive
  attacks bypass LLM defenses" paper: breaks 12 defenses to >90% ASR that reported near-zero;
  gives a general Propose–Score–Select–Update adaptive-attack framework (gradient / RL /
  search / human). Warns gradient-based token attacks "are still unreliable, we generally
  recommend attacks that operate in text space" — a caution against over-trusting embedding/
  gradient-only evidence in B1/B3. Does NOT itself break 2510.27062 (not among the 12), so
  B3's specific target survives, but the *thesis* B3 argues is now mainstream.
- **2502.10487** Beyer, Schuchardt, Schwinn, Günnemann (TUM), "Fast Proxies for LLM Robustness
  Evaluation" (Feb 2025). READ pp.1-2. Directly bears on B1's selling point: embedding-space
  attack ASR predicts full-attack-ensemble robustness at **r_p=0.87 / r_s=0.94** across 33
  models, 3 orders of magnitude cheaper. Double-edged: validates B1's "cheap proxy predicts
  robustness, no masking" premise, but means "a cheap forward/embedding proxy predicts LLM
  robustness" is ALREADY DONE. B1's novelty must be the *dissociation* (consistency does not,
  η/L does), not the proxy itself.
- **2503.01345** Fu & Barez (Oxford), "Same Question, Different Words: A Latent Adversarial
  Framework for Prompt Robustness" (LAP, Mar 2025). READ pp.1-2. Core insight is literally
  B1/B2's geometry: "worst-case prompts exhibit a drift in embedding space"; "poor-performing
  paraphrases exhibit larger Euclidean distances from the original prompt in hidden space
  despite semantic equivalence." Uses Schwinn-style latent perturbation + LAT to *train*
  paraphrase robustness. It CROSSES embedding-space geometry with paraphrase robustness, so
  B1's "no paper crosses these" is false as stated — but LAP is a training method, computes
  no margin/Lipschitz ratio and shows no consistency-vs-robustness dissociation. Must cite.
- **2510.14242** Hejabi et al. (USC), "Flip-Flop Consistency (F²C)" (Oct 2025). READ pp.1-2.
  Unsupervised consistency-training via majority-vote pseudo-label + representation alignment
  pulling minority variants to consensus = precisely B1's "orbit-marginalized / consistency-
  LoRA" arm, but published and off-the-shelf. Reports consistency+F1 gains, NEVER tests
  adversarial robustness. Ideal ready-made "perfect-consistency operator" for B1 to dissect.
- **2511.13494** Lee (Purdue), "Language-Guided Invariance Probing of Vision-Language Models"
  (LGIP, v2 Feb 2026). READ pp.1-3. **THE most important preemption for B2.** Measures per
  model an invariance error (similarity variation under meaning-preserving paraphrases) AND a
  semantic-sensitivity / positive-rate (whether meaning-changing flips — object/color/count —
  are down-weighted), and reports the invariance–sensitivity trade-off across 9 models,
  finding some (SigLIP) score flipped captions above human descriptions = excessive invariance.
  This IS B2's conceptual measurement — but for VLM image-text cosine similarity, NOT
  generative instruction-tuned LLMs, and NOT a *radius* (ρ_G) or a budget law (ε<ρ_G). B2 is
  not subsumed but its "first quantitative measure of excessive invariance / invariance-
  sensitivity trade-off in language models" claim is now overclaimed. Must cite and narrow.
- **2605.24535** Chen et al. (UTS/XJTU), "Steering Beyond the Support" (ICML 2026). READ p.1.
  A *defense* paper (adv-train on simulated jailbroken activations so safety-steering
  generalizes to unseen jailbreaks). Confirms B3's intuition that conditional/steering
  defenses fit known jailbreak classes and fail OOD, but computes no margin and runs no
  gradient adaptive attack vs consistency training. Background support for B3, not a preemption.

Also present in `pdfs/` and consulted: 2406.11717 (Arditi refusal-direction — verified,
supports B1/B3 low-D margin), 2403.00867 (Gradient Cuff — refusal-loss gradient landscape,
neighbor to the L denominator), 2412.06748 (Refusal Tokens — refusal calibration).

---

## DESIGN B1 — "Prompt Consistency Is Not Robustness"

**VERDICT: SURVIVES, needs-fix (re-frame novelty + add 3 citations).**

The transferable claim is real and the ingredients check out. The dissociation (consistency
does not order robustness; η/L does) is genuinely un-run on LLMs, and every cited paper is
characterized correctly. But two 2025 TUM/Oxford papers erode the framing, and the load-
bearing margin paper carries a self-caveat B1 must absorb.

Misread / overclaim to fix:
- The litsweep line "NO paper crosses [embedding-space geometry] with paraphrase robustness"
  is FALSE given **LAP (2503.01345)**, which crosses embedding drift with paraphrase
  performance, and given **Fast Proxies (2502.10487)**, which already shows a cheap
  embedding/prompt proxy predicts full-ensemble adversarial robustness at r_s=0.94. B1's
  contribution is NOT "a cheap proxy predicts robustness" (solved) and NOT "embedding drift
  relates to paraphrase quality" (LAP). It is specifically: (i) the *invariance/consistency*
  metric the prompt-robustness field reports is orthogonal-to-anti-correlated with adversarial
  robustness, while (ii) the *threat-matched* η/L predicts it, and (iii) they *dissociate* on
  the same models. Re-write "why standalone" around (i)-(iii) and cite LAP + Fast Proxies as
  the closest prior, positioning against them explicitly.
- Logit-Gap Steering (2506.24056) itself warns the gap is "an internal consistency check, not
  an independent predictor." B1's H2 ("η/L predicts robustness") only clears this bar via the
  partial-correlation-beyond-clean-accuracy and out-of-sample tests. Keep those as *primary*
  results, not robustness checks, and cite the hedge directly.

Missing papers to add: LAP (2503.01345), Fast Proxies (2502.10487), Flip-Flop Consistency
(2510.14242), and — as corroboration — the ShieldGemma-2B 20.7-pt format-sensitivity finding
in guardrail models (2511.22047).

Concrete protocol corrections:
- Replace the invented "consistency LoRA" arm (7) with the published **F²C (2510.14242)** as
  the concrete perfect-consistency / orbit-marginalized operator to dissect. It is exactly the
  group-average-projector analog, it is off-the-shelf, and using a published operator makes
  the "least-robust-despite-perfect-consistency" claim adversarially clean (no "you tuned your
  own strawman" objection).
- Given Fast Proxies + Nasr's "gradient attacks are unreliable, prefer text-space" caution:
  do NOT let the embedding-space radius be the sole strong attack. Keep GCG on the 200-item
  subset as a load-bearing (not optional) cross-check, and report the embedding-vs-GCG
  agreement as the anti-masking test — this is what makes the η/L-predicts-robustness claim
  survive the Nasr critique that will otherwise be the first reviewer comment.
- Kill criterion is well-set. Add a second kill: if η/L tracks robustness only because it
  restates the embedding-attack radius by construction (near-tautology), the partial
  correlation controlling for the radius itself must stay > 0. State this.

The MMLU-margin instantiation is sound; the class-logit-gap margin is clean and the gauge-
free rescaling check is a genuine differentiator from LAP/Fast-Proxies. This is the strongest
of the three designs.

---

## DESIGN B2 — "The Orbit-Flip Radius: Excessive Invariance in LLMs"

**VERDICT: SURVIVES, needs-fix (narrow the novelty claim, add LGIP, tighten the oracle).**

All three cited backbone papers (Tramèr 2020, Jacobsen 2019, UnNatural LI) are verified
accurate, including the 98.7% figure. The ρ_G radius + ε<ρ_G budget law is a genuine
formalization that the NLP literature does not have. But a Feb-2026 paper now occupies the
adjacent measurement space and forces a novelty re-scope.

Misread / overclaim to fix:
- "The first quantitative, model-agnostic measure of excessive invariance in LLMs... the
  first evidence that the Tramèr trade-off governs instruction-tuned LLMs" is now OVERCLAIMED.
  **LGIP (2511.13494)** already measures, per model, invariance error under meaning-preserving
  paraphrases AND sensitivity to meaning-changing flips, and reports the invariance–sensitivity
  trade-off across 9 models — the Tramèr picture, instantiated for language-conditioned models.
  B2's true, defensible novelty is narrower and must be stated as such: (a) *generative,
  instruction-tuned* LLMs (LGIP is frozen VLM image-text cosine), (b) a metric **radius** ρ_G
  in edit / embedding distance (LGIP has an error rate, not a minimal-flip distance), and
  (c) the formal **budget law** ε<ρ_G and Proposition-rhoG empirical check (LGIP has neither).
  Re-write the "why standalone" paragraph around (a)-(c) and cite LGIP as concurrent prior.
- "None of the NLP failure literatures unifies word-order / negation / over-refusal under one
  quantity" is still fair — LGIP does not unify them and does not touch over-refusal or
  generation-level refusal. Keep the unification claim; drop the "first measure of excessive
  invariance in language models" claim.

Missing papers to add: LGIP (2511.13494) — mandatory; LAP (2503.01345) as the embedding-drift
neighbor (so ρ_G-in-embedding-space is positioned against LAP's "worst-case-paraphrase drift");
and the VLM-robustness lineage LGIP cites (Winoground, ViLP) only if a related-work paragraph
needs them.

Concrete protocol corrections:
- The single biggest risk is the ORACLE. Tramèr's framework requires a reliable label oracle
  with a garbage class; B2's plan to "cross-check meaning-change with deberta-v3-zeroshot NLI"
  is weak — an NLI model is itself an excessively-invariant LLM (that is the whole point of
  UnNatural LI), so using it as the oracle risks circularity. Fix: anchor ρ_G ONLY on
  *deterministic* oracle flips (negation insertion, antonym swap, harmful↔benign rewrite)
  where the label change is definitional, and use the NLI model *solely* as a paraphrase-
  validity filter on the invariance side, never as the flip oracle. State this separation
  explicitly; it is the difference between a credible ρ_G and a contaminated one.
- The "trade-off slope" needs enough invariance comparison points. The within-model
  decoding-dose knob (paraphrase-marginalization strength) is the right fix and should be the
  PRIMARY axis (a clean within-model ρ_G(dose) curve), with cross-checkpoint points as
  secondary — this avoids a between-model confound (different checkpoints differ in more than
  invariance) that a reviewer will flag.
- H2 (oracle-robust radius ≤ ρ_G on ≥95% of items) is the Proposition-rhoG empirical test and
  is the paper's certificate contribution. Keep it front-and-center; it is what LGIP cannot
  claim.

Compute is modest (mostly forward-pass), so this is a cheap, high-novelty-per-GPU-hour design
once the oracle is de-circularized.

---

## DESIGN B3 — "Invariance Helps Only Under Weak Attacks: Adaptive-Attack Audit of
Consistency-Trained LLM Safety"

**VERDICT: NEEDS-FIX (hard re-aim) — as written, half-preempted; the pivot below saves it.**

B3's specific characterization of 2510.27062 is CORRECT (verified: no adaptive attack, no
GCG/embedding, no margin, in all 19 pp — by explicit design). But B3's *broader gap* — "no
paper tests whether consistency-imposed safety survives a threat-matched adaptive attack" —
is NO LONGER OPEN. **2605.28467 (May 2026) already runs an adaptive attack (a GRPO RL suffix
attacker) against BCT and ACT**, and its result CONTRADICTS B3's central hypothesis H2:
consistency training (ACT especially) *largely survives* the adaptive attack in the jailbreak
setting on 4/5 models. This is precisely B3's own stated Kill condition ("if the consistency
advantage survives the adaptive threat-matched attack... the transfer fails").

This does not kill B3, but the current design would, at best, partially re-run 2605.28467 and,
at worst, be scooped and refuted before it starts. The pivot: B3 must stop claiming the
adaptive-attack gap and instead claim the THREE things 2605.28467 and 2510.09023 explicitly
leave open, all of which are exactly the vision paper's transferable contribution:

1. **The white-box / gradient threat-matched attack.** 2605.28467's attacker is an RL suffix
   attacker; its own Limitations flag "white-box attacks with direct gradient access" as
   untested, and Nasr (2510.09023) recommends text-space but leaves gradient attacks as an
   open axis. B3's embedding-space attack + adaptive co-optimization of the wrapper against
   the *consistency objective itself* is the missing gradient-threat-matched piece. This is a
   real, un-run adaptive attack, not a re-run of the RL attacker.
2. **The margin/Lipschitz predictor.** NEITHER 2510.27062, 2605.28467, NOR 2510.09023 reports
   any η, L, or η/L. B3's genuine contribution is the FORWARD-PASS diagnostic: does the
   refusal-margin-to-embedding-sensitivity ratio η/L predict which consistency-trained
   checkpoint survives which attack, and does the imposed-consistency dose anti-predict it via
   margin collapse. That is untouched and is the paper.
3. **The dose-response mechanism + degeneracy.** 2605.28467 trains one BCT and one ACT
   checkpoint per model, not a consistency-*dose* sweep, and does not connect survival to
   margin collapse or to over-refusal (the constant-classifier degeneracy). B3's dose knob +
   the η-collapse-and-over-refusal story is the mechanistic layer nobody has.

Misread to fix:
- The claim in B3's gap section "No paper tests whether consistency/invariance-imposed safety
  survives a threat-matched adaptive attack" must be DELETED and replaced with an honest
  statement: "2605.28467 tests an RL-suffix adaptive attack and finds ACT largely survives in
  the jailbreak setting; we (a) add the gradient/embedding threat-matched adaptive attack it
  leaves open, and (b) are the first to ask whether a forward-pass margin-to-sensitivity ratio
  predicts survival, and whether the consistency dose anti-predicts it via margin collapse."
- H2 as written ("the advantage over the base model shrinks toward zero / inverts") is now
  LIKELY FALSE for ACT in jailbreak given 2605.28467. Re-scope H2: the advantage may persist
  under the RL attacker but (hypothesis) is governed by η/L, not by the consistency level —
  i.e., high-dose survives only when it did not collapse the margin. If ACT survives *because*
  it preserves a large refusal margin (2605.28467's linear-refusal-direction result is
  consistent with this), that is a POSITIVE confirmation of the η/L law, not a refutation of
  the paper. Frame the win as "η/L explains survival," making the paper robust to either
  outcome. This also neutralizes the Kill criterion, which currently makes the whole paper a
  coin-flip on one uncertain empirical inversion.

Missing papers to add (mandatory): 2605.28467 (must be the central engaged work, not
2510.27062 alone), 2510.09023 (the adaptive-attack-evaluation standard B3 must meet), and
2605.24535 (steering defenses fail OOD — supports the mechanism). Fast Proxies (2502.10487)
and the Nasr text-space caution both mean B3's embedding-only evidence needs the GCG cross-
check to be credible — keep GCG load-bearing despite the compute cost.

Standalone viability: with the pivot to (margin-predictor + gradient-threat-matched adaptive
attack + dose/degeneracy mechanism), B3 becomes a distinct, top-venue-credible paper that
*engages* rather than *ignores* the 2026 follow-up. Without the pivot it is a scooped re-run.
Of the three designs, B3 is the highest-risk and needs the most re-writing before compute.

---

## Cross-cutting corrections (apply to all three)

- The safety-side literature moved fast: 2605.28467, 2510.09023, 2503.01345, 2502.10487, and
  2511.13494 all post-date the litsweep's framing and each occupies adjacent ground. The
  common fix is the same: the vision paper's *unique* transferable object is the **threat-
  matched margin-to-Lipschitz ratio η/L as a forward-pass diagnostic and the consistency-vs-
  robustness dissociation** — NOT "cheap proxy predicts robustness" (Fast Proxies), NOT
  "embedding drift relates to paraphrase quality" (LAP), NOT "measure invariance vs semantic
  flips" (LGIP), NOT "adaptive attack vs consistency training" (2605.28467). Anchor every
  design's novelty on η/L + the dissociation and cite the neighbors explicitly.
- Nasr (2510.09023) is now the evaluation standard. Any B1/B3 robustness claim resting on the
  embedding-space attack alone will draw the "you didn't run a strong adaptive attack" comment.
  Keep GCG and the adaptive co-optimization load-bearing, not optional.
- Logit-Gap Steering's self-caveat (gap is a consistency check, not an independent predictor)
  means the partial-correlation-beyond-clean-accuracy and out-of-sample tests are the
  load-bearing evidence for "η/L predicts," across B1 and B3. Elevate them to primary results.
