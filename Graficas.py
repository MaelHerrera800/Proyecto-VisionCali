import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import timedelta

# ===============================================
# IMPORTAR DATOS DEL MODELO PREDICTIVO
# ===============================================
try:
    df_predicciones = pd.read_excel("predicciones_mio.xlsx")
except FileNotFoundError:
    messagebox.showerror(
        "Error", 
        "No se encontró el archivo 'predicciones_mio.xlsx'. Ejecuta primero el modelo predictivo."
    )
    df_predicciones = None

# ===============================================
# FUNCIONES AUXILIARES
# ===============================================
def verificar_df():
    if df_predicciones is None or df_predicciones.empty:
        messagebox.showwarning("Sin datos", "No hay datos para analizar.")
        return False
    return True

def limpiar_canvas():
    global canvas
    if canvas:
        canvas.get_tk_widget().destroy()

def limpiar_tabla():
    for widget in frame_resultados.winfo_children():
        widget.destroy()

# ===============================================
# SELECTOR DE ESTACIÓN
# ===============================================
def crear_selector_estacion(frame_padre):
    global combo_estaciones

    estaciones = sorted(df_predicciones["Terminal"].dropna().unique())

    label = tk.Label(frame_padre, text="Seleccionar estación:", font=("Arial", 12))
    label.grid(row=0, column=0, padx=5)

    combo_estaciones = ttk.Combobox(frame_padre, values=estaciones, state="readonly", width=25)
    combo_estaciones.grid(row=0, column=1, padx=5)

# ===============================================
# SELECTOR DE FECHA
# ===============================================
def crear_selector_fecha(frame_padre):
    global combo_fechas

    df_predicciones["Fecha"] = pd.to_datetime(df_predicciones["Fecha"]).dt.date
    fechas = sorted(df_predicciones["Fecha"].unique())

    label = tk.Label(frame_padre, text="Seleccionar fecha:", font=("Arial", 12))
    label.grid(row=0, column=2, padx=5)

    combo_fechas = ttk.Combobox(frame_padre, values=fechas, state="readonly", width=15)
    combo_fechas.grid(row=0, column=3, padx=5)

# ===============================================
# 1️⃣ MOSTRAR ESTACIONES COLAPSADAS (CON FILTROS)
# ===============================================
def mostrar_estaciones_colapso():
    if not verificar_df():
        return

    limpiar_canvas()
    limpiar_tabla()

    df_predicciones["Fecha"] = pd.to_datetime(df_predicciones["Fecha"]).dt.date

    # FILTRAR POR FECHA
    fecha_sel = combo_fechas.get()
    if fecha_sel:
        fecha_sel = pd.to_datetime(fecha_sel).date()
        df_filtrado = df_predicciones[df_predicciones["Fecha"] == fecha_sel]
    else:
        df_filtrado = df_predicciones.copy()

    # FILTRAR POR ESTACIÓN
    estacion_sel = combo_estaciones.get()
    if estacion_sel:
        df_filtrado = df_filtrado[df_filtrado["Terminal"] == estacion_sel]

    # FILTRAR COLAPSOS
    df_colapsos = df_filtrado[
        df_filtrado["Estado_Previsto"].str.contains("Colapsará", case=False, na=False)
    ]

    if df_colapsos.empty:
        messagebox.showinfo("Información", "No se predicen colapsos para esa fecha/estación.")
        return

    label = tk.Label(frame_resultados, text="Estaciones que colapsarán",
                     font=("Arial", 16, "bold"))
    label.pack(pady=10)

    cols = ["Terminal", "Fecha", "Franja Horaria", "Personas_Predichas", "Prob_Colapso"]
    tree = ttk.Treeview(frame_resultados, columns=cols, show="headings", height=15)

    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=180, anchor="center")

    for _, row in df_colapsos.iterrows():
        tree.insert("", "end", values=(
            row["Terminal"],
            row["Fecha"],
            row["Franja Horaria"],
            int(row["Personas_Predichas"]),
            f"{row['Prob_Colapso'] * 100:.1f}%"
        ))

    tree.pack(fill="both", expand=True)

