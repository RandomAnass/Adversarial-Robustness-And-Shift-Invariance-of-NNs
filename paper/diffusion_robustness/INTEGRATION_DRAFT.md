# Integration draft — diffusion result as the 3rd contribution (APPROVED spine + title generalization)

Status: skeleton with `⟨MS:...⟩` placeholders for the multi-seed firming numbers (run `b1zdu5toy`).
Execute the `main.tex` edits once those land. Single-seed numbers shown for reference.

## 1. Title candidates (user approved generalizing the title)

Current: *When Does Shift-Invariance Permit Adversarial Robustness? A Margin-Preservation Theory*

- **(A, recommended)** *The Margin-to-Lipschitz Ratio Across Invariance and Data: A Threat-Matched Account of Adversarial Robustness*
- (B) *What the Margin-to-Lipschitz Ratio Diagnoses About Adversarial Robustness: From Shift-Invariance to Synthetic Data*
- (C) *When Does Margin Preservation Permit Adversarial Robustness? A Threat-Matched η/L Theory for Architecture and Data Interventions*

Recommendation: (A) — keeps the η/L object central, signals the two arenas (invariance + data), avoids over-claiming ("account", not "governs everything"). Honest: η/L *predicts/diagnoses* robustness and bounds the certified radius (r₂ ≥ η/L); it is **not** a trainable target.

## 2. Spine (light generalization, not a reframe)

> The threat-matched, gauge-free ratio η/L is the quantity that tracks adversarial robustness — across both architecture/invariance and training-data interventions. Margin, Lipschitz, norm, invariance, and shift-consistency are not separately reliable.

Three contributions: (1) margin-preservation [thm:A]; (2) no-gap [thm:lazy-cluster]; (3) **η/L law under a data intervention + two confound demonstrations** (new, this draft).

## 3. Abstract additions (insert near the existing scale-invariance sentence)

> We further show the ratio is not specific to architecture: under a training-**data** intervention
> (adversarial training augmented with diffusion-generated images), the four data-dose models obey the
> same threat-matched law — the Linf-matched ratio η/L₁ predicts AutoAttack robust accuracy
> (Pearson ⟨MS:r_match⟩), while the mismatched L₂ ratio anti-predicts it (⟨MS:r_mis⟩). The same
> intervention exposes two ways a naive margin-versus-Lipschitz reading misleads: the split is
> gauge-dependent (only η/L and the certified radius are gauge-free), and at a fixed epoch it is
> confounded by robust overfitting — which, in this lens, is itself an η/L collapse that the added data
> prevents. This reinforces that η/L is a diagnostic of robustness, not a trainable target.

## 4. New §5 subsection (draft LaTeX — fill ⟨MS⟩ from multi-seed)

```latex
\subsection{The $\eta/L$ law extends to a data intervention}\label{sec:diffusion}
The structural results concern \emph{architecture} (invariance). We close with a \emph{data} intervention
that stresses the same diagnostic. We adversarially train (\,$\ell_\infty$, $8/255$) a PreActResNet-18 on
CIFAR-10 augmented with $0/100\text{k}/500\text{k}/1\text{M}$ EDM diffusion images
\citep{wang2023better}, compute-matched (identical optimizer steps per epoch; a fixed $30\%$ real fraction
per batch), $3$ seeds.

\paragraph{The threat-matched ratio predicts robustness; the mismatched one does not.}
At each arm's best robust checkpoint (early stopping on a held-out split), the $\ell_\infty$-matched ratio
$\eta/L_1=M/\lVert\nabla M\rVert_1$ tracks AutoAttack robust accuracy across the $12$ dose$\times$seed
models (Pearson $\,\eta/L_1$ vs.\ AA $=\langle MS:r\_match\rangle$, monotone in dose), whereas the
mismatched $\ell_2$ ratio $\eta/L_2$ \emph{anti}-predicts it ($\langle MS:r\_mis\rangle$); $\eta/L_2$
instead tracks the $\ell_2$ certified radius ($+0.99$). This is the threat-matching requirement of
\S\ref{sec:dich}, now demonstrated on a data rather than an architecture axis (Fig.~\ref{fig:etaL-law}).

\paragraph{Two ways the naive reading misleads.} (i) \emph{Gauge.} $M$ and $\lVert\nabla M\rVert$ are
degree-1 homogeneous in the logits, so the split of $\eta/L$ into a margin term and a Lipschitz term is
gauge-dependent: the same dose's ``smaller margin / smaller $L$'' attribution survives a logit-norm anchor
but reverses under an NLL/temperature anchor. Only $\eta/L$ and the input-space radius are gauge-free.
(ii) \emph{Robust overfitting.} At a fixed final epoch the comparison is confounded: the real-only baseline
robustly overfits, its $L$ inflating late while its robust accuracy decays, which manufactures an apparent
``smoothness'' gain. Proper early stopping removes it; the gain persists ($\mathrm{AA}\ \langle MS\rangle$)
but at \emph{equal-or-higher} $L$, and the only quantity that still predicts AA is the threat-matched
$\eta/L_1$. In this lens robust overfitting is an $\eta/L$ collapse (baseline $\eta/L_2$:
$1.06{\to}0.86$ over the overfitting phase) that the added data prevents.
```

## 5. Appendix (vicinal-coverage theorem, honestly scoped)

Move `THEORY_vicinal_coverage.tex`'s theorem in as an appendix subsection titled
*A candidate static mechanism: vicinal gradient coverage*, with the standing caveats already in that file
(static; local linearization; the realized network effect is robust-overfitting prevention; its
``smoothness'' decomposition is gauge-relative). **Do not** present it as the confirmed mechanism.

## 6. Honesty guardrails (carry verbatim into the writing)

- No claim of a novel "smoothness mechanism" — it was confounded (gauge + epoch).
- "Synthetic data improves AT robustness / reduces robust overfitting" is **known** (Wang 2023); the
  novelty is the η/L *accounting* and the two confound demonstrations.
- Keep n and seeds explicit; report the mismatched-anchor reversal honestly.
- 1-seed single-run reference numbers (to be replaced by multi-seed): r_match=+0.96, r_mis=-0.75,
  AA 0.391→0.482, η/L₂ collapse 1.057(ep20)→0.859(ep40).
```
