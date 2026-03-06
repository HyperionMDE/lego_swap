import streamlit as st
import pandas as pd
import networkx as nx

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="LEGO Swap Asociación", page_icon="🧩", layout="wide")

URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar_datos():
    # Cargamos como texto para evitar errores de formato
    inv = pd.read_csv(URL_INV, dtype=str).fillna("")
    des = pd.read_csv(URL_DES, dtype=str).fillna("")
    inv.columns = inv.columns.str.strip()
    des.columns = des.columns.str.strip()
    return inv, des

st.title("🧩 LEGO Swap: Sistema de Intercambio")

inv, des = cargar_datos()

tab1, tab2, tab3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Calcular Cambios"])

with tab1:
    st.header("Sets Disponibles")
    # Usamos st.table para evitar el error de LargeUtf8 que da st.dataframe
    st.table(inv)

with tab2:
    st.header("Lista de Deseos")
    st.table(des)

with tab3:
    if st.button("🔄 Buscar Cadenas de Intercambio", type="primary"):
        G = nx.DiGraph()
        for _, row in des.iterrows():
            pide, set_id = str(row['Socio']), str(row['SetID'])
            duenos = inv[inv['SetID'] == set_id]
            for _, d in duenos.iterrows():
                if pide != str(d['Socio']):
                    G.add_edge(str(d['Socio']), pide, set_id=set_id)

        ciclos = sorted(list(nx.simple_cycles(G)), key=len, reverse=True)
        
        if not ciclos:
            st.warning("No hay intercambios posibles aún. ¡Anima a los socios a pedir más sets!")
        else:
            usados = set()
            for i, ciclo in enumerate(ciclos, 1):
                if any(s in usados for s in ciclo): continue
                with st.expander(f"✅ Propuesta #{i}: Cambio entre {len(ciclo)} personas", expanded=True):
                    for j in range(len(ciclo)):
                        dante, recp = ciclo[j], ciclo[(j+1)%len(ciclo)]
                        st.write(f"👤 **{dante}** da Set **{G[dante][recp]['set_id']}** ➡️ a **{recp}**")
                for s in ciclo: usados.add(s)
            st.success(f"¡Intercambio optimizado para {len(usados)} personas!")
