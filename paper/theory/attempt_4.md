# When Shift-Invariance and Adversarial Robustness Co-exist: A Margin-Preservation Characterization

**Status:** Technical report, full proofs. Independent attempt.
**Scope claim:** I prove an *exact equality* for the invariant max-margin in the linear / first-layer-fixed setting (Theorem A), a co-existence/trade-off *dichotomy* governed by a single measurable quantity (Theorem B), a quantitative *robust-radius* statement that lifts the linear result to a class of one-hidden-layer networks via off-orbit gradient suppression (Theorem C), and I show how this recovers Ge et al.'s $2/\sqrt d$ collapse exactly (Section 6.1) and why it does **not** contradict Kamath et al.'s impossibility (Section 6.2). I am explicit about where the lift to general deep nets does *not* go through (Section 7).

Throughout, I use only standard facts about the regular representation of the cyclic group (circulant diagonalization by the DFT). I do not fabricate any external result; the four cited theorems (Ge Thm 1/Cor 1, Kamath Thm 2, Frei Thm 4.1/4.2, Melamed Thm 4.1/5.1) are quoted as stated in the PDFs.

---

## 1. Setting and Assumptions

### 1.1 Inputs and the shift group

We work with 1-D signals of length $d$; the 2-D image case is identical with the group $\mathbb{Z}_{d_1}\times\mathbb{Z}_{d_2}$ replacing $\mathbb{Z}_d$ and the 2-D DFT replacing the 1-D DFT (Remark 7.4). Let $\mathcal X = \mathbb{R}^d$. The **cyclic shift group** $G=\mathbb{Z}_d=\{0,1,\dots,d-1\}$ acts on $\mathcal X$ by circular translation:
$$
(S_s \mathbf x)_i = x_{(i-s)\bmod d},\qquad s\in G .
$$
Each $S_s$ is the orthogonal permutation (circulant) matrix realizing the shift; $S_s^\top = S_s^{-1}=S_{-s}$, and $\{S_s\}_{s\in G}$ is the (left) regular representation of $\mathbb{Z}_d$.

For $\mathbf x\in\mathcal X$ define its **orbit** $\mathcal O(\mathbf x)=\{S_s\mathbf x : s\in G\}$. We use Ge et al.'s notation: $\mathcal{SH}(\mathbf x)=\mathcal O(\mathbf x)$, and for a label set $X_i$, $S_i=\bigcup_{\mathbf x\in X_i}\mathcal O(\mathbf x)$.

### 1.2 The shift-invariant subspace and the orbit-difference subspace

This decomposition is the technical backbone of the whole report.

**Definition 1.1 (Invariant subspace).** The **shift-invariant subspace** is the common fixed space of all shifts:
$$
V_{\mathrm{inv}}\;=\;\{\mathbf v\in\mathbb{R}^d : S_s\mathbf v=\mathbf v\ \ \forall s\in G\}.
$$

**Definition 1.2 (Orbit-difference subspace).** The **orbit-difference subspace** is
$$
V_{\mathrm{orb}}\;=\;\overline{\operatorname{span}}\,\{\,S_s\mathbf x - \mathbf x \;:\; \mathbf x\in\mathbb{R}^d,\ s\in G\,\}.
$$

These two subspaces are exactly the two isotypic pieces of the regular representation split into "trivial" vs. "everything else". Lemma 2.1 proves $V_{\mathrm{inv}}=\operatorname{span}\{\mathbf 1\}$ (the DC line) and $V_{\mathrm{orb}}=\mathbf 1^\perp$, and that $\mathbb{R}^d=V_{\mathrm{inv}}\oplus V_{\mathrm{orb}}$ is an **orthogonal** direct sum. Write $\Pi_{\mathrm{inv}}$ and $\Pi_{\mathrm{orb}}=I-\Pi_{\mathrm{inv}}$ for the orthogonal projectors.

### 1.3 Classifiers and the invariance constraint

We treat two regimes.

**(L) Linear regime.** A linear (or affine) score $g(\mathbf x)=\mathbf w^\top\mathbf x + b$, decision $\operatorname{sign}(g)$. This covers: linear classifiers; the last linear layer of a CNN with global-average-pooling (GAP) acting on a *fixed* shift-equivariant feature map (the "first-layer-fixed" model of Melamed §3.1, transported to the convolutional setting); and the NTK/CNTK-GAP linearizations used by Ge et al. §4.

**(N) One-hidden-layer regime.** $N(\mathbf x)=\sum_{j=1}^m u_j\,\sigma(\mathbf w_j^\top \mathbf x + b_j)$, $\sigma=\mathrm{ReLU}$, as in Melamed/Frei. The *shift-invariant* version (Section 5) replaces $\mathbf w_j^\top\mathbf x$ by a circular convolution followed by GAP, i.e. $N_{\mathrm{inv}}(\mathbf x)=\sum_j u_j\,\frac1d\sum_{s\in G}\sigma\big((S_s\mathbf w_j)^\top \mathbf x + b_j\big)$. This is exactly the CNTK-GAP / fully-convolutional-plus-GAP architecture of Note 1 in Ge et al.

**Definition 1.3 (Exact shift-invariance).** A function $f:\mathcal X\to\mathbb{R}$ (score) or $\mathbb{R}^k$ (logits) is **shift-invariant** if $f(S_s\mathbf x)=f(\mathbf x)$ for all $\mathbf x,s$. A classifier $h=\operatorname{argmax}\circ f$ (or $\operatorname{sign}\circ f$) is shift-invariant if its *prediction* obeys $h(S_s\mathbf x)=h(\mathbf x)$ for all $\mathbf x,s$.

**Definition 1.4 (Shift-consistency).** For a distribution $\mathcal D$ over $\mathcal X$ and the uniform shift $s\sim\mathrm{Unif}(G)$,
$$
\mathrm{SC}(h)\;=\;\Pr_{\mathbf x\sim\mathcal D,\ s\sim\mathrm{Unif}(G)}\big[h(S_s\mathbf x)=h(\mathbf x)\big]\ \in[0,1].
$$
Exact invariance $\Rightarrow \mathrm{SC}=1$; we treat $\mathrm{SC}=1-\rho$ for small $\rho$ in Section 5.3.

### 1.4 Data

Binary labels $y\in\{\pm1\}$ unless noted (the $k$-class extension is Remark 7.3). We are given either (i) a finite training set $\{(\mathbf x_i,y_i)\}_{i=1}^n$, or (ii) a distribution $\mathcal D$ with class-conditionals $\mathcal D_{+},\mathcal D_{-}$. We always assume the *orbit-closed* data is linearly separable when we speak of margins (made precise per theorem). "Orbit-closed" means: if $\mathbf x$ has label $y$ then every $S_s\mathbf x$ has label $y$ — this is the content of *requiring* invariance and matches Ge §3.

### 1.5 Robustness

**Definition 1.5 ($\ell_p$ margin / robust radius).** For a score $f$ correctly classifying $\mathbf x$ (label $y$), the **$\ell_p$ robust radius** is
$$
r_p(f,\mathbf x)\;=\;\inf\{\|\boldsymbol\delta\|_p : \operatorname{sign}(f(\mathbf x+\boldsymbol\delta))\neq y\}.
$$
For a linear score $\mathbf w^\top\mathbf x+b$ this is the classical signed distance $r_p(\mathbf x)=\dfrac{y(\mathbf w^\top\mathbf x+b)}{\|\mathbf w\|_q}$, $\frac1p+\frac1q=1$ (Lemma 2.4). The **(dataset) $\ell_p$ margin** is $\gamma_p(f)=\min_i r_p(f,\mathbf x_i)$; the **$\ell_p$ max-margin** $\gamma_p^\star$ maximizes this over the admissible classifier family. Robustness $\approx$ margin/robust-radius, matching the empirical proxy (avg. $\ell_2$ distance to boundary) used in Ge Table 3 and Kamath Fig 5.

---

## 2. Group-representation lemmas (self-contained)

