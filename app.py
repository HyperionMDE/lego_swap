import streamlit as st
import pandas as pd
import networkx as nx
import requests  # Cambiamos a la librería requests que es más estable

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ALE! - Intercambio Masivo", page_icon="🏗️", layout="wide")

# URLs de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# --- FUNCIÓN DE BÚSQUEDA PROFESIONAL ---
@st.cache_data(ttl=86400) # Cache de 24 horas para no saturar
def obtener_nombre_set(set_id):
    if not set_id or str(set_id).strip() == "" or str(set_id) == "nan": 
        return "ID No válido"
    
    sid = str(set_id).strip().split('-')[0]
    # Intentamos la API de Rebrickable con un tiempo de espera (timeout)
    try:
        api_url = f"https://rebrickable.com/api/v3/lego/sets/{sid}-1/"
        headers = {
            'Authorization': 'key 9d7b97368d90473950669f64e2621453',
            'User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(api_url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json().get('name', f"Set #{sid}")
        else:
            return f"Set LEGO {sid}"
    except:
        return f"Set LEGO {sid}"

@st.cache_data(ttl=20)
def cargar_y_procesar():
    try:
        inv = pd.read_csv(URL_INV, dtype=str).fillna("")
        des = pd.read_csv(URL_DES, dtype=str).fillna("")
        inv.columns = inv.columns.str.strip()
        des.columns = des.columns.str.strip()

        # Generar nombres automáticamente
        if 'SetID' in inv.columns:
            inv['Nombre'] = inv['SetID'].apply(obtener_nombre_set)
        if 'SetID' in des.columns:
            des['Nombre'] = des['SetID'].apply(obtener_nombre_set)
            
        return inv, des
    except Exception as e:
        st.error(f"Error al leer Excel: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- ESTILO ---
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #FFD700; border-right: 2px solid #ddd; }
    th { background-color: #333333 !important; color: white !important; }
    .main-title { color: #222; font-size: 2.2rem; font-weight: 800; border-bottom: 4px solid #D32F2F; display: inline-block; margin-bottom: 20px;}
</style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL ---
with st.sidebar:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=60)
    with col2:
        st.image("https://www.alebricks.com/foro/Themes/OmegaOrange/images/header_foro2017.png", width=140)
    st.markdown("---")
    if st.button("🔄 Forzar Actualización Datos"):
        st.cache_data.clear()
        st.rerun()

# --- CUERPO ---
st.markdown('<p class="main-title">PLATAFORMA DE INTERCAMBIO MASIVO DE SETS</p>', unsafe_allow_html=True)

inv, des = cargar_y_procesar()

t1, t2, t3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🔄 Calcular"])

with t1:
    if not inv.empty:
        st.write(inv[['Socio', 'SetID', 'Nombre']].to_html(index=False), unsafe_allow_html=True)

with t2:
    if not des.empty:
        st.write(des[['Socio', 'SetID', 'Nombre']].to_html(index=False), unsafe_allow_html=True)

with t3:
    if st.button("🚀 Ejecutar Algoritmo", type="primary"):
        G = nx.DiGraph()
        nombres_map = pd.concat([inv, des]).set_index('SetID')['Nombre'].to_dict()
        for _, r in des.iterrows():
            p, s = str(r['Socio']).strip(), str(r['SetID']).strip()
            duenos = inv[inv['SetID'].astype(str).str.strip() == s]
            for _, d_row in duenos.iterrows():
                d = str(d_row['Socio']).strip()
                if p != d: G.add_edge(d, p, set_id=s)
        
        ciclos = list(nx.simple_cycles(G))
        if not ciclos: st.info("No hay ciclos encontrados.")
        else:
            usados = set()
            for i, c in enumerate(ciclos):
                if any(node in usados for node in c): continue
                with st.expander(f"PROPUESTA #{i+1} ({len(c)} socios)"):
                    for j in range(len(c)):
                        d, r = c[j], c[(j+1)%len(c)]
                        sid = G[d][r]['set_id']
                        st.write(f"✅ **{d}** da el set **{sid}** ({nombres_map.get(sid)}) ➡️ a **{r}**")
                for node in c: usados.add(node)
