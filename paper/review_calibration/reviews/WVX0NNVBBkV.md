# Robust Learning Meets Generative Models: Can Proxy Distributions Improve Adversarial Robustness?

- **Label:** `WVX0NNVBBkV`
- **Venue:** ICLR 2022  (ICLR 2022 Poster)
- **Forum:** https://openreview.net/forum?id=WVX0NNVBBkV
> _Fetched 2026-06-26T23:48:41.802284+00:00_

## Thread summary
- decision: 1
- official_comment: 14
- official_review: 4

## Official Reviews

### ICLR.cc/2022/Conference/Paper3553/Reviewer_sAeN — 2021-10-31T11:42:58.706000+00:00

**main_review:**

Strengths:
- The ARC metric is interesting and novel. The authors also show that has concrete benefits in allowing us to estimate which generative model would help in robust training.
- Empirical results are good, good number of datasets.

Weakness:
- One issue is a missing part of the proof of theorem 1. In the proof, the authors define a distribution D' by a mapping of average distance epsilon from D. This is clearly an upper bound on the Wasserstein distance, but to show that it is the Wasserstein distance, i.e. the minimal coupling is missing. Without this correction, I cannot take the theoretical part (which is the major novelty) into account.
- While the ARC metric is interesting, to compute it we need to compute several robust classifiers. This makes it pointless in practice as we could, in less computation time, directly measure the robust accuracy that we are interested in.
- Missing ablation study - in C.3 the authors show that if they generate 15M and then sample 10M to do robust training, their sampling is better than randomly taking 10M. What is missing is the results of training on the whole 15M. As the whole 15M are already generated, what would be the benefit of sampling 10M if it doesn't perform better?

**confidence:**

3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.

**summary_of_the_paper:**

The paper investigates how adding additional synthetic data can help with robust training.
While the basic idea is very simple, the paper adds an interesting theoretical analysis that allows us to estimate what generative distribution would work best for robust training.

**summary_of_the_review:**

The paper offers some interesting theoretical and practical results, but without the hole in the proof fixed I do not think it should be accepted. I will gladly raise my review if this is adressed.

**correctness:**

4: All of the claims and statements are well-supported and correct.

**technical_novelty_and_significance:**

3: The contributions are significant and somewhat new. Aspects of the contributions exist in prior work.

**empirical_novelty_and_significance:**

2: The contributions are only marginally significant or novel.

**flag_for_ethics_review:**

- NO.

**recommendation:**

6: marginally above the acceptance threshold

---

### ICLR.cc/2022/Conference/Paper3553/Reviewer_NSbG — 2021-11-02T19:26:11.751000+00:00

**main_review:**

The paper studies an important problem for adversarial robustness, and I like the theoretical analysis part. My concern is mainly on the experiments:
* For CelebA, CIFAR-100, ImageNet, why is there only one baseline while for Table 1, there are several other baselines.
* Could you provide some comparisons between the adversarial training on normal synthetic distribution and robust synthetic distribution?

And I have an additional questions:
* It's quite interesting that the performance of DDPM is much better than other generative models, is there any explanations for this? Could you provide an ablation study where a) use DDPM and standard synthetic metric b) use DDPM and robust synthetic metric?

**confidence:**

4: You are confident in your assessment, but not absolutely certain. It is unlikely, but not impossible, that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work.

**summary_of_the_paper:**

The paper proposed a new metric for how well a synthetic distribution can help to improve the adversarial robustness. This metric is designed based on measuring conditional Wasserstein distance between the two distributions.

**summary_of_the_review:**

The paper studies an important problem for adversarial robustness, and I like the theoretical analysis part. My concern is mainly on the experiments. 

**correctness:**

4: All of the claims and statements are well-supported and correct.

**technical_novelty_and_significance:**

3: The contributions are significant and somewhat new. Aspects of the contributions exist in prior work.

**empirical_novelty_and_significance:**

3: The contributions are significant and somewhat new. Aspects of the contributions exist in prior work.

**flag_for_ethics_review:**

- NO.

**recommendation:**

6: marginally above the acceptance threshold

---

### ICLR.cc/2022/Conference/Paper3553/Reviewer_fLTj — 2021-11-02T20:39:31.894000+00:00

**main_review:**

The paper is a very good contribution to the research on adversarial robustness. The authors manage to push the SOTA, explain why certain generative models work better at improving the robustness and extensively evaluate their approach across lots of datasets, attack models and hyperparameters. Related work is described and contrasted. Using generative models for robustness certainly is a very important direction for research.

ARC could also be an interesting metric for generative models in general. 

The paper is clearly written but sometimes a little bit cramped as the authors do a lot of things, especially in section 3. 

