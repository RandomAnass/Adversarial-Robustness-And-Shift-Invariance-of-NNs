# Agent C literature sweep — VLM / multimodal lens

Lens: adversarial images against VLMs; the vision encoder (ViT) patch embedding as an
aliased stride-14/16 downsampler; CLIP shift-consistency; whether vision-encoder invariance
predicts / anti-predicts VLM adversarial robustness; weak-vs-strong attack artifacts in the
VLM robustness literature; margin/Lipschitz (η/L) diagnostics computed **through a frozen
vision tower**.

Legend for each entry: **[COVERS]** a transfer (we must not re-do it), **[BLOCKS]** (an
assumption that would invalidate a transfer), **[OPEN]** (leaves the transfer available).
Transfer labels map to the paper elements:
- (a) shift-consistency does NOT order robustness; anti-predicts under AT; threat-matched η/L predicts.
- (b) "invariance helps robustness" = weak-attack artifact (FGSM reproduces, AutoAttack kills).
- (c) η/L attack-free diagnostic (margin over dual-norm input-gradient), computable through a frozen tower.
- (d) capacity-matched operator dissection (anti-aliased vs strided vs polyphase downsampling).
- (e) excessive invariance / orbit-flip (invariance to a transform that SHOULD change the answer).

--------------------------------------------------------------------------------
## 1. ViT shift-invariance / aliasing literature (the (d) operator family, in ViTs)

The single most important finding of this sweep: **the ViT shift-invariance / anti-aliasing
line measures shift-consistency and corruption robustness, and NEVER adversarial robustness,
and none of it is done inside a VLM.** This is precisely the unmade bridge our paper's
dissociation predicts.

- **Rojas-Gomez et al., "Making Vision Transformers Truly Shift-Equivariant," CVPR 2024**
  (arXiv:2305.16316). Adaptive tokenization (A-token, energy-selected patch grid), adaptive
  window self-attention, **Adaptive Polyphase Sampling (APS)** patch merging, adaptive RPE;
  achieves *perfect circular shift-equivariance* on Swin/SwinV2/CvT/MViTv2. FETCHED &
  CONFIRMED: **no adversarial robustness anywhere** — they measure only shift-consistency,
  clean accuracy, mIoU. This is the ViT analog of our "exact cyclic / APS" arm.
  → **[OPEN]** for (a),(b),(d): nobody measured adversarial robustness of a truly-shift-
  equivariant ViT, let alone in a VLM.

- **Ding et al., "Reviving Shift Equivariance in Vision Transformers"** (arXiv:2306.07470).
  Polyphase-anchoring for strided conv + window attention + subsampled global attention →
  circular shift-invariant ViT for classification. Consistency only. → **[OPEN]** for adversarial.

- **"Alias-Free ViT: Fractional Shift Invariance via Linear Attention"** (arXiv:2510.22673).
  Alias-free downsampling + nonlinearities + linear cross-covariance attention; shift-invariant
  to integer AND fractional translations. Consistency/clean acc only. → **[OPEN]** for adversarial + VLM.

- **Qian et al., "Blending Anti-Aliasing into Vision Transformer," NeurIPS 2021**
  (arXiv:2110.15156). Aliasing-Reduction Module (Gaussian/learnable/filter-bank smoothing on
  early attention maps). FETCHED & CONFIRMED: measures **ImageNet-C corruption robustness
  only** (mCE 59.8 vs 60.7), data-efficiency, generalization — **no FGSM/PGD/AutoAttack**.
  This is the ViT analog of our "anti-aliased blur-pool" arm. → **[OPEN]** for (b),(d).

- **"Phase Marginalization for Patch-Grid Instability in Vision Transformers"**
  (arXiv:2606.08132). Names the "patch-grid instability" from the non-overlapping tokenization
  grid; marginalizes over a discrete set of patch-grid phases **at inference time** on an
  already-trained ViT. Consistency-oriented. → **[OPEN]** but ALSO a **[TOOL]**: an inference-time,
  training-free invariance intervention we can drop onto a frozen VLM vision tower (used in C3).

- **"Octic Vision Transformers: Quicker ViTs Through Equivariance"** (arXiv:2505.15441).
  Dihedral-group (rotation/reflection) equivariant ViT; efficiency motivation. → **[OPEN]** for adversarial.

- **"Improved Robustness of ViT via PreLayerNorm in Patch Embedding"** (arXiv:2111.08413) and
  **"Towards Robust Vision Transformer," CVPR 2022** (Mao et al.). Robustify the patch-embed /
  attention for *corruption / natural* robustness. → **[OPEN]** for adversarial dissociation.

