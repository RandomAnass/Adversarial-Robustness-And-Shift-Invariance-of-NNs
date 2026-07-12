# Round-2 Experimental-Design Adversary — Lens C (VLM / multimodal)

Goal: make each design's **single strong-attack run** bulletproof and **feasible on 2×A6000 48 GB**,
so its result could carry a standalone top-tier journal paper. Round-1 (literature) corrections are
folded in. Priority stated up front and applied throughout: **ONE robust strong run > breadth.** A
second seed / second VLM / second dataset is OPTIONAL and explicitly demoted below the load-bearing run.

Method for this round: verified the load-bearing *feasibility* facts (not re-verified round-1's PDF
reads, which stand). Checks run: RobustVLM shipped checkpoints + how they load; LLaVA-1.5-7B openness
and size; local HF cache inventory; local library inventory; programmatic-oracle dataset availability
for C2; the R-Adapt / Fragility / VLM-RobustBench scoop facts that gate C2/C3.

---

## Environment reality (governs all three verdicts — read first)

**HF cache (`~/.cache/huggingface/hub`) inventory — decisive:**
- **Present:** `Qwen2.5-VL-7B-Instruct`, `Qwen3-VL-8B-Instruct`, `Qwen3-VL-8B-Thinking`,
  `Qwen3-VL-30B-A3B-Instruct`, `Qwen3-VL-32B-Instruct-FP8`. Also DINOv3 ViT-L/16, timm DINOv2 ViT-L/14.
- **ABSENT (must download, all open-weight):** LLaVA-1.5-7B, **any** OpenAI/OpenCLIP CLIP,
  and the RobustVLM towers (FARE/TeCoA). None are cached.

**Downloads required (all open, sizes confirmed):**
- RobustVLM towers are `open_clip` checkpoints on the Hub: `hf-hub:chs20/fare2-clip`, `fare4-clip`,
  `tecoa2-clip`, `tecoa4-clip` (ViT-L/14, 224 px, 2-epoch ImageNet AT). ~0.9–1.7 GB **each** — trivial.
  Round-1 fact confirmed: RobustVLM ships **only** {FARE2, FARE4, TeCoA2, TeCoA4} + base CLIP as
  drop-in LLaVA towers (`bash/llava_eval.sh`, `--vision_encoder_pretrained`). Sim-CLIP / ΔCLIP are
  **not** in this harness.
- Base CLIP ViT-L/14: `openai` weights via `open_clip` (~1.7 GB) or `openai/clip-vit-large-patch14`.
- LLaVA-1.5-7B: `liuhaotian/llava-v1.5-7b` (~14 GB) or `llava-hf/llava-1.5-7b-hf`. Vision tower is
  CLIP ViT-L/14-**336**; RobustVLM towers are 224 px — a resolution mismatch the harness handles
  (RobustVLM re-fits at 224), but note it (see C1 fix 4).

**Local libraries:** base env has `torch 2.12`, `torchvision 0.27`, but **`transformers 4.32.1`**
(too old for Qwen-VL, which needs ≥4.49) and **no `open_clip`, no `autoattack`, no `robustbench`,
no `llava`.** → A fresh conda env is a **one-time ~1–2 h setup**, not a per-run cost. Budget it once.

**Compute:** 2×A6000, currently ~2.5 / 5 GB used (essentially free). 48 GB/card is the constraint that
makes the **decoder-in-the-loop APGD** the cost/feasibility risk for every design.

**The single feasibility lever that saves all three designs:** the entire zero-shot ImageNet arm — SC,
η/L, and the strong AutoAttack — runs **at the `open_clip` encoder level with no LLaVA and no 7B
decoder in the attack graph.** APGD then backprops through a ~0.4 B ViT, not a 7B LM. This is 1–2
orders of magnitude cheaper than decoder-level APGD and is *decoder-independent*, which is scientifically
cleaner (round-1's 2407.11121 already shows the tower governs, so the decoder is not where the signal
is). **Every design's standalone run should be the encoder-level arm; the LLaVA-decoder arm is a small
confirmatory subset, never the headline.**

