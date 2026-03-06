import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de página
st.set_page_config(page_title="ALE! Intercambio Masivo", layout="wide")

# URLs de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 2. Diccionario de emergencia para nombres
NOMBRES_LOCALES = {
    "10316": "Rivendell", "75192": "Millennium Falcon UCS", 
    "21333": "The Starry Night", "6886": "Galactic Peace Keeper", 
    "10305": "Lion Knights' Castle"
}

@st.cache(ttl=3600, show_spinner=False)
def get_lego_info(sid):
    s = str(sid).strip()
    nombre_base = NOMBRES_LOCALES.get(s, f"Set LEGO {s}")
    info = {"name": nombre_base, "img": f"https://images.brickset.com/sets/images/{s}-1.jpg"}
    try:
        r = requests.get(f"https://rebrickable.com/api/v3/lego/sets/{s}-1/", 
                         headers={"Authorization": "key 9d7b97368d90473950669f64e2621453"}, timeout=1.2)
        if r.status_code == 200:
            data = r.json()
            if data.get('name'): info["name"] = data['name']
            if data.get('set_img_url'): info["img"] = data['set_img_url']
    except: pass
    return info

# 3. Función de tabla con diseño ALE! (Sin SetID ni SWAP)
def pintar_tabla_ale(df):
    if df.empty: return "<p>No hay datos registrados todavía.</p>"
    # Renombrado forzado para la vista
    df_v = df.rename(columns={"SetID": "Set", "Socio Entrega": "Socio", "Socio Recibe": "Destinatario"})
    
    html = '<table style="width:100%; border-collapse: separate; border-spacing: 0; font-family: sans-serif; margin-bottom: 30px; border: 1px solid #ddd; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">'
    html += '<tr style="background-color: #2E7D32; color: white; text-align: left;">'
    for col in df_v.columns:
        html += f'<th style="padding: 15px;">{col}</th>'
    html += '</tr>'
    for _, row in df_v.iterrows():
        html += '<tr>'
        for col in df_v.columns:
            val = row[col]
            if col == "Imagen":
                html += f'<td style="padding: 10px; border-top: 1px solid #eee; text-align: center;"><img src="{val}" width="90" style="border-radius: 5px;" onerror="this.src=\'https://via.placeholder.com/90?text=LEGO\'"></td>'
            else:
                html += f'<td style="padding: 15px; border-top: 1px solid #eee;">{val}</td>'
        html += '</tr>'
    html += '</table>'
    return html

# --- CABECERA CON DOBLE LOGO (LEGO Y ALE!) Y TÍTULO SIN SWAP ---
st.write('<div style="display: flex; align-items: center; justify-content: center; margin-bottom: 30px; gap: 30px; padding: 10px;">'
         '<img src="https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg" width="90">'
         '<img src="http://www.alebricks.com/wp-content/uploads/2015/05/logo_ale_web.png" width="160" onerror="this.src=\'https://via.placeholder.com/160x90?text=ALE!\'"> ' # URL alternativa y robusta
         '<div><h1 style="margin: 0; color: #2E7D32; font-size: 2.2em;">ASOCIACIÓN ALE!</h1>'
         '<p style="margin: 0; font-weight: bold; font-size: 1.4em;">SISTEMA DE INTERCAMBIO MASIVO DE SETS ENTRE SOCIOS</p></div>'
         '</div>', unsafe_allow_html=True)

try:
    inv = pd.read_csv(URL_INV).fillna("").astype(str)
    des = pd.read_csv(URL_DES).fillna("").astype(str)
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]

    with st.spinner("Actualizando catálogo masivo de ALE!..."):
        for df in [inv, des]:
            n_list, f_list = [], []
            for sid in df["SetID"]:
                res = get_lego_info(sid)
                n_list.append(res["name"])
                f_list.append(res["img"])
            df["Nombre"] = n_list
            df["Imagen"] = f_list

    # SECCIONES
    st.header("📦 Inventario Global de la Asociación")
    st.markdown(pintar_tabla_ale(inv[["Socio", "SetID", "Nombre", "Imagen"]]), unsafe_allow_html=True)

    st.header("❤️ Lista Maestra de Deseos")
    st.markdown(pintar_tabla_ale(des[["Socio", "SetID", "Nombre", "Imagen"]]), unsafe_allow_html=True)

    st.header("🚀 Propuesta de Intercambio Circular (Óptima)")
    G = nx.DiGraph()
    m_info = pd.concat([inv, des]).drop_duplicates('SetID').set_index('SetID')

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
            n_c = m_info.loc[sid_c, "Nombre"] if sid_c in m_info.index else f"Set {sid_c}"
            i_c = m_info.loc[sid_c, "Imagen"] if sid_c in m_info.index else ""
            res_list.append({"Socio Entrega": u1, "SetID": sid_c, "Nombre": n_c, "Imagen": i_c, "Socio Recibe": u2})
        
        # Tabla final con los nombres de columna corregidos (Sin SetID ni SWAP)
        st.markdown(pintar_tabla_ale(pd.DataFrame(res_list)), unsafe_allow_html=True)
    else:
        st.info("Buscando carambolas... Todavía no hay un ciclo de intercambio circular completo.")

except Exception as e:
    st.error(f"Error técnico en la plataforma: {e}")
