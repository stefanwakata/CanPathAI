"""Tests for dependency-light modules (run anywhere: stdlib + pandas only).

The heavier integration tests live in test_api.py / test_ingestion.py and run
in CI/Docker where all requirements are installed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from app.agent.citations import CitationTracker, ensure_citations, has_sources_section  # noqa: E402
from app.agent.sql_guard import UnsafeSqlError, enforce_limit, validate_sql  # noqa: E402
from app.agent.viz_spec import build_figure  # noqa: E402
from app.core.i18n import detect_language, normalize_lang  # noqa: E402
from app.ingestion.chunking import chunk_text  # noqa: E402
from app.ingestion.encoding import decode_bytes, sniff_delimiter, sniff_encoding  # noqa: E402
from app.ingestion.normalize import (  # noqa: E402
    normalize_pr_admissions,
    normalize_pr_by_citizenship,
    normalize_pr_by_noc,
    parse_int,
    parse_month,
)


def _assert_raises(exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc_type:
        return
    raise AssertionError(f"{fn.__name__} did not raise {exc_type.__name__}")


# ---------- encoding ----------

def test_encoding_utf8_bom():
    raw = "année,café\n2024,10".encode("utf-8-sig")
    assert sniff_encoding(raw) == "utf-8-sig"
    assert "année" in decode_bytes(raw)


def test_encoding_utf16():
    raw = "year,total\n2024,10".encode("utf-16")
    assert decode_bytes(raw).startswith("year")


def test_encoding_latin1():
    raw = "catégorie;10".encode("latin-1")
    text = decode_bytes(raw)
    assert "10" in text


def test_delimiter():
    assert sniff_delimiter("a,b,c\n1,2,3") == ","
    assert sniff_delimiter("a;b;c\n1;2;3") == ";"
    assert sniff_delimiter("a\tb\n1\t2") == "\t"


# ---------- chunking ----------

def test_chunking_basic():
    text = ("Lorem ipsum dolor sit amet. " * 20 + "\n\n") * 5
    chunks = chunk_text(text, chunk_size=300, overlap=50)
    assert len(chunks) > 1
    assert all(len(c.text) <= 300 for c in chunks)
    assert [c.metadata["chunk_index"] for c in chunks] == list(range(len(chunks)))


def test_chunking_empty_and_errors():
    assert chunk_text("") == []
    _assert_raises(ValueError, chunk_text, "x", chunk_size=0)
    _assert_raises(ValueError, chunk_text, "x", chunk_size=10, overlap=10)


def test_chunking_pathological_no_spaces():
    chunks = chunk_text("x" * 5000, chunk_size=400, overlap=50)
    assert chunks and all(len(c.text) <= 400 for c in chunks)


# ---------- sql guard ----------

def test_sql_guard_allows_select():
    q = validate_sql("SELECT province, SUM(admissions) FROM pr_admissions GROUP BY province")
    assert q.lower().startswith("select")


def test_sql_guard_allows_cte_and_joins():
    q = """WITH top AS (SELECT noc_code FROM pr_by_noc)
    SELECT w.noc_title, w.wage_median FROM wages_by_noc w JOIN top ON top.noc_code = w.noc_code"""
    assert validate_sql(q)


def test_sql_guard_strips_fences_and_semicolon():
    assert validate_sql("```sql\nSELECT 1 FROM pr_admissions;\n```")


def test_sql_guard_blocks_dml():
    for bad in ["DELETE FROM pr_admissions", "DROP TABLE wages_by_noc",
                "INSERT INTO pr_admissions VALUES (1)",
                "SELECT 1; DELETE FROM pr_admissions",
                "UPDATE pr_admissions SET admissions=0"]:
        _assert_raises(UnsafeSqlError, validate_sql, bad)


def test_sql_guard_blocks_unknown_tables():
    _assert_raises(UnsafeSqlError, validate_sql, "SELECT * FROM users")


def test_enforce_limit():
    assert enforce_limit("SELECT * FROM pr_admissions").endswith("LIMIT 200")
    assert enforce_limit("SELECT * FROM pr_admissions LIMIT 5").endswith("LIMIT 5")


# ---------- citations ----------

def test_citations_appended_when_missing():
    t = CitationTracker()
    t.add("IRCC PR admissions", "IRCC ODP", "https://open.canada.ca/x")
    out = ensure_citations("Voici la réponse.", t, lang="fr")
    assert has_sources_section(out)
    assert "open.canada.ca" in out


def test_citations_not_duplicated():
    t = CitationTracker()
    t.add("A", "A")
    t.add("A", "A")
    assert len(t.refs) == 1
    out = ensure_citations("Answer.\n\n**Sources:**\n- A", t)
    assert out.count("Sources") == 1


# ---------- i18n ----------

def test_detect_french():
    assert detect_language("Quel est le salaire médian d'un développeur au Québec ?") == "fr"


def test_detect_english():
    assert detect_language("What are the job prospects for nurses in Alberta?") == "en"


def test_normalize_lang():
    assert normalize_lang("FR-ca") == "fr"
    assert normalize_lang(None, "How many immigrants arrived?") == "en"


# ---------- viz ----------

def test_viz_bar_and_series():
    rows = [{"province": "Ontario", "admissions": 100, "year": 2024},
            {"province": "Quebec", "admissions": 50, "year": 2024},
            {"province": "Ontario", "admissions": 120, "year": 2025},
            {"province": "Quebec", "admissions": 60, "year": 2025}]
    fig = build_figure("grouped_bar", rows, x="province", y="admissions", series="year", title="PR")
    assert fig["layout"]["barmode"] == "group"
    assert len(fig["data"]) == 2


def test_viz_errors():
    _assert_raises(ValueError, build_figure, "heatmap", [{"a": 1}], x="a", y="a")
    _assert_raises(ValueError, build_figure, "bar", [], x="a", y="b")
    _assert_raises(ValueError, build_figure, "bar", [{"a": 1}], x="a", y="missing")


# ---------- normalizers ----------

def test_normalize_pr_admissions():
    df = pd.DataFrame({
        "EN_YEAR": ["2024", "2024", "2024"],
        "EN_MONTH": ["January", "février", "Total"],
        "EN_PROVINCE_TERRITORY": ["Ontario", "Québec", "Total"],
        "EN_IMMIGRATION_CATEGORY": ["Sponsored Family", "Economic", "Total"],
        "TOTAL": ["1,234", "567", "1801"],
    })
    out = normalize_pr_admissions(df)
    assert len(out) == 2
    assert out.iloc[0]["admissions"] == 1234
    assert out.iloc[0]["month"] == 1
    assert out.iloc[1]["month"] == 2


def test_normalize_citizenship_and_noc():
    df = pd.DataFrame({
        "EN_YEAR": ["2025"], "EN_MONTH": ["03"],
        "EN_COUNTRY_OF_CITIZENSHIP": ["India"], "TOTAL": ["10 500"],
    })
    out = normalize_pr_by_citizenship(df)
    assert out.iloc[0]["admissions"] == 10500

    df2 = pd.DataFrame({
        "EN_YEAR": ["2025"], "EN_PROVINCE_TERRITORY": ["Alberta"],
        "EN_NOC": ["21232 - Software developers and programmers"], "TOTAL": ["321"],
    })
    out2 = normalize_pr_by_noc(df2)
    assert out2.iloc[0]["noc_code"] == "21232"
    assert out2.iloc[0]["noc_title"].startswith("Software")


def test_parse_helpers():
    assert parse_int("1,234") == 1234
    assert parse_int("--") is None
    assert parse_int("<5") == 5
    assert parse_month("July") == 7
    assert parse_month("décembre") == 12
    assert parse_month("Total") is None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc!r}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