---

## C1 — "Shift-consistency does not order VLM tower robustness; a threat-matched η/L does"

### VERDICT: **RUN-READY (after the fixes below). Strongest and most feasible of the three. Make this the flagship.**

The core dissociation (frozen-tower SC does not rank strong-attack robustness; threat-matched η/L does,
attack-free, as a cross-tower *selection rule*) is unclaimed and maps 1:1 onto the paper's Table-1 laws.
The fixes are framing + panel + one protocol correction, not a redesign.

### The single run (encoder-level, standalone)
**Panel (7 towers, all no-train drop-ins, spanning the invariance × robustness plane):**
`openai` CLIP ViT-L/14 (non-robust), FARE2, FARE4, TeCoA2, TeCoA4 (the 4 RobustVLM AT towers), **plus
two non-AT invariance-axis wideners at the encoder level** to escape the round-1 collinearity kill:
(6) a **DINOv2/DINOv3 ViT-L** used zero-shot via a linear-probe head (high clean acc, different
invariance profile, non-AT), and (7) an **anti-aliased / APS ViT-L stem** variant of base CLIP (blur-pool
the patch-embed conv, or APS at the stem) — a training-free operator swap that *raises SC without AT*.
Rationale from the paper (§exp): the SC anti-prediction only appears once the consistency **range is
wide**; the 4 AT towers alone cluster (round-1's own collinearity risk). The two non-AT wideners open the
axis exactly as the paper's two low-invariance ResNet arms did (SC squeezed to [0.93,1.00] → widened to
[0.85,1.00] restored the anti-prediction).

**Benchmark:** **ImageNet-1k zero-shot, full 50 k val** (open_clip text-prompt classifier). High-n,
single clean arm, no decoder. This alone is the standalone paper.

**Per-tower measurements (all through the frozen tower + zero-shot head):**
1. **SC** = mean fraction of zero-shot predictions unchanged over the S×S patch-grid phase sweep
   (integer + circular shifts, 0..stride−1), plus pooled-embedding cosine-consistency. Report both.