Small comments and questions:


- You write that you do a hyperparameter search on γ. Did you find that different values work better for different generative models?
- Have you tried different ratios of real and synthetic images in the batch? How does it interact with γ?
- The improvement on especially imagenet is rather small. Do you have any intuition why?
- On the top of page 8 you talk about outperforming Zhang et al. 2020 but I don't see it listed in table 4.
- While you can infer it from the rankings it would be helpful to remind readers what metrics in table 5 are increasing or decreasing with quality (just a small arrow pointing up or down next to the metric would help). 

- The epsilon ball is sometimes written as Ball_e(x) and sometimes as Ball_x(e) (bottom of page 4 and bottom of page 5)
- Figure 1: The caption starts with "Why robust discrimination is effective?" Either this should be "Why is robust discrimination effective" or shouldn't end in a question mark. Same for page 5 "Why non-robust discrimination...?". 


**confidence:**

4: You are confident in your assessment, but not absolutely certain. It is unlikely, but not impossible, that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work.

**summary_of_the_paper:**

The paper investigates if generative models can be used to improve the robust accuracy of image models. The authors show that the current SOTA across multiple attack models and commonly used datasets can be significantly improved by using generative models. They show that the conditional Wasserstein difference between the test distribution and the one learned by the generative model is an upper bound for the difference in robustness achieved by models trained on either distribution. 
They investigate what generative models provide good proxy distributions by robustly training discriminators and using their accuracy at different attack strengths as a metric. The discriminators are also shown to be helpful to order generated samples by their effectiveness for adversarial training. 

**summary_of_the_review:**

The authors provide an in depth evaluation of using generative models to augment adversarial training, showing large improvements and interesting insights both empirical and analytical. I think the paper should be accepted.

**correctness:**

4: All of the claims and statements are well-supported and correct.

**technical_novelty_and_significance:**

3: The contributions are significant and somewhat new. Aspects of the contributions exist in prior work.

**empirical_novelty_and_significance:**

3: The contributions are significant and somewhat new. Aspects of the contributions exist in prior work.

**flag_for_ethics_review:**

- NO.

**recommendation:**

8: accept, good paper

---

### ICLR.cc/2022/Conference/Paper3553/Reviewer_c1MR — 2021-11-04T06:02:27.716000+00:00

**main_review:**

Strengths:

1. The paper captures the utility of a proxy distribution for ensuring robustness via conditional Wasserstein distance between the proxy distribution and real distribution.

2. Given that estimating the conditional Wasserstein distance is prohibitive, the paper proposed a tractable metric based on robust discrimination between proxy and real distribution to measure the utility of a proxy distribution for the underlying task.

3. Extensive experiments on five standard image benchmarks demonstrate the utility of the proposed method in improving model robustness by utilizing synthetic images produced by generative models.

4. The experimental results in the paper also show that widely used quality metrics for the generative models (e.g., FID) fail to capture their utility to general synthetic images that can ensure robustness for real images.

Weaknesses/questions:

1. What does PORT stand for?

2. What is the motivation for working 64x64 size images for ImageNet as opposed to utilizing usual 256x256 or 224x224 image sizes? Would the performance improvements attained by the proposed method scale to larger images?

3. In last line of page 5, '...our trained discriminator...' --> '...our trained *robust discriminator...'?  Also, should $f(x)$ be $\sigma(x)$?

4. What does ARC stand for?

5. While comparing with RST in Section 3.1.2, do you use $L_{smooth}$ in the definition of $L_{adv}$ in Section 2.3?

**confidence:**

3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.

**summary_of_the_paper:**

This paper focuses on utilizing synthetic images generated by a generative model for the task of achieving robustness to adversarial attacks. Towards this, the paper aims to assess the suitability of the proxy distribution defined by the generative model for the underlying task. The paper shows that conditional Wasserstein distance serves as a selection criterion for the proxy distribution. Acknowledging the intractability of estimating the conditional Wasserstein distance, the paper then proposed a novel metric based on robust discrimination between the proxy distribution and the real distribution. Finally, the paper empirically demonstrates that using synthetic images from a suitable generative model can indeed improve the robust and clean accuracy of the model over existing baselines.

**summary_of_the_review:**

The paper studies an important problem of improving the model robustness against adversarial attacks. Towards this paper aims to leverage the recent advancements in the area of generative models. The paper shows that utilizing the synthetic images generated from suitably chosen generative models can boost model robustness. The paper both theoretical and empirically studies various metrics to select the correct generative model for the underlying task.

**correctness:**

4: All of the claims and statements are well-supported and correct.

**technical_novelty_and_significance:**

3: The contributions are significant and somewhat new. Aspects of the contributions exist in prior work.

