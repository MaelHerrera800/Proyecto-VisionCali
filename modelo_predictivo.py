import pandas as pd
import numpy as np
import warnings
from datetime import timedelta
import os
# Scikit-learn imports
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    mean_squared_error, r2_score, mean_absolute_error, classification_report
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

warnings.filterwarnings("ignore")

if not os.path.exists("data_limpia_mio.xlsx"):
    try:
        from limpieza_mio import ObjetoDeDatos, df_terminales
        objeto_datos = ObjetoDeDatos(df_terminales)
        df_limpio = objeto_datos.limpiar_datos()  
        if df_limpio is not None:
            print("Archivo 'data_limpia_mio.xlsx' generado exitosamente.")
        else:
            print("No se pudo generar el DataFrame de data limpia.")

    except Exception as e:
        print("Error generando la data limpia:", e)

df_limpio = pd.read_excel("data_limpia_mio.xlsx")
class ModeloPredictivoMIO_sklearn:

    def __init__(self, usar_ultimo_mes=True, usar_random_forest=True):

        if usar_ultimo_mes:
            fecha_max = pd.to_datetime(df_limpio["Fecha"]).max()
            fecha_min = fecha_max - pd.Timedelta(days=30)
            self.df = df_limpio[df_limpio["Fecha"] >= fecha_min].copy()
        else:
            self.df = df_limpio.copy()

        self.usar_random_forest = usar_random_forest
        self._preparar_datos()

        # Modelos y escaladores
        self.modelo_ocupacion = None
        self.modelo_colapso = None
        self.scaler_ocupacion = StandardScaler()
        self.scaler_colapso = StandardScaler()
        self.label_encoders = {}
        self.df_predicciones = None



    # ===========================================================
    # PREPARAR DATOS
    # ===========================================================
    def _preparar_datos(self):

        columnas = [
            "Terminal", "Fecha", "Franja Horaria", "Día de la Semana",
            "Capacidad Máxima", "Personas Actuales", "Estado"
        ]

        self.df = self.df.dropna(subset=columnas)

        self.df["Fecha"] = pd.to_datetime(self.df["Fecha"], errors="coerce")
        self.df["Capacidad Máxima"] = pd.to_numeric(self.df["Capacidad Máxima"], errors="coerce")
        self.df["Personas Actuales"] = pd.to_numeric(self.df["Personas Actuales"], errors="coerce")

        self.df = self.df[self.df["Franja Horaria"] != "Desconocida"]

        # Calcular ocupación
        self.df["Ocupacion"] = np.where(
            self.df["Capacidad Máxima"] > 0,
            self.df["Personas Actuales"] / self.df["Capacidad Máxima"],
            np.nan
        )

        self.df = self.df.dropna(subset=["Ocupacion"])

        self.df["Colapsada"] = (self.df["Ocupacion"] > 0.80).astype(int)

        # Unificar nombres de días
        self.df["Día de la Semana"] = pd.to_datetime(self.df["Fecha"]).dt.day_name()



    # ===========================================================
    # ENCODING DE VARIABLES
    # ===========================================================
    def _preparar_features(self, df, entrenar=True):

        df_features = df.copy()
        categoricas = ['Terminal', 'Franja Horaria', 'Día de la Semana']

        if entrenar:
            for col in categoricas:
                le = LabelEncoder()
                df_features[f'{col}_encoded'] = le.fit_transform(df_features[col].astype(str))
                self.label_encoders[col] = le
        else:
            for col in categoricas:
                le = self.label_encoders[col]
                df_features[f'{col}_encoded'] = df_features[col].astype(str).apply(
                    lambda x: le.transform([x])[0] if x in le.classes_ else -1
                )

        features_numericas = ['Capacidad Máxima'] + [f'{col}_encoded' for col in categoricas]
        return df_features[features_numericas]



    # ===========================================================
    # MODELO DE OCUPACIÓN
    # ===========================================================
    def entrenar_modelo_ocupacion(self):

        X = self._preparar_features(self.df, entrenar=True)
        y = self.df["Ocupacion"].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        X_train_scaled = self.scaler_ocupacion.fit_transform(X_train)
        X_test_scaled = self.scaler_ocupacion.transform(X_test)

        if self.usar_random_forest:
            self.modelo_ocupacion = RandomForestRegressor(
                n_estimators=100, #numeros de arboles
                max_depth=20,  #evita sobreajuste
                min_samples_split=5, #mínimo 5 datos por división
                random_state=42 # es reproducible
            )
        else:
            self.modelo_ocupacion = LinearRegression() #nota este es por si llega a ver errores con el randomforest anque es menos pontente que este

        self.modelo_ocupacion.fit(X_train_scaled, y_train)
        y_test_pred = self.modelo_ocupacion.predict(X_test_scaled)

        r2 = r2_score(y_test, y_test_pred)
        print(f"Modelo de ocupación entrenado correctamente (R² = {r2:.3f})")



    # ===========================================================
    # MODELO DE COLAPSO
    # ===========================================================
    def entrenar_modelo_colapso(self):

        X = self._preparar_features(self.df, entrenar=True)
        X["Ocupacion"] = self.df["Ocupacion"].values
        y = self.df["Colapsada"].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        X_train_scaled = self.scaler_colapso.fit_transform(X_train)
        X_test_scaled = self.scaler_colapso.transform(X_test)

        if self.usar_random_forest:
            self.modelo_colapso = RandomForestClassifier(
                n_estimators=100, #numeros de arboles
                max_depth=20,
                min_samples_split=5,#mínimo 5 datos por división
                class_weight='balanced',
                random_state=42
            )
        else:
            self.modelo_colapso = LogisticRegression(
                class_weight='balanced',
                max_iter=1000, #max_iter=1000
                random_state=42
            )

        self.modelo_colapso.fit(X_train_scaled, y_train)
        self.columnas_colapso = list(X.columns)

        y_test_pred = self.modelo_colapso.predict(X_test_scaled)
        reporte = classification_report(y_test, y_test_pred, target_names=["Estable", "Colapsada"])

        print("Modelo de colapso entrenado correctamente")
        print(reporte)



    # ===========================================================
    #  GENERAR FECHAS FUTURAS
    # ===========================================================
    def generar_fechas_futuras(self, dias_futuros=5):

        fecha_max = self.df["Fecha"].max()

        fechas_futuras = pd.date_range(
            start=fecha_max + timedelta(days=1),
            periods=dias_futuros,
            freq="D"
        )

        terminales = self.df["Terminal"].unique()
        franjas = [f for f in self.df["Franja Horaria"].unique() if f != "Desconocida"]

        escenarios = []

        print(f"Generando escenarios futuros ({len(terminales)} terminales × {len(franjas)} franjas × {len(fechas_futuras)} días)...")

        for fecha in fechas_futuras:
            dia_semana = fecha.day_name()
            for terminal in terminales:
                for franja in franjas:
                    hist = self.df[
                        (self.df["Terminal"] == terminal) &
                        (self.df["Franja Horaria"] == franja)
                    ]

                    cap = hist["Capacidad Máxima"].median() if len(hist) > 0 else self.df["Capacidad Máxima"].median()

                    escenarios.append({
                        "Terminal": terminal,
                        "Fecha": fecha,
                        "Día de la Semana": dia_semana,
                        "Franja Horaria": franja,
                        "Capacidad Máxima": cap
                    })

        df_futuro = pd.DataFrame(escenarios)
        print(f"Escenarios generados: {len(df_futuro)} registros.")
        return df_futuro



    # ===========================================================
    # 🔮 PREDICCIÓN COMPLETA
    # ===========================================================
    def predecir(self, incluir_futuro=True, dias_futuros=5):

        if self.modelo_ocupacion is None:
            print("No hay modelo de ocupación entrenado.")
            return None

        df = self.df.copy()

        if incluir_futuro:
            df = self.generar_fechas_futuras(dias_futuros)

        # Predicción de ocupación
        X = self._preparar_features(df, entrenar=True)
        X_scaled = self.scaler_ocupacion.transform(X)

        ocupacion_pred = np.clip(
            self.modelo_ocupacion.predict(X_scaled),
            0.1,
            2.0
        )

        df["Ocupacion"] = ocupacion_pred
        df["Personas_Predichas"] = (df["Ocupacion"] * df["Capacidad Máxima"]).round().astype(int)

        # Predicción de colapso
        if self.modelo_colapso is not None:

            X_colapso = X.copy()
            X_colapso["Ocupacion"] = ocupacion_pred

            columnas_entrenamiento = getattr(self, "columnas_colapso", X_colapso.columns)
            X_colapso = X_colapso[columnas_entrenamiento]

            X_colapso_scaled = self.scaler_colapso.transform(X_colapso)
            prob_colapso = self.modelo_colapso.predict_proba(X_colapso_scaled)[:, 1]

            df["Prob_Colapso"] = prob_colapso
            df["Estado_Previsto"] = np.select(
                [df["Prob_Colapso"] > 0.65],
                ["Colapsará"],
                default="Estable"
            )

        self.df_predicciones = df
        print("Predicciones generadas correctamente")
        return df



    # ===========================================================
    # 💾 GUARDAR RESULTADOS
    # ===========================================================
    def guardar_predicciones(self, archivo="predicciones_mio.xlsx"):

        if self.df_predicciones is None:
            print("⚠️ No hay predicciones para guardar.")
            return

        df_export = self.df_predicciones.copy()
        df_export["Fecha"] = pd.to_datetime(df_export["Fecha"]).dt.date

        df_export = df_export[df_export["Franja Horaria"] != "Desconocida"]

        
        columnas = [
            "Fecha", "Día de la Semana", "Terminal", "Franja Horaria",
            "Capacidad Máxima", "Ocupacion", "Personas_Predichas",
            "Prob_Colapso", "Estado_Previsto"
        ]

        columnas_finales = [c for c in columnas if c in df_export.columns]
        df_export = df_export[columnas_finales]

        df_export.to_excel(archivo, index=False)

        print(f"Archivo guardado correctamente: {archivo}")
        print(f"Total de registros: {len(df_export)}")



