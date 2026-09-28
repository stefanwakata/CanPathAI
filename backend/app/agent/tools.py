"""LangChain tools: SQL query, RAG retrieval, visualization.

Each tool registers what it used with the request-scoped CitationTracker so
citations are enforceable downstream.
"""
import json
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy import text as sa_text

from app.agent.citations import CitationTracker
from app.agent.sql_guard import ALLOWED_TABLES, UnsafeSqlError, enforce_limit, validate_sql
from app.agent.viz_spec import build_figure
from app.core.db import db_session

SCHEMA_DOC = """Tables disponibles / available tables:
- pr_admissions(year, month, province, immigration_category, admissions, source) — IRCC PR admissions
- pr_by_citizenship(year, month, country, admissions, source) — IRCC PR by country
- pr_by_noc(year, province, noc_code, noc_title, admissions, source) — IRCC PR by occupation (NOC)
- processing_times(application_type, country_or_region, processing_days, processing_label, as_of_date, source)
- wages_by_noc(noc_code, noc_title, province, wage_low, wage_median, wage_high, reference_year, source)
- labour_force_stats(ref_date 'YYYY-MM', province, characteristic, value, unit, source) — StatCan LFS
- immigrant_labour_stats(ref_date, province, immigrant_status, characteristic, value, unit, source)
- job_outlooks(noc_code, noc_title, province, outlook, outlook_score 1-5, period, source)"""


class SqlInput(BaseModel):
    query: str = Field(..., description="A single SELECT (PostgreSQL dialect). " + SCHEMA_DOC)


class RagInput(BaseModel):
    question: str = Field(..., description="Natural-language question to search policy/report documents for")
    k: int = Field(4, ge=1, le=8, description="Number of passages to retrieve")


class VizInput(BaseModel):
    kind: str = Field(..., description="bar | line | grouped_bar | pie")
    rows_json: str = Field(..., description="JSON array of row objects (typically the SQL tool output)")
    x: str = Field(..., description="Column for the x axis (or pie labels)")
    y: str = Field(..., description="Numeric column for the y axis (or pie values)")
    series: str | None = Field(None, description="Optional column to split into multiple traces")
    title: str = Field("", description="Chart title, in the user's language")


def make_tools(tracker: CitationTracker, viz_sink: list[dict[str, Any]], chroma_collection=None):
    """Build the 3 tools bound to this request's tracker and viz sink."""

    def run_sql(query: str) -> str:
        try:
            clean = enforce_limit(validate_sql(query))
        except UnsafeSqlError as exc:
            return f"SQL rejected: {exc}. Allowed tables: {sorted(ALLOWED_TABLES)}"
        try:
            with db_session() as session:
                result = session.execute(sa_text(clean))
                cols = list(result.keys())
                rows = [dict(zip(cols, r)) for r in result.fetchall()]
        except Exception as exc:
            return f"SQL error: {exc}"
        # Register sources from returned rows
        for src in {str(r.get("source")) for r in rows if r.get("source")}:
            tracker.add(label=src.split("—")[0].strip(), source=src,
                        url=src.split("—")[-1].strip() if "—" in src and "http" in src else None)
        if not rows:
            return "Query returned no rows. Consider relaxing filters (e.g. LIKE '%...%' on names)."
        return json.dumps(rows, ensure_ascii=False, default=str)[:12000]

    def run_rag(question: str, k: int = 4) -> str:
        if chroma_collection is None:
            return "Document store unavailable."
        res = chroma_collection.query(query_texts=[question], n_results=k)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        if not docs:
            return "No relevant passages found."
        parts = []
        for doc, meta in zip(docs, metas):
            title = meta.get("title", "document")
            url = meta.get("url")
            tracker.add(label=title, source=title, url=url)
            parts.append(f"[{title}]({url})\n{doc}")
        return "\n\n---\n\n".join(parts)[:12000]

    def run_viz(kind: str, rows_json: str, x: str, y: str,
                series: str | None = None, title: str = "") -> str:
        try:
            rows = json.loads(rows_json)
            if not isinstance(rows, list):
                raise ValueError("rows_json must be a JSON array")
            fig = build_figure(kind, rows, x=x, y=y, series=series, title=title)
        except Exception as exc:
            return f"Visualization error: {exc}"
        viz_sink.append({"title": title or kind, "figure": fig})
        return f"Chart '{title or kind}' created and attached to the response. Reference it in your answer."

    return [
        StructuredTool.from_function(
            func=run_sql, name="query_database", args_schema=SqlInput,
            description=("Run a read-only SQL SELECT against IRCC immigration and StatCan/Job Bank "
                         "labour-market tables. Use for numbers: admissions, wages, unemployment, "
                         "outlooks, processing times. " + SCHEMA_DOC),
        ),
        StructuredTool.from_function(
            func=run_rag, name="search_documents", args_schema=RagInput,
            description=("Semantic search over policy pages and analytical reports (PGWP eligibility, "
                         "Express Entry, StatCan analyses, Job Bank trends). Use for rules, "
                         "eligibility, qualitative context."),
        ),
        StructuredTool.from_function(
            func=run_viz, name="create_visualization", args_schema=VizInput,
            description=("Create a Plotly chart from tabular rows (usually query_database output). "
                         "The chart is attached to the API response automatically."),
        ),
    ]
