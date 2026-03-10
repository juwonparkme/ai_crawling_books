# 프로젝트 상태 정리

## 한 줄 요약
- 책 제목/저자 기반으로 검색엔진 결과를 수집하고
- 각 결과 페이지에서 PDF 후보와 라이선스 신호를 찾고
- 합법 배포로 보이는 PDF만 저장하려는 Selenium 기반 CLI 크롤러

## 이번 세션에서 한 작업
- 실행 구조 파악
- `requirements.txt` 추가
- Google 기반 동작 확인
- Google이 `sorry` / reCAPTCHA 차단 페이지를 반환하는 것 확인
- headful 브라우저로 실제 차단 화면 확인
- 검색엔진을 Google -> Bing 으로 교체
- Bing 결과 파싱 로직 추가
- Bing 추적 링크 원본 URL 디코드 추가
- Selenium `expected_conditions` import 버그 수정
- JSON 저장 시 `Path` 직렬화 버그 수정
- 현재 디렉토리 아래 `result/` 로 실행해 결과 JSON 생성 확인

## 현재 아키텍처

### 1. CLI 계층
- 파일: `book_crawler/cli.py`
- 역할:
  - 명령행 인자 파싱
  - 설정 검증
  - 실행 진입점 제공
  - 검색엔진 차단 에러를 사용자 메시지로 변환

### 2. 설정/검증 계층
- 파일: `book_crawler/config.py`
- 역할:
  - `CrawlerConfig` 데이터 구조 정의

- 파일: `book_crawler/validators.py`
- 역할:
  - `title`, `lang`, `timeout`, `retries`, `out` 디렉토리 상태 검증

### 3. 오케스트레이션 계층
- 파일: `book_crawler/runner.py`
- 역할:
  - 검색 쿼리 생성
  - 검색 결과 수집 호출
  - 각 결과 페이지 분석 호출
  - 후보 PDF 우선순위 결정
  - 다운로드 여부 판단
  - 최종 JSON 결과 저장

### 4. 검색/페이지 분석 계층
- 파일: `book_crawler/crawler.py`
- 역할:
  - Selenium Chrome 드라이버 생성
  - Bing 검색 URL 생성
  - Bing 검색 결과 파싱
  - 차단/challenge 페이지 감지
  - 결과 페이지 본문/메타텍스트 수집
  - 책 메타데이터 추출
  - PDF 후보 링크 탐색

### 5. 라이선스 판단 계층
- 파일: `book_crawler/license_detector.py`
- 역할:
  - 긍정/부정 라이선스 키워드 탐지
  - 도메인 신뢰도 판단
  - `allowed` / `blocked` 결정

### 6. 다운로드 계층
- 파일: `book_crawler/downloader.py`
- 역할:
  - PDF 파일명 생성
  - HEAD/GET 요청으로 `application/pdf` 확인
  - 실제 PDF 저장
  - SHA-256, 파일 크기 기록

## 작동 원리

### 전체 흐름
1. 사용자 실행
2. CLI가 인자 파싱
3. 설정 검증
4. 검색 쿼리 생성
5. Selenium으로 Bing 검색 결과 수집
6. 각 결과 페이지 방문
7. 본문 텍스트/메타 정보 수집
8. 책 메타데이터 추출
9. PDF 후보 링크 수집
10. 라이선스 신호 판단
11. 허용된 경우만 PDF 다운로드
12. 결과를 `run_<uuid>.json` 으로 저장

### 현재 검색 쿼리 생성 방식
- 기본:
  - `"책 제목" "저자" filetype:pdf`
  - `"책 제목" "저자" site:.edu`
- 연도 조건 있으면 연도 범위 쿼리 추가

### Bing 검색 결과 처리 방식
- `li.b_algo` 블록을 검색 결과로 간주
- `h2 a` 에서 제목/링크 추출
- `.b_caption p` 에서 스니펫 추출
- Bing 추적 링크면 `u=` 파라미터를 디코드해서 실제 URL 복원

### 결과 페이지 분석 방식
- 페이지 `title`
- `meta[name="description"]`
- `meta[property="og:description"]`
- `body` 텍스트

위 텍스트를 합쳐서:
- 저자 추정
- 출판사 추정
- 연도 추정
- ISBN 추정
- PDF 링크 탐지
- 라이선스 키워드 탐지

### 라이선스 판단 방식
- 긍정 신호 예:
  - `Creative Commons`
  - `CC BY`
  - `Public Domain`
  - `Open Access`
