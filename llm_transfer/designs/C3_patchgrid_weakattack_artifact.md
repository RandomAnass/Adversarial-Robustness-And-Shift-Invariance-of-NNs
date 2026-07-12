# The Patch-Grid Weak-Attack Artifact: Anti-Aliasing a VLM Vision Tower Helps Under FGSM and Vanishes Under a Strong Attack

## Transferable element (from our paper)
- (b) **The contrary "invariance helps robustness" result is a weak-attack artifact**: our paper
  retrains the invariance-helps operators (TIPS, rotation-equivariant nets) and their advantage
  reproduces under FGSM but vanishes under AutoAttack; robustness is nonzero only under
  adversarial training, where the threat-matched η/L governs, not consistency.
- (d) **Operator dissection of the downsampler**: the ViT patch embedding is a stride-14/16
  aliased downsampler; anti-aliasing / phase-marginalizing it is exactly the "anti-aliased vs
  strided vs polyphase" axis, now applied at inference time to a frozen VLM tower.

## Literature gap (specific papers checked + why open)
- The ViT anti-aliasing / shift-equivariance line — Blending Anti-Aliasing (NeurIPS 2021,
  2110.15156), Alias-Free ViT (2510.22673), Making ViTs Truly Shift-Equivariant / APS (CVPR 2024,
  2305.16316), Reviving Shift Equivariance (2306.07470), **Phase Marginalization for Patch-Grid
  Instability (2606.08132)** — measures **shift-consistency and corruption robustness and NEVER
  adversarial robustness** (fetched & confirmed for the two most-cited). None inside a VLM.
- The VLM jailbreak/robustness-benchmark line (JailBreakV-28K 2404.03027, MM-SafetyBench, IDEATOR)
  and defense papers frequently evaluate with **PGD / transfer / template attacks**, and
  "Defense-to-Attack" (2509.12724) + "Keep It Real" (2508.05489) document that such gains collapse
  under adaptive/strong attacks — but **no one has tied the weak-attack artifact to a vision-tower
  invariance/anti-aliasing intervention**.
- Robust-CLIP papers (FARE etc.) DO use strong attacks, so the artifact does not live there — the
  right target is the *non-adversarially-trained* invariance intervention, which is exactly the
  untested case.
→ Open: whether raising a VLM tower's shift-invariance (anti-aliasing / phase marginalization)
buys adversarial robustness, and whether any gain is a weak-attack mirage.

## Hypothesis (falsifiable)
Apply a **training-free invariance intervention** to a frozen VLM's vision tower — (i) anti-aliased
(blur-pooled) patch-embedding stem, and (ii) **inference-time phase marginalization** over the
patch-grid phases (2606.08132) — which measurably **raises shift-consistency**. Then:
1. **Under weak attacks** (FGSM, PGD-10, transfer/VEAttack), the anti-aliased/phase-marginalized
   tower shows a robust-accuracy **advantage** over the standard strided tower (reproducing the
   "invariance helps" reading).
2. **Under a strong attack** (APGD ensemble, 100+ iters, adaptive to the intervention incl.
   Expectation-over-Transformation for the stochastic phase-marginalization), the advantage
   **collapses to within noise** — both towers near the same (low) robust accuracy.
3. **Only under an adversarially-robust tower (FARE)** is robustness nonzero, and there the
   **threat-matched η/L**, not shift-consistency, orders the intervention variants.
Kill: if the anti-aliasing advantage survives the strong adaptive attack, invariance genuinely
helps VLM robustness and transfer (b) fails.

## Protocol (model, dataset/benchmark, attack/eval incl. STRONG attack, metrics, exact steps)
**Model + towers.** LLaVA-1.5-7B (standard CLIP tower) and, as the robust arm, LLaVA-1.5-7B with
the **FARE tower** (chs20/RobustVLM). Second VLM: Qwen2.5-VL-7B (cached) for architecture breadth.
**Interventions (frozen, no training):**
- Standard strided patch embedding (baseline / aliased).
- **Anti-aliased stem**: blur-pool (Rect-2/Tri-3/Bin-5 filters) before the patch-conv stride —
  the graded anti-aliasing family from our paper, ported to the ViT stem.
- **Phase marginalization**: average the tower output over the S×S patch-grid phase offsets at
  inference (2606.08132); a stochastic single-phase-sample variant for the EoT-adaptive attack.
- **Polyphase/APS anchor** (energy-selected phase, exactly-invariant) as the high-consistency
  extreme, ported to the stem where feasible.
