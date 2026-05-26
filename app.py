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
    opcao_api =