- **"Unraveling Patch Size Effects in ViTs: Adversarial Robustness in Hyperspectral
  Classification"** (MDPI Remote Sensing 2024). One of the very few to touch ViT patch geometry
  AND adversarial robustness: smaller patches (1×1, 3×3) → higher adversarial accuracy, larger
  patches amplify localized perturbations. Narrow domain (hyperspectral), no VLM, no shift-
  consistency vs robustness dissociation, no η/L. → **[OPEN]** but a partial precedent to cite:
  patch-grid geometry does modulate adversarial robustness.

- **"Unlocking Noise-Resistant Vision: Key Architectural Secrets for Robust Models"**
  (arXiv:2509.20939). Anti-aliased downsampling reduces high-frequency sensitivity; output noise
  energy decays with stem kernel size / anti-aliasing factor. Natural-noise framing. → **[OPEN]** adversarial.

**Net for section 1:** the entire ViT invariance-operator family is a ready-made (d)-style
operator panel that has *never* been evaluated for adversarial robustness inside a VLM. Both
the "invariance helps" (anti-aliased) and the "exactly invariant" (polyphase/APS/alias-free)
arms exist as released or trivially-portable operators. This is the strongest opening.

--------------------------------------------------------------------------------
## 2. Robust CLIP / vision-encoder adversarial fine-tuning

These provide the *robust-tower* arms for an η/L dissection, and — importantly — they ARE
evaluated with strong attacks, so the weak-attack-artifact claim (b) does NOT apply to them;
it applies to the ViT-invariance line (section 1) and the jailbreak-defense line (section 5).

- **Schlarmann et al., "Robust CLIP: Unsupervised Adversarial Fine-Tuning of Vision
  Embeddings" (FARE), ICML 2024** (arXiv:2402.12336; repo chs20/RobustVLM). FETCHED &
  CONFIRMED: FARE loss `max_{‖z−x‖∞≤ε} ‖φ(z)−φ_org(x)‖²`; evaluated with **strong attacks** —
  APGD-CE + APGD-DLR (100 iters) for zero-shot, 100-iter APGD pipeline for VLM untargeted,
  **10,000-iter** APGD for targeted stealth; ε ∈ {2/255, 4/255}. VLMs: **LLaVA-1.5-7B,
  OpenFlamingo-9B**; benchmarks: COCO/Flickr30k captioning (CIDEr), VQAv2/TextVQA, ImageNet+13
  zero-shot, POPE, SQA-I. **No shift-consistency, aliasing, or margin/Lipschitz η/L anywhere.**
  → **[OPEN]** for (a),(c),(d): FARE is a perfect ready-to-use robust-tower arm whose *shift-
  consistency* and *η/L* nobody has computed, and whose robustness nobody has related to those.
  Also provides the LLaVA integration we need (no training).

- **Hossain & Imteaj, "Sim-CLIP: Unsupervised Siamese Adversarial Fine-Tuning," 2024**
  (arXiv:2407.14971). Siamese cosine-loss improvement over FARE; more semantically-rich robust
  embeddings. Strong-attack evaluated. → **[OPEN]** for the diagnostic/dissociation; another arm.

- **Mao et al., TeCoA, ICLR 2023** ("Understanding zero-shot adversarial robustness of CLIP").
  First zero-shot robust CLIP; supervised text-guided contrastive AT on ImageNet labels. Strong-
  attack evaluated. → **[OPEN]** for η/L; a lower-clean-accuracy arm (heavy distortion on unseen classes).

- **Wang et al., "Double Visual Defense," 2025** (arXiv:2501.09446). ΔCLIP (adversarial
  vision-language pretraining from scratch on web-scale) + Δ²LLaVA (adversarial visual
  instruction tuning); SOTA robust VLM, +~20% ImageNet-1k zero-shot robustness over prior,
  little clean cost; AutoAttack-evaluated. → **[OPEN]** the strongest robust-tower arm; its η/L
  and shift-consistency are unknown.

- **"What Makes VLMs Robust? Towards Reconciling Robustness and Accuracy in VLMs"**
  (arXiv:2603.12799). Robustness-accuracy tradeoff in VLMs. Relevant framing but does not use
  shift-consistency or η/L. → **[OPEN]**.

--------------------------------------------------------------------------------
## 3. Adversarial attacks ON VLMs (attack side)

- **Zhao et al., "On Evaluating Adversarial Robustness of Large VLMs," NeurIPS 2023**
  (arXiv:2305.16934, "AttackVLM"). Transfer + query-based (RGF) black-box attacks matching
  image CLIP/BLIP features to target-image features; ε=8/255 ℓ∞; VLMs BLIP/BLIP-2/MiniGPT-4/
  LLaVA/UniDiffuser + commercial Bard/Bing/GPT-4V/ERNIE. Aligning to a *target image* transfers
  better than to *target text*. No shift-consistency / aliasing / η/L. → **[OPEN]**.

