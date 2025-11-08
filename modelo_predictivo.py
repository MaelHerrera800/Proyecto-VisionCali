import pandas as pd
import numpy as np
import warnings
from datetime import timedelta

# Scikit-learn imports
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    mean_squared_error, r2_score, mean_absolute_error,
    classification_report
)

from limpieza_mio import df_limpio

warnings.filterwarnings("ignore")


class ModeloPredictivoMIO_sklearn:
    def __init__(self, usar_ultimo_mes=False, usar_random_forest=True):
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
    # 🧹 PREPARAR DATOS
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

        # Calcular ocupación
        self.df["Ocupacion"] = np.where(
            self.df["Capacidad Máxima"] > 0,
            self.df["Personas Actuales"] / self.df["Capacidad Máxima"],
            np.nan
        )
        self.df = self.df.dropna(subset=["Ocupacion"])
        self.df["Colapsada"] = (self.df["Ocupacion"] > 0.95).astype(int)

        # Unificar nombres de días
        self.df["Día de la Semana"] = pd.to_datetime(self.df["Fecha"]).dt.day_name()

    # ===========================================================
    # 🔧 ENCODING DE VARIABLES
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
    # 📈 MODELO DE OCUPACIÓN
    # ===========================================================
    def entrenar_modelo_ocupacion(self):
        X = self._preparar_features(self.df, entrenar=True)
        y = self.df["Ocupacion"].values

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        X_train_scaled = self.scaler_ocupacion.fit_transform(X_train)
        X_test_scaled = self.scaler_ocupacion.transform(X_test)

        if self.usar_random_forest:
            self.modelo_ocupacion = RandomForestRegressor(
                n_estimators=100, max_depth=20, min_samples_split=5, random_state=42
            )
        else:
            self.modelo_ocupacion = LinearRegression()

        self.modelo_ocupacion.fit(X_train_scaled, y_train)
        y_test_pred = self.modelo_ocupacion.predict(X_test_scaled)
        r2 = r2_score(y_test, y_test_pred)

        print(f"✅ Modelo de ocupación entrenado correctamente (R² = {r2:.3f})")

    # ===========================================================
    # 🔍 MODELO DE COLAPSO
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
                n_estimators=100, max_depth=20, min_samples_split=5,
                class_weight='balanced', random_state=42
            )
        else:
            self.modelo_colapso = LogisticRegression(
                class_weight='balanced', max_iter=1000, random_state=42
            )

        self.modelo_colapso.fit(X_train_scaled, y_train)
        self.columnas_colapso = list(X.columns)

        y_test_pred = self.modelo_colapso.predict(X_test_scaled)
        reporte = classification_report(y_test, y_test_pred, target_names=["Estable", "Colapsada"])
        print("✅ Modelo de colapso entrenado correctamente")
        print(reporte)

    # ===========================================================
    # 🔮 GENERAR FECHAS FUTURAS — VERSIÓN COMPLETA Y ROBUSTA
    # ===========================================================
    def generar_fechas_futuras(self, dias_futuros=5):
        fecha_max = self.df["Fecha"].max()
        fechas_futuras = pd.date_range(
            start=fecha_max + timedelta(days=1),
            periods=dias_futuros,
            freq="D"
        )

        terminales = self.df["Terminal"].unique()
        franjas = self.df["Franja Horaria"].unique()
        escenarios = []

        print(f"🧩 Generando escenarios futuros ({len(terminales)} terminales × {len(franjas)} franjas × {len(fechas_futuras)} días)...")

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
        print(f"✅ Escenarios generados: {len(df_futuro)} registros.")
        return df_futuro

    # ===========================================================
    # 🔮 PREDICCIÓN COMPLETA
    # ===========================================================
    def predecir(self, incluir_futuro=True, dias_futuros=5):
        if self.modelo_ocupacion is None:
            print("⚠️ No hay modelo de ocupación entrenado.")
            return None

        df = self.df.copy()
        if incluir_futuro:
            df = self.generar_fechas_futuras(dias_futuros)

        # --- Predicción de ocupación ---
        X = self._preparar_features(df, entrenar=False)
        X_scaled = self.scaler_ocupacion.transform(X)
        ocupacion_pred = np.clip(self.modelo_ocupacion.predict(X_scaled), 0.1, 2.0)

        df["Ocupacion"] = ocupacion_pred
        df["Personas_Predichas"] = (df["Ocupacion"] * df["Capacidad Máxima"]).round().astype(int)

        # --- Predicción de colapso ---
        if self.modelo_colapso is not None:
            X_colapso = X.copy()
            X_colapso["Ocupacion"] = ocupacion_pred

            columnas_entrenamiento = getattr(self, "columnas_colapso", X_colapso.columns)
            X_colapso = X_colapso[columnas_entrenamiento]

            X_colapso_scaled = self.scaler_colapso.transform(X_colapso)
            prob_colapso = self.modelo_colapso.predict_proba(X_colapso_scaled)[:, 1]

            df["Prob_Colapso"] = prob_colapso
            df["Estado_Previsto"] = np.select(
                [
                    df["Prob_Colapso"] > 0.75,
                    (df["Prob_Colapso"] > 0.5) & (df["Prob_Colapso"] <= 0.75),
                    (df["Prob_Colapso"] > 0.25) & (df["Prob_Colapso"] <= 0.5),
                    df["Prob_Colapso"] <= 0.25
                ],
                ["Colapsará", "Alto Riesgo", "Riesgo Moderado", "Estable"],
                default="Desconocido"
            )

        self.df_predicciones = df
        print("✅ Predicciones generadas correctamente")
        return df

    # ===========================================================
    # 💾 GUARDAR RESULTADOS ORDENADOS
    # ===========================================================
    def guardar_predicciones(self, archivo="predicciones_mio_sklearn.xlsx"):
        if self.df_predicciones is None:
            print("⚠️ No hay predicciones para guardar.")
            return

        df_export = self.df_predicciones.copy()
        df_export["Fecha"] = pd.to_datetime(df_export["Fecha"]).dt.date

        # 🔧 Eliminar franjas desconocidas
        df_export = df_export[df_export["Franja Horaria"] != "Desconocida"]

        # 🔧 Ordenar franjas horarias cronológicamente
        def extraer_hora_inicio(franja):
            try:
                return int(franja.split(":")[0])
            except:
                return 0

        df_export["Hora_Inicio"] = df_export["Franja Horaria"].apply(extraer_hora_inicio)
        df_export = df_export.sort_values(by=["Fecha", "Terminal", "Hora_Inicio"]).reset_index(drop=True)

        columnas = [
            "Fecha", "Día de la Semana", "Terminal", "Franja Horaria",
            "Capacidad Máxima", "Ocupacion", "Personas_Predichas",
            "Prob_Colapso", "Estado_Previsto"
        ]
        columnas_finales = [c for c in columnas if c in df_export.columns]
        df_export = df_export[columnas_finales]

        df_export.to_excel(archivo, index=False)
        print(f"💾 Archivo guardado correctamente: {archivo}")
        print(f"📊 Total de registros: {len(df_export)}")


# ===========================================================
# 🧠 BLOQUE PRINCIPAL
# ===========================================================
if __name__ == "__main__":
    print("\n🚀 Iniciando sistema predictivo del MIO...\n")

    modelo = ModeloPredictivoMIO_sklearn(usar_ultimo_mes=False, usar_random_forest=True)

    modelo.entrenar_modelo_ocupacion()
    modelo.entrenar_modelo_colapso()
    df_pred = modelo.predecir(incluir_futuro=True, dias_futuros=5)

    if df_pred is not None:
        modelo.guardar_predicciones()
        print("\n✅ Proceso completado con éxito.")
    else:
        print("\n⚠️ No se generaron predicciones.")
