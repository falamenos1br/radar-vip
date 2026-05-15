import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Radar VIP - Agência Pro", layout="wide")
st.markdown("""<style>.stApp { background-color: #0b0e14; } .stDataFrame { background-color: #161a23; } h1 { color: #f1c40f !important; text-align: center; font-weight: 800; } .stButton>button { background: linear-gradient(90deg, #f39c12, #e67e22); color: white; font-weight: bold; width: 100%; border-radius: 8px; height: 50px; }</style>""", unsafe_allow_html=True)

st.title("🎯 MASTER RADAR VIP: EDIÇÃO AGÊNCIA")
status = st.empty()

# --- DICIONÁRIO DE TRADUÇÃO DE PAÍSES ---
TRADUCAO_PAISES = {
    "Brazil": "Brasil", "Germany": "Alemanha", "England": "Inglaterra", "Spain": "Espanha",
    "Italy": "Itália", "France": "França", "Portugal": "Portugal", "Netherlands": "Holanda",
    "Argentina": "Argentina", "Uruguay": "Uruguai", "Mexico": "México", "USA": "EUA",
    "Saudi Arabia": "Arábia Saudita", "Japan": "Japão", "South Korea": "Coreia do Sul",
    "Norway": "Noruega", "Sweden": "Suécia", "Finland": "Finlândia", "Greece": "Grécia",
    "Scotland": "Escócia", "Austria": "Áustria", "Switzerland": "Suíça", "China": "China"
}

def traduzir_liga_e_pais(sport_title):
    # Se tiver " - ", separa Liga e País
    if " - " in sport_title:
        liga, pais_en = sport_title.split(" - ", 1)
        pais_pt = TRADUCAO_PAISES.get(pais_en, pais_en)
        return liga, pais_pt
    # Se não tiver, é continental ou especial
    return sport_title, None

# --- FUNÇÃO SECRETS ---
def get_secret(key, default=""):
    try: return st.secrets[key]
    except: return default

# --- PAINEL LATERAL ---
with st.sidebar:
    st.markdown("### 🔑 Chaves de Acesso")
    opcao_api = st.selectbox("Escolher conta da API:", ["Conta 1", "Conta 2", "Conta 3", "Conta 4"])
    
    # Mapeamento das 4 contas
    api_map = {"Conta 1": "api_key_1", "Conta 2": "api_key_2", "Conta 3": "api_key_3", "Conta 4": "api_key_4"}
    api_key_padrao = get_secret(api_map[opcao_api])
    api_key = st.text_input(f"Chave {opcao_api}:", value=api_key_padrao, type="password")
    
    st.markdown("---")
    st.markdown("### 📅 Filtros")
    data_alvo = st.date_input("Jogos do dia:", value=datetime.now().date() + timedelta(days=1))
    
    col1, col2 = st.columns(2)
    with col1: min_f = st.number_input("Min Fav", value=1.25, step=0.05)
    with col2: max_f = st.number_input("Max Fav", value=1.55, step=0.05)
    min_z = st.number_input("Min Zebra", value=4.50, step=0.10)
    
    st.markdown("---")
    st.markdown("### ✈️ Telegram")
    t_token = st.text_input("Bot Token:", value=get_secret("bot_token"), type="password")
    t_id = st.text_input("Chat ID:", value=get_secret("chat_id"))
    
    btn_scan = st.button("🚀 INICIAR BUSCA")

# Gestão de Créditos (Estado da Sessão)
if 'creditos_restantes' not in st.session_state: st.session_state.creditos_restantes = "---"
if 'creditos_usados' not in st.session_state: st.session_state.creditos_usados = "---"

st.sidebar.info(f"💳 Créditos Restantes: {st.session_state.creditos_restantes}")

# Configuração de Tempo
tz_br = timezone(timedelta(hours=-3))
ini_utc = datetime(data_alvo.year, data_alvo.month, data_alvo.day, 0, 0, 0, tzinfo=tz_br).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
fim_utc = datetime(data_alvo.year, data_alvo.month, data_alvo.day, 23, 59, 59, tzinfo=tz_br).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

