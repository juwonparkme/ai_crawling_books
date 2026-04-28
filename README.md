# ai_crawling_books

Selenium 기반 책 PDF 후보 크롤러입니다. 책 제목/저자에서 검색 쿼리를 만들고, 검색 결과 페이지를 분석해 합법 배포로 보이는 PDF 후보만 저장 대상으로 고릅니다.

## 현재 상태

- Brave/Bing 검색 결과 수집 및 결과 페이지 분석
- PDF 후보 링크 탐색
- Creative Commons, Open Access, Public Domain 등 라이선스 신호 탐지
- 검색 결과 관련성 점수화 및 잡음 도메인 감점
- 실행 결과를 `run_<uuid>.json`으로 저장
- 다운로드 전 `application/pdf` 확인, SHA-256/파일 크기 기록
- localhost 기반 로컬 웹 GUI 제공

자세한 설계 노트:

- `book_crawler/flow.md`
- `book_crawler/licensing.md`
- `PROJECT_STATUS.md`

## 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## CLI 실행

```bash
mkdir -p result
python3 -m book_crawler \
  --title "Database System Concepts" \
  --author "Silberschatz" \
  --out result \
  --search-provider brave \
  --dry-run
```

실제 다운로드까지 실행하려면 `--dry-run`을 빼면 됩니다.

## 주요 옵션

- `--title`: 책 제목. 필수.
- `--author`: 저자명.
- `--out`: 결과 JSON/PDF 저장 디렉토리. 부모 디렉토리가 쓰기 가능하면 자동 생성.
- `--max-results`: 분석할 검색 결과 수. 기본값 `20`.
- `--lang`: 검색 언어 힌트. 기본값 `ko`.
- `--year-from`, `--year-to`: 연도 범위 힌트.
- `--headless` / `--no-headless`: 브라우저 headless 모드 제어.
- `--dry-run` / `--no-dry-run`: 다운로드 생략 여부.
- `--search-provider`: `brave` 또는 `bing`. 기본값 `brave`.

## GUI 실행

```bash
python3 -m book_crawler.gui
```

GUI 기능:

- 제목/저자/연도/검색 provider/출력 경로 입력
- `brave` 또는 `bing` 검색 provider 선택
- 실행 상태와 로그 표시
- 실행 취소 요청
- `run_<uuid>.json` 결과 로딩
- 후보 URL, 관련성 점수, 라이선스 판단, 다운로드 결정 검토
- 실행 로그를 출력 폴더의 `gui_<timestamp>.log`로 저장

안전 정책:

- 기본값은 `dry-run`입니다.
- 합법 배포 근거가 약한 후보는 자동 다운로드 대상이 아닙니다.
- GUI의 라이선스 판단은 자동 필터이며 최종 법률 검토를 대체하지 않습니다.

## 테스트

```bash
python3 -m unittest discover -s tests
```

현재 테스트 범위:

- 검색 결과 관련성 점수
- 잡음 도메인 감점
- 영어/한국어 검색 결과 필터
- 라이선스 판단

## 알려진 제약

- Google은 challenge/reCAPTCHA 차단 가능성이 높아 현재 Brave/Bing 기반입니다.
- 검색엔진 DOM 변경이나 rate-limit에 취약합니다.
- 메타데이터 추출은 아직 페이지 텍스트 휴리스틱에 의존합니다.
- `--out` 디렉토리는 부모 디렉토리가 쓰기 가능하면 자동 생성됩니다.
- 합법 배포 판단은 보수적 휴리스틱이며 최종 법률 판단을 대체하지 않습니다.

## GUI 전환 백로그

Linear 프로젝트/태스크로 옮길 수 있는 최소 단위:

- 구현 형태: Python stdlib `http.server` 기반 localhost GUI
- 검색 실행 폼: 제목, 저자, 연도, 최대 결과, dry-run 입력
- 실행 상태 화면: 검색/분석/다운로드 단계별 로그
- 결과 검토 화면: 후보 URL, 관련성 점수, 라이선스 신호, 다운로드 결정 표시
- 설정 화면: 검색 provider, headless, timeout, retry, 출력 경로
- 안전장치: 합법 배포 근거가 약한 후보는 기본 다운로드 차단
- 패키징: `python3 -m book_crawler.gui`로 실행
