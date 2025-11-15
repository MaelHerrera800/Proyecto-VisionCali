import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd



#  CLASE QUE MANEJA TODAS LAS VISUALIZACIONES Y FILTROS

class VisualizacionesMIO:

    def __init__(self, df):
        self.df = df.copy()
        self.df["Fecha"] = pd.to_datetime(self.df["Fecha"]).dt.date

    # ------------------------------
    # FILTRAR POR FECHA Y ESTACIÓN
    # ------------------------------
    def filtrar(self, fecha=None, estacion=None):
        df = self.df.copy()
        if fecha:
            df = df[df["Fecha"] == fecha]
        if estacion:
            df = df[df["Terminal"] == estacion]
        return df

    
    # TABLA: COLAPSOS POR FILTROS
   
    def obtener_colapsos(self, fecha=None, estacion=None):
        df = self.filtrar(fecha, estacion)
        return df[df["Estado_Previsto"].str.contains("Colapsará", case=False, na=False)]


    # GRÁFICO ESTADO GENERAL (POR DÍA)
    
    def grafico_estado_general(self, fecha=None):
        df = self.filtrar(fecha)
        conteo = df["Estado_Previsto"].value_counts()

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(conteo.values, labels=conteo.index, autopct="%1.1f%%", startangle=90)
        ax.set_title("Estado general de estaciones")
        return fig

    # ------------------------------
    # TOP 10 COLAPSOS POR DÍA
    # ------------------------------
    def grafico_top_10(self, fecha=None):
        df = self.filtrar(fecha)

        top_colapso = (
            df.groupby(["Terminal", "Franja Horaria"])["Prob_Colapso"]
            .mean()
            .sort_values(ascending=False)
            .head(10)
        )

        fig, ax = plt.subplots(figsize=(10, 6))
        top_colapso.plot(kind="barh", ax=ax)
        ax.set_title("Top 10 estaciones en riesgo de colapso")
        ax.set_xlabel("Probabilidad promedio")
        plt.tight_layout()
        return fig



#   CLASE INTERFAZ TKINTER — SOLO MANEJA LA VENTANA

class InterfazMIO:

    def __init__(self, df_predicciones):
        self.df = df_predicciones

        # Crear instancia de visualizaciones
        self.visual = VisualizacionesMIO(self.df)

        # Crear ventana
        self.ventana = tk.Tk()
        self.ventana.title("Sistema Predictivo MIO - Análisis")
        self.ventana.geometry("1300x850")

        titulo = tk.Label(
            self.ventana,
            text="Análisis de comportamiento de estaciones",
            font=("Arial", 18, "bold"),
            pady=10
        )
        titulo.pack()

        # Selectores
        frame_selector = tk.Frame(self.ventana)
        frame_selector.pack(pady=10)
        self.crear_selector_estacion(frame_selector)
        self.crear_selector_fecha(frame_selector)

        # Botones
        self.crear_botones()

        # Área de resultados
        self.frame_resultados = tk.Frame(self.ventana)
        self.frame_resultados.pack(fill="both", expand=True)

        self.canvas = None

    
    # Selectores
    
    def crear_selector_estacion(self, frame):
        estaciones = sorted(self.df["Terminal"].dropna().unique())

        tk.Label(frame, text="Estación:", font=("Arial", 12)).grid(row=0, column=0, padx=5)

        self.combo_estaciones = ttk.Combobox(frame, values=estaciones, state="readonly", width=25)
        self.combo_estaciones.grid(row=0, column=1, padx=5)

    def crear_selector_fecha(self, frame):
        # Convertir fechas a string sin la hora
        fechas = sorted( pd.to_datetime(self.df["Fecha"]).dt.strftime("%Y-%m-%d").unique())

        tk.Label(frame, text="Fecha:", font=("Arial", 12)).grid(row=0, column=2, padx=5)

        self.combo_fechas = ttk.Combobox(frame, values=fechas, state="readonly", width=15)
        self.combo_fechas.grid(row=0, column=3, padx=5)

    
    # Botones
    def crear_botones(self):
        frame = tk.Frame(self.ventana)
        frame.pack(pady=15)

        botones = [
            ("Filtrar estación colapsada", self.mostrar_estaciones_colapso),
            ("Ver todas estaciones colapsadas", self.mostrar_todos_colapsos),
            ("Estado general por día", self.mostrar_estado_general),
            ("Top 10 por día", self.mostrar_top_10)
        ]

        for i, (texto, comando) in enumerate(botones):
            ttk.Button(frame, text=texto, command=comando).grid(row=0, column=i, padx=5, pady=5)

    
    # Utilidades
    def limpiar(self):
        for widget in self.frame_resultados.winfo_children():
            widget.destroy()
        if self.canvas:
            self.canvas.get_tk_widget().destroy()

    def get_fecha(self):
        f = self.combo_fechas.get()
        return pd.to_datetime(f).date() if f else None

    def get_estacion(self):
        return self.combo_estaciones.get() or None

    
    # TABLAS Y GRÁFICOS
    
    def mostrar_estaciones_colapso(self):
        self.limpiar()
        fecha = self.get_fecha()
        estacion = self.get_estacion()

        df = self.visual.obtener_colapsos(fecha, estacion)

        if df.empty:
            messagebox.showinfo("Información", "No hay colapsos para este filtro.")
            return

        cols = ["Terminal", "Fecha", "Franja Horaria", "Personas_Predichas", "Prob_Colapso"]
        tree = ttk.Treeview(self.frame_resultados, columns=cols, show="headings", height=15)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=180, anchor="center")

        for _, row in df.iterrows():
            tree.insert("", "end", values=(
                row["Terminal"],
                row["Fecha"],
                row["Franja Horaria"],
                int(row["Personas_Predichas"]),
                f"{row['Prob_Colapso'] * 100:.1f}%"
            ))

        tree.pack(fill="both", expand=True)

    def mostrar_todos_colapsos(self):
        self.limpiar()
        fecha = self.get_fecha()

        df = self.visual.obtener_colapsos(fecha)

        if df.empty:
            messagebox.showinfo("Información", "No hay colapsos para esa fecha.")
            return

        cols = ["Terminal", "Fecha", "Franja Horaria", "Personas_Predichas", "Prob_Colapso"]
        tree = ttk.Treeview(self.frame_resultados, columns=cols, show="headings", height=15)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=180, anchor="center")

        for _, row in df.iterrows():
            tree.insert("", "end", values=(
                row["Terminal"],
                row["Fecha"],
                row["Franja Horaria"],
                int(row["Personas_Predichas"]),
                f"{row['Prob_Colapso'] * 100:.1f}%"
            ))

        tree.pack(fill="both", expand=True)

    def mostrar_estado_general(self):
        self.limpiar()
        fecha = self.get_fecha()
        fig = self.visual.grafico_estado_general(fecha)
        self.canvas = FigureCanvasTkAgg(fig, master=self.frame_resultados)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def mostrar_top_10(self):
        self.limpiar()
        fecha = self.get_fecha()
        fig = self.visual.grafico_top_10(fecha)
        self.canvas = FigureCanvasTkAgg(fig, master=self.frame_resultados)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

     
    # Iniciar ventana
     
    def iniciar(self):
        self.ventana.mainloop()
    



#   EJECUCIÓN PRINCIPAL
if __name__ == "__main__":
    try:
        df = pd.read_excel("predicciones_mio.xlsx")
        app = InterfazMIO(df)
        app.iniciar()
    except FileNotFoundError:
        messagebox.showerror("Error", "No se encontró el archivo 'predicciones_mio.xlsx'.")
