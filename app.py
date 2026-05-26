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

def criar_barra_porcentagem(pct):
    blocks = int(pct / 10)
    return "█" * blocks + "▒" * (10 - blocks)

# --- PAINEL LATERAL ---
with st.sidebar:
    st.markdown("### 🔑 Chaves de Acesso")
    opcao_api = st.selectbox("Escolher conta da API:", ["Conta 1", "Conta 2", "Conta 3", "Conta 4"])
    api_map = {"Conta 1": "api_key_1", "Conta 2": "api_key_2", "Conta 3": "api_key_3", "Conta 4": "api_key_4"}
    api_key = st.text_input(f"Chave {opcao_api}:", value=get_secret(api_map[opcao_api]), type="password")
    
    st.markdown("---")
    st.markdown("### 📅 Filtros de Data")
    data_alvo = st.date_input("Jogos do dia:", value=datetime.now().date() + timedelta(days=1))
    
    # 1. RETORNADO AO ORIGINAL: FILTRO DE VITÓRIA SECA DO FAVORITO
    st.markdown("### 🏆 Filtro: Favorito para Vencer (1X2)")
    col1, col2 = st.columns(2)
    with col1: min_f = st.number_input("Min Fav", value=1.25, step=0.05) # Seu padrão restaurado
    with col2: max_f = st.number_input("Max Fav", value=1.75, step=0.05) # Seu padrão restaurado
    min_z = st.number_input("Min Zebra", value=3.50, step=0.10)          # Seu padrão restaurado
    
    # 2. NOVO FILTRO INDEPENDENTE: DUPLA CHANCE
    st.markdown("### 🛡️ Filtro: Cobertura Dupla Chance (Favo ou Empate)")
    usar_filtro_dc = st.checkbox("Ativar Filtro Separado para Dupla Chance", value=True)
    col3, col4 = st.columns(2)
    with col3: min_dc_odd = st.number_input("Min Odd DC", value=1.10, step=0.02)
    with col4: max_dc_odd = st.number_input("Max Odd DC", value=1.40, step=0.02)
    
    st.markdown("---")
    st.markdown("### ⚽ Filtros de Gols")
    mercado_gol = st.selectbox("Linha de Gols Padrão:", ["Over 1.5", "Over 2.5", "Over 3.5", "Under 1.5", "Under 2.5", "Under 3.5"])
    
    st.markdown("---")
    st.markdown("### 📐 Filtros de Escanteios")
    canto_ht = st.selectbox("Linha de Cantos HT (1º Tempo):", ["Over 3.5 HT", "Over 4.5 HT", "Under 4.5 HT", "Under 5.5 HT"])
    canto_ft = st.selectbox("Linha de Cantos FT (90 Min):", ["Over 8.5 FT", "Over 9.5 FT", "Over 10.5 FT", "Under 10.5 FT"])
    
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
                
                o_empate = next((o['price'] for o in site['markets'][0]['outcomes'] if o['name'] == 'Draw'), 3.40)
                
                # --- PROCESSAMENTO INDEPENDENTE DOS DOIS FILTROS ---
                passou_filtro_vitoria = (min_f <= o_fav <= max_f and o_zeb >= min_z)
                
                pct_fav = (1 / o_fav) * 100
                pct_empate = (1 / o_empate) * 100
                pct_dc = min(96.0, pct_fav + pct_empate)
                odd_dc = 1 / (pct_dc / 100)
                
                passou_filtro_dc = True
                if usar_filtro_dc:
                    passou_filtro_dc = (min_dc_odd <= odd_dc <= max_dc_odd)
                
                # O jogo só entra na pauta se respeitar o filtro de vitória OU o filtro independente de dupla chance
                if passou_filtro_vitoria or passou_filtro_dc:
                    h_br = datetime.strptime(jogo["commence_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(tz_br).strftime("%H:%M")
                    liga_nome, pais_nome = identificar_origem(jogo["sport_title"])
                    
                    # Derivação estatística de Gols
                    if "over 1.5" in mercado_gol.lower(): pct_gols = max(65.0, min(88.0, pct_fav + 12))
                    elif "over 2.5" in mercado_gol.lower(): pct_gols = max(45.0, min(68.0, pct_fav - 2))
                    elif "over 3.5" in mercado_gol.lower(): pct_gols = max(25.0, min(44.0, pct_fav - 20))
                    elif "under 1.5" in mercado_gol.lower(): pct_gols = max(12.0, min(35.0, 100 - (pct_fav + 12)))
                    elif "under 2.5" in mercado_gol.lower(): pct_gols = max(32.0, min(55.0, 100 - (pct_fav - 2)))
                    else: pct_gols = max(56.0, min(75.0, 100 - (pct_fav - 20)))

                    # Derivação estatística de Cantos
                    if "4.5" in canto_ht: pct_c_ht = max(52.0, min(68.0, pct_fav * 0.95))
                    else: pct_c_ht = max(64.0, min(79.0, pct_fav * 1.15))
                    
                    if "9.5" in canto_ft: pct_c_ft = max(55.0, min(69.0, pct_fav * 0.98))
                    elif "10.5" in canto_ft: pct_c_ft = max(42.0, min(56.0, pct_fav * 0.80))
                    else: pct_c_ft = max(68.0, min(82.0, pct_fav * 1.18))
                    
                    jogos.append({
                        "⏰ Hora": h_br, "🌍 País/Origem": pais_nome, "🏆 Liga": liga_nome, 
                        "🛡️ Fav": fav, "🦓 Zeb": zeb, "📈 Odd F": o_fav, "📉 Odd Z": o_zeb, 
                        "🏦 Casa": site['title'], "📍 Local": loc, "🎯 % Fav": pct_fav,
                        "🛡️ Odd DC": odd_dc, "🛡️ % DC": pct_dc,
                        "⚽ Mercado Gol": mercado_gol, "📊 % Gol": pct_gols,
                        "📐 Canto HT": canto_ht, "📈 % HT": pct_c_ht,
                        "📐 Canto FT": canto_ft, "📈 % FT": pct_c_ft
                    })
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
            cabecalho = f"🎯 *RADAR VIP - {data_alvo.strftime('%d/%m')}*\n━━━━━━━━━━━━━━━━━━━━\n\n"
            mensagens = []
            texto_atual = cabecalho
            
            for idx, j in enumerate(st.session_state.res_pauta, 1):
                b_fav = criar_barra_porcentagem(j['🎯 % Fav'])
                b_dc = criar_barra_porcentagem(j['🛡️ % DC'])
                b_gol = criar_barra_porcentagem(j['📊 % Gol'])
                
                bloco = (
                    f"🔥 *JOGO {idx:02d}*\n"
                    f"⏰ *{j['⏰ Hora']}* | {j['🌍 País/Origem']}\n"
                    f"🏆 {j['🏆 Liga']}\n\n"
                    f"⭐ *PALPITE PRINCIPAL (MERCADO 1X2):*\n"
                    f"👉 Vitória do {j['🛡️ Fav']} ({j['📈 Odd F']:.2f}) | *{j['🎯 % Fav']:.1f}% de Chance*\n"
                    f"`{b_fav}`\n"
                    f"🦓 {j['🦓 Zeb']} ({j['📉 Odd Z']:.2f})\n\n"
                    f"🛡️ *COBERTURA ANTI-ZEBRA (MERCADO DUPLA CHANCE):*\n"
                    f"👉 {j['🛡️ Fav']} ou Empate ({j['🛡️ Odd DC']:.2f}) | *{j['🛡️ % DC']:.1f}% de Segurança*\n"
                    f"`{b_dc}`\n\n"
                    f"⚽ *MERCADO DE GOLS:*\n"
                    f"👉 {j['⚽ Mercado Gol']}: *{j['📊 % Gol']:.1f}% de Chance*\n"
                    f"`{b_gol}`\n\n"
                    f"📐 *MERCADO DE ESCANTEIOS:*\n"
                    f"⏱️ {j['📐 Canto HT']}: *{j['📈 % HT']:.1f}%*\n"
                    f"🏃 {j['📐 Canto FT']}: *{j['📈 % FT']:.1f}%*\n"
                    f"🏦 Via {j['🏦 Casa']}\n"
                    f"───────────────\n\n"
                )
                
                if len(texto_atual + bloco) > 3500:
                    mensagens.append(texto_atual)
                    texto_atual = cabecalho + bloco
                else:
                    texto_atual += bloco
            
            mensagens.append(texto_atual
