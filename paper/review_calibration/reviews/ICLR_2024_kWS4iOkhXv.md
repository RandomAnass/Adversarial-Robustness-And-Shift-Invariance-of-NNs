# Scalable Lipschitz Estimation for CNNs

- **Label:** `ICLR_2024_kWS4iOkhXv`
- **Venue:** ICLR 2024  (Submitted to ICLR 2024)
- **Forum:** https://openreview.net/forum?id=kWS4iOkhXv
> _Fetched 2026-06-26T23:54:41.527543+00:00_

## Thread summary
- decision: 1
- meta_review: 1
- official_comment: 11
- official_review: 4

## Official Reviews

### ICLR.cc/2024/Conference/Submission5098/Reviewer_sG95 — 2023-10-30T14:47:25.787000+00:00

**summary:**

The paper proposes a new method called dynamic convolutional partitioning (DCP) to improve the scalability of estimating Lipschitz constants for convolutional neural networks (CNNs). Estimating the Lipschitz constant is useful for evaluating the robustness and generalizability of neural networks. Existing methods are either not tight enough or do not scale well to large CNNs. The core idea of DCP is to decompose a large CNN into smaller subnetworks using a joint layer and width-wise partition. The Lipschitz constant of the original network can then be bounded by the Lipschitz constants of the smaller networks. Experiments demonstrate improved scalability over baseline methods. Key factors affecting the accuracy vs scalability tradeoff are also analyzed, including the number and order of subnetworks and the choice of partition sizes.

**strengths:**

Lipschitz estimation for neural networks is an important problem for robustness and generalization. Given that current approaches for estimating the Lipschitz constant do not scale, investigating scalable methods is an important research direction.

**weaknesses:**

The paper has several weaknesses:

- I think the title "Scalable Lipschitz Estimation for CNNs" is overclaiming, while the proposed approach is more scalable than previous ones, the approach hardly scales to medium size convolutional neural networks (CIFAR10, TinyImagenet, ImageNet). Furthermore, to improve the scalability, the authors rely on the bounds of Eq. (3) and Eq. (4), which are known to be very loose. 
- The authors seem to have missed an important related work [1], which proposes a Lipschitz estimation for the CNN that is independent of the image size and only dependent on the channel size. 
- The experiments are performed
	- on random weights and not on trained networks: "All network weights were generated according to the Kaiming distribution".
	- on very small input sizes, more than twice smaller than MNIST: "[...] by constructing a convolutional block with an input size of 10 × 10 × 1 [...]". I understand that the authors want to evaluate their approach with different channel sizes: "We increased the width by varying c from 1 to 14", but an image size of 10 × 10 × 1 is too small to demonstrate scalability. 

[1] Gramlich et al. Convolutional neural networks as 2-D systems

Other comment:
I have reviewed the paper on a printed version and all the figures are unreadable, the authors should definitely increase the font of the figures.

**questions:**

Can the authors perform experiments with trained MNIST networks and compare against the approach proposed in [1]?

**soundness:**

2 fair

**presentation:**

3 good

**contribution:**

2 fair

**rating:**

5: marginally below the acceptance threshold

**confidence:**

3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.

**flag_for_ethics_review:**

- No ethics review needed.

**details_of_ethics_concerns:**

NA

**code_of_conduct:**

Yes

---

### ICLR.cc/2024/Conference/Submission5098/Reviewer_qywJ — 2023-10-30T15:59:44.637000+00:00

**summary:**

The author study the upper-bound of Lispchitz constant of CNNs. They refine LipSDP by dynamically splitting the layers of the network into smaller blocks that could be handled separately and then gathered together in order to give an upper-bound of the Lispchitz constant of the network. This method is called DCP-LipDSP. Finally, an experimental benchmark highlights some advantages of their approaches.

**strengths:**

The paper proposes a method called DCP-LipDSP that exploits the sparcity in the convolution matrices in order to provide faster upper-bounds for Lipschitz constant of convolutional blocks.

**weaknesses:**

The link given in the paper to access the code does not work for me.

