import streamlit as st
from supabase import create_client
from datetime import datetime

# 👇 Імпорт ключів
from my_secrets import SUPABASE_URL, SUPABASE_PUBLIC_KEY, AFFILIATE_LINK

st.set_page_config(page_title="Football Portal 2.0", page_icon="⚽", layout="wide")

@st.cache_resource
def init_db():
    # Для сайту використовуємо PUBLIC KEY (тільки читання)
    return create_client(SUPABASE_URL, SUPABASE_PUBLIC_KEY)

try:
    db = init_db()
except Exception as e:
    st.error(f"Помилка підключення до бази: {e}")
    st.stop()

# --- БІЧНА ПАНЕЛЬ ---
st.sidebar.title("🌍 Навігація")

try:
    response = db.table("matches").select("country").execute()
    countries = sorted(list(set([row['country'] for row in response.data]))) if response.data else []
    
    if not countries:
        st.sidebar.warning("База порожня. Запустіть backend_automation.py")
        selected_country = "Всі"
    else:
        selected_country = st.sidebar.selectbox("Оберіть країну:", ["Всі"] + countries)
except Exception as e:
    st.sidebar.error(f"Помилка: {e}")
    selected_country = "Всі"

try:
    if selected_country != "Всі":
        resp_leagues = db.table("matches").select("league").eq("country", selected_country).execute()
    else:
        resp_leagues = db.table("matches").select("league").execute()
    
    leagues = sorted(list(set([row['league'] for row in resp_leagues.data]))) if resp_leagues.data else []
    selected_league = st.sidebar.radio("Оберіть лігу:", leagues) if leagues else None
except:
    selected_league = None

# --- ГОЛОВНИЙ ЕКРАН ---
if selected_league:
    st.title(f"{selected_league}")
    
    matches_data = db.table("matches").select("*").eq("league", selected_league).order("date").execute().data
    
    future = [m for m in matches_data if m['status'] in ['NS', 'TBD']]
    past = [m for m in matches_data if m['status'] in ['FT', 'AET', 'PEN']]

    tab1, tab2 = st.tabs(["📅 Майбутні", "✅ Результати"])

    def show_card(m, is_future):
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([1, 2, 1, 2])
            
            try:
                dt = datetime.fromisoformat(m['date'].replace('Z', '+00:00'))
                d_str = dt.strftime("%d.%m %H:%M")
            except: d_str = m['date']
            
            with col1:
                st.caption(d_str)
                st.write(m['status'])
            with col2:
                c1, c2, c3 = st.columns([1, 0.5, 1])
                with c1: 
                    if m['home_logo']: st.image(m['home_logo'], width=40)
                    st.write(f"**{m['home_team']}**")
                with c2: 
                    st.markdown(f"<h3 style='text-align: center;'>{m['ai_analysis'] if not is_future else 'VS'}</h3>", unsafe_allow_html=True)
                with c3:
                    if m['away_logo']: st.image(m['away_logo'], width=40)
                    st.write(f"**{m['away_team']}**")
            
            if is_future:
                with col4:
                    if m.get('prediction'):
                        st.info(f"🤖 {m['prediction']}")
                        st.link_button("💰 Зробити ставку", AFFILIATE_LINK)
                    else:
                        st.caption("Очікуємо прогноз...")

    with tab1:
        if future:
            for m in future: show_card(m, True)
        else: st.info("Немає матчів.")

    with tab2:
        past.reverse()
        if past:
            for m in past: show_card(m, False)
        else: st.info("Немає результатів.")
else:
    st.write("👈 Оберіть лігу зліва")