# Survey: Geometry-Based and Certified Adversarial Robustness, and the Margin–Sensitivity Coupling

Scope: mechanistic / geometry-based and certified defenses, read against one question — does the method obtain **margin** (distance to the decision boundary) **without buying it through input sensitivity** (sharpening of the input gradient)? We are looking for a non-η/L training method that breaks or sidesteps the positive margin–gradient-norm coupling we observed under PGD adversarial training.

Date: 2026-06-27. Numbers are tagged `[verified]` (read from a paper table), `[benchmark]` (RobustBench / AutoAttack-paper), `[flag]` (extracted but not directly confirmed, or single-source / very recent). Absolute numbers are not one-to-one comparable across papers (different attacks, architectures, threat norms) — trust comparisons *within* a table.

---

## 0. The unifying object, and where our coupling result sits

Every method below is governed by the same first-order certificate. For a smooth classifier the distance from `x` to the decision boundary between the predicted class `c` and a competitor `j` is, to first order,

```
r(x)  ≈  [ f_c(x) − f_j(x) ]  /  ‖∇_x f_c(x) − ∇_x f_j(x)‖_q          (q = dual norm)
       =  margin / local-sensitivity
```

This is **Elsayed et al. 2018** Eq. 7 (arXiv:1803.05598), the **Hein & Andriushchenko 2017** robustness bound (arXiv:1705.08475, `r ≤ max_R min{ margin / max_{y∈B(x,R)}‖∇f_c−∇f_j‖_q , R }`), and the global-Lipschitz specialization **Tsuzuku et al. 2018** (`r ≥ margin / (√2·L)`, arXiv:1802.04034). Randomized smoothing is the same ratio with smoothness manufactured by convolution (§3). So "robust radius = margin / sensitivity" is not one framing among many; it is *the* object, and there are exactly two levers: **raise the numerator (margin)** or **lower the denominator (sensitivity / Lipschitz / curvature)**.

**Our result restated in this language.** Under PGD-AT the two levers are *not independent*: the network raises margin by raising local sensitivity (the numerator and denominator move together, a self-limiting coupling). Hence (i) η/L is an excellent *diagnostic* but a failed *training target* — penalizing ‖∇‖ collapses the margin, and maximizing the ratio degenerates to a constant classifier (‖∇‖→0, margin→0, ratio→0/0); and (ii) any method that lowers the denominator *only along the attack's loss surface* produces gradient-masked robustness. The survey's job: find methods that move the two levers **independently** — margin up with sensitivity held (or capped) — and locate the gap where this is not cleanly solved.

The literature splits cleanly:
- **Curvature / second-order (§1):** extend the *radius over which the first-order certificate is valid* (lower curvature = the Lipschitz constant of the gradient). Targets the *denominator's reliability*, not its size.
- **Lipschitz architectures (§2):** *cap the denominator architecturally* (L ≤ 1 by construction), leaving margin as the only lever. This is the literal realization of "margin without sharpening" — and the most directly relevant area.
- **Randomized smoothing (§3):** *manufacture* a bounded denominator (1/σ) by Gaussian convolution; certificate = probability-margin × σ.
- **Margin training (§4):** push the *numerator*. The ones that ignore the denominator hit our coupling wall; AutoAttack exposes them.

---

## 1. Curvature / second-order methods

These do not shrink the gradient *magnitude*; they shrink the *change* in the gradient across the threat ball (curvature = local Lipschitz constant of `∇`), so that the linear/margin certificate `margin/‖∇‖` actually holds out to radius ε instead of only infinitesimally. CURE's and LLR's central empirical claim is that PGD-AT *already* does this implicitly (it flattens the loss surface and makes the boundary quasi-linear near data); these methods target it directly and cheaper.

