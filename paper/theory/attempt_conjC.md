# Attack on Conjecture C (local, noise-free capacity ceiling)

**Target.** Conjecture C of `coupling_conjectures.tex`: under the Bubeck–Sellke data
assumptions but **without** label noise, and with $L$ the **local** expected
margin-gradient norm at the data ($L=\mathbb E\,\|\nabla M(x)\|$) rather than the
**global** Lipschitz constant, a bound
$$\eta/L \le \tilde O\!\big(\sqrt{p/(nd)}\big)$$
still holds (up to logs).

**One-line verdict.** **REFUTED as stated**, on two independent grounds, each of
which is asserted *firsthand by Bubeck and Sellke themselves*. (1) The
noise-free conjunct is false: without noise an $O(1)$-Lipschitz function
interpolates *any* labels (Kirszbraun / radial-bump construction), so even the
*global* bound collapses to $\eta/L=\Omega(1)$. (2) The global$\to$local-average
replacement is false: the expected (squared) gradient norm can be made
*exponentially small* on an interpolator; "it is crucial in the law of robustness
to consider the Lipschitz constant, i.e. the supremum of the norm of the
gradient." A genuinely-true restricted statement survives only by (i) **keeping
noise** and (ii) adding a **no-flat-spot / gradient-regularity** bridge
$\sup_x\|\nabla M\|\le C\cdot\mathbb E_{\rm data}\|\nabla M\|$ that ties the
average to the supremum — and that bridge is itself an implicit-bias statement
(it reduces C to Conjectures A/B, not to representation theory). Details below.

---

## 1. Bubeck–Sellke: exact statement, assumptions, and the two load-bearing steps

**Source.** S. Bubeck, M. Sellke, *A Universal Law of Robustness via
Isoperimetry*, NeurIPS 2021, **arXiv:2105.12806**. Read firsthand (NeurIPS/OpenReview
PDF `z71OSKqTFh7` and arXiv). Companion lower bounds: Y. Wu, H. Huang, H. Zhang,
*A Law of Robustness beyond Isoperimetry*, ICML 2023, **arXiv:2202.11592**; and
S. Bubeck, Y. Li, D. Nagaraj, *A law of robustness for two-layer neural
networks*, COLT 2021, **arXiv:2009.14444**.

### 1.1 The main theorem (verbatim, informal version = their Theorem 1)

> **Theorem 1 (Informal version of Theorem 3).** Let $\mathcal F$ be a class of
> functions from $\mathbb R^d\to\mathbb R$ and let $(x_i,y_i)_{i=1}^n$ be i.i.d.
> input–output pairs in $\mathbb R^d\times[-1,1]$. Assume that:
> 1. $\mathcal F$ admits a Lipschitz parametrization by $p$ real parameters, each
>    of size at most $\mathrm{poly}(n,d)$.
> 2. The distribution $\mu$ of the covariates $x_i$ satisfies isoperimetry (or is
>    a mixture thereof).
> 3. The expected conditional variance of the output (i.e. the "noise level") is
>    strictly positive, denoted $\sigma^2:=\mathbb E^\mu[\mathrm{Var}[y\mid x]]>0$.
>
> Then, with high probability over the sampling of the data, one has
> simultaneously for all $f\in\mathcal F$:
> $$\frac1n\sum_{i=1}^n (f(x_i)-y_i)^2 \le \sigma^2-\epsilon \;\Rightarrow\;
> \mathrm{Lip}(f)\ \ge\ \tilde\Omega\!\Big(\epsilon\sqrt{\tfrac{nd}{p}}\Big).$$

The conclusion bounds $\mathrm{Lip}(f)$, the **global** Lipschitz constant.
Isoperimetry is used in the precise normalized sense (their Definition 1.1 /
2.8): $\mu$ is $c$-isoperimetric if for every $L$-Lipschitz $f$ and all $t\ge0$,
$$\Pr[\,|f(x)-\mathbb E f|\ge t\,]\le 2\exp\!\big(-dt^2/(2cL^2)\big),$$
equivalently $f(x)$ is sub-Gaussian with parameter $L\sqrt{c/d}$ (the $1/\sqrt d$
is the whole point). Examples: $\mathcal N(0,\tfrac1d I)$, uniform on the sphere/
hypercube of diameter 1, log-concave measures, manifolds of positive Ricci
curvature.

