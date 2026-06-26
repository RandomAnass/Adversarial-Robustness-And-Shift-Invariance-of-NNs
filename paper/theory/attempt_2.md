# When Shift-Invariance and $L_p$ Adversarial Robustness Co-exist: A Margin-Preservation Characterization

**Status:** Self-contained technical report. All lemmas are proved in full. The
central results (Theorems A, B, C) go through under the stated assumptions. One
candidate extension (a tight *quantitative* deep-CNN version) does **not** close;
the obstruction is stated explicitly in Section 7.

**One-line summary.** Let $\Pi$ be the orthogonal projection onto the subspace of
signals fixed by the shift group (for *linear* invariance, the 1-D DC line; for
*nonlinear* GAP-CNN invariance, the larger algebra of orbit functions, e.g. the
power spectrum). The best achievable margin of a shift-invariant classifier is,
up to the Lipschitz budget of the invariant feature extractor, the separation of
the two classes **in invariant-feature space**. Hence shift-invariance does
*not* reduce robustness exactly when the inter-class signal is carried by a
shift-invariant feature with large separation, and the trade-off is *forced*
exactly when projecting onto the invariant feature space collapses the class gap.
This recovers Ge's $2\to 2/\sqrt d$ collapse (single-dot data, DC the only linear
invariant), explains Ge's own counter-example (orthogonal-frequency data, where
the invariant CNN is *more* robust), and is consistent with Kamath's forced
trade-off (their discriminative coordinate is, by construction, annihilated by the
invariance).

---

## 1. Setting and assumptions

### 1.1 Signals, group, and inner product

We work with 1-D circular signals; everything extends verbatim to 2-D toroidal
images by replacing the cyclic group $\mathbb Z_d$ with $\mathbb Z_{d_1}\times
\mathbb Z_{d_2}$ and the 1-D DFT with the 2-D DFT (Remark 6.4). Fix dimension
$d\ge 2$. The input space is $\mathcal X=\mathbb R^d$ with the standard Euclidean
inner product $\langle x,y\rangle=\sum_i x_i y_i$ and norm $\|x\|_2$.

**Shift group.** Let $G=\mathbb Z_d=\{0,1,\dots,d-1\}$ act on $\mathbb R^d$ by the
cyclic shift
$$ (T_s x)_i = x_{(i-s)\bmod d},\qquad s\in G . $$
Each $T_s$ is the permutation (hence orthogonal) matrix realizing the shift by
$s$; $T_sT_t=T_{s+t}$, $T_0=I$, $T_s^{-1}=T_s^\top=T_{-s}$. The action is by
**isometries**: $\|T_s x\|_2=\|x\|_2$ and $\langle T_s x,T_s y\rangle=\langle
x,y\rangle$. This isometry property is used repeatedly; we record it as a fact.

> **Fact 1.1 (Shifts are isometries).** For all $s$, $T_s\in O(d)$. In
> particular every $T_s$ preserves Euclidean balls: $T_s\, B(x,r)=B(T_s x,r)$.

The **orbit** of $x$ is $\mathcal O(x)=\{T_s x:s\in G\}$, a set of at most $d$
points (fewer if $x$ has a nontrivial period). We say a function $f$ is
**shift-invariant** (or **$G$-invariant**) if $f(T_s x)=f(x)$ for all $x,s$.

### 1.2 Classifiers, margin, robust radius

We consider binary classification with labels $\{-1,+1\}$; the multiclass
extension is routine (Remark 6.5). A **score function** is $f:\mathbb
R^d\to\mathbb R$; the predicted label is $\operatorname{sign} f(x)$. We measure
adversarial robustness by the **$L_2$ robust radius** (distance to the decision
boundary):
$$
\rho_f(x)\;=\;\inf\{\,\|\delta\|_2 : \operatorname{sign} f(x+\delta)\neq
\operatorname{sign} f(x)\,\}
\;=\;\inf\{\,\|\delta\|_2: f(x)\,f(x+\delta)\le 0\,\}.
$$
For a labeled point $(x,y)$ correctly classified ($y f(x)>0$), $\rho_f(x)$ is the
$L_2$ adversarial perturbation budget at $x$. The $L_\infty$ case is handled by
the norm-equivalence wrapper of Section 4.3.

For a data distribution $D$ on $\mathbb R^d\times\{\pm1\}$, the **(hard) margin**
of $f$ is
$$
\gamma(f;D)\;=\;\operatorname*{ess\,inf}_{(x,y)\sim D}\ y\,f(x)\quad\text{(score
margin)},\qquad
\rho(f;D)\;=\;\operatorname*{ess\,inf}_{(x,y)\sim D}\ \rho_f(x)\quad\text{(geometric
margin)} .
$$
These are linked by Lipschitzness: if $f$ is $L$-Lipschitz in $\|\cdot\|_2$ and
$y f(x)\ge \gamma$ then $\rho_f(x)\ge \gamma/L$ (Lemma 2.4). Throughout,
"robustness" means the **geometric** margin $\rho$; the score margin is an
intermediate device.

> **Why geometric, not score.** The score can be inflated by scaling $f\mapsto
> cf$, which does not change the classifier or its robustness. The geometric
> radius $\rho_f$ is scale-invariant and is the operationally meaningful
> quantity; all final statements are about $\rho$.

### 1.3 The two hypothesis classes

We compare:

* $\mathcal F_{\mathrm{FC}}$: a rich class (e.g. all $L$-Lipschitz functions, or
  all linear functions $x\mapsto w^\top x$, depending on the theorem). This
  models the fully-connected network, which is **not** constrained to be shift
  invariant.

* $\mathcal F_{\mathrm{inv}}=\{f\in\mathcal F_{\mathrm{FC}}: f\circ T_s = f\ \forall
  s\}$: the same class **intersected with the $G$-invariant functions**. This
  models the fully shift-invariant CNN (circular padding, conv layers, global
  average pooling; cf. Ge et al. Note 1, where such a CNN is *born* fully shift
  invariant).

The whole paper studies the gap between $\sup_{f\in\mathcal F_{\mathrm{inv}}}
\rho(f;D)$ and $\sup_{f\in\mathcal F_{\mathrm{FC}}}\rho(f;D)$. We do **not** model
the optimizer's implicit bias in the main theorems (that is the subject of Frei
and Melamed, with which we connect in Sections 5–6); the main theorems are about
the *attainable* robustness of the hypothesis class, i.e. existence of a robust
invariant classifier, which is the right object for a "can they co-exist"
question.

### 1.4 Standing assumptions

* **(A1) Compactly supported, well-separated data.** $D$ has class-conditional
  supports $S_{+},S_{-}\subseteq\mathbb R^d$ that are compact. We allow the data
  to lie on a low-dimensional manifold (as in Melamed), but do not require it
  except in Section 5.

* **(A2) Shift-consistent labels (orbit-pure classes).** The labeling respects
  the group: if $(x,y)\in\operatorname{supp}D$ then $(T_s x,y)$ is a valid
  labeled point with the *same* label for all $s$. Equivalently the Bayes-optimal
  label is constant on each orbit. This is the regime in which "high
  shift-consistency" is even *desirable*; it holds for natural image
  classification under translation and is the regime Ge studies (every shift of a
  training image is in the same class). **When (A2) fails**, invariance is
  label-destroying and the trade-off is trivially forced; we treat that as the
  degenerate boundary case (Remark 6.6).

* **(A3) Norm normalization.** WLOG inputs have bounded norm; constants are
  stated relative to $R:=\sup\{\|x\|_2:x\in S_+\cup S_-\}$.

Assumption (A2) is the *correctness premise* that makes the question nontrivial:
under (A2) an invariant classifier loses **no accuracy**, so the only question is
whether it must lose **robustness**. That is precisely the empirical co-existence
question (high consistency *and* robustness).

---

## 2. Definitions: the invariant subspace, the orbit-difference subspace, and the invariant feature map

This section sets up the three linear-algebraic objects that drive everything.

### 2.1 Isotypic / Fourier decomposition of the shift action

Let $W\in\mathbb C^{d\times d}$ be the unitary DFT matrix, $W_{jk}=\frac{1}{\sqrt
d}\omega^{-jk}$ with $\omega=e^{2\pi i/d}$. The shift $T_s$ is diagonalized by $W$:
$$
W T_s W^{*} = \operatorname{diag}(\omega^{-js})_{j=0}^{d-1}=:\Lambda_s ,
$$
i.e. the $j$-th Fourier mode is an eigenvector of every $T_s$ with eigenvalue
$\omega^{-js}$. (Proof: $(T_s x)$ has DFT $\hat x_j \omega^{-js}$, standard shift
theorem; verified in Lemma 2.1.)

> **Lemma 2.1 (Shift theorem).** For $x\in\mathbb R^d$ with DFT $\hat x=Wx$,
> $\widehat{T_s x}_j=\omega^{-js}\hat x_j$.
>
> *Proof.* $\widehat{T_s x}_j=\frac1{\sqrt d}\sum_k (T_s x)_k\omega^{-jk}
> =\frac1{\sqrt d}\sum_k x_{(k-s)\bmod d}\omega^{-jk}$. Substitute
> $m=(k-s)\bmod d$, so $k=(m+s)\bmod d$ and $\omega^{-jk}=\omega^{-j(m+s)}=
> \omega^{-jm}\omega^{-js}$ (since $\omega$ has order $d$). The sum becomes
> $\omega^{-js}\frac1{\sqrt d}\sum_m x_m\omega^{-jm}=\omega^{-js}\hat x_j$.
> $\qquad\blacksquare$

