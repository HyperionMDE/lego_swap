import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de página
st.set_page_config(page_title="ALE! Swap v16.2", layout="wide")

# URLs de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 2. Diccionario de emergencia (Si la API falla, usamos estos)
NOMBRES_LOCALES = {
    "10316": "Rivendell",
    "75192": "Millennium Falcon UCS",
    "21333": "The Starry Night",
    "6886": "Galactic Peace Keeper",
    "10305": "Lion Knights' Castle",
    "75313": "AT-AT UCS",
    "71040": "Disney Castle"
}

@st.cache(ttl=3600, show_spinner=False)
def get_lego_info(sid):
    s = str(sid).strip()
    # 1. Intentamos nombre local primero
    nombre_base = NOMBRES_LOCALES.get(s, f"Set LEGO {s}")
    info = {"name": nombre_base, "img": f"https://images.brickset.com/sets/images/{s}-1.jpg"}
    
    # 2. Intentamos API (si falla, no pasa nada porque ya tenemos lo de arriba)
    try:
        r = requests.get(f"https://rebrickable.com/api/v3/lego/sets/{s}-1/", 
                         headers={"Authorization": "key 9d7b97368d90473950669f64e2621453"}, timeout=1)
        if r.status_code == 200:
            data = r.json()
            if data.get('name'): info["name"] = data['name']
            if data.get('set_img_url'): info["img"] = data['set_img_url']
    except:
        pass
    return info

def pintar_tabla_estetica(df):
    if df.empty: return "<p>No hay datos disponibles</p>"
    html = '<table style="width:100%; border-collapse: collapse; font-family: sans-serif; margin-bottom: 30px;">'
    html += '<tr style="background-color: #2E7D32; color: white; text-align: left;">'
    for col in df.columns:
        html += f'<th style="padding: 12px; border: 1px solid #ddd;">{col}</th>'
    html += '</tr>'
    for _, row in df.iterrows():
        html += '<tr>'
        for col in df.columns:
            val = row[col]
            if col == "Imagen":
                html += f'<td style="padding: 5px; border: 1px solid #ddd; text-align: center;"><img src="{val}" width="80" style="border-radius: 4px;" onerror="this.src=\'https://via.placeholder.com/80?text=LEGO\'"></td>'
            else:
                html += f'<td style="padding: 12px; border: 1px solid #ddd;">{val}</td>'
        html += '</tr>'
    html += '</table>'
    return html

# --- FLUJO ---
st.title("Plataforma de Intercambio ALE!")

try:
    inv = pd.read_csv(URL_INV).fillna("").astype(str)
    des = pd.read_csv(URL_DES).fillna("").astype(str)
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]

    # PROCESAR NOMBRES E IMÁGENES ANTES DE TODO
    with st.spinner("Cargando datos de los sets..."):
        for df in [inv, des]:
            nombres, fotos = [], []
            for sid in df["SetID"]:
                res = get_lego_info(sid)
                nombres.append(res["name"])
                fotos.append(res["img"])
            df["Nombre"] = nombres
            df["Imagen"] = fotos

    st.header("📦 Inventario Disponible")
    st.markdown(pintar_tabla_estetica(inv[["Socio", "SetID", "Nombre", "Imagen"]]), unsafe_allow_html=True)

    st.header("❤️ Lista de Deseos")
    st.markdown(pintar_tabla_estetica(des[["Socio", "SetID", "Nombre", "Imagen"]]), unsafe_allow_html=True)

    st.header("🚀 Resultado Óptimo")
    G = nx.DiGraph()
    # Diccionario rápido para recuperar info en el cálculo
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
            # Sacamos la info que ya procesamos arriba
            n_c = master_info.loc[sid_c, "Nombre"] if sid_c in master_info.index else f"Set {sid_c}"
            i_c = master_info.loc[sid_c, "Imagen"] if sid_c in master_info.index else ""
            
            res_list.append({
                "Socio Entrega": u1,
                "SetID": sid_c,
                "Nombre": n_c,
                "Imagen": i_c,
                "Socio Recibe": u2
            })
        st.markdown(pintar_tabla_estetica(pd.DataFrame(res_list)), unsafe_allow_html=True)
    else:
        st.info("No hay ciclos de intercambio posibles.")

except Exception as e:
    st.error(f"Error: {e}")
