# Certified Adversarial Robustness via Randomized $\alpha$-Smoothing for Regression Models

- **Label:** `jLUbLxa4XV`
- **Venue:** NeurIPS 2024  (NeurIPS 2024 poster)
- **Forum:** https://openreview.net/forum?id=jLUbLxa4XV
> _Fetched 2026-06-26T23:37:22.867585+00:00_

## Thread summary
- decision: 1
- official_comment: 11
- official_review: 3
- rebuttal: 4

## Official Reviews

### NeurIPS.cc/2024/Conference/Submission10280/Reviewer_ZCs7 — 2024-06-29T06:35:20.533000+00:00

**summary:**

This paper considers randomized smoothing for (unbounded) regression models. An $\alpha$-trimming procedure is proposed in order to increase certification strength. Experiments to illustrate the effectiveness of the approach are conducted on synthetic datasets as well as camera re-localization tasks.

**strengths:**

The problem of scaling up certified robustness (e.g., via randomized smoothing-based methods) to regression models is an important one to consider, and is certainly of interest to the Neurips audience.

**weaknesses:**

Overall, the paper could use an extensive revision and polishing. There is quite a bit of terminology used throughout the paper that is not clearly defined, and the assumptions underlying some of the mathematical results are not made explicit/clear. In particular, some language from classification seems to be infiltrating the supposed regression setting of this paper, which makes things very difficult to understand. The paper seems to be heavily dependent on [17], with the only notable novelty being the incorporation of $\alpha$-trimming into the smoothing framework.

See the Questions section below.

**questions:**

1. Line 68: You mention the prior works [17, 19, 7, 4, 16] that develop smoothing methods for regression models very briefly, and assert that they all suffer from limitations. However, more explanation is needed to distinguish your contributions from theirs. I suggest including more in-depth discussion on the contributions of these works, and clarify how your method differs/overcomes their particular limitations.
2. In the introduction, you use the acronym CR to denote "certified robustness," but in Section 3, you use CR to denote "certified regression." Please only use this acronym to denote one thing throughout the paper.
3. Lines 93 and 116: "...is the lower bound on the probability of accepting prediction in ith output variable." What does this mean? If we're dealing with regression models, what does "accepting prediction" of a particular output variable mean?
4. Line 118: What is the "accepted region"?
5. Line 118: So does Proposition 1 not apply to $\ell_1$ threats?
6. Figure 1: I don't find this figure particularly enlightening/explanatory. For example, what is the index $m$ here? Also, what is the index $k$ here? In your explanation of $\alpha$-trimming, you use $k$ to denote an arbitrary index (after computing the order statistics). Furthermore, why is the region around $y_{1:k}$ nonconvex, but the region around $y_{m:t}$ convex? In your Theorem 2 statement, you assume that the "accepted region" (again, this is not clearly defined anywhere) for each output is convex. Finally, what is the difference between the outputs and regions ($y_{1:k}$, $y_{m:t}$, and their green regions) within the red dashed box, and those same outputs and regions outside the red dashed box?
7. Line 150: "...the following equality holds..." I think you mean inequality.
8. Line 151: What is $q$ in (9)? Is this allowed to be any real number in $[0,1]$?
9. Line 157: Is it ever possible for the change from $q$ to $I_q(n-[\alpha n], n+[\alpha n])$ to be a decrease?
10. Theorem 2: One of the powers of randomized smoothing (for classification) is that it allows us to "robustify" a non-robust base classifier. However, it seems like the strength of your robustness certificate for your smoothed classifier depends heavily on the underlying robustness of the base classifier. That is, it appears as though in order for your smoothed classifier to have a high level of robustness, you need your base classifier to have a high level of robustness. Can you please discuss and clarify these aspects? If this interpretation is correct, this could result in significant limitations.
11. Algorithm 1, Linw 5: What does it mean for a continuous-valued regression prediction to be "correct"? Isn't the "correct" output for a given input a singleton in $\mathbb{R}^t$ and hence a measure-zero set?
12. Line 249/Section 5: I suggest moving this paragraph to around Lines 68--71 to better clarify your contributions at the outset.

**limitations:**

N/A.

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

### NeurIPS.cc/2024/Conference/Submission10280/Reviewer_pBXb — 2024-07-03T00:07:25.038000+00:00

**summary:**

Prior work extends the notion of a 'certified robustness radius' from classification tasks to a regression task. The prior state-of-the art for calculating these certified robustness bounds in the regression setting had a major shortfall: it exhibited major instabilities when applied to values with an unbounded range. This paper suggests a method that is better conditioned for unbounded random variables.

**strengths:**

The authors identify a popular bound in the classification case that currently does not have a practical analog for regression. They then develop a technique for extending such a bound to regression.

**weaknesses:**

1. The authors write that the method suggested by prior work in [17] fails for unbounded quantities in regression because it is 'unstable' however, they do not back up this claim. It would be nice if the authors could demonstrate this with experiments or explain why the method of [17] could not be expected to work for unbounded quantities.

2. There were some important terms that were not defined at all, like "accepted region" and "bag" in the appendix.

**questions:**

Suggestions/ Questions:

line 19: I suggest you note that adversarial training does provide some defense


