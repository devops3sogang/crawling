# -*- coding: utf-8 -*-
import requests
from datetime import datetime, timedelta
import json
import calendar

# --- 날짜 계산 및 설정 ---

# 연휴로 식당메뉴가 없어 디버깅용 (지난 주 월요일 ~ 금요일)
today = datetime.now()
a_day_in_last_week = today - timedelta(days=7) 
monday = a_day_in_last_week - timedelta(days=a_day_in_last_week.weekday())
friday = monday + timedelta(days=4)

# MongoDB 스키마에 사용할 날짜 형식
week_start_date_str = monday.strftime('%Y-%m-%d')
api_start_date_str = monday.strftime('%Y.%m.%d')
api_end_date_str = friday.strftime('%Y.%m.%d')

# 요일 한글 매핑
WEEKDAY_KR = ['월', '화', '수', '목', '금', '토', '일']

# --- 세션 및 API 정의 ---
session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Referer': 'https://www.sogang.ac.kr/ko/menu-life-info'
}
session.headers.update(headers)

api_url = "https://www.sogang.ac.kr/api/api/v1/mainKo/menuList"
payload = {
    'configId': 1,
    'stDate': api_start_date_str,
    'enDate': api_end_date_str
}

try:
    print(f"API({api_url})에 POST 방식으로 데이터를 요청합니다...")
    
    response = session.post(api_url, json=payload)
    response.raise_for_status()
    raw_data = response.json()

    # --- 4. 데이터 정리 및 MongoDB 형식 변환 ---
    
    # 4-1. 식당 고정 정보 (restaurants 컬렉션용)
    # MongoDB ObjectID 등은 DB 삽입 시 자동으로 생성되므로 여기에 포함하지 않습니다.
    origin_info = raw_data['data']['origin'].replace('<br>\n', '\n').replace('<br>', '\n').strip()

    restaurant_info = {
        "name": "우정원",
        "type": "ON_CAMPUS",
        "category": "학생식당",
        "address": "서울특별시 마포구 백범로 35",
        "location": {
            "type": "Point",
            "coordinates": [126.9410, 37.5509]
        },
        # MongoDB 템플릿에 맞추기 위해 origin 정보를 별도 필드로 추가
        "origin_data": origin_info 
    }

    # 4-2. 메뉴 리스트 (menus 컬렉션용)
    daily_menus = []
    
    for day_menu in raw_data['data']['menuList']:
        # 날짜 포맷팅: 'YYYY.MM.DD' -> 'YYYY-MM-DD'
        date_obj = datetime.strptime(day_menu['menuDate'], '%Y.%m.%d')
        date_str = date_obj.strftime('%Y-%m-%d')
        day_of_week_kr = WEEKDAY_KR[date_obj.weekday()]

        meals_data = []
        for category_info in day_menu['menuInfo']:
            # <br> 태그를 기준으로 메뉴를 리스트로 분리하고, 공백/탭/빈 문자열 제거
            menu_items = [
                item.strip() 
                for item in category_info['menu'].split('<br>') 
                if item.strip()
            ]
            
            meals_data.append({
                "corner": category_info['category'],
                "items": menu_items
            })
        
        # dailyMenus 배열의 객체 생성
        daily_menus.append({
            "date": date_str,
            "dayOfWeek": day_of_week_kr,
            "meals": meals_data
        })

    # MongoDB Menu Collection의 최종 스키마에 맞춥니다.
    weekly_menus_data = {
        # **주의: restaurantId는 DB 삽입 후 알 수 있으므로, 임시로 0을 넣어둡니다.**
        "restaurantId": 0, 
        "restaurantName": "우정원",
        "weekStartDate": week_start_date_str,
        "dailyMenus": daily_menus
    }
    
    # --- 5. JSON 파일로 저장 ---

    # 식당 고정 정보 저장
    with open('restaurant_info.json', 'w', encoding='utf-8') as f:
        json.dump(restaurant_info, f, ensure_ascii=False, indent=4)
    print("\n'restaurant_info.json' 파일 저장이 완료되었습니다. (식당 고정 정보)")

    # 주간 메뉴 리스트 저장
    with open('weekly_menus.json', 'w', encoding='utf-8') as f:
        json.dump(weekly_menus_data, f, ensure_ascii=False, indent=4)
    print("'weekly_menus.json' 파일 저장이 완료되었습니다. (주간 메뉴 목록)")


except requests.exceptions.RequestException as e:
    print(f"웹사이트 접속 중 오류가 발생했습니다: {e}")
except Exception as e:
    print(f"데이터 처리 중 오류가 발생했습니다: {e}")