Section 4 is difficult to follow and, in my opinion, lacks many details. See some comments in the Questions below.

The experimental section is weak. In my opinion, it lacks of experiments using trained network for which the behaviour is expected to be really different from randomly generated ones, in particular for its Lipschitz constant. In order to select $N_{max}$, multiple calls to LipSDP are made that are not considered in the time benchmark, this should be discussed.  
Moreover it is not clear if LipSDP profits from the 20-cores CPU machine and hence if the experimental benchmark is fair.

Bibliography: many references are incomplete: please refer to peer-reviewed articles instead of arXiv when possible.

**questions:**

**Section 3**

Lemma 3.2 is only valid for $R^m$ together with the $L^2$ norm, this should be stated within the theorem assumptions.

**Section 4**

4.1.1 it is not clear what are precisely the functions $f_{i, j}$, and how to practically construct them.  
It seems that their domain should not be disjoint as it is however stated in Eq. (10). If $ \ell \times k > m_0, n_0$ where $k$ is the size of the kernel of these convolutions, then all $f_{i,j}$ should have domain $X^0$.  
It seems that this inaccuracy is repeated in the entire paper (e.g. in 4.1.2 Eq. (14)). However this idea may be exploited in order to better constraint the search space for the partitions.

I think a discussion should precise these concerns. And what is the impact of the potential overlap between the layers on the computation time.

**Experiments**

All neural networks considered have weights initialized with the Kaiming distribution, that aim at having gradients of magnitude O(1). We are in a regime that is most likely very different from a trained neural network. Overall I think the paper would be seriously improved if the author were to reproduce the experiments of Lip-SDP and benchmark them with the proposed DCP approach.

Figure 2 (c) provides an interesting illustration of the tradeoff between computation time and the given upper-bound. This behaviour is intuitively expected from Eq (18) and I am surprised that a 5-fold time reduction only decrease the upper-bound by 20%. It would be very interesting to see if the proposed approach could tackle much bigger neural networks where vanilla Lip-SDP would fail.  
I wonder if these curves could be derived analytically directly from Eq 18 with the assumptions than the weights follow Kaiming.

The only property of CNNs that this paper exploits is that their matrix representation may be sparse under appropriate assumptions. Can this work be generalized to a broader class of neural networks?

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

**code_of_conduct:**

Yes

---

### ICLR.cc/2024/Conference/Submission5098/Reviewer_szVD — 2023-11-01T00:15:28.023000+00:00

**summary:**

This paper addresses the problem of estimating the Lipschitz constant of deep neural networks, particularly focusing on convolutional neural networks (CNNs). While existing methods for estimating the Lipschitz constant can be accurate, they lack scalability especially when applied to CNNs. To address this limitation, the paper introduces a novel method to accelerate Lipschitz constant estimation for CNNs. The core idea involves breaking down large convolutional blocks into smaller ones using a joint layer and width-wise partition. The paper proves an upper-bound relationship between the Lipschitz constants of the larger and smaller blocks and demonstrates improved scalability and comparable accuracy through experimental results.

The paper's introduced DCP (dynamic convolutional partition) method can be useful for scaling Lipschitz estimation in deep and wide CNNs. The method is framework-invariant and can be used with several different estimation methods.

**strengths:**

The strengths of the paper are as follows:

1. Novel partition method: The paper introduces a novel method called dynamic convolutional partition (DCP) designed to address the scalability issue in Lipschitz constant estimation for deep and wide convolutional neural networks (CNNs). This method involves dividing large convolutional blocks into smaller ones using a joint layer and width-wise partition. This method also provides a practical solution to a known limitation in Lipschitz estimation.

2. Theoretical Foundation: The paper establishes a theoretical foundation for its method by proving that the Lipschitz constant of a large convolutional block can be upper-bounded by the Lipschitz constants of the smaller blocks. 

3. Empirical Validation: Through several experiments, the paper demonstrates that the DCP method offers enhanced scalability and achieves accuracy comparable to or better than existing baseline methods. This empirical validation showcases the practical utility of the proposed approach.

**weaknesses:**