**empirical_novelty_and_significance:**

3: The contributions are significant and somewhat new. Aspects of the contributions exist in prior work.

**flag_for_ethics_review:**

- NO.

**recommendation:**

8: accept, good paper

---

## Official Comments (multi-round discussion)

### ICLR.cc/2022/Conference/Paper3553/Authors — 2021-11-15T18:00:39.611000+00:00

**title:**

Response to reviewer c1MR

**comment:**

We thank the reviewer for the positive feedback on our paper. Please find our response to your concerns and suggestions below.

**What does PORT stand for?**

It stands for PrOxy distributions in Robust Training (PORT). We have italicized the expression on page-2 line-6 to further highlight it.
&nbsp;

**What is the motivation for working 64x64 size images for ImageNet as opposed to utilizing usual 256x256 or 224x224 image sizes? Would the performance improvements attained by the proposed method scale to larger images?**

The cost of both sampling from the generative models and training a classifier on sampled images increases quadratically with image resolution. Due to the large size of ImageNet (1.2M images), this cost overhead becomes a significant bottleneck. Thus we use smaller resolution images when working with ImageNet.

However, we do show that our method also improves performance on large resolution images. We show this on the AFHQ dataset which has 224x244 size images (Table 8). 
&nbsp;

**In last line of page 5, '...our trained discriminator...' --> '...our trained robust discriminator...'? Also, should  $f(x)$ be $\sigma (x)$?**

Thanks for pointing this out. We have updated it in the paper.  

**What does ARC stand for?**

We use ARC (Area under Robust discrimination Curve) to refer to the area under the robust discrimination accuracy v.s. perturbation curve. We define it in section 2.2 of the paper. 

**While comparing with RST in Section 3.1.2, do you use $L_{smooth}$ in the definition of $L_{adv}$ in Section 2.3?**

Yes, we use $L_{smooth}$ as $L_{adv}$ in Section 3.1.2. Our formulation in Section 2.3 is general and applicable to any adversarial robustness loss function. 



---

### ICLR.cc/2022/Conference/Paper3553/Authors — 2021-11-15T18:23:04.078000+00:00

**title:**

Response to reviewer fLTj

**comment:**

We thank the reviewer for the positive feedback on our paper. Please find our response to your concerns and suggestions below.

**You write that you do a hyperparameter search on $\gamma$. Did you find that different values work better for different generative models?**

We conduct this hyperparameter search for the CIFAR-10 dataset (figure 7) and find that $\gamma=0.4$ is the best choice. For each of the dataset, we find that samples from diffusion models are most helpful. Thus the question is whether the optimal $\gamma$ value for CIFAR-10 is also the best for other datasets.

Following the reviewer's suggestion, we also conducted this search for the CIFAR-100 dataset. Following results show that  $\gamma=0.4$ is also the best choice for CIFAR-100 dataset. We used 1M samples from the DDPM model and trained a ResNet18 network for this experiment. 

| $\gamma$&ensp; 	| 0.15&ensp; 	| 0.40&ensp; 	| 0.50&ensp; 	| 0.75&ensp; 	| 0.90 	|
|:--:	|:--:	|:--:	|:--:	|:--:	|:--:	|
| Clean accuracy&ensp; 	| 60.6&ensp; 	| **64.7**&ensp; 	| 64.5&ensp; 	| 62.2&ensp; 	| 59.8 	|
| Robust accuracy&ensp;	| 27.6&ensp; 	| **27.7**&ensp; 	| 26.4&ensp; 	| 23.7&ensp; 	| 21.9 	|

**Have you tried different ratios of real and synthetic images in the batch? How does it interact with $\gamma$?**

We observed that changing the ratio of real and synthetic images in each batch had a similar effect as changing gamma, i.e., using an equal number of synthetic and real images outperforms settings where either large number of synthetic or large number of real images are used. 

**The improvement on imagenet is rather small. Do you have any intuition why?**

This is because of the underlying limitation of generative models on the ImageNet dataset. ImageNet is a difficult dataset for generative models due to the very large and diverse number of classes. Even state-of-the-art generative models struggle to generate high fidelity and diverse images on this dataset [1, 2].

This limitation is evident when we train a model on only the synthetic dataset and measure its performance on real data. On the CIFAR-10 dataset, using synthetic data alone outperforms using real data (Table-6). However, on ImageNet, synthetic data alone struggles to match the performance of real data. For example, a ResNet50 network trained on synthetic data from state-of-the-art diffusion models achieve 63% top-1 accuracy [3]. In contrast, training on real data easily achieves 76% top-1 accuracy with the identical model [3]. 

