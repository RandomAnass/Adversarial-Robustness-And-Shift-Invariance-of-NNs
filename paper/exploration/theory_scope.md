# Theory Scope: the strongest provable theorem about the margin–sensitivity coupling

Goal: from our empirical findings on $\eta/L$ (margin-to-Lipschitz ratio) under PGD adversarial
training, identify the single strongest theorem we can prove end-to-end, grounded in the
capacity / law-of-robustness literature. Honest provability ratings throughout.
Compiled 2026-06-27. Every load-bearing external result is read to its statement and tagged
with an arXiv id; nothing here is invented.

---

## 0. TL;DR (the recommendation, up front)

Our three findings are:
1. **Self-limiting coupling.** Under PGD-AT, per-sample margin $M=f_y-\max_{j\neq y}f_j$ and
   input-gradient norm $\|\nabla M\|$ are *positively* coupled within a model (Spearman $\approx+0.5$),
   architecture-independent (ReLU/SiLU/GELU). The net buys margin by raising sensitivity.
2. **Two failed method experiments**, both consequences of (1): (a) penalising $\|\nabla M\|$
   raises $\eta/L$ but not robustness because $M$ falls in lockstep; (b) penalising $\|\nabla M\|/M$
   collapses to the constant classifier ($M\to0,\ \|\nabla M\|\to0$, chance accuracy).
3. **Already proved** in our paper: the two-sided bracket $\eta/L\le r_2\le\eta/\alpha$
   (Prop. `prop:sandwich`) and a lazy/NTK orbit-projection theorem (`thm:lazy-cluster`).

**Verdict.** The cleanest, fully-provable, non-trivial, *not-subsumed* result is **(B): the
homogeneity self-limiting bound** $\;\|\nabla M(x)\|\ge M(x)/\|x\|\;$ for bias-free
(degree-1 homogeneous) ReLU networks, which turns finding (1) into a *pointwise theorem*,
proves the $\eta/L\le\|x\|$ ceiling, and explains experiment 2(a) exactly. It pairs with **(C):
the scale-invariance degeneracy** of ratio-maximisation (clean but near-folklore) which explains
2(b). The most *valuable* but most *caveated* result is **(A): the capacity ceiling**
$\eta/L\le\tilde O(\sqrt{p/(nd)})$, a correct corollary of Bubeck–Sellke (2105.12806) for the
*global/certified* ratio in the *noise-fitting* regime — present it as the capacity wall, but do
not overclaim it as the local empirical coupling. Recommended deliverable: prove **B + C**
(both clean), and state **A** as the honestly-scoped capacity context. Candidate **D** is not a
separate theorem; the architecture-independence is a corollary of A's universality.

| Cand. | Statement (one line) | New? | Provability | Matches which finding |
|---|---|---|---|---|
| **A** | $\eta/L_{\text{glob}}\le\tilde O(\sqrt{p/nd})$ (need nd params for $O(1)$ certified radius) | corollary of BS21 | **clean but partly subsumed**; global-not-local, needs label noise | capacity wall behind (1) |
| **B** | $\|\nabla M(x)\|\ge M(x)/\|x\|$ for homogeneous nets $\Rightarrow \eta/L\le\|x\|$ | framing new, identity old | **clean** (Euler + Cauchy–Schwarz) | (1) pointwise + exp 2(a) |
| **C** | $\arg\max_f \mathbb E[M/\|\nabla M\|]$ is scale-free $\Rightarrow$ constant classifier is degenerate optimum | folklore | **clean but near-trivial** | exp 2(b) |
| **D** | architecture-independence of the coupling | — | subsumed by A (isoperimetry is activation-agnostic) | (1) universality |

---

## Part 1 — Literature survey (exact statements, assumptions, overlap)

### 1.1 Bubeck & Sellke, *A Universal Law of Robustness via Isoperimetry*, arXiv:2105.12806 (NeurIPS 2021)

This is the load-bearing paper for candidate A. Read to the theorem.

