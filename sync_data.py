import requests
from supabase import create_client, Client
import json

# --- ⚙️ КОНФІГУРАЦІЯ ---
# 1. Ключ від API-Football (той самий, що був)
FOOTBALL_API_KEY = "b18e20d5adf343097615699acff8d787" 

# 2. Ключі від SUPABASE (Див. Project Settings -> API)
# URL проекту (починається на https://...)
SUPABASE_URL = "https://hljqlfdcgygvdzpjfxrc.supabase.co" 
# SERVICE_ROLE KEY (Він довгий. Беріть саме service_role, щоб могти писати в базу)
SUPABASE_KEY = "sb_publishable_mHZtkCXmsCLBR0hqr9Bd4Q_L-QfLUqi" 

# Налаштування ліги
LEAGUE_ID = 39   # АПЛ
SEASON = 2025    # Поточний сезон

# --- 🚀 ЛОГІКА ---

# Підключення до бази
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def sync_matches():
    print("🔄 Підключаюся до API-Football...")
    
    url = "https://v3.football.api-sports.io/fixtures"
    
    # Беремо 20 найближчих матчів
    params = {
        "league": LEAGUE_ID,
        "season": SEASON,
        "next": 20,
        "timezone": "Europe/Kiev"
    }
    
    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': FOOTBALL_API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        # Перевірка на помилки тарифу
        if "errors" in data and data["errors"]:
            print(f"❌ Помилка API: {data['errors']}")
            return

        matches_list = data.get('response', [])
        print(f"📥 Завантажено {len(matches_list)} матчів. Записую в базу...")

        count = 0
        for m in matches_list:
            # Формуємо рядок для таблиці (імена полів як у SQL скрипті)
            match_record = {
                "id": m['fixture']['id'], 
                "home_team": m['teams']['home']['name'],
                "away_team": m['teams']['away']['name'],
                "home_logo": m['teams']['home']['logo'],
                "away_logo": m['teams']['away']['logo'],
                "date": m['fixture']['date'],
                "status": m['fixture']['status']['short']
                # prediction залишаємо порожнім, його заповнить інший скрипт або кнопка на сайті
            }
            
            # UPSERT: Якщо матч вже є - оновить його, якщо немає - створить.
            # Це геніальна функція, яка не створює дублікатів!
            supabase.table("matches").upsert(match_record).execute()
            count += 1
            
        print(f"✅ Успіх! Оновлено/Додано {count} матчів у Supabase.")

    except Exception as e:
        print(f"❌ Критична помилка: {e}")

if __name__ == "__main__":
    sync_matches()