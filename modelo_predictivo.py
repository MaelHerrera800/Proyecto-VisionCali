import pandas as pd
import numpy as np
import statsmodels.api as sm
import warnings
from datetime import datetime, timedelta
from limpieza_mio import df_limpio, obtener_ultimo_mes

warnings.filterwarnings("ignore")


class ModeloPredictivoMIO:
    def __init__(self, usar_ultimo_mes=False):
        """
        Inicializa el modelo con los datos limpios.
        
        Args:
            usar_ultimo_mes: Si True, filtra solo el último mes (CAMBIADO A FALSE POR DEFECTO)
        """
        if usar_ultimo_mes:
            self.df = obtener_ultimo_mes()
            print("🎯 Usando datos del último mes para entrenar el modelo")
        else:
            self.df = df_limpio.copy()
            print("📊 Usando todos los datos históricos")
            
        self._preparar_datos()
        self.modelo_ols = None
        self.modelo_logit = None
        self.logit_columns = None
        self.df_predicciones = None

    # ===========================================================
    # PREPARACIÓN DE DATOS
    # ===========================================================
    def _preparar_datos(self):
        """Prepara datos con métodos modernos de pandas"""
        columnas_necesarias = [
            "Terminal", "Fecha", "Franja Horaria",
            "Día de la Semana", "Capacidad Máxima",
            "Personas Actuales", "Estado"
        ]
        
        for col in columnas_necesarias:
            if col not in self.df.columns:
                raise KeyError(f"❌ Falta la columna requerida: '{col}' en df_limpio")

        # Convertir fechas
        self.df = self.df.assign(Fecha=pd.to_datetime(self.df["Fecha"], errors="coerce"))
        self.df = self.df.dropna(subset=["Terminal", "Fecha", "Personas Actuales", "Capacidad Máxima"])
        
        # Convertir a numérico
        self.df = self.df.assign(
            **{
                "Capacidad Máxima": pd.to_numeric(self.df["Capacidad Máxima"], errors="coerce"),
                "Personas Actuales": pd.to_numeric(self.df["Personas Actuales"], errors="coerce")
            }
        )
        
        self.df = self.df.dropna(subset=["Capacidad Máxima", "Personas Actuales"])

        # Calcular ocupación
        self.df = self.df.assign(
            Ocupacion=lambda x: np.where(
                x["Capacidad Máxima"] > 0,
                x["Personas Actuales"] / x["Capacidad Máxima"],
                np.nan
            )
        )
        
        self.df = self.df.replace([np.inf, -np.inf], np.nan)
        self.df = self.df.dropna(subset=["Ocupacion"])

        # Variable binaria para colapso (MEJORADA)
        self.df = self.df.assign(
            Colapsada=(
                self.df["Estado"].astype(str).str.strip().str.lower() == "colapsada"
            ).astype(int)
        )

        print(f"✅ Datos preparados: {len(self.df)} registros válidos.")
        print(f"   - Colapsadas: {self.df['Colapsada'].sum()}")
        print(f"   - Estables: {(self.df['Colapsada'] == 0).sum()}")

    # ===========================================================
    # MODELO OLS
    # ===========================================================
    def entrenar_modelo_regresion(self):
        """Entrena un modelo de regresión lineal (OLS) para predecir Personas."""
        try:
            X = self.df[["Capacidad Máxima", "Ocupacion"]].astype(float)
            X = sm.add_constant(X)
            y = self.df["Personas Actuales"].astype(float)

            self.modelo_ols = sm.OLS(y, X).fit()
            print("✅ Modelo de regresión (OLS) entrenado correctamente.")
            print(f"   R² = {self.modelo_ols.rsquared:.4f}")
            return self.modelo_ols
        except Exception as e:
            print(f"❌ Error al entrenar el modelo OLS: {e}")
            return None

    # ===========================================================
    # MODELO LOGIT - VERSIÓN MEJORADA Y CORREGIDA
    # ===========================================================
    def entrenar_modelo_colapso(self):
        """Entrena un modelo Logit con validaciones robustas y múltiples métodos."""
        try:
            print("\n" + "="*60)
            print("🔍 VALIDANDO DATOS PARA MODELO LOGIT")
            print("="*60)
            
            # 1. VERIFICAR VARIABILIDAD
            num_colapsadas = self.df["Colapsada"].sum()
            num_estables = (self.df["Colapsada"] == 0).sum()
            total = len(self.df)
            
            print(f"📊 Estadísticas:")
            print(f"   Total: {total}")
            print(f"   Colapsadas: {num_colapsadas} ({num_colapsadas/total*100:.1f}%)")
            print(f"   Estables: {num_estables} ({num_estables/total*100:.1f}%)")
            
            # 2. VALIDACIÓN CRÍTICA
            if num_colapsadas < 5 or num_estables < 5:
                print("\n⚠️ DATOS INSUFICIENTES PARA LOGIT")
                print("   Se necesitan al menos 5 casos de cada tipo")
                print("\n💡 SOLUCIONES:")
                print("   1. Usa usar_ultimo_mes=False (ya es el default)")
                print("   2. Revisa limpieza_mio.py para generar más datos colapsados")
                print("   3. Verifica que la columna 'Estado' contenga 'colapsada'")
                return None
            
            if total < 20:
                print("\n⚠️ Muy pocos registros totales (<20)")
                return None
            
            # 3. PREPARAR VARIABLES
            print("\n🔧 Preparando variables...")
            
            dummies_franja = pd.get_dummies(
                self.df["Franja Horaria"].astype(str),
                prefix="Franja",
                drop_first=True,
                dtype=int
            )
            
            dummies_dia = pd.get_dummies(
                self.df["Día de la Semana"].astype(str),
                prefix="Dia",
                drop_first=True,
                dtype=int
            )

            X = pd.concat([self.df[["Ocupacion"]], dummies_franja, dummies_dia], axis=1)
            X = X.apply(pd.to_numeric, errors="coerce")
            X = sm.add_constant(X, has_constant='add')
            y = pd.to_numeric(self.df["Colapsada"], errors="coerce")
            
            # 4. FILTRAR NULOS
            mask = X.notnull().all(axis=1) & y.notnull()
            X_clean = X[mask].astype(float)
            y_clean = y[mask].astype(float)
            
            print(f"   Variables: {X_clean.shape[1]}")
            print(f"   Observaciones válidas: {len(X_clean)}")

            if len(X_clean) < 20:
                print("⚠️ Muy pocos registros válidos después de filtrar")
                return None
            
            # 5. ENTRENAR CON MÚLTIPLES MÉTODOS
            print("\n🎯 Entrenando modelo...")
            
            metodos = [
                ('bfgs', 200, True),
                ('newton', 150, True),
                ('lbfgs', 200, False),
                ('nm', 300, False),
            ]
            
            modelo_entrenado = None
            
            for metodo, max_iter, usar_hess in metodos:
                try:
                    print(f"   Método {metodo}...", end=" ")
                    
                    kwargs = {
                        'method': metodo,
                        'maxiter': max_iter,
                        'disp': False,
                        'warn_convergence': False
                    }
                    
                    modelo = sm.Logit(y_clean, X_clean).fit(**kwargs)
                    
                    if modelo.mle_retvals.get('converged', False):
                        print("✅")
                        modelo_entrenado = modelo
                        break
                    else:
                        print("⚠️")
                        
                except Exception as e:
                    print(f"❌")
                    continue
            
            # 6. VALIDAR Y GUARDAR
            if modelo_entrenado is None:
                print("\n⚠️ Ningún método convergió")
                print("   Posibles causas:")
                print("   - Separación perfecta de clases")
                print("   - Multicolinealidad severa")
                print("   - Muy poca variabilidad")
                return None
            
            self.modelo_logit = modelo_entrenado
            self.logit_columns = X_clean.columns.tolist()
            
            print("\n✅ MODELO LOGIT ENTRENADO")
            print("="*60)
            print(f"   Pseudo R² = {modelo_entrenado.prsquared:.4f}")
            print(f"   AIC = {modelo_entrenado.aic:.2f}")
            print(f"   Log-Likelihood = {modelo_entrenado.llf:.2f}")
            
            # Coeficientes significativos
            params_sig = modelo_entrenado.pvalues[modelo_entrenado.pvalues < 0.05]
            if len(params_sig) > 0:
                print(f"\n   Variables significativas (p<0.05): {len(params_sig)}")
            
            print("="*60 + "\n")
            return modelo_entrenado

        except Exception as e:
            print("\n❌ ERROR INESPERADO:")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None

    # ===========================================================
    # PREDICCIÓN PARA FECHAS FUTURAS
    # ===========================================================
    def generar_fechas_futuras(self, dias_futuros=3):
        """Genera fechas futuras basándose en datos históricos."""
        fecha_max = self.df["Fecha"].max()
        fechas_futuras = pd.date_range(
            start=fecha_max + timedelta(days=1),
            periods=dias_futuros,
            freq='D'
        )
        
        terminales_unicas = self.df["Terminal"].unique()
        franjas_unicas = self.df["Franja Horaria"].unique()
        
        escenarios = []
        for fecha in fechas_futuras:
            for terminal in terminales_unicas:
                for franja in franjas_unicas:
                    hist = self.df[self.df["Terminal"] == terminal]
                    
                    if len(hist) > 0:
                        cap_promedio = hist["Capacidad Máxima"].median()
                        ocup_promedio = hist["Ocupacion"].median()
                    else:
                        cap_promedio = self.df["Capacidad Máxima"].median()
                        ocup_promedio = self.df["Ocupacion"].median()
                    
                    escenarios.append({
                        "Terminal": terminal,
                        "Fecha": fecha,
                        "Día de la Semana": fecha.day_name(),
                        "Franja Horaria": franja,
                        "Capacidad Máxima": cap_promedio,
                        "Ocupacion": ocup_promedio,
                        "Personas Actuales": cap_promedio * ocup_promedio
                    })
        
        df_futuro = pd.DataFrame(escenarios)
        print(f"📅 Generadas {len(df_futuro)} predicciones futuras ({dias_futuros} días)")
        return df_futuro

    # ===========================================================
    # PREDICCIÓN
    # ===========================================================
    def predecir(self, df_objetivo=None, incluir_futuro=True, dias_futuros=30):
        """Genera predicciones sobre datos históricos o futuros."""
        if self.modelo_ols is None and self.modelo_logit is None:
            print("⚠️ No hay modelos entrenados.")
            return None

        # Decidir qué datos predecir
        if df_objetivo is not None:
            df = df_objetivo.copy()
        elif incluir_futuro:
            df = self.generar_fechas_futuras(dias_futuros)
        else:
            df = self.df.copy()

        # PREDICCIONES DE PERSONAS (OLS)
        if self.modelo_ols is not None:
            X_reg = df[["Capacidad Máxima", "Ocupacion"]].astype(float)
            X_reg = sm.add_constant(X_reg, has_constant='add')
            
            try:
                preds = self.modelo_ols.predict(X_reg)
                df = df.assign(
                    Personas_Predichas=preds.clip(lower=0).round().astype("Int64")
                )
            except Exception as e:
                print(f"⚠️ Error en predicción OLS: {e}")
                df = df.assign(Personas_Predichas=pd.NA)
        else:
            df = df.assign(Personas_Predichas=pd.NA)

        # PREDICCIONES DE COLAPSO (LOGIT)
        if self.modelo_logit is not None and self.logit_columns is not None:
            try:
                dummies_franja = pd.get_dummies(
                    df["Franja Horaria"].astype(str),
                    prefix="Franja",
                    drop_first=True,
                    dtype=int
                )
                dummies_dia = pd.get_dummies(
                    df["Día de la Semana"].astype(str),
                    prefix="Dia",
                    drop_first=True,
                    dtype=int
                )

                X_logit = pd.concat([df[["Ocupacion"]], dummies_franja, dummies_dia], axis=1)
                X_logit = X_logit.apply(pd.to_numeric, errors="coerce")
                X_logit = sm.add_constant(X_logit, has_constant='add')

                # Asegurar mismas columnas que entrenamiento
                for col in self.logit_columns:
                    if col not in X_logit.columns:
                        X_logit[col] = 0

                X_logit = X_logit[self.logit_columns].astype(float)
                
                # PREDECIR PROBABILIDADES
                prob_colapso = self.modelo_logit.predict(X_logit)
                df = df.assign(Prob_Colapso=prob_colapso)
                
                # ASIGNAR ESTADOS
                df = df.assign(
                    Estado_Previsto=np.select(
                        [
                            df["Prob_Colapso"] > 0.7,
                            (df["Prob_Colapso"] > 0.4) & (df["Prob_Colapso"] <= 0.7),
                            df["Prob_Colapso"] <= 0.4
                        ],
                        ["Colapsará", "Riesgo de Colapso", "Estable"],
                        default="Desconocido"
                    )
                )
                
                print(f"✅ Predicciones de colapso generadas")
                conteo_estados = df["Estado_Previsto"].value_counts()
                for estado, count in conteo_estados.items():
                    print(f"   - {estado}: {count}")
                    
            except Exception as e:
                print(f"⚠️ Error al predecir con Logit: {e}")
                df = df.assign(Prob_Colapso=np.nan, Estado_Previsto="No disponible")
        else:
            print("⚠️ Modelo Logit no disponible. Solo predicciones OLS.")
            df = df.assign(Prob_Colapso=np.nan, Estado_Previsto="No disponible")

        # Seleccionar columnas
        columnas_salida = [
            "Terminal", "Fecha", "Día de la Semana", "Franja Horaria",
            "Capacidad Máxima", "Ocupacion", "Personas_Predichas",
            "Prob_Colapso", "Estado_Previsto"
        ]
        
        if "Personas Actuales" in df.columns:
            columnas_salida.insert(5, "Personas Actuales")
        
        self.df_predicciones = df[columnas_salida].copy()

        print(f"\n✅ Predicciones generadas: {len(self.df_predicciones)} registros")
        print(f"   - OLS: {'✅' if self.modelo_ols else '❌'}")
        print(f"   - Logit: {'✅' if self.modelo_logit else '❌'}")
        
        return self.df_predicciones

    # ===========================================================
    # GUARDAR RESULTADOS
    # ===========================================================
    def guardar_predicciones(self, archivo="predicciones_mio.xlsx"):
        """Guarda predicciones en Excel con formato mejorado"""
        if self.df_predicciones is not None:
            df_export = self.df_predicciones.copy()
            df_export["Fecha"] = pd.to_datetime(df_export["Fecha"]).dt.date
            
            df_export.to_excel(archivo, index=False)
            print(f"\n💾 Archivo guardado: {archivo}")
            print(f"   Total registros: {len(df_export)}")
            if "Estado_Previsto" in df_export.columns:
                print(f"   Estados previstos:")
                for estado, count in df_export["Estado_Previsto"].value_counts().items():
                    print(f"      - {estado}: {count}")
        else:
            print("⚠️ No hay predicciones para guardar.")


