import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta

# --- 1. 날짜 계산 (이번 주 월요일 ~ 금요일) ---
today = datetime.now()
monday = today - timedelta(days=today.weekday())
friday = monday + timedelta(days=4)
start_date_str = monday.strftime('%Y.%m.%d')
end_date_str = friday.strftime('%Y.%m.%d')

# --- 2. 방문할 URL 설정 ---
# 이번 주의 메뉴 페이지 주소를 직접 방문
url = f"https://www.sogang.ac.kr/ko/menu-life-info?startDate={start_date_str}&endDate={end_date_str}"

driver = None
try:
    print("봇 탐지 우회 드라이버를 시작합니다...")
    options = uc.ChromeOptions()
    # options.add_argument('--headless') # 필요시 주석 해제하여 백그라운드 실행
    driver = uc.Chrome(options=options)
    
    print(f"이번 주 메뉴 페이지({url})에 접속합니다...")
    driver.get(url)

    print("메뉴가 로드될 때까지 대기합니다...")
    wait = WebDriverWait(driver, 20)
    
    # '.menu-list' 영역이 화면에 나타날 때까지 기다림
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "menu-list")))
    
    print("메뉴 정보 추출을 시작합니다...")
    
    # XPath를 사용하여 '우정원' 텍스트를 포함하는 restaurant-name div의 부모인 restaurant div를 찾음
    woojungwon_xpath = "//div[contains(@class, 'restaurant-name') and contains(text(), '우정원')]/ancestor::div[contains(@class, 'restaurant')]"
    woojungwon_restaurant = wait.until(EC.presence_of_element_located((By.XPATH, woojungwon_xpath)))

    if woojungwon_restaurant:
        print(f"\n--- 우정원 주간 메뉴 ({start_date_str} ~ {end_date_str}) ---")
        # Selenium의 내장 기능을 사용하여 메뉴 아이템들을 직접 찾음
        menu_items = woojungwon_restaurant.find_elements(By.CLASS_NAME, "menu-item")
        if not menu_items:
            print("등록된 메뉴가 없습니다.")
        else:
            for item in menu_items:
                menu_date = item.find_element(By.CLASS_NAME, "menu-date").text
                menu_name = item.find_element(By.CLASS_NAME, "menu-name").text
                menu_price = item.find_element(By.CLASS_NAME, "menu-price").text
                print(f"[{menu_date}] {menu_name} ({menu_price})")
    else:
        print("이번 주의 우정원 메뉴 정보를 찾을 수 없습니다.")

except Exception as e:
    print(f"오류가 발생했습니다: {e}")

finally:
    if driver:
        print("\n드라이버를 종료합니다.")
        driver.quit()