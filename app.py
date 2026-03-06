import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Ajustes de la App
st.set_page_config(page_title="ALE! Swap v4.0", layout="centered")

URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 2. Motor de Nombres (Blindado)
@st.cache_data(ttl=3600)
def get_name(sid):
    s = str(sid).strip()
    favs = {"10316": "Rivendell", "75192": "Millennium Falcon UCS", "21333": "The Starry Night"}
    if s in favs: return favs[s]
    try:
        r = requests.get(f"https://rebrickable.com/api/v3/lego/sets/{s}-1/", 
                         headers={"Authorization": "key 9d7b97368d90473950669f64e2621453"}, timeout=2)
        if r.status_code == 200: return r.json().get('name', f"Set {s}")
    except: pass
    return f"LEGO {s}"

# 3. Función de Visualización v4.0 (Sin fallos de tipo de datos)
def pintar_lista_simple(df, titulo):
    st.subheader(titulo)
    if df.empty:
        st.write("No hay datos.")
        return
    # Pintamos fila a fila manualmente para evitar CUALQUIER error de tabla de Streamlit
    for _, fila in df.iterrows():
        st.markdown(f"👤 **{fila['Socio']}** → 🏗️ {fila['SetID']} (*{fila.get('Nombre', '')}*)")
    st.divider()

# 4. Lógica Principal
st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=80)
st.title("Intercambio Masivo ALE!")

try:
    inv = pd.read_csv(URL_INV).fillna("")
    des = pd.read_csv(URL_DES).fillna("")
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]
    
    # Añadimos los nombres de los sets
    inv["Nombre"] = inv["SetID"].astype(str).apply(get_name)
    des["Nombre"] = des["SetID"].astype(str).apply(get_name)

    t1, t2, t3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Calcular"])

    with t1:
        pintar_lista_simple(inv, "Sets Disponibles")

    with t2:
        pintar_lista_simple(des, "Sets Buscados")

    with t3:
        if st.button("🔍 Calcular Intercambios"):
            G = nx.DiGraph()
            n_map = pd.concat([inv, des]).set_index("SetID")["Nombre"].to_dict()
            for _, rd in des.iterrows():
                p, s = str(rd["Socio"]).strip(), str(rd["SetID"]).strip()
                duenos = inv[inv["SetID"].astype(str).str.strip() == s]
                for _, ri in duenos.iterrows():
                    d = str(ri["Socio"]).strip()
                    if p != d: G.add_edge(d, p, sid=s)
            
            ciclos = list(nx.simple_cycles(G))
            if not ciclos:
                st.info("Sin intercambios circulares por ahora.")
            else:
                for idx, c in enumerate(ciclos):
                    with st.expander(f"PROPUESTA #{idx+1}"):
                        for j in range(len(c)):
                            u1, u2 = c[j], c[(j+1)%len(c)]
                            item = G[u1][u2]["sid"]
                            st.write(f"✅ **{u1}** da **{item}** ({n_map.get(item)}) a **{u2}**")

except Exception as e:
    st.error(f"Error crítico: {e}")

if st.button("🔄 Recargar Todo"):
    st.cache_data.clear()
    st.rerun()