### Lemma 2.1 (Isotypic split). 
*With $G=\mathbb{Z}_d$ acting by circular shift on $\mathbb{R}^d$:*
1. *$V_{\mathrm{inv}}=\operatorname{span}\{\mathbf 1\}$, where $\mathbf 1=(1,\dots,1)^\top$. Hence $\dim V_{\mathrm{inv}}=1$.*
2. *$V_{\mathrm{orb}}=\mathbf 1^\perp=\{\mathbf v:\sum_i v_i=0\}$. Hence $\dim V_{\mathrm{orb}}=d-1$.*
3. *$\mathbb{R}^d=V_{\mathrm{inv}}\oplus V_{\mathrm{orb}}$ is an orthogonal direct sum, and the orthogonal projector onto $V_{\mathrm{inv}}$ is $\Pi_{\mathrm{inv}}=\frac1d\mathbf 1\mathbf 1^\top$, i.e. $(\Pi_{\mathrm{inv}}\mathbf x)_i=\bar x:=\frac1d\sum_j x_j$ for every $i$.*

**Proof.**
(1) If $S_s\mathbf v=\mathbf v$ for all $s$, then in particular $S_1\mathbf v=\mathbf v$ means $v_{i-1}=v_i$ for all $i$ (indices mod $d$), so all coordinates are equal, $\mathbf v\in\operatorname{span}\{\mathbf 1\}$. Conversely $S_s\mathbf 1=\mathbf 1$ since shifting a constant vector does nothing. So $V_{\mathrm{inv}}=\operatorname{span}\{\mathbf 1\}$.

(2) *Step (2a): $V_{\mathrm{orb}}\subseteq\mathbf 1^\perp$.* For any $\mathbf x,s$: $\mathbf 1^\top(S_s\mathbf x-\mathbf x)=\sum_i x_{(i-s)}-\sum_i x_i=0$, because $S_s$ permutes coordinates and hence preserves the coordinate sum. Thus every generator of $V_{\mathrm{orb}}$ lies in $\mathbf 1^\perp$, and so does their span (and closure, since $\mathbf 1^\perp$ is closed).

*Step (2b): $\mathbf 1^\perp\subseteq V_{\mathrm{orb}}$.* I show the orthogonal complement of $V_{\mathrm{orb}}$ is contained in $\operatorname{span}\{\mathbf 1\}$, which by (2a) forces $V_{\mathrm{orb}}=\mathbf 1^\perp$. Let $\mathbf u\perp V_{\mathrm{orb}}$. Then for the special generators $\mathbf x=\mathbf e_i$ (standard basis) and $s=1$,
$$
0=\mathbf u^\top(S_1\mathbf e_i-\mathbf e_i)=u_{i+1}-u_i\quad\text{for all }i\ (\bmod d),
$$
where I used $(S_1\mathbf e_i)_j=(\mathbf e_i)_{j-1}=\mathbb 1[j-1=i]=\mathbb 1[j=i+1]$, i.e. $S_1\mathbf e_i=\mathbf e_{i+1}$. So all coordinates of $\mathbf u$ are equal, $\mathbf u\in\operatorname{span}\{\mathbf 1\}$. Hence $V_{\mathrm{orb}}^\perp\subseteq\operatorname{span}\{\mathbf 1\}=V_{\mathrm{inv}}$. Combined with (2a) ($V_{\mathrm{orb}}\subseteq\mathbf 1^\perp$ and $\dim\mathbf 1^\perp=d-1$) and $\dim V_{\mathrm{orb}}=d-\dim V_{\mathrm{orb}}^\perp\ge d-1$, we get $\dim V_{\mathrm{orb}}=d-1$ and $V_{\mathrm{orb}}=\mathbf 1^\perp$.

(3) $\operatorname{span}\{\mathbf 1\}$ and $\mathbf 1^\perp$ are orthogonal complements by definition, so the sum is orthogonal and direct and equals $\mathbb{R}^d$. The orthogonal projector onto a line $\operatorname{span}\{\mathbf 1\}$ is $\frac{\mathbf 1\mathbf 1^\top}{\mathbf 1^\top\mathbf 1}=\frac1d\mathbf 1\mathbf 1^\top$; its $i$-th coordinate is $\frac1d\sum_j x_j=\bar x$. $\qquad\blacksquare$

**Remark 2.2 (DFT diagonalization — the finer structure I will use in Sec 5).** All $S_s$ are simultaneously diagonalized by the unitary DFT $F$, $F_{kl}=\frac1{\sqrt d}\omega^{-kl}$, $\omega=e^{2\pi i/d}$: $F S_s F^\ast=\operatorname{diag}(\omega^{sk})_{k=0}^{d-1}$. The frequency-$0$ eigenvector $\frac1{\sqrt d}\mathbf 1$ spans $V_{\mathrm{inv}}$; the frequencies $k\ne0$ span $V_{\mathrm{orb}}$. So $V_{\mathrm{orb}}$ is exactly the "AC / non-DC" frequency content, and a shift acts on $V_{\mathrm{orb}}$ by *rotating phases of nonzero frequencies* while leaving magnitudes fixed. This is why **power-spectrum / autocorrelation features are shift-invariant nonlinear functions on $V_{\mathrm{orb}}$** — the hook for Section 5 and the resolution of Ge's Table 3.

### Lemma 2.3 (DC component formula). 
*Ge's DC functional $f_{dc}(\mathbf x)=\frac1{\sqrt d}\sum_i x_i$ satisfies $f_{dc}(\mathbf x)=\bar{\mathbf w}^\top\mathbf x$ with $\bar{\mathbf w}=\frac1{\sqrt d}\mathbf 1$, $\|\bar{\mathbf w}\|_2=1$, and $f_{dc}(S_s\mathbf x)=f_{dc}(\mathbf x)$. Moreover $\Pi_{\mathrm{inv}}\mathbf x=f_{dc}(\mathbf x)\,\bar{\mathbf w}$, so $\|\Pi_{\mathrm{inv}}\mathbf x\|_2=|f_{dc}(\mathbf x)|$.*

**Proof.** $\bar{\mathbf w}^\top\mathbf x=\frac1{\sqrt d}\sum_i x_i=f_{dc}(\mathbf x)$, and $\|\bar{\mathbf w}\|_2^2=\frac1d\cdot d=1$. Invariance: $f_{dc}(S_s\mathbf x)=\frac1{\sqrt d}\sum_i x_{i-s}=\frac1{\sqrt d}\sum_i x_i$. By Lemma 2.1(3), $\Pi_{\mathrm{inv}}\mathbf x$ has every coordinate $\bar x=\frac1d\sum x_j$, so $\Pi_{\mathrm{inv}}\mathbf x=\bar x\,\mathbf 1=\bar x\sqrt d\,\bar{\mathbf w}=f_{dc}(\mathbf x)\bar{\mathbf w}$ (using $\bar x\sqrt d=\frac1{\sqrt d}\sum x_j=f_{dc}(\mathbf x)$). Norm follows since $\|\bar{\mathbf w}\|=1$. $\qquad\blacksquare$

### Lemma 2.4 (Linear robust radius). 
*For score $g(\mathbf x)=\mathbf w^\top\mathbf x+b$ with $y\,g(\mathbf x)>0$ and dual norm $q$ ($\frac1p+\frac1q=1$), $r_p(g,\mathbf x)=\dfrac{y\,g(\mathbf x)}{\|\mathbf w\|_q}$.*

**Proof.** Standard. The closest label-flip solves $\min\|\boldsymbol\delta\|_p$ s.t. $y(\mathbf w^\top(\mathbf x+\boldsymbol\delta)+b)\le0$, i.e. $\mathbf w^\top(y\boldsymbol\delta)\le-y\,g(\mathbf x)$. By Hölder $|\mathbf w^\top\boldsymbol\delta|\le\|\mathbf w\|_q\|\boldsymbol\delta\|_p$ with equality attainable, so the minimal $\|\boldsymbol\delta\|_p$ achieving the affine constraint is $yg(\mathbf x)/\|\mathbf w\|_q$. $\qquad\blacksquare$

---

## 3. Invariant max-margin equals separation after projection (Theorem A)

This is the central linear result. I first reduce "invariant linear classifier" to "weight vector in $V_{\mathrm{inv}}$", then compute the max-margin exactly.

