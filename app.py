import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="ALE! Swap v1.0", layout="wide")

# URLs de tus Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 2. MOTOR DE NOMBRES (REBRICKABLE)
@st.cache_data(ttl=3600)
def obtener_nombre_set(set_id):
    sid = str(set_id).strip()
    # Diccionario de seguridad para carga rápida
    favoritos = {"10316": "Rivendell", "75192": "Millennium Falcon UCS", "21333": "The Starry Night"}
    if sid in favoritos: return favoritos[sid]
    try:
        url = f"https://rebrickable.com/api/v3/lego/sets/{sid}-1/"
        headers = {"Authorization": "key 9d7b97368d90473950669f64e2621453"}
        r = requests.get(url, headers=headers, timeout=3)
        if r.status_code == 200: return r.json().get('name', f"Set {sid}")
    except: pass
    return f"Lego {sid}"

# 3. CARGA DE DATOS
def cargar_todo():
    try:
        inv = pd.read_csv(URL_INV).fillna("")
        des = pd.read_csv(URL_DES).fillna("")
        inv.columns = [c.strip() for c in inv.columns]
        des.columns = [c.strip() for c in des.columns]
        # Generar nombres
        inv["Nombre"] = inv["SetID"].astype(str).apply(obtener_nombre_set)
        des["Nombre"] = des["SetID"].astype(str).apply(obtener_nombre_set)
        return inv, des
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 4. INTERFAZ VISUAL
col_l, col_t = st.columns([1, 5])
with col_l:
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=80)
with col_t:
    st.title("Plataforma de Intercambio ALE!")
    st.caption("v1.0 - Sistema de Gestión de Sets")

inv_df, des_df = cargar_todo()

t1, t2, t3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Calcular"])

with t1:
    if not inv_df.empty:
        # st.table es la opción más segura contra errores de visualización
        st.table(inv_df[["Socio", "SetID", "Nombre"]])

with t2:
    if not des_df.empty:
        st.table(des_df[["Socio", "SetID", "Nombre"]])

with t3:
    if st.button("Buscar Intercambios"):
        G = nx.DiGraph()
        nombres = pd.concat([inv_df, des_df]).set_index("SetID")["Nombre"].to_dict()
        for _, r_d in des_df.iterrows():
            p = str(r_d["Socio"]).strip()
            i = str(r_d["SetID"]).strip()
            poseedores = inv_df[inv_df["SetID"].astype(str).str.strip() == i]
            for _, r_i in poseedores.iterrows():
                d = str(r_i["Socio"]).strip()
                if p != d: G.add_edge(d, p, set_id=i)
        
        ciclos = list(nx.simple_cycles(G))
        if not ciclos:
            st.info("No hay ciclos disponibles.")
        else:
            for i, c in enumerate(ciclos):
                with st.expander(f"Propuesta #{i+1}"):
                    for j in range(len(c)):
                        u1, u2 = c[j], c[(j+1)%len(c)]
                        sid = G[u1][u2]["set_id"]
                        st.write(f"✅ **{u1}** da **{sid}** ({nombres.get(sid)}) a **{u2}**")