In summary, our community needs better generative models on ImageNet. Our work is forward looking from the perspective that as better generative models become available, the benefits of our approach on the ImageNet dataset will further increase. 


**On the top of page 8 you talk about outperforming Zhang et al. 2020 but I don't see it listed in table 4.**

Thanks for identifying this missing comparison. We have added it in Table 5 (previously table 4). We achieve more than 12 percentage point higher certified robust accuracy than Zhang et al. 

**While you can infer it from the rankings it would be helpful to remind readers what metrics in table 5 are increasing or decreasing with quality (just a small arrow pointing up or down next to the metric would help).**

This is a very helpful suggestion. We’ve added these arrows in Table 6 (previously table 5). 

**The epsilon ball is sometimes written as Ball_e(x) and sometimes as Ball_x(e) (bottom of page 4 and bottom of page 5)**

We have fixed this issue by consistently using the $Ball_\epsilon(x)$ notation.

**Figure 1: The caption starts with "Why robust discrimination is effective?" Either this should be "Why is robust discrimination effective" or shouldn't end in a question mark. Same for page 5 "Why non-robust discrimination...?".**

Thanks for identifying these grammar issues. We have fixed both.

**This paper is sometimes a little bit cramped as the authors do a lot of things, especially in section 3.**

We agree, since it's sometimes hard to provide a rigorous set of experimental results within the short page limit. We will alleviate this issue in the camera ready version of the paper. 

&ensp;


1. Nichol, Alex, and Prafulla Dhariwal. "Improved denoising diffusion probabilistic models." arXiv preprint arXiv:2102.09672 (2021).
2. https://paperswithcode.com/sota/conditional-image-generation-on-imagenet
3. Ho, Jonathan, et al. "Cascaded diffusion models for high fidelity image generation." arXiv preprint arXiv:2106.15282 (2021).



---

### ICLR.cc/2022/Conference/Paper3553/Authors — 2021-11-15T18:47:08.628000+00:00

**title:**

Response to reviewer NSbG

**comment:**

We thank the reviewer for the constructive comments and feedback. Please find our response to your comments below.

**For CelebA, CIFAR-100, ImageNet, why is there only one baseline while for Table 1, there are several other baselines.**

We report multiple baselines on the CIFAR-10 dataset (Table-1), as this is the most commonly studied dataset in robust machine learning [1]. To address reviewer's concern on lack of baselines on other datasets, we take following steps.

1. **CIFAR-100**: We have added additional comparison with Cui et al. [2], Rade et al. [3], and Wu et al. [4] in Table 3.
2. **CelebA**: This dataset is mainly used for generative modeling and has not been the subject of prior work on adversarial robustness (leading to fewer baselines).  Nevertheless, we have added another baseline by training with TRADES [5] and showing our improvement when additional synthetic data is included with TRADES.
| CelebA 	| Clean accuracy 	| Robust accuracy 	|
|:--:	|:--:	|:--:	|
| TRADES [5] 	| 86.1 	| 61.2   |
| PORT	| 86.1 	| **62.7**  |
3. **ImageNet**: Similar to CelebA, we will provide another baseline using TRADES for this dataset. However, the scale of ImageNet and TRADES adversarial training has significant computational overhead, making it a time intensive process. We will provide the results as soon as they are available and most certainly add them in the camera-ready version of the paper.

We would also like to highlight that most previous baselines innovate on the algorithmic front in adversarial robustness [5, 6, 7] while we innovate on the data front. However our approach of including synthetic data is complementary to previous algorithmic improvement and thus it can be combined with them.  


**Could you provide some comparisons between the adversarial training on normal synthetic distribution and robust synthetic distribution?**

We are a bit unsure of what the reviewer means by normal and robust synthetic distribution?
1. *Are you referring to the synthetic data selection method?* If yes, we provide the comparison when selecting synthetic data randomly vs adaptively using our robust discriminators in Table 11.
2. *Are you referring to very helpful and not very helpful generative models as robust and normal?* If yes, we provide a rigorous comparison of different generative models in Table 4 and 6. 

**It's quite interesting that the performance of DDPM is much better than other generative models, is there any explanations for this?**

This intriguing observation was indeed our motivation to dig deeper into the success of different generative models. We explain it using 1) Our theoretical framework on when a generative models helps and resulting ARC metric (Section 2)  and 2) Experimentally demonstrating how the ARC metric can explain the success of diffusion based models and multiple others (​​Table 6 in Section 3.2) 

**Could you provide an ablation study where a) use DDPM and standard synthetic metric b) use DDPM and robust synthetic metric?**

We provide this comparison in Table 11 in Appendix. We show that selecting samples based on ARC, i.e., our synthetic metric based on robust discriminators, indeed outperform the standard baseline. 

