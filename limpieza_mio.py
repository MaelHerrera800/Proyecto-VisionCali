import pandas as pd
import numpy as np
import openpyxl
import calendar 
from datetime import datetime, timedelta

# ------------------- CLASE OBJETO DE DATOS -------------------
class ObjetoDeDatos:
    def __init__(self, dataframe):
        self.dataframe = dataframe

    def limpiar_datos(self):
        """Limpia datos usando métodos modernos de pandas"""
        df_limpio = self.dataframe.drop_duplicates(subset=["Terminal"])
        
        # ✅ Método moderno: usar assign en lugar de fillna con inplace
        mediana_personas = df_limpio["Personas Actuales"].median()
        df_limpio = df_limpio.assign(
            **{"Personas Actuales": df_limpio["Personas Actuales"].fillna(mediana_personas)}
        )
        
        df_limpio = df_limpio.assign(
            **{"Franja Horaria": df_limpio["Franja Horaria"].fillna("Desconocida")}
        )
        
        df_limpio = df_limpio.dropna(subset=["Estado"])
        return df_limpio


# ------------------- DATOS DE TERMINALES -------------------
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

num_datos = 1000  

# Generar datos aleatorios con variación realista
np.random.seed(42)  # Para reproducibilidad
terminales_random = np.random.choice(nombres_terminales, num_datos)
capacidades = np.random.randint(80, 200, num_datos)

# ✅ MEJORA: Generar personas con distribución más realista
# Algunas estarán por encima de la capacidad (colapso real)
personas = []
for cap in capacidades:
    # 70% estable, 20% cerca del límite, 10% colapsada
    rand = np.random.random()
    if rand < 0.70:
        personas.append(np.random.randint(int(cap * 0.5), int(cap * 0.85)))
    elif rand < 0.90:
        personas.append(np.random.randint(int(cap * 0.85), int(cap * 1.1)))
    else:
        personas.append(np.random.randint(int(cap * 1.1), int(cap * 1.3)))

personas = np.array(personas)
estado = np.where(personas > capacidades, "Colapsada", "Estable")


fecha_fin = datetime.now().date()
fecha_inicio = fecha_fin - timedelta(days=730)  # 2 años de histórico
fechas_secuenciales = pd.date_range(start=fecha_inicio, end=fecha_fin, periods=num_datos)

FRANJAS_DISPONIBLES = [
    "05:30-09:00", "09:00-12:00", "12:00-15:00",
    "15:00-18:00", "18:00-21:00", "21:00-23:00"
]

# Crear DataFrame principal
df_terminales = pd.DataFrame({
    "Terminal": terminales_random,
    "Capacidad Máxima": capacidades,
    "Personas Actuales": personas,
    "Estado": estado,
    "Franja Horaria": np.random.choice(FRANJAS_DISPONIBLES, num_datos),
    "Fecha": fechas_secuenciales.date
})

# ✅ Método moderno: usar dt accessor para operaciones de fecha
df_terminales["Fecha"] = pd.to_datetime(df_terminales["Fecha"])
df_terminales["Día de la Semana"] = df_terminales["Fecha"].dt.day_name()

print(f"✅ Se generaron {len(df_terminales)} registros de simulación.")
print(f"📅 Rango de fechas: {df_terminales['Fecha'].min().date()} a {df_terminales['Fecha'].max().date()}")

# Introducir valores nulos (5%)
num_nulls = int(num_datos * 0.05)

# ✅ Método moderno: usar loc con sample en lugar de random.choice
indices_nulls_personas = df_terminales.sample(n=num_nulls, random_state=42).index
indices_nulls_franja = df_terminales.sample(n=num_nulls, random_state=43).index
indices_nulls_estado = df_terminales.sample(n=num_nulls, random_state=44).index

df_terminales.loc[indices_nulls_personas, "Personas Actuales"] = None
df_terminales.loc[indices_nulls_franja, "Franja Horaria"] = None
df_terminales.loc[indices_nulls_estado, "Estado"] = None

# Crear DataFrame con identificación de valores nulos
df_nulos = df_terminales.isnull().astype(int)

# ------------------- LIMPIAR DATOS -------------------
objeto_datos = ObjetoDeDatos(df_terminales)
df_limpio = objeto_datos.limpiar_datos()

print(f"Datos limpios: {len(df_limpio)} registros después de limpieza")
print(f"Estados: {df_limpio['Estado'].value_counts().to_dict()}")

# ------------------- EXPORTAR A EXCEL -------------------
with pd.ExcelWriter("data_limpia_mio.xlsx", engine="openpyxl") as writer:
    df_terminales.to_excel(writer, sheet_name="Datos Originales", index=False)
    df_nulos.to_excel(writer, sheet_name="Valores Nulos", index=False)
    df_limpio.to_excel(writer, sheet_name="Datos Limpios", index=False)

print("✅ Archivo 'data_limpia_mio.xlsx' generado exitosamente.")

# ------------------- FUNCIÓN AUXILIAR PARA MODELO -------------------
def obtener_ultimo_mes():
    """Retorna datos del último mes para entrenar el modelo"""
    fecha_corte = df_limpio["Fecha"].max() - timedelta(days=30)
    df_ultimo_mes = df_limpio[df_limpio["Fecha"] >= fecha_corte].copy()
    print(f"📆 Último mes: {len(df_ultimo_mes)} registros desde {fecha_corte.date()}")
    return df_ultimo_mes

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📊 RESUMEN DE DATOS GENERADOS")
    print("="*60)
    print(f"Total registros: {len(df_terminales)}")
    print(f"Terminales únicas: {df_terminales['Terminal'].nunique()}")
    print(f"Registros colapsados: {(df_limpio['Estado'] == 'Colapsada').sum()}")
    print(f"Registros estables: {(df_limpio['Estado'] == 'Estable').sum()}")
    print("="*60)