import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración básica (Sin funciones modernas)
st.set_page_config(page_title="ALE! Swap v14", layout="wide")

# 2. URLs protegidas contra errores de sintaxis
U_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
U_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9l (URL_DES)" # Corregido abajo para evitar el error de tu captura

# Re-definición limpia de URLs para evitar el SyntaxError de la captura 10
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

@st.cache(ttl=3600) # Usamos st.cache antiguo para máxima compatibilidad
def get_lego_name(sid):
    s = str(sid).strip()
    manual = {"10316": "Rivendell", "75192": "Millennium Falcon UCS", "21333": "The Starry Night"}
    if s in manual: return manual[s]
    try:
        r = requests.get(f"https://rebrickable.com/api/v3/lego/sets/{s}-1/", 
                         headers={"Authorization": "key 9d7b97368d90473950669f64e2621453"}, timeout=2)
        if r.status_code == 200: return r.json().get('name', f"Set {s}")
    except: pass
    return f"Lego {s}"

def pintar_tabla_manual(df):
    # Creamos la tabla usando Markdown, que es inmune al error "LargeUtf8"
    header = "| " + " | ".join(df.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join([str(val) for val in row]) + " |")
    return "\n".join([header, separator] + rows)

st.title("Plataforma de Intercambio ALE!")

try:
    # Carga automática de datos (Sin botones)
    inv = pd.read_csv(URL_INV).fillna("").astype(str)
    des = pd.read_csv(URL_DES).fillna("").astype(str)
    
    # Limpieza de columnas
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]

    # Añadir nombres
    inv["Nombre"] = inv["SetID"].apply(get_lego_name)
    des["Nombre"] = des["SetID"].apply(get_lego_name)

    # SECCIÓN 1: INVENTARIO
    st.subheader("📦 Inventario de Socios")
    st.markdown(pintar_tabla_manual(inv[["Socio", "SetID", "Nombre"]]))

    # SECCIÓN 2: DESEOS
    st.subheader("❤️ Lista de Deseos")
    st.markdown(pintar_tabla_manual(des[["Socio", "SetID", "Nombre"]]))

    # SECCIÓN 3: CÁLCULO
    st.subheader("🚀 Resultado Óptimo de Intercambio")
    G = nx.DiGraph()
    n_map = pd.concat([inv, des]).set_index("SetID")["Nombre"].to_dict()
    
    for _, rd in des.iterrows():
        pide, sid = rd["Socio"].strip(), rd["SetID"].strip()
        duenos = inv[inv["SetID"].str.strip() == sid]
        for _, ri in duenos.iterrows():
            da = ri["Socio"].strip()
            if pide != da: G.add_edge(da, pide, sid=sid)
    
    ciclos = list(nx.simple_cycles(G))
    if not ciclos:
        st.info("No se han encontrado ciclos de intercambio todavía.")
    else:
        mejor = max(ciclos, key=len)
        res_list = []
        for j in range(len(mejor)):
            u1, u2 = mejor[j], mejor[(j+1)%len(mejor)]
            sid = G[u1][u2]["sid"]
            res_list.append({"Da": u1, "Set": f"{sid} ({n_map.get(sid)})", "Recibe": u2})
        
        st.markdown(pintar_tabla_manual(pd.DataFrame(res_list)))

except Exception as e:
    st.error(f"Error de carga: {e}")
