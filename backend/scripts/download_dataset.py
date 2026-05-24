"""
Download the LEGO Brick Images dataset from Kaggle and organise it into
the ImageFolder structure expected by train.py.

Dataset: joosthazelzet/lego-brick-images  (~40k images, 50 brick types)

Authentication — one of:
  A) Place kaggle.json at ~/.kaggle/kaggle.json
       {"username": "your_username", "key": "your_api_key"}
  B) Set env vars: KAGGLE_USERNAME and KAGGLE_KEY

Get your API key at: https://www.kaggle.com/settings → "API" → "Create New Token"

Output:
  data/lego_bricks/
    train/<class_name>/*.png
    valid/<class_name>/*.png
    test/<class_name>/*.png
"""

import random
import re
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env")
DATA_DIR = ROOT / "data"
OUT_DIR = DATA_DIR / "lego_bricks"
RAW_DIR = DATA_DIR / "raw"

KAGGLE_DATASET = "joosthazelzet/lego-brick-images"
TRAIN_RATIO = 0.80
VALID_RATIO = 0.15
# test gets the remainder (~0.05)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
RANDOM_SEED = 42


# ── helpers ───────────────────────────────────────────────────────────────────

def _class_from_filename(stem: str) -> str:
    """'3001 Brick 2x4_0123' → '3001 Brick 2x4'"""
    m = re.match(r"^(.*?)[\s_]\d{1,5}$", stem)
    return m.group(1).strip() if m else stem.strip()


def _find_classes(root: Path) -> dict[str, list[Path]]:
    """
    Returns {class_name: [image_path, ...]} by searching root.
    Tries class-subdirectory layout first; falls back to filename parsing.
    """
    classes: dict[str, list[Path]] = {}

    # Pass 1: directories that directly contain images → use dir name as class
    for d in sorted(root.rglob("*")):
        if not d.is_dir():
            continue
        images = [f for f in d.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTS]
        if len(images) >= 5:
            classes[d.name] = sorted(images)

    if classes:
        return classes

    # Pass 2: flat folder — extract class from filename
    for img in sorted(root.rglob("*")):
        if img.is_file() and img.suffix.lower() in IMAGE_EXTS:
            cls = _class_from_filename(img.stem)
            classes.setdefault(cls, []).append(img)

    return classes


def _split_and_copy(classes: dict[str, list[Path]], out_dir: Path) -> None:
    random.seed(RANDOM_SEED)

    for split in ("train", "valid", "test"):
        (out_dir / split).mkdir(parents=True, exist_ok=True)

    total = {"train": 0, "valid": 0, "test": 0}

    for cls_name, images in sorted(classes.items()):
        imgs = images.copy()
        random.shuffle(imgs)
        n = len(imgs)
        n_train = int(n * TRAIN_RATIO)
        n_valid = int(n * VALID_RATIO)

        buckets = {
            "train": imgs[:n_train],
            "valid": imgs[n_train : n_train + n_valid],
            "test":  imgs[n_train + n_valid :],
        }

        for split, bucket in buckets.items():
            if not bucket:
                continue
            dest = out_dir / split / cls_name
            dest.mkdir(parents=True, exist_ok=True)
            for src in bucket:
                shutil.copy2(src, dest / src.name)
            total[split] += len(bucket)

    print(f"\nDataset written to {out_dir}")
    for split, count in total.items():
        print(f"  {split:5s}  {count:5d} images  ({len(classes)} classes)")


# ── download ──────────────────────────────────────────────────────────────────

def download_kaggle() -> None:
    try:
        import kaggle  # noqa: F401 — triggers authentication check
    except ImportError:
        print("kaggle package not installed. Run: pip install kaggle")
        sys.exit(1)

    from kaggle.api.kaggle_api_extended import KaggleApiExtended
    api = KaggleApiExtended()
    try:
        api.authenticate()
    except Exception as e:
        print(f"Kaggle authentication failed: {e}")
        print()
        print("To authenticate, either:")
        print("  A) Download kaggle.json from https://www.kaggle.com/settings")
        print("     and place it at ~/.kaggle/kaggle.json")
        print("  B) Set environment variables:")
        print("       export KAGGLE_USERNAME=your_username")
        print("       export KAGGLE_KEY=your_api_key")
        sys.exit(1)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {KAGGLE_DATASET} → {RAW_DIR} ...")
    api.dataset_download_files(KAGGLE_DATASET, path=str(RAW_DIR), unzip=True, quiet=False)
    print("Download complete.\n")


def check_existing() -> bool:
    train_dir = OUT_DIR / "train"
    if train_dir.exists():
        classes = [d for d in train_dir.iterdir() if d.is_dir()]
        if classes:
            print(f"Dataset already present: {len(classes)} classes at {train_dir}")
            return True
    return False


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if check_existing():
        print("Skipping download. Delete data/lego_bricks/ to re-download.")
        sys.exit(0)

    download_kaggle()

    print("Scanning downloaded files ...")
    classes = _find_classes(RAW_DIR)

    if not classes:
        print(f"No images found under {RAW_DIR}. Check the download completed correctly.")
        sys.exit(1)

    print(f"Found {len(classes)} classes, {sum(len(v) for v in classes.values())} images total.")
    _split_and_copy(classes, OUT_DIR)