- 부정 신호 예:
  - `copyright`
  - `no download`
  - `purchase`
  - `buy now`
- 도메인 신뢰도와 합쳐 최종 결정

## 현재 결과물 저장 방식
- 사용자가 `--out <dir>` 로 넘긴 경로에 저장
- 실행 요약 JSON:
  - `run_<uuid>.json`
- 실제 PDF:
  - `<정제된 책제목_저자_연도>.pdf`

### 이번 세션에서 확인한 저장 경로
- 실행 예:
  - `python3 -m book_crawler --title 'Think Python' --author 'Downey' --out result`
- 생성 결과:
  - `result/run_b3104074-2c4f-4bd6-8d9c-5d77751d299b.json`

## 현재 확인된 문제

### 1. 검색 품질이 낮음
- Bing 첫 결과가 책과 무관한 페이지로 잡히는 경우 있음
- 예: `Think Python` 검색에서 Larousse 사전 페이지가 결과로 들어옴
- 영향:
  - 관련 없는 페이지 분석
  - PDF 후보 없음
  - `domain_untrusted` 로 종료

### 2. 출력 디렉토리 정책이 모순
- `runner.py` 는 출력 폴더를 자동 생성 가능
- 하지만 `validators.py` 는 디렉토리가 미리 있어야 통과
- 현재 사용자는 `mkdir -p result` 같은 사전 생성 필요

### 3. 메타데이터 추출 정확도가 낮음
- 연도 regex가 페이지 아무 숫자나 잡을 수 있음
- ISBN regex도 실제 ISBN 아닌 값을 잡을 수 있음
- 제목도 결과 페이지 title fallback 에 많이 의존

### 4. 도메인 신뢰도 규칙이 너무 거칠음
- `.edu`, `.ac`, `.gov`, `.org` 위주
- 정상적인 공식 배포 도메인도 쉽게 차단될 수 있음
- 반대로 특정 케이스는 더 세분화 필요

### 5. 검색엔진 의존성이 큼
- Google 은 현재 차단
- Bing 도 추후 rate-limit / challenge 가능
- 검색엔진 변경 시 셀렉터 재수정 필요

### 6. 테스트가 없음
- 회귀 테스트 없음
- 파서 변경 시 깨져도 바로 감지 어려움

### 7. 패키징이 약함
- `requirements.txt` 는 추가했지만
- 아직 `pyproject.toml` 없음
- 재현 가능한 개발 환경이 약함

## 다음으로 수정해야 할 사항

### 우선순위 높음
- 검색 결과 관련성 필터 추가
  - 제목/저자 토큰 매칭 점수
  - `pdf`, `book`, `edition`, `isbn` 가중치
  - 사전/포럼/잡음 도메인 감점

- 출력 디렉토리 자동 생성 정책 통일
  - `validators.py` 에서 없는 디렉토리 허용
  - 또는 CLI에서 미리 생성

- 메타데이터 추출 정교화
  - ISBN 체크섬 검증
  - 연도/출판사 후보 스코어링
  - 저자 패턴 개선

- 결과 페이지 예외 처리 강화
  - timeout
  - redirect loop
  - robots/blocked page
  - non-html response

### 우선순위 중간
- 검색엔진 추상화
  - `BingSearchProvider`
  - `DuckDuckGoSearchProvider`
  - 추후 API 기반 provider 추가

- 테스트 추가
  - Bing 결과 HTML fixture 파싱 테스트
  - 라이선스 판단 단위 테스트
  - URL 디코딩 테스트
  - 출력 JSON 구조 테스트

- 문서 보강
  - 설치
  - 실행 예시
  - 결과 JSON 예시
  - known limitations

### 우선순위 낮음
- pagination 지원
- dedupe 강화
- 다운로드 전 파일 크기/헤더 검증 보강
- structured logging 추가

## 추천 개선 순서
1. `--out` 자동 생성 문제 해결
2. 검색 결과 관련성 점수 도입
3. 메타데이터 추출 정확도 개선
4. 테스트 추가
5. provider 분리

## 현재 상태 결론
- 프로그램은 실행된다
- JSON 결과도 생성된다
- 하지만 아직 “좋은 책/PDF 후보를 안정적으로 찾는 단계”까지는 못 갔다
- 지금 단계 평가는:
  - 실행 가능 프로토타입
  - 검색 품질/판단 품질 보강 필요
