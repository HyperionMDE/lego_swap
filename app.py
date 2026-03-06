import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de página (Debe ser lo primero)
st.set_page_config(page_title="ALE! Swap", layout="wide")

# 2. URLs de tus Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 3. Base de datos de nombres (Backup para asegurar carga inmediata)
DICCIONARIO_SETS = {
    "10316": "Rivendell",
    "75192": "Millennium Falcon UCS",
    "21333": "The Starry Night (Vincent van Gogh)",
    "10305": "Lion Knights' Castle",
    "75331": "The Razor Crest UCS"
}

@st.cache_data(ttl=600)
def traer_nombre(set_id):
    sid = str(set_id).strip()
    if sid in DICCIONARIO_SETS:
        return DICCIONARIO_SETS[sid]
    try:
        search_id = sid if "-" in sid else f"{sid}-1"
        url = f"https://rebrickable.com/api/v3/lego/sets/{search_id}/"
        headers = {"Authorization": "key 9d7b97368d90473950669f64e2621453"}
        r = requests.get(url, headers=headers, timeout=3)
        if r.status_code == 200:
            return r.json().get("name", f"Set {sid}")
    except:
        pass
    return f"Set LEGO {sid}"

# 4. Función de Carga (Simplificada para evitar el error LargeUtf8)
def cargar_datos():
    try:
        df_inv = pd.read_csv(URL_INV).fillna("---")
        df_des = pd.read_csv(URL_DES).fillna("---")
        # Limpieza de columnas
        df_inv.columns = [c.strip() for c in df_inv.columns]
        df_des.columns = [c.strip() for
