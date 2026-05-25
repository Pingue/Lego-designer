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
import zipfile
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env")

# Credentials are read from this gitignored file (or KAGGLE_USERNAME/KAGGLE_KEY).
KAGGLE_JSON = ROOT / "kaggle.json"

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


def _unzip_with_progress(zip_path: Path, dest: Path) -> None:
    from tqdm import tqdm
    with zipfile.ZipFile(zip_path) as zf:
        members = zf.infolist()
        with tqdm(total=len(members), desc="Extracting", unit="files", dynamic_ncols=True) as bar:
            for member in members:
                zf.extract(member, dest)
                bar.update(1)


def _split_and_copy(classes: dict[str, list[Path]], out_dir: Path) -> None:
    from tqdm import tqdm
    random.seed(RANDOM_SEED)

    for split in ("train", "valid", "test"):
        (out_dir / split).mkdir(parents=True, exist_ok=True)

    total = {"train": 0, "valid": 0, "test": 0}

    for cls_name, images in tqdm(sorted(classes.items()), desc="Organising", unit="class", dynamic_ncols=True):
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


def _read_credentials() -> tuple[str | None, str | None]:
    import json
    for path in (KAGGLE_JSON, Path.home() / ".kaggle" / "kaggle.json"):
        if path.exists():
            try:
                data = json.loads(path.read_text())
                if data.get("username") and data.get("key"):
                    return data["username"], data["key"]
            except (json.JSONDecodeError, OSError):
                pass
    user = os.environ.get("KAGGLE_USERNAME")
    key = os.environ.get("KAGGLE_KEY")
    if user and key:
        return user, key
    return None, None


def download_kaggle() -> None:
    """
    Download directly over HTTP with requests + tqdm.

    We bypass kaggle.api.dataset_download_files() because some kaggle
    library versions (1.7.x) crash with
        TypeError: call() got an unexpected keyword argument 'headers'
    The Kaggle API supports HTTP Basic auth (username + key/token), which
    is all we need, and a Range header lets us resume a partial download.
    """
    import requests
    from tqdm import tqdm

    username, key = _read_credentials()
    if not (username and key):
        _print_credentials_help()
        sys.exit(1)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = RAW_DIR / "lego-brick-images.zip"
    url = f"https://www.kaggle.com/api/v1/datasets/download/{KAGGLE_DATASET}"

    resume = zip_path.stat().st_size if zip_path.exists() else 0
    headers = {"Range": f"bytes={resume}-"} if resume else {}

    print(f"Downloading {KAGGLE_DATASET} ...")
    with requests.get(url, auth=(username, key), headers=headers,
                      stream=True, allow_redirects=True, timeout=60) as r:
        if r.status_code == 416:  # range not satisfiable → already complete
            print("Already fully downloaded.")
        else:
            if resume and r.status_code == 200:
                resume = 0  # server ignored Range; restart from scratch
            r.raise_for_status()

            total = int(r.headers.get("content-length", 0)) + resume
            mode = "ab" if resume else "wb"
            with open(zip_path, mode) as f, tqdm(
                total=total or None, initial=resume, unit="B", unit_scale=True,
                desc="Downloading", dynamic_ncols=True,
            ) as bar:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))

    print(f"\nUnzipping {zip_path.name} ...")
    _unzip_with_progress(zip_path, RAW_DIR)
    zip_path.unlink()
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