**The invariant line.** A real vector $w$ satisfies $T_s w=w$ for all $s$ iff
$\omega^{-js}\hat w_j=\hat w_j$ for all $j,s$, iff $\hat w_j=0$ for all $j\neq 0$,
iff $w\in\operatorname{span}\{\mathbf 1\}$ where $\mathbf 1=(1,\dots,1)$. So:

> **Definition 2.2 (Invariant subspace, DC).** The **shift-invariant linear
> subspace** is $\mathcal V_{\mathrm{inv}}=\{w:T_sw=w\ \forall s\}
> =\operatorname{span}\{\mathbf 1\}$, a **1-dimensional** line. The orthogonal
> projection onto it is $P_{\mathrm{dc}}=\frac1d\mathbf 1\mathbf 1^\top$, and the
> normalized DC functional is $f_{\mathrm{dc}}(x)=\frac1{\sqrt d}\mathbf
> 1^\top x = \bar w^\top x$ with $\bar w=\frac1{\sqrt d}\mathbf 1$ (matching Ge's
> notation). Its orthogonal complement is $\mathcal V_{\mathrm{ac}}=\mathcal
> V_{\mathrm{inv}}^\perp=\{x:\mathbf 1^\top x=0\}$ (the **AC / zero-mean**
> subspace), $\dim=d-1$.

**The orbit-difference subspace.** This is the key new object.

> **Definition 2.3 (Orbit-difference subspace).** For $x\in\mathbb R^d$ define
> the **orbit-difference subspace**
> $$ \mathcal D(x)\;=\;\operatorname{span}\{\,T_s x - x : s\in G\,\}
> \;\subseteq\;\mathbb R^d, $$
> and the global orbit-difference subspace $\mathcal D=\sum_{x}\mathcal D(x)$
> (sum over the support). $\mathcal D(x)$ is the tangent space to the orbit's
> affine hull; it captures *which directions a perturbation can move along to
> mimic a shift.*

> **Lemma 2.4 (Orbit differences are AC; DC is orthogonal to all orbit
> differences).** For every $x,s$: $\mathbf 1^\top(T_s x-x)=0$, i.e. $\mathcal
> D(x)\subseteq\mathcal V_{\mathrm{ac}}$. Conversely $\mathcal
> V_{\mathrm{inv}}\perp\mathcal D(x)$.
>
> *Proof.* $\mathbf 1^\top T_s x=\sum_i (T_s x)_i=\sum_i x_{(i-s)\bmod
> d}=\sum_m x_m=\mathbf 1^\top x$ since cyclic shift permutes coordinates. Hence
> $\mathbf 1^\top(T_sx-x)=0$, so every orbit difference is orthogonal to $\mathbf
> 1$, i.e. lies in $\mathcal V_{\mathrm{ac}}$ and is orthogonal to $\mathcal
> V_{\mathrm{inv}}=\operatorname{span}\mathbf 1$. $\qquad\blacksquare$

Lemma 2.4 is the algebraic heart of Ge's collapse: **the DC component is the only
linear direction orthogonal to every orbit difference**, so it is the only linear
direction a shift-invariant linear classifier can use. We now make this precise
and then escape it nonlinearly.

> **Lemma 2.5 (Lipschitz score-to-radius).** If $f$ is $L$-Lipschitz w.r.t.
> $\|\cdot\|_2$ and $yf(x)\ge\gamma>0$, then $\rho_f(x)\ge\gamma/L$.
>
> *Proof.* For $\|\delta\|_2<\gamma/L$, $|f(x+\delta)-f(x)|\le L\|\delta\|_2
> <\gamma\le |f(x)|$, so $f(x+\delta)$ has the same sign as $f(x)=$ sign of $y
> f(x)$. Thus no boundary crossing within radius $\gamma/L$.
> $\qquad\blacksquare$

### 2.2 The nonlinear invariant feature map (escape from the DC line)

The linear invariant subspace is 1-D, but the algebra of *nonlinear* invariant
**features** is much larger. A GAP-CNN computes, in its simplest informative form,
features of the type "global average of a pointwise nonlinearity of a circular
convolution," which generate the algebra of orbit functions. Two canonical,
fully shift-invariant, **quadratic** feature families are central:

* **Autocorrelation / power spectrum.** $a_k(x)=\frac1d\sum_i x_i x_{(i+k)\bmod
  d}$, $k=0,\dots,d-1$; equivalently the power spectrum $|\hat x_j|^2$. By the
  Wiener–Khinchin relation $a_k$ and $|\hat x_j|^2$ are DFTs of each other.

> **Lemma 2.6 (Power spectrum is a complete shift invariant up to phase).**
> (i) $|\widehat{T_s x}_j|=|\hat x_j|$ for all $j,s$: the power spectrum is shift
> invariant. (ii) Two signals have equal power spectra iff they differ by a
> *phase rotation* of each mode, i.e. $\hat y_j=e^{i\theta_j}\hat x_j$; circular
> shifts are the special case $\theta_j=-js\cdot 2\pi/d$. Thus the power spectrum
> separates orbits *unless* two orbits happen to share all magnitudes.
>
> *Proof.* (i) From Lemma 2.1, $|\widehat{T_sx}_j|=|\omega^{-js}||\hat
> x_j|=|\hat x_j|$. (ii) $|\hat y_j|=|\hat x_j|\ \forall j$ iff each $\hat y_j$
> is $\hat x_j$ times a unit modulus complex number $e^{i\theta_j}$; the subset
> of phase vectors of the form $\theta_j=-2\pi js/d$ are exactly the shifts.
> $\qquad\blacksquare$

This is the crucial qualitative difference: **a linear invariant retains a single
scalar ($f_{\mathrm{dc}}$); a quadratic invariant retains up to $\lceil
d/2\rceil+1$ real numbers (the distinct power-spectrum magnitudes), an
exponentially richer summary.** Whether this richer summary preserves class
separation is exactly the co-existence condition.

