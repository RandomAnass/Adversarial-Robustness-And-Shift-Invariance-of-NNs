# A Study of the Effects of Transfer Learning on Adversarial Robustness

- **Label:** `ICLR_2024_vY4iBYm9TU`
- **Venue:** ICLR 2024  (Submitted to ICLR 2024)
- **Forum:** https://openreview.net/forum?id=vY4iBYm9TU
> _Fetched 2026-06-26T23:38:54.068904+00:00_

## Thread summary
- decision: 1
- meta_review: 1
- official_review: 4

## Official Reviews

### ICLR.cc/2024/Conference/Submission2789/Reviewer_AUoQ — 2023-10-24T09:34:26.251000+00:00

**summary:**

This paper examines the impact of fine-tuning on downstream or primary tasks using pretrained models in terms of empirical and certified robustness. It identifies trends in the robustness of models fine-tuned in supervised or self-supervised pretraining settings compared to baseline models (initialized randomly) across various low and high-resolution image datasets. The findings suggest that, empirically, whether a pretrained model undergoes adversarial training or not doesn't significantly influence the robustness performance for the downstream task. Furthermore, they illustrate that the introduction of pretrain model to adversarial training of downstream tasks improves both standard and robust performances of the tasks. These insights indicate that for tasks with limited labeled data, there is no necessity for adversarial training during the pretraining phase of the model. Utilizing models trained either in supervised or unsupervised manners can yield comparable robustness performance.

**strengths:**

- From both empirical and certified perspectives, the paper demonstrates that there's no need for a robust pretrained model for adversarial training of the downstream task. This suggests the potential for efficient transfer learning using standard pretrained models.
- Through experiments across various datasets, the study empirically illustrates that the aforementioned phenomenon is a consistent trend observed during the pretrain-finetuning process.
- Furthermore, the paper indicates that, in contrast to pretraining, finetuning requires training in an adversarial setting.

**weaknesses:**

- A strength of this paper is the suggestion that one can achieve efficiency in transfer learning using standard pretrained models, as there's no need for a robust pretrained model for adversarial training of the downstream task. However, the absence of comparative experimental results and analyses from this perspective, coupled with a lack of information on baseline training, pretraining, and fine-tuning, makes it challenging to anticipate the outcomes. Given that the studies cited by the authors conducted such analyses, it seems imperative to perform analogous investigations for each downstream task.
- Beyond presenting results from transfer learning using standard and adversarial pretrained models, the paper does not seem to offer additional contributions. The experiments related to certified robustness in transfer learning don't offer much beyond simple application, making it hard to view them as significant contributions. Furthermore, it's reasonably intuitive that empirical robustness would display trends similar to those observed.
- For the authors to claim they "proposed" transfer learning, they should have either introduced a distinct robust transfer learning methodology and validated its superiority against prior methods, or at the very least, presented a "bag of tricks" that analyzes optimal hyperparameter settings for robust transfer learning.

**questions:**

- Did the authors directly apply the SimCLR method used in the self-supervised learning setting to train the model in a standard setting, or did they modify it for an adversarial setting? Based on the results in Table 4, it appears they might have used the standard setting. However, for a precise comparison, it seems necessary to display results comparing methodologies that adapt to an adversarial setting in Tables 2 and 3. Furthermore, Table 4 should provide a side-by-side comparison of results from both supervised and self-supervised methods.
- Are there experimental results addressing the efficiency aspect mentioned under weaknesses?

**soundness:**

2 fair

**presentation:**

2 fair

**contribution:**

1 poor

**rating:**

3: reject, not good enough

**confidence:**

3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.

**flag_for_ethics_review:**

- Yes, Privacy, security and safety

**details_of_ethics_concerns:**

No

**code_of_conduct:**

Yes

---

### ICLR.cc/2024/Conference/Submission2789/Reviewer_rH6Y — 2023-10-29T06:36:09.592000+00:00

**summary:**

This paper uses both supervised and self-supervised pretraining methods across a range of downstream tasks to analyze the effects of pre-training with adversarial robustness. Although some experimental conclusions are helpful to the AI safety community. However, a key issue in this paper is that comparative studies are clearly inadequate.

**strengths:**

1. The paper is easy to follow.
2. The authors present some insightful observations for transfer learning on adversarial robustness.

**weaknesses:**

The entire paper is more like a simple experimental report, a key issue in this paper is that comparative studies are clearly inadequate. In addition, some conclusions of this paper have been verified in previous papers on transfer learning, and there is not too much innovative content.

**questions:**

1. How does the quality of pre-trained models affect the robustness of downstream models?
2. The author claims one of the contributions is the first successful demonstration of training models with high certified robustness on downstream tasks irrespective of the amount of labelled data available, either during pre-training or fine-tuning.  The author only showed an experimental result and did not provide any theoretical proof.

**soundness:**

3 good

**presentation:**

3 good

**contribution:**

2 fair

**rating:**

5: marginally below the acceptance threshold

**confidence:**

4: You are confident in your assessment, but not absolutely certain. It is unlikely, but not impossible, that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work.

**flag_for_ethics_review:**

- No ethics review needed.

**details_of_ethics_concerns:**

N/A

**code_of_conduct:**

Yes

---

### ICLR.cc/2024/Conference/Submission2789/Reviewer_mVVr — 2023-10-30T13:47:44.143000+00:00

**summary:**

