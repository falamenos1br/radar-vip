import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Radar VIP - Gestão de Créditos", layout="wide")
st.markdown("""<style>.stApp { background-color: #0b0e14; } .stDataFrame { background-color: #161a23; } h1 { color: #f1c40f !important; text-align: center; } .stButton>button { background: linear-gradient(90deg, #f39c12, #e67e22); color: white; font-weight: bold; width: 100%; border-radius: 8px; height: 50px; }</style>""", unsafe_allow_html=True)

st.title("🎯 MASTER RADAR VIP: GESTÃO INTELIGENTE")
status = st.empty()

# --- PAINEL LATERAL ---
with st.sidebar:
    st.markdown("### 🔑 Gerenciador de APIs")
    conta = st.selectbox("Selecione a API Key:", ["Conta 1", "Conta 2", "Conta 3", "Conta 4"])
    api_key = st.text_input(f"Chave da {conta}:", type="password")
    
    st.markdown("---")
    st.markdown("### 📅 Programação de Data")
    data_alvo = st.date_input("Escolha a data dos jogos:", value=datetime.now().date() + timedelta(days=1))
    
    st.markdown("---")
    st.markdown("### 🎛️ Filtros de Assertividade")
    col1, col2 = st.columns(2)
    with col1: min_f = st.number_input("Odd Mín Fav", value=1.25, step=0.05)
    with col2: max_f = st.number_input("Odd Máx Fav", value=1.55, step=0.05)
    min_z = st.number_input("Zebra Mínima", value=4.50, step=0.10)
    
    st.markdown("---")
    st.markdown("### ✈️ Integração Telegram")
    bot_token = st.text_input("Token do Bot (BotFather):")
    chat_id = st.text_input("Seu Chat ID (userinfobot):")
    
    btn_scan = st.button("🚀 INICIAR VARREDURA SEGURA")

# Configuração de Fuso Horário Brasil
tz_br = timezone(timedelta(hours=-3))
ini_utc = datetime(data_alvo.year, data_alvo.month, data_alvo.day, 0, 0, 0, tzinfo=tz_br).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
fim_utc = datetime(data_alvo.year, data_alvo.month, data_alvo.day, 23, 59, 59, tzinfo=tz_br).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# --- SISTEMA DE SEGURANÇA 1 & 2: LISTAGEM E CACHE ---
@st.cache_data(ttl=3600)
def get_ligas_seguro(chave):
    """Consulta a lista de esportes ativos. Não costuma consumir créditos de odds."""
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={chave}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return res.json()
    except: return []
    return []

def filtrar_ligas_artesanal(lista_total):
    """SISTEMA DE SEGURANÇA 3: Filtra ligas indesejadas localmente para não gastar crédito."""
    selecionadas = []
    # Divisões que vamos bloquear fora do Brasil
    bloqueio = ["championship", "league_one", "league_two", "liga_2", "division_2", "bundesliga_2", "serie_b", "serie_c"]
    # Palavras de torneios continentais que aceitamos sempre
    continentais = ["uefa", "conmebol", "afc", "caf", "concacaf", "champions", "libertadores", "sudamericana"]
    
    for liga in lista_total:
        key = liga['key'].lower()
        title = liga['title'].lower()
        
        # 1. BRASIL: Aceita tudo (A, B, C, D, Copa, Estadual)
        if "brazil" in key or "brazil" in title:
            selecionadas.append(liga['key'])
            continue
            
        # 2. CONTINENTAIS: Aceita tudo
        if any(c in key or c in title for c in continentais):
            selecionadas.append(liga['key'])
            continue
            
        # 3. OUTROS PAÍSES: Aceita apenas 1ª Divisão (bloqueia se tiver palavras de divisão inferior)
        if not any(b in key for b in bloqueio):
            selecionadas.append(liga['key'])
            
    return selecionadas

def scan_odds(chave, ligas_filtradas, d_ini, d_fim, min_f, max_f, min_z):
    jogos_final = []
    progresso = st.progress(0)
    
    # Lista de casas preferenciais (Betano, Betfair, Bet365)
    casas_alvo = ["betano", "betfair_ex_eu", "betfair_sb_uk", "bet365"]
    
    for i, liga_key in enumerate(ligas_filtradas):
        url = f"https://api.the-odds-api.com/v4/sports/{liga_key}/odds/?apiKey={chave}&regions=eu&markets=h2h&commenceTimeFrom={d_ini}&commenceTimeTo={d_fim}"
        try:
            res = requests.get(url).json()
            if isinstance(res, list):
                for jogo in res:
                    bookmakers = jogo.get("bookmakers", [])
                    if not bookmakers: continue
                    
                    # Tenta achar a melhor casa de aposta da lista
                    site = next((b for b in bookmakers if b['key'] in casas_alvo), bookmakers[0])
                    odds_raw = site['markets'][0]['outcomes']
                    odds = {o['name']: o['price'] for o in odds_raw}
                    
                    casa, fora = jogo['home_team'], jogo['away_team']
                    o_c, o_f = odds.get(casa, 0), odds.get(fora, 0)
                    
                    # Lógica de Favorito
                    if o_c <= o_f: fav, zeb, odd_f, odd_z, loc = casa, fora, o_c, o_f, "🏠 Casa"
                    else: fav, zeb, odd_f, odd_z, loc = fora, casa, o_f, o_c, "✈️ Fora"
                    
                    if min_f <= odd_f <= max_f and odd_z >= min_z:
                        h_utc = datetime.strptime(jogo["commence_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        h_br = h_utc.astimezone(tz_br).strftime("%H:%M")
                        jogos_final.append({
                            "📅 Data": data_alvo.strftime("%d/%m"), "⏰ Hora": h_br, "🏆 Liga": jogo["sport_title"], 
                            "🛡️ Fav": f"⭐ {fav}", "🦓 Zeb": f"🦓 {zeb}", "📈 Odd F": odd_f, "📉 Odd Z": odd_z, "🏦 Casa": site['title']
                        })
        except: pass
        progresso.progress((i + 1) / len(ligas_filtradas))
    progresso.empty()
    return jogos_final

# --- EXECUÇÃO ---
if btn_scan:
    if not api_key: st.warning("Por favor, insira a chave da API.")
    else:
        status.info("Iniciando varredura segura...")
        todas_ligas = get_ligas_seguro(api_key)
        if todas_ligas:
            ligas_alvo = filtrar_ligas_artesanal(todas_ligas)
            status.info(f"Analisando {len(ligas_alvo)} ligas filtradas para o dia {data_alvo.strftime('%d/%m')}...")
            resultados = scan_odds(api_key, ligas_alvo, ini_utc, fim_utc, min_f, max_f, min_z)
            
            if resultados:
                st.success(f"Encontrados {len(resultados)} jogos de alto valor!")
                df = pd.DataFrame(resultados)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Botão para enviar ao Telegram (Opcional)
                if st.button("📲 DESPACHAR PARA O TELEGRAM"):
                    # Aqui iria a função de envio que já configuramos
                    pass
            else:
                st.warning("Nenhum jogo passou pelos filtros de segurança nesta data.")
        else:
            st.error("Erro ao conectar com a API. Verifique sua chave.")
