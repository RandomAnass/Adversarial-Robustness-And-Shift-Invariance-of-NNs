# Color Equivariant Convolutional Networks

- **Label:** `NeurIPS_2023_xz8j3r3oUA`
- **Venue:** NeurIPS 2023  (NeurIPS 2023 poster)
- **Forum:** https://openreview.net/forum?id=xz8j3r3oUA
> _Fetched 2026-06-26T23:42:58.079690+00:00_

## Thread summary
- decision: 1
- official_comment: 8
- official_review: 4
- rebuttal: 5

## Official Reviews

### NeurIPS.cc/2023/Conference/Submission7778/Reviewer_w9HG — 2023-06-28T21:30:01.541000+00:00

**summary:**

This paper questions the importance of color variations for neural classifiers and proposes to use color-equivariant architectures in the case of unbalanced datasets.
To demonstrate the validity of the presented approach, the authors conduct experiments both on synthetic controlled datasets and on common object recognition benchmarks.
As the experiments show, the injection of color-equivariant layers leads to a slight improvement on almost all common benchmarks when the performance is measured on the original test set but the advantage of the presented method becomes more evident when the test data is corrupted with hue shifts.

**strengths:**

This paper studies an interesting and underinvestigated question of the importance of color representation for neural networks.
The submission is easy to read, and the motivation is well explained in the example of the Flowers dataset. 
The authors have conducted a significant number of experiments to support their claims.
Additional strength is that the demonstrated performance improvement is achieved without increasing the number of trainable parameters (line 238).

**weaknesses:**

1. While the idea of extending equivariance from geometric to photometric transformations is definitely interesting, the submitted manuscript, unfortunately, focuses on the only type of such transformations, i.e. hue shifts. Despite the case of the Flowers dataset is a perfect fit for this transformation, the authors do not discuss other use cases when this type of equivariance may be interesting in practice and just mention "accidental recording conditions" (line 3). For other datasets, hue shifts seem less meaningful, and the better robustness of the proposed CE-ResNets to such shifts at test time is explained by the fact the architecture was just intentionally designed for this scenario. Taking this into account, I find the scope of the paper a bit limited.

1. In addition to being limited in the number of considered photometric transformations, the paper also considers a single task of object recognition. I would encourage the authors to consider other tasks as well, e.g. unsupervised domain adaptation.

1. While the authors claim their approach makes networks more robust to test time corruptions (Tab. 1), they do not demonstrate other baselines aiming to provide robust outputs, e.g. adversarially robust models.

**questions:**

1. I ask the authors to discuss the weaknesses stated above. The main thing I am interested in is the usage of robust baseline models.

1. While preserving the number of trainable parameters is valuable, I wonder if the network throughput remains the same for color-equivariant architectures in comparison with the baselines. If this is not the case, how significant is the decrease?

**limitations:**

Limitations are addressed adequately.

**soundness:**

3 good

**presentation:**

3 good

**contribution:**

2 fair

**rating:**

5: Borderline accept: Technically solid paper where reasons to accept outweigh reasons to reject, e.g., limited evaluation. Please use sparingly.

**confidence:**

2: You are willing to defend your assessment, but it is quite likely that you did not understand the central parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.

**flag_for_ethics_review:**

- No ethics review needed.

**code_of_conduct:**

Yes

---

### NeurIPS.cc/2023/Conference/Submission7778/Reviewer_9e3n — 2023-06-28T23:24:33.311000+00:00

**summary:**

The authors introduce a color equivariant convolutional neural network. To achieve this the authors represent the image in HSV format, and achieve hue equivariance using methods for rotational equivariance. This is possible since hue can be represented by an angle. The authors show that the proposed approach out performs standard CNNs and color invariant CNNs when there is a hue shift between the train and test set.

**strengths:**

* Originality: The presented method of building a color equivariant CNN appears to be original. 
* Quality: The work appears to be of fairly good quality. 
* Clarity: The paper is well written. 
* Significance: The observation that color equivariance can be achieved by identifying hue with the rotation group is interesting. The results show the proposed approach leads to improved performance when there is a color based domain shift.

**weaknesses:**

* Quality: I have some questions about the mathematical presentation, and experiment design (see questions).
* Clarity: Some aspects were unclear to me, due to presentation or motivation (see questions)

**questions:**

* regarding equation 3. I believe the correlation should be between the feature maps and $C^{l+1}$ filters [7]. I think it could be clarifying to write that $c$ is the input channel and $i$ is output channel.
* regarding equation 6: I'm not sure I understand how does H_n(k) acts on \psi_c? In the case of group 2D rotation equivariance, the filters are transformed by in plane rotations. It is not clear to me how one can perform a 3D rotation of a filter with an arbitrary number of channels.
* It seems to me that the network is designed for local hue equivariance, can the authors clarify the benefit of this over global hue equivariance (i.e, performing hue shift on the input image then processing all inputs with the same cnn, and combining representations at the final layer to get a hue-equivariant representation)?
* Does computational expense improve if input images are converted to HSV before being passed into the network? In this case, I expect hue equivariance could be achieved by discretization of the 2D rotation group rather than a 3D transformation.
* Have the authors experimented with finer/coarser discretizations of the hue/rotation group


**limitations:**

* Limitations -- in particular the issue of computational cost -- are communicated

**soundness:**

