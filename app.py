import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración mínima absoluta
st.set_page_config(page_title="ALE! Swap")

# 2. Enlaces a tus datos
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 3. Función de carga ultra-simple
def cargar_datos_basicos():
    try:
        inv = pd.read_csv(URL_INV).fillna("")
        des = pd.read_csv(URL_DES).fillna("")
        inv.columns = [c.strip() for c in inv.columns]
        des.columns = [c.strip() for c in des.columns]
        return inv, des
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 4. Interfaz limpia
st.title("🏗️ ALE! Intercambio Masivo")

with st.sidebar:
    st.write("Panel de Control")
    if st.button("Limpiar Caché"):
        st.cache_data.clear()
        st.info("Caché limpia. Refresca el navegador.")

inv, des = cargar_datos_basicos()

tab1, tab2, tab3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Calcular"])

with tab1:
    if not inv.empty:
        # st.write es lo más seguro contra el error LargeUtf8
        st.write("Listado de Sets Disponibles:")
        st.write(inv[["Socio", "SetID"]])

with tab2:
    if not des.empty:
        st.write("Listado de Sets Buscados:")
        st.write(des[["Socio", "SetID"]])

with tab3:
    if st.button("Buscar Cambios Posibles"):
        G = nx.DiGraph()
        for _, r_des in des.iterrows():
            pide = str(r_des["Socio"]).strip()
            item = str(r_des["SetID"]).strip()
            duenos = inv[inv["SetID"].astype(str).str.strip() == item]
            for _, r_inv in duenos.iterrows():
                tiene = str(r_inv["Socio"]).strip()
                if pide != tiene:
                    G.add_edge(tiene, pide, set_id=item)
        
        ciclos = list(nx.simple_cycles(G))
        if not ciclos:
            st.warning("No hay intercambios circulares todavía.")
        else:
            for i, c in enumerate(ciclos):
                st.success(f"Propuesta de Cambio #{i+1}")
                for j in range(len(c)):
                    da = c[j]
                    recibe = c[(j+1)%len(c)]
                    sid = G[da][recibe]["set_id"]
                    st.write(f"✅ {da} entrega {sid} a {recibe}")
