from __future__ import annotations

import importlib
import time
import urllib.parse
from dataclasses import dataclass
from typing import Callable, List

from .config import CrawlerConfig
from .search_ranker import is_supported_search_language


@dataclass(frozen=True)
class BingSearchResult:
    title: str
    link: str
    snippet: str
    domain: str


class SearchEngineBlockedError(RuntimeError):
    """Raised when a search engine blocks automated access."""


def run_bing_search(
    driver,
    config: CrawlerConfig,
    query: str,
    url_extractor: Callable[[str], str],
) -> List[BingSearchResult]:
    by_module = importlib.import_module("selenium.webdriver.common.by")
    ui_module = importlib.import_module("selenium.webdriver.support.ui")
    By = by_module.By
    WebDriverWait = ui_module.WebDriverWait

    driver.get(_build_search_url(query, config.lang))
    WebDriverWait(driver, config.timeout).until(
        lambda current_driver: _has_search_results(current_driver)
        or _has_no_results(current_driver)
        or _search_block_reason(current_driver)
    )
    reason = _search_block_reason(driver)
    if reason:
        raise SearchEngineBlockedError(reason)

    results: List[BingSearchResult] = []
    for item in driver.find_elements(By.CSS_SELECTOR, "li.b_algo"):
        try:
            link = item.find_element(By.CSS_SELECTOR, "h2 a")
            title = _element_text(link)
            url = url_extractor(link.get_attribute("href") or "")
            snippet = ""
            try:
                snippet = _element_text(item.find_element(By.CSS_SELECTOR, ".b_caption p"))
            except Exception:
                pass
            if not title or not url:
                continue
            allowed_language, _ = is_supported_search_language(title, snippet)
            if not allowed_language:
                continue
            results.append(
                BingSearchResult(
                    title=title,
                    link=url,
                    snippet=snippet,
                    domain=urllib.parse.urlparse(url).netloc,
                )
            )
        except Exception:
            continue

    _fixed_delay(config)
    return results


def _build_search_url(query: str, lang: str) -> str:
    params = {"q": query, "count": 10, "setlang": _bing_lang(lang)}
    return "https://www.bing.com/search?" + urllib.parse.urlencode(params)


def _bing_lang(lang: str) -> str:
    normalized = (lang or "").strip().lower().replace("_", "-")
    if normalized == "ko":
        return "ko-kr"
    if normalized == "en":
        return "en-us"
    return normalized or "ko-kr"


def _fixed_delay(config: CrawlerConfig) -> None:
    delay = config.delay_min
    if config.delay_max > config.delay_min:
        delay = config.delay_min + (config.delay_max - config.delay_min) * 0.5
    time.sleep(delay)


def _page_text(driver) -> str:
    try:
        return (driver.page_source or "").lower()
    except Exception:
        return ""


def _search_block_reason(driver) -> str | None:
    current_url = (getattr(driver, "current_url", "") or "").lower()
    if "google.com/sorry/" in current_url:
        return "google_sorry"

    text = _page_text(driver)
    markers = (
        "g-recaptcha",
        "captcha-form",
        "unusual traffic",
        "our systems have detected unusual traffic",
        "verify you are human",
        "please solve this challenge",
        "비정상적인 트래픽",
        "로봇이 아닙니다",
        "보안문자",
    )
    if any(marker in text for marker in markers):
        return "search_challenge"
    return None


def _has_search_results(driver) -> bool:
    by_module = importlib.import_module("selenium.webdriver.common.by")
    By = by_module.By
    for selector in ("li.b_algo", "#b_results .b_algo"):
        try:
            if driver.find_elements(By.CSS_SELECTOR, selector):
                return True
        except Exception:
            continue
    return False


def _has_no_results(driver) -> bool:
    by_module = importlib.import_module("selenium.webdriver.common.by")
    By = by_module.By
    for selector in (".b_no", "#b_results .b_no"):
        try:
            if driver.find_elements(By.CSS_SELECTOR, selector):
                return True
        except Exception:
            continue

    markers = (
        "there are no results for",
        "do not contain the terms",
        "검색 결과가 없습니다",
        "포함한 결과 없음",
    )
    return any(marker in _page_text(driver) for marker in markers)


def _element_text(element) -> str:
    for value in (
        element.text,
        element.get_attribute("textContent"),
        element.get_attribute("innerText"),
    ):
        if value:
            return value.strip()
    return ""
