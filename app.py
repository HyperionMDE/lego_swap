import streamlit as st
import pandas as pd
import networkx as nx

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="LEGO Swap Asociación", page_icon="🧩", layout="wide")

# Tus enlaces de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        # Cargamos todo como texto puro (dtype=str) para evitar errores de formato
        inv = pd.read_csv(URL_INV, dtype=str).fillna("")
        des = pd.read_csv(URL_DES, dtype=str).fillna("")
        
        # Limpiamos espacios en blanco en los nombres de las columnas
        inv.columns = inv.columns.str.strip()
        des.columns = des.columns.str.strip()
        
        return inv, des
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- TÍTULO ---
st.title("🧩 LEGO Swap: Sistema de Intercambio")
st.markdown("Plataforma oficial para la gestión de intercambios de la asociación.")

inv, des = cargar_datos()

# --- PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["📦 Inventario Disponible", "❤️ Lista de Deseos", "🚀 Calcular Intercambios"])

with tab1:
    st.subheader("Sets que los socios ofrecen")
    if not inv.empty:
        # st.table es la solución al error rosa "LargeUtf8"
        st.table(inv)
    else:
        st.info("No hay datos en el Inventario.")

with tab2:
    st.subheader("Sets que los socios buscan")
    if not des.empty:
        st.table(des)
    else:
        st.info("No hay deseos registrados.")

with tab3:
    st.subheader("Algoritmo de Maximización de Intercambios")
    if st.button("🔥 ¡Calcular Intercambios Óptimos!", type="primary"):
        if inv.empty or des.empty:
            st.warning("Necesitamos datos en ambas pestañas para calcular.")
        else:
            # Crear el grafo de intercambios
            G = nx.DiGraph()
            for _, row_pide in des.iterrows():
                pide = str(row_pide['Socio']).strip()
                set_buscado = str(row_pide['SetID']).strip()
                
                # Buscamos quién tiene ese SetID en el inventario
                duenos = inv[inv['SetID'].astype(str).str.strip() == set_buscado]
                
                for _, row_dueno in duenos.iterrows():
                    da = str(row_dueno['Socio']).strip()
                    # Evitamos que alguien se intercambie consigo mismo
                    if pide != da:
                        G.add_edge(da, pide, set_id=set_buscado)

            # Buscamos ciclos (cadenas cerradas de intercambio)
            ciclos = sorted(list(nx.simple_cycles(G)), key=len, reverse=True)
            
            if not ciclos:
                st.info("No se han encontrado ciclos posibles. Prueba a añadir más deseos.")
            else:
                usados = set()
                count = 0
                for ciclo in ciclos:
                    # Si un socio ya está en un intercambio, no puede estar en otro
                    if any(s in usados for s in ciclo):
                        continue
                    
                    count += 1
                    with st.expander(f"✅ Propuesta de Intercambio #{count} ({len(ciclo)} socios)", expanded=True):
                        for i in range(len(ciclo)):
                            dante = ciclo[i]
                            receptor = ciclo[(i + 1) % len(ciclo)]
                            set_id = G[dante][receptor]['set_id']
                            st.write(f"👤 **{dante}** entrega el Set **{set_id}** ➡️ a **{receptor}**")
                    
                    for s in ciclo: usados.add(s)
                
                st.success(f"¡Éxito! Hemos encontrado soluciones para {len(usados)} socios.")