- **Isoperimetry (Def. 1.1).** A measure $\mu$ on $\mathbb R^d$ is *$c$-isoperimetric* if every
  bounded $L$-Lipschitz $f$ obeys $\;\mathbb P[\,|f(x)-\mathbb E f|\ge t\,]\le 2e^{-dt^2/(2cL^2)}$.
  (Gaussian $N(0,I_d)$ and the uniform sphere/cube satisfy this with $c=O(1)$.)
- **Function class.** $\mathcal F=\{f_w:\ w\in\mathbb R^p\}$ parametrised by $p$ reals with
  $\|w\|\le\mathrm{poly}(n,d)$, and $w\mapsto f_w$ is $J$-Lipschitz (Lipschitz-in-parameters,
  $J\le\mathrm{poly}$). Each $f_w$ is itself Lipschitz in $x$; $\mathrm{Lip}(f)$ is that constant.
- **Data.** $n$ i.i.d. pairs $(x_i,y_i)\in\mathbb R^d\times[-1,1]$, $x_i\sim\mu$ isoperimetric;
  noise floor $\sigma^2:=\mathbb E_\mu[\mathrm{Var}(y\mid x)]>0$.
- **Theorem 1 (the law).** With high probability, *every* $f\in\mathcal F$ satisfying
  $\tfrac1n\sum_i(f(x_i)-y_i)^2\le \sigma^2-\varepsilon$ has
  $$\boxed{\ \mathrm{Lip}(f)\ \ge\ \tilde\Omega\!\Big(\tfrac{\varepsilon}{\sigma}\sqrt{\tfrac{nd}{p}}\Big)\ }$$
  ($\tilde\Omega$ hides $\log$ and the $J,\|w\|$ poly factors). So $O(1)$-Lipschitz interpolation of
  $n$ points needs $p\gtrsim nd$ parameters: "$d\times$ more than mere interpolation."
- **Mechanism.** Below the noise floor the model must *memorise the label noise*; on isoperimetric
  data a low-Lipschitz function concentrates, so it cannot wiggle to fit $n$ independent noise bits
  unless it has $\gtrsim nd$ effective degrees of freedom.
- **Overlap with us.** Directly powers candidate A. **Crucial caveats** when reused: (i) it lower-bounds
  the **global** $\mathrm{Lip}(f)$, whereas our empirical $L=\|\nabla M(x_i)\|$ is the **local** gradient
  at the data; $\|\nabla M(x_i)\|\le\mathrm{Lip}$, so the bound on the global ratio does **not** bound
  the local ratio. (ii) It needs $\sigma^2>0$ (label noise / memorisation); on clean, $r$-separated
  real data (Yang 2020, arXiv:2003.02460, CIFAR class sep $\approx0.21\gg 8/255$) the law does **not**
  forbid robust interpolation. Both caveats must be stated.

### 1.2 Bubeck, Li, Nagaraj, *A law of robustness for two-layer neural networks*, arXiv:2009.14444 (COLT 2021)

- **Conjecture.** For any Lipschitz activation and "most" datasets, a two-layer net with $k$ neurons
  that perfectly fits $n$ points has $\mathrm{Lip}\gtrsim\sqrt{n/k}$. (Consistent with BS21: for a
  two-layer net $p\approx kd$, so $\sqrt{nd/p}=\sqrt{n/k}$.) Proven for the spectral-norm surrogate,
  in the regime $n\approx d$, and for degree-$p$ polynomial activations when $n\approx d^p$.
- **Overlap.** The neuron-count form of the same wall; cite as the historical/2-layer specialisation
  of A. Already general-purpose; nothing here is specific to $\eta/L$.

### 1.3 Wu, Huang, Zhang, *A Law of Robustness beyond Isoperimetry*, arXiv:2202.11592 (ICML 2023)

- Removes the isoperimetry assumption: under a finite-Wasserstein / sub-Gaussian condition, a
  distribution-free Lipschitz lower bound $\tilde\Omega(n^{1/d})$ for interpolators. Weaker rate, broader
  data. Useful to cite so candidate A is not hostage to "is CIFAR isoperimetric?".
- A 2026 follow-up, *Does Order Matter: Connecting the Law of Robustness to Robust Generalization*
  (arXiv:2602.20971), ties the law to generalisation gaps. Peripheral.