- **Zhang et al., "Adversarial Illusions in Multi-Modal Embeddings," USENIX Sec 2024**
  (arXiv:2308.11804). Perturb an image so its embedding sits near an adversary-chosen target in
  another modality; task/modality-agnostic; illusions transfer within (not across) architectures,
  fixable by joint multi-surrogate optimization. Exploits embedding proximity — i.e. exactly the
  low-η/L corner in embedding space, but never framed as margin/Lipschitz. → **[OPEN]** for (c).

- **"VEAttack: Downstream-agnostic Vision Encoder Attack against LVLMs"** (arXiv:2505.17440).
  FETCHED: attacks the **vision-encoder token/CLS features** directly (downstream-agnostic),
  PGD ℓ∞; CLIP/Qwen-VL/MiniGPT-4/LLaVA/OpenFlamingo/Gemini; ImageNet/COCO/Flickr30k. Confirms
  "attack the tower, break the VLM." **No invariance/aliasing/η/L diagnostics.** → **[OPEN]** and a
  strong justification for evaluating the *tower* as the load-bearing component.

- **"Image Hijacks: Adversarial Images Control Generative Models at Runtime"** (image-hijacks.
  github.io). White-box PGD behaviour-matching; up to 91% ASR on LLaVA. Attack-capability paper,
  no diagnostic. → context.

- **"Revisiting the Adversarial Robustness of VLMs: a Multimodal Perspective"**
  (arXiv:2404.19287). Key *cited* claim: image-based robustness is **less sensitive to LLM
  size**; strengthening the **vision encoder's** robustness is largely sufficient; robustness
  also depends on cross-modal-alignment stability. Proposes MMCoA (multimodal contrastive AT).
  → **[SUPPORTS]** the premise that the tower governs VLM adversarial robustness (motivates all
  three designs); does not use shift-consistency or η/L → **[OPEN]** for the diagnostic.

--------------------------------------------------------------------------------
## 4. Certified robustness / attack-free diagnostics for VLMs

- **"Randomized Smoothing Meets Vision-Language Models"** (arXiv:2509.16088). FETCHED:
  certifies via an **oracle (LLM) classification layer** over noisy outputs + majority vote;
  ℓ2 radii ~0.42–0.60 at σ=0.5, 10k samples; LLaVA-1.6-7B, Llama-3.2-11B, Gemma-2-9B oracle;
  jailbreak / MM-SafetyBench. Randomized-smoothing, output-level. **No deterministic
  margin/Lipschitz η/L through the tower, no invariance-operator dissection.** → **[OPEN]** for (c).

- **"Fast Certification of VLMs Using Incremental Randomized Smoothing" / Open-Vocabulary
  Certification (OVC)** (arXiv:2311.09024). Fast RS certification for CLIP-based open-vocab
  classifiers. RS, not deterministic η/L. → **[OPEN]**.

- **"Provably Robust Adaptation for Language-Empowered Foundation Models" (LeFCert-L)**
  (arXiv:2510.08659) and **"Provable Robustness in MLLMs via Feature Space"** (arXiv:2601.16200).
  RS + Lipschitz-in-feature-space certificates. Feature-space, not the shift-invariance / η/L
  dissociation. → **[OPEN]**.

- **Ngnawe et al., "Detecting Brittle Decisions for Free: Leveraging Margin Consistency,"
  2024** (arXiv:2406.18451; cited in our paper as ngnawe2024detecting). Correlation between
  logit/output margin and input-space margin lets you flag non-robust samples **attack-free** —
  but studied on **plain adversarially-trained image classifiers (RobustBench), NOT VLMs/CLIP.**
  → **[OPEN]**: the attack-free margin diagnostic has never been carried *through a VLM vision
  tower*. This is the closest prior to our (c) transfer and confirms it is open for VLMs.

- **"Beyond Accuracy: What Matters in Designing Well-Behaved Image Classification Models?"**
  (arXiv:2503.17110) and **"Toward a Holistic Evaluation of Robustness in CLIP Models"**
  (arXiv:2410.01534). Multi-property CLIP robustness audits (corruption, invariance, OOD). Do
  NOT relate shift-consistency to adversarial robustness via η/L. → **[OPEN]**.

--------------------------------------------------------------------------------
## 5. VLM robustness / jailbreak benchmarks and their attack strength (the (b) target)

The claim we transfer for (b): a large slice of VLM robustness/jailbreak-defense work reports
robustness under **PGD / transfer / weak** attacks, and gains evaporate under adaptive/strong
attacks. Confirmed as a live, documented problem — but not yet tied to *vision-tower invariance
operators*.

