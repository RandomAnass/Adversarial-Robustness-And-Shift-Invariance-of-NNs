# Regression Check — `paper/report/main.tex`

Scope: verify the fixes to the prior `COHERENCE_AUDIT.md` items landed, and hunt
for new defects introduced by the rename (envelope `κ` → `τ`) and the abstract
rewrite. **Read-only; no files edited.** Line numbers refer to
`paper/report/main.tex` as read 2026-06-28.

Confidence key for new issues: HIGH / MED / LOW.

---

## Checklist (audit fixes)

### Fix 1 — `τ` (envelope/gradient-floor slack) distinguished from `κ = L/α` (bracket condition number) — **LANDED**

The envelope factor is now `τ`, and it is explicitly separated from the bracket `κ`.

- Prop. split body (line 137):
  > "The upper envelope $\|\nabla M(x_i)\|_2\le\tau\,M(x_i)/\|x_i\|_2$ holds exactly when the tangential factor is bounded, $\|\nabla_{\mathbb S}\log m(u_i)\|_2\le\sqrt{\tau^2-1}$; equivalently $\tau_i=\sec\angle(\nabla M(x_i),x_i)$. **This $\tau$ is the slack between the gradient and its radial floor, distinct from the bracket condition number $\kappa=L/\alpha$ of Proposition~\ref{prop:sandwich}** (the certificate's looseness): $\tau=1$ means the gradient is purely radial, $\kappa=1$ means the certificate $r_2=\eta/L$ is tight."

- Linear case in body now uses `τ` (line 143):
  > "For a linear classifier $g(x)=w^\top x$ at its hard-margin solution the factor is exact, $\tau_i=\|x_i\|_2/\gamma$ with $\gamma$ the geometric margin ... and sharp."
- Appendix agrees (line 515): "the linear case is exact with $\tau_i=\|x_i\|_2/\gamma$".

**No remaining place calls the envelope factor `κ`.** Every `\kappa` in the file (lines 100, 102, 137, 147, 424, 425, 431, 433, 436, 438) is the bracket condition number `L/α`. There is **no** "κ = 1 for a linear feature" in the old conflated (envelope) sense. The only "κ = 1 ... linear" statements are the *bracket* claim that the certificate is tight for a linear feature, which is correct:
- line 100: "The bracket is exact ($r_2=\eta/\|w\|_2$, $\kappa=1$) for linear invariant features"
- lines 431–433 (proof): "Thus $L=\alpha=\|w\|_2$, $\kappa=1$, and the boundary is reached at distance $\eta/\|w\|_2$".

This is the legitimate bracket use, not the envelope conflation H2 flagged.

### Fig. `coupling_split` caption — **LANDED**

Caption (line 147) now uses `τ`, states `τ=1` ⇔ purely radial, and gives the linear case as `τ=‖x‖/γ` (NOT `τ=1`):
> "the envelope factor $\tau=\|\nabla M\|/(M/\|x\|)=\sqrt{1+\|\nabla_{\mathbb S}\log m(u)\|^2}$ measures how far the gradient exceeds its radial floor. **It equals $1$ only when $\nabla M$ is purely radial ($\nabla_{\mathbb S}\log m=0$); for a linear or exactly invariant score it is the data condition number $\|x\|/\gamma$**, and at the trained networks it is large ($\tau\approx26$) ... (**$\tau$ is the gradient-floor slack, distinct from the bracket condition number $\kappa=L/\alpha$** of Proposition~\ref{prop:sandwich}.)"

The old caption's contradictory clause ("It is 1 only for a linear or exactly invariant feature") is gone and replaced exactly as the audit recommended.

### Fix 2 — duplicated `η = ½ dist(conv Ψ(X₊), conv Ψ(X₋))` after Corollary C removed — **LANDED**

Formula now appears once, in the Corollary C *statement* (line 118). The follow-up paragraph (line 120) keeps only the gloss, with the formula deleted:
> "Here $\eta$ is the exact hard-margin separation of the feature sets."

Sentence is grammatical after the deletion; no half-deleted fragment.

### Fix 3 — abstract de-run-on + CIFAR-100 scaling check — **LANDED**

The abstract (line 42) is now broken into ~13 shorter sentences. The two worst run-ons the audit named are split: the "Empirically, across ..." sentence now ends at "AutoAttack robust accuracy.", with the consistency anti-relation ("Shift-consistency does not predict robustness by itself, and under adversarial training it is negatively related to it.") and the selection rule ("Used as an attack-free rule ... shift-consistency picks the least.") as separate sentences.

`"three datasets"` now carries the CIFAR-100 qualifier:
> "across standard and adversarial training, **three datasets, two threat models, and a PreActResNet-18 backbone (with a CIFAR-100 scaling check)**, the threat-matched ratio predicts the adversarial robust radius and AutoAttack robust accuracy."

