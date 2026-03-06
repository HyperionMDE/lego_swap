import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de página
st.set_page_config(page_title="Intercambio Masivo ALE!", layout="wide")

# URLs de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 2. Motor de búsqueda de sets
@st.cache(ttl=3600, show_spinner=False)
def get_lego_info(sid):
    s = str(sid).strip()
    info = {"name": f"Set LEGO {s}", "img": f"https://images.brickset.com/sets/images/{s}-1.jpg"}
    try:
        r = requests.get(f"https://rebrickable.com/api/v3/lego/sets/{s}-1/", 
                         headers={"Authorization": "key 9d7b97368d90473950669f64e2621453"}, timeout=1.2)
        if r.status_code == 200:
            data = r.json()
            if data.get('name'): info["name"] = data['name']
            if data.get('set_img_url'): info["img"] = data['set_img_url']
    except: pass
    return info

# 3. Diseño de tablas responsivas
def pintar_tabla_ale(df):
    if df.empty: return "<p>No hay datos registrados.</p>"
    df_v = df.rename(columns={"SetID": "Set", "Socio Entrega": "Socio", "Socio Recibe": "Destinatario"})
    
    html = '<div style="overflow-x:auto;">' # Permite scroll lateral en móvil si la tabla es ancha
    html += '<table style="width:100%; border-collapse: separate; border-spacing: 0; font-family: sans-serif; margin-bottom: 30px; border: 1px solid #ddd; border-radius: 10px; overflow: hidden;">'
    html += '<tr style="background-color: #2E7D32; color: white; text-align: left;">'
    for col in df_v.columns:
        html += f'<th style="padding: 12px; font-size: 0.9em;">{col}</th>'
    html += '</tr>'
    for _, row in df_v.iterrows():
        html += '<tr>'
        for col in df_v.columns:
            val = row[col]
            if col == "Imagen":
                html += f'<td style="padding: 5px; border-top: 1px solid #eee; text-align: center;"><img src="{val}" width="70" style="border-radius: 5px;" onerror="this.src=\'https://via.placeholder.com/70?text=LEGO\'"></td>'
            else:
                html += f'<td style="padding: 12px; border-top: 1px solid #eee; font-size: 0.85em;">{val}</td>'
        html += '</tr>'
    html += '</table></div>'
    return html

# --- CABECERA RESPONSIVA (Se adapta a móvil) ---
st.write('''
<style>
    .header-container {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: center;
        gap: 20px;
        background-color: #ffffff;
        padding: 15px;
        border-radius: 15px;
        border-bottom: 4px solid #2E7D32;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .logos-box {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .title-box {
        min-width: 250px;
    }
    @media (min-width: 600px) {
        .header-container { text-align: left; justify-content: flex-start; }
    }
</style>
<div class="header-container">
    <div class="logos-box">
        <img src="https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg" width="60">
        <img src="https://www.alebricks.com/foro/custom_avatar/avatar_2_1508999828.png" width="100">
    </div>
    <div class="title-box">
        <h1 style="margin: 0; color: #d11111; font-size: 1.5em; line-height: 1;">ASOCIACIÓN ALE!</h1>
        <p style="margin: 5px 0 0 0; font-weight: bold; font-size: 1em; color: #333; text-transform: uppercase;">Sistema de Intercambio Masivo de Sets</p>
    </div>
</div>
''', unsafe_allow_html=True)

try:
    inv = pd.read_csv(URL_INV).fillna("").astype(str)
    des = pd.read_csv(URL_DES).fillna("").astype(str)
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]

    with st.spinner("Cargando datos..."):
        for df in [inv, des]:
            n_list, f_list = [], []
            for sid in df["SetID"]:
                res = get_lego_info(sid)
                n_list.append(res["name"])
                f_list.append(res["img"])
            df["Nombre"] = n_list
            df["Imagen"] = f_list

    st.header("📦 Inventario")
    st.markdown(pintar_tabla_ale(inv[["Socio", "SetID", "Nombre", "Imagen"]]), unsafe_allow_html=True)

    st.header("❤️ Lista de Deseos")
    st.markdown(pintar_tabla_ale(des[["Socio", "SetID", "Nombre", "Imagen"]]), unsafe_allow_html=True)

    st.header("🚀 Resultado Óptimo")
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
        st.markdown(pintar_tabla_ale(pd.DataFrame(res_list)), unsafe_allow_html=True)
    else:
        st.info("No hay ciclos de intercambio disponibles.")

except Exception as e:
    st.error(f"Error: {e}")