line 43: it's not clear what 'normalized' $z$ means here


lines 126-128: I couldn't understand what this meant


figure 2: I'm having a hard time interpreting b and c. What is the blue line? what is the function $g$?


section 3.3: it seems that the data points between the $\alpha$th and $1-\alpha$th percentiles are what you call the ``accepted region" make sure the "accepted region" is defined!



line 228: % is in the wrong place

**limitations:**

It seems that there is a lot of prior work on $\alpha$ filtering in other contexts. Is it discussed when $\alpha$ filtering tends to work well/ not work well?

**soundness:**

3

**presentation:**

1

**contribution:**

3

**rating:**

5

**confidence:**

3

**flag_for_ethics_review:**

- No ethics review needed.

**code_of_conduct:**

Yes

---

### NeurIPS.cc/2024/Conference/Submission10280/Reviewer_wW8d — 2024-07-12T12:51:22.953000+00:00

**summary:**

This work extends current randomized smoothing on the regression task via the $\alpha$-trimming filter. A new probabilistic certificate bound for is given against the $l_p$ norm attack for all regression models with the unconstrained output. Comprehensive synthetic simulations and evaluation on the real-world camera re-localization task are conducted to demonstrate the effectiveness of the proposed method

**strengths:**

1. This work gives good theoretical insights and rigorous proof.

2. The derived certification bound is valid for any regression model with bounded or unbounded output.

**weaknesses:**

**Give more straightforward examples for equation (12).** As the main improvement brought by $\alpha-$ trimming filter lies on $I_{n,\alpha}^{-1}(P)$, it is recommended to give a more straightforward illustration of the situation when $I^{-1}_{n,\alpha}(P)$  provides better certified robustness than $P$, such as a curve or a table which shows different certified bound with different $P$ and $\alpha$.

**More explanation in Figures 4 and 5.** In Figure 4, after reading the experiment part, I still feel confused about why the predicted location of the camera is a trajectory but not a point. Moreover, I have not found any further explanation for Figure 5. It's recommended to explain the experiment results more which may help readers understand easier.

**Lack of comparative results.** This work lacks comprehensive comparative results with other certified robustness methods designed for the regression model.

**questions:**

I am curious about the probability calculated from equation (6) and (9). Is there a closed-form solution to get the probability or is the probability gotten by sampling? If is by sampling, will the sampling brought by smoothing delay the prediction process of the regression model?

**limitations:**

See the weakness.

**soundness:**

3

**presentation:**

2

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

## Author Rebuttals / Responses

### NeurIPS.cc/2024/Conference/Submission10280/Authors — 2024-08-05T08:31:39.171000+00:00

**rebuttal:**

The authors appreciate the reviewer's recognition of the theoretical rigor in the paper. This work represents the first universal certification framework for regression models designed to defend against adversarial examples during the inference stage. Below, we provide a detailed response and further insights to support our proposed methodology, demonstrating the value of our analysis and we hope they help in receiving higher scores and increasing the chance of publication.

**Give more straightforward examples for equation (12). As the main improvement brought by α− trimming filter lies on ...**

Equation (12) states that for a base regression model that generates outputs within the accepted region with probability $q$, the chance of observing a valid output after applying $\alpha$-trimming filter becomes $\textit{{I}}_q(n-[\alpha n],[\alpha n]+1)$. In order to show this is an improvement even for worst-case scenario, we proved that the filtering rate should be greater than a threshold denoted by $\alpha^+$. The inverse process has been used in Theorem 3 to estimate the certificate radii. Therefore, a plot for $\textit{{I}}_q(n-[\alpha n],[\alpha n]+1)$ vs $\alpha$ can better visualize this improvement. This visualization can be found in the attached PDF along with this rebuttal. This new visualization will be added to the final camera-ready version of the manuscript: *Figure 1 shows two different models one with $q=0.7$ and one with $q=0.9$. After applying $\alpha$-trimming the obtained probability of validity in the results are shown in blue and orange colours, respectively. In both settings, $\alpha^+$ values are demonstrated in vertical dashed lines and it can be observed that the success rate of the prediction ($\textit{{I}}_q(n-[\alpha n],[\alpha n]+1)$) is always greater than the assumed $q$ values for $\alpha \geq \alpha^+$. As described in the example in Lines 179- Line 189 of the manuscript, the corresponding $\alpha^+$ values are slightly greater than $1-q$ to ensure improvement even in worst-case scenarios.*

**More explanation in Figures 4 and 5. In Figure 4, after reading the experiment part, I still feel confused about why the predicted location of the camera is a trajectory but not a point. Moreover, I have not found any further explanation for Figure 5. It's recommended to explain the experiment results more which may help readers understand easier.**

