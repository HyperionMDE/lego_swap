import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de página
st.set_page_config(page_title="ALE! Swap v11", layout="wide")

# 2. URLs de tus Google Sheets
U_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
U_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 3. Función para obtener nombres de sets (con caché para ir rápido)
@st.cache_data
def get_name(sid):
    s = str(sid).strip()
    # Favoritos rápidos
    favs = {"10316": "Rivendell", "75192": "Millennium Falcon UCS", "21333": "The Starry Night"}
    if s in favs: return favs[s]
    try:
        r = requests.get(f"https://rebrickable.com/api/v3/lego/sets/{s}-1/", 
                         headers={"Authorization": "key 9d7b97368d90473950669f64e2621453"}, timeout=2)
        if r.status_code == 200: return r.json().get('name', f"Lego {s}")
    except: pass
    return f"Lego {s}"

# --- INICIO DE LA APP ---
st.title("Plataforma de Intercambio ALE!")

try:
    # Carga de datos original
    inv = pd.read_csv(U_INV).fillna("")
    des = pd.read_csv(U_DES).fillna("")
    
    # Limpieza básica de columnas
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]

    # Preparamos los datos con nombres antes de mostrar las tablas
    with st.spinner("Cargando nombres de sets..."):
        inv["Nombre"] = inv["SetID"].apply(get_name)
        des["Nombre"] = des["SetID"].apply(get_name)
    
    # SECCIÓN 1: INVENTARIO EN TABLA
    st.header("📦 Sets Disponibles para Intercambio")
    # Mostramos solo las columnas deseadas y forzamos strings para evitar errores de tipo
    tabla_inv = inv[["Socio", "SetID", "Nombre"]].astype(str)
    st.table(tabla_inv)

    # SECCIÓN 2: DESEOS EN TABLA
    st.header("❤️ Sets Buscados por los Socios")
    tabla_des = des[["Socio", "SetID", "Nombre"]].astype(str)
    st.table(tabla_des)

    # SECCIÓN 3: CÁLCULO DE INTERCAMBIO
    st.header("🚀 Resultado Óptimo Calculado")
    
    G = nx.DiGraph()
    for _, rd in des.iterrows():
        pide, sid = str(rd["Socio"]).strip(), str(rd["SetID"]).strip()
        duenos = inv[inv["SetID"].astype(str).str.strip() == sid]
        for _, ri in duenos.iterrows():
            da = str(ri["Socio"]).strip()
            if pide != da:
                G.add_edge(da, pide, sid=sid)
    
    ciclos = list(nx.simple_cycles(G))
    if not ciclos:
        st.info("Buscando combinaciones... No hay intercambios circulares posibles con los datos actuales.")
    else:
        mejor = max(ciclos, key=len)
        st.success(f"¡Se ha encontrado una cadena de intercambio para {len(mejor)} socios!")
        
        # Mostrar el resultado de la cadena de forma clara
        for j in range(len(mejor)):
            u1, u2 = mejor[j], mejor[(j+1)%len(mejor)]
            item = G[u1][u2]["sid"]
            nombre_item = inv[inv["SetID"].astype(str).str.strip() == item]["Nombre"].iloc[0]
            st.write(f"✅ **{u1}** entrega el set **{item}** ({nombre_item}) a **{u2}**")

except Exception as e:
    st.error(f"Error al procesar las tablas: {e}")
