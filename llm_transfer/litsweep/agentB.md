# Agent B literature sweep — invariance/equivariance analogs in LLMs vs adversarial robustness

Lens: paraphrase / prompt-format / template / token-order / positional-shift (RoPE) invariance in LLMs, and
whether MEASURED or IMPOSED invariance PREDICTS or ANTI-PREDICTS adversarial robustness — the transfer of our
paper's central dissociation (shift-consistency does not order robustness; anti-predicts under adversarial
training; the exactly invariant operator is least robust via margin collapse; a threat-matched margin-to-Lipschitz
ratio η/L predicts instead; excessive invariance is its own attack surface).

Verdict up front: the two literatures needed for the transfer BOTH exist and are large, but they have never been
crossed. (i) A big "prompt/format/order/paraphrase sensitivity" literature MEASURES invariance. (ii) A big
"jailbreak / adversarial-prompt robustness" literature MEASURES robustness. (iii) A separate "excessive-invariance"
literature (word-order-invariant NLI, negation insensitivity, over-refusal) shows imposed invariance is a failure
mode. NO paper puts an invariance METRIC and an adversarial-robustness metric on the SAME models and reports the
SIGN of the correlation, and none frames a threat-matched margin-to-Lipschitz ratio as the quantity that predicts.
The excessive-invariance / orbit-flip trade-off (Tramèr 2020) is proven in vision but not instantiated or measured
in instruction-tuned LLMs. All three transfer targets are open.

Legend: [COVERS] gives us the ingredient / confirms an analog is measurable; [BLOCKS] would kill a candidate;
[LEAVES-OPEN] is a gap we can take.

---

## A. Measuring invariance in LLMs (the shift-consistency analog)

1. **Sclar, Choi, Tsvetkov, Suhr — "Quantifying LMs' Sensitivity to Spurious Features in Prompt Design"
   (FormatSpread), ICLR 2024. arXiv:2310.11324.**
   Semantically-equivalent prompt-format changes move accuracy by up to 76 points (LLaMA-2-13B, few-shot);
   persists with scale, more shots, instruction tuning. FormatSpread = cheap search over the format orbit reporting
   the performance interval, i.e. an INVARIANCE metric (spread = 1 − consistency).
   [COVERS] the prompt-format consistency metric = shift-consistency analog. [LEAVES-OPEN] never related to
   adversarial robustness; treats spread as noise, not as a robustness predictor.

2. **Zheng et al. — "Large Language Models Are Not Robust Multiple Choice Selectors," ICLR 2024. arXiv:2309.03882.**
   Option-order permutation shifts accuracy 13–75% via selection/token bias; PriDe debiases by permuting options.
   [COVERS] the token-PERMUTATION-group analog of the cyclic shift group; permutation-averaging (PriDe) = the
   group-average projector applied to MCQ. [LEAVES-OPEN] never linked to adversarial vulnerability or a margin.

3. **Voronov, Wolf, Ryabinin — "Mind Your Format," 2024. arXiv:2401.06766.**
   Template choice can drop strong models to random-guess; best templates do not transfer across models; TEMPLATE
   ENSEMBLES (averaging predictions over templates) recover average performance — the orbit-average predictor.
   [COVERS] template-invariance metric + orbit-averaging as a defense. [LEAVES-OPEN] robustness not tested.

4. **"The Order Effect: Prompt Sensitivity to Input Order," 2025. arXiv:2502.04134.** Few-shot / input-order
   sensitivity. [COVERS] order-invariance metric. Secondary.

5. **Kuhn, Gal, Farquhar — "Semantic Uncertainty: Linguistic Invariances for Uncertainty Estimation," ICLR 2023**
   (and Semantic Entropy Probes, arXiv:2406.15927). Cluster generations by MEANING equivalence (NLI), take entropy
   over clusters. This IS orbit-averaging over the paraphrase/meaning orbit made into a scalar.
   [COVERS] a ready-made construction of the invariant (meaning-quotient) representation — reuse it to build the
   INVARIANT MARGIN of Theorem 1 (separation of meaning-averaged representations). [LEAVES-OPEN] used for
   hallucination, never for adversarial robustness or as a projection margin.

6. **Wang et al. — "Self-Consistency Improves Chain-of-Thought," ICLR 2023. arXiv:2203.11171.**
   Marginalize over sampled reasoning paths, pick the majority answer; +5–24 pts. Root of the "consistency helps"
   framing. [COVERS] the consistency-as-quality prior we are dissociating from robustness. [LEAVES-OPEN] robustness.

