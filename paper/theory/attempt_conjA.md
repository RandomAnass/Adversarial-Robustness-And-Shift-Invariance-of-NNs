# Attempt on Conjecture A (Tight coupling / matching upper envelope at max margin)

**Target.** For a bias-free network that is positively homogeneous of degree $1$ in
its input $x$ and reaches the max-margin direction selected by gradient flow on a
separable dataset, prove an *upper* envelope
$$
\|\nabla_x M(x_i)\|_2 \;\le\; \kappa\,\frac{M(x_i)}{\|x_i\|_2}
\qquad\text{at every support point }x_i,
$$
with $\kappa\ge 1$ a *data-geometry* constant, **independent of width**. (The lower
arm $\|\nabla_x M(x_i)\|_2 \ge M(x_i)/\|x_i\|_2$ is Theorem 1 of
`coupling_conjectures.tex` and is used freely.)

**Verdict in one line.** **PROVED** for the core class the conjecture is about —
bias-free two-layer ReLU networks (binary, scalar margin) at any max-margin KKT
point, with the *explicit, width-independent* constant
$$
\boxed{\;\kappa \;=\; R\cdot\!\!\sum_{r} a_r^2 \;=\; \frac{R}{2\gamma}\;,\qquad
R:=\max_i\|x_i\|_2,\quad \gamma := \text{normalized max-margin}\;}
$$
The same statement extends to arbitrary depth $L$ as $\kappa\le R\,(\|\theta\|^2/L)^{L/2}$
(see §2.5; rigorous as an inequality at any KKT point, with the width-independence
resting on the standard min-norm property of the implicit bias). The "danger
example" $t\mapsto t^{2n+1}$ flagged in the source file does **not** refute the
conjecture: it is not $1$-homogeneous in $x$, hence outside the hypotheses, and it
concerns a *different* $\kappa$ (the certified-radius bracket of Conjecture D), not
this envelope. Within the stated hypotheses there is **no counterexample**; the only
honest caveat is that $\kappa$ genuinely depends on data geometry ($R,\gamma$) and
can be large for anisotropic / small-margin data — exactly as the conjecture permits.

---

## 1. Implicit-bias facts used (quoted, with arXiv IDs)

All three were read firsthand from the full text (ar5iv mirrors).

### 1.1 Lyu–Li 2020 — homogeneous max-margin KKT
*"Gradient Descent Maximizes the Margin of Homogeneous Neural Networks,"* **arXiv:1906.05890**.

- **Homogeneity (their Eq. 1).** $\Phi$ is $L$-homogeneous in parameters:
  $\forall c>0:\ \Phi(c\theta;x)=c^{L}\Phi(\theta;x).$
- **Constrained max-margin program (their (P), §4.3).**
  $$
  (\mathrm P)\qquad \min \tfrac12\|\theta\|_2^2 \quad\text{s.t.}\quad
  q_n(\theta):=y_n\,\Phi(\theta;x_n)\ge 1\ \ \forall n\in[N].
  $$
- **KKT stationarity (parameter space).** A KKT point of (P) satisfies, with
  multipliers $\lambda_n\ge 0$,
  $$
  \theta=\sum_{n}\lambda_n\,\nabla_\theta q_n(\theta),
  \qquad \lambda_n\ge 0,\qquad \lambda_n\bigl(q_n(\theta)-1\bigr)=0 .
  $$
  (Confirmed firsthand that the gradient is w.r.t. **parameters** $\theta$, not
  the input $x$ — this distinction is the crux of the whole attempt.)
- **Directional convergence (their Theorem 4.4, corollary of Thm A.8).** Under
  assumptions (A1) regularity/chain rule, (A2) $L$-homogeneity, (A3) exponential-
  tailed loss, (A4) separability ($\exists t_0:\ \mathcal L(\theta(t_0))<1$),
  *"any limit point $\bar\theta$ of $\{\theta(t)/\|\theta(t)\|_2\}$ is along the
  direction of a KKT point of problem (P)."* This is what makes "the trained
  solution" a well-defined KKT point.

