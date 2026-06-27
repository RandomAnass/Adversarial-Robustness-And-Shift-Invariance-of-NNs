# Empirical Adversarial-Robustness Frontier (2022-2026): Levers, Walls, and Gaps for a New Method

Scope: CIFAR-10, ℓ∞, ε = 8/255, AutoAttack (AA) as the robustness metric unless stated. Compiled 2026-06 from a 5-angle deep-research sweep with adversarial cross-checking. Every load-bearing number carries a source URL and a confidence/caveat tag.

Our standing result this survey serves: **under PGD adversarial training, per-sample classification margin M and input-gradient norm ‖∇‖ are POSITIVELY coupled** — the network buys margin by raising local sensitivity ("self-limiting coupling"). Directly regularizing the ratio η/L (≈ M/‖∇‖) FAILS: penalizing ‖∇‖ collapses M in lockstep; maximizing the ratio yields a useless constant classifier. We want a method that raises effective margin **without sharpening** (without inflating the input gradient), ideally attacking the coupling at its source (data / architecture / training dynamics). We have a fast CIFAR-10 PGD-AT + AutoAttack pilot pipeline.

---

## 0. TL;DR

- **The frontier is data-and-scale, and it is saturating.** Vanilla PGD-AT (Madry) sits at ~46% AA on a WideResNet; today's top is ~73.7% AA from training (Bartoldson2024, WRN-94-16, 500M synthetic images) and ~75.3% AA with a post-hoc inference trick on top (MeanSparse2024). Roughly **two-thirds to three-quarters of the entire +29pp jump over Madry is the diffusion/EDM generated-data lever alone**; everything else (loss, weight-averaging, architecture micro-design, brute scale, post-hoc tricks) splits the last ~9pp.
- **Scaling is a wall.** Bartoldson2024's AT scaling laws predict robustness plateaus near **~90% AA**, and closing the remaining ~15pp by scale alone would cost ~10^30 FLOPs ("≈3,000 years on 25,000 H100/MI300 GPUs"). Their own conclusion: *progress now requires better algorithms and architectures, not more scale.* This is the single most important strategic fact for positioning a new method.
- **Most "clever loss / reweighting / feature-space" levers are saturated, fragile, or debunked under AutoAttack.** GAIRAT-style geometric reweighting is a gradient-masking artifact (triple-confirmed). Feature-scatter / adversarial-interpolation collapse 29-40pp under AA. Distillation for small students is real but capped at ~2pp below the teacher. SAM-alone "robustness" is reported at ε=1/255, not 8/255.
- **The two papers closest to our thesis** are Smooth Adversarial Training (Xie2020) and Low-Curvature Activations (Singla2021), plus the curvature-robustness identity CURE (Moosavi2019) and the fixed-Lipschitz + margin-maximization line (LiResNet's "EMMA"). None of them frames the contribution as *explicitly breaking the margin↔gradient-norm coupling* — that framing is open.
- **Novelty bar 2026:** AutoAttack (not PGD) + a full gradient-masking checklist is mandatory; comparisons must be at matched data and matched architecture; a pure new mechanism without SOTA can still publish if it shows a clean *mechanistic* contribution plus honest diagnostics. A WRN-28-10 entry is "competitive" around clean ≥88-92% / AA ≥63-67%.

---

## 1. The lever map (with saturation status)

### 1.1 Current RobustBench CIFAR-10 ℓ∞ 8/255 leaderboard (top training entries)

| Model / paper | Clean % | AA % | Lever | Extra/gen data |
|---|---|---|---|---|
| **MeanSparse** on Bartoldson WRN-94-16 (Amini 2024) | ~93.6 | **75.28** | post-training feature sparsification (no retrain) | (inherits) |
| **Bartoldson2024** WRN-94-16 (ICML'24) | 93.68 | **73.71** | brute scale + scaling-law recipe | 500M EDM synthetic |
| Bartoldson2024 WRN-82-8 | 93.11 | 71.59 | scale | synthetic |
| **Peng2023** RaWideResNet-70-16 (BMVC'23) | 93.27 | **71.07** | architecture micro-design | Wang's EDM data |
| **Wang2023** WRN-70-16 (ICML'23) | 93.25 | **70.69** | diffusion (EDM) data + TRADES | 50M EDM |
| Wang2023 WRN-28-10 | 92.44 | 67.31 | diffusion data | 20M EDM |
| Cui2023 WRN-28-10 (Decoupled-KL) | 92.16 | 67.73 | loss + data | synthetic |

Confirmed: MeanSparse abstract states "a new robustness record of 75.28% (from 73.71%)" via AutoAttack, applied post-hoc to adversarially-trained models with no retraining (arxiv.org/abs/2406.05927). Bartoldson abstract confirms "74% AutoAttack accuracy (+3% gain)" and plateau "near 90%" (arxiv.org/abs/2404.09349). Wang2023 abstract confirms 70.69% on CIFAR-10 for the best model (arxiv.org/abs/2302.04638).
Caveat: the live RobustBench board is JS-rendered/not text-fetchable; exact cell ordering should be spot-checked at robustbench.github.io/cifar10/Linf.html before quoting in a paper. The "S-WRN-94-16 = 73.10" variant seen in one README dump is a different/stale entry; the paper headline is 75.28.

### 1.2 Lever-by-lever, gain and saturation

| Lever | Representative method | AA gain vs its baseline | Saturation verdict |
|---|---|---|---|
| **Generated/extra data** | DDPM (Rebuffi2021, Gowal2021) → EDM (Wang2023) | **+20pp** (Madry~46→DDPM~66), then +4.6pp (DDPM→EDM 70.7) | **SATURATED.** Dominant historical lever; now diminishing — scaling laws plateau ~90% at impractical compute |
| **Brute scale (width/depth)** | WRN-28-10→70-16→94-16 (Gowal2020, Bartoldson2024) | +3-6pp w/ data; depth ≳ width at fixed params | **PARTIALLY SATURATED.** Still helps but diminishing; data scaling dominates |
| **Weight averaging / flatness** | AWP (Wu2020), SWA/EMA (Gowal2020) | AWP +2.0-2.6pp, additive; EMA enabling | **SATURATED → mandatory default.** In essentially every leader; no longer a differentiator |
| **Loss: tradeoff dial** | TRADES (Zhang2019, β knob) | +~5pp over Madry | **SATURATED.** Canonical baseline/dial everyone compares to |
| **Loss: misclassification-aware** | MART (Wang2020) | +~3pp (PGD-favorable, weaker AA) | **SATURATED / superseded** |
| **Loss: boundary-guided** | LBGAT (Cui2021) | ~TRADES robustness, higher clean (88.2/52.9) | **SATURATED** (accuracy-frontier point) |
| **Loss: proper definition** | SCORE (Pang2022) | top-rank only *with* data (89.0/63.4 WRN-70-16) | **ACTIVE but fused with data scaling** |
| **Loss: helper/excessive-margin** | HAT (Rade2022) | +~1pp clean & +~1pp robust over TRADES | **Numerically modest, conceptually load-bearing** (see §5) |
| **Architecture micro-design** | RaWideResNet (Peng2023): conv stem + SE + smooth act | +1-3pp CIFAR, +4-9pp ImageNet | **ACTIVE** but small on CIFAR |
| **Smooth activations** | Smooth-AT (Xie2020): ReLU→SiLU | **+7-9pp robust** (ImageNet ε=4/255) | **ABSORBED as a design principle; mechanism still active** (see §5) |
| **Low-curvature activations** | Singla2021 | +1.7pp robust + cuts robust-overfitting gap 3.1→0.5% | **Underexplored / active** (see §5) |
| **Architecture family** | ViT vs CNN (Bai2021) | ~0 at matched recipe/scale | **NOT a lever.** Recipe + data dominate |
| **Post-training inference trick** | MeanSparse (Amini2024) | +1.6pp (73.7→75.3) | new micro-frontier; tiny gains, no retrain |

Attribution of the ~29pp Madry→SOTA jump: generated data ~+20pp (largest single chunk) → better generator (DDPM→EDM) ~+4.6pp → architecture ~+0.4pp → scale ~+2.6pp → post-hoc trick ~+1.6pp. **Data is the lever; the rest is the long tail.**

Sources: Rebuffi2021 arxiv.org/abs/2103.01946 · Gowal2021 arxiv.org/abs/2110.09468 · Wang2023 arxiv.org/abs/2302.04638 · Peng2023 arxiv.org/abs/2308.16258 · Bartoldson2024 arxiv.org/abs/2404.09349 · Amini2024 arxiv.org/abs/2406.05927 · TRADES arxiv.org/abs/1901.08573 · MART openreview.net/forum?id=rklOg6EFwS · LBGAT arxiv.org/abs/2011.11164 · SCORE arxiv.org/abs/2202.10103 · HAT openreview.net/forum?id=BuD2LmNaU3a + github.com/imrahulr/hat · AWP arxiv.org/abs/2004.05884 · Gowal2020 arxiv.org/abs/2010.03593 · Smooth-AT arxiv.org/abs/2006.14536 · Singla2021 arxiv.org/abs/2102.07861 · Bai2021 arxiv.org/abs/2111.05740.

---

## 2. Open problems / diminishing-returns walls (2024-2026)

1. **The ℓ∞ ~70-75% AA ceiling is a hard practical wall (OPEN).** Despite enormous diffusion data, SOTA moved only ~70.7% (2023) → ~73.7-75.3% (2024). Bartoldson2024 scaling laws: robustness "slowly grows then plateaus at 90%"; reaching ~90% by scale alone ≈ 10^30 FLOPs ("≈3,000 years of TF32 on 25,000 MI300/H100"). A ~90% *human-alignment* ceiling also caps the threat model (ε=8/255 ℓ∞ attacks produce label-flipped "invalid images"), so perfect robustness is impossible here. Conclusion verbatim: progress "requires the design of more efficient training algorithms and improved architectures, rather than simply scaling." (arxiv.org/abs/2404.09349)

2. **Robust overfitting: workaround exists, mechanism unexplained (OPEN).** Rice2020 (arXiv:2002.11569, ICML'20): robust *test* acc peaks just after the first LR decay then degrades while train robustness rises — best→final degradation of **8.2pp** (43.2%→51.4% robust error) on CIFAR-10. "Virtually all recent algorithmic improvements upon adversarial training can be matched by simply using early stopping." Cause still "not fully explained" in 2024-2026; active mitigations (random forgetting, Wasserstein-DRO ICLR'25, SWA/self-distillation smoothing) are partial. Nuance: with sufficient diffusion data, robust overfitting largely dissolves (Wang2023) — it is partly an artifact of data scarcity.

3. **Robustness-accuracy trade-off: not information-theoretically fundamental for real data, but unsolved in practice (OPEN-in-practice).** Tsipras2019 (arXiv:1805.12152) proved a trade-off *in a constructed distribution* (e.g. ≥99% clean ⇒ ≤19% robust). Yang2020 (arXiv:2003.02460) showed real image classes are r-separated (CIFAR-10 min class separation ≈0.21 ≈ 3.4× the 0.031 attack radius), so a locally-Lipschitz classifier can in principle be both accurate and robust — the trade-off is "an artifact of current methods failing to impose local Lipschitzness." SCORE (Pang2022) and HAT (Rade2022) reduce but do not eliminate the empirical gap. **This is the strongest theoretical license for our program: the binding constraint is local Lipschitzness / margin geometry, not an information limit.**

4. **Robust generalization needs ~√d more data (OPEN).** Schmidt2018 (arXiv:1804.11285): robust generalization sample complexity exceeds standard by a factor polynomial in dimension (Ω(ε²√d) in the Gaussian model), information-theoretic and algorithm-independent. Drives the whole extra-data line; mitigated (not closed) by synthetic data at extreme compute.

5. **The field openly says it is stuck.** Carlini-style 2025 position paper "Adversarial ML Problems Are Getting Harder to Solve and to Evaluate" (arXiv:2502.02260): "even fundamental 'toy' problems like robustness to ℓp-bounded perturbations remain largely unsolved to this day"; "many defense evaluations still lack rigor"; warns "yet another decade of work … may fail to produce meaningful progress." A 2024 position paper (arXiv:2405.01349) argues for pivoting from static robustness to *resilience* (fast adaptation to unseen attacks).

---

## 3. Underexplored / contrarian directions — honest status

Bottom line: most of this space is either fragile under AutoAttack or saturated. Knowing what is *dead* is as valuable as what is live, because it tells you the failure modes a new method must avoid.

- **Geometric instance reweighting — DEBUNKED.** GAIRAT (Zhang2021) reweights by distance-to-boundary (# PGD steps to flip). A one-line logit-scaling PGD collapses it (53.8%→43.9%); its own AutoAttack is only ~33% (RN-18) / ~40% (WRN-32-10) vs ~54-59% PGD — triple-confirmed (Hitaj arXiv:2103.01914, MAIL arXiv:2106.07904, VIR-AT arXiv:2307.07167). **This is the canonical "false robustness / gradient masking" case.**
- **Reweighting only works *through* TRADES (CONTRARIAN, well-supported).** MAIL-AT ≈ vanilla AT under AA (44.2 vs 44.9, RN-18); the gain appears only as MAIL-TRADES (50.6 vs TRADES 48.1). Even 2023's repaired VIR-AT (48.2 AA RN-18) merely *ties* plain TRADES. Reweighting-on-vanilla-AT contributes ≈0 AA points.
- **Curriculum / friendly AT — superseded for peak robustness.** FAT (Zhang2020) early-stopped PGD trades AA robustness for clean accuracy; "Bag of Tricks" (arXiv:2010.00467) shows the PGD-vs-AA gap. Learnable attack-strategy (LAS-AT, CVPR'22) and ε-scheduling give small but real AA gains (~0.3-4pp) — **live but small-margin/underexplored.**
- **Flatness beyond AWP — live, incremental.** RWP (IJCAI'22, arXiv:2205.14826) +3pp PGD over AWP and suppresses robust overfitting. SAM-alone is **NOT** an 8/255 AT substitute — its "robustness" numbers are at ε=1/255 with a ~30pp gap to AT (arXiv:2305.05392). Hessian/second-order flatness remains underexplored.
- **Feature-space objectives — mostly DEBUNKED.** Feature Scattering (58.6→29.4 under AA), Adversarial Interpolation (68.7→36.5), Bilateral AT (66.9→26.9): all collapse 29-40pp under AutoAttack (Croce-Hein arXiv:2003.01690). Channel-wise Activation Suppression (CAS, ICLR'21) survives but is minor/uncertain. **Strong cautionary cluster for any latent-space objective.**
- **Distillation for small students — real but saturated.** RN-18 student AA: SAT 45.8 · TRADES 49.2 · ARD 49.2 · IAD 49.1 · RSLAD **51.5** (teacher 53.1). ARD≈IAD≈TRADES (early distillers add ~0 over just running TRADES on the student); RSLAD's robust soft labels add ~+2.3; the student is bounded above by the teacher. 2023-2026 variants chase the same 1-2pp. The "unreliable teacher" / "why robust teachers fail" question is the live open piece. (RSLAD arXiv:2108.07969, ARD arXiv:1905.09747, IAD arXiv:2106.04928.)

---

## 4. The 2026 novelty bar

Mandatory gates (desk-reject without them):
1. **AutoAttack, not PGD.** PGD-only is not credible; the Croce-Hein ensemble (APGD-CE + APGD-DLR + FAB + Square) and the RobustBench protocol are the de-facto standard (arxiv.org/abs/2010.09670, robustbench.github.io).
2. **Gradient-masking / obfuscated-gradients checklist.** Reviewers expect explicit ruling-out: black-box ≥ white-box sanity, unbounded attack → 0% acc, more iterations/restarts don't help, PGD-robust-but-FAB/Square-weak is the tell (Athalye2018 arXiv:1802.00420, Carlini2019 arXiv:1902.06705). Our whole §3 shows why this gate kills most "clever" methods.
3. **Controlled comparison at matched data + matched architecture.** Generated data inflates everyone ~+5-10pp; a new method must either beat TRADES+EDM-data *at the same data budget and architecture*, or match SOTA at substantially lower compute (Bartoldson framing: SOTA at ~20% fewer training / 70% fewer inference FLOPs).

Concrete competitiveness on WRN-28-10 CIFAR-10 ℓ∞ 8/255: roughly **clean ≥88-92% and AA ≥63-67%** with generated data, OR a credible Pareto improvement (same robustness at lower clean-accuracy cost or lower compute), OR a clean *mechanistic* result with full diagnostics. Raw board SOTA (~71-75% AA) is on much larger nets with massive synthetic data; you do not need to top the board to publish, but you must be honest about which regime you are in.

---

## 5. The 3-5 concrete GAPS where a new method could live

Ranked by fit to our margin↔sensitivity result and by how crowded each is. Each gap states the bet, the closest prior work to beat, and an honest difficulty/crowdedness read.

### GAP A (BEST FIT) — "Margin without sharpening": decouple margin growth from input-gradient growth, the coupling our paper measured

The bet: our positive coupling (PGD-AT buys margin by raising ‖∇‖) explains *why* the naive ratio-regularizer and MMA-style direct margin maximization fail — they buy apparent margin by sharpening/masking. The opening is a training objective or architectural constraint that **provably grows the linearized margin M while holding ‖∇‖ (or local Lipschitz L) flat**, verified by directly measuring the M-vs-‖∇‖ scatter before/after, plus the AA + gradient-masking gates. The diagnostic ("does the method move points up-and-left in the M vs ‖∇‖ plane, instead of up-and-right?") is itself a contribution and is, as far as this sweep found, **not the explicit frame of any existing paper.**

- Closest prior to beat / cite: Tsuzuku2018 Lipschitz-Margin (the M/(√2·L) identity, arXiv:1802.04034) — the naive joint margin+Lipschitz penalty is the baseline; MMA (Ding2020, arXiv:1812.02637; ~84/41 AA, with gradient-masking-inflated PGD — a *worked example of our failure mode*); HAT (Rade2022) which shows AT manufactures *excessive*, directional margin that hurts clean accuracy; CURE (Moosavi2019, arXiv:1811.09716) which proves robustness ⇔ low input-loss curvature (i.e. a *stable* gradient, not a big one).
- Difficulty/crowdedness: **conceptually crowded around the parts, empirically open at the frame.** The pieces (Tsuzuku, MMA, HAT, CURE, EMMA) exist; nobody packages "break the empirically-measured margin/gradient coupling" as the thesis with the scatter-plot diagnostic. Risk: ending up at MMA's fate (apparent margin via masking) — which is exactly why the AA + diagnostic discipline is the contribution, not a formality. This is the highest-fit, most-defensible gap because our coupling result is the genuinely new asset.

### GAP B (HIGH FIT) — Architecture/activation as the source-level fix: get margin via curvature control, not gradient inflation

The bet: smooth / low-curvature activations already improve robustness *for free* by smoothing the input-space loss landscape (stabilizing the gradient across the ε-ball) rather than enlarging it — the same axis our coupling lives on. The gap is to (i) connect this mechanism explicitly to the margin↔sensitivity coupling, and (ii) push it: e.g. curvature-budgeted training, learnable per-layer curvature, or activation/normalization choices that demonstrably hold ‖∇‖ flat while AT raises margin.

- Closest prior to beat / cite: Smooth-AT (Xie2020): ReLU→SiLU gives +9.3pp robust on ImageNet (ε=4/255) with +0.9% clean, and the forward/backward control isolates *gradient quality*, not the forward shape, as the cause (+3.9pp from fixing only the backward pass). Singla2021 Low-Curvature Activations: +1.7pp robust and robust-overfitting gap 3.1%→0.5% on CIFAR-10. Peng2023 RaWideResNet folds smooth activations into a robust-design recipe (+1-3pp CIFAR).
- Difficulty/crowdedness: **moderately crowded; the "for free" mechanism is real and underused on CIFAR ℓ∞.** Most smooth-activation evidence is ImageNet ε=4/255; a clean CIFAR-10 ℓ∞ 8/255 study that ties curvature control to the measured coupling, with AA, is a plausible focused contribution. Risk: incrementality — gains may be small (1-3pp), so the framing/mechanism must carry the paper, not the leaderboard delta.

### GAP C (MEDIUM FIT) — Local (not global) Lipschitz + margin, closing the certified↔empirical gap from the empirical side

The bet: 1-Lipschitz architectures *fix the denominator by construction* (L=1) and then maximize margin — LiResNet's loss is literally EMMA (Efficient Margin MAximization). But global-Lipschitz constraints cost ~30pp of accuracy in ℓ∞ (certified ~40% at 8/255 vs empirical ~70%). The gap: bring the "fixed L, maximize M" discipline to *empirical* AT via **local** sensitivity control (per-batch/per-region Lipschitz or curvature budgets) so you get the favorable M/L ratio without paying the global-Lipschitz clean-accuracy tax.

- Closest prior to beat / cite: SortNet/GroupSort, Cayley (Trockman2021), SLL (Araujo2023 arXiv:2303.03169), LiResNet/EMMA (Hu2023/24), BRONet (arXiv:2505.15174). ℓ∞ certified at 8/255 ≈ 40.4% (SortNet, arXiv:2110.06850). Keep the ℓ2-vs-ℓ∞ trap explicit: most clean Lipschitz numbers are ℓ2 at radius 36/255, not ℓ∞ 8/255.
- Difficulty/crowdedness: **crowded and hard.** The certified-robustness community is large, sophisticated, and has tried many local-Lipschitz ideas; the global→local move is the obvious direction everyone eyes. Honest read: high risk of being scooped or of the local bound being too loose to help. Lower priority than A/B unless we have a specific local-control mechanism the coupling result suggests.

### GAP D (MEDIUM FIT, contrarian) — Data-centric reshaping of the coupling: which examples *create* the margin↔sensitivity coupling, and can data fix it at the source

The bet: instance reweighting failed (GAIRAT debunked; reweighting-on-AT ≈0 AA) because it reweights a *loss*, inducing masking. But the *source-level* question — which training examples drive the up-and-right (margin-via-sharpening) behavior, and whether curating/relabeling/generating data along the coupling axis can shift it — is largely untouched. HAT's "helper examples" (correctly-perturbed inputs given wrong labels to cap excess margin) is the one data-side intervention on margin geometry; generated-data papers never analyze *which* synthetic examples reshape the M-vs-‖∇‖ relationship.

- Closest prior to beat / cite: HAT (Rade2022, the only margin-geometry data intervention); the debunked reweighting line (GAIRAT/MAIL/VIR-AT) as the cautionary boundary; Wang2023/Bartoldson2024 generated-data (which treat data as undifferentiated volume). The 2023 data-survey (arXiv:2303.09767) frames data as the central lever but not along this axis.
- Difficulty/crowdedness: **underexplored but treacherous.** Data-centric robustness is fashionable, and any reweighting smell invites the gradient-masking critique — must be evaluated with the §4 gates from day one. Upside: data interventions are cheap to pilot on our fast CIFAR pipeline, and a per-example *measurement* of the coupling (which examples push margin via sharpening) is a novel diagnostic even before a method.

### GAP E (LONGER SHOT) — Training-dynamics / scheduling that prevents the coupling from forming, not flatness-after-the-fact

The bet: the coupling is a *dynamics* phenomenon (margin and ‖∇‖ co-grow over training). Most flatness work (AWP/SWA/RWP) flattens the *weight* landscape post-hoc. The gap: a schedule or dynamics intervention (ε/curvature/curriculum on the *input-gradient* trajectory) that keeps M and ‖∇‖ decoupled *as they form*, monitored live via the coupling diagnostic.

- Closest prior to beat / cite: AWP (Wu2020), RWP (arXiv:2205.14826), LAS-AT (arXiv:2203.06616), Strength-Adaptive AT (arXiv:2210.01288), robust-overfitting dynamics work.
- Difficulty/crowdedness: **scheduling is well-trodden and gains are small (sub-1 to few pp).** Lowest-priority standalone, but a strong *complement* to A/B: "our objective decouples M from ‖∇‖, and the right schedule keeps it decoupled throughout training." Best used as a section, not a paper.

### How the gaps connect to the coupling (one-line each)
- A: attack the coupling directly with an objective/constraint + the scatter-plot diagnostic. **(core asset)**
- B: attack it via activation curvature — the "for free", stable-gradient axis. **(most ready to pilot)**
- C: fix L by construction (global→local) and let margin be the lever. **(crowded/hard)**
- D: find/curate the data that creates the coupling. **(novel diagnostic, masking-risk)**
- E: prevent the coupling in the training trajectory. **(complement, not standalone)**

Recommended pilot order on our fast pipeline: **B then A** (B is cheap and almost-free to test: swap activations, measure the M-vs-‖∇‖ scatter and AA; A reuses the same diagnostic and is the higher-novelty payoff), with **D** as a parallel cheap data probe. C and E are higher-risk / better as supporting sections.

---

## 6. Verification notes and confidence

- **High confidence (cross-checked, multi-source):** Madry baseline ~46% AA; data lever ~+20pp; Wang2023 70.69% (best) / 67.31% (WRN-28-10); Bartoldson2024 ~73.7% AA, ~90% asymptote, 10^30 FLOPs, "algorithms not scale" conclusion; MeanSparse 75.28% post-hoc; Rice2020 8.2pp robust-overfitting gap and "early stopping matches everything"; GAIRAT AA collapse (triple-confirmed); feature-scatter/interpolation AA collapse; Smooth-AT +9.3pp (ImageNet ε=4/255, flagged); Singla2021 curvature/overfitting numbers; Tsuzuku M/(√2L) identity.
- **Flagged caveats:** (1) RobustBench live board is JS-rendered — confirm exact cell ordering before publication. (2) Smooth-AT's headline numbers are **ImageNet ε=4/255**, not CIFAR-10 ℓ∞ 8/255 — do not transplant the +9pp figure to our setting; it must be re-piloted. (3) Most Lipschitz-net clean numbers are **ℓ2 (radius 36/255)**, not ℓ∞ 8/255; keep the threat model explicit. (4) Citation collision resolved: arXiv:2002.11569 = Rice2020 (robust overfitting); HAT = OpenReview BuD2LmNaU3a / github.com/imrahulr/hat (an earlier subagent mis-attributed 2002.11569 to HAT).

## Key sources
RobustBench robustbench.github.io/cifar10/Linf.html · AutoAttack arxiv.org/abs/2010.09670 · Madry/Athalye-obfuscated-gradients arxiv.org/abs/1802.00420 · Carlini-eval arxiv.org/abs/1902.06705 · Rebuffi2021 arxiv.org/abs/2103.01946 · Gowal2021 arxiv.org/abs/2110.09468 · Gowal2020 arxiv.org/abs/2010.03593 · Wang2023 arxiv.org/abs/2302.04638 · Peng2023 arxiv.org/abs/2308.16258 · Bartoldson2024 arxiv.org/abs/2404.09349 · Amini2024-MeanSparse arxiv.org/abs/2406.05927 · TRADES arxiv.org/abs/1901.08573 · MART openreview.net/forum?id=rklOg6EFwS · SCORE arxiv.org/abs/2202.10103 · LBGAT arxiv.org/abs/2011.11164 · HAT openreview.net/forum?id=BuD2LmNaU3a · AWP arxiv.org/abs/2004.05884 · RWP arxiv.org/abs/2205.14826 · Smooth-AT arxiv.org/abs/2006.14536 · Singla2021 arxiv.org/abs/2102.07861 · CURE arxiv.org/abs/1811.09716 · Tsuzuku2018 arxiv.org/abs/1802.04034 · MMA arxiv.org/abs/1812.02637 · SLL arxiv.org/abs/2303.03169 · BRONet arxiv.org/abs/2505.15174 · SortNet-Linf arxiv.org/abs/2110.06850 · Rice2020 arXiv:2002.11569 · Tsipras2019 arxiv.org/abs/1805.12152 · Yang2020 arxiv.org/abs/2003.02460 · Schmidt2018 arxiv.org/abs/1804.11285 · GAIRAT-debunk arxiv.org/abs/2103.01914 · MAIL arxiv.org/abs/2106.07904 · VIR-AT arxiv.org/abs/2307.07167 · FAT arxiv.org/abs/2002.11242 · Bag-of-Tricks arxiv.org/abs/2010.00467 · SAM-robustness arxiv.org/abs/2305.05392 · RSLAD arxiv.org/abs/2108.07969 · ARD arxiv.org/abs/1905.09747 · IAD arxiv.org/abs/2106.04928 · Position2025 arxiv.org/abs/2502.02260 · Resilience-position arxiv.org/abs/2405.01349 · Data-survey arxiv.org/abs/2303.09767.
