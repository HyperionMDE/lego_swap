import streamlit as st
import pandas as pd
import networkx as nx

# --- CONFIGURACIÓN DE PÁGINA ---
# Eliminamos el icono de puzzle genérico y ponemos el nombre de la asociación
st.set_page_config(
    page_title="ALE! - Plataforma de Intercambio",
    page_icon="🤖", # Un icono más neutral, o puedes quitarlo
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enlaces de tus pestañas de Google Sheets (se mantienen)
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

@st.cache_data(ttl=30)
def cargar_datos():
    try:
        # Cargamos todo como texto puro (dtype=str) para evitar errores "LargeUtf8"
        inv = pd.read_csv(URL_INV, dtype=str).fillna("")
        des = pd.read_csv(URL_DES, dtype=str).fillna("")
        
        # Limpiamos espacios en blanco en los nombres de las columnas
        inv.columns = inv.columns.str.strip()
        des.columns = des.columns.str.strip()
        
        return inv, des
    except Exception as e:
        st.error(f"Error de conexión con Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- DISEÑO Y ESTILO OFICIAL (CSS Custom) ---
# Eliminamos el patrón de ladrillos de fondo y usamos un tono gris neutro y limpio.
st.markdown("""
<style>
    /* Fondo general neutro y limpio */
    .stApp {
        background-color: #f8f9fa;
    }

    /* Barra lateral estilo ALE! (Mantenemos el amarillo como color de la asociación) */
    [data-testid="stSidebar"] {
        background-color: #FFD700; /* Amarillo LEGO */
        border-right: 3px solid #FFC107;
    }
    
    /* Botones estilo ALE! (Rojo corporativo) */
    .stButton>button {
        background-color: #D32F2F !important; /* Rojo */
        color: white !important;
        border-radius: 4px !important;
        font-weight: bold !important;
        border: none !important;
        padding: 10px 20px !important;
    }

    /* Estilo para Títulos y Subtítulos */
    h1 { color: #212121; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 700; }
    h2, h3 { color: #37474F; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }

    /* PARCHE ANTIRROSA: Estilo para las tablas HTML estáticas */
    table { width: 100%; border-collapse: collapse; margin: 15px 0; font-family: 'Helvetica Neue', sans-serif; font-size: 0.95rem; background-color: white; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    th { background-color: #455A64; color: white; text-align: left; padding: 12px; font-weight: 600; text-transform: uppercase; }
    td { padding: 10px; border-bottom: 1px solid #e0e0e0; color: #424242; }
    tr:hover td { background-color: #f1f3f4; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (Barra Lateral Oficial ALE!) ---
with st.sidebar:
    # Mostramos los dos logos juntos y bien alineados
    col_logo1, col_logo2 = st.columns([1, 2])
    with col_logo1:
        st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=60)
    with col_logo2:
        # Logo oficial de ALE!
        st.image("https://www.alebricks.com/foro/Themes/OmegaOrange/images/header_foro2017.png", width=140)
    
    # Eliminamos el texto "LEGO Swap" genérico
    st.markdown("---")
    st.markdown("## **Asociación ALE!**")
    st.markdown("Plataforma oficial para la gestión de intercambios masivos entre socios.")
    st.markdown("---")
    st.write("🔧 **Soporte:** Si detectas errores en los datos, por favor actualiza el Google Sheets central de la asociación.")

# --- PANEL PRINCIPAL ---
# TÍTULO SOLICITADO POR EL USUARIO
st.title("PLATAFORMA DE INTERCAMBIO MASIVO DE SETS")
st.write("Consulta el inventario disponible y calcula las cadenas de cambio óptimas.")

inv, des = cargar_datos()

# --- PESTAÑAS (Nombres más directos) ---
tab1, tab2, tab3 = st.tabs(["📦 Inventario de Sets", "❤️ Lista de Deseos", "🚀 Calcular Cambios"])

with tab1:
    st.subheader("Sets que los socios ofrecen")
    if not inv.empty:
        # Convertimos a HTML (Solución blindada al error "LargeUtf8")
        st.write(inv.to_html(index=False, classes='table'), unsafe_allow_html=True)
    else:
        st.info("El inventario está vacío. Por favor, añade sets al Excel.")

with tab2:
    st.subheader("Lo que los socios quieren recibir")
    if not des.empty:
        st.write(des.to_html(index=False, classes='table'), unsafe_allow_html=True)
    else:
        st.info("No hay deseos registrados. Añade tus peticiones al Excel.")

with tab3:
    st.subheader("Cadenas de Intercambio Encontradas")
    if st.button("🔄 Ejecutar Motor de Intercambio ALE!", type="primary"):
        if inv.empty or des.empty:
            st.warning("Faltan datos para realizar el cálculo.")
        else:
            # Crear el grafo dirigido de socios
            G = nx.DiGraph()
            for _, row_pide in des.iterrows():
                pide = str(row_pide['Socio']).strip()
                set_buscado = str(row_pide['SetID']).strip()
                
                # Buscamos quién tiene ese set en el inventario
                duenos = inv[inv['SetID'].astype(str).str.strip() == set_buscado]
                
                for _, row_dueno in duenos.iterrows():
                    da = str(row_dueno['Socio']).strip()
                    if pide != da:
                        G.add_edge(da, pide, set_id=set_buscado)

            # Encontrar ciclos (cadenas cerradas de intercambio)
            ciclos = sorted(list(nx.simple_cycles(G)), key=len, reverse=True)
            
            if not ciclos:
                st.info("No se han encontrado ciclos de intercambio posibles en este momento.")
            else:
                usados = set()
                count = 0
                for ciclo in ciclos:
                    if any(s in usados for s in ciclo):
                        continue
                    
                    count += 1
                    with st.expander(f"✅ Propuesta de Intercambio #{count} ({len(ciclo)} socios)", expanded=True):
                        # Imagen de minifigura sutil para cada propuesta
                        st.image("https://cdn.pixabay.com/photo/2016/11/18/19/20/lego-1836330_1280.png", width=40)
                        for j in range(len(ciclo)):
                            dante = ciclo[j]
                            receptor = ciclo[(j + 1) % len(ciclo)]
                            set_id = G[dante][receptor]['set_id']
                            st.markdown(f"👤 **{dante}** entrega Set **{set_id}** ➡️ a **{receptor}**")
                    
                    for s in ciclo: usados.add(s)
                
                st.success(f"¡Éxito! Intercambio masivo optimizado para {len(usados)} socios.")
