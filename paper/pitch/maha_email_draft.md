# Draft reply to Maha — summary + deck

**To:** mahalakshmi.sabanayagam@adelaide.edu.au
**Subject:** Re: (your thread) — invariance vs robustness: short summary + deck

---

Hi Maha,

Thanks so much, and no rush at all — I know you're deep in ICLR, so whenever you have
a moment is completely fine.

Here's the short version of where the practical course ended up. I've attached a two-page
summary and a short deck; the one-line idea and the main results are below.

**The idea.** The literature disagrees on whether shift-invariance helps or hurts adversarial
robustness (Ge shows it can hurt; the anti-aliasing / equivariance line reports it helps). I
think the disagreement comes from measuring the wrong thing. Shift-consistency — the metric
that line tracks — does not order robustness. A threat-matched, scale-free margin-to-Lipschitz
ratio η/L (a Lipschitz–margin certificate, which I complete to a two-sided bracket) does, and
it needs no attack to compute.

**The results.**
- Across capacity-matched models, and more cleanly *within* single frozen CLIP encoders where
  training can't be the confound, η/L orders the robust radius while shift-consistency is flat
  or anti-correlated (it's saturated at 0.96–0.99 on modern encoders, so it can't rank them).
- The "invariance helps" correlation is a weak-attack artifact: it appears under FGSM and
  vanishes under AutoAttack.
- To rank already-robust models, where η/L no longer separates, the *shape* of the input
  gradient (an ℓ1/ℓ2 anisotropy) tracks robustness across 30 RobustBench models (−0.79).

**Where I'd love your input.** The last slide of the deck lists four specific questions —
mostly whether the certificate framing and the two-sided bracket are a real addition given
your work on robustness certificates and kernel-machine theory, which parts look weakest to
you, and whether we're missing anything at the certified-robustness × invariance intersection.

**Plan / timeline.** The theory and the core experiments are done; I'm finishing one
prompt-conditioned foundation-model experiment now, then a final coherence and writing pass.
I'm aiming for a main-track submission, and if the direction looks right to you I'd be glad to
iterate over email or find a short time to chat — whatever is easiest given your schedule.

Thanks again, and genuinely no pressure on timing.

Best,
Anas
