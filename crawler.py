import requests
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

BACKEND_LOGIN_API = "http://localhost:8080/api/auth/login"
BACKEND_ONCAMPUSMENU_API = "http://localhost:8080/api/on-campus-menus"
BACKEND_RESTAURANTS_API = "http://localhost:8080/api/restaurants/MAIN_CAMPUS/menu"
BACKEND_ADMIN_RESTAURANTS_API = "http://localhost:8080/api/admin/restaurants/MAIN_CAMPUS"


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

def get_admin_token():
    login_payload = {
        "email": "admin@sogang.ac.kr",
        "password": "Devops3sogang!"
    }

    try:
        res = requests.post(BACKEND_LOGIN_API, json=login_payload)
        res.raise_for_status()
        token = res.json().get("accessToken")
        if not token:
            raise ValueError("로그인 응답에 accessToken이 없습니다.")
        return token
    except Exception as e:
        print(f"[오류] 관리자 로그인 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_existing_menu(token):
    res = requests.get(BACKEND_RESTAURANTS_API)
    res.raise_for_status()
    restaurant_data = res.json()
    return restaurant_data

def merge_menus(existing_menu, crawled_item_names):
    merged_menu = existing_menu.copy()
    for item_name in crawled_item_names:
        if not any(m['name'] == item_name for m in existing_menu):
            merged_menu.append({
                "id": str(uuid.uuid4()),
                "name": item_name,
                "price": 0
            })
    return merged_menu

def update_restaurant_menu(token, merged_menu):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": "서강대학교 우정원 학생식당",
        "type": "ON_CAMPUS",
        "category": "한식",
        "address": "서강대학교 우정원",
        "location": {"type": "Point", "coordinates": [126.936, 37.556]},
        "menu": merged_menu
    }
    res = requests.put(BACKEND_ADMIN_RESTAURANTS_API, json=payload, headers=headers)
    res.raise_for_status()
    print("[성공] 메뉴 업데이트 완료")


def crawl_on_campus():
    res = requests.get(BACKEND_RESTAURANTS_API)
    res.raise_for_status()
    main_campus_menu = res.json() 
    
    new_items = []

    try:
        print(f"요청 → {API_URL}")
        response = session.post(API_URL, json=payload)
        response.raise_for_status()

        raw = response.json()
        menus = raw.get("data", {}).get("menuList", [])

        if not menus:
            print("[오류] menuList 없음")
            return None, []

        daily_menus_dict = defaultdict(list)
        crawled_item_names = []

        for day in menus:
            date_str = day.get("menuDate", "")
            if not date_str:
                continue
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

                item_list = []
                for item_name in items:
                    crawled_item_names.append(item_name)
                    existing = next((m for m in main_campus_menu if m['name'] == item_name), None)
                    if existing:
                        item_id = existing['id']
                    else:
                        item_id = str(uuid.uuid4())
                        main_campus_menu.append({"id": item_id, "name": item_name, "price": 0})
                        new_items.append({"id": item_id, "name": item_name, "price": 0})
                    
                    item_list.append({"id": item_id, "name": item_name, "price": 0})

                if item_list:  # 메뉴 항목이 있을 때만 추가
                    daily_menus_dict[date_normalized].append({
                        "category": info.get("category", "").strip(),
                        "items": item_list,
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

        return result, new_items

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
        res = requests.post(BACKEND_ONCAMPUSMENU_API, json=menu_doc, timeout=10)
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
    global ADMIN_TOKEN
    ADMIN_TOKEN = get_admin_token()
    if not ADMIN_TOKEN:
        print("관리자 권환 획득 실패")
        return
    
    existing_menu = get_existing_menu(ADMIN_TOKEN)
    
    crawled_data, new_items = crawl_on_campus()
    if not crawled_data:
        print("저장할 메뉴 없음 (크롤링 실패 or 데이터 없음)")
        return

    merged_menu = merge_menus(existing_menu, [item['name'] for item in new_items])
    update_restaurant_menu(ADMIN_TOKEN, merged_menu)
    
    save_to_backend(crawled_data)


if __name__ == "__main__":
    main()