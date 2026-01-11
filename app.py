import streamlit as st
from supabase import create_client, Client
from openai import OpenAI
from datetime import datetime

# --- НАЛАШТУВАННЯ ---
st.set_page_config(page_title="PRO Football Predictor", page_icon="⚽", layout="centered")

# 🔑 КЛЮЧІ (Скопіюйте їх з sync_data.py!)
SUPABASE_URL = "https://hljqlfdcgygvdzpjfxrc.supabase.co"
SUPABASE_KEY = "sb_publishable_mHZtkCXmsCLBR0hqr9Bd4Q_L-QfLUqi"

# Ваше партнерське посилання
AFFILIATE_LINK = "https://favbet.com/uk/register/" 

# --- ПІДКЛЮЧЕННЯ ДО БАЗИ ---
# @st.cache_resource тримає з'єднання відкритим, щоб сайт працював швидко
@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Помилка підключення до бази: {e}")
        return None

supabase = init_connection()

# --- ФУНКЦІЇ ---
def get_matches_from_db():
    """Читає матчі з нашої бази Supabase (це безкоштовно!)"""
    if not supabase:
        return []
    
    # Вибираємо всі матчі, сортуємо за датою
    try:
        response = supabase.table("matches").select("*").order("date").execute()
        return response.data
    except Exception as e:
        st.error(f"Помилка читання бази: {e}")
        return []

def get_ai_prediction(match, openai_key):
    """Генерує прогноз через AI"""
    if not openai_key:
        return "⚠️ Введіть OpenAI API Key у меню зліва."
        
    client = OpenAI(api_key=openai_key)
    
    prompt = f"""
    Проаналізуй матч: {match['home_team']} vs {match['away_team']}.
    Дата: {match['date']}.
    Дай прогноз переможця та пораду для ставки.
    Пиши коротко, українською.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Помилка OpenAI: {e}"

# --- ІНТЕРФЕЙС ---
st.title("⚽ PRO Bet Analytics")
st.caption("Дані завантажені з вашої Database ⚡")

# Сайдбар
st.sidebar.header("⚙️ Налаштування")
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")

# Отримуємо дані з бази
matches = get_matches_from_db()

if matches:
    # Випадаючий список
    # Форматуємо дату для краси: 2025-02-15T14:30 -> 15.02 14:30
    match_map = {}
    for m in matches:
        date_obj = datetime.fromisoformat(m['date'].replace('Z', '+00:00'))
        date_str = date_obj.strftime("%d.%m %H:%M")
        name = f"{m['home_team']} vs {m['away_team']} ({date_str})"
        match_map[name] = m
    
    selected_name = st.selectbox("Оберіть матч:", list(match_map.keys()))
    
    if selected_name:
        match = match_map[selected_name]
        
        st.divider()
        
        # Відображення команд
        c1, c2, c3 = st.columns([1, 0.6, 1])
        with c1:
            st.image(match['home_logo'], width=70)
            st.markdown(f"**{match['home_team']}**")
        with c2:
            st.markdown("<h3 style='text-align: center;'>VS</h3>", unsafe_allow_html=True)
            # Показуємо час
            dt = datetime.fromisoformat(match['date'].replace('Z', '+00:00'))
            st.markdown(f"<p style='text-align: center;'>{dt.strftime('%H:%M')}</p>", unsafe_allow_html=True)
        with c3:
            st.image(match['away_logo'], width=70)
            st.markdown(f"**{match['away_team']}**")
            
        st.divider()

        # Кнопка прогнозу
        if st.button("🔮 Згенерувати прогноз"):
            with st.spinner("AI думає..."):
                prediction = get_ai_prediction(match, openai_api_key)
                st.success("Прогноз готовий!")
                st.info(prediction)
                
                st.markdown("---")
                st.link_button("💰 ЗРОБИТИ СТАВКУ", AFFILIATE_LINK, type="primary", use_container_width=True)

else:
    st.warning("База даних порожня! Запустіть скрипт sync_data.py локально, щоб оновити дані.")