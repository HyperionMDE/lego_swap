import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de Marca
st.set_page_config(page_title="ALE! Swap", layout="wide")

# URLs de tus Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 2. Motor de Nombres (Recuperado y Blindado)
@st.cache_data(ttl=600)
def traer_nombre_lego(set_id):
    sid = str(set_id).strip()
    # Diccionario rápido para los sets de las fotos
    nombres_propios = {
        "10316": "Rivendell",
        "75192": "Millennium Falcon UCS",
        "21333": "The Starry Night (Van Gogh)"
    }
    if sid in nombres_propios:
        return nombres_propios[sid]
    
    try:
        search_id = sid if "-" in sid else f"{sid}-1"
        url = f"https://rebrickable.com/api/v3/lego/sets/{search_id}/"
        headers = {"Authorization": "key 9d7b97368d90473950669f64e2621453"}
        r = requests.get(url, headers=headers, timeout=3)
        if r.status_code == 200:
            return r.json().get("name", f"Set {sid}")
    except:
        pass
    return f"LEGO Set {sid}"

# 3. Carga de Datos
def cargar_datos():
    try:
        df_i = pd.read_csv(URL_INV).fillna("")
        df_d = pd.read_csv(URL_DES).fillna("")
        df_i.columns = [c.strip() for c in df_i.columns]
        df_d.columns = [c.strip() for c in df_d.columns]
        
        # Generar nombres automáticamente
        df_i["Nombre"] = df_i["SetID"].apply(traer_nombre_lego)
        df_d["Nombre"] = df_d["SetID"].apply(traer_nombre_lego)
        
        return df_i, df_d
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 4. Interfaz con Colores ALE!
# Usamos columnas para el encabezado en lugar de CSS complejo
col_logo, col_titulo = st.columns([1, 4])

with