The method, while novel is not scalable to modern large convolutional neural networks. However, the improvements on top of the existing methods are impressive. 

The paper is missing references to important works on estimating the Lipschitz constants of convolutional layers:

1. Singular Values of Convolution layers
2. Fantastic Four: Differentiable and Efficient Bounds on Singular Values of Convolution Layers

**questions:**

I believe that a comparison between the bounds computed by the proposed methods and some existing provably 1 Lipschitz neural networks whose Lipschitz constant is well known (such as Lipschitz Convnets, see references below) can be useful in evaluating the effectiveness of the proposed approach.

1. Sorting Out Lipschitz Function Approximation
2. Skew Orthogonal Convolutions
3. Orthogonalizing Convolutional Layers with the Cayley Transform

**soundness:**

3 good

**presentation:**

3 good

**contribution:**

2 fair

**rating:**

6: marginally above the acceptance threshold

**confidence:**

4: You are confident in your assessment, but not absolutely certain. It is unlikely, but not impossible, that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work.

**flag_for_ethics_review:**

- No ethics review needed.

**code_of_conduct:**

Yes

---

### ICLR.cc/2024/Conference/Submission5098/Reviewer_G8PH — 2023-11-06T15:36:18.729000+00:00

**summary:**

This paper studies how to scale up the Lipschitz constant estimation of CNNs using SDPs and a decomposition technique. The authors prove an upper-bound on the Lipschitz constant of the original CNN in terms of the Lipschitz constants of some smaller blocks. Some experiments are presented to support the theoretical developments.

**strengths:**

1. The topic is quite interesting. Scalability of LipSDP is an important issue.

2. In comparison to using interior point methods for the original LipSDP on CNN, the proposed method is more scalable.

3. The authors carefully discuss how to do the partition to make their method more efficient.

**weaknesses:**

1. The experiments are still on toy examples. Is the proposed approach working for larger networks trained on CIFAR10/100? At least, the proposed method should be better than the matrix product bound for CIFAR?

2. The authors missed several important related work on LipSDP.  Comparisons and discussions of the following works are missing.

[Gramlich2023] Convolutional neural networks as 2-D systems (arXiv)

The above paper extends LipSDP for 2D convolutional networks. Is the proposed approach more scalable than the above paper?

[Araujo2023] A unified algebraic perspective on Lipschitz neural networks (ICLR)

Theorem 4 of the above paper extends LipSDP for residual networks. Is the proposed approach directly applicable to the residual network considered in the above paper? Some remarks are needed.

[Revay2020] Lipschitz bounded equilibrium networks (arXiv)

Theorem 2 of the above paper extends LipSDP for equilibrium networks. Is the proposed approach directly applicable to the equilibrium network considered in the above paper? Some remarks are needed.

**questions:**

1.  Is the proposed approach working for larger networks trained on CIFAR10/100 and can at least outperform the matrix norm product for those tasks?

2. [Gramlich2023] Convolutional neural networks as 2-D systems (arXiv)

The above paper extends LipSDP for 2D convolutional networks. Is the proposed approach more scalable than the above paper?

3. [Araujo2023] A unified algebraic perspective on Lipschitz neural networks (ICLR)

Theorem 4 of the above paper extends LipSDP for residual networks. Is the proposed approach directly applicable to the residual network considered in the above paper? Some remarks are needed.

4. [Revay2020] Lipschitz bounded equilibrium networks (arXiv)

Theorem 2 of the above paper extends LipSDP for equilibrium networks. Is the proposed approach directly applicable to the equilibrium network considered in the above paper? Some remarks are needed.

**soundness:**

3 good

**presentation:**

3 good

**contribution:**

2 fair

**rating:**

6: marginally above the acceptance threshold

**confidence:**

3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.

**flag_for_ethics_review:**

- No ethics review needed.

**code_of_conduct:**

Yes

---

## Official Comments (multi-round discussion)

### ICLR.cc/2024/Conference/Submission5098/Authors — 2023-11-21T20:32:21.578000+00:00

**comment:**

