# Novelty check: "new vs prior work" for the pitch deck

Verification of the deck's six claimed contributions against the primary literature (read from
the local source text, quoted where possible) plus targeted web search for 2023-2025 preemption.
Purpose: a rigorous, honest "new vs used/refined" accounting for a talk deck. Do NOT treat the
deck's one-liners as ground truth; corrections to them are flagged below.

Legend: **NEW** = no prior work does this; **PARTIAL** = the ingredient exists but our specific
use/combination is new; **PREEMPTED** = a prior paper already does essentially this.

Sources read in full text/PDF: Ge et al. 2021, Kamath et al. 2021, Saha & Gokhale (TIPS) 2024,
Wang et al. 2025, Hein & Andriushchenko 2017, Tsuzuku et al. 2018, Simon-Gabriel et al. 2019,
Moosavi-Dezfooli et al. 2019, Ngnawe et al. 2024. Web search for the two highest-risk claims
(weak-attack artifact under AutoAttack; gradient-anisotropy ranking) returned no preempting paper.

---

## Claim 1 — The empirical DISSOCIATION
"Shift-consistency does not order adversarial robustness, while a threat-matched margin-to-Lipschitz
ratio eta/L does, across model families."

**Verdict: NEW (as a positive, threat-matched dissociation across families).**

Closest prior work and exactly what it does / does not do:

- **Ge et al. 2021** ("Shift Invariance Can Reduce Adversarial Robustness", NeurIPS 2021) shows,
  across MNIST/Fashion/SVHN/CIFAR/ImageNet, that *more* shift-invariant models (higher Zhang
  consistency) tend to be *less* robust. Their metric of invariance is exactly Zhang's consistency
  (they compute it, e.g. Tables 1-2, "the consistency calculates the percentage of the time that the
  model preserves its predicted labels when a random shift is applied"). So Ge already reports that
  consistency **anti-correlates** with robustness under PGD (l2/l-inf, 10 iters). What Ge does NOT do:
  (a) they never claim consistency *fails to order* robustness — they use it precisely as an ordering
  signal (more invariant => less robust); (b) they never propose eta/L (margin-to-Lipschitz ratio) as
  the quantity that orders robustness — their mechanism is the DC-collapse of the *linear margin*, and
  their explanatory variable is *input/intrinsic dimension and the data margin*, not a per-model
  gradient-normalized certificate; (c) they never use a strong parameter-free attack.

- **Saha & Gokhale (TIPS) 2024** report the opposite sign: "better shift invariance is generally
  correlated with better adversarial robustness" (Sec 6.4, verbatim), PGD+FGSM from Foolbox, one
  ResNet-34, standard training. So the literature *sign is contradictory* across Ge and TIPS.

- Web search (margin-to-Lipschitz as a cross-architecture diagnostic, 2024-2025): the margin/Lipschitz
  ratio appears only as a **training regularizer / certification target** (GloRo, Lipschitz-Margin
  Training, Dynamic Margin Maximization). No paper uses it as an attack-free *diagnostic that
  dissociates from shift-consistency across model families*.

What is genuinely new here: the *positive* statement that (i) consistency carries no ordering
information once the attack is strong (and *anti*-predicts under AT), while (ii) the **threat-matched,
gauge-free** eta/L does order robustness, demonstrated jointly across CIFAR classifiers, PreActResNet,
ImageNet-100, RobustBench, and CLIP. The dissociation *between* the two signals, and eta/L as the
replacement, is not in Ge, Kamath, TIPS, or Wang.

**Deck wording is accurate.** The Q1 slide's own novelty note ("the relationship itself was studied by
Ge and TIPS; the eta/L certificate is from Hein/Tsuzuku") is honest and correct.

---

## Claim 2 — The "invariance helps" effect is a WEAK-ATTACK ARTIFACT
"It appears under FGSM/PGD but vanishes under a parameter-free strong attack (AutoAttack)."

**Verdict: NEW (this specific control is not in the prior line).**

- The "helps" papers we test — **TIPS (Saha 2024)**, **Wang et al. 2025**, and by construction
  **Zhang 2019 / Grabinski 2023** — use ONLY FGSM and PGD (and corruption metrics). Verified verbatim:
  - TIPS: "We investigate l2 and l-inf robustness of TIPS ... using PGD and FGSM attacks from Foolbox"
    (Sec 6.4). No AutoAttack.
  - Wang 2025: entire evaluation is "FGSM and PGD attacks" (contributions + Sec 6); their own
    Limitations section (App. B) concedes "empirical evaluations are limited to small-scale datasets
    and common l_p-norm attacks." No AutoAttack.
- The general methodological point that FGSM/PGD can overstate robustness via gradient masking, and
  that AutoAttack (Croce & Hein 2020) is the parameter-free arbiter, is well established (Athalye 2018;
  Croce & Hein 2020). We are USING that tool, not inventing it.
- Web search (2023-2025) found **no** paper that specifically re-evaluates the shift-invariance /
  equivariance-helps-robustness line under AutoAttack and shows the effect disappears. This is the new
  contribution: applying the known strong-attack control to *this particular* literature and showing the
  "helps" correlation is an artifact (and, on frozen CLIP, that FGSM's 16-61% robust accuracy is erased
  to zero by AutoAttack — the classic gradient-masking signature).

**Deck wording is accurate.** The Q2 slide's novelty note ("none of the 'helps' papers applied a
parameter-free strong attack; this is the new control") is correct and the strongest honest framing.
Minor caution for the talk: Wang 2025 is *equivariance* (rotation/scale), not pixel-shift consistency;
keep the "helps" bucket labeled as the broader invariance/equivariance line, which the deck already does.

---

## Claim 3 — The TWO-SIDED BRACKET  eta/L <= r <= eta/alpha
"We add the upper arm to the known lower-bound certificate; kappa = L/alpha."

**Verdict: NEW (upper arm + explicit condition number), lower arm is standard.**

Verified against the two cited anchors:

- **Hein & Andriushchenko 2017** (Thm 2.1): gives only a **lower** bound on the safe radius,
  r >= margin / (local cross-Lipschitz constant in the dual q-norm). They state the bound is **tight
  (equality) for linear classifiers**: verbatim "our bound is tight, that is the bound is attained,
  for linear classifiers ... ||delta||_p = min_{j!=c} <w_c - w_j, x> / ||w_c - w_j||_q". So kappa = 1
  for the linear case is directly supported. They provide **no** upper bound on the true radius (their
  "upper bounds" are empirically-constructed adversarial examples used only to gauge tightness).
- **Tsuzuku et al. 2018** (Prop 1): r >= M / (sqrt(2) * L), a **lower** bound only. Their Eq. 5 chains
  margin/L <= margin/L_global <= margin/L_local <= (empirical smallest adversarial perturbation) — the
  margin/Lipschitz quantity always sits on the *lower* side; there is **no** analytic upper bound of the
  form r <= eta/alpha anywhere in the paper. Note Tsuzuku's canonical bound carries a **sqrt(2)** factor;
  if the deck/paper writes r >= M/||grad M|| without it, that is the informal/Prop-2 form (a
  presentational detail, not a novelty problem).

So the *upper* arm r <= eta/alpha (alpha = co-Lipschitz / slowest rate the margin falls) and the
explicit kappa = L/alpha are not in Hein or Tsuzuku. The deck correctly says "this completes the
certificate chain of Tsuzuku, which bounds r only from below."

**Deck wording is accurate.** Caveat to keep in the paper (not necessarily the slide): a two-sided
Lipschitz-margin bracket is conceptually "the classifier is also *not* certifiable beyond margin over a
lower-Lipschitz/co-Lipschitz slope" — sandwich/co-Lipschitz arguments exist in the certified-robustness
literature in adjacent forms, so scope the claim as "for this margin certificate, with this kappa,
verified exact for linear invariant features and kappa in [1.6,2.4] for the power-spectrum surrogate,"
which the deck already does. Do not claim two-sided Lipschitz bounds are unprecedented in general.

---

## Claim 4 — The ANISOTROPY law
"A = ||grad M||_1 / ||grad M||_2 ranks already-robust models (lower A = more robust), via an
effective-dimension margin-deficit mechanism."

**Verdict: NEW (this is the deck's genuinely novel finding). Relaxes Simon-Gabriel; differs from
Moosavi; NOT preempted by Wang's "anisotropy" wording.**

- **Simon-Gabriel et al. 2019**: their sqrt(d) vulnerability law *assumes* equal per-coordinate gradient
  magnitude (isotropy): "coordinates of grad L have typical magnitude |grad L|", and "the magnitude of
  grad L(x) is 1/sqrt(d) for all x". Under that assumption ||grad||_1/||grad||_2 is **pinned to sqrt(d)**.
  Their variable is the input **dimension d**, and across models they report a near-constant (linear)
  L1-L2 relation — i.e. the ratio does NOT vary to rank models. Letting A vary *at fixed d* and using it
  as a cross-model ranking statistic genuinely **relaxes** their isotropy premise. Confirmed: they never
  use A = L1/L2 to order models. (Cite it as "per-coordinate magnitude assumed uniform, Sec 3.1 +
  App A.2", not as a single labeled 'equal-variance assumption'.)
- **Moosavi-Dezfooli et al. 2019 (CURE)**: robustness is related to **loss-surface curvature** (input
  Hessian eigenvalues), reduced by adversarial training, used as a **training regularizer** — never a
  gradient-norm shape/anisotropy ratio, and they do NOT rank a population of already-robust models. They
  even warn small gradient norm gives "a false sense of robustness." So our "transverse, not on-direction
  curvature" positioning is correct.
- **Wang et al. 2025** — IMPORTANT NEAR-MISS TERMINOLOGY: Wang uses the word *"anisotropy"* ("This
  anisotropy in gradient variability contributes to improved adversarial robustness", Sec 4.4, Thm 2).
  But Wang's "anisotropy" is a **directional** statement — equivariance suppresses gradient *variability*
  along the group orbit while leaving off-orbit directions sensitive — NOT a scalar ||grad||_1/||grad||_2
  ratio, and NOT used to rank a set of robust models. So Wang does not preempt the law, but the shared
  word is a collision to pre-empt in Q&A: be ready to say "Wang's 'anisotropy' is orbit-vs-off-orbit
  gradient variability from equivariance; ours is the scalar L1/L2 gradient-norm shape used as a
  cross-model robustness ranking."
- Web search hits and their status:
  - "Characterizing Model Robustness via Natural Input Gradients" (arXiv:2409.20139): gradient
    *edge-concentration* as a **training method**, not L1/L2 anisotropy ranking of robust models. Not a
    preemption; adjacent, worth citing as related "gradient-shape-and-robustness" work.
  - "Intriguing Properties of Robust Classification" (arXiv:2412.04245): about **data requirements** for
    robust generalization; no shift-invariance, no margin/Lipschitz ratio, no anisotropy. Not relevant.
  - General finding (e.g. arXiv:2409.20139 discussion): robust models have ~2 orders-of-magnitude smaller
    E[||grad||_1] — this is about gradient *magnitude*, i.e. our eta/L "detect" axis, not the *shape*
    ranking axis. Consistent with, does not preempt, our A.

**Deck wording is accurate** ("the anisotropy-ranks-robust-models law and its mechanism are new; it
relaxes the equal-variance assumption of Simon-Gabriel"). The effective-dimension margin-deficit is
correctly presented as a *proposed mechanism*, not a theorem (Q&A 20 is honest about this).

---

## Claim 5 — The threat-matched, gauge-free framing of eta/L
"We match the gradient dual norm to the attack norm; the ratio is scale-invariant."

**Verdict: PARTIAL (refinement / clarification, not a new object).**

- The **dual-norm matching** is inherent to the certificate itself: Hein 2017 Thm 2.1 already measures the
  gradient in the dual q-norm (1/p+1/q=1), and Simon-Gabriel 2019 already pairs l-inf attacks with
  ||grad||_1 and l2 with ||grad||_2 (Lemma 2). So "threat-matching" is not invented here; what is new is
  making it an explicit, load-bearing methodological rule and showing empirically that the *mismatched*
  norm gives the wrong sign (MNIST). That empirical "mismatch flips the sign" demonstration is a
  contribution; the principle is not.
- **Gauge-freeness** (logit rescaling f -> cf leaves M/||grad M|| unchanged) is a correct and useful
  *clarification* — it makes margin-vs-Lipschitz attributions well-posed — but it is a property of the
  ratio, not a new theorem. The deck's Q&A 5 already frames it exactly this way ("It is a clarification").

**Deck wording is accurate and appropriately modest.** The "Derived (not assumed)" slide explicitly says
"eta/L is not a new robustness measure; it is a first-order certificate we make threat-matched and
gauge-free." Keep that honesty; do not upgrade "gauge-free" to a headline contribution.

---

## Claim 6 — SATURATION of shift-consistency on modern encoders
"Consistency ranges ~0.96-0.99 and cannot rank models; extends to a second (text) modality."

**Verdict: NEW as an explicit 'the metric is saturated / has no ordering power on modern encoders'
statement; the underlying observation that modern nets are highly consistent is known.**

- That modern CNNs are *approximately* shift-consistent after training is known: Ge 2021 notes "realistic
  architectures with zero padding still preserve approximate invariance to shifts after training" and
  reports consistency >85 for most ImageNet models; Zhang 2019 built anti-aliasing precisely because
  consistency is high but imperfect. So high consistency on modern models is not new.
- What is new: the *quantified saturation as an argument that the metric loses discriminative/ordering
  power* on 16-17 frozen CLIP encoders (0.963-0.988; 0.977 +/- 0.009 image, 0.977 +/- 0.007 paraphrase),
  and the demonstration that within this saturated band eta/L still orders per-image robustness while
  consistency does not. Web search found no paper making the "consistency is saturated on foundation
  encoders and therefore cannot rank robustness" point. The extension to a text/paraphrase modality is
  new (and the deck is honest that the paraphrase set is too mild to host a real text-adversarial axis).

**Deck wording is accurate.** Keep the honest caveat (Q&A 26/27) that the tower-level CLIP n is small and
the load-bearing result is per-image.

---

## Cross-cutting accuracy check of the deck's one-line summaries of papers

All the following were verified against source text; flags are minor and about *precision*, not errors:

- **Ge 2021** — deck: "shift-invariant linear classifier uses only the average (DC) component; margin
  collapses 2 -> 2/sqrt d; PGD/DDN, MNIST/Fashion." ACCURATE. (DC-collapse Thm 1 + Corollary 1 give
  exactly 2 -> 2/sqrt d; Fig 1 uses DDN on the single-image toy case; MNIST/Fashion use PGD l2/l-inf.)
  One nuance: DDN is used for the *single-image toy* radius; the MNIST/Fashion/real-data results use PGD.
  The deck's "PGD/DDN" is fine but if asked, attribute DDN to the toy example, PGD to the real data.

- **Kamath 2021** — deck: "proven trade-off between spatial (rotation/translation) and adversarial
  robustness; their 'rate of invariance' is the consistency metric; rotation as a cyclic shift."
  ACCURATE with one wording caution: Kamath's metric is literally the **"rate of invariance"** (fraction
  of images whose label is unchanged under the transform); they do NOT call it "consistency," and their
  invariance is over **random rotations/translations** modeled as cyclic shifts (cyclic codes,
  Proposition 1), and the adversarial side is **l-inf PGD**. So "rate of invariance = the consistency
  metric" is *our equating* (fair, functionally identical), not Kamath's term. Say "their rate of
  invariance is the analogue of Zhang's consistency" to be exact. Their trade-off is average-case spatial
  vs worst-case l-inf, proven in a statistical setting.

- **Saha (TIPS) 2024** — deck: "'Better shift invariance is generally correlated with better adversarial
  robustness' (Sec 6.4); PGD/FGSM (Foolbox), one ResNet-34." ACCURATE, verbatim quote confirmed, backbone
  and attacks confirmed. Good.

- **Wang 2025** — deck: "Rotation/scale-equivariant CNNs improve robustness on CIFAR-10/100; FGSM and
  PGD." ACCURATE (CIFAR-10/100/-10C; FGSM+PGD; no adversarial training; CLEVER as the theory framing).
  Add for the talk: Wang's theory tool is CLEVER (a margin/local-Lipschitz ratio) — worth noting because
  it is the same family as our eta/L, so Wang is a natural point of contact / contrast, not just a "helps"
  citation.

- **Zhang 2019 / Grabinski 2023** — deck: "anti-aliased / alias-free downsampling improves robustness;
  FGSM/PGD/APGD." Reasonable; not independently re-verified line-by-line here (out of the 6-claim scope),
  but consistent with what these papers do. If the talk leans on Grabinski's "APGD," double-check whether
  that is full AutoAttack or APGD-only, since the deck's own thesis is that APGD-only != AutoAttack.

- **Ngnawe 2024** — FLAG (sign-flip slide). Deck: "margin-consistency in robust models was noted by
  Ngnawe et al., 2024." PARTIALLY accurate, risk of overclaim. Ngnawe's "margin consistency" is a positive
  rank correlation between the **logit margin and the input-space margin (distance to boundary)** in
  *robust* models (Kendall tau up to 0.86) — it is NOT a correlation between logit margin and
  input-gradient *sensitivity*, has NO sign, NO sign flip, and Ngnawe studies robust models *only* (never
  standard vs robust). Our sign-flip result (per-image logit-margin vs input-sensitivity correlation
  flipping from ~-0.5 to ~+0.5 across standard->adversarial training) is therefore NOT something Ngnawe
  observed. RECOMMENDED wording: cite Ngnawe only for "logit margin correlates with input-space margin in
  robust classifiers," and present the *signed sensitivity coupling and its inversion* as ours. As written
  the slide is defensible but a careful referee could read it as crediting Ngnawe with the sign flip.

- **Simon-Gabriel 2019** — deck (Q5/Q&A 22): "they fix equal per-coordinate gradient variance, so
  A ~ sqrt d; we let A vary at fixed d." ACCURATE in substance; precise attribution is "per-coordinate
  magnitude assumed uniform (~1/sqrt d for all coordinates), Sec 3.1 + App A.2" rather than a single
  explicitly-labeled 'equal-variance assumption.'

- **Moosavi 2019** — deck: "curvature ... on-direction curvature ... CURE." ACCURATE. Curvature = input
  Hessian eigenvalues, used as the CURE training regularizer, not a ranking of robust models. Our
  "transverse effective-dimension deficit, not on-direction curvature" contrast holds.

- **eta/L certificate attribution** — deck: "Hein & Andriushchenko 2017; Tsuzuku et al. 2018." ACCURATE.
  Both are lower-bound-only; linear-case exactness is Hein; the sqrt(2) factor is Tsuzuku's Prop 1.

---

## Preempting papers found via search (with URLs) — none fully preempt; adjacency noted

- Croce & Hein 2020, AutoAttack — https://arxiv.org/abs/2003.01690 — the arbiter tool we USE (not new).
- "Characterizing Model Robustness via Natural Input Gradients" — https://arxiv.org/abs/2409.20139 —
  gradient edge-concentration as a *training* method; robust models have much smaller E[||grad||_1].
  Adjacent to Claim 4/5 (gradient shape & magnitude vs robustness) but does NOT rank robust models by
  L1/L2 anisotropy. Cite as related; not a preemption.
- "Intriguing Properties of Robust Classification" — https://arxiv.org/abs/2412.04245 — data-requirement
  focus; irrelevant to all six claims. No overlap.
- "Detecting Brittle Decisions for Free" (Ngnawe 2024) — https://arxiv.org/abs/2406.18451 — margin
  consistency (logit vs input-space margin) in robust models. Relevant to the sign-flip slide; see FLAG.
- Dynamic Margin Maximization / GloRo / Lipschitz-Margin Training — margin/Lipschitz as a *training/
  certification* objective, not an attack-free cross-family *diagnostic*. Do not preempt Claim 1.

Search queries run (all July 2026): weak-attack-artifact-under-AutoAttack for shift/equivariance;
gradient L1/L2 anisotropy ranking robust models; consistency-fails-margin-predicts diagnostic; TIPS
re-evaluation strong attack; consistency saturation on encoders. No query surfaced a paper that
(b) shows the invariance-helps effect vanishes under AutoAttack, or (d) uses L1/L2 gradient anisotropy
to rank robust models. These two remain the cleanest novelty claims.

---

## Corrected, honest "new vs used/refined" accounting for the talk

NEW (defensible as our contribution):
1. The dissociation: consistency carries no robustness-ordering (anti-orders under AT) while
   threat-matched eta/L orders it, across families. [Claim 1]
2. The weak-attack debunk: the invariance/equivariance-helps effect is an FGSM/PGD artifact that
   vanishes under AutoAttack; on CLIP it is outright gradient masking. [Claim 2] — cleanest novelty.
3. The upper arm eta/L <= r <= eta/alpha and explicit kappa = L/alpha (lower arm is Hein/Tsuzuku).
   [Claim 3]
4. The anisotropy law A = ||grad M||_1/||grad M||_2 ranking already-robust models + effective-dimension
   deficit mechanism. [Claim 4] — the paper's most original quantity.
5. Saturation of consistency on foundation encoders as a *loss of ordering power*, extended to a second
   modality. [Claim 6]
6. The signed logit-margin vs input-sensitivity coupling and its standard->robust sign flip
   (distinct from Ngnawe's two-margin consistency). [sign-flip slide]

USED / REFINED (not ours):
- The Lipschitz-margin lower bound r >= M/||grad M||: Hein 2017 (exact for linear, dual-norm), Tsuzuku
  2018 (global-Lipschitz, sqrt2 factor).
- The DC-collapse mechanism and consistency<->robustness relationship: Ge 2021 (and Kamath 2021 for the
  rotation/spatial trade-off; TIPS 2024 and Wang 2025 for the positive-sign "helps" reports).
- AutoAttack as arbiter: Croce & Hein 2020.
- Threat-matched dual-norm pairing (l-inf<->L1 grad, l2<->L2 grad): implicit in Hein 2017 / Simon-Gabriel
  2019; we make it an explicit rule and show mismatch flips the sign.
- Curvature and gradient-dimension views: Moosavi 2019 (curvature/CURE), Simon-Gabriel 2019 (sqrt d).
- Margin-consistency in robust models (logit vs input-space margin): Ngnawe 2024.

TWO THINGS TO WATCH IN THE TALK (surprises):
- Wang 2025 literally uses the word "anisotropy" for a *different* (orbit-directional) concept — pre-empt
  the collision in Q&A.
- The Ngnawe citation on the sign-flip slide risks crediting them with the sign flip they did not report;
  reword to attribute only the logit-vs-input-margin correlation to Ngnawe.