3 good

**presentation:**

3 good

**contribution:**

3 good

**rating:**

6: Weak Accept: Technically solid, moderate-to-high impact paper, with no major concerns with respect to evaluation, resources, reproducibility, ethical considerations.

**confidence:**

5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully.

**flag_for_ethics_review:**

- No ethics review needed.

**code_of_conduct:**

Yes

---

### NeurIPS.cc/2023/Conference/Submission7778/Reviewer_81VY — 2023-07-12T16:36:45.771000+00:00

**summary:**

Paper proposes color-equivariant CNN layers by imposing equivariance to H_n (a discrete subgroup of SO(3)) in the RGB space which is imposes hue equivariance. Implementation follows the framework of Group-equivariant CNNs. Experiments show marginal improvements over standard CNNs for in-distribution test data but significant improvements when test data is hue-shifted.

**strengths:**

1. Color equivariance in CNNs is a relatively less-studied but an important topic for robustness. The proposed idea of incorporating equivariance to hue transformations via rotations in the RGB space is novel. 
2. Experiments are setup well clearly showing when color equivariance is helpful vs color invariance vs no symmetry. Proposed approach shows improves over CNN even when in in-distribution test data, but major improvements come when test data is hue-shifted.

**weaknesses:**

1. Definition of color equivariance considered in the paper seems to be restricted as it only considers the hue dimension. One of the motivations for incorporating color equivariance is for robustness to illumination changes which I do not think is guaranteed here. A general definition of color-equivariance should consider other dimensions. Maybe the claims are better justified if Hue-equivariance is emphasized in the title/introduction/method name, etc.
2. The definition of hue-equivariance is not precise in the paper. Ideally, it should include all rotations in the RGB space (i.e., SO(3)), but also consider the fact that many of these rotations take the color values out of the RGB space (unit cube). In general, this issue occurs for the discrete subgroup $H_n$ as well. Simply projecting the color values back into the RGB space does not work as it breaks the invertibility property of these transformations. 
3. Experiments compare with a standard CNN (+grayscale) as baseline. Other baselines can be included, for example [1], that considers invariance to illumination color/intensity. 
4. Experiments in the main paper only consider the group $H_3$ (i.e., 3 rotations in the RGB space), which seems limited in robustness, as shown in Figure 1 without jitter augmentations. 


References:

[1] Lengyel, Attila, et al. "Zero-shot day-night domain adaptation with a physics prior." _Proceedings of the IEEE/CVF International Conference on Computer Vision_. 2021.

**questions:**

1. How is the hyperparameter $s$ chosen for different datasets in Table 1, especially for hue-shifted test dataset (assumed not known during training/validation)?
2. Is the invariance captured by Grayscale-Z2CNN same as that considered in the paper, i.e., invariance to hue? Would a better preprocessing step be only considering a canonical representation in the hue dimension?
3. In the color-imbalance experiments, were the CNNs trained with loss weighted according to the class imbalance? 
4. Except being computationally expensive, are there other issues with using $H_n$ for higher n? Ablation in the Appendix seem to show better robustness with higher n, and also good in-distribution performance (at 0 hue shift). So I am not sure why $H_3$ alone was considered in the main paper.
5. It would be helpful to add a few lines of summary on the ablation studies in Sec 4.2.
6. Can experiments in Section 4.1 include CNN+jitter as it seems to provide competitive performance in Section 4.2?


**AFTER REBUTTAL**

Authors have addressed most of my concerns, particularly, adjusted the claims regarding color vs hue equivariance and added relevant baselines. I am increasing my score as I think this paper can be an important addition to an understudied topic. 

However, I am still concerned about the mathematical definition of hue-equivariance (via H_n group) since these transformations can map a color outside the unit cube and projecting back loses invertibility requirement of a group. I accept that this may not reduce performance in practical tasks (except certain inconsistencies pointed out by the authors), but I believe it is not mathematically correct.

**limitations:**

Limitations should discuss lack of robustness to other color dimensions (e.g., illumination).

**soundness:**

2 fair

**presentation:**

4 excellent

**contribution:**

3 good

**rating:**

6: Weak Accept: Technically solid, moderate-to-high impact paper, with no major concerns with respect to evaluation, resources, reproducibility, ethical considerations.

**confidence:**

4: You are confident in your assessment, but not absolutely certain. It is unlikely, but not impossible, that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work.

**flag_for_ethics_review:**

- No ethics review needed.

**code_of_conduct:**

Yes

---

### NeurIPS.cc/2023/Conference/Submission7778/Reviewer_gSRU — 2023-07-25T14:02:40.498000+00:00

**summary:**

This paper proposes color equivariant convolutional networks (CE-CNNs), a novel convolutional neural network architecture that achieves equivariance to hue changes.&#x20;

They introduce color equivariant convolutions that apply a discrete set of hue rotations to the convolution filters during the forward pass. This makes the network output invariant to corresponding hue changes in the input image.
They propose a group coset pooling layer that pools feature maps over the group of hue transformations to achieve invariance.
They evaluate CE-CNNs on several image classification datasets, showing improved robustness to hue changes at test time compared to regular CNNs. The method also improves absolute classification performance in some cases.
Overall, the paper presents a novel and intuitive technique to build invariance to hue changes into CNNs. The evaluations demonstrate its advantages over standard networks, especially under shifted hue distributions between training and test.