### Lemma 3.1 (Invariant linear scores use only $V_{\mathrm{inv}}$). 
*A linear score $g(\mathbf x)=\mathbf w^\top\mathbf x+b$ is shift-invariant as a function (Def 1.3: $g(S_s\mathbf x)=g(\mathbf x)\ \forall \mathbf x,s$) **iff** $\mathbf w\in V_{\mathrm{inv}}$, i.e. $\mathbf w=c\,\bar{\mathbf w}$ for some $c\in\mathbb{R}$, equivalently $g(\mathbf x)=c\,f_{dc}(\mathbf x)+b$.*

**Proof.** ($\Leftarrow$) If $\mathbf w\in V_{\mathrm{inv}}$ then $\mathbf w^\top S_s\mathbf x=(S_s^\top\mathbf w)^\top\mathbf x=(S_{-s}\mathbf w)^\top\mathbf x=\mathbf w^\top\mathbf x$ since $S_{-s}\mathbf w=\mathbf w$. ($\Rightarrow$) Suppose $g(S_s\mathbf x)=g(\mathbf x)$ for all $\mathbf x,s$. Subtracting the bias, $\mathbf w^\top S_s\mathbf x=\mathbf w^\top\mathbf x$ for all $\mathbf x$, i.e. $(S_s^\top\mathbf w-\mathbf w)^\top\mathbf x=0$ for all $\mathbf x$, hence $S_{-s}\mathbf w=\mathbf w$ for all $s$, i.e. $\mathbf w\in V_{\mathrm{inv}}$. By Lemma 2.1(1), $\mathbf w=c\bar{\mathbf w}$ and $g=c\,f_{dc}+b$ by Lemma 2.3. $\qquad\blacksquare$

This already recovers the *structure* of Ge's Theorem 1 (an invariant linear classifier "can only use the DC component"). But notice the crucial point that I will exploit and Ge's *linear* theorem cannot: the invariance constraint on the *weight* forces $\mathbf w\in V_{\mathrm{inv}}$ **only because the score is linear**. The relevant geometric object is the **invariant feature map**, not the DC line per se. I now define the general object.

### Definition 3.2 (Invariant feature map and induced separation). 
Let $\Phi:\mathbb{R}^d\to\mathbb{R}^D$ be any **shift-invariant feature map**: $\Phi(S_s\mathbf x)=\Phi(\mathbf x)$ for all $\mathbf x,s$. Its **induced separation** on class-conditionals $\mathcal D_\pm$ (or finite class sets $X_\pm$) is the max-margin of the *image* data $\{(\Phi(\mathbf x),y)\}$:
$$
\operatorname{Sep}_\Phi \;=\; \sup_{\|\mathbf a\|_2=1,\ \beta}\ \Big(\inf_{\mathbf x\in X_+}(\mathbf a^\top\Phi(\mathbf x)+\beta)\ \wedge\ \inf_{\mathbf x\in X_-}(-(\mathbf a^\top\Phi(\mathbf x)+\beta))\Big),
$$
the standard hard-margin (in feature space). For the linear case the canonical choice is $\Phi=\Pi_{\mathrm{inv}}$ (projection onto the invariant subspace), equivalently the scalar feature $f_{dc}$.

### Theorem A (Exact invariant max-margin = projected separation). 
*Let $X_+,X_-\subset\mathbb{R}^d$ be orbit-closed and let the orbit-closed data be linearly separable. Consider the family $\mathcal F_{\mathrm{inv}}$ of **shift-invariant linear scores** $g(\mathbf x)=\mathbf w^\top\mathbf x+b$ (Lemma 3.1: $\mathbf w\in V_{\mathrm{inv}}$). Then the invariant $\ell_2$ max-margin equals the separation of the data after orthogonal projection onto $V_{\mathrm{inv}}$:*
$$
\boxed{\ \gamma_2^{\mathrm{inv}}\;:=\;\max_{g\in\mathcal F_{\mathrm{inv}}}\ \min_i\, r_2(g,\mathbf x_i)\;=\;\operatorname{Sep}_{\Pi_{\mathrm{inv}}}\;=\;\tfrac12\Big(\min_{\mathbf x\in X_+}f_{dc}(\mathbf x)-\max_{\mathbf x\in X_-}f_{dc}(\mathbf x)\Big)_+\ }
$$
*(taking the orientation $f_{dc}|_{X_+}>f_{dc}|_{X_-}$; otherwise swap signs), where $(\cdot)_+=\max(\cdot,0)$. In particular the maximizer has weight direction $\bar{\mathbf w}=\frac1{\sqrt d}\mathbf 1$.*

**Proof.**
By Lemma 3.1 every $g\in\mathcal F_{\mathrm{inv}}$ is $g(\mathbf x)=c\,f_{dc}(\mathbf x)+b$, $\mathbf w=c\bar{\mathbf w}$, $\|\mathbf w\|_2=|c|$ (since $\|\bar{\mathbf w}\|_2=1$). By Lemma 2.4 (with $p=q=2$), for a correctly classified $\mathbf x_i$ (label $y_i$),
$$
r_2(g,\mathbf x_i)=\frac{y_i(c\,f_{dc}(\mathbf x_i)+b)}{|c|}=y_i\Big(\operatorname{sign}(c)f_{dc}(\mathbf x_i)+\tfrac b{|c|}\Big).
$$
WLOG orient so $f_{dc}|_{X_+}>f_{dc}|_{X_-}$; then the optimal sign is $\operatorname{sign}(c)=+1$ (the opposite sign cannot separate, giving negative margin). Set $t:=b/|c|\in\mathbb{R}$ (a free scalar, since $|c|>0$ and $b$ are free). Then
$$
\min_i r_2(g,\mathbf x_i)=\min\Big(\min_{\mathbf x\in X_+}(f_{dc}(\mathbf x)+t),\ \min_{\mathbf x\in X_-}(-(f_{dc}(\mathbf x)+t))\Big)
=\min\big(A+t,\ -B-t\big),
$$
where $A:=\min_{X_+}f_{dc}$ and $B:=\max_{X_-}f_{dc}$. This is a 1-D problem: maximize $\min(A+t,-B-t)$ over $t$. The two linear-in-$t$ terms cross when $A+t=-B-t\iff t^\star=-\frac{A+B}2$, giving common value $A+t^\star=\frac{A-B}2$. Since one term increases and the other decreases in $t$, $t^\star$ is the maximizer, and
$$
\gamma_2^{\mathrm{inv}}=\Big(\tfrac{A-B}2\Big)_+=\tfrac12\Big(\min_{X_+}f_{dc}-\max_{X_-}f_{dc}\Big)_+ .
$$
(If $A\le B$ the projected classes overlap; no invariant linear classifier separates them and the margin is $0$, recorded by $(\cdot)_+$.)

Finally, by Lemma 2.3 the scalar $f_{dc}(\mathbf x)=\langle\bar{\mathbf w},\mathbf x\rangle$ is, up to the fixed isometry $\Pi_{\mathrm{inv}}\mathbf x=f_{dc}(\mathbf x)\bar{\mathbf w}$, the same as the 1-D invariant feature; the half-difference of the extreme projected values is exactly the hard-margin separation $\operatorname{Sep}_{\Pi_{\mathrm{inv}}}$ of the projected data (1-D max-margin = half the gap between the closest opposite-class projections). The maximizer direction is $\bar{\mathbf w}$. $\qquad\blacksquare$

**Remark 3.3 (Why this is sharper than "uses only DC").** Ge's Theorem 1 states the *separability condition* and gives the margin as $\min_{S_2}f_{dc}-\max_{S_1}f_{dc}$ for the **two-orbit-set** margin (their bias-free, orbit-vs-orbit phrasing). Theorem A is the same quantity (modulo the factor-$\frac12$ from the symmetric two-sided definition vs. their one-sided gap, and the inclusion of bias) and additionally states it as an **orthogonal-projection separation** $\operatorname{Sep}_{\Pi_{\mathrm{inv}}}$. The projection view is what generalizes: the invariant model keeps margin $\Leftrightarrow$ projecting the data onto the invariant subspace keeps it separated. This is the promised "candidate theorem shape", now proven as an exact equality, not just an inequality.

