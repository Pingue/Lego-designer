# Lego Designer AI

An AI-guided app that classifies Lego pieces from a webcam and generates creative build plans using a local LLM.

## Architecture

```
Browser (React) ──── FastAPI backend ──── MobileNetV3 classifier
                  └──────────────────── Ollama (llama3.2) build planner
```

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.com) installed and running

```bash
ollama pull llama3.2   # ~2 GB download
ollama serve           # start the Ollama server (or it starts automatically)
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Download dataset & train the classifier

The script uses the [LEGO Brick Images](https://www.kaggle.com/datasets/joosthazelzet/lego-brick-images) dataset from Kaggle (~40k images, 50 brick types).

**Get your Kaggle token** at https://www.kaggle.com/settings → *API*.  
Kaggle shows something like `export KAGGLE_API_TOKEN={"username":"...","key":"..."}`.  
Copy the JSON value (the part after `=`) into a `.env` file at the project root:

```bash
cp .env.example .env
# Edit .env and paste your JSON token as the value of KAGGLE_API_TOKEN
```

Then run:

```bash
python scripts/download_dataset.py   # downloads + splits into train/valid/test
python scripts/train.py              # ~20 min CPU / ~3 min GPU
```

Or skip the download and place your own ImageFolder dataset at:
```
data/lego_bricks/
  train/<class_name>/*.jpg
  valid/<class_name>/*.jpg
```

### 4. Start the backend

Make sure the venv is active first (`source backend/.venv/bin/activate`), then:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

---

## Usage

### Part 1 — Classify pieces

1. Click **Start Camera** and grant webcam access
2. Hold a Lego piece in front of the camera
3. Click **Scan Piece** — the piece is added to your inventory
4. Enable **Conveyor Belt** mode for automatic periodic scanning

### Part 2 — Generate a build plan

1. Once you have pieces in inventory, type a goal in the right panel  
   *e.g. "Build the most impressive space station possible"*
2. Click **Generate Plan** (or Ctrl+Enter)
3. Watch the AI stream a step-by-step build plan in real time
4. Once generation finishes, click **Download PDF** to save a Lego-manual-style PDF

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/classify` | Classify a base64 JPEG frame |
| `POST` | `/inventory/add` | Add a piece to inventory |
| `GET` | `/inventory` | Get current piece counts |
| `DELETE` | `/inventory` | Clear inventory |
| `GET` | `/build-plan?prompt=...` | Stream a build plan (SSE) |
| `POST` | `/export-pdf` | Generate a Lego-manual PDF from plan text |
| `GET` | `/classes` | List known piece classes |

---

## Training Details

- **Model**: MobileNetV3-Small (pretrained on ImageNet, fine-tuned on Lego dataset)
- **Frozen layers**: All except last 2 feature blocks + classifier head
- **Optimizer**: AdamW, lr=1e-3, weight_decay=1e-4
- **Scheduler**: CosineAnnealingLR over 20 epochs
- **Augmentations**: RandomResizedCrop, flips, rotation, ColorJitter
- **Output**: `backend/models/lego_classifier.pt` + `backend/models/classes.json`