# ===============================================
# 2️⃣ MOSTRAR TODAS LAS ESTACIONES COLAPSADAS
# ===============================================
def mostrar_todas_estaciones_colapso():
    if not verificar_df():
        return

    limpiar_canvas()
    limpiar_tabla()

    df_predicciones["Fecha"] = pd.to_datetime(df_predicciones["Fecha"]).dt.date

    # FILTRO POR FECHA OPCIONAL
    fecha_sel = combo_fechas.get()
    if fecha_sel:
        fecha_sel = pd.to_datetime(fecha_sel).date()
        df_filtrado = df_predicciones[df_predicciones["Fecha"] == fecha_sel]
    else:
        df_filtrado = df_predicciones.copy()

    # FILTRAR SOLO COLAPSOS
    df_colapsos = df_filtrado[
        df_filtrado["Estado_Previsto"].str.contains("Colapsará", case=False, na=False)
    ]

    if df_colapsos.empty:
        messagebox.showinfo("Información", "No se predicen colapsos para esa fecha.")
        return

    label = tk.Label(frame_resultados, text="Todas las estaciones que colapsarán",
                     font=("Arial", 16, "bold"))
    label.pack(pady=10)

    cols = ["Terminal", "Fecha", "Franja Horaria", "Personas_Predichas", "Prob_Colapso"]
    tree = ttk.Treeview(frame_resultados, columns=cols, show="headings", height=15)

    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=180, anchor="center")

    for _, row in df_colapsos.iterrows():
        tree.insert("", "end", values=(
            row["Terminal"],
            row["Fecha"],
            row["Franja Horaria"],
            int(row["Personas_Predichas"]),
            f"{row['Prob_Colapso'] * 100:.1f}%"
        ))

    tree.pack(fill="both", expand=True)

# ===============================================
# 3️⃣ GRÁFICO ESTADO GENERAL
# ===============================================
def grafico_estado_general():
    if not verificar_df():
        return

    limpiar_canvas()
    limpiar_tabla()

    df_predicciones["Fecha"] = pd.to_datetime(df_predicciones["Fecha"]).dt.date
    conteo = df_predicciones["Estado_Previsto"].value_counts()

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(conteo.values, labels=conteo.index, autopct="%1.1f%%", startangle=90)
    ax.set_title("Estado general de las estaciones")
    mostrar_grafico(fig)

