"""CLI for Phase 1 ingestion."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date, datetime

from src.ingestion.pipeline import run_ingestion


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nykaa Fashion Phase 1 multi-source ingestion")
    parser.add_argument(
        "--sources",
        nargs="+",
        default=None,
        help="Subset of sources (play_store app_store reddit forum youtube)",
    )
    parser.add_argument(
        "--run-date",
        type=_parse_date,
        default=None,
        help="Output folder date YYYY-MM-DD (default: today)",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    summary = run_ingestion(sources=args.sources, run_date=args.run_date)
    print(json.dumps(summary, indent=2, default=str))
    return 0