We hope that the new experiments along with detailed response to the comments address all your concerns. If you find our response satisfactory, we kindly request you to reconsider your score. 

&ensp;

1. https://robustbench.github.io/
2. Cui, Jiequan, et al. "Learnable boundary guided adversarial training." Proceedings of the IEEE/CVF International Conference on Computer Vision. 2021.
3. Rade, Rahul, and Seyed-Mohsen Moosavi-Dezfooli. "Helper-based adversarial training: Reducing excessive margin to achieve a better accuracy vs. robustness trade-off." ICML 2021 Workshop on Adversarial Machine Learning. 2021.
4. Wu, Dongxian, Shu-Tao Xia, and Yisen Wang. "Adversarial Weight Perturbation Helps Robust Generalization." Advances in Neural Information Processing Systems 33 (2020).
5. Zhang, Hongyang, et al. "Theoretically principled trade-off between robustness and accuracy." International Conference on Machine Learning. PMLR, 2019.
6. Wu, Dongxian, Shu-Tao Xia, and Yisen Wang. "Adversarial weight perturbation helps robust generalization." arXiv preprint arXiv:2004.05884 (2020).
7. Gowal, Sven, et al. "Uncovering the limits of adversarial training against norm-bounded adversarial examples." arXiv preprint arXiv:2010.03593 (2020).






---

### ICLR.cc/2022/Conference/Paper3553/Authors — 2021-11-15T18:56:54.987000+00:00

**title:**

Response to reviewer sAeN

**comment:**

We thank the reviewers for the constructive feedback and comments. Please find our response to your comments below. 

**One issue is a missing part of the proof of theorem 1. In the proof, the authors define a distribution D' by a mapping of average distance epsilon from D. This is clearly an upper bound on the Wasserstein distance, but to show that it is the Wasserstein distance, i.e. the minimal coupling is missing.**

To address the reviewer's concern about the correctness of the proof, we added Lemma 3 (Appendix A.1) which proves that the Wasserstein distance between D and D' is equal to robustness of any classifier on distribution D. In this proof, we show that the mapping from D to D’ is indeed the minimal coupling.

We also want to clarify that the proof does not depend on Lemma 3 and is complete without it. The first few paragraphs of the proof of Theorem 1(Appendix A.1), in which Lemma 3 is stated, are merely a proof sketch. We included these in the proof only to make it easier to understand. The full proof is provided at near the end of subsection A1. In the updated version, we have disentangled the sketch and main proof and clearly labeled them. If the reviewers think the proof sketch is more confusing than helpful, we will be happy to remove it and only keep the full proof. 


**While the ARC metric is interesting, to compute it we need to compute several robust classifiers. This makes it pointless in practice as we could, in less computation time, directly measure the robust accuracy that we are interested in.**

Our key reason to develop the metric ARC was to explain the phenomenon in Table 6, i.e., some generative models help significantly more than others in robust training. The need to develop such a metric was critical as existing metrics such as FID and inceptions score, which are widely used, fail to explain this phenomenon. In contrast, ARC perfectly explains the ranking across generative models. It also provides additional insights by connecting the success of synthetic data with its distance from real data distribution. 

To summarize, our goal was not to develop a metric that empirically determines the best generative model. As the reviewer noted, this can be done using other efficient approaches. Instead, our goal to develop ARC was to characterize this phenomenon and provide further insights into it. 

**Missing ablation study - in C.3 the authors show that if they generate 15M and then sample 10M to do robust training, their sampling is better than randomly taking 10M. What is missing is the results of training on the whole 15M. As the whole 15M are already generated, what would be the benefit of sampling 10M if it doesn't perform better?**

We answer it in a step by step manner.
1. *What is missing is the results of training on the whole 15M.*

&ensp; &ensp; We find that using all 15M images brings a small improvement (0.1-0.2%) over using a 10M subset. When training a ResNet18 network on CIFAR-10 ($\ell_\infty$) it improves clean accuracy from 84.6 to 84.8 (+0.2) and robust accuracy 55.7 to 55.8 (+0.1).

2. *As the whole 15M are already generated, what would be the benefit of sampling 10M if it doesn't perform better?*

&ensp; &ensp; The goal of this experiment is to show that some samples are more beneficial than others in robust training. Yes, using a rejection sampling based approach requires generating more images than necessary. The ideal approach would be to generate these most beneficial samples adaptively from the network. However, we are not aware of any existing adaptive sampler for diffusion models, thus had to resort to a rejection sampling based approach. We leave the question of how to develop an adaptive sampler for future work, as we believe that developing such adaptive samplers for diffusion models is an interesting question for future research. 

---