### 1.4 Memorization capacity (the BS mechanism's other face)

The "$nd$ parameters" lower bound is the robust/smooth dual of memorization-capacity upper bounds
(a width-$O(\sqrt n)$ ReLU net can memorise $n$ points; smoothly/robustly memorising needs the
extra $d$ factor). Feldman 2020 (arXiv:2008.03703) "memorisation is necessary for near-optimal
accuracy" is the data-side companion (our `survey_empirical.md` §3); BS21 is the capacity-side
companion. Together they say robust+accurate is capacity-bound when tails must be fit. Cite as
context, not as a separate theorem.

### 1.5 Lower bounds on input-gradient norm vs margin / dimension

- **Simon-Gabriel et al., arXiv:1802.01421 (ICML 2019).** Adversarial vulnerability $\propto\|\nabla_x\ell\|$;
  the $\ell_1$ gradient norm grows like $\sqrt d$ at init and *persists after robust training*. This is the
  direct empirical anchor of our coupling's denominator and of the "$\eta/L$ small in high $d$" intuition.
- **Isoperimetric / Poincaré view.** For isoperimetric $\mu$, a classifier that is $\approx\pm1$ on two
  sets of constant mass must have $\mathbb E\|\nabla g\|\gtrsim\sqrt d\cdot(\text{boundary measure})$ — a
  Cheeger/Poincaré lower bound on average sensitivity. This is the "lower bound on $\|\nabla\|$ vs margin"
  the task asks about; it is real but blunt (it bounds the *average*, not the per-sample coupling).

### 1.6 Constant-function / degenerate-minimizer phenomena

- **Tsuzuku, Su, Sugiyama, *Lipschitz-Margin Training*, arXiv:1802.04034 (NeurIPS 2018).** Gives the
  certificate $r_2\ge \text{margin}/(\sqrt2\,L)$ (their Eq. 5), our lower arm. They explicitly warn that
  naively maximising margin while shrinking $L$ has a **degenerate optimum at the constant function**
  (margin and $L$ both $\to0$): the ratio is ill-posed without a scale anchor. This is the published seed
  of candidate C; our paper already cites it for the 2(b) degeneracy.
- **Hein & Andriushchenko, arXiv:1705.08475 (NeurIPS 2017).** Cross-Lipschitz bound
  $r\ge\min_j (f_c-f_j)/\max_{B}\|\nabla(f_c-f_j)\|$; exact for linear ($r=\eta/\|w\|$). This is the
  $\kappa=1$ case of our bracket. Their regularizer is local and soft; no modern AA validation.
- **Reading.** The constant-classifier degeneracy is *known* (Tsuzuku). The contribution candidate C can
  add is the clean *scale-invariance* characterisation (why it is structurally unavoidable, not a tuning
  artifact), tied to our exp 2(b). Honest: low novelty.

### 1.7 Implicit bias of GD / AT toward (non-)robust solutions

- **Lyu & Li, arXiv:1906.05890 (ICLR 2020)** and **Ji & Telgarsky**: for homogeneous nets with
  exp/logistic loss, GD converges *in direction* to a KKT point of the parameter-space max-margin problem.
  Foundation for the homogeneous-net analyses, and the reason candidate B's homogeneity hypothesis is the
  natural one.
- **Soudry et al., arXiv:1710.10345.** GD on separable data $\to$ max-margin in
  *parameter/representation* space — **not** input-space robustness once divided by the unbounded input
  gradient. "GD already maximises margin $\ne$ robustness"; this is the gap our coupling exploits.
- **Vardi, Yehudai, Shamir, *Gradient Methods Provably Converge to Non-Robust Networks*, arXiv:2202.04347
  (NeurIPS 2022).** Depth-2 ReLU nets trained by gradient flow are provably non-robust (small
  $\ell_2$ adversarial perturbations) *even though robust nets fitting the same data exist*; **every** KKT
  point of the max-margin problem is non-robust. The non-robustness is exactly a *large input-gradient*
  phenomenon at the max-margin solution — kin to candidate B.
