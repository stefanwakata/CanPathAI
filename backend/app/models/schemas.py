"""Pydantic request/response schemas for the API."""
from typing import Any, Literal

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    noc_code: str | None = Field(None, description="NOC 2021 code, e.g. '21231'")
    occupation: str | None = Field(None, description="Free-text occupation")
    province: str | None = Field(None, description="Target province, e.g. 'Ontario'")
    country_of_citizenship: str | None = None
    status: str | None = Field(None, description="e.g. 'PGWP', 'PR applicant', 'study permit'")
    years_experience: int | None = None
    language: Literal["fr", "en"] | None = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None
    language: Literal["fr", "en"] | None = None
    profile: UserProfile | None = None


class Citation(BaseModel):
    label: str
    source: str
    url: str | None = None


class Visualization(BaseModel):
    """A Plotly figure spec (JSON-serialized `data` and `layout`)."""

    title: str
    figure: dict[str, Any]


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    language: str
    citations: list[Citation] = []
    visualizations: list[Visualization] = []


class ProfileResponse(BaseModel):
    session_id: str
    profile: UserProfile


class RagasMetric(BaseModel):
    name: str
    value: float


class StatsResponse(BaseModel):
    ragas: list[RagasMetric] = []
    evaluated_at: str | None = None
    n_questions: int = 0
    ingestion: list[dict[str, Any]] = []


class HealthResponse(BaseModel):
    status: str
    version: str
    db_ok: bool
    chroma_ok: bool