**strengths:**

This paper introduces a clever yet intuitive technique to make convolutional neural networks invariant to hue changes in the input image. The core idea is to apply discrete hue rotations to the convolution filters during the forward pass, essentially "baking in" robustness to color changes.

The paper is clearly written and easy to follow. The authors motivate the problem well, explain their proposed method succinctly, and provide thorough experimentation across image datasets. The visualizations offer useful insights, confirming that the networks learn consistent features across hues.

Overall, I found this to be an original and significant contribution. Invariance to hue shifts is a practical problem, and this paper tackles it through an elegant approach that outperforms regular CNNs. The concept of encoding transformations into convolutions seems powerful. While not the flashiest technique, the method is thoughtful, principled, and achieves strong results. The paper is presented clearly and comprehensively, making the ideas accessible. In summary, this is a high quality paper with both theoretical and practical value.

**weaknesses:**

-   The method is demonstrated on image classification, but it's unclear how well it would generalize to other tasks like detection or segmentation. Additional experiments on other applications could strengthen the claims.
-   The ablation study on number of hue rotations suggests performance varies across different shifts. It would be useful to dig deeper into why - is it an artifact of how shifts are applied? Better understanding this could improve results further.
-   The approach encodes discrete hue rotations. An interesting extension could be supporting continuous rotations for finer-grained equivariance.
-   The comparisons to "grayscale" networks should be interpreted carefully, as removing color information entirely handicaps models. Comparisons to networks pre-trained onImagenet may be more meaningful.
-   The Flowers-102 experiments indicate the method doesn't help much on datasets without color bias. Analyzing when color equivariance helps or hurts could guide adoption.

**questions:**

1.  The amount of color jitter augmentation during training seems to significantly impact performance. Could you do an ablation or analysis to tease apart the direct benefits of the color equivariant convolutions versus the data augmentation?
2.  Have you evaluated the method on larger-scale datasets like ImageNet? Results on more complex data could better demonstrate the scalability.
3.  The choice of 3 discrete rotations seems arbitrary. Can you analyze the impact of the group size to help guide selection? Are there benefits beyond 3 rotations?

**limitations:**

1.  The comparison to only a ResNet baseline limits the conclusions on the benefits of the proposed method. Comparisons to other approaches could provide useful context.
2.  The long-term impacts of building color equivariance into models is unclear. Discussion of downstream effects on fairness and interpretability could be beneficial.

**soundness:**

2 fair

**presentation:**

3 good

**contribution:**

2 fair

**rating:**

5: Borderline accept: Technically solid paper where reasons to accept outweigh reasons to reject, e.g., limited evaluation. Please use sparingly.

**confidence:**

3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.

**flag_for_ethics_review:**

- No ethics review needed.

**code_of_conduct:**

Yes

---

## Author Rebuttals / Responses

### NeurIPS.cc/2023/Conference/Submission7778/Authors — 2023-08-04T09:35:32.899000+00:00

**rebuttal:**

Thank you for the highly detailed and constructive feedback! In this rebuttal we address all points raised by the review team, leading to multiple improvements, including: evaluations against relevant baseline methods, clarifications, and insights. Below, we answer individual questions per reviewer in a point by point fashion. All answers will appear in the camera-ready version of the submission.

For the ColorMNIST experiments, we have performed additional experiments with color jitter augmentation. An updated version of Figure 2 is included in the rebuttal PDF. In both the "longtailed" setting (Figure 2a) and the low $\sigma$ settings of the "biased" setting (Figure 2b), color jitter hurts performance since the tasks require color as a discriminative feature. Only for the high $\sigma$ settings of the "biased" setting, color jitter improves performance since it induces color invariance. However, CECNN captures the best of both worlds: CECNN improves performance over the baseline Z2CNN in both tasks, regardless of $\sigma$.

For the image classification experiments, as multiple reviewers have suggested additional baselines for comparison, we will present the results here. We have included experiments with CIConv-W [1], as well as AugMix [2] - please find the results below. “Baseline” denotes a vanilla ResNet-18/44, [1] and [2] use the same ResNet with color invariant (CIconv) and equivariant (CEconv) convolutions, respectively. Despite discarding color information [1] indeed proves to be a robust baseline to hue shifts, though performing poorly on CIFAR due to the loss of detail by the edge detector. [2] slightly improves performance on both the original and hue-shifted test set, but its robustness lacks behind that of CEConv. Finally, for completeness we have trained CEConv with [2], yielding good performance on both test sets.

[1] Lengyel, Attila, et al. "Zero-shot day-night domain adaptation with a physics prior." Proceedings of the IEEE/CVF International Conference on Computer Vision. 2021.

[2] Hendrycks, Dan et al. "AugMix: A Simple Data Processing Method to Improve Robustness and Uncertainty." Proceedings of the International Conference on Learning Representations (ICLR). 2020"