7. **"Automated Consistency Analysis of LLMs" (arXiv:2502.07036) and "Prompt-Reverse Inconsistency"
   (arXiv:2504.01282).** State plainly: **semantic consistency does NOT imply accuracy** — a model can be
   consistently wrong across paraphrases. [COVERS] the exact dissociation logic (consistency ⊥ correctness) that we
   sharpen into consistency ⊥ (or anti-) adversarial robustness. [LEAVES-OPEN] no adversarial axis, no margin.

## B. Positional encoding = the translation-group analog (RoPE shifts)

8. **Su et al. RoPE; Barbero et al. — "Round and Round We Go! What makes RoPE useful?," 2024. arXiv:2410.06205.**
   RoPE encodes RELATIVE position (rotation of query/key by position) → relative-shift equivariance "for free."
   [COVERS] RoPE = the discrete translation-group representation; a position shift is the token-index analog of the
   image circular shift. [LEAVES-OPEN] robustness of the shift-equivariance never measured adversarially.

9. **Kazemnejad et al. — "The Impact of Positional Encoding on Length Generalization," NeurIPS 2023.
   arXiv:2305.19466.** APE/ALiBi/RoPE vs NoPE; **NoPE generalizes best**; explicit PEs are not well-suited to
   length generalization. [COVERS] positional-invariance is not free lunch — the "more imposed positional structure
   ≠ more robust" analog of "more shift-invariance ≠ more robust." [LEAVES-OPEN] adversarial robustness untied.

10. **"Lost in the Middle" (Liu et al., TACL 2024) + "Found in the Middle" (arXiv:2406.16008).** Strong POSITION
    BIAS: mid-context info is under-used; RoPE/attention are far from position-invariant. [COVERS] the
    position-shift-consistency of real LLMs is low and structured. [LEAVES-OPEN] robustness/margin link.

## C. Excessive invariance = the orbit-flip / ρ_G failure mode (our element d)

11. **Jacobsen, Behrmann, Zemel, Bethge — "Excessive Invariance Causes Adversarial Vulnerability," ICLR 2019.
    arXiv:1811.00401.** Networks are too INVARIANT to task-relevant changes → invariance-based adversarial examples
    (change the true label, keep the prediction). [COVERS] our Prop. ρ_G is the norm-form of this; the LLM analog is
    unbuilt. [LEAVES-OPEN] no LLM instantiation.

12. **Tramèr, Behrmann, Carlini, Papernot, Jacobsen — "Fundamental Tradeoffs between Invariance and Sensitivity to
    Adversarial Perturbations," ICML 2020. arXiv:2002.04599.** Defenses against sensitivity attacks ACTIVELY HARM
    robustness to invariance attacks; they break certified-robust models with label-changing perturbations the model
    is "provably robust" to. This is the exact trade-off our ε ≤ η/L AND ε < ρ_G condition formalizes.
    [COVERS] the theory backbone for design B2. [LEAVES-OPEN] never instantiated for text/LLMs — the clean gap.

13. **Sinha, Parthasarathi, Pineau, Williams — "UnNatural Language Inference," ACL 2021. arXiv:2101.00010.**
    SOTA NLI models are INVARIANT to random word-order permutations (98.7% of MNLI examples have a permutation
    eliciting the gold label); holds across Transformers/RNNs/languages. This is a real, measured EXCESSIVE
    word-order invariance in NLP. [COVERS] a concrete permutation-orbit over-invariance to attack. [LEAVES-OPEN]
    never framed as an adversarial-robustness trade-off or given an orbit-flip radius.

14. **Negation insensitivity: Thunder-NUBench / "When Prohibitions Become Permissions: Auditing Negation
    Sensitivity" (arXiv:2601.21433); Truong et al.; "Simple Linguistic Inferences… Blind Spots"
    (arXiv:2305.14785); "Revisiting Systematicity in Negation in ICL" (arXiv:2606.16867).** LLMs frequently give
    IDENTICAL answers after negation (a meaning-flipping edit) — invariance to the exact edit that flips the oracle
    label. [COVERS] the sharpest orbit-flip primitive (negation) with existing eval data. [LEAVES-OPEN] no ρ_G, no
    trade-off vs measured paraphrase-invariance.

15. **Gardner et al. Contrast Sets; "Contrast Sets for LLM Evaluation" (2025).** Minimal meaning-changing
    perturbations that models mispredict. [COVERS] a source of oracle-labeled minimal edits for the orbit-flip
    benchmark in B2. [LEAVES-OPEN] not tied to an invariance metric or trade-off curve.

