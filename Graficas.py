import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import pandas as pd
from datetime import timedelta

# ===============================================
# IMPORTAR DATOS DEL MODELO PREDICTIVO
# ===============================================
try:
    from modelo_predictivo import ModeloPredictivoMIO
    modelo = ModeloPredictivoMIO()

    modelo.entrenar_modelo_regresion()
    modelo.entrenar_modelo_colapso()

    df_predicciones = modelo.predecir()
    if df_predicciones is None or df_predicciones.empty:
        raise ValueError("El modelo no generó predicciones válidas.")
except Exception as e:
    messagebox.showerror("Error", f"No se pudo cargar el modelo predictivo: {e}")
    raise SystemExit

sns.set_style("whitegrid")

# ===============================================
# FUNCIONES AUXILIARES
# ===============================================
def verificar_df():
    """Verifica que df_predicciones tenga datos."""
    if df_predicciones is None or df_predicciones.empty:
        messagebox.showwarning("Sin datos", "No hay datos para analizar.")
        return False
    return True

def limpiar_canvas():
    """Elimina cualquier gráfico previo del canvas."""
    global canvas
    if canvas:
        canvas.get_tk_widget().destroy()

def limpiar_tabla():
    """Elimina cualquier tabla previa."""
    for widget in frame_resultados.winfo_children():
        widget.destroy()

# ===============================================
# 1️⃣ MOSTRAR ESTACIONES QUE COLAPSARÁN
# ===============================================

def mostrar_estaciones_colapso():
    """Muestra en tabla las estaciones que colapsarán en los próximos 5 días."""
    if not verificar_df():
        return

    limpiar_canvas()
    limpiar_tabla()

    # Asegurar formato de fecha sin hora
    df_predicciones["Fecha"] = pd.to_datetime(df_predicciones["Fecha"]).dt.date

    # Simular los próximos 5 días (futuro)
    fecha_actual = df_predicciones["Fecha"].max()
    fecha_futura = fecha_actual + timedelta(days=5)
    df_futuro = df_predicciones[df_predicciones["Fecha"] <= fecha_futura]

    # Filtrar solo las estaciones que colapsarán
    df_colapsos = df_futuro[df_futuro["Estado_Previsto"].str.contains("Colapsará", case=False, na=False)]

    if df_colapsos.empty:
        messagebox.showinfo("Información", "No se predicen colapsos en los próximos 5 días.")
        return

    label = tk.Label(frame_resultados, text="🚨 Estaciones que colapsarán en los próximos 5 días", font=("Arial", 16, "bold"))
    label.pack(pady=10)

    # Crear tabla de visualización
    cols = ["Terminal", "Fecha", "Franja Horaria", "Personas_Predichas", "Prob_Colapso"]
    tree = ttk.Treeview(frame_resultados, columns=cols, show="headings", height=15)

    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=180, anchor="center")

    # Agregar filas
    for _, row in df_colapsos.iterrows():
        tree.insert("", "end", values=(
            row.get("Terminal", ""),
            row.get("Fecha", ""),
            row.get("Franja Horaria", ""),
            int(row.get("Personas_Predichas", 0)),
            f"{row.get('Prob_Colapso', 0)*100:.1f}%"
        ))

    tree.pack(fill="both", expand=True)
    frame_resultados.pack(fill="both", expand=True)

# ===============================================
# 2️⃣ ESTADO GENERAL DE LOS PRÓXIMOS 5 DÍAS
# ===============================================

def grafico_estado_general():
    """Gráfico circular del estado general de todas las estaciones en los próximos 5 días."""
    if not verificar_df():
        return

    limpiar_canvas()
    limpiar_tabla()

    df_predicciones["Fecha"] = pd.to_datetime(df_predicciones["Fecha"]).dt.date

    fecha_actual = df_predicciones["Fecha"].max()
    fecha_futura = fecha_actual + timedelta(days=5)
    df_futuro = df_predicciones[df_predicciones["Fecha"] <= fecha_futura]

    conteo = df_futuro["Estado_Previsto"].value_counts()

    fig, ax = plt.subplots(figsize=(6, 6))
    colores = ["#2ecc71", "#f1c40f", "#e74c3c"]
    ax.pie(
        conteo.values,
        labels=conteo.index,
        autopct="%1.1f%%",
        startangle=90,
        colors=colores
    )
    ax.set_title("🌍 Estado general de las estaciones (próximos 5 días)")
    mostrar_grafico(fig)

# ===============================================
# 3️⃣ TOP ESTACIONES EN RIESGO DE COLAPSO
# ===============================================

def grafico_top_colapsos():
    """Gráfico de barras con las estaciones más propensas a colapsar."""
    if not verificar_df():
        return

    limpiar_canvas()
    limpiar_tabla()

    df_predicciones["Fecha"] = pd.to_datetime(df_predicciones["Fecha"]).dt.date

    fecha_actual = df_predicciones["Fecha"].max()
    fecha_futura = fecha_actual + timedelta(days=5)
    df_futuro = df_predicciones[df_predicciones["Fecha"] <= fecha_futura]

    # Agrupar también por franja horaria
    top_colapso = (
        df_futuro.groupby(["Terminal", "Franja Horaria"])["Prob_Colapso"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    top_colapso.plot(kind="barh", color="#e74c3c", ax=ax)
    ax.set_title("🚨 Top 10 estaciones y franjas horarias con mayor probabilidad de colapso (próximos 5 días)")
    ax.set_xlabel("Probabilidad de colapso promedio")
    ax.set_ylabel("Terminal y Franja Horaria")
    plt.tight_layout()
    mostrar_grafico(fig)

# ===============================================
# FUNCIÓN PARA MOSTRAR GRÁFICOS
# ===============================================

def mostrar_grafico(fig):
    global canvas
    canvas = FigureCanvasTkAgg(fig, master=frame_resultados)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

# ===============================================
# INTERFAZ TKINTER
# ===============================================

ventana = tk.Tk()
ventana.title("📊 Sistema Predictivo MIO - Análisis Futuro (Próximos 5 Días)")
ventana.geometry("1200x800")

titulo = tk.Label(
    ventana,
    text="🔹 Análisis de comportamiento de estaciones (Próximos 5 días)",
    font=("Arial", 18, "bold"),
    pady=10
)
titulo.pack()

frame_botones = tk.Frame(ventana)
frame_botones.pack(pady=15)

botones = [
    ("🚨 Ver estaciones que colapsarán", mostrar_estaciones_colapso),
    ("🌍 Estado general futuro", grafico_estado_general),
    ("📊 Top 10 estaciones en riesgo", grafico_top_colapsos)
]

for i, (texto, comando) in enumerate(botones):
    btn = ttk.Button(frame_botones, text=texto, command=comando)
    btn.grid(row=0, column=i, padx=5, pady=5)

frame_resultados = tk.Frame(ventana)
frame_resultados.pack(fill="both", expand=True)

canvas = None

if __name__ == "__main__":
    ventana.mainloop()

#ejemplo de uso: python Graficas.py