Each intervention is applied identically to clean and adversarial inputs; a light projector re-fit
(≤1 epoch, only if clean CIDEr/VQA drops >3 pts) keeps clean performance comparable so that a
robustness change is not a clean-accuracy artifact (the paper's matched-clean-accuracy control).

**Measurements per intervention.** (i) shift-consistency SC (patch-grid phase sweep of downstream
answers), (ii) tower η/L (attack-free, clean), (iii) clean task score.

**Benchmark (FULL).** ImageNet zero-shot (encoder-level, high-n) + VQAv2 (~5k) + COCO captioning.

**Attacks — the whole point is the weak-vs-strong contrast.**
- **Weak**: FGSM (ε∈{1,2,4}/255), PGD-10, and a transfer attack (perturbation crafted on the
  standard tower, applied to the intervention tower) — the invariance-helps protocol.
- **Strong**: **APGD-CE + APGD-DLR ensemble, 100 iters, 5 restarts**, ℓ∞ ε∈{2,4}/255, made
  **adaptive**: BPDA-free (interventions are differentiable except phase-argmax; for APS use the
  straight-through / EoT over phases), **Expectation-over-Transformation** across phases for the
  phase-marginalized tower so the strong attack is not defeated by the stochasticity (the standard
  way to avoid a false robustness reading). Plus black-box **Square Attack** as a masking check.
- **Mandatory gradient-masking audit** (from our paper): APGD ≤ PGD-40 for every arm; report EoT
  vs no-EoT APGD gap; report Square-Attack gap. A robustness that survives weak but not strong
  *and* passes the masking audit is the artifact; a robustness that only survives because of
  masking is reported as such.

**Analysis.** For each attack strength, robust accuracy vs SC and vs η/L across interventions;
the "FGSM ordering appears, AutoAttack ordering vanishes" table (our Table on weak-vs-strong);
under the FARE tower, η/L vs strong-attack robustness across interventions.

## Compute estimate (GPU-hours on A6000s)
No pretraining; optional ≤1-epoch projector re-fit ≈ 3–5 GPU-h/arm if needed. Per intervention:
weak attacks (FGSM/PGD-10) on 5k VQA ≈ ~4 GPU-h; strong adaptive APGD (100 iter × 5 restart, EoT)
on 2k VQA through the 7B decoder ≈ ~20–25 GPU-h; ImageNet zero-shot clean+APGD (tower-only) ≈ ~6
GPU-h. ≈ 30 GPU-h/arm × ~4 interventions × 2 towers (clean + FARE) ≈ **~200 GPU-h** at full
scale; a **~70 GPU-h pilot** covers 3 interventions × 2 towers on 2k-image subsets. ~2–4 days on
2×A6000.

## Why standalone top-tier (what a reviewer would call the contribution)
A precise, causal **methodological warning** for the fast-growing VLM-robustness field: making a
VLM's vision tower more shift-invariant (the anti-aliasing/patch-grid-stability community's goal)
produces an adversarial-robustness gain that is **real under the FGSM/PGD/transfer attacks that
dominate VLM safety benchmarks and an illusion under a properly adaptive strong attack** — unless
the tower is adversarially trained, where η/L (not consistency) governs. It is the VLM incarnation
of our TIPS/rotation-equivariant retraining result, but on the exact operators (patch-grid
anti-aliasing / phase marginalization) that the ViT literature is actively pushing without ever
checking adversarial robustness. Reviewer one-liner: "anti-aliasing the patch grid looks like a
free robustness win on weak attacks and disappears under AutoAttack; strong-attack evaluation is
not optional for invariance-based VLM defenses."

## Risks / kill criteria
- **Inference-time stem swap tanks clean accuracy** (alignment mismatch) → cap with the ≤1-epoch
  projector re-fit and matched-clean-accuracy reporting; if clean collapses irrecoverably, restrict
  to phase-marginalization (which preserves the trained stem) as the primary intervention.
- **False collapse via gradient masking** (phase stochasticity defeats the attack, not real
  robustness) → the EoT-adaptive APGD + Square Attack + APGD≤PGD-40 audit is designed exactly to
  rule this in/out; report the audit, do not claim collapse without it.
- Kill (b)-transfer if the anti-aliasing advantage **survives** the adaptive strong attack on a
  non-robust tower with the masking audit passed — that would be genuine evidence invariance helps
  VLM robustness, which we would report honestly.
