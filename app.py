import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Radar VIP - Agência Pro", layout="wide")
st.markdown("""<style>.stApp { background-color: #0b0e14; } .stDataFrame { background-color: #161a23; } h1 { color: #f1c40f !important; text-align: center; font-weight: 800; } .stButton>button { background: linear-gradient(90deg, #f39c12, #e67e22); color: white; font-weight: bold; width: 100%; border-radius: 8px; height: 50px; }</style>""", unsafe_allow_html=True)

st.title("🎯 MASTER RADAR VIP")
status = st.empty()

# --- DICIONÁRIO DE TRADUÇÃO ---
TRADUCAO = {
    "Germany": "Alemanha", "England": "Inglaterra", "Spain": "Espanha", "Italy": "Itália",
    "France": "França", "Portugal": "Portugal", "Netherlands": "Holanda", "Brazil": "Brasil",
    "Argentina": "Argentina", "Uruguay": "Uruguai", "Mexico": "México", "USA": "EUA",
    "Saudi Arabia": "Arábia Saudita", "Japan": "Japão", "South Korea": "Coreia do Sul",
    "Norway": "Noruega", "Sweden": "Suécia", "Finland": "Finlândia", "Greece": "Grécia",
    "Scotland": "Escócia", "Austria": "Áustria", "Switzerland": "Suíça", "China": "China",
    "Belgium": "Bélgica", "Turkey": "Turquia", "Denmark": "Dinamarca", "Poland": "Polônia"
}

CONTINENTAIS = {
    "uefa": "Europa 🇪🇺", "conmebol": "América do Sul 🌎", "afc": "Ásia 🌏", 
    "caf": "África 🌍", "concacaf": "América do Norte 🌎", "champions": "Elite Continental",
    "libertadores": "Libertadores 🏆", "sudamericana": "Sul-Americana 🏆"
}

def identificar_origem(sport_title):
    title_low = sport_title.lower()
    for chave, nome in CONTINENTAIS.items():
        if chave in title_low: return sport_title, f"Torneio {nome}"
    if " - " in sport_title:
        liga, pais_en = sport_title.split(" - ", 1)
        return liga, TRADUCAO.get(pais_en, pais_en)
    return sport_title, "Internacional"

def get_secret(key, default=""):
    try: return st.secrets[key]
    except: return default

# --- PAINEL LATERAL ---
with st.sidebar:
    st.markdown("### 🔑 Chaves de Acesso")
    opcao_api = st.selectbox("Escolher conta da API:", ["Conta 1", "Conta 2", "Conta 3", "Conta 4"])
    api_map = {"Conta 1": "api_key_1", "Conta 2": "api_key_2", "Conta 3": "api_key_3", "Conta 4": "api_key_4"}
    api_key = st.text_input(f"Chave {opcao_api}:", value=get_secret(api_map[opcao_api]), type="password")
    
    st.markdown("---")
    st.markdown("### 📅 Filtros")
    data_alvo = st.date_input("Jogos do dia:", value=datetime.now().date() + timedelta(days=1))
    
    col1, col2 = st.columns(2)
    with col1: min_f = st.number_input("Min Fav", value=1.25, step=0.05)
    with col2: max_f = st.number_input("Max Fav", value=1.75, step=0.05)
    min_z = st.number_input("Min Zebra", value=3.50, step=0.10)
    
    st.markdown("---")
    st.markdown("### ✈️ Telegram")
    t_token = st.text_input("Bot Token:", value=get_secret("bot_token"), type="password")
    t_id = st.text_input("Chat ID:", value=get_secret("chat_id"))
    
    btn_scan = st.button("🚀 INICIAR BUSCA")

if 'creditos_restantes' not in st.session_state: st.session_state.creditos_restantes = "---"
st.sidebar.info(f"💳 Créditos Restantes: {st.session_state.creditos_restantes}")

tz_br = timezone(timedelta(hours=-3))
ini_utc = datetime(data_alvo.year, data_alvo.month, data_alvo.day, 0, 0, 0, tzinfo=tz_br).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
fim_utc = datetime(data_alvo.year, data_alvo.month, data_alvo.day, 23, 59, 59, tzinfo=tz_br).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

@st.cache_data(ttl=3600)
def get_ligas_futebol(chave):
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={chave}"
    try:
        res = requests.get(url).json()
        bloqueio = ["championship", "league_one", "league_two", "liga_2", "division_2", "bundesliga_2", "serie_b", "serie_c", "3. liga", "la liga 2"]
        selecionadas = []
        for liga in res:
            k, t = liga['key'].lower(), liga['title'].lower()
            if "soccer" not in k: continue
            if "brazil" in k or any(c in k or c in t for c in ["uefa", "conmebol", "champions", "libertadores", "sudamericana"]):
                selecionadas.append(liga['key'])
            elif not any(b in k or b in t for b in bloqueio):
                selecionadas.append(liga['key'])
        return selecionadas
    except: return []

