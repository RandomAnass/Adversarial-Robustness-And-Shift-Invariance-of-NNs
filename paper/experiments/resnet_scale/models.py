#!/usr/bin/env python3
"""
PreActResNet-18 (CIFAR) with capacity-matched shift-invariance arms.

Padding is held FIXED (circular) across the four comparison arms, so the ONLY thing that differs is
the downsampling operator at the 3 sites (stage2/3/4 block1: strided main 3x3 + strided 1x1 shortcut):
  standard : circular padding, stride-2 subsample            (non-anti-aliased baseline; exact only on
                                                              the cumulative-stride shift subgroup)
  blurpool : circular padding, stride-1 + BlurPool (Zhang2019)        (approx shift-invariant, consist<1)
  aps      : circular padding, stride-1 + Adaptive Polyphase Sampling (Chaman&Dokmanic2021)
                                                              (EXACT to all integer circular shifts, consist=1)
  aug      : same architecture as `standard` (circular), invariance learned via random circular-shift aug
  stdzero  : ZERO padding, stride-2 subsample    (ABLATION ONLY: isolates the padding effect vs `standard`)

Normalization is folded into the model (Normalize) so attacks operate in [0,1]. BlurPool kernel and APS
selection are non-learned -> all arms are parameter-matched. Architecture: He2016 full pre-activation +
locuslab/robust_overfitting (final BN+ReLU before GAP).
"""
import torch, torch.nn as nn, torch.nn.functional as F

CIFAR_MEAN = (0.4914, 0.4822, 0.4465); CIFAR_STD = (0.2470, 0.2435, 0.2616)
ARMS = ["standard", "blurpool", "aps", "aug"]      # the four comparison arms (all circular padding)
ABLATION_ARMS = ["stdzero", "maxpool"]              # low-invariance arms: stdzero=zero-pad strided
                                                    # (padding control); maxpool=zero-pad + maxpool
                                                    # downsampling (canonical aliasing op, Zhang2019).
                                                    # Both deliberately widen the consistency axis.
ALL_ARMS = ARMS + ABLATION_ARMS

def _pad_mode(arm):  return "zeros" if arm in ("stdzero", "maxpool") else "circular"
def _downsamp(arm):  return arm if arm in ("blurpool", "aps", "maxpool") else "stride"  # else: plain strided conv


class Normalize(nn.Module):
    def __init__(self, mean, std):
        super().__init__()
        self.register_buffer("m", torch.tensor(mean).view(1, -1, 1, 1))
        self.register_buffer("s", torch.tensor(std).view(1, -1, 1, 1))
    def forward(self, x): return (x - self.m) / self.s


def _blur_kernel(filt_size):
    a = {2: [1., 1.], 3: [1., 2., 1.], 5: [1., 4., 6., 4., 1.]}[filt_size]
    a = torch.tensor(a); k = torch.outer(a, a); return k / k.sum()


class BlurPool2d(nn.Module):
    """Circular blur-then-subsample (Zhang2019): depthwise fixed low-pass filter, stride 2. 0 params."""
    def __init__(self, channels, stride=2, filt_size=3):
        super().__init__()
        self.stride, self.channels, self.pad = stride, channels, (filt_size - 1) // 2
        self.register_buffer("filt", _blur_kernel(filt_size)[None, None].repeat(channels, 1, 1, 1))
    def forward(self, x):
        x = F.pad(x, (self.pad,) * 4, mode="circular")
        return F.conv2d(x, self.filt, stride=self.stride, groups=self.channels)


def aps_downsample(x, stride=2, idx=None, norm_p="inf"):
    """Adaptive Polyphase Sampling (Chaman&Dokmanic2021): select the max-norm polyphase component
    (permutation-invariant -> shift-invariant). Returns (selected, idx); pass idx to force the same
    component (keeps the main and shortcut branches aligned, which is what makes the block exact)."""
    B, C, H, W = x.shape
    comps = torch.stack([x[:, :, i::stride, j::stride] for i in range(stride) for j in range(stride)], 1)
    if idx is None:
        flat = comps.reshape(B, stride * stride, -1)
        n = flat.abs().amax(-1) if norm_p == "inf" else (flat.norm(dim=-1) if norm_p == "2" else flat.abs().sum(-1))
        idx = n.argmax(1)
    sel = comps[torch.arange(B, device=x.device), idx]
    return sel, idx