2. **Threat-matched η/L (attack-free, clean inputs):** η = mean active margin (correct-class vs
   runner-up logit gap of the zero-shot head); **L = mean ‖∇_x M‖₁** (the **ℓ₁** dual norm of the ℓ∞
   attack — this is the paper's *threat-matched* ratio; the ℓ₂ version is the mismatched control).
   Compute on 2 k clean val images. Report **matched (η/‖∇M‖₁) and mismatched (η/‖∇M‖₂)** as the paper does.
3. **Clean zero-shot acc** (confound control).

**STRONG attack (load-bearing):** **AutoAttack-style APGD-CE + targeted APGD-DLR ensemble, 100 iters**,
ℓ∞ **ε ∈ {2/255, 4/255}** (FARE's own protocol; RobustBench-grade), on the correctly-classified subset,
5 k–10 k images per tower is enough for tight CIs at n=50 k available if wall-clock allows. S = robust
zero-shot accuracy. **Encoder-level only** — no decoder.
- **Gradient-masking audit (mandatory, from the paper):** APGD ≤ **PGD-40** per tower; **Square-Attack**
  black-box spot-check (≥1 k images); report both gaps. A low S that passes the audit is real; report it.
  This directly mirrors the paper's "AutoAttack ≤ matched PGD, no masking" gate.

**Analysis (headline = the dissociation, not the raw η/L number):**
Pearson & Spearman of {SC, η/‖∇M‖₁, η/‖∇M‖₂, clean-acc} vs S over the 7 towers; **partial correlation
of η/‖∇M‖₁ vs S controlling for clean acc** (the load-bearing statistic, per the paper's own caveat that
η/L must beat clean-acc-as-confound); the **selection-rule regret table** (η/L-pick vs SC-pick vs
clean-pick vs oracle-pick, regret in robust-acc points); **bootstrap 95 % CIs resampling towers/images**
+ permutation test (matches the paper's statistical-power paragraph).

### Fixes to apply before running
1. **Reframe the two novelty overclaims (round-1).** Do **not** claim "first margin/Lipschitz through a
   CLIP tower" (ICLR'25 purification OpenReview TQ2ZOy6miT did local-Lipschitz through CLIP) nor
   "attack-free robustness prediction from clean stats has never been done" (RDI 2504.18556). The
   defensible unclaimed contribution: **cross-tower, attack-free robustness-*ranking* by a threat-matched
   η/L on a frozen panel, paired against a shift-consistency *null* result** — state it exactly so.
2. **Swap the tower-governs miscite 2404.19287 → 2407.11121** (round-1 cross-cutting). Keep 2404.19287
   only if used correctly for the multimodal-attack angle.
3. **Cite:** RDI 2504.18556, Singla–Ge 2103.02695 (motivation: shift-invariance *reduces* robustness →
   why SC should fail to order S), 2407.11121, the ICLR'25 CLIP-Lipschitz paper; and **pre-empt R-Adapt
   2603.12799** with one paragraph separating "spectral bias as a training story" from "η/L as an
   attack-free cross-tower selector."
4. **Resolution control (new, C1-specific).** Base CLIP-336 (LLaVA's native tower) vs RobustVLM's 224
   towers vs the DINO wideners differ in input resolution; resolution changes both SC (phase grid size)
   and gradient norm scale. **Fix a single common eval resolution (224) for all 7 towers** and state it,
   or report η/L in resolution-normalized units. Otherwise a referee attributes the η/L ranking to a
   resolution confound. (This is the one genuinely new protocol hole round-1 did not flag.)
5. **Report SC on the *same* correctly-classified subset** used for η/L and S, so the three axes are
   commensurable per-tower (avoids the "SC measured on a different population" objection).

### GPU-hours on 2×A6000 (encoder-level standalone)
Per tower: SC+η/L on 2 k images ≈ 0.3 GPU-h; ImageNet-50k clean zero-shot ≈ 0.5 GPU-h; APGD ensemble
(100-iter, 2 losses, 2 ε) on 10 k correctly-classified + PGD-40 + Square audit ≈ 4–6 GPU-h. **≈ 5–7
GPU-h/tower × 7 = ~40–50 GPU-h**, ~1–1.5 days on 2×A6000. **FEASIBLE — comfortably.** Full 50 k-image
APGD (instead of 10 k) is ~90 GPU-h if desired; not needed for tight CIs.
**Optional/secondary:** LLaVA-1.5-7B decoder-level APGD on ~1 k VQAv2 items, 5 towers, to show the
encoder ranking survives into the generative VLM (~15–20 GPU-h). Explicitly a confirmatory arm, not the
headline. **FEASIBILITY FLAG: green.**

### Headline sentence if it works
"A margin-to-Lipschitz statistic computed through a frozen VLM vision tower on clean images ranks
encoders by their strong-attack (AutoAttack) robustness without running any attack, while
shift-consistency — the invariance metric the anti-aliasing literature tracks — does not order it and
under adversarial training anti-predicts it."

---

## C2 — "Excessive invariance / orbit-flip in VLMs; the ρ_G axis is distinct from and not fixed by η/L"

### VERDICT: **FIX-THEN-RUN. Most conceptually novel; highest scoop-risk. Feasible, but the oracle and the differentiation are the whole game.**

No verified prior defines/measures ρ_G (smallest oracle-flipping geometric transform where the VLM
answer stays fixed) as an adversarial axis, correlates it with pixel η/L on the same models, or tests
whether a robust (FARE) tower is *worse* on it. But the run only stands alone if (i) the oracle is
non-circular and programmatic, (ii) the differentiation from the near-scoop is hard-coded into the design.

### The single run (grounded-VQA, programmatic oracle, gradient-free orbit attack)
**Model:** **Qwen2.5-VL-7B-Instruct (cached)** as the primary generative VLM — the strong, modern,
grounded-VQA-capable model, already local. **Paired sensitivity contrast:** LLaVA-1.5-7B with the
**FARE4 tower** vs **base CLIP tower** (this is the hypothesis-2 test: does pixel-robustness buy ρ_G?).
Second scale point (Qwen3-VL-8B) is **OPTIONAL**, demoted.

**Benchmark — restrict the *headline* to datasets with a true programmatic oracle:**
- **CLEVR** (full 3D scene graph → 2D boxes; counts, left/right, behind/front all computable) and
  **TallyQA** (ships bounding boxes for the counted regions). **These two carry the headline** because
  the transformed oracle answer is computed from geometry with **zero judge-VLM involvement**.
- **VSR has NO native boxes** → move it to a *secondary* qualitative arm or drop from the headline.
  BLINK/CV-Bench spatial only where coordinates are available. TextVQA/ST-VQA OCR phase arm is
  **secondary** (oracle for "does OCR still read the same" is judgment-laden — keep it illustrative).

**Orbit + oracle (the load-bearing, most-attackable step):** For each item, define a **parametric
transform orbit** (integer + sub-patch translations across the full 14/16 phase grid, graded crops,
horizontal flip, small scales/rotations). For each transform, the **new oracle answer is computed
programmatically** from the known scene geometry (count after removing objects whose box exits the crop;
relation from transformed coordinates; flip inverts left/right). **ρ_G(item) = min pixel-ℓ₂ transform
that changes the *oracle* answer.** Record whether the **VLM answer stayed fixed** (= orbit-flip failure)
at that transform. **STRONG attack = worst-case-over-orbit answer accuracy** (the ρ_G-realizing,
gradient-free attack). The **judge VLM is used ONLY as a legibility gate** (discard items where a local
judge marks the transformed image "unanswerable"), **never** to relabel the target's own class — headline
numbers reported on the programmatic-oracle subset so no referee can attack the judge (round-1 fix 3).

**Controls (both mandatory):**
- **Condition on single-view-correct items** (the flip is an invariance failure, not incompetence).
- **Legibility gate** (transform did not destroy the image) via programmatic crop-geometry + judge veto.
- Report **clean single-view accuracy** per model so orbit-flip rate is not a weak-model artifact.

**Sensitivity-axis control attack:** standard **ℓ∞ APGD (ε=4/255, 100 iter)** pixel attack on the same
items, so the two axes (η/L / pixel-robust vs ρ_G / orbit-robust) can be shown to **rank the FARE-vs-CLIP
pair differently** — the paper's "needs room under both" η/L–ρ_G plane, one point per model.

### Fixes to apply before running
1. **Differentiate from the near-scoop on page 1, not a footnote:** *Semantic Richness or Geometric
   Reasoning? The Fragility of VLM's Visual Invariance* (2604.01848). Your three separators, none of which
   it has: (i) a **metric** (minimal oracle-flipping transform where the VLM stays fixed = ρ_G), (ii) the
   **ρ_G ↔ pixel-η/L two-axis correlation on the same models**, (iii) the **robust-tower (FARE) test**.
   2604.01848 uses accuracy/TPR/TNR on rotation/scale/identity of object-identity images — no metric,
   no adversarial/FARE link. Frame C2 as **operationalizing what they left qualitative.**
2. **Cite the mandatory five (else desk-flag):** Jacobsen 1811.00401 + Tramèr ICML 2020 (axis
   definition), 2604.01848 (nearest narrative scoop), **VLM-RobustBench 2603.06148** (opposite-framing
   foil: it scores answer-*flips* under label-*preserving* corruption as failure — C2's point is the
   inverse, that *keeping* the answer under a label-*changing* flip is the failure), **2602.06652** "Same
   Answer, Different Representations" (mirror image), FARE 2402.12336 (robust-tower premise). Read
   2604.04473 before submission (round-1 flagged it unverified).
3. **Sharpen hypothesis 2 with a mechanism (round-1 fix 4):** predict FARE is **worse** (not merely "no
   better") on ρ_G because ℓ∞ AT smooths the tower and *widens* excessive invariance; then even a null is
   informative. Pre-empt FARE's own "robustification is marginal on reasoning" claim by noting its eval
   is coarse VQA, never counting-under-crop or left/right-under-flip.
4. **Make the white-box orbit-manifold search OPTIONAL, not load-bearing** (round-1). The grid/parametric
   orbit search is already a valid strong gradient-free attack and is the safer single run; differentiating
   answer-log-likelihood through the tower along the transform manifold is engineering risk on the critical
   path — demote it.
5. **Kill criterion, pre-registered:** kill if conditioned (single-view-correct, legible) orbit-flip rate
   < 5 %, **or** if the FARE tower is *as* orbit-robust as base CLIP (axes not distinct → (e) collapses
   into (a)). Honest-negative: a clean null on hypothesis 2 with the mechanism stated is still a result.

### GPU-hours on 2×A6000
Dominated by generation. CLEVR+TallyQA headline subset ~4–6 k items × ~25–35 orbit views × Qwen2.5-VL-7B.
Round-1's 0.3 s/gen is optimistic under long grounded prompts + batched sampling — **budget 1.5–2×**:
~5 k × 30 × 0.5 s ≈ ~20–25 GPU-h. FARE-vs-CLIP LLaVA pair on the same items ≈ ~15 GPU-h. Pixel-APGD
control on 1 k ≈ 6 GPU-h. Judge legibility gate (small) ≈ 5 GPU-h. **≈ 45–55 GPU-h**, ~1.5–2 days.
**FEASIBILITY FLAG: green** (inference-bound; the risk is engineering the programmatic oracle correctly,
not GPU). No training.

### Headline sentence if it works
"The same vision-tower engineering that makes VLMs shift-stable makes them blind to benign geometric
transforms that change the answer, and adversarial training of the tower — which improves pixel
robustness — does not fix and can worsen this orbit-flip vulnerability: sensitivity (η/L) and invariance
(ρ_G) robustness are decoupled axes."

---

## C3 — "Anti-aliasing a VLM tower helps under FGSM, vanishes under a strong attack"

### VERDICT: **FIX-THEN-RUN, narrow. Survives ONLY as repositioned in round-1: APS/polyphase ViT-stem + inference-time phase-averaging under EoT-adaptive APGD. Drop the blur-pool/Gaussian arm as a contribution. Tightest feasibility; keep the strong attack at encoder level or it is INFEASIBLE.**

Round-1 established the gap is mostly closed: the weak-helps/strong-kills mechanism is Athalye 2018 +
Ensemble-Everywhere 2024; anti-aliasing-under-AutoAttack for CNNs is Grabinski/FLC/ASAP/Torralba;
**Gaussian low-pass on a frozen CLIP tower under AutoAttack is already R-Adapt (2603.12799).** The one
genuinely open cell (~80 % novel): **APS/polyphase-anchored ViT *stem*, or inference-time patch-grid
phase-averaging, in a frozen VLM tower, under any Lₚ attack.** The run must be centered there or it dies.

### The single run (encoder-level, EoT-adaptive, the one open operator)
**Tower:** base CLIP ViT-L/14 (`open_clip`), frozen. **Interventions on the patch-embed stem:**
1. **Standard strided patch-embed** (baseline / aliased).
2. **Inference-time phase-averaging** — average the pooled tower embedding over the S×S patch-grid phase
   offsets (implement your *own* pooled-embedding average; **cite 2606.08132 for the phenomenon only** —
   round-1 fix 5: that paper is dense-prediction TTA and its inverse-align-dense-outputs mechanism does
   not map onto a pooled CLS/global embedding). Stochastic single-phase-sample variant for the EoT attack.
3. **APS / polyphase-anchored stem** (energy-selected phase, exactly shift-invariant) — the high-SC
   extreme; the *actually-open* operator.
4. **Blur-pool stem (Rect-2/Tri-3/Bin-5)** — **DEMOTED to a replication anchor** with correct citations
   (ASAP, R-Adapt), **not** a claimed contribution (round-1 fix 2).

**Benchmark:** **ImageNet-1k zero-shot** (encoder level, high-n). This is the standalone.

**Per-intervention measurements:** SC (patch-grid phase sweep), threat-matched η/‖∇M‖₁ (attack-free,
clean), clean zero-shot acc. Light re-fit only if clean drops >3 pts (matched-clean-accuracy control).

**Attacks — the whole point is weak-vs-strong:**
- **Weak:** FGSM (ε∈{1,2,4}/255), PGD-10, and a **transfer** attack (crafted on the standard stem,
  applied to the intervention stem). Expect the anti-aliasing "advantage" to appear here.
- **Strong (load-bearing):** **APGD-CE + APGD-DLR ensemble, 100 iters, 5 restarts**, ℓ∞ ε∈{2,4}/255,
  made **adaptive**: differentiable interventions attacked directly; for APS phase-argmax use
  **straight-through + EoT over phases**; **Expectation-over-Transformation over the K phase offsets** for
  the phase-averaged/stochastic tower so stochasticity cannot fake robustness. Expect the advantage to
  collapse to within noise.
- **Gradient-masking / adaptivity audit (mandatory, from the paper):** APGD ≤ **PGD-40** per arm; report
  **EoT-APGD vs no-EoT-APGD gap** (the phase-stochasticity masking check); **Square-Attack** black-box.
  Cite **Ensemble-Everywhere 2411.14834** as the acknowledged blueprint and **Athalye 1802.00420** as the
  mechanism origin, so the expected collapse reads as *confirmation-with-rigor*, not a claimed surprise.
- **FARE arm:** repeat interventions on the FARE4 tower to show that *there* robustness is nonzero and
  **η/‖∇M‖₁ (not SC)** orders the intervention variants — the paper's "under AT, η/L governs" claim.

### The feasibility bottleneck (the reason this is the tightest design)
**EoT of K phases multiplies APGD cost by K, and APGD is already the expensive part.** Round-1 is right:
**decoder-in-the-loop, EoT-adaptive APGD through a 7B LM is INFEASIBLE at scale on 48 GB.** The minimal
feasible core: **keep the entire strong-attack + EoT arm at the `open_clip` encoder/zero-shot level**
(APGD backprops through the ~0.4 B ViT, K≤8 EoT phases, on the embedding-margin loss). The VLM-decoder
APGD is a **≤1 k-image, K≤4 confirmatory subset** only. As written ("~200 GPU-h, 4 interventions × 2
towers, decoder APGD"), the full plan is optimistic; the standalone paper is the **encoder-level ImageNet
APGD+EoT** result.

### Fixes to apply before running
1. **Correct the false gap sentence** (round-1 fix 1): "the anti-aliasing line NEVER measures adversarial
   robustness" is **false** for CNNs (Grabinski/FLC/ASAP/Torralba all use AutoAttack/APGD). Restrict the
   open claim to **ViT-stem anti-aliasing / shift-equivariant ViT stems / phase-averaging**, where it holds
   (cite Reviving Shift Equivariance 2306.07470 as the gap-open anchor).
2. **Drop the Gaussian/blur-pool arm as a contribution; keep it as a replication anchor** citing R-Adapt
   2603.12799 (Gaussian-on-frozen-CLIP-under-AutoAttack) + ASAP. **Add the explicit filter-only
   weak-vs-strong ablation R-Adapt did not run** — that ablation is your differentiator.
3. **Center on APS/polyphase-stem + phase-averaging** as *the last shift-invariance operator never
   adversarially tested in a VLM* (round-1 fix 3).
4. **Fix the phase-marginalization usage** (round-1 fix 5): implement your own pooled-embedding phase
   average; cite 2606.08132 for the phenomenon, do **not** claim to use its dense-prediction method.
5. **Pre-registered KILL / honest-negative:** kill the (b)-transfer if the anti-aliasing advantage
   **survives** the EoT-adaptive strong attack on the non-AT tower *with the masking audit passed* — that
   would be genuine evidence invariance helps VLM robustness, reported honestly. The expected result
   (advantage collapses) is a confirmation, so the design must state up front that the *contribution is
   the rigor + the operator + the VLM setting*, not a surprising sign.

### GPU-hours on 2×A6000 (encoder-level core)
Per intervention (encoder level): weak attacks (FGSM/PGD-10, transfer) on ImageNet-10k ≈ 1 GPU-h; strong
EoT-adaptive APGD (100 iter × 5 restart × K≤8 EoT) on 5–10 k ≈ 8–12 GPU-h (EoT is the K× multiplier);
SC+η/L+clean ≈ 0.5 GPU-h. **≈ 10–14 GPU-h/intervention × 4 (std, phase-avg, APS, blur-anchor) × 2 towers
(CLIP, FARE) ≈ 90–110 GPU-h**, ~2.5–3.5 days. **FEASIBILITY FLAG: yellow** — feasible *only* at encoder
level; the decoder-level EoT-APGD confirmatory subset must be tiny (≤1 k images, K≤4, ~15 GPU-h) or the
run does not fit. Trim to 3 interventions × 2 towers for a ~60 GPU-h pilot if wall-clock is tight.

### Headline sentence if it works
"Anti-aliasing the ViT patch grid — including the exactly-shift-invariant APS/polyphase stem and
inference-time phase-averaging, the last shift-invariance operators never adversarially tested — looks
like a free robustness gain on FGSM/PGD/transfer attacks and vanishes under an EoT-adaptive strong attack
on a frozen VLM tower; strong-attack evaluation is not optional for invariance-based VLM defenses."

---

## Cross-design corrections to apply before any compute (from round-1, still binding)
- **Swap the tower-governs miscite 2404.19287 → 2407.11121 in all three.**
- **Every standalone run is the encoder-level (`open_clip`, no 7B decoder) arm.** Decoder-level APGD is a
  small confirmatory subset in each, never the headline (feasibility + the tower-governs result both say so).
- **One-time env setup:** fresh conda env with `open_clip_torch`, `autoattack`/`robustbench`,
  `transformers>=4.49` (for Qwen-VL), LLaVA repo. ~1–2 h, not a per-run cost.
- **Gradient-masking audit (APGD ≤ PGD-40 + Square + EoT-gap where stochastic)** is mandatory in all three,
  exactly as the paper's dissection uses "AutoAttack ≤ matched PGD, no masking."
- **Partial correlation controlling clean accuracy + bootstrap CIs over cells** is the load-bearing
  statistic, matching the paper's own statistical-power protocol — not the raw correlation.

## Summary table
| Design | Verdict | Single biggest experimental fix | Standalone GPU-h (encoder-level) | Feasibility |
|---|---|---|---|---|
| **C1** | **run-ready** | Widen the panel with 2 non-AT invariance-axis arms (DINO + anti-aliased CLIP stem) + fix a common eval resolution, so SC has range to (anti-)predict and η/L's rank is not a resolution confound | ~40–50 | green |
| **C2** | **fix-then-run** | Restrict the *headline* orbit-flip oracle to CLEVR+TallyQA (true programmatic boxes; drop VSR from headline) and hard-differentiate from 2604.01848 on page 1 | ~45–55 | green |
| **C3** | **fix-then-run (narrow)** | Center on APS/polyphase-stem + own pooled-embedding phase-averaging under EoT-adaptive APGD **at the encoder level only**; demote blur-pool/Gaussian to a cited replication anchor | ~90–110 (encoder), decoder subset ≤1k | yellow |

**Most feasible / flagship: C1** — cheapest, cleanest, decoder-independent, maps 1:1 onto the paper's
Table-1 laws, and every piece (towers, ImageNet, APGD, audit) is off-the-shelf.
