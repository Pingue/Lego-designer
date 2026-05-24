import asyncio
import json
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ── startup: load model once ──────────────────────────────────────────────────

_model = None
_class_names: list[str] = []
_device = "cpu"

# In-memory inventory: list of {"label": str, "confidence": float}
_inventory: list[dict] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model, _class_names
    try:
        from classifier.model import load_model
        _model, _class_names = load_model(device=_device)
        print(f"[classifier] Loaded model with {len(_class_names)} classes", flush=True)
    except RuntimeError as e:
        print(f"[classifier] WARNING: {e}", file=sys.stderr, flush=True)
        print("[classifier] The /classify endpoint will return errors until the model is trained.", file=sys.stderr)
    yield


app = FastAPI(title="Lego Classifier API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── schemas ───────────────────────────────────────────────────────────────────

class ClassifyRequest(BaseModel):
    image: str  # base64-encoded JPEG


class AddPieceRequest(BaseModel):
    label: str
    confidence: float


class BuildPlanRequest(BaseModel):
    prompt: str


# ── routes ────────────────────────────────────────────────────────────────────

@app.post("/classify")
def classify(req: ClassifyRequest):
    if _model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Run scripts/download_dataset.py then scripts/train.py.",
        )
    from classifier.inference import classify_image
    result = classify_image(req.image, _model, _class_names, device=_device)
    return result


@app.post("/inventory/add")
def inventory_add(req: AddPieceRequest):
    _inventory.append({"label": req.label, "confidence": req.confidence})
    counts = _counts()
    return {"counts": counts, "total": sum(counts.values())}


@app.get("/inventory")
def inventory_get():
    counts = _counts()
    return {"counts": counts, "total": sum(counts.values())}


@app.delete("/inventory")
def inventory_clear():
    _inventory.clear()
    return {"counts": {}, "total": 0}


@app.get("/build-plan")
def build_plan(prompt: str = ""):
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="prompt query param is required")

    counts = _counts()
    from planner.build_planner import stream_build_plan

    def event_stream():
        for chunk in stream_build_plan(counts, prompt):
            # SSE format: data: <payload>\n\n
            safe = chunk.replace("\n", "\\n")
            yield f"data: {safe}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/classes")
def get_classes():
    return {"classes": _class_names}


# ── helpers ───────────────────────────────────────────────────────────────────

def _counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in _inventory:
        counts[item["label"]] = counts.get(item["label"], 0) + 1
    return counts