Please note that for all these three evaluated scenes, a single camera is continuously moving along a path and taking images. For example, in Great Court scene as mentioned in the experiment, 760 images were taken in different locations within the scene. Therefore, when all the predicted positions are shown together, a trajectory from the locations of the camera can be obtained. However, for each predicted location, the estimated certification radius which is colour-coded for each point in Figure 4, gives a measure of how sensitive the prediction is against adversarial examples around the given image.
Figure 5, on the other hand, reflects the certified median error as defined in Line 230 for the scenes in comparison with certification of models with bounded outputs. In sensitivity analysis section (Appendix E) some aspects of these curves have been explained in detail. However, the following detailed explanation has been added to the main experiment section as reviewer suggested to better explain settings and the take home messages of the results: *As shown in these plots, $\alpha$-trimming filter consistently decreased the certified median error (orange curve) across all input perturbation ranges ($r$) compared to the results obtained by the base regression model (blue curve). The main reasons for this improvement are firstly, because of the better approximation of position parameters leveraging outlier removal and averaging using $\alpha$-trimming filter . Secondly, because of better certificate radii for each image in the scene which decreases penalization in the process of certified median error calculation. Leveraging the $\alpha$-trimming approach for smoothing, we are no longer worried about the output ranges, and no further assumptions such as large sample size or discount factor are required to provide a valid certificate.*

**Lack of comparative results. This work lacks comprehensive comparative results with other certified robustness methods designed for the regression model.**

Please note that one of the main claims of the paper is that this study is the first that proposes a technique that enables to provide certification for regression models with unbounded outputs. None of the existing techniques [17,19,7,4,16] are feasible to be used in the context of unbounded outputs or certification in the inference stage, unless setting some assumed bounds for the output as authors did for the work [17] in Figure 5 (top left) which is the most related work to this study. Therefore, this study should be considered as a standalone work and as a baseline for future studies not as an incremental improvement of previous studies.

**I am curious about the probability calculated from equation (6) and (9). Is there a closed-form solution to get the probability or is the probability gotten by sampling? If is by sampling, will the sampling brought by smoothing delay the prediction process of the regression model?**

Thanks for this question. Similar to the classification counterparts, the probability $ {p_A}_i$ should be estimated using sampling strategies and Monte Carlo estimation;  however, the lower bound estimate  $ \underline{p_A}_i$ is obtained by Clopper-Pearson interval prediction which gives a lower bound estimate given number of samples and required confidence level. Therefore, the delay caused by sampling can be compromised with the tightness of the lower bound (using smaller number of samples) and this is fully under control of the user.

---

### NeurIPS.cc/2024/Conference/Submission10280/Authors — 2024-08-05T08:47:03.540000+00:00

**rebuttal:**

We thank the reviewer for their valuable time spent on this manuscript, as well as their comments on the contribution of the work. Below, we reply to each comment separately.

**The authors write that the method suggested by prior work in [17] fails for unbounded quantities in regression because it is 'unstable' however, they do not back up this claim. It would be nice if the authors could demonstrate this with experiments or explain why the method of [17] could not be expected to work for unbounded quantities.**

A common assumption in [17] was the presence of lower and upper bounds for the model output for any input data. It was shown in [17] that as the difference between these bounds increases, the probabilistic certificate becomes impractical and approaches zero. This occurs because the averaging function used in the smoothing stage is highly sensitive to a single large outlier. Even one data point at the upper or lower bounds (assuming these bounds are large) can significantly alter the averaging function's result, making the output invalid (outside the accepted range). This fact was explained in Section 3.2. Therefore, in the unbounded scenario considered in this paper, the previous certificate is impractical due to the type of smoothing function used in that study. Figure 5 (top-left) illustrates the required discount factor (200%) as defined in [17] to achieve almost the same performance, highlighting the previous technique's failure for unbounded outputs.

**There were some important terms that were not defined at all, like "accepted region" and "bag" in the appendix.**

While the term “bag” simply refers to set of leftover data points after applying $\alpha$-trimming filter, the term “accepted region” is now clearly defined after Definition 1: *Based on Definition 1, users can define a region for $i^{th}$ continuous output variable by $\{z \mid diss_y(z,\textbf{y}_i) \leq \epsilon{y_i}\}$ as the accepted region where the output prediction can fit in without being considered as a wrong prediction.* This region is set by the user around $f(\textbf{x})$ to determine how much deviation is acceptable. For example, in camera- re-localization in a 3D scene with size $100m \times 100m$, the user might reasonably accept up to 0.5m deviations in the predictions.

**line 19: I suggest you note that adversarial training does provide some defense.**

Thanks for highlighting this important point. The authors believe that adversarial training is indeed one of the best strategies to defend against adversarial examples in the inference stage. This will be added to the camera-ready version for the sake of completeness.

**line 43: it's not clear what 'normalized' z means here.**

The normalization of $\textbf{z}$ is included because some divergences can only be applied to probability mass functions. This choice is up to the user, but in our paper, we used the $\ell_p$ norm as the measure of similarity without imposing any constraints on $\textbf{z}$.

**lines 126-128: I couldn't understand what this meant.**

This has been explained in response to the above question regarding the method in [17].

**figure 2: I'm having a hard time interpreting b and c. What is the blue line? what is the function g?**

In both figures in (b) and (c), blue lines demonstrate the certified range around the centre points as the input (e.g., $x_1=2, x_2=3$) for base regression model ($f(\textbf{x})$) that is visualized in (a). On the other hand, $g(\textbf{x})$ is the smoothing function defined in equation (8) applied to the results of base regression with different $\alpha$ values. Figure 2 (b) demonstrates the certificate for $\ell_2$ attack (circles around the evaluated points) and Figure 2 (c) demonstrates the certificate for $\ell_{\infty}$ attack (squares around the evaluated points). In both figures, smoothing using $\alpha$-trimming increased the certification area while for higher $\alpha$ values this range has been further increased.


