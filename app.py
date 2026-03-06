import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración básica (Máxima compatibilidad)
st.set_page_config(page_title="ALE! Swap v5.0", layout="centered")

URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 2. Motor de Nombres Infalible
@st.cache_data(ttl=3600)
def conseguir_nombre(sid):
    s = str(sid).strip()
    # Forzamos los nombres que te interesan
    manual = {
        "10316": "Rivendell",
        "75192": "Millennium Falcon UCS",
        "21333": "The Starry Night (Van Gogh)"
    }
    if s in manual: return manual[s]
    
    try:
        url = f"https://rebrickable.com/api/v3/lego/sets/{s}-1/"
        headers = {"Authorization": "key 9d7b97368d90473950669f64e2621453"}
        r = requests.get(url, headers=headers, timeout=2)
        if r.status_code == 200:
            return r.json().get('name', f"Set {s}")
    except:
        pass
    return f"Lego {s}"

# 3. Interfaz Principal
st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=80)
st.title("Intercambio ALE! - Versión 5.0")

try:
    # Carga de datos
    df_i = pd.read_csv(URL_INV).fillna("")
    df_d = pd.read_csv(URL_DES).fillna("")
    df_i.columns = [c.strip() for c in df_i.columns]
    df_d.columns = [c.strip() for c in df_d.columns]

    # PROCESO DE NOMBRES (Crucial)
    df_i["Nombre"] = df_i["SetID"].astype(str).apply(conseguir_nombre)
    df_d["Nombre"] = df_d["SetID"].astype(str).apply(conseguir_nombre)

    # Pestañas
    t1, t2, t3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Calcular"])

    with t1:
        st.subheader("Sets que ofrecen los socios")
        for _, fila in df_i.iterrows():
            st.markdown(f"👤 **{fila['Socio']}** tiene: `{fila['SetID']}` - **{fila['Nombre']}**")

    with t2:
        st.subheader("Sets que buscan los socios")
        if df_d.empty:
            st.write("No hay deseos registrados.")
        else:
            for _, fila in df_d.iterrows():
                st.markdown(f"👤 **{fila['Socio']}** busca: `{fila['SetID']}` - **{fila['Nombre']}**")

    with t3:
        if st.button("🔍 Buscar Cadenas de Cambio"):
            G = nx.DiGraph()
            # Mapa para los nombres en el resultado
            m_nombres = pd.concat([df_i, df_d]).set_index("SetID")["Nombre"].to_dict()
            
            for _, rd in df_d.iterrows():
                pide, sid = str(rd["Socio"]).strip(), str(rd["SetID"]).strip()
                duenos = df_i[df_i["SetID"].astype(str).str.strip() == sid]
                for _, ri in duenos.iterrows():
                    da = str(ri["Socio"]).strip()
                    if pide != da:
                        G.add_edge(da, pide, set_id=sid)
            
            ciclos = list(nx.simple_cycles(G))
            if not ciclos:
                st.info("No hay intercambios circulares posibles ahora.")
            else:
                st.success(f"¡Se han encontrado {len(ciclos)} propuestas!")
                for i, c in enumerate(ciclos):
                    with st.expander(f"PROPUESTA #{i+1}"):
                        for j in range(len(c)):
                            u1, u2 = c[j], c[(j+1)%len(c)]
                            item = G[u1][u2]["set_id"]
                            st.write(f"✅ **{u1}** entrega **{item}** ({m_nombres.get(item)}) a **{u2}**")

except Exception as e:
    st.error(f"Error cargando los datos: {e}")

st.write("")
if st.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    # Usamos un método de recarga compatible con versiones viejas
    st.markdown('<meta http-equiv="refresh" content="0">', unsafe_allow_html=True)
