"""CLI for Phase 5 catalog generation."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date, datetime

from src.generation.pipeline import run_generation


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nykaa Fashion Phase 5 — JSON + Markdown catalog for Q1–Q10"
    )
    parser.add_argument(
        "--run-date",
        type=_parse_date,
        default=None,
        help="Retrieval/processed folder date YYYY-MM-DD (default: latest packs)",
    )
    parser.add_argument(
        "--stub",
        action="store_true",
        help="Skip Groq; build catalog from retrieval packs + sub-theme rollup",
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
    summary = run_generation(run_date=args.run_date, stub=args.stub)
    print(json.dumps(summary, indent=2, default=str))
    if not summary.get("coverage_10_of_10"):
        return 1
    return 0
