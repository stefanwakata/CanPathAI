"""Registry of public data sources (all open licence).

URLs verified against open.canada.ca CKAN metadata (dataset
f7e5498e-0ad8-4417-85c9-9b8aff9b9eda, updated monthly) and StatCan WDS.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class CsvSource:
    key: str
    url: str
    table: str
    description_en: str
    description_fr: str
    landing_page: str


IRCC_SOURCES: list[CsvSource] = [
    CsvSource(
        key="pr_admissions",
        url="https://www.ircc.canada.ca/opendata-donneesouvertes/data/ODP-PR-PT_IMMCAT.csv",
        table="pr_admissions",
        description_en="PR admissions by province/territory and immigration category",
        description_fr="Admissions de RP par province/territoire et catégorie d'immigration",
        landing_page="https://open.canada.ca/data/en/dataset/f7e5498e-0ad8-4417-85c9-9b8aff9b9eda",
    ),
    CsvSource(
        key="pr_by_citizenship",
        url="https://www.ircc.canada.ca/opendata-donneesouvertes/data/ODP-PR-Citz.csv",
        table="pr_by_citizenship",
        description_en="PR admissions by country of citizenship",
        description_fr="Admissions de RP par pays de citoyenneté",
        landing_page="https://open.canada.ca/data/en/dataset/f7e5498e-0ad8-4417-85c9-9b8aff9b9eda",
    ),
    CsvSource(
        key="pr_by_noc",
        url="https://www.ircc.canada.ca/opendata-donneesouvertes/data/ODP-PR-PT_NOC4.csv",
        table="pr_by_noc",
        description_en="PR admissions by province and occupation (NOC)",
        description_fr="Admissions de RP par province et profession (CNP)",
        landing_page="https://open.canada.ca/data/en/dataset/f7e5498e-0ad8-4417-85c9-9b8aff9b9eda",
    ),
]

# StatCan Web Data Service — full-table CSV downloads.
# GET https://www150.statcan.gc.ca/t1/wds/rest/getFullTableDownloadCSV/{pid}/en
# returns a JSON envelope whose "object" field is a zip URL.
STATCAN_TABLES = {
    "labour_force_stats": {
        "pid": "14100287",
        "description_en": "Labour force characteristics, monthly, by province",
        "description_fr": "Caractéristiques de la population active, mensuel, par province",
        "landing_page": "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410028701",
    },
    "wages_by_noc": {
        "pid": "14100417",
        "description_en": "Employee wages by occupation (NOC), annual",
        "description_fr": "Salaires des employés selon la profession (CNP), annuel",
        "landing_page": "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410041701",
    },
    "immigrant_labour_stats": {
        "pid": "14100083",
        "description_en": "Labour force characteristics by immigrant status",
        "description_fr": "Caractéristiques de la population active selon le statut d'immigrant",
        "landing_page": "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410008301",
    },
}

STATCAN_WDS_BASE = "https://www150.statcan.gc.ca/t1/wds/rest"

# Unstructured documents for the RAG store (reports, guides).
RAG_DOCUMENTS = [
    {
        "key": "ircc_pgwp_eligibility",
        "url": (
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/"
            "study-canada/work/after-graduation/eligibility.html"
        ),
        "title_en": "Work in Canada after you graduate: eligibility (PGWP)",
        "title_fr": "Travailler au Canada après vos études : admissibilité (PTPD)",
        "kind": "html",
    },
    {
        "key": "ircc_express_entry",
        "url": (
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/"
            "immigrate-canada/express-entry.html"
        ),
        "title_en": "Express Entry overview",
        "title_fr": "Aperçu d'Entrée express",
        "kind": "html",
    },
    {
        "key": "statcan_immigrant_lm_report",
        "url": "https://www150.statcan.gc.ca/n1/pub/71-606-x/71-606-x2018001-eng.htm",
        "title_en": "Immigrants in the Canadian labour market (analysis)",
        "title_fr": "Les immigrants sur le marché du travail canadien (analyse)",
        "kind": "html",
    },
    {
        "key": "jobbank_trends",
        "url": "https://www.jobbank.gc.ca/trend-analysis",
        "title_en": "Job Bank — labour market trends",
        "title_fr": "Guichet-Emplois — tendances du marché du travail",
        "kind": "html",
    },
]
