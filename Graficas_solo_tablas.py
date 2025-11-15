# ================================================================
# 🔴 NOTA IMPORTANTE
# No fue posible mantener dos tipos diferentes de tablas dentro del
# mismo módulo de gráficas, ya que mezclar interfaces gráficas con
# funciones sin gráficas generaba conflictos visuales y de control
# de ventana. Por ello, se creó este módulo separado que contiene
# exclusivamente las TABLAS SIN GRÁFICAS.
# ================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd


# ============================================================
#   👉 CLASE QUE MANEJA SOLAMENTE TABLAS (SIN GRÁFICAS)
# ============================================================
class TablasMIO:

    def __init__(self, df):
        self.df = df.copy()
        self.df["Fecha"] = pd.to_datetime(self.df["Fecha"]).dt.date

    # Filtro general
    def filtrar(self, fecha=None, estacion=None):
        df = self.df.copy()
        if fecha:
            df = df[df["Fecha"] == fecha]
        if estacion:
            df = df[df["Terminal"] == estacion]
        return df

    # Solo colapsos
    def obtener_colapsos(self, fecha=None, estacion=None):
        df = self.filtrar(fecha, estacion)
        return df[df["Estado_Previsto"].str.contains("Colapsará", case=False, na=False)]


# ============================================================
#   👉 INTERFAZ QUE MUESTRA SOLO TABLAS
# ============================================================
class InterfazTablas:

    def __init__(self, df):
        self.df = df
        self.tablas = TablasMIO(df)

        self.ventana = tk.Tk()
        self.ventana.title("Tabla de Estaciones en Riesgo")
        self.ventana.geometry("1100x700")

        tk.Label(
            self.ventana,
            text="Estaciones en riesgo de colapso",
            font=("Arial", 16, "bold"),
            pady=10
        ).pack()

        # Selectores
        frame_selector = tk.Frame(self.ventana)
        frame_selector.pack(pady=10)

        self.crear_selector_estacion(frame_selector)
        self.crear_selector_fecha(frame_selector)

        # Botón para mostrar tabla filtrada
        tk.Button(
            self.ventana,
            text="Mostrar Estaciones",
            command=self.mostrar_tabla_colapsos,
            bg="#3498DB",
            fg="white",
            width=20
        ).pack(pady=10)

        # Botón para mostrar todas las terminales
        tk.Button(
            self.ventana,
            text="Mostrar todas las terminales",
            command=self.mostrar_todas_las_terminales,
            bg="#27AE60",
            fg="white",
            width=25
        ).pack(pady=5)

        # Área de tabla
        self.frame_tabla = tk.Frame(self.ventana)
        self.frame_tabla.pack(fill="both", expand=True)

    # ==========================
    #  SELECTORES
    # ==========================

    def crear_selector_estacion(self, frame):
        estaciones = sorted(self.df["Terminal"].dropna().unique())
        tk.Label(frame, text="Estación:", font=("Arial", 12)).grid(row=0, column=0, padx=5)
        self.combo_estaciones = ttk.Combobox(frame, values=estaciones, state="readonly", width=25)
        self.combo_estaciones.grid(row=0, column=1, padx=5)

    def crear_selector_fecha(self, frame):
        fechas = sorted(pd.to_datetime(self.df["Fecha"]).dt.strftime("%Y-%m-%d").unique())
        tk.Label(frame, text="Fecha:", font=("Arial", 12)).grid(row=0, column=2, padx=5)
        self.combo_fechas = ttk.Combobox(frame, values=fechas, state="readonly", width=15)
        self.combo_fechas.grid(row=0, column=3, padx=5)

    # ==========================
    #  UTILIDADES
    # ==========================

    def limpiar_tabla(self):
        for widget in self.frame_tabla.winfo_children():
            widget.destroy()

    def get_fecha(self):
        f = self.combo_fechas.get()
        return pd.to_datetime(f).date() if f else None

    def get_estacion(self):
        return self.combo_estaciones.get() or None

    # ==========================
    #  TABLA FILTRADA
    # ==========================
    def mostrar_tabla_colapsos(self):
        self.limpiar_tabla()

        fecha = self.get_fecha()
        estacion = self.get_estacion()

        df = self.tablas.obtener_colapsos(fecha, estacion)

        if df.empty:
            messagebox.showinfo("Información", "No hay estaciones en riesgo para este filtro.")
            return

        cols = ["Terminal", "Fecha", "Franja Horaria", "Personas_Predichas", "Prob_Colapso"]
        tabla = ttk.Treeview(self.frame_tabla, columns=cols, show="headings", height=20)

        for col in cols:
            tabla.heading(col, text=col)
            tabla.column(col, width=180, anchor="center")

        for _, row in df.iterrows():
            tabla.insert("", "end", values=(
                row["Terminal"],
                row["Fecha"],
                row["Franja Horaria"],
                int(row["Personas_Predichas"]),
                f"{row['Prob_Colapso']*100:.1f}%"
            ))

        tabla.pack(fill="both", expand=True)

    # ==========================
    #  TODAS LAS TERMINALES
    # ==========================
    def mostrar_todas_las_terminales(self):
        self.limpiar_tabla()

        df = self.tablas.obtener_colapsos()

        if df.empty:
            messagebox.showinfo("Información", "No existen estaciones con riesgo de colapso.")
            return

        df = df.sort_values(by="Terminal")

        cols = ["Terminal", "Fecha", "Franja Horaria", "Personas_Predichas", "Prob_Colapso"]
        tabla = ttk.Treeview(self.frame_tabla, columns=cols, show="headings", height=20)

        for col in cols:
            tabla.heading(col, text=col)
            tabla.column(col, width=180, anchor="center")

        for _, row in df.iterrows():
            tabla.insert("", "end", values=(
                row["Terminal"],
                row["Fecha"],
                row["Franja Horaria"],
                int(row["Personas_Predichas"]),
                f"{row['Prob_Colapso']*100:.1f}%"
            ))

        tabla.pack(fill="both", expand=True)

    # ==========================
    #  INICIAR VENTANA
    # ==========================
    def iniciar(self):
        self.ventana.mainloop()


# ============================================================
#   EJECUCIÓN DEL MÓDULO
# ============================================================
if __name__ == "__main__":
    try:
        df = pd.read_excel("predicciones_mio.xlsx")
        app = InterfazTablas(df)
        app.iniciar()
    except FileNotFoundError:
        messagebox.showerror("Error", "No se encontró el archivo 'predicciones_mio.xlsx'.")