class PreActBlock(nn.Module):
    expansion = 1
    def __init__(self, in_planes, planes, stride=1, arm="standard", filt_size=3, aps_norm="inf"):
        super().__init__()
        self.stride, self.arm, self.aps_norm = stride, arm, aps_norm
        ds = _downsamp(arm); pad_mode = _pad_mode(arm)
        conv_stride = stride if ds == "stride" else 1            # blur/aps downsample separately
        self.bn1 = nn.BatchNorm2d(in_planes)
        self.conv1 = nn.Conv2d(in_planes, planes, 3, stride=conv_stride, padding=1, bias=False, padding_mode=pad_mode)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, 3, stride=1, padding=1, bias=False, padding_mode=pad_mode)
        self.downsample = (stride != 1 or in_planes != planes)
        if self.downsample:
            sc_stride = stride if ds == "stride" else 1
            self.shortcut = nn.Conv2d(in_planes, planes, 1, stride=sc_stride, bias=False)
        if stride != 1 and ds == "blurpool":
            self.blur_main = BlurPool2d(planes, stride, filt_size)
            self.blur_sc = BlurPool2d(planes, stride, filt_size)

    def forward(self, x):
        pre = F.relu(self.bn1(x))
        out = self.conv1(pre)
        sc = self.shortcut(pre) if self.downsample else x
        ds = _downsamp(self.arm)
        if self.stride != 1 and ds != "stride":
            if ds == "blurpool":
                out, sc = self.blur_main(out), self.blur_sc(sc)
            elif ds == "maxpool":                                # zero-pad + maxpool subsample (aliasing)
                out, sc = F.max_pool2d(out, 2), F.max_pool2d(sc, 2)
            else:                                                # aps: shared polyphase index
                out, idx = aps_downsample(out, self.stride, norm_p=self.aps_norm)
                sc, _ = aps_downsample(sc, self.stride, idx=idx)
        out = self.conv2(F.relu(self.bn2(out)))
        return out + sc


class PreActResNet(nn.Module):
    def __init__(self, arm="standard", width=1.0, num_classes=10, in_ch=3,
                 mean=CIFAR_MEAN, std=CIFAR_STD, filt_size=3, aps_norm="inf", num_blocks=(2, 2, 2, 2)):
        super().__init__()
        assert arm in ALL_ARMS, arm
        self.arm = arm; self.norm = Normalize(mean, std)
        w = [int(round(c * width)) for c in (64, 128, 256, 512)]
        self.in_planes = w[0]
        self.stem = nn.Conv2d(in_ch, w[0], 3, stride=1, padding=1, bias=False, padding_mode=_pad_mode(arm))
        self.layer1 = self._make(w[0], num_blocks[0], 1, arm, filt_size, aps_norm)
        self.layer2 = self._make(w[1], num_blocks[1], 2, arm, filt_size, aps_norm)
        self.layer3 = self._make(w[2], num_blocks[2], 2, arm, filt_size, aps_norm)
        self.layer4 = self._make(w[3], num_blocks[3], 2, arm, filt_size, aps_norm)
        self.bn = nn.BatchNorm2d(w[3]); self.fc = nn.Linear(w[3], num_classes)

    def _make(self, planes, n, stride, arm, filt_size, aps_norm):
        layers = []
        for s in [stride] + [1] * (n - 1):
            layers.append(PreActBlock(self.in_planes, planes, s, arm, filt_size, aps_norm)); self.in_planes = planes
        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.norm(x); x = self.stem(x)
        x = self.layer4(self.layer3(self.layer2(self.layer1(x))))
        x = F.relu(self.bn(x))
        return self.fc(F.adaptive_avg_pool2d(x, 1).flatten(1))


def build(arm, width=1.0, num_classes=10, in_ch=3, mean=CIFAR_MEAN, std=CIFAR_STD, filt_size=3, aps_norm="inf"):
    return PreActResNet(arm, width, num_classes, in_ch, mean, std, filt_size, aps_norm)

def nparams(m): return sum(p.numel() for p in m.parameters())


if __name__ == "__main__":
    torch.manual_seed(0); x = torch.rand(8, 3, 32, 32)
    pc = {a: nparams(build(a).eval()) for a in ALL_ARMS}
    print("param counts:", pc)
    assert len(set(pc.values())) == 1, f"arms NOT param-matched: {pc}"
    print("PARAM-MATCHED across all arms (incl. ablation): OK")
    # invariance spectrum: APS exact to all shifts; standard(circular) exact only on the stride subgroup;
    # stdzero (zero pad) exact on none.
    for arm in ALL_ARMS:
        m = build(arm).eval()
        with torch.no_grad():
            d_arb = (m(x) - m(torch.roll(x, (3, 5), dims=(2, 3)))).abs().max().item()    # off-subgroup
            d_sub = (m(x) - m(torch.roll(x, (8, 8), dims=(2, 3)))).abs().max().item()    # subgroup (mult of 8)
        print(f"{arm:9s}: max|dlogit|  shift(3,5)={d_arb:.2e}   shift(8,8)={d_sub:.2e}")
