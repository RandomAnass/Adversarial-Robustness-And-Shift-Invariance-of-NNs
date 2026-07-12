# Shift-Consistency Does Not Order VLM Adversarial Robustness; a Tower-Computed Margin-to-Lipschitz Diagnostic Does

## Transferable element (from our paper)
- (a) **The dissociation**: shift-consistency does not order adversarial robustness and
  anti-predicts it under adversarial training, while the threat-matched margin-to-Lipschitz
  ratio η/L predicts it.
- (c) **η/L as an attack-free diagnostic** (margin over dual-norm input gradient), here
  computed **through the frozen VLM vision tower** on clean inputs only.
- (d) **Capacity/role-matched operator dissection**: the panel of vision towers spans the
  shift-invariance axis (standard CLIP → anti-aliased → adversarially-robust → truly-shift-
  equivariant/polyphase), i.e. the ViT patch embedding read as a stride-14/16 aliased
  downsampler with different anti-aliasing treatments.
The paper's "attack-free selection rule" (Appendix: pick the operator with highest η/L,
mean regret 0.06 pts vs oracle; consistency mis-selects by 8.8 pts) is transferred verbatim
to the VLM deployment question "which vision tower do I ship?".

## Literature gap (specific papers checked + why open)
- Robust-CLIP line — FARE (arXiv:2402.12336, repo chs20/RobustVLM), Sim-CLIP (2407.14971),
  TeCoA (ICLR 2023), Double Visual Defense / ΔCLIP (2501.09446) — is **strong-attack
  evaluated** but **never computes vision-tower shift-consistency or a margin/Lipschitz η/L**,
  and never relates either to downstream VLM robustness. Confirmed by fetching FARE: it reports
  APGD/AutoAttack numbers on LLaVA/OpenFlamingo with zero mention of invariance or Lipschitz.
- The attack-free **margin-consistency** diagnostic (Ngnawe et al. 2024, arXiv:2406.18451) is
  demonstrated **only on plain adversarially-trained classifiers (RobustBench)** — never through
  a VLM/CLIP tower.
- CLIP multi-property audits ("Holistic Evaluation of Robustness in CLIP," 2410.01534;
  "Beyond Accuracy," 2503.17110) measure invariance and corruption but do **not** test whether
  shift-consistency orders *adversarial* robustness, and use no η/L.
- "Revisiting Adversarial Robustness of VLMs" (2404.19287) establishes the tower governs image
  robustness — de-risking a tower-only diagnostic — but offers no diagnostic.
→ No prior work computes η/L or shift-consistency through a VLM tower or tests the dissociation.

## Hypothesis (falsifiable)
Across a panel of ≥6 open vision towers used inside one fixed VLM harness, ranked by their
downstream **strong-attack** robust score S:
1. **Vision-tower shift-consistency SC does not order S** (|Pearson(SC, S)| < 0.4), and among
   the *robust* towers it is near-constant or anti-predictive.
2. **The threat-matched, tower-computed η/L predicts S** (Pearson(η/L, S) ≥ 0.8), and does so
   attack-free (η/L is computed on clean inputs, no attack run).
3. **Selection by η/L** picks the most/2nd-most robust tower (regret ≤ 1 pt), while **selection
   by SC** picks a materially worse tower (regret ≥ 5 pts), because SC is maximized by the most
   invariant (often least-robust-when-not-AT) tower.
Kill: if SC correlates with S as strongly as η/L, or if η/L fails to predict, the transfer dies.

## Protocol (model, dataset/benchmark, attack/eval incl. STRONG attack, metrics, exact steps)
**VLM harness.** Fixed decoder + projector, swap the frozen vision tower. Two concrete routes:
- Route A (no training, preferred): LLaVA-1.5-7B with the **RobustVLM drop-in encoders**
  (chs20/RobustVLM ships CLIP ViT-L/14 + FARE2/FARE4 + TeCoA2/TeCoA4 as LLaVA vision towers).
  Panel = {clean CLIP, TeCoA2, TeCoA4, FARE2, FARE4, Sim-CLIP, ΔCLIP if released}. This is a
  role-matched panel spanning the shift-invariance × robustness plane, all released, no training.
- Route B (breadth): also evaluate towers *inside* a modern VLM already in cache
  (Qwen2.5-VL-7B-Instruct) by substituting its ViT with the same encoder family via feature
  re-projection (light 1-epoch projector fit only if alignment degrades clean acc >3 pts).

