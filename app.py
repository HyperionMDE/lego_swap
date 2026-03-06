import streamlit as st
import pandas as pd
import networkx as nx
import requests
import time

# 1. Configuración de página
st.set_page_config(page_title="ALE! Intercambio Masivo", layout="wide")

# URLs de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 2. Diccionario de emergencia (Nombres garantizados)
NOMBRES_LOCALES = {
    "10316": "Rivendell", "75192": "Millennium Falcon UCS", 
    "21333": "The Starry Night", "6886": "Galactic Peace Keeper", 
    "10305": "Lion Knights' Castle", "75313": "AT-AT UCS", "10317": "Land Rover Classic"
}

@st.cache(ttl=3600, show_spinner=False)
def get_lego_info(sid):
    s = str(sid).strip()
    # Nombre por defecto siempre presente
    info = {"name": NOMBRES_LOCALES.get(s, f"Set {s}"), "img": f"https://images.brickset.com/sets/images/{s}-1.jpg"}
    try:
        # Petición con timeout más largo para asegurar respuesta
        r = requests.get(f"https://rebrickable.com/api/v3/lego/sets/{s}-1/", 
                         headers={"Authorization": "key 9d7b97368d90473950669f64e2621453"}, timeout=2.0)
        if r.status_code == 200:
            data = r.json()
            if data.get('name'): info["name"] = data['name']
            if data.get('set_img_url'): info["img"] = data['set_img_url']
    except: pass
    return info

# 3. Diseño de tablas ultra-responsivas
def pintar_tabla_ale(df, es_resultado=False):
    if df.empty: return "<p>No hay datos.</p>"
    df_v = df.rename(columns={"SetID": "Set", "Socio Entrega": "Socio", "Socio Recibe": "Destinatario"})
    
    # Ajuste de tamaño según si es la tabla de resultados (que es más ancha)
    padding = "8px" if es_resultado else "12px"
    font_size = "0.75em" if es_resultado else "0.85em"
    
    html = '<div style="overflow-x:auto;">'
    html += f'<table style="width:100%; border-collapse: collapse; font-family: sans-serif; margin-bottom: 20px; border: 1px solid #ddd; border-radius: 8px; font-size: {font_size};">'
    html += '<tr style="background-color: #2E7D32; color: white; text-align: left;">'
    for col in df_v.columns:
        html += f'<th style="padding: {padding}; border-bottom: 2px solid #1B5E20;">{col}</th>'
    html += '</tr>'
    for _, row in df_v.iterrows():
        html += '<tr>'
        for col in df_v.columns:
            val = row[col]
            if col == "Imagen":
                html += f'<td style="padding: 5px; border-bottom: 1px solid #eee; text-align: center;"><img src="{val}" width="55" style="border-radius: 3px;" onerror="this.src=\'https://via.placeholder.com/55?text=LEGO\'"></td>'
            else:
                html += f'<td style="padding: {padding}; border-bottom: 1px solid #eee;">{val}</td>'
        html += '</tr>'
    html += '</table></div>'
    return html

# --- CABECERA RESPONSIVA ---
st.write('''
<style>
    .header-ale { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 15px; padding: 15px; background: #fff; border-bottom: 4px solid #2E7D32; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .logo-container { display: flex; gap: 10px; align-items: center; }
    .text-container { text-align: center; min-width: 200px; }
    @media (min-width: 600px) { .header-ale { justify-content: flex-start; text-align: left; } .text-container { text-align: left; } }
</style>
<div class="header-ale">
    <div class="logo-container">
        <img src="https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg" width="50">
        <img src="https://www.alebricks.com/foro/custom_avatar/avatar_2_1508999828.png" width="90">
    </div>
    <div class="text-container">
        <h2 style="margin: 0; color: #d11111; font-size: 1.4em;">ASOCIACIÓN ALE!</h2>
        <p style="margin: 0; font-weight: bold; font-size: 0.9em; color: #333; text-transform: uppercase;">Intercambio Masivo de Sets</p>
    </div>
</div>
''', unsafe_allow_html=True)

try:
    inv = pd.read_csv(URL_INV).fillna("").astype(str)
    des = pd.read_csv(URL_DES).fillna("").astype(str)
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]

    # PROCESO CRÍTICO DE NOMBRES
    with st.spinner("Sincronizando nombres de la base de datos..."):
        for df in [inv, des]:
            n_list, f_list = [], []
            for sid in df["SetID"]:
                res = get_lego_info(sid)
                n_list.append(res["name"])
                f_list.append(res["img"])
                # Pequeña pausa para no saturar la API y que no nos bloquee los nombres
                if len(n_list) % 5 == 0: time.sleep(0.1)
            df["Nombre"] = n_list
            df["Imagen"] = f_list

    # SECCIONES
    st.subheader("📦 Inventario")
    st.markdown(pintar_tabla_ale(inv[["Socio", "SetID", "Nombre", "Imagen"]]), unsafe_allow_html=True)

    st.subheader("❤️ Deseos")
    st.markdown(pintar_tabla_ale(des[["Socio", "SetID", "Nombre", "Imagen"]]), unsafe_allow_html=True)

    st.subheader("🚀 Resultado Óptimo")
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
            res_list.append({"Entrega": u1, "SetID": sid_c, "Nombre": n_c, "Imagen": i_c, "Recibe": u2})
        
        # Tabla de resultados con fuente más pequeña para que quepa en móvil
        st.markdown(pintar_tabla_ale(pd.DataFrame(res_list), es_resultado=True), unsafe_allow_html=True)
    else:
        st.info("No hay intercambios posibles por ahora.")

except Exception as e:
    st.error(f"Error de conexión: {e}")
