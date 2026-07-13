"""C1 tower panel: frozen VLM vision towers wrapped as zero-shot ImageNet classifiers.

All towers evaluated at ONE common input resolution (224 px) so that shift-consistency
(phase-grid size) and gradient-norm scale are not resolution confounds (round2_C fix 4).

Panel (7 towers spanning the invariance x robustness plane):
  - clip        : openai CLIP ViT-L/14 (non-robust base)                [open_clip]
  - fare2/fare4 : RobustVLM FARE adversarially-trained CLIP towers      [open_clip hf-hub]
  - tecoa2/tecoa4: RobustVLM TeCoA adversarially-trained CLIP towers    [open_clip hf-hub]
  - dinov2      : DINOv2 ViT-L/14 (non-AT, high-invariance widener)     [timm, linear-probe head]
  - clip_aa     : anti-aliased (blur-pool patch-embed stem) base CLIP   [training-free operator swap]

The two non-AT wideners (dinov2, clip_aa) open the shift-consistency axis so the SC
anti-prediction can appear (the 4 AT towers alone cluster; round1/round2 collinearity fix).

Each tower exposes:
  logits(images) -> [B, n_classes] zero-shot logits (differentiable, for margin/grad/attack)
  images are already normalized to the tower's own mean/std by the caller-provided normalizer,
  BUT for attacks we keep the [0,1] pixel space outside and fold normalization INTO the forward
  so APGD/PGD operate on raw [0,1] pixels (correct threat model).
"""
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import open_clip

COMMON_RES = 224  # single common eval resolution for the whole panel (resolution-confound fix)

# CLIP normalization (used by CLIP, FARE, TeCoA towers)
CLIP_MEAN = (0.48145466, 0.4578275, 0.40821073)
CLIP_STD = (0.26862954, 0.26130258, 0.27577711)
# DINOv2/ImageNet normalization
IN_MEAN = (0.485, 0.456, 0.406)
IN_STD = (0.229, 0.224, 0.225)


class Normalizer(nn.Module):
    """Fold channel normalization into the forward graph so attacks live in [0,1] pixels."""
    def __init__(self, mean, std):
        super().__init__()
        self.register_buffer("mean", torch.tensor(mean).view(1, 3, 1, 1))
        self.register_buffer("std", torch.tensor(std).view(1, 3, 1, 1))

    def forward(self, x):
        return (x - self.mean) / self.std


class BlurPoolPatchEmbed(nn.Module):
    """Anti-aliased patch-embed stem: low-pass filter (binomial blur) the input before the
    stride-14 patch conv. Training-free operator that raises shift-consistency without AT.
    Applied as a depthwise 'blur then conv' on the RGB input; the conv weights are the
    original CLIP patch-embed weights (frozen), so clean accuracy is largely preserved.
    """
    def __init__(self, orig_conv: nn.Conv2d, blur_size=3):
        super().__init__()
        self.conv = orig_conv  # frozen original patch-embed conv (kept as-is)
        # Binomial (Pascal) 1D kernel -> separable 2D low-pass, depthwise over 3 channels.
        if blur_size == 3:
            k1 = torch.tensor([1.0, 2.0, 1.0])
        elif blur_size == 5:
            k1 = torch.tensor([1.0, 4.0, 6.0, 4.0, 1.0])
        else:
            raise ValueError(blur_size)
        k2 = torch.outer(k1, k1)
        k2 = k2 / k2.sum()
        blur = k2.view(1, 1, blur_size, blur_size).repeat(3, 1, 1, 1)  # depthwise
        self.register_buffer("blur", blur)
        self.pad = blur_size // 2

    def forward(self, x):
        # x: [B,3,H,W] normalized input. Low-pass (reflect pad, depthwise), then patch conv.
        xb = F.pad(x, (self.pad,) * 4, mode="reflect")
        xb = F.conv2d(xb, self.blur, groups=3)
        return self.conv(xb)


