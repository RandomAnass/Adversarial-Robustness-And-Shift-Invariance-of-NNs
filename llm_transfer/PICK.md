# PICK — Strong-Picker synthesis of the 9 LLM-transfer pilots

Synthesizes the 9 designs (A1-3, B1-3, C1-3), the 6 adversarial audits (literature round 1 +
experimental-design round 2), and the source theory (`paper/report/main.tex`: `\eta/L` margin-to-
Lipschitz ratio, gauge Lemma `lem:ratiodegen`, dual-norm threat-matching, count law `prop:count`,
orbit-flip radius `prop:rhoG`, group-average projector `thm:finite-group`).

**Decision law (from the audits, binding on all protocols below):**
1. The vision paper's own matched-vs-mismatched correlation only separated at ~12 arms; at 6-8 arms
   CIs overlap. **Rest significance on the per-prompt / per-image axis (>=1,000 items, bootstrap CIs,
   partial correlations), not on a handful of operator arms.** Operator/dose correlation is the coarse
   confirmation only.
2. **The Schwinn embedding attack (2402.09063) is UNCONSTRAINED and APPEND-BASED** — not an "L2-ball
   perturbation of the prompt embeddings." Every design that cited it that way is wrong. The strong
   attack must be a *self-defined projected* embedding-PGD on the prompt's own `e(x)` (for a radius:
   wrap in a minimum-norm bisection search), sharing the certificate's threat model. Keep unbounded
   append-Schwinn only as the "unbounded ceiling" masking check.
3. **Gradient-masking audit is mandatory, first-class, reported** (not a footnote): steps/restarts
   monotonicity + vanishing-gradient log + unbounded ceiling + discrete GCG cross-check (text side) /
   APGD<=PGD-40 + Square-Attack + EoT-gap (vision side). Nasr "Attacker Moves Second" (2510.09023) is
   now the eval standard; embedding-only evidence draws "you didn't run a strong adaptive attack."
4. **Partial correlation controlling clean accuracy** (and, on text, controlling the attack radius
   itself against near-tautology) is the load-bearing statistic — matches the paper's own caveat that
   `\eta/L` must beat clean-acc-as-confound.

**Environment (verified on disk, this session):** use the existing **`al_selfdistill` conda env**
(`~/.conda/envs/al_selfdistill`: torch 2.9.0+cu128, transformers 4.57.1, peft 0.17.1, CUDA OK). It is
healthy — do NOT rebuild a venv (round-2's "base anaconda broken" note applies to the *base* env, not
this one). Missing pieces to add: `nanogcg`, `open_clip_torch`, `autoattack`/`robustbench`, a local
judge, and the benchmarks (details per pilot). Cached & relevant: `Meta-Llama-3-8B-Instruct`,
`Qwen2.5-7B-Instruct`, `Qwen3-8B`, `gpt-oss-20b`, `Qwen2.5-VL-7B-Instruct`, `deberta-v3-large-zeroshot-
v2.0`, `cais/mmlu`, `sst2`, `rotten_tomatoes`, `PKU-SafeRLHF`, DINOv3 ViT-L/16 + DINOv2 ViT-L/14
(C1 panel wideners). ABSENT: any CLIP / FARE / TeCoA / LLaVA / Llama-Guard / HarmBench-cls /
HarmBench / AdvBench / XSTest.

---

## 1. Ranked shortlist (after merging overlaps; best first)

Scores are 1-5 (5 best). **Novelty** = what survived the literature audit as genuinely un-run.
**Feasibility** = run-readiness on 2xA6000 including download/eng risk. **Impact** = standalone
top-tier-journal potential. Merges: **A1+B1** (same gauge-free ratio + consistency-vs-robustness
dissociation, text) and **B2+C2** (orbit-flip radius rho_G; text vs VLM, kept as two instantiations
of one idea but scored once as a family).