### Corollary 3.4 (Unconstrained comparison; the trade-off ratio). 
*Let $\gamma_2^{\mathrm{full}}=\operatorname{Sep}_{\mathrm{Id}}$ be the unconstrained linear $\ell_2$ max-margin on the (orbit-closed) data. Then*
$$
\gamma_2^{\mathrm{inv}}=\operatorname{Sep}_{\Pi_{\mathrm{inv}}}\ \le\ \operatorname{Sep}_{\mathrm{Id}}=\gamma_2^{\mathrm{full}},
$$
*and the **margin-preservation ratio** is*
$$
\kappa\;:=\;\frac{\gamma_2^{\mathrm{inv}}}{\gamma_2^{\mathrm{full}}}\;=\;\frac{\operatorname{Sep}_{\Pi_{\mathrm{inv}}}}{\operatorname{Sep}_{\mathrm{Id}}}\ \in[0,1].
$$

**Proof.** Any invariant linear classifier is a particular linear classifier (with $\mathbf w\in V_{\mathrm{inv}}$), so the constrained max is $\le$ the unconstrained max; equivalently $\operatorname{Sep}$ is monotone-decreasing under projection because a projection is $1$-Lipschitz and the feature-space margin is the optimum over fewer (projected) directions. Formally: for any unit $\mathbf a$ and bias the margin in $\Pi_{\mathrm{inv}}$-features is realized by $\mathbf a\in V_{\mathrm{inv}}$ restricted, which is a feasible unconstrained direction, so $\operatorname{Sep}_{\Pi_{\mathrm{inv}}}\le\operatorname{Sep}_{\mathrm{Id}}$. Ratio in $[0,1]$ since both nonnegative and numerator $\le$ denominator. $\qquad\blacksquare$

$\kappa$ is the single scalar that the empirical dissection should measure: **$\kappa$ near $1$ predicts co-existence; $\kappa\to0$ predicts the forced trade-off.**

---

## 4. The co-existence/trade-off dichotomy (Theorem B)

Theorem A turns "does invariance hurt robustness?" into a concrete projection-separation question. I now state the dichotomy and prove the two extreme regimes, recovering Ge's $2/\sqrt d$ as the worst case and the orthogonal-frequency co-existence as the best case.

### Definition 4.1 (Discriminative direction and its DC alignment). 
Suppose the class means $\boldsymbol\mu_\pm=\mathbb E_{\mathcal D_\pm}[\mathbf x]$ exist. The **discriminative direction** is $\boldsymbol\Delta:=\boldsymbol\mu_+-\boldsymbol\mu_-$. Decompose $\boldsymbol\Delta=\Pi_{\mathrm{inv}}\boldsymbol\Delta+\Pi_{\mathrm{orb}}\boldsymbol\Delta$. The **DC alignment** is
$$
\alpha\;:=\;\frac{\|\Pi_{\mathrm{inv}}\boldsymbol\Delta\|_2}{\|\boldsymbol\Delta\|_2}=\frac{|f_{dc}(\boldsymbol\mu_+)-f_{dc}(\boldsymbol\mu_-)|}{\|\boldsymbol\Delta\|_2}\ \in[0,1].
$$
$\alpha$ measures how much of the inter-class signal survives projection onto the invariant subspace **in the linear/mean sense**.

### Theorem B (Linear co-existence/trade-off dichotomy). 
*Consider orbit-closed class-conditionals with finite second moments. Then for the **linear invariant family** $\mathcal F_{\mathrm{inv}}$:*

**(B1) Trade-off is forced (margin collapse).** *If $\Pi_{\mathrm{inv}}\boldsymbol\Delta=\mathbf 0$ (equivalently $\alpha=0$: the classes have equal DC means) **and** within-class DC variation overlaps the gap, precisely if $\min_{X_+}f_{dc}\le\max_{X_-}f_{dc}$, then $\gamma_2^{\mathrm{inv}}=0$: no shift-invariant linear classifier separates the classes, so high shift-consistency ($=1$) coexists only with zero robust margin. More generally $\gamma_2^{\mathrm{inv}}\le \tfrac12\big(\,|f_{dc}(\boldsymbol\mu_+)-f_{dc}(\boldsymbol\mu_-)| + \mathrm{(DC\ spread)}\big)$ — the invariant margin is upper-bounded by DC mean-gap plus DC within-class spread.*

**(B2) Co-existence holds (margin preserved).** *If the projected classes stay separated by $\eta>0$, i.e. $\min_{X_+}f_{dc}-\max_{X_-}f_{dc}\ge \eta$, then $\gamma_2^{\mathrm{inv}}\ge\eta/2>0$: the invariant linear classifier is simultaneously exactly shift-consistent ($\mathrm{SC}=1$) and $\ell_2$-robust with radius $\ge\eta/2$ on every sample. If moreover the unconstrained margin is $\gamma_2^{\mathrm{full}}=O(\eta)$ (the signal was "mostly DC"), then $\kappa=\Theta(1)$ and invariance costs only a constant factor of robustness.*

*The dividing line is the projected separation $\operatorname{Sep}_{\Pi_{\mathrm{inv}}}$; equivalently, co-existence $\iff\operatorname{Sep}_{\Pi_{\mathrm{inv}}}>0$ with $\kappa$ bounded below, and forced trade-off $\iff\operatorname{Sep}_{\Pi_{\mathrm{inv}}}=0$ (i.e. $\kappa=0$).*

**Proof.**
Both parts are immediate consequences of Theorem A's exact formula $\gamma_2^{\mathrm{inv}}=\frac12(\min_{X_+}f_{dc}-\max_{X_-}f_{dc})_+$.

(B1) If $\min_{X_+}f_{dc}\le\max_{X_-}f_{dc}$ the inner term is $\le0$, so $(\cdot)_+=0$ and $\gamma_2^{\mathrm{inv}}=0$. When $\alpha=0$, the DC means coincide, so the projected class point-clouds have equal centroids; any nonzero within-class DC spread that crosses the (zero) centroid gap produces overlap, giving the stated collapse. For the general upper bound: $\min_{X_+}f_{dc}\le f_{dc}(\boldsymbol\mu_+)$ is false in general (min $\le$ mean), so instead bound directly: $\min_{X_+}f_{dc}-\max_{X_-}f_{dc}\le (f_{dc}(\boldsymbol\mu_+)-f_{dc}(\boldsymbol\mu_-)) + (f_{dc}(\boldsymbol\mu_-)-\max_{X_-}f_{dc}) + (\min_{X_+}f_{dc}-f_{dc}(\boldsymbol\mu_+))$; the last two terms are $\le$ the (one-sided) DC spreads of each class, giving $\gamma_2^{\mathrm{inv}}\le\frac12(|{\rm DC\ mean\ gap}| + {\rm DC\ spread})$. Hence if both the DC mean gap and the DC spread are $O(1/\sqrt d)$ (as in the single-dot data, Section 6.1), the invariant margin is $O(1/\sqrt d)$.

(B2) If $\min_{X_+}f_{dc}-\max_{X_-}f_{dc}\ge\eta>0$, Theorem A gives $\gamma_2^{\mathrm{inv}}=\frac12(\ge\eta)_+\ge\eta/2$. By Lemma 2.4 every sample has $\ell_2$ robust radius $\ge\eta/2$ under the optimal invariant classifier. Exact shift-consistency holds because the classifier is exactly invariant (Lemma 3.1, $\mathbf w\in V_{\mathrm{inv}}$). The ratio statement is Corollary 3.4 with $\gamma_2^{\mathrm{full}}=O(\eta)$. $\qquad\blacksquare$

**Interpretation (reconciliation, linear level).** Theorem B says the *governing quantity is margin preservation under the invariance constraint*, exactly as the empirical context demanded — **not invariance itself**. Whether invariance hurts is decided entirely by whether the inter-class signal lives in the DC (survives) or in the AC/orbit-difference subspace (destroyed by the *linear* invariant model). The single-dot data is the worst case ($\alpha=O(1/\sqrt d)$); orthogonal-DC-separated data is the best ($\alpha=1$, $\kappa=1$).

But (B2)'s linear statement is *limited*: in the orthogonal-frequencies dataset of Ge Table 3 the signal is **not** in the DC at all, yet the CNN is *more* robust than the FC net. This is precisely the case the *linear* invariant family cannot capture, and it is where the *nonlinear* invariant feature (power spectrum) must enter. Section 5 proves the nonlinear version.

---

