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

# Enlaces de tus pestañas de Google Sheets
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

# --- DISEÑO Y ESTILO LEGO & ALE! ---
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
    }
    th { background-color: #0277BD !important; color: white !important; }
    /* Estilo para el mensaje de la asociación */
    .banner-ale {
        background-color: #D32F2F;
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 25px;
        border: 3px solid #FFD700;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=100)
    st.title("🧩 LEGO Swap")
    st.markdown("**Asociación ALE!**")
    st.write("Herramienta oficial para socios.")

# --- PANEL PRINCIPAL ---
st.title("🧩 LEGO Swap: Motor de Intercambios")

# MENCION ESPECIAL ALE!
st.markdown('<div class="banner-ale">🚀 ¡Esta es la aplicación oficial de intercambio masivo de la Asociación ALE! 🚀</div>', unsafe_allow_html=True)

inv, des = cargar_datos()

tab1, tab2, tab3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Calcular"])

with tab1:
    st.header("Sets Disponibles")
    if not inv.empty:
