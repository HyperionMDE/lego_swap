import streamlit as st
import pandas as pd
import networkx as nx

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="LEGO Swap", page_icon="🧩", layout="wide")

URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

@st.cache_data(ttl=30)
def cargar_datos():
    try:
        # Forzamos a que todo sea texto para evitar el error LargeUtf8
        inv = pd.read_csv(URL_INV, dtype=str).fillna("")
        des = pd.read_csv(URL_DES, dtype=str).fillna("")
        inv.columns = [str(c).strip() for c in inv.columns]
        des.columns = [str(c).strip() for c in des.columns]
        return inv, des
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame(), pd.DataFrame()

st.title("🧩 LEGO Swap: Sistema de Intercambio")

inv, des = cargar_datos()

# --- ESTILO PARA TABLAS ---
# Este bloque elimina cualquier procesamiento raro del navegador
st.markdown("""
<style>
    table { width: 100%; border-collapse: collapse; }
    th { background-color: #f0f2f6; text-align: left; padding: 10px; }
    td { padding: 10px; border-bottom: 1px solid #ddd; }
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Calcular"])

with tab1:
    st.header("Sets Disponibles")
    if not inv.empty:
        # USAMOS HTML PURO: Esto es lo que mata el error rosa
        st.write(inv.to_html(index=False, escape=False), unsafe_allow_html=True)

with tab2:
    st.header("Lista de Deseos")
    if not des.empty:
        st.write(des.to_html(index=False, escape=False), unsafe_allow_html=True)

with tab3:
    st.header("Cadenas de Cambio")
    if st.button("🔄 Ejecutar Motor", type="primary"):
        G = nx.DiGraph()
        for _, row in des.iterrows():
            pide, set_id = str(row['Socio']).strip(), str(row['SetID']).strip()
            duenos = inv[inv['SetID'].astype(str).str.strip() == set_id]
            for _, d in duenos.iterrows():
                da = str(d['Socio']).strip()
                if pide != da:
                    G.add_edge(da, pide, set_id=set_id)

        ciclos = sorted(list(nx.simple_cycles(G)), key=len, reverse=True)
        
        if not ciclos:
            st.info("No hay cambios circulares posibles hoy.")
        else:
            usados = set()
            for i, ciclo in enumerate(ciclos, 1):
                if any(s in usados for s in ciclo): continue
                with st.expander(f"✅ Propuesta #{i}", expanded=True):
                    for j in range(len(ciclo)):
                        dante, recp = ciclo[j], ciclo[(j+1)%len(ciclo)]
                        st.write(f"👤 **{dante}** da Set **{G[dante][recp]['set_id']}** ➡️ a **{recp}**")
                for s in ciclo: usados.add(s)
            st.success(f"¡Intercambios logrados para {len(usados)} personas!")
