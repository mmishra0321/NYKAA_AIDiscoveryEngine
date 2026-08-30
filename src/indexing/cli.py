"""CLI for Phase 3 indexing."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date, datetime
from pathlib import Path

from src.indexing.pipeline import run_indexing


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nykaa Fashion Phase 3 — embed chunks and upsert Chroma"
    )
    parser.add_argument(
        "--run-date",
        type=_parse_date,
        default=None,
        help="Processed folder date YYYY-MM-DD (default: latest processed)",
    )
    parser.add_argument(
        "--stub",
        action="store_true",
        help="Hash embeddings instead of MiniLM (tests / no sentence-transformers)",
    )
    parser.add_argument(
        "--persist-dir",
        type=Path,
        default=None,
        help="Chroma persist directory (default: data/chroma)",
    )
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    summary = run_indexing(
        run_date=args.run_date,
        stub=args.stub,
        persist_directory=args.persist_dir,
        skip_smoke=args.skip_smoke,
    )
    print(json.dumps(summary, indent=2, default=str))
    smoke = summary.get("smoke") or {}
    if not args.skip_smoke and not smoke.get("passed", True):
        return 1
    return 0
