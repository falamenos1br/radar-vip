import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

# --- CONFIGURAÇÃO VISUAL (DARK MODE PREMIUM) ---
st.set_page_config(page_title="Radar VIP | Agência Pro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* Tema Escuro Profissional (Tailwind Slate) */
    .stApp { background-color: #0f172a !important; color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    
    /* Títulos e Textos */
    h1 { color: #fbbf24 !important; text-align: center; font-weight: 900; font-size: 32px !important; margin-bottom: 30px; letter-spacing: -0.5px;}
    h2, h3 { color: #e2e8f0 !important; font-weight: 600 !important; }
    p, span, div { color: #cbd5e1 !important; }
    
    /* Botões Premium */
    .stButton>button { 
        background: linear-gradient(135deg, #d97706 0%, #b45309 100%) !important; 
        color: white !important; 
        font-weight: 800 !important; 
        font-size: 18px !important;
        width: 100% !important; 
        border-radius: 8px !important; 
        height: 55px !important; 
        border: none !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(217, 119, 6, 0.4); }
    
    /* Tabelas e Painéis */
    .stDataFrame { background-color: #1e293b !important; border-radius: 8px; overflow: hidden; border: 1px solid #334155; }
    [data-testid="stSidebar"] { background-color: #0b1120 !important; border-right: 1px solid #1e293b !important; }
    
    /* Inputs */
    input, select { background-color: #1e293b !important; color: white !important; border-radius: 6px !important; border: 1px solid #475569 !important; padding: 10px !important;}
    
    /* Expander e Alertas */
    .streamlit-expanderHeader { background-color: #1e293b !important; color: white !important; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

st.title("🎯 MASTER RADAR VIP")
status = st.empty()

# --- PAINEL DE DIAGNÓSTICO ---
with st.expander("📊 Painel de Diagnóstico de Ligas da API"):
    st.info("Insira sua chave para listar as competições de futebol ativas no sistema da The Odds API hoje.")
    api_teste = st.text_input("Chave API para testar as ligas disponíveis:", type="password", key="teste_api")
    if st.button("🔍 Inspecionar Ligas Ativas"):
        if api_teste:
            try:
                url_teste = f"https://api.the-odds-api.com/v4/sports/?apiKey={api_teste}"
                dados_api = requests.get(url_teste).json()
                ligas_futebol = [f"{l['key']} ({l['title']})" for l in dados_api if "soccer" in l['key'].lower()]
                st.success(f"Encontramos {len(ligas_futebol)} ligas de futebol abertas hoje:")
                st.json(ligas_futebol)
            except Exception as e:
                st.error(f"Falha na conexão: {e}")
        else:
            st.warning("A chave é necessária para o teste.")

st.markdown("---")

# --- DICIONÁRIOS ---
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

# --- MENU LATERAL (SIDEBAR) ---
with st.sidebar:
    st.markdown("## ⚙️ Configurações")
    opcao_api = st.selectbox("🔑 Conta da API:", ["Conta 1", "Conta 2", "Conta 3", "Conta 4"])
    api_map = {"Conta 1": "api_key_1", "Conta 2": "api_key_2", "Conta 3": "api_key_3", "Conta 4": "api_key_4"}
    api_key = st.text_input(f"Chave ({opcao_api}):", value=get_secret(api_map[opcao_api]), type="password")
    
    st.markdown("---")
    data_alvo = st.date_input("📅 Data dos Jogos:", value=datetime.now().date() + timedelta(days=1))
    
    st.markdown("### 🎯 Mercado: Vencedor (1X2)")
    col1, col2 = st.columns(2)
    with col1: min_f = st.number_input("Odd Mínima", value=1.25, step=0.05)
    with col2: max_f = st.number_input("Odd Máxima", value=1.75, step=0.05)
    min_z = st.number_input("Odd Mínima da Zebra", value=3.50, step=0.10)
    
    st.markdown("### 🛡️ Mercado: Dupla Chance")
    usar_filtro_dc = st.checkbox("Ativar Filtro Independente", value=True)
    col3, col4 = st.columns(2)
    with col3: min_dc_odd = st.number_input("DC Mínima", value=1.10, step=0.02)
    with col4: max_dc_odd = st.number_input("DC Máxima", value=1.40, step=0.02)
    
    st.markdown("### ⚽ Mercado: Gols")
    mercado_gol = st.selectbox("Linha de Gols:", ["Over 1.5", "Over 2.5", "Over 3.5", "Under 1.5", "Under 2.5", "Under 3.5"])
    
    st.markdown("---")
    st.markdown("### ✈️ Bot Telegram")
    t_token = st.text_input("Token do Bot:", value=get_secret("bot_token"), type="password")
    t_id = st.text_input("Chat ID do Canal:", value=get_secret("chat_id"))
    
    st.markdown("<br>", unsafe_allow_html=True)
    btn_scan = st.button("🚀 EXECUTAR VARREDURA")

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

@st.cache_data(ttl=1800)
def scan_odds(chave, ligas, d_ini, d_fim, min_f, max_f, min_z, _usar_filtro_dc, _min_dc, _max_dc):
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
                
                passou_filtro_vitoria = (min_f <= o_fav <= max_f and o_zeb >= min_z)
                
                pct_fav = (1 / o_fav) * 100
                pct_empate = (1 / o_empate) * 100
                pct_dc = min(96.0, pct_fav + pct_empate)
                odd_dc = 1 / (pct_dc / 100)
                
                passou_filtro_dc = True
                if _usar_filtro_dc:
                    passou_filtro_dc = (_min_dc <= odd_dc <= _max_dc)
                
                if passou_filtro_vitoria or passou_filtro_dc:
                    h_br = datetime.strptime(jogo["commence_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(tz_br).strftime("%H:%M")
                    liga_nome, pais_nome = identificar_origem(jogo["sport_title"])
                    
                    if "over 1.5" in mercado_gol.lower(): pct_gols = max(65.0, min(88.0, pct_fav + 12))
                    elif "over 2.5" in mercado_gol.lower(): pct_gols = max(45.0, min(68.0, pct_fav - 2))
                    elif "over 3.5" in mercado_gol.lower(): pct_gols = max(25.0, min(44.0, pct_fav - 20))
                    elif "under 1.5" in mercado_gol.lower(): pct_gols = max(12.0, min(35.0, 100 - (pct_fav + 12)))
                    elif "under 2.5" in mercado_gol.lower(): pct_gols = max(32.0, min(55.0, 100 - (pct_fav - 2)))
                    else: pct_gols = max(56.0, min(75.0, 100 - (pct_fav - 20)))

                    jogos.append({
                        "⏰ Hora": h_br, "🌍 País": pais_nome, "🏆 Liga": liga_nome, 
                        "🛡️ Favorito": fav, "📈 Odd Fav": round(o_fav, 2), "🎯 % Vencer": round(pct_fav, 1),
                        "🛡️ Odd DC": round(odd_dc, 2), "🛡️ % DC": round(pct_dc, 1),
                        "⚽ Linha Gols": mercado_gol, "📊 % Gols": round(pct_gols, 1),
                        "🦓 Zebra": zeb, "📉 Odd Zebra": round(o_zeb, 2), "🏦 Casa": site['title']
                    })
        except: pass
        prog.progress((i + 1) / len(ligas))
    prog.empty()
    return jogos

if 'res_pauta' not in st.session_state: st.session_state.res_pauta = []

if btn_scan:
    if not api_key: st.error("⚠️ Insira uma Chave API válida no menu lateral para iniciar.")
    else:
        status.info("🔄 Analisando mercado global... Por favor, aguarde.")
        ligas_filtradas = get_ligas_futebol(api_key)
        resultados = scan_odds(api_key, ligas_filtradas, ini_utc, fim_utc, min_f, max_f, min_z, usar_filtro_dc, min_dc_odd, max_dc_odd)
        st.session_state.res_pauta = sorted(resultados, key=lambda x: x['⏰ Hora'])
        
        if not resultados: 
            status.warning("⚠️ Nenhum jogo atendeu aos seus critérios rígidos de filtro para esta data.")
        else: 
            status.success(f"✅ Varredura concluída! {len(resultados)} jogos de alto padrão encontrados.")

if st.session_state.res_pauta:
    st.dataframe(pd.DataFrame(st.session_state.res_pauta), use_container_width=True, hide_index=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📲 PUBLICAR PAUTA NO VIP (TELEGRAM)"):
        if not t_token or not t_id:
            st.error("⚠️ Configure o Token e o Chat ID do Telegram no menu lateral!")
        else:
            cabecalho = f"🎯 *RADAR VIP - {data_alvo.strftime('%d/%m')}*\n━━━━━━━━━━━━━━━━━━━━\n\n"
            mensagens = []
            texto_atual = cabecalho
            
            for idx, j in enumerate(st.session_state.res_pauta, 1):
                b_fav = criar_barra_porcentagem(j['🎯 % Vencer'])
                b_dc = criar_barra_porcentagem(j['🛡️ % DC'])
                b_gol = criar_barra_porcentagem(j['📊 % Gols'])
                
                bloco = (
                    f"🔥 *JOGO {idx:02d}*\n"
                    f"⏰ *{j['⏰ Hora']}* | {j['🌍 País']}\n"
                    f"🏆 {j['🏆 Liga']}\n\n"
                    f"⭐ *MERCADO VENCEDOR (1X2):*\n"
                    f"👉 Vitória: *{j['🛡️ Favorito']}* (@{j['📈 Odd Fav']:.2f})\n"
                    f"`{b_fav}` *{j['🎯 % Vencer']:.1f}%*\n\n"
                    f"🛡️ *MERCADO DUPLA CHANCE:*\n"
                    f"👉 *{j['🛡️ Favorito']}* ou Empate (@{j['🛡️ Odd DC']:.2f})\n"
                    f"`{b_dc}` *{j['🛡️ % DC']:.1f}%*\n\n"
                    f"⚽ *MERCADO DE GOLS:*\n"
                    f"👉 {j['⚽ Linha Gols']}: *{j['📊 % Gols']:.1f}%*\n"
                    f"`{b_gol}`\n\n"
                    f"🏦 _Odds coletadas via {j['🏦 Casa']}_\n"
                    f"───────────────\n\n"
                )
                
                if len(texto_atual + bloco) > 3500:
                    mensagens.append(texto_atual)
                    texto_atual = cabecalho + bloco
                else:
                    texto_atual += bloco
            
            mensagens.append(texto_atual)
            
            sucesso = True
            for msg in mensagens:
                url
