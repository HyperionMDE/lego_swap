import streamlit as st
import pandas as pd
import networkx as nx
import urllib.request
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ALE! - Intercambio Masivo", page_icon="🏗️", layout="wide")

# URLs de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# --- FUNCIÓN DE BÚSQUEDA REFORZADA ---
@st.cache_data(ttl=3600)
def obtener_nombre_set(set_id):
    if not set_id or str(set_id).strip() == "": return "ID vacío"
    try:
        sid = str(set_id).strip().split('-')[0]
        url = f"https://rebrickable.com/api/v3/lego/sets/{sid}-1/?key=9d7b97368d90473950669f64e2621453"
        
        # Añadimos cabeceras de "User-Agent" para evitar bloqueos
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get('name', f"Set #{sid}")
    except Exception as e:
        # Si falla la API, intentamos una búsqueda alternativa simple en Bricklink (simulada)
        return f"Cargando nombre para {set_id}..."

@st.cache_data(ttl=10)
def cargar_y_procesar():
    try:
        inv = pd.read_csv(URL_INV, dtype=str).fillna("")
        des = pd.read_csv(URL_DES, dtype=str).fillna("")
        inv.columns = inv.columns.str.strip()
        des.columns = des.columns.str.strip()

        # Inyectar nombres
        if 'SetID' in inv.columns:
            inv['Nombre'] = inv['SetID'].apply(obtener_nombre_set)
        if 'SetID' in des.columns:
            des['Nombre'] = des['SetID'].apply(obtener_nombre_set)
            
        return inv, des
    except Exception as e:
        st.error(f"Error de datos: {e}")
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
    col_l1, col_l2 = st.columns([1, 2])
    with col_l1:
        st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=60)
    with col_l2:
        st.image("https://www.alebricks.com/foro/Themes/OmegaOrange/images/header_foro2017.png", width=140)
    st.markdown("---")
    st.write("**Asociación ALE!**")
    st.info("💡 Los nombres se descargan automáticamente desde Rebrickable.")

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
    if st.button("🚀 Calcular Intercambios", type="primary"):
        # Lógica de ciclos igual a la anterior pero con nombres actualizados
        G = nx.DiGraph()
        nombres_map = pd.concat([inv, des]).set_index('SetID')['Nombre'].to_dict()
        for _, r in des.iterrows():
            p, s = str(r['Socio']).strip(), str(r['SetID']).strip()
            duenos = inv[inv['SetID'].astype(str).str.strip() == s]
            for _, d_row in duenos.iterrows():
                d = str(d_row['Socio']).strip()
                if p != d: G.add_edge(d, p, set_id=s)
        
        ciclos = list(nx.simple_cycles(G))
        if not ciclos: st.info("No hay ciclos.")
        else:
            usados = set()
            for i, c in enumerate(ciclos):
                if any(s in usados for s in c): continue
                with st.expander(f"PROPUESTA #{i+1}"):
                    for j in range(len(c)):
                        d, r = c[j], c[(j+1)%len(c)]
                        sid = G[d][r]['set_id']
                        st.write(f"✅ **{d}** entrega **{sid}** ({nombres_map.get(sid)}) ➡️ **{r}**")
                for s in c: usados.add(s)
