import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de Página (Sin barra lateral por defecto)
st.set_page_config(page_title="ALE! Swap v3.0", layout="centered")

# URLs de datos
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 2. Motor de Nombres de Sets
@st.cache_data(ttl=3600)
def fetch_set_name(set_id):
    sid = str(set_id).strip()
    # Diccionario de emergencia para asegurar tus sets principales
    hardcoded = {"10316": "Rivendell", "75192": "Millennium Falcon UCS", "21333": "The Starry Night"}
    if sid in hardcoded: return hardcoded[sid]
    try:
        url = f"https://rebrickable.com/api/v3/lego/sets/{sid}-1/"
        headers = {"Authorization": "key 9d7b97368d90473950669f64e2621453"}
        r = requests.get(url, headers=headers, timeout=3)
        if r.status_code == 200: return r.json().get('name', f"Set {sid}")
    except: pass
    return f"Lego {sid}"

# 3. Función para mostrar tablas sin errores de "LargeUtf8"
def mostrar_tabla_segura(df):
    # Convertimos el DataFrame a Markdown (Texto puro)
    # Esto evita que Streamlit use su motor de tablas complejo que falla
    st.markdown(df.to_markdown(index=False))

# 4. Carga de datos
def cargar_datos_v3():
    try:
        inv = pd.read_csv(URL_INV).fillna("")
        des = pd.read_csv(URL_DES).fillna("")
        inv.columns = [c.strip() for c in inv.columns]
        des.columns = [c.strip() for c in des.columns]
        inv["Nombre"] = inv["SetID"].astype(str).apply(fetch_set_name)
        des["Nombre"] = des["SetID"].astype(str).apply(fetch_set_name)
        return inv, des
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- INTERFAZ ---

# Logo y Título centrados
st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=100)
st.title("Plataforma de Intercambio ALE!")
st.write("Versión 3.0 - Limpia y Estable")

inv_df, des_df = cargar_datos_v3()

# Botón de refresco ahora arriba y visible, ya que no hay barra lateral
if st.button("🔄 Forzar Recarga de Datos"):
    st.cache_data.clear()
    st.rerun()

tab1, tab2, tab3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Calcular"])

with tab1:
    if not inv_df.empty:
        st.subheader("Sets Disponibles")
        mostrar_tabla_segura(inv_df[["Socio", "SetID", "Nombre"]])

with tab2:
    if not des_df.empty:
        st.subheader("Sets Buscados")
        mostrar_tabla_segura(des_df[["Socio", "SetID", "Nombre"]])

with tab3:
    if st.button("🔍 Buscar Cambios Circulares"):
        G = nx.DiGraph()
        n_map = pd.concat([inv_df, des_df]).set_index("SetID")["Nombre"].to_dict()
        
        for _, rd in des_df.iterrows():
            pide = str(rd["Socio"]).strip()
            sid = str(rd["SetID"]).strip()
            poseedores = inv_df[inv_df["SetID"].astype(str).str.strip() == sid]
            for _, ri in poseedores.iterrows():
                da = str(ri["Socio"]).strip()
                if pide != da:
                    G.add_edge(da, pide, set_id=sid)
        
        ciclos = list(nx.simple_cycles(G))
        if not ciclos:
            st.info("No hay intercambios circulares posibles ahora mismo.")
        else:
            st.success(f"¡Encontradas {len(ciclos)} propuestas!")
            for idx, c in enumerate(ciclos):
                with st.expander(f"PROPUESTA #{idx+1}"):
                    for j in range(len(c)):
                        u1, u2 = c[j], c[(j+1)%len(c)]
                        item = G[u1][u2]["set_id"]
                        st.write(f"✅ **{u1}** da **{item}** ({n_map.get(item)}) a **{u2}**")
