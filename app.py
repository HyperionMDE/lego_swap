import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de página
st.set_page_config(page_title="ALE! Swap v9.0", layout="wide")

# 2. URLs (Verificadas sin errores de comillas)
U_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
U_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 3. Motor de Nombres (Con respaldo manual absoluto)
@st.cache_data(ttl=3600)
def get_name(sid):
    s = str(sid).strip()
    favs = {"10316": "Rivendell", "75192": "Millennium Falcon UCS", "21333": "The Starry Night"}
    if s in favs: return favs[s]
    try:
        r = requests.get(f"https://rebrickable.com/api/v3/lego/sets/{s}-1/", 
                         headers={"Authorization": "key 9d7b97368d90473950669f64e2621453"}, timeout=2)
        if r.status_code == 200: return r.json().get('name', f"Set {s}")
    except: pass
    return f"Lego {s}"

# 4. Función de Tabla Infalible (HTML Puro)
def pintar_tabla_html(df):
    # Esto evita el error "LargeUtf8" al no usar st.dataframe ni st.table
    html = df.to_html(index=False, classes='table table-striped', escape=False)
    st.markdown(html, unsafe_allow_html=True)

# --- INTERFAZ ---
st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=60)
st.title("Sistema de Intercambio ALE!")

try:
    inv = pd.read_csv(U_INV).fillna("")
    des = pd.read_csv(U_DES).fillna("")
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]
    
    inv["Nombre"] = inv["SetID"].astype(str).apply(get_name)
    des["Nombre"] = des["SetID"].astype(str).apply(get_name)

    t1, t2, t3 = st.tabs(["📦 Inventario", "❤️ Deseos", "🚀 Resultado Óptimo"])

    with t1:
        st.subheader("Sets Disponibles")
        pintar_tabla_html(inv[["Socio", "SetID", "Nombre"]])

    with t2:
        st.subheader("Sets Buscados")
        pintar_tabla_html(des[["Socio", "SetID", "Nombre"]])

    with t3:
        st.subheader("Intercambio Priorizado")
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
            st.info("No hay ciclos de cambio disponibles.")
        else:
            # Seleccionamos el ciclo más largo
            mejor = max(ciclos, key=len)
            res_data = []
            for j in range(len(mejor)):
                u1, u2 = mejor[j], mejor[(j+1)%len(mejor)]
                sid = G[u1][u2]["sid"]
                res_data.append({"Socio DA": u1, "Set": f"{sid} - {n_map.get(sid)}", "Socio RECIBE": u2})
            
            pintar_tabla_html(pd.DataFrame(res_data))

except Exception as e:
    st.error(f"Fallo técnico: {e}")

if st.button("🔄 Recargar Datos"):
    st.cache_data.clear()
    st.rerun()