- **Frei, Vardi, Bartlett, Srebro, PMLR v195 (COLT 2023), "double-edged sword".** For clustered data with
  small inter-cluster correlation, GD-trained two-layer ReLU generalises with perfect clean accuracy but is
  non-robust; mechanism = **feature averaging** (hidden weights align to class-mean, not individual
  features). Robust nets exist and are explicitly constructible.
- **Li et al. 2025 (feature averaging).** Refines the mechanism: averaging is the cause; a *supervision*
  fix (finer labels) restores robustness.
- **Min & Vidal, *Can Implicit Bias Imply Adversarial Robustness?*, arXiv:2405.15942 (ICML 2024).** With
  polynomial-ReLU (pReLU) two-layer nets, the implicit bias of GD *can* favour robust solutions — they
  prove a positive direction for pReLU and **conjecture** an architectural re-pointing in general. Our
  retracted optimization attempt (`CONSOLIDATED_OPT_THEORY.md`) tried and failed to convert this
  conjecture for conv-GAP; that lane is **open** and not a clean target.
- **Overlap with our candidates.** This whole line is *trajectory*-level (which solution GD selects).
  Candidate B is *static* (a property of any homogeneous net at its data) and is therefore independent of,
  and complementary to, Vardi/Frei: B says *why* the selected (or any) homogeneous solution has the
  coupling; Vardi/Frei say GD selects a non-robust one. B is not subsumed by them (they bound robustness of
  a specific GF limit; B is a deterministic pointwise identity for all homogeneous nets).

### 1.8 What our paper already proves (do not re-derive)

- `prop:sandwich`: $\eta/L\le r_2\le\eta/\alpha$, $\kappa=L/\alpha\ge1$, exact ($\kappa=1$) for linear/
  invariant features (Hein); verified `verify_sandwich.py` (5/5, $\kappa\approx1.6$–$2.4$).
- `thm:lazy-cluster`: in the lazy/NTK + smooth-activation regime, orbit-averaging is a non-expansive RKHS
  projection (Elesedy 2021), so invariance weakly raises the certified $\eta/L$; gap = orbit-variance;
  bare-ReLU NTK non-Lipschitz caveat (Bietti–Mairal). These are **structural/optimization** results; the
  *capacity/coupling* statements below are orthogonal new content.

---

## Part 2 — Candidate theorems

Notation: $M(x)=f_y(x)-\max_{j\neq y}f_j(x)$ is the (signed) margin function; $\nabla M$ its input
gradient; $L$ the relevant Lipschitz/sensitivity constant; $r_2$ the $\ell_2$ robust radius; $r_2\ge M/\|\nabla M\|$ to first order.

### (A) Capacity ceiling on the coupling — *specialise Bubeck–Sellke to $\eta/L$*

**Statement (proposed Theorem A).** Let $\mu$ on $\mathbb R^d$ be $c$-isoperimetric, $x_1,\dots,x_n$
i.i.d.\ $\sim\mu$ with **random** labels $y_i\in\{\pm1\}$ ($\sigma^2=1$). Let $g_w$ be a binary score from
a $p$-parameter class with $\|w\|\le\mathrm{poly}(n,d)$, $J$-Lipschitz in $w$. If $g_w$ separates the data
with **uniform logit margin** $y_i g_w(x_i)\ge\eta$ for all $i$ and has global $\ell_2$-Lipschitz constant
$L=\mathrm{Lip}(g_w)$, then with high probability
$$\frac{\eta}{L}\ \le\ \tilde O\!\Big(\sqrt{\tfrac{p}{nd}}\Big),\qquad\text{equivalently}\quad r_2^{\mathrm{cert}}=\frac{\eta}{L}\le\tilde O\!\Big(\sqrt{\tfrac{p}{nd}}\Big).$$
So a *certified* robust radius of order $1$ forces $p\gtrsim nd$: the coupling (you cannot have large $\eta$
and small $L$ at fixed capacity) is a necessary consequence of bounded capacity.

