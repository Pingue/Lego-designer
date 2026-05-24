"""
Download the Lego brick classification dataset.

Option A (recommended): Roboflow dataset — requires a free API key.
  Set ROBOFLOW_API_KEY in your environment or .env file.

Option B: Manual — place an ImageFolder-compatible dataset at:
  data/lego_bricks/
    train/<class_name>/*.jpg
    valid/<class_name>/*.jpg
    test/<class_name>/*.jpg   (optional)
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "data"

ROBOFLOW_WORKSPACE = "roboflow-universe-projects"
ROBOFLOW_PROJECT = "lego-brick-classification"
ROBOFLOW_VERSION = 1


def download_roboflow():
    api_key = os.environ.get("ROBOFLOW_API_KEY", "").strip()
    if not api_key:
        print("ROBOFLOW_API_KEY not set.")
        print("Get a free key at https://roboflow.com and set it:")
        print("  export ROBOFLOW_API_KEY=your_key_here")
        print()
        print("Or place your own dataset manually at:")
        print("  data/lego_bricks/train/<class_name>/*.jpg")
        print("  data/lego_bricks/valid/<class_name>/*.jpg")
        sys.exit(1)

    try:
        from roboflow import Roboflow
    except ImportError:
        print("roboflow not installed. Run: pip install roboflow")
        sys.exit(1)

    print(f"Downloading dataset to {DATA_DIR} ...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    rf = Roboflow(api_key=api_key)
    project = rf.workspace(ROBOFLOW_WORKSPACE).project(ROBOFLOW_PROJECT)
    version = project.version(ROBOFLOW_VERSION)
    dataset = version.download("folder", location=str(DATA_DIR / "lego_bricks"))
    print(f"Dataset downloaded to: {dataset.location}")


def check_manual():
    train_dir = DATA_DIR / "lego_bricks" / "train"
    if train_dir.exists():
        classes = [d.name for d in train_dir.iterdir() if d.is_dir()]
        if classes:
            print(f"Found existing dataset with {len(classes)} classes at {train_dir}")
            return True
    return False


if __name__ == "__main__":
    if check_manual():
        print("Dataset already present. Skipping download.")
        sys.exit(0)
    download_roboflow()
