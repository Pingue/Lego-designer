"""
Download the LEGO Brick Images dataset from Kaggle and organise it into
the ImageFolder structure expected by train.py.

Dataset: joosthazelzet/lego-brick-images  (~40k images, 50 brick types)

Authentication:
  Create a kaggle.json file at the project root (gitignored):
      {"username": "your_username", "key": "your_token"}
  Copy the template to get started:
      cp kaggle.json.example kaggle.json

Get your token at: https://www.kaggle.com/settings → "API"

Output:
  data/lego_bricks/
    train/<class_name>/*.png
    valid/<class_name>/*.png
    test/<class_name>/*.png
"""

import os
import random
import re
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env")

# Point the kaggle library at our local, gitignored kaggle.json.
# This must happen before `import kaggle`, which authenticates on import.
KAGGLE_JSON = ROOT / "kaggle.json"
if KAGGLE_JSON.exists():
    os.environ["KAGGLE_CONFIG_DIR"] = str(ROOT)
    try:
        os.chmod(KAGGLE_JSON, 0o600)  # kaggle warns about world-readable creds
    except OSError:
        pass

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

def _print_credentials_help() -> None:
    print("No Kaggle credentials found.\n")
    print("Create a kaggle.json file at the project root:")
    print(f"  cp {ROOT / 'kaggle.json.example'} {KAGGLE_JSON}")
    print("Then edit it with your details from https://www.kaggle.com/settings → API:")
    print('  {"username": "your_username", "key": "your_token"}')


def download_kaggle() -> None:
    has_creds = (
        KAGGLE_JSON.exists()
        or (os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"))
        or os.environ.get("KAGGLE_API_TOKEN")
    )
    if not has_creds:
        _print_credentials_help()
        sys.exit(1)

    try:
        import kaggle  # authenticates on import using KAGGLE_CONFIG_DIR / env vars
    except ImportError:
        print("kaggle package not installed. Run: pip install -r requirements.txt")
        sys.exit(1)
    except OSError as e:
        print(f"Kaggle authentication failed: {e}\n")
        _print_credentials_help()
        sys.exit(1)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {KAGGLE_DATASET} -> {RAW_DIR} ...")
    kaggle.api.dataset_download_files(KAGGLE_DATASET, path=str(RAW_DIR), unzip=True, quiet=False)
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