**Proof strategy (the clip reduction — clean).** Define $h_w:=\mathrm{clip}(g_w/\eta,-1,1)$. Then
(i) $h_w(x_i)=y_i$ exactly, since $y_ig_w(x_i)\ge\eta\Rightarrow g_w(x_i)/\eta$ is on the correct side of
$\pm1$; so $\tfrac1n\sum(h_w(x_i)-y_i)^2=0\le\sigma^2-\varepsilon$ with $\varepsilon=\sigma^2=1$.
(ii) clip is $1$-Lipschitz, so $\mathrm{Lip}(h_w)\le \mathrm{Lip}(g_w)/\eta=L/\eta$, and $w\mapsto h_w$ is
$(J/\eta)$-Lipschitz with the same $p$ and weight bound. (iii) Apply BS21 Theorem 1 to $h_w$:
$\mathrm{Lip}(h_w)\ge\tilde\Omega(\sqrt{nd/p})$. Chain: $L/\eta\ge\mathrm{Lip}(h_w)\ge\tilde\Omega(\sqrt{nd/p})$,
i.e.\ $\eta/L\le\tilde O(\sqrt{p/nd})$. $\square$

**New vs subsumed.** It is a **corollary** of BS21; the only new content is the $\eta/L$ / certified-radius
reformulation and the explicit clip reduction. Honest: not a deep new theorem, but a correct, citable,
useful repackaging that names the capacity wall behind our coupling.

**Main risk / obstacle.** *Two real gaps.* (1) **Global vs local.** It bounds $\eta/\mathrm{Lip}$, the
*certified* ratio; our empirical $\eta/L$ uses the *local* $\|\nabla M(x_i)\|\le\mathrm{Lip}$, so the
empirical ratio can exceed the bound. The theorem explains the *certified* radius and the capacity wall,
not the measured local coupling. (2) **Label noise required.** $\sigma^2>0$ is essential; clean $r$-separated
data escapes it. So Theorem A bites in the memorisation / hard-example regime (where AT lives) but is not a
statement about clean interpolation. Both must be stated; do **not** claim A explains the $+0.5$ Spearman.

**Provability rating: CLEAN (the corollary) but PARTLY SUBSUMED + CAVEATED.** Order-of-magnitude sanity:
$p\approx1.1\times10^7$ (PRN-18), $n d\approx 5\times10^4\cdot3072\approx1.5\times10^8\Rightarrow\sqrt{p/nd}\approx0.27$,
the right ballpark for an AT model's certified $\ell_2$ radius — a plausibility note, not a fit.

### (B) Impossibility of first-order decoupling for homogeneous nets — *the recommended core*

**Statement (proposed Theorem B).** Let $f$ be a bias-free network with positively-homogeneous degree-1
activations (ReLU, leaky-ReLU, abs, maxout): $f(cx)=cf(x)$ for $c>0$. Then $M=f_y-\max_{j\neq y}f_j$ is also
degree-1 positively homogeneous, and at every differentiability point $x$:
$$\langle\nabla M(x),x\rangle=M(x)\quad\text{(Euler)}\ \Longrightarrow\ \|\nabla M(x)\|_2\ \ge\ \frac{M(x)}{\|x\|_2}\ \Longrightarrow\ \frac{M(x)}{\|\nabla M(x)\|_2}\le\|x\|_2 .$$
For the dual-norm (threat-matched) form, $\|\nabla M(x)\|_1\ge M(x)/\|x\|_\infty$. **Consequences:**
(i) the first-order robust radius is capped by the input norm, $\eta/L\le\sup_i\|x_i\|$, independent of
training; (ii) across samples of comparable norm $\|x_i\|\approx R$, $\|\nabla M(x_i)\|\ge M(x_i)/R$ is a
deterministic **lower envelope** forcing larger margin $\Rightarrow$ larger gradient (the $+$ coupling);
(iii) any objective that drives $\|\nabla M\|$ below $M/\|x\|$ must drive $M$ down in lockstep — exactly the
self-limiting failure of experiment 2(a).

