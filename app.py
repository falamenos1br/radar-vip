import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

# --- CONFIGURAÇÃO VISUAL ---
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
        if chave in title_low: 
            return sport_title, f"Torneio {nome}"
    if " - " in sport_title:
        liga, pais_en = sport_title.split(" - ", 1)
        return liga, TRADUCAO.get(pais_en, pais_en)
    return sport_title, "Internacional"

def get_secret(key, default=""):
    try: 
        return st.secrets[key]
    except Exception: 
        return default

def criar_barra(pct):
    blocks = int(pct / 10)
    return "█" * blocks + "▒" * (10 - blocks)

# --- MENU LATERAL ---
with st.sidebar:
    st.markdown("## ⚙️ Configurações")
    opcao_api = st.selectbox("🔑 Conta da API:", ["Conta 1", "Conta 2", "Conta 3", "Conta 4"])
    api_map = {"Conta 1": "api_key_1", "Conta 2": "api_key_2", "Conta 3": "api_key_3", "Conta 4": "api_key_4"}
    api_key = st.text_input("Chave:", value=get_secret(api_map[opcao_api]), type="password")
    data_alvo = st.date_input("📅 Data dos Jogos:", value=datetime.now().date() + timedelta(days=1))
    
    st.markdown("---")
    st.markdown("### 🎯 MODO DE OPERAÇÃO")
    modo_busca = st.radio("Selecione o Mercado:", ["Vitória Seca (1X2)", "Dupla Chance", "Mercado de Gols (API Real)"])
    
    st.markdown("---")
    min_f = max_f = min_z = min_dc = max_dc = min_odd_gol = max_odd_gol = 0.0
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
        
    elif modo_busca == "Mercado de Gols (API Real)":
        mercado_gol = st.selectbox("Linha Exata de Gols:", ["Over 1.5", "Over 2.5", "Over 3.5", "Under 1.5", "Under 2.5", "Under 3.5"])
        st.caption("Filtre pela odd real do mercado de Gols:")
        col5, col6 = st.columns(2)
        with col5: min_odd_gol = st.number_input("Odd Min Gol", value=1.30, step=0.05)
        with col6: max_odd_gol = st.number_input("Odd Max Gol", value=1.80, step=0.05)

    st.markdown("---")
    t_token = st.text_input("Token do Bot:", value=get_secret("bot_token"), type="password")
    t_id = st.text_input("Chat ID:", value=get_secret("chat_id"))
    
    st.markdown("<br>", unsafe_allow_html=True)
    btn_scan = st.button("🚀 EXECUTAR VARREDURA")

if 'creditos_restantes' not in st.session_state: 
    st.session_state.creditos_restantes = "---"
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
    except Exception: 
        return []