16. **Röttger et al. — "XSTest: Exaggerated Safety," NAACL 2024; "OR-Bench" (Cui et al. 2025); "Beyond
    Over-Refusal" (arXiv:2510.08158).** Over-refusal = safety models INVARIANT to intent, triggered by keywords
    ("kill a process"); strengthening refusal raises benign-refusal rate. This is the SAFETY instance of excessive
    invariance / the constant-classifier degeneracy (a maximal refuser = chance "helpfulness accuracy," our Lemma
    ratiodegen). [COVERS] over-refusal = orbit-flip on the benign→benign meaning axis; a measurable ρ_G for safety.
    [LEAVES-OPEN] never connected to a margin-to-Lipschitz law or to jailbreak (sensitivity) robustness on the same
    axis.

## D. Adversarial robustness / jailbreaks of LLMs (the robustness metric + strong attacks)

17. **Zou et al. — "Universal and Transferable Adversarial Attacks on Aligned LMs" (GCG), 2023. arXiv:2307.15043.**
    Greedy-coordinate-gradient suffixes; universal + transfer across formats/models. The STRONG discrete attack —
    the AutoAttack analog. [COVERS] the strong-attack side of "weak-attack artifact." Expensive → use on subsets.

18. **Schwinn et al. — "Soft Prompt Threats: Attacking Safety Alignment through the Embedding Space," NeurIPS 2024.
    arXiv:2402.09063** (and "Regularized Relaxation," arXiv:2410.19160; exponentiated-gradient GCG relaxation,
    arXiv:2508.14853). CONTINUOUS embedding-space attacks: differentiable, cheap, strong on open weights.
    [COVERS] the key enabler — a differentiable threat in which the margin-to-Lipschitz ratio η/L is DIRECTLY
    computable (margin = logit gap; L = embedding-gradient norm), exactly threat-matched. Makes B1/B3 measurable.

19. **Zhu et al. — "PromptBench / PromptRobust," 2023. arXiv:2306.04528.** 4,788 adversarial prompts, char/word/
    sentence/semantic attacks (TextBugger, TextFooler, BERTAttack) over 8 tasks/13 datasets; LLMs are not robust.
    [COVERS] a ready adversarial-prompt attack suite on TASK accuracy (not just safety) for design B1.

20. **Jain et al. — "Baseline Defenses for Adversarial Attacks Against Aligned LMs," 2023. arXiv:2309.00614.**
    PARAPHRASE defense (impose paraphrase invariance to strip suffixes) works vs non-adaptive GCG; **adaptive
    attacks break it.** [COVERS] a canonical "imposed invariance helps under the weak/non-adaptive attack it was
    tested on, fails adaptively" data point — direct evidence for element (e). Anchor for B3.

21. **DeepMind — "Consistency Training Helps Stop Sycophancy and Jailbreaks," Oct 2025. arXiv:2510.27062.**
    Train the model to answer IDENTICALLY across sycophancy cues / jailbreak wrappers (output-level BCT, and
    activation-level ACT). Reports jailbreak-success reductions. **Crucially: evaluated on fixed jailbreak patterns,
    NOT adaptive attacks that target the consistency objective; no GCG/embedding attack; no margin/Lipschitz
    reported.** [PARTIALLY BLOCKS a naive "imposed invariance always hurts" claim — imposed invariance DOES lower
    non-adaptive ASR] BUT [LEAVES-OPEN — and is the ideal target for] B3: our theory predicts the gain is a
    weak-attack artifact that collapses under a threat-matched adaptive attack, with the surviving order set by the
    refusal margin, not the imposed invariance. Must cite and stress-test, not ignore.

22. **Jiang et al. — "ChatBug: A Common Vulnerability Induced by Chat Templates," AAAI 2025. arXiv:2406.12935.**
    Rigid chat-template FORMAT is a jailbreak surface (format-mismatch, message-overflow); boosts GCG/others.
    Adversarial training fixes it but with significant helpfulness cost (invariance-robustness trade-off).
    [COVERS] format-invariance failure as an attack + the trade-off. [LEAVES-OPEN] no margin law.

