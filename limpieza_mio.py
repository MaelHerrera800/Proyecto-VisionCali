import pandas as pd
import numpy as np
import openpyxl
import calendar 
from datetime import datetime, timedelta

# ============================================================
# 🧩 CLASE OBJETO DE DATOS
# ============================================================
class ObjetoDeDatos:
    def __init__(self, dataframe):
        self.dataframe = dataframe

    def limpiar_datos(self):
        """Limpia los datos y conserva solo la última observación por terminal"""
        df_limpio = self.dataframe.copy()

        # Validar que existan las columnas necesarias
        cols_requeridas = ["Personas Actuales", "Franja Horaria", "Estado"]
        for col in cols_requeridas:
            if col not in df_limpio.columns:
                raise KeyError(f"❌ Falta la columna requerida: {col}")

        # Asegurar tipos de datos correctos
        df_limpio["Personas Actuales"] = df_limpio["Personas Actuales"].astype(float)

        # Rellenar valores faltantes
        mediana_personas = df_limpio["Personas Actuales"].median()
        df_limpio["Personas Actuales"] = df_limpio["Personas Actuales"].fillna(mediana_personas)
        df_limpio["Franja Horaria"] = df_limpio["Franja Horaria"].fillna("Desconocida")
        df_limpio = df_limpio.dropna(subset=["Estado"])

        # Asegurar que la fecha esté sin hora (solo año-mes-día)
        df_limpio["Fecha"] = pd.to_datetime(df_limpio["Fecha"]).dt.date

        # Devolver el DataFrame limpio
        return df_limpio


# ============================================================
# 🏙️ DATOS DE TERMINALES SIMULADOS
# ============================================================
nombres_terminales = [
    "Terminal Paso del Comercio", "Terminal Menga", "Terminal Andrés Sanín",
    "Terminal Simón Bolívar", "Terminal Aguablanca", "Centro", "Plaza de Caycedo",
    "Santa Rosa", "Universidades", "Univalle", "Manzana del Saber", "Meléndez",
    "Estadio", "Unidad Deportiva", "Versalles", "Las Américas", "Torre de Cali",
    "Flora Industrial", "Chiminangos", "San Bosco", "Salomia", "Popular", "Manzanares",
    "Fátima", "Piloto", "San Nicolás", "Río Cali", "Plaza de Toros", "Refugio",
    "Capri", "Álamos", "Vipasa", "Prados del Norte", "Calipso", "Villa del Lago",
    "Lleras Restrepo", "Ciudad Modelo", "Villa del Sur", "Mariano Ramos", "Cañaverales"
]

num_datos = 10000  
np.random.seed(42)

terminales_random = np.random.choice(nombres_terminales, num_datos)
capacidades = np.random.randint(80, 200, num_datos)

# Generar número de personas realista según capacidad
personas = []
for cap in capacidades:
    rand = np.random.random()
    if rand < 0.60:
        personas.append(np.random.randint(int(cap * 0.4), int(cap * 0.8)))
    elif rand < 0.85:
        personas.append(np.random.randint(int(cap * 0.8), int(cap * 1.1)))
    else:
        personas.append(np.random.randint(int(cap * 1.1), int(cap * 1.4)))

personas = np.array(personas)
estado = np.where(personas > capacidades, "Colapsada", "Estable")

# ✅ Fechas entre hace 2 años y hoy (sin hora)
fecha_fin = datetime.now().date()
fecha_inicio = fecha_fin - timedelta(days=730)
fechas_secuenciales = pd.date_range(start=fecha_inicio, end=fecha_fin, periods=num_datos)

FRANJAS_DISPONIBLES = [
    "05:30-09:00", "09:00-12:00", "12:00-15:00",
    "15:00-18:00", "18:00-21:00", "21:00-23:00"
]

df_terminales = pd.DataFrame({
    "Terminal": terminales_random,
    "Capacidad Máxima": capacidades,
    "Personas Actuales": personas,
    "Estado": estado,
    "Franja Horaria": np.random.choice(FRANJAS_DISPONIBLES, num_datos),
    "Fecha": [f.date() for f in fechas_secuenciales]
})

df_terminales["Día de la Semana"] = pd.to_datetime(df_terminales["Fecha"]).dt.day_name()

print(f"✅ Se generaron {len(df_terminales)} registros de simulación.")
print(f"📅 Rango de fechas: {df_terminales['Fecha'].min()} → {df_terminales['Fecha'].max()}")

# Introducir valores nulos (5%)
num_nulls = int(num_datos * 0.05)
indices_nulls_personas = df_terminales.sample(n=num_nulls, random_state=42).index
indices_nulls_franja = df_terminales.sample(n=num_nulls, random_state=43).index
indices_nulls_estado = df_terminales.sample(n=num_nulls, random_state=44).index

df_terminales.loc[indices_nulls_personas, "Personas Actuales"] = None
df_terminales.loc[indices_nulls_franja, "Franja Horaria"] = None
df_terminales.loc[indices_nulls_estado, "Estado"] = None

df_nulos = df_terminales.isnull().astype(int)

# ============================================================
# 🧹 LIMPIAR DATOS
# ============================================================
objeto_datos = ObjetoDeDatos(df_terminales)
df_limpio = objeto_datos.limpiar_datos()

# Crear DataFrame con el último día disponible por terminal
df_ultimo_dia_ejemplo = (
    df_limpio.sort_values("Fecha")
    .groupby("Terminal")
    .tail(1)
)

# ============================================================
# 📤 EXPORTAR A EXCEL
# ============================================================
with pd.ExcelWriter("data_limpia_mio.xlsx", engine="openpyxl") as writer:
    df_terminales.to_excel(writer, sheet_name="Datos Originales", index=False)
    df_nulos.to_excel(writer, sheet_name="Valores Nulos", index=False)
    df_limpio.to_excel(writer, sheet_name="Datos Limpios", index=False)

print("✅ Archivo 'data_limpia_mio.xlsx' generado exitosamente.")

# ============================================================
# 🧾 BLOQUE PRINCIPAL
# ============================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("📊 RESUMEN DE DATOS GENERADOS")
    print("="*60)
    print(f"Total registros: {len(df_terminales)}")
    print(f"Terminales únicas: {df_terminales['Terminal'].nunique()}")
    print(f"Registros colapsados: {(df_limpio['Estado'] == 'Colapsada').sum()}")
    print(f"Registros estables: {(df_limpio['Estado'] == 'Estable').sum()}")
    print("="*60)

    print("\n" + "="*60)
    print("📅 EJEMPLO: ÚLTIMO DÍA POR TERMINAL")
    print("="*60)
    print(df_ultimo_dia_ejemplo.head().to_string(index=False))
    print("="*60)