@st.cache_data(ttl=1800)
def scan_odds_dados(chave, ligas, d_ini, d_fim, modo, min_f, max_f, min_z, min_dc, max_dc, m_gol, min_odd_gol, max_odd_gol):
    jogos = []
    creditos = "---"
    mercados_api = "h2h,totals,alternate_totals" if modo == "Mercado de Gols (API Real)" else "h2h"
    
    for l_key in ligas:
        url = f"https://api.the-odds-api.com/v4/sports/{l_key}/odds/?apiKey={chave}&regions=eu&markets={mercados_api}&commenceTimeFrom={d_ini}&commenceTimeTo={d_fim}"
        try:
            response = requests.get(url)
            if 'x-requests-remaining' in response.headers:
                creditos = response.headers['x-requests-remaining']
                
            for jogo in response.json():
                bks = jogo.get("bookmakers", [])
                if not bks: continue
                site = next((b for b in bks if b['key'] in ["betano", "betfair_ex_eu", "bet365"]), bks[0])
                h2h_market = next((m for m in site.get('markets', []) if m['key'] == 'h2h'), None)
                if not h2h_market: continue
                
                odds_h2h = {o['name']: o['price'] for o in h2h_market['outcomes']}
                c, f = jogo['home_team'], jogo['away_team']
                oc, of = odds_h2h.get(c, 0), odds_h2h.get(f, 0)
                if oc == 0 or of == 0: continue
                    
                fav, zeb, o_fav, o_zeb = (c, f, oc, of) if oc <= of else (f, c, of, oc)
                o_empate = next((o['price'] for o in h2h_market['outcomes'] if o['name'] == 'Draw'), 3.40)
                
                pct_fav = (1 / o_fav) * 100
                odd_dc = 1 / (min(96.0, pct_fav + (1 / o_empate) * 100) / 100)
                
                odd_gol_real = 0.0
                if modo == "Mercado de Gols (API Real)":
                    target_name = "Over" if "Over" in m_gol else "Under"
                    target_point = float(m_gol.split()[1])
                    for market in site.get('markets', []):
                        if market['key'] in ['totals', 'alternate_totals']:
                            for outcome in market.get('outcomes', []):
                                if outcome['name'] == target_name and outcome.get('point') == target_point:
                                    odd_gol_real = outcome['price']
                                    break
                
                h_br = datetime.strptime(jogo["commence_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(tz_br).strftime("%H:%M")
                liga_nome, pais_nome = identificar_origem(jogo["sport_title"])

                # FILTROS
                if modo == "Vitória Seca (1X2)" and (min_f <= o_fav <= max_f and o_zeb >= min_z):
                    jogos.append({"⏰ Hora": h_br, "🌍 País": pais_nome, "🏆 Liga": liga_nome, "🛡️ Palpite": f"Vitória {fav}", "📈 Odd": round(o_fav, 2), "🎯 Chance %": round(pct_fav, 1), "🦓 Zebra": zeb, "📉 Odd Zebra": round(o_zeb, 2), "🏦 Casa": site['title']})
                elif modo == "Dupla Chance" and (min_dc <= odd_dc <= max_dc):
                    jogos.append({"⏰ Hora": h_br, "🌍 País": pais_nome, "🏆 Liga": liga_nome, "🛡️ Palpite": f"{fav} ou Empate", "📈 Odd DC": round(odd_dc, 2), "🎯 Segura %": round((1/odd_dc)*100, 1), "🏦 Casa": site['title']})
                elif modo == "Mercado de Gols (API Real)" and (min_odd_gol <= odd_gol_real <= max_odd_gol):
                    jogos.append({"⏰ Hora": h_br, "🌍 País": pais_nome, "🏆 Liga": liga_nome, "⚽ Linha": m_gol, "📈 Odd Gol": round(odd_gol_real, 2), "📊 Chance %": round((1/odd_gol_real)*100, 1), "🛡️ Favorito": fav, "🏦 Casa": site['title']})
        except Exception: 
            pass
            
    return jogos, creditos

# --- CRIAÇÃO DAS ABAS (TABS) ---
tab_varredura, tab_dashboard = st.tabs(["🚀 Buscar Jogos VIP", "📈 Dashboard e Simulador"])

with tab_varredura:
    if 'res_pauta' not in st.session_state: st.session_state.res_pauta = []
    if 'modo_salvo' not in st.session_state: st.session_state.modo_salvo = ""

    if btn_scan:
        if not api_key: 
            st.error("⚠️ Insira uma Chave API!")
        else:
            with st.spinner(f"🔄 Buscando pauta de {modo_busca} (Aguarde)..."):
                ligas_f = get_ligas(api_key)
                resultados, creditos = scan_odds_dados(api_key, ligas_f, ini_utc, fim_utc, modo_busca, min_f, max_f, min_z, min_dc, max_dc, mercado_gol, min_odd_gol, max_odd_gol)
                
                st.session_state.creditos_restantes = creditos
                st.session_state.res_pauta = sorted(resultados, key=lambda x: x['⏰ Hora'])
                st.session_state.modo_salvo = modo_busca
                
                if not resultados: 
                    st.warning("Nenhum jogo atendeu aos filtros rigorosos.")
                else: 
                    st.success(f"✅ {len(resultados)} jogos encontrados!")
                    st.rerun() # Atualiza a tela para mostrar os créditos na barra lateral

    if st.session_state.res_pauta:
        st.dataframe(pd.DataFrame(st.session_state.res_pauta), use_container_width=True, hide_index=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📲 PUBLICAR PAUTA NO VIP"):
            if not t_token or not t_id: 
                st.error("⚠️ Faltam dados do Telegram!")
            else:
                modo = st.session_state.modo_salvo
                # HTML format para evitar crash do Telegram
                texto = f"🎯 <b>RADAR VIP - {data_alvo.strftime('%d/%m')}</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
                msgs = []
                
                # --- LÓGICA DA MÚLTIPLA DO DIA ---
                chave_odd = '📈 Odd' if modo == "Vitória Seca (1X2)" else '📈 Odd DC' if modo == "Dupla Chance" else '📈 Odd Gol'
                # Pega os 3 jogos com a menor odd (maior chance)
                top_3_jogos = sorted(st.session_state.res_pauta, key=lambda x: x[chave_odd])[:3]
                odd_multipla = 1.0
                texto_multipla = "🎟️ <b>MÚLTIPLA SUGERIDA (Ouro):</b>\n"
                
                for idx, j in enumerate(st.session_state.res_pauta, 1):
                    bloco = f"🔥 <b>JOGO {idx:02d}</b>\n⏰ <b>{j['⏰ Hora']}</b> | {j['🌍 País']}\n🏆 {j['🏆 Liga']}\n\n"
                    
                    if modo == "Vitória Seca (1X2)":
                        bloco += f"⭐ <b>PALPITE:</b>\n👉 <b>{j['🛡️ Palpite']}</b> (@{j['📈 Odd']:.2f})\n<code>{criar_barra(j['🎯 Chance %'])}</code> <b>{j['🎯 Chance %']:.1f}%</b>\n"
                        bloco += f"🦓 {j['🦓 Zebra']} (@{j['📉 Odd Zebra']:.2f})\n\n"
                    elif modo == "Dupla Chance":
                        bloco += f"🛡️ <b>PALPITE SEGURO:</b>\n👉 <b>{j['🛡️ Palpite']}</b> (@{j['📈 Odd DC']:.2f})\n<code>{criar_barra(j['🎯 Segura %'])}</code> <b>{j['🎯 Segura %']:.1f}%</b>\n\n"
                    elif modo == "Mercado de Gols (API Real)":
                        bloco += f"⚽ <b>MERCADO DE GOLS:</b>\n👉 <b>{j['⚽ Linha']}</b> (@{j['📈 Odd Gol']:.2f})\n<code>{criar_barra(j['📊 Chance %'])}</code> <b>{j['📊 Chance %']:.1f}%</b>\n"
                        bloco += f"🛡️ Favorito no jogo: {j['🛡️ Favorito']}\n\n"
                    
                    bloco += f"🏦 <i>Via {j['🏦 Casa']}</i>\n───────────────\n\n"
                    
                    if len(texto + bloco) > 3500: 
                        msgs.append(texto)
                        texto = f"🎯 <b>RADAR VIP (Cont.)</b>\n━━━━━━━━━━━━━━━━━━━━\n\n" + bloco
                    else: 
                        texto += bloco

                # Adicionar o bloco da múltipla no fim da última mensagem
                if len(top_3_jogos) >= 2:
                    for i, tj in enumerate(top_3_jogos, 1):
                        palpite_mult = tj.get('🛡️ Palpite', tj.get('⚽ Linha'))
                        texto_multipla += f"{i}️⃣ {tj['🏆 Liga']} - {palpite_mult}\n"
                        odd_multipla *= tj[chave_odd]
                    texto_multipla += f"\n📈 <b>Odd Total do Bilhete: @{odd_multipla:.2f}</b>\n───────────────\n\n"
                    
                    if len(texto + texto_multipla) > 3900:
                        msgs.append(texto)
                        texto = texto_multipla
                    else:
                        texto += texto_multipla

                msgs.append(texto)
                
                sucesso = True
                for m in msgs:
                    # Trocado para HTML
                    r = requests.post(f"https://api.telegram.org/bot{t_token}/sendMessage", json={"chat_id": t_id, "text": m, "parse_mode": "HTML"})
                    if r.status_code != 200: 
                        sucesso = False
                        st.error(f"Erro Telegram: {r.text}")
                if sucesso: 
                    st.success("✅ Pauta publicada no VIP com sucesso!")
                    # TODO: Aqui chamaremos a função de salvar no banco de dados!

with tab_dashboard:
    st.markdown("## 📊 Simulador de Lucros e Resultados")
    st.write("Simule quanto você lucraria com base na taxa de acerto do seu radar.")
    
    col_stake, col_info = st.columns([1, 2])
    with col_stake:
        st.info("💡 Escolha o valor da aposta:")
        valor_stake = st.number_input("Valor da Stake (R$):", min_value=0.50, value=10.00, step=0.50)
    
    # --- EXEMPLO DE CÁLCULO VISUAL (Até conectarmos o Banco de Dados) ---
    st.markdown("---")
    st.subheader(f"Desempenho Simulado com Stakes de R$ {valor_stake:.2f}")
    
    # Números fictícios para você ver como a tela vai ficar
    greens = 28
    reds = 6
    odd_media = 1.45
    
    lucro_bruto = greens * (valor_stake * odd_media)
    custo_total = (greens + reds) * valor_stake
    lucro_liquido = lucro_bruto - custo_total
    
    met1, met2, met3 = st.columns(3)
    met1.metric("✅ Greens / ❌ Reds", f"{greens} / {reds}", f"{(greens/(greens+reds))*100:.1f}% Winrate")
    met2.metric("📈 Odd Média Ganhadora", f"@{odd_media:.2f}")
    met3.metric("💰 Lucro Líquido Real", f"R$ {lucro_liquido:.2f}", f"Retorno" if lucro_liquido > 0 else "Prejuízo")

    st.markdown("---")
    st.warning("⚠️ **Atenção:** Os dados acima são apenas uma demonstração visual do layout. Para registrar os jogos reais enviados e checar os placares, precisamos conectar o sistema a um Banco de Dados.")
