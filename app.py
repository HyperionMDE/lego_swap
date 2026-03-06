import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de página
st.set_page_config(page_title="ALE! Swap v8.0", layout="wide")

# 2. URLs corregidas (Sin errores de sintaxis)
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 3. Motor de nombres (Con diccionario de seguridad para Rivendell)
@st.cache_data(ttl=3600)
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

# 4. Interfaz centrada sin barra lateral
st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=60)
st.title("Sistema de Intercambio ALE!")

try:
    # Carga y limpieza de datos
    df_i = pd.read_csv(URL_INV).fillna("")
    df_d = pd.read_csv(URL_DES).fillna("")
    df_i.columns = [c.strip() for c in df_i.columns]
    df_d.columns = [c.strip() for c in df_d.columns]
    
    # Procesar nombres (Crucial para que aparezcan en las tablas)
    df_i["Nombre"] = df_i["SetID"].astype(str).apply(get_lego_name)
    df_d["Nombre"] = df_d["SetID"].astype(str).apply(get_lego_name)

    # Tabs
    t1, t2, t3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Resultado Óptimo"])

    with t1:
        st.subheader("Sets Disponibles para Cambio")
        # Usamos st.table para evitar el error "LargeUtf8" definitivamente
        st.table(df_i[["Socio", "SetID", "Nombre"]])

    with t2:
        st.subheader("Lista de Deseos de los Socios")
        st.table(df_d[["Socio", "SetID", "Nombre"]])

    with t3:
        st.subheader("Propuesta de Intercambio Seleccionada")
        
        G = nx.DiGraph()
        n_map = pd.concat([df_i, df_d]).set_index("SetID")["Nombre"].to_dict()
        
        for _, rd in df_d.iterrows():
            p, s = str(rd["Socio"]).strip(), str(rd["SetID"]).strip()
            duenos = df_i[df_i["SetID"].astype(str).str.strip() == s]
            for _, ri in duenos.iterrows():
                d = str(ri["Socio"]).strip()
                if p != d: G.add_edge(d, p, sid=s)
        
        ciclos = list(nx.simple_cycles(G))
        if not ciclos:
            st.info("No se han encontrado ciclos de intercambio completos.")
        else:
            # Priorizamos el intercambio que involucre a más socios
            mejor_opcion = max(ciclos, key=len)
            st.success(f"¡Éxito! Intercambio de {len(mejor_opcion)} pasos encontrado.")
            
            res_list = []
            for j in range(len(mejor_opcion)):
                u_da = mejor_opcion[j]
                u_recibe = mejor_opcion[(j+1)%len(mejor_opcion)]
                item_id = G[u_da][u_recibe]["sid"]
                res_list.append({
                    "Socio que DA": u_da,
                    "Set que ENTREGA": f"{item_id} - {n_map.get(item_id)}",
                    "Socio que RECIBE": u_recibe
                })
            
            st.table(pd.DataFrame(res_list))

except Exception as e:
    st.error(f"Error crítico: {e}")

# Botón de actualización
if st.button("🔄 Forzar Recarga"):
    st.cache_data.clear()
    st.rerun()
