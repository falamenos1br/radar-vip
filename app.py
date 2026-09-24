import streamlit as st
import pandas as pd
import requests
import json
import gspread
from datetime import datetime, timedelta, timezone

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Radar VIP | Agência Pro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #0f172a !important; color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    h1 { color: #fbbf24 !important; text-align: center; font-weight: 900; font-size: 32px !important; margin-bottom: 30px; }
    h2, h3 { color: #e2e8f0 !important; font-weight: 600 !important; }
    p, span, div, label { color: #cbd5e1 !important; }
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

# ==========================================
# ⚙️ NOME DA SUA PLANILHA NO GOOGLE DRIVE ⚙️
NOME_DA_PLANILHA = "Banco_Dados_Radar"
# ==========================================

# --- DICIONÁRIOS ---
TRADUCAO = {
    "Germany": "Alemanha", "England": "Inglaterra", "Spain": "Espanha", "Italy": "Itália",
    "France": "França", "Portugal": "Portugal", "Netherlands": "Holanda", "Brazil": "Brasil",
    "Argentina": "Argentina", "Uruguay": "Uruguai", "Mexico": "México", "USA": "EUA"
}
CONTINENTAIS = {"uefa": "Europa 🇪🇺", "conmebol": "América do Sul 🌎", "libertadores": "Libertadores", "sudamericana": "Sul-Americana"}

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
    except Exception: return default

def criar_barra(pct):
    blocks = int(pct / 10)
    return "█" * blocks + "▒" * (10 - blocks)

# --- FUNÇÃO DO GOOGLE SHEETS ---
def conectar_planilha():
    try:
        if "google_json" not in st.secrets:
            return None, "⚠️ Chave 'google_json' não encontrada nos Secrets."
        cred_dict = json.loads(st.secrets["google_json"])
        gc = gspread.service_account_from_dict(cred_dict)
        planilha = gc.open(NOME_DA_PLANILHA)
        return planilha, "OK"
    except Exception as e:
        return None, f"⚠️ Erro ao conectar no Sheets: {e}"

def salvar_no_sheets(dados, modo):
    planilha, msg = conectar_planilha()
    if not planilha:
        st.error(msg)
        return False

    mes_atual = datetime.now().strftime("%m_%Y")
    try: aba = planilha.worksheet(mes_atual)
    except gspread.exceptions.WorksheetNotFound:
        aba = planilha.add_worksheet(title=mes_atual, rows="1000", cols="10")
        aba.append_row(["Data", "Hora", "País", "Liga", "Palpite", "Odd", "Mercado", "Tipo", "Resultado"])

    data_hoje = datetime.now().strftime("%d/%m/%Y")
    linhas_para_inserir = []

    for j in dados:
        odd = j.get('📈 Odd', j.get('📈 Odd DC', j.get('📈 Odd Gol', 0)))
        palpite = j.get('🛡️ Palpite', j.get('⚽ Linha', ''))
        linhas_para_inserir.append([data_hoje, j['⏰ Hora'], j['🌍 País'], j['🏆 Liga'], palpite, odd, modo, "Simples", "Pendente"])
    
    chave_odd = '📈 Odd' if modo == "Vitória Seca (1X2)" else '📈 Odd DC' if modo == "Dupla Chance" else '📈 Odd Gol'
    top_3_jogos = sorted(dados, key=lambda x: x[chave_odd])[:3]
    if len(top_3_jogos) >= 2:
        odd_total = 1.0
        palpite_multipla = ""
        for i, tj in enumerate(top_3_jogos, 1):
            palpite_multipla += f"{i}. {tj.get('🛡️ Palpite', tj.get('⚽ Linha', ''))} | "
            odd_total *= tj[chave_odd]
        linhas_para_inserir.append([data_hoje, "---", "Múltipla", "Combinada", palpite_multipla, round(odd_total, 2), modo, "Múltipla", "Pendente"])

    aba.append_rows(linhas_para_inserir)
    return True

# --- MENU LATERAL ---
with st.sidebar:
    st.markdown("## ⚙️ Configurações")
    opcao_api = st.selectbox("🔑 Conta da API:", ["Conta 1", "Conta 2", "Conta 3", "Conta 4"])
    api_map = {"Conta 1": "api_key_1", "Conta 2": "api_key_2", "Conta 3": "api_key_3", "Conta 4": "api_key_4"}
    api_key = st.text_input("Chave API:", value=get_secret(api_map[opcao_api]), type="password")
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
        min_z = st.number_input("Odd Min Zebra", value=3.50, step=0.10)
    elif modo_busca == "Dupla Chance":
        col3, col4 = st.columns(2)
        with col3: min_dc = st.number_input("DC Min", value=1.10, step=0.02)
        with col4: max_dc = st.number_input("DC Max", value=1.40, step=0.02)
    elif modo_busca == "Mercado de Gols (API Real)":
        mercado_gol = st.selectbox("Linha de Gols:", ["Over 1.5", "Over 2.5", "Over 3.5", "Under 1.5", "Under 2.5", "Under 3.5"])
        col5, col6 = st.columns(2)
        with col5: min_odd_gol = st.number_input("Odd Min Gol", value=1.30, step=0.05)
        with col6: max_odd_gol = st.number_input("Odd Max Gol", value=1.80, step=0.05)

    st.markdown("---")
    t_token = st.text_input("Token Bot Telegram:", value=get_secret("bot_token"), type="password")
    t_id = st.text_input("Chat ID Telegram:", value=get_secret("chat_id"))
    
    btn_scan = st.button("🚀 EXECUTAR VARREDURA")

if 'creditos_restantes' not in st.session_state: st.session_state.creditos_restantes = "---"
st.sidebar.info(f"💳 Créditos Restantes: {st.session_state.creditos_restantes}")

tz_br = timezone(timedelta(hours=-3))
ini_utc = datetime(data_alvo.year, data_alvo.month, data_alvo.day, 0, 0, 0, tzinfo=tz_br).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
fim_utc = datetime(data_alvo.year, data_alvo.month, data_alvo.day, 23, 59, 59, tzinfo=tz_br).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

@st.cache_data(ttl=3600)
def get_ligas(chave):
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={chave}"
    try:
        res = requests.get(url).json()
        # REMOVIDO: O bloqueio de ligas inferiores. Agora puxa QUALQUER torneio de futebol.
        return [l['key'] for l in res if "soccer" in l['key'].lower()]
    except Exception: return []

@st.cache_data(ttl=1800)
def scan_odds_dados(chave, ligas, d_ini, d_fim, modo, min_f, max_f, min_z, min_dc, max_dc, m_gol, min_odd_gol, max_odd_gol):
    jogos = []
    creditos = "---"
    mercados_api = "h2h,totals,alternate_totals" if modo == "Mercado de Gols (API Real)" else "h2h"
    
    for l_key in ligas:
        url = f"https://api.the-odds-api.com/v4/sports/{l_key}/odds/?apiKey={chave}&regions=eu,uk&markets={mercados_api}&commenceTimeFrom={d_ini}&commenceTimeTo={d_fim}"
        try:
            response = requests.get(url)
            if 'x-requests-remaining' in response.headers: creditos = response.headers['x-requests-remaining']
            
            for jogo in response.json():
                bks = jogo.get("bookmakers", [])
                if not bks: continue
                
                # ADICIONADO: Nova hierarquia de Casas (Betano > Betfair > Bet365)
                casas_preferidas = ["betano", "betfair_ex_eu", "bet365"]
                bks_sorted = sorted(bks, key=lambda b: casas_preferidas.index(b['key']) if b['key'] in casas_preferidas else 999)
                
                jogo_valido = False
                
                for site in bks_sorted:
                    if jogo_valido: break 
                    
                    h2h_market = next((m for m in site.get('markets', []) if m['key'] == 'h2h'), None)
                    if not h2h_market: continue
                    
                    odds_h2h = {o['name']: o['price'] for o in h2h_market['outcomes']}
                    c, f = jogo['home_team'], jogo['away_team']
                    oc, of = odds_h2h.get(c, 0), odds_h2h.get(f, 0)
                    if oc == 0 or of == 0: continue
                        
                    oc, of = round(oc, 2), round(of, 2)
                    fav, zeb, o_fav, o_zeb = (c, f, oc, of) if oc <= of else (f, c, of, oc)
                    
                    o_empate = round(next((o['price'] for o in h2h_market['outcomes'] if o['name'] == 'Draw'), 3.40), 2)
                    
                    pct_fav = (1 / o_fav) * 100
                    odd_dc = round(1 / (min(96.0, pct_fav + (1 / o_empate) * 100) / 100), 2)
                    
                    odd_gol_real = 0.0
                    if modo == "Mercado de Gols (API Real)":
                        target_name = "Over" if "Over" in m_gol else "Under"
                        target_point = float(m_gol.split()[1])
                        for market in site.get('markets', []):
                            if market['key'] in ['totals', 'alternate_totals']:
                                for outcome in market.get('outcomes', []):
                                    if outcome['name'] == target_name and outcome.get('point') == target_point:
                                        odd_gol_real = round(outcome['price'], 2)
                                        break
                    
                    h_br = datetime.strptime(jogo["commence_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(tz_br).strftime("%H:%M")
                    liga_nome, pais_nome = identificar_origem(jogo["sport_title"])

                    if modo == "Vitória Seca (1X2)" and (min_f <= o_fav <= max_f and o_zeb >= min_z):
                        jogos.append({"⏰ Hora": h_br, "🌍 País": pais_nome, "🏆 Liga": liga_nome, "🛡️ Palpite": f"Vitória {fav}", "📈 Odd": o_fav, "🎯 Chance %": round(pct_fav, 1), "⚖️ Empate": o_empate, "🦓 Zebra": zeb, "📉 Odd Zebra": o_zeb, "🏦 Casa": site['title']})
                        jogo_valido = True
                        
                    elif modo == "Dupla Chance" and (min_dc <= odd_dc <= max_dc):
                        jogos.append({"⏰ Hora": h_br, "🌍 País": pais_nome, "🏆 Liga": liga_nome, "🛡️ Palpite": f"{fav} ou Empate", "📈 Odd DC": odd_dc, "🎯 Segura %": round((1/odd_dc)*100, 1), "🏦 Casa": site['title']})
                        jogo_valido = True
                        
                    elif modo == "Mercado de Gols (API Real)" and (min_odd_gol <= odd_gol_real <= max_odd_gol):
                        jogos.append({"⏰ Hora": h_br, "🌍 País": pais_nome, "🏆 Liga": liga_nome, "⚽ Linha": m_gol, "📈 Odd Gol": odd_gol_real, "📊 Chance %": round((1/odd_gol_real)*100, 1), "🛡️ Favorito": fav, "🏦 Casa": site['title']})
                        jogo_valido = True

        except Exception as e: 
            pass
            
    return jogos, creditos

# --- ABAS PRINCIPAIS ---
tab_varredura, tab_dashboard = st.tabs(["🚀 Buscar Jogos VIP", "📈 Dashboard e Simulador"])

with tab_varredura:
    if 'res_pauta' not in st.session_state: st.session_state.res_pauta = []
    if 'modo_salvo' not in st.session_state: st.session_state.modo_salvo = ""

    if btn_scan:
        if not api_key: st.error("⚠️ Insira uma Chave API!")
        else:
            with st.spinner(f"🔄 Buscando pauta de {modo_busca} (Aguarde)..."):
                ligas_f = get_ligas(api_key)
                resultados, creditos = scan_odds_dados(api_key, ligas_f, ini_utc, fim_utc, modo_busca, min_f, max_f, min_z, min_dc, max_dc, mercado_gol, min_odd_gol, max_odd_gol)
                
                st.session_state.creditos_restantes = creditos
                st.session_state.res_pauta = sorted(resultados, key=lambda x: x['⏰ Hora'])
                st.session_state.modo_salvo = modo_busca
                if not resultados: st.warning("Nenhum jogo atendeu aos filtros.")
                else: 
                    st.success(f"✅ {len(resultados)} jogos encontrados!")
                    st.rerun()

    if st.session_state.res_pauta:
        st.dataframe(pd.DataFrame(st.session_state.res_pauta), use_container_width=True, hide_index=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("📲 PUBLICAR NO VIP E SALVAR"):
            if not t_token or not t_id: 
                st.error("⚠️ Faltam dados do Telegram!")
            else:
                modo = st.session_state.modo_salvo
                texto = f"🎯 <b>RADAR VIP - {data_alvo.strftime('%d/%m')}</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
                msgs = []
                
                chave_odd = '📈 Odd' if modo == "Vitória Seca (1X2)" else '📈 Odd DC' if modo == "Dupla Chance" else '📈 Odd Gol'
                top_3_jogos = sorted(st.session_state.res_pauta, key=lambda x: x[chave_odd])[:3]
                odd_multipla = 1.0
                texto_multipla = "🎟️ <b>MÚLTIPLA SUGERIDA (Ouro):</b>\n"
                
                for idx, j in enumerate(st.session_state.res_pauta, 1):
                    bloco = f"🔥 <b>JOGO {idx:02d}</b>\n⏰ <b>{j['⏰ Hora']}</b> | {j['🌍 País']}\n🏆 {j['🏆 Liga']}\n\n"
                    
                    if modo == "Vitória Seca (1X2)":
                        bloco += f"⭐ <b>PALPITE:</b>\n👉 <b>{j['🛡️ Palpite']}</b> (@{j['📈 Odd']:.2f})\n<code>{criar_barra(j['🎯 Chance %'])}</code> <b>{j['🎯 Chance %']:.1f}%</b>\n"
                        bloco += f"⚖️ Empate (@{j['⚖️ Empate']:.2f})\n"
                        bloco += f"🦓 {j['🦓 Zebra']} (@{j['📉 Odd Zebra']:.2f})\n\n"
                    elif modo == "Dupla Chance":
                        bloco += f"🛡️ <b>PALPITE SEGURO:</b>\n👉 <b>{j['🛡️ Palpite']}</b> (@{j['📈 Odd DC']:.2f})\n<code>{criar_barra(j['🎯 Segura %'])}</code> <b>{j['🎯 Segura %']:.1f}%</b>\n\n"
                    elif modo == "Mercado de Gols (API Real)":
                        bloco += f"⚽ <b>MERCADO DE GOLS:</b>\n👉 <b>{j['⚽ Linha']}</b> (@{j['📈 Odd Gol']:.2f})\n<code>{criar_barra(j['📊 Chance %'])}</code> <b>{j['📊 Chance %']:.1f}%</b>\n\n"
                    
                    bloco += f"🏦 <i>Via {j['🏦 Casa']}</i>\n───────────────\n\n"
                    if len(texto + bloco) > 3500: 
                        msgs.append(texto)
                        texto = f"🎯 <b>RADAR VIP (Cont.)</b>\n━━━━━━━━━━━━━━━━━━━━\n\n" + bloco
                    else: texto += bloco

                if len(top_3_jogos) >= 2:
                    for i, tj in enumerate(top_3_jogos, 1):
                        palpite_mult = tj.get('🛡️ Palpite', tj.get('⚽ Linha'))
                        texto_multipla += f"{i}️⃣ {tj['🏆 Liga']} - {palpite_mult}\n"
                        odd_multipla *= tj[chave_odd]
                    texto_multipla += f"\n📈 <b>Odd Total: @{odd_multipla:.2f}</b>\n───────────────\n\n"
                    
                    if len(texto + texto_multipla) > 3900:
                        msgs.append(texto)
                        texto = texto_multipla
                    else: texto += texto_multipla

                msgs.append(texto)
                
                sucesso = True
                for m in msgs:
                    r = requests.post(f"https://api.telegram.org/bot{t_token}/sendMessage", json={"chat_id": t_id, "text": m, "parse_mode": "HTML"})
                    if r.status_code != 200: sucesso = False; st.error(f"Erro Telegram: {r.text}")
                
                if sucesso:
                    with st.spinner("Salvando dados na Planilha do Google..."):
                        salvo_ok = salvar_no_sheets(st.session_state.res_pauta, modo)
                        if salvo_ok: st.success("✅ Pauta publicada e jogos salvos no Banco de Dados!")

with tab_dashboard:
    st.markdown("## 📊 Dashboard de Desempenho")
    
    col_mes, col_stake = st.columns(2)
    with col_mes:
        mes_visualizar = st.text_input("Qual mês deseja analisar? (Ex: 09_2026)", value=datetime.now().strftime("%m_%Y"))
    with col_stake:
        valor_stake = st.number_input("💰 Valor da Stake (R$):", min_value=0.50, value=10.00, step=0.50)
    
    if st.button("🔄 Atualizar Resultados da Planilha"):
        planilha, msg = conectar_planilha()
        if planilha:
            try:
                aba = planilha.worksheet(mes_visualizar)
                dados_tabela = aba.get_all_records()
                df = pd.DataFrame(dados_tabela)
                
                if df.empty:
                    st.warning("Nenhum jogo registrado neste mês ainda.")
                else:
                    greens_simples = df[(df['Tipo'] == 'Simples') & (df['Resultado'].astype(str).str.contains("Green|✅", case=False, na=False))]
                    reds_simples = df[(df['Tipo'] == 'Simples') & (df['Resultado'].astype(str).str.contains("Red|❌", case=False, na=False))]
                    
                    greens_multipla = df[(df['Tipo'] == 'Múltipla') & (df['Resultado'].astype(str).str.contains("Green|✅", case=False, na=False))]
                    reds_multipla = df[(df['Tipo'] == 'Múltipla') & (df['Resultado'].astype(str).str.contains("Red|❌", case=False, na=False))]

                    qtd_green = len(greens_simples)
                    qtd_red = len(reds_simples)
                    odd_media_g = greens_simples['Odd'].astype(float).mean() if qtd_green > 0 else 0
                    
                    lucro_s = (qtd_green * (valor_stake * odd_media_g)) - ((qtd_green + qtd_red) * valor_stake)

                    st.markdown("### 🎲 Entradas Simples")
                    met1, met2, met3 = st.columns(3)
                    winrate = (qtd_green / (qtd_green + qtd_red) * 100) if (qtd_green + qtd_red) > 0 else 0
                    met1.metric("✅ Greens / ❌ Reds", f"{qtd_green} / {qtd_red}", f"{winrate:.1f}% Winrate")
                    met2.metric("📈 Odd Média Vencedora", f"@{odd_media_g:.2f}")
                    met3.metric("💰 Lucro Líquido", f"R$ {lucro_s:.2f}", "Retorno")

                    qtd_gm = len(greens_multipla)
                    qtd_rm = len(reds_multipla)
                    odd_media_gm = greens_multipla['Odd'].astype(float).mean() if qtd_gm > 0 else 0
                    
                    lucro_m = (qtd_gm * (valor_stake * odd_media_gm)) - ((qtd_gm + qtd_rm) * valor_stake)
                    
                    st.markdown("### 🎟️ Entradas Múltiplas (Bilhetes Ouro)")
                    m1, m2, m3 = st.columns(3)
                    winrate_m = (qtd_gm / (qtd_gm + qtd_rm) * 100) if (qtd_gm + qtd_rm) > 0 else 0
                    m1.metric("✅ Greens / ❌ Reds", f"{qtd_gm} / {qtd_rm}", f"{winrate_m:.1f}% Winrate")
                    m2.metric("📈 Odd Média Vencedora", f"@{odd_media_gm:.2f}")
                    m3.metric("💰 Lucro Líquido", f"R$ {lucro_m:.2f}", "Retorno")

            except gspread.exceptions.WorksheetNotFound:
                st.warning(f"O mês '{mes_visualizar}' ainda não existe na planilha.")
        else:
            st.error(msg)
