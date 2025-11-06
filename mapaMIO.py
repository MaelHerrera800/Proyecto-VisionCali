# mapaMIO.py
import pandas as pd
import folium
import numpy as np

# ===============================================================
# 📍 COORDENADAS DE ESTACIONES MIO
# ===============================================================
ESTACIONES_MIO = {
    "Terminal Paso del Comercio": (3.4886563335118, -76.493596701742),
    "Terminal Menga": (3.489476, -76.509063),
    "Terminal Andrés Sanín": (3.443941, -76.482916),
    "Terminal Simón Bolívar": (3.4325, -76.5325),
    "Terminal Aguablanca": (3.4892, -76.4558),
    "Centro": (3.4483534462224, -76.530063504386),
    "Plaza de Caycedo": (3.4482, -76.5310),
    "Santa Rosa": (3.4479, -76.5320),
    "Universidades": (3.367013, -76.529109),
    "Univalle": (3.370903, -76.536686),
    "Manzana del Saber": (3.435000, -76.540833),
    "Meléndez": (3.377079, -76.542809),
    "Estadio": (3.431926, -76.543083),
    "Unidad Deportiva": (3.414278, -76.548206),
    "Versalles": (3.461210, -76.527040),
    "Las Américas": (3.462000, -76.526000),
    "Torre de Cali": (3.456822, -76.530251),
    "Flora Industrial": (3.478416, -76.502034),
    "Chiminangos": (3.481719, -76.497999),
    "San Bosco": (3.446000, -76.532000),
    "Salomia": (3.4875, -76.5075),
    "Popular": (3.4840, -76.4980),
    "Manzanares": (3.4760, -76.5060),
    "Fátima": (3.4560, -76.5040),
    "Piloto": (3.4440, -76.5180),
    "San Nicolás": (3.4520, -76.4920),
    "Río Cali": (3.4300, -76.5300),
    "Plaza de Toros": (3.4250, -76.5600),
    "Refugio": (3.4015, -76.5190),
    "Capri": (3.388056, -76.545000),
    "Álamos": (3.4910, -76.5070),
    "Vipasa": (3.5170, -76.4790),
    "Prados del Norte": (3.5030, -76.5180),
    "Calipso": (3.4650, -76.4980),
    "Villa del Lago": (3.5130, -76.4660),
    "Lleras Restrepo": (3.4355, -76.5185),
    "Ciudad Modelo": (3.4560, -76.4800),
    "Villa del Sur": (3.3950, -76.5200),
    "Mariano Ramos": (3.4250, -76.5400),
    "Cañaverales": (3.4110, -76.4950),
}

# ===============================================================
# 📊 CARGAR DATOS PREDICHOS DEL MODELO
# ===============================================================
try:
    df_pred = pd.read_excel("predicciones_mio.xlsx")
except FileNotFoundError:
    raise FileNotFoundError("⚠️ No se encontró el archivo 'predicciones_mio.xlsx'. Ejecuta primero modelo_predictivo.py")

# Renombrar columnas para mantener consistencia
df_pred.rename(columns={
    "Fecha": "Fecha Predicha",
    "Personas_Predichas": "Personas Predichas",
    "Prob_Colapso": "Probabilidad Colapso",
    "Estado_Previsto": "Estado Futuro"
}, inplace=True)

# ===============================================================
# 🌍 AGREGAR COORDENADAS A CADA TERMINAL
# ===============================================================
df_coords = pd.DataFrame.from_dict(ESTACIONES_MIO, orient="index", columns=["Latitud", "Longitud"]).reset_index()
df_coords.rename(columns={"index": "Terminal"}, inplace=True)
df_mapa = pd.merge(df_pred, df_coords, on="Terminal", how="left")

# 🔹 Mostrar todas las estaciones (no filtrar por fecha)
df_mapa_ultima = df_mapa.copy()
print(f"📊 Total de estaciones visualizadas: {len(df_mapa_ultima)}")

# ===============================================================
# 🗺️ FUNCIÓN PARA GENERAR MAPA DE PREDICCIONES
# ===============================================================
def generar_mapa_predicciones(df):
    mapa = folium.Map(location=[3.4516, -76.5320], zoom_start=12, tiles="CartoDB positron")

    for _, fila in df.iterrows():
        if fila["Estado Futuro"] == "Colapsará":
            color = "red"
        elif fila["Estado Futuro"] == "Riesgo de Colapso":
            color = "orange"
        else:
            color = "green"

        popup_html = f"""
        <b>{fila['Terminal']}</b><br>
        Estado futuro: <b style='color:{color}'>{fila['Estado Futuro']}</b><br>
        Personas predichas: {fila['Personas Predichas']}<br>
        Capacidad máxima: {fila['Capacidad Máxima']}<br>
        Probabilidad de colapso: {(fila['Probabilidad Colapso'] * 100):.1f}%<br>
        Fecha predicha: {pd.to_datetime(fila['Fecha Predicha']).date()}
        """

        if not np.isnan(fila["Latitud"]) and not np.isnan(fila["Longitud"]):
            folium.CircleMarker(
                location=[fila["Latitud"], fila["Longitud"]],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(mapa)

    # ---------------------------------------------------------------
    # 🧭 AGREGAR LEYENDA
    # ---------------------------------------------------------------
    legend_html = """
    <div style="
        position: fixed; 
        bottom: 30px; left: 30px; width: 210px; height: 130px; 
        background-color: white; border:2px solid grey; z-index:9999;
        font-size:14px; border-radius:10px; padding:10px;">
        <b>🧭 Leyenda del mapa MIO</b><br>
        <i style="background:green; width:15px; height:15px; float:left; margin-right:8px;"></i> Estable<br>
        <i style="background:orange; width:15px; height:15px; float:left; margin-right:8px;"></i> Riesgo de colapso<br>
        <i style="background:red; width:15px; height:15px; float:left; margin-right:8px;"></i> Colapsará<br>
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(legend_html))

    return mapa

# ===============================================================
# 💾 GUARDAR MAPA COMO HTML
# ===============================================================
mapa_pred = generar_mapa_predicciones(df_mapa_ultima)
mapa_pred.save("mapa_predicciones_mio.html")
print("✅ Mapa de predicciones generado: mapa_predicciones_mio.html")

if __name__ == "__main__":
    pass