### ICLR.cc/2022/Conference/Paper3553/Authors — 2021-11-15T19:04:57.951000+00:00

**title:**

Summary of our response

**comment:**

We thank all reviewers for providing very constructive and detailed feedback. We are delighted to know that the reviewers also find that improving adversarial robustness is an important challenge and our solution to it is detailed and insightful. Following is a summary of the key points in our rebuttal. 

1. *Additional search for gamma*. Following suggestion from Reviewer fLTj, we conducted another hyperparameter search for gamma on the CIFAR-100 dataset. We show that it also validates our choice of using $\gamma$=0.4 

2. *Additional baselines.* Following the suggestion from Reviewer NSbG, we have added additional baselines for both CIFAR-100 and Celeb-A datasets. Note that we already include a large set of baselines on the widely used CIFAR-10 dataset. We've also provided a future plan to include more baselines on the ImageNet dataset since it requires running very computationally expensive experiments on our end. 

3. *Additional clarification on Proof of theorem 1.* In a detailed response, we argue that the limitation pointed out by the reviewer sAeN  in our proof is not true and likely it's a misunderstanding. To avoid this confusion, we have separated our proof sketch and main proof in Appendix A.1. We have also added Lemma 3 (in Appendix A.1), specifically to address the reviewer's concern.

4. *Motivation of section 3.2.* We provided additional experimental results on all 15M images, as asked by reviewer sAeN . We also further clarified our motivation behind running experiments on ARC and adaptive sampling in this section. Our main motivation was to characterize why different generative models have a different impact on robustness and provide deeper insights into this phenomenon.

5. *Presentation changes*. Following suggestions from reviewers, we have made the necessary changes to improve the presentation of the paper.

---

### ICLR.cc/2022/Conference/Paper3553/Reviewer_sAeN — 2021-11-18T11:39:14.894000+00:00

**title:**

Response to authors

**comment:**

I upgraded my score based on the correction to the proof. 

The reason I still do not think this should be accepted is that the main novelty is of little value. 

The main idea of adding samples using a generative model is not novel. The main novel contribution is the ARC metric and its derivation, and I do not see any insight that it gives besides the ability to predict which generative model will be better for robust training. As the ARC is slower than simply training the model and checking directly it adds nothing.

---

### ICLR.cc/2022/Conference/Paper3553/Authors — 2021-11-19T03:06:43.001000+00:00

**title:**

Response to the critique on novelty (part-1)

**comment:**

We thank the reviewer for increasing the score. However, we would like to further address the critique that our main novelty is of little value. 

**The main idea of adding samples using a generative model is not novel.**

Our core observation that synthetic data helps in adversarial training is a novel observation and has tremendous value. We deliberately integrate synthetic data with the simplest baseline formulation of adversarial training, i.e., projected gradient descent (PGD) attack based adversarial training [1], and show that adding synthetic data alone surpasses numerous algorithmic improvements made in previous works. 

| Authors           	| Method                                                  	| Venue        	| Robust accuracy 	|
|-------------------	|---------------------------------------------------------	|--------------	|-----------------	|
| Madry et al. [1]  	| *PGD based adversarial training*                          	| ICLR’18      	| *44.1*            	|
| Mao et al. [2]    	| Metric learning to improve adversarial training         	| NeurIPS’19   	| 47.4            	|
| Singh et al. [3]  	| Latent layers for better adversarial training           	| IJCAI’19     	| 49.1            	|
| Sitawarin et al. [4]  	| Curriculum adversarial training                         	| AISec '21    	| 50.7            	|
| Qin et al. [5]    	| local linearization with adversarial training           	| NeurIPS’19   	| 52.8            	|
| Cui et al. [6]    	| Boundary guided adversarial training                    	| ICCV’21      	| 52.9            	|
| Zhang et al. [7]  	| Tradeoff inspired adversarial training (TRADES)         	| ICML’19      	| 53.1            	|
| Huang et al. [8]  	| Self-adaptive adversarial training                      	| Neurips’20   	| 53.4            	|
| Zhang et al. [9]  	| Friendly adversarial training                           	| ICML’20      	| 53.5            	|
| Pang et al. [10]  	| Hypersphere embeddings with adversarial training        	| NeurIPS’20   	| 53.7            	|
| Pang et al. [11]  	| *Strong regularization in PGD based adversarial training* 	| ICLR’20      	| *54.4*            	|
| Hendrycks et al. [12]   	| Adversarial pre-training on larger datasets             	| ICML’19      	| 54.9            	|
| Wu et al. [13]    	| Adversarial weight perturbation in adversarial training 	| NeurIPS’20   	| 56.2            	|
| Wang et al. [14]  	| Misclassification aware adversarial training            	| ICLR’20      	| 56.3            	|
| Chen et al. [15]  	| Low-temperature distillation in adversarial training    	| Arxiv’21     	| 57.7            	|
| Addepalli et.[16] 	| Adversarial training beyond perceptual limits           	| ICML WAML’21 	| 58.0            	|
| **Our work** 	| PGD based adversarial with strong regularization + Synthetic data           	| --- 	| **60.6**            	|

