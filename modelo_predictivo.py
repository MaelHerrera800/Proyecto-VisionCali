import pandas as pd
import numpy as np
import statsmodels.api as sm
import warnings
from datetime import datetime, timedelta
from limpieza_mio import df_limpio

warnings.filterwarnings("ignore")


class ModeloPredictivoMIO:
    def __init__(self, usar_ultimo_mes=False):
        """
        Inicializa el modelo con los datos limpios.
        Args:
            usar_ultimo_mes: Si True, filtra solo el último mes (por defecto False)
        """
        if usar_ultimo_mes:
            fecha_max = pd.to_datetime(df_limpio["Fecha"]).max()
            fecha_min = fecha_max - pd.Timedelta(days=30)
            self.df = df_limpio[df_limpio["Fecha"] >= fecha_min].copy()
            print("📆 Usando solo datos del último mes.")
        else:
            self.df = df_limpio.copy()
            print("📊 Usando todos los datos históricos.")

        self._preparar_datos()
        self.modelo_ols = None
        self.modelo_logit = None
        self.logit_columns = None
        self.df_predicciones = None

    # ===========================================================
    # 🧹 PREPARACIÓN DE DATOS
    # ===========================================================
    def _preparar_datos(self):
        """Prepara datos con métodos modernos de pandas."""
        columnas_necesarias = [
            "Terminal", "Fecha", "Franja Horaria", "Día de la Semana",
            "Capacidad Máxima", "Personas Actuales", "Estado"
        ]

        for col in columnas_necesarias:
            if col not in self.df.columns:
                raise KeyError(f"❌ Falta la columna requerida: '{col}' en df_limpio")

        # Convertir fechas
        self.df["Fecha"] = pd.to_datetime(self.df["Fecha"], errors="coerce")
        self.df = self.df.dropna(subset=["Terminal", "Fecha", "Personas Actuales", "Capacidad Máxima"])

        # Convertir a numérico
        self.df["Capacidad Máxima"] = pd.to_numeric(self.df["Capacidad Máxima"], errors="coerce")
        self.df["Personas Actuales"] = pd.to_numeric(self.df["Personas Actuales"], errors="coerce")
        self.df = self.df.dropna(subset=["Capacidad Máxima", "Personas Actuales"])

        # Calcular ocupación
        self.df["Ocupacion"] = np.where(
            self.df["Capacidad Máxima"] > 0,
            self.df["Personas Actuales"] / self.df["Capacidad Máxima"],
            np.nan
        )
        self.df = self.df.replace([np.inf, -np.inf], np.nan).dropna(subset=["Ocupacion"])

        # Variable binaria para colapso
        self.df["Colapsada"] = (
            self.df["Estado"].astype(str).str.strip().str.lower() == "colapsada"
        ).astype(int)

        print(f"✅ Datos preparados: {len(self.df)} registros válidos.")
        print(f" - Colapsadas: {self.df['Colapsada'].sum()}")
        print(f" - Estables: {(self.df['Colapsada'] == 0).sum()}")

    # ===========================================================
    # 📈 MODELO OLS
    # ===========================================================
    def entrenar_modelo_regresion(self):
        """Entrena un modelo de regresión lineal (OLS) para predecir Personas."""
        try:
            X = self.df[["Capacidad Máxima", "Ocupacion"]].astype(float)
            X = sm.add_constant(X)
            y = self.df["Personas Actuales"].astype(float)

            self.modelo_ols = sm.OLS(y, X).fit()
            print("✅ Modelo de regresión (OLS) entrenado correctamente.")
            print(f" R² = {self.modelo_ols.rsquared:.4f}")
            return self.modelo_ols

        except Exception as e:
            print(f"❌ Error al entrenar el modelo OLS: {e}")
            return None

    # ===========================================================
    # 🔍 MODELO LOGIT - VERSIÓN MEJORADA
    # ===========================================================
    def entrenar_modelo_colapso(self):
        """Entrena un modelo Logit con validaciones robustas."""
        try:
            print("\n" + "="*60)
            print("🔍 VALIDANDO DATOS PARA MODELO LOGIT")
            print("="*60)

            num_colapsadas = self.df["Colapsada"].sum()
            num_estables = (self.df["Colapsada"] == 0).sum()
            total = len(self.df)

            print(f"📊 Total: {total}")
            print(f" Colapsadas: {num_colapsadas}")
            print(f" Estables: {num_estables}")

            if num_colapsadas < 5 or num_estables < 5 or total < 20:
                print("⚠️ Datos insuficientes para entrenar el modelo Logit.")
                return None

            # Preparar variables
            dummies_franja = pd.get_dummies(
                self.df["Franja Horaria"].astype(str),
                prefix="Franja", drop_first=True, dtype=int
            )
            dummies_dia = pd.get_dummies(
                self.df["Día de la Semana"].astype(str),
                prefix="Dia", drop_first=True, dtype=int
            )

            X = pd.concat([self.df[["Ocupacion"]], dummies_franja, dummies_dia], axis=1)
            X = sm.add_constant(X, has_constant='add')
            y = self.df["Colapsada"].astype(float)

            # Eliminar NaN
            mask = X.notnull().all(axis=1) & y.notnull()
            X_clean = X[mask].astype(float)
            y_clean = y[mask].astype(float)

            print(f"📈 Datos válidos: {len(X_clean)} observaciones")

            modelo = sm.Logit(y_clean, X_clean).fit(method="lbfgs", maxiter=200, disp=False)
            self.modelo_logit = modelo
            self.logit_columns = X_clean.columns.tolist()

            print("✅ Modelo LOGIT entrenado correctamente.")
            print(f" Pseudo R² = {modelo.prsquared:.4f}")
            print(f" AIC = {modelo.aic:.2f}")
            return modelo

        except Exception as e:
            print(f"❌ Error al entrenar el modelo Logit: {e}")
            return None

    # ===========================================================
    # 🔮 PREDICCIÓN FUTURA
    # ===========================================================
    def generar_fechas_futuras(self, dias_futuros=5):
        """Genera predicciones para los próximos N días."""
        fecha_max = self.df["Fecha"].max()
        fechas_futuras = pd.date_range(start=fecha_max + timedelta(days=1),
                                       periods=dias_futuros, freq='D')
        terminales = self.df["Terminal"].unique()
        escenarios = []

        for fecha in fechas_futuras:
            for terminal in terminales:
                hist = self.df[self.df["Terminal"] == terminal]
                if len(hist) > 0:
                    franja = hist["Franja Horaria"].mode()[0]
                    cap = hist["Capacidad Máxima"].median()
                    ocup = hist["Ocupacion"].median()
                else:
                    franja = self.df["Franja Horaria"].mode()[0]
                    cap = self.df["Capacidad Máxima"].median()
                    ocup = self.df["Ocupacion"].median()

                escenarios.append({
                    "Terminal": terminal,
                    "Fecha": fecha,
                    "Día de la Semana": fecha.day_name(),
                    "Franja Horaria": franja,
                    "Capacidad Máxima": cap,
                    "Ocupacion": ocup,
                    "Personas Actuales": cap * ocup
                })

        df_futuro = pd.DataFrame(escenarios)
        print(f"📅 Generadas predicciones para {dias_futuros} días ({len(df_futuro)} registros)")
        return df_futuro

    # ===========================================================
    # 📊 PREDICCIÓN COMPLETA
    # ===========================================================
    def predecir(self, incluir_futuro=True, dias_futuros=5):
        """Genera predicciones usando OLS y Logit."""
        if self.modelo_ols is None and self.modelo_logit is None:
            print("⚠️ No hay modelos entrenados.")
            return None

        df = self.generar_fechas_futuras(dias_futuros) if incluir_futuro else self.df.copy()

        # Predicción OLS
        if self.modelo_ols is not None:
            try:
                X_reg = sm.add_constant(df[["Capacidad Máxima", "Ocupacion"]].astype(float), has_constant='add')
                df["Personas_Predichas"] = self.modelo_ols.predict(X_reg).clip(lower=0).round().astype("Int64")
            except Exception as e:
                print(f"⚠️ Error en predicción OLS: {e}")
                df["Personas_Predichas"] = pd.NA

        # Predicción Logit
        if self.modelo_logit is not None and self.logit_columns is not None:
            try:
                dummies_franja = pd.get_dummies(df["Franja Horaria"].astype(str), prefix="Franja", drop_first=True, dtype=int)
                dummies_dia = pd.get_dummies(df["Día de la Semana"].astype(str), prefix="Dia", drop_first=True, dtype=int)
                X_logit = pd.concat([df[["Ocupacion"]], dummies_franja, dummies_dia], axis=1)
                X_logit = sm.add_constant(X_logit, has_constant='add')

                for col in self.logit_columns:
                    if col not in X_logit.columns:
                        X_logit[col] = 0
                X_logit = X_logit[self.logit_columns].astype(float)

                df["Prob_Colapso"] = self.modelo_logit.predict(X_logit)
                df["Estado_Previsto"] = np.select(
                    [
                        df["Prob_Colapso"] > 0.7,
                        (df["Prob_Colapso"] > 0.4) & (df["Prob_Colapso"] <= 0.7),
                        df["Prob_Colapso"] <= 0.4
                    ],
                    ["Colapsará", "Riesgo de Colapso", "Estable"],
                    default="Desconocido"
                )
                print("✅ Predicciones de colapso generadas.")
            except Exception as e:
                print(f"⚠️ Error en predicción Logit: {e}")
                df["Prob_Colapso"] = np.nan
                df["Estado_Previsto"] = "No disponible"

        self.df_predicciones = df.copy()
        return df

    # ===========================================================
    # 💾 GUARDAR RESULTADOS
    # ===========================================================
    def guardar_predicciones(self, archivo="predicciones_mio.xlsx"):
        """Guarda predicciones en Excel con formato mejorado."""
        if self.df_predicciones is not None:
            df_export = self.df_predicciones.copy()
            df_export["Fecha"] = pd.to_datetime(df_export["Fecha"]).dt.date
            df_export.to_excel(archivo, index=False)
            print(f"\n💾 Archivo guardado: {archivo}")
            print(f" Total registros: {len(df_export)}")

            if "Estado_Previsto" in df_export.columns:
                print("\n📊 Estados previstos:")
                for estado, count in df_export["Estado_Previsto"].value_counts().items():
                    print(f" - {estado}: {count}")
        else:
            print("⚠️ No hay predicciones para guardar.")


# ===========================================================
# 🧠 BLOQUE PRINCIPAL
# ===========================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 SISTEMA PREDICTIVO MIO - PREDICCIÓN 5 DÍAS")
    print("="*60 + "\n")

    modelo = ModeloPredictivoMIO(usar_ultimo_mes=False)

    print("\n📊 ENTRENANDO MODELOS...")
    modelo.entrenar_modelo_regresion()
    modelo.entrenar_modelo_colapso()

    print("\n🔮 GENERANDO PREDICCIONES PARA LOS PRÓXIMOS 5 DÍAS...")
    df_pred = modelo.predecir(incluir_futuro=True, dias_futuros=5)

    if df_pred is not None:
        modelo.guardar_predicciones()
        print("\n📋 PREDICCIONES GENERADAS CON ÉXITO")
    else:
        print("\n⚠️ No se pudieron generar predicciones.")
