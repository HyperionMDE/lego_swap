import streamlit as st
import pandas as pd
import networkx as nx

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="LEGO Swap Asociación", page_icon="🧩", layout="wide")

# Enlaces de tus pestañas de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

@st.cache_data(ttl=30)
def cargar_datos():
    try:
        # Cargamos todo como texto para que no haya errores de formato
        inv = pd.read_csv(URL_INV, dtype=str).fillna("")
        des = pd.read_csv(URL_DES, dtype=str).fillna("")
        inv.columns = [str(c).strip() for c in inv.columns]
        des.columns = [str(c).strip() for c in des.columns]
        return inv, des
    except Exception as e:
        st.error(f"Error de conexión con Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- ESTILO CSS PARA LAS TABLAS ---
st.markdown("""
<style>
    .reportview-container .main .block-container { padding-top: 2rem; }
    table { width: 100%; border-collapse: collapse; margin: 10px 0; font-family: sans-serif; }
    th { background-color: #2e7d32; color: white; text-align: left; padding: 12px; }
    td { padding: 10px; border-bottom: 1px solid #ddd; }
    tr:hover { background-color: #f5f5f5; }
</style>
""", unsafe_allow_html=True)

st.title("🧩 LEGO Swap: Motor de Intercambios")
st.write("Consulta los sets y calcula las mejores cadenas de cambio.")

inv, des = cargar_datos()

tab1, tab2, tab3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Calcular Cambios"])

with tab1:
    st.subheader("Sets que los socios ofrecen")
    if not inv.empty:
        # Convertimos a HTML para evitar el error "LargeUtf8"
        st.write(inv.to_html(index=False, classes='table'), unsafe_allow_html=True)
    else:
        st.info("No hay datos en el Inventario.")

with tab2:
    st.subheader("Lo que los socios quieren")
    if not des.empty:
        st.write(des.to_html(index=False, classes='table'), unsafe_allow_html=True)
    else:
        st.info("No hay deseos registrados.")

with tab3:
    st.subheader("Cadenas de Intercambio Encontradas")
    if st.button("🔍 Ejecutar Algoritmo", type="primary"):
        G = nx.DiGraph()
        for _, row_pide in des.iterrows():
            pide, set_id = str(row_pide['Socio']).strip(), str(row_pide['SetID']).strip()
            duenos = inv[inv['SetID'].astype(str).str.strip() == set_id]
            for _, row_dueno in duenos.iterrows():
                da = str(row_dueno['Socio']).strip()
                if pide != da:
                    G.add_edge(da, pide, set_id=set_id)

        ciclos = sorted(list(nx.simple_cycles(G)), key=len, reverse=True)
        
        if not ciclos:
            st.warning("No hay intercambios posibles con los datos actuales.")
        else:
            usados = set()
            for i, ciclo in enumerate(ciclos, 1):
                if any(s in usados for s in ciclo): continue
                with st.expander(f"📦 Propuesta #{i} - {len(ciclo)} socios", expanded=True):
                    for j in range(len(ciclo)):
                        dante, recp = ciclo[j], ciclo[(j+1)%len(ciclo)]
                        st.write(f"👤 **{dante}** entrega Set **{G[dante][recp]['set_id']}** ➡️ a **{recp}**")
                for s in ciclo: usados.add(s)
            st.success(f"¡Intercambio optimizado para {len(usados)} socios!")
