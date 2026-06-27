# Fresh Angles for a New Adversarial-Robustness Method — Survey & Candidate Mechanisms

Scope: a method that improves on PGD adversarial training (PGD-AT), is NOT input-gradient (η/L) regularization, and either (a) reuses our spectral-invariant machinery (power-spectrum + degree-3 bispectrum convolution-pooling layers) as a *robustness mechanism*, or (b) is genuinely fresh. Default threat model throughout: CIFAR-10, ℓ∞ ε = 8/255, evaluated with AutoAttack + a method-specific adaptive attack. "AA" = AutoAttack robust accuracy.

Compiled 2026-06-27 from a 5-angle web survey with adversarial verification of load-bearing claims.

---

## TL;DR — the three facts that constrain everything

1. **Invariance buys robustness only inside the group orbit.** Translation/rotation invariance (what power spectrum and bispectrum give) protects only against perturbations that lie in a translation/rotation orbit. The ℓ∞ ball at ε=8/255 is **not** contained in any such orbit, so spectral invariance gives **no a-priori ℓ∞ guarantee**. Anti-aliasing/BlurPool [Zhang 2019, ICML] is the cautionary data point closest to us: it buys shift-consistency and common-corruption robustness but **zero** white-box ℓ∞ robustness. Our own shift-invariance ↔ robustness paper already implies this; do not oversell invariance as ℓ∞ defense.

2. **Spectral/frequency PREPROCESSING is a graveyard.** Every JPEG / low-pass / feature-squeezing / feature-distillation / manifold-projection front-end was broken by BPDA or adaptive attacks because the non-differentiable or stochastic transform masks gradients [Athalye 2018, ICML; Tramèr 2020, NeurIPS]. The bispectrum is a non-smooth triple product B(k₁,k₂)=F(k₁)F(k₂)F*(k₁+k₂) — exactly the kind of front-end that produced false robustness. **Any bispectral defense used as a front-end is presumed gradient-masking until proven otherwise with BPDA + Square attack.**

3. **What actually survives is narrow:** PGD-AT + an architectural margin (feature denoising, smooth activations, sparse-on-AT), honest randomized smoothing (Gaussian noise / diffusion-L2, certified), and large diffusion-generated training data. The CIFAR-10 ℓ∞ 8/255 frontier is **≈73.7% AA / 93.7% clean** [Bartoldson 2024, ICML], pushed to **≈75.3% AA** by the post-training MeanSparse feature-sparsification add-on [Amini 2024]. PGD-AT (Madry) and Carmon-2019 (~59.5%) are the classic reference points. Any new number lives or dies against ~73–75%.

---

## 1. Frequency-domain / spectral robustness

