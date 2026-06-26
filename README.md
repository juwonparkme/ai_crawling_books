# ai_crawling_books - 합법 PDF 후보 크롤러

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)
![Selenium](https://img.shields.io/badge/Selenium-4.x-43B02A)
![PyQt6](https://img.shields.io/badge/PyQt6-6.x-41CD52)
![License](https://img.shields.io/badge/License-MIT-blue)

**책 제목과 저자를 기반으로 공개 배포 근거가 있는 PDF 후보만 보수적으로 찾는 로컬 크롤러입니다.**

[English](#english) | [실행 가이드](#-시작하기) | [라이선스 판단 노트](book_crawler/licensing.md) | [이슈 리포트](https://github.com/juwonparkme/ai_crawling_books/issues)

</div>

---

## 📋 목차

- [소개](#-소개)
- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [시작하기](#-시작하기)
  - [필수 요구사항](#필수-요구사항)
  - [설치](#설치)
  - [환경 변수 설정](#환경-변수-설정)
  - [데이터베이스 설정](#데이터베이스-설정)
  - [실행](#실행)
- [배포](#-배포)
- [프로젝트 구조](#-프로젝트-구조)
- [주요 기능 상세](#-주요-기능-상세)
- [트러블슈팅](#-트러블슈팅)
- [기여하기](#-기여하기)
- [라이선스](#-라이선스)
- [문의](#-문의)
- [감사의 말](#-감사의-말)

---

## 🎯 소개

**ai_crawling_books**는 책 제목, 저자, 연도 힌트를 검색 쿼리로 바꾸고 Bing 또는 Brave 검색 결과를 분석해 PDF 후보를 수집하는 Python 애플리케이션입니다. 페이지 본문과 메타 정보를 읽어 Creative Commons, Open Access, Public Domain 같은 신호를 찾고, 도메인 신뢰도와 함께 판단해 다운로드 대상을 보수적으로 제한합니다.

### 핵심 가치

- 합법 배포 근거가 약한 PDF는 기본적으로 차단
- 검색 결과 관련성 점수화로 사전, 포럼, 잡음 도메인 감점
- CLI와 PyQt6 GUI를 함께 제공해 자동 실행과 수동 검토 모두 지원
- 실행 결과를 `run_<uuid>.json`으로 저장해 후보, 판단 사유, 다운로드 로그 추적

---

## ✨ 주요 기능

### 1. 검색 결과 수집
- Bing 검색 결과를 Selenium Chrome 세션으로 수집
- Brave provider 선택 가능
- Bing 추적 링크를 원본 URL로 복원
- 영어/한국어 검색 결과만 통과시키는 언어 필터 적용

### 2. PDF 후보 분석
- 검색 결과 페이지의 제목, 메타 설명, 본문 텍스트 분석
- `.pdf` 직접 링크와 PDF 텍스트가 있는 링크 탐색
- PDF 힌트 링크를 제한적으로 따라가 중첩 PDF 후보 확인
- 제목, 저자, 출판사, 연도, ISBN을 best-effort로 추출

### 3. 라이선스 안전장치
- Creative Commons, CC BY, Public Domain, Open Access 등 긍정 신호 탐지
- copyright, purchase, no download 등 부정 신호 탐지
- `.edu`, `.ac`, `.gov`, `.org`, 일부 신뢰 도메인에 가중치 적용
- 신호가 불명확하면 `blocked`로 남김

### 4. 실행 결과와 다운로드
- 실행별 JSON 결과 파일 생성
- 다운로드 전 `application/pdf` content type 확인
- 저장 파일의 SHA-256과 크기 기록
- `--dry-run`으로 다운로드 없이 후보 검토 가능

### 5. 로컬 GUI
- 제목, 저자, provider, 언어, 출력 경로 입력
- 실행 상태와 로그 표시
- 실행 취소 지원
- 기존 `run_*.json` 결과 로딩
- 후보 URL, 관련성 점수, 라이선스 판단 검토

---

## 🛠 기술 스택

### Runtime
- **Python 3.10+** - `str | None` 타입 문법을 사용하는 로컬 실행 환경
- **unittest** - 표준 라이브러리 기반 회귀 테스트

### Crawling
- **Selenium 4.x** - Chrome 기반 검색/페이지 탐색
- **webdriver-manager 4.x** - ChromeDriver 설치 보조
- **urllib.request** - PDF content type 확인과 다운로드

### Desktop UI
- **PyQt6 6.x** - 로컬 데스크톱 GUI
- **threading / queue** - GUI 실행 중 크롤러 작업과 이벤트 전달

### Packaging
- **PyInstaller 6.x** - 현재 OS용 GUI 실행 파일 빌드
- **zip archive** - macOS 또는 Windows 배포 파일 생성

---

## 🚀 시작하기

### 필수 요구사항

- Python 3.10 이상
- Google Chrome
- 인터넷 연결
- macOS 또는 Windows

### 설치

1. **저장소 클론**

```bash
git clone https://github.com/juwonparkme/ai_crawling_books.git
cd ai_crawling_books
```

2. **가상환경 생성**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. **의존성 설치**

```bash
python3 -m pip install -r requirements.txt
```

### 환경 변수 설정

기본 Bing provider는 별도 환경 변수가 필요 없습니다.

```env
# required env: none
```

Brave provider는 일반 배포용 기능이 아니라 Juwon 로컬 `brave-search` skill의 `search.js`에 의존합니다. 일반 사용자는 기본값인 `bing`을 사용하세요.

### 데이터베이스 설정

별도 데이터베이스를 사용하지 않습니다. 실행 결과는 사용자가 지정한 출력 폴더에 JSON과 PDF 파일로 저장됩니다.

### 실행

**CLI dry-run 실행**

```bash
mkdir -p result
python3 -m book_crawler \
  --title "Database System Concepts" \
  --author "Silberschatz" \
  --out result \
  --search-provider bing \
  --dry-run
```

**실제 다운로드 허용**

```bash
python3 -m book_crawler \
  --title "Think Python" \
  --author "Downey" \
  --out result \
  --search-provider bing \
  --no-dry-run
```

허용 판단을 받은 후보만 다운로드를 시도합니다.

**GUI 실행**

```bash
python3 -m book_crawler.gui
```

**테스트 실행**

```bash
python3 -m unittest discover -s tests
```

---

## 📦 배포

이 프로젝트는 PyInstaller로 현재 OS용 GUI 실행 파일을 zip으로 묶습니다. macOS에서 빌드하면 macOS용 zip이, Windows에서 빌드하면 Windows용 zip이 생성됩니다.

### 빌드 준비

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
```

### 현재 OS용 zip 생성

```bash
python3 scripts/build_zip.py --clean
```

### 생성 위치

- macOS: `dist/ai_crawling_books-macos-<arch>.zip`
- Windows: `dist/ai_crawling_books-windows-<arch>.zip`

### 배포 주의사항

- Chrome 설치가 필요합니다.
- 기본 provider는 `bing`입니다.
- `brave` provider는 로컬 skill 의존성이 있어 일반 사용자 배포용으로 적합하지 않습니다.
- macOS 앱은 서명/공증하지 않으면 Gatekeeper 경고가 표시될 수 있습니다.

---

## 📁 프로젝트 구조

```text
ai_crawling_books/
├── book_crawler/
│   ├── cli.py                # CLI 인자 파싱과 실행 진입점
│   ├── crawler.py            # Selenium 드라이버, 검색 결과 분석, PDF 후보 탐색
│   ├── runner.py             # 전체 실행 오케스트레이션과 JSON 저장
│   ├── service.py            # GUI/서비스 계층 설정과 실행 래퍼
│   ├── gui.py                # PyQt6 데스크톱 GUI
│   ├── bing_search.py        # Bing 검색 결과 수집
│   ├── brave_search.py       # 로컬 brave-search skill 연동
│   ├── search_ranker.py      # 검색 결과 관련성 점수화
│   ├── license_detector.py   # 라이선스 신호 탐지와 다운로드 판단
│   ├── downloader.py         # PDF 검증, 저장, SHA-256 기록
│   ├── flow.md              # 크롤링 흐름 설계 노트
│   └── licensing.md         # 라이선스 판단 노트
├── scripts/
│   └── build_zip.py          # PyInstaller zip 빌드 스크립트
├── tests/                    # unittest 기반 회귀 테스트
├── requirements.txt          # 런타임 의존성
├── requirements-dev.txt      # 빌드 의존성
├── LICENSE
└── README.md
```

---

## 🎨 주요 기능 상세

### 1. 검색 쿼리 생성

- **기본 쿼리**: `"책 제목" "저자" filetype:pdf`
- **연도 힌트**: `--year-from`, `--year-to`가 있으면 연도 범위 쿼리 추가
- **provider**: `--search-provider bing|brave`

### 2. 관련성 점수화

- **가산점**: 제목/저자 일치, PDF, ebook, open access, textbook, download 신호
- **감점**: 사전, 번역 페이지, 포럼, 커뮤니티, 블로그성 도메인
- **정렬**: 관련성 점수가 높은 결과부터 분석

### 3. 라이선스 판단

- **허용 조건**: 신뢰 도메인과 강한 공개 배포 신호가 함께 있는 경우
- **차단 조건**: 저작권/구매/다운로드 금지 신호가 있거나 근거가 불명확한 경우
- **직접 PDF 예외**: 신뢰된 직접 PDF 도메인과 높은 관련성 점수는 공식 배포로 판단 가능

### 4. 결과 JSON

각 실행은 출력 폴더에 `run_<uuid>.json`을 남깁니다.

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

## 🔧 트러블슈팅

### Chrome 또는 ChromeDriver 오류

**증상**: Selenium이 브라우저를 열지 못합니다.

**해결 방법**:
1. Chrome이 설치되어 있는지 확인합니다.
2. 가상환경에서 의존성을 다시 설치합니다.

```bash
python3 -m pip install -r requirements.txt
```

### 검색엔진 challenge 또는 차단

**증상**: `blocked by search engine challenge page` 오류가 납니다.

**해결 방법**:
1. 잠시 뒤 다시 실행합니다.
2. `--delay-min`, `--delay-max` 값을 늘립니다.
3. `--max-results`를 줄입니다.

### Brave provider 오류

**증상**: `brave-search skill not found` 오류가 납니다.

**해결 방법**:
1. 일반 실행에서는 `--search-provider bing`을 사용합니다.
2. Brave provider는 로컬 skill이 있는 개발 환경에서만 사용합니다.

### 다운로드가 되지 않음

**증상**: 후보는 있는데 PDF가 저장되지 않습니다.

**해결 방법**:
1. `--dry-run`이 켜져 있는지 확인합니다.
2. 실제 다운로드가 필요하면 `--no-dry-run`으로 실행합니다.
3. 결과 JSON의 `decision.reason`을 확인합니다.

---

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 라이선스

이 프로젝트는 MIT License로 배포됩니다. 자세한 내용은 [LICENSE](LICENSE)를 확인하세요.

---

## 📞 문의

- **이름**: Juwon Park
- **이메일**: hello@juwonpark.me
- **GitHub**: [@juwonparkme](https://github.com/juwonparkme)
- **웹사이트**: [juwonpark.me](https://juwonpark.me)

---

## 🙏 감사의 말

- Selenium 프로젝트와 Chrome WebDriver 생태계
- PyQt6 데스크톱 UI 생태계
- PyInstaller 패키징 도구
- 공개 접근 도서와 Open Access 자료를 제공하는 저자 및 기관

---

<div align="center">

**Made with ❤️ by Juwon Park**

[⬆ 맨 위로 이동](#ai_crawling_books---합법-pdf-후보-크롤러)

</div>

---

<a id="english"></a>

# ai_crawling_books - Legal PDF Candidate Crawler

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)
![Selenium](https://img.shields.io/badge/Selenium-4.x-43B02A)
![PyQt6](https://img.shields.io/badge/PyQt6-6.x-41CD52)
![License](https://img.shields.io/badge/License-MIT-blue)

**A local crawler that searches book PDFs conservatively and only downloads candidates with public distribution signals.**

[한국어](#ai_crawling_books---합법-pdf-후보-크롤러) | [Quick Start](#-quick-start) | [License Notes](book_crawler/licensing.md) | [Report Issues](https://github.com/juwonparkme/ai_crawling_books/issues)

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

[⬆ Back to Top](#english)

</div>
