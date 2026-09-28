"""Ingestion CLI.

Usage:
    python -m app.ingestion.run_ingestion --all
    python -m app.ingestion.run_ingestion --csv          # IRCC CSVs + seeds
    python -m app.ingestion.run_ingestion --statcan      # StatCan WDS full tables
    python -m app.ingestion.run_ingestion --rag          # PDF/HTML → ChromaDB
"""
import argparse
import json
import logging
import sys


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="CanPath AI data ingestion")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--csv", action="store_true")
    parser.add_argument("--statcan", action="store_true")
    parser.add_argument("--rag", action="store_true")
    args = parser.parse_args()
    if not any([args.all, args.csv, args.statcan, args.rag]):
        parser.error("choose at least one of --all/--csv/--statcan/--rag")

    summary: dict[str, dict[str, int]] = {}
    if args.all or args.csv:
        from app.ingestion.csv_pipeline import run_csv_ingestion

        summary["csv"] = run_csv_ingestion()
    if args.all or args.statcan:
        from app.ingestion.statcan import run_statcan_ingestion

        summary["statcan"] = run_statcan_ingestion()
    if args.all or args.rag:
        from app.ingestion.rag_pipeline import run_rag_ingestion

        summary["rag"] = run_rag_ingestion()

    print(json.dumps(summary, indent=2))
    failed = [k for group in summary.values() for k, v in group.items() if v == 0]
    if failed:
        print(f"WARNING: sources with 0 rows/chunks: {failed}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