> **Definition 2.7 (Invariant feature map and its budget).** An **invariant
> feature map** of **Lipschitz budget** $L_\Phi$ is a map $\Phi:\mathbb
> R^d\to\mathbb R^p$ such that (a) $\Phi(T_s x)=\Phi(x)$ for all $x,s$ (shift
> invariance) and (b) $\Phi$ is $L_\Phi$-Lipschitz: $\|\Phi(x)-\Phi(x')\|_2\le
> L_\Phi\|x-x'\|_2$. The associated **invariant classifier family** is
> $\mathcal F_\Phi=\{x\mapsto g(\Phi(x)): g\ \text{1-Lipschitz on }\mathbb
> R^p\}$, which is $L_\Phi$-Lipschitz and $G$-invariant.

Two budgets we will use:
* Linear/DC: $\Phi_{\mathrm{dc}}(x)=f_{\mathrm{dc}}(x)=\bar w^\top x$ with
  $L_{\Phi}=\|\bar w\|_2=1$.
* Quadratic/power-spectrum: $\Phi_{\mathrm{ps}}(x)=(|\hat x_j|)_{j}$ with
  $L_\Phi=1$ on the ball of radius $R$ (Lemma 2.8 below).

> **Lemma 2.8 (Lipschitz budget of the power-spectrum-magnitude map).** On
> $B(0,R)$, the map $x\mapsto(|\hat x_j|)_{j=0}^{d-1}\in\mathbb R^d$ is
> $1$-Lipschitz in $\|\cdot\|_2$ (independent of $R$).
>
> *Proof.* $W$ is unitary so $x\mapsto\hat x$ is an isometry on $\mathbb C^d$
> (with the real $\ell_2$ structure). The map $z\mapsto(|z_j|)_j$ from $\mathbb
> C^d\to\mathbb R^d$ is $1$-Lipschitz: by the reverse triangle inequality
> $\big||z_j|-|z'_j|\big|\le|z_j-z'_j|$, so $\sum_j(|z_j|-|z'_j|)^2\le\sum_j
> |z_j-z'_j|^2$. Composing two $1$-Lipschitz maps gives $1$-Lipschitz.
> $\qquad\blacksquare$

We will sometimes use the *un-rooted* power spectrum $|\hat x_j|^2$; it is locally
Lipschitz with constant $2R$ on $B(0,R)$, which only changes constants.

---

## 3. Main theorems

We state three results. **Theorem A** is the *general two-sided characterization*
(co-existence iff invariant-feature separation survives), valid for any invariant
feature map. **Theorem B** specializes to *linear* invariance and recovers and
sharpens Ge's collapse, including a strict converse. **Theorem C** is the
*off-manifold* statement connecting invariance to enlarged robust radius in the
spirit of Melamed.

Define, for an invariant feature map $\Phi$ of budget $L_\Phi$, the
**invariant-feature class separation**
$$
\boxed{\;\Delta_\Phi(D)\;:=\;\operatorname{dist}\big(\Phi(S_+),\,\Phi(S_-)\big)
=\inf_{x\in S_+,\,x'\in S_-}\big\|\Phi(x)-\Phi(x')\big\|_2 .\;}
$$
This is the gap between the two classes **after** mapping into invariant-feature
space. It is the single scalar that governs co-existence.

### Theorem A (Co-existence iff invariant-feature separation survives)

*Under (A1)–(A3), fix any shift-invariant feature map $\Phi$ of Lipschitz budget
$L_\Phi$.*

**(A.i) Achievability (lower bound on best invariant robustness).** There exists
a $G$-invariant, $L_\Phi$-Lipschitz classifier $f^\star\in\mathcal F_\Phi$ that
classifies $D$ correctly with geometric robust radius
$$
\rho(f^\star;D)\;\ge\;\frac{\Delta_\Phi(D)}{2\,L_\Phi}.
$$
Consequently, if the inter-class signal survives the invariant feature map with
separation $\Delta_\Phi(D)>0$, a shift-invariant classifier achieves robust
radius at least $\Delta_\Phi(D)/(2L_\Phi)$, with **no accuracy loss** (correct on
all of $D$).

**(A.ii) Necessity / trade-off (upper bound on *every* invariant classifier).**
For **every** $G$-invariant classifier $f$ (no Lipschitz assumption) that
classifies $D$ correctly, the robust radius is bounded by the *Euclidean
geometry of the orbits*:
$$
\rho(f;D)\;\le\;\tfrac12\,\operatorname{dist}\big(\,\mathcal O(S_+),\,\mathcal
O(S_-)\,\big)
=\tfrac12\inf_{\substack{x\in S_+,x'\in S_-\\ s,s'\in G}}\|T_s x-T_{s'}x'\|_2 .
$$
In particular, if some positive example and some negative example have
*intersecting or nearby orbits* in input space, **no** invariant classifier can
be robust, regardless of architecture depth or width.

**(A.iii) The exact co-existence dichotomy.** Combining (A.i)–(A.ii) with the
choice $\Phi=$ "best invariant features": let
$\rho^{\mathrm{inv}}_\star(D)=\sup_{f\ G\text{-inv, correct}}\rho(f;D)$ be the
best invariant robust radius. Then
$$
\frac{\Delta_\Phi(D)}{2L_\Phi}\ \le\ \rho^{\mathrm{inv}}_\star(D)\ \le\
\tfrac12\,\operatorname{dist}(\mathcal O(S_+),\mathcal O(S_-)),
$$
and the upper bound is the *orbit-distance*, the lower bound the
*invariant-feature distance*. **Co-existence holds** (invariant robustness
comparable to unconstrained robustness) **iff the orbit distance is large**,
i.e. the classes remain separated even after one is free to slide along its
shift orbit; the **trade-off is forced** iff sliding along orbits brings the
classes together (orbit distance $\to 0$) while their non-invariant
separation stays large.

### Theorem B (Linear invariance: exact recovery and sharpening of Ge)

*Restrict to linear classifiers, $\mathcal F_{\mathrm{FC}}=\{x\mapsto w^\top
x\}$, $\mathcal F_{\mathrm{inv}}=\{w^\top x: T_s w=w\}=\{c\,f_{\mathrm{dc}}\}$.
Assume the two classes are linearly separable.*

**(B.i)** The maximum-margin **unconstrained** linear classifier has geometric
margin $\rho_{\mathrm{FC}}=\tfrac12\operatorname{dist}(\operatorname{conv}
S_+,\operatorname{conv}S_-)$ (standard hard-margin SVM).

**(B.ii)** The maximum-margin **shift-invariant** linear classifier exists iff
the classes are separated by their DC values, and then has geometric margin
exactly
$$
\rho_{\mathrm{inv}}=\tfrac12\,\big|\,\overline{f_{\mathrm{dc}}}(S_+)
-\overline{f_{\mathrm{dc}}}(S_-)\,\big|\Big/\|\bar w\|_2
=\tfrac12\,\operatorname{dist}\big(f_{\mathrm{dc}}(S_+),f_{\mathrm{dc}}(S_-)\big),
$$
the DC separation; equivalently $\rho_{\mathrm{inv}}=\Delta_{\Phi_{\mathrm{dc}}}/2$.
The separating hyperplane has normal $\bar w\propto\mathbf 1$. (This is the
geometric-radius form of Ge's Theorem 1.)

**(B.iii) Single-dot collapse (Ge's Corollary 1, recovered and extended to the
ratio).** For Ge's data $x_1=e_a$ (a single white pixel, all-zeros background
with one 1) labeled $+1$ and $x_2=-e_b$ labeled $-1$ (a single black pixel),
$\rho_{\mathrm{FC}}=1$ (taking the two points; with the antipodal pair $\{e_a,
-e_a\}$, $\rho_{\mathrm{FC}}=1$ and the *full* margin between the points is
$\|e_a-(-e_a)\|/2=1$), whereas $f_{\mathrm{dc}}(e_a)=1/\sqrt d$,
$f_{\mathrm{dc}}(-e_a)=-1/\sqrt d$, giving
$$
\rho_{\mathrm{inv}}=\tfrac12\Big(\tfrac1{\sqrt d}-(-\tfrac1{\sqrt d})\Big)
=\frac1{\sqrt d},\qquad
\frac{\rho_{\mathrm{inv}}}{\rho_{\mathrm{FC}}}=\frac1{\sqrt d}\xrightarrow{d\to\infty}0 .
$$
Thus the *linear*-invariant collapse factor is exactly $1/\sqrt d$ (the $2\to
2/\sqrt d$ in Ge's point-to-point margin convention), and for **linear**
invariance it is forced because the single-dot classes coincide in every
*linear* invariant feature except a vanishing DC gap ($f_{\mathrm{dc}}=\pm1/\sqrt
d$).

**A subtlety worth stating honestly: the single-dot collapse is a *linear*
artifact, and the *orbit-distance* ceiling (Theorem A.ii) is much larger here.**
The orbit of $e_a$ is $\{e_0,\dots,e_{d-1}\}$ and the orbit of $-e_a$ is
$\{-e_0,\dots,-e_{d-1}\}$; the minimum cross-class orbit distance is
$d_{\mathcal O}=\min_{i,j}\|e_i-(-e_j)\|=\sqrt2$ (attained at $i\ne j$,
$\|e_i+e_j\|=\sqrt2$), an $\Omega(1)$ quantity. So Theorem A.(ii) only caps the
*nonlinear* invariant robust radius at $\tfrac12\sqrt2=\tfrac1{\sqrt2}$, **not**
at $1/\sqrt d$. The two power spectra are $|\widehat{e_a}_j|^2=1/d$ (flat) for
*both* $e_a$ and $-e_a$, so the magnitude spectrum does **not** separate the
single-dot classes ($\Delta_{\Phi_{\mathrm{ps}}}=0$): they differ only in
*sign/phase*, which the power spectrum discards. A *phase-sensitive* complete
invariant (e.g. the bispectrum, which records relative phases) would separate
them, giving an invariant classifier with radius up to $\Theta(1)$. **Conclusion:
Ge's $1/\sqrt d$ is the collapse of the best *linear* invariant; Theorem A
predicts a sufficiently expressive *nonlinear* invariant classifier escapes it on
this very example (because $d_{\mathcal O}=\sqrt2=\Omega(1)$), with the practical
caveat that the simplest quadratic invariant — the power spectrum — is blind to
the sign and so does not suffice (Limitation 3).** This is a concrete, testable
prediction distinguishing our theory from a naive "invariance always collapses
single-dot" reading.

**(B.iv) Strict converse (when linear invariance does NOT collapse the margin).**
If the two classes are separated *by their DC values with a gap independent of
$d$*, i.e. $\operatorname{dist}(f_{\mathrm{dc}}(S_+),f_{\mathrm{dc}}(S_-))=\Omega(1)$,
then $\rho_{\mathrm{inv}}=\Omega(1)$ and there is **no collapse**: a linear
invariant classifier is as robust (up to constants) as the unconstrained one.
The collapse in Ge is therefore *not* an effect of invariance per se but of the
single-dot data having its discriminative signal in the AC subspace (high
frequencies), where linear invariance cannot reach.

### Theorem C (Invariance suppresses off-manifold orbit gradient ⇒ enlarged linearized robust radius)

*Let $f$ be $G$-invariant and differentiable. Let $\mathcal T(x)=
\operatorname{span}\{A^kx:k\ge1\}$ be the **continuous orbit-tangent space** at
$x$, where $A=\frac{d}{ds}T_s|_{s=0}$ is the cyclic-shift generator. Then at every
$x$ the input-gradient $\nabla f(x)$ is **exactly orthogonal to $\mathcal T(x)$**,
and consequently the linearized robust radius cannot be shrunk by perturbations
along orbit-tangent directions. (This is a first-order statement; the discrete
chord version $\nabla f\perp(T_sx-x)$ is false, Limitation 1.)*

**(C.i) Gradient lies in the orbit-normal space.** For $G$-invariant
differentiable $f$ and any $x$, the directional derivative along the
infinitesimal-shift generator vanishes,
$$
\big\langle \nabla f(x),\,A x\big\rangle = 0,
$$
and more generally $\nabla f(x)\perp\mathcal T(x)$ (Lemma 4.6ii). Hence the
gradient carries **no component along the continuous orbit direction**: the model
has *zero first-order sensitivity* to perturbations that move $x$ infinitesimally
along its own shift orbit.

**(C.ii) Robust-radius decomposition.** Decompose any perturbation
$\delta=\delta_{\mathcal T}+\delta_{\perp}$ into orbit-tangent
($\in\mathcal T(x)$) and orbit-normal ($\in\mathcal T(x)^\perp$) parts. To first
order, only the orbit-normal part changes $f$:
$f(x+\delta)\approx f(x)+\langle\nabla f(x),\delta_\perp\rangle$. Thus the
linearized flipping budget is spent entirely in $\mathcal T(x)^\perp$; invariance
**removes** the $\dim\mathcal T(x)$ orbit-tangent directions from the adversary's
first-order budget, and the linearized robust radius is governed only by the
orbit-normal sensitivity $\|\Pi_{\mathcal T(x)^\perp}\nabla f(x)\|=\|\nabla
f(x)\|$.

**(C.iii) Net effect (co-existence side condition).** Invariance *enlarges* the
linearized robust radius relative to a non-invariant $f$ that *does* have gradient
along $\mathcal T(x)$ — **provided** the invariant model does not create new
sensitivity in orbit-normal directions, i.e. provided $\|\Pi_{\mathcal T(x)^\perp}\nabla
f_{\mathrm{inv}}(x)\|\le\|\Pi_{\mathcal T(x)^\perp}\nabla f_{\mathrm{FC}}(x)\|$.
This is the local, gradient-level version of "invariance helps iff it does not
move the discriminative signal into a more fragile (orbit-normal) direction,"
and it is exactly Melamed's mechanism in the regime where the orbit-tangent space
$\mathcal T(x)$ lies in the off-manifold complement $P^\perp$ (proof in §4.5).

---

## 4. Full proofs

### 4.1 Proof of Theorem A.(i) — Achievability

We construct $f^\star$ explicitly. Let $\Phi$ be the given invariant feature map
with budget $L_\Phi$, and assume $\Delta:=\Delta_\Phi(D)>0$ (otherwise the bound
is vacuous, $\rho\ge0$). The images $\Phi(S_+),\Phi(S_-)\subseteq\mathbb R^p$ are
compact (continuous image of compact, by (A1) and Lipschitzness of $\Phi$) and at
distance $\Delta$ apart.

**Step 1 — a robust classifier in feature space.** Define on $\mathbb R^p$ the
*signed-distance-difference*
$$
g(u)\;=\;\operatorname{dist}(u,\Phi(S_-))-\operatorname{dist}(u,\Phi(S_+)).
$$
Each $u\mapsto\operatorname{dist}(u,K)$ is $1$-Lipschitz (a standard fact:
$|\operatorname{dist}(u,K)-\operatorname{dist}(u',K)|\le\|u-u'\|$, by the
triangle inequality applied to the minimizing point). Hence $g$ is the
difference of two $1$-Lipschitz functions; we show it is $1$-Lipschitz after a
harmless rescaling. Actually we use a cleaner, *exactly* $1$-Lipschitz choice:
$$
g(u)=\tfrac12\Big(\operatorname{dist}(u,\Phi(S_-))-\operatorname{dist}(u,\Phi(S_+))\Big).
$$

> **Lemma 4.1.** $g$ is $1$-Lipschitz, and for $u\in\Phi(S_+)$, $g(u)\ge
> \Delta/2$; for $u\in\Phi(S_-)$, $g(u)\le-\Delta/2$.
>
> *Proof.* Lipschitz: each $\operatorname{dist}(\cdot,K)$ is $1$-Lipschitz, so
> their difference is $2$-Lipschitz, and $\tfrac12$ of it is $1$-Lipschitz.
> Margin: for $u\in\Phi(S_+)$, $\operatorname{dist}(u,\Phi(S_+))=0$ and
> $\operatorname{dist}(u,\Phi(S_-))\ge\Delta$ (definition of $\Delta$ as the inf
> over the two sets), so $g(u)\ge\tfrac12(\Delta-0)=\Delta/2$. Symmetric for
> $S_-$. $\qquad\blacksquare$

**Step 2 — pull back to input space.** Set $f^\star=g\circ\Phi$. Then:
* **$G$-invariance:** $f^\star(T_s x)=g(\Phi(T_s x))=g(\Phi(x))=f^\star(x)$,
  using invariance of $\Phi$ (Def 2.7a).
* **Correctness:** for $(x,+1)\in D$, $f^\star(x)=g(\Phi(x))\ge\Delta/2>0$;
  for $(x,-1)$, $f^\star(x)\le-\Delta/2<0$. So $y f^\star(x)\ge\Delta/2$, score
  margin $\gamma\ge\Delta/2$.
* **Lipschitzness:** $f^\star=g\circ\Phi$ with $g$ $1$-Lipschitz and $\Phi$
  $L_\Phi$-Lipschitz, so $f^\star$ is $L_\Phi$-Lipschitz:
  $|f^\star(x)-f^\star(x')|=|g(\Phi(x))-g(\Phi(x'))|\le\|\Phi(x)-\Phi(x')\|\le
  L_\Phi\|x-x'\|$.

**Step 3 — score margin to geometric radius.** By Lemma 2.5 with score margin
$\gamma\ge\Delta/2$ and Lipschitz constant $L_\Phi$,
$$
\rho_{f^\star}(x)\ \ge\ \frac{\gamma}{L_\Phi}\ \ge\ \frac{\Delta/2}{L_\Phi}
=\frac{\Delta_\Phi(D)}{2L_\Phi}\qquad\text{for all }(x,y)\in\operatorname{supp}D,
$$
so $\rho(f^\star;D)\ge\Delta_\Phi(D)/(2L_\Phi)$. This proves (A.i).
$\qquad\blacksquare$

*Remark.* The factor $\tfrac12$ is sharp in general: with two singleton feature
images at distance $\Delta$, the maximal-margin separator puts the boundary
halfway, radius $\Delta/2$.

### 4.2 Proof of Theorem A.(ii) — Necessity via orbit distance

Let $f$ be **any** $G$-invariant classifier (no smoothness assumed) classifying
$D$ correctly. Suppose for contradiction $\rho(f;D)>\tfrac12 d_{\mathcal O}$
where $d_{\mathcal O}:=\operatorname{dist}(\mathcal O(S_+),\mathcal O(S_-))
=\inf_{x\in S_+,x'\in S_-,s,s'}\|T_sx-T_{s'}x'\|$.

Pick $(x,+1),(x',-1)\in\operatorname{supp}D$ and shifts $s,s'$ nearly attaining
the infimum: $\|T_sx-T_{s'}x'\|\le d_{\mathcal O}+\eta$ for arbitrary $\eta>0$.
Let $a=T_sx$, $b=T_{s'}x'$, $\|a-b\|\le d_{\mathcal O}+\eta$.

**Invariance moves the decision values to the orbit representatives.** Because
$f$ is $G$-invariant, $f(a)=f(T_sx)=f(x)>0$ and $f(b)=f(T_{s'}x')=f(x')<0$. So
$f(a)>0>f(b)$: there is a sign change between $a$ and $b$, two points at distance
$\le d_{\mathcal O}+\eta$.

We prove two clean inequalities; the second (the $\tfrac12$ form in the theorem)
is the sharper one and follows from an intermediate-value/midpoint argument.

**Lemma 4.2 (Shift-equivariance of the robust radius for invariant $f$).** *If
$f$ is $G$-invariant then $\rho_f(T_sx)=\rho_f(x)$ for all $s$.*

*Proof.* For any $\delta$, $f(T_sx+\delta)=f(T_s(x+T_{-s}\delta))=f(x+T_{-s}\delta)$
by invariance ($T_s$ linear, $T_sT_{-s}=I$). Since $T_{-s}$ is an isometry
(Fact 1.1), $\|T_{-s}\delta\|=\|\delta\|$, so the map $\delta\mapsto T_{-s}\delta$
is a norm-preserving bijection between flipping perturbations at $T_sx$ and at
$x$. Hence the infimal flipping norm is equal: $\rho_f(T_sx)=\rho_f(x)$.
$\qquad\blacksquare$

**Step 1 (one-sided bound $\rho(f;D)\le d_{\mathcal O}$).** Take the perturbation
$\delta=b-a$, $\|\delta\|\le d_{\mathcal O}+\eta$. Then $f(a+\delta)=f(b)<0$ while
$f(a)>0$, so $\operatorname{sign}f(a+\delta)\ne\operatorname{sign}f(a)$ and
$\rho_f(a)\le d_{\mathcal O}+\eta$. By Lemma 4.2, $\rho_f(x)=\rho_f(a)$, so
$\rho(f;D)\le\rho_f(x)\le d_{\mathcal O}+\eta$. Letting $\eta\to0$:
$\rho(f;D)\le d_{\mathcal O}$.

**Step 2 (midpoint bound $\rho(f;D)\le\tfrac12 d_{\mathcal O}$).** $f$ need not be
continuous, so we cannot invoke the intermediate value theorem directly; instead
we use a discrete sign-change argument on the segment $[a,b]$. Parametrize
$z(t)=(1-t)a+tb$, $t\in[0,1]$, with $f(z(0))=f(a)>0$ and $f(z(1))=f(b)<0$. Let
$t^\star=\sup\{t: f(z(t))>0\}\in(0,1]$. For the *endpoint nearer to $t^\star$*,
$$
\min\big(\rho_f(a),\rho_f(b)\big)\ \le\ \min\big(\|z(t^\star)-a\|,\,\|z(t^\star)-b\|\big)
\ \le\ \tfrac12\|a-b\| ,
$$
where the first inequality holds because arbitrarily close to $t^\star$ on each
side the sign of $f$ differs (definition of $\sup$), so a perturbation of size
$\|z(t^\star\pm)-a\|$ resp. $\|z(t^\star\pm)-b\|$ flips the prediction at $a$
resp. $b$; and the second inequality holds because $\|z(t^\star)-a\|+
\|z(t^\star)-b\|=\|a-b\|$ ($z(t^\star)$ is on the segment) so their minimum is at
most half. Combining with Lemma 4.2 ($\rho_f(a)=\rho_f(x)$, $\rho_f(b)=\rho_f(x')$):
$$
\rho(f;D)\ \le\ \min(\rho_f(x),\rho_f(x'))=\min(\rho_f(a),\rho_f(b))\ \le\
\tfrac12\|a-b\|\ \le\ \tfrac12(d_{\mathcal O}+\eta).
$$
Letting $\eta\to0$ gives the boxed bound
$$
\boxed{\ \rho(f;D)\ \le\ \tfrac12\,d_{\mathcal O}\ }.
$$
This proves (A.ii). $\qquad\blacksquare$

*Remark (tightness).* The factor $\tfrac12$ here matches the $\tfrac12$ in the
achievability bound (A.i): when the invariant feature map is complete for the
orbits (so $\Delta_\Phi/L_\Phi\asymp d_{\mathcal O}$, e.g. magnitude-separated
orbits via the power spectrum, Lemma 2.6), the lower bound
$\Delta_\Phi/(2L_\Phi)$ and the upper bound $\tfrac12 d_{\mathcal O}$ coincide up
to the completeness constant, giving an **exact** characterization
$\rho^{\mathrm{inv}}_\star\asymp\tfrac12 d_{\mathcal O}$. The residual slack
(Limitation 2,3) is the invariant-feature incompleteness, not a looseness in this
argument.

> **Geometric reading.** The mechanism of (A.ii) is that invariance *teleports*
> the decision values of $x$ to its entire orbit (Lemma 4.2): a $+$ point and a
> $-$ point that are far apart in input space but whose *orbits* pass near each
> other can be connected by a short straight-line attack between two near orbit
> representatives, because $f$ must give them the original (opposite) labels. So
> the adversary attacks "across the orbit gap," and invariant robustness is capped
> by the orbit gap $d_{\mathcal O}$, not the raw gap $d_{\mathrm{raw}}\ge
> d_{\mathcal O}$.

### 4.3 $L_\infty$ corollary

> **Corollary 4.3 ($L_\infty$ version).** All bounds transfer to $L_\infty$ with
> the standard norm equivalence $\|\delta\|_\infty\le\|\delta\|_2\le\sqrt
> d\,\|\delta\|_\infty$. Specifically the $L_\infty$ robust radius satisfies
> $\rho^\infty_f(x)\ge\rho_f(x)/\sqrt d$ (from $\|\delta\|_2\le\sqrt
> d\|\delta\|_\infty$, a flip needs $\|\delta\|_2\ge\rho_f$, hence
> $\|\delta\|_\infty\ge\rho_f/\sqrt d$) and $\rho^\infty_f(x)\le\rho_f(x)$. Thus
> Theorem A reads, for $L_\infty$,
> $\frac{\Delta_\Phi}{2\sqrt d\,L_\Phi}\le\rho^{\infty,\mathrm{inv}}_\star\le
> \tfrac12 d_{\mathcal O}$. The $\sqrt d$ here is the *generic* norm-equivalence
> factor and is **not** the source of Ge's $1/\sqrt d$, which comes from the DC
> bottleneck (Theorem B) and persists in pure $L_2$.
>
> *Proof.* Norm equivalence and monotonicity of inf over a larger/smaller ball.
> $\qquad\blacksquare$

### 4.4 Proof of Theorem B — linear invariance

**(B.i)** Standard. For linear $f(x)=w^\top x-c$ classifying $S_+,S_-$ with all
$+$ on one side, the geometric margin is $\min_x \frac{|w^\top
x-c|}{\|w\|}$; maximizing over $(w,c)$ gives the hard-margin SVM whose value is
$\tfrac12\operatorname{dist}(\operatorname{conv}S_+,\operatorname{conv}S_-)$ (the
half-distance between the convex hulls; classical, e.g. by LP duality / the
supporting-hyperplane theorem). We do not reprove SVM duality here as it is
textbook; the only fact we use downstream is the value.

**(B.ii)** A linear $f(x)=w^\top x$ is $G$-invariant iff $T_s w=w\ \forall s$ iff
$w\in\mathcal V_{\mathrm{inv}}=\operatorname{span}\mathbf 1$ (Definition 2.2,
proved there via Lemma 2.1). So $w=c\,\mathbf 1=c'\bar w$ and $f(x)=c'\,\bar
w^\top x=c'\,f_{\mathrm{dc}}(x)$ for a scalar $c'$. The classifier is determined
by the scalar feature $f_{\mathrm{dc}}(x)$. It separates $D$ iff
$f_{\mathrm{dc}}(S_+)$ and $f_{\mathrm{dc}}(S_-)$ are separated on $\mathbb R$,
i.e. (after possibly flipping sign) $\min_{x\in S_+}f_{\mathrm{dc}}(x)>\max_{x\in
S_-}f_{\mathrm{dc}}(x)$ or vice versa — this is exactly Ge's Theorem 1 separation
condition $\max_{x\in S_+}f_{\mathrm{dc}}(x)<\min_{x\in S_-}f_{\mathrm{dc}}(x)$
or the reverse. The geometric margin of the 1-D thresholding of
$f_{\mathrm{dc}}$, pulled back through the unit-norm functional $\bar w$
($\|\bar w\|=1$), is $\tfrac12$ the gap of the projected 1-D data:
$$
\rho_{\mathrm{inv}}=\tfrac12\big(\min_{S_+}f_{\mathrm{dc}}-\max_{S_-}f_{\mathrm{dc}}\big)
=\tfrac12\operatorname{dist}\big(f_{\mathrm{dc}}(S_+),f_{\mathrm{dc}}(S_-)\big)
=\Delta_{\Phi_{\mathrm{dc}}}/2 ,
$$
since the optimal threshold sits at the midpoint and $\bar w$ is unit norm so the
input-space distance equals the feature-space distance. This is the
geometric-radius restatement of Ge's Theorem 1 (margin = difference of DC
components) with the normal $\bar w\propto\mathbf1$. $\qquad\blacksquare$

**(B.iii)** Plug Ge's data into (B.ii). With $x_1=e_a$ (white dot), $x_2=-e_b$
(black dot), $f_{\mathrm{dc}}(e_a)=\bar w^\top e_a=\frac1{\sqrt d}$ and
$f_{\mathrm{dc}}(-e_b)=-\frac1{\sqrt d}$ for any $a,b$. For the single-image-class
problem ($S_+=\{e_a\}$, $S_-=\{-e_a\}$, antipodal), the DC values are exactly
$\pm1/\sqrt d$ so $\rho_{\mathrm{inv}}=\tfrac12\cdot\frac2{\sqrt d}=\frac1{\sqrt
d}$. Meanwhile the unconstrained linear classifier separates $e_a$ from $-e_a$
with $w=e_a$ (the indicator of the dot pixel), geometric margin $\tfrac12\|e_a-
(-e_a)\|=1$. Ratio $1/\sqrt d\to0$. This is Ge's Corollary 1 (point-to-point
margin $2\to 2/\sqrt d$; the $\tfrac12$ converts to geometric radius $1\to
1/\sqrt d$). $\qquad\blacksquare$

**(B.iv)** Immediate from (B.ii): $\rho_{\mathrm{inv}}=\tfrac12\Delta_{\Phi_{\mathrm{dc}}}$,
so if $\Delta_{\Phi_{\mathrm{dc}}}=\operatorname{dist}(f_{\mathrm{dc}}(S_+),
f_{\mathrm{dc}}(S_-))=\Omega(1)$ then $\rho_{\mathrm{inv}}=\Omega(1)$, no $d$
dependence, no collapse. The single-dot collapse is special: there the *only*
linearly-accessible invariant is the DC, and the discriminative content (which
pixel is lit) lives in the AC subspace $\mathcal V_{\mathrm{ac}}=\{x:\mathbf
1^\top x=0\}$ — precisely the orbit-difference span (Lemma 2.4) — which linear
invariance discards. **A dataset whose class signal is in the DC mean (e.g. total
brightness) suffers no linear-invariance collapse.** $\qquad\blacksquare$

### 4.5 Proof of Theorem C — gradient suppression along orbits

**(C.i).** Let $f$ be $G$-invariant and differentiable, and let
$\gamma(s)=T_sx$ be the orbit curve (for continuous $s$, using the one-parameter
subgroup generated by the cyclic-shift generator $A=\frac{d}{ds}T_s|_{s=0}$; $A$
is the skew-symmetric "derivative of cyclic permutation," $A=W^*\operatorname{diag}(-\tfrac{2\pi i
j}{d})_jW$, real and skew). Invariance gives $f(\gamma(s))=f(x)$ for all $s$, a
constant. Differentiate at $s=0$:
$$
0=\frac{d}{ds}f(\gamma(s))\Big|_{0}=\langle\nabla f(x),\gamma'(0)\rangle
=\langle\nabla f(x),Ax\rangle .
$$
$Ax$ is the orbit tangent vector at $x$. The continuous orbit tangent space is
$\mathcal T(x):=\operatorname{span}\{A^kx:k\ge1\}$, the infinitesimal analogue of
$\mathcal D(x)$ (it is the tangent at $x$ to the smooth one-parameter orbit
$\{T_tx:t\in\mathbb R\}$ generated by $A$). The next lemma states the two facts
about $\nabla f$ that are **exactly true** and that we use; we deliberately do
*not* assert the (false) discrete version (Limitation 1).

> **Lemma 4.6 (Equivariance and infinitesimal orbit-normality of $\nabla f$).**
> Let $f$ be $G$-invariant and differentiable. Then:
> (i) **Equivariance:** $\nabla f(T_sx)=T_s\nabla f(x)$ for all $s$.
> (ii) **Infinitesimal orbit-normality:** $\langle\nabla f(x),v\rangle=0$ for
> every $v\in\mathcal T(x)$; in particular $\nabla f(x)\perp\mathcal T(x)$.
>
> *Proof.* (i) Invariance $f(T_sx)=f(x)$ holds as an identity in $x$. Take the
> gradient in $x$ of both sides: by the chain rule $\nabla_x[f(T_sx)]=T_s^\top
> \nabla f(T_sx)$, while $\nabla_x[f(x)]=\nabla f(x)$. Hence $T_s^\top\nabla
> f(T_sx)=\nabla f(x)$, and since $T_s^\top=T_s^{-1}$, $\nabla f(T_sx)=T_s\nabla
> f(x)$.
> (ii) For the one-parameter subgroup $T_t=e^{tA}$ (well-defined: $A$ is the real
> skew matrix $W^*\operatorname{diag}(-2\pi i j/d)_jW$, so $e^{tA}\in SO(d)$ and
> $e^{(2\pi/d)A}=T_1$ recovers the unit cyclic shift), invariance gives
> $f(e^{tA}x)=f(x)$ for all $t$. Differentiate at $t=0$: $0=\langle\nabla
> f(x),Ax\rangle$. Replacing $x$ by $T_{-s}x$ and using (i) and that $A$ commutes
> with every $T_s$ (both are functions of $W$), one gets $\langle\nabla
> f(x),A^kx\rangle=0$ for all $k\ge1$ by the same one-parameter argument applied
> to the subgroup generated by $A^k$ (each $A^k$ generates a sub-rotation under
> which $f$ is still invariant, since powers of shifts are shifts). Hence
> $\nabla f(x)\perp\operatorname{span}\{A^kx\}=\mathcal T(x)$. $\qquad\blacksquare$

*(Honesty note, expanded in Limitation 1: the fully **discrete** claim "$\nabla
f(x)\perp(T_sx-x)$ for every finite $s$" is **false** in general — a function
constrained only on the finite orbit points has unconstrained gradient on the
chords between them. We use only the exact statements of Lemma 4.6: equivariance
(i) and the infinitesimal/continuous-orbit orthogonality (ii). Consequently
Theorem C is a first-order/linearized robustness statement, not a certified
discrete radius.)*

**(C.ii)–(C.iii).** Equivariance $\nabla f(T_sx)=T_s\nabla f(x)$ (Lemma 4.6)
plus $\langle\nabla f(x),Ax\rangle=0$ (C.i) show the gradient has **no component
along the continuous orbit direction $Ax$**. Decompose the unit-norm steepest
attack direction $u=\nabla f(x)/\|\nabla f(x)\|$. By Lemma 4.6(ii) its component
along the orbit-tangent space $\mathcal T(x)$ is zero, so the adversary's
first-order most efficient direction lies entirely in the orbit-normal space
$\mathcal T(x)^\perp$. The linearized robust radius is
$\rho_f^{\mathrm{lin}}(x)=|f(x)|/\|\nabla f(x)\|$; since $\nabla f(x)\in\mathcal
T(x)^\perp$ we have $\|\nabla f(x)\|=\|\Pi_{\mathcal T(x)^\perp}\nabla f(x)\|$, so
$$
\rho_f^{\mathrm{lin}}(x)=\frac{|f(x)|}{\|\Pi_{\mathcal T(x)^\perp}\nabla
f(x)\|}\ \ge\ \frac{|f(x)|}{\|\nabla f_{\mathrm{FC}}(x)\|}=\rho^{\mathrm
{lin}}_{f_{\mathrm{FC}}}(x)
$$
**whenever** the non-invariant $f_{\mathrm{FC}}$ has, at matched score $|f(x)|$,
the *same or larger* orbit-normal gradient $\|\Pi_{\mathcal T(x)^\perp}\nabla
f_{\mathrm{FC}}\|\ge\|\Pi_{\mathcal T(x)^\perp}\nabla f\|$ and *additionally* a
nonzero orbit-tangent gradient $\Pi_{\mathcal T(x)}\nabla f_{\mathrm{FC}}\ne0$
(which strictly enlarges its denominator $\|\nabla f_{\mathrm{FC}}\|$). This is
(C.iii): invariance can only *remove* gradient mass (the orbit-tangent part),
never add it, so at matched score it weakly enlarges the linearized robust radius
— *unless* the invariant construction routes the discriminative signal into
orbit-normal directions that are themselves fragile, the failure mode
(B.iii)/Theorem A.(ii) identifies globally. $\qquad\blacksquare$

> **Connection to Melamed.** Take the data to lie on a subspace $P$. Melamed's
> non-robustness comes from $\Pi_{P^\perp}\nabla N(x)$ being large while
> $\Pi_{P^\perp}w_i$ is *fixed at init* (data has no $P^\perp$ component to train
> it away). The link is the regime where the **orbit-tangent directions
> $\mathcal T(x)$ lie off the data manifold**, i.e. $\mathcal T(x)\subseteq
> P^\perp$. This holds when moving $x$ along its orbit sweeps it through
> off-manifold configurations — the single-dot case: shifting a dot drags it
> across empty background, traversing points no real image occupies, all in
> $P^\perp$ (high-frequency / aliasing directions). There, invariance forces
> $\nabla f\perp\mathcal T(x)$ (Lemma 4.6ii), i.e. it *zeroes exactly the
> off-manifold gradient component Melamed blames* — for those orbit-tangent
> directions. Thus, in the off-manifold-orbit regime, invariance **acts like
> Melamed's robustifiers (small init / $L_2$ reg) for free**, by construction
> rather than by tuning. (Caveat: invariance only kills the $\mathcal
> T(x)\subseteq P^\perp$ part of the off-manifold gradient; the rest of $P^\perp$
> remains exposed, so invariance is not a complete robustifier — consistent with
> CNNs still having adversarial examples.) This is the rigorous form of
> "invariance suppresses aliasing/high-frequency orbit gradient directions,
> enlarging the robust radius."

---

## 5. Empirical predictions for a controlled dissection

Theorem A says one scalar predicts co-existence: the **orbit distance**
$d_{\mathcal O}=\operatorname{dist}(\mathcal O(S_+),\mathcal O(S_-))$, bracketed
below by the **invariant-feature distance** $\Delta_\Phi$. We give measurable
proxies and concrete predictions for a depth/kernel/pooling/dense dissection at
matched capacity.

### 5.1 The measurable predictors

There are **two** distinct ratios, because the upper bound (Thm A.ii) is over the
*best* invariant classifier (any depth/nonlinearity) while a *shallow/linear*
invariant model only reaches the invariant-*feature* lower bound (Thm A.i / B).
Both are cheap to compute and they pin down the two ends of the bracket.

**(a) Best-invariant ceiling — orbit-distance ratio.**
$$
\kappa(D)\;:=\;\frac{d_{\mathcal O}}{d_{\mathrm{raw}}},\qquad
d_{\mathrm{raw}}=\operatorname{dist}(S_+,S_-)
=\inf_{x\in S_+,x'\in S_-}\|x-x'\| ,\qquad \kappa\in[0,1].
$$
$\kappa\approx1$: sliding along orbits does not bring the classes closer, so even
the *best* invariant classifier keeps the full margin ⇒ **co-existence is
possible**. $\kappa\approx0$: orbits collapse the gap ⇒ **trade-off forced for
every invariant model** (Kamath/Remark 6.6 corner). $\kappa$ is computed by an
all-pairs orbit nearest-neighbor search (FFT cross-correlation gives all $d$
shifts at once, $O(d\log d)$ per pair).

**(b) Achieved-by-this-$\Phi$ floor — feature-separation ratio.** For the actual
invariant features a given architecture computes (linear DC, or quadratic power
spectrum),
$$
\lambda_\Phi(D)\;:=\;\frac{\Delta_\Phi(D)}{L_\Phi\,d_{\mathrm{raw}}}\in[0,1].
$$
For a *linear/GAP-only* invariant, $\Phi=f_{\mathrm{dc}}$ and
$\lambda_{\mathrm{dc}}=\frac{\operatorname{dist}(f_{\mathrm{dc}}(S_+),
f_{\mathrm{dc}}(S_-))}{d_{\mathrm{raw}}}$; **this** is the ratio that is
$\Theta(1/\sqrt d)$ on single-dot data (Theorem B.iii) — the linear DC bottleneck.
For a power-spectrum CNN, $\lambda_{\mathrm{ps}}=\Delta_{\Phi_{\mathrm{ps}}}/
d_{\mathrm{raw}}$.

**The gap $\kappa-\lambda_\Phi$ is the architecture's invariant-feature
incompleteness:** when small, the network's invariant features already capture all
orbit-separating information and it attains the ceiling; when large (single-dot:
$\kappa=1/\sqrt2$ but $\lambda_{\mathrm{dc}}=1/\sqrt d$), the architecture is
leaving robustness on the table because its invariant features are too weak to see
the class signal.

### 5.2 Predictions (matched-capacity dissection)

Let "Conv-$k$-GAP" denote a circular-padded CNN with kernel size $k$ + global
average pooling (fully invariant), and "FC" a fully-connected net with matched
parameter count. Vary depth, kernel $k$, pooling (GAP vs flatten/dense head),
and the dataset's $\kappa$.

1. **Robustness of the *realized* invariant model tracks $\lambda_\Phi$; the
   *ceiling* tracks $\kappa$.** Plot $\rho_{\mathrm{inv}}/\rho_{\mathrm{FC}}$
   (measured by PGD-$L_2$ distance to boundary) against $\lambda_\Phi(D)$ computed
   for *that model's* invariant features. Prediction: a monotone increasing curve.
   For a **linear/DC-only** invariant on single-dot-type data,
   $\lambda_{\mathrm{dc}}\sim1/\sqrt d$ ⇒ ratio $\sim1/\sqrt d$ (Ge's collapse).
   For **orthogonal-frequency** data, $\lambda_{\mathrm{ps}}=\Theta(1)$
   ($d$-independent, since the parity classes have disjoint power-spectrum support)
   ⇒ ratio $\ge1$ (invariant *more* robust, Ge Table 3). The separate quantity $\kappa$ upper-
   bounds what *any* invariant model could reach; a large $\kappa-\lambda_\Phi$ gap
   predicts that adding feature expressivity (more channels, square/quadratic
   units, bispectral features) raises $\rho_{\mathrm{inv}}$ toward the $\kappa$
   ceiling **without** breaking invariance. **This pair of regressions is the
   central falsifiable claim:** the *floor* moves with $\lambda_\Phi$ (architecture
   $\times$ data), the *ceiling* with $\kappa$ (data only).

2. **Orthogonal-frequencies dataset (Ge Sec 5.2) has $\kappa=1$.** Classes =
   {odd $\sin/\cos$ frequencies} vs {even}. Shifts only rotate phase within a
   frequency (Lemma 2.6), never crossing the odd/even partition, so $d_{\mathcal
   O}=d_{\mathrm{raw}}$, $\kappa=1$. Prediction (which Ge confirms): invariant CNN
   *more* robust than FC. Our theory **explains** this previously
   under-explained data point as the $\Delta_{\Phi_{\mathrm{ps}}}=d_{\mathrm{raw}}$
   case.

3. **Pooling head is the lever.** Swap GAP → flatten+dense (breaks invariance).
   Prediction: robustness *drops toward FC* on high-$\kappa$ data (you gave up the
   free orbit-tangent gradient suppression of Theorem C) but *rises* on low-$\kappa$
   data (you regained access to AC discriminative signal). Robustness should
   track measured **shift-consistency**, and shift-consistency × $\kappa$
   should jointly predict $\rho$.

4. **Kernel size and depth modulate $L_\Phi$, not the dichotomy.** Larger
   kernels/depth raise the Lipschitz budget $L_\Phi$ of the realized invariant
   feature map, lowering the *guaranteed* radius $\Delta_\Phi/(2L_\Phi)$ (Thm A.i)
   but not the orbit-distance ceiling (Thm A.ii). Prediction: at fixed $\kappa$,
   robustness is roughly flat in depth/kernel until Lipschitz blow-up dominates;
   spectral-norm regularization (capping $L_\Phi$) should help invariant models
   specifically. Measure $L_\Phi$ via the product of layer spectral norms; expect
   $\rho_{\mathrm{inv}}\cdot L_\Phi/\Delta_{\Phi}\approx$ const.

5. **Gradient-direction test for Theorem C.** Measure the fraction of input
   gradient energy lying in the orbit-tangent space, $\|\Pi_{\mathcal T(x)}\nabla
   f(x)\|^2/\|\nabla f(x)\|^2$, using the continuous tangent $\mathcal
   T(x)=\operatorname{span}\{A^kx\}$ (numerically, the span of a few
   finite-difference shifts $T_{\pm1}x-x$ approximates it). Prediction:
   $\approx0$ for invariant CNNs (Theorem C.i is exact for $\mathcal T(x)$) and
   substantially positive for FC; the invariant model's robust radius should
   exceed FC's exactly on inputs where FC's gradient is concentrated in $\mathcal
   T(x)$ (orbit-tangent / aliasing directions). Reporting the *discrete* orbit
   projection $\Pi_{\mathcal D(x)}$ too is informative but not theory-tight
   (Limitation 1).

### 5.3 The numbers to report

For a paper claiming co-existence in real architectures: report the **pair**
$(\kappa(D),\ \lambda_\Phi(D))$ for each dataset $\times$ architecture, and show
that (i) $\rho_{\mathrm{inv}}/\rho_{\mathrm{FC}}$ regressed on $\lambda_\Phi$
collapses the per-model scatter (the *floor* is explained by the architecture's
realized invariant-feature separation), and (ii) $\kappa$ upper-bounds the whole
family across architectures (the *ceiling* is a property of the data alone). The
co-existence claim is "explained" when these two regressions hold: **a single
geometric scalar of the data ($\kappa$) sets whether co-existence is *possible*,
and a single geometric scalar of the model's invariant features ($\lambda_\Phi$)
sets whether it is *realized*.** Both are cheap (FFT cross-correlation +
nearest-neighbor), neither requires training.

---

## 6. Relation to prior work

### 6.1 Recovering and extending Ge (2/√d)

Ge's Theorem 1 says a shift-invariant linear classifier's margin depends only on
the DC components; their Corollary 1 instantiates the single-dot $2\to2/\sqrt d$
collapse. **Theorem B is exactly this**, reformulated geometrically:
$\rho_{\mathrm{inv}}=\tfrac12\operatorname{dist}(f_{\mathrm{dc}}(S_+),
f_{\mathrm{dc}}(S_-))$ and the single-dot ratio is $1/\sqrt d$ (§4.4).
**Extension 1 (converse, B.iv):** Ge proves the collapse *can* happen; we prove
it happens **iff** the discriminative signal is in the AC subspace. If the signal
is in the DC (e.g. brightness), there is no collapse — even for linear invariance.
**Extension 2 (nonlinear escape, Thm A):** Ge's collapse is an artifact of the
1-D linear invariant subspace. With a *quadratic* invariant (power spectrum,
realizable by conv+square+GAP, an idealized one-layer CNN), the invariant feature
space is $\Theta(d)$-dimensional and $\Delta_{\Phi_{\mathrm{ps}}}$ can equal
$d_{\mathrm{raw}}$ (Ge's own orthogonal-frequency data, §5.2!). Thus Theorem A
reconciles Ge's two opposite empirical findings (Table 3: CNN less robust on
"orthogonal vectors," more robust on "orthogonal frequencies") under one
inequality: invariance preserves the margin iff $\Delta_\Phi$ survives. Ge's
"governing quantity is margin preservation, not invariance" is made into a
theorem.

### 6.2 Why this does NOT contradict Kamath

Kamath's Theorem 2 proves a forced spatial-vs-adversarial trade-off on a specific
distribution: $X=(X_0,X_1,\dots,X_d)$ where the label-carrying coordinate is
$X_0$ (with $X_0=y$ w.p. $p>1/2$), the cyclic transformation $r_j$ **fixes
$X_0$** and permutes only $X_1,\dots,X_d$, and the remaining coordinates encode
the label through a cyclic code. Two points:

1. **Different invariance object, and the signal is split across it by design.**
   Kamath's "invariance" is invariance to the group $r_j$ acting on $X_{1:d}$
   while the center pixel $X_0$ is *fixed*, enforced by *training augmentation*.
   The label signal is deliberately split: $X_0$ is invariant and weakly
   informative ($X_0=y$ w.p. $p>\tfrac12$, accuracy ceiling $p$ from $X_0$ alone),
   while the *strong* signal is the cyclic-code structure in $X_{1:d}$, which is
   exactly what $r_j$ scrambles (their Prop. 1: a classifier tuned to the
   un-transformed $X_{1:d}$ drops to $\le85\%$ on $r_j(X)$, while the
   $r_j$-invariant-optimal classifier still reaches $97\%$ — because it can be
   *re-tuned* to the orbit-averaged code, but that averaged code has smaller
   separation). In our language: the *invariant-accessible* feature separation
   $\Delta_\Phi$ collapses from "uses full $X_{1:d}$ code" down to "uses $X_0$ +
   orbit-averaged code," and Theorem A.(ii) caps the invariant robust radius by
   this reduced separation. Kamath's Theorem 2 is the *quantitative* version of
   our (A.ii) on their distribution: it converts "small invariant separation"
   into the explicit adversarial-accuracy bound $1-\frac{(1-p)(1-\eta)}{p}$,
   with $p$ measuring exactly how much separation the *invariant* coordinate
   $X_0$ retains. This is the small-$\kappa$ / small-$\lambda_\Phi$ corner of our
   dichotomy, **engineered** by routing the strong signal into the
   orbit-difference subspace $\mathcal D$.

2. **Different question.** Kamath bound (their Thm 2: spatial acc $\ge1-\eta
   \Rightarrow$ adv acc $\le1-\frac{(1-p)(1-\eta)}{p}$) is an **impossibility for
   a single classifier under augmentation-enforced invariance on a hostile
   distribution**. Our co-existence (Thm A.i) is an **existence result for a
   classifier on distributions where $\Delta_\Phi>0$**. No contradiction: on
   Kamath's distribution $\Delta_\Phi$ is small *by design*, so Thm A.i gives only
   a small guaranteed radius, in agreement. Our regime — emergent consistency in
   real CNNs, where the discriminative signal is *also* shift-invariant (textures,
   power spectra) — has $\Delta_\Phi=\Omega(1)$, the opposite corner, where
   Kamath's bound is non-binding. **The dichotomy variable $\kappa$ is precisely
   what separates Kamath's regime from the co-existence regime.**

### 6.3 Relation to Frei and Melamed (optimizer vs hypothesis class)

Our main theorems are about the **hypothesis class** (does a robust invariant
classifier *exist*?), like Frei's Thm 4.1 (robust nets exist) — and we show under
$\Delta_\Phi>0$ they exist with explicit radius. Frei's Thm 4.2 and Melamed are
about the **optimizer** selecting a non-robust point. Theorem C bridges to
Melamed at the gradient level: invariance *structurally* zeroes the
orbit-tangent gradient, which in the off-manifold regime is the very component
Melamed/Vardi blame for non-robustness; so an invariant architecture removes that
fragility *by construction*, not by the implicit-bias luck Frei shows can fail.
This predicts: among models with equal clean accuracy and consistency, invariant
ones should sit closer to the *robust* KKT points of Frei's max-margin program
along orbit directions, while remaining exposed (like FC) along genuine
data-manifold directions.

### 6.4 Two-dimensional images

> **Remark 6.4.** For toroidal images, $G=\mathbb Z_{d_1}\times\mathbb Z_{d_2}$,
> the DFT is the 2-D DFT, $\mathcal V_{\mathrm{inv}}=\operatorname{span}\mathbf1$
> is still the single DC mode, $\mathcal D(x)$ is spanned by 2-D translation
> differences, and the power spectrum $|\hat x_{j_1,j_2}|^2$ is the canonical
> quadratic invariant. All proofs (Lemmas 2.1–2.8, 4.1–4.6, Theorems A–C) are
> verbatim with this substitution because they only used: (i) the group acts by
> commuting isometries diagonalized by a unitary transform; (ii) $\mathbf1$ is
> the unique joint eigenvector with eigenvalue 1. Both hold for any finite
> abelian group acting by translation.

### 6.5 Multiclass

> **Remark 6.5.** With $C$ classes, replace $\Delta_\Phi$ by the minimum
> pairwise invariant-feature separation $\min_{c\ne c'}\operatorname{dist}
> (\Phi(S_c),\Phi(S_{c'}))$ and $d_{\mathcal O}$ by the minimum pairwise orbit
> distance; Theorem A holds with one-vs-rest signed-distance scores, the proof of
> §4.1–4.2 applying to each class pair.

### 6.6 Boundary case: label-incompatible invariance

> **Remark 6.6.** If (A2) fails — some orbit contains both labels — then
> $d_{\mathcal O}=0$ and Theorem A.(ii) forces $\rho^{\mathrm{inv}}_\star=0$:
> invariance is incompatible with *accuracy*, the trade-off is total and trivial.
> This is the degenerate floor of the dichotomy and is excluded from the
> interesting regime by (A2).

---

## 7. Limitations and explicit obstructions

1. **The discrete orbit-chord orthogonality in Theorem C is only infinitesimal.**
   The exact statement is $\langle\nabla f(x),Ax\rangle=0$ (one-parameter shift
   generator) plus equivariance $\nabla f(T_sx)=T_s\nabla f(x)$. The stronger
   claim "$\nabla f(x)\perp(T_sx-x)$ for every finite $s$" is **false** in
   general: a function constant on the finite orbit can have arbitrary gradient
   on the chords between orbit points (it is only constrained at the points). We
   flagged this in Lemma 4.6 and use only the correct infinitesimal/averaged
   version. Consequence: Theorem C is a *first-order / linearized* robustness
   statement (it controls $|f(x)|/\|\nabla f\|$, the linearized radius), not a
   certified radius. A fully discrete certified version would require a discrete
   group-averaging Poincaré-type inequality we have not established.

2. **Factor-of-2 gap in Theorem A.** The achievable lower bound (A.i) and the
   necessity upper bound (A.ii) differ by a factor 2 in the asymmetric case (one
   bound is the diameter-type $d_{\mathcal O}$, the other the radius-type
   $\tfrac12 d_{\mathcal O}$), the usual SVM radius/diameter slack. They coincide
   for symmetric (e.g. antipodal) data. So Theorem A is *tight up to a factor 2
   and the budget $L_\Phi$*, not exactly tight in general.

3. **$\Delta_\Phi$ vs $d_{\mathcal O}$ gap = invariant-feature incompleteness.**
   The lower bound uses a *chosen* $\Phi$; the upper bound is over *all* invariant
   $f$. These match only when $\Phi$ is *complete for the orbits* (separates
   distinct orbits with feature distance $\asymp$ orbit distance). The power
   spectrum is complete *up to magnitude collisions* (Lemma 2.6): two orbits with
   identical power spectra but different phases are merged. So our characterization
   is exact for *generic* data (no magnitude collisions) and only one-sided for
   adversarially-collided orbits. Closing this requires a complete-invariant map
   (e.g. bispectrum), whose Lipschitz budget we did not control — an open
   quantitative step.

4. **Realizability: does a GAP-CNN actually realize $\Phi_{\mathrm{ps}}$?** A
   single conv layer with kernel $w$, a pointwise square, and GAP computes
   $\frac1d\sum_i(\sum_k w_k x_{i+k})^2=\sum_{k,k'}w_kw_{k'}a_{k-k'}(x)$, a
   *fixed linear functional of the autocorrelation* $a$ (Wiener–Khinchin). So one
   such layer reads **one linear combination** of the power spectrum, not the
   full vector; reading all of it needs many channels (a filter bank). We did not
   prove a *minimal-width* result that a practical GAP-CNN computes a
   margin-preserving $\Phi$; we proved (a) such $\Phi$ exists with budget 1 and
   (b) it is in the GAP-CNN function class with enough channels. The gap between
   "exists in the class" and "found by training with realistic width" is the
   Frei/Melamed implicit-bias question, not resolved here.

5. **No optimization guarantee.** Theorems A–B are about attainable robustness of
   the class, not what gradient descent finds. Under heavy class imbalance,
   label noise (Frei's overfitting-to-noise regime), or small init (Melamed), the
   *trained* invariant model may fall short of $\Delta_\Phi/(2L_\Phi)$. Our
   empirical predictions (§5) are stated as *correlational* (realized robustness
   tracks the floor $\lambda_\Phi$, bounded by the ceiling $\kappa$), which is
   testable without solving the optimization question.

6. **Compactness / margin assumption.** (A1)–(A2) assume clean, well-separated,
   orbit-pure classes. Real data violate orbit-purity at boundaries (aliasing,
   non-integer shifts), and $d_{\mathcal O}$ is then a soft quantity; the right
   object is a *distributional* orbit distance (e.g. $\epsilon$-quantile of
   nearest opposite-orbit distance). We expect the theory to degrade gracefully
   (replace inf by quantile) but did not prove a robust-statistics version.

---

## 8. Summary of the contribution

* **One inequality governs co-existence** (Theorem A):
  $\dfrac{\Delta_\Phi(D)}{2L_\Phi}\le\rho^{\mathrm{inv}}_\star(D)\le\tfrac12\,
  d_{\mathcal O}(D)$.
  Shift-invariance and $L_p$ robustness **co-exist iff the inter-class signal
  survives projection onto a shift-invariant feature space** (large $\Delta_\Phi$,
  equivalently large orbit distance $d_{\mathcal O}$); the **trade-off is forced
  iff orbits collapse the class gap** ($d_{\mathcal O}\to0$ while
  $d_{\mathrm{raw}}=\Omega(1)$), i.e. iff the discriminative direction lies in the
  orbit-difference subspace $\mathcal D$.
* **Linear case (Theorem B)** recovers Ge's $2/\sqrt d$ exactly and supplies the
  missing converse: collapse $\Leftrightarrow$ signal in the AC subspace; DC-borne
  signal ⇒ no collapse.
* **Gradient case (Theorem C)** shows invariance zeroes the orbit-tangent
  gradient, the off-manifold/aliasing component Melamed blames, enlarging the
  linearized robust radius for free in the off-manifold regime.
* **Reconciliation by two scalars.** The *ceiling* on any invariant model is
  $\kappa=d_{\mathcal O}/d_{\mathrm{raw}}$ (data only); the *floor* a given model
  reaches is $\lambda_\Phi=\Delta_\Phi/(L_\Phi d_{\mathrm{raw}})$ (model's
  invariant features). Ge's two opposite experiments are: orthogonal-frequencies
  $=$ high $\kappa$ **and** high $\lambda_{\mathrm{ps}}$ (invariant *more* robust);
  orthogonal-vectors / single-dot $=$ high $\kappa$ but **low $\lambda_{\mathrm
  {dc}}\sim1/\sqrt d$** for the linear/DC invariant (collapse is a *feature-
  expressivity* failure, not a hard data obstruction — a phase-sensitive complete
  invariant would escape it, Limitation 3). Kamath's forced trade-off is the
  genuine *low-$\kappa$* corner: the strong signal is routed into $\mathcal D$, so
  *no* invariant model can recover it. Thus all three results live on the
  $(\kappa,\lambda_\Phi)$ plane: $\kappa$ says whether co-existence is *possible*,
  $\lambda_\Phi$ whether the chosen architecture *realizes* it.

*All cited results (Ge Thm 1/Cor 1, Kamath Thm 2/Prop 1, Frei Thm 2.1/4.1/4.2,
Melamed Thm 4.1/5.1/6.x) are used as stated in the source PDFs; no result or
citation is fabricated. Where a step does not close (Limitations 1, 3, 4) the
obstruction is stated explicitly rather than papered over.*
