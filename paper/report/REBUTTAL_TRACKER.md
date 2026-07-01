# Rebuttal tracker — addressing the R6 panel (all points except page-length)

Panel scores 4/4/4/5. User directive: address every substantive criticism EXCEPT the NeurIPS page-limit (targeting a top venue where length is not the gate). Status per point below.

| # | Criticism (from the 4 reviewers) | Type | Status |
|---|----------------------------------|------|--------|
| C1 | η/L–r₂ correlation is near-tautological (0.998 "by construction") | reframe | ✅ surfaced as explicit Limitation (consistency-check not validation; load-bearing = dissociation + AT anti-corr + partial-corr) |
| C2 | Consistency dissociation is arm-selected + rides on the exact-cyclic outlier | analysis+reframe | ✅ **DONE** — η/L\|clean is +0.85–0.90 across ALL subsets incl. exact-cyclic-removed (+0.88) and natural arms only (+0.90); added to §5. Positive claim robust; only consistency's anti-prediction is range-dependent (honestly stated). |
| C3 | η/L ties clean-accuracy as a selector; can't be trained → thin payoff | analysis+reframe | ✅ **DONE** — η/L\|clean = +0.89 shows predictive content beyond clean-acc (added §5); selector-tie honestly kept; untrainability is a deliberate diagnostic finding. |
| C4 | Data axis n=4 + title overclaim + OFFSET | experiment+reframe | ✅ reframe DONE (title scoped to "...A Threat-Matched Margin-to-Lipschitz Diagnostic"; abstract/intro reposition data as a 2nd-axis §5 result; offset in Limitations). S3 (widen band, characterize offset) RUNNING on GPU 1. |
| C5 | Theory known/elementary; bracket definitional | reframe | ✅ paper already frames orbit results as "modest structural contributions", bracket as conditional (independent-α clause, R2), certificate as classical. Adequate. |
| C6 | Threat-matching clearly helps in only 1/4 conditions | analysis+reframe | ✅ CIs computed: overlap in ALL 4 at n=8; separation clearest on 12-cell grid (+0.83 vs +0.27 n.s.) + data axis. Honest note added to §5. |
| C7 | Does not confront TIPS/Wang-2025 | experiment | 🔄 **S1a (TIPS) RUNNING** on GPU 0 (AT cells training). S1b (Wang GCNN) DROPPED per author (env friction). Verified: both rest their claim on FGSM/PGD, no AT, no AutoAttack — our head-to-head regime. |
| C8 | CIFAR-scale only | experiment | 🔄 **S2 (ImageNet-100)** QUEUED — launches on GPU 0 when S1a frees it; Fast-AT ε=4/255 + AutoAttack, reuses TIPS resnet backbone (~1.5 days). |
| C9 | MNIST/Fashion dissection not capacity-matched | reframe(+opt exp) | ✅ scoped in Limitations (capacity-matched evidence = CIFAR+ResNet; MNIST/Fashion supplementary). |
| C10 | Exact-cyclic underfit artifact? | reframe | ✅ APS reproduces exact-invariance via a 2nd mechanism (in §5 scaling); anti-prediction survives its removal (C2, +0.88). Adequate. |

**Experiments (the big levers):** S1 head-to-head, S2 ImageNet, S3 widen-data-axis+offset. Scout `a086e...` assessing S1/S2 feasibility.
**Analyses run:** C2 (arm-subset robustness ✅), C3 (partial corr ✅); pending C6 (threat-matching CIs).
**Reframing:** C1, C4, C5, C6, C9, C10 — apply as one honest revision pass, then compile+commit.