- **CURE — Moosavi-Dezfooli et al., CVPR 2019, arXiv:1811.09716.** Penalizes input curvature via a finite-difference Hessian along the gradient direction, `(1/h²)·E‖∇ℓ(x+hz)−∇ℓ(x)‖²`. CIFAR-10, ε=8/255, PGD-20 `[verified]`: WRN-28-10 **83.1% clean / 41.4% robust** vs Madry-AT 87.3% / 45.8%; ResNet-18 81.2% / 36.3% vs AT 79.4% / 43.7%. Consistently a few points **below** PGD-AT. Its own Remark 2 warns the bound depends on ‖∇ℓ‖ and that **"small gradients might provide a false sense of robustness"** — i.e. CURE itself flags the denominator-shrinking failure mode.
- **GradAlign — Andriushchenko & Flammarion, NeurIPS 2020, arXiv:2007.02617.** Regularizer `1 − cos(∇ℓ(x), ∇ℓ(x+η))` over random η in the ε-ball. **The conceptually sharpest case for us: it is invariant to gradient *norm* and constrains only gradient *direction* (local linearity)** — the denominator-shrinking lever is deliberately removed. CIFAR-10 PreActRN-18, PGD-50-10 `[verified]`: FGSM+GradAlign **81.0% / 47.58%** (vs PGD-10-AT 81.88% / 50.04%); at ε=16/255 it is the *only* fast method that survives (28.88% vs FGSM-RS 0.00%); AutoAttack 44.54% @8/255. Cost ≈ 3× FGSM (double backprop). It prevents catastrophic overfitting and does *not* show gradient masking — direct evidence that genuine robustness comes from controlling curvature/linearity, not gradient magnitude.
- **LLR — Qin et al., NeurIPS 2019, arXiv:1907.02610.** Penalizes the Taylor-violation `γ(ε,x)=max_δ|ℓ(x+δ)−ℓ(x)−δ·∇ℓ|` plus the gradient magnitude in the adversarial direction. CIFAR-10 WRN-28-8 Multi-Targeted `[verified]` 86.83% / 51.13%; ImageNet RN-152 ε=4/255 **72.7% / 47.0% with only 2 inner steps** (vs AT 69.2% / 39.7%, 30 steps), 5× faster. Smaller Untargeted→Multi-Targeted drop than AT → less obfuscation.
- **SOAR — Ma et al., ICLR 2021, arXiv:2004.01832 — the cautionary tale.** Second-order Taylor upper bound on the inner-max (uses input Hessian). Its first-order analogue **FOAR reduces exactly to the ℓ∞ gradient penalty `ε‖∇ℓ‖₁`** — i.e. pure denominator-shrinking — and it tanks clean accuracy (65.8%). SOAR reports CIFAR-10 PGD-20 **56.06%** but under **targeted APGD-DLR collapses to 18.25%** `[verified]`; the authors themselves conclude it **"might rely on gradient masking."** This is our failure mode caught in the act: shrink the cross-entropy gradient → big PGD number → evaporates under a different attack loss.

**Relation to the coupling.** Curvature methods do *not* break the coupling; they make the *existing* margin/‖∇‖ certificate trustworthy over a finite ball by stabilizing the gradient field. GradAlign is the cleanest "norm-free" instance and behaves honestly; FOAR/SOAR show that the moment you target gradient *magnitude*, you slide into masking. Measured limit: even GradAlign/LLR close but do not exceed the PGD-AT robustness ceiling — consistent with the coupling being the binding constraint that curvature regularization does not remove.

Supporting evidence that AT *raises* sensitivity (so "robust = low gradient" is false): **Simon-Gabriel et al. ICML 2019 (arXiv:1802.01421)** — vulnerability ∝ ‖∇ℓ‖, ℓ1 gradient norm grows like √d and persists after robust training; **"AT is data-dependent operator-norm regularization" (arXiv:1906.01527)**; **"AT makes the loss landscape sharper" (arXiv:2102.02950)** — gradient norm grows with ε. These are the literature anchors for our coupling claim.

---

## 2. Lipschitz-constrained architectures — the direct realization of "margin without sharpening"

This is the most relevant area. By bounding `L ≤ 1` *architecturally*, the certificate `r = margin / (√2·L)` reduces to `r ∝ margin`. The network **cannot** buy a bigger certificate by sharpening the input gradient — the gradient norm is capped by construction. **The only remaining lever is maximizing the logit margin inside a fixed-sensitivity network.** That is precisely "margin without sharpening," done at the architectural level. The whole research program is therefore (a) how to build expressive `L≤1` layers without vanishing gradients, and (b) how to actually *optimize* margin in such a capacity-limited network.

**The enabling theory.** Anil et al. (GroupSort, ICML 2019, arXiv:1811.05381) proved that to be both expressive and 1-Lipschitz, the network must use **gradient-norm-preserving (GNP)** layers (orthogonal weights + norm-preserving activations like GroupSort/MaxMin); ordinary contractive ReLU stacks lose the capacity to express large margins at all. This is the load-bearing reason naive spectral-norm clipping fails and why all SOTA layers below are GNP/orthogonal.

### CIFAR-10 deterministic certified accuracy, L2 ε = 36/255 = 0.141

