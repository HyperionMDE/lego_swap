import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración inicial (Siempre en la primera línea)
st.set_page_config(page_title="ALE! Swap", layout="wide")

# 2. Enlaces a tus hojas de cálculo
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 3. Diccionario de respaldo para asegurar nombres comunes
DICCIONARIO_SETS = {
    "10316": "Rivendell",
    "75192": "Millennium Falcon UCS",
    "21333": "The Starry Night",
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

# 4. Carga de datos ultra-segura
def cargar_datos():
    try:
        # Cargamos los datos crudos
        df_inv = pd.read_csv(URL_INV).fillna("---")
        df_des = pd.read_csv(URL_DES).fillna("---")
        
        # Limpiamos nombres de columnas (quitar espacios invisibles)
        df_inv.columns = [c.strip() for c in df_inv.columns]
        df_des.columns = [c.strip() for c in df_des.columns]
        
        # Generamos los nombres de los sets
        df_inv["Nombre"] = df_inv["SetID"].astype(str).apply(traer_nombre)
        df_des["Nombre"] = df_des["SetID"].astype(str).apply(traer_nombre)
        
        return df_inv, df_des
    except Exception as e:
        st.error(f"Error cargando los datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 5. Interfaz Visual
st.title("🏗️ Intercambio Masivo ALE!")

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=100)
    st.markdown("---")
    if st.button("🔄 Limpiar Memoria"):
        st.cache_data.clear()
        st.warning("Memoria limpia. Por favor, refresca tu navegador (F5).")

# Cargamos los datos antes de las pestañas
inv, des = cargar_datos()

# Usamos st.tabs para organizar
t1, t2, t3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Calcular Cambios"])

with t1:
    if not inv.empty:
        # Usamos st.table: es lo más simple y evita el error "LargeUtf8"
        st.table(inv[["Socio", "SetID", "Nombre"]])

with t2:
    if not des.empty:
        st.table(des[["Socio", "SetID", "Nombre"]])

with t3:
    if st.button("Buscar Intercambios Circulares"):
        G = nx.DiGraph()
        # Mapeo global de nombres para el resultado
        nombres_map = pd.concat([inv, des]).set_index("SetID")["Nombre"].to_dict()
        
        for _, fila_des in des.iterrows():
            socio_pide = str(fila_des["Socio"]).strip()
            set_buscado = str(fila_des["SetID"]).strip()
            
            # Quién tiene el set que este socio busca
            poseedores = inv[inv["SetID"].astype(str).str.strip() == set_buscado]
            for _, fila_inv in poseedores.iterrows():
                socio_da = str(fila_inv["Socio"]).strip()
                if socio_pide != socio_da:
                    G.add_edge(socio_da, socio_pide, set_id=set_buscado)
        
        ciclos = list(nx.simple_cycles(G))
        if not ciclos:
            st.info("No se han encontrado ciclos de cambio todavía. ¡Sigue añadiendo sets!")
        else:
            for i, ciclo in enumerate(ciclos):
                with st.expander(f"PROPUESTA DE CAMBIO #{i+1}"):
                    for j in range(len(ciclo)):
                        da = ciclo[j]
                        recibe = ciclo[(j+1)%len(ciclo)]
                        sid = G[da][recibe]["set_id"]
                        st.write(f"✅ **{da}** le entrega **{sid}** ({nombres_map.get(sid)}) a **{recibe}**")
