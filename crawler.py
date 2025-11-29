import requests
from datetime import datetime, timedelta

BACKEND_API = "http://localhost:8080/api/on-campus-menus"

# --- 날짜 계산 (이번 주 월요일~금요일) ---
today = datetime.now()
monday = today - timedelta(days=today.weekday())
friday = monday + timedelta(days=4)
start_date_str = monday.strftime('%Y.%m.%d')
end_date_str = friday.strftime('%Y.%m.%d')

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
            print("❌ menuList 없음")
            return []

        result = {
            "weekStartDate": monday.strftime('%Y-%m-%d'),
            "menus": []
        }

        for day in menus:
            date = day.get("menuDate")
            for info in day.get("menuInfo", []):
                items = (
                    info.get("menu", "")
                    .replace("<br>", "\n")
                    .replace("<br/>", "\n")
                    .split("\n")
                )
                items = [x.strip() for x in items if x.strip()]

                result["menus"].append({
                    "date": date,
                    "category": info.get("category"),
                    "items": items
                })

        return result

    except Exception as e:
        print(f"크롤링 실패: {e}")
        return []


def save_to_backend(crawled_data):
    menu_doc = {
        "restaurantId": "MAIN_CAMPUS",  # 적절한 ID 설정
        "restaurantName": "서강대학교 학생식당",
        "weekStartDate": crawled_data["weekStartDate"],
        "dailyMenus": []
    }

    for day in crawled_data["menus"]:
        daily_menu = {
            "date": day["date"].replace(".", "-"),
            "dayOfWeek": "",
            "meals": [
                {
                    "corner": "",
                    "category": day["category"],
                    "items": day["items"],
                    "price": 0
                }
            ]
        }
        menu_doc["dailyMenus"].append(daily_menu)
    
    print(f"📤 전송할 데이터: {menu_doc}")

    try:
        res = requests.post(BACKEND_API, json=menu_doc, timeout=10)
        print(f"📊 Status Code: {res.status_code}")
        print(f"📄 Response Headers: {res.headers}")
        print(f"📝 Response Body: {res.text}")
        res.raise_for_status()
        print("✅ 저장 성공")
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 에러: {e}")
        print(f"Response: {res.text}")
    except Exception as e:
        print(f"❌ 저장 실패: {e}")

def main():
    menu_doc = crawl_on_campus()
    if not menu_doc:
        print("저장할 메뉴 없음 (크롤링 실패 or 데이터 없음)")
        return

    save_to_backend(menu_doc)


if __name__ == "__main__":
    main()