| Method | Year | arXiv | Clean | Certified | Tag |
|---|---|---|---|---|---|
| Tsuzuku LMT (foundational `margin/L`) | 2018 | 1802.04034 | — | — | no CIFAR; theory |
| BCOP | 2019 | 1911.00937 | 69.8 | 52.1 | verified |
| GloRo | 2021 | 2102.08452 | ~77 | ~51 (lib 60.0) | flag (orig table not read) |
| Cayley | 2021 | 2104.07167 | 74.6 | 61.4 | verified |
| SOC | 2021 | 2105.11417 | 76.4 | 61.9 | verified |
| SOC+LLN+CR | 2022 | 2211.08453 | 76.3 | 62.6 | verified |
| AOL | 2022 | 2208.03160 | 71.6 | 64.0 | verified |
| CPL | 2022 | 2110.12690 | 78.5 | 64.4 | verified |
| LOT | 2022 | 2210.11620 | 77.1 | 64.3 | verified |
| Sandwich / LBDN (SDP-tight, projection-free) | 2023 | 2301.11526 | — | — | CIFAR-100 35.3 verified; C10 not read |
| SLL X-Large | 2023 | 2303.03169 | 73.3 | 64.8 | verified (corrected nums) |
| **CRM** (dynamic margin + directional Lipschitz) | 2023 | 2310.00116 | 74.8 | **64.2** (6C2F) | verified |
| **LiResNet + EMMA + LLN** | 2023/24 | 2301.12549 | 81.3 / 82.1* | 66.9 / 70.1* | verified (*+DDPM data) |
| **BRONet + Logit Annealing** | 2025 | 2505.15174 | 81.6 | **70.6** | verified (no extra data SOTA) |
| **LipNeXt** (1–2B params) | 2026 | 2601.18513 | 85.0 | **73.2** | flag (Jan-2026, single source) |

Other datasets, best deterministic at this radius: CIFAR-100 LipNeXt 44.1 `[flag]` > BRONet 40.2 > LiResNet 41.5(+DDPM); Tiny-ImageNet LipNeXt 35.0 `[flag]` > LiResNet 33.6; **ImageNet** LipNeXt(2B) 41.2 `[flag]` > BRONet 37.6 > LiResNet 35.0 (LiResNet 2023 = first deterministic Lipschitz cert scaled to ImageNet).

**Key sub-results.**
- **LiResNet (arXiv:2301.12549 / recipe 2310.02513):** linear residual branch keeps the Lipschitz product tight (conventional residuals blow it up); **LLN** (last-layer normalization) + **EMMA** (Efficient Margin MAximization — penalize worst-case logits of *all* classes at once). Frames the core difficulty as: *margin maximization in a bounded-L net is capacity-bound;* gain grows with #classes; **self-attention is not Lipschitz** so Transformers are excluded from this route.
- **BRONet (arXiv:2505.15174):** Householder/Block-Reflector orthogonal layers (orthogonal without iterative approximation) + Logit Annealing `(1−p_t)^β log p_t` that down-weights easy examples to "allocate the network's *limited capacity* to hard ones" — again the binding constraint is capacity for margin.
- **CRM — "Certified Robustness via Dynamic Margin Maximization and Improved Lipschitz Regularization," Fazlyab group, NeurIPS 2023, arXiv:2310.00116.** The closest existing method to a deliberate "margin-without-sharpening" objective: **maximize logit-space margin while regularizing the Lipschitz constant only along vulnerable directions** (not globally), using a differentiable lower bound on distance-to-boundary and accurate (LipLT-style) directional Lipschitz upper bounds. CIFAR-10 6C2F `[verified]` **74.82% clean / 64.16% certified**, beating GloRo (77.0 / 58.4) and Local-Lip-G (76.4 / 51.3); MNIST ε=1.58 96.27% / 63.37%. It explicitly argues that the *relative accuracy* of the directional bound "prevents excessive regularization," i.e. avoids the over-smoothing capacity tax. **This is prior art for candidate mechanism C1 — but it still sits on a globally-Lipschitz-parameterized net and tops out well below LiResNet/BRONet on clean accuracy.**

