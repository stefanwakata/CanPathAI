"""Column normalization for government CSVs. Pure pandas/stdlib — unit-testable.

IRCC open-data CSVs ship bilingual headers whose exact names drift between
releases (e.g. EN_YEAR, EN_ANNEE, "Year", "EN_PT/PROVINCE"). We resolve columns
by keyword patterns instead of exact names so the weekly refresh survives
schema drift.
"""
import re
import unicodedata

import pandas as pd

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12,
}

TOTAL_ROW_MARKERS = {"total", "grand total", "total general", "all", "tous", "toutes"}


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def resolve_column(df: pd.DataFrame, patterns: list[str], prefer_en: bool = True) -> str | None:
    """Find the first column whose folded name matches any regex pattern.

    English-prefixed columns (EN_) are preferred over French ones when both exist.
    """
    cols = list(df.columns)
    ranked = sorted(
        cols,
        key=lambda c: (0 if str(c).lower().startswith("en") else 1) if prefer_en else 0,
    )
    for pat in patterns:
        rx = re.compile(pat)
        for col in ranked:
            if rx.search(_fold(col)):
                return col
    return None


def parse_int(value) -> int | None:
    """Parse counts like '1,234', '12 345', '--', '<5'."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip().replace(" ", " ")
    if s in ("", "--", "-", "..", "n/a", "N/A", "x", "X", "F"):
        return None
    s = s.replace(",", "").replace(" ", "")
    if s.startswith("<"):
        s = s[1:]
    try:
        return int(float(s))
    except ValueError:
        return None


def parse_month(value) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = _fold(value)
    if not s or s in TOTAL_ROW_MARKERS:
        return None
    if s.isdigit():
        m = int(s)
        return m if 1 <= m <= 12 else None
    return MONTHS.get(s.split(" ")[0])


def is_total_row(*values) -> bool:
    return any(_fold(v) in TOTAL_ROW_MARKERS for v in values if v is not None)


def normalize_pr_admissions(df: pd.DataFrame) -> pd.DataFrame:
    """→ columns: year, month, province, immigration_category, admissions."""
    c_year = resolve_column(df, [r"\byear\b", r"\bannee\b"])
    c_month = resolve_column(df, [r"\bmonth\b", r"\bmois\b"])
    c_prov = resolve_column(df, [r"province", r"\bpt\b", r"territor"])
    c_cat = resolve_column(df, [r"immigration categor", r"categor"])
    c_total = resolve_column(df, [r"^total$", r"\btotal\b", r"\bcount\b", r"\bnombre\b"])
    if not (c_year and c_prov and c_cat and c_total):
        raise ValueError(f"Unrecognized PR admissions schema: {list(df.columns)}")

    out = []
    for _, row in df.iterrows():
        if is_total_row(row.get(c_prov), row.get(c_cat)):
            continue
        year = parse_int(row[c_year])
        n = parse_int(row[c_total])
        if year is None or n is None:
            continue
        out.append({
            "year": year,
            "month": parse_month(row[c_month]) if c_month else None,
            "province": str(row[c_prov]).strip(),
            "immigration_category": str(row[c_cat]).strip(),
            "admissions": n,
        })
    return pd.DataFrame(out)


def normalize_pr_by_citizenship(df: pd.DataFrame) -> pd.DataFrame:
    """→ columns: year, month, country, admissions."""
    c_year = resolve_column(df, [r"\byear\b", r"\bannee\b"])
    c_month = resolve_column(df, [r"\bmonth\b", r"\bmois\b"])
    c_country = resolve_column(df, [r"citizenship", r"citoyennete", r"country", r"pays"])
    c_total = resolve_column(df, [r"^total$", r"\btotal\b", r"\bnombre\b"])
    if not (c_year and c_country and c_total):
        raise ValueError(f"Unrecognized PR-by-citizenship schema: {list(df.columns)}")

    out = []
    for _, row in df.iterrows():
        if is_total_row(row.get(c_country)):
            continue
        year = parse_int(row[c_year])
        n = parse_int(row[c_total])
        if year is None or n is None:
            continue
        out.append({
            "year": year,
            "month": parse_month(row[c_month]) if c_month else None,
            "country": str(row[c_country]).strip(),
            "admissions": n,
        })
    return pd.DataFrame(out)


def normalize_pr_by_noc(df: pd.DataFrame) -> pd.DataFrame:
    """→ columns: year, province, noc_code, noc_title, admissions."""
    c_year = resolve_column(df, [r"\byear\b", r"\bannee\b"])
    c_prov = resolve_column(df, [r"province", r"\bpt\b", r"territor"])
    c_noc = resolve_column(df, [r"\bnoc\b", r"\bcnp\b", r"occupation", r"profession"])
    c_total = resolve_column(df, [r"^total$", r"\btotal\b", r"\bnombre\b"])
    if not (c_year and c_prov and c_noc and c_total):
        raise ValueError(f"Unrecognized PR-by-NOC schema: {list(df.columns)}")

    noc_rx = re.compile(r"^\s*(\d{1,5})\s*[-–—:]?\s*(.*)$")
    out = []
    for _, row in df.iterrows():
        if is_total_row(row.get(c_prov), row.get(c_noc)):
            continue
        year = parse_int(row[c_year])
        n = parse_int(row[c_total])
        if year is None or n is None:
            continue
        raw = str(row[c_noc]).strip()
        m = noc_rx.match(raw)
        code, title = (m.group(1), m.group(2).strip() or raw) if m else ("", raw)
        out.append({
            "year": year,
            "province": str(row[c_prov]).strip(),
            "noc_code": code,
            "noc_title": title,
            "admissions": n,
        })
    return pd.DataFrame(out)


NORMALIZERS = {
    "pr_admissions": normalize_pr_admissions,
    "pr_by_citizenship": normalize_pr_by_citizenship,
    "pr_by_noc": normalize_pr_by_noc,
}