All claims from the audit's preservation list are present (two-regime framing, η/L, `1/√d` recovery, power-spectrum escape, certificate + two-sided bracket, Kamath placement, optimization margin-free + lazy-regime, empirical predictions across training/datasets/threats/PreActResNet-18, selection rule, margin/Lipschitz decomposition, polar identity, diagnostic-not-trainable). No claim dropped or duplicated vs the body.

*Note (not a defect):* the abstract remains a single paragraph (no blank-line break into the 4 beats the audit drafted). NeurIPS abstracts must be one paragraph, and the task's criterion was "shorter sentences", which is met. Em-dashes from the audit's draft were correctly avoided (replaced by commas), consistent with the house writing rules.

### Fix 4 — "margin-free theorem" → "margin-free result" — **LANDED**

Contribution heading (line 51):
> "**Optimization: a margin-free result** and the open selection problem (\S\ref{sec:opt})."

No occurrence of "margin-free theorem" remains anywhere (grep). The body uses the adjective form "\emph{margin-free}" (lines 51, 181) with no "theorem" attached.

### Fix 5 — no dangling "second degeneracy"; "trainable" vs "training target" consistent — **LANDED (with a LOW residual note)**

- Dangling ordinal fixed (line 151):
  > "**A further degeneracy** rules out the obvious workaround of maximizing the ratio directly."
  ("second" is gone; "further" needs no labelled "first".)

- The two near-identical headlines the audit flagged (L5) now match: §3.5 subsection title (line 127) and the experiments paragraph title (line 342) both read **"is a diagnostic, not a trainable target"**, and the appendix subsection title (line 561) also uses "not a trainable target". The specific "trainable" vs "training" headline clash is resolved.

*LOW residual (pre-existing, not introduced by the edits):* the document still mixes the wider family — "training target" in the abstract (line 42) and Fig. `tmreg` caption (line 566), vs "trainable target" in the three headings, plus "training objective" (lines 153, 340) and "trainable objective" (lines 50, 128). All are grammatical and meaningful; "target/objective" and "trainable/training" drift is stylistic and predates the fix. Flag only for completeness.

---

## New defects introduced by the rename / rewrite

**None found.**

Cross-checks performed:
- **`τ` defined before use.** `τ` first appears at its definition in Prop. split (line 137); all later uses (lines 143, 147 caption, 515) follow. Abstract and intro use the prose phrase "tangential factor / data condition number", no `τ` symbol — no use-before-definition.
- **`κ` defined before use.** First `\kappa` is the definition `κ := L/α` in Prop. sandwich (line 100); the intro (line 50) uses only the prose "up to a condition number", no symbol. No use-before-definition; no orphaned `κ`.
- **No internal contradiction between the two factors.** Body and caption agree: linear ⇒ `τ = ‖x‖/γ` (≠ 1) and bracket `κ = 1` (certificate tight). These are two distinct true statements about the linear case, now clearly separated.
- **No grammar breakage in edited regions** (lines 42, 50–52, 120, 137, 143, 147, 151, 350): each reads as a complete sentence; the Corollary-C deletion and the "further degeneracy" / "margin-free result" edits leave no doubled word, dangling clause, or half-deleted phrase.
- **`\ref` environment types still correct.** All cross-references resolve to the right genre: `Theorem~\ref{thm:A}` / `thm:lazy-cluster` → `theorem`; `Proposition~\ref{prop:sandwich}` / `prop:split` / `prop:rhoG` / `prop:rank` / `prop:generic` / `thm:finite-group` (label name cosmetic, referenced as "Proposition") → `proposition`; `Corollary~\ref{cor:C}` → `corollary`; `Lemma~\ref{lem:ps}` / `lem:rank` / `lem:bundle` / `lem:ratiodegen` → `lemma`. The rename touched no labels, so no reference was orphaned.
- **Abstract vs body claim parity** (Fix 3): "three datasets (with a CIFAR-100 scaling check)" now matches the limitations sentence (line 350) and the intro (line 52, which already names "CIFAR-10 and CIFAR-100"); the "data condition number (exact for linear max-margin)" abstract phrase matches the body `τ = ‖x‖/γ`. No claim added that the body lacks; none dropped.

---

## Summary

All five audit fixes LANDED and quote cleanly. The `κ`→`τ` rename is complete and
internally consistent (envelope = `τ`, bracket = `κ = L/α`, the figure caption
corrected, no leftover envelope-`κ` and no false "κ = 1 for linear feature").
The abstract rewrite preserves every claim with shorter sentences and the
CIFAR-100 qualifier. No new defects introduced. One LOW pre-existing residual:
"trainable/training" + "target/objective" wording still drifts outside the now-unified
section headings.
