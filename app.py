import streamlit as st
import pandas as pd
import networkx as nx
import urllib.request
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ALE! - Intercambio", page_icon="🏗️", layout="wide")

# URLs de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# --- FUNCIÓN PARA OBTENER NOMBRE DEL SET AUTOMÁTICAMENTE ---
@st.cache_data(ttl=3600)
def obtener_nombre_set(set_id):
    """Busca el nombre del set usando la API abierta de Brickset/Rebrickable o similar"""
    try:
        # Limpiamos el ID por si acaso
        set_id_clean = str(set_id).strip().split('-')[0]
        url = f"https://rebrickable.com/api/v3/lego/sets/{set_id_clean}-1/?key=9d7b97368d90473950669f64e2621453"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data.get('name', "Nombre no encontrado")
    except:
        return "Set LEGO #" + str(set_id)

@st.cache_data(ttl=10)
def cargar_y_procesar():
    try:
        inv = pd.read_csv(URL_INV, dtype=str).fillna("")
        des = pd.read_csv(URL_DES, dtype=str).fillna("")
        
        # Limpieza de columnas
        inv.columns = inv.columns.str.strip()
        des.columns = des.columns.str.strip()

        # ASIGNACIÓN AUTOMÁTICA DE NOMBRES
        # Creamos la columna 'Nombre' basándonos solo en el SetID
        if 'SetID' in inv.columns:
            inv['Nombre'] = inv['SetID'].apply(obtener_nombre_set)
        if 'SetID' in des.columns:
            des['Nombre'] = des['SetID'].apply(obtener_nombre_set)
            
        return inv, des
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- DISEÑO ---
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #FFD700; border-right: 2px solid #ddd; }
    th { background-color: #2c3e50 !important; color: white !important; }
    .main-title { color: #222; font-size: 2.2rem; font-weight: 800; border-bottom: 4px solid #D32F2F; display: inline-block; margin-bottom: 20px;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://www.alebricks.com/foro/Themes/OmegaOrange/images/header_foro2017.png", width=180)
    st.markdown("---")
    st.info("Sistema Automático: El nombre del set se genera solo a partir del SetID.")

# --- CUERPO ---
st.markdown('<p class="main-title">PLATAFORMA DE INTERCAMBIO MASIVO DE SETS</p>', unsafe_allow_html=True)

inv, des = cargar_y_procesar()

tab1, tab2, tab3 = st.tabs(["📦 Inventario ALE!", "❤️ Deseos Socios", "🔄 Generar Cambios"])

with tab1:
    if not inv.empty:
        # Solo mostramos Socio, ID y el Nombre generado automáticamente
        st.write(inv[['Socio', 'SetID', 'Nombre']].to_html(index=False), unsafe_allow_html=True)

with tab2:
    if not des.empty:
        st.write(des[['Socio', 'SetID', 'Nombre']].to_html(index=False), unsafe_allow_html=True)

with tab3:
    if st.button("🚀 Calcular Cadenas de Intercambio", type="primary"):
        G = nx.DiGraph()
        # Diccionario para nombres en el resultado final
        nombres_dict = pd.concat([inv, des]).set_index('SetID')['Nombre'].to_dict()

        for _, row_pide in des.iterrows():
            pide, sid = str(row_pide['Socio']), str(row_pide['SetID'])
            duenos = inv[inv['SetID'] == sid]
            for _, row_dueno in duenos.iterrows():
                da = str(row_dueno['Socio'])
                if pide != da: G.add_edge(da, pide, set_id=sid)

        ciclos = list(nx.simple_cycles(G))
        if not ciclos:
            st.info("No hay ciclos disponibles.")
        else:
            usados = set()
            for i, ciclo in enumerate(ciclos):
                if any(s in usados for s in ciclo): continue
                with st.expander(f"PROPUESTA #{i+1}", expanded=True):
                    for j in range(len(ciclo)):
                        d, r = ciclo[j], ciclo[(j+1)%len(ciclo)]
                        sid = G[d][r]['set_id']
                        st.write(f"✅ **{d}** entrega **{sid}** ({nombres_dict.get(sid)}) ➡️ **{r}**")
                for s in ciclo: usados.add(s)
