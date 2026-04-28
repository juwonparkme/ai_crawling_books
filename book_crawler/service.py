from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from .config import CrawlerConfig
from .crawler import SearchEngineBlockedError
from .runner import CrawlerCancelled, run
from .validators import validate_config

ProgressCallback = Callable[[str, str], None]


@dataclass(frozen=True)
class RunSettings:
    title: str
    author: str = ""
    out_dir: str = "result"
    max_results: int = 20
    lang: str = "ko"
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    headless: bool = True
    dry_run: bool = True
    delay_min: float = 1.5
    delay_max: float = 3.5
    timeout: float = 20
    retries: int = 2
    search_provider: str = "brave"


@dataclass(frozen=True)
class RunResult:
    status: str
    run_path: Optional[Path]
    error: Optional[str] = None


def build_config(settings: RunSettings) -> CrawlerConfig:
    return CrawlerConfig(
        title=settings.title.strip(),
        author=settings.author.strip() or None,
        out_dir=Path(settings.out_dir).expanduser().resolve(strict=False),
        max_results=settings.max_results,
        lang=settings.lang.strip() or "ko",
        year_from=settings.year_from,
        year_to=settings.year_to,
        headless=settings.headless,
        dry_run=settings.dry_run,
        delay_min=settings.delay_min,
        delay_max=settings.delay_max,
        timeout=settings.timeout,
        retries=settings.retries,
        search_provider=settings.search_provider,
    )


def validate_settings(settings: RunSettings) -> list[str]:
    return validate_config(build_config(settings))


def run_crawler(
    settings: RunSettings,
    progress_callback: ProgressCallback | None = None,
    cancel_event: threading.Event | None = None,
) -> RunResult:
    config = build_config(settings)
    errors = validate_config(config)
    if errors:
        return RunResult(status="failed", run_path=None, error="; ".join(errors))
    try:
        run_path = run(config, progress_callback=progress_callback, cancel_event=cancel_event)
        return RunResult(status="completed", run_path=run_path)
    except CrawlerCancelled:
        return RunResult(status="cancelled", run_path=None, error="cancelled")
    except SearchEngineBlockedError as exc:
        return RunResult(status="failed", run_path=None, error=f"search blocked: {exc}")
    except Exception as exc:
        return RunResult(status="failed", run_path=None, error=str(exc))


def load_run_file(path: str | Path) -> dict:
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        return json.load(handle)
