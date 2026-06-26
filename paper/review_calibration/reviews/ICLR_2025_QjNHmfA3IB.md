# BEARD: Benchmarking the Adversarial Robustness for Dataset Distillation

- **Label:** `ICLR_2025_QjNHmfA3IB`
- **Venue:** ICLR 2025  (ICLR 2025 Conference Withdrawn Submission)
- **Forum:** https://openreview.net/forum?id=QjNHmfA3IB
> _Fetched 2026-06-26T23:45:07.257203+00:00_

## Thread summary
- official_review: 4
- unknown: 1

## Official Reviews

### ICLR.cc/2025/Conference/Submission3390/Reviewer_fu4Q — 2024-11-03T02:21:43.221000+00:00

**summary:**

BEARD proposes a standardized benchmarking tool for the evaluation of adversarial robustness of models trained with dataset distillation (DD) techniques. BEARD implements several existing dataset distillation methods as baselines, as well as classic adversarial attack strategies for evaluation. BEARD additionally introduces three metrics to compare performance of different DD methods.

**strengths:**

- Provides a standardized/common notation under which to describe adversarial attack tactics and dataset distillation strategies
- Multiple useful evaluation metrics RR, AE, CREI for comparing different strategies
- Implementation of a comprehensive framework combining libraries for network training, adversarial attack evaluation, and dataset distillation
- Novel observations like increased IPC leading to decreasing adversarial robustness, but increasing dataset scale enhancing adversarial robustness which may not be an immediately obvious conclusion

**weaknesses:**

- The implemented library serves mostly as a glue library for established packages (TorchAttack and dataset distillation package)
- The proposed metrics are straightforward modifications of existing metrics (thresholding ASR and AST)

**questions:**

- The code provided uses pre-distilled datasets, what procedure/libraries/packages were used for this distillation?
- What is your procedure to choose an appropriate &gamma; and &Beta; in the adversarial game framework?

**soundness:**

4

**presentation:**

4

**contribution:**

2

**rating:**

5

**confidence:**

3

**flag_for_ethics_review:**

- No ethics review needed.

**code_of_conduct:**

Yes

---

### ICLR.cc/2025/Conference/Submission3390/Reviewer_FPZb — 2024-11-03T02:46:22.594000+00:00

**summary:**

This paper proposes a dataset distillation benchmark called BREAD, designed to evaluate the robustness of various existing dataset distillation methods. The authors introduce several metrics to support this benchmark. For instance, the Attack Success Time (AST) metric measures the time taken to generate a successful adversarial example, while the Robustness Ratio (RR) assesses robustness across different model architectures and attack methods.

However, the paper lacks novelty, and its contribution is limited. The metrics provided are not specifically tailored for dataset distillation tasks. More importantly, an existing study by Wu et al. (2024) has already proposed a robustness benchmark, predating this work. I do not see any significant improvement in this paper; the authors merely note that the previous work does not release its code. However, this paper also does not append their codes as supplementary.

**strengths:**

Strength:
1. The authors append the link of their github project page to demonstrate their leadboard. The dataset pool and model pool contains the codes of the dataset distillation methods and model architectures. 

2. The authors provide many figures to demonstrate their proposed metrics.

**weaknesses:**

Weakness:
1. The github project page is not completed. The codes is not released and only 6 methods are listed in the leaderboards.  

2. Although the paper is 19 pages long, the benchmark neglects several aspects:
(a) The robustness evaluation considers only white-box attacks, omitting black-box attacks.
(b) Only three datasets are considered, CIFAR10, CIFAR100, and Tiny-Imagenet. The imagenet subsets and ImageNet-1k are also very important in dataset distillation tasks. 
(c) Many methods are not evaluated in this benchmark, including DATM, DREAM.

[1]Ziyao Guo, Kai Wang, George Cazenavette, HUI LI, Kaipeng Zhang, and Yang You. Towards
lossless dataset distillation via difficulty-aligned trajectory matching. In International Conference on Learning Representations (ICLR), 2024.

[2] Liu, Y., Gu, J., Wang, K., Zhu, Z., Jiang, W., & You, Y. (2023). Dream: Efficient dataset distillation by representative matching. In Proceedings of the IEEE/CVF International Conference on Computer Vision (pp. 17314-17324).

3. The motivation of this paper is unclear. What specific contributions set this work apart from the existing study by Wu et al. (2024)? The authors merely criticize that the previous work does not release its code; however, they also do not release their own code.

4. Attack Success Time (AST) defined here is not inappropriate. The inference time varies among different models and different attack methods. The metric should only vary in different distilled datasets. 

