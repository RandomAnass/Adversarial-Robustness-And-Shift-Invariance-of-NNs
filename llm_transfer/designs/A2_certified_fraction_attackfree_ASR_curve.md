# Attack-free robustness curves for LLMs: a first-order embedding-space certificate whose certified fraction equals the empirical jailbreak success rate, threat-matched and budget-normalized

## Transferable element (from our paper)
- **Exact certificate count (b)**: in the locally-affine regime robust accuracy = certified fraction,
  i.e. the population survival rate at budget eps equals P(per-sample first-order radius >= eps). Text
  analog: attack-success-rate ASR(eps) at embedding budget eps equals the *non-certified* fraction
  CF(eps) = P_x( R_q(x) < eps ), where R_q(x) = M(x)/L_q(x) is the per-prompt first-order refusal radius
  (M = refusal-affirmation logit gap, L_q = embedding-gradient norm in the attack's dual norm).
- **Threat-matching (dual norm)**: L2-ball embedding attack is resisted by the L2 gradient norm, Linf by
  the L1 gradient norm; the certificate must use the matched norm.
- **Budget-normalization (e)**: the raw ratio anti-correlates with ASR across budgets, but eta/(L*eps)
  collapses the family onto one monotone curve; here R_q/eps (radius measured in units of the attack).

## Literature gap (specific papers checked + why open)
- **Certifying LLM Safety / erase-and-check (arXiv:2309.02705)** and **SmoothLLM (arXiv:2310.03684)**
  give certificates over *discrete* token edits / randomized character perturbations (L0/edit budgets),
  not a *continuous first-order* embedding-space certificate, and never show certified fraction = ASR.
- **Soft Prompt Threats / embedding attacks (arXiv:2402.09063)** define a continuous L2 threat model but
  only *attack*; they do not derive a per-prompt certificate or an attack-free ASR-vs-budget curve.
- **Fast Proxies (arXiv:2502.10487)** predicts robustness with cheap *attacks*, not an attack-free
  certificate; explicitly does not threat-match or budget-normalize.
- **Gradient Cuff (arXiv:2403.00867)** uses the gradient norm for per-input detection, never as a term in
  a per-prompt radius that is validated to equal ASR at a budget.
- No LLM work states or tests "ASR(eps) = certified fraction of prompts whose first-order embedding radius
  is below eps", nor the budget-normalized collapse, nor the dual-norm matching for embedding attacks. OPEN.

## Hypothesis (falsifiable)
On one model over a full harmful-prompt benchmark:
1. **Count law**: across a ladder of embedding budgets eps, the *measured* ASR(eps) of the strong
   embedding attack matches the *attack-free* certified-non-robust fraction CF(eps) = P(R_q(x) < eps)
   to within a small mean absolute gap (target < 0.05, analogous to the paper's 0.014 vision gap) in the
   small-eps (locally-affine) regime, and the two curves agree in shape and ordering throughout.
2. **Budget-normalization**: the raw mean ratio anti-correlates with ASR across budgets, while the
   budget-normalized per-prompt certified fraction (R_q/eps) collapses all budgets onto one monotone
   curve.
3. **Dual-norm matching**: CF built with the L2 gradient norm predicts the L2-ball attack's ASR; CF built
   with the L1 gradient norm predicts the Linf-ball attack's ASR; the mismatched pairing over/under-shoots.
Kill: if CF(eps) and ASR(eps) diverge even at the smallest budgets (gap > ~0.1) the locally-affine
premise fails for LLMs -> the certificate is only a loose lower bound (still reportable, but not the
headline). If matched and mismatched CF are indistinguishable, threat-matching does not transfer.

## Protocol (model, dataset/benchmark, attack/eval incl. STRONG attack, metrics, exact steps)
- **Model**: `meta-llama/Meta-Llama-3-8B-Instruct` (cached).
- **Benchmark (full)**: AdvBench 520 + HarmBench 400 = 920 clean harmful prompts.
- **Attack-free side**: per prompt, one forward + one backward -> M(x), L2(x), L1(x); per-prompt radii
  R_2 = M/L2 (for the L2 attack) and R_inf = M/L1 (for the Linf attack). CF_q(eps) = fraction with
  R_q < eps over a budget ladder eps in a geometric grid (e.g. 8 values spanning the attack's operating
  range in embedding-norm units).
- **Attack side (ground-truth ASR, STRONG)**: Schwinn embedding attack run *at each budget on the ladder*
  in both an L2 ball and an Linf ball (signed GD 100 steps, per-budget projection). Success judged locally
  (HarmBench Llama-2-13B classifier or Llama-Guard-3-8B). PGD-style masking check: verify more steps /
  restarts do not raise ASR (no gradient masking), the text analog of "AutoAttack <= PGD".
- **Metrics**: mean-absolute-gap and max-gap between CF_q(eps) and ASR_q(eps) per budget; Pearson/Spearman
  of the budget-normalized curve; matched-vs-mismatched CF gap; bootstrap CIs over prompts. Report the
  per-prompt scatter of R_q vs the measured min successful budget (Spearman), the direct per-sample form.
- **Steps**: (1) compute per-prompt M, grads, radii; (2) run embedding attacks at each budget x norm;
  (3) judge; (4) build ASR(eps) and CF(eps), overlay; (5) masking check; (6) budget-normalize and test
  collapse; (7) matched-vs-mismatched.

## Compute estimate (GPU-hours on A6000s)
- Attack-free diagnostics: < 0.5 h. Attack ladder: 920 prompts x 100 steps x 8 budgets x 2 norms is the
  cost driver; with warm-starting down the budget ladder ~15-25 h on one A6000. Masking check on a
  256-subset: ~3 h. Judge: ~1-2 h. **Total ~1.5-2 GPU-days**, parallelizable across the 2 A6000s to ~1 day.

## Why standalone top-tier (what a reviewer would call the contribution)
"Attack-free robustness curves for LLMs: a single forward+backward per prompt yields a first-order
embedding-space certificate whose certified fraction *equals* the measured jailbreak success rate across
budgets, and whose budget-normalized form collapses all budgets onto one curve — turning expensive
per-budget red-teaming into one cheap pass, with the correct (dual-norm, budget-normalized) scalar for
LLM robustness evaluation." This is a measurement-theory contribution: it gives the field the right
axis to report embedding-space robustness on, and a cheap, validated proxy for the ASR-vs-budget frontier.
Venue: ICLR/NeurIPS/USENIX-Sec/SaTML.

## Risks / kill criteria
- **Locally-affine premise may hold only at tiny eps**; the count law could be exact only near eps->0.
  Mitigate: report the regime where the gap < 0.05 and treat its breakdown budget as a finding (the
  "curvature edge", as the vision paper does).
- **Embedding-space budgets are not human-meaningful**; frame the contribution as evaluation methodology
  for open-weight white-box robustness (the accepted embedding threat model of Schwinn et al.), not as a
  deployment guarantee.
- **Transformer non-Lipschitz caveat**: the certificate uses the *local* gradient norm (finite everywhere),
  not a global constant; state this explicitly (self-attention is not globally Lipschitz, arXiv:2006.04710).
- Overlap with A1 is bounded: A1 is per-prompt ranking + gauge + invariance; A2 is the distributional
  count law + budget/norm geometry. Keep A2's headline on ASR(eps) = CF(eps).
