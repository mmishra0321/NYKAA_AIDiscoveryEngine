"""CLI for Phase 4 retrieval."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date, datetime
from pathlib import Path

from src.retrieval.pipeline import run_catalog_retrieval


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nykaa Fashion Phase 4 — retrieve evidence packs per catalog question"
    )
    parser.add_argument(
        "--catalog",
        action="store_true",
        help="Retrieve all 10 catalog questions (default if --query-id omitted)",
    )
    parser.add_argument(
        "--query-id",
        nargs="+",
        default=None,
        help="Subset of question ids (e.g. q1_wishlist_motive q10_unmet_needs)",
    )
    parser.add_argument(
        "--run-date",
        type=_parse_date,
        default=None,
        help="Output / processed folder date YYYY-MM-DD",
    )
    parser.add_argument(
        "--stub",
        action="store_true",
        help="Hash query vectors (use when the index was built with --stub)",
    )
    parser.add_argument(
        "--persist-dir",
        type=Path,
        default=None,
        help="Chroma persist directory (default: data/chroma)",
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
    summary = run_catalog_retrieval(
        run_date=args.run_date,
        stub=args.stub,
        persist_directory=args.persist_dir,
        query_ids=args.query_id,
    )
    print(json.dumps(summary, indent=2, default=str))
    return 0
