"""CanPath AI — FastAPI application entrypoint."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="CanPath AI",
    description=(
        "Canadian Immigration & Labour Market Agent — crosses IRCC open data with "
        "StatCan/Job Bank labour statistics. Bilingual FR/EN."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.on_event("startup")
def _ensure_tables() -> None:
    """Create missing tables (idempotent) so profile persistence works
    even before the first ingestion run."""
    try:
        from app.core.db import get_engine
        from app.models.tables import Base

        Base.metadata.create_all(get_engine())
    except Exception as exc:  # DB not up yet: routes will surface real errors
        logging.getLogger(__name__).warning("Startup table check failed: %s", exc)


@app.get("/")
def root() -> dict:
    return {"service": "CanPath AI", "docs": "/docs", "api": "/api"}
