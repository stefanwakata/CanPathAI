"""StatCan Web Data Service ingestion.

Downloads full-table CSV zips via the WDS REST API, filters to the columns the
product needs, and loads PostgreSQL. Full tables are large (100 MB+), so this
is designed for the weekly GitHub Action, not per-request use.

API: https://www.statcan.gc.ca/en/developers/wds
"""
import io
import logging
import zipfile
from datetime import datetime

import httpx
import pandas as pd
from sqlalchemy import delete

from app.core.config import get_settings
from app.core.db import db_session
from app.ingestion.sources import STATCAN_TABLES, STATCAN_WDS_BASE
from app.models.tables import ImmigrantLabourStat, IngestionRun, LabourForceStat, WageByNoc

logger = logging.getLogger(__name__)

# Keep the SQL store focused: only these LFS characteristics are loaded.
LFS_KEEP = {
    "Employment rate", "Unemployment rate", "Participation rate",
    "Employment", "Unemployment", "Labour force",
}


def _wds_get(path: str) -> dict:
    url = f"{STATCAN_WDS_BASE}/{path}"
    with httpx.Client(timeout=get_settings().http_timeout_seconds, follow_redirects=True) as c:
        resp = c.get(url)
        resp.raise_for_status()
        return resp.json()


def download_full_table(pid: str) -> pd.DataFrame:
    """Download a StatCan full-table CSV (zipped) into a DataFrame."""
    envelope = _wds_get(f"getFullTableDownloadCSV/{pid}/en")
    if envelope.get("status") != "SUCCESS":
        raise RuntimeError(f"WDS error for {pid}: {envelope}")
    zip_url = envelope["object"]
    with httpx.Client(timeout=600, follow_redirects=True) as c:
        resp = c.get(zip_url)
        resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        csv_name = next(n for n in zf.namelist() if n.endswith(".csv") and "MetaData" not in n)
        with zf.open(csv_name) as fh:
            return pd.read_csv(fh, dtype=str, low_memory=False)


def _to_float(v) -> float | None:
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def load_labour_force(df: pd.DataFrame, months_back: int = 36) -> int:
    df = df.rename(columns=str.strip)
    df = df[df["Labour force characteristics"].isin(LFS_KEEP)]
    if "Sex" in df.columns:
        df = df[df["Sex"].fillna("").str.contains("Both", na=False) | (df["Sex"] == "Total - Gender")]
    if "Gender" in df.columns:
        df = df[df["Gender"].fillna("").str.contains("Total", na=False)]
    if "Age group" in df.columns:
        df = df[df["Age group"] == "15 years and over"]
    if "Data type" in df.columns:
        df = df[df["Data type"].fillna("").str.contains("Seasonally adjusted", na=False)]
    df = df.sort_values("REF_DATE")
    cutoff = sorted(df["REF_DATE"].unique())[-months_back:]
    df = df[df["REF_DATE"].isin(cutoff)]

    with db_session() as session:
        session.execute(delete(LabourForceStat))
        n = 0
        for _, r in df.iterrows():
            session.add(LabourForceStat(
                ref_date=r["REF_DATE"], province=r["GEO"],
                characteristic=r["Labour force characteristics"],
                value=_to_float(r["VALUE"]), unit=r.get("UOM"),
            ))
            n += 1
    return n


def load_immigrant_labour(df: pd.DataFrame, months_back: int = 36) -> int:
    df = df.rename(columns=str.strip)
    char_col = next(c for c in df.columns if "characteristics" in c.lower())
    imm_col = next(c for c in df.columns if "immigrant" in c.lower())
    df = df[df[char_col].isin(LFS_KEEP)]
    df = df.sort_values("REF_DATE")
    cutoff = sorted(df["REF_DATE"].unique())[-months_back:]
    df = df[df["REF_DATE"].isin(cutoff)]

    with db_session() as session:
        session.execute(delete(ImmigrantLabourStat))
        n = 0
        for _, r in df.iterrows():
            session.add(ImmigrantLabourStat(
                ref_date=r["REF_DATE"], province=r["GEO"],
                immigrant_status=r[imm_col], characteristic=r[char_col],
                value=_to_float(r["VALUE"]), unit=r.get("UOM"),
            ))
            n += 1
    return n


def load_wages(df: pd.DataFrame) -> int:
    df = df.rename(columns=str.strip)
    noc_col = next(c for c in df.columns if "occupation" in c.lower() or "noc" in c.lower())
    wage_col = next(c for c in df.columns if "wages" in c.lower())
    df = df[df[wage_col].fillna("").str.contains("Average hourly wage", na=False)]
    latest = sorted(df["REF_DATE"].unique())[-1]
    df = df[df["REF_DATE"] == latest]

    import re
    noc_rx = re.compile(r"^(.*?)\s*\[(\d+)\]\s*$")
    with db_session() as session:
        session.execute(delete(WageByNoc))
        n = 0
        for _, r in df.iterrows():
            raw = str(r[noc_col]).strip()
            m = noc_rx.match(raw)
            title, code = (m.group(1), m.group(2)) if m else (raw, "")
            session.add(WageByNoc(
                noc_code=code, noc_title=title, province=r["GEO"],
                wage_median=_to_float(r["VALUE"]),
                reference_year=int(str(latest)[:4]),
            ))
            n += 1
    return n


LOADERS = {
    "labour_force_stats": load_labour_force,
    "immigrant_labour_stats": load_immigrant_labour,
    "wages_by_noc": load_wages,
}


def run_statcan_ingestion() -> dict[str, int]:
    results: dict[str, int] = {}
    for table, meta in STATCAN_TABLES.items():
        try:
            df = download_full_table(meta["pid"])
            rows = LOADERS[table](df)
            results[table] = rows
            status, detail = "success", f"WDS pid={meta['pid']}"
        except Exception as exc:
            logger.error("StatCan ingestion failed for %s: %s", table, exc)
            results[table] = 0
            status, detail = "failed", str(exc)
        with db_session() as session:
            session.add(IngestionRun(
                dataset=f"statcan:{table}", status=status,
                rows_loaded=results[table], detail=detail[:2000],
                started_at=datetime.utcnow(),
            ))
    return results
