from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class CrawlerConfig:
    title: str
    author: Optional[str]
    out_dir: Path
    max_results: int
    lang: str
    year_from: Optional[int]
    year_to: Optional[int]
    headless: bool
    dry_run: bool
    delay_min: float
    delay_max: float
    timeout: float
    retries: int

    @classmethod
    def from_namespace(cls, ns) -> "CrawlerConfig":
        title = (ns.title or "").strip()
        author = (ns.author or "").strip() or None
        out_dir = Path(ns.out).expanduser().resolve(strict=False)
        return cls(
            title=title,
            author=author,
            out_dir=out_dir,
            max_results=ns.max_results,
            lang=ns.lang,
            year_from=ns.year_from,
            year_to=ns.year_to,
            headless=ns.headless,
            dry_run=ns.dry_run,
            delay_min=ns.delay_min,
            delay_max=ns.delay_max,
            timeout=ns.timeout,
            retries=ns.retries,
        )