class ClipZeroShot(nn.Module):
    """open_clip tower + frozen zero-shot text-prototype head -> ImageNet logits."""
    def __init__(self, clip_model, text_features, mean, std, logit_scale=None):
        super().__init__()
        self.visual = clip_model.visual
        self.norm = Normalizer(mean, std)
        self.register_buffer("text_features", text_features)  # [n_classes, d], L2-normalized
        if logit_scale is None:
            logit_scale = clip_model.logit_scale.exp().detach()
        self.register_buffer("logit_scale", torch.as_tensor(float(logit_scale)))

    def encode(self, x01):
        x = self.norm(x01)
        feats = self.visual(x)
        return F.normalize(feats, dim=-1)

    def forward(self, x01):
        # x01 in [0,1], [B,3,224,224]
        img = self.encode(x01)
        return self.logit_scale * img @ self.text_features.t()


class LinearProbeZeroShot(nn.Module):
    """DINOv2 backbone (timm) + a fitted linear-probe head -> ImageNet-100 logits.
    Used as a non-AT high-invariance panel widener (no CLIP text space)."""
    def __init__(self, backbone, head_w, head_b, mean, std):
        super().__init__()
        self.backbone = backbone
        self.norm = Normalizer(mean, std)
        self.register_buffer("head_w", head_w)  # [n_classes, d]
        self.register_buffer("head_b", head_b)  # [n_classes]

    def encode(self, x01):
        x = self.norm(x01)
        feats = self.backbone(x)  # pooled CLS feature [B,d]
        return feats

    def forward(self, x01):
        feats = self.encode(x01)
        return F.linear(feats, self.head_w, self.head_b)


# ---------------------------------------------------------------------------
# Zero-shot text prototype construction (OpenAI ImageNet prompt ensemble subset)
# ---------------------------------------------------------------------------
OPENAI_TEMPLATES = [
    "a photo of a {}.",
    "a bad photo of a {}.",
    "a photo of many {}.",
    "a photo of the large {}.",
    "a photo of the small {}.",
    "a cropped photo of a {}.",
    "a close-up photo of a {}.",
    "a good photo of a {}.",
    "a photo of one {}.",
    "itap of a {}.",
]


@torch.no_grad()
def build_text_features(clip_model, tokenizer, class_names, device):
    """Zero-shot text prototypes: mean over prompt templates per class, L2-normalized."""
    clip_model = clip_model.to(device).eval()
    feats = []
    for name in class_names:
        # take the first alias before comma as the primary name; also keep full
        primary = name.split(",")[0].strip()
        prompts = [t.format(primary) for t in OPENAI_TEMPLATES]
        toks = tokenizer(prompts).to(device)
        tf = clip_model.encode_text(toks)
        tf = F.normalize(tf, dim=-1).mean(0)
        tf = F.normalize(tf, dim=-1)
        feats.append(tf)
    return torch.stack(feats, 0)  # [n_classes, d]


# ---------------------------------------------------------------------------
# Panel factory
# ---------------------------------------------------------------------------
CLIP_TOWERS = {
    "clip":   ("ViT-L-14-quickgelu", "openai"),
    "fare2":  ("hf-hub:chs20/fare2-clip", None),
    "fare4":  ("hf-hub:chs20/fare4-clip", None),
    "tecoa2": ("hf-hub:chs20/tecoa2-clip", None),
    "tecoa4": ("hf-hub:chs20/tecoa4-clip", None),
    # --- extended panel: NON-AT CLIP towers spanning a range of eta/L and SC (verifier) ---
    # These widen the invariance x robustness plane away from the AT-vs-non-AT split, so the
    # eta/L ranking is tested against genuinely diverse non-AT encoders (different pretraining
    # corpora, patch sizes, capacities). All are Linf-non-robust (S~0), so they test whether
    # (i) low eta/L uniformly co-occurs with S~0 across diverse non-AT towers, and (ii) whether
    # SC_cos "predicts" S only because it co-detects AT (it should collapse on this non-AT sweep).
    "clip_l14_laion2b": ("ViT-L-14", "laion2b_s32b_b82k"),
    "clip_l14_datacomp": ("ViT-L-14", "datacomp_xl_s13b_b90k"),
    "clip_b16_openai":  ("ViT-B-16", "openai"),
    "clip_b16_laion2b": ("ViT-B-16", "laion2b_s34b_b88k"),
    "clip_b32_laion2b": ("ViT-B-32", "laion2b_s34b_b79k"),
    "clip_l14_metaclip": ("ViT-L-14-quickgelu", "metaclip_fullcc"),
    # --- ROBUST-PANEL EXPANSION (review round 1 fix: power the tower axis, more robust encoders) ---
    # 6 more chs20 FARE/TeCoA robust towers at new backbones (eps=4/255), open_clip hf-hub drop-ins.
    "fare4_b32":   ("hf-hub:chs20/FARE4-ViT-B-32-laion2B-s34B-b79K", None),
    "tecoa4_b32":  ("hf-hub:chs20/TeCoA4-ViT-B-32-laion2B-s34B-b79K", None),
    "fare4_b16":   ("hf-hub:chs20/FARE4-ViT-B-16-laion2B-s34B-b88K", None),
    "tecoa4_b16":  ("hf-hub:chs20/TeCoA4-ViT-B-16-laion2B-s34B-b88K", None),
    "fare4_cnxt":  ("hf-hub:chs20/FARE4-convnext_base_w-laion2B-s13B-b82K-augreg", None),
    "tecoa4_cnxt": ("hf-hub:chs20/TeCoA4-convnext_base_w-laion2B-s13B-b82K-augreg", None),
    # Delta-CLIP (Double Visual Defense, distinct method, SOTA robust) -- open_clip hf-hub; verify load.
    "delta_l14":   ("hf-hub:zw123/delta_clip_l14_224", None),
}

