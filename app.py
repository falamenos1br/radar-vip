import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Radar VIP - Agência", layout="wide")
st.markdown("""<style>.stApp { background-color: #0b0e14; } .stDataFrame { background-color: #161a23; } h1 { color: #f1c40f !important; text-align: center; } .stButton>button { background: linear-gradient(90deg, #f39c12, #e67e22); color: white; font-weight: bold; width: 100%; border-radius: 8px; }</style>""", unsafe_allow_html=True)

st.title("🎯 MASTER RADAR VIP: AGÊNCIA")
status = st.empty()

# --- PAINEL LATERAL ---
with st.sidebar:
    st.markdown("### 🔑 Gerenciador de APIs")
    conta_selecionada = st.selectbox("Usar qual conta?", ["Conta 1", "Conta 2", "Conta 3", "Conta 4"])
    
    # Campo que muda conforme a conta selecionada
    api_key = st.text_input(f"API Key da {conta_selecionada}:", type="password")
    
    st.markdown("---")
    st.markdown("### 📅 Calendário de Busca")
    # Data padrão é amanhã (dia 16), mas você pode mudar
    data_alvo = st.date_input("Escolha a data dos jogos:", value=datetime.now().date() + timedelta(days=1))
    
    st.markdown("---")
    st.markdown("### 🎛️ Filtros")
    col1, col2 = st.columns(2)
    with col1: min_f = st.number_input("Min Fav", value=1.40)
    with col2: max_f = st.number_input("Max Fav", value=1.85)
    min_z = st.number_input("Min Zebra", value=3.50)
    
    st.markdown("---")
    st.markdown("### ✈️ Integração Telegram")
    bot_token = st.text_input("Bot Token:", type="password", help="Pegue no @BotFather do Telegram")
    chat_id = st.text_input("Seu Chat ID:", help="Pegue no @userinfobot")
    
    btn_scan = st.button("🚀 INICIAR VARREDURA")

# --- LÓGICA DE DATAS ---
# Converte a data escolhida no Brasil para o formato UTC que a API exige
tz_br = timezone(timedelta(hours=-3))
inicio_dia_br = datetime(data_alvo.year, data_alvo.month, data_alvo.day, 0, 0, 0, tzinfo=tz_br)
fim_dia_br = datetime(data_alvo.year, data_alvo.month, data_alvo.day, 23, 59, 59, tzinfo=tz_br)

# Converte para UTC para mandar para a API
inicio_utc = inicio_dia_br.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
fim_utc = fim_dia_br.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# --- MOTOR DE BUSCA COM CALENDÁRIO ---
def scan_api(chave, min_fav, max_fav, min_zebra, data_ini, data_fim):
    jogos_filtrados = []
    
    # Lista VIP (As mesmas do código anterior)
    ligas_foco = [
        "soccer_brazil_campeonato", "soccer_brazil_campeonato_serie_b",
        "soccer_uefa_champs_league", "soccer_uefa_europa_league", "soccer_conmebol_libertadores", "soccer_conmebol_sudamericana",
        "soccer_epl", "soccer_spain_la_liga", "soccer_italy_serie_a", "soccer_germany_bundesliga", "soccer_france_ligue_one",
        "soccer_portugal_primeira_liga", "soccer_netherlands_eredivisie", "soccer_fifa_world_cup"
    ]
    
    # Pergunta quais ligas estão ativas de graça
    try:
        res_ativas = requests.get(f"https://api.the-odds-api.com/v4/sports/?apiKey={chave}")
        ativas = [s['key'] for s in res_ativas.json() if s['active']]
    except:
        return [], "Erro ao checar ligas ativas."
        
    ligas = [l for l in ligas_foco if l in ativas]
    if not ligas: return [], "Nenhuma liga foco ativa."
    
    progresso = st.progress(0)
    
    for i, liga in enumerate(ligas):
        # A MÁGICA DO CALENDÁRIO AQUI: commenceTimeFrom e commenceTimeTo
        url = f"https://api.the-odds-api.com/v4/sports/{liga}/odds/?apiKey={chave}&regions=eu&markets=h2h&commenceTimeFrom={data_ini}&commenceTimeTo={data_fim}"
        try:
            res = requests.get(url)
            if res.status_code == 200:
                for jogo in res.json():
                    casa, fora = jogo.get("home_team"), jogo.get("away_team")
                    if not jogo.get("bookmakers"): continue
                    
                    odds = {o["name"]: o["price"] for o in jogo["bookmakers"][0]["markets"][0]["outcomes"]}
                    o_c, o_f = odds.get(casa, 0), odds.get(fora, 0)
                    
                    if o_c <= o_f: fav, zeb, o_f, o_z, local = casa, fora, o_c, o_f, "🏠 Casa"
                    else: fav, zeb, o_f, o_z, local = fora, casa, o_f, o_c, "✈️ Fora"

                    if min_fav <= o_f <= max_fav and o_z >= min_zebra:
                        h_utc = datetime.strptime(jogo["commence_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        h_br = h_utc.astimezone(tz_br).strftime("%H:%M")
                        
                        jogos_filtrados.append({
                            "⏰ Hora": h_br, "🏆 Liga": jogo["sport_title"],
                            "🛡️ Favorito": f"⭐ {fav}", "🦓 Zebra": f"🦓 {zeb}",
                            "📍 Local": local, "📈 Odd F": o_f, "📉 Odd Z": o_z
                        })
        except: pass
        progresso.progress((i + 1) / len(ligas))
        
    progresso.empty()
    return jogos_filtrados, "OK"

# --- ENVIO PARA TELEGRAM ---
def enviar_telegram(token, chat, dados, data_alvo):
    if not token or not chat:
        st.error("Preencha o Token e o Chat ID do Telegram!")
        return
    
    mensagem = f"🎯 *RADAR VIP - JOGOS DO DIA {data_alvo.strftime('%d/%m')}*\n\n"
    for j in dados:
        mensagem += f"🏆 {j['🏆 Liga']}\n⏰ {j['⏰ Hora']} | {j['📍 Local']}\n⭐ {j['🛡️ Favorito']} (Odd: {j['📈 Odd F']})\n🦓 {j['🦓 Zebra']} (Odd: {j['📉 Odd Z']})\n\n"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat, "text": mensagem, "parse_mode": "Markdown"}
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        st.success("✅ Pauta enviada para o Telegram com sucesso!")
    else:
        st.error(f"Erro ao enviar: {res.text}")

# --- EXECUÇÃO ---
if 'resultados' not in st.session_state:
    st.session_state.resultados = []

if btn_scan:
    if not api_key: st.warning("Insira a chave da API selecionada.")
    else:
        status.info(f"Buscando jogos exclusivamente para o dia {data_alvo.strftime('%d/%m/%Y')}...")
        resultados, msg = scan_api(api_key, min_f, max_f, min_z, inicio_utc, fim_utc)
        
        if resultados:
            status.success(f"Encontrados {len(resultados)} jogos para a data {data_alvo.strftime('%d/%m')}!")
            st.session_state.resultados = resultados
        else:
            st.session_state.resultados = []
            status.warning(f"Nenhum jogo atendeu aos filtros para o dia {data_alvo.strftime('%d/%m')}.")

# Mostra a tabela e o botão do Telegram se houver resultados na memória
if st.session_state.resultados:
    st.dataframe(pd.DataFrame(st.session_state.resultados), use_container_width=True, hide_index=True)
    
    # Botão para despachar para o celular
    if st.button("📲 ENVIAR PAUTA PARA O TELEGRAM"):
        enviar_telegram(bot_token, chat_id, st.session_state.resultados, data_alvo)