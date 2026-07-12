# Round-1 Literature Adversary — Lens C (VLM / multimodal) pilot designs

Adversarial audit of C1 / C2 / C3 against the literature, before compute. Method: every
load-bearing cited paper was verified by downloading the PDF and reading the relevant sections
(not abstracts); missing-literature hunts run by three parallel adversarial search agents with
verbatim-quote discipline. PDFs saved under `llm_transfer/adversarial/pdfs/`.

Priority applied throughout: one robust, strong-attack, single-benchmark run that stands alone at a
top venue — not an addendum. VLM attacks are compute-heavy; feasibility on 2×A6000 48GB is flagged
per design.

---

## Cross-cutting finding (affects ALL THREE designs) — a shared miscitation

**The "vision tower governs VLM adversarial robustness" premise is miscited.** `agentC.md` (and all
three designs, which inherit it) attribute this de-risking claim to **"Revisiting Adversarial
Robustness of VLMs" (arXiv:2404.19287)**. I read 2404.19287 in full (`RevisitingAdvRobVLM_2404.19287.pdf`):
it is **MMCoA**, a *multimodal* contrastive adversarial-training method operating on **CLIP itself**
(zero-shot classification on 4 datasets). It does **not** compare LLM backbones (no LLaVA/Vicuna/
MiniGPT anywhere in the text), so it **cannot** support "image robustness is less sensitive to LLM
size / the tower is largely sufficient." Its actual thesis is the *opposite* emphasis — that the
field over-focuses on the image encoder and neglects text/multimodal robustness.

