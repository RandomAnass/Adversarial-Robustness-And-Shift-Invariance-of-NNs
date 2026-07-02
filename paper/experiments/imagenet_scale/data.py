#!/usr/bin/env python3
"""
ImageNet-100 data for the S2 scale check.

Source: HuggingFace `clane9/imagenet-100` (100-class ImageNet-1k subset of Tian et al. 2019 CMC,
images pre-resized to 160px shorter side; 126,689 train / 5,000 val images). Downloaded as parquet
(paper/data/imagenet100/download.sh); this module decodes once into cached uint8 tensors
(center-crop 160x160) and then serves everything from RAM. The official validation split is our
TEST set; a seeded 1000-image holdout from train is the val split (CO-guard / model selection),
mirroring the CIFAR ResNet-scale protocol.

Cache build: `python data.py build` (needs pyarrow on PYTHONPATH; ~18 shards decoded in parallel).
"""
import os, io, sys, glob, json
import numpy as np, torch
from concurrent.futures import ProcessPoolExecutor

DATA = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "data", "imagenet100"))
PARQUET, CACHE = os.path.join(DATA, "parquet"), os.path.join(DATA, "cache")
SIZE = 160


def _decode_shard(args):
    shard, out, size = args
    import pyarrow.parquet as pq
    from PIL import Image
    t = pq.read_table(shard)
    imgs, labels = t.column("image").to_pylist(), t.column("label").to_pylist()
    X = np.empty((len(labels), 3, size, size), dtype=np.uint8)
    for i, d in enumerate(imgs):
        im = Image.open(io.BytesIO(d["bytes"])).convert("RGB")
        w, h = im.size
        if min(w, h) != size:                       # guard; dataset is already 160 shorter-side
            s = size / min(w, h)
            im = im.resize((max(size, round(w * s)), max(size, round(h * s))), Image.BICUBIC)
            w, h = im.size
        l, t0 = (w - size) // 2, (h - size) // 2    # center crop
        X[i] = np.asarray(im.crop((l, t0, l + size, t0 + size)), dtype=np.uint8).transpose(2, 0, 1)
    torch.save({"X": torch.from_numpy(X), "y": torch.tensor(labels, dtype=torch.long)}, out)
    return out, len(labels)


def build_cache(workers=9):
    os.makedirs(CACHE, exist_ok=True)
    tr_shards = sorted(glob.glob(os.path.join(PARQUET, "train-*.parquet")))
    va_shards = sorted(glob.glob(os.path.join(PARQUET, "validation-*.parquet")))
    assert len(tr_shards) == 17 and len(va_shards) == 1, (len(tr_shards), len(va_shards))
    jobs = [(s, os.path.join(CACHE, os.path.basename(s) + ".pt"), SIZE) for s in tr_shards + va_shards]
    with ProcessPoolExecutor(workers) as ex:
        for out, n in ex.map(_decode_shard, jobs):
            print(f"decoded {os.path.basename(out)}: {n} imgs", flush=True)
    for split, shards in [("train", tr_shards), ("test", va_shards)]:
        parts = [torch.load(os.path.join(CACHE, os.path.basename(s) + ".pt")) for s in shards]
        X = torch.cat([p["X"] for p in parts]); y = torch.cat([p["y"] for p in parts])
        torch.save({"X": X, "y": y}, os.path.join(CACHE, f"{split}.pt"))
        print(f"{split}: {tuple(X.shape)} uint8, {y.max().item()+1} classes", flush=True)
    for s in tr_shards + va_shards:
        os.remove(os.path.join(CACHE, os.path.basename(s) + ".pt"))
    with open(os.path.join(CACHE, "meta.json"), "w") as f:
        json.dump({"source": "hf:clane9/imagenet-100", "size": SIZE, "crop": "center"}, f)
    print("CACHE_BUILT", flush=True)


def load_data(val_size=1000, seed=0):
    """uint8 tensors in RAM. Seeded val holdout from train (CIFAR protocol); official val = test."""
    tr = torch.load(os.path.join(CACHE, "train.pt"))
    te = torch.load(os.path.join(CACHE, "test.pt"))
    g = torch.Generator().manual_seed(seed)
    perm = torch.randperm(len(tr["X"]), generator=g)
    vi, ti = perm[:val_size], perm[val_size:]
    return {"Xtr": tr["X"][ti], "ytr": tr["y"][ti], "Xval": tr["X"][vi], "yval": tr["y"][vi],
            "Xte": te["X"], "yte": te["y"], "n_classes": 100}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        build_cache()
    else:
        d = load_data()
        print({k: (tuple(v.shape) if torch.is_tensor(v) else v) for k, v in d.items()})
