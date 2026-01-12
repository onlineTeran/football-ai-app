import requests
from supabase import create_client, Client
from openai import OpenAI
import time
from datetime import datetime

# 👇 Імпортуємо ваші ключі (переконайтеся, що вони в файлі my_secrets.py)
try:
    from my_secrets import SUPABASE_URL, SUPABASE_SERVICE_KEY, FOOTBALL_API_KEY, OPENAI_API_KEY
except ImportError:
    print("❌ Помилка: Не знайдено файл my_secrets.py. Створіть його!")
    exit()

# --- НАЛАШТУВАННЯ ---
LEAGUES = {
    39: "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    140: "La Liga 🇪🇸",
    135: "Serie A 🇮🇹",
    78: "Bundesliga 🇩🇪",
    61: "Ligue 1 🇫🇷"
}

# ✅ АКТУАЛЬНИЙ СЕЗОН (Для Січня 2026 це сезон 2025/2026)
SEASON = 2025 

# --- ПІДКЛЮЧЕННЯ ---
try:
    # Використовуємо SERVICE_KEY для запису в базу
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    print(f"❌ Критична помилка ключів: {e}")
    exit()

def generate_ai_prediction(home, away, date):
    """Генерує прогноз через OpenAI"""
    try:
        prompt = f"""
        Матч: {home} vs {away}. Дата: {date}.
        Ти професійний футбольний аналітик.
        1. Хто фаворит (у %)?
        2. Прогнозований точний рахунок.
        3. Найкраща ставка (наприклад: "Обидві заб'ють" або "П1").
        Відповідай українською, лаконічно.
        """
        response = client.chat.completions.create(
            model="gpt-4o", # Якщо маєте доступ до 4o, або gpt-3.5-turbo
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"⚠️ OpenAI помилка: {e}")
        return None

def sync_league(league_id, league_name):
    print(f"\n🏆 Ліга: {league_name}...")
    
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {'x-rapidapi-host': "v3.football.api-sports.io", 'x-rapidapi-key': FOOTBALL_API_KEY}
    
    # 1. ОТРИМУЄМО МИНУЛІ МАТЧІ (Архів результатів)
    try:
        params_last = {
            "league": league_id, 
            "season": SEASON,
            "last": 10,     # 10 останніх зіграних
            "status": "FT", # Тільки завершені
            "timezone": "Europe/Kiev"
        }
        resp_last = requests.get(url, headers=headers, params=params_last)
        data_last = resp_last.json().get('response', [])
        print(f"   ✅ Завантажено {len(data_last)} результатів.")
        save_matches(data_last, league_name, is_future=False)
    except Exception as e:
        print(f"   ❌ Помилка отримання минулих: {e}")

    # 2. ОТРИМУЄМО МАЙБУТНІ МАТЧІ (Календар + Прогнози)
    try:
        params_next = {
            "league": league_id, 
            "season": SEASON,
            "next": 10,     # 10 майбутніх ігор (Платна функція - тепер працює!)
            "timezone": "Europe/Kiev"
        }
        resp_next = requests.get(url, headers=headers, params=params_next)
        
        # Перевірка на помилки API
        if "errors" in resp_next.json() and resp_next.json()["errors"]:
             print(f"   ⚠️ API Error: {resp_next.json()['errors']}")
        
        data_next = resp_next.json().get('response', [])
        print(f"   🔮 Завантажено {len(data_next)} майбутніх матчів.")
        save_matches(data_next, league_name, is_future=True)
        
    except Exception as e:
        print(f"   ❌ Помилка отримання майбутніх: {e}")

def save_matches(matches_list, league_name, is_future):
    """Зберігає список матчів у Supabase"""
    if not matches_list:
        return

    for m in matches_list:
        match_id = m['fixture']['id']
        home = m['teams']['home']['name']
        away = m['teams']['away']['name']
        date = m['fixture']['date']
        status = m['fixture']['status']['short']
        
        # Логіка Прогнозу (тільки для майбутніх)
        prediction = None
        if is_future: 
            # Перевіряємо, чи вже є прогноз в базі
            existing = supabase.table("matches").select("prediction").eq("id", match_id).execute()
            
            if existing.data and existing.data[0].get('prediction'):
                prediction = existing.data[0]['prediction'] # Беремо існуючий
            else:
                print(f"      🤖 Генерую прогноз: {home} vs {away}...")
                prediction = generate_ai_prediction(home, away, date)
                # Маленька пауза, щоб не перевантажити OpenAI
                time.sleep(0.5) 
        
        # Формуємо запис
        record = {
            "id": match_id,
            "league": league_name,
            "country": m['league']['country'],
            "home_team": home,
            "away_team": away,
            "home_logo": m['teams']['home']['logo'],
            "away_logo": m['teams']['away']['logo'],
            "date": date,
            "status": status,
            "prediction": prediction,
            # Якщо матч завершено - пишемо рахунок, якщо ні - ставимо VS
            "ai_analysis": f"{m['goals']['home']}-{m['goals']['away']}" if status in ['FT', 'AET', 'PEN'] else "VS"
        }
        
        try:
            supabase.table("matches").upsert(record).execute()
        except Exception as e:
            print(f"      ❌ Помилка запису в базу: {e}")

if __name__ == "__main__":
    print(f"🚀 Старт оновлення (Сезон {SEASON})...")
    for lid, lname in LEAGUES.items():
        sync_league(lid, lname)
    print("\n✅ Оновлення завершено! Перевірте сайт.")