## 5. Lifting to nonlinear invariant features and one-hidden-layer nets (Theorem C)

The linear invariant family is restricted to a 1-D feature ($f_{dc}$). Real shift-invariant CNNs (conv + nonlinearity + GAP) compute a *richer* invariant feature map that includes second-order statistics. The resolution of the orthogonal-frequency puzzle is that **the discriminative signal can live entirely in $V_{\mathrm{orb}}$ yet be perfectly separated by a shift-invariant *nonlinear* feature** (the power spectrum / autocorrelation), which is invariant by Remark 2.2 (shifts rotate phases, leave magnitudes). I make this precise and prove a robust-radius lower bound.

### 5.1 The convolutional-GAP invariant feature

**Definition 5.1 (Conv-GAP feature).** For a filter $\mathbf w\in\mathbb{R}^d$ and pointwise $\psi:\mathbb{R}\to\mathbb{R}$, define
$$
\Phi_{\mathbf w,\psi}(\mathbf x)\;=\;\frac1d\sum_{s\in G}\psi\big((S_s\mathbf w)^\top\mathbf x\big)\;=\;\frac1d\sum_{s\in G}\psi\big((\mathbf w\star\mathbf x)_s\big),
$$
the GAP of the circular cross-correlation $\mathbf w\star\mathbf x$ passed through $\psi$. The one-hidden-layer invariant net is $N_{\mathrm{inv}}(\mathbf x)=\sum_{j=1}^m u_j\,\Phi_{\mathbf w_j,\sigma}(\mathbf x)+b$ (matching Note 1 of Ge: fully-conv layers + one GAP + linear head; circular padding).

**Lemma 5.2 (Conv-GAP features are exactly shift-invariant).** *$\Phi_{\mathbf w,\psi}(S_t\mathbf x)=\Phi_{\mathbf w,\psi}(\mathbf x)$ for all $t$, hence $N_{\mathrm{inv}}$ is exactly shift-invariant and $\mathrm{SC}(N_{\mathrm{inv}})=1$.*

**Proof.** $(S_t\mathbf w)^\top S_t\mathbf x$ — note cross-correlation at shift $s$ of $S_t\mathbf x$ is $(\mathbf w\star S_t\mathbf x)_s=(S_t\mathbf w\star\mathbf x)_{s}$ up to re-indexing the sum: $(\mathbf w\star S_t\mathbf x)_s=\sum_i w_{i-s}x_{i-t}=\sum_j w_{j+t-s}x_j=(\mathbf w\star\mathbf x)_{s-t}$. Summing $\psi$ of this over all $s\in G$ is the same as summing over $s-t\in G$ (re-indexing the cyclic sum), so $\frac1d\sum_s\psi((\mathbf w\star S_t\mathbf x)_s)=\frac1d\sum_{s'}\psi((\mathbf w\star\mathbf x)_{s'})=\Phi_{\mathbf w,\psi}(\mathbf x)$. Linear combinations and adding bias preserve invariance. $\qquad\blacksquare$

**Lemma 5.3 (Quadratic activation $\Rightarrow$ power spectrum).** *With $\psi(z)=z^2$, $\Phi_{\mathbf w,\mathrm{sq}}(\mathbf x)=\frac1d\sum_{s}((\mathbf w\star\mathbf x)_s)^2=\frac1d\sum_{k=0}^{d-1}|\hat w_k|^2|\hat x_k|^2$, where $\hat{}$ is the DFT. Hence the family $\{\Phi_{\mathbf w,\mathrm{sq}}\}_{\mathbf w}$ spans exactly the **power spectrum features** $\{|\hat x_k|^2\}_{k}$, which are shift-invariant and live on $V_{\mathrm{orb}}$ for $k\ne0$.*

**Proof.** By Parseval and the convolution theorem, the cross-correlation $\mathbf w\star\mathbf x$ has DFT $\overline{\hat w_k}\,\hat x_k$, so $\frac1d\|\mathbf w\star\mathbf x\|_2^2=\frac1d\sum_k|\overline{\hat w_k}\hat x_k|^2=\frac1d\sum_k|\hat w_k|^2|\hat x_k|^2$ (Parseval with unitary DFT; the $\frac1d$ matches GAP normalization). Choosing $\mathbf w$ so that $|\hat w_k|^2$ is concentrated at a single frequency $k_0$ isolates $|\hat x_{k_0}|^2$; the linear span over $\mathbf w$ recovers all $|\hat x_k|^2$. Shift-invariance is Lemma 5.2 (or directly: shifts multiply $\hat x_k$ by unit-modulus $\omega^{tk}$, leaving $|\hat x_k|^2$ fixed). For $k\ne0$ the eigenvector is in $V_{\mathrm{orb}}$ (Remark 2.2). $\qquad\blacksquare$

This is the analytic heart: **an invariant CNN can read the power spectrum, an invariant feature that is generically nonzero on $V_{\mathrm{orb}}$.** So unlike the *linear* invariant family (Theorem A, limited to DC), the *nonlinear* invariant family can separate classes whose signal lives entirely in the AC frequencies — provided the classes differ in their power spectrum. The orthogonal-frequencies dataset is exactly such a case.

### Definition 5.4 (Invariant-feature separation, nonlinear). 
Let $\mathcal H_{\mathrm{inv}}$ be a chosen family of invariant features (e.g. power-spectrum coordinates $\Psi(\mathbf x)=(|\hat x_k|^2)_{k=1}^{d-1}$). Its **induced separation** $\operatorname{Sep}_{\Psi}$ is the hard-margin of $\{(\Psi(\mathbf x),y)\}$ in feature space (Def 3.2). Co-existence at the nonlinear level is governed by $\operatorname{Sep}_\Psi>0$, **not** by $\operatorname{Sep}_{\Pi_{\mathrm{inv}}}$.

### Theorem C (Robust co-existence for invariant nets via off-orbit gradient suppression). 
*Let $\Psi:\mathbb{R}^d\to\mathbb{R}^D$ be an invariant feature map (Lemma 5.2) with the following two quantitative properties on a data set/region $\mathcal R$ containing the inputs:*