**section 3.3: it seems that the data points between the $\alpha$-th and 1−$\alpha$-th percentiles are what you call the ``accepted region" make sure the "accepted region" is defined!**

Accepted region around a given value $y$, motivated by Definition 1, includes points whose dissimilarity with $y$ is smaller than a threshold defined by the user. This definition has been added to the revised manuscript as the reviewer has requested.

**line 228: % is in the wrong place.**

Thanks for mentioning this typo. It has been fixed in the revised manuscript.

**It seems that there is a lot of prior work on α filtering in other contexts. Is it discussed when $\alpha$-filtering tends to work well/ not work well?**

$\alpha$-trimming is a popular technique for outlier rejection in robust statistics. While the appropriate filter design might differ from one application to another depending on the criteria, Proposition 2 and Theorem 3 state how this filter should be designed in the context of certified robustness given a level of robustness and number of samples. A summary of other approaches in other contexts such as robust parameter estimation will be added to the camera-ready version of the paper.

---

### NeurIPS.cc/2024/Conference/Submission10280/Authors — 2024-08-05T08:55:30.452000+00:00

**rebuttal:**

**The problem of scaling up certified robustness (e.g., via randomized smoothing-based methods) to regression models is an important one to consider, and is certainly of interest to the Neurips audience.**

The authors would like to express their gratitude to the reviewer for recognizing the significance of the defined problem for the NeurIPS audience. This study is the first to apply the randomized smoothing technique to a broad class of regression models with both bounded and unbounded outputs. It provides proofs of their performance under constraints such as maximum permitted latency and limited computational resources, which restrict the number of examination points. Additionally, the results are benchmarked against the critical task of camera re-localization, where reliability is crucial for robotic vision and autonomous systems.

**Overall, the paper could use ...**

We appreciate the reviewer's efforts in reading the manuscript and providing feedback. Although the authors conducted several rounds of proofreading before the final submission, some typos might still be present, which will be corrected in the camera-ready revision, especially those mentioned by the reviewer in the following questions. In terms of underlying assumptions, to the best of our knowledge, there is no further assumptions needed in any of the results to be claimed. While the certification setup was designed for regression problems, we acknowledge that steps and model parameters are shared between classification and regression settings. The core concept of the randomized smoothing approach was initially developed for classification models and has been adapted for use in regression settings, leading to some similarities in terminology.
As noted in the manuscript and mentioned by the reviewer, this paper extends the results in [17] by incorporating $\alpha$-trimming into the smoothing process to address a broader class of regression models, including those with unbounded outputs which is the main focus of this paper. This new smoothing approach includes an end-to-end analysis and demonstrates through various theorems that output predictions are certifiable even with limited data points, unlike in [17] which required a large discount factor. Additionally, we present a robustness analysis against $\ell_p$ attacks, extending the $\ell_2$ attack analysis in [17]. The connection between the certification of regression and classification models is also provided to give readers a deeper understanding of their similarities.

**Line 68: You mention the prior works ...**

We thank the reviewer for highlighting the need to clarify the distinctions between this study and those referenced in [17, 19, 7, 4, 16]. Although these differences were briefly summarized in Line 68, the authors believe that a more detailed explanation in Section 5 (Related Work) provides a precise description of each study and their respective differences or limitations compared to our work. Our study presents a universal certification technique applicable to any regression model. If the explanations in Section 5 are deemed insufficient, we are happy to add further clarification. In summary, we noted that  *``The most related works to our study are [4,17] where in the former study, the object detection was investigated through the lens of certified regression, however, their analysis is relying on the scaling output of classifier models to expand the range of output values which constrains the architecture of considered models, and in the latter the certification was provided for a class of bounded output regression model in the asymptotic case. Compared to these methods, our approach provides a probabilistic certificate for all regression models (including models with a wide range of outputs) with a limited number of evaluations through drawing noisy samples.’’*

**In the introduction, you use the acronym...**

Thank you for pointing out this typo. The redundant acronym for certified regression has been removed in the revised version.

**Lines 93 and 116: "...is the lower bound on ...**

Please note that in the context of classification, a model is considered certifiably robust if any perturbation in the input sample does not change the output label prediction. For example, if the predicted label for the input sample $\textbf{x}$ is class A, it remains (or is highly likely to remain) class A for the perturbed sample $\textbf{x} + \boldsymbol{\delta}$. However, in the context of regression, due to the continuity of the output variable, any perturbation in the input causes changes in the output, which are directly related to the model weights and the gradient of the output with respect to the input. Therefore, the notion of robustness in regression differs from that in classification. In this setting, robustness is defined by Definition 1. In summary, it states that for each output variable, the user can define an acceptable region around the model output ($\textbf{y}_i$) for the input sample $\textbf{x}$ using a chosen measure of dissimilarity ($diss_y(.,.)$) and a corresponding radius ($\epsilon{y}_i$). If the output variability exceeds the defined region, the model is considered non-robust.

