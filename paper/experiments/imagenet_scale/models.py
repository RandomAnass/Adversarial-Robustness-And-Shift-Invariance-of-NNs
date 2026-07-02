#!/usr/bin/env python3
"""
ImageNet-ready PreActResNet-18 with the same capacity-matched shift-invariance arms as the CIFAR
ResNet-scale dissection (S2: ImageNet-100 @160px check).

Reuses the operator classes VERBATIM from experiments/resnet_scale/models.py (PreActBlock, BlurPool2d,
aps_downsample, Normalize) via importlib (the file is also named models.py, so a plain import would
self-shadow). Only the stem differs from the CIFAR model: the standard ImageNet ResNet-18 stem
(conv7x7/s2 -> BN -> ReLU -> maxpool3x3/s2), giving 5 downsample sites total (stem conv, stem pool,
stage2/3/4 first blocks). The arm operator is applied at ALL 5 sites (incl. both stem sites):

  standard : circular padding, strided conv7x7 + circular-pad maxpool3x3/s2, strided blocks
             (exact only on the cumulative-stride-32 circular-shift subgroup)
  blurpool : conv7x7/s1 + BlurPool, maxpool3x3/s1 + BlurPool, blocks stride-1 + BlurPool (Zhang 2019).
             NOTE Zhang leaves conv1 strided for memory; we antialias it too so every site is treated
             uniformly by the arm operator (documented deviation).
  aps      : conv7x7/s1 + APS, maxpool3x3/s1 + APS, blocks stride-1 + APS with shared main/shortcut
             index (Chaman & Dokmanic 2021). All 5 sites polyphase-adaptive + circular padding
             everywhere => EXACT invariance to all integer circular shifts (logit-level, after GAP).
  aug      : architecture identical to `standard`; invariance learned via random circular-shift
             augmentation (+-16 px at 160px, proportional to the CIFAR +-4 at 32px) during training.

All arm operators are 0-param => arms are exactly capacity-matched. Padding is circular everywhere
(as in the CIFAR dissection) so the ONLY difference between arms is the downsampling operator.
Normalization (ImageNet mean/std) is folded into the model; attacks operate in [0,1].
160px input: 160 ->(stem conv) 80 ->(pool) 40 ->(L2) 20 ->(L3) 10 ->(L4) 5 -> GAP. All even, so APS
divisibility holds at every site.
"""
import os, importlib.util
import torch, torch.nn as nn, torch.nn.functional as F

_RS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resnet_scale", "models.py")
_spec = importlib.util.spec_from_file_location("resnet_scale_models", _RS_PATH)
_rsm = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_rsm)
PreActBlock, BlurPool2d, aps_downsample, Normalize = (_rsm.PreActBlock, _rsm.BlurPool2d,
                                                      _rsm.aps_downsample, _rsm.Normalize)

IMAGENET_MEAN = (0.485, 0.456, 0.406); IMAGENET_STD = (0.229, 0.224, 0.225)
ARMS = ["standard", "blurpool", "aps", "aug"]