| Original test set | Caltech-101 | CIFAR-10 | CIFAR-100 | Flowers-102 | Oxford-IIIT Pet | Stanford Cars | STL-10 |
|:------------------|:-----------------|:-----------------|:------------------|:-----------------|:------------------|:-----------------|:-----------------|
| Baseline          | 71.61 $\pm$ 0.88 | 93.69 $\pm$ 0.16 | 71.28 $\pm$ 0.20 | 66.79 $\pm$ 0.89 | 69.87 $\pm$ 0.57  | 76.54 $\pm$ 0.10 | 83.80 $\pm$ 0.36 |
| Baseline + Jitter | 73.93 $\pm$ 0.73 | 93.03 $\pm$ 0.16 | 69.23 $\pm$ 0.44 | 68.75 $\pm$ 1.50 | 72.71 $\pm$ 0.68  | 80.59 $\pm$ 0.36 | 83.91 $\pm$ 0.38 |
| CEConv            | 70.16 $\pm$ 1.05 | 93.71 $\pm$ 0.26 | 71.37 $\pm$ 0.24 | 68.18 $\pm$ 0.45 | 70.24 $\pm$ 0.79  | 76.22 $\pm$ 0.19  | 84.24 $\pm$ 0.48 |
| CEConv + Jitter | 73.58 $\pm$ 0.68 | 93.51 $\pm$ 0.10 | 71.12 $\pm$ 0.57 | 74.17 $\pm$ 0.49 | 73.29 $\pm$ 0.63  | 79.79 $\pm$ 0.37  | 84.16 $\pm$ 0.10 |
| CIConv-W [1] | 72.85 $\pm$ 1.12 | 75.26 $\pm$ 0.57 | 38.81 $\pm$ 0.66 | 68.71 $\pm$ 0.29 | 61.53 $\pm$ 0.53  | 79.52 $\pm$ 0.42  | 80.71 $\pm$ 0.27 |
| CIConv-W [1] + Jitter | **74.38 $\pm$ 0.43** | 77.49 $\pm$ 0.53 | 42.27 $\pm$ 0.56 | 75.05 $\pm$ 0.39 | 64.23 $\pm$ 0.51  | *81.56 $\pm$ 0.32* | 81.88 $\pm$ 0.24 |
| Baseline + AugMix [2] | 71.92 $\pm$ 0.95 | 94.13 $\pm$ 0.22 | **72.64 $\pm$ 0.27** | 75.49 $\pm$ 0.24 | **76.02 $\pm$ 0.51**  | **82.32 $\pm$ 0.07**  | 84.99 $\pm$ 0.24 |
| CEConv + AugMix [2]   | 70.74 $\pm$ 1.12 | **94.22 $\pm$ 0.16** | 72.48 $\pm$ 0.18 | **78.10 $\pm$ 0.50** | 75.90 $\pm$ 0.22  | 80.81 $\pm$ 0.27  | **85.46 $\pm$ 0.30** |

| Hue-shifted test set | Caltech-101 | CIFAR-10 | CIFAR-100 | Flowers-102 | Oxford-IIIT Pet | Stanford Cars | STL-10 |
|:------------------|:-----------------|:-----------------|:-----------------|:-----------------|:------------------|:-----------------|:-----------------|
| Baseline | 51.14 $\pm$ 0.71 | 85.26 $\pm$ 0.56 | 47.01 $\pm$ 0.38 | 13.41 $\pm$ 0.35 | 37.56 $\pm$ 0.76  | 55.59 $\pm$ 0.74 | 67.60 $\pm$ 0.56 |
| Baseline + Jitter | 73.61 $\pm$ 0.60 | 92.91 $\pm$ 0.17 | 69.12 $\pm$ 0.47 | 68.44 $\pm$ 1.60 | 72.30 $\pm$ 0.49  | 80.65 $\pm$ 0.36 | 83.71 $\pm$ 0.35 |
| CEConv | 62.17 $\pm$ 1.01 | 90.90 $\pm$ 0.25 | 59.04 $\pm$ 0.45 | 33.33 $\pm$ 0.38 | 54.02 $\pm$ 1.34  | 67.16 $\pm$ 0.58 | 78.25 $\pm$ 0.51 |
| CEConv + Jitter | 73.57 $\pm$ 0.75 | **93.39 $\pm$ 0.08** | **71.06 $\pm$ 0.53** | 73.86 $\pm$ 0.39 | **72.94 $\pm$ 0.56**  | 79.79 $\pm$ 0.34 | **84.02 $\pm$ 0.14** |
| CIConv-W [1] | 71.92 $\pm$ 1.11 | 74.88 $\pm$ 0.54 | 37.09 $\pm$ 0.74 | 59.03 $\pm$ 0.62 | 60.54 $\pm$ 0.46  | 78.71 $\pm$ 0.33 | 79.92 $\pm$ 0.25 |
| CIConv-W [1] + Jitter | **74.40 $\pm$ 0.55** | 77.28 $\pm$ 0.54 | 42.30 $\pm$ 0.48 | **75.66 $\pm$ 0.27** | 63.93 $\pm$ 0.42  | **81.44 $\pm$ 0.26** | 81.54 $\pm$ 0.21 |
| Baseline + AugMix [2] | 51.82 $\pm$ 0.60 | 88.03 $\pm$ 0.26 | 51.39 $\pm$ 0.19 | 15.99 $\pm$ 0.28 | 48.04 $\pm$ 0.74  | 68.69 $\pm$ 0.73 | 72.19 $\pm$ 0.45 |
| CEConv + AugMix [2] | 62.29 $\pm$ 0.97 | 91.68 $\pm$ 0.21 | 60.75 $\pm$ 0.24 | 41.43 $\pm$ 0.97 | 62.27 $\pm$ 0.81  | 73.59 $\pm$ 0.30 | 80.17 $\pm$ 0.15 |

