import streamlit as st
import pandas as pd
import networkx as nx
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ALE! - Intercambio Masivo", page_icon="🏗️", layout="wide")

# URLs de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# --- FUNCIÓN DE BÚSQUEDA REBRICKABLE (CON -1 AUTOMÁTICO) ---
@st.cache_data(ttl=86400)
def obtener_nombre_set(set_id):
    if not set_id or str(set_id).strip() == "" or str(set_id).lower() == "nan":
        return "ID No válido"
    
    sid = str(set_id).strip()
    # Si el usuario no puso guion, Rebrickable necesita el -1
    search_id = f"{sid}-1" if "-" not in sid else sid

    try:
        api_url = f"https://rebrickable.com/api/v3/lego/sets/{search_id}/"
        headers = {'Authorization': 'key 9d7b97368d90473950669f64e2621453'}
        response = requests.get(api_url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json().get('name', f"Set {sid}")
        return f"Set LEGO {sid}"
    except:
        return f"Set LEGO {sid}"

@st.cache_data(ttl=20)
def cargar_datos():
    try:
        inv = pd.read_csv(URL_INV, dtype=str).fillna("")
        des = pd.read_csv(URL_DES, dtype=str).fillna("")
        inv.columns = inv.columns.str.strip()
        des.columns = des.columns.str.strip()
        # Aplicamos la búsqueda de nombres
        if 'SetID' in inv.columns:
            inv['Nombre'] = inv['SetID'].apply(obtener_nombre_set)
        if 'SetID' in des.columns:
            des['Nombre'] = des['SetID'].apply(obtener_nombre_set)
        return inv, des
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- ESTILO VISUAL ---
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #FFD700; border-right: 2px solid #ddd; }
    th { background-color: #333333 !important; color: white !important; }
    .main-title { color: #222; font-size: 2.2rem; font-weight: 800; border-bottom: 4px solid #D32F2F; display: inline-block; margin-bottom: 20px;}
</style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL (Logos corregidos) ---
with st.sidebar:
    col1, col2 = st.columns([1, 2])
    with col1:
        # Logo de LEGO con URL verificada y cerrada
        st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=60)
    with col2:
        # Logo ALE!
        st.image("https://www.alebricks.com/foro/Themes/OmegaOrange/images/header_foro2017.png", width=140)
    st.markdown("---")
    if st.button("🔄 Forzar Recarga de Nombres"):
        st.cache_data.clear()
        st.rerun()

# --- CUERPO ---
st.markdown('<p class="main-title">PLATAFORMA DE INTERCAMBIO MASIVO DE SETS</p>', unsafe_allow_html=True)

inv, des = cargar_datos()

t1, t2, t3 = st.tabs(["📦 Inventario ALE!", "❤️ Deseos Socios", "🔄 Calcular"])

with t1:
    if not inv.empty:
        st.write(inv[['Socio', 'SetID', 'Nombre']].to_html(index=False), unsafe_allow_html=True)

with t2:
    if not des.empty:
        st.write(des[['Socio', 'SetID', 'Nombre']].to_html(index=False), unsafe_allow_html=True)

with t3:
    if st.button("🚀 Calcular Intercambios", type="primary"):
        G = nx.DiGraph()
        nombres_map = pd.concat([inv, des]).set_index('SetID')['Nombre'].to_dict()
        for _, r in des.iterrows():
            p, s = str(r['Socio']).strip(), str(r['SetID']).strip()
            duenos = inv[inv['SetID'] == s]
            for _, d_row in duenos.iterrows():
                d = str(d_row['Socio']).strip()
                if p != d: G.add_edge(d, p, set_id=s)
        
        ciclos = list(nx.simple_cycles(G))
        if not ciclos:
            st.info("No hay ciclos de intercambio disponibles.")
        else:
            usados = set()
            for i, c in enumerate(ciclos):
                if any(node in usados for node in c): continue
                with st.expander(f"PROPUESTA #{i+1} ({len(c)} socios)"):
                    for j in range(len(c)):
                        d, r = c[j], c[(j+1)%len(c)]
                        sid = G[d][r]['set_id']
                        st.write(f"✅ **{d}** da **{sid}** ({nombres_map.get(sid)}) ➡️ a **{r}**")
                for node in c: usados.add(node)
