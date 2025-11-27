# Proyecto-VisionCali
Sistema Predictivo MIO – VisiónCali

Predicción, análisis y visualización del comportamiento de estaciones del Sistema Integrado de Transporte MIO en Cali, Colombia.

📑 Tabla de Contenidos

Características

Requisitos

Instalación

Flujo de Trabajo

Descripción de Archivos

Estructura del Proyecto

Uso

Configuración

Arquitectura

Modelado y Decisiones Técnicas

Buenas Prácticas de Reproducibilidad

Testing

Roles y Permisos

Autenticación

Contribución

Mejoras Futuras

✨ Características

Modelos predictivos de ocupación y probabilidad de colapso (Random Forest, Regresión Lineal)

Alertas tempranas para estaciones críticas

Dashboards de gráficos avanzados

Mapas georreferenciados con riesgo por estación

Sistema multirol (Administrador, Operario, Usuario)

Reportes Excel automáticos

Pipeline automatizado mediante Menu.py

🔧 Requisitos
Python

Python >= 3.8

📦 Dependencias (requirements.txt)
# Dependencias del Sistema Predictivo MIO
# Python >= 3.8

# Core dependencies
pandas>=1.5.0,<2.0.0
numpy>=1.23.0,<2.0.0
openpyxl>=3.0.0,<4.0.0

# Machine Learning
scikit-learn>=1.2.0,<2.0.0

# Visualización
matplotlib>=3.6.0,<4.0.0

# GUI
# tkinter viene incluido con Python, no requiere instalación

# Mapas
folium>=0.14.0,<1.0.0

# Firebase
pyrebase4>=4.6.0,<5.0.0

# Procesamiento de imágenes
Pillow>=9.0.0,<11.0.0

# Testing (opcional)
pytest>=7.0.0,<8.0.0
pytest-cov>=4.0.0,<5.0.0

📦 Instalación
1. Crear entorno virtual
Windows
python -m venv venv
venv\Scripts\activate

Linux/macOS
python3 -m venv venv
source venv/bin/activate

2. Instalar dependencias
pip install -r requirements.txt

3. Verificar instalación
python -c "import pandas, sklearn, folium; print('✓ Dependencias instaladas correctamente')"

🚦 Flujo de Trabajo
✔ 1. Generar datos limpios
python limpieza_mio.py


Produce: data_limpia_mio.xlsx

✔ 2. Entrenar modelos y generar predicciones
python modelo_predictivo.py


Produce: predicciones_mio.xlsx

✔ 3. Visualización

Gráficos: python Graficas.py

Tablas: python Graficas_solo_tablas.py

Mapas: python mapaMIO.py

Reportes: python Reportes_finales.py

🚀 Flujo Simplificado (Automático)

Ejecutar:

python Menu.py


Este módulo:

Muestra pantalla de carga

Genera datos limpios (si no existen)

Entrena modelos (si no existe archivo)

Crea predicciones

Abre menú de roles

📁 Descripción de Archivos
limpieza_mio.py

Limpieza de datos

Manejo de nulos

Normalización

Exportación de 3 hojas Excel

Semilla fija para reproducibilidad:

np.random.seed(42)

modelo_predictivo.py

Entrenamiento de:

Random Forest

Regresión Lineal

Generación de predicciones

Probabilidad de colapso

Clipping justificado:

ocupacion = ocupacion.clip(0.1, 2.0)

Menu.py

Sistema de roles

Autenticación Firebase

Automatización del pipeline

Graficas.py

Gráficos avanzados:

Lollipop chart

Gráfico de torta

Top 10 estaciones en riesgo

Graficas_solo_tablas.py

Tablas detalladas filtrables por estación y riesgo

mapaMIO.py

Mapa HTML con colores de riesgo

🟢 Estación estable

🔴 Estación colapsará

Reportes_finales.py

Reportes Excel con análisis por día y estación

🏗️ Estructura del Proyecto
sistema-predictivo-mio/
│
├── config.json
├── requirements.txt
├── README.md
│
├── utils.py
├── limpieza_mio.py
├── modelo_predictivo.py
│
├── Menu.py
├── Graficas.py
├── Graficas_solo_tablas.py
├── mapaMIO.py
│
├── tests/
│   ├── test_limpieza.py
│   ├── test_modelo.py
│   └── test_utils.py
│
└── data/
    ├── data_limpia_mio.xlsx
    └── predicciones_mio.xlsx

🔍 Modelado y Decisiones Técnicas
✔ Random Forest como modelo principal

Maneja no linealidades

Robusto al ruido

Excelente en datos tabulares

No requiere normalización

✔ Clipping entre 0.1 y 2.0

Controla:

Predicciones irreales

Estabilidad del modelo

Outliers extremos

Normalización visual en mapas

✔ Escenarios futuros

El sistema:

Usa los patrones históricos

Proyecta días futuros

Calcula capacidad:

capacidad = pasajeros / ocupacion


Determina riesgo y estado

🎯 Buenas Prácticas de Reproducibilidad

✔ Semilla fija:

np.random.seed(42)


✔ Entorno reproducible (requirements.txt)
✔ Script opcional para Windows:

setup_env.ps1
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
Write-Host "Entorno configurado correctamente."

🧪 Testing

Ejecutar:

pytest tests/ -v


Cobertura:

pytest tests/ --cov=. --cov-report=html

🛡️ Roles y Permisos

👑 Administrador

Reportes

Gráficos

Mapas

Estaciones en riesgo

👷 Operario

Mapas

Estaciones en riesgo

👤 Usuario

Solo tablas

🔐 Autenticación

Implementado con Firebase Authentication

Credenciales cargadas mediante .env

Seguridad reforzada evitando exponer claves

🤝 Contribución

Fork

Rama

Commit

Push

Pull Request

📝 Mejoras Futuras

 Dashboard web (Streamlit)

 API REST

 Optimización del Random Forest

 Incremento de cobertura de tests