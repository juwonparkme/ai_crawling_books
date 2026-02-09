# Selenium crawling flow

## Goals
- Query Google Search with book title and optional author.
- Collect top N result entries.
- For each result, extract metadata and find PDF candidates.
- Do not download if license signals are missing or unclear.

## High-level flow
1. Build query strings (base + trusted-domain variants).
2. Open Google Search with Selenium (headless).
3. Parse search results (rank, title, url, snippet).
4. Visit each result url and extract book metadata.
5. Discover PDF candidates on the page and linked pages.
6. Collect license signals and decide eligibility.
7. Produce JSON output; download only allowed PDFs.

## Page navigation
- Use a single Selenium session per run.
- Respect delays between requests (random between delay_min and delay_max).
- Apply retries on transient failures (timeouts, stale elements).

## Google results parsing
- Target search result blocks: CSS `div.g` (fallback `div.MjjYud`).
- Extract:
  - title: `h3` text
  - url: first `a` under result block
  - snippet: `div.VwiC3b` or `span.VwiC3b`
- Ignore ads/sponsored blocks by checking url host or missing h3.

## Metadata extraction per result
- Fetch the result page and parse:
  - title: `meta[property="og:title"]` or `title` tag
  - author: keywords in page text ("by <name>") or meta tags
  - publisher/year/isbn: simple regex search on visible text
- Keep extraction best-effort; allow missing fields.

## PDF candidate discovery
- Primary: find links with `.pdf` or `content-type: application/pdf`.
- Secondary: find anchors with text containing "PDF" and follow once.
- Record candidate urls and link context.

## License signal detection
- Scan page text and meta description for known signals.
- Map signals to confidence:
  - high: CC or Public Domain + trusted domain
  - medium: Open Access/official distribution
  - low: personal blog or ambiguous wording

## Output structure
- Build `results[]` and `candidates[]` as defined in AGENTS.md.
- Store decision per result: allowed/blocked/unclear.

## Error handling
- For each url:
  - retry on timeout/stale element
  - record error in `downloads[]` or `decision.reason`
- Continue on failure; do not abort entire run.

## Future improvements
- Add pagination support for Google results.
- Add heuristic to de-duplicate same PDF across results.
- Add optional sitemap or robots.txt compliance checks.
