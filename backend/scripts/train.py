"""
Train MobileNetV3-Small on the Lego brick dataset.

Usage:
  cd backend
  python scripts/train.py

Expects dataset at:
  ../data/lego_bricks/train/<class_name>/*.jpg
  ../data/lego_bricks/valid/<class_name>/*.jpg

Saves:
  models/lego_classifier.pt   — best checkpoint (state dict)
  models/classes.json          — list of class names
"""

import json
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from tqdm import tqdm

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT.parent / "data" / "lego_bricks"
MODELS_DIR = ROOT / "models"
WEIGHTS_PATH = MODELS_DIR / "lego_classifier.pt"
CLASSES_PATH = MODELS_DIR / "classes.json"

# ── hyper-parameters ──────────────────────────────────────────────────────────
EPOCHS = 20
BATCH_SIZE = 32
LR = 1e-3
WEIGHT_DECAY = 1e-4
NUM_WORKERS = 2
IMAGE_SIZE = 224

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_transforms(train: bool):
    if train:
        return transforms.Compose([
            transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.RandomRotation(20),
            transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def main():
    train_dir = DATA_DIR / "train"
    valid_dir = DATA_DIR / "valid"

    if not train_dir.exists():
        print(f"Training data not found at {train_dir}")
        print("Run: python scripts/download_dataset.py")
        sys.exit(1)

    train_ds = datasets.ImageFolder(str(train_dir), transform=get_transforms(True))
    valid_ds = datasets.ImageFolder(str(valid_dir), transform=get_transforms(False))

    class_names = train_ds.classes
    num_classes = len(class_names)
    print(f"Classes ({num_classes}): {class_names}")

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                              num_workers=NUM_WORKERS, pin_memory=True)
    valid_loader = DataLoader(valid_ds, batch_size=BATCH_SIZE, shuffle=False,
                              num_workers=NUM_WORKERS, pin_memory=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Training on: {device}")

    sys.path.insert(0, str(ROOT))
    from classifier.model import build_model
    model = build_model(num_classes).to(device)

    # Freeze backbone, only train classifier + last inverted residual block
    for name, param in model.named_parameters():
        if "classifier" not in name and "features.12" not in name and "features.11" not in name:
            param.requires_grad = False

    optimizer = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=LR, weight_decay=WEIGHT_DECAY,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
    criterion = nn.CrossEntropyLoss()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    best_acc = 0.0

    for epoch in range(1, EPOCHS + 1):
        t0 = time.time()

        # ── train ──
        model.train()
        train_loss, train_correct, train_total = 0.0, 0, 0
        train_bar = tqdm(train_loader, desc=f"Epoch {epoch}/{EPOCHS} [train]",
                         unit="batch", dynamic_ncols=True)
        for images, labels in train_bar:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * images.size(0)
            train_correct += (outputs.argmax(1) == labels).sum().item()
            train_total += images.size(0)
            train_bar.set_postfix(loss=f"{train_loss/train_total:.4f}",
                                  acc=f"{train_correct/train_total:.3f}")

        # ── validate ──
        model.eval()
        val_loss, val_correct, val_total = 0.0, 0, 0
        val_bar = tqdm(valid_loader, desc=f"Epoch {epoch}/{EPOCHS} [valid]",
                       unit="batch", dynamic_ncols=True)
        with torch.no_grad():
            for images, labels in val_bar:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                val_correct += (outputs.argmax(1) == labels).sum().item()
                val_total += images.size(0)
                val_bar.set_postfix(loss=f"{val_loss/val_total:.4f}",
                                    acc=f"{val_correct/val_total:.3f}")

        scheduler.step()

        train_acc = train_correct / train_total
        val_acc = val_correct / val_total
        elapsed = time.time() - t0

        print(
            f"Epoch {epoch:2d}/{EPOCHS} | "
            f"train loss {train_loss/train_total:.4f} acc {train_acc:.3f} | "
            f"val loss {val_loss/val_total:.4f} acc {val_acc:.3f} | "
            f"{elapsed:.1f}s"
        )

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), WEIGHTS_PATH)
            print(f"  ✓ Saved best model (val acc {best_acc:.3f})")

    with open(CLASSES_PATH, "w") as f:
        json.dump(class_names, f, indent=2)

    print(f"\nTraining complete. Best val acc: {best_acc:.3f}")
    print(f"Weights: {WEIGHTS_PATH}")
    print(f"Classes: {CLASSES_PATH}")


if __name__ == "__main__":
    main()
