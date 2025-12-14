from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Any

from app.core.config import settings
from app.models.db import init_db, SessionLocal, Feedback
from app.rag.pipelines import get_pipelines, PipelineId


app = FastAPI(title="OSS RAG Lab")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3)
    pipeline_id: PipelineId = "hybrid"


class AskResponse(BaseModel):
    answer: str
    context: List[str]
    latency_ms: float
    pipeline_id: PipelineId


class FeedbackRequest(BaseModel):
    question: str
    answer: str
    pipeline_id: PipelineId
    thumbs_up: bool
    latency_ms: float | None = None


class MetricsResponse(BaseModel):
    per_pipeline: Dict[str, Dict[str, float]]


@app.on_event("startup")
def on_startup():
    init_db()
    try:
        get_pipelines()
    except Exception as e:
        print(f"[startup] Warning initialising pipelines: {e}")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "model_name": settings.ollama_model,
        },
    )


@app.post("/api/ask", response_model=AskResponse)
async def ask(payload: AskRequest):
    pipelines = get_pipelines()
    result = pipelines.answer(payload.question, payload.pipeline_id)
    return AskResponse(**result)


@app.post("/api/feedback")
async def feedback(payload: FeedbackRequest, db=Depends(get_db)):
    fb = Feedback(
        question=payload.question,
        answer=payload.answer,
        pipeline_id=payload.pipeline_id,
        thumbs_up=payload.thumbs_up,
        latency_ms=payload.latency_ms,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return {"status": "ok", "id": fb.id}


@app.get("/api/metrics", response_model=MetricsResponse)
async def metrics(db=Depends(get_db)):
    rows = db.query(Feedback).all()
    stats: Dict[str, Dict[str, float]] = {}
    counts: Dict[str, int] = {}
    positives: Dict[str, int] = {}

    for r in rows:
        pid = r.pipeline_id
        counts[pid] = counts.get(pid, 0) + 1
        if r.thumbs_up:
            positives[pid] = positives.get(pid, 0) + 1

    for pid, c in counts.items():
        pos = positives.get(pid, 0)
        stats[pid] = {
            "total": float(c),
            "positive": float(pos),
            "positive_rate": float(pos) / c if c > 0 else 0.0,
        }

    return MetricsResponse(per_pipeline=stats)
