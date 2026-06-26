# ai_crawling_books - Legal PDF Candidate Crawler

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)
![Selenium](https://img.shields.io/badge/Selenium-4.x-43B02A)
![PyQt6](https://img.shields.io/badge/PyQt6-6.x-41CD52)
![License](https://img.shields.io/badge/License-MIT-blue)

**A local crawler that searches book PDFs conservatively and only downloads candidates with public distribution signals.**

[한국어](README.md) | [Quick Start](#-quick-start) | [License Notes](book_crawler/licensing.md) | [Report Issues](https://github.com/juwonparkme/ai_crawling_books/issues)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Database Setup](#database-setup)
  - [Run](#run)
- [Distribution](#-distribution)
- [Project Structure](#-project-structure)
- [Feature Details](#-feature-details)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)
- [Acknowledgements](#-acknowledgements)

---

## 🎯 Overview

**ai_crawling_books** is a Python application that turns a book title, author, and optional year hints into search queries, then analyzes Bing or Brave results to find PDF candidates. It reads page body text and metadata, looks for signals such as Creative Commons, Open Access, and Public Domain, and uses domain trust to decide whether a candidate should be downloaded.

### Core Value

- Blocks PDF candidates by default when legal distribution evidence is weak
- Scores search relevance and penalizes noisy dictionary, forum, and blog-like domains
- Supports both CLI automation and a PyQt6 GUI for manual review
- Writes each run to `run_<uuid>.json` with candidates, decision reasons, and download logs

---

## ✨ Features

### 1. Search Result Collection
- Collects Bing search results through a Selenium Chrome session
- Supports an optional Brave provider
- Decodes Bing tracking links back to original URLs
- Filters search results to English and Korean text

### 2. PDF Candidate Analysis
- Analyzes page title, meta description, and body text
- Finds direct `.pdf` links and links whose text hints at PDFs
- Follows a small number of PDF hint links to discover nested PDF candidates
- Extracts title, author, publisher, year, and ISBN on a best-effort basis

### 3. License Safeguards
- Detects positive signals such as Creative Commons, CC BY, Public Domain, and Open Access
- Detects negative signals such as copyright, purchase, and no download
- Weighs trusted domains such as `.edu`, `.ac`, `.gov`, `.org`, and selected known domains
- Keeps unclear signals as `blocked`

### 4. Run Output and Downloads
- Creates a JSON file for every run
- Checks `application/pdf` content type before downloading
- Records SHA-256 and file size for saved PDFs
- Supports `--dry-run` to review candidates without downloading

### 5. Local GUI
- Inputs for title, author, provider, language, and output directory
- Run status and log display
- Cancellation support
- Loading existing `run_*.json` files
- Review table for candidate URLs, relevance scores, and license decisions

---

## 🛠 Tech Stack

### Runtime
- **Python 3.10+** - Local runtime using `str | None` type syntax
- **unittest** - Standard-library regression tests

### Crawling
- **Selenium 4.x** - Chrome-based search and page navigation
- **webdriver-manager 4.x** - ChromeDriver installation helper
- **urllib.request** - PDF content type checks and downloads

### Desktop UI
- **PyQt6 6.x** - Local desktop GUI
- **threading / queue** - Background crawler execution and GUI event delivery

### Packaging
- **PyInstaller 6.x** - Builds a GUI executable for the current OS
- **zip archive** - Produces macOS or Windows distribution archives

---

## 🚀 Quick Start

### Requirements

- Python 3.10 or newer
- Google Chrome
- Internet connection
- macOS or Windows

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/juwonparkme/ai_crawling_books.git
cd ai_crawling_books
```

2. **Create a virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**

```bash
python3 -m pip install -r requirements.txt
```

### Environment Variables

The default Bing provider does not require environment variables.

```env
# required env: none
```

The Brave provider is not intended for general distribution. It depends on Juwon's local `brave-search` skill and its `search.js` file. Most users should keep the default `bing` provider.

### Database Setup

No database is required. Run results are stored as JSON and PDF files in the output directory you choose.

### Run

**CLI dry-run**

```bash
mkdir -p result
python3 -m book_crawler \
  --title "Database System Concepts" \
  --author "Silberschatz" \
  --out result \
  --search-provider bing \
  --dry-run
```

**Allow actual downloads**

```bash
python3 -m book_crawler \
  --title "Think Python" \
  --author "Downey" \
  --out result \
  --search-provider bing \
  --no-dry-run
```

Only candidates with an allowed decision are downloaded.

**Launch the GUI**

```bash
python3 -m book_crawler.gui
```

**Run tests**

```bash
python3 -m unittest discover -s tests
```

---

## 📦 Distribution

This project uses PyInstaller to package the GUI executable for the current OS and wrap it in a zip archive. Building on macOS produces a macOS zip. Building on Windows produces a Windows zip.

### Prepare Build Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
```

### Build a Zip for the Current OS

```bash
python3 scripts/build_zip.py --clean
```

### Output Paths

- macOS: `dist/ai_crawling_books-macos-<arch>.zip`
- Windows: `dist/ai_crawling_books-windows-<arch>.zip`

### Distribution Notes

- Chrome must be installed.
- The default provider is `bing`.
- The `brave` provider depends on a local skill and is not suitable for general user distribution.
- Unsigned and unnotarized macOS apps may trigger Gatekeeper warnings.

---

## 📁 Project Structure

```text
ai_crawling_books/
├── book_crawler/
│   ├── cli.py                # CLI argument parsing and entry point
│   ├── crawler.py            # Selenium driver, result analysis, PDF candidate discovery
│   ├── runner.py             # Run orchestration and JSON persistence
│   ├── service.py            # GUI/service settings and execution wrapper
│   ├── gui.py                # PyQt6 desktop GUI
│   ├── bing_search.py        # Bing search result collection
│   ├── brave_search.py       # Local brave-search skill integration
│   ├── search_ranker.py      # Search relevance scoring
│   ├── license_detector.py   # License signal detection and download decisions
│   ├── downloader.py         # PDF verification, saving, and SHA-256 records
│   ├── flow.md              # Crawling flow design notes
│   └── licensing.md         # License decision notes
├── scripts/
│   └── build_zip.py          # PyInstaller zip build script
├── tests/                    # unittest regression tests
├── requirements.txt          # Runtime dependencies
├── requirements-dev.txt      # Build dependencies
├── LICENSE
├── README.en.md
└── README.md
```

---

## 🎨 Feature Details

### 1. Search Query Generation

- **Base query**: `"Book Title" "Author" filetype:pdf`
- **Year hints**: `--year-from` and `--year-to` add a year-range query
- **Provider**: `--search-provider bing|brave`

### 2. Relevance Scoring

- **Positive weights**: title/author match, PDF, ebook, open access, textbook, download signals
- **Penalties**: dictionary, translation, forum, community, and blog-like domains
- **Ordering**: higher relevance results are analyzed first

### 3. License Decision

- **Allowed**: trusted domain plus strong public distribution signals
- **Blocked**: copyright, purchase, no-download signals, or unclear evidence
- **Direct PDF exception**: trusted direct PDF domains with high relevance can be treated as official distribution

### 4. Result JSON

Each run writes `run_<uuid>.json` to the output directory.

```json
{
  "run_id": "uuid",
  "input": {},
  "query": [],
  "results": [],
  "stats": {
    "total_results": 0,
    "total_candidates": 0,
    "downloaded": 0,
    "skipped": 0,
    "failed": 0
  }
}
```

---

## 🔧 Troubleshooting

### Chrome or ChromeDriver Error

**Symptom**: Selenium cannot open the browser.

**Fix**:
1. Confirm Chrome is installed.
2. Reinstall dependencies inside the virtual environment.

```bash
python3 -m pip install -r requirements.txt
```

### Search Engine Challenge or Block

**Symptom**: You see `blocked by search engine challenge page`.

**Fix**:
1. Retry later.
2. Increase `--delay-min` and `--delay-max`.
3. Lower `--max-results`.

### Brave Provider Error

**Symptom**: You see `brave-search skill not found`.

**Fix**:
1. Use `--search-provider bing` for general runs.
2. Use Brave only in a development environment where the local skill exists.

### No PDF Downloaded

**Symptom**: Candidates exist, but no PDF file is saved.

**Fix**:
1. Check whether `--dry-run` is enabled.
2. Use `--no-dry-run` when you want actual downloads.
3. Inspect `decision.reason` in the result JSON.

---

## 🤝 Contributing

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is distributed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 📞 Contact

- **Name**: Juwon Park
- **Email**: hello@juwonpark.me
- **GitHub**: [@juwonparkme](https://github.com/juwonparkme)
- **Website**: [juwonpark.me](https://juwonpark.me)

---

## 🙏 Acknowledgements

- Selenium and the Chrome WebDriver ecosystem
- PyQt6 desktop UI ecosystem
- PyInstaller packaging tooling
- Authors and institutions that provide public access books and Open Access materials

---

<div align="center">

**Made with ❤️ by Juwon Park**

[⬆ Back to Top](#ai_crawling_books---legal-pdf-candidate-crawler)

</div>
