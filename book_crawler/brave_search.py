from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class BraveSearchResult:
    title: str
    link: str
    snippet: str


def run_brave_search(query: str, num_results: int, timeout: float) -> List[BraveSearchResult]:
    skill_dir = _brave_skill_dir()
    command = ["node", "search.js", query, "-n", str(num_results)]
    for attempt in range(2):
        completed = subprocess.run(
            command,
            cwd=skill_dir,
            capture_output=True,
            text=True,
            timeout=max(15, int(timeout * 2)),
            check=False,
        )
        if completed.returncode == 0:
            return parse_brave_search_output(completed.stdout)

        stderr = (completed.stderr or "").strip()
        if "HTTP 429" in stderr and attempt == 0:
            time.sleep(3)
            continue
        raise RuntimeError(stderr or "brave_search_failed")

    return []


def parse_brave_search_output(output: str) -> List[BraveSearchResult]:
    blocks = re.split(r"(?m)^--- Result \d+ ---\n", output)
    results: List[BraveSearchResult] = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        title = _field_value(block, "Title")
        link = _field_value(block, "Link")
        snippet = _field_value(block, "Snippet")
        if title and link:
            results.append(BraveSearchResult(title=title, link=link, snippet=snippet))
    return results


def _field_value(block: str, label: str) -> str:
    pattern = rf"(?m)^{re.escape(label)}:\s*(.*)$"
    match = re.search(pattern, block)
    return match.group(1).strip() if match else ""


def _brave_skill_dir() -> Path:
    candidates = (
        Path.home() / ".codex" / "skills" / "brave-search",
        Path.home() / "Projects" / "agent-scripts" / "skills" / "brave-search",
    )
    for candidate in candidates:
        if (candidate / "search.js").exists():
            return candidate
    raise FileNotFoundError("brave-search skill not found")
