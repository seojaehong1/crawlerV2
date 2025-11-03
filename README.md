## 다나와 카테고리 크롤러 (crawlerV2)

다나와 카테고리 페이지에서 상품 상세 정보를 수집하여 CSV로 저장하는 크롤러입니다. `Playwright`(Python) 기반으로 동작합니다.

### 사전 준비
- **Python 3.10+** 권장 (Windows 10/11에서 확인)
- **pip** 사용 가능
- 크롬(Chromium) 등 브라우저 바이너리는 Playwright가 자동 설치합니다

### 설치
```bash
# 1) (선택) 가상환경 생성
python -m venv .venv

# 2) 가상환경 활성화 (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# 3) 의존성 설치
pip install -r requirements.txt

# 4) Playwright 브라우저 설치 (Windows)
python -m playwright install
```

### 실행 방법 (기본)
```bash
python danawa_crawler.py --category-url "<다나와_카테고리_URL>" \
  --output danawa_output.csv \
  --items-per-page 20 \
  --max-total-items 100 \
  --delay-ms 600 \
  --headless
```

### 필수/선택 옵션
- **--category-url (필수)**: 크롤링할 다나와 카테고리 페이지 URL
- **--output (선택)**: 결과 CSV 파일 경로 (기본값: `danawa_output.csv`)
- **--items-per-page (선택)**: 각 페이지에서 방문할 최대 상품 수 (기본값: 0 → 제한 없음)
- **--max-total-items (선택)**: 전체 크롤링할 최대 상품 수 (기본값: 0 → 제한 없음)
- **--delay-ms (선택)**: 사람처럼 대기하는 기본 딜레이(ms) (기본값: 600)
- **--headless (선택 플래그)**: 헤드리스 모드로 실행 (창 표시 없이 실행)

### 출력 형식
생성된 CSV에는 아래 컬럼이 포함됩니다.
- `상품명`
- `URL`
- `상세정보` (사양/인증/등록일 등의 가공된 텍스트)

### 실행 완료 시 동작
크롤링이 완료되면:
- 수집된 데이터가 지정한 CSV 파일로 저장됩니다
- 브라우저(Chromium)가 **자동으로 종료**됩니다
- 프로그램이 정상적으로 종료됩니다

### 사용 예시
```bash
# 1) 창 표시(비헤드리스)로 페이지당 최대 10개만 수집
python danawa_crawler.py \
  --category-url "https://search.danawa.com/dsearch.php?query=%EC%9D%B4%EC%9C%A0%EC%8B%9D&cate_c1=431" \
  --items-per-page 10 \
  --output result.csv \
  --delay-ms 700

# 2) 헤드리스로 전체 제한 없이 빠르게 수집
python danawa_crawler.py \
  --category-url "https://search.danawa.com/dsearch.php?query=%EB%B0%98%EC%B0%AC" \
  --headless \
  --output quick.csv

# 3) 전체 최대 50개까지만 수집
python danawa_crawler.py \
  --category-url "https://search.danawa.com/dsearch.php?query=%EC%95%84%EA%B8%B0%EB%B0%A5" \
  --max-total-items 50 \
  --output top50.csv
```

### 팁 및 권장 설정
- **차단/에러 회피**: `--delay-ms` 값을 600~1200ms 사이로 적절히 늘리면 안정성이 올라갑니다.
- **디버깅**: 처음에는 `--headless`를 빼고 실행해 동작을 눈으로 확인하세요.
- **아이템 제한**: 개발·테스트 중에는 `--items-per-page`, `--max-total-items`를 작게 설정하세요.

### 오류/문제 해결
- `Timeout` 또는 빈 결과: 네트워크가 느리면 `--delay-ms`를 키우고, `--items-per-page`를 줄여보세요.
- 브라우저 관련 오류: `python -m playwright install`을 다시 실행하세요.
- PowerShell 실행 정책 오류: PowerShell을 관리자 권한으로 열고 `Set-ExecutionPolicy RemoteSigned` 후 재시도하세요.

### 주의 사항
- 대상 사이트의 이용약관/로봇정책을 준수하고, 과도한 요청을 지양하세요.
- 본 도구 사용으로 인한 책임은 사용자에게 있습니다.


