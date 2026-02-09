from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from .config import CrawlerConfig


def build_queries(config: CrawlerConfig) -> List[str]:
    base = f"{config.title} {config.author}".strip() if config.author else config.title
    queries = [f"{base} filetype:pdf", f"{base} site:.edu"]

    if config.year_from is not None or config.year_to is not None:
        year_from = config.year_from or ""
        year_to = config.year_to or ""
        queries.append(f"{base} {year_from}..{year_to} filetype:pdf")

    return queries


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _initial_payload(config: CrawlerConfig, queries: List[str]) -> dict:
    run_id = str(uuid.uuid4())
    return {
        "run_id": run_id,
        "timestamp": _now_iso(),
        "input": {
            **asdict(config),
            "out": str(config.out_dir),
        },
        "query": queries,
        "results": [],
        "stats": {
            "total_results": 0,
            "total_candidates": 0,
            "downloaded": 0,
            "skipped": 0,
            "failed": 0,
        },
    }


def write_run_json(out_dir: Path, payload: dict) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = payload["run_id"]
    path = out_dir / f"run_{run_id}.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return path


def run(config: CrawlerConfig) -> Path:
    queries = build_queries(config)
    payload = _initial_payload(config, queries)
    return write_run_json(config.out_dir, payload)
