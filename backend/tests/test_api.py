"""Integration tests for the FastAPI app (run in CI/Docker with full deps).

Uses SQLite + seed data so no external services are required.
"""
import os
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.gettempdir()}/canpath_test.db")
os.environ.setdefault("ANTHROPIC_API_KEY", "")  # /chat should 503 without a key
os.environ.setdefault("INGEST_USE_SEED_FALLBACK", "true")
os.environ["DATA_SEED_DIR"] = str(Path(__file__).resolve().parents[1] / "data" / "seed")

from fastapi.testclient import TestClient  # noqa: E402

from app.core.db import reset_engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def seed_db():
    reset_engine()
    from app.ingestion.csv_pipeline import create_tables, ingest_seed_only_tables

    create_tables()
    ingest_seed_only_tables()
    yield


client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["service"] == "CanPath AI"


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["db_ok"] is True


def test_profile_roundtrip():
    r = client.post("/api/profile", json={"noc_code": "21232", "province": "Ontario",
                                          "status": "PGWP", "language": "fr"})
    assert r.status_code == 200
    body = r.json()
    assert body["session_id"]
    assert body["profile"]["noc_code"] == "21232"


def test_chat_requires_api_key():
    r = client.post("/api/chat", json={"message": "Bonjour"})
    assert r.status_code == 503


def test_chat_validates_input():
    r = client.post("/api/chat", json={"message": ""})
    assert r.status_code == 422


def test_stats_shape():
    r = client.get("/api/stats")
    assert r.status_code == 200
    body = r.json()
    assert "ragas" in body and "ingestion" in body
    # seed ingestion recorded runs
    assert any(run["status"] == "success" for run in body["ingestion"])


def test_sql_tool_end_to_end():
    """The SQL tool must query seeded tables through the guard."""
    from app.agent.citations import CitationTracker
    from app.agent.tools import make_tools

    tracker = CitationTracker()
    viz: list = []
    sql_tool = make_tools(tracker, viz, chroma_collection=None)[0]
    out = sql_tool.invoke({"query": (
        "SELECT province, wage_median FROM wages_by_noc "
        "WHERE noc_code = '21232' ORDER BY wage_median DESC"
    )})
    assert "Ontario" in out or "Alberta" in out
    assert tracker.refs  # citations registered


def test_viz_tool_end_to_end():
    from app.agent.citations import CitationTracker
    from app.agent.tools import make_tools

    tracker = CitationTracker()
    viz: list = []
    viz_tool = make_tools(tracker, viz, chroma_collection=None)[2]
    out = viz_tool.invoke({
        "kind": "bar",
        "rows_json": '[{"province":"Ontario","admissions":100},{"province":"Quebec","admissions":50}]',
        "x": "province", "y": "admissions", "title": "Test",
    })
    assert "created" in out
    assert len(viz) == 1
    assert viz[0]["figure"]["data"][0]["type"] == "bar"