---

### NeurIPS.cc/2023/Conference/Submission7778/Authors — 2023-08-04T10:05:18.735000+00:00

**rebuttal:**

Many thanks for the helpful comments, please find our detailed response to your questions and remarks below:

---
**Weaknesses:**
> 1. Definition of color equivariance considered in the paper seems to be restricted as it only considers the hue dimension. [...]

Yes! While hue is arguably the most fundamental property of color, others such as saturation and brightness are also important. We will refocus the title, introduction, and method sections to be on "hue-equivariance". In the conclusion and future work we will clarify limitations and possible extensions.

> 2. The definition of hue-equivariance is not precise in the paper. Ideally, it should include all rotations in the RGB space (i.e., SO(3)), but also consider the fact that many of these rotations take the color values out of the RGB space (unit cube). [...]

Agreed. To clarify, for an operation to be hue-equivariant, it should be equivariant only to all rotations around the [1,1,1] diagonal (not necessarily full SO(3)). It is indeed true that pixel values near the cube borders can fall outside of the RGB cube and need to be projected back. In practice, this caused some inconsistencies over varying hue (this explains inconsistent peaks in Fig 7 of supplemental material). We will better clarify this in the method and limitations sections. See also our answer to Reviewer gSRU.

> 3. Experiments compare with a standard CNN (+grayscale) as baseline. Other baselines can be included, for example [1], that considers invariance to illumination color/intensity.

Agreed. We added [1], as well as AugMix - please find the results above.

> 4. Experiments in the main paper only consider the group  (i.e., 3 rotations in the RGB space), which seems limited in robustness [...].

Due to space limitations we had to restrict our analyses in the main paper to 3 rotations - in appendix D we provide an ablation study on the number of hue rotations. Figure 7 shows that increasing the number of rotations improves test-time hue shift performance. However, there is also a trade-off in model capacity as increasing the number of rotations increases the number of parameters in the model. We will add this to the paper.

---

**Questions:**
> 1. How is the hyperparameter chosen for different datasets in Table 1, especially for hue-shifted test dataset?

Due to space limitations, Table 1 in the main text shows only the best networks. The same value for $s$ is used for both the original and hue-shifted test set and we provide the full results in Table 1 of supplementary material - we will better clarify this in the main paper text and caption. Note that for any fixed $s$ the CE networks outperform the baseline model on the hue-shifted test set of almost all datasets.

> 2. Is the invariance captured by Grayscale-Z2CNN same as that considered in the paper, i.e., invariance to hue? Would a better preprocessing step be only considering a canonical representation in the hue dimension?

Interestingly, the grayscale invariance makes objects less distinct from their background (see fig 1 of the original paper). A canonical representation in the hue dimension would indeed retain background distinction and be hue-shift invariant. Yet, such a mapping is non-trivial as it depends on the semantic object/background colors. Such a canonical representation approach is similar to white balancing for achieving color constancy (see also our answer to Reviewer w9HG) . As such, finding a "canonical hue representation" is orthogonal to our equivariance approach and reminds us of a spectral variant of "spatial transformer networks" (ref below). 

We will better explain the relationship with color constancy and white-balancing in related work; and add this alternative approach to the conclusion and future work.

- Jaderberg, Max, Karen Simonyan, and Andrew Zisserman. "Spatial transformer networks." Advances in neural information processing systems 28 (2015).

> 3. In the color-imbalance experiments, were the CNNs trained with loss weighted according to the class imbalance?

This was not the case in the original experiments. We have re-run the experiments with a weighted loss and observed no significant differences to an unweighted loss. We will include both results in the paper / supp. mat.

> 4. Except being computationally expensive, are there other issues with using $H_n$ for higher $n$?

Increasing $n$ increases both computation cost as well as the model’s parameter count. As such, in fair experiments where the total number of parameters is to be equalized between tested models, there is a trade-off between increasing $n$ and increasing the number of channels. Increasing $n$ by too much therefore hurts the model capacity, as can be seen by the slightly decreasing performance at 0-deg. in Figure 7 of the supp. mat. We will further clarify this in the paper.

> 5. It would be helpful to add a few lines of summary on the ablation studies in Sec 4.2.

Definitely! We will add the following to our camera-ready version of the paper: “In short, we find a) that hue equivariant networks require less intense color jitter augmentation to achieve the same test-time hue shift robustness and accuracy, b) that removing group coset pooling breaks hue invariance, and c) that increasing the number of hue rotations increases robustness to test-time hue shifts.”

> 6. Can experiments in Section 4.1 include CNN+jitter as it seems to provide competitive performance in Section 4.2?

We included CNN+jitter - please find the results above. For long tailed MNIST, adding jitter makes solving the classification problem prohibitive, as color is required. For biased MNIST, performance decreases for small and improves for large  $\sigma$, with CEConv still performing best.

---

### NeurIPS.cc/2023/Conference/Submission7778/Authors — 2023-08-04T12:57:54.323000+00:00

**rebuttal:**

Great thanks for your helpful comments and appreciation for our work. Please find detailed answers to your questions and remarks below:

---

**Questions:**