### 1.1 What "high-frequency vulnerability" actually means (analysis, not defense)
- **Tsuzuku & Sato 2019** (CVPR; arXiv:1809.04098): CNN sensitivity is **anisotropic in the Fourier basis**; single data-agnostic Fourier-direction perturbations degrade accuracy. Grounds the "Fourier heat map."
- **Yin et al. 2019** "A Fourier Perspective on Model Robustness" (NeurIPS; [proceedings](https://proceedings.neurips.cc/paper_files/paper/2019/file/b05b57f6add810d3b7490866d74c0053-Paper.pdf)): natural models are most vulnerable to mid/high-frequency perturbations, **but it is a trade-off, not a switch** — Gaussian aug and adversarial training improve high-freq robustness while *reducing* low-freq robustness (fog/contrast). You cannot get robustness by deleting high frequencies; interventions *shift* the sensitive band.
- **Wang et al. 2020** "High-Frequency Component Helps Explain Generalization of CNNs" (CVPR; arXiv:1905.13545): CNNs exploit human-imperceptible high-freq components. Numbers (ResNet-18, CIFAR-10): low-freq-only ≈75% test acc vs high-freq-only ≈10%, yet HFC can flip predictions. Kernel-smoothing to suppress HFC gives only marginal robustness (12.7% vs 0.2% under PGD) — **HFC suppression alone is not a defense.**

Takeaway: white-box attacks adapt to whatever band the model relies on, so a fixed low-pass / fixed-band front-end provably cannot give general ℓ∞ robustness.

### 1.2 Spectral / JPEG / low-pass / input-transform defenses — DEAD ENDS (gradient masking)
| Defense | Status | Broken by |
|---|---|---|
| Guo 2018 input transforms (JPEG, TV-min, quilting), ICLR | **BROKEN → ~0%** | Athalye 2018 BPDA (broke 7/9 ICLR-18 defenses) |
| Das 2018 SHIELD/JPEG, KDD | **BROKEN** | differentiable-JPEG / adaptive |
| Xu 2017 Feature Squeezing (detector), NDSS | **BROKEN** | Sharma & Chen; detection-aware adaptive |
| Liu 2019 Feature Distillation (DNN-JPEG), CVPR | **BROKEN (presumed)** | BPDA-vulnerable, no adaptive eval |

General verdict: Tramèr 2020 (NeurIPS) broke **13** further defenses with tailored adaptive attacks. Treat all spectral/JPEG/low-pass preprocessing as dead unless it has a *published* adaptive evaluation (none do).

### 1.3 Spectral / Lipschitz REGULARIZATION — weak standalone; only certified-architecture line genuinely survives
- Parseval Networks [Cisse 2017, ICML], Spectral Norm [Yoshida 2017; Miyato 2018]: only ever evaluated under weak attacks (FGSM/SNR); standalone Lipschitz penalty does **not** reach AT-level robustness. Curvature/Jacobian penalties (CURE) themselves flagged for partial gradient masking.
- **Genuine survivors = certified 1-Lipschitz architectures** (survive AA by construction): GloRo [Leino 2021, ICML], SortNet [Zhang 2022, NeurIPS], LiResNet [Hu 2023] (~76% certified at the evaluated L2 radius). Caveat: certified radii are small (~36/255 L2, ~1–2/255 L∞), far below the ε=8/255 ℓ∞ regime; real but limited.

### 1.4 Invariant spectral features as a robustness MECHANISM — the actual gap
- **Sanborn et al. 2023, "Bispectral Neural Networks"** (ICLR; arXiv:2209.03416). VERIFIED: their robustness claim is **"invariance-based adversarial robustness," NOT standard ℓp.** They attack on **Rotated-MNIST** with *invariance-based adversarial attacks* (optimize an input to match the model's invariant representation → "metamers"). For BNN, adversarial solutions converge to genuine within-orbit group transforms; for baselines (E2CNN, Augerino) ≈35% of representation-matching inputs are perceptually unrelated metamers. **They report no PGD/AutoAttack and never test ℓ∞/ℓ2.** Different threat model (group-orbit), not standard adversarial robustness.
- **Chen et al. 2021, "Amplitude-Phase Recombination"** (ICCV; arXiv:2108.08487): phase carries human-aligned shape; amplitude is fragile. But it is a **corruption/OOD data-augmentation** (ImageNet-C mCE 80.6→57.5), **not** an ℓ∞ defense (no AutoAttack).
- Rippel 2015 spectral pooling (no robustness claim); Selective G-Bispectrum [Mataigne 2024, NeurIPS] (efficiency, no adversarial eval; note: a *complete, invertible* invariant carries the full signal → no information-theoretic shrinkage against an ℓ∞ adversary outside the orbit).

**GAP (verified, with a sharp caveat).** No published work takes a complete group-invariant spectral feature (bispectrum / power spectrum / phase-coupling) and evaluates it as an ℓp defense under AutoAttack. The three closest works each test a *different* problem (group-orbit metamers; common corruptions; efficiency). So "bispectrum + AutoAttack-grade ℓ∞ robustness" is genuinely untested. **But** invariance helps only inside the orbit, and the bispectrum is exactly the non-smooth front-end that produced gradient masking elsewhere. The honest prior: a naive bispectral front-end will either (i) help only against the specific geometric group (narrow but legit), or (ii) be another masking dead end. Pursue only with an adaptive-attack-first protocol.

---

## 2. Test-time defenses

Bottom line: **no heuristic test-time defense beats the best train-time AT under a proper adaptive ℓ∞ attack.** Most collapse; diffusion purification survives only partially and is badly overestimated.

- **DiffPure** [Nie 2022, ICML; arXiv:2205.07460]: claimed CIFAR-10 ℓ∞ 8/255 ≈71% (WRN-70-16). **Re-evaluated down to ~46%** by Lee & Kim 2023 (ICCV Oral; arXiv:2303.09051, PGD+EOT with surrogate process) and independently ~45.8% by ADBM 2024 (arXiv:2408.00315). The original adjoint-gradient eval under-attacks the long stochastic sampler (gradient dilemma of EOT averaging; DiffAttack arXiv:2311.16124, DiffHammer). **L2 result (~79%) is much more genuine than ℓ∞.** Does not beat AT (~70.7%) and costs orders of magnitude more compute.
- **Croce et al. 2022** "Evaluating Adaptive Test-time Defenses" (ICML) — the definitive debunk. On CIFAR-10 ℓ∞ 8/255, **none** of the evaluated adaptive test-time defenses significantly beat its *static* baseline; several actively hurt while multiplying inference cost. E.g. SOAP 51→3.7% (static 0%), ADP-score-purification 69.7→33.7%, ATLD 65.1→12.6%, SODEF 57.8→52.2 vs static 53.9, Anti-Adversaries 79.2→66.6 = static.
- **TTT/Tent** [Sun 2020; Wang 2021]: built for corruptions, not adversarial; and TTA opens a NEW attack surface — Distribution Invading Attack poisons benign batch-mates via shared BN stats [Wu 2023, ICML]. Can be *worse* than no adaptation.
- **Equivariance restoration** [Mao 2023, ICML; arXiv:2212.06079]: the "real-but-small" signal. Test-time restores feature equivariance; on ImageNet ℓ∞ 4/255 **on top of an AT model**, +3.9 pts under (identity-backward) BPDA. Genuine but small, only as an AT add-on, only on 2% of ImageNet, and only mild adaptive testing. Mao 2021's earlier self-supervised version gives **no gain** under Croce 2022 (58.4 vs 59.4 static).
- **Randomized smoothing** [Cohen 2019, ICML] is a *separate, certified* category (provable L2 certificate, ~49% certified at L2 r=0.5) — immune to the masking critique by construction, but answers the certified-L2 question, not ℓ∞.

Open: whether diffusion purification has any *real* ℓ∞ signal beyond the underlying classifier, and the unsettled question of the strongest attack on long stochastic samplers.

---

## 3. Data-centric robustness

The single biggest lever, and AA-verified (real signal, not masking):
- **Generated data + EMA + TRADES is the frontier.** Rebuffi 2021 (1M DDPM → 64.2% AA), Gowal 2021 (DDPM-only → 66.1% AA; scaling 1M→100M adds +2.5%), **Wang 2023 "Better Diffusion Models"** (ICML; EDM data → WRN-28-10 67.31% AA / WRN-70-16 **70.69% AA**, no external real data). Quality (FID) and quantity both help; quality is the higher-leverage axis now.
- **Which examples drive robustness — mixed; partly artifact.** MART [Wang 2020, ICLR] survives AA (56.29%, legitimate). **GAIRAT** geometry-aware instance reweighting [Zhang 2021, ICLR] is the canonical **artifact**: a one-line logit-scaling adaptive PGD drops it ~55%→44% [Hitaj 2021]; excluded from RobustBench for gradient masking. Honest reweighting (VIR-AT [Khan 2023], MAIL) yields only a few AA points. Friendly-AT [Zhang 2020] preserves clean acc / stabilizes AT but doesn't top leaderboards.
- **Memorization tension** [Feldman 2020, NeurIPS]: near-optimal clean accuracy *requires* memorizing rare tail examples, but memorizing them *hurts* robustness; AT refuses to fit high-self-influence samples. A real, barely-exploited accuracy↔robustness Pareto lever.
- **Coreset/pruning/distillation** (HYDRA-adjacent, RCS, GUARD): mostly *efficiency*, with an intriguing unexplained "tiny distilled set → more robust than full data" anomaly. Not competitive on absolute AA.

**Fresh signal:** nobody curates/selects *generated* samples by causal contribution to the robust margin (everyone ranks by FID, which is a leaky proxy — DDIM gives best FID but worst purification robustness). Generate-then-prune-by-robust-influence, validated AA-only, is the cleanest open lane.

---

## 4. Contrarian / bio-inspired / ensemble / sparsity / module-level

GENUINELY SURVIVES strong adaptive / AutoAttack-class eval:
- **Feature Denoising** [Xie 2019, CVPR] — the standout. Non-local-means blocks + AT; ImageNet 42.6% under 2000-iter PGD; won CAAD 2018. Never broken (most robustness from AT, denoising adds real margin).
- **Smooth activations / Smooth AT** [Xie 2020; Singla 2021, ICCV] — reproducible architectural lever on top of AT; best *pure-architecture* idea.
- **Sparsity-as-compression-on-AT** — HYDRA [Sehwag 2020, NeurIPS], Sparsity Winning Twice [Chen 2022, ICLR]: preserve AT robustness at high sparsity. Genuine.
- **MeanSparse** [Amini 2024; arXiv:2406.05927] — VERIFIED current near-SOTA: a **post-training** operator that zeroes mean-centered feature variations within ±α·σ per channel; +1.6% AA on top of Bartoldson (73.71→**75.28%** AA, clean 93.68→93.63), also +2.3% on Wang-2023 L2. Authors **openly state it masks gradients** but show black-box Square attack improves similarly, and an adaptive attack (full knowledge of locations/μ/σ) only "slightly" reduces the gain. This is the most important recent data point for us (see Candidate C).
- **Structured spectral front-end + noise (AT-free)** — "Wavelets Beat Monkeys" [2023, arXiv:2304.09403]: a parameter-free **scattering transform + uniform Gaussian noise** gives substantially more CIFAR-10 adversarial robustness than VOneBlock, **without adversarial training**. The noise is the mechanism (≈ randomized smoothing); the structured front-end shapes the tradeoff. Directly analogous to our spectral conv-pooling layer (see Candidate E).

GRADIENT MASKING / DEAD (broken by adaptive attacks):
- VOneNet's headline +18% is inflated by Poisson-noise masking; the deterministic Gabor front-end alone shows **no** PGD/AA robustness [Dapello 2020/2021]. The noise ≈ randomized smoothing, not the biology.
- k-Winners-Take-All [Xiao 2020] 50→0.16% [Tramèr 2020]. ADP ensemble diversity [Pang 2019] 48.4→0% [Tramèr 2020]. Neural ODEs / TisODE → gradient masking [Huang 2022]. Defense-GAN/PixelDefend → BPDA [Athalye 2018]. "Ensemble Everything Everywhere" multi-res self-ensemble [Fort 2024] 61.8→3.5% / 47.9→0.3% [Zhang/Carlini/Tramèr 2024, arXiv:2411.14834].
- Anti-aliasing/BlurPool [Zhang 2019]: helps **corruptions/shift, NOT** ℓ∞ adversarial — the key nuance for a shift-invariance paper.

Meta-lesson: surviving defenses are either (a) AT + an architectural margin, or (b) honest randomized smoothing. Everything whose robustness came from non-differentiability, discontinuity, or stochastic gradient obfuscation was broken.

---

## 5. The rigor bar (NeurIPS/ICLR 2026) and the obfuscated-gradients trap

**Current SOTA to situate against (CIFAR-10 ℓ∞ 8/255, AA / clean):** Bartoldson 2024 (WRN-94-16) **73.7 / 93.7**; +MeanSparse → **~75.3** AA; Peng 2023 71.1; Wang 2023 70.7. Classic reference points: Carmon 2019 ~59.5, Madry PGD-AT well below.

**Obfuscated gradients** [Athalye 2018, ICML] — three types: shattered (non-differentiable), stochastic (test-time randomness), vanishing/exploding (deep iterated). **Diagnostics that signal masking:** (1) iterative attack worse than single-step FGSM; (2) black-box/gradient-free beats white-box; (3) unbounded ε does not reach 0% accuracy; (4) success-vs-ε not monotone; (5) random search beats gradient descent. **Circumventions a method must survive:** BPDA (non-differentiable), EOT (stochastic), reparameterization (vanishing/exploding).

**Adaptive attacks are mandatory and cannot be automated** [Tramèr 2020, NeurIPS] — 13 defenses that *claimed* adaptive evals were re-broken; adapt the loss to the defense; only the final number matters. **AutoAttack** [Croce & Hein 2020] (APGD-CE, APGD-T/DLR, FAB, Square) is the necessary **floor, not sufficient** — see Ensemble-Everything (61.8→3.5% under adaptive while AA only reached 52% success). Carlini 2019 "On Evaluating Adversarial Robustness" is the checklist.

**Pass/fail gate for our method:** precise threat model · AA + method-specific adaptive attack · all 5 masking diagnostics pass · EOT for any randomness · BPDA for any non-differentiable component · compute- AND synthetic-data-matched baselines · released code/checkpoints. A defense passing AA but failing any masking diagnostic or an adaptive attack is a dead end.

---

## 6. CANDIDATE MECHANISMS (the deliverable)

Five candidates, each flagged **(a)** reuses our spectral/bispectrum machinery, **(b)** genuinely fresh, or both. Ranked by my honest bet. Each has a CHEAP pilot with a falsifiable prediction. The "kill it before training" diagnostic in Candidate 1 should be run first regardless.

---

### Candidate 1 — Phase-coupling stability probe → bispectral two-stream robust features  **(a)+(b)**  [HIGHEST-VALUE FIRST MOVE]

**Mechanism.** Hypothesis from APR [Chen 2021] (phase = semantic, amplitude = fragile) crossed with the bispectrum being a *translation-invariant phase-coupling* invariant. The power spectrum discards phase; the bispectrum B(k₁,k₂)=F(k₁)F(k₂)F*(k₁+k₂) retains *relative* phase (phase coupling) while being translation-invariant. Conjecture: small broadband ℓ∞ perturbations corrupt amplitude/power more than the phase-coupling structure, so a bispectral feature stream is a more attack-stable signal to classify from. Build a two-stream net (power-spectrum stream + bispectrum stream from our existing conv-pooling layers) trained WITH PGD-AT, end-to-end differentiable (no preprocessing step).

**Prior art + why open.** Bispectral NNs [Sanborn 2023] only tested *group-orbit* robustness; APR only tested *corruptions*; nobody has measured the clean→adv stability of a complete phase-coupling invariant under ℓp PGD, nor used it as an AT feature stream. Genuinely untested.

**Adaptive-attack risk: MEDIUM-HIGH.** Must be fully differentiable end-to-end so AutoAttack/APGD flows through the bispectrum (else it's masking). Adversary can target the bispectral stream directly. Risk it merely duplicates TRADES/feature-denoising consistency.

**CHEAP PILOT (do this FIRST — pure diagnostic, no training).** On an existing RobustBench AT model, for N test images compute per-sample relative drift ‖φ(x+δ) − φ(x)‖/‖φ(x)‖ under a standard PGD attack, for φ ∈ {raw pixels, power spectrum, bispectrum}. **Falsifiable prediction:** if the phase-stability hypothesis is real, bispectral features drift *strictly less* than power-spectrum and raw features (e.g., median drift ratio < 0.7×). **If bispectral features drift as much or more than raw features, the entire spectral-robustness direction is dead — kill it for ~$0 of compute before any training.** This single experiment gates Candidates 1, 2, 3, 5.

---

### Candidate 2 — Spectral-basis feature sparsification ("Spectral MeanSparse")  **(a), builds on near-SOTA**  [MOST LIKELY TO PRODUCE A REAL NUMBER]

**Mechanism.** MeanSparse [Amini 2024] is the current near-SOTA add-on: a post-training operator clipping mean-centered feature variations within ±α·σ in the *spatial* feature domain (73.71→75.28% AA on Bartoldson). Fresh angle motivated by Yin 2019 (adversarial energy concentrates in specific frequency bands): apply the sparsification in a *spectral basis* (DCT or our spectral-pooling basis) — clip/zero the frequency components that the AT model doesn't rely on, keeping the bands carrying class signal. Reuses our spectral-pooling machinery as the basis for sparsification; bolts onto any RobustBench AT checkpoint (no retraining).

**Prior art + why open.** MeanSparse sparsifies in the spatial/channel domain only; no one has tried a frequency-domain sparsification basis, and Yin 2019 gives a principled reason it could beat spatial sparsification (the discriminative-vs-adversarial split is cleaner in frequency).

**Adaptive-attack risk: MEDIUM-HIGH (but with a roadmap).** Sparsification masks gradients — but MeanSparse *already* navigates this honestly: it shows Square (black-box) improves too, and an adaptive attack with full operator knowledge only slightly erodes the gain. Replicate that exact protocol (Square + full-knowledge adaptive APGD). Honest worst case: it's spatial MeanSparse with extra steps.

**CHEAP PILOT.** Take Bartoldson/Wang-2023 checkpoint; insert spectral-domain sparsification operators; sweep threshold; evaluate AA + Square + adaptive. **Falsifiable prediction:** spectral-basis sparsification beats spatial MeanSparse's +1.6% AA (target ≥ +2% over base, ≥ +0.5% over spatial MeanSparse) at equal clean-accuracy cost, AND the Square-attack gain tracks the white-box gain (masking check). If it underperforms spatial MeanSparse under matched adaptive eval, drop it.

---

### Candidate 3 — Bispectral consistency regularizer for AT  **(a)**  [SAFE, LOWER NOVELTY]

**Mechanism.** Add a fully-differentiable auxiliary loss to PGD-AT: penalize the change in our (differentiable) bispectral + power-spectrum invariant between clean x and adversarial x+δ, λ·‖φ_bispec(x+δ) − φ_bispec(x)‖². Unlike a front-end, this is a smooth regularizer on top of AT — no preprocessing, no BPDA surface. Rationale: enforce representation stability in a *complete translation-invariant spectral* space rather than logit space (TRADES) or arbitrary feature space (feature denoising).

**Prior art + why open.** TRADES enforces clean/adv KL consistency in logit space; feature denoising denoises arbitrary features. Consistency in a *complete group-invariant spectral* feature has not been tried for ℓ∞ AT. The novelty over TRADES is the *space* in which consistency is enforced; it directly leverages the "self-limiting coupling" framing (a non-η/L regularizer).

**Adaptive-attack risk: LOW-MEDIUM.** Robustness comes from AT; the term is a smooth add-on, so masking risk is low. Main risk is *no effect* — it duplicates TRADES.

**CHEAP PILOT.** WRN-28-10, 1M generated images, PGD-AT vs PGD-AT + bispectral-consistency, matched compute/data. **Falsifiable prediction:** AA improves ≥ +0.5% over matched AT (above run-to-run noise). If gain ≤ noise, it's redundant with TRADES — dead.

---

### Candidate 4 — Margin-criticality curation of GENERATED training data  **(b)**  [FRESHEST, SAFEST FROM MASKING, ORTHOGONAL TO SPECTRAL]

**Mechanism.** The frontier scales diffusion-generated data ranked by FID; nobody selects synthetic samples by *causal contribution to the robust margin*. Generate a large EDM pool, score each candidate by robust-influence / margin-criticality (e.g., effect on per-example margin of an AT proxy, or boundary-distance estimate), train PGD-AT on the curated subset. Combines the generated-data line [Wang 2023], the memorization tension [Feldman 2020], and *honest* (AA-validated) reweighting [VIR-AT].

**Prior art + why open.** GAIRAT-style reweighting was an artifact (white-box-tuned). With 20–50M synthetic images now standard, margin-aware *selection of synthetic data*, validated AA-only, sidesteps the original masking trap and is unexplored. FID is a known-leaky proxy for robustness — there is room for a robustness-predictive data metric.

**Adaptive-attack risk: LOW.** Pure train-time data curation; robustness is from AT itself; no inference-time component to mask gradients. Safest candidate.

**CHEAP PILOT.** Fix data budget (e.g., 1M synthetic); train AT on FID-ranked vs margin-criticality-ranked vs random subsets. **Falsifiable prediction:** margin-curated subset beats FID-ranked and random by ≥ +1% AA at equal data budget. If it ties random, the curation signal isn't there.

---

### Candidate 5 — Spectral-invariant front-end + calibrated noise = certified randomized smoothing  **(a)**  [UNBREAKABLE-BY-CONSTRUCTION, BUT L2]

**Mechanism.** From "Wavelets Beat Monkeys": scatternet + Gaussian noise beats VOneNet AT-free, with the noise as the real (randomized-smoothing) mechanism. Our power-spectrum/bispectrum conv-pooling layer is a structured spectral front-end of the same family. Use it as the smoothing base classifier under Cohen-2019 randomized smoothing: the structured translation-invariant front-end may improve the certified accuracy/radius Pareto by making the smoothed classifier's decision regions align with class-discriminative spectral structure.

**Prior art + why open.** Randomized smoothing base classifiers are standard CNNs; no one has used a complete spectral-invariant front-end as the smoothing base. Wavelets-Beat-Monkeys suggests structured spectral front-ends + noise help, but it reported *empirical* (not certified) numbers and didn't use a complete invariant.

**Adaptive-attack risk: LOW (if done honestly).** Randomized smoothing with proper EOT and a *certified* L2 bound is immune to the masking critique by construction. Risk: the front-end may add nothing over a plain CNN at matched σ; and the guarantee is **L2, not ℓ∞** (a different, smaller-radius claim — must be framed as certified-L2, not as beating the ℓ∞ leaderboard).

**CHEAP PILOT.** Cohen randomized smoothing, plain-CNN base vs spectral-invariant-front-end base, matched σ; compare certified accuracy at L2 radii {0.25, 0.5, 1.0}. **Falsifiable prediction:** spectral front-end improves the certified-accuracy/radius Pareto vs plain CNN at matched σ (e.g., ≥ +2% certified at r=0.5). If it matches plain CNN, the front-end is inert.

---

## 7. Honest recommendation

1. **Run Candidate 1's phase-coupling stability probe FIRST.** It is essentially free (no training, an afternoon on an existing checkpoint) and it gates the entire spectral-robustness thesis. If bispectral features are *not* more attack-stable than raw/power-spectrum features, abandon the spectral-mechanism angle and go to Candidate 4 (margin-criticality data curation), which is fresh, masking-safe, and orthogonal.
2. **If the probe is positive,** the highest-EV publishable path is **Candidate 2 (Spectral MeanSparse)** — it builds on a mechanism that *already* survives adaptive evaluation near SOTA, plugs into RobustBench checkpoints with no retraining, and has a principled Yin-2019 motivation. Pair it with **Candidate 3** (bispectral-consistency AT) as the train-time companion.
3. **Candidate 5** is the "guaranteed unbreakable but modest, L2-only" insurance result — useful if reviewers demand a non-empirical contribution, but don't expect it to top the ℓ∞ board.
4. **Brutal honesty for the paper:** invariance ≠ ℓ∞ robustness; the bispectrum is a masking-shaped front-end; and the bar is ~73–75% AA with full adaptive evaluation. The only credible spectral contributions are ones that (i) bolt onto AT rather than replace it, (ii) are end-to-end differentiable so AutoAttack flows through them, and (iii) pass Square + a full-knowledge adaptive attack with the masking diagnostics reported. Frame any spectral mechanism as an *AT add-on margin*, never as a standalone preprocessing defense.

---

## References (verified)
- Athalye, Carlini, Wagner 2018, ICML — Obfuscated Gradients. arXiv:1802.00420
- Tramèr, Carlini, Brendel, Madry 2020, NeurIPS — On Adaptive Attacks. arXiv:2002.08347
- Carlini, Athalye et al. 2019 — On Evaluating Adversarial Robustness. arXiv:1902.06705
- Croce & Hein 2020, ICML — AutoAttack. PMLR v119; github.com/fra31/auto-attack
- Croce et al. 2021, NeurIPS D&B — RobustBench. robustbench.github.io
- Bartoldson, Diffenderfer, Parasyris, Kailkhura 2024, ICML — Scaling-law robustness (SOTA ~73.7% AA)
- Amini et al. 2024 — MeanSparse. arXiv:2406.05927 (post-training feature sparsification; 73.71→75.28% AA)
- Zhang, Nikolić, Carlini, Tramèr 2024 — Ensemble Everything Everywhere Is Not Robust. arXiv:2411.14834
- Yin et al. 2019, NeurIPS — A Fourier Perspective on Model Robustness
- Wang et al. 2020, CVPR — High-Frequency Component. arXiv:1905.13545
- Tsuzuku & Sato 2019, CVPR — Structural Sensitivity to Fourier directions. arXiv:1809.04098
- Sanborn et al. 2023, ICLR — Bispectral Neural Networks. arXiv:2209.03416 (invariance-based robustness only)
- Chen et al. 2021, ICCV — Amplitude-Phase Recombination. arXiv:2108.08487
- Cisse et al. 2017, ICML — Parseval Networks; Leino 2021 GloRo; Hu 2023 LiResNet (certified Lipschitz)
- Nie et al. 2022, ICML — DiffPure. arXiv:2205.07460; Lee & Kim 2023, ICCV — re-eval. arXiv:2303.09051; ADBM arXiv:2408.00315
- Croce et al. 2022, ICML — Evaluating Adaptive Test-time Defenses. arXiv:2202.13711
- Mao et al. 2023, ICML — Robust Perception through Equivariance. arXiv:2212.06079; Mao 2021, ICCV arXiv:2103.14222
- Cohen, Rosenfeld, Kolter 2019, ICML — Randomized Smoothing. PMLR v97
- Gowal et al. 2021, NeurIPS — Generated data. arXiv:2110.09468; Rebuffi 2021 arXiv:2103.01946; Wang et al. 2023, ICML — Better Diffusion Models. arXiv:2302.04638
- Zhang 2021, ICLR — GAIRAT; Hitaj 2021 break arXiv:2103.01914; Wang 2020 MART (ICLR); Khan 2023 VIR-AT arXiv:2307.07167
- Feldman & Zhang 2020, NeurIPS — Memorization. arXiv:2008.03703
- Dapello et al. 2020, NeurIPS — VOneNet; Dapello 2021 NeurIPS arXiv:2111.06979; "Wavelets Beat Monkeys" 2023 arXiv:2304.09403
- Xie et al. 2019, CVPR — Feature Denoising. arXiv:1812.03411; Xie 2020 Smooth AT arXiv:2006.14536
- Sehwag et al. 2020, NeurIPS — HYDRA; Xiao 2020 k-WTA (broken); Pang 2019 ADP (broken)
- Zhang 2019, ICML — Making CNNs Shift-Invariant Again (BlurPool; corruptions not ℓ∞). arXiv:1904.11486
