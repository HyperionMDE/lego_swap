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
        # Forzamos a que todo se lea como texto simple para evitar el error LargeUtf8
        inv = pd.read_csv(URL_INV, dtype=str).fillna("")
        des = pd.read_csv(URL_DES, dtype=str).fillna("")
        
        # Limpieza de nombres de columnas
        inv.columns = inv.columns.str.strip()
        des.columns = des.columns.str.strip()
        
        return inv, des
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

st.title("🧩 LEGO Swap: Sistema de Intercambio")

inv, des = cargar_datos()

tab1, tab2, tab3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Calcular Cambios"])

with tab1:
    st.header("Sets Disponibles para Cambio")
    if not inv.empty:
        # Usamos st.table() en lugar de st.dataframe() para evitar el error rosa
        st.table(inv)
    else:
        st.info("El inventario está vacío.")

with tab2:
    st.header("Lista de Deseos Actuales")
    if not des.empty:
        st.table(des)
    else:
        st.info("No hay deseos registrados.")

with tab3:
    st.header("Cadenas de Intercambio Encontradas")
    if st.button("🔄 Ejecutar Motor de Intercambio", type="primary"):
        if inv.empty or des.empty:
            st.warning("Faltan datos en el Excel para calcular.")
        else:
            G = nx.DiGraph()
            # Construcción del grafo
            for _, row_pide in des.iterrows():
                pide = str(row_pide['Socio']).strip()
                set_buscado = str(row_pide['SetID']).strip()
                
                duenos = inv[inv['SetID'].astype(str).str.strip() == set_buscado]
                
                for _, row_dueno in duenos.iterrows():
                    da = str(row_dueno['Socio']).strip()
                    if pide != da:
                        G.add_edge(da, pide, set_id=set_buscado)

            # Encontrar ciclos
            ciclos = sorted(list(nx.simple_cycles(G)), key=len, reverse=True)
            
            if not ciclos:
                st.info("No hay intercambios posibles con los datos actuales.")
            else:
                usados = set()
                count = 0
                for ciclo in ciclos:
                    if any(s in usados for s in ciclo):
                        continue
                    
                    count += 1
                    with st.container():
                        st.subheader(f"✅ Propuesta #{count} ({len(ciclo)} socios)")
                        for i in range(len(ciclo)):
                            dante = ciclo[i]
                            receptor = ciclo[(i + 1) % len(ciclo)]
                            set_id = G[dante][receptor]['set_id']
                            st.write(f"👤 **{dante}** entrega Set **{set_id}** ➡️ a **{receptor}**")
                        for s in ciclo: usados.add(s)
                
                st.success(f"¡Se han encontrado soluciones para {len(usados)} socios!")