**Proof strategy (clean, 3 lines).** $f_y$ and $\max_{j\neq y}f_j$ are degree-1 positively homogeneous
(max of homogeneous is homogeneous), so $M$ is. Euler's identity for degree-1 positively homogeneous,
locally-Lipschitz $M$ gives $\langle\nabla M(x),x\rangle=M(x)$ a.e. Cauchy–Schwarz (resp. Hölder) gives
$M(x)\le\|\nabla M(x)\|_2\|x\|_2$ (resp. $\|\nabla M\|_1\|x\|_\infty$). Rearranged, done. $\square$

**New vs subsumed.** The identity is elementary and used in the margin-maximisation literature
(Lyu–Li 1906.05890; Vardi–Shamir 2110.02732) and underlies Vardi 2202.04347's non-robustness. What is
**not** in the literature is its use as the *explanation of the AT margin–sensitivity coupling and the
self-limiting $\eta/L$ ceiling*, i.e. a *no-go for first-order margin/sensitivity decoupling in homogeneous
nets*. That framing + the tie to our exp 2(a) is genuinely new and citable.

**Main risk / obstacle.** (1) **Bias-free + homogeneous only.** With biases or smooth activations
(SiLU/GELU) Euler fails exactly, so B does **not** by itself explain the architecture-independence in
finding (1). Mitigation: for $\|x\|$ large the biased-ReLU gradient $\approx$ the homogeneous one (standard
fact; cf. search hit on bias-free approximation), and any net is locally well-approximated by its
homogeneous tangent at $x$; state B as exact for homogeneous and approximate otherwise, and let A carry the
architecture-independence. (2) Euler is a.e. (ReLU non-differentiable on a measure-zero set) — harmless,
use the locally-Lipschitz version. (3) It is a *lower bound* (envelope), not a correlation; it predicts the
*sign and a floor* of the coupling, not the exact $\rho=+0.5$. Be precise about that.

**Provability rating: CLEAN.** Unconditional, exact, assumption-light, directly proves finding (1)
pointwise for ReLU and explains experiment 2(a). This is the recommended core.

### (C) Degeneracy of ratio-maximisation — *the clean lemma killing experiment 2(b)*

**Statement (proposed Lemma C).** For any differentiable classifier, the per-sample robust-radius proxy
$\rho(f;x):=M_f(x)/\|\nabla M_f(x)\|$ is **invariant to positive rescaling**: $\rho(cf;x)=\rho(f;x)$ for all
$c>0$ (numerator and denominator both scale by $c$). Hence:
(i) the population objective $R(f)=\mathbb E_x[\rho(f;x)]$ (and the penalty
$P(f)=\mathbb E_x[\|\nabla M_f\|/M_f]$ over correctly classified points) is **scale-free**: it carries zero
gradient toward increasing absolute margin/confidence — the one quantity a fixed-$\varepsilon$ threat model
needs. (ii) $\inf_f P(f)=0$, approached by any sequence $f_t\to$ constant ($\nabla M\to0$); because $P$ is
scale-invariant, confidence cannot lower $P$, so the *only* descent direction for $P$ is toward local
constancy ($\nabla M\to0$), i.e. the **constant classifier** (chance accuracy) is the degenerate global
optimum. Adding $P$ to cross-entropy with weight $\lambda$ therefore has a penalty-dominated optimum at
$M\to0,\ \|\nabla M\|\to0$ — exactly experiment 2(b).

**Proof strategy (clean).** Homogeneity of $M\mapsto cM$ gives (i) immediately. For (ii): a constant $f$
has $\nabla M\equiv0$, so $P=0$; $P\ge0$ always; scale-invariance means $P(cf)=P(f)$, so the sublevel sets
of $P$ are scale-invariant cones and the infimum is attained only by flattening $\nabla M\to0$. $\square$

**New vs subsumed.** The constant-function degeneracy is **already noted by Tsuzuku (1802.04034)** and our
paper cites it. Novelty is only the explicit *scale-invariance* reason and the exact tie to 2(b).

**Main risk / obstacle.** Near-trivial; a referee will call it folklore. It is a *lemma*, not a headline.
Sign subtlety: state $P$ over correctly-classified points (or use $|M|$) to avoid the $M<0$ pathology.

**Provability rating: CLEAN but NEAR-TRIVIAL.** Use as the rigorous explanation of 2(b), not as the
contribution.

