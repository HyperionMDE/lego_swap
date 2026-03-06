import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de página
st.set_page_config(page_title="ALE! Swap v17", layout="wide")

# URLs de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 2. Motor de Datos y Diccionario Local
NOMBRES_LOCALES = {
    "10316": "Rivendell", "75192": "Millennium Falcon UCS", "21333": "The Starry Night",
    "6886": "Galactic Peace Keeper", "10305": "Lion Knights' Castle"
}

@st.cache(ttl=3600, show_spinner=False)
def get_lego_info(sid):
    s = str(sid).strip()
    nombre_base = NOMBRES_LOCALES.get(s, f"Set LEGO {s}")
    info = {"name": nombre_base, "img": f"https://images.brickset.com/sets/images/{s}-1.jpg"}
    try:
        r = requests.get(f"https://rebrickable.com/api/v3/lego/sets/{s}-1/", 
                         headers={"Authorization": "key 9d7b97368d90473950669f64e2621453"}, timeout=1)
        if r.status_code == 200:
            data = r.json()
            if data.get('name'): info["name"] = data['name']
            if data.get('set_img_url'): info["img"] = data['set_img_url']
    except: pass
    return info

# 3. Diseño de Tablas ALE!
def pintar_tabla_ale(df):
    if df.empty: return "<p>No hay datos disponibles</p>"
    # Renombrar SetID a Set para visualización
    df_visual = df.rename(columns={"SetID": "Set"})
    
    html = '<table style="width:100%; border-collapse: separate; border-spacing: 0; font-family: sans-serif; margin-bottom: 30px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">'
    html += '<tr style="background-color: #2E7D32; color: white; text-align: left;">'
    for col in df_visual.columns:
        html += f'<th style="padding: 15px; border-bottom: 1px solid #ddd;">{col}</th>'
    html += '</tr>'
    for _, row in df_visual.iterrows():
        html += '<tr>'
        for col in df_visual.columns:
            val = row[col]
            if col == "Imagen":
                html += f'<td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;"><img src="{val}" width="80" style="border-radius: 5px; border: 1px solid #eee;" onerror="this.src=\'https://via.placeholder.com/80?text=LEGO\'"></td>'
            else:
                html += f'<td style="padding: 15px; border-bottom: 1px solid #eee;">{val}</td>'
        html += '</tr>'
    html += '</table>'
    return html

# --- CABECERA CON LOGO ---
col1, col2 = st.columns([1, 4])
with col1:
    # Logo oficial de ALE! (Asociación de Coleccionistas de LEGO en España)
    st.image("http://www.alebricks.com/wp-content/uploads/2015/05/logo_ale_web.png", width=150)
with col2:
    st.title("Sistema de Intercambio ALE!")
    st.subheader("Plataforma de gestión de sets entre socios")

try:
    inv = pd.read_csv(URL_INV).fillna("").astype(str)
    des = pd.read_csv(URL_DES).fillna("").astype(str)
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]

    with st.spinner("Sincronizando con la base de datos de ALE!..."):
        for df in [inv, des]:
            nombres, fotos = [], []
            for sid in df["SetID"]:
                res = get_lego_info(sid)
                nombres.append(res["name"])
                fotos.append(res["img"])
            df["Nombre"] = nombres
            df["Imagen"] = fotos

    st.header("📦 Sets Disponibles (Inventario)")
    st.markdown(pintar_tabla_ale(inv[["Socio", "SetID", "Nombre", "Imagen"]]), unsafe_allow_html=True)

    st.header("❤️ Sets Buscados (Deseos)")
    st.markdown(pintar_tabla_ale(des[["Socio", "SetID", "Nombre", "Imagen"]]), unsafe_allow_html=True)

    st.header("🚀 Propuesta de Intercambio Óptima")
    G = nx.DiGraph()
    master_info = pd.concat([inv, des]).drop_duplicates('SetID').set_index('SetID')

    for _, rd in des.iterrows():
        pide, sid = rd["Socio"].strip(), rd["SetID"].strip()
        duenos = inv[inv["SetID"].str.strip() == sid]
        for _, ri in duenos.iterrows():
            da = ri["Socio"].strip()
            if pide != da: G.add_edge(da, pide, sid=sid)
    
    ciclos = list(nx.simple_cycles(G))
    if ciclos:
        mejor = max(ciclos, key=len)
        res_list = []
        for j in range(len(mejor)):
            u1, u2 = mejor[j], mejor[(j+1)%len(mejor)]
            sid_c = G[u1][u2]["sid"]
            n_c = master_info.loc[sid_c, "Nombre"] if sid_c in master_info.index else f"Set {sid_c}"
            i_c = master_info.loc[sid_c, "Imagen"] if sid_c in master_info.index else ""
            res_list.append({"Socio Entrega": u1, "SetID": sid_c, "Nombre": n_c, "Imagen": i_c, "Socio Recibe": u2})
        st.markdown(pintar_tabla_ale(pd.DataFrame(res_list)), unsafe_allow_html=True)
    else:
        st.info("No hay ciclos de intercambio posibles todavía. ¡Sigue añadiendo sets!")

except Exception as e:
    st.error(f"Hubo un problema al cargar la aplicación: {e}")
