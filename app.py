import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de página
st.set_page_config(page_title="ALE! Swap v15", layout="wide")

# URLs de Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 2. Motor de Datos (Nombres e Imágenes)
@st.cache(ttl=3600)
def get_lego_info(sid):
    s = str(sid).strip()
    # Fallback por si la API falla
    info = {"name": f"Lego {s}", "img": "https://via.placeholder.com/50?text=LEGO"}
    
    # Intentar obtener datos de Rebrickable
    try:
        # Añadimos "-1" que es el estándar de LEGO para sets
        r = requests.get(f"https://rebrickable.com/api/v3/lego/sets/{s}-1/", 
                         headers={"Authorization": "key 9d7b97368d90473950669f64e2621453"}, timeout=2)
        if r.status_code == 200:
            data = r.json()
            info["name"] = data.get('name', info["name"])
            info["img"] = data.get('set_img_url', info["img"])
    except:
        pass
    return info

# 3. Pintar tabla manualmente (Markdown + HTML para las fotos)
def pintar_tabla_visual(df):
    # Encabezados
    html = '<table style="width:100%; border-collapse: collapse; font-family: sans-serif;">'
    html += '<tr style="background-color: #2E7D32; color: white;">'
    for col in df.columns:
        html += f'<th style="padding: 10px; border: 1px solid #ddd;">{col}</th>'
    html += '</tr>'
    
    # Filas
    for _, row in df.iterrows():
        html += '<tr>'
        for col in df.columns:
            val = row[col]
            # Si es la columna de imagen, la renderizamos como <img>
            if col == "Imagen":
                html += f'<td style="padding: 5px; border: 1px solid #ddd; text-align: center;"><img src="{val}" width="60"></td>'
            else:
                html += f'<td style="padding: 10px; border: 1px solid #ddd;">{val}</td>'
        html += '</tr>'
    html += '</table>'
    return html

# --- FLUJO PRINCIPAL ---
st.title("Plataforma de Intercambio ALE! (Visual)")

try:
    # Carga de datos
    inv = pd.read_csv(URL_INV).fillna("").astype(str)
    des = pd.read_csv(URL_DES).fillna("").astype(str)
    
    # Limpiar columnas
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]

    # Procesar información de sets (4 o 5 cifras funciona igual aquí)
    with st.spinner("Buscando fotos de los sets..."):
        # Inventario
        nombres_inv = []
        fotos_inv = []
        for sid in inv["SetID"]:
            info = get_lego_info(sid)
            nombres_inv.append(info["name"])
            fotos_inv.append(info["img"])
        inv["Nombre"] = nombres_inv
        inv["Imagen"] = fotos_inv

        # Deseos
        nombres_des = []
        fotos_des = []
        for sid in des["SetID"]:
            info = get_lego_info(sid)
            nombres_des.append(info["name"])
            fotos_des.append(info["img"])
        des["Nombre"] = nombres_des
        des["Imagen"] = fotos_des

    # MOSTRAR TABLAS
    st.header("📦 Inventario Disponible")
    st.write(pintar_tabla_visual(inv[["Socio", "SetID", "Nombre", "Imagen"]]), unsafe_allow_html=True)

    st.header("❤️ Lista de Deseos")
    st.write(pintar_tabla_visual(des[["Socio", "SetID", "Nombre", "Imagen"]]), unsafe_allow_html=True)

    # CÁLCULO DE INTERCAMBIO
    st.header("🚀 Resultado del Intercambio")
    G = nx.DiGraph()
    for _, rd in des.iterrows():
        pide, sid = rd["Socio"].strip(), rd["SetID"].strip()
        duenos = inv[inv["SetID"].str.strip() == sid]
        for _, ri in duenos.iterrows():
            da = ri["Socio"].strip()
            if pide != da:
                G.add_edge(da, pide, sid=sid)
    
    ciclos = list(nx.simple_cycles(G))
    if not ciclos:
        st.info("Aún no hay coincidencias para un intercambio circular.")
    else:
        mejor = max(ciclos, key=len)
        res_list = []
        for j in range(len(mejor)):
            u1, u2 = mejor[j], mejor[(j+1)%len(mejor)]
            sid = G[u1][u2]["sid"]
            info = get_lego_info(sid)
            res_list.append({
                "Entrega": u1,
                "Set": f"{sid} - {info['name']}",
                "Imagen": info['img'],
                "Recibe": u2
            })
        
        st.write(pintar_tabla_visual(pd.DataFrame(res_list)), unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error al cargar datos o imágenes: {e}")
