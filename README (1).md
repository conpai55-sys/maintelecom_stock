# 메인텔레콤 재고 현황판

거래처에 카톡 링크로 전달할 수 있는, 15분마다 자동 갱신되는 재고 현황 페이지입니다.

## 구성
- `login_and_fetch.py` — Telkit에 자동 로그인해서 재고 데이터를 가져와 모델x색상별로 집계, `stock_summary.json`으로 저장
- `index.html` — `stock_summary.json`을 읽어서 보여주는 웹페이지 (거래처가 보게 될 화면)
- `.github/workflows/update-stock.yml` — 15분마다 자동으로 `login_and_fetch.py`를 실행하는 설정
- `stock_summary.json` — 지금은 미리보기용 샘플 데이터. 실제 운영 시작하면 자동으로 덮어써집니다.

## 배포 방법 (무료, GitHub 이용)

1. **GitHub 저장소 만들기**
   - github.com 에서 새 저장소(Repository) 생성 (예: `main-telecom-stock`)
   - **Public**으로 설정해야 GitHub Actions를 무료로 무제한 사용할 수 있습니다.
   - 이 폴더 안의 파일들을 그대로 업로드하세요.

2. **로그인 정보를 안전하게 등록 (Secrets)**
   - 저장소 → Settings → Secrets and variables → Actions → New repository secret
   - `TELKIT_USER` : Telkit 로그인 아이디
   - `TELKIT_PASS` : Telkit 로그인 비밀번호
   - (비밀번호를 코드나 파일에 직접 적지 마세요. 반드시 이 Secrets 기능을 사용하세요.)

3. **GitHub Pages 켜기**
   - 저장소 → Settings → Pages
   - Source를 "Deploy from a branch" → Branch: `main` (또는 기본 브랜치), 폴더는 `/ (root)` 선택 → Save
   - 몇 분 뒤 `https://[계정이름].github.io/[저장소이름]/` 주소가 생깁니다. 이 링크를 거래처에 전달하면 됩니다.

4. **자동 갱신 확인**
   - 저장소 → Actions 탭에서 `Update Stock Dashboard` 워크플로우가 15분마다 실행되는지 확인
   - 처음엔 "Run workflow" 버튼으로 수동 실행해서 정상 동작하는지 먼저 테스트해보세요.

## 로컬에서 먼저 테스트하는 방법

```bash
pip install playwright requests
playwright install --with-deps chromium

TELKIT_USER=아이디 TELKIT_PASS=비밀번호 python login_and_fetch.py
```

실행 후 `stock_summary.json`이 실제 데이터로 갱신됐는지 확인하고,

```bash
python -m http.server 8000
```

으로 로컬 서버를 띄운 뒤 브라우저에서 `http://localhost:8000` 접속하면 화면을 미리 볼 수 있습니다.
(index.html을 더블클릭해서 직접 여는 방식은 브라우저 보안 정책 때문에 데이터를 못 불러올 수 있어요.)

## 참고
- 현재는 "매장재고"(status_code=1) 기준으로만 집계합니다. `login_and_fetch.py`의 `INCLUDE_STATUS_CODES`를 수정하면 다른 상태도 포함할 수 있어요.
- 세션은 2시간마다 만료되지만, 매번 새로 로그인하는 방식이라 문제 없습니다.
- GitHub Actions 무료 사용량: Public 저장소는 완전 무료입니다.
