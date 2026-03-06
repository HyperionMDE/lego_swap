import streamlit as st
import pandas as pd
import networkx as nx
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ALE! - Intercambio Masivo", page_icon="🏗️", layout="wide")

# URLs de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# --- FUNCIÓN DE BÚSQUEDA CON NOMENCLATURA REBRICKABLE ---
@st.cache_data(ttl=86400)
def obtener_nombre_set(set_id):
    if not set_id or str(set_id).strip() == "" or str(set_id) == "nan": 
        return "ID No válido"
    
    # Limpiamos el ID
    sid = str(set_id).strip()
    
    # REGLA DE NOMENCLATURA: Si no tiene guion, le añadimos el -1
    if "-" not in sid:
        search_id = f"{sid}-1"
    else:
        search_id = sid

    try:
        # Usamos la clave de API que ya tenemos
        api_url = f"https://rebrickable.com/api/v3/lego/sets/{search_id}/"
        headers = {
            'Authorization': 'key 9d7b97368d90473950669f64e2621453',
            'User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(api_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json().get('name', f"Set LEGO {sid}")
        else:
            return f"Set LEGO {sid}"
    except:
        return f"Set LEGO {sid}"

@st.cache_data(ttl=20)
def cargar_y_procesar():
    try:
        inv = pd.read_csv(URL_INV, dtype=str).fillna("")
        des = pd.read_csv(URL_DES, dtype=str).fillna("")
        inv.columns = inv.columns.str.strip()
        des.columns = des.columns.str.strip()

        if 'SetID' in inv.columns:
            inv['Nombre'] = inv['SetID'].apply(obtener_nombre_set)
        if 'SetID' in des.columns:
            des['Nombre'] = des['SetID'].apply(obtener_nombre_set)
            
        return inv, des
    except Exception as e:
        st.error(f"Error al leer Excel: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- ESTILO ---
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #FFD700; border-right: 2px solid #ddd; }
    th { background-color: #333333 !important; color: white !important; }
    .main-title { color: #222; font-size: 2.2rem; font-weight: 800; border-bottom: 4px solid #D32F2F; display: inline-block; margin-bottom: 20px;}
</style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL (Logos LEGO y ALE!) ---
with st.sidebar:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.