# adversarially-robust towers (for the AT indicator in analysis)
ROBUST_TOWERS = {"fare2", "fare4", "tecoa2", "tecoa4",
                 "fare4_b32", "tecoa4_b32", "fare4_b16", "tecoa4_b16",
                 "fare4_cnxt", "tecoa4_cnxt"}
# 6 verified-loadable robust encoders to run for the panel expansion (4 -> 10 robust towers).
# delta_l14 (Double Visual Defense, SOTA) deferred: zw123 hf-hub config incompatible with this
# open_clip (CLIPTextCfg vocab_path); add via vision-state_dict if more power is needed.
NEW_ROBUST = ["fare4_b32", "tecoa4_b32", "fare4_b16", "tecoa4_b16", "fare4_cnxt", "tecoa4_cnxt"]


def load_clip_tower(name, class_names, device, anti_alias=False, blur_size=3):
    """Load an open_clip tower and attach a frozen zero-shot head at COMMON_RES."""
    arch, pretrained = CLIP_TOWERS[name] if not anti_alias else CLIP_TOWERS["clip"]
    # RobustVLM/base share a ViT-L-14 text tower; extended non-AT towers carry their own tag.
    if pretrained is not None:
        model, _, _ = open_clip.create_model_and_transforms(arch, pretrained=pretrained)
        tokenizer = open_clip.get_tokenizer(arch)
    else:
        model, _, _ = open_clip.create_model_and_transforms(arch)
        # RobustVLM towers share the base ViT-L/14 text tower + tokenizer
        tokenizer = open_clip.get_tokenizer("ViT-L-14")
    model = model.to(device).eval()
    for p in model.parameters():
        p.requires_grad_(False)
    # text prototypes are built from the SAME model's text tower (CLIP space is shared for
    # base/FARE/TeCoA since RobustVLM only fine-tunes the vision tower)
    text_features = build_text_features(model, tokenizer, class_names, device)
    if anti_alias:
        # swap patch-embed conv for blur-pool version (frozen)
        orig = model.visual.conv1  # open_clip ViT patch-embed conv (Conv2d, stride=patch)
        model.visual.conv1 = BlurPoolPatchEmbed(orig, blur_size=blur_size).to(device)
    tower = ClipZeroShot(model, text_features, CLIP_MEAN, CLIP_STD).to(device).eval()
    for p in tower.parameters():
        p.requires_grad_(False)
    return tower


def load_dinov2_backbone(device):
    """DINOv2 ViT-L/14 from local timm cache; returns a callable that pools CLS feature."""
    import timm
    backbone = timm.create_model(
        "vit_large_patch14_reg4_dinov2.lvd142m",
        pretrained=True, num_classes=0, img_size=COMMON_RES,
    ).to(device).eval()
    for p in backbone.parameters():
        p.requires_grad_(False)
    return backbone
