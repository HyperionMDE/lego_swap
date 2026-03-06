import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de página (Debe ser lo primero)
st.set_page_config(page_title="ALE! Swap", layout="wide")

# 2. URLs de tus Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 3. Base de datos de nombres (Backup)
DICCIONARIO_SETS = {
    "10316": "Rivendell",
    "75192": "Millennium Falcon UCS",
    "21333": "Vincent van Gogh - The Starry Night",
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

# 4. Función de Carga (Simplificada al máximo)
def cargar_datos():
    try:
        df_inv = pd.read_csv(URL_INV).fillna("---")
        df_des = pd.read_csv(URL_DES).fillna("---")
        # Limpieza de columnas
        df_inv.columns = [c.strip() for c in df_inv.columns]
        df_des.columns = [c.strip() for c in df_des.columns]
        # Poner nombres
        df_inv["Nombre"] = df_inv["SetID"].apply(traer_nombre)
        df_des["Nombre"] = df_des["SetID"].apply(traer_nombre)
        return df_inv, df_des
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 5. Interfaz de Usuario
st.title("🏗️ Intercambio Masivo ALE!")

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=100)
    st.markdown("---")
    if st.button("🔄 Forzar Recarga"):
        st.cache_data.clear()
        st.info("Caché limpia. Refresca el navegador.")

inv, des = cargar_datos()

t1, t2, t3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Calcular"])

with t1:
    if not inv.empty:
        st.dataframe(inv[["Socio", "SetID", "Nombre"]], use_container_width=True)

with t2:
    if not des.empty:
        st.dataframe(des[["Socio", "SetID", "Nombre"]], use_container_width=True)

with t3:
    if st.button("Buscar Intercambios"):
        G = nx.DiGraph()
        nombres = pd.concat([inv, des]).set_index("SetID")["Nombre"].to_dict()
        
        for _, r_des in des.iterrows():
            socio_pide = str(r_des["Socio"]).strip()
            set_buscado = str(r_des["SetID"]).strip()
            # Quién lo tiene
            duenos = inv[inv["SetID"].astype(str).str.strip() == set_buscado]
            for _, r_inv in duenos.iterrows():
                socio_da = str(r_inv["Socio"]).strip()
                if socio_pide != socio_da:
                    G.add_edge(socio_da, socio_pide, item=set_buscado)
        
        ciclos = list(nx.simple_cycles(G))
        if not ciclos:
            st.warning("No hay cambios circulares disponibles.")
        else:
            for i, c in enumerate(ciclos):
                with st.expander(f"PROPUESTA #{i+1}"):
                    for j in range(len(c)):
                        d, r = c[j], c[(j+1)%len(c)]
                        sid = G[d][r]["item"]
                        st.write(f"✅ **{d}** da **{sid}** ({nombres.get(sid)}) ➡️ **{r}**")
