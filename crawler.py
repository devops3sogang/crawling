import requests
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

BACKEND_API = "http://localhost:8080/api/on-campus-menus"

# --- 날짜 계산 (이번 주 월요일~금요일) ---
today = datetime.now()
monday = today - timedelta(days=today.weekday())
friday = monday + timedelta(days=4)
start_date_str = monday.strftime('%Y.%m.%d')
end_date_str = friday.strftime('%Y.%m.%d')

# 요일 한글 매핑
WEEKDAY_KOR = {
    0: "월요일",
    1: "화요일",
    2: "수요일",
    3: "목요일",
    4: "금요일",
    5: "토요일",
    6: "일요일"
}

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.sogang.ac.kr/ko/menu-life-info"
})

API_URL = "https://www.sogang.ac.kr/api/api/v1/mainKo/menuList"
payload = {
    "configId": 1,
    "stDate": start_date_str,
    "enDate": end_date_str
}

def crawl_on_campus():
    try:
        print(f"요청 → {API_URL}")
        response = session.post(API_URL, json=payload)
        response.raise_for_status()

        raw = response.json()
        menus = raw.get("data", {}).get("menuList", [])

        if not menus:
            print("[오류] menuList 없음")
            return None

        # 날짜별로 메뉴를 그룹화
        daily_menus_dict = defaultdict(list)

        for day in menus:
            date_str = day.get("menuDate", "")  # YYYY.MM.DD 형식
            if not date_str:
                continue

            # 날짜 형식 변환: YYYY.MM.DD → YYYY-MM-DD
            date_normalized = date_str.replace(".", "-")

            for info in day.get("menuInfo", []):
                raw_items = (
                    info.get("menu", "")
                    .replace("<br>", "\n")
                    .replace("<br/>", "\n")
                    .split("\n")
                )

                items = []
                for line in raw_items:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("[") and line.endswith("]"):
                        continue
                    if len(line) <= 2 and not any(ch.isalnum() for ch in line):
                        continue
                    if "운영없음" in line or "운영 없음" in line:
                        continue
                    items.append(line)

                if items:  # 메뉴 항목이 있을 때만 추가
                    daily_menus_dict[date_normalized].append({
                        "category": info.get("category", "").strip(),
                        "items": [
                            { "id": str(uuid.uuid4()), "name": item, "price": 0 }
                            for item in items
                        ],
                        "price": 0
                    })

        # DailyMenu 리스트 생성
        daily_menus = []
        for date_str in sorted(daily_menus_dict.keys()):
            # 날짜로부터 요일 계산
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            day_of_week = WEEKDAY_KOR[date_obj.weekday()]

            daily_menus.append({
                "date": date_str,
                "dayOfWeek": day_of_week,
                "meals": daily_menus_dict[date_str]
            })

        result = {
            "weekStartDate": monday.strftime('%Y-%m-%d'),
            "dailyMenus": daily_menus
        }

        return result

    except Exception as e:
        print(f"크롤링 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_to_backend(crawled_data):
    menu_doc = {
        "restaurantId": "MAIN_CAMPUS",
        "restaurantName": "서강대학교 우정원 학생식당",
        "weekStartDate": crawled_data["weekStartDate"],
        "dailyMenus": crawled_data["dailyMenus"]
    }

    print(f"[전송] 데이터: {menu_doc}")

    try:
        res = requests.post(BACKEND_API, json=menu_doc, timeout=10)
        print(f"[응답] Status Code: {res.status_code}")
        print(f"[응답] Headers: {res.headers}")
        print(f"[응답] Body: {res.text}")
        res.raise_for_status()
        print("[성공] 저장 완료")
    except requests.exceptions.HTTPError as e:
        print(f"[오류] HTTP 에러: {e}")
        print(f"Response: {res.text}")
    except Exception as e:
        print(f"[오류] 저장 실패: {e}")

def main():
    menu_doc = crawl_on_campus()
    if not menu_doc:
        print("저장할 메뉴 없음 (크롤링 실패 or 데이터 없음)")
        return

    save_to_backend(menu_doc)


if __name__ == "__main__":
    main()