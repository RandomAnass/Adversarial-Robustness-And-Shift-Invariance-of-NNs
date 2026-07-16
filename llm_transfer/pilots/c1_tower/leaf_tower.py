"""STRETCH: LEAF robust-TEXT tower (leaf_L_text) as a drop-in ClipZeroShot-compatible tower.

LEAF-CLIP/CLIP-ViT-L-rho50-k1-constrained-FARE2 is a transformers-format CLIPModel whose VISION
tower is FARE2-hardened AND whose TEXT tower is Levenshtein-k1 (char-edit) constrained -- the ONLY
panel candidate with a robustified TEXT tower. So, unlike the FARE/TeCoA/Sim-CLIP towers (which
share the frozen OpenAI text tower), this tower uses ITS OWN hardened text tower to build the
zero-shot head. That is the whole point: it lets the text-adversarial cell vary independently.

We wrap the transformers CLIPModel to expose the EXACT ClipZeroShot interface used by the hardened
runner (encode / forward on [0,1] pixels, text_features, logit_scale), so it flows through
diagnostics.margin_and_grad, attacks.run_autoattack/per_image_robust_radius_linf, shift_consistency,
and the S_text worst-case-over-paraphrases code with NO other changes. Normalization is folded into
forward so attacks live in [0,1] pixels (same threat model as every other tower).

This is a recipe-C conversion (transformers CLIPModel -> tower); the vision backbone is the standard
CLIP ViT-L/14 (hidden 1024, 24 layers, patch 14, projection 768), so gradients/margins are directly
comparable. Sanity gates (clean acc reasonable, S>0) are enforced by the runner before merging.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

import towers

LEAF_REPO = "LEAF-CLIP/CLIP-ViT-L-rho50-k1-constrained-FARE2"
# CLIP tokenizer for the LEAF text tower (standard CLIP BPE, 77 ctx).
LEAF_TOKENIZER = "openai/clip-vit-large-patch14"


class LeafClipZeroShot(nn.Module):
    """transformers CLIPModel wrapped as a zero-shot ImageNet tower on [0,1] pixels.

    Uses LEAF's OWN vision AND text towers (both hardened). Mirrors towers.ClipZeroShot:
      encode(x01) -> L2-normalized image embedding
      forward(x01) -> logit_scale * img @ text_features.T   (differentiable, [0,1] pixels)
    """
    def __init__(self, clip_model, text_features, mean, std, logit_scale):
        super().__init__()
        self.clip = clip_model
        self.norm = towers.Normalizer(mean, std)
        self.register_buffer("text_features", text_features)     # [n_classes, d], L2-normalized
        self.register_buffer("logit_scale", torch.as_tensor(float(logit_scale)))

    def encode(self, x01):
        x = self.norm(x01)
        feats = self.clip.get_image_features(pixel_values=x)     # [B, d] (already projected)
        return F.normalize(feats, dim=-1)

    def forward(self, x01):
        img = self.encode(x01)
        return self.logit_scale * img @ self.text_features.t()


@torch.no_grad()
def _build_leaf_text_features(clip_model, tokenizer, class_names, template, device):
    """One text prototype per class from ONE template, via LEAF's OWN text tower."""
    feats = []
    for name in class_names:
        primary = name.split(",")[0].strip()
        toks = tokenizer([template.format(primary)], padding="max_length",
                         max_length=77, truncation=True, return_tensors="pt").to(device)
        tf = clip_model.get_text_features(input_ids=toks["input_ids"],
                                          attention_mask=toks["attention_mask"])
        tf = F.normalize(tf, dim=-1)[0]
        feats.append(tf)
    return torch.stack(feats, 0)


def load_leaf_text_tower(class_names, device, template="a photo of a {}."):
    """Load leaf_L_text with a reference single-template head built from its own hardened text tower.

    Returns (tower, clip_model, tokenizer) matching the runner's load_tower_dispatch contract, where
    `tower` is a LeafClipZeroShot and `clip_model`/`tokenizer` support building the paraphrase heads
    for PC and S_text (also via LEAF's own text tower)."""
    from transformers import CLIPModel, CLIPTokenizer
    model = CLIPModel.from_pretrained(LEAF_REPO).to(device).eval()
    tokenizer = CLIPTokenizer.from_pretrained(LEAF_TOKENIZER)
    for p in model.parameters():
        p.requires_grad_(False)
    logit_scale = model.logit_scale.exp().detach().item()
    ref_tf = _build_leaf_text_features(model, tokenizer, class_names, template, device)
    tower = LeafClipZeroShot(model, ref_tf, towers.CLIP_MEAN, towers.CLIP_STD, logit_scale)
    tower = tower.to(device).eval()
    for p in tower.parameters():
        p.requires_grad_(False)
    return tower, model, tokenizer


# --- shim so the runner's build_single_template_features / paraphrase / S_text code works ---
# run_crownjewel_hardened builds paraphrase heads via CJ.build_single_template_features(clip_model,
# tokenizer, class_names, template, device), which calls clip_model.encode_text(tokenizer([...])).
# A transformers CLIPModel has no .encode_text; we attach a compatible method + a callable tokenizer
# wrapper so the SAME paraphrase/S_text code path is reused verbatim (no branching in the metrics).
class _LeafTokenizerShim:
    def __init__(self, tok):
        self.tok = tok

    def __call__(self, texts):
        out = self.tok(texts, padding="max_length", max_length=77, truncation=True,
                       return_tensors="pt")
        # return an object exposing .to(device) that yields input dict; but the reuse code does
        # tokenizer([...]).to(device) then clip_model.encode_text(toks). We stash attention mask
        # on the tensor via a light wrapper.
        return _LeafToks(out)


class _LeafToks:
    def __init__(self, enc):
        self.enc = enc

    def to(self, device):
        self.enc = {k: v.to(device) for k, v in self.enc.items()}
        return self


def wrap_leaf_for_reuse(model, tokenizer):
    """Attach .encode_text to the transformers model and wrap the tokenizer so that
    CJ.build_single_template_features(model, tok, ...) runs unchanged on LEAF."""
    def encode_text(toks):
        enc = toks.enc if isinstance(toks, _LeafToks) else toks
        return model.get_text_features(input_ids=enc["input_ids"],
                                       attention_mask=enc.get("attention_mask"))
    model.encode_text = encode_text
    return model, _LeafTokenizerShim(tokenizer)