| # | Pilot (merged) | Why it survived the audit | Nov | Feas | Imp |
|---|---|---|---|---|---|
| **1** | **T-DISS** = A1+B1 — gauge-free threat-matched `M/L_q` predicts per-prompt jailbreakability where the raw logit gap (once you rescale logits) and paraphrase-consistency do not | Both audits: strongest text design. The *ratio* + gauge-invariance + consistency dissociation is the vision paper's unique object and is un-run on LLMs. Fast Proxies/LAP/Logit-Gap each touch one piece, none crosses consistency×robustness under a margin-to-Lipschitz law. Cleanest kill criterion; both branches publishable. | 4.5 | 4.5 | 5 |
| **2** | **C1** — shift-consistency does NOT order a frozen VLM tower's strong-attack robustness; a tower-computed threat-matched `\eta/L` does, attack-free, as a cross-tower selection rule | Both C audits: "strongest and most feasible; make it the flagship." Encoder-level (open_clip, no 7B decoder) => 1-2 orders cheaper and decoder-independent. Maps 1:1 onto the paper's Table-1 laws. FARE confirmed to never compute SC or `\eta/L`. | 4 | 5 | 4.5 |
| **3** | **B2+C2** — orbit-flip radius rho_G: excessive invariance as a measurable adversarial axis; the sensitivity axis (`\eta/L`) and invariance axis (rho_G) are decoupled (Tramer trade-off, budget law eps<rho_G) | Cheapest text pilot (B2, ~12-25 GPU-h, no LoRA/GCG needed). rho_G *radius* + budget law `prop:rhoG` + generative LLMs are uncontested by LGIP (which has rates not radii, VLM not generative LLM). C2 is the most conceptually novel VLM pilot but carries the highest scoop risk (2604.01848) and a load-bearing programmatic-oracle engineering step. | 4 | 3.5 | 4 |
| **4** | **A2** — attack-free robustness curve: certified fraction `CF(eps)=P(R_q<eps)` equals empirical jailbreak `ASR(eps)`, dual-norm-matched, budget-normalized | Measurement-theory contribution genuinely open in LLM-land. BUT both audits flag high risk: the count law `prop:count` is exact only on affine cells; transformers (softmax/SiLU/GELU) are curved, so the equality may hold only in a thin regime. Survives *only* if repositioned onto the measured "curvature edge" eps_c. | 3.5 | 3 | 3.5 |
| **5** | **A3** — refusal margin is a gauge-dependent diagnostic, not a steerable robustness target: steering it up buys over-refusal (the constant classifier), not robustness | Survives but must reposition: "steering isn't a robustness lever" is now partly established by Steering-Off-a-Cliff (2602.06256) and Attacker-Moves-Second (2510.09023). A3 still uniquely owns the *gauge-degeneracy explanation* + the ratio-as-correct-readout + the push to the over-refuser endpoint. Lower novelty ceiling. | 3 | 4 | 3.5 |
| **6** | **B3** — `\eta/L` explains survival of consistency-trained (ACT/BCT) LLM safety under a white-box threat-matched attack + dose sweep | Heavily eroded: **2605.28467 already ran a (black-box RL) adaptive attack and found ACT largely survives** — so the original "invariance-helps is a weak-attack artifact" claim is refuted for jailbreak. Salvageable only by the hard re-aim to "eta/L explains survival" + the white-box gradient attack the authors flag as untested. Highest cost (45-130 GPU-h), highest risk. | 2.5 | 2.5 | 3.5 |
| **7** | **C3** — anti-aliasing a VLM ViT stem helps under FGSM, vanishes under a strong EoT-adaptive attack | Both C audits: "needs-fix bordering on KILL — the gap is mostly CLOSED." Athalye 2018 (mechanism), Grabinski/FLC/ASAP/Torralba (anti-aliasing under AutoAttack for CNNs), R-Adapt 2603.12799 (Gaussian low-pass on frozen CLIP under AutoAttack) preempt ~85%. Only the APS/polyphase ViT-*stem* + inference phase-averaging cell (~80% novel) is open, and the expected result is a *confirmation*, not a surprise. Tightest feasibility (EoT x K multiplies APGD). | 1.5 | 2.5 | 2.5 |
| — | **A3-family duplicate note** | A3 and B3 both invoke the over-refusal = constant-classifier degeneracy (`lem:ratiodegen`). Do not run both as separate papers; A3 is the cleaner, cheaper carrier of the degeneracy story. B3 only justifies itself via the *white-box-attack-on-the-consistency-objective + eta/L-explains-survival* angle. | — | — | — |