**Why haven't 1-Lipschitz nets displaced AT?** Three evidenced reasons.
1. **Clean-accuracy / capacity tax.** Best CIFAR-10 clean accuracy under a *global* 1-Lipschitz constraint is ~81% (LiResNet/BRONet), only the brand-new billion-param LipNeXt reaches 85%, vs ~95% unconstrained and ~89% for L2-AT. That ~10–15 pt clean drop compounds with #classes/resolution (CIFAR-100 best clean ~54–57%, ImageNet ~49–57%). The community's whole loss-design effort (EMMA, Logit Annealing, CRM, +DDPM data) is buying this capacity back.
2. **Threat-model + magnitude mismatch.** They certify **L2 at a small radius** (0.14); AT targets **empirical L∞ at 8/255** where it reaches ~50–60% AutoAttack. Practitioners get a *guarantee* only inside a tiny L2 ball, while AT gives stronger *empirical* robustness on the standard threat — so AT still dominates when a certificate is not mandatory.
3. **Scaling lag.** Deterministic Lipschitz cert reached ImageNet only in 2023; Transformers remain excluded; only 2025–26 work (BRONet, LipNeXt) is closing the scale gap.

**Do they decouple margin from sensitivity?** Yes — by construction, and this is the central lesson for our method. They convert the problem from "robust radius" to "pure margin maximization at fixed L." The cost of that decoupling is that **margin becomes the binding, capacity-starved optimization problem** (Anil's GNP requirement, EMMA/Logit-Annealing loss engineering). The **Bubeck–Sellke universal law of robustness** (NeurIPS 2021, arXiv:2105.12806) explains *why* the tax is structural: smoothly interpolating `n` points in `d` dimensions requires roughly `d×` more parameters than merely interpolating them. Low-Lipschitz (smooth) + high-margin is a *large-capacity* regime — so a global 1-Lipschitz net at fixed width is capacity-starved, and that is the deep reason clean accuracy drops. (Wu–Huang–Zhang, ICML 2023, arXiv pmlr-v202-wu23g, extends the law beyond isoperimetry to a distribution-free `Ω(n^{1/d})` lower bound; a 2026 follow-up "Does Order Matter: Connecting the Law of Robustness to Robust Generalization," arXiv:2602.20971, ties it to generalization.)

---

## 3. Randomized smoothing frontier — manufactured smoothness, certified-vs-empirical gap

Gaussian smoothing `g(x)=argmax_c P_{ε∼N(0,σ²I)}[f(x+ε)=c]` makes the surrogate provably `(1/σ)`-Lipschitz, and the **Cohen et al. certificate is again margin/sensitivity**: `R = (σ/2)(Φ⁻¹(p_A) − Φ⁻¹(p_B))` — numerator is a probability-space margin, `1/σ` is the Lipschitz constant. Smoothness is *manufactured by convolution* instead of constrained architecturally. Raising σ buys radius but destroys clean margin (explicit accuracy/robustness knob).

| Method | arXiv | CIFAR-10 (L2) | ImageNet (L2) | note |
|---|---|---|---|---|
| Cohen (ICML'19) | 1902.02918 | ~61@.25, 43@.5, 22@1.0 | 49@.5, 37@1.0, 19@2.0 | verified; needs ~1e5 MC samples (~110s/img) |
| SmoothAdv (NeurIPS'19) | 1906.04584 | 73@.25, 58@.5, 38@1.0 | 56@.5, 45@1.0 | verified |
| Denoised Smoothing (NeurIPS'20) | 2003.01908 | ~56@.25,..,19@1.0 | ~50@.25 | flag (extracted); value = frozen-model applicability |
| MACER (ICLR'20) | 2001.02378 | larger ACR, attack-free | — | differentiable certified-radius objective (= margin max for smoothing) |
| Consistency Reg (NeurIPS'20) | 2006.04062 | ACR 0.525→0.720 @σ0.5 | — | regularizes p_A−p_B directly |
| Diffusion Denoised "for free" (ICLR'23) | 2206.10550 | 77@.25, 63@.5, 32@1.0 | **71@.5**, 54@1.0, 30@2.0 | verified; off-the-shelf diffusion denoiser, no training |
| DensePure (ICLR'23) | 2211.00322 | 77@.25, 65@.5, 37@1.0 | 78@.5, 67@1.0 | verified; multi-shot reverse + majority vote |

**Certified-vs-empirical gap (structural).** (1) **Radius ceiling / curse of dimensionality:** `R ≤ σ·Φ⁻¹(p_A)` grows only like σ, and σ↑ destroys clean accuracy; high-d makes noise more destructive (diffusion denoisers raise the ceiling but "hallucinate" past r≈3). (2) **Inference cost:** ~1e4–1e5 forward passes per image for a *probabilistic* guarantee with abstention, vs one pass for AT. (3) **L2 only** — no L∞ guarantee, the threat AT targets. So "certified" and "empirically robust" headlines are often not even in the same norm.

**Relation to coupling.** Smoothing is the *third* way to get a bounded denominator (after curvature-stabilization and architectural capping). It fully decouples margin from sensitivity — `1/σ` is fixed independent of the base net — and **MACER** (arXiv:2001.02378) is the smoothing-world analogue of exactly the method we want: make the certified radius differentiable and maximize it directly (attack-free margin maximization at fixed manufactured smoothness). The price is probabilistic, expensive, L2-only.

---

## 4. Margin-based training — who clears the coupling wall, who hits it

Test: a method *addresses* the coupling only if it (a) explicitly divides margin by sensitivity, (b) implicitly caps local sensitivity (output smoothing / ε-matched inner-max), or (c) survives AutoAttack. Raw input-space or feature/reweighting margin proxies validated only with PGD hit the wall.

- **Elsayed et al. 2018 (arXiv:1803.05598) — the only one that explicitly normalizes.** Loss = margin / dual-norm gradient (ℓ∞ margin ⇒ ℓ1 gradient), across input *and* hidden layers. Conceptually the exact antidote to sharpening — but validated pre-AutoAttack (black-box IFGSM only). *Right idea, not benchmark-proven.*
- **TRADES (ICML'19, arXiv:1901.08573) — implicit sensitivity cap.** `CE(f(x),y) + (1/λ)·max_{x'}KL(f(x),f(x'))`; the KL term forces predictions flat in the ε-ball = local-stability control. WRN-34-10 `[verified]` 84.92% / 56.61% PGD-20; AutoAttack ~53% `[benchmark]`. Genuine (small AA gap). Closest AT method in spirit to "margin relative to stability."
- **MMA (ICLR'20, arXiv:1812.02637):** maximizes *raw* per-sample input-space margin via adaptive per-sample ε; no normalization. AA 41.4% (only −5.7 vs reported), SPSA-clean → mildly inflated only; the ε-matched inner-max keeps it honest.
- **MART (ICLR'20, OpenReview rklOg6EFwS):** misclassification-aware reweighted KL; output-space, no normalization. AA ≈49% (no extra data) / 56.29% (+500K TinyImages) `[flag]`. AA-validated, genuine, but does not touch sensitivity.
- **LBGAT (ICCV'21, arXiv:2011.11164):** match robust-model adversarial logits to a clean model's "natural boundary." WRN-34-10 `[verified]` **88.22% / 52.86% AA** — genuine; win is clean-accuracy recovery at TRADES-level robustness.
- **HIT THE WALL (PGD↑ but AA↓ — gradient masking):**
  - **Feature Scattering (NeurIPS'19, arXiv:1907.10764):** reported 60.6% → **AA 36.64%** (−24), the largest gap in the AutoAttack table.
  - **AFD (NeurIPS'21, arXiv:2006.04621):** PGD 59.4% but **AA 37.3%**, *below* TRADES despite far higher PGD — textbook inflation.
  - **GAIRAT (ICLR'21):** loss-reweighting masks gradients; **55%→44%** under adaptive/logit-scaling PGD (critique arXiv:2103.01914). MAIL (arXiv:2106.07904) is the better-behaved cousin but inherits the reweighting-masking risk.
- **Theory caveat — Soudry et al. (arXiv:1710.10345):** GD on separable data converges to the max-margin direction in **parameter/representation space**, which is *not* input-space robustness margin once divided by the unbounded input-gradient norm. "GD already maximizes margin" ≠ robustness — this *is* the gap our coupling exploits.

**Verdict.** Honest robustness clusters at ~49–53% AA; no method beats that ceiling by raw-margin maximization alone. Robustness tracks **margin relative to sensitivity**, exactly the wall. Only Elsayed explicitly normalizes (but is unproven); TRADES/MMA/MART/LBGAT survive because AT's ε-matched inner-max or output smoothing implicitly caps the denominator; Feature-Scattering/AFD/GAIRAT inflate and AutoAttack deflates them 11–24 pts.

---

## 5. Synthesis: the mechanistic gap, and concrete candidate mechanisms

### What the field *has* cleanly solved
"**Margin without sharpening**" is, abstractly, solved three ways — each caps/decouples the denominator and then maximizes the numerator: (A) **architectural** capping (1-Lipschitz nets, §2: best CIFAR-10 certified 70.6% no-extra-data / 73.2% billion-param), (B) **manufactured** smoothness (randomized smoothing + MACER, §3, L2-only/expensive), (C) **stabilized** denominator (curvature/TRADES, §1/§4, honest but at the AT ceiling). The "bound L, then maximize margin" recipe is **extremely crowded and improving monthly** (GloRo→SOC→CPL→AOL→LOT→SLL→CRM→LiResNet→BRONet→LipNeXt). A vanilla "spectral-norm + margin loss" paper is already done many times over and would not be novel.

### What is genuinely open (the seam to aim at)
The clean decoupling (A) pays a **structural capacity tax** (Bubeck–Sellke: smooth+high-margin needs `d×` capacity; empirically ~10–15 clean pts on CIFAR-10, worse on ImageNet) because it caps L **globally and isotropically** — everywhere, in every direction, for every sample. But the certificate only needs the denominator controlled **locally, along the margin-defining direction, near the data**. The unsolved problem:

> **Decouple margin from sensitivity *locally and anisotropically* — control sensitivity only where the certificate uses it — so you keep clean accuracy near AT levels while making the margin lever independent of the sharpening lever.**

This is also exactly why **our η/L target degenerated**: penalizing the *full* input gradient over-constrains all directions and all samples (→ constant classifier), and maximizing a *global* ratio rewards ‖∇‖→0. The fix is to make the sensitivity term **directional, local, and margin-paired**, not global. CRM (arXiv:2310.00116) is the only prior work explicitly in this direction and it is *not* saturated (still a global-Lipschitz net, clean acc 74.8% < LiResNet 81%). Below are concrete, falsifiable mechanisms ordered by how cleanly they sidestep the coupling at the source.

---

#### C1 — Directional/anisotropic local-Lipschitz budget paired to the margin (a *fixed* η/L target)
**Mechanism.** Replace the failed global-gradient penalty with a per-sample regularizer that controls **only the local Lipschitz constant in the runner-up-class direction**, `g(x)=∇_x[f_y(x)−f_{j*}(x)]`, where `j*` is the current closest competitor. Train with a margin objective whose denominator is exactly this directional, *locally estimated* (over the ε-ball, à la Hein/LLR) Lipschitz term — not the full Jacobian. All other directions stay unconstrained, so the network keeps capacity to fit clean data.
**Prior art + why not solved.** CRM (arXiv:2310.00116) regularizes "Lipschitz along vulnerable directions" but inside a globally-Lipschitz-parameterized net (still capacity-taxed, 74.8% clean); Hein cross-Lipschitz (arXiv:1705.08475) is local but a soft 2-layer regularizer with no modern AT/AA validation; Local-Lip-G training (arXiv:2111.01395) *underperforms* global methods (51.3% certified) — so "local" has been tried but not in the *single-direction, margin-paired* form, and not as a faithful η/L target. Our own finding (penalizing full ‖∇‖ → degenerate) is the missing diagnostic for *why* the direction must be restricted.
**Falsifiable pilot prediction.** On CIFAR-10, training with the **single-direction** local-Lipschitz penalty will (i) hold clean accuracy ≥ standard L∞-AT (~85–89%, vs the ~75–81% global-Lipschitz ceiling), and (ii) **break the positive margin–gradient-norm correlation** we measured: per-sample margin and the *off-margin-direction* gradient norm should decorrelate (Pearson → ~0), while margin and the *on-direction* local-Lipschitz stay coupled by design. If instead clean accuracy collapses toward the global-Lipschitz ceiling, the tax is not direction-localizable and C1 fails. *(Cheap: a regularizer + two correlation measurements on an existing AT pipeline.)*

#### C2 — Adversarial training inside a gradient-norm-preserving (orthogonal) backbone
**Mechanism.** Keep PGD-AT — the best empirical margin engine — but **reparameterize every layer as GNP/orthogonal (GroupSort/MaxMin + orthogonal convs)** so the global Lipschitz product is `O(1)` *by construction*. The sharpening lever is physically removed: AT can no longer raise ‖∇‖ to buy margin, so any margin it finds must come from **reorienting the boundary**, not steepening it. One model, both empirical (AT) and certified (bounded L) robustness.
**Prior art + why not solved.** Parseval Networks (arXiv:1704.08847) combined AT-style training with *soft* orthogonality, pre-AutoAttack — never tested as a hard GNP constraint inside modern PGD-AT. The Lipschitz-net community uses GNP layers for *certification with clean/TRADES losses*, not as a cage around PGD-AT; the AT community uses unconstrained nets (whose Lipschitz product is astronomically large). The cross — *hard-GNP backbone + full PGD-AT inner-max* — is essentially untried and directly tests whether AT's margin survives when the sharpening escape valve is welded shut.
**Falsifiable pilot prediction.** In a GNP-AT network the margin–gradient-norm coupling should **flatten** (gradient norm pinned near L by construction), and AutoAttack robustness should approach standard AT (~50% @8/255) **while the global Lipschitz product stays small enough to yield a non-trivial deterministic L2 certificate** — something standard AT can never provide. Failure signature (consistent with Bubeck–Sellke): clean+robust accuracy collapse because the GNP cage starves capacity exactly as in §2. The pilot cleanly separates "AT's robustness is sharpening" (then GNP-AT collapses) from "AT's robustness is reorientation that GNP can host" (then GNP-AT gives empirical *and* certified robustness).

#### C3 — Margin-structure distillation: AT teacher → Lipschitz student
**Mechanism.** Use a high-margin AT teacher purely as a **source of per-sample margin targets** (its distance-to-boundary ordering / soft boundary geometry), and distill *that geometry* — not logits — into a 1-Lipschitz student. The student inherits the teacher's boundary *shape* without inheriting its sharpening, because the student's denominator is capped architecturally.
**Prior art + why not solved.** CC-Dist (arXiv:2602.02626, ICLR 2025) distills an AT teacher into an IBP/certified student (CIFAR-10 64.6% certified @2/255, but clean only 55% @8/255 — still deep in the capacity tax) — it distills *features/bounds*, not the **margin ordering**. LBGAT (arXiv:2011.11164) distills a *clean* teacher's boundary into a robust student (not Lipschitz, empirical only). No one distills the **AT teacher's margin structure into a GNP/Lipschitz student**.
**Falsifiable pilot prediction.** A LiResNet/BRONet student trained with a **margin-matching** distillation term from an L2-AT teacher will reach **higher certified accuracy at fixed architecture than the same net trained with EMMA from scratch**, because the capacity-limited student cannot *discover* the teacher's margin geometry unaided but *can* imitate it. If margin-distillation gives no lift over EMMA-from-scratch, the bottleneck is student capacity (Bubeck–Sellke), not optimization, and C3 fails.

#### C4 — Deterministic single-pass smoothing with an explicit margin objective
**Mechanism.** Smoothing already decouples (denominator = `1/σ`, independent of the base net), but it is probabilistic/expensive/L2-only. Fold a **fixed denoiser (one diffusion step or a trained denoiser) into the architecture as a frozen front-end**, giving a *deterministic* surrogate whose input-Lipschitz is bounded by the denoiser's, then train the composition with a **MACER-style differentiable margin/certified-radius objective** — single forward pass at inference.
**Prior art + why not solved.** MACER (arXiv:2001.02378) maximizes the certified radius but for the *stochastic* smoothed classifier; diffusion-denoised smoothing (arXiv:2206.10550) is deterministic-ish per-sample but still Monte-Carlo-certified and not margin-trained end-to-end. A deterministic, single-pass, margin-trained denoiser-front-end is an open seam.
**Falsifiable pilot prediction.** The composition will achieve a **deterministic** (non-MC) certified radius competitive with global-Lipschitz nets at *higher clean accuracy*, because the denoiser supplies smoothness without constraining the classifier's capacity. Falsified if the frozen denoiser's own Lipschitz bound is too loose to yield a useful deterministic certificate (likely the main risk) — measurable directly by bounding the denoiser's Lipschitz constant before any training.

#### C5 (speculative) — Reparameterize so SGD's implicit bias targets *input*-margin, not representation-margin
**Mechanism.** Soudry's implicit bias drives GD to max **representation-space** margin, which is robustness-irrelevant because it ignores the input-gradient denominator. Apply a **change of variables / preconditioning** that makes the input-space Lipschitz an explicit, cheap coordinate (e.g. parameterize weights on the orthogonal manifold so that representation-margin *equals* input-margin up to the fixed layer norms). Then the "free" max-margin bias of GD lands on the *robust* margin automatically — no extra loss term.
**Prior art + why not solved.** Manifold/direct parameterizations exist (Sandwich/LBDN arXiv:2301.11526, LipNeXt's constraint-free orthogonal optimization arXiv:2601.18513) but are used to *enforce* L≤1, not to *redirect the implicit bias*; the connection to Soudry's implicit-bias geometry is unexplored.
**Falsifiable pilot prediction.** Under the reparameterization, **plain cross-entropy SGD (no robustness loss at all)** should yield non-trivial certified robustness that grows with training time (as the implicit margin bias sharpens), whereas the same SGD on the standard parameterization yields zero certified robustness. Falsified if certified robustness stays at zero — meaning the implicit bias does not transfer through the reparameterization.

---

## 6. Honest assessment — crowdedness and difficulty

- **Most crowded / avoid as headline:** "1-Lipschitz layer + margin loss" (§2) is saturated and improves monthly; "input-gradient penalty for robustness" is the FOAR/SOAR failure mode; "randomized smoothing variant" (§3) is mature. A new η/L *target* is also unlikely to work — our own result plus FOAR/SOAR/GAIRAT show that targeting the global gradient/ratio either degenerates or masks.
- **The real wall is capacity, not optimization (mostly).** Bubeck–Sellke makes the clean-accuracy tax of global smoothness a *theorem*, not an engineering gap. Any mechanism (C1–C5) lives or dies on whether it can localize/borrow capacity (anisotropic control, AT-teacher geometry, frozen denoiser) instead of paying the global `d×` tax. Each pilot above is designed to expose exactly that.
- **Strongest, cheapest bets:** **C1** (directional local-Lipschitz as a *fixed* η/L target) is the most direct fix to our specific degeneracy and the cheapest pilot (regularizer + two correlation measurements on an existing AT run); **C2** (GNP-AT) most cleanly tests whether AT's margin *is* sharpening or reorientation, and would, if it works, deliver the rare combination of empirical-AT + deterministic certificate in one model. **C3** is low-risk incremental; **C4/C5** are higher-variance.
- **Framing for the paper:** position our coupling result as the *mechanistic explanation* for why (i) global gradient/ratio targets fail (§1 FOAR/SOAR, §4 GAIRAT) and (ii) global 1-Lipschitz nets pay a capacity tax (§2 + Bubeck–Sellke), then propose the **anisotropic/local decoupling** (C1/C2) as the non-η/L mechanism that gets margin without sharpening *without* the global tax. The diagnostic→mechanism arc is the contribution; the candidate that survives its pilot is the method.

---

## References (arXiv id · verification)

**Foundations / certificate:** Hein & Andriushchenko 1705.08475 (cross-Lipschitz, verified) · Tsuzuku LMT 1802.04034 (verified theory) · Elsayed large-margin 1803.05598 (verified formula) · Simon-Gabriel 1802.01421 (abstract) · Soudry implicit bias 1710.10345 · Bubeck–Sellke law of robustness 2105.12806 · Wu–Huang–Zhang beyond isoperimetry (PMLR v202 wu23g) · "Does Order Matter" 2602.20971 (flag, 2026).
**Curvature/2nd-order:** CURE 1811.09716 (verified) · GradAlign 2007.02617 (verified) · LLR 1907.02610 (verified) · SOAR/FOAR 2004.01832 (verified) · AT=operator-norm-reg 1906.01527 · sharper-landscape 2102.02950 (abstract).
**Lipschitz architectures:** GroupSort 1811.05381 · BCOP 1911.00937 (verified) · GloRo 2102.08452 (flag orig table) · Cayley 2104.07167 (verified) · SOC 2105.11417 (verified) · SOC+LLN+CR 2211.08453 (verified) · AOL 2208.03160 (verified) · CPL 2110.12690 (verified) · LOT 2210.11620 (verified) · Sandwich/LBDN 2301.11526 (partial) · SLL 2303.03169 (verified, corrected) · CRM/dynamic-margin 2310.00116 (verified) · LiResNet 2301.12549 + recipe 2310.02513 (verified) · BRONet 2505.15174 (verified) · LipNeXt 2601.18513 (flag, Jan-2026 single source) · LipSDP 1906.04893 · Local-Lip 2111.01395 · Parseval 1704.08847 · LipShiFT 2503.14751.
**Randomized smoothing:** Cohen 1902.02918 (verified) · SmoothAdv 1906.04584 (verified) · Denoised 2003.01908 (flag) · MACER 2001.02378 · Consistency 2006.04062 (ACR verified) · Diffusion-for-free 2206.10550 (verified) · DensePure 2211.00322 (verified) · raising-the-bar 2305.10388.
**Margin/feature/boundary:** MMA 1812.02637 (verified) · TRADES 1901.08573 (verified) · MART OpenReview rklOg6EFwS · GAIRAT-critique 2103.01914 (verified) · MAIL 2106.07904 · Feature Scattering 1907.10764 (AA verified) · AFD 2006.04621 (verified) · Boundary thickness 2007.05086 · LBGAT 2011.11164 (verified) · CC-Dist (AT→certified distillation) 2602.02626 (ICLR 2025) · AutoAttack 2003.01690.
