"""CLI for Phase 7 validation."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date, datetime

from src.eval.pipeline import run_eval


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nykaa Fashion Phase 7 — gold labels and catalog checks")
    parser.add_argument(
        "--run-date",
        type=_parse_date,
        default=None,
        help="Eval output folder date YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--stub",
        action="store_true",
        help="Score heuristic relevance/classify (default unless --groq)",
    )
    parser.add_argument(
        "--groq",
        action="store_true",
        help="Score Groq relevance/classify/ask (needs GROQ_API_KEY)",
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
    summary = run_eval(stub=args.stub or not args.groq, groq=args.groq, run_date=args.run_date)
    slim = {k: v for k, v in summary.items() if k != "metrics"}
    metrics = summary.get("metrics") or {}
    slim["metrics"] = {
        name: {k: v for k, v in block.items() if k != "rows"}
        for name, block in metrics.items()
    }
    print(json.dumps(slim, indent=2, default=str))
    return 0 if summary.get("hard_gates_pass") else 1