# ===========================================================
# BLOQUE PRINCIPAL
# ===========================================================
if __name__ == "__main__":

    print("\nIniciando sistema predictivo del MIO...\n")

    modelo = ModeloPredictivoMIO_sklearn(
        usar_ultimo_mes=False,
        usar_random_forest=True
    )

    modelo.entrenar_modelo_ocupacion()
    modelo.entrenar_modelo_colapso()

    df_pred = modelo.predecir(incluir_futuro=True, dias_futuros=5)

    if df_pred is not None:
        modelo.guardar_predicciones()
        print("\nProceso completado con éxito.")
    else:
        print("\nNo se generaron predicciones.")



def generar_predicciones_desde_archivo(data_limpia_path: str = None, usar_ultimo_mes: bool = True, usar_random_forest: bool = True):
    """
    Conveniencia: carga data limpia (si no se proporciona, busca en BASE_DIR),
    entrena modelos y genera + guarda predicciones.
    """
    if data_limpia_path is None:
        data_limpia_path = os.path.join(BASE_DIR, "data_limpia_mio.xlsx")

    if not os.path.exists(data_limpia_path):
        raise FileNotFoundError(f"No se encontró {data_limpia_path}. Genera data_limpia_mio.xlsx primero.")

    df_limpio = pd.read_excel(data_limpia_path)
    modelo = ModeloPredictivoMIO_sklearn(df_limpio, usar_ultimo_mes=usar_ultimo_mes, usar_random_forest=usar_random_forest)
    modelo.entrenar_modelo_ocupacion()
    modelo.entrenar_modelo_colapso()
    df_pred = modelo.predecir(incluir_futuro=True, dias_futuros=5)
    modelo.guardar_predicciones()
    return df_pred