"""ImageNet-100 validation loader for C1.

Decodes the HF `clane9/imagenet-100` validation parquet (5000 images, 100 classes)
to [0,1] RGB tensors at COMMON_RES=224 (bicubic resize + center crop), returning
tensors in PIXEL space [0,1] so attacks operate on raw pixels (normalization is folded
into each tower's forward). Also returns integer labels and the 100 class name strings.

We use ImageNet-100 val as the stated fallback so the run completes end-to-end
(full ImageNet-1k val is not present locally). It is a clean high-n zero-shot arm.
"""
import io
import json
import os
import torch
import numpy as np
from PIL import Image
import pyarrow.parquet as pq
import torchvision.transforms.functional as TF
from torchvision.transforms import InterpolationMode

VAL_PARQUET = "/home/students/code/Anas/adversarial-robustness-shift-invariance/paper/data/imagenet100/parquet/validation-00000-of-00001.parquet"
RES = 224


def get_class_names():
    f = pq.ParquetFile(VAL_PARQUET)
    md = f.schema_arrow.metadata
    hf = json.loads(md[b"huggingface"].decode())
    names = hf["info"]["features"]["label"]["names"]
    assert len(names) == 100, len(names)
    return names


def _decode_one(img_bytes, res=RES):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    # Resize shorter side to res then center-crop res (standard CLIP eval geometry)
    w, h = img.size
    scale = res / min(w, h)
    nw, nh = round(w * scale), round(h * scale)
    img = img.resize((nw, nh), Image.BICUBIC)
    left = (nw - res) // 2
    top = (nh - res) // 2
    img = img.crop((left, top, left + res, top + res))
    arr = np.asarray(img, dtype=np.float32) / 255.0  # HWC in [0,1]
    t = torch.from_numpy(arr).permute(2, 0, 1).contiguous()  # CHW
    return t


def load_val(n=None, seed=0, cache_path=None):
    """Return (images [N,3,224,224] in [0,1], labels [N]).

    If cache_path is set and exists, load from there; else decode and save.
    n subsamples a class-balanced-ish random subset (by shuffling) of size n.
    """
    if cache_path and os.path.exists(cache_path):
        d = torch.load(cache_path)
        imgs, labels = d["images"], d["labels"]
    else:
        f = pq.ParquetFile(VAL_PARQUET)
        t = f.read().to_pydict()
        img_structs = t["image"]
        labels = torch.tensor(t["label"], dtype=torch.long)
        imgs = torch.empty((len(labels), 3, RES, RES), dtype=torch.float32)
        for i, s in enumerate(img_structs):
            imgs[i] = _decode_one(s["bytes"])
        if cache_path:
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            torch.save({"images": imgs, "labels": labels}, cache_path)
    if n is not None and n < len(labels):
        g = torch.Generator().manual_seed(seed)
        idx = torch.randperm(len(labels), generator=g)[:n]
        imgs, labels = imgs[idx], labels[idx]
    return imgs, labels