**Panel measurements (per tower).**
1. **Shift-consistency SC**: circular + integer pixel shifts of the input (patch-grid phase
   sweep, 0..stride-1 in x,y = 14×14 or 16×16 offsets); SC = mean fraction of downstream answers
   unchanged (and, at the embedding level, cosine-consistency of the pooled embedding).
2. **Tower η/L (attack-free, clean inputs)**: η = mean active margin (for the VQA/zero-shot head
   the correct-vs-runner-up logit gap; for open-ended captioning the target-token vs top-rival
   log-prob gap), L_q = mean ‖∇_x M‖_q with q the dual norm of the eval threat (q=1 for ℓ∞).
   Compute on 2k clean eval images. This is the paper's η/L read through the tower+head.
3. **Clean task score** (control; the paper insists η/L must beat clean-acc-as-confound).

**Benchmarks (FULL, not toy).** ImageNet zero-shot (encoder-level, full 50k val) + a VLM task:
VQAv2 (full val subset used by FARE, ~5k) and COCO captioning (CIDEr). Zero-shot ImageNet gives a
clean high-n arm; the VLM tasks give the deployment-relevant arm.

**STRONG attack (this is the load-bearing evaluation).**
- Encoder-level: **APGD-CE + APGD-DLR ensemble (AutoAttack's first two), 100 iters**, ℓ∞
  ε∈{2/255, 4/255} on ImageNet zero-shot — RobustBench-grade, the exact FARE protocol.
- VLM-level: **APGD on the answer log-likelihood**, ℓ∞ ε=4/255, 100 iters + 5 restarts, targeted
  (flip to a wrong answer) and untargeted; plus an **embedding-matching APGD** (VEAttack/AttackVLM
  style) as a transfer arm. Report robust accuracy / CIDEr-under-attack as S.
- **Gradient-masking check (mandatory, from our paper)**: APGD ≤ PGD-40; add a black-box Square
  Attack spot-check; report the gap so a low S cannot be dismissed as masking.

**Analysis.** Pearson/Spearman of SC vs S and η/L vs S over the panel; partial correlation of
η/L vs S controlling for clean score; the selection-rule regret table (η/L-pick vs SC-pick vs
clean-pick vs oracle). Bootstrap CIs over eval images.

## Compute estimate (GPU-hours on A6000s)
No training in Route A. Per tower: (i) η/L + SC on 2k images ≈ 2k fwd+bwd of tower(+head),
~0.5 GPU-h; (ii) ImageNet-50k zero-shot clean+APGD(100-iter, 2 losses) ≈ tower-only, ~6–8 GPU-h;
(iii) VLM APGD on ~5k VQA images at 100 iters through the 7B decoder ≈ ~12–18 GPU-h. ≈ 20–27
GPU-h/tower × 6 towers ≈ **~130–160 GPU-h**, i.e. ~3–4 days wall-clock on 2×A6000. Trim by
subsampling ImageNet to 10k and VQA to 2k for a ~60 GPU-h pilot.

## Why standalone top-tier (what a reviewer would call the contribution)
First **attack-free deployment diagnostic for VLM vision towers**: a single clean-input number
(tower η/L) that ranks encoders by their *strong-attack* downstream robustness, and a clean
demonstration that the property the anti-aliasing/consistency community foregrounds
(shift-consistency) is the *wrong* signal for this choice. It converts a 100-GPU-h AutoAttack
sweep into a 0.5-GPU-h forward pass, with an honest failure mode (consistency mis-selection)
that reframes how the field should pick robust encoders. Reviewer one-liner: "a margin-to-
Lipschitz statistic computed through the frozen tower predicts VLM adversarial robustness without
running an attack, and shift-consistency provably does not."

## Risks / kill criteria
- **Panel too collinear** (all robust towers similar SC and η/L): mitigate by including the
  extreme arms (clean CLIP, TeCoA4 with heavy clean-acc cost, a truly-shift-equivariant/APS ViT
  ported as an extra tower) to widen the axis — the paper shows the anti-prediction only appears
  once the consistency range is wide.
- **Projector re-alignment confound** in Route B: prefer Route A (RobustVLM ships aligned towers).
- **η/L definitional-inflation worry** (our paper's own caveat): report the *dissociation* (SC
  fails, η/L beats clean-acc in partial correlation) as the load-bearing claim, not the raw η/L–S
  number.
- Kill if SC predicts S as well as η/L, or η/L–S partial-correlation (controlling clean score)
  drops below 0.5.