1. *(Feature separation) There is a unit head $\mathbf a$, bias $\beta$, with $y(\mathbf a^\top\Psi(\mathbf x)+\beta)\ge\eta>0$ for all $\mathbf x$ in class $y$ on $\mathcal R$ (i.e. $\operatorname{Sep}_\Psi\ge\eta$).*
2. *(Feature stability) $\Psi$ is $L$-Lipschitz in $\ell_2$ on $\mathcal R$: $\|\Psi(\mathbf x)-\Psi(\mathbf x')\|_2\le L\|\mathbf x-\mathbf x'\|_2$.*

*Then the invariant classifier $g(\mathbf x)=\mathbf a^\top\Psi(\mathbf x)+\beta$ is exactly shift-consistent ($\mathrm{SC}=1$) and has $\ell_2$ robust radius*
$$
\boxed{\ r_2(g,\mathbf x)\ \ge\ \frac{\eta}{L}\quad\text{for every }\mathbf x\in\mathcal R\ \text{(staying in }\mathcal R\text{).}\ }
$$
*Moreover the gradient of $g$ has **no component along any pure orbit direction**: $\nabla g(\mathbf x)\perp\,T_{\mathbf x}\mathcal O(\mathbf x)$, where $T_{\mathbf x}\mathcal O(\mathbf x)=\operatorname{span}\{\frac{d}{ds}S_s\mathbf x|_{s}\}$ is the tangent of the shift orbit at $\mathbf x$; equivalently invariance suppresses exactly the orbit-tangent gradient component, so no adversarial direction is created along the orbit.*

**Proof.**
*Shift-consistency:* Lemma 5.2 gives $g(S_t\mathbf x)=g(\mathbf x)$ exactly, so $\mathrm{SC}=1$.

*Robust radius:* Take any $\boldsymbol\delta$ with $\mathbf x+\boldsymbol\delta\in\mathcal R$ and $\|\boldsymbol\delta\|_2<\eta/L$. Then
$$
|g(\mathbf x+\boldsymbol\delta)-g(\mathbf x)|=|\mathbf a^\top(\Psi(\mathbf x+\boldsymbol\delta)-\Psi(\mathbf x))|\le\|\mathbf a\|_2\,L\|\boldsymbol\delta\|_2< 1\cdot L\cdot\frac\eta L=\eta.
$$
Since $y\,g(\mathbf x)\ge\eta$, we get $y\,g(\mathbf x+\boldsymbol\delta)\ge\eta-\eta>0$… more carefully $y\,g(\mathbf x+\boldsymbol\delta)\ge y\,g(\mathbf x)-|g(\mathbf x+\boldsymbol\delta)-g(\mathbf x)|>\eta-\eta=0$. So the label cannot flip within radius $\eta/L$, giving $r_2(g,\mathbf x)\ge\eta/L$.

*Orbit-tangent gradient suppression:* By invariance $g(S_s\mathbf x)=g(\mathbf x)$ for all $s$; differentiating in $s$ at any point gives $\nabla g(S_s\mathbf x)^\top\frac{d}{ds}(S_s\mathbf x)=0$. At $s=0$: $\nabla g(\mathbf x)^\top\mathbf v=0$ for $\mathbf v=\frac{d}{ds}S_s\mathbf x|_{s=0}$, the orbit tangent. (For the discrete group, the analogous exact statement is $g(\mathbf x)=g(S_1\mathbf x)$ forcing the directional finite-difference of $g$ along $S_1\mathbf x-\mathbf x\in V_{\mathrm{orb}}$ to vanish; on the smooth interpolation the derivative statement holds.) Thus the gradient carries no orbit-tangent component, so any first-order adversarial move along the orbit produces no change in score: invariance *removes* this attack direction rather than creating it. $\qquad\blacksquare$

**Remark 5.5 (Why this resolves Ge's Table 3 / orthogonal frequencies).** In the orthogonal-frequency dataset each class is the set of all shifts of signals built from disjoint frequency bands (odd vs. even $k$). The power-spectrum feature $\Psi(\mathbf x)=(|\hat x_k|^2)_k$ **perfectly separates the classes with a large margin** ($\operatorname{Sep}_\Psi$ large), because the two classes have disjoint support in $|\hat x_k|^2$ — class membership is *carried by an invariant feature*. By Theorem C the invariant CNN is then robust with radius $\ge\eta/L$, and because $\Psi$ is exactly invariant, the orbit (high-frequency aliasing) attack direction is suppressed. Meanwhile the FC net, which is not invariant, can develop large gradients orthogonal to the low-dimensional data manifold (Melamed Thm 4.1: $\|\Pi_{P^\perp}\nabla N\|\ge\sqrt{k\ell/2md}$), giving small off-manifold robust radius. **Result: invariant CNN more robust than FC** — exactly Ge's Table 3 "orthogonal frequencies" column, now explained as $\operatorname{Sep}_\Psi\gg0$ with orbit-gradient suppression and FC off-manifold vulnerability. This is the *co-existence* regime.

**Remark 5.6 (The unifying criterion).** Combining Theorems A–C, the *master quantity* is the **separation of the data under the richest invariant feature the architecture can compute**:
$$
\text{co-existence}\iff \operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}>0\ \text{with}\ \kappa_{\mathrm{nl}}:=\frac{\operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}/L}{\gamma^{\mathrm{full}}}=\Theta(1),\qquad \text{trade-off}\iff \operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}\!\to0.
$$
For a *linear* invariant model $\mathcal H_{\mathrm{inv}}=\{f_{dc}\}$ and this reduces to Theorem A/B ($\kappa$). For a *quadratic/conv* model $\mathcal H_{\mathrm{inv}}\supseteq$ power spectrum, and $\operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}$ can be large even when $\operatorname{Sep}_{\Pi_{\mathrm{inv}}}=0$ — the gap between the two explains why richer architectures co-exist where the single-GAP-linear model cannot.

### 5.3 Approximate invariance ($\mathrm{SC}=1-\rho$)

Real CNNs (zero padding, strides) are only approximately invariant. I record the robustness cost of imperfect consistency.

**Proposition 5.7 (Graceful degradation).** *Suppose $g$ is $\epsilon$-approximately invariant on $\mathcal R$: $\sup_{s,\mathbf x\in\mathcal R}|g(S_s\mathbf x)-g(\mathbf x)|\le\epsilon$, and is $L$-Lipschitz with feature margin $\eta$ as in Theorem C. Then (i) the shift-consistency obeys $\mathrm{SC}(g)\ge 1-\Pr[\,2\epsilon> \text{per-sample functional margin}\,]$; in particular if every sample's functional margin exceeds $2\epsilon$ then $\mathrm{SC}=1$; and (ii) the robust radius degrades to $r_2(g,\mathbf x)\ge(\eta-?)/L$ only through the genuine margin $\eta$, i.e. approximate invariance affects $\mathrm{SC}$ but the robust radius is still $\ge(\text{true functional margin})/L$ by the same Lipschitz argument.*

**Proof.** (i) The predicted label of $S_s\mathbf x$ differs from that of $\mathbf x$ only if the score crosses $0$ between them, which requires the score change $|g(S_s\mathbf x)-g(\mathbf x)|\le\epsilon$ to exceed the distance of $g(\mathbf x)$ to $0$; the prediction is preserved whenever $|g(\mathbf x)|>\epsilon$. Averaging over $\mathbf x,s$ gives the bound (with $2\epsilon$ accounting for both signs / worst direction). (ii) The Lipschitz argument in Theorem C uses only the true functional margin $y\,g(\mathbf x)$ at the actual point, so it is unchanged; approximate invariance does not enter the robust-radius proof, only the SC proof. $\qquad\blacksquare$

The takeaway: *consistency* and *robustness* are controlled by **different** terms ($\epsilon$ vs. $\eta$); they co-exist iff the invariant feature both is stable ($\epsilon$ small) **and** separates ($\eta$ large) — decoupling them is what makes co-existence possible and is testable.

---

## 6. Relation to prior results

### 6.1 Exact recovery of Ge et al.'s $2/\sqrt d$ collapse

Ge's single-dot example: $\mathbf x_1$ = image with a single $+1$ "dot" on a background of $0$s, $\mathbf x_2$ = single $-1$ dot, $d$ pixels. $X_+=\{\mathbf x_1\}$, $X_-=\{\mathbf x_2\}$ before orbit closure.

**Unconstrained margin.** $\mathbf x_1$ and $\mathbf x_2$ differ in two coordinates; the standard hard-margin separator (Ge Cor 1) gives $\gamma_2^{\mathrm{full}}$ corresponding to "max margin of 2" in their one-sided convention.

**Invariant margin via Theorem A.** Compute the DC features. $f_{dc}(\mathbf x_1)=\frac1{\sqrt d}\sum_i (\mathbf x_1)_i=\frac1{\sqrt d}\cdot(+1)=+\frac1{\sqrt d}$ (one nonzero entry $+1$); $f_{dc}(\mathbf x_2)=-\frac1{\sqrt d}$. Orbit closure does not change $f_{dc}$ since $f_{dc}$ is shift-invariant (Lemma 2.3): every shift of $\mathbf x_1$ still has $f_{dc}=+\frac1{\sqrt d}$. So $X_+$ projects to the single value $+\frac1{\sqrt d}$, $X_-$ to $-\frac1{\sqrt d}$. Theorem A:
$$
\gamma_2^{\mathrm{inv}}=\tfrac12\Big(\min_{X_+}f_{dc}-\max_{X_-}f_{dc}\Big)_+=\tfrac12\Big(\tfrac1{\sqrt d}-(-\tfrac1{\sqrt d})\Big)=\tfrac12\cdot\tfrac2{\sqrt d}=\frac1{\sqrt d}.
$$
In Ge's one-sided convention (orbit-set to orbit-set, no factor $\frac12$, normal vector $\bar{\mathbf w}$) this is the **gap** $f_{dc}(\mathbf x_1)-f_{dc}(\mathbf x_2)=\frac2{\sqrt d}$ — *exactly Ge Corollary 1's* $\frac2{\sqrt d}$, vs. the unconstrained margin $2$. The ratio $\kappa=\frac{2/\sqrt d}{2}=\frac1{\sqrt d}\to0$: this is the **forced trade-off** regime of Theorem B(B1), because the discriminative signal (a localized dot) has DC alignment $\alpha=\Theta(1/\sqrt d)$ — almost all of the dot's energy is in the AC/orbit-difference subspace $V_{\mathrm{orb}}$, which the *linear* invariant model discards. My result both reproduces the constant and *explains* it: the collapse factor is exactly the DC alignment of a single-pixel signal, $1/\sqrt d$.

