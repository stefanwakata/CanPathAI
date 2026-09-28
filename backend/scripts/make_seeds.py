"""Generate seed CSVs mimicking real IRCC/StatCan/Job Bank shapes.

Seeds guarantee a fully working local product before the first live ingestion.
Values are realistic orders of magnitude (calibrated on published 2023-2025
figures) but are placeholders until `run_ingestion --all` pulls live data.
"""
import csv
import random
from pathlib import Path

random.seed(42)
OUT = Path(__file__).resolve().parents[1] / "data" / "seed"
OUT.mkdir(parents=True, exist_ok=True)

PROVINCES = {
    "Ontario": 0.42, "Quebec": 0.13, "British Columbia": 0.16, "Alberta": 0.12,
    "Manitoba": 0.05, "Saskatchewan": 0.04, "Nova Scotia": 0.03,
    "New Brunswick": 0.025, "Newfoundland and Labrador": 0.01,
    "Prince Edward Island": 0.008,
}
CATEGORIES = {
    "Economic - Federal High Skilled": 0.32, "Economic - Provincial Nominee Program": 0.25,
    "Sponsored Family": 0.22, "Resettled Refugee & Protected Person": 0.14,
    "Economic - Canadian Experience Class": 0.05, "All Other Immigration": 0.02,
}
COUNTRIES = {
    "India": 0.27, "China": 0.07, "Philippines": 0.07, "Nigeria": 0.05, "Afghanistan": 0.04,
    "Pakistan": 0.03, "France": 0.03, "Iran": 0.03, "United States of America": 0.02,
    "Cameroon": 0.02, "Morocco": 0.02, "Brazil": 0.02, "Haiti": 0.015, "Algeria": 0.015,
}
NOCS = [
    ("21231", "Software engineers and designers"), ("21232", "Software developers and programmers"),
    ("31301", "Registered nurses and registered psychiatric nurses"),
    ("21311", "Computer and information systems managers"),
    ("62020", "Food service supervisors"), ("73300", "Transport truck drivers"),
    ("41200", "University professors and lecturers"), ("11100", "Financial auditors and accountants"),
    ("21301", "Mechanical engineers"), ("32101", "Licensed practical nurses"),
    ("60030", "Restaurant and food service managers"), ("31102", "General practitioners and family physicians"),
]
MONTHLY_PR_TOTAL = {2023: 39000, 2024: 40000, 2025: 33000, 2026: 31500}

def w(name, header, rows):
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"{name}: {len(rows)} rows")

def jitter(n, pct=0.18):
    return max(0, int(n * random.uniform(1 - pct, 1 + pct)))

# --- pr_admissions.csv (raw IRCC shape) ---
rows = []
for year, total in MONTHLY_PR_TOTAL.items():
    months = range(1, 5) if year == 2026 else range(1, 13)
    for m in months:
        for prov, pshare in PROVINCES.items():
            for cat, cshare in CATEGORIES.items():
                rows.append([year, m, prov, cat, jitter(total * pshare * cshare)])
w("pr_admissions.csv",
  ["EN_YEAR", "EN_MONTH", "EN_PROVINCE_TERRITORY", "EN_IMMIGRATION_CATEGORY", "TOTAL"], rows)

# --- pr_by_citizenship.csv ---
rows = []
for year, total in MONTHLY_PR_TOTAL.items():
    months = range(1, 5) if year == 2026 else range(1, 13)
    for m in months:
        for country, share in COUNTRIES.items():
            rows.append([year, m, country, jitter(total * share)])
w("pr_by_citizenship.csv", ["EN_YEAR", "EN_MONTH", "EN_COUNTRY_OF_CITIZENSHIP", "TOTAL"], rows)

# --- pr_by_noc.csv (annual, economic classes) ---
rows = []
for year in MONTHLY_PR_TOTAL:
    for prov, pshare in PROVINCES.items():
        for code, title in NOCS:
            base = 5200 * pshare * random.uniform(0.3, 1.6)
            rows.append([year, prov, f"{code} - {title}", jitter(base)])
