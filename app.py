import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de página
st.set_page_config(page_title="ALE! Swap v7.0", layout="wide")

# 2. URLs de datos
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 3. Motor de Nombres (Blindado contra fallos de red)
@st.cache_data(ttl=3600)
def fetch_name(sid):
    s = str(sid).strip()
    favs = {"10316": "Rivendell", "75192": "Millennium Falcon UCS", "21333": "The Starry Night"}
    if s in favs: return favs[s]
    try:
        r = requests.get(f"https://rebrickable.com/api/v3/lego/sets/{s}-1/", 
                         headers={"Authorization": "key 9d7b97368d90473950669f64e2621453"}, timeout=2)
        if r.status_code == 200: return r.json().get('name', f"Set {s}")
    except: pass
    return f"Lego {s}"

# 4. Cabecera
st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=60)
st.title("Sistema de Intercambio ALE!")
st.write("---")

try:
    # Carga de datos
    inv = pd.read_csv(URL_INV).fillna("")
    des = pd.read_csv(URL_DES).fillna("")
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]
    
    # Procesar nombres
    inv["Nombre"] = inv["SetID"].astype(str).apply(fetch_name)
    des["Nombre"] = des["SetID"].astype(str).apply(fetch_name)

    # Tabs de visualización
    t1, t2, t3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Resultado Óptimo"])

    with t1:
        st.subheader("Sets Disponibles")
        st.table(inv[["Socio", "SetID", "Nombre"]])

    with t2:
        st.subheader("Lista de Deseos")
        st.table(des[["Socio", "SetID", "Nombre"]])

    with t3:
        # Lógica de Intercambio
        G = nx.DiGraph()
        n_map = pd.concat([inv, des]).set_index("SetID")["Nombre"].to_dict()
        
        for _, rd in des.iterrows():
            p, s = str(rd["Socio"]).strip(), str(rd["SetID"]).strip()
            duenos = inv[inv["SetID"].astype(str).str.strip() == s]
            for _, ri in duenos.iterrows():
                d = str(ri["Socio"]).strip()
                if p != d: G.add_edge(d, p, sid=s)
        
        ciclos = list(nx.simple_cycles(G))
        
        if not ciclos:
            st.info("No hay ciclos de intercambio posibles ahora mismo.")
        else:
            # PRIORIZACIÓN: Elegimos el ciclo que involucra a más socios
            mejor = max(ciclos, key=len)
            st.success(f"¡Intercambio Optimizado Encontrado! ({len(mejor)} participantes)")
            
            # Construcción de la tabla de resultados
            res = []
            for j in range(len(mejor)):
                u1, u2 = mejor[j], mejor[(j+1)%len(mejor)]
                sid = G[u1][u2]["sid"]
                res.append({"Socio Donante": u1, "Entrega Set": f"{sid} - {n_map.get(sid)}", "Para Socio": u2})
            
            st.table(pd.DataFrame(res))

except Exception as e:
    st.error(f"Error de ejecución: {e}")

if st.button("🔄 Refrescar Datos"):
    st.cache_data.clear()
    st.rerun()