> 1. regarding equation 3. I believe the correlation should be between the feature maps and $C^{l+1}$ filters [7]. I think it could be clarifying to write that is the input channel and  is output channel.

Thank you, this is indeed a mistake from our side. We will correct / clarify in the paper.

> 2. regarding equation 6: I'm not sure I understand how does H_n(k) acts on \psi_c? In the case of group 2D rotation equivariance, the filters are transformed by in plane rotations. It is not clear to me how one can perform a 3D rotation of a filter with an arbitrary number of channels.

Excellent question - as each "pixel" of a filter in a hidden layer lives in a high-dimensional space, applying 3D rotations is indeed not possible. 3D rotations are only applied at the input layer, whereas in hidden layers cyclic permutations are performed to retain equivariance throughout the network. We will better clarify this in the paper.

> 3. It seems to me that the network is designed for local hue equivariance, can the authors clarify the benefit of this over global hue equivariance (i.e, performing hue shift on the input image then processing all inputs with the same cnn, and combining representations at the final layer to get a hue-equivariant representation)?

Interesting alternative - we have briefly considered this, but initial experiments did not yield promising results and therefore did not further pursue this approach. The theoretical benefit of local over global hue invariance is that multiple objects in one image can be recognized invariantly in any combination of hues - this indeed appears to be a useful property. We will include a note on local vs. global equivariance in the Discussion.

> 4. Does computational expense improve if input images are converted to HSV before being passed into the network? In this case, I expect hue equivariance could be achieved by discretization of the 2D rotation group rather than a 3D transformation.

Thanks, we have indeed considered this option. Converting an input to the HSV space introduces a discontinuity between 359-0 degrees, which can lead to suboptimal results when used as an input to a neural network. Alternatively, color spaces such as LAB could be used, where a hue shift can indeed be modeled as a 2D rotation. Eventually we did not see any benefit in 2D rotations, as the additional compute of 3D rotations is negligible on the scale of deep NNs, and this way the network could work directly on RGB images.

> 5. Have the authors experimented with finer/coarser discretizations of the hue/rotation group?

This is indeed something we have looked at - in appendix D we provide an ablation study on the number of hue rotations, i.e. the discretization of the hue group. Figure 7 shows that increasing the number of rotations improves test-time hue shift performance. However, there is also a trade-off in model capacity as increasing the number of rotations increases the number of parameters in the model. This should be counteracted by reducing the width (number of channels) in the architecture to keep the number of parameters equal, thereby somewhat reducing model capacity.

---

### NeurIPS.cc/2023/Conference/Submission7778/Authors — 2023-08-04T13:53:21.641000+00:00

**rebuttal:**

We highly appreciate your helpful comments and the recognition of our efforts. Please find a point-by-point response to your remarks below.

---

**Weaknesses:**
> 1. The method is demonstrated on image classification, but it's unclear how well it would generalize to other tasks like detection or segmentation. Additional experiments on other applications could strengthen the claims.

This is true. yet, given the limited space we could only focus on image classification. Image classification models, including the tested ResNets, are commonly used as backbones for other applications. We will publish our code where CEConv and CE-ResNets are implemented as easy to use plug-and-play modules such as to accommodate for exploring other relevant tasks.

> 2. The ablation study on number of hue rotations suggests performance varies across different shifts. It would be useful to dig deeper into why - is it an artifact of how shifts are applied? Better understanding this could improve results further.

Great question! We analyzed this inconsistency and found that they results from the clipping caused by occasionally rotating outside of the RGB cube and projecting it back. While the values are now not exact; the general trend for improvement still holds: albeit no longer exact, but approximately the same. See also our answer to Reviewer 81VY. 

We will add this analysis and conclusions to the paper; and add a warning about "color clipping" in the source code. 

> 3. The approach encodes discrete hue rotations. An interesting extension could be supporting continuous rotations for finer-grained equivariance.

Definitely. Such “steerable” hue equivariance method would however require a quite different method from the proposed G-CNN-based approach. As this is an interesting direction to explore, we will add this idea to our discussion of future work.

> 4. The comparisons to "grayscale" networks should be interpreted carefully, as removing color information entirely handicaps models. Comparisons to networks pre-trained on Imagenet may be more meaningful.

Exactly - This is what hue-equivariance aims to remedy. See "Grayscale" in Fig 1 of the paper. We will better emphasis this.

> 5. The Flowers-102 experiments indicate the method doesn't help much on datasets without color bias. Analyzing when color equivariance helps or hurts could guide adoption.

This is indeed an important analysis, which we have looked into by investigating the color selectivity of CNN neurons when trained on different datasets (see Fig. 3 in the main paper). Color equivariance appears to be most beneficial whenever color selective neurons are learned - this is mostly the case for colorful datasets, such as Flowers-102. We will further clarify this in the text.

---

**Questions**

> 1. The amount of color jitter augmentation during training seems to significantly impact performance. Could you do an ablation or analysis to tease apart the direct benefits of the color equivariant convolutions versus the data augmentation?

Certainly - we provide an ablation study on the strength of color jitter augmentation in appendix D. Figure 5 shows that training with color jitter improves both the baseline and the hue equivariant models, however the equivariant model needs less jitter to achieve good generalization and achieves a higher accuracy overall. The reason for this is that the equivariant architecture only requires hue augmentation "between" the discrete rotations that it is already robust to, as opposed to the full scale of hue shifts for the baseline architecture. We will elaborate on this in the paper.

