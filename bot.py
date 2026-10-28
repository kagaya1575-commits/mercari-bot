ython
import os
import time
import requests

# ================= [여기에 본인 설정 입력] =================
# 1. 디스코드 웹훅 주소를 아래 따옴표 안에 붙여넣으세요
DISCORD_WEBHOOK_URL = "여기에_디스코드_웹훅_주소_붙여넣기"

# 2. 찾고 싶은 검색어 (일본어로 적어야 정확합니다)
KEYWORD = "ピカチュウ"  

# 3. 최대 가격 설정 (엔화 기준, 0이면 상한선 없음)
MAX_PRICE = 5000  

# 4. 검색 주기 (초 단위: 90초 권장)
CHECK_INTERVAL = 90
# ==========================================================

SEEN_FILE = "seen_items.txt"

def load_seen_items():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_seen_item(item_id):
    with open(SEEN_FILE, "a", encoding="utf-8") as f:
        f.write(f"{item_id}\n")

def send_discord(item):
    data = {
        "embeds": [
            {
                "title": f"🔔 새 매물: {item['name']}",
                "url": f"https://jp.mercari.com/item/{item['id']}",
                "description": f"**가격:** ¥{item['price']:,}",
                "color": 15105570,
                "image": {"url": item.get("thumbnail", "")}
            }
        ]
    }
    try:
        res = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"디스코드 전송 실패: {e}")

def check_mercari():
    print(f"[{time.strftime('%H:%M:%S')}] 메루카리 매물 확인 중... (검색어: {KEYWORD})")
    seen_items = load_seen_items()

    params = {
        "keyword": KEYWORD,
        "status": "on_sale",
        "sort": "created_time",
        "order": "desc"
    }
    if MAX_PRICE > 0:
        params["price_max"] = MAX_PRICE

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get("https://api.mercari.jp/items/search", params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            items = response.json().get("data", [])
            for item in items:
                item_id = item.get("id")
                if not item_id or item_id in seen_items:
                    continue

                item_info = {
                    "id": item_id,
                    "name": item.get("name", "이름 없음"),
                    "price": int(item.get("price", 0)),
                    "thumbnail": item.get("thumbnails", [""])[0] if item.get("thumbnails") else ""
                }
                
                print(f"-> 새 매물 발견: {item_info['name']} (¥{item_info['price']})")
                send_discord(item_info)
                save_seen_item(item_id)
                seen_items.add(item_id)
        elif response.status_code == 403:
            print("접근이 일시 차단되었습니다. 다음 주기에 재시도합니다.")
        else:
            print(f"메루카리 응답 상태 코드: {response.status_code}")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    print("=== 메루카리 디스코드 알림 봇 시작 ===")
    while True:
        check_mercari()
        time.sleep(CHECK_INTERVAL)