Following the suggestion from Reviewer NSbG, we have also demonstrated that our approach is complementary to algorithmic innovations and can be combined with them (Table 3). We also show generality of our approach by combining it with randomized smoothing, where it achieves even higher certified robustness than the baseline that uses additional 500K real world samples (Table 5). 

*Setup.* All baselines in the aforementioned table are borrowed from robustbench [17], which is a standardized benchmark in the community. For fairness, we only compared results across similar architecture, i.e,. wide-resnets and in the setting of not using extra data and at 8/255 perturbation budget in $\ell_\infty$ threat model on the CIFAR-10 dataset.

 

---

### ICLR.cc/2022/Conference/Paper3553/Authors — 2021-11-19T03:13:24.840000+00:00

**title:**

Response to the critique on novelty (part-2) 

**comment:**

**The main novel contribution is the ARC metric and its derivation** 

We respectfully disagree. Our paper contributions extend much beyond ARC. In particular, 
1. We not only uncover that synthetic data can provide a large boost in adversarial robustness, but also demonstrate its success across different datasets, network architectures, threat models, and both empirical and certified robustness. 
2. To understand the tremendous benefits of synthetic data, we provide a theoretical framework to characterize how robustness transfers from synthetic to real data distribution (Theorem 1). We also empirically validate our proposed analytical bound (Appendix A.5).
3. We propose the ARC metric that allows us to explain why some generative models help more than others. 
4. Using the design principle from the ARC metric, we also demonstrate that some synthetic samples help more than others in robust training (Table 11). 

**I do not see any insight that it gives besides the ability to predict which generative model will be better for robust training. As the ARC is slower than simply training the model and checking directly it adds nothing.**

We would like to clarify that the ARC metric provides multiple benefits.

**Objective**: ARC satisfies two objectives, simultaneously. 
1. *How to approximate distributional distance between synthetic and real data distribution?* We prove that the distributional distance between synthetic and real data can determine the benefit of synthetic data in robust training (Theorem 1). ARC, which can be empirically estimated, enables us to compute a bound on the distributional distance (Theorem 2)  
2. *How to successfully predict the ranking of generative models?* ARC also excels at the task where it predicts the ranking of generative models much more accurately than other metrics, such as FID and Inception score (Table 6).   

**Impact**: Going beyond predicting ranking of generative models, it also allows us to characterize the benefit of individual samples. Using tools from ARC, we develop a technique that identifies instances which are most beneficial for robust training (section 2.3, Table 11).

If the reviewer believes that it will benefit the paper, we are happy to incorporate this discussion on ARC benefits vs. its computational cost in the paper. 


---

### ICLR.cc/2022/Conference/Paper3553/Authors — 2021-11-19T03:15:07.012000+00:00

**title:**

Response to the critique on novelty (part-3)

**comment:**

**References**

1. Madry, Aleksander, et al. "Towards Deep Learning Models Resistant to Adversarial Attacks." International Conference on Learning Representations. 2018.
2. Mao, Chengzhi, et al. "Metric Learning for Adversarial Robustness." Advances in Neural Information Processing Systems 32 (2019): 480-491.
3. Singh, Mayank, et al. "Harnessing the vulnerability of latent layers in adversarially trained models." IJCAI (2019).
4. Sitawarin, Chawin, Supriyo Chakraborty, and David Wagner. "SAT: Improving Adversarial Training via Curriculum-Based Loss Smoothing." Proceedings of the 14th ACM Workshop on Artificial Intelligence and Security. 2021.
5. Qin, Chongli, et al. "Adversarial Robustness through Local Linearization." Advances in Neural Information Processing Systems 32 (2019): 13847-13856.
6. Cui, Jiequan, et al. "Learnable boundary guided adversarial training." Proceedings of the IEEE/CVF International Conference on Computer Vision. 2021.
7. ​​Zhang, Hongyang, et al. "Theoretically principled trade-off between robustness and accuracy." International Conference on Machine Learning. PMLR, 2019.
8. Huang, Lang, Chao Zhang, and Hongyang Zhang. "Self-adaptive training: beyond empirical risk minimization." Advances in Neural Information Processing Systems 33 (2020).
9. Zhang, Jingfeng, et al. "Attacks which do not kill training make adversarial learning stronger." International Conference on Machine Learning. PMLR, 2020.
10. Pang, Tianyu, et al. "Boosting Adversarial Training with Hypersphere Embedding." NeurIPS. 2020.
11. Pang, Tianyu, et al. "Bag of Tricks for Adversarial Training." International Conference on Learning Representations. 2020.
12. Hendrycks, Dan, Kimin Lee, and Mantas Mazeika. "Using pre-training can improve model robustness and uncertainty." International Conference on Machine Learning. PMLR, 2019.
13. Wu, Dongxian, Shu-Tao Xia, and Yisen Wang. "Adversarial Weight Perturbation Helps Robust Generalization." Advances in Neural Information Processing Systems 33 (2020).
14. Wang, Yisen, et al. "Improving adversarial robustness requires revisiting misclassified examples." International Conference on Learning Representations. 2020.
15. Chen, Erh-Chung, and Che-Rung Lee. "LTD: Low Temperature Distillation for Robust Adversarial Training." arXiv preprint arXiv:2111.02331 (2021).
16. Addepalli, Sravanti, et al. "Towards Achieving Adversarial Robustness Beyond Perceptual Limits." ICML 2021 Workshop on Adversarial Machine Learning. 2021.
17. https://robustbench.github.io


