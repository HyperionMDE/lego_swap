import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de página
st.set_page_config(page_title="ALE! Swap v16", layout="wide")

# URLs de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 2. Motor de Datos con fallback de imagen mejorado
@st.cache(ttl=3600, show_spinner=False)
def get_lego_info(sid):
    s = str(sid).strip()
    # Nombre por defecto
    info = {"name": f"Set {s}", "img": f"https://images.brickset.com/sets/images/{s}-1.jpg"}
    
    # Intentamos Rebrickable para el nombre real, pero si falla, ya tenemos la imagen de Brickset
    try:
        r = requests.get(f"https://rebrickable.com/api/v3/lego/sets/{s}-1/", 
                         headers={"Authorization": "key 9d7b97368d90473950669f64e2621453"}, timeout=1)
        if r.status_code == 200:
            data = r.json()
            info["name"] = data.get('name', info["name"])
            # Solo actualizamos la imagen si Rebrickable nos da una válida
            if data.get('set_img_url'):
                info["img"] = data.get('set_img_url')
    except:
        pass
    return info

# 3. Pintar tabla con el estilo verde que te gusta
def pintar_tabla_estetica(df):
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
                # Añadimos un estilo para que la imagen no falle y se vea bien
                html += f'<td style="padding: 5px; border: 1px solid #ddd; text-align: center;"><img src="{val}" width="80" style="border-radius: 4px; box-shadow: 1px 1px 5px rgba(0,0,0,0.1);" onerror="this.src=\'https://via.placeholder.com/80?text=LEGO\'"></td>'
            else:
                html += f'<td style="padding: 12px; border: 1px solid #ddd;">{val}</td>'
        html += '</tr>'
    html += '</table>'
    return html

# --- PROCESO ---
st.title("Plataforma de Intercambio ALE! (Visual)")

try:
    # Carga automática
    inv = pd.read_csv(URL_INV).fillna("").astype(str)
    des = pd.read_csv(URL_DES).fillna("").astype(str)
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]

    # Generar columnas de Nombre e Imagen
    for df in [inv, des]:
        nombres, fotos = [], []
        for sid in df["SetID"]:
            res = get_lego_info(sid)
            nombres.append(res["name"])
            fotos.append(res["img"])
        df["Nombre"] = nombres
        df["Imagen"] = fotos

    # Mostrar Tablas con tu diseño
    st.header("📦 Inventario Disponible")
    st.markdown(pintar_tabla_estetica(inv[["Socio", "SetID", "Nombre", "Imagen"]]), unsafe_allow_html=True)

    st.header("❤️ Lista de Deseos")
    st.markdown(pintar_tabla_estetica(des[["Socio", "SetID", "Nombre", "Imagen"]]), unsafe_allow_html=True)

    # Cálculo de ciclos
    st.header("🚀 Resultado Óptimo")
    G = nx.DiGraph()
    for _, rd in des.iterrows():
        pide, sid = rd["Socio"].strip(), rd["SetID"].strip()
        duenos = inv[inv["SetID"].str.strip() == sid]
        for _, ri in duenos.iterrows():
            da = ri["Socio"].strip()
            if pide != da:
                G.add_edge(da, pide, sid=sid)
    
    ciclos = list(nx.simple_cycles(G))
    if ciclos:
        mejor = max(ciclos, key=len)
        res_list = []
        for j in range(len(mejor)):
            u1, u2 = mejor[j], mejor[(j+1)%len(mejor)]
            sid = G[u1][u2]["sid"]
            info = get_lego_info(sid)
            res_list.append({"Socio Entrega": u1, "Set": f"{sid} - {info['name']}", "Imagen": info['img'], "Socio Recibe": u2})
        st.markdown(pintar_tabla_estetica(pd.DataFrame(res_list)), unsafe_allow_html=True)
    else:
        st.info("No hay intercambios posibles en este momento.")

except Exception as e:
    st.error(f"Error de sistema: {e}")
