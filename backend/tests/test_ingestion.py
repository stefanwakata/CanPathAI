"""Ingestion integration tests (CI/Docker): seed fallback → SQLite, RAG chunk upsert."""
import os
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.gettempdir()}/canpath_ing_test.db")
os.environ["DATA_SEED_DIR"] = str(Path(__file__).resolve().parents[1] / "data" / "seed")
os.environ["INGEST_USE_SEED_FALLBACK"] = "true"

from sqlalchemy import text as sa_text  # noqa: E402

from app.core.db import db_session, reset_engine  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def fresh_db():
    reset_engine()
    yield


def test_seed_fallback_loads_all_tables(monkeypatch):
    """Force network failure → pipeline must fall back to seeds and load rows."""
    import app.ingestion.csv_pipeline as cp

    def boom(url, timeout=None):
        raise ConnectionError("network disabled in tests")

    monkeypatch.setattr(cp, "fetch_bytes", boom)
    results = cp.run_csv_ingestion()
    assert all(v > 0 for v in results.values()), results

    with db_session() as s:
        n_adm = s.execute(sa_text("SELECT COUNT(*) FROM pr_admissions")).scalar()
        n_wage = s.execute(sa_text("SELECT COUNT(*) FROM wages_by_noc")).scalar()
        n_pt = s.execute(sa_text("SELECT COUNT(*) FROM processing_times")).scalar()
    assert n_adm > 1000 and n_wage > 50 and n_pt > 5

    # audit rows recorded
    with db_session() as s:
        statuses = [r[0] for r in s.execute(
            sa_text("SELECT DISTINCT status FROM ingestion_runs")).fetchall()]
    assert "success" in statuses


def test_ircc_binary_csv_roundtrip():
    """Simulate IRCC's UTF-16 binary CSV serving."""
    from app.ingestion.csv_pipeline import read_csv_bytes
    from app.ingestion.normalize import normalize_pr_by_citizenship

    csv_text = "EN_YEAR,EN_MONTH,EN_COUNTRY_OF_CITIZENSHIP,TOTAL\n2025,7,India,8 900\n2025,7,Total,8900\n"
    df = read_csv_bytes(csv_text.encode("utf-16"))
    out = normalize_pr_by_citizenship(df)
    assert len(out) == 1
    assert out.iloc[0]["admissions"] == 8900


def test_rag_upsert_idempotent(tmp_path):
    """Chroma upsert must replace, not duplicate, on re-ingestion."""
    chromadb = pytest.importorskip("chromadb")
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

    client = chromadb.PersistentClient(path=str(tmp_path))
    col = client.get_or_create_collection("t", embedding_function=DefaultEmbeddingFunction())

    from app.ingestion.rag_pipeline import upsert_document

    text = "PGWP eligibility requires study at a DLI. " * 40
    n1 = upsert_document(col, key="doc1", text=text, title="PGWP", url="https://x")
    n2 = upsert_document(col, key="doc1", text=text, title="PGWP", url="https://x")
    assert n1 == n2
    assert col.count() == n1  # no duplicates


def test_html_to_text_strips_chrome():
    from app.ingestion.rag_pipeline import html_to_text

    html = """<html><head><script>x()</script></head><body>
    <nav>menu</nav><main><h1>PGWP</h1><p>Eligibility rules.</p></main>
    <footer>foot</footer></body></html>"""
    text = html_to_text(html)
    assert "Eligibility rules." in text
    assert "menu" not in text and "x()" not in text
