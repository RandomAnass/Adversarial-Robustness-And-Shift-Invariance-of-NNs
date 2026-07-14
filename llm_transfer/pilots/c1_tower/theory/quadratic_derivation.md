# Quadratic margin model: anisotropy vs true L-inf robust radius at fixed eta/L1

## Setup
M(x) = w^T x + (1/2) x^T H x, evaluated at x=0 WLOG (so M(0)=b... actually let margin at the point be m0).
Let the current point be x0 with margin M0 = M(x0) > 0. Shift coordinates so x0=0.
Then locally M(delta) = M0 + w^T delta + (1/2) delta^T H delta,
where w = grad M(x0), H = Hessian (constant for a quadratic).

Attack: find smallest ||delta||_inf =: r such that M(delta) <= 0 (margin crosses 0 => misclassified).

## First-order (textbook)
The L-inf worst case of the LINEAR part w^T delta over ||delta||_inf <= eps is -eps ||w||_1
(achieved at delta = -eps sign(w)). So first-order margin drop = eps ||w||_1,
=> first-order radius r_inf^(1st) = M0 / ||w||_1 = eta/L1.  (dual norm of Linf is L1.)

## Second-order correction
At the linear worst case direction s = -sign(w), take delta = eps * s = -eps sign(w).
Then
  M(eps s) = M0 - eps ||w||_1 + (1/2) eps^2 s^T H s.
The quadratic term:  Q := (1/2) s^T H s = (1/2) sign(w)^T H sign(w) = (1/2) sum_{ij} H_ij sign(w_i) sign(w_j).

So along the fixed Linf direction s=-sign(w):
  M(eps s) = M0 - eps||w||_1 + (1/2) eps^2 (sign(w)^T H sign(w)).

Set r2 = second-order estimate of radius along this fixed direction.  Solve M=0:
  (1/2)(s^T H s) r^2 - ||w||_1 r + M0 = 0.
Let a = (1/2) s^T H s = Q, b = ||w||_1, c = M0.
  r = [ b - sqrt(b^2 - 4 a c) ] / (2a)   (smaller positive root; the branch that reduces to c/b as a->0)
Check a->0: r -> c/b = M0/||w||_1 = eta/L1. Good.

Taylor of the root in a:
  r = (c/b) [ 1 + (a c / b^2) + O(a^2) ]  ... let me verify.
r = [b - sqrt(b^2 - 4ac)]/(2a). Let u = 4ac/b^2 small.
sqrt(b^2-4ac) = b sqrt(1-u) = b(1 - u/2 - u^2/8 - ...).
b - that = b(u/2 + u^2/8 + ...) = b( 2ac/b^2 + 2a^2c^2/b^4 + ...).
Divide by 2a:  r = (c/b) + (a c^2)/b^3 + ... = (c/b)[1 + a c / b^2 + ...].

So:
  r = (M0/||w||_1) * [ 1 + (Q * M0)/||w||_1^2 + O(Q^2) ],   Q = (1/2) sign(w)^T H sign(w).

INTERPRETATION:
- If Q > 0 (margin curves UP along attack dir, convex margin): true radius LARGER than eta/L1 (harder to attack). Radius gap positive.
- If Q < 0 (margin curves DOWN, concave): true radius SMALLER than eta/L1 (first-order OVER-estimates). This is the dangerous case, the "looseness" our anisotropy is supposed to track.

The correction magnitude relative to eta/L1:
  (r - eta/L1)/(eta/L1) ≈ Q * M0 / ||w||_1^2 = Q * (eta/L1) / ||w||_1.

But note eta/L1 is HELD FIXED. So the sign & size of the gap is controlled by Q/||w||_1
i.e. by (1/2) sign(w)^T H sign(w) / ||w||_1.

## Does anisotropy A = ||w||_1/||w||_2 control the gap AT FIXED eta/L1?

The key term is Q = (1/2) sign(w)^T H sign(w) = (1/2) <s, H s> with s=sign(w), a +/-1 vector.

