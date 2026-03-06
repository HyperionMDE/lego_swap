import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de página ultra-compatible
st.set_page_config(page_title="ALE! Swap v13", layout="wide")

# 2. URLs de Google Sheets (Verificadas)
U_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
U_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 3. Motor de Nombres (Caché inteligente)
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

# 4. Función para pintar tablas sin que Streamlit se rompa
def mostrar_tabla_html(df):
    # Convertimos el DataFrame a HTML puro para evitar el error LargeUtf8
    estilo = """
    <style>
        .mystyle {font-family: sans-serif; border-collapse: collapse; width: 100%;}
        .mystyle td, .mystyle th {border: 1px solid #ddd; padding: 8px;}
        .mystyle tr:nth-child(even){background-color: #f2f2f2;}
        .mystyle th {padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: #2E7D32; color: white;}
    </style>
    """
    html_table = df.to_html(classes='mystyle', index=False, escape=False)
    st.markdown(estilo + html_table, unsafe_allow_html=True)

# --- FLUJO PRINCIPAL (SIN BOTONES) ---
st.title("Plataforma de Intercambio ALE!")

try:
    # Carga de datos
    inv = pd.read_csv(U_INV).fillna("").astype(str)
    des = pd.read_csv(U_DES).fillna("").astype(str)
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]

    # Asignar nombres a los sets
    inv["Nombre"] = inv["SetID"].apply(get_lego_name)
    des["Nombre"] = des["SetID"].apply(get_lego_name)

    # VISTAS DE TABLAS
    st.header("📦 Inventario de Socios")
    mostrar_tabla_html(inv[["Socio", "SetID", "Nombre"]])

    st.header("❤️ Lista de Deseos")
    mostrar_tabla_html(des[["Socio", "SetID", "Nombre"]])

    # CÁLCULO DE INTERCAMBIO
    st.header("🚀 Resultado Óptimo")
    G = nx.DiGraph()
    n_map = pd.concat([inv, des]).drop_duplicates('SetID').set_index("SetID")["Nombre"].to_dict()
    
    for _, rd in des.iterrows():
        pide, sid = rd["Socio"].strip(), rd["SetID"].strip()
        duenos = inv[inv["SetID"].str.strip() == sid]
        for _, ri in duenos.iterrows():
            da = ri["Socio"].strip()
            if pide != da:
                G.add_edge(da, pide, sid=sid)
    
    ciclos = list(nx.simple_cycles(G))
    if not ciclos:
        st.info("No hay ciclos de intercambio completos detectados.")
    else:
        mejor = max(ciclos, key=len)
        res_list = []
        for j in range(len(mejor)):
            u1, u2 = mejor[j], mejor[(j+1)%len(mejor)]
            sid = G[u1][u2]["sid"]
            res_list.append({
                "Socio Entrega": u1,
                "Set LEGO": f"{sid} - {n_map.get(sid, 'Set')}",
                "Socio Recibe": u2
            })
        
        mostrar_tabla_html(pd.DataFrame(res_list))

except Exception as e:
    st.error(f"Error crítico de ejecución: {e}")