> 2. Have you evaluated the method on larger-scale datasets like ImageNet? Results on more complex data could better demonstrate the scalability.

We have performed experiments on Imagenet; the results are reported in Table 1 in the main text, as well as in Table 1 in the supplementary material. We find that also on more complex datasets color equivariance is beneficial, though model capacity is of bigger importance. The hybrid color equivariant architectures where only the first $s$ stages are equivariant demonstrate the best of both worlds, i.e. equivariance to hue shifts, while also allowing a bigger network width for the same number of parameters compared to a fully equivariant architecture.

> 3. The choice of 3 discrete rotations seems arbitrary. Can you analyze the impact of the group size to help guide selection? Are there benefits beyond 3 rotations?

In appendix D we provide an ablation study on the number of hue rotations. Figure 7 shows that increasing the number of rotations improves test-time hue shift performance. However, there is also a trade-off in model capacity as increasing the number of rotations increases the number of parameters in the model, as discussed in the Limitations section of the paper. The trade-off therefore depends on the amount of color vs. the complexity of the data - we will clarify this in the paper.

---

**Limitations**

> 1. The comparison to only a ResNet baseline limits the conclusions on the benefits of the proposed method. Comparisons to other approaches could provide useful context.

Thank you for the suggestion. We have performed additional comparisons with two baselines, CIConv and AugMix, the results and discussion can be seen in the general author rebuttal, and will also be included in the paper.

> 2. The long-term impacts of building color equivariance into models is unclear. Discussion of downstream effects on fairness and interpretability could be beneficial.

Improving performance on tasks where color is a discriminative feature could affect humans that are the target of discrimination based on skin tone. CEConvs benefit datasets with long-tailed color distributions by increasing robustness to color changes, which could be useful in reducing a CNN's reliance on skin tone as a discriminating factor. We will add these considerations to the paper.

---

### NeurIPS.cc/2023/Conference/Submission7778/Authors — 2023-08-04T16:22:41.437000+00:00

**rebuttal:**

We thank reviewer w9HG for the helpful remarks and interest in our work. Please find a detailed response to your questions and suggestions below:

---

**Weaknesses:**

> 1. While the idea of extending equivariance from geometric to photometric transformations is definitely interesting, the submitted manuscript, unfortunately, focuses on the only type of such transformations, i.e. hue shifts. [...] Taking this into account, I find the scope of the paper a bit limited.

We regret that we did not clarify this better. A hue-shift is truly fundamental: simply changing the light bulb or the time of day yields a different illumunant and thus a hue-shift. Being robust to hue-shifts is a still unsolved, important, and an active research direction (color constancy). See, eg, the following recent (top venue) publications below. 

We will add these citations and motivation to related work. 

- Mahmoud and Brown. "What else can fool deep learning? Addressing color constancy errors on deep neural network performance." ICCV. 2019.
- Li, Bing, et al. "Ranking-based color constancy with limited training samples." IEEE Transactions on Pattern Analysis and Machine Intelligence (2023).
- Ono, Taishi, et al. "Degree-of-linear-polarization-based color constancy." CVPR. 2022.




> 2. In addition to being limited in the number of considered photometric transformations, the paper also considers a single task of object recognition. I would encourage the authors to consider other tasks as well, e.g. unsupervised domain adaptation.

This is true. Unfortunately, given the limited time of the rebuttal, we were not able to run additional tasks.

Please also see our answer to Reviewer gSRU:  We chose for  image classification because classification models, including the tested ResNets, are also commonly used as backbones for other applications. While we acknowledge that additional experiments on extra applications would strengthen the argument for generalization of our method, we instead opted, given limited compute resources, for a more thorough evaluation on multiple classification datasets. 

> 3. While the authors claim their approach makes networks more robust to test time corruptions (Tab. 1), they do not demonstrate other baselines aiming to provide robust outputs, e.g. adversarially robust models.

Agreed. Additional comparisons with two baselines, CIConv and AugMix, can be found in the general author rebuttal, and will also be included in the paper.

---

**Questions:**

> 1. I ask the authors to discuss the weaknesses stated above. The main thing I am interested in is the usage of robust baseline models.

See above.

> 2. While preserving the number of trainable parameters is valuable, I wonder if the network throughput remains the same for color-equivariant architectures in comparison with the baselines. If this is not the case, how significant is the decrease?

Definitely. We do already discuss some compute efficiency in the Implementation section of the paper where the same number of channels, CEConv performs a factor $\frac{|H_n|^2}{k^2} + |H_n|$ more MACs. However, the true MAC increase is lower since the number of channels in a CEConv network is reduced to maintain the same parameter count as the baseline.

 Unfortunately, given the limited time for the rebuttal, we could not yet provide these numbers in the rebuttal, but we will include these measurements in the final paper.




---

## Official Comments (multi-round discussion)

### NeurIPS.cc/2023/Conference/Submission7778/Reviewer_9e3n — 2023-08-17T16:59:18.068000+00:00

**comment:**

Thank you for your response. It seems reasonable to me that hue transformations for higher dimensional filters would need to be defined differently, but the solution the authors propose i.e., using a cyclic permutation, is not intuitive to me. Is the motivation for choosing a cyclic permutation that it is also orthogonal? How does it relate back to considerations of hue?

