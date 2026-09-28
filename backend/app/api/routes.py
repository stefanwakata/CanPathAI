"""API routes: /chat, /profile, /stats, /health."""
import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from sqlalchemy import text as sa_text

from app.agent.memory import memory_store
from app.core.config import get_settings
from app.core.db import db_session
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ProfileResponse,
    RagasMetric,
    StatsResponse,
    UserProfile,
)

logger = logging.getLogger(__name__)
router = APIRouter()

APP_VERSION = "1.0.0"


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if not get_settings().anthropic_api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY is not configured")
    from app.agent.agent import run_agent  # deferred: heavy imports

    try:
        result = run_agent(
            message=req.message,
            session_id=req.session_id,
            language=req.language,
            profile=req.profile.model_dump(exclude_none=True) if req.profile else None,
        )
    except Exception as exc:
        logger.exception("Agent failure")
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc
    return ChatResponse(**result)


@router.post("/profile", response_model=ProfileResponse)
def set_profile(profile: UserProfile, session_id: str | None = None) -> ProfileResponse:
    sid, _ = memory_store.get_or_create(session_id)
    memory_store.set_profile(sid, profile.model_dump(exclude_none=True))
    return ProfileResponse(session_id=sid, profile=profile)


@router.get("/stats", response_model=StatsResponse)
def stats() -> StatsResponse:
    settings = get_settings()
    ragas_metrics: list[RagasMetric] = []
    evaluated_at = None
    n_questions = 0
    path = Path(settings.ragas_results_path)
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        ragas_metrics = [RagasMetric(name=k, value=v) for k, v in payload.get("metrics", {}).items()]
        evaluated_at = payload.get("evaluated_at")
        n_questions = payload.get("n_questions", 0)

    ingestion: list[dict] = []
    try:
        with db_session() as session:
            rows = session.execute(sa_text(
                "SELECT dataset, status, rows_loaded, started_at FROM ingestion_runs "
                "ORDER BY started_at DESC LIMIT 20"
            )).fetchall()
            ingestion = [
                {"dataset": r[0], "status": r[1], "rows_loaded": r[2], "started_at": str(r[3])}
                for r in rows
            ]
    except Exception as exc:
        logger.warning("Could not read ingestion_runs: %s", exc)

    return StatsResponse(
        ragas=ragas_metrics, evaluated_at=evaluated_at,
        n_questions=n_questions, ingestion=ingestion,
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    db_ok = True
    try:
        with db_session() as session:
            session.execute(sa_text("SELECT 1"))
    except Exception:
        db_ok = False
    chroma_ok = True
    try:
        from app.ingestion.rag_pipeline import get_chroma_collection

        get_chroma_collection().count()
    except Exception:
        chroma_ok = False
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        version=APP_VERSION, db_ok=db_ok, chroma_ok=chroma_ok,
    )
