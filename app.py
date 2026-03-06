import streamlit as st
import pandas as pd
import networkx as nx
import urllib.request
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="ALE! - Intercambio Masivo",
    page_icon="🏗️",
    layout="wide"
)

# URLs de Google Sheets (Tus fuentes de datos)
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# --- FUNCIÓN PARA OBTENER NOMBRE DEL SET AUTOMÁTICAMENTE ---
@st.cache_data(ttl=3600)
def obtener_nombre_set(set_id):
    """Busca el nombre del set usando una API pública de LEGO (Rebrickable)"""
    try:
        # Limpiamos el ID por si acaso
        set_id_clean = str(set_id).strip().split('-')[0]
        # Usamos una clave de API pública para la demostración
        url = f"https://rebrickable.com/api/v3/lego/sets/{set_id_clean}-1/?key=9d7b97368d90473950669f64e2621453"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data.get('name', f"Set LEGO #{set_id}")
    except Exception:
        # Si la API falla, devolvemos un nombre genérico
        return f"Set LEGO #{set_id}"

@st.cache_data(ttl=10)
def cargar_y_procesar():
    try:
        # Cargamos datos asegurando que se lean como texto
        inv = pd.read_csv(URL_INV, dtype=str).fillna("")
        des = pd.read_csv(URL_DES, dtype=str).fillna("")
        
        # Limpieza de nombres de columnas
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
        st.error(f"Error al conectar con la base de datos de ALE!: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- ESTILO VISUAL CORPORATIVO ---
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #FFD700; border-right: 2px solid #ddd; }
    
    /* Estilo de tablas profesionales */
    table { width: 100%; border-radius: 8px; overflow: hidden; border: 1px solid #ddd; font-family: sans-serif; }
    th { background-color: #333333 !important; color: white !important; padding: 12px; text-align: left; }
    td { padding: 10px; border-bottom: 1px solid #eee; }
    tr:hover { background-color: #f9f9f9; }

    /* Título principal */
    .main-title { color: #222; font-size: 2.2rem; font-weight: 800; border-bottom: 4px solid #D32F2F; display: inline-block; margin-bottom: 20px;}
</style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL (Logos ALE! + LEGO de vuelta) ---
with st.sidebar:
    # Mostramos los dos logos juntos y bien alineados
    col_logo1, col_logo2 = st.columns([1, 2])
    with col_logo1:
        # LOGO DE LEGO DE VUELTA
        st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=60)
    with col_logo2:
        st.image("https://www.alebricks.com/foro/Themes/OmegaOrange/images/header_foro2017.png", width=140)
    
    st.markdown("---")
    st.subheader("Panel de Control")
    st.info("Sistema Automático: El nombre del set se genera solo a partir del SetID.")

# --- CUERPO PRINCIPAL ---
st.markdown('<p class="main-title">PLATAFORMA DE INTERCAMBIO MASIVO DE SETS</p>', unsafe_allow_html=True)

inv, des = cargar_y_procesar()

# Definimos las pestañas
tab1, tab2, tab3 = st.tabs(["📦 Inventario ALE!", "❤️ Deseos Socios", "🔄 Generar Cambios"])

with tab1:
    st.subheader("Sets Disponibles para Intercambio")
    if not inv.empty:
        # Solo mostramos Socio, ID y el Nombre generado automáticamente
        cols_mostrar = ['Socio', 'SetID', 'Nombre']
        st.write(inv[cols_mostrar].to_html(index=False), unsafe_allow_html=True)
    else:
        st.warning("No hay datos en el Inventario.")

with tab2:
    st.subheader("Sets que los Socios Desean")
    if not des.empty:
        cols_mostrar_des = ['Socio', 'SetID', 'Nombre']
        st.write(des[cols_mostrar_des].to_html(index=False), unsafe_allow_html=True)
    else:
        st.warning("No hay datos en la Lista de Deseos.")

with tab3:
    st.subheader("Generador de Cadenas ALE!")
    st.write("El sistema buscará combinaciones donde varios socios puedan intercambiar en círculo.")
    
    if st.button("🚀 Ejecutar Algoritmo de Intercambio", type="primary"):
        if inv.empty or des.empty:
            st.error("Datos insuficientes.")
        else:
            # Construcción del grafo de intercambios
            G = nx.DiGraph()
            
            # Mapeo de nombres para que aparezcan en los resultados
            nombres_dict = pd.concat([inv, des]).set_index('SetID')['Nombre'].to_dict()

            for _, row_pide in des.iterrows():
                pide = str(row_pide['Socio']).strip()
                sid = str(row_pide['SetID']).strip()
                
                # Quién tiene lo que este socio quiere
                duenos = inv[inv['SetID'].astype(str).str.strip() == sid]
                
                for _, row_dueno in duenos.iterrows():
                    da = str(row_dueno['Socio']).strip()
                    if pide != da:
                        G.add_edge(da, pide, set_id=sid)

            # Encontrar ciclos
            ciclos = list(nx.simple_cycles(G))
            
            if not ciclos:
                st.info("No se han encontrado cadenas cerradas de intercambio. Prueba a añadir más deseos.")
            else:
                usados = set()
                for i, ciclo in enumerate(ciclos):
                    if any(s in usados for s in ciclo): continue
                    
                    with st.expander(f"PROPUESTA #{i+1} - Intercambio de {len(ciclo)} bandas", expanded=True):
                        for j in range(len(ciclo)):
                            dador = ciclo[j]
                            receptor = ciclo[(j + 1) % len(ciclo)]
                            sid = G[dador][receptor]['set_id']
                            st.write(f"✅ **{dador}** entrega **{sid}** ({nombres_dict.get(sid)}) ➡️ **{receptor}**")
                    
                    for s in ciclo: usados.add(s)
                st.success(f"Se han optimizado intercambios para {len(usados)} socios.")
