# License signal detection

## Goal
Detect whether a PDF candidate is legally downloadable based on page text, metadata, and domain trust.

## Inputs
- page text (visible content)
- meta tags (description, og:description, dc.rights, dc.license)
- candidate url + domain

## Positive signals (keyword map)
High confidence:
- "Creative Commons"
- "CC BY"
- "CC BY-SA"
- "CC BY-NC"
- "CC0"
- "Public Domain"

Medium confidence:
- "Open Access"
- "OA"
- "free access"
- "official distribution"
- "author provided"
- "무료 공개"
- "공식 배포"
- "저자 제공"

Negative signals (block)
- "All rights reserved"
- "copyright"
- "no redistribution"
- "no download"
- "purchase"
- "buy now"
- "유료"
- "구매"

## Domain trust
Trusted (higher weight):
- .edu, .ac, .gov, .org with academic/official context
- known publishers / official author pages

Low trust:
- file sharing sites
- personal blogs
- URL shorteners

## Decision rules
1. If any negative signal is present -> block (reason: `license_denied`).
2. If high confidence signal present and domain trusted -> allow.
3. If high/medium signal present but domain unknown -> mark unclear.
4. If no positive signal -> block (reason: `license_unclear`).
5. If signals conflict -> block (reason: `license_conflict`).

## Output mapping
- `confidence`: high | medium | low
- `decision.status`: allowed | blocked
- `decision.reason`: license_denied | license_unclear | license_conflict | domain_untrusted

## Test plan (manual + unit)
Unit tests:
- keyword detection on sample text
- domain trust classification
- decision rule combinations

Manual checks:
- a known CC book page (should allow)
- a publisher paywall page (should block)
- a university repo with unclear license (should be unclear)

## Implementation notes
- Normalize text to lowercase.
- Strip punctuation for keyword matching.
- Use exact match for short tokens ("OA", "CC0").