w("pr_by_noc.csv", ["EN_YEAR", "EN_PROVINCE_TERRITORY", "EN_NOC", "TOTAL"], rows)

# --- wages_by_noc.csv (normalized shape) ---
WAGES = {
    "21231": (38.46, 51.92, 72.12), "21232": (33.65, 46.15, 64.90),
    "31301": (35.00, 44.50, 56.00), "21311": (43.27, 57.69, 78.85),
    "62020": (16.55, 20.00, 27.00), "73300": (18.00, 25.00, 33.65),
    "41200": (35.90, 51.28, 71.79), "11100": (28.85, 41.35, 62.50),
    "21301": (31.25, 43.27, 60.10), "32101": (26.00, 32.00, 38.46),
    "60030": (17.31, 22.60, 32.69), "31102": (60.00, 105.00, 165.00),
}
PROV_WAGE_FACTOR = {
    "Ontario": 1.05, "Quebec": 0.95, "British Columbia": 1.04, "Alberta": 1.08,
    "Manitoba": 0.90, "Saskatchewan": 0.93, "Nova Scotia": 0.88,
    "New Brunswick": 0.87, "Newfoundland and Labrador": 0.92, "Prince Edward Island": 0.85,
}
rows = []
for code, title in NOCS:
    lo, med, hi = WAGES[code]
    for prov, f in PROV_WAGE_FACTOR.items():
        rows.append([code, title, prov, round(lo * f, 2), round(med * f, 2), round(hi * f, 2), 2025])
w("wages_by_noc.csv",
  ["noc_code", "noc_title", "province", "wage_low", "wage_median", "wage_high", "reference_year"], rows)

# --- job_outlooks.csv ---
OUTLOOKS = {"very good": 5, "good": 4, "moderate": 3, "limited": 2, "very limited": 1}
BASE_OUTLOOK = {
    "21231": "good", "21232": "moderate", "31301": "very good", "21311": "good",
    "62020": "moderate", "73300": "good", "41200": "moderate", "11100": "good",
    "21301": "good", "32101": "very good", "60030": "moderate", "31102": "very good",
}
rows = []
for code, title in NOCS:
    for prov in PROVINCES:
        keys = list(OUTLOOKS)
        base_idx = keys.index(BASE_OUTLOOK[code])
        idx = min(len(keys) - 1, max(0, base_idx + random.choice([-1, 0, 0, 0, 1])))
        label = keys[idx]
        rows.append([code, title, prov, label, OUTLOOKS[label], "2024-2026"])
w("job_outlooks.csv", ["noc_code", "noc_title", "province", "outlook", "outlook_score", "period"], rows)

# --- processing_times.csv ---
rows = [
    ["Express Entry - Canadian Experience Class", "All", 150, "5 months", "2026-06"],
    ["Express Entry - Federal Skilled Worker", "All", 180, "6 months", "2026-06"],
    ["Provincial Nominee Program (Express Entry)", "All", 180, "6 months", "2026-06"],
    ["Provincial Nominee Program (non-Express Entry)", "All", 330, "11 months", "2026-06"],
    ["Post-Graduation Work Permit", "Inside Canada", 100, "100 days", "2026-06"],
    ["Study Permit", "Outside Canada", 56, "8 weeks", "2026-06"],
    ["Study Permit", "India", 63, "9 weeks", "2026-06"],
    ["Work Permit (outside Canada)", "All", 120, "4 months", "2026-06"],
    ["Work Permit Extension", "Inside Canada", 130, "130 days", "2026-06"],
    ["Spousal Sponsorship (inland)", "All", 330, "11 months", "2026-06"],
    ["Spousal Sponsorship (outland)", "All", 300, "10 months", "2026-06"],
    ["Citizenship Grant", "All", 240, "8 months", "2026-06"],
    ["Visitor Visa", "Outside Canada", 30, "30 days", "2026-06"],
]
w("processing_times.csv",
  ["application_type", "country_or_region", "processing_days", "processing_label", "as_of_date"], rows)

print("Seeds written to", OUT)