@st.cache_data(ttl=3600)
def get_ligas_futebol(chave):
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={chave}"
    try:
        res = requests.get(url).json()
        # Bloqueio estrito de divisões inferiores
        bloqueio = ["championship", "league_one", "league_two", "liga_2", "division_2", "bundesliga_2", "serie_b", "serie_c", "3. liga", "la liga 2"]
        continentais = ["uefa", "conmebol", "afc", "caf", "concacaf", "champions", "libertadores", "sudamericana"]
        
        selecionadas = []
        for liga in res:
            k, t = liga['key'].lower(), liga['title'].lower()
            if "soccer" not in k: continue
            if "brazil" in k or any(c in k or c in t for c in continentais):
                selecionadas.append(liga['key'])
            elif not any(b in k or b in t for b in bloqueio):
                selecionadas.append(liga['key'])
        return selecionadas
    except: return []

def scan_odds(chave, ligas, d_ini, d_fim, min_f, max_f, min_z):
    jogos = []
    prog = st.progress(0)
    casas = ["betano", "betfair_ex_eu", "betfair_sb_uk", "bet365"]
    creditos_consumidos = 0
    
    for i, l_key in enumerate(ligas):
        url = f"https://api.the-odds-api.com/v4/sports/{l_key}/odds/?apiKey={chave}&regions=eu&markets=h2h&commenceTimeFrom={d_ini}&commenceTimeTo={d_fim}"
        try:
            response = requests.get(url)
            # Atualiza créditos a cada chamada
            st.session_state.creditos_restantes = response.headers.get('x-requests-remaining', "---")
            creditos_consumidos += 1
            
            res = response.json()
            for jogo in res:
                book = next((b for b in jogo.get("bookmakers", []) if b['key'] in casas), None)
                if not book: continue
                odds = {o['name']: o['price'] for o in book['markets'][0]['outcomes']}
                c, f = jogo['home_team'], jogo['away_team']
                oc, of = odds.get(c, 0), odds.get(f, 0)
                
                fav, zeb, o_fav, o_zeb, loc = (c, f, oc, of, "🏠 Casa") if oc <= of else (f, c, of, oc, "✈️ Fora")
                
                if min_f <= o_fav <= max_f and o_zeb >= min_z:
                    h_br = datetime.strptime(jogo["commence_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(tz_br).strftime("%H:%M")
                    nome_liga, nome_pais = traduzir_liga_e_pais(jogo["sport_title"])
                    
                    jogos.append({
                        "⏰ Hora": h_br, "🌍 País": nome_pais, "🏆 Liga": nome_liga, 
                        "🛡️ Fav": fav, "🦓 Zeb": zeb, "📈 Odd F": o_fav, "📉 Odd Z": o_zeb, 
                        "🏦 Casa": book['title'], "📍 Local": loc
                    })
        except: pass
        prog.progress((i + 1) / len(ligas))
    
    st.session_state.creditos_usados = creditos_consumidos
    prog.empty()
    return jogos

if 'res_pauta' not in st.session_state: st.session_state.res_pauta = []

if btn_scan:
    if not api_key: st.error("Insira uma Chave API!")
    else:
        status.info("Buscando pauta elite...")
        ligas_filtradas = get_ligas_futebol(api_key)
        resultados = scan_odds(api_key, ligas_filtradas, ini_utc, fim_utc, min_f, max_f, min_z)
        
        # ORDENAÇÃO POR HORÁRIO
        st.session_state.res_pauta = sorted(resultados, key=lambda x: x['⏰ Hora'])
        
        if not resultados: status.warning("Nenhum jogo encontrado.")
        else: status.success(f"Busca finalizada! Gastou {st.session_state.creditos_usados} créditos.")

if st.session_state.res_pauta:
    st.dataframe(pd.DataFrame(st.session_state.res_pauta), use_container_width=True, hide_index=True)
    if st.button("📲 ENVIAR PARA O TELEGRAM"):
        msg = f"🎯 *RADAR VIP - {data_alvo.strftime('%d/%m')}*\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        for j in st.session_state.res_pauta:
            header = f"🌍 *País:* {j['🌍 País']}\n" if j['🌍 País'] else ""
            msg += f"⏰ *{j['⏰ Hora']}* | {j['📍 Local']}\n{header}🏆 *Liga:* {j['🏆 Liga']}\n⭐ {j['🛡️ Fav']} ({j['📈 Odd F']:.2f})\n🦓 {j['🦓 Zeb']} ({j['📉 Odd Z']:.2f})\n🏦 {j['🏦 Casa']}\n\n"
        
        requests.post(f"https://api.telegram.org/bot{t_token}/sendMessage", json={"chat_id": t_id, "text": msg, "parse_mode": "Markdown"})
        st.success("✅ Enviado!")
