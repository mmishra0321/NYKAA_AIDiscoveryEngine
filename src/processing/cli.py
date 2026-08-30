"""CLI for Phase 2 processing."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date, datetime

from src.processing.pipeline import run_processing


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nykaa Fashion Phase 2 — relevance, classify, cluster, quantify"
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        default=None,
        help="Subset of raw sources (play_store app_store reddit …)",
    )
    parser.add_argument(
        "--run-date",
        type=_parse_date,
        default=None,
        help="Raw/processed folder date YYYY-MM-DD (default: latest raw)",
    )
    parser.add_argument(
        "--stub",
        action="store_true",
        help="Force heuristic relevance/classify/names (no Groq)",
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
    summary = run_processing(
        sources=args.sources,
        run_date=args.run_date,
        stub=args.stub,
    )
    print(json.dumps(summary, indent=2, default=str))
    return 0
