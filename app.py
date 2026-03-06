import streamlit as st
import pandas as pd
import networkx as nx
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ALE! - Intercambio Masivo", page_icon="🏗️", layout="wide")

# URLs de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# --- BASE DE DATOS INTERNA DE EMERGENCIA ---
# Si la API falla, estos nombres saldrán siempre bien
DICCIONARIO_SETS = {
    "10316": "Rivendell",
    "75192": "Millennium Falcon (UCS)",
    "21333": "The Starry Night (Vincent van Gogh)",
    "10305": "Lion Knights' Castle",
    "75331": "The Razor Crest (UCS)",
    "10333": "The Lord of the Rings: Barad-dûr",
    "75367": "Venator-Class Republic Attack Cruiser",
    "10307": "Eiffel Tower"
}

@st.cache_data(ttl=86400)
def obtener_nombre_set(set_id):
    sid = str(set_id).strip()
    if not sid or sid == "nan": return "ID no válido"
    
    # 1. Intentar primero con el diccionario interno (Instantáneo)
    if sid in DICCIONARIO_SETS:
        return DICCIONARIO_SETS[sid]
    
    # 2. Intentar consulta externa reforzada
    search_id = f"{sid}-1" if "-" not in sid else sid
    try:
        api_url = f"https://rebrickable.com/api/v3/lego/sets/{search_id}/"
        headers = {
            'Authorization': 'key 9d7b97368d90473950669f64e2621453',
            'User-Agent': 'Mozilla/5.0'
        }
        r = requests.get(api_url, headers=headers, timeout=3)
        if r.status_code == 200:
            return r.json().get('name', f"Set LEGO {sid}")
    except:
        pass
    
    return f"Set LEGO {sid}"

@st.cache_data(ttl=10)
def cargar_datos():
    try:
        inv = pd.read_csv(URL_INV, dtype=str).fillna("")
        des = pd.read_csv(URL_DES, dtype=str).fillna("")
        inv.columns = inv.columns.str.strip()
        des.columns = des.columns.str.strip()
        
        inv['Nombre'] = inv['SetID'].apply(obtener_nombre_set)
        des['Nombre'] = des['SetID'].apply(obtener_nombre_set)
        return inv, des
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- DISEÑO ---
st.markdown("""
<style>
    .stApp { background-color: white; }
    [data-testid="stSidebar"] { background-color: #FFD700; border-right: 2px solid #ddd; }
    th { background-color: #2c3e50 !important; color: white !important; font-weight: bold; }
    .main-title { color: #222; font-size: 2rem; font-weight: 800; border-bottom: 4px solid #D32F2F; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL ---
with st.sidebar:
    # Logo de LEGO y Asociación ALE!
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=80)
    st.image("https://www.alebricks.com/foro/Themes/OmegaOrange/images/header_foro2017.png", width=160)
    st.markdown("---")
    if st.button("🔄 Forzar Recarga de Datos", type="secondary"):
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
    if st.button("🚀 Ejecutar Algoritmo de Cambio", type="primary"):
        G = nx.DiGraph()
        # Mapa de nombres para el resultado final
        nombres_map = pd.concat([inv, des]).set_index('SetID')['Nombre'].to_dict()
        
        for _, r in des.iterrows():
            pide, sid = str(r['Socio']).strip(), str(r['SetID']).strip()
            duenos = inv[inv['SetID'].astype(str).str.strip() == sid]
            for _, d_row in duenos.iterrows():
                da = str(d_row['Socio']).strip()
                if pide != da: G.add_edge(da, pide, set_id=sid)
        
        ciclos = list(nx.simple_cycles(G))
        if not ciclos:
            st.info("No hay ciclos de intercambio posibles con los datos actuales.")
        else:
            usados = set()
            for i, c in enumerate(ciclos):
                if any(n in usados for n in c): continue
                with st.expander(f"PROPUESTA #{i+1} ({len(c)} socios)"):
                    for j in range(len(c)):
                        d, r = c[j], c[(j+1)%len(c)]
                        sid = G[d][r]['set_id']
                        st.markdown(f"✅ **{d}** entrega **{sid}** ({nombres_map.get(sid)}) ➡️ a **{r}**")
                for n in c: usados.add(n)
