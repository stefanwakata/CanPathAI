"""SQL safety guard for the agent's SQL tool. Pure stdlib — unit-testable.

Only single SELECT statements over the allowlisted tables are permitted.
The LLM never gets raw DDL/DML access.
"""
import re

ALLOWED_TABLES = {
    "pr_admissions", "pr_by_citizenship", "pr_by_noc", "processing_times",
    "wages_by_noc", "labour_force_stats", "immigrant_labour_stats",
    "job_outlooks", "ingestion_runs",
}

_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|attach|"
    r"pragma|vacuum|copy|call|execute|merge|replace)\b",
    re.IGNORECASE,
)
_TABLE_RX = re.compile(r"\b(?:from|join)\s+([a-zA-Z_][\w.\"]*)", re.IGNORECASE)


class UnsafeSqlError(ValueError):
    pass


def strip_sql(query: str) -> str:
    """Remove comments, code fences, and trailing semicolons."""
    q = query.strip()
    q = re.sub(r"^```(?:sql)?\s*|\s*```$", "", q, flags=re.IGNORECASE | re.MULTILINE).strip()
    q = re.sub(r"--[^\n]*", " ", q)
    q = re.sub(r"/\*.*?\*/", " ", q, flags=re.DOTALL)
    return q.strip().rstrip(";").strip()


def validate_sql(query: str, max_length: int = 4000) -> str:
    """Validate and return the cleaned query, or raise UnsafeSqlError."""
    q = strip_sql(query)
    if not q:
        raise UnsafeSqlError("Empty query")
    if len(q) > max_length:
        raise UnsafeSqlError("Query too long")
    if ";" in q:
        raise UnsafeSqlError("Multiple statements are not allowed")
    if not re.match(r"^(select|with)\b", q, re.IGNORECASE):
        raise UnsafeSqlError("Only SELECT queries are allowed")
    if _FORBIDDEN.search(q):
        raise UnsafeSqlError("Query contains a forbidden keyword")

    tables = {t.strip('"').split(".")[-1].lower() for t in _TABLE_RX.findall(q)}
    ctes = {m.group(1).lower() for m in
            re.finditer(r"\b([a-zA-Z_]\w*)\s+as\s*\(", q, re.IGNORECASE)}
    unknown = tables - ALLOWED_TABLES - ctes
    if unknown:
        raise UnsafeSqlError(f"Unknown or forbidden tables: {sorted(unknown)}")
    return q


def enforce_limit(query: str, max_rows: int = 200) -> str:
    """Append a LIMIT clause when the query has none."""
    if re.search(r"\blimit\s+\d+", query, re.IGNORECASE):
        return query
    return f"{query} LIMIT {max_rows}"
