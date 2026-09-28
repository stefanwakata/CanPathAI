"""CSV → PostgreSQL ingestion pipeline (IRCC + seed data).

Idempotent: each run replaces the dataset's rows in a single transaction and
records an IngestionRun audit row. Falls back to bundled seed CSVs when the
remote source is unreachable (useful for local dev and demos).
"""
import io
import logging
from datetime import datetime
from pathlib import Path

import httpx
import pandas as pd
from sqlalchemy import delete

from app.core.config import get_settings
from app.core.db import db_session, get_engine
from app.ingestion.encoding import decode_bytes, sniff_delimiter
from app.ingestion.normalize import NORMALIZERS
from app.ingestion.sources import IRCC_SOURCES, CsvSource
from app.models.tables import (
    Base,
    IngestionRun,
    JobOutlook,
    PrAdmission,
    PrByCitizenship,
    PrByNoc,
    ProcessingTime,
    WageByNoc,
)

logger = logging.getLogger(__name__)

TABLE_MODELS = {
    "pr_admissions": PrAdmission,
    "pr_by_citizenship": PrByCitizenship,
    "pr_by_noc": PrByNoc,
    "wages_by_noc": WageByNoc,
    "job_outlooks": JobOutlook,
    "processing_times": ProcessingTime,
}


def create_tables() -> None:
    Base.metadata.create_all(get_engine())


def fetch_bytes(url: str, timeout: int | None = None) -> bytes:
    timeout = timeout or get_settings().http_timeout_seconds
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        resp = client.get(url, headers={"User-Agent": "CanPathAI/1.0 (open data ingestion)"})
        resp.raise_for_status()
        return resp.content


def read_csv_bytes(raw: bytes) -> pd.DataFrame:
    text = decode_bytes(raw)
    return pd.read_csv(io.StringIO(text), sep=sniff_delimiter(text), dtype=str)


def _load_dataframe(table: str, df: pd.DataFrame, source_label: str) -> int:
    model = TABLE_MODELS[table]
    records = df.to_dict(orient="records")
    with db_session() as session:
        session.execute(delete(model))
        for rec in records:
            clean = {}
            for k, v in rec.items():
                if not isinstance(v, str) and pd.isna(v):
                    clean[k] = None
                elif hasattr(v, "item"):  # numpy scalar → python native
                    clean[k] = v.item()
                else:
                    clean[k] = v
            clean["source"] = source_label
            session.add(model(**clean))
    return len(records)


def _record_run(dataset: str, status: str, rows: int, detail: str = "") -> None:
    with db_session() as session:
        session.add(IngestionRun(
            dataset=dataset, status=status, rows_loaded=rows,
            detail=detail[:2000], started_at=datetime.utcnow(),
        ))


def _seed_path(key: str) -> Path:
    return Path(get_settings().data_seed_dir) / f"{key}.csv"


def ingest_source(source: CsvSource) -> int:
    """Ingest one IRCC CSV source; returns rows loaded."""
    normalize = NORMALIZERS[source.key]
    label = f"{source.description_en} — {source.landing_page}"
    try:
        raw = fetch_bytes(source.url)
        df = normalize(read_csv_bytes(raw))
        origin = source.url
    except Exception as exc:  # network or schema failure → seed fallback
        if not get_settings().ingest_use_seed_fallback or not _seed_path(source.key).exists():
            _record_run(source.key, "failed", 0, str(exc))
            raise
        logger.warning("Remote fetch failed for %s (%s); using seed data", source.key, exc)
        df = normalize(pd.read_csv(_seed_path(source.key), dtype=str))
        origin = f"seed:{_seed_path(source.key).name}"
    if df.empty:
        _record_run(source.key, "failed", 0, f"empty dataframe from {origin}")
        raise ValueError(f"No rows parsed for {source.key} from {origin}")
    rows = _load_dataframe(source.table, df, label)
    _record_run(source.key, "success", rows, origin)
    logger.info("Loaded %d rows into %s from %s", rows, source.table, origin)
    return rows


def ingest_seed_only_tables() -> None:
    """Tables sourced from curated seeds (wages, outlooks, processing times).

    In production these are refreshed by the StatCan pipeline (see statcan.py)
    and the weekly GitHub Action; the seed guarantees a working local product.
    """
    seeds = {
        "wages_by_noc": "StatCan 14-10-0417 / Job Bank wages — https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410041701",
        "job_outlooks": "Job Bank Canada 3-year outlooks — https://www.jobbank.gc.ca/trend-analysis",
        "processing_times": "IRCC processing times — https://www.canada.ca/en/immigration-refugees-citizenship/services/application/check-processing-times.html",
    }
    for table, label in seeds.items():
        path = _seed_path(table)
        if not path.exists():
            logger.warning("Seed missing for %s; skipping", table)
            _record_run(table, "skipped", 0, "seed missing")
            continue
        df = pd.read_csv(path)
        rows = _load_dataframe(table, df, label)
        _record_run(table, "success", rows, f"seed:{path.name}")
        logger.info("Loaded %d rows into %s (seed)", rows, table)


def run_csv_ingestion() -> dict[str, int]:
    create_tables()
    results: dict[str, int] = {}
    for source in IRCC_SOURCES:
        try:
            results[source.key] = ingest_source(source)
        except Exception as exc:
            logger.error("Ingestion failed for %s: %s", source.key, exc)
            results[source.key] = 0
    ingest_seed_only_tables()
    return results