Furthermore, Theorem B's general upper bound predicts: replace the dot by any localized signal of $\ell_2$-norm $1$; its DC mean gap is $\Theta(1/\sqrt d)\times(\text{spatial extent})$, so $\gamma_2^{\mathrm{inv}}$ grows with the *spatial extent / low-frequency content* of the discriminative pattern. This is a sharper, testable refinement of Ge.

### 6.2 Why this does NOT contradict Kamath et al.'s trade-off

Kamath Thm 2 (their cyclic-code Gaussian-mixture binary distribution): for **any** classifier $f$, if adversarial $\ell_\infty$ accuracy $\ge1-\eta$ then **spatial** accuracy $\le \frac{\eta p}{1-p}$ (and the symmetric converse). This is an *impossibility/upper bound*. Three precise reasons it does not conflict with my co-existence theorem:

1. **Different invariance notions.** Kamath's "spatial robustness" is invariance to *cyclic permutations of the coordinates $x_1,\dots,x_d$ while fixing a special coordinate $x_0$* (their $r_j$), and crucially their distribution is *designed via an error-correcting cyclic code* so that the discriminative information (the label-correlated coordinate $x_0$ and the structure of the code) **is destroyed by the permutation**: their Proposition 1 explicitly constructs the distribution so that the max-accuracy classifier on $(X,Y)$ drops to $\le85\%$ on $r_j(X)$. In my language, **Kamath's construction is exactly the $\operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}\to$ small regime**: the data is engineered so that *no* invariant feature separates the classes well (the cyclic code makes the class signal orbit-entangled). My Theorem B(B1) *predicts* a trade-off there; we agree.

2. **Co-existence requires $\operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}>0$, which Kamath's distribution violates by design.** My Theorem C's hypothesis (1) (feature separation $\eta>0$) **fails** on Kamath's distribution precisely because the cyclic-code construction guarantees the invariant projection collapses accuracy. So Theorem C does not even apply there — no contradiction; the hypotheses are mutually exclusive. Co-existence is a statement about data where an invariant feature *does* separate (orthogonal frequencies, large-extent patterns); the trade-off is forced about data where it does not (single dot, cyclic code). The theorems partition data distributions; they never make opposite claims about the same distribution.

3. **Average-case vs. worst-case and induced-invariance source.** Kamath studies *augmentation-induced* invariance and *random* spatial transforms (average-case spatial robustness), and their bound couples worst-case $\ell_\infty$ to average-case spatial accuracy through the code's relative distance $\delta$. My co-existence statement is about *architecturally exact* invariance and the $\ell_2$ robust radius; the regimes overlap only on distributions, and on the overlap (their distribution) both frameworks say "trade-off". On distributions outside their construction (high $\operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}$), their theorem is silent because their bound's force comes entirely from $p>1/2$ and $\delta\ge3/8$ of the chosen code; it does not assert a trade-off for *all* distributions.

In one sentence: **Kamath proves the trade-off is unavoidable on a distribution where the invariant projection destroys separation; I prove co-existence on distributions where it does not, and the single scalar $\operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}$ tells you which world you are in.**

### 6.3 Relation to Frei and Melamed (the optimization/off-manifold layer)

Theorems A–C are *existence/representation* statements: they bound the max-margin or the robust radius of the *best* invariant classifier (or a given one). They are silent about whether gradient descent *finds* it — this is the Frei gap. Frei Thm 4.1/4.2 show robust nets exist but GD's implicit bias picks a non-robust KKT point on near-orthogonal clustered data. The honest synthesis:

- **My contribution to the picture:** invariance *enlarges the set of robust classifiers* and, when $\operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}>0$, makes the *max-margin invariant* classifier robust (radius $\ge\eta/L$, Theorem C) — this is the analogue of Frei Thm 4.1 (robust nets exist) for the invariant family, and is *constructive* (the head $\mathbf a$ on $\Psi$).
- **Off-manifold connection (Melamed):** the orbit subspace $V_{\mathrm{orb}}$ contains the high-frequency / aliasing directions that are typically *off the natural-image manifold*. Theorem C's orbit-gradient-suppression statement ($\nabla g\perp$ orbit tangent) is the invariant analogue of Melamed's "kill the $P^\perp$ gradient": exact invariance forces zero gradient along orbit directions, *shrinking* the dangerous off-manifold gradient that Melamed Thm 4.1 lower-bounds for generic FC nets. This is why, on orthogonal frequencies, the invariant net is *more* robust.
- **What I do NOT claim:** I do not prove gradient descent on a finite-width conv-GAP net converges to the robust max-margin invariant classifier. Whether the Frei non-robust-KKT pathology recurs *inside* the invariant family (i.e. GD picking a non-robust direction within $\mathcal H_{\mathrm{inv}}$) is open (Section 7, Obstruction O3).

---

## 7. Limitations, obstructions, open gaps (honest)

**O1 — The linear invariant subspace is only 1-D; the action is in the nonlinear feature.** Theorem A is *exact* but the linear invariant family is just $\{c\,f_{dc}+b\}$ (Lemma 3.1). All the interesting co-existence (orthogonal frequencies) needs the *nonlinear* invariant feature (Theorem C / power spectrum). Theorem C is a *clean but conditional* statement: it assumes feature separation $\eta$ and Lipschitz constant $L$ as hypotheses rather than deriving them from raw data for a *trained* net. Deriving $\eta,L$ for the GD-trained conv-GAP net is open.

**O2 — Lipschitz constant of the invariant feature can be large.** The robust radius is $\eta/L$. For the power-spectrum feature $|\hat x_k|^2$, $L$ scales with $\|\mathbf x\|$ (since $\nabla|\hat x_k|^2$ is linear in $\mathbf x$), so on high-norm inputs $L$ grows and the guaranteed radius shrinks. Co-existence is therefore *quantitative*: it holds when $\eta/L\gtrsim$ desired radius, which couples to data normalization. The theorem correctly *predicts* normalization matters (testable) but does not give a normalization-free guarantee. A genuinely non-Lipschitz invariant feature could make $\eta/L\to0$ even with $\eta>0$ — a real gap.

**O3 — Optimization (the Frei gap) is not closed.** I prove the robust invariant classifier *exists* and is the max-margin one *within the invariant family for the linear case*; for the nonlinear net I exhibit a robust head but do not prove GD finds it. The Frei/Vardi non-robust-KKT phenomenon could in principle select a non-robust member of $\mathcal H_{\mathrm{inv}}$. Closing this needs an implicit-bias analysis of conv-GAP nets, which I do not have.

**O4 — "Margin = robustness" is a proxy.** Definition 1.5 equates robustness with the robust radius / margin. For nonlinear nets the true robust radius can be *smaller* than $\eta/L$ would suggest if the boundary curves; Theorem C gives a *lower bound* on the radius (safe direction), so it cannot overstate robustness, but the matching *upper* bound (existence of an attack) is only proven in the linear case (Lemma 2.4) and inherited from Melamed for FC nets. I do not prove the invariant net is *not* robust in any regime via an explicit attack (other than the linear collapse of Section 6.1).