**Line 118: What is the "accepted region"?**

Based on Definition 1, the accepted region for the $i^{th}$ output variable, according to the user's level of tolerance, is defined by ${z \mid diss_y(z,\textbf{y}_i) \leq \epsilon{y_i}}$. This region represents a neighborhood around the observed output $\textbf{y}_i$, within which the user is satisfied if the perturbed input data generates such outputs. This explanation has been added immediately after Definition 1 to reduce confusion.

---

### NeurIPS.cc/2024/Conference/Submission10280/Authors — 2024-08-05T09:08:28.084000+00:00

**rebuttal:**

The authors thank the reviewers for their feedback and constructive comments. Please find visualisation of the probabilistic certicates vs $\alpha$ in the attached PDF (Reply to reviewer wW8d).

---

## Official Comments (multi-round discussion)

### NeurIPS.cc/2024/Conference/Submission10280/Authors — 2024-08-05T10:34:56.132000+00:00

**comment:**

**Line 118: So does Proposition 1 not apply to $\ell_1$ threats?**

As described in Proposition 1 and its proof sketch, this result is valid only for $p\geq 2$ which excludes $\ell_1$ threats. However, other inequalities can be used to relate $\ell_1$ to the $\ell_2$ norm which might result in a different form of certificate radii which is not within our interest in this study.


**Figure 1: I don't find this figure...**

This figure visualizes the general case of certification for regression models, where outputs are allowed to vary within a non-convex region around the output prediction for a given sample $\textbf{x}$. The outputs can be jointly analyzed within smaller groups, denoted by indices $1:k$ and $m:t$. However, the results provided in this manuscript address a particular case where outputs are examined separately, and their accepted regions are assumed to be convex. Throughout the paper, output accepted regions are assumed to be convex, though the general problem of certification for regression models may involve non-convex output vicinities (less likely) that can be defined by the user depending on the applications. The figure caption has been changed to *General schematic of how $\alpha$-trimming can be applied to the base regressor with $\ell_2$-norm ball (can be $\ell_p$ norm in this paper and can be any neighboring function in general) defined for input vicinity and any form of convex (in this paper) or nonconvex (in general) set for the output vicinity. Furthermore, outputs can be examined separately (in this paper) or jointly with other outputs (in the general case as denoted by $\textbf{y}_{m:t}$), etc.* to mitigate any confusion.


**Line 150: "...the following equality holds..." I think you mean inequality.**

Yes, thanks for mentioning this typo. It has been fixed in the revised manuscript.

**Line 151: What is q in (9)? Is this allowed to be any real number in [0,1]?**

The parameter $q$ is a real number between [0,1] and serves as the lower bound on the probability of observing a valid output in the base regression model. The range of this parameter has been added to the statement.

**Line 157: Is it ever possible for the change from q to $I_q(n-[\alpha n],n+[\alpha n])$ to be a decrease?**

The authors assume the reviewer means changing from $q$ to $I_q(n-[\alpha n],[\alpha n]+1)$ as stated in Theorem 2. This is an excellent question, and Proposition 2 was stated to address the same question. Please note that we are dealing with an unbounded scenario, and with probability $1−q$, some outputs can exceed the output vicinity around the observed $\textbf{y}_i$. In the worst-case scenario, which is always considered in robust certification, all these off the range outputs could be at infinity, and the $\alpha$-trimming filter might not be able to remove all these outliers. In such cases, the average of the remaining points would be invalid. Therefore, it is crucial to find the minimum rate of filtering ($\alpha^+$) to ensure this probability improves, as described in Proposition 2.

**Theorem 2: One of the powers of randomized smoothing ...**

Thank you for this insightful question. The authors believe that the performance of the base classifier always impacts the overall performance of the smoothed classifier, irrespective of whether the setting is classification or regression. In classification tasks, this strong relationship is reflected in the gap between $ \underline{p_A}$ and $ \overline{p_B}$. If a base classifier performs poorly under input perturbations, this gap will shrink, diminishing the effectiveness of the final certification. In classification settings, there is only one other parameter ($\sigma$) that can potentially compensate for this gap. 
In regression settings, a similar relationship applies: better performance in the base regression model results in a better value for $q$. However, as demonstrated in Theorem 3, the final performance is also influenced by $\sigma$, $n$ and importantly $\alpha$. Using an appropriate value for $\alpha$ can significantly enhance the certification, as illustrated in the examples from Line 179 to Line 189, even when the base regression model performs poorly.

**Algorithm 1, Line 5: What does it mean...?**

The correctness here (similar to the response to the above questions) refers to the fact that the output variable is within the defined accepted region. The term “valid” might better reflect this fact and “correct” has been changed to “valid” in the revised manuscript. Additionally, the probability value should be changed from $ \underline{p_{A_i}}$ to $\textit{{I}}_{p_Ai}(n-[\alpha n],[\alpha n]+1)$,  because no attack was involved yet. Then further in Line 6, we estimate the radius for the perturbation of input data $\textbf{x}$ that generates acceptable results with probability at least P.

**Line 249/Section 5: I suggest moving...**

This suggestion will be taken into account for the camera-ready version of the paper.

---

