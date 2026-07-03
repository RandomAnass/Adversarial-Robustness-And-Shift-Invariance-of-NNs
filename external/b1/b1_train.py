#!/usr/bin/env python3
"""
B1 training: their 10-layer P4 (C4 rotation-equivariant) CIFAR-10 model, THEIR recipe verbatim.

Model class + recipe come from external/role_of_equivariance/cifar10/cascadedGCNN10layer_cifar10.py
(class extracted verbatim via AST, see b1_common.py). Recipe replicated line-for-line:
  ToTensor + Normalize((0.5,)*3,(0.5,)*3) (NO augmentation), DataLoader bs=128 shuffle,
  Adam lr=1e-3, StepLR(step_size=50, gamma=0.1), CrossEntropyLoss, 200 epochs,
  standard train loop (zero_grad -> backward -> step), scheduler.step() per epoch,
  final-epoch state_dict saved (they keep the LAST model, no early stopping / model selection),
  then clean test accuracy.

Additions that do NOT alter the recipe (bookkeeping only, each documented):
  --seed N     : torch/numpy seeding for reproducibility (their code sets NO seed at all)
  epoch log    : loss per epoch to a JSONL file (they print to stdout only)
  resume       : optional periodic snapshot (last epoch state) so a killed run can resume;
                 optimizer+scheduler state included, so the trajectory is unchanged
  --smoke      : CPU plumbing test (tiny subset, 1 epoch) -- never used for the real run

Usage (real run, on a free GPU):
  CUDA_VISIBLE_DEVICES=0 e2cnn_env/bin/python b1_train.py --variant cascaded --seed 0
Smoke (CPU only):
  CUDA_VISIBLE_DEVICES="" e2cnn_env/bin/python b1_train.py --smoke
"""
import argparse, json, os, time, numpy as np, torch, torch.nn as nn
from b1_common import (VARIANTS, RESDIR, load_their_model_class, their_loaders, repo_sha)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="cascaded", choices=list(VARIANTS))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=200)        # theirs: 200
    ap.add_argument("--snapshot_every", type=int, default=25)
    ap.add_argument("--smoke", action="store_true", help="CPU plumbing test: 512 imgs, 1 epoch")
    a = ap.parse_args()

    os.makedirs(RESDIR, exist_ok=True)
    tag = f"{a.variant}_s{a.seed}" + ("_smoke" if a.smoke else "")
    ckpt_final = RESDIR / f"{tag}.pth"
    snap = RESDIR / f"{tag}.snapshot.pt"
    log_path = RESDIR / f"{tag}_train.jsonl"
    if ckpt_final.exists():
        print(f"[b1_train] {ckpt_final} already exists -- nothing to do", flush=True)
        return

    # their code: device = cuda if available else cpu
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(a.seed); np.random.seed(a.seed)          # addition: reproducibility only

    Model, cls_src = load_their_model_class(a.variant, device)
    epochs = 1 if a.smoke else a.epochs
    train_loader, test_loader = their_loaders(batch_size=128, smoke_n=512 if a.smoke else 0)

    # --- their exact setup ---
    model = Model().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=50, gamma=0.1)

    start_ep = 0
    if snap.exists():
        st = torch.load(snap, map_location=device)
        model.load_state_dict(st["model"]); optimizer.load_state_dict(st["opt"])
        scheduler.load_state_dict(st["sched"]); start_ep = st["epoch"] + 1
        print(f"[b1_train] resumed from {snap} at epoch {start_ep}", flush=True)

    print(f"[b1_train] {tag}: {sum(p.numel() for p in model.parameters())} params, "
          f"device={device}, epochs={epochs}", flush=True)
    logf = open(log_path, "a")
    t0 = time.time()
    # --- their exact training loop ---
    for epoch in range(start_ep, epochs):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        scheduler.step()
        rec = {"epoch": epoch + 1, "loss": running_loss / len(train_loader),
               "lr": optimizer.param_groups[0]["lr"], "t": round(time.time() - t0, 1)}
        print(f"Epoch [{epoch + 1}/{epochs}], Loss: {rec['loss']:.4f}", flush=True)
        logf.write(json.dumps(rec) + "\n"); logf.flush()
        if (epoch + 1) % a.snapshot_every == 0 and epoch + 1 < epochs:
            torch.save({"model": model.state_dict(), "opt": optimizer.state_dict(),
                        "sched": scheduler.state_dict(), "epoch": epoch}, snap)

    # --- their save: final-epoch state_dict ---
    torch.save(model.state_dict(), ckpt_final)
    if snap.exists():
        os.remove(snap)

    # --- their clean-test evaluation ---
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            _, predicted = torch.max(model(images), 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    clean = 100 * correct / total

    meta = {"tag": tag, "variant": a.variant, "class": VARIANTS[a.variant][2],
            "seed": a.seed, "epochs": epochs, "smoke": a.smoke,
            "clean_acc_their_eval": clean, "wall_s": time.time() - t0,
            "recipe": "Adam lr=1e-3, StepLR(50,0.1), bs=128, no augmentation, "
                      "Normalize(0.5,0.5), CE, final-epoch checkpoint (theirs verbatim)",
            "their_repo_sha": repo_sha(), "torch": torch.__version__,
            "model_class_source_sha256": __import__("hashlib").sha256(cls_src.encode()).hexdigest()}
    json.dump(meta, open(RESDIR / f"{tag}_train_meta.json", "w"), indent=1)
    print(f"[b1_train] DONE {tag}: clean={clean:.2f}%  ckpt={ckpt_final}  "
          f"({meta['wall_s']/60:.1f} min)", flush=True)

if __name__ == "__main__":
    main()
