import os
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.units import inch

# ==========================================================
# 📁 ARCHIVO DE DATOS
# ==========================================================
archivo_excel = "predicciones_mio.xlsx"
if not os.path.exists(archivo_excel):
    print(f"⚠️ No se encontró el archivo {archivo_excel}. Ejecuta primero el modelo predictivo.")
    exit()

df = pd.read_excel(archivo_excel)

# ==========================================================
# 📊 ESTADÍSTICAS BÁSICAS
# ==========================================================
total_estaciones = df["Terminal"].nunique() if "Terminal" in df.columns else 0
total_registros = len(df)

# Colapsos
if "Estado_Previsto" in df.columns:
    colapsos = (df["Estado_Previsto"].str.contains("Colapsará", case=False, na=False)).sum()
    porcentaje_colapsos = (colapsos / total_registros) * 100 if total_registros else 0
else:
    colapsos, porcentaje_colapsos = 0, 0

# Buscar columna de ocupación
columna_ocupacion = None
for col in df.columns:
    if "ocup" in col.lower():
        columna_ocupacion = col
        break

if columna_ocupacion:
    ocupacion_promedio = df[columna_ocupacion].mean() * 100
    fuente_ocupacion = columna_ocupacion
else:
    fuente_ocupacion = "Personas_Predichas" if "Personas_Predichas" in df.columns else None
    ocupacion_promedio = df[fuente_ocupacion].mean() if fuente_ocupacion else 0

# Probabilidad de colapso
if "Prob_Colapso" in df.columns:
    prob_colapso_promedio = df["Prob_Colapso"].mean() * 100
else:
    prob_colapso_promedio = 0

# ==========================================================
# 🖼️ GENERAR GRÁFICAS
# ==========================================================
os.makedirs("graficas", exist_ok=True)

# Gráfico circular del estado previsto
if "Estado_Previsto" in df.columns:
    plt.figure(figsize=(6, 6))
    conteo = df["Estado_Previsto"].value_counts()
    plt.pie(conteo, labels=conteo.index, autopct="%1.1f%%")
    plt.title("Distribución del Estado Previsto")
    plt.savefig("graficas/grafico_circular.png")
    plt.close()
    print("🟢 Gráfico circular generado correctamente.")

# Gráfico de barras: promedio de probabilidad por terminal
if "Terminal" in df.columns and "Prob_Colapso" in df.columns:
    plt.figure(figsize=(10, 5))
    promedio_terminal = df.groupby("Terminal")["Prob_Colapso"].mean().sort_values(ascending=False)
    promedio_terminal.plot(kind="bar")
    plt.title("Probabilidad promedio de colapso por terminal")
    plt.ylabel("Probabilidad (%)")
    plt.tight_layout()
    plt.savefig("graficas/grafico_barras.png")
    plt.close()
    print("Gráfico de barras generado correctamente.")

# ==========================================================
# 📝 CREAR REPORTE EN PDF
# ==========================================================
pdf_filename = "Reporte_Modelo_Predictivo_MIO.pdf"
doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
styles = getSampleStyleSheet()
elements = []

# Encabezado con fecha
fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
titulo = Paragraph("📘 Reporte del Modelo Predictivo del Sistema MIO", styles["Title"])
subtitulo = Paragraph(f"Generado el {fecha}", styles["Normal"])
elements += [titulo, subtitulo, Spacer(1, 12)]

# Descripción
texto_intro = f"""
Este reporte resume los resultados del modelo predictivo aplicado al sistema MIO,
incluyendo las estadísticas generales de todas las estaciones y las gráficas generadas
automáticamente a partir de los datos más recientes.<br/><br/>
<b>Fuente de ocupación:</b> {fuente_ocupacion if fuente_ocupacion else 'No disponible'}
"""
elements.append(Paragraph(texto_intro, styles["BodyText"]))
elements.append(Spacer(1, 12))

# Tabla resumen
data = [
    ["Indicador", "Valor"],
    ["Total de estaciones analizadas", total_estaciones],
    ["Total de registros procesados", total_registros],
    ["Promedio de ocupación (%)", f"{ocupacion_promedio:.2f}%"],
    ["Promedio de probabilidad de colapso (%)", f"{prob_colapso_promedio:.2f}%"],
    ["Escenarios colapsados", f"{colapsos} ({porcentaje_colapsos:.2f}%)"],
]
tabla = Table(data, colWidths=[250, 200])
tabla.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
    ("GRID", (0, 0), (-1, -1), 1, colors.black),
]))
elements += [tabla, Spacer(1, 20)]

# Gráficos
graficos = [
    ("Gráfico Circular - Estado Previsto", "graficas/grafico_circular.png"),
    ("Gráfico de Barras - Probabilidad por Terminal", "graficas/grafico_barras.png")
]

for titulo, ruta in graficos:
    if os.path.exists(ruta):
        elements.append(Paragraph(f"<b>{titulo}</b>", styles["Heading2"]))
        elements.append(Image(ruta, width=5*inch, height=4*inch))
        elements.append(Spacer(1, 20))
    else:
        elements.append(Paragraph(f"⚠️ {titulo} no disponible", styles["BodyText"]))

# Crear PDF
try:
    doc.build(elements)
    print(f"PDF generado correctamente: {pdf_filename}")
except Exception as e:
    print(f"Error al generar el PDF: {e}")
    
