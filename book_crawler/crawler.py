from __future__ import annotations

# pyright: ignore[reportMissingImports]

import time
import urllib.parse
from dataclasses import dataclass
from typing import List

import importlib
import re

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


def _extract_metadata(text: str, fallback_title: str) -> dict:
    normalized = re.sub(r"\s+", " ", text)
    lower = normalized.lower()

    title = fallback_title or None
    author = None
    publisher = None
    year = None
    isbn = None

    author_match = re.search(r"\bby\s+([A-Z][A-Za-z.'\-\s]{2,60})", normalized)
    if author_match:
        author = author_match.group(1).strip()

    publisher_match = re.search(
        r"\b(?:published by|publisher|출판사)\s*[:\-]?\s*([A-Za-z0-9.&'\-\s]{2,80})",
        normalized,
        re.IGNORECASE,
    )
    if publisher_match:
        publisher = publisher_match.group(1).strip()

    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", normalized)
    if year_match:
        year = int(year_match.group(1))

    isbn_match = re.search(
        r"\b(?:ISBN(?:-1[03])?:?\s*)?((97[89][\-\s]?\d{1,5}[\-\s]?\d{1,7}"
        r"[\-\s]?\d{1,7}[\-\s]?\d)|([0-9][\-\s]?\d{1,5}[\-\s]?\d{1,7}"
        r"[\-\s]?\d{1,7}[\-\s]?[0-9X]))\b",
        normalized,
        re.IGNORECASE,
    )
    if isbn_match:
        isbn = isbn_match.group(1).replace(" ", "").replace("-", "")

    if "isbn" in lower and isbn is None:
        isbn_token = re.search(r"isbn\s*[:\-]?\s*([0-9X\-\s]{10,20})", lower)
        if isbn_token:
            isbn = isbn_token.group(1).replace(" ", "").replace("-", "")

    return {
        "title": title,
        "author": author,
        "publisher": publisher,
        "year": year,
        "isbn": isbn,
    }


def _find_pdf_candidates(driver) -> List[dict]:
    by_module = importlib.import_module("selenium.webdriver.common.by")
    By = by_module.By

    candidates: List[dict] = []
    anchors = driver.find_elements(By.CSS_SELECTOR, "a")
    for anchor in anchors:
        href = anchor.get_attribute("href") or ""
        text = (anchor.text or "").lower()
        if not href:
            continue
        href_lower = href.lower()
        direct_pdf = href_lower.endswith(".pdf") or ".pdf" in href_lower
        hinted_pdf = "pdf" in text
        if direct_pdf or hinted_pdf:
            candidates.append(
                {
                    "url": href,
                    "direct_pdf": direct_pdf,
                    "hinted_pdf": hinted_pdf,
                }
            )
    deduped = {}
    for item in candidates:
        key = item["url"].lower()
        if key in deduped:
            continue
        deduped[key] = item
    return list(deduped.values())


def _follow_pdf_hints(driver, config: CrawlerConfig, candidates: List[dict]) -> List[str]:
    by_module = importlib.import_module("selenium.webdriver.common.by")
    support_module = importlib.import_module("selenium.webdriver.support")
    ui_module = importlib.import_module("selenium.webdriver.support.ui")
    By = by_module.By
    EC = support_module.expected_conditions
    WebDriverWait = ui_module.WebDriverWait

    found: List[str] = []
    follow_limit = 3
    followed = 0

    for item in candidates:
        if followed >= follow_limit:
            break
        if item.get("direct_pdf"):
            continue
        if not item.get("hinted_pdf"):
            continue
        url = item.get("url")
        if not url:
            continue
        try:
            driver.get(url)
            WebDriverWait(driver, config.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            _random_delay(config)
            nested = _find_pdf_candidates(driver)
            for nested_item in nested:
                if nested_item.get("direct_pdf"):
                    found.append(nested_item["url"])
        except Exception:
            continue
        followed += 1

    return list(dict.fromkeys(found))


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
            metadata = _extract_metadata(text, result.title)
            candidates = _find_pdf_candidates(driver)
            hinted_urls = _follow_pdf_hints(driver, config, candidates)
            candidate_urls = [item["url"] for item in candidates]
            candidate_urls.extend(hinted_urls)
            candidate_urls = list(dict.fromkeys(candidate_urls))
            decision = decision_for(text, result.domain)
            return {
                "rank": result.rank,
                "source": {
                    "title": result.title,
                    "url": result.url,
                    "domain": result.domain,
                    "snippet": result.snippet,
                },
                "book": metadata,
                "candidates": [
                    {
                        "url": url,
                        "content_type": None,
                        "license_signals": decision.get("license_signals", []),
                        "confidence": decision.get("confidence", "low"),
                    }
                    for url in candidate_urls
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