### (D) Architecture-independence via isoperimetry — *not a separate theorem*

**Claim.** The coupling's architecture-independence (ReLU/SiLU/GELU) follows because the BS21 bound
(candidate A) depends only on $(p, J, \|w\|, \mu)$ and **not on the activation** — any smoothly-parametrised
class obeys the same $\eta/L\le\tilde O(\sqrt{p/nd})$ ceiling. Separately, the isoperimetric/Poincaré
average-gradient lower bound (§1.5) gives an activation-free $\mathbb E\|\nabla\|$ floor.

**Assessment.** This is a **corollary/reading of A**, not a new theorem, and it inherits A's global-vs-local
and noise caveats. The isoperimetric average-gradient bound is real but blunt (bounds the average, not the
per-sample coupling). Do not promote D to a theorem; use it as one sentence of interpretation under A.
**Provability: SUBSUMED.**

---

## Part 3 — Recommendation and full proof sketch

**Recommended deliverable: prove B and C; state A as the capacity context.** The single strongest *clean,
correct, non-trivial, not-subsumed* theorem is **B** (the homogeneity self-limiting bound). It is the only
candidate that (i) is unconditionally provable, (ii) directly converts our headline finding (1) into a
pointwise theorem and explains experiment 2(a), (iii) matches the *local* empirical object $\|\nabla M(x_i)\|$,
and (iv) has a defensible new framing not in the literature. C is a one-paragraph lemma that closes 2(b).
A is the more valuable capacity story but is a caveated corollary — present it honestly as "the certified
ratio and the capacity wall," never as the local coupling.

### Full proof sketch — Theorem B (homogeneous self-limiting bound)

*Setup.* $f:\mathbb R^d\to\mathbb R^k$, bias-free, all activations positively homogeneous of degree 1
($\sigma(ct)=c\sigma(t)$, $c>0$): then each logit $f_j(cx)=cf_j(x)$ for $c>0$ (induction over layers, since
each affine-without-bias and each activation preserves degree-1 positive homogeneity). For fixed label $y$,
$\max_{j\neq y}f_j$ is a max of degree-1 positively-homogeneous functions, hence degree-1 positively
homogeneous; so $M=f_y-\max_{j\neq y}f_j$ is degree-1 positively homogeneous and locally Lipschitz.

*Step 1 (Euler).* For a degree-1 positively homogeneous, locally Lipschitz $M$, at every differentiability
point $x$, $\;\langle\nabla M(x),x\rangle = M(x)$. (Differentiate $M(cx)=cM(x)$ in $c$ at $c=1$:
$\langle\nabla M(x),x\rangle=M(x)$. Holds a.e. by Rademacher; on the ReLU non-smooth set use a Clarke
subgradient $v$ with $\langle v,x\rangle=M(x)$.)

*Step 2 (Cauchy–Schwarz / Hölder).* $M(x)=\langle\nabla M(x),x\rangle\le\|\nabla M(x)\|_2\,\|x\|_2$, hence
$\|\nabla M(x)\|_2\ge M(x)/\|x\|_2$ and $M(x)/\|\nabla M(x)\|_2\le\|x\|_2$. The threat-matched version uses
$\langle\nabla M,x\rangle\le\|\nabla M\|_1\|x\|_\infty$ (so $\ell_\infty$ threat $\to\ell_1$ gradient, the
$q$ used in the paper).

*Step 3 (coupling).* Restrict to data; normalise (or note CIFAR norms cluster) so $\|x_i\|_2\in[R_{\min},R_{\max}]$.
Then $\|\nabla M(x_i)\|_2\ge M(x_i)/R_{\max}$: the scatter of $(M,\|\nabla M\|)$ lies above the line of slope
$1/R_{\max}$, a deterministic positive lower envelope. Thus, for positive-margin (correctly classified,
robust-trained) points, margin and gradient norm are positively associated; the association is *forced*, not
optimisation-dependent. (To predict $\rho\approx+0.5$ rather than merely its sign, one would model where in
the feasible cone the trained net sits — out of scope for the theorem; the theorem delivers the *necessary*
lower envelope and the ceiling.)

