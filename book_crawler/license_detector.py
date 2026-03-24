from __future__ import annotations

import re
from typing import Iterable, List, Tuple


POSITIVE_HIGH = (
    "creative commons",
    "cc by",
    "cc by-sa",
    "cc by-nc",
    "cc0",
    "public domain",
)

POSITIVE_MED = (
    "open access",
    "oa",
    "free access",
    "official distribution",
    "author provided",
    "무료 공개",
    "공식 배포",
    "저자 제공",
)

NEGATIVE = (
    "all rights reserved",
    "copyright",
    "no redistribution",
    "no download",
    "purchase",
    "buy now",
    "유료",
    "구매",
)

LOW_TRUST_HOSTS = (
    "drive.google.com",
    "mega.nz",
    "dropbox.com",
    "mediafire.com",
    "z-lib",
    "libgen",
)

DIRECT_PDF_TRUSTED_HOSTS = (
    "greenteapress.com",
)


def _normalize(text: str) -> str:
    text = text.lower()
    return re.sub(r"\s+", " ", text)


def find_signals(text: str) -> Tuple[List[str], List[str]]:
    normalized = _normalize(text)
    positives: List[str] = []
    negatives: List[str] = []

    for token in POSITIVE_HIGH + POSITIVE_MED:
        if token in normalized:
            positives.append(token)

    for token in NEGATIVE:
        if token in normalized:
            negatives.append(token)

    return positives, negatives


def is_trusted_domain(domain: str) -> bool:
    domain = domain.lower()
    if any(host in domain for host in DIRECT_PDF_TRUSTED_HOSTS):
        return True
    if domain.endswith(".edu") or domain.endswith(".ac"):
        return True
    if domain.endswith(".gov") or domain.endswith(".org"):
        return True
    if any(host in domain for host in LOW_TRUST_HOSTS):
        return False
    return False


def decision_for(text: str, domain: str) -> dict:
    positives, negatives = find_signals(text)
    trusted = is_trusted_domain(domain)

    if negatives:
        return {
            "status": "blocked",
            "reason": "license_denied",
            "selected_url": None,
            "confidence": "low",
            "license_signals": positives + negatives,
        }

    if positives:
        confidence = "high" if any(p in POSITIVE_HIGH for p in positives) and trusted else "medium"
        if trusted and any(p in POSITIVE_HIGH for p in positives):
            return {
                "status": "allowed",
                "reason": "license_ok",
                "selected_url": None,
                "confidence": "high",
                "license_signals": positives,
            }
        return {
            "status": "blocked",
            "reason": "license_unclear",
            "selected_url": None,
            "confidence": confidence,
            "license_signals": positives,
        }

    if not trusted:
        return {
            "status": "blocked",
            "reason": "domain_untrusted",
            "selected_url": None,
            "confidence": "low",
            "license_signals": [],
        }

    return {
        "status": "blocked",
        "reason": "license_unclear",
        "selected_url": None,
        "confidence": "low",
        "license_signals": [],
    }


def decision_for_direct_pdf(text: str, domain: str, relevance_score: int) -> dict:
    base = decision_for(text, domain)
    if base["status"] == "allowed":
        return base

    domain_lower = domain.lower()
    trusted_direct_pdf = any(host in domain_lower for host in DIRECT_PDF_TRUSTED_HOSTS)
    if trusted_direct_pdf and relevance_score >= 80:
        return {
            "status": "allowed",
            "reason": "official_distribution",
            "selected_url": None,
            "confidence": "high",
            "license_signals": ["official_distribution"],
        }

    return base


def merge_text_parts(parts: Iterable[str]) -> str:
    return "\n".join(p for p in parts if p)
