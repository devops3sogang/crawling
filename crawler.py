import requests
from datetime import datetime, timedelta
import json  # JSON 라이브러리를 가져옵니다.

# --- 1. 날짜 계산 (이번 주 월요일 ~ 금요일) ---
#today = datetime.now()
#monday = today - timedelta(days=today.weekday())
#friday = monday + timedelta(days=4)
#start_date_str = monday.strftime('%Y.%m.%d')
#end_date_str = friday.strftime('%Y.%m.%d')


# 연휴로 식당메뉴가 없어 디버깅용
# --- 1. 날짜 계산 (지난 주 월요일 ~ 금요일) ---
today = datetime.now()
a_day_in_last_week = today - timedelta(days=7) # 오늘 날짜에서 7일을 뺌
monday = a_day_in_last_week - timedelta(days=a_day_in_last_week.weekday())
friday = monday + timedelta(days=4)
start_date_str = monday.strftime('%Y.%m.%d')
end_date_str = friday.strftime('%Y.%m.%d')

# --- 2. 세션 및 헤더 설정 ---
session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Referer': 'https://www.sogang.ac.kr/ko/menu-life-info'
}
session.headers.update(headers)

# --- 3. API 주소 및 Payload 정의 ---
api_url = "https://www.sogang.ac.kr/api/api/v1/mainKo/menuList"
payload = {
    'configId': 1,
    'stDate': start_date_str,
    'enDate': end_date_str
}

try:
    print(f"API({api_url})에 POST 방식으로 데이터를 요청합니다...")
    
    response = session.post(api_url, json=payload)
    response.raise_for_status()
    raw_data = response.json()

    # --- 4. JSON 파일로 저장 ---
    # 'menu.json' 파일을 쓰기('w') 모드로 열고, 인코딩은 'utf-8'로 설정
    with open('menu.json', 'w', encoding='utf-8') as f:
        # json.dump()를 사용하여 파이썬 딕셔너리(raw_data)를 파일(f)에 저장
        # ensure_ascii=False: 한글이 깨지지 않게 해주는 중요한 옵션
        # indent=4: 보기 좋게 4칸씩 들여쓰기해서 저장
        json.dump(raw_data, f, ensure_ascii=False, indent=4)
    
    print("\n'menu.json' 파일 저장이 완료되었습니다.")
    

except requests.exceptions.RequestException as e:
    print(f"웹사이트 접속 중 오류가 발생했습니다: {e}")
except Exception as e:
    print(f"데이터 처리 중 오류가 발생했습니다: {e}")