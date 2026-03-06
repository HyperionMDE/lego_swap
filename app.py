import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de Página
st.set_page_config(page_title="ALE! Swap v6.0", layout="wide")

URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9l (URL_DES)
# Nota: He mantenido tus URLs originales de las versiones anteriores

# 2. Motor de Nombres (Blindado)
@st.cache_data(ttl=3600)
def get_lego_name(sid):
    s = str(sid).strip()
    # Diccionario local prioritario
    manual = {
        "10316": "Rivendell",
        "75192": "Millennium Falcon UCS",
        "21333": "The Starry Night (Van Gogh)"
    }
    if s in manual: return manual[s]
    try:
        url = f"https://rebrickable.com/api/v3/lego/sets/{s}-1/"
        headers = {"Authorization": "key 9d7b97368d90473950669f64e2621453"}
        r = requests.get(url, headers=headers, timeout=2)
        if r.status_code == 200: return r.json().get('name', f"Set {s}")
    except: pass
    return f"Lego {s}"

# 3. Encabezado ALE!
st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=60)
st.title("Sistema de Intercambio ALE!")
st.write("---")

try:
    # Carga y limpieza
    inv = pd.read_csv(URL_INV).fillna("")
    des = pd.read_csv(URL_DES).fillna("")
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]
    
    # Aplicar nombres a las tablas
    inv["Nombre"] = inv["SetID"].astype(str).apply(get_lego_name)
    des["Nombre"] = des["SetID"].astype(str).apply(get_lego_name)

    # VISTAS EN TABLAS (Usamos st.table para evitar el error rosa de memoria)
    tab1, tab2, tab3 = st.tabs(["📦 Inventario Disponible", "❤️ Lista de Deseos", "🚀 Resultado del Cambio"])

    with tab1:
        st.table(inv[["Socio", "SetID", "Nombre"]])

    with tab2:
        st.table(des[["Socio", "SetID", "Nombre"]])

    with tab3:
        st.subheader("Propuesta de Intercambio Optimizada")
        
        G = nx.DiGraph()
        n_map = pd.concat([inv, des]).set_index("SetID")["Nombre"].to_dict()
        
        for _, rd in des.iterrows():
            pide, sid = str(rd["Socio"]).strip(), str(rd["SetID"]).strip()
            duenos = inv[inv["SetID"].astype(str).str.strip() == sid]
            for _, ri in duenos.iterrows():
                da = str(ri["Socio"]).strip()
                if pide != da:
                    G.add_edge(da, pide, sid=sid)
        
        ciclos = list(nx.simple_cycles(G))
        
        if not ciclos:
            st.info("No hay ciclos de intercambio detectados actualmente.")
        else:
            # PRIORIZACIÓN: Elegimos el ciclo más largo (más socios contentos)
            mejor_ciclo = max(ciclos, key=len)
            
            st.success(f"Se ha priorizado un intercambio de {len(mejor_ciclo)} pasos:")
            
            # Formateamos el resultado como una tabla limpia
            res_data = []
            for j in range(len(mejor_ciclo)):
                u1 = mejor_ciclo[j]
                u2 = mejor_ciclo[(j+1)%len(mejor_ciclo)]
                sid = G[u1][u2]["sid"]
                res_data.append({
                    "De (Socio)": u1,
                    "Entrega": f"{sid} - {n_map.get(sid)}",
                    "A (Socio)": u2
                })
            
            st.table(pd.DataFrame(res_data))
            st.warning("⚠️ Este es el intercambio óptimo detectado. Realiza el contacto entre socios para confirmar.")

except Exception as e:
    st.error(f"Error en los datos: {e}")

# Botón discreto al final
if st.button("🔄 Refrescar Datos"):
    st.cache_data.clear()
    st.rerun()
