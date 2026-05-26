import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

# --- CONFIGURAÇÃO VISUAL (DARK MODE PREMIUM) ---
st.set_page_config(page_title="Radar VIP | Agência Pro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #0f172a !important; color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    h1 { color: #fbbf24 !important; text-align: center; font-weight: 900; font-size: 32px !important; margin-bottom: 30px; }
    h2, h3 { color: #e2e8f0 !important; font-weight: 600 !important; }
    p, span, div { color: #cbd5e1 !important; }
    .stButton>button { 
        background: linear-gradient(135deg, #d97706 0%, #b45309 100%) !important; 
        color: white !important; font-weight: 800 !important; font-size: 18px !important;
        width: 100% !important; border-radius: 8px !important; height: 55px !important; border: none !important;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(217, 119, 6, 0.4); }
    .stDataFrame { background-color: #1e293b !important; border-radius: 8px; border: 1px solid #334155; }
    [data-testid="stSidebar"] { background-color: #0b1120 !important; border-right: 1px solid #1e293b !important; }
    input, select { background-color: #1e293b !important; color: white !important; border-radius: 6px !important; border: 1px solid #475569 !important;}
</style>
""", unsafe_allow_html=True)

st.title("🎯 MASTER RADAR VIP")
status = st.empty()

# --- DICIONÁRIOS ---
TRADUCAO = {
    "Germany": "Alemanha", "England": "Inglaterra", "Spain": "Espanha", "Italy": "Itália",
    "France": "França", "Portugal": "Portugal", "Netherlands": "Holanda", "Brazil": "Brasil",
    "Argentina": "Argentina", "Uruguay": "Uruguai", "Mexico": "México", "USA": "EUA",
    "Saudi Arabia": "Arábia Saudita", "Japan": "Japão", "South Korea": "Coreia do Sul"
}
CONTINENTAIS = {
    "uefa": "Europa 🇪🇺", "conmebol": "América do Sul 🌎", "libertadores": "Libertadores 🏆", "sudamericana": "Sul-Americana 🏆"
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

def criar_barra(pct):
    blocks = int(pct / 10)
    return "█" * blocks + "▒" * (10 - blocks)

# --- MENU LATERAL (MODO DE OPERAÇÃO) ---
with st.sidebar:
    st.markdown("## ⚙️ Configurações")
    opcao_api = st.selectbox("🔑 Conta da API:", ["Conta 1", "Conta 2", "Conta 3", "Conta 4"])
    api_map = {"Conta 1": "api_key_1", "Conta 2": "api_key_2", "Conta 3": "api_key_3", "Conta 4": "api_key_4"}
    api_key = st.text_input("Chave:", value=get_secret(api_map[opcao_api]), type="password")
    data_alvo = st.date_input("📅 Data dos Jogos:", value=datetime.now().date() + timedelta(days=1))
    
    st.markdown("---")
    st.markdown("### 🎯 MODO DE OPERAÇÃO")
    modo_busca = st.radio(
        "Qual mercado você quer enviar para o VIP hoje?", 
        ["Vitória Seca (1X2)", "Dupla Chance", "Gols (Estimado)"]
    )
    
    st.markdown("---")
    # VAI MOSTRAR APENAS OS FILTROS DO MODO ESCOLHIDO
    min_f = max_f = min_z = min_dc = max_dc = 0
    mercado_gol = ""
    
    if modo_busca == "Vitória Seca (1X2)":
        col1, col2 = st.columns(2)
        with col1: min_f = st.number_input("Odd Min Fav", value=1.25, step=0.05)
        with col2: max_f = st.number_input("Odd Max Fav", value=1.75, step=0.05)
        min_z = st.number_input("Odd Mínima Zebra", value=3.50, step=0.10)
        
    elif modo_busca == "Dupla Chance":
        col3, col4 = st.columns(2)
        with col3: min_dc = st.number_input("DC Mínima", value=1.10, step=0.02)
        with col4: max_dc = st.number_input("DC Máxima", value=1.40, step=0.02)
        
    elif modo_busca == "Gols (Estimado)":
        mercado_gol = st.selectbox("Linha de Gols:", ["Over 1.5", "Over 2.5", "Under 2.5"])
        st.caption("Para achar jogos de gols, filtramos favoritos fortes:")
        col5, col6 = st.columns(2)
        with col5: min_f = st.number_input("Min Fav", value=1.20, step=0.05)
        with col6: max_f = st.number_input("Max Fav", value=1.60, step=0.05)

    st.markdown("---")
    t_token = st.text_input("Token do Bot:", value=get_secret("bot_token"), type="password")
    t_id = st.text_input("Chat ID:", value=get_secret("chat_id"))
    
    st.markdown("<br>", unsafe_allow_html=True)
    btn_scan = st.button("🚀 EXECUTAR VARREDURA")

if 'creditos_restantes' not in st.session_state: st.session_state.creditos_restantes = "---"
st.sidebar.info(f"💳 Créditos: {st.session_state.creditos_restantes}")

tz_br = timezone(timedelta(hours=-3))
ini_utc = datetime(data_alvo.year, data_alvo.month, data_alvo.day, 0, 0, 0, tzinfo=tz_br).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
fim_utc = datetime(data_alvo.year, data_alvo.month, data_alvo.day, 23, 59, 59, tzinfo=tz_br).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

@st.cache_data(ttl=3600)
def get_ligas(chave):
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={chave}"
    try:
        res = requests.get(url).json()
        bloqueio = ["championship", "league_one", "league_two", "liga_2", "division_2", "bundesliga_2", "serie_b", "serie_c", "3. liga", "la liga 2"]
        return [l['key'] for l in res if "soccer" in l['key'].lower() and ("brazil" in l['key'].lower() or not any(b in l['key'].lower() for b in bloqueio))]
    except: return []

@st.cache_data(ttl=1800)
def scan_odds(chave, ligas, d_ini, d_fim, modo, min_f, max_f, min_z, min_dc, max_dc, m_gol):
    jogos = []
    prog = st.progress(0)
    for i, l_key in enumerate(ligas):
        url = f"https://api.the-odds-api.com/v4/sports/{l_key}/odds/?apiKey={chave}&regions=eu&markets=h2h&commenceTimeFrom={d_ini}&commenceTimeTo={d_fim}"
        try:
            response = requests.get(url)
            st.session_state.creditos_restantes = response.headers.get('x-requests-remaining', "---")
            for jogo in response.json():
                bks = jogo.get("bookmakers", [])
                if not bks: continue
                site = next((b for b in bks if b['key'] in ["betano", "betfair_ex_eu", "bet365"]), bks[0])
                odds = {o['name']: o['price'] for o in site['markets'][0]['outcomes']}
                c, f = jogo['home_team'], jogo['away_team']
                oc, of = odds.get(c, 0), odds.get(f, 0)
                fav, zeb, o_fav, o_zeb = (c, f, oc, of) if oc <= of else (f, c, of, oc)
                o_empate = next((o['price'] for o in site['markets'][0]['outcomes'] if o['name'] == 'Draw'), 3.40)
                
                pct_fav = (1 / o_fav) * 100
                odd_dc = 1 / (min(96.0, pct_fav + (1 / o_empate) * 100) / 100)
                h_br = datetime.strptime(jogo["commence_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(tz_br).strftime("%H:%M")
                liga_nome, pais_nome = identificar_origem(jogo["sport_title"])

                # LÓGICA CIRÚRGICA: Só salva o que o usuário pediu no "Modo"
                if modo == "Vitória Seca (1X2)" and (min_f <= o_fav <= max_f and o_zeb >= min_z):
                    jogos.append({"⏰ Hora": h_br, "🌍 País": pais_nome, "🏆 Liga": liga_nome, "🛡️ Palpite": f"Vitória {fav}", "📈 Odd": round(o_fav, 2), "🎯 Chance %": round(pct_fav, 1), "🏦 Casa": site['title']})
                elif modo == "Dupla Chance" and (min_dc <= odd_dc <= max_dc):
                    jogos.append({"⏰ Hora": h_br, "🌍 País": pais_nome, "🏆 Liga": liga_nome, "🛡️ Palpite": f"{fav} ou Empate", "📈 Odd DC": round(odd_dc, 2), "🎯 Segura %": round((1/odd_dc)*100, 1), "🏦 Casa": site['title']})
                elif modo == "Gols (Estimado)" and (min_f <= o_fav <= max_f):
                    pct_gol = max(65.0, min(88.0, pct_fav + 12)) if "1.5" in m_gol else max(45.0, min(68.0, pct_fav - 2))
                    jogos.append({"⏰ Hora": h_br, "🌍 País": pais_nome, "🏆 Liga": liga_nome, "⚽ Linha": m_gol, "📊 Chance %": round(pct_gol, 1), "🏦 Casa": site['title']})
        except: pass
        prog.progress((i + 1) / len(ligas))
    prog.empty()
    return jogos

if 'res_pauta' not in st.session_state: st.session_state.res_pauta = []
if 'modo_salvo' not in st.session_state: st.session_state.modo_salvo = ""

if btn_scan:
    if not api_key: st.error("⚠️ Insira uma Chave API!")
    else:
        status.info(f"🔄 Buscando exclusivamente pauta de {modo_busca}...")
        ligas_f = get_ligas(api_key)
        resultados = scan_odds(api_key, ligas_f, ini_utc, fim_utc, modo_busca, min_f, max_f, min_z, min_dc, max_dc, mercado_gol)
        st.session_state.res_pauta = sorted(resultados, key=lambda x: x['⏰ Hora'])
        st.session_state.modo_salvo = modo_busca
        if not resultados: status.warning("Nenhum jogo atendeu aos filtros.")
        else: status.success(f"✅ {len(resultados)} jogos encontrados!")

if st.session_state.res_pauta:
    st.dataframe(pd.DataFrame(st.session_state.res_pauta), use_container_width=True, hide_index=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📲 PUBLICAR PAUTA NO VIP"):
        if not t_token or not t_id: st.error("⚠️ Faltam dados do Telegram!")
        else:
            modo = st.session_state.modo_salvo
            texto = f"🎯 *RADAR VIP - {data_alvo.strftime('%d/%m')}*\n━━━━━━━━━━━━━━━━━━━━\n\n"
            msgs = []
            
            for idx, j in enumerate(st.session_state.res_pauta, 1):
                bloco = f"🔥 *JOGO {idx:02d}*\n⏰ *{j['⏰ Hora']}* | {j['🌍 País']}\n🏆 {j['🏆 Liga']}\n\n"
                
                if modo == "Vitória Seca (1X2)":
                    bloco += f"⭐ *PALPITE:*\n👉 *{j['🛡️ Palpite']}* (@{j['📈 Odd']:.2f})\n`{criar_barra(j['🎯 Chance %'])}` *{j['🎯 Chance %']:.1f}%*\n\n"
                elif modo == "Dupla Chance":
                    bloco += f"🛡️ *PALPITE SEGURO:*\n👉 *{j['🛡️ Palpite']}* (@{j['📈 Odd DC']:.2f})\n`{criar_barra(j['🎯 Segura %'])}` *{j['🎯 Segura %']:.1f}%*\n\n"
                elif modo == "Gols (Estimado)":
                    bloco += f"⚽ *MERCADO DE GOLS:*\n👉 *{j['⚽ Linha']}*\n`{criar_barra(j['📊 Chance %'])}` *{j['📊 Chance %']:.1f}%*\n\n"
                
                bloco += f"🏦 _Via {j['🏦 Casa']}_\n───────────────\n\n"
                if len(texto + bloco) > 3500: msgs.append(texto); texto = f"🎯 *RADAR VIP (Cont.)*\n━━━━━━━━━━━━━━━━━━━━\n\n" + bloco
                else: texto += bloco
            msgs.append(texto)
            
            sucesso = True
            for m in msgs:
                r = requests.post(f"https://api.telegram.org/bot{t_token}/sendMessage", json={"chat_id": t_id, "text": m, "parse_mode": "Markdown"})
                if r.status_code != 200: sucesso = False; st.error(f"Erro Telegram: {r.text}")
            if sucesso: st.success("✅ Pauta publicada no VIP com sucesso!")