This is a quadratic form of the SIGN pattern of w, NOT of w's magnitudes.
=> WITHOUT structure on H, Q is INDEPENDENT of the anisotropy A. 

COUNTEREXAMPLE candidate: two gradients w, w' with same ||w||_1 and same M0 (so same eta/L1),
same sign pattern (so same s, same Q), but different anisotropy (different ||w||_2).
Then r is IDENTICAL to second order. => anisotropy does NOT determine the gap in general.
This is a clean COUNTEREXAMPLE to the naked claim.

So the proposition is FALSE without extra assumptions linking H to w.

## What assumption rescues it? The mechanism narrative: "spread gradient engages more curvature."
The mechanism only bites if the curvature the attack accumulates SCALES with how spread the
gradient is. Formalize: suppose H = curvature is ISOTROPIC on the attack-relevant subspace,
H = h I (scalar curvature h). Then
  Q = (1/2) h * ||s||_2^2 = (1/2) h * d   (since s in {+/-1}^d, ||s||^2 = d).
Hmm that's just h*d/2, independent of w entirely. Under H = hI, the correction is
  r ≈ (eta/L1)[1 + (h d /2)(eta/L1)/||w||_1].
Still no anisotropy. Because the Linf attack delta = eps sign(w) has ||delta||_2^2 = eps^2 d
regardless of w's spread. So an isotropic-H model accumulates the same curvature.

The anisotropy enters only if H is ALIGNED with the gradient structure.

### The alignment assumption that makes it work
Realistic mechanism: curvature is largest in the directions the model is most sensitive to,
i.e. H correlates with w w^T (Gauss-Newton / feature-alignment). Take the extreme aligned model
  H = -c * (w w^T)/||w||_2^2  ... (negative => margin concave along w, first-order too optimistic)
Actually to connect to anisotropy cleanly, consider H = kappa-generating curvature ALONG w:
Let hat_w = w/||w||_2. Suppose the dominant curvature is along hat_w with magnitude -c (concave):
  H = -c hat_w hat_w^T.
Then
  Q = (1/2) s^T H s = -(c/2) (s^T hat_w)^2 = -(c/2) ( sign(w)^T w / ||w||_2 )^2
     = -(c/2) ( ||w||_1 / ||w||_2 )^2         [since sign(w)^T w = ||w||_1]
     = -(c/2) A^2,   where A = ||w||_1/||w||_2 = anisotropy.

=> Q = -(c/2) A^2.   THE ANISOTROPY APPEARS, SQUARED.

Then the radius correction:
  r ≈ (eta/L1)[ 1 + Q (eta/L1)/||w||_1 ]
    = (eta/L1)[ 1 - (c/2) A^2 (eta/L1)/||w||_1 ].
And ||w||_1 = A ||w||_2, so (eta/L1)/||w||_1... let's keep eta/L1 = M0/||w||_1 fixed = R1.
  r ≈ R1 [ 1 - (c/2) A^2 R1 / (A ||w||_2) ] = R1[ 1 - (c/2) A R1/||w||_2 ].
Hmm ||w||_2 = ||w||_1/A = (M0/R1)/A. So R1/||w||_2 = R1 A/(M0/R1)... wait:
||w||_1 = M0/R1 (fixed). ||w||_2 = ||w||_1/A = M0/(R1 A).
So R1/||w||_2 = R1 * R1 A/M0 = R1^2 A/M0.
Then r ≈ R1[1 - (c/2) A * R1^2 A/M0] = R1[1 - (c/2) c... ] = R1[ 1 - (c R1^2 A^2)/(2 M0) ].
With R1 = M0/||w||_1 fixed and M0 fixed, this is
  gap = r - R1 = -(c R1^3 A^2)/(2 M0) * ... let me just keep the clean intermediate:
  r ≈ R1 [ 1 - (c/2) A^2 R1 /||w||_1 ]   and ||w||_1 fixed = M0/R1:
     = R1 [ 1 - (c/2) A^2 R1^2/M0 ].

MONOTONE DECREASING in A (for c>0, concave-along-gradient curvature).  QED-ish.

