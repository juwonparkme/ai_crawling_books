from __future__ import annotations

# pyright: ignore[reportMissingImports]

import time
import urllib.parse
from dataclasses import dataclass
from typing import List

import importlib

from .config import CrawlerConfig
from .license_detector import decision_for, merge_text_parts


@dataclass
class SearchResult:
    rank: int
    title: str
    url: str
    domain: str
    snippet: str


def build_google_url(query: str, lang: str) -> str:
    params = {"q": query, "hl": lang, "num": 10}
    return "https://www.google.com/search?" + urllib.parse.urlencode(params)


def create_driver(config: CrawlerConfig):
    webdriver = importlib.import_module("selenium.webdriver")
    options_module = importlib.import_module("selenium.webdriver.chrome.options")
    Options = options_module.Options

    options = Options()
    if config.headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        manager_module = importlib.import_module("webdriver_manager.chrome")
        service_module = importlib.import_module("selenium.webdriver.chrome.service")
        service = service_module.Service(manager_module.ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    except Exception:
        return webdriver.Chrome(options=options)


def _random_delay(config: CrawlerConfig) -> None:
    delay = config.delay_min
    if config.delay_max > config.delay_min:
        delay = config.delay_min + (config.delay_max - config.delay_min) * 0.5
    time.sleep(delay)


def collect_search_results(driver, config: CrawlerConfig, query: str) -> List[SearchResult]:
    by_module = importlib.import_module("selenium.webdriver.common.by")
    support_module = importlib.import_module("selenium.webdriver.support")
    ui_module = importlib.import_module("selenium.webdriver.support.ui")
    By = by_module.By
    EC = support_module.expected_conditions
    WebDriverWait = ui_module.WebDriverWait

    url = build_google_url(query, config.lang)
    driver.get(url)
    WebDriverWait(driver, config.timeout).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.g, div.MjjYud"))
    )

    blocks = driver.find_elements(By.CSS_SELECTOR, "div.g, div.MjjYud")
    results: List[SearchResult] = []

    for block in blocks:
        try:
            title_el = block.find_element(By.CSS_SELECTOR, "h3")
            link_el = block.find_element(By.CSS_SELECTOR, "a")
        except Exception:
            continue

        title = title_el.text.strip()
        url = link_el.get_attribute("href") or ""
        if not title or not url:
            continue

        snippet = ""
        snippet_els = block.find_elements(By.CSS_SELECTOR, ".VwiC3b")
        if snippet_els:
            snippet = snippet_els[0].text.strip()

        domain = urllib.parse.urlparse(url).netloc
        results.append(
            SearchResult(
                rank=len(results) + 1,
                title=title,
                url=url,
                domain=domain,
                snippet=snippet,
            )
        )

        if len(results) >= config.max_results:
            break

    return results


def _collect_page_text(driver) -> str:
    by_module = importlib.import_module("selenium.webdriver.common.by")
    By = by_module.By

    parts: List[str] = []
    try:
        parts.append(driver.title or "")
    except Exception:
        pass

    for selector in ("meta[name='description']", "meta[property='og:description']"):
        try:
            meta = driver.find_element(By.CSS_SELECTOR, selector)
            content = meta.get_attribute("content")
            if content:
                parts.append(content)
        except Exception:
            continue

    try:
        body = driver.find_element(By.TAG_NAME, "body")
        parts.append(body.text)
    except Exception:
        pass

    return merge_text_parts(parts)


def _find_pdf_candidates(driver) -> List[str]:
    by_module = importlib.import_module("selenium.webdriver.common.by")
    By = by_module.By

    urls: List[str] = []
    anchors = driver.find_elements(By.CSS_SELECTOR, "a")
    for anchor in anchors:
        href = anchor.get_attribute("href") or ""
        text = (anchor.text or "").lower()
        if not href:
            continue
        if ".pdf" in href.lower() or "pdf" in text:
            urls.append(href)
    return list(dict.fromkeys(urls))


def analyze_result(driver, config: CrawlerConfig, result: SearchResult) -> dict:
    exc_module = importlib.import_module("selenium.common.exceptions")
    by_module = importlib.import_module("selenium.webdriver.common.by")
    support_module = importlib.import_module("selenium.webdriver.support")
    ui_module = importlib.import_module("selenium.webdriver.support.ui")
    TimeoutException = exc_module.TimeoutException
    StaleElementReferenceException = exc_module.StaleElementReferenceException
    By = by_module.By
    EC = support_module.expected_conditions
    WebDriverWait = ui_module.WebDriverWait

    for attempt in range(config.retries + 1):
        try:
            driver.get(result.url)
            WebDriverWait(driver, config.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            _random_delay(config)
            text = _collect_page_text(driver)
            candidates = _find_pdf_candidates(driver)
            decision = decision_for(text, result.domain)
            return {
                "rank": result.rank,
                "source": {
                    "title": result.title,
                    "url": result.url,
                    "domain": result.domain,
                    "snippet": result.snippet,
                },
                "book": {
                    "title": None,
                    "author": None,
                    "publisher": None,
                    "year": None,
                    "isbn": None,
                },
                "candidates": [
                    {
                        "url": url,
                        "content_type": None,
                        "license_signals": decision.get("license_signals", []),
                        "confidence": decision.get("confidence", "low"),
                    }
                    for url in candidates
                ],
                "decision": {
                    "status": decision["status"],
                    "reason": decision["reason"],
                    "selected_url": None,
                },
                "downloads": [],
            }
        except (TimeoutException, StaleElementReferenceException):
            if attempt >= config.retries:
                return {
                    "rank": result.rank,
                    "source": {
                        "title": result.title,
                        "url": result.url,
                        "domain": result.domain,
                        "snippet": result.snippet,
                    },
                    "book": {
                        "title": None,
                        "author": None,
                        "publisher": None,
                        "year": None,
                        "isbn": None,
                    },
                    "candidates": [],
                    "decision": {
                        "status": "blocked",
                        "reason": "page_timeout",
                        "selected_url": None,
                    },
                    "downloads": [],
                }
            continue

    return {}