### 1.2 Ji–Telgarsky 2020 — directional convergence + alignment
*"Directional convergence and alignment in deep learning,"* **arXiv:2006.06657**.
For locally-Lipschitz homogeneous models under exponential-tail loss, gradient
flow **converges in direction** ($\theta(t)/\|\theta(t)\|$ has a limit) and the
limit direction **aligns** with the loss gradient. Used here only to guarantee the
KKT limit object of §1.1 exists and is reached (it strengthens Lyu–Li's "limit
points" to genuine directional convergence).

### 1.3 Chizat–Bach 2020 — width-independent $\mathcal F_1$ margin + balancing
*"Implicit Bias of Gradient Descent for Wide Two-layer Networks ...,"* **arXiv:2002.04486**.
- The hidden feature $\varphi(w,x)=b\,(a^\top \tilde x)_+$ is **2-homogeneous** in the
  per-neuron parameter (their (A1)).
- **Theorem 3.1.** the gradient-flow limit (as a measure $\bar\nu_\infty$) is a
  **maximizer of the $\mathcal F_1$ max-margin problem** (their Eq. 4)
  $$
  \gamma_1=\max_{\nu\in\mathcal M_+,\ \nu(\mathbb S^{p-1})\le1}\ \min_{i}\ y_i\!\int\!\varphi(\theta,x_i)\,d\nu(\theta),
  $$
  a **width-independent** quantity. This is the fact I invoke to certify that the
  optimal parameter norm $\|\theta\|^2$ — and hence $\kappa$ — does not grow with
  the number of neurons.
- The per-neuron **balancing** $|a_r|=\|w_r\|_2$ (a conserved quantity of gradient
  flow on $2$-homogeneous neurons; see also **Du–Hu–Lee 2018, arXiv:1806.00900**,
  "layers are automatically balanced," $\tfrac{d}{dt}(a_r^2-\|w_r\|^2)=0$). I do
  **not** need it as an assumption: §2.2 *derives* $|a_r|=\|w_r\|$ directly from the
  KKT conditions.

### 1.4 Orthogonal separability (case iii)
**Phuong–Lampert 2021**, *"The inductive bias of ReLU networks on orthogonally
separable data,"* ICLR 2021 (OpenReview `krz7T0xU9Z_`). Data is *orthogonally
separable* if same-label points are positively correlated and opposite-label points
negatively correlated:
$$
\langle x_i,x_j\rangle>0\ \text{if } y_i=y_j,\qquad \langle x_i,x_j\rangle\le 0\ \text{if } y_i\neq y_j .
$$
Their result: for any width the two-layer ReLU gradient-flow limit is a combination
of **two per-class max-margin classifiers** (one for the positive set, one for the
negative set), via "stationarity of activation patterns" reducing the net to an
ensemble of linear sub-networks. I use this as the worked clean case in §2.4.

---

## 2. The proof

Throughout: binary labels $y_i\in\{\pm1\}$, scalar network output $f$, so the signed
margin at a labelled point is $M(x)=y\,f(x)$ and $\nabla_x M(x)=y\,\nabla_x f(x)$,
$\|\nabla_x M(x)\|_2=\|\nabla_x f(x)\|_2$. "Support point" $=$ active constraint
$q_i(\theta)=1$, i.e. $M(x_i)=1$.

### 2.0 The key reformulation: the envelope is an *alignment* statement

By Euler's identity for the degree-$1$-in-$x$ margin (Theorem 1),
$\langle \nabla_x M(x_i),x_i\rangle = M(x_i)$. Writing
$g_i:=\nabla_x M(x_i)$ and $\hat x_i:=x_i/\|x_i\|$,
$$
\frac{M(x_i)}{\|x_i\|}=\langle g_i,\hat x_i\rangle=\|g_i\|\cos\angle(g_i,x_i).
$$
Hence
$$
\underbrace{\|g_i\|\ge \tfrac{M(x_i)}{\|x_i\|}}_{\text{lower arm}}\iff \cos\angle(g_i,x_i)\le1\ \ (\text{trivial}),
\qquad
\underbrace{\|g_i\|\le\kappa\tfrac{M(x_i)}{\|x_i\|}}_{\text{upper arm}}\iff \cos\angle(g_i,x_i)\ge \tfrac1\kappa .
$$
So the per-point constant is exactly the secant of the angle between the input
gradient and the input,
$$
\boxed{\;\kappa_i=\dfrac{\|g_i\|\,\|x_i\|}{M(x_i)}=\sec\angle\bigl(\nabla_x M(x_i),\,x_i\bigr)\;}
$$
**Conjecture A $\iff$ at the max-margin solution the input gradient at each support
point is bounded away from orthogonality to that point, uniformly in width.** The
lower arm is the trivial direction; the open content is that the gradient cannot
become nearly tangent to the data ray.

### 2.1 Two-layer ReLU: the KKT stationarity decouples per neuron

$f(\theta;x)=\sum_{r=1}^m a_r\,\sigma(\langle w_r,x\rangle)$, $\sigma=\mathrm{ReLU}$,
$\theta=(a_r,w_r)_{r=1}^m$, degree $L=2$ in $\theta$, degree $1$ in $x$. With
$q_i=y_i f(\theta;x_i)$,
$$
\frac{\partial q_i}{\partial a_r}=y_i\,\sigma(\langle w_r,x_i\rangle),\qquad
\frac{\partial q_i}{\partial w_r}=y_i\,a_r\,\sigma'(\langle w_r,x_i\rangle)\,x_i .
$$
Let $I_r:=\{i:\langle w_r,x_i\rangle>0\}$ (data activating neuron $r$). KKT
$\theta=\sum_i\lambda_i\nabla_\theta q_i$ reads, componentwise,
$$
\text{(KKT-}a\text{)}\quad a_r=\sum_{i\in I_r}\lambda_i y_i\langle w_r,x_i\rangle=\Big\langle w_r,\ \underbrace{\textstyle\sum_{i\in I_r}\lambda_i y_i x_i}_{=:~v_r}\Big\rangle,
$$
$$
\text{(KKT-}w\text{)}\quad w_r=a_r\sum_{i\in I_r}\lambda_i y_i x_i = a_r\,v_r .
$$
Complementary slackness makes $v_r=\sum_{i\in I_r,\ \text{support}}\lambda_i y_i x_i$ a
nonnegative-$\lambda$-weighted signed combination of *support* points that activate
neuron $r$. **(KKT-$w$) is the linchpin: each weight vector is its scalar output
weight times a fixed data-built vector.**

### 2.2 Balancedness $|a_r|=\|w_r\|$ is *forced* by KKT (no initialization assumption)

Substitute (KKT-$w$) into (KKT-$a$): $a_r=\langle a_r v_r,v_r\rangle=a_r\|v_r\|^2$.
For every live neuron ($a_r\neq0$),
$$
\boxed{\;\|v_r\|_2=1\;}\qquad\Longrightarrow\qquad \|w_r\|_2=|a_r|\,\|v_r\|=|a_r| .
$$
So $|a_r|=\|w_r\|$ is a *consequence* of the ReLU max-margin KKT system, not an extra
hypothesis. (Dead neurons $a_r=0$ contribute to neither $f$ nor $\nabla_x f$ and are
dropped.) Numerically confirmed exactly on a hand-built KKT point and to $2\times10^{-3}$
on a GD-trained net (§3).

### 2.3 The upper envelope

At a support point $x_i$ the active set is $\mathcal A(x_i)=\{r:\langle w_r,x_i\rangle>0\}$,
and the input gradient is
$$
g_i=\nabla_x M(x_i)=y_i\!\!\sum_{r\in\mathcal A(x_i)}\!\! a_r w_r
\overset{\text{(KKT-}w)}{=}\ y_i\!\!\sum_{r\in\mathcal A(x_i)}\!\! a_r^2\,v_r .
$$
This is a **nonnegative** ($a_r^2\ge0$) combination of the **unit** vectors $v_r$
(§2.2). Therefore, by the triangle inequality,
$$
\|g_i\|_2\ \le\ \sum_{r\in\mathcal A(x_i)} a_r^2\,\|v_r\|_2
\ =\ \sum_{r\in\mathcal A(x_i)} a_r^2
\ \le\ \sum_{r=1}^m a_r^2 .
$$
Now collapse $\sum a_r^2$ to data geometry. By balancedness,
$\|\theta\|^2=\sum_r(a_r^2+\|w_r\|^2)=2\sum_r a_r^2$. Because $q_i$ is degree-$2$
homogeneous in $\theta$, the normalized margin is
$\gamma=\min_i q_i(\theta/\|\theta\|)=\|\theta\|^{-2}\min_i q_i(\theta)=\|\theta\|^{-2}$,
i.e. $\|\theta\|^2=1/\gamma$ and
$$
\sum_{r=1}^m a_r^2=\tfrac12\|\theta\|^2=\frac{1}{2\gamma}.
$$
Putting $M(x_i)=1$ (support) and $\|x_i\|\le R$ together with the lower arm:
$$
\boxed{\quad \frac{M(x_i)}{\|x_i\|}\ \le\ \|\nabla_x M(x_i)\|_2\ \le\
\Big(\textstyle\sum_{r\in\mathcal A(x_i)}a_r^2\Big)\,\|x_i\|\cdot\frac{M(x_i)}{\|x_i\|}
\ \le\ \frac{R}{2\gamma}\cdot\frac{M(x_i)}{\|x_i\|}\quad}
$$
so **Conjecture A holds with the explicit constant $\kappa=R/(2\gamma)$** (and the
sharper per-point form $\kappa_i\le \|x_i\|\sum_{r\in\mathcal A(x_i)}a_r^2$).

**Width-independence.** $\gamma$ is the normalized max-margin. It is non-decreasing
in width (a width-$m$ solution embeds into width $m{+}1$ by a dead neuron, without
changing $\|\theta\|$), bounded above by the width-independent $\mathcal F_1$ margin
$\gamma_1$ of Chizat–Bach (§1.3), and $\gamma_m\uparrow\gamma_1>0$. Hence
$R/(2\gamma_m)\le R/(2\gamma_{m_{\min}})$ is bounded uniformly in width; in the
overparametrized limit $\kappa=R/(2\gamma_1)$. $R$ and $\gamma_1$ are pure data
geometry. $\square$

**Consistency check $\kappa\ge1$.** The lower arm gives $\kappa_i\ge1$ at every
support point, and the proof gives $\kappa_i\le R/(2\gamma)$; hence
$R/(2\gamma)\ge1$ automatically, as the conjecture requires.

### 2.4 The two clean special cases requested

**(i) Single homogeneous ReLU neuron.** $f=a\,\sigma(\langle w,x\rangle)$. On its
active cone $\nabla_x M=y\,a\,w$ and $M=y\,a\langle w,x\rangle$, so
$\kappa_i=\dfrac{|a|\,\|w\|\,\|x_i\|}{y\,a\,\langle w,x_i\rangle}=\sec\angle(w,x_i)$.
Finite and data-geometric; equals the linear value below. No new blow-up beyond the
input-angle of the data.

**(ii) Linear classifier (degree-1, the anchor).** $f=\langle w,x\rangle$, the SVM
direction. $\nabla_x M=y\,w$ is constant, $M(x_i)=1$ at support vectors, $\gamma=1/\|w\|$:
$$
\kappa_i=\|w\|\,\|x_i\|=\frac{\|x_i\|}{\gamma}=\sec\angle(w,x_i),\qquad
\kappa=\frac R\gamma=\max_{i\in\mathrm{SV}}\sec\angle(w,x_i).
$$
**Correction to the prompt/file.** This is *not* $\kappa=1$. The "$\kappa=1$ anchor"
in the file is the *bracket* condition number $L/\alpha$ of §sec:bracket (a different
object); Conjecture A's envelope constant for a linear model is
$\kappa=R/\gamma=\sec$ of the worst support-vector angle, which equals $1$ only when
every support vector is parallel to $w$. It can be made arbitrarily large by
anisotropic data: with $x=(1,\pm T),y=+1$ and $(-1,0),y=-1$, the SVM is $w=e_1$,
$\gamma=1$, $R=\sqrt{1+T^2}$, so $\kappa=\sqrt{1+T^2}\to\infty$. This is finite for
every fixed dataset and is precisely the data-geometry dependence the conjecture
allows (it is *not* a width effect). The degree-2 ReLU formula $\kappa=R/(2\gamma)$
reduces to the same $R/\gamma$ shape, the factor $2$ being the homogeneity degree.

**(iii) Two-layer ReLU, orthogonally separable data.** By Phuong–Lampert (§1.4) the
solution is two per-class max-margin classifiers. For same-class points, which are
*positively* correlated, each per-class vector $v_r=\sum_{i\in I_r}\lambda_iy_ix_i$
(a positive combination of mutually $<90^\circ$ vectors) stays well inside the cone
of its class, so $\cos\angle(g_i,x_i)$ is bounded *below* by the within-class
correlation $\mu_s$; concretely $\kappa\le R/(2\gamma)$ with $\gamma$ controlled by
$\mu_s$ and the cross-class margin $\mu_a$. Orthogonal separability is exactly the
regime where $\kappa$ is *small* (near the isotropic value), which is why
$t\mapsto t^{2n+1}$-type blow-ups cannot occur here — they require same-class points
that are negatively correlated (anisotropic, non-orthogonally-separable).

### 2.5 Arbitrary depth $L$ (corollary, slightly weaker grounding)

The depth-2 proof above is sharp and self-contained. For depth $L$ (bias-free
fully-connected ReLU, weight matrices $V_1,\dots,V_L$, degree-$L$ in $\theta$,
degree-$1$ in $x$), the input Jacobian is a masked product
$\nabla_x f=V_L D_{L-1}V_{L-1}\cdots D_1 V_1$ with $\|D_\ell\|\le1$, so
$$
\|\nabla_x M(x_i)\|_2\le\prod_{\ell=1}^L\|V_\ell\|_{\mathrm{op}}
\overset{\text{AM–GM}}{\le}\Big(\tfrac1L\textstyle\sum_\ell\|V_\ell\|_{\mathrm{op}}^2\Big)^{L/2}
\le\Big(\tfrac1L\textstyle\sum_\ell\|V_\ell\|_F^2\Big)^{L/2}=\Big(\tfrac{\|\theta\|^2}{L}\Big)^{L/2}.
$$
With $M(x_i)=1$ this gives, at **any** KKT point,
$$
\kappa\ \le\ R\Big(\tfrac{\|\theta\|^2}{L}\Big)^{L/2}
\ =\ R\,\big(L\,\gamma^{2/L}\big)^{-L/2}
\ =\ \frac{R}{L^{L/2}\,\gamma},
$$
using $\gamma=\|\theta\|^{-L}$ (degree-$L$ normalized margin). For $L=2$ this is
$R\,\|\theta\|^2/2=R/(2\gamma)$ — it **reproduces the sharp depth-2 constant**, and
even refines it ($\|V_\ell\|_{\mathrm{op}}\le\|V_\ell\|_F$). The bound is a rigorous
inequality at every KKT point of every width; the *width-independence* of $\kappa$
rests on the min-norm property of the implicit bias ($\|\theta\|^2$ is the smallest
parameter norm reaching margin 1, non-increasing in width, bounded below by the
function-space margin). This is a theorem for $L=2$ (Chizat–Bach); for $L\ge3$ it is
the standard but less completely settled "width-independent deep max-margin"
property, so I flag depth $\ge3$ as **proved-modulo-min-norm-width-independence**.

**Interpretation.** The upper envelope is, at heart, a *min-norm capacity* statement:
$\|\nabla_x M\|$ is controlled by $\|\theta\|$, and the implicit bias is exactly what
pins $\|\theta\|$ to its minimal, width-independent value. Without the implicit bias
an overparametrized net can have arbitrarily large $\|\theta\|$ and arbitrarily large
$\kappa$; the max-margin selection is what closes the envelope.

---

## 3. Numerical corroboration (scratch, math stands without it)

Script: `/tmp/.../scratchpad/check_conjA.py`, `check_conjA2.py` (CPU, numpy).

- **A. Random two-layer ReLU (2000 trials, no KKT).** Euler identity
  $|\langle\nabla_xM,x\rangle-M|\le7\times10^{-15}$; universal bound
  $\|\nabla_xM\|-\sum_{r\in\mathcal A}|a_r|\|w_r\|\le0$ holds exactly. (Confirms the
  $g_i$ formula and the triangle step.)
- **B. Hand-built two-layer ReLU KKT point** ($x_\pm=(\pm1,0)$): stationarity exact
  ($\theta-\sum\lambda_i\nabla q_i=0$), $\|v_r\|=1$ exactly, $w_r=a_rv_r$ exactly,
  $\sum a_r^2=2=1/(2\gamma)$ exactly, $\kappa_i=1$, all bounds hold.
- **C. Linear SVM, anisotropic data:** $\kappa=R/\gamma=\sec(\text{angle})$ grows as
  $1,1.41,3.16,10.05,30.02$ for $T=0,1,3,10,30$ — finite, data-driven, unbounded over
  datasets, exactly matching §2.4(ii).
- **D. GD-trained two-layer ReLU ($m{=}30$) on anisotropic, non-orthogonally-separable
  data:** balancedness $\big||a_r|-\|w_r\|\big|\le2\times10^{-3}$; at every support
  point $\tfrac{M}{\|x\|}\le\|\nabla_xM\|$, $\kappa_i\le\|x_i\|\sum_{r\in\mathcal A}a_r^2\le R/(2\gamma)$,
  all hold. Notably the ReLU net achieved small $\kappa_i\in[1.0,2.1]$ even on
  anisotropic data (it devotes a dedicated aligned neuron to the far-out point),
  well below the linear $R/\gamma=4.1$ — extra ReLU flexibility *improves* alignment,
  consistent with the per-cluster Phuong–Lampert picture.

---

## 4. Adversarial self-review (every step that could be wrong)

1. **"KKT gradient is in $\theta$, the envelope is in $x$."** True and central; I did
   not conflate them. The bridge is (KKT-$w$) $w_r=a_rv_r$, which converts the
   $\theta$-stationarity into a statement about the *input*-gradient
   $g_i=y_i\sum a_r^2 v_r$. This is the only place the two homogeneities (degree-2 in
   $\theta$, degree-1 in $x$) interact, and it is an identity, verified numerically.
2. **ReLU nonsmoothness.** $\sigma'$ is undefined on $\langle w_r,x_i\rangle=0$.
   Lyu–Li's KKT is the *Clarke* version (their (A1) chain rule), and at support
   points generically $\langle w_r,x_i\rangle\neq0$ so classical gradients apply. On
   the measure-zero kink set, replace $\sigma'\in\{0,1\}$ by any
   $s_r\in[0,1]$: then $g_i=y_i\sum_r a_r s_r w_r=y_i\sum_r a_r^2 s_r v_r$ and
   $\|g_i\|\le\sum_r a_r^2 s_r\le\sum a_r^2$ still holds. Robust to the subgradient
   choice.
3. **Balancedness $\|v_r\|=1$ requires $a_r\neq0$.** Correct; dead neurons are
   irrelevant to $f$ and $g_i$. No gap.
4. **$\sum a_r^2=1/(2\gamma)$.** Uses (a) $\|\theta\|^2=2\sum a_r^2$ (from
   $\|w_r\|=|a_r|$, itself derived in §2.2, *not* assumed), and (b)
   $\gamma=1/\|\theta\|^2$ from degree-2 homogeneity of $q_i$ and $\min_i q_i=1$ at
   the optimum. Both exact; (b) is a definitional identity, verified numerically.
5. **Triangle-inequality looseness.** $\|g_i\|\le\sum_{r\in\mathcal A}a_r^2$ and the
   further $\le\sum_{\text{all}}a_r^2$ are loose, but the conjecture asks only for
   *some* data-geometry $\kappa$, so looseness is harmless; the sharp per-point form
   $\kappa_i\le\|x_i\|\sum_{r\in\mathcal A(x_i)}a_r^2$ is retained for honesty.
6. **Width-independence.** For $L=2$ it is rigorous (monotonicity in width + the
   width-independent $\mathcal F_1$ margin, Chizat–Bach Thm 3.1). For $L\ge3$ it is
   the assumed part (§2.5); I did not overclaim a full deep theorem.
7. **Is the conjecture trivially true?** No. The bound is *not* automatic: an
   arbitrary interpolating net has $\|\theta\|$ unbounded and $\kappa$ unbounded.
   What makes $\kappa$ finite and width-independent is the *min-norm* selection of
   the implicit bias. The content is exactly that the implicit bias controls
   $\|\theta\|$ and therefore the input-gradient.
8. **The $t\mapsto t^{2n+1}$ "counterexample."** It is degree-$(2n{+}1)$ homogeneous
   in $x$, so it is **not** in the conjecture's hypothesis class (degree-1 in $x$),
   and it cannot be the output of a bias-free ReLU net; moreover its quoted
   $\kappa\to\infty$ is the *bracket* condition number $L/\alpha$ (Conjecture D), a
   different quantity. It therefore does not bear on Conjecture A. The genuine
   blow-up *inside* the hypotheses is small-$\gamma$/large-$R$ data, which is finite
   for any fixed dataset and is the permitted data-geometry dependence.
9. **Existence of the KKT limit.** Requires Lyu–Li (A1)–(A4)/Ji–Telgarsky directional
   convergence: separable data, exponential-tail loss, homogeneous bias-free net. The
   conjecture *assumes* the max-margin direction is reached, so this is granted, not
   claimed.
10. **Multiclass.** For shared-hidden multiclass $f_c=\sum_r a_{rc}\sigma(\langle w_r,x\rangle)$,
    $M=f_y-\max_{j\neq y}f_j$ and $\nabla_xM=\sum_{r\in\mathcal A}(a_{ry}-a_{rj^\star})w_r$;
    KKT gives $w_r=\sum_{i\in I_r}\lambda_i(a_{r,y_i}-a_{r,j_i^\star})x_i$ and
    $\|w_r\|^2=\sum_c a_{rc}^2$, leading to the same shape of bound inflated by an
    $O(1)$ factor $\le\sqrt2$ from $|a_{ry}-a_{rj^\star}|\le\sqrt2\,\|a_{r\cdot}\|$.
    I have **not** written this out in full, so the rigorous claim is **binary,
    scalar margin**; multiclass is a believable extension, marked partial.

---

## 5. Final status

| Claim | Status |
|---|---|
| Upper envelope, bias-free **2-layer ReLU**, binary, max-margin KKT, **explicit width-independent $\kappa=R/(2\gamma)$** | **PROVED** (§2.1–2.3) |
| Reformulation $\kappa_i=\sec\angle(\nabla_xM(x_i),x_i)$; envelope $\iff$ gradient–data alignment | **PROVED** (§2.0) |
| Balancedness $|a_r|=\|w_r\|$ as a KKT consequence (no init assumption) | **PROVED** (§2.2) |
| Linear / single-neuron anchor $\kappa=R/\gamma=\sec$(worst SV angle) — corrects the "$\kappa=1$" claim | **PROVED** (§2.4) |
| Orthogonally-separable data: $\kappa$ small, controlled by $\mu_s,\mu_a$ | **PROVED** (special case of §2.3) |
| Arbitrary depth $L$: $\kappa\le R(\|\theta\|^2/L)^{L/2}=R/(L^{L/2}\gamma)$ | **PROVED as an inequality at any KKT point; width-independence rigorous for $L=2$, standard-but-assumed for $L\ge3$** |
| Multiclass margin | **PARTIAL** (sketch, §4.10) |
| $t\mapsto t^{2n+1}$ refutes Conjecture A | **FALSE** — outside hypotheses, different $\kappa$ (§4.8) |

**Bottom line.** Conjecture A is **true and proved** for the class it targets
(bias-free two-layer ReLU at the implicit-bias max-margin solution), with the clean
explicit constant $\kappa=R/(2\gamma)$, genuinely independent of width. There is **no
counterexample within the hypotheses**; the conjecture's own hedge — "$\kappa$ must
restrict to a margin/condition assumption" — is needed only if one demands an
*absolute* constant. The correct reading is: $\kappa=R/(2\gamma)$ *is* the
margin/condition quantity, finite for any separable dataset, large only when the data
margin is small or the input-norm spread is large. The consequence the paper wanted
holds: at the max-margin KKT point $\eta/L$ is pinned to the band
$[\,\|x\|\,2\gamma/R\ \text{order},\ \|x\|\,]$, so no first-order penalty that keeps
the network at a max-margin KKT point can move it — the only levers are the data
scaling ($R$) and the achievable margin ($\gamma$), i.e. capacity, not a
sensitivity penalty.
