import streamlit as st
import requests
import json
from openai import OpenAI

# --- НАЛАШТУВАННЯ ---
st.set_page_config(page_title="Football AI Predictor", page_icon="⚽")

# 🔑 ВАШІ КЛЮЧІ
# Ми вставили ваш ключ API-Football прямо сюди
API_FOOTBALL_KEY = "b18e20d5adf343097615699acff8d787" 
LEAGUE_ID = 39   # Англійська Прем'єр-ліга
SEASON = 2024    # Сезон 2024-2025

# --- ФУНКЦІЇ ---
def get_next_matches():
    """Отримує найближчі матчі з API-Football"""
    url = "https://v3.football.api-sports.io/fixtures"
    
    # Параметри запиту: Ліга 39, поточний сезон, наступні 10 ігор
    params = {
        "league": LEAGUE_ID,
        "season": SEASON,
        "next": 10
    }
    
    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': API_FOOTBALL_KEY
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        # Перевірка на помилки API
        if "errors" in data and data["errors"]:
            st.error(f"API Error: {data['errors']}")
            return []
            
        return data['response']
    except Exception as e:
        st.error(f"Помилка з'єднання: {e}")
        return []

def analyze_match(match_info, openai_key):
    """Відправляє дані матчу в OpenAI для прогнозу"""
    if not openai_key:
        return "⚠️ Будь ласка, введіть ваш OpenAI API Key у бічній панелі зліва, щоб отримати прогноз."
        
    client = OpenAI(api_key=openai_key)
    
    # Витягуємо назви команд
    home_team = match_info['teams']['home']['name']
    away_team = match_info['teams']['away']['name']
    date = match_info['fixture']['date']
    
    # Формуємо запит для ШІ
    prompt = f"""
    Ти професійний футбольний аналітик.
    Проаналізуй матч: {home_team} (Вдома) vs {away_team} (Виїзд).
    Дата: {date}.
    Ліга: Англійська Прем'єр-ліга.
    
    Завдання:
    1. Оціни шанси команд (у відсотках).
    2. Дай прогноз на результат (Перемога 1, Нічия, Перемога 2).
    3. Порекомендуй ризиковану ставку (наприклад, точний рахунок).
    
    Відповідай українською мовою, коротко і по суті. Використовуй жирний шрифт для головного.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Помилка OpenAI: {e}"

# --- ГОЛОВНИЙ ІНТЕРФЕЙС ---
st.title("⚽ Live Футбольний Асистент")
st.write("Цей додаток підтягує реальні матчі АПЛ та використовує ШІ для прогнозів.")

# Бічна панель для ключа OpenAI
st.sidebar.header("🔐 Налаштування AI")
openai_api_key = st.sidebar.text_input("Введіть OpenAI API Key", type="password")
st.sidebar.caption("Без цього ключа прогнози не працюватимуть.")

# 1. ЗАВАНТАЖЕННЯ МАТЧІВ
with st.spinner("Завантажуємо розклад матчів з Лондона..."):
    matches = get_next_matches()

if matches:
    # Створюємо гарний список для вибору
    # Формат: "Liverpool vs Arsenal"
    match_map = {f"{m['teams']['home']['name']} vs {m['teams']['away']['name']}": m for m in matches}
    
    selected_match_name = st.selectbox("Оберіть матч для аналізу:", list(match_map.keys()))
    
    # Отримуємо дані обраного матчу
    match_data = match_map[selected_match_name]
    
    st.divider()
    
    # Візуалізація матчу (Логотипи)
    col1, col2, col3 = st.columns([1, 0.5, 1])
    with col1:
        st.image(match_data['teams']['home']['logo'], width=80)
        st.write(f"**{match_data['teams']['home']['name']}**")
    with col2:
        st.write("### VS")
    with col3:
        st.image(match_data['teams']['away']['logo'], width=80)
        st.write(f"**{match_data['teams']['away']['name']}**")
        
    st.divider()

    # Кнопка прогнозу
    if st.button("🔮 Отримати прогноз AI"):
        with st.spinner("Аналізую статистику та новини команд..."):
            prediction = analyze_match(match_data, openai_api_key)
            
            st.subheader("Думка штучного інтелекту:")
            st.success("Аналіз завершено!")
            st.markdown(prediction)
            
            # Для налагодження (можна прибрати)
            with st.expander("Показати технічні дані (JSON)"):
                st.json(match_data)

else:
    st.info("На жаль, зараз немає запланованих матчів або вичерпано ліміт API.")