from __future__ import annotations

import argparse
import sys
from typing import Sequence

from .config import CrawlerConfig
from .crawler import SearchEngineBlockedError
from .runner import run
from .validators import validate_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="book_crawler",
        description="Bing book crawler (metadata + legal PDFs only)",
    )
    parser.add_argument("--title", required=True, help="Book title")
    parser.add_argument("--author", help="Author name")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--max-results", type=int, default=20, help="Max results")
    parser.add_argument("--lang", default="ko", help="Language hint")
    parser.add_argument("--year-from", type=int, dest="year_from", help="Year from")
    parser.add_argument("--year-to", type=int, dest="year_to", help="Year to")
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run browser headless",
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Skip downloads",
    )
    parser.add_argument("--delay-min", type=float, default=1.5, help="Min delay")
    parser.add_argument("--delay-max", type=float, default=3.5, help="Max delay")
    parser.add_argument("--timeout", type=float, default=20, help="Page timeout")
    parser.add_argument("--retries", type=int, default=2, help="Retries per page")
    return parser


def parse_args(argv: Sequence[str]) -> CrawlerConfig:
    parser = build_parser()
    ns = parser.parse_args(argv)
    config = CrawlerConfig.from_namespace(ns)
    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)
    return config


def main(argv: Sequence[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    config = parse_args(argv)
    try:
        out_path = run(config)
    except SearchEngineBlockedError as exc:
        print(f"error: blocked by search engine challenge page: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote run file: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