def scan_odds(chave, ligas, d_ini, d_fim, min_f, max_f, min_z):
    jogos = []
    prog = st.progress(0)
    casas_prioridade = ["betano", "betfair_ex_eu", "betfair_sb_uk", "bet365"]
    for i, l_key in enumerate(ligas):
        url = f"https://api.the-odds-api.com/v4/sports/{l_key}/odds/?apiKey={chave}&regions=eu&markets=h2h&commenceTimeFrom={d_ini}&commenceTimeTo={d_fim}"
        try:
            response = requests.get(url)
            st.session_state.creditos_restantes = response.headers.get('x-requests-remaining', "---")
            res = response.json()
            for jogo in res:
                bookmakers = jogo.get("bookmakers", [])
                if not bookmakers: continue
                site = None
                for cp in casas_prioridade:
                    site = next((b for b in bookmakers if b['key'] == cp), None)
                    if site: break
                if not site: site = bookmakers[0]
                odds = {o['name']: o['price'] for o in site['markets'][0]['outcomes']}
                c, f = jogo['home_team'], jogo['away_team']
                oc, of = odds.get(c, 0), odds.get(f, 0)
                fav, zeb, o_fav, o_zeb, loc = (c, f, oc, of, "🏠 Casa") if oc <= of else (f, c, of, oc, "✈️ Fora")
                if min_f <= o_fav <= max_f and o_zeb >= min_z:
                    h_br = datetime.strptime(jogo["commence_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(tz_br).strftime("%H:%M")
                    liga_nome, pais_nome = identificar_origem(jogo["sport_title"])
                    jogos.append({"⏰ Hora": h_br, "🌍 País/Origem": pais_nome, "🏆 Liga": liga_nome, "🛡️ Fav": fav, "🦓 Zeb": zeb, "📈 Odd F": o_fav, "📉 Odd Z": o_zeb, "🏦 Casa": site['title'], "📍 Local": loc})
        except: pass
        prog.progress((i + 1) / len(ligas))
    prog.empty()
    return jogos

if 'res_pauta' not in st.session_state: st.session_state.res_pauta = []

if btn_scan:
    if not api_key: st.error("Insira uma Chave API!")
    else:
        status.info("Buscando pauta elite...")
        ligas_filtradas = get_ligas_futebol(api_key)
        resultados = scan_odds(api_key, ligas_filtradas, ini_utc, fim_utc, min_f, max_f, min_z)
        st.session_state.res_pauta = sorted(resultados, key=lambda x: x['⏰ Hora'])
        if not resultados: status.warning("Nenhum jogo encontrado.")
        else: status.success(f"Busca finalizada!")

if st.session_state.res_pauta:
    st.dataframe(pd.DataFrame(st.session_state.res_pauta), use_container_width=True, hide_index=True)
    
    if st.button("📲 DESPACHAR PARA O TELEGRAM"):
        if not t_token or not t_id:
            st.error("Token ou ID ausentes!")
        else:
            # --- SISTEMA DE ENVIO EM PARTES (CHUNKING) ---
            cabecalho = f"🎯 *RADAR VIP - {data_alvo.strftime('%d/%m')}*\n━━━━━━━━━━━━━━━━━━━━\n\n"
            mensagens = []
            texto_atual = cabecalho
            
            for idx, j in enumerate(st.session_state.res_pauta, 1):
                bloco = f"🔥 *JOGO {idx:02d}*\n⏰ *{j['⏰ Hora']}* | {j['🌍 País/Origem']}\n🏆 {j['🏆 Liga']}\n⭐ {j['🛡️ Fav']} ({j['📈 Odd F']:.2f})\n🦓 {j['🦓 Zeb']} ({j['📉 Odd Z']:.2f})\n🏦 Via {j['🏦 Casa']}\n───────────────\n\n"
                
                # Se o bloco atual + o próximo jogo passar de 3500 caracteres, fecha a mensagem e começa outra
                if len(texto_atual + bloco) > 3500:
                    mensagens.append(texto_atual)
                    texto_atual = cabecalho + bloco
                else:
                    texto_atual += bloco
            
            mensagens.append(texto_atual) # Adiciona a última parte
            
            sucesso_total = True
            for msg in mensagens:
                res = requests.post(f"https://api.telegram.org/bot{t_token}/sendMessage", json={"chat_id": t_id, "text": msg, "parse_mode": "Markdown"})
                if res.status_code != 200:
                    sucesso_total = False
                    st.error(f"Erro no envio: {res.text}")
            
            if sucesso_total:
                st.success(f"✅ {len(mensagens)} mensagens enviadas com sucesso!")
