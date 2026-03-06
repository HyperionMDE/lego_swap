import streamlit as st
import pandas as pd
import networkx as nx

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="LEGO Swap - ALE!",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enlaces de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

@st.cache_data(ttl=30)
def cargar_datos():
    try:
        inv = pd.read_csv(URL_INV, dtype=str).fillna("")
        des = pd.read_csv(URL_DES, dtype=str).fillna("")
        inv.columns = inv.columns.str.strip()
        des.columns = des.columns.str.strip()
        return inv, des
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- ESTILO LEGO & ALE! ---
st.markdown("""
<style>
    .stApp {
        background-image: url("https://www.transparenttextures.com/patterns/brick-wall.png");
        background-color: #f4f4f4;
        background-blend-mode: overlay;
    }
    [data-testid="stSidebar"] {
        background-color: #FFD700;
        border-right: 5px solid #FFC107;
    }
    .stButton>button {
        background-color: #D32F2F !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        border: 2px solid #B71C1C !important;
    }
    .banner-ale {
        background-color: #D32F2F;
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        font-weight: 800;
        font-size: 1.5rem;
        margin-bottom: 30px;
        border: 4px solid #FFD700;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
    th { background-color: #0277BD !important; color: white !important; padding: 12px; }
    td { padding: 10px; border-bottom: 1px solid #eee; color: #333; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (Barra Lateral Corregida) ---
with st.sidebar:
    # Mostramos los dos logos juntos
    col_logo1, col_logo2 = st.columns(2)
    with col_logo1:
        st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=80)
    with col_logo2:
        st.image("https://www.alebricks.com/foro/Themes/OmegaOrange/images/header_foro2017.png", width=120)
    
    st.title("🧩 LEGO Swap")
    st.markdown("### **Asociación ALE!**")
    st.info("Plataforma oficial de intercambio masivo para socios.")
    st.markdown("---")
    st.write("🔧 **Soporte:** Si ves datos incorrectos, actualiza el Google Sheets de la asociación.")

# --- PANEL PRINCIPAL ---
st.title("🧩 LEGO Swap: Motor de Intercambios")
st.markdown('<div class="banner-ale">🧱 APLICACIÓN DE INTERCAMBIO MASIVO - ASOCIACIÓN ALE! 🧱</div>', unsafe_allow_html=True)

inv, des = cargar_datos()

tab1, tab2, tab3 = st.tabs(["📦 Inventario ALE!", "❤️ Mis Deseos", "🚀 Calcular Cambios"])

with tab1:
    st.subheader("Sets disponibles para cambio")
    if not inv.empty:
        st.write(inv.to_html(index=False, border=0), unsafe_allow_html=True)
    else:
        st.info("No hay sets registrados en el inventario.")

with tab2:
    st.subheader("Lo que los socios están buscando")
    if not des.empty:
        st.write(des.to_html(index=False, border=0), unsafe_allow_html=True)
    else:
        st.info("Aún no hay deseos registrados.")

with tab3:
    st.subheader("Algoritmo de Intercambio ALE!")
    if st.button("🔥 ¡Lanzar Intercambio Masivo!", type="primary"):
        if inv.empty or des.empty:
            st.warning("Faltan datos para procesar.")
        else:
            G = nx.DiGraph()
            for _, row_pide in des.iterrows():
                pide = str(row_pide['Socio']).strip()
                set_id = str(row_pide['SetID']).strip()
                duenos = inv[inv['SetID'].astype(str).str.strip() == set_id]
                for _, row_dueno in duenos.iterrows():
                    da = str(row_dueno['Socio']).strip()
                    if pide != da:
                        G.add_edge(da, pide, set_id=set_id)

            ciclos = sorted(list(nx.simple_cycles(G)), key=len, reverse=True)
            
            if not ciclos:
                st.info("No se han encontrado ciclos posibles hoy.")
            else:
                usados = set()
                for i, ciclo in enumerate(ciclos, 1):
                    if any(s in usados for s in ciclo): continue
                    with st.expander(f"✅ Propuesta ALE! #{i} ({len(ciclo)} socios)", expanded=True):
                        for j in range(len(ciclo)):
                            dante, recp = ciclo[j], ciclo[(j+1)%len(ciclo)]
                            st.write(f"👤 **{dante}** entrega el Set **{G[dante][recp]['set_id']}** ➡️ a **{recp}**")
                    for s in ciclo: usados.add(s)
                st.success(f"¡Se han encontrado soluciones para {len(usados)} socios!")