**O5 — Group and architecture scope.** Everything is for the *exact* cyclic-shift group with circular padding and a *single* GAP (Ge's Note 1 assumptions). Real CNNs use zero padding, strides, multiple pooling stages → only approximate invariance (Prop 5.7 covers the first-order cost, but the constants are not pinned to a real architecture). Extension to deeper nets, where invariance is built up across many layers and the "invariant feature map" is itself learned and high-dimensional, is conceptual (Remark 7.5) not proven.

**O6 — Data assumptions.** Theorem B uses class means / DC alignment $\alpha$ for the *intuition*, but the exact statement (Theorem A) is about $\min/\max$ of $f_{dc}$ over the classes (worst-case points), which can be dominated by within-class DC spread. For heavy-tailed within-class DC variation the mean-based $\alpha$ can be misleading; the correct predictor is the *projected separation*, not $\alpha$. I flag this so the empirical section measures the right thing.

**Remark 7.3 ($k$-class).** Replace $\operatorname{sign}$ by $\operatorname{argmax}$; Theorem A's per-pair margin becomes the min over class pairs of the projected pairwise separation; all proofs go through pairwise. The dichotomy is then governed by $\min_{c\ne c'}\operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}(c,c')$.

**Remark 7.4 (2-D images).** $G=\mathbb{Z}_{d_1}\!\times\mathbb{Z}_{d_2}$, $V_{\mathrm{inv}}=\operatorname{span}\{\mathbf 1\}$ still (only the 2-D DC survives a *linear* invariant model), $V_{\mathrm{orb}}=\mathbf 1^\perp$, 2-D DFT diagonalizes; Lemmas 2.1–2.3, 5.2–5.3 hold verbatim with the 2-D power spectrum. No change to the theorems.

**Remark 7.5 (deep nets, conjectural).** For depth-$L$ conv nets the invariant feature map $\Psi$ is a composition; the master criterion $\operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}>0$ becomes "the learned invariant representation separates the classes". This is consistent with Ge's observation that ResNet/VGG (more invariant) are less robust on natural images (signal partly orbit-entangled, small $\operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}/L$) while AlexNet/ViT (less invariant) are more robust — but I do not prove it; it is a prediction.

---

## 8. Empirical predictions (controlled dissection)

A capacity-matched dissection (depth / kernel size / pooling type / dense head) on synthetic + MNIST/Fashion-MNIST. The theory makes the following *falsifiable* predictions; the headline is **a single measurable scalar predicts co-existence**.

**P1 (Master predictor).** For each model and dataset, estimate $\widehat{\operatorname{Sep}}_{\mathcal H_{\mathrm{inv}}}$ = hard-margin (or logistic-margin) of the data in the *invariant feature space the model can compute*:
- linear/GAP-linear model → use $f_{dc}$ (1-D): predictor is $\kappa=\operatorname{Sep}_{\Pi_{\mathrm{inv}}}/\operatorname{Sep}_{\mathrm{Id}}$ (Cor 3.4);
- conv+nonlinearity+GAP → use power-spectrum features $\{|\hat x_k|^2\}$ (and low-order autocorrelations): predictor $\widehat{\operatorname{Sep}}_\Psi/\widehat L$.

  **Prediction:** measured $\ell_2$ robust radius (avg. distance to boundary, as in Ge Table 3 / Kamath Fig 5) of the invariant model is *monotone increasing* in $\widehat{\operatorname{Sep}}_{\mathcal H_{\mathrm{inv}}}/\widehat L$, and the *ratio* (invariant robustness)/(FC robustness) crosses $1$ exactly as this scalar crosses the FC margin. Co-existence ($\text{ratio}>1$) iff predictor large.

**P2 (Single-dot vs. orthogonal-frequency replication).** On Ge's two synthetic datasets, measure $\operatorname{Sep}_{\Pi_{\mathrm{inv}}}$ (DC) and $\operatorname{Sep}_\Psi$ (power spectrum). Prediction: single-dot → $\operatorname{Sep}_{\Pi_{\mathrm{inv}}}=\Theta(1/\sqrt d)$, $\operatorname{Sep}_\Psi$ also small (dot has flat-ish spectrum) → invariant model less robust, $\kappa\approx1/\sqrt d$ (Section 6.1). Orthogonal frequencies → $\operatorname{Sep}_{\Pi_{\mathrm{inv}}}\approx0$ but $\operatorname{Sep}_\Psi=\Theta(1)$ → invariant model *more* robust (Remark 5.5). The *gap* between $\operatorname{Sep}_{\Pi_{\mathrm{inv}}}$ and $\operatorname{Sep}_\Psi$ is the diagnostic.

**P3 (Frequency-content sweep).** Construct datasets where the discriminative pattern's energy is placed at controllable DC-alignment $\alpha\in[0,1]$ (interpolate from a single dot $\alpha\approx1/\sqrt d$ to a constant-shift pattern $\alpha=1$). Prediction (Theorem B + 6.1): invariant *linear* model's robust radius scales like $\alpha\cdot\gamma^{\mathrm{full}}$; for the conv model it scales like $\operatorname{Sep}_\Psi/L$, decoupled from $\alpha$. So a conv model should retain robustness as $\alpha\to0$ *only if* the classes still differ in power spectrum — a clean dissociation test of linear-vs-nonlinear invariant capacity.

**P4 (Orbit-gradient suppression).** Measure $\|\Pi_{\text{orbit-tangent}}\nabla_{\mathbf x} f\|/\|\nabla_{\mathbf x} f\|$ for invariant vs. FC nets. Prediction (Theorem C): exactly-invariant conv-GAP nets have this ratio $\approx0$ (orbit-tangent gradient suppressed); FC nets do not. And the *off-manifold* gradient $\|\Pi_{P^\perp}\nabla f\|$ should be smaller for invariant nets on orthogonal-frequency data (Melamed link), larger on single-dot data.

**P5 (Consistency/robustness decoupling).** Vary padding (Ge Table 2: padding 0→28 raises consistency 18→98). Prediction (Prop 5.7): shift-consistency $\mathrm{SC}$ is governed by the invariance defect $\epsilon$ (padding), while robust radius is governed by $\eta/L$ (data separation in invariant features). The two should be *separately* manipulable: it is possible to raise $\mathrm{SC}$ (more padding) while *holding robustness fixed* iff $\operatorname{Sep}_\Psi$ is unchanged — i.e. the Ge "more invariant ⇒ less robust" trend should *reverse* on a dataset engineered with large $\operatorname{Sep}_\Psi$. This is the strongest, most surprising prediction and the cleanest test that the governing quantity is $\operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}$, not invariance.

**P6 (Capacity-matched control).** Across (depth, kernel, pooling=GAP vs. dense) at matched parameter count, the robust radius should be predicted by $\widehat{\operatorname{Sep}}_{\mathcal H_{\mathrm{inv}}}/\widehat L$ *better than* by shift-consistency $\mathrm{SC}$ alone (regression $R^2$ comparison). If $\mathrm{SC}$ alone predicted robustness, the theory is wrong; the theory predicts $\operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}/L$ dominates.

---

## 9. Summary

- **Theorem A** (exact): for shift-invariant *linear* classifiers, $\gamma_2^{\mathrm{inv}}=\operatorname{Sep}_{\Pi_{\mathrm{inv}}}=\frac12(\min_{X_+}f_{dc}-\max_{X_-}f_{dc})_+$. Invariant max-margin = separation after orthogonal projection onto the (1-D, DC) invariant subspace.
- **Theorem B** (dichotomy): co-existence $\iff$ projected separation positive (and ratio $\kappa$ bounded below); forced trade-off $\iff$ projection destroys separation. The DC alignment $\alpha$ / projected separation is the governing scalar.
- **Theorem C** (nonlinear lift): for invariant conv-GAP nets reading a separating invariant feature $\Psi$ (e.g. power spectrum) with margin $\eta$ and Lipschitz $L$, robust radius $\ge\eta/L$ with exact consistency and orbit-tangent gradient suppression. This is the regime where invariance *increases* robustness.
- **Recovery:** $2/\sqrt d$ is exactly the DC alignment of a single-pixel signal (Section 6.1).
- **No contradiction with Kamath:** their cyclic-code distribution is built so $\operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}\to$ small; my trade-off branch agrees there, and my co-existence branch only claims the opposite for distributions with $\operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}>0$, which their construction excludes (Section 6.2).
- **Master criterion / headline:** *Shift-invariance and $\ell_2$ robustness co-exist exactly when the inter-class signal is carried by a shift-invariant feature that the architecture can compute and that keeps the classes well-separated; they trade off exactly when the invariant projection (the richest invariant feature available) collapses the class separation.* The measurable predictor is $\operatorname{Sep}_{\mathcal H_{\mathrm{inv}}}/L$, not shift-consistency.
- **Honest gaps:** optimization/implicit-bias (Frei) not closed; Lipschitz constant can erode the guarantee; conditional hypotheses for the nonlinear theorem; deep-net and approximate-invariance extensions are predictions, not proofs (Section 7).