- **JailBreakV-28K** (arXiv:2404.03027), **MM-SafetyBench** (5,040 pairs, 13 scenarios),
  **IDEATOR** (ICCV 2025), **JailbreakZoo** survey (arXiv:2407.01599). Image-jailbreak
  benchmarks; attacks are typically PGD / transfer / template-image, not APGD/AutoAttack-grade
  optimization. → **[SUPPORTS]** (b): weak-attack prevalence in VLM safety evals.

- **"Defense-to-Attack: Bypassing Weak Defenses Enables Stronger Jailbreaks in VLMs"**
  (arXiv:2509.12724); **"Keep It Real: Challenges in Attacking Compression-Based Adversarial
  Purification"** (arXiv:2508.05489). Document that many VLM defenses look robust only because
  the evaluation attack is weak / obfuscates gradients; **gradient-masking / adaptive-attack
  collapse** explicitly discussed. → **[SUPPORTS]** (b), and give us the adaptive-attack
  methodology to use, but do NOT frame the artifact around *shift-invariance operators*. → **[OPEN]**.

- **"Time-Efficient Evaluation and Enhancement of Adversarial Robustness in DNNs"**
  (arXiv:2512.20893). Efficient strong-attack evaluation methodology. → **[TOOL]**.

--------------------------------------------------------------------------------
## 6. Excessive invariance / semantic-invariance failures (the (e) target)

- **Jacobsen et al., "Excessive Invariance Causes Adversarial Vulnerability," ICLR 2019** and
  **Tramèr et al., "Fundamental Tradeoffs between Invariance and Sensitivity to Adversarial
  Perturbations," ICML 2020** (our tramer2020fundamental). Invariance-based adversarial examples
  = a transform that changes the oracle label but not the model's — exactly our ρ_G orbit-flip
  bound. Studied on **classifiers**, not VLMs. → **[OPEN]** for the VLM analog.

- **"Semantic Adversarial Examples"** (arXiv:1804.00499) and **"Semantic Adversarial Attacks:
  Parametric Transformations," ICCV 2019** (arXiv:1907...). Semantics-preserving vs semantics-
  changing transforms. Classifier-level. → context for (e).

- **"Same Answer, Different Representations: Hidden Instability in VLMs"** (arXiv:2602.06652).
  (PDF too large to fully fetch.) Title/abstract: VLMs give the same answer while their hidden
  representations are unstable — the *inverse* worry to excessive invariance (representation
  moves, answer fixed). Relevant framing that VLM answer-stability and representation-stability
  decouple. → **[OPEN]** for a principled orbit-flip / excessive-invariance treatment tied to η/L and ρ_G.

- **"Boosting the Local Invariance for Better Adversarial Transferability"** (arXiv:2503.06140)
  and scale-invariant gradient attacks: use *input invariances* to strengthen attacks (transfer),
  not to diagnose excessive invariance. → context.

- VLM spatial/counting/OCR grounding benchmarks (e.g. CV-Bench, MMVP, BLINK, VSR, TallyQA,
  CLEVR) are the natural substrate for orbit-flip tests: tasks where a geometric transform
  SHOULD change the answer. None framed as excessive-invariance robustness. → **[OPEN]**.

--------------------------------------------------------------------------------
## 7. Summary of what is BLOCKED vs OPEN

**Nothing found blocks the four transfers.** Strongest supports and openings:
1. ViT invariance-operator line (polyphase/anti-aliased/alias-free/phase-marginalized ViTs)
   measures shift-consistency + corruption but **never adversarial robustness, never in a VLM**
   → (a),(b),(d) wide open, with ready operators.
2. Robust-CLIP line (FARE/TeCoA/Sim-CLIP/ΔCLIP) is strong-attack-evaluated but **never computes
   shift-consistency or η/L, never relates them to robustness** → (a),(c),(d) open, with ready
   drop-in encoders + LLaVA integration (chs20/RobustVLM) → no training needed.
3. Attack-free margin diagnostic (Ngnawe 2024) exists **only for plain classifiers** → (c) open
   for VLM towers.
4. Excessive-invariance / orbit-flip theory (Jacobsen 2019, Tramèr 2020) exists **only for
   classifiers**; VLM semantic-invariance failures are documented but not framed as ρ_G/orbit-flip
   robustness → (e) open.
5. "Revisiting Adversarial Robustness of VLMs" establishes the tower governs VLM image-robustness,
   which de-risks studying the tower in isolation.

**One caveat (partial block for the naive (b) framing):** the *robust-CLIP* papers already use
strong attacks, so we must NOT claim "the robust-CLIP literature over-reports via weak attacks."
The (b) artifact belongs to the **ViT-invariance line** and the **jailbreak-defense line**, which
is where C3 aims.
