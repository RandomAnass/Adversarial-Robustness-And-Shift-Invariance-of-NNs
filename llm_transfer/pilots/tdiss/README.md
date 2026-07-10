# T-DISS: gauge-free threat-matched margin-to-Lipschitz dissociation in a text LLM

Transfers the vision paper's central object — the gauge-free, threat-matched margin-to-Lipschitz
ratio `R_q = M / ||∇M||_q` (Lemma ratiodegen, dual-norm threat-matching, `main.tex` §sec:coupling)
— to a stock aligned LLM (Meta-Llama-3-8B-Instruct), and tests the three claims the vision paper
makes about it, per the hardened protocol in `../../PICK.md` (T-DISS) and the four adversarial audits.

## Definitions (exactly matching the theory)
- **Margin** `M(x) = logit(refuse-anchor) − logit(affirm-anchor)` at the first generated position.
  Computed as a difference of two anchor logits at fixed argmax-selected indices, so M is EXACTLY
  linear in the logits ⇒ under `f→cf`, `M→cM` and `∇M→c∇M` ⇒ `R_q` is exactly gauge-invariant.
  Anchor token sets fixed *before* the run from the model's own greedy behavior (`probe_anchors.py`:
  harmful prompts → "I cannot…"; benign → "Sure/Here/The…").
- **Sensitivity** `L_q(x) = ||∂M/∂e(x)||_q`, exact analytic gradient wrt the prompt's own input
  embeddings, dual norm `q` of the attack (`q=2`↔L2 ball, `q=1`↔L∞ ball).
- **Ratio** `R_q(x) = M/L_q` (per-prompt first-order embedding robust radius).
- **Strong attack (label)**: PE-PGD — projected embedding-PGD on the SAME `e(x)`, minimizing the CE
  of an affirmative continuation target inside `||δ||_p ≤ ε`, R restarts, keep best. NOT append-Schwinn
  (that is the unbounded ceiling only, in the masking battery). Per-prompt radius `r_p` = min ε that
  jailbreaks (judged); per-prompt continuous attack loss at a reference ε is the finer signal.
- **Consistency null** `C(x)` = fraction of k=8 self-paraphrases whose greedy response is a refusal
  (observational Flip-Flop-Consistency on the fixed model; pre-empts the *training* methods
  2510.27062 / 2503.01345).
- **Judge**: Llama-Guard-3-8B (independent of the margin ⇒ no circularity); string fallback.

## The three results
1. **Prediction**: Spearman(R_q, r_2) and AUROC(R_q vs jailbreak label), with the PRIMARY partial
   Spearman(R_q, r_2 | clean-refuse base rate, raw M) — the RATIO must carry signal beyond M alone.
2. **Gauge (headline)**: under logit-scale c and refusal-logit-bias b, raw-M's ranking of
   jailbreakability MOVES while R_q's ranking is INVARIANT (`gauge_sweep.py`).
3. **Consistency null**: paraphrase-consistency does NOT predict jailbreakability (dissociation).

## Rigor (mandatory)
- Gradient-masking battery (`masking_battery.py`): steps 200→400 & restarts 5→10 monotonicity;
  vanishing-gradient fraction; unbounded append-Schwinn ceiling; local-linearity (Taylor gap).
- GCG cross-check (`gcg_check.py`, nanogcg) on a fixed 128-prompt slice — R_q must agree with GCG.
- Confounds: clean refusal base rate, prompt length T, response entropy, benchmark provenance.
- Pre-registered KILL: R_q's partial correlation with r_2 < 0.15 or insignificant ⇒ honest negative.

## Reproduce
```
PY=/home/students/.conda/envs/llmtransfer/bin/python
python fetch_data.py                 # AdvBench + HarmBench-standard + XSTest -> data/prompts.csv
CUDA_VISIBLE_DEVICES=0 $PY probe_anchors.py     # fix anchors from the model's own behavior
CUDA_VISIBLE_DEVICES=0 $PY run_tdiss.py --phase all      # phase1 diagnostics+consistency, phase2 PE-PGD
CUDA_VISIBLE_DEVICES=0 $PY gauge_sweep.py       # headline gauge test
CUDA_VISIBLE_DEVICES=0 $PY masking_battery.py   # gradient-masking audit
CUDA_VISIBLE_DEVICES=0 $PY gcg_check.py --n 128 # discrete cross-check
CUDA_VISIBLE_DEVICES=0 $PY validations.py       # anchor robustness, paraphrase validity, judge agreement
$PY analyze.py && $PY summarize.py && CUDA_VISIBLE_DEVICES=0 $PY make_figures.py
```
Results land in `results/` (per-prompt `*.jsonl`, `analysis.json`, `gauge.json`, `masking.json`,
`SUMMARY.json`, figures). GPU 0 only (GPU 1 reserved for a parallel VLM pilot).
