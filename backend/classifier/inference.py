from __future__ import annotations

import base64
import io

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])


def _decode_image(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def classify_image(
    image_data: str | bytes,
    model: torch.nn.Module,
    class_names: list[str],
    device: str = "cpu",
) -> dict:
    """
    image_data: raw bytes or base64-encoded JPEG string
    Returns {"label": str, "confidence": float, "top3": [{"label": str, "confidence": float}]}
    """
    if isinstance(image_data, str):
        image_bytes = base64.b64decode(image_data)
    else:
        image_bytes = image_data

    image = _decode_image(image_bytes)
    tensor = _transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(tensor)
        probs = F.softmax(logits, dim=1)[0]

    top3_vals, top3_idx = torch.topk(probs, min(3, len(class_names)))
    top3 = [
        {"label": class_names[i.item()], "confidence": round(v.item(), 4)}
        for v, i in zip(top3_vals, top3_idx)
    ]

    return {
        "label": top3[0]["label"],
        "confidence": top3[0]["confidence"],
        "top3": top3,
    }
