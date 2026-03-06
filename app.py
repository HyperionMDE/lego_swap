import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de página básica
st.set_page_config(page_title="ALE! Swap v10", layout="centered")

# 2. URLs (Copia estas líneas con cuidado, están verificadas)
U_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
U_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 3. Función para obtener nombres (Con seguridad total)
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

# --- INICIO DE LA APP ---
st.title("Intercambio ALE! (v10)")

try:
    # Carga de datos
    inv = pd.read_csv(U_INV).fillna("")
    des = pd.read_csv(U_DES).fillna("")
    
    # Limpieza de nombres de columnas
    inv.columns = [c.strip() for c in inv.columns]
    des.columns = [c.strip() for c in des.columns]
    
    # Crear diccionario de nombres
    n_map = {}
    ids_unicos = pd.concat([inv["SetID"], des["SetID"]]).unique()
    for sid in ids_unicos:
        n_map[str(sid).strip()] = get_name(sid)

    # SECCIÓN 1: INVENTARIO
    st.header("📦 Sets Disponibles")
    for _, fila in inv.iterrows():
        sid = str(fila['SetID']).strip()
        st.write(f"• **{fila['Socio']}** tiene el {sid} ({n_map.get(sid)})")

    st.write("---")

    # SECCIÓN 2: DESEOS
    st.header("❤️ Sets Buscados")
    for _, fila in des.iterrows():
        sid = str(fila['SetID']).strip()
        st.write(f"• **{fila['Socio']}** busca el {sid} ({n_map.get(sid)})")

    st.write("---")

    # SECCIÓN 3: CÁLCULO DE INTERCAMBIO (Priorizado)
    st.header("🚀 Resultado del Intercambio")
    
    G = nx.DiGraph()
    for _, rd in des.iterrows():
        pide, sid = str(rd["Socio"]).strip(), str(rd["SetID"]).strip()
        duenos = inv[inv["SetID"].astype(str).str.strip() == sid]
        for _, ri in duenos.iterrows():
            da = str(ri["Socio"]).strip()
            if pide != da:
                G.add_edge(da, pide, sid=sid)
    
    ciclos = list(nx.simple_cycles(G))
    if not ciclos:
        st.info("No hay intercambios circulares posibles todavía.")
    else:
        # PRIORIZACIÓN: Elegimos el ciclo más largo (más socios felices)
        mejor = max(ciclos, key=len)
        st.success(f"¡Propuesta óptima para {len(mejor)} socios!")
        
        for j in range(len(mejor)):
            u1, u2 = mejor[j], mejor[(j+1)%len(mejor)]
            item = G[u1][u2]["sid"]
            st.write(f"✅ **{u1}** entrega **{item}** ({n_map.get(item)}) a **{u2}**")

except Exception as e:
    st.error(f"Error en los datos: {e}")

if st.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.rerun()
