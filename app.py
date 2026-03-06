import streamlit as st
import pandas as pd
import networkx as nx
import requests

# --- CONFIGURACIÓN BÁSICA ---
st.set_page_config(page_title="ALE! Swap", layout="wide")

# URLs de Google Sheets (Verifica que estas URLs sean las correctas en tu Sheets)
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# Diccionario interno para asegurar nombres de tus sets principales
DICCIONARIO_SETS = {
    "10316": "Rivendell",
    "75192": "Millennium Falcon UCS",
    "21333": "Vincent van Gogh - The Starry Night",
    "10305": "Lion Knights' Castle",
    "75331": "The Razor Crest UCS"
}

@st.cache_data(ttl=600)
def obtener_nombre(set_id):
    sid = str(set_id).strip()
    if sid in DICCIONARIO_SETS:
        return DICCIONARIO_SETS[sid]
    try:
        # Intento de conexión con Rebrickable (con nomenclatura -1)
        search_id = f"{sid}-1" if "-" not in sid else sid
        url = f"https://rebrickable.com/api/v3/lego/sets/{search_id}/"
        headers = {'Authorization': 'key 9d7b97368d90473950669f64e2621453'}
        r = requests.get(url, headers=headers, timeout=3)
        if r.status_code == 200:
            return r.json().get('name', f"Set {sid}")
    except:
        pass
    return f"Set LEGO {sid}"

def cargar_datos():
    try:
        # Carga cruda de los CSV
        df_