This paper investigates the impact of pre-training on empirical and certified adversarial robustness. The authors demonstrate that in addition to the existing research that shows the effectiveness of transfer learning in terms of empirical adversarial robustness, transfer learning also aids in certified adversarial robustness. Moreover, contrary to previous research, the authors argue that pre-trained networks do not necessarily need to be adversarially robust models and demonstrate that fine-tuning should involve adversarial training.

**strengths:**

1. Adversarial training was conducted for various downstream tasks.
2. Demonstrating the effect of transfer learning in terms of certified adversarial robustness seems novel.

**weaknesses:**

1. I appreciate the authors who demonstrated the effect of transfer learning in terms of certified adversarial robustness. However, I believe their contribution is not significant, as many researchers may infer this fact to some extent from the effectiveness of transfer learning in empirical adversarial robustness.
2. This paper makes a claim that contradicts previous research (Hendrycks et al., 2019), which argues the necessity of robust pre-training for a substantial improvement in empirical adversarial robustness, but it does not provide sufficient analysis to support it. Considering the results in Table 2, when observing the results for Rand Init. on CIFAR-10, the gap between SA and RA is only 4.5% points. This suggests that the adversarial budget used in the experiments might be too small to highlight the difference between adversarial training and standard training.
3. The claim in Section 4.1 that the improved RA is due to improved SA is difficult to accept. When comparing the results of Sup. Pre-Training and Self-Sup. Pre-Training for Food, CIFAR-100, CIFAR-10, SUN397, DTD, and Pets in Table 2, it can be seen that despite SA being lower, RA is higher.

**questions:**

1. What factors have contributed to making the claims of this study contrary to previous research [1]?

[1] Hendrycks, Dan, Kimin Lee, and Mantas Mazeika. "Using pre-training can improve model robustness and uncertainty." ICML, 2019.

**soundness:**

2 fair

**presentation:**

2 fair

**contribution:**

2 fair

**rating:**

3: reject, not good enough

**confidence:**

5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully.

**flag_for_ethics_review:**

- No ethics review needed.

**code_of_conduct:**

Yes

---

### ICLR.cc/2024/Conference/Submission2789/Reviewer_MNnj — 2023-11-06T03:20:10.502000+00:00

**summary:**

This paper studies how transfer learning improves adversarial robustness under different settings. By several sets of experiments, the authors demonstrate that 1) the adversarial fine-tuning phase is necessary and the key to improving robustness; 2) pre-trained models by adversarial training or self-supervised training can help improve robustness after adversarial fine-tuning.

**strengths:**

Transfer learning has not been studied in the context of adversarial training. This paper conducts a preliminary investigation into this topic.

**weaknesses:**

1. [Novelty] The novelty of this work is limited. Despite extensive experiments, the authors have demonstrated little deep insight explaining the reason behind the observation.

2. [Reproduction] As a purely empirical study, no sample code is provided.

3. [Comprehensiveness] The experiments are not comprehensive, for example, the authors only consider the $l_2$ bounded perturbations and conduct adversarial training with a very small perturbation magnitude ($\epsilon = 0.5$ is very small for $224 \times 224$ colored images). In addition, all pre-trained models are based on ImageNet. The observations might not be the same as demonstrated in this paper if the authors use other types of adversarial perturbations (such as ones based on $l_\infty$ norm).

4. [Presentation] The presentation is fine. However, there is some terminology confusion. For example, the abbreviation "RA" represents empirical robust accuracy in Table 2 while the same abbreviation represents certified robust accuracy in Table 3, which is confusing.

**questions:**

My questions are demonstrated in the weakness part. Among them, I think the key is to provide more insights explaining why adversarial fine-tuning helps robustness and why pre-training can help robustness. In addition, more experimental studies are needed to make the conclusions more convincing.

**soundness:**

2 fair

**presentation:**

2 fair

**contribution:**

1 poor

**rating:**

3: reject, not good enough

**confidence:**

5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully.

**flag_for_ethics_review:**

- No ethics review needed.

**code_of_conduct:**

Yes

---

## Meta Review

### ICLR.cc/2024/Conference/Submission2789/Area_Chair_5Go5 — 2023-12-09T02:57:46.947000+00:00

**metareview:**

This paper investigates how transfer learning affects the robustness of models to adversarial attacks. Through various experiments, they demonstrate that while pre-trained models can improve robustness, the key to achieving significant gains is through adversarial fine-tuning in the downstream task. Additionally, the type of pre-training (adversarial or self-supervised) does not significantly influence robustness as long as adversarial training is applied during fine-tuning. These findings suggest that transfer learning can be a valuable tool for improving model robustness, especially for tasks with limited data, where adversarial training during pre-training may not be necessary.

Strengths: This paper is an early exploration of transfer learning in the context of adversarial training. The paper is easy to follow, and the authors make some insightful observations about transfer learning for adversarial robustness.

Weaknesses: This paper suggests standard pretrained models are efficient for transfer learning, but lacks comparative analyses and baseline information, making outcomes unclear. Further, experiments don't offer significant contributions beyond simple application.

**justification_for_why_not_higher_score:**

While I appreciate the suggestion of using standard pre-trained models for efficient transfer learning, the absence of comparative data and baseline information makes it challenging to assess the validity of this claim. Given the paper's focus on efficiency, I would be hesitant to recommend acceptance without addressing these limitations. Providing additional analysis and comparisons would undoubtedly strengthen the paper and increase its impact.

**justification_for_why_not_lower_score:**

N/A

---

## Decision

### ICLR.cc/2024/Conference/Program_Chairs — 2024-01-16T11:54:05.193000+00:00

**title:**

Paper Decision

**decision:**

Reject

---
