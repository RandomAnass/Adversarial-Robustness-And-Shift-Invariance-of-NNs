# Excessive Invariance in VLMs: When the Vision Tower Ignores a Transform That Should Change the Answer

## Transferable element (from our paper)
- (e) **Excessive invariance / orbit-flip** (Proposition on the orbit-flip radius ρ_G): an
  invariant classifier can be correct at x yet wrong at a transformed R_h·x whose oracle label
  differs — an *invariance-based* adversarial example. A perturbation budget admits a robust
  invariant model only if ε ≤ η/L (score stability, sensitivity-based) **and** ε < ρ_G (the
  imposed invariance does not cross the oracle boundary).
- The paper's framing that **sensitivity-based robustness (η/L) and invariance-based robustness
  (ρ_G) are two different axes and a model needs room under both** — directly transferable to
  VLMs, whose vision towers are trained/architected to be increasingly transform-invariant.

## Literature gap (specific papers checked + why open)
- Excessive-invariance theory (Jacobsen et al., ICLR 2019; Tramèr et al., "Fundamental
  Tradeoffs...", ICML 2020 = our tramer2020fundamental) is developed **only for classifiers**.
- VLM semantic-transform work uses invariances to *strengthen attacks* ("Boosting Local
  Invariance for Transferability," 2503.06140; scale-invariant gradient attacks), not to
  *diagnose excessive invariance* as a robustness axis.
- "Same Answer, Different Representations" (2602.06652) notes VLM answer-stability and
  representation-stability decouple, but does not formalize an orbit-flip robustness or tie it to
  ρ_G / η/L.
- Spatially-grounded VLM benchmarks (CV-Bench, BLINK, MMVP, VSR, TallyQA, CLEVR, chart/OCR sets)
  exist but none frame a *geometric transform that changes the ground-truth answer* as an
  invariance-based attack or measure a VLM orbit-flip rate.
→ No prior work measures VLM excessive invariance as an adversarial axis or connects it to the
sensitivity axis on the same models.

## Hypothesis (falsifiable)
For spatially/positionally grounded VQA, there exist **label-changing geometric transforms**
(crop that removes a counted object, translation that moves an object across a queried region
boundary, patch-grid phase shift that re-tiles fine OCR text, horizontal flip for left/right
relations) such that:
1. **Orbit-flip rate is high**: on a nontrivial fraction (hypothesis ≥ 20%) of grounded questions,
   the smallest transform that flips the *oracle* answer leaves the **VLM answer unchanged**
   (now wrong) — an excessive-invariance failure the model is "blind" to.
2. **The two axes are distinct**: a tower with *higher* pixel-level (sensitivity) robustness — a
   robust-CLIP / adversarially-trained tower (FARE) — is **not** more robust on the orbit-flip
   axis, and may be *worse* (adversarial training smooths the tower, widening excessive
   invariance), so pixel-robustness (η/L) does not buy orbit-flip robustness (ρ_G).
3. **A search over the transform orbit is a strong, gradient-free attack**: worst-case-over-orbit
   answer accuracy drops far below single-view accuracy, and below what any ℓ∞ pixel attack at a
   perceptible budget achieves, because it exploits invariance rather than sensitivity.
Kill: if orbit-flip failures are rare (<5%) or fully explained by clean-accuracy / the transform
also breaking human legibility, the axis is not real for VLMs.

## Protocol (model, dataset/benchmark, attack/eval incl. STRONG attack, metrics, exact steps)
**Model.** Qwen2.5-VL-7B-Instruct (cached) as primary; Qwen3-VL-8B-Instruct (cached) as a second
scale point; LLaVA-1.5-7B with a **robust FARE tower** vs the **clean CLIP tower** as the paired
sensitivity-axis contrast (tests hypothesis 2). All open-weight, ≤ 8B active.

**Benchmark (FULL).** A grounded-VQA suite where geometry is answer-relevant:
- **TallyQA / CLEVR-count** (counting: crop/translate objects out of frame → oracle count drops).
- **VSR + CV-Bench-2D/3D + BLINK spatial** (left/right/above, depth ordering: flip/translate →
  relation flips).
- **A fine-print OCR set** (TextVQA / ST-VQA subset: sub-patch (phase) shifts and mild scale that
  re-tile the 14/16-px patch grid → OCR should read differently or degrade).
Use the full validation splits of the counting + spatial subsets (several thousand items).

**Oracle labeling under transform (local, no paid API).** For each item and transform, the new
ground-truth answer is computed *programmatically* where possible (counting from object boxes /
scene graph; relation from coordinates; crop geometry known), and otherwise verified by a **local
judge VLM ensemble** (Qwen2.5-VL-7B + Qwen3-VL-30B-A3B as cross-check) that only certifies whether
the oracle answer changed — never used to grade the target model against itself. Items where the
transform destroys legibility (judge "unanswerable") are discarded, closing the "transform broke
the image" confound.

**STRONG attack = worst-case over the transform orbit (invariance-based).** For each item,
search a parametric transform family (integer + sub-patch translations across the full 14/16 phase
grid, crops at graded scales, flips, small rotations/scales) for the *smallest* transform (in an
ℓ2-in-pixels or a semantic-distance metric) that changes the oracle answer; record whether the VLM
answer changed. **Orbit-flip robust accuracy** = fraction correct under the worst-case
label-changing transform. This is the ρ_G-realizing attack. Add an optional **white-box orbit-flip
search** (differentiate answer-likelihood through the tower along the transform manifold) to find
minimal flips efficiently.
**Sensitivity-axis control (the other attack):** standard ℓ∞ APGD pixel attack (ε=4/255, 100 iters)
on the same items, to show the two robustness axes rank towers differently.

**Metrics.** Single-view accuracy; orbit-flip robust accuracy; per-item minimal orbit-flip
"radius" ρ_G distribution; correlation of ρ_G-robustness with pixel-robustness across the tower
pair (predict near-zero or negative). Report the η/L (sensitivity) vs ρ_G (invariance) plane with
each model as a point — the paper's "needs room under both" figure.

## Compute estimate (GPU-hours on A6000s)
Mostly inference. Grounded suite ~5–8k items × ~20–40 transform views × 2–3 models: generation is
the cost. At ~0.3 s/generation on A6000 for a 7B VLM, 8k×30×3 ≈ 720k generations ≈ ~60 GPU-h.
White-box orbit-flip search on a 1k subset adds ~10 GPU-h. Pixel-APGD control on 1k items ≈ ~6
GPU-h. Local-judge oracle verification ≈ ~10 GPU-h. **≈ 80–90 GPU-h**, ~2 days on 2×A6000. No training.

## Why standalone top-tier (what a reviewer would call the contribution)
Introduces **excessive invariance as a first-class, measurable adversarial axis for VLMs** and
shows it is *orthogonal to and not fixed by* the pixel-robustness the field optimizes — even
adversarially-robust towers stay orbit-flip-vulnerable, and can be worse. It gives a gradient-free,
perceptually-valid attack (a geometric transform, not an ℓ∞ blob) that a safety/robustness reviewer
recognizes as a genuine deployment failure (a VLM confidently miscounts / misreads after a benign
crop). The η/L–ρ_G plane is a clean conceptual contribution: "VLM robustness needs room under both
sensitivity and invariance, and the two are decoupled." Reviewer one-liner: "the same tower
engineering that makes VLMs shift-stable makes them blind to transforms that change the answer."

## Risks / kill criteria
- **Confound: transform destroys human legibility** → killed by the local-judge "still answerable"
  gate and programmatic oracle where possible.
- **Confound: base VLM just weak at grounded VQA** → report orbit-flip *conditioned on items the
  model gets right single-view*, so the flip is a genuine invariance failure, not incompetence.
- **Transform search too weak** → escalate from grid search to the white-box manifold search.
- Kill if conditioned orbit-flip rate <5%, or if pixel-robust towers are also orbit-flip-robust
  (then the two axes are not distinct and the (e) transfer collapses into (a)).