We thank the reviewer for their appreciation of the proposed method and their constructive comments on improving experiments, for which we have added a series of new experiments testing for larger networks trained on MNIST and CIFAR10 images (see our revised Section 5.1). Please see our detailed response below.
1. **Weakness 1 and Question 1**: We have compared the proposed approach with the matrix product bound (referred to as naive estimation in our paper) for two larger networks (CNN1 and CNN2). CNN1 has size: $28\times 28\times 1 \rightarrow 24\times 24\times 1 \rightarrow 20\times 20\times 1 \rightarrow 50 \rightarrow 10$, trained on MNIST, and CNN2 has size: $32 \times 32 \times 3 \rightarrow 30 \times 30 \times 5 \rightarrow  28 \times 28 \times 5 \rightarrow  26 \times 26 \times 5 \rightarrow  24 \times 24 \times 5 \rightarrow  22 \times 22 \times 5 \rightarrow 50 \rightarrow 100 \rightarrow 100$, trained on CIFAR10. Our approach  outperforms the matrix product bound in both cases. Please see Trained Networks and Table 1 in our revised Section 5.1 for further details.   
 2. **Weakness 2, [Gramlich2023](https://arxiv.org/pdf/2303.03042.pdf) and Question 2**: We have conducted the CNN1 experiment trained on MNIST images, aiming to reproduce Example 3 in [Gramlich2023](https://arxiv.org/pdf/2303.03042.pdf) as closely as possible, given the details provided. Our CNN1 used an identical CNN setting to Example 3 apart from padding. Their CNN size is $28\times 28\times 1 \rightarrow 24\times 24\times 5 \rightarrow 16\times 16\times 5 \rightarrow 50 \rightarrow 10$, while our CNN1 has a slightly larger size $20\times 20\times 5$ in the second convolutional layer. To the best of our knowledge, the code for [Gramlich2023](https://arxiv.org/pdf/2303.03042.pdf) is not publicly available, and it is challenging for us to implement their approach from scratch within the time allowed by the discussion period. Moreover, they do not report their computing environment, so we cannot compare results directly. However, we  summarise the results for reference; for CNN1, the matrix norm product bound computed a Lipschitz estimation of 91.31, and our method computed an estimation of $65.84$ in 
 $864$ seconds. [Gramlich2023](https://arxiv.org/pdf/2303.03042.pdf) reported an estimation of $18.9$ computed in $1550$ seconds. 
  3. **Weakness 2 of [Araujo2023](https://openreview.net/pdf?id=k71IGLC8cfc), [Revay2020](https://arxiv.org/pdf/2010.01732.pdf) and Questions 3, 4**: As suggested, we have added a discussion of potential applications of the proposed approach to other types of neural networks, including the discussion based on the two papers [Araujo2023](https://openreview.net/pdf?id=k71IGLC8cfc) and [Revay2020](https://arxiv.org/pdf/2010.01732.pdf). This can be found in the revised version of Section 6.

---

### ICLR.cc/2024/Conference/Submission5098/Authors — 2023-11-21T20:39:33.604000+00:00

**comment:**

We appreciate the reviewer's acknowledgement of the novelty, theoretical foundation and empirical validation of our work. We agree that we should strengthen our experiments, e.g. testing with larger networks, for which we have added new experiments. Please see our response below.

1.**Weakness**: We have added new experiments testing against larger neural networks trained on MNIST and CIFAR10 images. Please see our revised Section 5.1 for further details. We have also added the two suggested works [Sedghi](https://openreview.net/pdf?id=rJevYoA9Fm)  and [Singla2021a](https://openreview.net/pdf?id=JCRblSgs34Z) to Section 2, in the revised draft.

2.**Questions**: As suggested, we have conducted additional experiments using provably 1-Lipschitz networks as described in [Anil2019](https://proceedings.mlr.press/v97/anil19a/anil19a.pdf) and [Singla2021b](https://proceedings.mlr.press/v139/singla21a/singla21a.pdf). Specifically, we considered the ReLU activation function, which is 1-Lipschitz and orthogonalised the weight matrices. Please see Appendix A.5.2 of the revised supplementary material for further details.

---

### ICLR.cc/2024/Conference/Submission5098/Authors — 2023-11-21T20:51:25.902000+00:00

**comment:**

We thank the reviewer for the constructive comments. In the revised draft, we have added new experiments, clarified issues about Section 4 and amended the references. Please see our response below.

1.**Code Link (Weakness)**: The link works when clicked on as opposed to copy and pasting. We apologise for not noticing this earlier and have fixed it in the revised draft.

2.**Bigger and Trained Networks (Weakness, Question on Experiments)**: To strengthen the experiments, we have tested against larger CNNs trained on MNIST and CIFAR10 images where Lip-SDP would fail, and compared our method with the naive estimation. Please see our revised Section 5.1 for details. When designing the experiments, our focus was on assessing the scalability to wide layers resulting from flattening the convolutional operators, as opposed to LipSDP [Fazlyab2019](https://proceedings.neurips.cc/paper_files/paper/2019/file/95e1533eb1b20a97777749fb94fdb944-Paper.pdf), who  focused on fully-connected layers and scaled to deeper networks through layer-wise cutting. As our approach also incorporates layer-wise cutting, experiment emphasis was placed on scalability to wider layers under the SDP-based framework.  For instance, [Fazlyab2019](https://proceedings.neurips.cc/paper_files/paper/2019/file/95e1533eb1b20a97777749fb94fdb944-Paper.pdf) experimented with a  maximum network width of $100$ neurons, while we experimented with maximum widths ranging from $3600$ to $4500$ neurons. 

3.**$N_{\max}$ Estimation (Weakness)**:  To select $N_{\max}$ requires multiple calls of SDP, which can be time consuming as the problem size increases. However, this estimation is only needed once for each computing requirement. In our implementation, we adopted a faster prediction-based approach by solving several moderate sized SDP problems, and predicting $N_{\max}$ from these via extrapolation. We provide further details of this in Section A.5.1 of the revised supplementary material. 
 
4.**LipSDP/20-core CPU (Weakness)**: Both LipSDP and our method DCP-LipSDP have access to the 20 cores, so the benchmark is fair. We have clarified this at the start of revised version of Section 5.

5.**Bibliography (Weakness)**: We have fixed this in the revised draft, replacing all the arXiv papers with the official venues where applicable. 
  
6.**Section 3 (Question)**: We have stated this in the revised Lemma 3.2. 

7.**Section 4 (Weakness and Question)**: We have clarified how to construct $f_{ij}$ and that the domains $X_{ij}^{0}$ are not disjoint in general, in Section 4.1.1 of the revised manuscript. Regarding the impact of the potential overlap between the layers, if we understand the reviewer correctly, then we remark that the layer-wise cutting is applied in such a way that the output layer of one subnetwork is the input layer of the proceeding one. Furthermore, while the receptive fields of the smaller convolutional blocks overlap in general, the corresponding weights do not. This independence between convolutional blocks is a key component of our method as it permits the computation of the Lipschitz constants in parallel. 

8.**Other Questions on Experiments**:  Regarding to an analytical derivation of the type of curves in Figure 2(c), this is an interesting research question posed by the reviewer and we hope to pursue it rigorously in the future. 

Regarding the generalisation to a broader class of neural networks, the proposed method, which currently exploits the sparsity structure of the CNN weights, can be generalised to certain types of neural networks containing convolutional blocks. In the future, we are interested in researching other strategies that exploit a wider range of network properties, in addition to sparsity. We have added further discussion of this to Section 6.

---

### ICLR.cc/2024/Conference/Submission5098/Area_Chair_ScN8 — 2023-11-21T20:57:06.785000+00:00

**title:**

The benefit of estimating the Lipschitz constant?

**comment:**

I went through the paper and have the following concerns:

(1) The paper mentions the connection to the measurement of the robustness. However, the experiments only focus on the estimation of the Lipschitz constant, and there is no other result on the measurement of the robustness.

(2) As can be seen from the experiment on CIFAR10,  the estimated values are quite large --- at the order of 10^6. If we plugin such values into any kind of robust generalization bound/or certificate, we will get a vacuous bound, considering that CIFAR10 only contains 50k training samples.

(3) The Lipschitz constant only considers the worst case robustness, and therefore cannot accurately reflect the robust generalization performance over the entire population. If we care about the generalization performance, shouldn't we consider other distribution-dependent metric, other than the Lipschiz constant?

---

### ICLR.cc/2024/Conference/Submission5098/Authors — 2023-11-21T21:00:10.083000+00:00

**comment:**

We thank the reviewer for their constructive comments. As suggested, we have added new experiments for larger neural networks and attempted to compare with [Gramlich2023](https://arxiv.org/pdf/2303.03042.pdf). Please see the new results added to Section 5.1 in the revised draft and our response below. We have also increased the font size of the figures. 

1.**Larger Trained Networks (Weakness)**: First of all, we would like to mention that, in our submitted draft, we did experiment with several neural networks with a larger input size than $10 \times 10\times 1$. The largest of which is a 10-layer convolutional block with an input size of $64 \times 64$ and a maximum hidden-layer width of 3600 when flattened, and is used to analyse the behaviour of the proposed DCP approach, resulting in Figure 2(c). Now we have added another experiment testing with an even larger network trained on CIFAR10 images, referred to as CNN2 in the draft. CNN2 has 5 convolutional layers of dimension: $30 \times 30 \times 5, 28 \times 28 \times 5, 26 \times 26 \times 5, 24 \times 24 \times 5$ and $22 \times 22 \times 5$, corresponding to a maximum hidden-layer width of 4500 when flattened. This was followed by 2 fully-connected layers of size 50 and 100 respectively. 
    
2.**Comparison with [[Gramlich2023]](https://arxiv.org/pdf/2303.03042.pdf), MNIST (Question and Weakness)**:
As suggested, we have included [Gramlich2023](https://arxiv.org/pdf/2303.03042.pdf) in related work and attempted to compare with it. Reviewer G8PH suggested the same comparison, and we repeat the same response here:

We conducted the CNN1 experiment trained on MNIST images, hoping to reproduce Example 3 in [Gramlich2023](https://arxiv.org/pdf/2303.03042.pdf) as closely as possible. We used an identical architecture to Example 3 apart from padding. Their CNN size is $28\times 28\times 1 \rightarrow 24\times 24\times 1 \rightarrow 16\times 16\times 1 \rightarrow 50 \rightarrow 10$, while CNN1 has a larger size $20\times 20\times 1$ in the second convolutional layer. To the best of our knowledge, the code for [Gramlich2023](https://arxiv.org/pdf/2303.03042.pdf) is not publicly available, and it is challenging for us to implement their approach from scratch within the time allowed by discussion period. Moreover, they do not report computing environment, so we cannot compare results directly. However, we  summarise the results for reference; For CNN1, the matrix norm product bound computed a Lipschitz estimation of 91.31 , and our method computed an estimation of $65.84$ in 
$864$ seconds. In comparison, [Gramlich2023](https://arxiv.org/pdf/2303.03042.pdf) reported an estimation of $18.9$ computed in $1550$ seconds. 

3.**On Equations (3, 4) (Weakness)**: We would like to point out that Eq. (3) has been used by the LipSDP paper [Fazlyab2019](https://proceedings.neurips.cc/paper_files/paper/2019/file/95e1533eb1b20a97777749fb94fdb944-Paper.pdf) to accelerate Lipschitz estimation for deep, fully-connected neural networks. While our work uses Eqs. (3) and (4) to accelerate deep and wide CNNs. Both their experiments and ours show the obtained estimations are sufficiently good in practice. However, a rigorous analysis of the gaps between the bounds resulting from applying Eqs. (3) and (4) and the exact Lipschitz constant, as well as developing and proving tighter bounds, are interesting future research directions.

---

### ICLR.cc/2024/Conference/Submission5098/Authors — 2023-11-22T00:53:10.741000+00:00

**comment:**

We thank the area chair for their comments. 

1.While the Lipschitz constant is connected to robustness, the focus of our paper is to accelerate an existing estimation framework to CNNs, demonstrated through our experiments in which we also achieve comparable accuracy.  We believe this is an important contribution to the Lipschitz estimation community.

2.Constraining the Lipschitz constant during training has been shown to improve network generalisation. Incorporation of such techniques- such as constraining the naive upper-bound, can provide useful information on model generalisation when trained on datasets such as CIFAR10. Another possible approach to obtain useful generalisation bounds would be to track changes in the Lipschitz constant during training through use of our acceleration method. When an increase above a certain threshold is detected, an appropriate process for decaying the weights can be deployed. 

3.Regarding the generalisation performance, while this is not our exact area of expertise, we agree that a distribution-dependent metric is a good choice. For example, a probabilistic Lipschitz constant could be adapted. In this case, a probability distribution of the local Lipschitz constants can be established, which can be more informative than the global Lipschitz constant in assessing the robust generalisation performance.

---

### ICLR.cc/2024/Conference/Submission5098/Authors — 2023-11-22T09:50:31.994000+00:00

**comment:**

To add to our initial response, which is focused more on the use of the Lipschitz constant to improve generalisation, and in general, one can scale it or indirectly reduce its value, e.g., by decaying the weights. As it relates to observing the bound/certificate values, a comparison between such values of networks would be more informative.

---

### ICLR.cc/2024/Conference/Submission5098/Reviewer_sG95 — 2023-11-22T19:06:57.073000+00:00

**title:**

Response to Rebuttal

**comment:**

Thank you for your detailed rebuttal, which answers most of my comments. However, I still think a proper evaluation against Gramlich2023 should be done either by requesting the code or by reimplementing it. 

I'll raise my score from 3 to 5.

---

### ICLR.cc/2024/Conference/Submission5098/Reviewer_qywJ — 2023-12-04T14:33:35.372000+00:00

**title:**

I read the rebuttal

**comment:**

Thank you very much for the added explanations. I appreciate the effort by the author in particular the addition of experiments on trained neural networks. The paper greatly improved thanks to all the new points but I do believe that this work is quite incremental and mainly consist in a technical improvement.

I however raise my grade from 3 to 5 following the different answers the authors provided to the other reviewers and myself.

---

### ICLR.cc/2024/Conference/Submission5098/Reviewer_G8PH — 2023-12-04T18:37:32.595000+00:00

**title:**

Response to Rebuttal

**comment:**

Thanks for the rebuttal. The authors have addressed most of my comments. I have increased my score from 5 to 6.

---

### ICLR.cc/2024/Conference/Submission5098/Reviewer_szVD — 2023-12-04T19:36:04.221000+00:00

**title:**

I read the rebuttal

**comment:**

Thanks for the comment. I read the rebuttal and would like to keep the same score.

---

## Meta Review

### ICLR.cc/2024/Conference/Submission5098/Area_Chair_ScN8 — 2023-12-15T04:00:34.436000+00:00

**metareview:**

This paper proposes a method to estimate the Lipschitz constant of convolutional neural networks. While the method demonstrates improved scalability over prior approaches, the experiments are limited in scope. Specifically:

- Experiments use random weights rather than trained networks where behavior may differ. 

- Input sizes are far smaller than common benchmarks like MNIST, limiting demonstration of scalability. 

- Details are lacking on compute resources used and whether approaches were fairly benchmarked.

- The estimated Lipschitz constants in the experiments are very large, which would give vacuous bounds on robust generalization. 

- The Lipschitz constant only measures worst-case robustness, which may not reflect distributional robustness properties that matter more for generalization.

I would encourage the authors to consider a major revision, and the paper could be much stronger if these concerns could be properly addressed.

**justification_for_why_not_higher_score:**

NA

**justification_for_why_not_lower_score:**

NA

---

## Decision

### ICLR.cc/2024/Conference/Program_Chairs — 2024-01-16T11:54:35.987000+00:00

**title:**

Paper Decision

**decision:**

Reject

---