**Preempted / do-not-run family (the audits' "invariance-helps is a weak-attack artifact" cluster):**
A3(partial), **B3**, **C3** — all materially preempted (2602.06256, 2605.28467, R-Adapt/FARE
strong-attack-evaluated, Grabinski-under-AutoAttack, Athalye-2018). Treat with suspicion; none is a
first-choice run. B3 and C3 are salvageable only after their audited re-aims and only if compute is idle.

---

## 2. The TOP 3 — RUN-READY specs

### TOP 1 — T-DISS (merged A1 + B1): "Prompt consistency is not robustness; a gauge-free threat-matched margin-to-sensitivity ratio is"

**Standalone contribution sentence.** On a stock aligned LLM, the gauge-free threat-matched ratio
`R_q(x)=M(x)/\|\nabla_e M(x)\|_q` predicts per-prompt jailbreak vulnerability (AUROC >> 0.5, and above
the raw margin and the gradient norm alone); the raw refusal-affirmation logit gap predicts it only
until you rescale the logits (a temperature / logit-bias gauge move it cannot survive and the ratio
can); and paraphrase/format consistency — the "stability" metric the prompt-robustness field reports —
does not predict it at all.

**Model + data (what to download).**
- Model: `meta-llama/Meta-Llama-3-8B-Instruct` (cached). Report ONE model; `Qwen2.5-7B-Instruct`
  (cached) is an appendix generalization check, NOT a sweep.
- Benchmark: AdvBench harmful behaviors (520) + HarmBench standard behaviors (400) = 920 clean
  harmful prompts. **Download** (small CSV/JSON). Restrict per-prompt statistics to a >=1,000-prompt
  working set (the 920 harmful + optional benign for confound stratification).
- Paraphrases: k=8 content-preserving paraphrases/format variants per prompt, generated by the target
  model itself (or cached Mistral-7B) at T=0, filtered by bidirectional NLI
  (`deberta-v3-large-zeroshot-v2.0`, cached). This is data prep, not a model sweep.
- Consistency operator (published, not invented): **Flip-Flop Consistency (2510.14242)** protocol,
  scoped to a *per-prompt observational* metric `C(x)` = fraction of the k paraphrases whose greedy
  response is a refusal. (Do NOT train it; pre-empt Consistency-Training 2510.27062 and LAP 2503.01345
  by name — they *train* invariance on a fixed model; T-DISS *measures* it.)
- Judge: **Llama-Guard-3-8B** (~16 GB, **download**, fits one A6000) OR HarmBench-Llama-2-13b-cls.
  Report judge agreement on a hand-checked 100-sample slice (the judge error is the floor on AUROC).

**Threat-matched strong attack (PE-PGD).** Let `e(x) in R^{T x d}` be the prompt's own token
embeddings (the SAME tensor the diagnostic differentiates). Perturb `e' = e(x)+delta`, maximize
`L(e') = logit(affirm | e') - logit(refuse | e')` at the first generated position by signed PGD with
per-step projection onto `\|delta\|_p <= eps` (`p in {2, inf}`). 200 steps, step `eps/25`, **R=5 random
restarts** inside the ball, keep worst-case. Success = greedily-generated continuation judged harmful.
Set the per-prompt binary label at the budget `eps*` where clean-complied ASR ~= 0.5 (pre-register the
*rule*, not the number). L2-ball PE-PGD is ground truth for `R_2 = M/\|\nabla M\|_2`; Linf-ball PE-PGD
for `R_inf = M/\|\nabla M\|_1`.

**Predictor / target / null (no circularity).**
- Margin `M(x) = logit(refuse-token) - logit(affirm-token)` at position 1. Fix the token anchors in
  writing before the run from the model's own greedy refusal/compliance strings ("I" vs "Sure"); report
  robustness of M to the anchor choice on a 50-prompt slice.
- Sensitivity `L_q(x) = \|\partial M/\partial e(x)\|_q`, exact analytic gradient, dual norm `q` of the
  attack (`q=2` for L2, `q=1` for Linf). Sharper than Gradient Cuff's zeroth-order pooled-embedding
  gradient — state this.
- Ratio / radius `R_q(x) = M(x)/L_q(x)`.
- Consistency null `C(x)` (above). Baselines it must beat: raw M alone, L_q alone, clean response
  entropy, clean refusal indicator.
- Not-circular framing: the label is the SUCCESS of the 200-step optimized PE-PGD; the predictor is a
  1-backward first-order Taylor radius of the SAME objective on the SAME `e(x)`. They share a threat
  model by design but are computed by different mechanisms — we test how well the first-order radius
  predicts the fully-optimized radius. Report the second partial correlation controlling the measured
  radius itself to stays > 0 (kills the near-tautology objection).

**Per-prompt statistical plan (load-bearing).**
- PRIMARY: per-prompt Spearman(`R_2`, measured min-successful-eps) over >=920 prompts, bootstrap 95% CI
  (judge-noise-robust — survives even if AUROC is capped by the judge).
- PRIMARY: AUROC of `R_q` vs the binary PE-PGD label, with **DeLong test** AUROC(`R_q`) > AUROC(`M`)
  and > AUROC(`C`); bootstrap CIs over prompts.
- PRIMARY (gauge, the headline): apply (a) logit-scale `f->cf`, `c in {0.25,0.5,1,2,4}` and (b) a
  self-defined refusal-token logit bias `b in {0,+/-2,+/-5}`. Show raw-M AUROC / calibrated threshold
  **moves** with c and b; `R_q` ranking is **invariant**. (Do NOT attribute the bias knob to Refusal-
  Tokens 2412.06748 — that needs training; cite it only as "refusal rate is movable.")
- COARSE: threat-matching — `R_2` beats `R_inf` at the L2 attack and vice versa.

**Confound controls.** Partial-out / stratify on: clean refusal base rate (restrict AUROC to
clean-complied prompts); prompt length T (both M and grad scale with T — report length-partialled
AUROC); clean response entropy; benchmark provenance (AdvBench vs HarmBench within-stratum).

**Gradient-masking audit (report all).** (i) ASR must not rise 200->400 steps or R 5->10; (ii) log
fraction of prompts with `\|\nabla M\| ~= 0` (vanishing-gradient masking); (iii) unbounded append-
Schwinn at eps=inf reaches ~100% ASR (ceiling — if PE-PGD plateaus well below, it was masked);
(iv) **discrete GCG cross-check** (`nanogcg`, 500 steps, fixed 128-prompt slice) — role is to confirm
the per-prompt ORDERING survives a different threat model, not to match numerically.

**Pre-registered KILL + honest-negative.** Kill the ratio's added value iff BOTH: raw M matches `R_q`
AUROC within CI AND is empirically gauge-stable across the c,b grid. Kill the dissociation iff C
predicts PE-PGD success as well as `R_q`. **Publishable negative either way:** "the raw refusal gap
already predicts per-prompt jailbreakability and is gauge-stable in practice, so normalization is
unnecessary for stock aligned models" — a clean citable negative for margin-based diagnostics.

**Realistic GPU-hours (2xA6000).** Clean diagnostics 920 prompts (fwd+bwd, both norms) ~0.5 h;
paraphrase gen (8x920) ~1-2 h; PE-PGD 200 steps x 5 restarts x 920 prompts x ~5 budgets ~10-16 h on one
card; GCG 128x500 ~6-10 h on the second card; judge + gauge sweep ~2-3 h. **~1.5-2 GPU-days across both
cards.**

**Env / infra setup.**
```
source ~/.conda/envs/al_selfdistill/bin/activate
pip install nanogcg          # discrete GCG cross-check (Nasr adaptive-eval standard)
# judge (pick one):
huggingface-cli download meta-llama/Llama-Guard-3-8B          # ~16 GB, fits one A6000
# benchmarks (small text):
#   AdvBench harmful_behaviors.csv (llm-attacks repo), HarmBench standard behaviors,
#   XSTest (optional, for benign confound stratum)
# datasets already cached: cais/mmlu, sst2, rotten_tomatoes, deberta-v3-large-zeroshot-v2.0
```

---

### TOP 2 — C1: "Shift-consistency does not order VLM tower robustness; a threat-matched tower `\eta/L` does"

**Standalone contribution sentence.** A margin-to-Lipschitz statistic computed through a frozen VLM
vision tower on clean images ranks encoders by their strong-attack (AutoAttack) robustness *without
running any attack*, while shift-consistency — the invariance metric the anti-aliasing literature
tracks — does not order it and under adversarial training anti-predicts it; picking a tower by `\eta/L`
has near-zero regret vs the oracle, picking by shift-consistency mis-selects by many robust-accuracy
points.

**Model + data (what to download).**
- Panel of **7 frozen towers, all no-train drop-ins, spanning the invariance x robustness plane:**
  `openai` CLIP ViT-L/14 (non-robust), FARE2, FARE4, TeCoA2, TeCoA4 (the 4 RobustVLM AT towers), plus
  **two non-AT invariance-axis wideners** to escape the collinearity kill: (6) DINOv2/DINOv3 ViT-L
  (cached) zero-shot via a linear-probe head, and (7) an anti-aliased / APS ViT-L stem variant of base
  CLIP (blur-pool the patch-embed conv). The 4 AT towers alone cluster in SC and `\eta/L`; the two
  non-AT wideners open the axis exactly as the paper's two low-invariance ResNet arms did.
- Benchmark: **ImageNet-1k zero-shot, full 50k val** (open_clip text-prompt classifier). High-n, single
  clean arm, no decoder. This alone is the standalone paper.
- Downloads (all open, ~1-2 GB each, trivial): RobustVLM towers `hf-hub:chs20/{fare2,fare4,tecoa2,
  tecoa4}-clip`; base CLIP `openai` weights via open_clip; ImageNet-1k val. LLaVA-1.5-7B only for the
  optional decoder confirmatory arm.

**Threat-matched strong attack.** AutoAttack-style **APGD-CE + targeted APGD-DLR ensemble, 100 iters**,
Linf `eps in {2/255, 4/255}` (FARE's own RobustBench-grade protocol), on the correctly-classified
subset, 10k images/tower (50k if wall-clock allows). S = robust zero-shot accuracy. **Encoder-level
only — no 7B decoder in the attack graph** (the tower governs, per 2407.11121).

**Predictor / target / null.**
- SC = mean fraction of zero-shot predictions unchanged over the SxS patch-grid phase sweep (integer +
  circular shifts, 0..stride-1) + pooled-embedding cosine-consistency; report both.
- Threat-matched `\eta/L` (attack-free, clean): `\eta` = mean active margin (correct-class vs
  runner-up logit gap of the zero-shot head); `L = \|\nabla_x M\|_1` (the **L1** dual norm of the Linf
  attack — the matched ratio; `\|\nabla_x M\|_2` is the mismatched control). On 2k clean val images.
- Clean zero-shot acc (confound control).
- Target S = robust zero-shot acc under the APGD ensemble. Null = SC (predict it does NOT order S).

**Per-image statistical plan.** Pearson & Spearman of {SC, `\eta/\|\nabla M\|_1`, `\eta/\|\nabla M\|_2`,
clean-acc} vs S over the 7 towers; **partial correlation of `\eta/\|\nabla M\|_1` vs S controlling for
clean acc** (load-bearing, per the paper's caveat); the **selection-rule regret table** (`\eta/L`-pick
vs SC-pick vs clean-pick vs oracle, regret in robust-acc points); bootstrap 95% CIs resampling
towers/images + a permutation test.

**Confound controls.** (1) Fix a single common eval resolution (224) for all 7 towers — resolution
changes both SC (phase grid size) and gradient-norm scale; otherwise the `\eta/L` ranking is a
resolution confound (the one genuinely new hole round-2 flagged). (2) Report SC on the *same*
correctly-classified subset used for `\eta/L` and S. (3) Partial-out clean accuracy.

**Gradient-masking audit (mandatory).** APGD <= **PGD-40** per tower; **Square-Attack** black-box
spot-check (>=1k images); report both gaps. A low S that passes the audit is real robustness, not
masking — mirrors the paper's "AutoAttack <= matched PGD, no masking" gate.

**Pre-registered KILL + honest-negative.** Kill iff SC predicts S as strongly as `\eta/L` (Pearson CIs
overlap) OR the `\eta/L`-S partial correlation controlling clean acc drops below 0.5. Honest-negative:
"through a VLM tower, shift-consistency is as good a robustness selector as the margin-to-Lipschitz
ratio" would still be a clean, citable calibration for how the field picks robust encoders.

**Realistic GPU-hours (2xA6000).** Per tower: SC+`\eta/L` on 2k images ~0.3 h; ImageNet-50k clean
zero-shot ~0.5 h; APGD ensemble (100-iter, 2 losses, 2 eps) on 10k + PGD-40 + Square audit ~4-6 h.
**~5-7 GPU-h/tower x 7 = ~40-50 GPU-h, ~1-1.5 days.** Optional LLaVA-1.5-7B decoder-level APGD on ~1k
VQAv2 items, 5 towers (~15-20 GPU-h) as a confirmatory arm only. Feasibility: **green.**

**Env / infra setup.**
```
source ~/.conda/envs/al_selfdistill/bin/activate
pip install open_clip_torch autoattack robustbench
huggingface-cli download chs20/fare2-clip chs20/fare4-clip chs20/tecoa2-clip chs20/tecoa4-clip
# base CLIP ViT-L/14 via open_clip 'openai'; ImageNet-1k val (torchvision or HF)
# DINOv3 ViT-L/16 + DINOv2 ViT-L/14 already cached (panel wideners)
# LLaVA-1.5-7B (llava-hf/llava-1.5-7b-hf) only if running the optional decoder arm
```

---

### TOP 3 — B2 (+ C2 as the VLM sibling): "The orbit-flip radius rho_G — excessive invariance as a measurable adversarial axis, decoupled from `\eta/L`"

Run **B2 (text) as the primary top-3**: it is the cheapest, lowest-eng-risk, highest-novelty-per-GPU-
hour pilot of the whole set, its novelty is uncontested by LGIP, and it needs no LoRA/GCG/judge-
download to stand. **C2 (VLM) is the sibling** — most conceptually novel VLM pilot but higher scoop
risk (2604.01848) and a load-bearing programmatic-oracle engineering step; queue it as the follow-up
or the parallel VLM run only if C1 is deferred (see run order).

**Standalone contribution sentence (B2).** Generative instruction-tuned LLMs have a measurable
orbit-flip radius rho_G — the minimal meaning-changing edit (negation, antonym, harmful->benign) they
stay invariant to — and raising a model's paraphrase/refusal invariance provably shrinks rho_G, so the
Tramer sensitivity/invariance trade-off governs LLMs with a budget law eps < rho_G that holds on >=95%
of items (the empirical `prop:rhoG` certificate), while the sensitivity axis `\eta/L` and the
invariance axis rho_G are decoupled.

**Model + data (what to download).**
- Model: `Meta-Llama-3-8B-Instruct` (cached), primary. `Qwen2.5-7B-Instruct` appendix cross-point only.
- Deterministic-oracle flip corpus (the label change must be definitional): negation insertion
  (rule-based on `sst2`/`rotten_tomatoes`, both cached; + MoNLI-style hypothesis negation — **download
  MoNLI** or construct); antonym swap (WordNet, `nltk.download('wordnet')`, tiny); harmful<->benign
  minimal rewrite (from `PKU-SafeRLHF`, cached); quantifier/entity swaps where truth-conditionally
  decisive. Use a >=1,000-item set.
- Paraphrase-validity filter (invariance side ONLY): `deberta-v3-large-zeroshot-v2.0` (cached),
  bidirectional entailment. **Never use the NLI model as the flip oracle** — an NLI model is itself
  excessively invariant, so that would be circular (the round-1 fix).
- Safety-refusal axis judge: HarmBench-cls (download) OR a string+DeBERTa ensemble to avoid the 26 GB
  download.

**Threat-matched strong attack (the rho_G search).** For each item, over the deterministic
meaning-CHANGING edit set, find the **minimal-distance edit that flips the oracle label yet leaves the
model's prediction/refusal unchanged.** Report distance in BOTH token edit distance AND embedding
displacement `\|Delta emb\|_2` (same geometry as the `\eta/L` embedding attack, so rho_G and `\eta/L`
land on one plot). rho_G(x) = min such distance; invariance-attack ASR = fraction with any invariant
meaning-flip within a budget. The sensitivity side reuses the T-DISS PE-PGD radius / `\eta/L` on the
same items (shared infra).

**Predictor / target / null / rho_G.**
- Sensitivity: `\eta/L` and the per-prompt PE-PGD radius (from T-DISS module) — the sensitivity axis.
- Invariance: rho_G(x) (above) — the invariance axis.
- Invariance dose (the PRIMARY axis, within-model to avoid a between-checkpoint confound): decoding-
  level paraphrase-marginalization strength (0 = greedy on canonical; higher = average the answer
  distribution over more of the paraphrase orbit) as a continuous knob -> a clean within-model
  rho_G(dose) curve. Cross-checkpoint points (base vs a consistency-LoRA point) are SECONDARY.

**Per-item statistical plan.**
- H1 (trade-off): Spearman(rho_G, dose) <= -0.6, PRIMARY curve = within-model rho_G(dose) over >=1,000
  items, bootstrap CI.
- H2 (budget law = the certificate, `prop:rhoG`): fraction of items where the oracle-robust radius <=
  rho_G is >= 95%. This is what LGIP cannot claim — keep it front-and-center.
- H3 (safety degeneracy, `lem:ratiodegen`): as benign-context refusal-invariance (over-refusal) rises,
  rho_G on the benign->benign axis falls.
- Two-axis figure: rho_G vs `\eta/L` on the same items (the paper's "needs room under both" plane).

**Confound controls.** Paraphrase validity (bidirectional-NLI filter, drop non-equivalent
"paraphrases"); between-model confound (within-model dose axis primary); oracle circularity
(deterministic flips only, NLI never the oracle); geometry (report both token-edit and embedding
distance).

**Gradient-masking audit.** For the sensitivity-side `\eta/L`/PE-PGD reuse the T-DISS battery. For the
rho_G search (gradient-free, edit-space), the analog audit is: verify the minimal-flip edit is verified
by the *deterministic* oracle (not a judge), and report the fraction of items where NO invariant
meaning-flip exists within the max budget (so a low ASR is a real invariance property, not a weak
search).

**Pre-registered KILL + honest-negative.** Kill iff rho_G is flat or RISES with measured invariance
(trade-off absent) OR the oracle-robust radius routinely exceeds rho_G (`prop:rhoG` fails empirically).
Publishable as a bound on when the Tramer trade-off transfers to LLMs.

**Realistic GPU-hours (2xA6000).** Mostly forward-pass generation + NLI filtering + a small
embedding-displacement search over ~1-2k items x a handful of edit candidates. **~12-25 GPU-h.**
Optional consistency-LoRA cross-point +3-5 h. Cheapest of the whole set.

**Env / infra setup.**
```
source ~/.conda/envs/al_selfdistill/bin/activate
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
# download MoNLI (or construct negation pairs); optional HarmBench-cls for the safety-refusal axis
# reuse the T-DISS PE-PGD + M/gradM module for the sensitivity axis (shared code)
```

**(C2 sibling, if run instead of / alongside as the VLM arm):** Qwen2.5-VL-7B-Instruct (cached) primary;
headline oracle restricted to **CLEVR + TallyQA only** (true programmatic boxes; drop VSR from the
headline); rho_G = min pixel-L2 transform that changes the programmatically-computed oracle answer while
the VLM answer stays fixed; strong attack = worst-case-over-orbit accuracy (gradient-free); judge VLM as
a *legibility gate only*, never a relabeler; paired FARE4-vs-CLIP LLaVA test of hypothesis-2 (predict
FARE is *worse* on rho_G). Must differentiate from 2604.01848 on page 1. ~45-55 GPU-h, feasibility green,
white-box manifold search kept OPTIONAL.

---

## 3. Run order

**First, in parallel (one text + one VLM => different models, data, and GPUs; no contention):**
- **GPU-A: T-DISS (TOP 1)** — text, Llama-3-8B, needs Llama-Guard + AdvBench/HarmBench + nanogcg.
  Strongest single standalone run; build the PE-PGD + `M`/`\nabla M` + judge module here (T-DISS reuses
  it, B2 reuses it for its sensitivity axis).
- **GPU-B: C1 (TOP 2)** — VLM, open_clip encoder-level, needs open_clip + autoattack + RobustVLM
  towers + ImageNet. Cheapest high-confidence VLM result; fully decoder-independent so it never
  competes with T-DISS for the 7B-decoder memory.

These two touch disjoint models, benchmarks, and libraries, so they run truly concurrently on the two
A6000s with no shared bottleneck. Combined wall-clock ~1.5-2 days.

**Third: B2 (TOP 3)** — text orbit-flip, Llama-3-8B. Runs after T-DISS because it *reuses* T-DISS's
PE-PGD / `\eta/L` module for its sensitivity axis, and it is cheap (~12-25 GPU-h) so it slots onto
whichever card frees first. If a *second VLM* result is wanted instead of a second text result, swap in
**C2** as the third run (it uses the cached Qwen2.5-VL-7B, disjoint from C1's encoder-level pipeline).

**Do not run first (preempted family):** A3 (reposition-only survivor, cheaper than B3, run only if the
degeneracy story is wanted as a standalone), B3 (highest cost/risk, salvage only via the white-box +
eta/L-explains-survival re-aim), C3 (near-kill; only the APS-stem cell is open and the result is a
confirmation). A2 is a defensible fourth if the measurement-theory angle is prioritized, but only with
the "curvature-edge eps_c" repositioning that makes a large ASR-CF gap a finding rather than a null.

---

## Total infra to download / install before kickoff

**Env (once):** activate `~/.conda/envs/al_selfdistill` (healthy: torch 2.9, transformers 4.57, peft
0.17, CUDA OK — do NOT rebuild). Then:
- `pip install nanogcg open_clip_torch autoattack robustbench`
- `python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"` (B2)

**Downloads:**
- Judge (text): `meta-llama/Llama-Guard-3-8B` (~16 GB) — or HarmBench-Llama-2-13b-cls (~26 GB).
- Benchmarks (text, small): AdvBench `harmful_behaviors.csv`, HarmBench standard behaviors, XSTest
  (optional benign stratum), MoNLI (B2 negation pairs, or construct).
- VLM towers (C1, ~1-2 GB each): `chs20/fare2-clip`, `fare4-clip`, `tecoa2-clip`, `tecoa4-clip`; base
  CLIP ViT-L/14 (`openai` via open_clip); ImageNet-1k val split.
- (C2 only, if run) LLaVA-1.5-7B (`llava-hf/llava-1.5-7b-hf`, ~14 GB) for the FARE-vs-CLIP pair; CLEVR
  + TallyQA (with boxes).

**Already cached (no download):** Llama-3-8B, Qwen2.5-7B, Qwen3-8B, gpt-oss-20b, Qwen2.5-VL-7B,
deberta-v3-large-zeroshot-v2.0, cais/mmlu, sst2, rotten_tomatoes, PKU-SafeRLHF, DINOv3 ViT-L/16,
DINOv2 ViT-L/14.
