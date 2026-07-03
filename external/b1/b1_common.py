#!/usr/bin/env python3
"""
B1 (Wang et al. 2025, "Bridging Symmetry and Robustness", NeurIPS 2025) shared code.

Steelman guarantee: the model classes and their FGSM/PGD attack functions are NOT reimplemented.
They are extracted VERBATIM (by AST source segment) from the authors' files in
external/role_of_equivariance/ and exec'd unchanged. Only the attack is upgraded (AutoAttack),
everything else -- architecture, preprocessing, training recipe, attack protocol -- is theirs.

Their preprocessing: ToTensor + Normalize((0.5,)*3, (0.5,)*3)  =>  model input space is [-1,1].
Their attacks perturb the NORMALIZED tensor (so their eps=0.03 is 0.015 in [0,1] pixel units)
and clamp adversarial images to [0,1] (their code, kept verbatim -- clamp quirk included).
AutoAttack is run in the standard [0,1] pixel space with the normalization wrapped inside the
model (PixelSpaceModel); eps=0.015 pixel-space therefore equals their eps=0.03 budget.
"""
import ast, os, pathlib, torch, torch.nn as nn

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent / "role_of_equivariance"
PAPER = HERE.parent.parent / "paper"
RESDIR = PAPER / "results" / "b1_wang"
DATADIR = PAPER / "data"          # shared CIFAR root (cifar-10-batches-py already present)

# (their training file, their test file, model class name) per variant
VARIANTS = {
    "cascaded": ("cifar10/cascadedGCNN10layer_cifar10.py",
                 "cifar10/cascadedGCNN10layer_cifar10_test.py", "CascadedGCNN"),
    "parallel": ("cifar10/parallelGCNN10layer_cifar10_no_aug.py",
                 "cifar10/parallelGCNN10layer_cifar10_no_aug.py", "ImprovedParallelGCNN"),
}

def _their_namespace(device, criterion=None):
    """The exact global names their file-level code relies on."""
    import torch.nn.functional as F
    from e2cnn.nn import R2Conv, GeometricTensor, FieldType, ReLU
    from e2cnn.gspaces import Rot2dOnR2
    ns = dict(torch=torch, nn=nn, F=F, R2Conv=R2Conv, GeometricTensor=GeometricTensor,
              FieldType=FieldType, ReLU=ReLU, Rot2dOnR2=Rot2dOnR2, device=device)
    ns["criterion"] = criterion if criterion is not None else nn.CrossEntropyLoss()
    return ns

def _extract(src_path, node_type, name):
    src = (REPO / src_path).read_text()
    for node in ast.parse(src).body:
        if isinstance(node, node_type) and node.name == name:
            return ast.get_source_segment(src, node)
    raise KeyError(f"{name} not found in {src_path}")

def load_their_model_class(variant, device):
    """exec the verbatim class source from their training file; returns (cls, source_str)."""
    train_file, _, cls_name = VARIANTS[variant]
    src = _extract(train_file, ast.ClassDef, cls_name)
    ns = _their_namespace(device)
    exec(compile(src, str(REPO / train_file), "exec"), ns)
    return ns[cls_name], src

def load_their_attacks(variant, device, criterion):
    """exec their verbatim fgsm_attack / pgd_attack from their *test* file.
    They close over module globals `criterion` and `device`, which we provide identically."""
    _, test_file, _ = VARIANTS[variant]
    ns = _their_namespace(device, criterion)
    fns = {}
    for fname in ("fgsm_attack", "pgd_attack"):
        src = _extract(test_file, ast.FunctionDef, fname)
        exec(compile(src, str(REPO / test_file), "exec"), ns)
        fns[fname] = ns[fname]
    return fns["fgsm_attack"], fns["pgd_attack"]

# ---------- data: exactly their transforms; root points at the shared paper/data ----------
def their_loaders(batch_size=128, train=True, smoke_n=0):
    """Their preprocessing verbatim: ToTensor + Normalize((0.5,)*3,(0.5,)*3), bs=128,
    shuffle train / no-shuffle test. smoke_n>0 subsets both splits (CPU smoke only)."""
    import torchvision, torchvision.transforms as transforms
    from torch.utils.data import DataLoader, Subset
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])
    te = torchvision.datasets.CIFAR10(root=str(DATADIR), train=False, transform=transform, download=True)
    tr = torchvision.datasets.CIFAR10(root=str(DATADIR), train=True, transform=transform, download=True) if train else None
    if smoke_n:
        te = Subset(te, range(min(smoke_n, len(te))))
        tr = Subset(tr, range(min(smoke_n, len(tr)))) if tr else None
    tr_ld = DataLoader(tr, batch_size=batch_size, shuffle=True) if tr else None
    te_ld = DataLoader(te, batch_size=batch_size, shuffle=False)
    return tr_ld, te_ld

def pixel_testset(n=None):
    """[0,1] pixel-space test tensors (no normalization) for AutoAttack / reference PGD."""
    import torchvision, torchvision.transforms as transforms
    te = torchvision.datasets.CIFAR10(root=str(DATADIR), train=False,
                                      transform=transforms.ToTensor(), download=True)
    n = len(te) if n is None else min(n, len(te))
    X = torch.stack([te[i][0] for i in range(n)])
    y = torch.tensor([te[i][1] for i in range(n)])
    return X, y

class PixelSpaceModel(nn.Module):
    """[0,1] pixel input -> their Normalize((0.5),(0.5)) -> their model. Output = raw logits
    (their forward ends in nn.Linear; verified logits-only, as AutoAttack requires)."""
    def __init__(self, model):
        super().__init__()
        self.model = model
    def forward(self, x):
        return self.model((x - 0.5) / 0.5)

def repo_sha():
    try:
        import subprocess
        return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"