*Step 4 (exp 2(a)).* The certified/first-order ratio obeys $\eta/L\le R_{\max}$ regardless of any
$\|\nabla M\|$ penalty: pushing $\|\nabla M(x_i)\|$ below $M(x_i)/\|x_i\|$ is infeasible, so the penalty can
only reduce $\|\nabla M\|$ by simultaneously reducing $M$ (the lockstep), reproducing "$\eta/L$ rises while
robustness does not, because $M$ falls" exactly as measured ($\eta$ $1.58\!\to\!1.03$ in `fig:tmreg`).

*Honest scope to write into the paper.* Exact for bias-free homogeneous (ReLU family); approximate for
biased/smooth nets via the large-$\|x\|$ and local-tangent approximations; it is a one-sided envelope (sign
+ ceiling), and the architecture-independence of the *magnitude* is carried by A's universality, not by B.

### Full proof sketch — Lemma C (ratio degeneracy)

As in Part 2(C): scale-invariance $\rho(cf)=\rho(f)$ (one line), then $\inf P=0$ attained only in the
$\nabla M\to0$ (constant) limit, hence the penalty-dominated optimum of $\mathrm{CE}+\lambda P$ is the
constant classifier; combined with B (which forbids lowering $\|\nabla M\|$ without lowering $M$), the two
failed experiments are *both* theorems: 2(a) by B, 2(b) by C.

### Optional reach — Theorem A as the capacity section

State A exactly as in Part 2(A) with the clip-reduction proof, *prefaced* by its two caveats (global
Lipschitz; $\sigma^2>0$ memorisation regime), and use Wu–Huang–Zhang (2202.11592) to soften the
isoperimetry assumption to a distribution-free $\tilde\Omega(n^{1/d})$ rate. Frame: "B is the local,
unconditional mechanism; A is the global, capacity-theoretic wall it sits under; together they say the
self-limiting coupling is enforced both pointwise (homogeneity) and globally (capacity), so $\eta/L$ is a
diagnostic, not a trainable lever." Do **not** claim A proves the measured local coupling.

### Brutal-honesty ledger

- **B**: correct, clean, new-as-framing, but *homogeneous-only* and a *one-sided envelope*. Strongest single
  theorem. Write it.
- **C**: correct, clean, but *folklore* (Tsuzuku already flags the degeneracy). A lemma, not a headline.
- **A**: correct as a *corollary*, *valuable* framing, but *subsumed by BS21*, bounds the *global/certified*
  ratio (not the local empirical one), and needs *label noise*. Present honestly or a referee will catch the
  global-vs-local sleight of hand.
- **D**: not a theorem; a reading of A. Do not promote.
- **Avoid**: claiming a *new local capacity law* (no clean one exists); claiming A explains the $+0.5$
  Spearman; re-deriving the bracket/lazy theorem (already in the paper); reopening the Min–Vidal
  optimization conjecture (open, and our prior attempt was retracted).

---

## References (arXiv ids; all read to statement)

Bubeck & Sellke, universal law of robustness — 2105.12806 · Bubeck, Li, Nagaraj, two-layer law — 2009.14444
· Wu, Huang, Zhang, law beyond isoperimetry — 2202.11592 · "Does Order Matter" — 2602.20971 · Feldman,
memorisation — 2008.03703 · Simon-Gabriel, first-order vulnerability — 1802.01421 · Tsuzuku, Lipschitz-Margin
— 1802.04034 · Hein & Andriushchenko, cross-Lipschitz — 1705.08475 · Lyu & Li, homogeneous max-margin —
1906.05890 · Soudry, implicit bias — 1710.10345 · Vardi, Yehudai, Shamir, non-robust convergence — 2202.04347
· Vardi & Shamir, margin maximisation — 2110.02732 · Frei, Vardi, Bartlett, Srebro, double-edged sword —
COLT 2023 (PMLR v195) · Min & Vidal, implicit bias & robustness — 2405.15942 · Yang et al., $r$-separation —
2003.02460 · Elesedy & Zaidi, provably invariant — Elesedy 2021 (orbit-projection) · Bietti & Mairal, NTK
inductive bias — 1905.12173.