23. **"Logit-Gap Steering: A Forward-Pass Diagnostic for Alignment Robustness," 2025. arXiv:2506.24056.**
    Defines the REFUSAL–AFFIRMATION LOGIT GAP (top refusal-token logit − top affirmative-token logit at first
    decoded step); recasts suffix jailbreaks as closing that gap; the gap predicts jailbreak outcome (Cohen's d>1)
    within 5 tokens. This is EXACTLY our margin η for the safety domain, and confirms it is a forward-pass,
    attack-free predictor. [COVERS] the margin numerator of η/L is defined and validated. [LEAVES-OPEN] no
    Lipschitz/threat-matching, no invariance dissociation — we add the denominator L and the invariance axis.

24. **Arditi et al. — "Refusal in LLMs Is Mediated by a Single Direction," NeurIPS 2024. arXiv:2406.11717.**
    One residual-stream direction is necessary+sufficient for refusal across 13 chat models; adding it forces
    refusal on harmless prompts. [COVERS] the refusal margin = projection onto this direction → a clean, low-D
    place to compute the INVARIANT MARGIN (Theorem 1) after orbit-averaging over paraphrase/format; adding the
    direction to harmless prompts IS the excessive-invariance/over-refusal orbit-flip. [LEAVES-OPEN] margin-to-
    Lipschitz law, invariance dissociation.

## E. Imposed-invariance regularization / defenses (does it help under STRONG attack?)

25. **Tack et al. — "Consistency Regularization for Adversarial Robustness," AAAI 2022. arXiv:2103.04623.**
    (Vision.) Consistency loss across augmentations mainly PREVENTS ROBUST OVERFITTING during adversarial training.
    [COVERS] the mechanism our data-axis result invokes; the LLM analog (consistency training vs robust overfitting)
    is untested. Precedent, not a block.

26. **Xie et al. UDA; R-Drop; SimCSE — consistency/invariance regularization in NLP.** Standard tools that impose
    invariance to augmentations/dropout. [COVERS] the imposed-invariance operators for an LLM dissection.
    [LEAVES-OPEN] whether they help/hurt under strong adaptive text attacks — untested at LLM scale.

27. **Certified text robustness: Ye et al. SAFER (ACL 2020); Zeng et al. Randomized [MASK] (2021); Text-CRS
    (S&P 2024); Semantic Smoothing (arXiv:2402.16192).** Randomized-smoothing certificates over synonym-substitution
    / reordering / insertion — the certified-radius analog. SAFER etc. certify by making the model INVARIANT to the
    substitution set. [COVERS] the certified-robustness half of the criterion; smoothing = imposed invariance with a
    radius. [LEAVES-OPEN] whether imposed-invariance certificates trade off against invariance (label-flip) attacks —
    the two-sided story from Tramèr — never measured in this literature.

## F. Lipschitz / margin machinery for transformers (the denominator L)

28. **Kim, Papamakarios, Mnih — "The Lipschitz Constant of Self-Attention," ICML 2021. arXiv:2006.04710.**
    Standard dot-product self-attention is NOT globally Lipschitz; L2-attention is. [COVERS/CAVEAT] the global
    Lipschitz constant is ill-defined for standard transformers — so, exactly as our paper does, the LLM transfer
    must use the LOCAL, per-input gradient norm ∥∇M∥ (embedding-space), not a global L. Aligns with our practice.

29. **"Pay Attention to Attention Distribution: A New Local Lipschitz Bound for Transformers," 2025.
    arXiv:2507.07814** (JaSMin regularizer lowers local Lipschitz, boosts robustness). [COVERS] local-Lipschitz is
    the right, computable object; a knob to lower L. [LEAVES-OPEN] margin side untouched — mirrors our "lowering L
    alone does not order robustness."

## G. Jailbreak evaluation rigor (needed so a pilot is credible)

30. **Mazeika et al. HarmBench; Chao et al. JailbreakBench; "Distributional ASR" (arXiv:2605.09070); Andriushchenko
    et al. "Simple Adaptive Attacks" (ICLR 2025, arXiv:2404.02151).** Standard behaviors + open-weight classifiers;
    adaptive attacks; report distribution not single-config ASR. [COVERS] local (no paid-API) judges (HarmBench
    Llama-2-13B classifier; NLI/zero-shot DeBERTa) and the evaluation protocol for B2/B3.

---

## Net gap map (what is safe to design)

- The **consistency⊥robustness dissociation + threat-matched η/L predictor** (elements a,b,c): the ingredients all
  exist separately (FormatSpread consistency [1], logit-gap margin [23], embedding-attack Lipschitz [18], semantic-
  quotient orbit-average [5]); NO paper crosses them. **Fully open → Design B1.**
- The **excessive-invariance orbit-flip radius ρ_G + invariance/sensitivity trade-off** (element d): proven in
  vision [11,12], observed piecemeal in NLP (word-order [13], negation [14], over-refusal [16]) but never unified
  into a measurable ρ_G and a trade-off curve on instruction-tuned LLMs. **Open → Design B2.**
- **"Invariance helps" as a weak-attack artifact** (element e): paraphrase defense breaks adaptively [20], ChatBug
  AT costs helpfulness [22]; DeepMind consistency training [21] claims a gain but omits adaptive/threat-matched
  attacks and any margin. **Open, with a live claim to refute → Design B3.**

Nothing found BLOCKS a design; [21] is the one live result that must be engaged head-on (B3 is built to do so).