# ===============================================
# 4️⃣ GRÁFICO TOP 10
# ===============================================
def grafico_top_colapsos():
    if not verificar_df():
        return

    limpiar_canvas()
    limpiar_tabla()

    df_predicciones["Fecha"] = pd.to_datetime(df_predicciones["Fecha"]).dt.date

    top_colapso = (
        df_predicciones.groupby(["Terminal", "Franja Horaria"])["Prob_Colapso"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    top_colapso.plot(kind="barh", ax=ax)
    ax.set_title("Top 10 estaciones en riesgo de colapso")
    ax.set_xlabel("Probabilidad promedio")
    plt.tight_layout()
    mostrar_grafico(fig)

# ===============================================
# FUNCIÓN PARA MOSTRAR GRÁFICO
# ===============================================
def mostrar_grafico(fig):
    global canvas
    canvas = FigureCanvasTkAgg(fig, master=frame_resultados)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

# ===============================================
# INTERFAZ TKINTER
# ===============================================
def iniciar_graficas():
    ventana = tk.Tk()
    ventana.title("Sistema Predictivo MIO - Análisis")
    ventana.geometry("1300x850")

    titulo = tk.Label(
        ventana,
        text="Análisis de comportamiento de estaciones",
        font=("Arial", 18, "bold"),
        pady=10
    )
    titulo.pack()

    frame_selector = tk.Frame(ventana)
    frame_selector.pack(pady=10)

    crear_selector_estacion(frame_selector)
    crear_selector_fecha(frame_selector)

    frame_botones = tk.Frame(ventana)
    frame_botones.pack(pady=15)

    botones = [
        ("Filtrar estación colapsada", mostrar_estaciones_colapso),
        ("Ver todas las estaciones colapsadas", mostrar_todas_estaciones_colapso),
        ("Estado general", grafico_estado_general),
        ("Top 10 estaciones en riesgo", grafico_top_colapsos)
    ]

    for i, (texto, comando) in enumerate(botones):
        btn = ttk.Button(frame_botones, text=texto, command=comando)
        btn.grid(row=0, column=i, padx=5, pady=5)

    global frame_resultados
    frame_resultados = tk.Frame(ventana)
    frame_resultados.pack(fill="both", expand=True)

    global canvas
    canvas = None

def tabla_estaciones_colapso():
    # Crear ventana
    win = tk.Toplevel()
    win.title("Estaciones que colapsarán")
    win.geometry("900x600")

    tk.Label(win, text="Filtrar Estaciones", font=("Arial", 14, "bold")).pack(pady=10)

    # Frame de filtros
    frame_filtros = tk.Frame(win)
    frame_filtros.pack(pady=10)

    # Selector estación
    estaciones = sorted(df["Terminal"].dropna().unique())
    tk.Label(frame_filtros, text="Estación:", font=("Arial", 12)).grid(row=0, column=0, padx=5)
    combo_est = ttk.Combobox(frame_filtros, values=estaciones, state="readonly", width=25)
    combo_est.grid(row=0, column=1, padx=5)

    # Selector fecha
    fechas = sorted(df["Fecha"].unique())
    tk.Label(frame_filtros, text="Fecha:", font=("Arial", 12)).grid(row=0, column=2, padx=5)
    combo_fec = ttk.Combobox(frame_filtros, values=fechas, state="readonly", width=15)
    combo_fec.grid(row=0, column=3, padx=5)

    # Frame tabla
    frame_tabla = tk.Frame(win)
    frame_tabla.pack(fill="both", expand=True)

def tabla_estaciones_colapso():
    # Crear ventana
    win = tk.Toplevel()
    win.title("Estaciones que colapsarán")
    win.geometry("900x600")

    tk.Label(win, text="Filtrar Estaciones", font=("Arial", 14, "bold")).pack(pady=10)

    # Frame de filtros
    frame_filtros = tk.Frame(win)
    frame_filtros.pack(pady=10)

    # Selector estación
    estaciones = sorted(df_predicciones["Terminal"].dropna().unique())
    tk.Label(frame_filtros, text="Estación:", font=("Arial", 12)).grid(row=0, column=0, padx=5)
    combo_est = ttk.Combobox(frame_filtros, values=estaciones, state="readonly", width=25)
    combo_est.grid(row=0, column=1, padx=5)

    # Selector fecha
    df_predicciones["Fecha"] = pd.to_datetime(df_predicciones["Fecha"]).dt.date
    fechas = sorted(df_predicciones["Fecha"].unique())
    tk.Label(frame_filtros, text="Fecha:", font=("Arial", 12)).grid(row=0, column=2, padx=5)
    combo_fec = ttk.Combobox(frame_filtros, values=fechas, state="readonly", width=15)
    combo_fec.grid(row=0, column=3, padx=5)

    # Frame tabla
    frame_tabla = tk.Frame(win)
    frame_tabla.pack(fill="both", expand=True)

    # Función interna para mostrar la tabla
    def mostrar_tabla():
        for widget in frame_tabla.winfo_children():
            widget.destroy()

        df_filtrado = df_predicciones.copy()

        estacion = combo_est.get()
        if estacion:
            df_filtrado = df_filtrado[df_filtrado["Terminal"] == estacion]

        fecha = combo_fec.get()
        if fecha:
            fecha = pd.to_datetime(fecha).date()
            df_filtrado = df_filtrado[df_filtrado["Fecha"] == fecha]

        # Filtrar colapsos
        df_filtrado = df_filtrado[
            df_filtrado["Estado_Previsto"].str.contains("Colapsará", case=False, na=False)
        ]

        if df_filtrado.empty:
            messagebox.showinfo("Sin datos", "No hay colapsos para esos filtros.")
            return

        # Crear tabla
        columnas = ["Terminal", "Fecha", "Franja Horaria", "Personas_Predichas", "Prob_Colapso"]
        tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=15)

        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=180, anchor="center")

        for _, fila in df_filtrado.iterrows():
            tabla.insert("", "end", values=(
                fila["Terminal"],
                fila["Fecha"],
                fila["Franja Horaria"],
                int(fila["Personas_Predichas"]),
                f"{fila['Prob_Colapso'] * 100:.1f}%"
            ))

        tabla.pack(fill="both", expand=True)

    tk.Button(win, text="Aplicar filtros", font=("Arial", 12, "bold"), command=mostrar_tabla).pack(pady=10)
    


if __name__ == "__main__":
    iniciar_graficas()
