import streamlit as st
import pandas as pd
import networkx as nx
import requests

# 1. Configuración de Marca (Identidad Visual ALE!)
st.set_page_config(page_title="ALE! Swap", layout="wide", page_icon="🏗️")

# URLs de tus Google Sheets
URL_INV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=1446180612&single=true&output=csv"
URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgUeWKSvV8S20NodEnV3RMVQtE3xQk84NgDEnSpBd9knQY8MxyrcOgCPO9lQSHlmrPjLecm5NuUiAA/pub?gid=119622631&single=true&output=csv"

# 2. Motor de Identificación de Sets (Recupera los nombres reales)
@st.cache_data(ttl=3600)
def identificar_set(set_id):
    sid = str(set_id).strip()
    # Diccionario de seguridad para carga instantánea de tus fotos
    favoritos = {
        "10316": "Rivendell",
        "75192": "Millennium Falcon UCS",
        "21333": "The Starry Night (Van Gogh)"
    }
    if sid in favoritos:
        return favoritos[sid]
    
    try:
        # Consulta a API externa
        search = sid if "-" in sid else f"{sid}-1"
        url = f"https://rebrickable.com/api/v3/lego/sets/{search}/"
        headers = {"Authorization": "key 9d7b97368d90473950669f64e2621453"}
        response = requests.get(url, headers=headers, timeout=3)
        if response.status_code == 200:
            return response.json().get('name', f"Set {sid}")
    except:
        pass
    return f"Lego {sid}"

# 3. Carga y Procesamiento de Datos
def cargar_inventarios():
    try:
        inv = pd.read_csv(URL_INV).fillna("")
        des = pd.read_csv(URL_DES).fillna("")
        # Limpiar espacios en los nombres de las columnas
        inv.columns = [c.strip() for c in inv.columns]
        des.columns = [c.strip() for c in des.columns]
        
        # Aplicar el motor de nombres
        inv["Nombre"] = inv["SetID"].astype(str).apply(identificar_set)
        des["Nombre"] = des["SetID"].astype(str).apply(identificar_set)
        
        return inv, des
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 4. Diseño de la Interfaz (Estética ALE!)
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/24/LEGO_logo.svg", width=80)
with col2:
    st.title("Plataforma de Intercambio ALE!")
    st.caption("Asociación Cultural de Aficionados a LEGO® de España")

with st.sidebar:
    st.markdown("### ⚙️ Administración")
    if st.button("🔄 Refrescar Datos y Nombres"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.info("Utiliza este panel para forzar la lectura de nuevos sets del Excel.")

inv_data, des_data = cargar_inventarios()

# Pestañas con Iconos y Colores
tab_inv, tab_des, tab_calc = st.tabs(["📦 Inventario ALE!", "❤️ Lista de Deseos", "🚀 Calcular Cambios"])

with tab_inv:
    st.subheader("Sets Disponibles para Intercambio")
    if not inv_data.empty:
        # st.dataframe es seguro ahora que hemos limpiado el código
        st.dataframe(inv_data[["Socio", "SetID", "Nombre"]], use_container_width=True, hide_index=True)

with tab_des:
    st.subheader("Deseos de los Socios")
    if not des_data.empty:
        st.dataframe(des_data[["Socio", "SetID", "Nombre"]], use_container_width=True, hide_index=True)

with tab_calc:
    st.subheader("Algoritmo de Intercambio Circular")
    if st.button("🔍 Buscar Combinaciones"):
        G = nx.DiGraph()
        nombres_global = pd.concat([inv_data, des_data]).set_index("SetID")["Nombre"].to_dict()
        
        for _, fila_d in des_data.iterrows():
            pide = str(fila_d["Socio"]).strip()
            item = str(fila_d["SetID"]).strip()
            # Buscar quién lo tiene
            poseedores = inv_data[inv_data["SetID"].astype(str).str.strip() == item]
            for _, fila_i in poseedores.iterrows():
                donante = str(fila_i["Socio"]).strip()
                if pide != donante:
                    G.add_edge(donante, pide, set_id=item)
        
        ciclos = list(nx.simple_cycles(G))
        if not ciclos:
            st.warning("Aún no existen ciclos de cambio completos. ¡Prueba a añadir más deseos!")
        else:
            st.success(f"¡Se han encontrado {len(ciclos)} propuestas de cambio circular!")
            for i, ciclo in enumerate(ciclos):
                with st.expander(f"PROPUESTA DE CAMBIO #{i+1} ({len(ciclo)} participantes)"):
                    for j in range(len(ciclo)):
                        u1 = ciclo[j]
                        u2 = ciclo[(j+1)%len(ciclo)]
                        set_id = G[u1][u2]["set_id"]
                        st.write(f"🎁 **{u1}** entrega **{set_id}** ({nombres_global.get(set_id)}) a **{u2}**")