---

### ICLR.cc/2022/Conference/Paper3553/Reviewer_fLTj — 2021-11-19T10:42:08.714000+00:00

**title:**

Answer

**comment:**

Thanks for the detailed response.

---

### ICLR.cc/2022/Conference/Paper3553/Reviewer_sAeN — 2021-11-21T06:59:11.012000+00:00

**title:**

Answer

**comment:**

Considering your response, I was convinced that the paper has more novelty/merit than I first gave it credit for. While the ARC is still useless (in my opinion) as a metric for ranking, it does have other value. I will raise my score. 

---

### ICLR.cc/2022/Conference/Paper3553/Reviewer_c1MR — 2021-11-29T06:23:58.361000+00:00

**title:**

Post rebuttal

**comment:**

Thank you for the response. 

---

### ICLR.cc/2022/Conference/Paper3553/Reviewer_NSbG — 2021-11-29T08:01:24.099000+00:00

**title:**

Post rebuttal.

**comment:**

Thank you for the detailed response! I have some remaining questions.
1. Why do you only use the ARC to choose a generative model instead of training a better model for adversarial training?
2. I am thinking that whether using ARC to choose a good synthetic distribution is necessary. Since you can train different generative models and use the validation dataset to choose the generative model that can train the best robust classifier. Could you provide more discussion on this?
Thanks!

---

### ICLR.cc/2022/Conference/Paper3553/Authors — 2021-11-30T03:49:09.025000+00:00

**title:**

Further clarification on our motivation to develop ARC

**comment:**

We would like to clarify that our goal is *not* to develop a metric that solely determines the best generative model. As the reviewer noted, this can be done more efficiently by training robust classifiers on the synthetic data. 

However, this approach only characterizes *which* generative models are most helpful and doesn’t answer *why* some models are more helpful than others. In particular, *why are diffusion models surprisingly more beneficial than other generative models (Table 4)*? Our goal to develop ARC was to answer this question and provide further insights into the phenomenon (Figure 1, 3; Table 6, 10).

In particular, we aim to satisfy the following two objectives using ARC, simultaneously: 
1. **How to approximate distributional distance between synthetic and real data distribution?** We prove that the distributional distance between synthetic and real data can determine the benefit of synthetic data in robust training (Theorem 1). ARC, which can be empirically estimated, enables us to compute a bound on the distributional distance (Theorem 2).
2. **How to successfully predict and explain the ranking of generative models?** ARC also excels at the task where it predicts the ranking of generative models much more accurately than other metrics, such as FID and Inception score (Table 6). In doing so, ARC also identifies that diffusion models are most helpful because the synthetic data from these models is hardest to distinguish from real data under robust classification (Figure 3). 

**Further Impact**: Going beyond predicting ranking of generative models, it also allows us to characterize the benefit of individual samples. Using tools from ARC, we develop a technique that identifies instances which are most beneficial for robust training (section 2.3, Table 11).

We will be happy to add a discussion on it in the updated version of the paper. 


---

## Decision

### ICLR.cc/2022/Conference/Program_Chairs — 2022-01-20T16:44:39.618000+00:00

**title:**

Paper Decision

**comment:**

In this work, authors use proxy distributions learned by advanced generative models to improve adversarial robustness. In the discussion period, authors did a good job in addressing reviewers' questions and comments. All reviewers think the paper is above the accept threshold, so do I.

**decision:**

Accept (Poster)

---