So: UNDER the assumption that the dominant (destabilizing, concave) curvature lies along the
gradient direction with fixed magnitude c, at FIXED eta/L1 and fixed M0, higher anisotropy A
=> strictly smaller true radius. The gap scales as A^2.

This is the clean PROPOSITION. Assumptions:
 (A1) quadratic margin;
 (A2) H = -c hat_w hat_w^T + (curvature orthogonal to the attack's engagement) i.e. dominant
      concave curvature aligned with the gradient, magnitude c>0 fixed across the model family;
 (A3) hold eta/L1 = M0/||w||_1 and M0 fixed; vary only the anisotropy A=||w||_1/||w||_2.
Conclusion: true Linf radius r ≈ (eta/L1)(1 - (c/2)(eta/L1)^2 A^2 * ... ) monotone decreasing in A.

Actually let me recompute cleanly keeping only leading order and expressing gap as fraction:
 relative gap  (R1 - r)/R1 ≈ (c/2) A^2 R1^2 / M0 = (c/2) (eta/L1)^2 A^2 / M0.
Since M0 = eta (per-point margin) — with eta/L1 fixed, relative first-order looseness ∝ c A^2 /eta... 
fine. Monotone increasing looseness in A. 

## Connection to kappa (sandwich)
The sandwich says eta/L <= r2 <= eta/alpha, kappa = L/alpha >= 1. Here L is the ball/global
Lipschitz constant toward the boundary and alpha the co-Lipschitz secant slope on the reaching
path. For our concave quadratic along the attack direction, the secant slope alpha over the path
from x0 to the boundary is SMALLER than the local slope ||w||_1-ish because the function bends
toward the boundary => the actual drop per unit distance is steeper early... 

Careful: L-inf, so norms are Linf/L1. Let me define kappa_inf = looseness of the Linf certificate:
 true radius r_inf vs first-order R1 = eta/L1. We have r_inf < R1 in the concave case, so the
 certificate eta/L1 is an OVER-estimate?? 

WAIT. Sign check. The certificate r_inf >= eta/L1 is a LOWER bound and always holds for an
L1-Lipschitz (global) function. But here ||w||_1 is the LOCAL gradient norm, NOT a global
Lipschitz bound. For a quadratic, the global Lipschitz constant grows without bound. The
first-order estimate M0/||w||_1 using the LOCAL gradient is NOT a certificate; it's an
approximation that can be optimistic (too large) when curvature is concave.
=> In our empirical setting L1 = E||grad M||_1 is the LOCAL mean gradient, and eta/L1 is the
first-order radius ESTIMATE, which the TRUE (strong-attack) radius falls BELOW when curvature
bends the wrong way. Exactly the "true radius falls further below eta/L1" story.

So the object is: kappa := R1 / r_inf = (eta/L1)/r_true >= 1 in the concave-aligned regime,
and kappa ≈ 1/(1 - (c/2)A^2 R1^2/M0) ≈ 1 + (c/2) A^2 R1^2/M0, INCREASING in A.
=> anisotropy A is a monotone proxy for the certificate looseness kappa. This is the sandwich
connection: A^2 tracks (kappa - 1) to leading order under the aligned-curvature assumption.

## Verdict
- NAKED claim (A predicts gap at fixed eta/L1 for arbitrary H): FALSE. Counterexample: Q depends
  only on sign(w), not on |w|, so two models with same sign pattern & ||w||_1 & M0 but different
  A have identical second-order radius. Also isotropic H gives A-independent gap.
- CONDITIONAL claim (aligned concave curvature, H's dominant eigenvector ∝ w): TRUE and clean,
  gap ∝ A^2. Provable proposition.
- Mechanism "spread gradient engages more curvature" only holds if curvature is aligned with the
  gradient; for isotropic curvature the Linf attack engages the SAME curvature (delta=eps sign(w),
  ||delta||_2^2 = eps^2 d) regardless of spread.
So: CONJECTURE with a conditional proof + the honest caveat. Aligned-curvature is the assumption.