# ===========================================================
# BLOQUE PRINCIPAL
# ===========================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 SISTEMA PREDICTIVO MIO - VERSIÓN CORREGIDA")
    print("="*60 + "\n")
    
    # IMPORTANTE: Ahora usa usar_ultimo_mes=False por defecto
    modelo = ModeloPredictivoMIO(usar_ultimo_mes=False)
    
    print("\n📊 ENTRENANDO MODELOS...")
    modelo.entrenar_modelo_regresion()
    modelo.entrenar_modelo_colapso()
    
    print("\n🔮 GENERANDO PREDICCIONES FUTURAS...")
    df_pred = modelo.predecir(incluir_futuro=True, dias_futuros=30)

    if df_pred is not None:
        modelo.guardar_predicciones()
        
        print("\n" + "="*60)
        print("📋 VISTA PREVIA DE PREDICCIONES")
        print("="*60)
        print(df_pred.head(15).to_string(index=False))
        
        print("\n" + "="*60)
        print("📊 RESUMEN ESTADÍSTICO")
        print("="*60)
        print(df_pred[["Personas_Predichas", "Prob_Colapso", "Estado_Previsto"]].describe())
    else:
        print("\n⚠️ No se pudieron generar predicciones.")
        print("Revisa los mensajes de error anteriores.")