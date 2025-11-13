import pandas as pd
import folium
import numpy as np
import webbrowser

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
# 📊 CARGAR PREDICCIONES DEL MODELO
# ===============================================================
try:
    df_pred = pd.read_excel("predicciones_mio.xlsx")
except FileNotFoundError:
    raise FileNotFoundError("⚠️ No se encontró el archivo 'predicciones_mio.xlsx'. Ejecuta primero modelo_predictivo.py")

# Renombrar columnas para consistencia
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

df_mapa["Fecha Predicha"] = pd.to_datetime(df_mapa["Fecha Predicha"])

# ===============================================================
# 📅 FILTRAR SOLO LAS PREDICCIONES DE MAÑANA
# ===============================================================
fechas_ordenadas = sorted(df_mapa["Fecha Predicha"].dt.date.unique())
fecha_max = max(fechas_ordenadas)
fecha_maniana = fecha_max  # Mostrar el último día disponible

df_mapa_maniana = df_mapa[df_mapa["Fecha Predicha"].dt.date == fecha_maniana]

print(f"📅 Mostrando predicciones para: {fecha_maniana}")
print(f"🚌 Total de registros: {len(df_mapa_maniana)}")

# ===============================================================
# 📊 AGRUPAR POR TERMINAL Y RESUMIR FRANJAS
# ===============================================================
resumen_estaciones = []

for terminal, grupo in df_mapa_maniana.groupby("Terminal"):
    franjas_colapsadas = grupo.loc[
        grupo["Estado Futuro"].str.contains("Colapsará", case=False, na=False),
        "Franja Horaria"
    ].tolist()
    franjas_estables = grupo.loc[
        grupo["Estado Futuro"].str.contains("Estable", case=False, na=False),
        "Franja Horaria"
    ].tolist()

    resumen_estaciones.append({
        "Terminal": terminal,
        "Latitud": grupo["Latitud"].iloc[0],
        "Longitud": grupo["Longitud"].iloc[0],
        "Fecha": fecha_maniana,
        "Colapsadas": franjas_colapsadas,
        "Estables": franjas_estables
    })

df_resumen = pd.DataFrame(resumen_estaciones)

# ===============================================================
# 🗺️ CREAR MAPA
# ===============================================================
mapa = folium.Map(location=[3.4516, -76.5320], zoom_start=12, tiles="CartoDB positron")

for _, fila in df_resumen.iterrows():
    popup_html = f"""
    <b>{fila['Terminal']}</b><br>
    Fecha: {fila['Fecha']}<br><br>
    <b>Franja(s) colapsadas:</b><br>{', '.join(fila['Colapsadas']) if fila['Colapsadas'] else 'Ninguna'}<br><br>
    <b>Franja(s) estables:</b><br>{', '.join(fila['Estables']) if fila['Estables'] else 'Ninguna'}
    """

    if not np.isnan(fila["Latitud"]) and not np.isnan(fila["Longitud"]):
        folium.CircleMarker(
            location=[fila["Latitud"], fila["Longitud"]],
            radius=7,
            color="yellow",
            fill=True,
            fill_color="yellow",
            popup=folium.Popup(popup_html, max_width=350)
        ).add_to(mapa)

# ===============================================================
# 💾 GUARDAR Y ABRIR MAPA
# ===============================================================
mapa.save("mapa_predicciones_mio_mañana.html")
print("✅ Mapa generado: mapa_predicciones_mio_mañana.html")
webbrowser.open("mapa_predicciones_mio_mañana.html")
