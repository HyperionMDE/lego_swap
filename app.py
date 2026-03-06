import streamlit as st
import pandas as pd
import networkx as nx
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ALE! - Intercambio Masivo", page_icon="🏗️", layout="wide")

# URLs de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# --- BASE DE DATOS INTERNA (Garantiza que tus sets se vean bien siempre) ---
DICCIONARIO_SETS = {
    "10316": "Rivendell (Icons)",
    "75192": "Millennium Falcon (UCS)",
    "21333": "The Starry Night (Vincent van Gogh)",
    "10305": "Lion Knights' Castle",
    "75331": "The Razor Crest (UCS)"
}

@st.cache_data(ttl=86400)
def obtener_nombre_set(set_id):
    sid = str(set_id).strip()
    if not sid or sid == "nan": return "ID no válido"
    
    # Prioridad 1: Diccionario local
    if sid in DICCIONARIO_SETS:
        return DICCIONARIO_SETS[sid]
    
    # Prioridad 2: Consulta Rebrickable con nomenclatura -1
    search_id = f"{sid}-1" if "-" not in sid else sid
    try:
        api_url = f"https://rebrickable.com/api/v3/lego/sets/{search_id}/"
        headers = {'Authorization': 'key 9d7b97368d90473950669f64e2621453', 'User-Agent': 'Mozilla/5.0'}
        r = requests.get(api_url, headers=headers, timeout=5)
        if r.status_code == 200:
            return r.json().get('name', f"Set LEGO {sid}")
    except:
        pass
    return f"Set LEGO {sid}"

@st.cache_data(ttl=10)
def cargar_datos():
    try:
        inv = pd.read_csv(URL_INV, dtype=str).fillna("")
        des = pd.read_csv(URL_DES, dtype=str).fillna("")
        inv.columns = inv.columns.str.strip()
        des.columns = des.columns.str.strip()
        
        inv['Nombre'] = inv['SetID'].apply(obtener_nombre_set)
        des['Nombre'] = des['SetID'].apply(obtener_nombre_set)
        return inv, des
    except Exception as e:
        st.error(f"Error de datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- ESTILO ---
st.markdown("""
<style>
    .stApp { background-color: white; }
    [data-testid="stSidebar"] { background-color: #FFD700; border-right: 2px solid #ddd; }
    th { background-color: #2c3e50 !important; color: white !important; }
    .main-title { color: #222; font-size: 2rem; font-
