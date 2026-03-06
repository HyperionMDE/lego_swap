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

# 2. DICCIONARIO DE REFUERZO (Nombres que saldrán SÍ O SÍ)
NOMBRES_LOCALES = {
    "10316": "Rivendell", 
    "75192": "Millennium Falcon UCS", 
    "21333": "The Starry Night", 
    "6886": "Galactic Peace Keeper", 
    "10305": "Lion Knights' Castle",
    "75313": "AT-AT UCS",
    "10317": "Land Rover Classic",
    "10302": "Optimus Prime",
    "75308": "R2-D2",
    "10274": "Ghostbusters ECTO-1"
}

@st.cache(ttl=3600, show_spinner=False)
def get_lego_info(sid):
    s = str(sid).strip()
    # PASO 1: Prioridad absoluta al diccionario local
    nombre_final = NOMBRES_LOCALES.get(s, f"Set LEGO {s}")
    img_final = f"https://images.brickset.com/sets/images/{s}-1.jpg"
    
    # PASO 2: Intentar mejorar la info con la API, pero si falla, mantenemos lo anterior
    try:
        r = requests.get(f"https://rebrickable.com/api/v3/lego/sets/{s}-1/", 
                         headers={"Authorization": "key 9d7b97368d90473950669f64e2621453"}, timeout=1.5)
        if r.status_code == 200:
            data = r.json()
            nombre_final = data.get('name', nombre_final)
            img_final = data.get('set_img_url', img_final)
    except:
        pass
    return {"name": nombre_final, "img": img_final}

# 3. Función de tabla ultra-compacta para móviles
def pintar_tabla_ale(df, es_resultado=False):
    if df.empty: return "<p style='color:gray;'>Sin datos.</p>"
    
    # Renombrar para ahorrar espacio en móvil
    df_v = df.rename(columns={"SetID": "Set", "Socio Entrega": "Socio", "Socio Recibe": "Recibe"})
    
    f_size = "0.75rem" if es_resultado else "0.85rem"
    img_w = "50" if es_resultado else "65"
    
    html = '<div style="overflow-x:auto; -webkit-overflow-scrolling: touch;">'
    html += f'<table style="width:100%; border-collapse: collapse; font-family: sans-serif; font-size: {f_size}; border: 1px solid #ddd; border-radius: 8px;">'
    html += '<tr style="background-color: #2E7D32; color: white;">'
    for col in df_v.columns:
        html += f'<th style="padding: 8px; text-align: left;">{col}</th>'
    html += '</tr>'
    
    for _, row in df_v.iterrows():
        html += '<tr style="border-bottom: 1px solid #eee;">'
        for col in df_v.columns:
            val = row[col]
            if col == "Imagen":
                html += f'<td style="padding: 4px; text-align: center;"><img src="{val}" width="{img_w}" style="border-radius: 4px;" onerror="this.src=\'https://via.placeholder.com/50?text=LEGO\'"></td>'
            else:
                html += f'<td style="padding: 8px;">{val}</td>'
        html += '</tr>'
    html += '</table></div>'
    return html

# --- CABECERA RESPONSIVA ---
st.write('''
<style>
    .header-ale { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 15px; padding: 15px; background: #fff; border-bottom: 4px solid #2E7D32; border-radius: 12px; margin-bottom: 20px; }
    @media (min-width: 600px) { .header-ale { justify-content: flex-start; } }
</style>
<div class="header-ale">
    <img src="https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg" width="50">
    <img src="https://www.alebricks.com/foro/custom_avatar/avatar_2_1508999828.png" width="90">
    <div>
        <h2 style="margin: 0; color: #d11111; font-size: 1.3em;">ASOCIACIÓN ALE!</h2>
        <p style="margin: 0; font-weight: bold; font-size: 0.85em; color: #333;">INTERCAMBIO MASIVO DE SETS</p>
    </div>
</div>
''', unsafe_allow_html=True)

try:
    inv = pd.read_csv(URL_INV).fillna("").astype(str)
    des = pd.read_csv(URL_DES).fillna("").astype(str)
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]

    # CARGA DE NOMBRES CON SEGURIDAD
    with st.spinner("Cargando nombres de la Asociación..."):
        m_info = {}
        todos_sets = pd.concat([inv["SetID"], des["SetID"]]).unique()
        for sid in todos_sets:
            m_info[sid] = get_lego_info(sid)
            time.sleep(0.05) # Pausa mínima para no saturar
            
        for df in [inv, des]:
            df["Nombre"] = df["SetID"].map(lambda x: m_info[x]["name"])
            df["Imagen"] = df["SetID"].map(lambda x: m_info[x]["img"])

    # SECCIONES
    st.subheader("📦 Inventario")
    st.markdown(pintar_tabla_ale(inv[["Socio", "SetID", "Nombre", "Imagen"]]), unsafe_allow_html=True)

    st.subheader("❤️ Deseos")
    st.markdown(pintar_tabla_ale(des[["Socio", "SetID", "Nombre", "Imagen"]]), unsafe_allow_html=True)

    st.subheader("🚀 Resultado Óptimo")
    G = nx.DiGraph()
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
            res_list.append({
                "Entrega": u1, 
                "Set": sid_c, 
                "Nombre": m_info[sid_c]["name"], 
                "Imagen": m_info[sid_c]["img"], 
                "Recibe": u2
            })
        st.markdown(pintar_tabla_ale(pd.DataFrame(res_list), es_resultado=True), unsafe_allow_html=True)
    else:
        st.info("Sin intercambios circulares por ahora.")

except Exception as e:
    st.error(f"Error: {e}")
