# Coherence Audit — `paper/report/main.tex`

Scope: patchwork / coherence defects only (redundancy, inconsistent notation,
broken transitions, claim mismatches, abstract structure, naming/genre).
This is **not** a scientific-merit review and **no files were edited**.
Line numbers refer to `paper/report/main.tex` as read on 2026-06-28.

Confidence key: **HIGH** = clearly a defect, safe to fix; **MED** = likely, check;
**LOW** = verify, may be intentional.

---

## HIGH-confidence items

### H1 — Redundant verbatim re-definition of `η` around Corollary C
**Class:** Redundancy (leftover duplicated sentence from edits)
**Location:** lines 117–120.

Corollary C's *statement* already defines η:
> "...with achievable head margin $\eta=\tfrac12\,\mathrm{dist}(\mathrm{conv}\,\Psi(X_+),\mathrm{conv}\,\Psi(X_-))$ and Lipschitz constant $L$..." (line 118)

The very next paragraph repeats the identical formula:
> "Here $\eta=\tfrac12\,\mathrm{dist}(\mathrm{conv}\,\Psi(X_+),\mathrm{conv}\,\Psi(X_-))$ is the exact hard-margin separation of the feature sets." (line 120)

**Why:** the same definition `η = ½ dist(conv Ψ(X₊), conv Ψ(X₋))` appears twice within three lines; the second occurrence adds only the gloss "is the exact hard-margin separation."
**Suggested fix:** delete the duplicated formula in line 120 and fold the gloss into the corollary (or replace line 120's clause with "Here η is the exact hard-margin separation of the feature sets" without restating the formula).
**Confidence:** HIGH.

### H2 — `fig:coupling-split` caption says the envelope `κ = 1` for a linear feature; the body says `κ = ‖x‖/γ` for linear
**Class:** Inconsistent notation / internal claim mismatch
**Location:** figure caption line 147 vs Proposition-split discussion line 143 (and abstract line 42).

Caption (line 147):
> "the envelope constant $\kappa=\|\nabla M\|/(M/\|x\|)=\sqrt{1+\|\nabla_{\mathbb S}\log m(u)\|^2}$. **It is $1$ only for a linear or exactly invariant feature**, where the certificate $r_2=\eta/L$ is tight; at the trained networks the tangential factor is large ($\kappa\approx26$), equal to the data condition number $\|x\|/\gamma$..."

Body (line 143):
> "For a linear classifier $g(x)=w^\top x$ at its hard-margin solution **the factor is exact, $\kappa_i=\|x_i\|_2/\gamma$** with $\gamma$ the geometric margin, and sharp."

Abstract (line 42): "that factor is the data condition number **(exact for linear max-margin)**, large at the operating point."

**Why:** for a linear classifier the envelope/tangential factor `κ = ‖∇M‖/(M/‖x‖) = ‖x‖/γ`, which is generally `> 1` (line 143, line 137 `κ_i = sec∠(∇M,x)`, line 515, and the abstract all agree). The caption's clause "It is 1 only for a linear or exactly invariant feature" is the *bracket* property (`κ_bracket = L/α = 1` for linear ⇒ tight certificate `r₂ = η/L`, Prop sandwich, line 100/431), not the envelope `κ` it is defining. The caption conflates the two κ's, and as written directly contradicts line 143. The caption is even self-inconsistent: it equates `κ` with `‖x‖/γ` at trained nets, yet `‖x‖/γ ≠ 1` for the linear case it just called `κ = 1`.
**Suggested fix:** in the caption, decouple the two statements, e.g. "It equals 1 only when `∇M` is radial (`∇M ∥ x`); for a linear or exactly invariant *score* the **certificate** `r₂ = η/L` is tight (bracket `κ_bracket = L/α = 1`), but the envelope factor itself is `‖x‖/γ`." Or simply drop "It is 1 only for a linear or exactly invariant feature."
**Confidence:** HIGH (two directly conflicting quotes; the math sides with the body).

---

## MED-confidence items

### M1 — Symbol `κ` and the term "condition number" denote two different quantities
**Class:** Inconsistent notation/terminology
**Locations:** Prop sandwich line 100 / proof line 424 vs Prop split line 137 / §coupling line 143 / fig line 147 / abstract line 42.

- **κ as bracket condition number:** "with condition number $\kappa:=L/\alpha\ge1$... realized $\kappa\approx1.6$–$2.4$" (line 100); "$\kappa:=L/\alpha\ge1$" (line 424); intro "a characterization up to a condition number" (line 50).
- **κ as tangential/data condition number:** "$\kappa_i=\sec\angle(\nabla M(x_i),x_i)$" (line 137), "$\kappa_i=\|x_i\|_2/\gamma$" (line 143), "$\kappa\approx26$, equal to the data condition number $\|x\|/\gamma$" (line 147), abstract "the data condition number" (line 42).

**Why:** the same letter `κ` and the same phrase "condition number" name two definitionally and numerically distinct objects (bracket looseness `L/α ≈ 1.6–2.4` vs gradient-floor slack `‖x‖/γ ≈ 26`). A reader meeting "up to a condition number κ" in §3.2 and "κ ≈ 26" in §3.5 will assume one quantity. This is the root cause of H2.
**Suggested fix:** rename one of them (e.g. `κ_bracket = L/α` vs `κ_data = ‖x‖/γ`, or use `τ` for the tangential factor), and qualify "condition number" each time.
**Confidence:** MED (clearly a reused symbol; whether the authors intend them as "the same family" is the only reason it is not HIGH).

### M2 — "three datasets, two threat models" vs CIFAR-100 also being used
**Class:** Claim mismatch (undercount)
**Locations:** abstract line 42, intro line 52, limitations line 350 vs ResNet section lines 311, 329.

Headline claim (3×): "across ... three datasets, two threat models" (abstract); "across three datasets and two threat models" (intro line 52); "across three datasets, two threat models, and small-convolutional and PreActResNet-18 backbones" (line 350).
But the ResNet section uses a fourth dataset: "we repeat it on a PreActResNet-18 backbone **on CIFAR-10 and CIFAR-100**" (line 311); "On **CIFAR-100** the threat-matched law holds in the same direction (Spearman $+1.0$ over the four arms), underpowered at four cells" (line 311); "$\approx0.97$ on CIFAR-100" (line 329).

**Why:** the empirical study actually touches four datasets (MNIST, Fashion-MNIST, CIFAR-10, CIFAR-100); a reader who reaches the CIFAR-100 results may find "three datasets" inaccurate.
**Suggested fix:** either say "three datasets (with a CIFAR-100 scaling check)" or note CIFAR-100 is the fully-powered grid's exclusion. May be intentional scoping (CIFAR-100 is "underpowered at four cells" and only Spearman over arms), so VERIFY.
**Confidence:** MED (leaning verify).

### M3 — Intro calls it "a margin-free theorem"; the body presents the margin-free result in prose, not as a numbered Theorem
**Class:** Naming/genre (per `conventions_*` "keep theorem honest")
**Locations:** intro contribution heading line 51 vs §opt body line 181.

Intro: "**Optimization: a margin-free theorem** and the open selection problem (\S\ref{sec:opt})." (line 51)
Body: the margin-free result appears only as prose — "on orbit-closed data the invariant and unconstrained two-layer-ReLU max-margin values coincide, because orbit-averaging an unconstrained solution gives an invariant one of equal minimum norm" (line 181). There is no `\begin{theorem}` for it; the only numbered theorem in this area is `thm:lazy-cluster` (appendix).

**Why:** the comparator conventions reserve "Theorem" for numbered, proven headline results and warn against over-labeling (`conventions_sametopic.md` item 13, `conventions_certtheory.md` "keep theorem honest"). Labeling a prose-proved claim "a margin-free theorem" in a section heading mismatches the body and the genre, and may make a reader hunt for a Theorem environment that is not there.
**Suggested fix:** either promote the margin-free statement to a numbered Proposition/Theorem (with the one-line proof or an appendix pointer), or soften the heading to "a margin-free result"/"margin invariance".
**Confidence:** MED.

### M4 — The abstract is a single run-on paragraph
**Class:** Abstract structure (issue 5)
**Location:** lines 41–43.

The abstract is one ~430-word paragraph chaining ~13 distinct claims, several joined by semicolons into very long sentences (e.g. the "Empirically, across..." sentence spanning robust-radius prediction, AutoAttack, the consistency anti-relation, and the selection rule; and the "The mechanism is a decomposition..." sentence). See the dedicated rewrite in the final section (claims preserved, broken into logical beats).
**Confidence:** MED (stylistic; the rewrite is the actionable output).

---

## LOW-confidence items (verify; may be intentional)

### L1 — Invariant (linear) margin denoted three ways
**Class:** notation proliferation. `γ_inv` (Theorem A, lines 75/123), `Sep_inv` / `Sep(Π_inv)` (§dich line 96, Table struct line 193), and `η` (§dich line 94). They are the same quantity; the equality is stated only once, in the `fig:concept` caption "here $\eta=\gamma_{\mathrm{inv}}$ for the linear case" (line 67). **Fix:** add a one-clause bridge in §3.2 text ("write `η = γ_inv = Sep(Π_inv)`"). **Confidence:** LOW.

### L2 — Bracket hypothesis named two ways
**Class:** terminology variation. "reachability condition" (abstract line 42, §dich line 98) vs "co-Lipschitz condition" (intro line 50). Same Prop-sandwich hypothesis (reaching path + co-Lipschitz lower bound). **Fix:** pick one name. **Confidence:** LOW.

### L3 — "A second degeneracy" with no explicitly-labeled first
**Class:** dangling ordinal. Line 151: "A second degeneracy rules out the obvious workaround of maximizing the ratio directly." The "first" degeneracy (the margin–gradient coupling/slack of Prop split) is discussed but never called a "degeneracy," so the ordinal "second" is slightly unanchored. **Fix:** call the coupling the "first degeneracy" earlier, or drop "second." **Confidence:** LOW.

### L4 — "margin-to-Lipschitz" vs "margin-to-sensitivity"; `L` called both "Lipschitz" and "sensitivity"
**Class:** terminology. Abstract: "margin-to-Lipschitz ratio" (line 42); captions/body: "margin-to-sensitivity ratio" (lines 265, 331) and "margin-to-sensitivity axis" (line 309). `L = E‖∇M‖` is named both a Lipschitz constant and an input-sensitivity. The dual use is bridged at line 128, so this is likely intentional. **Confidence:** LOW.

### L5 — Repeated paragraph/section title "η/L is a diagnostic, not a trainable/training target"
**Class:** structural redundancy. §3.5 subsection title (line 127, "...is a diagnostic, not a trainable target") and the experiments paragraph title (line 342, "...is a diagnostic, not a training target") are near-identical (note "trainable" vs "training"). Defensible as theory-claim vs empirical-confirmation, but the duplicated headline is a coherence smell; also unify "trainable" vs "training." **Confidence:** LOW.

### L6 — "four controlled interventions" claimed twice within the intro
**Class:** intra-intro redundancy. Appears in the structural-theory bullet ("...four controlled interventions (Appendix~\ref{app:tmreg}) shows $\eta/L$ is a diagnostic and not a trainable objective", line 50) and again in the experiments bullet ("Four controlled interventions then show $\eta/L$ cannot be trained...", line 52). The same finding is previewed twice in adjacent bullets. **Fix:** keep it in one bullet (the experiments bullet). **Confidence:** LOW.

### L7 — "small-margin corner" (abstract) vs "small-η/L corner" (body)
**Class:** terminology. Abstract line 42 "a small-margin corner"; body §3.4 repeatedly "small-$\eta/L$ corner" (lines 123, 125). Minor; the abstract's "small margin relative to sensitivity" makes it recoverable. **Confidence:** LOW.

### L8 — Table column header `η/L` (Table 3, `tab:cifar`) vs `η/L_2` (Table 4, `tab:cifar-at`)
**Class:** notation drift. Both denote `η / E‖∇M‖₂`. The AT table adds the `_2` subscript to distinguish from `η/‖∇M‖₁`; harmless but slightly inconsistent between adjacent tables. **Confidence:** LOW.

### L9 — Appendix results stated but never `\ref`-cross-referenced
**Class:** dangling (mild). `lem:ps-lip` (line 370), `thm:toy` (line 381), `prop:ib-envelope` (line 505), `rem:lazy-relu` (line 490) are described in prose in the body (e.g. "the power-spectrum feature is $2B$-Lipschitz", line 120; "an exactly solvable two-subspace model ... robust radius $a/\sqrt2$", line 120) but the body never cites them by number. Acceptable for self-contained appendix material; flag only for completeness. **Confidence:** LOW.

---

## Cross-checks that came back CLEAN (no defect)

To document the false-positive screen, the following were checked and are **consistent**:
- All `\ref` targets resolve to an existing `\label` (figures, tables, theorems, appendices); no dangling reference to a removed object.
- Correlation numbers match between prose, tables, and figure captions: MNIST/Fashion Spearman `+0.96 / +0.71`, consistency `−0.31 / 0.00` (lines 202, 220); CIFAR Pearson `0.998` (lines 250, 260); AT matched/mismatched `+0.88 / +0.55` and consistency `−0.88` (lines 262, 301); generality table values (lines 291, 301–304); ResNet `+0.91 / −0.81`, partial `−0.82` (line 311); graded `+0.93` (line 321); statistical-power CIs (line 309).
- Cell-count arithmetic is consistent: 8 cells = 4 arms × 2 widths (3 seeds); 24-cell = 4×6 widths; 12-cell = 4×3 widths; ResNet 12 cells = 6 arms × 2 widths; graded "39 of 40" = 4 anti-alias arms × 2 widths × 5 seeds; "36 CIFAR-10 models = 12 standard + 24 adversarial."
- Clean-accuracy ranges quoted in prose match the AT table: exact-cyclic `0.57–0.63` vs others `0.69–0.78` (line 262 ↔ Table 4).
- Ge `1/√d` recovery (`γ_inv = 1/√d = 0.125` at d=64) consistent across abstract, intro, §3.4, Table 1.
- Kamath is consistently framed as an "interpretation"/"corner," not a proven counterexample, in both abstract and body (line 125) — no over-claimed "impossibility/no-go."
- Theorem/Proposition/Lemma environment labels match their in-text references (e.g. `\label{thm:finite-group}` is referred to as "Proposition" in text and proof, lines 85/90/362 — label name is cosmetic only).

---

## Proposed restructured Abstract (claims unchanged)

The rewrite below keeps every claim of the current abstract (lines 41–43) — the
two-regime framing, η/L, the linear `1/√d` recovery, the power-spectrum escape,
the certificate + two-sided bracket, the Kamath placement, the optimization
margin-free + lazy-regime result, the empirical predictions across standard and
adversarial training / three datasets / two threat models / PreActResNet-18, the
selection-rule result, the margin/Lipschitz decomposition, the polar identity,
and the diagnostic-not-trainable conclusion — but breaks the single paragraph
into logical beats with shorter sentences.

> Making a convolutional network more shift-invariant has been reported both to reduce its adversarial robustness [Ge et al.] and to improve it [Grabinski et al.; Saha et al.]. We show these are two regimes of one quantity: the margin of the discriminative signal that survives projection onto the invariant feature space, measured against that feature's sensitivity — a margin-to-Lipschitz ratio η/L. A large ratio lets invariance and robustness coexist; a small surviving margin forces a trade-off.
>
> Structurally, for a shift-invariant linear classifier the ratio is exact and recovers the `1/√d` robustness collapse of [Ge et al.] for a localized signal, while for frequency-coded classes a convolution-plus-pooling layer with a nonlinearity computes power-spectrum features that separate classes no linear classifier can. The ratio is also a robustness certificate, `r₂ ≥ η/L`, which we complete to a two-sided bracket under an explicit reachability condition; it places the apparent counterexample of [Kamath et al.] as a small-margin corner rather than a contradiction. On the optimization side, shift-invariance cannot raise the margin on orbit-closed data, so any robustness gain there must come through the Lipschitz term, which we prove in the lazy regime.
>
> Empirically — across standard and adversarial training, three datasets, two threat models, and a PreActResNet-18 backbone — the threat-matched ratio predicts the adversarial robust radius and AutoAttack robust accuracy, while shift-consistency does not by itself and is negatively related to robustness under adversarial training. The mechanism is a decomposition of each operator's effect into a margin term and a Lipschitz term: a graded anti-aliasing sweep improves robustness at matched clean accuracy, whereas exact invariance hurts by collapsing the margin — a single change that lowers clean accuracy and robustness together. Used as an attack-free rule for choosing an invariance operator, η/L picks the most or near-most robust one, while shift-consistency picks the least.
>
> An exact polar identity splits the margin gradient of a bias-free homogeneous network into a radial floor `M(x)/‖x‖` and a tangential factor, exactly characterizing the coupling; that factor is the data condition number (exact for linear max-margin) and is large at the operating point. The obstruction to training η/L is therefore empirical and sharp: four controlled interventions that penalize or directly maximize η/L all collapse the margin and leave robustness flat or worse, and because the ratio is scale-invariant its maximizer is the constant classifier. So η/L diagnoses robustness rather than serving as a training target.

Notes on the rewrite:
- No numbers, datasets, citations, or claim directions were added or removed.
- "data condition number (exact for linear max-margin)" is kept verbatim from the
  current abstract; if M1/H2 are fixed, the same κ-naming fix should be reflected
  here for consistency.
- If M2 is fixed ("three datasets" → include CIFAR-100), update this rewrite's
  third beat accordingly.