The companion lower bounds keep both features. Wu–Huang–Zhang (arXiv:2202.11592)
remove isoperimetry (Thm 3.4: $\mathrm{Lip}(f)\ge\Omega(\epsilon\sqrt{n/p})$) and
even the parametrization (Thm 3.9: $\mathrm{Lip}(f)\ge\Omega(\epsilon\,n^{1/d})$),
but **every** one of their theorems still bounds the *global* $\mathrm{Lip}(f)$
and still assumes $\sigma^2=\mathbb E[\mathrm{Var}[y\mid x]]>0$. Bubeck–Li–Nagaraj
(arXiv:2009.14444) is the two-layer original: Conjecture 1 there is
$\mathrm{Lip}_{\mathbb S^{d-1}}(f)\ge c\sqrt{n/k}$ for $k$-neuron nets fitting
**random $\pm1$ labels** (random labels independent of $x$ are exactly the
maximal-noise case $\sigma^2=1$); they prove it only for a spectral-norm proxy
$L\|a\|\|W\|_{\rm op}\ge\sqrt{n/k}$, in the regime $n\approx d$, and for
polynomial activations — again all about a *global* steepness measure with noise.

### 1.2 Load-bearing step (a): the bound is on the GLOBAL Lipschitz constant

The mechanism. Fix one $L$-Lipschitz $f$. Isoperimetry says $f(x)$ is sub-Gaussian
with parameter $L\sqrt{c/d}$. Their finite-class core (Proposition 1.2 + Theorem 2)
then shows that for a class of $N$ functions, all $L$-Lipschitz, the probability
that *some* member fits below the noise level is at most
$$\exp\!\Big(\log N-\tfrac{nd}{L^2}\Big),$$
(their own one-paragraph summary: "isoperimetry implies that *either* the 0-level
set of $f$ *or* the 1-level set of $f$ must have probability smaller than
$\exp(-nd/\mathrm{Lip}(f)^2)$ ... Thus the probability that $f$ fits all the $n$
points is at most $\exp(-nd/\mathrm{Lip}(f)^2)$"). With $\log N=\tilde O(p)$ from a
covering of the $p$-parameter class, fitting forces $L\gtrsim\sqrt{nd/p}$.

The isoperimetry inequality is a statement about the fluctuation of $f$ over the
**whole** measure $\mu$, and it is driven by the **global** Lipschitz constant
$L=\sup_x\|\nabla f(x)\|$. It says the function must be steep *somewhere*; it says
nothing about $\|\nabla f\|$ *at the data points*. This is exactly the seam
Conjecture C tries to exploit, and the authors close it explicitly:

> "Classical lower bounds on the gradient of a function include Poincaré type
> inequalities, but they are of a qualitatively different nature compared to the
> law of robustness lower bound. We recall that a measure $\mu$ on $\mathbb R^d$
> satisfies a Poincaré inequality if for any function $f$, one has
> $\mathbb E^\mu[\|\nabla f\|^2]\ge C\cdot\mathrm{Var}(f)$ (for some constant
> $C>0$). **In our context, such a lower bound for an interpolating function $f$
> has essentially no consequence since the variance $f$ could be exponentially
> small. In fact this is tight, as one easily use[s] similar constructions to
> those in [BLN21] to show that one can interpolate with an exponentially small
> expected norm squared of the gradient (in particular it is crucial in the law
> of robustness to consider the Lipschitz constant, i.e. the supremum of the norm
> of the gradient).**" — Bubeck–Sellke (arXiv:2105.12806), §1.2.

This is a direct, firsthand refutation of the *population-average* form of
Conjecture C: the expected (squared) gradient norm admits interpolators with an
exponentially small value, so no law of robustness can hold for it. The supremum
(global Lipschitz) is load-bearing and cannot be downgraded to an average.

(They also note the converse refinement: under *only* a Poincaré inequality on
$\mu$ one still gets a weaker law — they cite a $\mathrm{Lip}\gtrsim n\sqrt d/p$
form via the concentration result of Bobkov–Ledoux — but this is again a bound on
the global $\mathrm{Lip}$, not on the average gradient.)

### 1.3 Load-bearing step (b): label noise $\sigma^2>0$ is necessary

The noise enters the proof as the irreducible variance the interpolator must
*absorb*. In the finite-class bound (their Theorem 2),
$$\Pr\Big(\exists f\in\mathcal F:\tfrac1n\textstyle\sum_i (y_i-f(x_i))^2\le
\sigma^2-\epsilon\Big)\le 4k\,e^{-n\epsilon^2/8^3}+2\exp\!\Big(\log|\mathcal F|
-\tfrac{\epsilon^2 nd}{9^4 L^2}\Big),$$
the right-hand exponent carries the factor $\epsilon^2/L^2$ where $\epsilon$ is
how far *below* the noise floor $\sigma^2$ one fits. Lemma 2.1 makes the
mechanism explicit: writing $g(x)=\mathbb E[y\mid x]$ and $z_i=y_i-g(x_i)$,
fitting below $\sigma^2$ *forces a correlation* $\tfrac1{\sqrt n}\sum_i f(x_i)z_i
\ge\epsilon/4$ with the **noise component** $z_i$ — and a low-complexity,
concentrated $f$ cannot correlate with fresh noise. If $\sigma^2=0$ there is no
$z_i$ to chase, $\epsilon$ collapses, and the bound is vacuous. The authors state
this necessity twice:

> "From a theoretical point of view, this noise assumption is necessary for
> otherwise there could exist a smooth classifier with perfect accuracy in
> $\mathcal F$, defeating the point of any lower bound on the size of
> $\mathcal F$." — §1.1.

and, crucially for Conjecture C, they tell us precisely what a noise-free law
would require — *not* representation theory but learning dynamics:

> "We believe that versions of the law of robustness might hold without noise;
> these would need to go beyond representational power and consider the
> **dynamics of learning algorithms**." — §1.1.

The explicit noise-free interpolator is their Remark 1.1 (verbatim, abridged):

> "For the distributions $\mu$ we have in mind, for instance uniform on the unit
> sphere, there exists with high probability some $O(1)$-Lipschitz function
> $f:\mathbb R^d\to\mathbb R$ satisfying $f(x_i)=y_i$ for all $i$. Indeed, with
> probability $1-e^{-\Omega(d)}$ we have $\|x_i-x_j\|\ge1$ for all $1\le i\ne
> j\le n$ so long as $n\le\mathrm{poly}(d)$. In this case we may apply the
> Kirszbraun extension theorem to find a suitable $f$ regardless of the labels
> $y_i$. More explicitly we may fix a smooth bump function $g:\mathbb R^+\to
> \mathbb R$ with $g(0)=1$ and $g(x)=0$ for $x\ge1$, and then interpolate using
> the sum of radial basis functions $f(x)=\sum_{i=1}^n g(\|x-x_i\|)\,y_i$. In
> fact this construction requires only $p=n(d+1)$ parameters."

This single object refutes *both* axes of Conjecture C simultaneously, as shown
next.

---

## 2. The local-replacement attempt (sub-question (a))

**Goal.** Replace $\sup_x\|\nabla M(x)\|$ by $L=\mathbb E_{\rm data}\|\nabla M(x)\|$.

### 2.1 The obstruction is real and the authors already exhibit it

Two regimes of the counterexample, both clean.

**(i) Population-average.** Bubeck–Sellke §1.2 (quoted above): there exist
interpolators with $\mathbb E^\mu[\|\nabla f\|^2]$ *exponentially small*. Since
$\mathbb E\|\nabla f\|\le(\mathbb E\|\nabla f\|^2)^{1/2}$ by Cauchy–Schwarz, the
expected-norm version $L=\mathbb E\|\nabla M\|$ used in the conjecture is *also*
exponentially small. Mechanism: in high dimension the steep transition region can
be confined to a set of exponentially small $\mu$-measure, so the average gradient
sees almost none of it while the supremum (and the interpolation) is unaffected.
This kills the population-average form outright.

**(ii) Data-average, evaluated at the $n$ training points.** Use Remark 1.1's
radial-bump interpolator $f(x)=\sum_i g(\|x-x_i\|)y_i$ with $g$ *smooth* and
peaked at $0$ ($g(0)=1,\ g'(0)=0$). With separation $\|x_i-x_j\|\ge1$ and bump
support radius $1$, at each data point only the local bump is active, so
$$f(x_i)=y_i,\qquad \nabla f(x_i)=g'(0)\,\widehat{(x-x_i)}\big|_{x=x_i}=0 .$$
Hence the margin is $\Theta(1)$ while $L=\tfrac1n\sum_i\|\nabla f(x_i)\|=0$, i.e.
$\eta/L=\infty$ — an infinite violation of *any* finite ceiling. This works for
arbitrary labels (noisy or not), needs $n\le\mathrm{poly}(d)$, and costs
$p=n(d+1)$ parameters.

### 2.2 Honest accounting of where the counterexample bites, and the one gap

The data-average counterexample of §2.1(ii) lives at $p\approx nd$, where the
*global* bound $\sqrt{nd/p}\approx 1$ is itself non-binding. So a fair skeptic asks:
in the regime that the global law actually bites, $p\ll nd$ (so
$\sqrt{nd/p}\gg1$), can the **average over the $n$ training points** be driven
below $\sqrt{nd/p}$?

Forcing $\nabla f(x_i)=0$ ("a flat spot") is $d$ scalar constraints per point;
fitting the value $f(x_i)=y_i$ is one more. Producing flat spots at all $n$ points
is $n(d+1)$ generic constraints and needs $p\gtrsim nd$ degrees of freedom. With
$p\ll nd$ one can flatten at most $\sim p/d$ of the points; the remaining
$n-p/d=n(1-p/(nd))\approx n$ points keep gradient of order the global scale
$\sqrt{nd/p}$, so the *training-point average* stays
$$L=\tfrac1n\sum_i\|\nabla f(x_i)\|\ \gtrsim\ \big(1-\tfrac{p}{nd}\big)\sqrt{nd/p}
\ \approx\ \sqrt{nd/p}\qquad(p\ll nd).$$
So the explicit spike counterexample does **not** refute the data-average form in
the $p\ll nd$ regime. This is the single niche where a true local statement could
in principle live (see §4). It is *not* delivered by Bubeck–Sellke — their proof
bounds the supremum, never the average — and it still needs the noise of §3.

### 2.3 Can a regularity assumption rescue the general local bound? No (it self-destructs)

The natural fix is a curvature bound. If $\|\nabla^2 f\|_{\rm op}\le\beta$
everywhere, then $\|\nabla f\|$ is $\beta$-Lipschitz, so by isoperimetry
$\|\nabla f(x)\|$ concentrates around its mean and
$$\sup_x\|\nabla f\|\ \le\ \mathbb E_\mu\|\nabla f\|+O\big(\beta\cdot
\mathrm{diam}(\mathrm{supp}\,\mu)\big).$$
Plugging into Bubeck–Sellke gives $L=\mathbb E\|\nabla f\|\ge
\tilde\Omega(\sigma\sqrt{nd/p})-O(\beta D)$, a real bound **iff**
$\beta D\lesssim\sigma\sqrt{nd/p}$. But fitting $n$ noisy values across data at
inter-point scale $\delta$ requires gradients $\sim\sigma/\delta$ and curvature
$\beta\sim(\sigma/\delta)/\delta$, so $\beta D\sim\sigma\sqrt{nd/p}\cdot(D/\delta)
\gtrsim\sigma\sqrt{nd/p}$: the correction is of the *same order* as the signal.
The low-curvature regime in which $\mathrm{average}\approx\mathrm{sup}$ is exactly
the near-linear regime in which the function *cannot* fit $n>d+1$ noisy points, so
the lower bound is vacuous there. **The two requirements — "average controls the
sup" and "a nontrivial law-of-robustness lower bound" — are in direct conflict.**
This is strong structural evidence that no *unconditional* curvature assumption
rescues the local average; the only thing that can is an assumption directly on the
realized solution (§4).

### 2.4 The homogeneity floor (from `coupling_conjectures.tex` Thm 1) is far too weak to rescue C

For bias-free, $1$-homogeneous nets the paper's own Euler identity gives the
*per-point lower* bound $\|\nabla M(x)\|_2\ge M(x)/\|x\|_2$, hence
$L\ge\mathbb E[M/\|x\|]\ge\eta/\sup_i\|x_i\|$ and $\eta/L\le\sup_i\|x_i\|$. This
rules out the most extreme spike ($L=0$) **for that subclass** — good to note —
but it only caps $\eta/L\lesssim\|x\|_2\sim\sqrt d$ (unit-variance coordinates),
which is enormously weaker than the conjectured $\sqrt{p/(nd)}$. The floor neither
proves nor saves C; it leaves a $\sqrt d$-vs-$\sqrt{p/(nd)}$ gap and applies only
to bias-free exactly-homogeneous nets (not the bias+BN models in the experiments,
cf. (W3) of the note).

**Verdict on (a):** the global$\to$local-*average* replacement is **false** in
general (population-average: firsthand; data-average at $p\gtrsim nd$: explicit),
and cannot be rescued by any curvature/regularity assumption that is compatible
with fitting noise. It is *open but not refuted* only in the narrow
noisy/$p\ll nd$/training-point-average niche, where it would require a new
average-not-sup argument.

---

## 3. The noise-removal attempt (sub-question (b))

**Goal.** Drop $\sigma^2>0$; substitute a margin / min-separation /
anti-concentration assumption.

### 3.1 Without noise the bound dies even for the GLOBAL Lipschitz constant

Remark 1.1 settles this directly: for $n\le\mathrm{poly}(d)$ on isoperimetric
data, *any* labeling is interpolated by an $O(1)$-Lipschitz function (Kirszbraun,
or the explicit radial-bump $f$). "Noise-free" means the labels are realizable —
$y_i=g(x_i)$ for some target $g$. If the target is itself an $O(1)$-Lipschitz /
small-network function (the generic meaning of "robust, noise-free task"), then
$g$ interpolates with $\mathrm{Lip}=O(1)$ and few parameters, giving
$\mathrm{Lip}=O(1)$, $L=O(1)=O(\eta)$, hence
$$\eta/L=\Omega(1)\ \gg\ \sqrt{p/(nd)}\quad(p\ll nd).$$
So removing noise breaks the bound by an unbounded factor even for the *global*
constant — before any local weakening. This is precisely the "smooth classifier
with perfect accuracy" the authors flag, and it is why every theorem in the family
(2105.12806 Thm 3; 2202.11592 Thms 3.4, 3.9; 2009.14444 Conj 1) keeps
$\sigma^2>0$ (BLN's "random $\pm1$ labels" *is* the $\sigma^2=1$ case).

### 3.2 Does a min-separation / anti-concentration assumption substitute for noise?

Partially, and only for a *much weaker* bound, and only on the *global* constant.
A pure two-point argument: if two points carry opposite labels (margin $\eta$
each) at distance $\delta$, the value gap $2\eta$ over distance $\delta$ forces
$$\sup_x\|\nabla M\|\ \ge\ \mathrm{Lip}(M)\ \ge\ 2\eta/\delta .$$
This is a real noise-free lower bound, but:
- it bounds the **supremum**, not the average $L$ — the steepness sits on the
  segment *between* the two points, exactly where the data-average does not look
  (§2);
- it gives $\eta/L\le\delta/2$ at best (if average $\approx$ sup), i.e. a
  *separation*-controlled cap, **not** a $\sqrt{p/(nd)}$ capacity cap. To upgrade
  a separation bound to $\sqrt{nd/p}$ one needs *many* mutually-frustrated points
  packed at scale $\delta\sim\sqrt{p/(nd)}$, which is the high-frequency /
  $n\ge\exp(\omega(d))$ "curse of big data" regime (Wu–Huang–Zhang Thm 3.9,
  $\mathrm{Lip}\ge\Omega(n^{1/d})$) — and *that* theorem still assumes
  $\sigma^2>0$. Their tightness construction (Thm 3.11) shows generic separated
  data is interpolated by an $O(n^{1/d})$-Lipschitz function, matching the lower
  bound only because of noise.

The honest reading: "label noise" in these theorems is a stand-in for
*irreducible, $x$-unpredictable label variation that a low-complexity function
cannot absorb*. A min-separation assumption does the opposite of supplying that —
well-separated points are *easy* to interpolate smoothly (Remark 1.1). The only
thing that substitutes for noise is "the target itself demands resolution finer
than $O(1)$-Lipschitz," i.e. a **non-robust target** — which is circular for a
capacity ceiling meant to *explain* non-robustness.

**Verdict on (b):** noise is **not removable**. It can be reframed as
"fit below the $O(1)$-Lipschitz interpolation floor" (= ε-overfitting in the
Bregman/BS sense, arXiv:2405.16639), but a min-separation/margin assumption does
**not** substitute for it; it weakens the conclusion to a separation cap on the
*global* constant, far from $\sqrt{p/(nd)}$.

---

## 4. VERDICT

**Conjecture C is REFUTED as stated** (local average gradient *and* noise-free),
with a precisely delimited PARTIAL true core.

Two independent, firsthand-grounded obstructions:

| Axis of C | Status | Firsthand basis |
|---|---|---|
| "without label noise" | **false** | 2105.12806 Remark 1.1 + §1.1: noise-free ⇒ $O(1)$-Lipschitz interpolation of any labels ⇒ $\eta/L=\Omega(1)$ |
| "$L=$ local/average gradient, not $\sup$" | **false** (general); open in one niche | 2105.12806 §1.2: $\mathbb E\|\nabla f\|^2$ can be exp. small; "crucial to consider … the supremum of the norm of the gradient" |

**Strongest TRUE variant (minimal assumptions).** The currently-provable
statement is Bubeck–Sellke / Wu–Huang–Zhang *unchanged*: with (i) isoperimetric
(or arbitrary, for the $n^{1/d}$ version) covariates, (ii) a $p$-parameter
Lipschitz parametrization, and (iii) **noise** $\sigma^2=\mathbb E[\mathrm{Var}
[y\mid x]]>0$, any below-noise interpolator has
$\sup_x\|\nabla M(x)\|\ge\tilde\Omega(\sigma\sqrt{nd/p})$, i.e. the bound holds for
the **worst-case** local gradient $=$ global Lipschitz constant. To transfer it to
the **measured average** $L=\mathbb E_{\rm data}\|\nabla M\|$ — i.e. to obtain
$\eta/L\le\tilde O(\sqrt{p/(nd)})$ — the *minimal* additional hypothesis is a
**no-flat-spot / gradient-regularity** condition on the realized solution,
$$\boxed{\ \sup_x\|\nabla M(x)\|\ \le\ C\cdot\mathbb E_{\rm data}\|\nabla M(x)\|\ }
\qquad(\text{some }C=O(\mathrm{polylog})),$$
under which the global bound divides through by $C$. Equivalently one may demand
that GD/max-margin training does not place flat extrema at data — but that is
precisely an **implicit-bias** statement, i.e. Conjecture A (the matching upper
envelope at the max-margin solution) and/or Conjecture B. This matches the
authors' own diagnosis that a stronger/noise-free law "would need to go beyond
representational power and consider the dynamics of learning algorithms."

Consequently **C is not provable in isolation**: stripped of noise it is false;
stripped of the implicit-bias bridge it is false. The useful deliverable is the
reduction:
> *Conjecture C (for the trained network) $\equiv$ Bubeck–Sellke (with noise) $+$
> a no-flat-spot bridge $\sup\|\nabla M\|\le C\,\mathbb E_{\rm data}\|\nabla M\|$,
> and that bridge is Conjecture A/B, not a representation-theoretic fact.*

This also *explains the empirical success* of the $\eta/L$ diagnostic without
contradiction: for GD-trained nets the realized solution is generic (no engineered
flat spots), so the bridge holds with a moderate constant — the paper's own
$\|\nabla M\|\approx 26\,M/\|x\|$ (W2) is an empirical estimate of $C$ — and the
$\sqrt{p/(nd)}$ scaling shows through the average. It is a property of the *implicit
bias*, not of the function class, exactly as the verdict requires.

**The single open niche.** The data-average form, *with noise kept*, in the regime
$p\ll nd$, averaged over the $n$ training points, is not refuted by any
construction here (§2.2): producing $n$ flat spots costs $\gtrsim nd$ parameters,
so with $p\ll nd$ at most a $p/(nd)$-fraction of training-point gradients can be
suppressed and the average stays $\approx\sqrt{nd/p}$. Proving a law there would
require a genuinely new "average-not-supremum" argument (bounding
$\frac1n\sum_i\|\nabla f(x_i)\|$ rather than $\sup$) and would *still* need
$\sigma^2>0$. This is the only honest target for a *new* theorem; it is strictly
weaker than C (it abandons "noise-free") and is not what Bubeck–Sellke prove.

---

## 5. Adversarial self-review

**Did I quote real theorems?** Yes. Theorem 1 (informal) and Remark 1.1 are
transcribed from the NeurIPS-2021 paper pages (arXiv:2105.12806); the §1.2
Poincaré passage and the two noise-necessity sentences are quoted from the same
PDF. The Wu–Huang–Zhang theorems (3.4, 3.9, 3.11) and the Bubeck–Li–Nagaraj
conjecture are taken from arXiv:2202.11592 (read page-by-page) and arXiv:2009.14444.
Earlier automated *summaries* hallucinated a nonexistent "Theorem 1.1" and a
spurious "$\epsilon/\sigma$" prefactor; I discarded those and used only text read
directly from the page images. **Caveat I am flagging honestly:** the exact
fraction in the "Poincaré-only weaker law" aside (rendered roughly as
$\mathrm{Lip}\gtrsim n\sqrt d/p$) I could not pin to the digit from the figure; I
use it only qualitatively ("a weaker law on the global constant"), and nothing in
the verdict depends on it.

**Is the noise-free refutation airtight?** The one place it could be challenged is
the meaning of "noise-free." If "noise-free" allowed an *adversarially
high-frequency but deterministic* target (labels = sign of a high-degree
polynomial), a noise-free lower bound could survive. I addressed this in §3.2: that
is a *non-robust target* assumption, which makes the capacity ceiling circular
(it assumes what it should explain). For the intended reading — noise-free = labels
realizable by a smooth/low-complexity function — Remark 1.1 is decisive. I state
this scope explicitly rather than papering over it.

**Is the local refutation airtight?** The population-average refutation is the
authors' own (§1.2) and unconditional. The data-average refutation is explicit but
I was careful **not** to overclaim: it bites cleanly only at $p\gtrsim nd$, and I
gave the parameter-counting reason (§2.2) why it does *not* extend to
$p\ll nd$/training-point averages. I resisted the temptation to call C "fully
refuted" — the niche in §2.2 is genuinely open. The curvature self-destruct
argument (§2.3) is a heuristic scaling argument, not a theorem; I labeled it as
"strong structural evidence," not proof.

**Could C still be true as the authors of the note intend it?** Only if "local"
secretly means "worst-case local" (= global) and "noise-free" is dropped — i.e.
only as Bubeck–Sellke already proved. As a *new* statement (average gradient,
noise-free) it is false. The salvage in §4 is therefore the maximal honest claim:
keep noise, add the no-flat-spot bridge, and observe that the bridge is Conjecture
A/B — so C contributes nothing independent of A/B.

**Bottom line.** PROVE: no. REFUTE: yes, as literally stated (two axes, both
firsthand). PARTIAL: the true theorem is Bubeck–Sellke (global $\sup$-gradient,
with noise); the measured-average ratio inherits $\eta/L\le\tilde O(\sqrt{p/(nd)})$
only under a no-flat-spot/implicit-bias bridge, reducing C to Conjecture A/B and
explaining—rather than proving—the empirical regularity.

---

### Sources (read firsthand)
- S. Bubeck, M. Sellke. *A Universal Law of Robustness via Isoperimetry.*
  NeurIPS 2021. arXiv:2105.12806.
- Y. Wu, H. Huang, H. Zhang. *A Law of Robustness beyond Isoperimetry.*
  ICML 2023. arXiv:2202.11592.
- S. Bubeck, Y. Li, D. Nagaraj. *A law of robustness for two-layer neural
  networks.* COLT 2021. arXiv:2009.14444.
- S. Das, J. Batra, P. Srivastava. *A direct proof of a unified law of robustness
  for Bregman divergence losses.* arXiv:2405.16639 (recasts the BS technique;
  confirms the framing that interpolation = fitting below the conditional-mean
  loss, and the centrality of the global Lipschitz constant).