### NeurIPS.cc/2024/Conference/Submission10280/Reviewer_wW8d — 2024-08-09T03:30:24.601000+00:00

**title:**

Response to the author

**comment:**

Thank you for your detailed response. My concerns are mostly addressed. After carefully reviewing the comments from the other reviewers, I keep my original score as borderline accept.

---

### NeurIPS.cc/2024/Conference/Submission10280/Reviewer_pBXb — 2024-08-09T19:44:32.983000+00:00

**comment:**

**Unbounded quantities**:

" It was shown in [17] that as the difference between these bounds increases, the probabilistic certificate becomes impractical and approaches zero." 

No, this was actually not discussed at all in section 3.2. Neither was "discount factors" (and I'm not sure what this means). I think you should add such a discussion to this section to put your paper in context.

** Definition of terms**
This is not a standard use of the word "bag". You should either define it or re-write this section.

As for the "accepted region"--- please make it clear in that sentence that you are defining a new term, that will be used throughout the paper. The current presentation of this term is rather confusing


**$\alpha$-filtering in other contexts**: 

Could you describe such other criteria? I think it would be a nice way to connect your paper with existing literature

**exposition:** Based on this exchange, I think you should work on improving the quality of the exposition of your paper. Are there further changes you plan to make to the exposition?

---

### NeurIPS.cc/2024/Conference/Submission10280/Reviewer_ZCs7 — 2024-08-10T16:28:55.050000+00:00

**comment:**

**Line 68: You mention the prior works... / Line 249/Section 5: I suggest moving...**

"This suggestion will be taken into account for the camera-ready version of the paper." Thanks.

**In the introduction, you use the acronym...**

Thanks for fixing this.

**Lines 93 and 116: "...is the lower bound on...**

If "accepting prediction in the $i$th output variable" means that "$\mathbf{f}\_{\theta}(\mathbf{x}+\mathbf{e})_i \in \mathbf{N}\_y(\mathbf{y}\_i, \epsilon\_{y\_i})$", then you should explicitly and clearly state/define this (before using the language). Otherwise, it may not be immediately clear to the reader that this is what you mean.

**Line 118: What is the "accepted region"?**

"This explanation has been added immediately after Definition 1 to reduce confusion." Thanks.

---

### NeurIPS.cc/2024/Conference/Submission10280/Reviewer_ZCs7 — 2024-08-10T16:58:05.846000+00:00

**comment:**

**Line 118: So does Proposition 1 not apply to $\ell\_1$ threats?**

Your choice to set $r=2$ in the proof of Proposition 1, which leads to the requirement that $p\ge 2$, appears to be completely arbitrary to me. Why make this restriction? If someone wants to use your result in the case of $p=1$, then it appears as though they can't, even though, according to your proof, they can by choosing $r=1$, $p=1$, and $q=\infty$. I suggest stating and proving the result (Proposition 1) in its most generally applicable form.

**Figure 1: I don't find this figure...**

Your new caption still does not address my question " Finally, what is the difference between the outputs and regions ($y\_{1:k}$, $y\_{m:t}$, and their green regions) within the red dashed box, and those same outputs and regions outside the red dashed box?" The interpretation of the figure is still unclear.

**Line 150: "...the following equality holds..." I think you mean inequality.**

Thanks for fixing this.

**Line 151: What is q in (9)? Is this allowed to be any real number in [0,1]?**

"The range of this parameter has been added to the statement." Thanks.

**Line 157: Is it ever possible for the change from $q$ to $I\_q(n-\alpha[n],n+\alpha[n])$ to be a decrease?**

I see that Proposition 2 gives a sufficient condition for an increase. Based on your response and discussion after Theorem 2, it seems that it is possible for a decrease to occur, in general. You should explicitly mention this as a possible limitation (in such easily understandable terms), as it essentially boils down to your $\alpha$-trimming procedure failing to increase the robustness of the base model in such cases. It makes the most sense to me to assert this limitation (again, in simple language such as "failure to robustify") at the end of the discussion following Theorem 2, and then to move into your sufficient conditions (for "successful robustification") of Proposition 2 thereafter.

**Theorem 2: One of the powers of randomized smoothing...**

Thanks for your response; it gives nice comparisons between the underlying parameters of smoothing in classification versus regression, and how they relate to robustification. I suggest including such an explanation in your manuscript somewhere around Theorem 3.

**Algorithm 1, Line 5: What does it mean...?**

"The term *valid* might better reflect this fact and *correct* has been changed to *valid* in the revised manuscript." If so, then please be sure to clearly define what you mean by "valid" (i.e., to be in the "accepted region," after you clearly define that).

**Line 249/Section 5: I suggest moving...**

"This suggestion will be taken into account for the camera-ready version of the paper." Thanks.

---

### NeurIPS.cc/2024/Conference/Submission10280/Reviewer_ZCs7 — 2024-08-10T16:59:45.687000+00:00

**comment:**

I have read and responded to the author rebuttal. I have decided to increase my score by 1 point.

---

### NeurIPS.cc/2024/Conference/Submission10280/Authors — 2024-08-11T07:07:17.356000+00:00

**comment:**

We thank the reviewer for the additional feedback. We hope this discussion may address sufficient concerns to increase the score towards acceptance.

**No, this was actually not discussed at all in section 3.2. Neither was "discount factors" (and I'm not sure what this means). I think you should add such a discussion to this section to put your paper in context.**

In Section 3.2 as a summary of our previous reply, it was mentioned that *even a single adversarial point (in unbounded scenarios) can entirely shift the result of averaging into the invalid zone (from the user's perspective). This behavior is known as the zero breakdown point of averaging in robust statistics.* It was also noted that *it was shown for some cases where these considered bounds in the output are loose, the certificate bound in the input becomes worse than the base regression model.* We therefore believe the limitations of simple averaging smoothing have already been thoroughly discussed. However, if the reviewer still believes the discussion is deficient in some way, we would appreciate a pointer to parts requiring clarification.

The “Discount factor” parameter was introduced in [17] (Section 4.3) to propose an approach for certifying bounded models in a finite sample regime. They used this positive parameter to apply a discount, which made the accepted region wider than that of the base regression model, aiming for better analytical results in worst-case scenarios. However, in our paper, we did not use any discount factor as described in [17]. We only mentioned it as a limitation of the approach in [17] when comparing our results in the camera re-localization task (Figure 5).
For the sake of completeness, the discount factor will be explained in the camera-ready version.

**This is not a standard use of the word "bag". You should either define it or re-write this section. As for the "accepted region"--- please make it clear in that sentence that you are defining a new term, that will be used throughout the paper. The current presentation of this term is rather confusing.**

As the reviewer suggested, we will provide a precise definition of the term "bag" in the appendix where it is used. Concerning the term "accepted region," we appreciate the reviewer's suggestion and will clarify that this term will be used throughout the paper to refer to the neighbourhood defined in the output.

**$\alpha$-filtering in other contexts: Could you describe such other criteria? I think it would be a nice way to connect your paper with existing literature**

One of the primary uses of the $\alpha$-trimming filter is in data preprocessing and outlier rejection within signal processing, prior to parameter estimation. The adjustment of $\alpha$ in this context typically relies on prior knowledge about the proportion of data points that deviate from the nominal distribution, such as a Gaussian distribution. While this prior knowledge may not always be accurate, it has been widely utilized in signal processing to reduce the sensitivity of estimators. Another method for tuning $\alpha$ in parameter estimation is to consider efficiency at the nominal density. For instance, if no outliers are present in the dataset, how should $\alpha$ be set to achieve an estimation that closely matches the performance of its maximum likelihood counterpart?

The authors appreciate the reviewer's suggestion and are eager to include a brief paragraph discussing the application of the $\alpha$-trimming approach in the literature, further supporting its selection in this new context.

**exposition: Based on this exchange, I think you should work on improving the quality of the exposition of your paper. Are there further changes you plan to make to the exposition?**

The authors are planning to only add/change the parts that are communicated to the reviewers during the rebuttal and discussion period. This includes parts related to the definition of terms “bag”, “discount factor” and “accepted region”, a short explanation for Figure 5 (see our rebuttal), application of $\alpha$-trimming in the literature, referring to the differences with the other works in the literature at the end of section 2, caption in Figure 2, etc. The authors are open to any other suggestions which the reviewer may believe would enhance the exposition of the work. If, however, the reviewer believes that there aren’t specific further additions, then we would appreciate the opportunity to publish the paper.

---

### NeurIPS.cc/2024/Conference/Submission10280/Authors — 2024-08-11T07:10:10.699000+00:00

**comment:**

**If "accepting prediction in the ith output variable" means that $\textbf{f}_\theta(x+e)_i \in \textbf{N}_y(y_i,\epsilon_i)$, then you should explicitly and clearly state/define this (before using the language). Otherwise, it may not be immediately clear to the reader that this is what you mean.**

We agree. As requested by the reviewers, the definition of the accepted region is now clearly stated in the revised manuscript immediately following Definition 1.

**Your choice to set $r=2$, in the proof of Proposition 1, which leads to the requirement that $p\geq 2$, appears to be completely arbitrary to me. Why make this restriction? If someone wants to use your result in the case of $p=1$, then it appears as though they can't, even though, according to your proof, they can by choosing $r=1$, $p=1$, and $q=\infty$. I suggest stating and proving the result (Proposition 1) in its most generally applicable form.**

We appreciate the reviewer's suggestions to enhance the validity of the results for other norms. As the reviewer correctly noted, by setting $r=1$, we can relate the $\ell_1$ norm to the $\ell_p$ norm ($p \geq 1$). However, it is important to note that one of these norms must be the $\ell_2$ norm in order to apply Theorem 1, which provides an upper bound on the input perturbation. Therefore, we must set $r=2$, and the constraint $p \geq 2$ directly follows from this choice.

**Your new caption still does not address my question " Finally, what is the difference between the outputs and regions ($y_{1:k}$,$y_{m:t}$, and their green regions) within the red dashed box, and those same outputs and regions outside the red dashed box?” The interpretation of the figure is still unclear.**

Apologies if this part of the question was not previously addressed. As noted in the paper, we apply the $\alpha$-trim smoothing function $\textbf{g}_\alpha(\textbf{x})$ as a wrapper around the base regression model, using the same definition of the vicinity sets in both input and output, as illustrated in Figure 1. Consequently, everything within the red dashed box is related to base regression certification and the results provided in Theorem 1 and Proposition 1. The corresponding output regions outside the red dashed box represent the certification analysis for the smoothed function and the applicability of the improved certification results shown in Theorems 2 and 3, and Propositions 2, with the accepted regions remaining consistent with those in the base regression model. This additional explanation will also be included in the camera-ready version.

**I see that Proposition 2 gives a sufficient condition for an increase. Based on your response and discussion after Theorem 2, it seems that it is possible for a decrease to occur, in general. You should explicitly mention this as a possible limitation (in such easily understandable terms), as it essentially boils down to your $\alpha-$trimming procedure failing to increase the robustness of the base model in such cases. It makes the most sense to me to assert this limitation (again, in simple language such as "failure to robustify") at the end of the discussion following Theorem 2, and then to move into your sufficient conditions (for "successful robustification") of Proposition 2 thereafter.**

This is an excellent suggestion that underscores the importance of the sufficient condition derived in Proposition 2. The authors are happy to add such an explanation in simple terms right before Proposition 2 in the camera-ready version.

**Thanks for your response; it gives nice comparisons between the underlying parameters of smoothing in classification versus regression, and how they relate to robustification. I suggest including such an explanation in your manuscript somewhere around Theorem 3.**

Thank you for your positive feedback on our response. As suggested, we will include this note in the camera-ready version of the paper.

**"The term valid might better reflect this fact and correct has been changed to valid in the revised manuscript." If so, then please be sure to clearly define what you mean by "valid" (i.e., to be in the "accepted region," after you clearly define that).**

Certainly, both the accepted region and the validity of the outputs will be clearly defined in the camera-ready version, as suggested by the reviewer.

**I have read and responded to the author rebuttal. I have decided to increase my score by 1 point.**

Thank you for taking the time to read our responses and for raising the score to a borderline reject. We have carefully addressed the other questions raised by the reviewer, and we hope that these new responses, along with the improvements made to the paper based on the reviewers' constructive comments, will result in a higher score. This, combined with the evaluations from the other reviewers, could lead to the publication of this new line of research in certifying machine learning models for regression tasks.

---

### NeurIPS.cc/2024/Conference/Submission10280/Authors — 2024-08-11T08:47:43.486000+00:00

**comment:**

We thank Reviewer wW8d for acknowledging receipt of the author rebuttal, and for acknowledging that their *“concerns are mostly addressed”*. If the reviewer might point us to which concerns (if any) remain unaddressed, we would appreciate this during the discussion period, as it would help improve the paper and provide us the valuable opportunity to work with the reviewer.

The reviewer has stated *” After carefully reviewing the comments from the other reviewers, I keep my original score as borderline accept”*. Approximately 1.5 days later, one of the other reviewers increased their scores. Moreover, there has been rebuttals and discussion, beyond the other reviews. We would therefore respectfully ask if the reviewer has any further updates to their advice or scores.

With thanks, The authors

---

### NeurIPS.cc/2024/Conference/Submission10280/Reviewer_pBXb — 2024-08-12T17:06:55.296000+00:00

**comment:**

**Exposition** 

Based on this exchange, it seems that I misunderstood many essential pieces of your paper due to the exposition. Unfortunately, I don't have the time to carefully read your submission again to offer concrete pieces of feedback. 

I think the content of this paper is good and meets the bar for publication. 

I'm going to keep my score and leave the issue to the meta reviewers.

---

### NeurIPS.cc/2024/Conference/Submission10280/Reviewer_ZCs7 — 2024-08-12T19:07:43.652000+00:00

**comment:**

I thank the authors for responding to my remaining concerns. In light of the promised revisions, I have increased my score by 1 more point. Overall, I think that this is still a borderline paper, and therefore I defer to the meta reviewers.

---

## Decision

### NeurIPS.cc/2024/Conference/Program_Chairs — 2024-09-25T15:19:12.134000+00:00

**title:**

Paper Decision

**comment:**

This paper extends existing results on certified robustness of regression models.
By applying $alpha$-filtering (a tool from robust statistics), the authors are able to provide certificates for models with unbounded outputs, something which no prior work provides.
This is a meaningful contribution, which reviewers agree is worthy of publication.

Reviewers also raised a number of concerns about the submission, and I also asked them to discuss the practical relevance and significance of the contribution.
Reviewing the discussion, I believe the only remaining concern which might prevent publication of this work is the quality of the presentation, which all 3 reviewers critiqued.
In particular, several terms were not defined in the initial submission.
After looking at the paper myself, I believe the presentation is not bad enough to prevent publication, and as the authors have promised to address all of the specific issues of clarity raised by the reviewers, I am pleased to recommend acceptance.

I additionally ask the authors to revisit Figure 1, as I agree with Reviewer ZCs7 that the current version is not very enlightening, and I found the caption was insufficiently detailed to explain what the take-away is meant to be.  I also believe the work would benefit from further attention to presentation, so, contra the author's stated intentions, I recommend they seek and incorporate further feedback on how to improve clarity, as I believe it could significantly increase the impact of their work.

**decision:**

Accept (poster)

---
