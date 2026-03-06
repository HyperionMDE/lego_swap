import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de página
st.set_page_config(page_title="ALE! Swap v12", layout="wide")

# 2. URLs (Verificadas línea por línea)
U_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
U_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 3. Motor de Nombres (Caché de 1 hora)
@st.cache_data(ttl=3600)
def get_lego_name(sid):
    s = str(sid).strip()
    favs = {"10316": "Rivendell", "75192": "Millennium Falcon UCS", "21333": "The Starry Night"}
    if s in favs: return favs[s]
    try:
        r = requests.get(f"https://rebrickable.com/api/v3/lego/sets/{s}-1/", 
                         headers={"Authorization": "key 9d7b97368d90473950669f64e2621453"}, timeout=2)
        if r.status_code == 200: return r.json().get('name', f"Set {s}")
    except: pass
    return f"Lego {s}"

# --- PROCESAMIENTO ---
st.title("Plataforma de Intercambio ALE!")

try:
    # Carga silenciosa (sin botones)
    inv = pd.read_csv(U_INV).fillna("").astype(str)
    des = pd.read_csv(U_DES).fillna("").astype(str)
    
    # Limpiar espacios en nombres de columnas
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]

    # Convertir SetID a nombres ANTES de mostrar
    inv["Nombre"] = inv["SetID"].apply(get_lego_name)
    des["Nombre"] = des["SetID"].apply(get_lego_name)

    # VISTAS (Convertimos a tabla estática para matar el error LargeUtf8)
    st.header("📦 Inventario de Socios")
    st.table(inv[["Socio", "SetID", "Nombre"]])

    st.header("❤️ Lista de Deseos")
    st.table(des[["Socio", "SetID", "Nombre"]])

    # CÁLCULO DE CAMBIO
    st.header("🚀 Intercambio Sugerido")
    G = nx.DiGraph()
    n_map = pd.concat([inv, des]).set_index("SetID")["Nombre"].to_dict()
    
    for _, rd in des.iterrows():
        pide, sid = rd["Socio"].strip(), rd["SetID"].strip()
        duenos = inv[inv["SetID"].str.strip() == sid]
        for _, ri in duenos.iterrows():
            da = ri["Socio"].strip()
            if pide != da:
                G.add_edge(da, pide, sid=sid)
    
    ciclos = list(nx.simple_cycles(G))
    if not ciclos:
        st.info("No hay combinaciones circulares disponibles con los datos actuales.")
    else:
        # Priorizar el ciclo más largo
        mejor = max(ciclos, key=len)
        res_list = []
        for j in range(len(mejor)):
            u1, u2 = mejor[j], mejor[(j+1)%len(mejor)]
            sid = G[u1][u2]["sid"]
            res_list.append({
                "Entrega (Socio)": u1,
                "Set": f"{sid} - {n_map.get(sid)}",
                "Recibe (Socio)": u2
            })
        
        # Resultado final en tabla también
        st.table(pd.DataFrame(res_list))

except Exception as e:
    st.error(f"Error de sistema: {e}")
