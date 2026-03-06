import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Ajustes de Página
st.set_page_config(page_title="ALE! Swap v2.0", layout="wide")

# 2. Fuentes de Datos
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 3. Motor de Nombres (Rebrickable + Diccionario Local)
@st.cache_data(ttl=3600)
def get_lego_name(set_id):
    sid = str(set_id).strip()
    # Aseguramos los sets de tus capturas
    hardcoded = {
        "10316": "Rivendell",
        "75192": "Millennium Falcon UCS",
        "21333": "The Starry Night"
    }
    if sid in hardcoded:
        return hardcoded[sid]
    try:
        url = f"https://rebrickable.com/api/v3/lego/sets/{sid}-1/"
        headers = {"Authorization": "key 9d7b97368d90473950669f64e2621453"}
        r = requests.get(url, headers=headers, timeout=3)
        if r.status_code == 200:
            return r.json().get('name', f"Set {sid}")
    except:
        pass
    return f"LEGO {sid}"

# 4. Carga de Datos
def load_data():
    try:
        i = pd.read_csv(URL_INV).fillna("")
        d = pd.read_csv(URL_DES).fillna("")
        i.columns = [c.strip() for c in i.columns]
        d.columns = [c.strip() for c in d.columns]
        # Añadir nombres de sets
        i["Nombre"] = i["SetID"].astype(str).apply(get_lego_name)
        d["Nombre"] = d["SetID"].astype(str).apply(get_lego_name)
        return i, d
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 5. Cabecera Visual (Como la que te gustaba)
col_logo, col_text = st.columns([1, 5])
with col_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=80)
with col_text:
    st.title("Plataforma de Intercambio ALE!")
    st.caption("Asociación Cultural de Aficionados a LEGO® de España | v2.0")

# 6. Lógica de la App
inv, des = load_data()

tab1, tab2, tab3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Calcular Cambios"])

with tab1:
    if not inv.empty:
        # Usamos st.table para evitar el error "LargeUtf8" definitivamente
        st.table(inv[["Socio", "SetID", "Nombre"]])

with tab2:
    if not des.empty:
        st.table(des_df := des[["Socio", "SetID", "Nombre"]])

with tab3:
    if st.button("Buscar Intercambios Circulares"):
        G = nx.DiGraph()
        # Mapa de nombres para el resultado final
        n_map = pd.concat([inv, des]).set_index("SetID")["Nombre"].to_dict()
        
        for _, rd in des.iterrows():
            u_pide = str(rd["Socio"]).strip()
            s_id = str(rd["SetID"]).strip()
            # Quién lo tiene
            duenos = inv[inv["SetID"].astype(str).str.strip() == s_id]
            for _, ri in duenos.iterrows():
                u_da = str(ri["Socio"]).strip()
                if u_pide != u_da:
                    G.add_edge(u_da, u_pide, set_id=s_id)
        
        ciclos = list(nx.simple_cycles(G))
        if not ciclos:
            st.info("No se han detectado ciclos de intercambio.")
        else:
            st.success(f"¡{len(ciclos)} combinaciones encontradas!")
            for idx, c in enumerate(ciclos):
                with st.expander(f"Propuesta #{idx+1}"):
                    for j in range(len(c)):
                        dante = c[j]
                        recept = c[(j+1)%len(c)]
                        sid = G[dante][recept]["set_id"]
                        st.write(f"🎁 **{dante}** entrega **{sid}** ({n_map.get(sid)}) a **{recept}**")
