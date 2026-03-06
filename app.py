import streamlit as st
import pandas as pd
import networkx as nx

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="LEGO Swap Asociación", page_icon="🧩", layout="wide")

# Enlaces de tus pestañas
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        # Cargamos todo como string puro para evitar el error LargeUtf8
        inv = pd.read_csv(URL_INV, dtype=str).fillna("")
        des = pd.read_csv(URL_DES, dtype=str).fillna("")
        
        # Limpieza técnica de columnas
        inv.columns = [str(c).strip() for c in inv.columns]
        des.columns = [str(c).strip() for c in des.columns]
        
        return inv, des
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- INTERFAZ ---
st.title("🧩 LEGO Swap: Sistema de Intercambio")
st.markdown("Gestión de sets y deseos en tiempo real.")

inv, des = cargar_datos()

tab1, tab2, tab3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Calcular"])

with tab1:
    st.subheader("Sets que los socios ofrecen")
    if not inv.empty:
        # SOLUCIÓN AL ERROR ROSA: Usamos st.table() en lugar de st.dataframe()
        st.table(inv)
    else:
        st.info("Inventario vacío.")

with tab2:
    st.subheader("Sets que los socios buscan")
    if not des.empty:
        st.table(des)
    else:
        st.info("Sin deseos registrados.")

with tab3:
    st.subheader("Intercambios Sugeridos")
    if st.button("🔥 ¡Calcular ahora!", type="primary"):
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
                st.info("No hay ciclos de cambio posibles hoy.")
            else:
                usados = set()
                for i, ciclo in enumerate(ciclos, 1):
                    if any(s in usados for s in ciclo): continue
                    with st.expander(f"✅ Propuesta #{i} ({len(ciclo)} socios)", expanded=True):
                        for j in range(len(ciclo)):
                            dante, recp = ciclo[j], ciclo[(j+1)%len(ciclo)]
                            st.write(f"👤 **{dante}** entrega el Set **{G[dante][recp]['set_id']}** ➡️ a **{recp}**")
                    for s in ciclo: usados.add(s)
                st.success(f"¡{len(usados)} socios pueden intercambiar!")