5. What is the purpose to demonstrating the figure 2? There is no useful information disclosed in figure 2, it is better to place it in the appendix.

**questions:**

As stated in weakness part. To conclude, this work resembles engineering more than research. I hope the authors could help me address my concerns in weakness part.

**soundness:**

2

**presentation:**

2

**contribution:**

2

**rating:**

5

**confidence:**

4

**flag_for_ethics_review:**

- No ethics review needed.

**code_of_conduct:**

Yes

---

### ICLR.cc/2025/Conference/Submission3390/Reviewer_B4VD — 2024-11-05T02:22:16.063000+00:00

**summary:**

This paper introduces BEARD, a comprehensive benchmark framework for evaluating adversarial robustness of Dataset Distillation (DD) methods, featuring novel evaluation metrics and an adversarial game framework. The authors provide extensive experiments across multiple datasets and DD methods, along with a public model pool, dataset pool and leaderboard. The work establishes a standardized evaluation protocol for DD methods' robustness, though several aspects require further investigation.

**strengths:**

1. Addresses an important gap in DD research by providing a standardized way to evaluate adversarial robustness
2. Comprehensive experimental evaluation across multiple datasets, methods and attack types
3. Open-source implementation and leaderboard to benefit the research community

**weaknesses:**

- Only considers image classification tasks, limiting generalizability
- Uses relatively small datasets (CIFAR-10/100, TinyImageNet) compared to modern standards
- Limited model architectures (only ConvNet) without exploring more modern architectures like Vision Transformers
- No analysis of trade-offs between robustness and model performance

**questions:**

- How does computational complexity scale with dataset size and model architecture? Is BEARD practical for evaluating large-scale models and datasets?
- For a comprehensive benchmark, have you considered combining DD methods with defense methods? The interaction between DD and defenses could provide valuable insights.

**soundness:**

2

**presentation:**

2

**contribution:**

2

**rating:**

5

**confidence:**

4

**flag_for_ethics_review:**

- No ethics review needed.

**code_of_conduct:**

Yes

---

### ICLR.cc/2025/Conference/Submission3390/Reviewer_393r — 2024-11-06T15:23:55.107000+00:00

**summary:**

This paper introduced a benchmark that employs an adversarial game framework to systematically evaluate dataset distillation (DD) models under various adversarial attack scenarios. The authors explored the vulnerabilities introduced by adversarial attacks, and the robustness of models trained on distilled datasets.

**strengths:**

- This paper proposed three novel metrics - Robustness Ratio (RR), Attack Efficiency Ratio (AE), and Comprehensive Robustness-Efficiency Index (CREI) - to evaluate adversarial robustness against different attacks.
- It established a leaderboard that ranks existing DD methods based on these metrics;
- It provided open-source code with comprehensive documentation, along with a Model Pool and Dataset Pool to facilitate adversarial robustness evaluations.

**weaknesses:**

This paper (BEARD) seems to overlap significantly with DD-RobustBench [Wu et al., 2024], including:
- The goal of both papers is the same: benchmark adversarial robustness in dataset distillation
- They both use a similar three-stage evaluation pipeline: distillation -> model training -> adversarial attack testing
- They both adopt a similar experimental setup, including datasets, IPC settings, attach methods, DD methods (DD-RobustBench tested more recent DD methods, e.g. D4M, which is particularly important as it represents the latest generative dataset distillation method that achieves high scalability and accuracy).
- The analysis perspectives are very similar, for example, they both analyzed performance across different IPCs.

**questions:**

It would be great to emphasize the unique novelty to differentiate from existing literature given the significant overlap with DD-RobustBench [Wu et al., 2024]. Especially, there are misunderstandings the authors may have about DD-RobustBench:
- The authors of DD-RobustBench did provide their code on GitHub.
- Beyond the model accuracy, DD-RobustBench also introduced the Drop Rate (DR) metric specifically designed to evaluate robustness and conducts a comprehensive analysis on how different components affect robustness.

**soundness:**

3

**presentation:**

3

**contribution:**

2

**rating:**

5

**confidence:**

4

**flag_for_ethics_review:**

- No ethics review needed.

**code_of_conduct:**

Yes

---

## Other replies

### ICLR.cc/2025/Conference/Submission3390/Authors — 2024-11-14T05:45:20.483000+00:00

**comment:**

We sincerely thank the reviewer for their invaluable feedback and time. We will incorporate the provided comments for our next submission.

**withdrawal_confirmation:**

I have read and agree with the venue's withdrawal policy on behalf of myself and my co-authors.

---
