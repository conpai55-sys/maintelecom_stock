"""
Telkit(utelkit.telkit.com) 자동 로그인 후 재고 데이터를 가져와
모델x색상별 수량으로 집계해서 stock_summary.json으로 저장하는 스크립트.

실행 전 준비:
  pip install playwright requests
  playwright install --with-deps chromium

환경변수로 로그인 정보를 넘겨서 실행합니다 (코드에 직접 아이디/비밀번호를 적지 마세요):
  TELKIT_USER=아이디 TELKIT_PASS=비밀번호 python login_and_fetch.py
"""

import os
import sys
import json
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta

import requests
from playwright.sync_api import sync_playwright

BASE_URL = "https://utelkit.telkit.com"
OUTPUT_FILE = "stock_summary.json"

# 재고로 집계할 상태 코드. 현재는 "매장재고"(1)만 포함.
# 다른 상태(예: 이동중, 판매완료 등)도 포함하고 싶으면 이 리스트에 추가하세요.
INCLUDE_STATUS_CODES = {1}


def get_session_cookies() -> dict:
    """헤드리스 브라우저로 로그인해서 세션 쿠키를 얻는다."""
    user = os.environ.get("TELKIT_USER")
    password = os.environ.get("TELKIT_PASS")
    if not user or not password:
        sys.exit("환경변수 TELKIT_USER / TELKIT_PASS 가 설정되어 있지 않습니다.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto(BASE_URL, wait_until="networkidle")

        # 로그인 폼: 아이디 input#input-59, 비밀번호 input#input-63, "LOGIN" 버튼
        page.wait_for_selector("#input-59", timeout=15000)
        page.fill("#input-59", user)
        page.fill("#input-63", password)
        page.click("text=LOGIN")

        # 로그인 후 대시보드가 뜰 때까지 대기
        page.wait_for_load_state("networkidle", timeout=20000)
        time.sleep(1)

        cookies = {c["name"]: c["value"] for c in context.cookies()}
        browser.close()

    if "laravel_session" not in cookies:
        sys.exit("로그인에 실패한 것 같습니다 (laravel_session 쿠키를 못 받음). "
                 "아이디/비밀번호 또는 로그인 폼 선택자를 확인하세요.")

    return cookies


def fetch_all_stock(cookies: dict) -> list:
    """재고 목록 API를 한 번에 모두 가져온다."""
    session = requests.Session()
    session.cookies.update(cookies)
    session.headers.update({
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": BASE_URL + "/",
    })

    params = [
        ("page", 1),
        ("status", "D"),
        ("sortDesc", "false"),
        ("search_several_type", 0),
        ("search_several_days", 0),
        ("status_code[]", 0),
        ("status_code[]", 1),
        ("status_code[]", 8),
        ("status_code[]", 99),
        ("useSession", 1),
        ("itemPerPage", 1000),  # 전체를 한 번에 받기 위해 크게 설정
    ]

    resp = session.get(f"{BASE_URL}/api/stockList", params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("data", [])


def aggregate(items: list) -> list:
    """모델 x 통신사 x 색상 별 수량 집계 (지정된 status_code만 포함)."""
    counts = defaultdict(int)

    for item in items:
        if not isinstance(item, dict):
            continue
        phone = item.get("tbl_pubphone")
        if not phone:
            continue
        if item.get("status_code") not in INCLUDE_STATUS_CODES:
            continue

        telecom = (phone.get("tbl_telecom") or {}).get("t_name") or "기타"
        model = phone.get("reg_name") or "모델명 없음"
        color_obj = (item.get("tbl_pubcolor") or {}).get("tbl_color") or {}
        color = color_obj.get("color_name") or "색상 없음"

        counts[(telecom, model, color)] += 1

    result = [
        {"telecom": telecom, "model": model, "color": color, "count": count}
        for (telecom, model, color), count in counts.items()
    ]
    result.sort(key=lambda r: (r["telecom"], r["model"], r["color"]))
    return result


def main():
    cookies = get_session_cookies()
    items = fetch_all_stock(cookies)
    summary = aggregate(items)

    kst = timezone(timedelta(hours=9))
    output = {
        "updated_at": datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S"),
        "total": sum(r["count"] for r in summary),
        "items": summary,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"저장 완료: 총 {output['total']}대, {len(summary)}개 그룹 -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
