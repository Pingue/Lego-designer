import json
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models
from torchvision.models import MobileNet_V3_Small_Weights

MODELS_DIR = Path(__file__).parent.parent / "models"
WEIGHTS_PATH = MODELS_DIR / "lego_classifier.pt"
CLASSES_PATH = MODELS_DIR / "classes.json"


def build_model(num_classes: int) -> nn.Module:
    model = models.mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model


def load_model(device: str = "cpu") -> tuple[nn.Module, list[str]]:
    if not WEIGHTS_PATH.exists():
        raise RuntimeError(
            f"Model weights not found at {WEIGHTS_PATH}.\n"
            "Run: python scripts/download_dataset.py && python scripts/train.py"
        )
    if not CLASSES_PATH.exists():
        raise RuntimeError(
            f"Class names not found at {CLASSES_PATH}.\n"
            "Re-run: python scripts/train.py"
        )

    with open(CLASSES_PATH) as f:
        class_names: list[str] = json.load(f)

    model = build_model(len(class_names))
    state = torch.load(WEIGHTS_PATH, map_location=device, weights_only=True)
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model, class_names