**The correct citation for the tower-governs claim is arXiv:2407.11121** ("Towards Adversarially
Robust VLMs: Insights from Design Choices and Prompt Formatting Techniques"), which I downloaded and
read (`TowardsAdvRobVLM_designchoices_2407.11121.pdf`). It compares **Vicuna-7B vs 13B with the same
vision encoder** and finds (verbatim, p.5): "accuracy remain consistent, regardless of the model's
scale… adversarial attacks compromise the representations from the vision encoder. As a result, LLMs
[do not help]." It uses APGD (100 iters), PGD, FGSM at ε∈{4,8,16}/255. This is the paper that
actually de-risks the tower-only diagnostic. **Fix in all three designs: swap 2404.19287 → 2407.11121
for the tower-governs premise** (keep 2404.19287 only if you want the multimodal-attack angle, and
then describe it correctly). This is a strict improvement — the premise is *better* supported than the
designs realized, just wrongly sourced.

---

## C1 — "Shift-consistency does not order VLM robustness; a tower η/L does"

### VERDICT: **SURVIVES — needs-fix (wording + panel + one added citation), and is the strongest of the three.**

The two-part core (shift-consistency of a frozen VLM tower does **not** order strong-attack robustness,
while tower-computed η/L on clean inputs **does**, as an attack-free selection rule) is **unclaimed** in
the literature I could reach. But two novelty overclaims must be softened, and the no-training panel is
narrower than stated.

### Papers downloaded + read (1-line findings)
- **FARE / Robust-CLIP, ICML 2024 (2402.12336)** — read `FARE_2402.12336.pdf`. Uses genuinely strong
  attacks (APGD-CE + targeted APGD-DLR ensemble, 100 iters zero-shot; up to 10,000-iter targeted VLM).
  **Zero** shift-consistency / anti-aliasing / Lipschitz / margin content (only colloquial "by a large
  margin" and a cited-title "invariant"). → confirms C1's gap: FARE never computes SC or η/L. Also
  confirms it ships drop-in LLaVA towers → Route A no-training is real.
- **Ngnawe et al., NeurIPS 2024 (2406.18451)** — read `Ngnawe_MarginConsistency_2406.18451.pdf`.
  Margin-consistency (logit-margin ↔ input-margin) is a **per-sample, attack-free vulnerability signal
  on RobustBench plain CIFAR-10/100 classifiers only** — no CLIP/VLM, no cross-encoder ranking, no
  shift-consistency. C1's characterization is accurate; it is the correct "point of departure."
- **2407.11121** (see cross-cutting) — the real tower-governs source.
- **RobustVLM repo (chs20/RobustVLM)** — verified via README fetch: ships **only** {FARE2, FARE4,
  TeCoA2, TeCoA4} as drop-in LLaVA towers with `llava_eval.sh`. **Does NOT ship Sim-CLIP or ΔCLIP.**

### Missing papers the designer never saw
- **RDI, "Adversarial robustness evaluation from clustering features" (2504.18556, 2025)** —
  **[PARTIAL scoop of the "attack-free predictor" novelty].** Verified by fetch: an explicitly
  *attack-independent* metric from **clean intra/inter-class feature distances** that correlates with
  attack-success-rate at ~1/30 PGD cost. Plain classifiers only; feature-clustering geometry, **not**
  margin/Lipschitz, **not** invariance, **no** encoder ranking. It does **not** close C1's gap, but it
  **kills** any claim that "attack-free robustness prediction from clean statistics has never been done."
  → **Must cite; reframe novelty.**
- **Singla & Ge, "Shift Invariance Can Reduce Adversarial Robustness," NeurIPS 2021 (2103.02695)** —
  **[MUST CITE — supports, does not scoop].** Classifier-level theory+experiment that shift invariance
  (a near-identical shift-consistency %) *reduces* adversarial robustness. This is C1's motivation, not
  a competitor — it is the reason SC should fail to order robustness. Must cite prominently; the paper's
  own related work likely already has it (`ge2021shift` in `main.tex`) but the *VLM design* omits it.
- **ICLR 2025 CLIP-purification paper** (surfaced by the C1 agent; OpenReview TQ2ZOy6miT) —
  **[narrows one wording].** Computes logit-margin and *effective local Lipschitz* through a CLIP
  encoder — but as post-hoc mechanism analysis of one purification defense, not a cross-encoder
  attack-free selector. → soften "η/L has NEVER been computed through a CLIP tower."
- **"What Makes VLMs Robust? / R-Adapt" (2603.12799)** — **[BLOCKS an assumption, read before finalizing].**
  Argues VLM adversarial robustness is localized in shallow layers / driven by low-frequency spectral
  bias + input-insensitive attention. Risk: a referee says "spectral bias already explains this," and it
  complicates the assumption that a single tower-level η/L summarizes robustness. Pre-empt with a
  paragraph distinguishing "spectral bias as training motivation" from "η/L as attack-free cross-tower
  selector."

### Corrections (framing / statements / gap / protocol)
1. **Reframe the two novelty overclaims.** Not "first margin/Lipschitz through a CLIP tower" (ICLR'25
   purification did local-Lipschitz through CLIP) and not "attack-free robustness prediction from clean
   stats has never been done" (RDI). The defensible, unclaimed contribution is: **cross-tower, attack-free,
   robustness-*ranking* use of a threat-matched η/L on a frozen panel, paired against a shift-consistency
   null result.** State it exactly that way.
2. **Fix the panel.** RobustVLM ships only clean-CLIP + FARE2/4 + TeCoA2/4 as no-training LLaVA drop-ins
   → 5 towers, and 4 of them are AT variants that will **cluster** in SC and η/L (C1's own collinearity
   kill-risk). Sim-CLIP (2407.14971) and ΔCLIP (2501.09446) are **not** in the RobustVLM LLaVA harness —
   adding them is extra integration, not "no training." To widen the invariance axis without training, add
   the **standard non-robust anti-aliased/APS ViT** arm at the *encoder* (ImageNet zero-shot) level, where
   there is no projector to realign — that is where SC ranges widely and the anti-prediction appears.
3. **Cite RDI, 2103.02695, 2407.11121; soften the two "never" sentences.** Keep Ngnawe as departure point.
4. **Protocol keep:** APGD-CE+APGD-DLR ensemble + Square-Attack masking check + APGD≤PGD-40 audit are all
   correct and match FARE's own protocol. The partial-correlation-controlling-clean-score is the
   load-bearing analysis — keep it as the headline, not the raw η/L–S number (matches the paper's caveat).

### Feasibility on 2×A6000
The 6-tower / full-ImageNet-50k / 5k-VQA plan at ~130–160 GPU-h is **realistic** as a 3–4 day run.
**Recommend the ~60 GPU-h pilot** (10k ImageNet + 2k VQA, 5 real drop-in towers) as the *standalone*
paper: the encoder-level ImageNet arm alone (tower-only APGD, no 7B decoder in the loop) is cheap,
high-n, and already demonstrates SC-fails / η/L-predicts. This is the one run that stands alone.

---

## C2 — "Excessive invariance / orbit-flip in VLMs; ρ_G vs η/L two-axis"

### VERDICT: **SURVIVES — needs-fix (hard differentiation + 4 mandatory citations). Highest scoop-risk of the three; also the most conceptually novel if differentiated.**

No verified prior defines or measures ρ_G (smallest oracle-flipping geometric transform on grounded VQA
where the VLM answer stays fixed) as an adversarial axis, and none correlates it with pixel η/L on the
same VLMs or tests whether FARE is worse on it. But one 2026 paper shares the *narrative* and will read
as a scoop unless C2 differentiates sharply.

### Papers downloaded + read / verified
- **Jacobsen et al., "Excessive Invariance Causes Adversarial Vulnerability," ICLR 2019 (1811.00401)**
  + **Tramèr et al., ICML 2020 (`tramer2020fundamental`)** — already in the repo's `pdfs/`. These *define*
  invariance-based adversarial examples exactly as C2 uses them ("changes that leave the model's
  prediction unaffected despite the input's label having changed") — on **classifiers, pre-VLM, no
  geometric orbit, no grounded VQA**. This is C2's axis definition. **Must cite as foundation.**
- **FARE (2402.12336)** — read (see C1). Its own claim that robustification is "marginal" vs CLIP on
  reasoning tasks is a **double-edged sword**: a referee will use it to call C2's "FARE no better on
  orbit-flip" result *unsurprising*. Pre-empt: FARE's reasoning eval is coarse VQA, never
  counting-under-crop or left/right-under-flip.

### Missing papers the designer never saw
- **"Semantic Richness or Geometric Reasoning? The Fragility of VLM's Visual Invariance"
  (arXiv:2604.01848, Apr 2026)** — **[PARTIAL scoop of the narrative — the single biggest C2 threat].**
  Verified by fetch of the verbatim abstract: shares C2's thesis ("fundamental fragility of VLMs under
  basic geometric transformations… lack of robust spatial invariance and equivariance"). BUT: **no**
  orbit-flip / excessive-invariance *metric* (uses accuracy/TPR/TNR); tests only **rotation/scaling/
  identity-matching**, not C2's label-changing orbit (crop-removes-object, translation-across-boundary,
  phase-shift); tasks are object-identity, **not** counting/spatial-VQA/OCR; **no** adversarial/L∞/FARE
  link. → **Not a protocol scoop, but a narrative one. Must cite prominently and frame C2 as
  operationalizing (metric + ρ_G↔η/L link + robust-tower test) what they left qualitative.**
- **VLM-RobustBench (2603.06148, Mar 2026)** — **[trap / must-cite contrast].** Verified: measures the
  **opposite direction** — label-*preserving* corruptions (49 augmentations incl. flips, "spatially
  fragile," answer-flip = correct→wrong under corruption). Verbatim: "corruptions are applied to images
  only… in the absence of an adaptive attacker." It **never** scores a model wrong for *keeping* the same
  answer. → perfect **foil**: C2's whole point is that holding the answer fixed under a label-changing
  flip is the *failure*. Cite as contrast; zero scoop, but omitting it invites a desk-flag.
- **"Same Answer, Different Representations" (2602.06652)** — **[trap — mirror image].** Studies
  label-*preserving* perturbations where the model *correctly* keeps the answer but the representation
  drifts. Its "same answer" is the desirable case; C2's is the failure case. Cite to sharpen the
  definition; does not close the gap.
- Secondary (report for completeness, cite lightly): "On the Limitations of VLMs in Understanding Image
  Transforms" (2503.09837, opposite task — wants the model to *detect* the transform); "Why Far Looks Up"
  (2605.30161, closest whiff that geometric ≠ pixel robustness, but representation-structure, not an
  η/L-vs-ρ_G correlation). One **loose end flagged by the agent, unverified**: "Audit of VLM Robustness to
  Natural Semantic Variation" (2604.04473) — PDF was image-only; framing suggests label-preserving
  corruption robustness, low scoop probability, **read before final submission**.

### Corrections
1. **Differentiate from 2604.01848 in the first page**, not a footnote. Your three separators: (i) a
   *metric* (minimal oracle-flipping transform where the VLM stays fixed), (ii) the ρ_G↔η/L two-axis
   correlation on the same models, (iii) the robust-tower (FARE) comparison. None exist in 2604.01848.
2. **Cite the mandatory five or expect desk-flagging:** 1811.00401 + Tramèr-ICML2020 (axis definition),
   2604.01848 (nearest narrative scoop), 2603.06148 (opposite-framing foil), 2602.06652 (mirror image),
   2402.12336 (robust-tower premise).
3. **Protocol tightening (the real risk).** The "oracle answer changed" labeling is the load-bearing step
   and the most attackable. Prefer **programmatic oracle only** (counting from boxes/scene-graph;
   left/right from coordinates; crop geometry known) for the headline result; treat the local-judge-VLM
   ensemble as a *filter for legibility*, never as a relabeler of the target's own class, and report
   headline numbers on the programmatic-oracle subset so no referee can attack the judge. Keep the
   "conditioned on items the model gets right single-view" control — it is what makes the flip a genuine
   invariance failure rather than incompetence.
4. **Sharpen hypothesis 2** so it is not pre-empted by FARE's "marginal" claim: predict FARE is *worse*
   (not merely "no better") on ρ_G because L∞ AT smooths the tower, and back it with the mechanism, so a
   null result is still informative.

### Feasibility on 2×A6000
~80–90 GPU-h, mostly inference (~720k generations). **Realistic**, but the generation count is the whole
cost and 0.3 s/gen for a 7B VLM is optimistic under batched sampling with long grounded prompts — budget
1.5–2×. The **white-box orbit-flip manifold search adds real engineering** (differentiating answer
log-likelihood through the tower along a transform manifold); make it optional, not load-bearing. The
grid-search orbit alone is a valid strong gradient-free attack and is the safer "one run."

---

## C3 — "Anti-aliasing a VLM tower helps under FGSM, vanishes under a strong attack"

### VERDICT: **NEEDS-FIX bordering on KILL as currently framed — the gap is mostly CLOSED. Survives only if radically repositioned to the one untested operator (APS/polyphase ViT stem + inference-time phase-marginalization) and stripped of the blur-pool/Gaussian arm.**

The "smoothing/invariance helps under weak attacks and collapses under strong adaptive attacks" punchline
is **established since 2018 for classifiers**, the anti-aliasing↔adversarial link is **already
strong-attack-tested for CNNs**, and a **Gaussian low-pass filter on a frozen CLIP tower has already been
run under AutoAttack**. C3's stated gap ("the anti-aliasing line NEVER measures adversarial robustness")
is **factually false** for the CNN anti-aliasing papers and must be corrected.

### Papers downloaded + read / verified
- **Making ViTs Truly Shift-Equivariant, CVPR 2024 (2305.16316)** — read
  `MakingViTsShiftEquiv_2305.16316.pdf`. grep {adversar,attack,PGD,FGSM} = **0 method hits**; every
  "robust" is shift-robustness / OOD (erased patches, flips) / segmentation-under-shift. **Confirmed: never
  tests adversarial robustness.** C3's claim holds *for this ViT paper.*
- **Blending Anti-Aliasing, NeurIPS 2021 (2110.15156)** — read `BlendingAntiAliasing_2110.15156.pdf`. Only
  "adversarial" hit is a bibliography reference [61]; all "robust" = corruptions/ImageNet-C. **Confirmed:
  never tests adversarial robustness.** Holds *for this ViT paper.*
- **Phase Marginalization (2606.08132)** — read `PhaseMarginalization_2606.08132.pdf` (full). It is a
  **dense-prediction (segmentation/depth/matching) test-time-augmentation** method: it inverse-aligns and
  averages **per-pixel dense outputs** back to image coordinates, K=4 phases, single-author TUBITAK
  preprint. **Zero adversarial content; NOT a stem intervention; its mechanism (inverse-align dense
  outputs) does not map onto a pooled CLS/global VLM embedding** — a VLM VQA/caption task has no dense
  per-pixel map to inverse-align. → **C3's plan to use it as a drop-in tower invariance intervention is a
  method misfit.** What C3 actually wants is "average the pooled tower embedding over patch-grid phase
  offsets," which is plain phase-averaging TTA — cite 2606.08132 for the *phenomenon* (patch-grid phase as
  a nuisance), but do not claim to be *using its method*.

### Missing papers the designer never saw — these are what damage C3
- **Grabinski et al., "Aliasing and adversarial robust generalization of CNNs," ECML 2022** + **FLC
  Pooling, ECCV 2022 (2204.00491)** + **ASAP (2307.09804)** —
  **[establishes-punchline-for-classifiers-already + PARTIAL operator scoop].** These evaluate
  anti-aliasing / aliasing-free pooling **under AutoAttack + APGD + PGD-with-restarts** at ε∈{1,4,8}/255
  and find anti-aliasing gives **real (modest, mostly-L2) adversarial-robustness gains**, and
  anti-aliasing + AT beats AT alone on L2. **This is exactly "does anti-aliasing help under a strong
  attack," answered for CNNs — a qualified yes, not a pure mirage.** Note: this is the very paper the
  team's own manuscript cites as `grabinski2022aliasing` ("invariance helps"). C3 must correct its gap
  sentence and engage this nuance (architectural anti-aliasing is *not* a clean weak-attack artifact for
  CNNs; the paper's own resolution is that η/L governs *in the AT regime* — so C3's "vanishes under
  AutoAttack" arm must be the **non-AT** tower, matching the paper's theory exactly).
- **Rodriguez-Muñoz & Torralba, "Aliasing is a Driver of Adversarial Attacks" (2212.11760)** —
  **[establishes-punchline-for-classifiers-already].** A **training-free, structural** anti-aliasing
  intervention *for adversarial robustness* (Quantile-ReLU) — precisely C3's genre. Weakens the
  "training-free anti-aliasing for adversarial robustness is novel" angle for classifiers.
- **"What Makes VLMs Robust? / R-Adapt" (2603.12799)** — **[PARTIAL scoop — the single biggest C3 threat].**
  Verified via fetch: introduces a **Gaussian low-pass Input Filter before the embedding layer of a
  FROZEN CLIP tower** ("robust models suppress high-frequency components… attenuating high-frequency noise
  exploited by adversarial perturbations"), evaluated **under AutoAttack (APGD) at ε=4/255**. This is
  almost exactly C3's "low-pass smoothing in a frozen VLM tower under strong attack." It differs from C3
  only in: (i) raw-input Gaussian blur, **not** stem-level anti-aliasing/APS/phase-marg; (ii) it is
  pitched as a *working defense* + a **trained** Fixed Robustness Anchor (so not purely training-free);
  (iii) I could not confirm a *filter-alone weak-vs-strong ablation*. → **C3 must cite it, must sharpen its
  operator to stem-level / phase-marg (not raw Gaussian), and must run the explicit filter-only
  weak-vs-strong ablation R-Adapt did not.**
- **Athalye et al., "Obfuscated Gradients," ICML 2018 (1802.00420)** — **[the punchline's canonical
  source].** BPDA + EoT; breaks input-transformation/randomization/smoothing defenses. **C3's mechanism is
  a direct instance since 2018.** Non-negotiable citation; C3 cannot claim conceptual novelty for the
  mechanism, only for the operator+VLM setting.
- **"Ensemble Everything Everywhere Is Not Robust" (2411.14834)** — **[the modern blueprint].** Breaks a
  2024 defense built on stochastic multi-scale aggregation with PGD-500 + transfer + **EoT**; robust acc
  48%→1%. This is the closest published template to C3's stochastic-phase-marginalization + EoT collapse.
  Cite as the acknowledged blueprint so reviewers see the result is expected.
- **Xie (1711.01991) / Guo (input transformations) ICLR 2018** — randomization/JPEG/blur preprocessing
  defenses broken by EoT/BPDA. The "smoothing looks robust under weak attack, dies under adaptive" template
  is textbook.
- **Alias-Free ViT (2510.22673)** — **[trap].** Its "robustness to adversarial translations" = worst-case
  *shifts*, **not** Lp pixel attacks. Does NOT close the gap; pre-empt the reviewer who mis-reads the term.
- **"Reviving Shift Equivariance in ViTs" (2306.07470)** — **[MUST CITE — gap-open, supports C3].**
  Confirmed by the agent to test shift-consistency/crop/flip/corruptions, **no** FGSM/PGD/AutoAttack. The
  shift-equivariant ViT *stem* has genuinely never been adversarially tested. This is where C3's real open
  cell lives.

### Where the gap actually is (novelty budget)
- Mechanism (weak-helps/strong-kills): **~0% novel** (Athalye 2018; Ensemble-Everywhere 2024).
- Anti-aliasing operator, CNN classifier, under AutoAttack: **~0% novel** (Grabinski ×3, ASAP, Torralba).
- Low-pass smoothing in a frozen VLM tower under AutoAttack: **~15% novel** (R-Adapt already did Gaussian
  low-pass on frozen CLIP + AutoAttack).
- **APS/polyphase-anchored ViT *stem*, or inference-time patch-grid phase-averaging, under any Lp attack,
  in a VLM: genuinely open (~80% novel).** No paper does this.

### Corrections (this design needs the most)
1. **Correct the false gap sentence.** "The anti-aliasing line NEVER measures adversarial robustness" is
   false for CNNs (Grabinski/FLC/ASAP/Torralba all use AutoAttack/APGD). Restrict the claim to **ViT-stem
   anti-aliasing / shift-equivariant ViT stems / phase-marginalization**, which is where it holds.
2. **Drop or demote the blur-pool / Gaussian-smoothing arm.** Scooped by ASAP (CNN) and R-Adapt (VLM).
   Keep it only as a *replication anchor* with correct citations, not as a contribution.
3. **Center the contribution on the one open cell:** APS/polyphase-anchored ViT stem + stochastic
   inference-time phase-averaging in a frozen VLM tower, with **EoT-adaptive APGD**, framed explicitly as
   "the last shift-invariance operator never adversarially tested." Cite Ensemble-Everywhere (2411.14834)
   as the acknowledged blueprint and Athalye (1802.00420) as the mechanism origin so the expected result
   reads as *confirmation-with-rigor*, not as a claimed surprise.
4. **Cite R-Adapt (2603.12799)** and add a filter-only weak-vs-strong ablation to differentiate.
5. **Fix the phase-marginalization usage** (2606.08132 is dense-prediction TTA; cite for the phenomenon,
   implement your own pooled-embedding phase-average; do not claim to use its method).

### Feasibility on 2×A6000 — the tightest of the three
Full plan ~200 GPU-h across 4 interventions × 2 towers; a ~70 GPU-h pilot for 3 interventions × 2 towers
on 2k-image subsets. **The EoT-adaptive strong-attack arm is the cost driver and the risk:** APGD ×100
iter ×5 restart ×EoT-over-phases through a 7B decoder multiplies quickly — an EoT of K phases multiplies
the already-expensive VLM-APGD by K. On 48 GB this is **feasible only if you keep the strong attack at the
encoder/zero-shot level** (tower-only, no 7B decoder in the APGD loop) and treat the VLM-level APGD as a
small confirmatory subset (≤1k images, K≤4). As written, the full-scale run is optimistic; the standalone
paper should be the **encoder-level ImageNet APGD + EoT** result, with VLM-level as a small arm.

---

## Summary table

| Design | Verdict | Gap status | Compute on 2×A6000 |
|---|---|---|---|
| **C1** | **survives / needs-fix** | Core (SC-fails / η/L-predicts, attack-free selection) unclaimed; 2 novelty overclaims to soften (RDI, ICLR'25 purification); panel narrower than stated | Realistic; 60 GPU-h pilot stands alone (encoder-level ImageNet arm) |
| **C2** | **survives / needs-fix** | ρ_G metric + ρ_G↔η/L link + FARE-worse all open; narrative partial-scoop (2604.01848) demands hard differentiation; 5 mandatory citations | Realistic (~80–90 GPU-h, budget 1.5–2×); white-box search optional |
| **C3** | **needs-fix → near-kill as framed** | Mostly CLOSED (Athalye 2018; Grabinski/ASAP under AutoAttack; R-Adapt Gaussian-on-frozen-CLIP under AutoAttack). Only APS/polyphase ViT-stem + phase-averaging in a VLM is open | Tightest; keep strong attack at encoder level, VLM-APGD+EoT only as small subset |

**Correct the shared miscitation (2404.19287 → 2407.11121) in all three before compute.**
