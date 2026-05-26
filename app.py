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
    api_teste = st.text_input("Chave API para teste rápido:", type="password", key="teste_api")
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

CONTIN