class ImageNet100ResNet18(nn.Module):
    def __init__(self, arm="standard", num_classes=100, filt_size=3, aps_norm="inf",
                 mean=IMAGENET_MEAN, std=IMAGENET_STD):
        super().__init__()
        assert arm in ARMS, arm
        arch = "standard" if arm == "aug" else arm      # aug shares the standard architecture
        self.arm, self.arch, self.aps_norm = arm, arch, aps_norm
        self.norm = Normalize(mean, std)
        # --- stem: conv7x7 -> BN -> ReLU -> maxpool3x3, each downsampling via the arm operator ---
        self.stem_conv = nn.Conv2d(3, 64, 7, stride=(2 if arch == "standard" else 1),
                                   padding=3, bias=False, padding_mode="circular")
        self.stem_bn = nn.BatchNorm2d(64)
        if arch == "blurpool":
            self.stem_blur_conv = BlurPool2d(64, 2, filt_size)   # 0 params (fixed buffer)
            self.stem_blur_pool = BlurPool2d(64, 2, filt_size)
        # --- stages: PreActBlock reused as-is from the CIFAR dissection (arm ops at stride-2 blocks) ---
        self.in_planes = 64
        self.layer1 = self._make(64,  2, 1, arch, filt_size, aps_norm)
        self.layer2 = self._make(128, 2, 2, arch, filt_size, aps_norm)
        self.layer3 = self._make(256, 2, 2, arch, filt_size, aps_norm)
        self.layer4 = self._make(512, 2, 2, arch, filt_size, aps_norm)
        self.bn = nn.BatchNorm2d(512); self.fc = nn.Linear(512, num_classes)

    def _make(self, planes, n, stride, arch, filt_size, aps_norm):
        layers = []
        for s in [stride] + [1] * (n - 1):
            layers.append(PreActBlock(self.in_planes, planes, s, arch, filt_size, aps_norm))
            self.in_planes = planes
        return nn.Sequential(*layers)

    def _stem(self, x):
        x = self.stem_conv(x)                                    # site 1: stem conv
        if self.arch == "blurpool":   x = self.stem_blur_conv(x)
        elif self.arch == "aps":      x, _ = aps_downsample(x, 2, norm_p=self.aps_norm)
        x = F.relu(self.stem_bn(x))
        x = F.pad(x, (1, 1, 1, 1), mode="circular")              # site 2: stem pool (circular pad)
        if self.arch == "standard":
            x = F.max_pool2d(x, 3, stride=2)
        else:
            x = F.max_pool2d(x, 3, stride=1)
            # APS selection norm at the POOL site must be L2, not inf: a stride-1 maxpool smears the
            # global max over a 3x3 block, so ALL 4 polyphase components share the same inf-norm
            # (exact tie) and argmax tie-breaking by index order silently breaks shift equivariance.
            # L2 discriminates (ties are measure-zero). This matches Chaman & Dokmanic's default
            # (their public APS ResNets select on L2). Conv-output sites keep `aps_norm` ("inf",
            # as in the CIFAR dissection blocks), where values are generic and inf-norm is safe.
            x = self.stem_blur_pool(x) if self.arch == "blurpool" else aps_downsample(x, 2, norm_p="2")[0]
        return x

    def forward(self, x):
        assert x.shape[-1] % 32 == 0 and x.shape[-2] % 32 == 0, f"input {tuple(x.shape)} not /32"
        x = self._stem(self.norm(x))
        x = self.layer4(self.layer3(self.layer2(self.layer1(x))))
        x = F.relu(self.bn(x))
        return self.fc(F.adaptive_avg_pool2d(x, 1).flatten(1))


def build(arm, num_classes=100, filt_size=3, aps_norm="inf"):
    return ImageNet100ResNet18(arm, num_classes, filt_size, aps_norm)

def nparams(m): return sum(p.numel() for p in m.parameters())


if __name__ == "__main__":
    torch.manual_seed(0)
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    x = torch.rand(4, 3, 160, 160, device=dev)
    pc = {a: nparams(build(a)) for a in ARMS}
    print("param counts:", pc)
    assert len(set(pc.values())) == 1, f"arms NOT param-matched: {pc}"
    print(f"PARAM-MATCHED across all 4 arms: OK ({pc['standard']:,} params)")
    # invariance spectrum at 160px: APS exact to ALL integer circular shifts; standard/aug (circular
    # padding) exact only on the stride-32 subgroup; blurpool approximate everywhere.
    for arm in ARMS:
        m = build(arm).to(dev).eval()
        with torch.no_grad():
            d_arb = (m(x) - m(torch.roll(x, (3, 5),   dims=(2, 3)))).abs().max().item()   # off-subgroup
            d_one = (m(x) - m(torch.roll(x, (1, 0),   dims=(2, 3)))).abs().max().item()   # worst case
            d_sub = (m(x) - m(torch.roll(x, (32, 32), dims=(2, 3)))).abs().max().item()   # subgroup
        print(f"{arm:9s}: max|dlogit|  shift(3,5)={d_arb:.2e}  shift(1,0)={d_one:.2e}  shift(32,32)={d_sub:.2e}")