---

### NeurIPS.cc/2023/Conference/Submission7778/Authors — 2023-08-18T10:31:40.283000+00:00

**title:**

Response to Official Comment by Reviewer 9e3n

**comment:**

Dear reviewer 9e3n,

Thank you for your question. We will try to clarify the intuition behind our method. Group equivariant convolutions encode additional transformations (i.e. other than translations) in an extra feature map dimension $G$. In the case of Color Equivariant Convolutions, each index $g \in G$ represents one hue transformation, where a hue shift in the input results in a permutation in $G$. The cyclic permutation in the hidden layers therefore preserves the hue equivariance property in the network. This is consistent with the original GConvs [1], where a rotated input results in a rotation and cyclic permutation in the network feature maps. We will further clarify this in the text.

*References*

[1] Taco S. Cohen and Max Welling. Group equivariant convolutional networks. In Proceedings of the 33rd 312 International Conference on International Conference on Machine Learning - Volume 48, ICML’16, page 313 2990–2999. JMLR.org, 2016.

---

### NeurIPS.cc/2023/Conference/Submission7778/Reviewer_w9HG — 2023-08-18T16:24:14.329000+00:00

**comment:**

I thank the authors for their detailed feedback and provided additional results. After reading other reviews as well as authors' comments, I tend to slightly raise the score. I strongly encourage the authors to add all the promised experiments to the updated manuscript.

---

### NeurIPS.cc/2023/Conference/Submission7778/Reviewer_gSRU — 2023-08-19T06:44:57.017000+00:00

**title:**

Reply

**comment:**

Authors, thank you for the detailed responses to my comments. Your rebuttal addresses most of my questions and provides valuable discussion. In particular, the additional experiments analyzing color jitter augmentation better explain the advantages of your method. I have some follow-up thoughts:

1.  The ImageNet experiments show model capacity is also important. This reminds us that there is a balance between color equivariance and network width when designing models. Further analysis from the authors on how to strike this balance would be helpful.
2.  Thanks for the comparisons to CIConv and AugMix. These do provide more thorough baseline comparisons. If space allows, I'd recommend including these results in the main paper rather than just the rebuttal.
3.  You mention more hue rotations improves robustness but also increases parameters. I strongly suggest analyzing the impact of group size on performance with fixed parameters. This would better illustrate the trade-off for readers.
4.  Very glad to see the authors discuss effects on algorithmic fairness. This is an important aspect. Expanding this discussion would provide value if space permits.

Overall, your responses have addressed my questions and I'm more satisfied with the paper now. Thank you for the diligent work, I look forward to the final manuscript.

---

### NeurIPS.cc/2023/Conference/Submission7778/Reviewer_9e3n — 2023-08-19T14:00:09.348000+00:00

**comment:**

Thank you for the clarification. 

This seems quite distinct from G-CNN since in G-CNN the group transformation acts on the spatial pixel location rather than the channel dimension as you've described. 

Moreover, in G-CNN the lifting layer maps the input image to the group, which does not appear to be the case in the proposed work, unless you are identifying the hue transformations with the cyclic permutations, is that the case? 

I can see how the identification between hue transformations and cyclic permutations makes sense but if this is what's happening, the group action is changing from the input layer to the feature layer which is also quite distinct from the approach in G-CNN where the group action is consistent across layers.

---

### NeurIPS.cc/2023/Conference/Submission7778/Authors — 2023-08-21T16:03:59.526000+00:00

**comment:**

Many thanks for your follow-up remarks. We will make sure to include points 1, 2 and 4 in the main paper and / or supplementary materials, depending on available space. Regarding point 3: in the ablation study on the effect of the number of rotations in supp. mat. section D we have kept the parameter count fixed by downscaling the network width as we increase the number of hue rotations. We will make this more clear in the text.

---

### NeurIPS.cc/2023/Conference/Submission7778/Authors — 2023-08-21T16:55:09.505000+00:00

**comment:**

Many thanks for the follow-up.

> Moreover, in G-CNN the lifting layer maps the input image to the group, which does not appear to be the case in the proposed work, unless you are identifying the hue transformations with the cyclic permutations, is that the case?

This is indeed correct - a hue-shift in the input image results in a cyclic permutation in the group dimension of the feature map. In this sense our proposed hue equivariant convolutional layers are indeed distinct from G-CNNs - we will make sure to make this distinction more clear in the method section.

---

### NeurIPS.cc/2023/Conference/Submission7778/Reviewer_9e3n — 2023-08-21T19:06:19.965000+00:00

**comment:**

Thank you for clarifying. As I understand, the cyclic permutation layers can be used with any lifting layer of the same dimension to produce an equivariant network, is that right?

As I understand, the proposed work is not a G-CNN. While that in and of itself is not an issue, the claim that it is seems somewhat central to the paper. I will determine how this impacts my score in the reviewer-AC discussion period.

---

## Decision

### NeurIPS.cc/2023/Conference/Program_Chairs — 2023-09-21T17:38:19.074000+00:00

**title:**

Paper Decision

**comment:**

All reviewers find that the paper meets NeurIPS standards. Initially, there were concerns regarding unsupported claims and confusion in the definition. During the rebuttal, these concerns have been addressed and several reviewers increased their score.

**decision:**

Accept (poster)

---
