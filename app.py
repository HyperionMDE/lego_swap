import streamlit as st
import pandas as pd
import networkx as nx

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="LEGO Swap Asociación", page_icon="🧩", layout="wide")

# Enlaces de tus pestañas (se mantienen iguales)
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        # PARCHE 1: Forzamos lectura como texto puro (dtype=str) para evitar formatos raros
        inv = pd.read_csv(URL_INV, dtype=str).fillna("")
        des = pd.read_csv(URL_DES, dtype=str).fillna("")
        
        # PARCHE 2: Limpieza profunda de espacios invisibles en las cabeceras
        inv.columns = inv.columns.str.strip()
        des.columns = des.columns.str.strip()
        
        return inv, des
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- INTERFAZ ---
st.title("🧩 LEGO Swap: Sistema de Intercambio")
st.info("Actualización automática conectada a Google Sheets.")

inv, des = cargar_datos()

tab1, tab2, tab3 = st.tabs(["📦 Inventario Disponible", "❤️ Lista de Deseos", "🚀 Calcular Intercambios"])

with tab1:
    st.subheader("Sets que los socios ofrecen")
    if not inv.empty:
        # PARCHE 3: Usamos st.table() en lugar de st.dataframe()
        # Esto soluciona el error rosa de "LargeUtf8" definitivamente.
        st.table(inv)
    else:
        st.warning("No hay datos en la pestaña de Inventario.")

with tab2:
    st.subheader("Sets que los socios buscan")
    if not des.empty:
        st.table(des)
    else:
        st.warning("No hay datos en la pestaña de Deseos.")

with tab3:
    st.subheader("Resultado del Algoritmo de Intercambio")
    if st.button("🔄 Buscar Cadenas de Cambio", type="primary"):
        if inv.empty or des.empty:
            st.error("Faltan datos para realizar el cálculo.")
        else:
            # Construcción del grafo de socios
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

            # Algoritmo de búsqueda de ciclos cerrados
            ciclos = sorted(list(nx.simple_cycles(G)), key=len, reverse=True)
            
            if not ciclos:
                st.info("No hay intercambios circulares posibles en este momento.")
            else:
                usados = set()
                count = 0
                for ciclo in ciclos:
                    if any(s in usados for s in ciclo):
                        continue
                    
                    count += 1
                    with st.expander(f"📦 Propuesta #{count} ({len(ciclo)} socios involucrados)", expanded=True):
                        for i in range(len(ciclo)):
                            dante = ciclo[i]
                            receptor = ciclo[(i + 1) % len(ciclo)]
                            set_id = G[dante][receptor]['set_id']
                            st.markdown(f"👤 **{dante}** entrega Set **{set_id}** ➡️ a **{receptor}**")
                    
                    for s in ciclo: usados.add(s)
                
                st.success(f"¡Se han optimizado intercambios para {len(usados)} socios!")
