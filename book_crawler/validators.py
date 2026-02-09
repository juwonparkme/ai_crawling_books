from __future__ import annotations

import os
import re
from typing import List

from .config import CrawlerConfig

_LANG_RE = re.compile(r"[A-Za-z]{2,8}([_-][A-Za-z0-9]{2,8})?")
_YEAR_MIN = 1000
_YEAR_MAX = 2100


def validate_config(config: CrawlerConfig) -> List[str]:
    errors: List[str] = []

    if not config.title:
        errors.append("--title is required")

    if config.max_results <= 0:
        errors.append("--max-results must be greater than 0")

    if not _LANG_RE.fullmatch(config.lang or ""):
        errors.append("--lang must be a valid language code")

    if config.year_from is not None:
        if not (_YEAR_MIN <= config.year_from <= _YEAR_MAX):
            errors.append(f"--year-from must be between {_YEAR_MIN} and {_YEAR_MAX}")

    if config.year_to is not None:
        if not (_YEAR_MIN <= config.year_to <= _YEAR_MAX):
            errors.append(f"--year-to must be between {_YEAR_MIN} and {_YEAR_MAX}")

    if config.year_from is not None and config.year_to is not None:
        if config.year_from > config.year_to:
            errors.append("--year-from must be less than or equal to --year-to")

    if config.delay_min < 0 or config.delay_max < 0:
        errors.append("--delay-min/--delay-max must be non-negative")
    elif config.delay_min > config.delay_max:
        errors.append("--delay-min must be less than or equal to --delay-max")

    if config.timeout <= 0:
        errors.append("--timeout must be greater than 0")

    if config.retries < 0:
        errors.append("--retries must be 0 or greater")

    if not config.out_dir.exists():
        errors.append("--out directory does not exist")
    elif not config.out_dir.is_dir():
        errors.append("--out must be a directory")
    elif not os.access(config.out_dir, os.W_OK):
        errors.append("--out directory is not writable")

    return errors
