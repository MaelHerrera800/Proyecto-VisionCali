import os
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import webbrowser
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.units import inch

import tkinter as tk
from tkinter import ttk, messagebox


# ==========================================================
# 📌 FUNCIÓN PRINCIPAL: GENERAR REPORTE
# ==========================================================
def generar_reporte_por_dia(df_original, dia):

    df = df_original.copy()

    # Validar columna fecha
    if "Fecha" not in df.columns:
        messagebox.showerror("Error", "El archivo no contiene columna 'Fecha'. Cambia el nombre.")
        return

    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

    # Filtrar por día
    df = df[df["Fecha"].dt.day == dia]

    if df.empty:
        messagebox.showwarning("Sin datos", f"No existen datos para el día {dia}.")
        return

    # ================================
    # 📊 ESTADÍSTICAS
    # ================================
    total_estaciones = df["Terminal"].nunique()
    total_registros = len(df)

    # Colapsos
    colapsos = df[df["Estado_Previsto"].str.contains("Colapsará", case=False, na=False)]
    cantidad_colapsos = len(colapsos)
    porcentaje_colapsos = (cantidad_colapsos / total_registros) * 100

    # Ocupación
    ocupacion_promedio = df["Ocupacion"].mean() * 100

    # Probabilidad de colapso
    prob_colapso_promedio = df["Prob_Colapso"].mean() * 100

    # ================================
    # 🖼️ GENERAR GRÁFICAS
    # ================================
    os.makedirs("graficas", exist_ok=True)

    # GRAFICO 1: ESTADO GENERAL
    plt.figure(figsize=(6, 6))
    conteo = df["Estado_Previsto"].value_counts()
    plt.pie(conteo, labels=conteo.index, autopct="%1.1f%%")
    plt.title("Estado General de Estaciones")
    plt.savefig("graficas/estado_general.png")
    plt.close()

    # GRAFICO 2: TOP 10 COLAPSOS
    top_colapso = (
        df.groupby(["Terminal", "Franja Horaria"])["Prob_Colapso"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )

    plt.figure(figsize=(10, 6))
    top_colapso.plot(kind="barh")
    plt.title("Top 10 estaciones/franjas en riesgo de colapso")
    plt.xlabel("Probabilidad promedio")
    plt.tight_layout()
    plt.savefig("graficas/top_colapso.png")
    plt.close()

    # ================================
    # 📈 ANÁLISIS DE TENDENCIAS
    # ================================
    tendencias = []

    # TENDENCIA COLAPSO
    if prob_colapso_promedio > 70:
        tendencias.append("Existe una tendencia ALTA al colapso durante este día.")
    elif prob_colapso_promedio > 40:
        tendencias.append("Se observa una tendencia MODERADA al colapso.")
    else:
        tendencias.append("La tendencia al colapso es BAJA, indicando un día estable.")

    # TENDENCIA OCUPACIÓN
    if ocupacion_promedio > 80:
        tendencias.append("La ocupación promedio es CRÍTICA (superior al 80%).")
    elif ocupacion_promedio > 50:
        tendencias.append("La ocupación promedio es MODERADA (mayor al 50%).")
    else:
        tendencias.append("La ocupación promedio es BAJA para este día.")

    # TERMINAL MÁS RIESGOSA
    top_riesgo = df.groupby("Terminal")["Prob_Colapso"].mean().sort_values(ascending=False)
    estacion_riesgo = top_riesgo.index[0]
    riesgo_valor = top_riesgo.iloc[0] * 100
    tendencias.append(
        f"La terminal con mayor riesgo de colapso es <b>{estacion_riesgo}</b> "
        f"con un riesgo promedio de <b>{riesgo_valor:.2f}%</b>."
    )

    # FRANJA HORARIA MÁS CRÍTICA
    franja_top = df.groupby("Franja Horaria")["Prob_Colapso"].mean().sort_values(ascending=False)
    franja_riesgo = franja_top.index[0]
    franja_valor = franja_top.iloc[0] * 100
    tendencias.append(
        f"La franja horaria más crítica del día fue <b>{franja_riesgo}</b> "
        f"con una probabilidad de <b>{franja_valor:.2f}%</b>."
    )

    # ====================================================
    # 📝 CREAR PDF
    # ====================================================
    pdf_filename = f"Reporte_MIO_Dia_{dia}.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"<b>Reporte Predictivo del MIO - Día {dia}</b>", styles["Title"]))
    elements.append(Paragraph(f"Generado el: {fecha_actual}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # INTRODUCCIÓN
    intro = f"""
    Este reporte presenta el análisis predictivo correspondiente al día <b>{dia}</b>,
    basado en datos del modelo de predicción del sistema MIO. Incluye indicadores clave,
    descripción de gráficas y análisis de tendencias operativas relevantes.
    """
    elements.append(Paragraph(intro, styles["BodyText"]))
    elements.append(Spacer(1, 12))

    # TABLA DE INDICADORES
    data = [
        ["Indicador", "Valor"],
        ["Total de estaciones analizadas", total_estaciones],
        ["Total de registros", total_registros],
        ["Promedio de ocupación (%)", f"{ocupacion_promedio:.2f}%"],
        ["Probabilidad promedio de colapso (%)", f"{prob_colapso_promedio:.2f}%"],
        ["Escenarios previstos como 'Colapsará'", f"{cantidad_colapsos} ({porcentaje_colapsos:.2f}%)"],
    ]

    tabla = Table(data, colWidths=[250, 200])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(tabla)
    elements.append(Spacer(1, 20))

    # 📈 ANÁLISIS DE TENDENCIAS
    elements.append(Paragraph("<b>Análisis de Tendencias</b>", styles["Heading2"]))
    for t in tendencias:
        elements.append(Paragraph(f"- {t}", styles["BodyText"]))
    elements.append(Spacer(1, 20))

    # GRAFICOS + TEXTO
    descripcion_graficos = {
        "Estado General de Estaciones":
            """
            Este gráfico circular representa qué porcentaje de las estaciones estuvieron 
            clasificados como 'Estable' o 'Colapsará'. Permite identificar rápidamente 
            el nivel general de riesgo presente en el sistema durante el día analizado.
            """,
        "Top 10 estaciones/franjas en riesgo de colapso":
            """
            Este gráfico de barras identifica las combinaciones de terminal y franja horaria 
            con mayor probabilidad de colapso. Es fundamental para priorizar la intervención 
            operativa en los puntos más vulnerables del sistema.
            """
    }

    graficos = [
        ("Estado General de Estaciones", "graficas/estado_general.png"),
        ("Top 10 estaciones/franjas en riesgo de colapso", "graficas/top_colapso.png")
    ]

    for titulo, ruta in graficos:
        if os.path.exists(ruta):
            elements.append(Paragraph(f"<b>{titulo}</b>", styles["Heading2"]))
            elements.append(Image(ruta, width=5 * inch, height=4 * inch))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(descripcion_graficos[titulo], styles["BodyText"]))
            elements.append(Spacer(1, 20))

    # GUARDAR PDF
    try:
     doc.build(elements)
     messagebox.showinfo("PDF generado", f"Reporte creado correctamente:\n{pdf_filename}")

    
     ruta_completa = os.path.abspath(pdf_filename)
     webbrowser.open(ruta_completa)

    except Exception as e:
     messagebox.showerror("Error al generar PDF", str(e))



# ==========================================================
# 🔹 INTERFAZ GRÁFICA TKINTER
# ==========================================================
def abrir_interfaz():
    ventana = tk.Tk()
    ventana.title("Generador de Reportes MIO")
    ventana.geometry("350x500")
    ventana.config(bg="#d9e6f2")

    ttk.Label(ventana, text="Seleccione el reporte a generar:", font=("Arial", 12, "bold")).pack(pady=15)

    dias_unicos = sorted(df_global["Fecha"].dt.day.unique())

    for dia in dias_unicos:
        ttk.Button(
            ventana,
            text=f"Generar Reporte Día {dia}",
            width=30,
            command=lambda d=dia: generar_reporte_por_dia(df_global, d)
        ).pack(pady=5)
    ventana.mainloop()

archivo_excel = "predicciones_mio.xlsx"

if not os.path.exists(archivo_excel):
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", "No se encontró predicciones_mio.xlsx")
    root.destroy()
    exit()

df_global = pd.read_excel(archivo_excel)
df_global["Fecha"] = pd.to_datetime(df_global["Fecha"], errors="coerce")

if __name__ == "__main__":
    abrir_interfaz()
    

