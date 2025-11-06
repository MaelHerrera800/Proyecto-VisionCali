import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import pandas as pd

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

def mostrar_grafico(fig):
    """Renderiza el gráfico actual en el canvas."""
    global canvas
    if canvas:
        canvas.get_tk_widget().destroy()
    canvas = FigureCanvasTkAgg(fig, master=ventana)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

def verificar_df():
    """Verifica que df_predicciones tenga datos."""
    if df_predicciones is None or df_predicciones.empty:
        messagebox.showwarning("Sin datos", "No hay datos para graficar. Ejecuta el modelo primero.")
        return False
    return True

# ===============================================
# 1️⃣ TENDENCIAS TEMPORALES
# ===============================================

def grafico_tendencia():
    if not verificar_df():
        return
    fig, ax = plt.subplots(figsize=(10, 6))
    df_temp = df_predicciones.groupby("Fecha")["Personas_Predichas"].sum().reset_index()
    ax.plot(df_temp["Fecha"], df_temp["Personas_Predichas"], marker="o", color="#1f77b4", linewidth=2)
    ax.fill_between(df_temp["Fecha"], df_temp["Personas_Predichas"], color="#1f77b4", alpha=0.3)
    ax.set_title("📈 Tendencia de Personas Predichas por Fecha")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Personas Predichas")
    plt.xticks(rotation=45)
    mostrar_grafico(fig)

def heatmap_ocupacion():
    if not verificar_df():
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    pivot = df_predicciones.pivot_table(
        index="Día de la Semana",
        columns="Franja Horaria",
        values="Ocupacion",
        aggfunc="mean"
    )
    sns.heatmap(pivot, cmap="YlOrRd", annot=True, fmt=".2f", ax=ax)
    ax.set_title("🔥 Heatmap de Ocupación por Día y Franja Horaria")
    plt.xticks(rotation=45)
    mostrar_grafico(fig)

# ===============================================
# 2️⃣ ANÁLISIS DE RIESGO
# ===============================================

def heatmap_riesgo():
    if not verificar_df():
        return
    fig, ax = plt.subplots(figsize=(12, 6))
    pivot = df_predicciones.pivot_table(
        index="Terminal",
        columns="Franja Horaria",
        values="Prob_Colapso",
        aggfunc="mean"
    )
    sns.heatmap(pivot, cmap="coolwarm", ax=ax)
    ax.set_title("⚠️ Mapa de Riesgo de Colapso (Terminal vs Franja Horaria)")
    plt.xticks(rotation=45)
    plt.yticks(rotation=0)
    mostrar_grafico(fig)

def barras_estado():
    if not verificar_df():
        return
    fig, ax = plt.subplots(figsize=(12, 6))
    conteo = df_predicciones.groupby(["Terminal", "Estado_Previsto"]).size().unstack(fill_value=0)
    conteo.plot(kind="bar", stacked=True, color=["#2ecc71", "#f1c40f", "#e74c3c"], ax=ax)
    ax.set_title("🏗️ Estado Previsto por Terminal")
    ax.set_xlabel("Terminal")
    ax.set_ylabel("Cantidad de registros")
    plt.xticks(rotation=90)
    mostrar_grafico(fig)

# ===============================================
# 3️⃣ COMPARACIÓN ENTRE TERMINALES
# ===============================================

def boxplot_ocupacion():
    if not verificar_df():
        return
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(data=df_predicciones, x="Terminal", y="Ocupacion", ax=ax, palette="Set2")
    ax.set_title("📊 Distribución de Ocupación por Terminal")
    ax.set_xlabel("Terminal")
    ax.set_ylabel("Ocupación")
    plt.xticks(rotation=90)
    mostrar_grafico(fig)

def dispersion_ocupacion():
    if not verificar_df():
        return
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(
        data=df_predicciones,
        x="Ocupacion",
        y="Personas_Predichas",
        hue="Estado_Previsto",
        palette={"Colapsará": "#e74c3c", "Riesgo de Colapso": "#f1c40f", "Estable": "#2ecc71"},
        ax=ax
    )
    ax.set_title("💬 Personas Predichas vs Ocupación (por Estado Previsto)")
    ax.set_xlabel("Ocupación")
    ax.set_ylabel("Personas Predichas")
    mostrar_grafico(fig)

# ===============================================
# INTERFAZ TKINTER
# ===============================================

ventana = tk.Tk()
ventana.title("📊 Sistema Predictivo MIO - Visualización de Resultados")
ventana.geometry("1200x800")

titulo = tk.Label(
    ventana,
    text="🔹 Visualización de Predicciones del Sistema MIO",
    font=("Arial", 18, "bold"),
    pady=10
)
titulo.pack()

# Botones principales
frame_botones = tk.Frame(ventana)
frame_botones.pack(pady=15)

botones = [
    ("📈 Tendencia temporal", grafico_tendencia),
    ("🔥 Heatmap Ocupación", heatmap_ocupacion),
    ("⚠️ Mapa de Riesgo", heatmap_riesgo),
    ("🏗️ Estado por Terminal", barras_estado),
    ("📊 Boxplot Ocupación", boxplot_ocupacion),
    ("💬 Dispersión Ocupación", dispersion_ocupacion)
]

for i, (texto, comando) in enumerate(botones):
    btn = ttk.Button(frame_botones, text=texto, command=comando)
    btn.grid(row=0, column=i, padx=5, pady=5)

canvas = None
grafico_tendencia()

if __name__ == "__main__":
    ventana.mainloop()
