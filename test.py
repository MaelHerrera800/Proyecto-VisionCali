"""
Tests unitarios para el módulo utils.py
"""

import pytest
import os
import json
import pandas as pd
import sys

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    cargar_config, obtener_ruta_archivo, obtener_estaciones,
    obtener_franjas_horarias, obtener_coordenadas,
    validar_columnas_requeridas, ConfigError, DataFileError
)


class TestConfiguracion:
    """Tests para funciones de configuración."""
    
    def test_cargar_config_exitoso(self):
        """Verifica que se puede cargar la configuración correctamente."""
        config = cargar_config()
        assert isinstance(config, dict)
        assert "estaciones" in config
        assert "franjas_horarias" in config
        assert "modelo" in config
    
    def test_cargar_config_archivo_inexistente(self):
        """Verifica que se lanza ConfigError si el archivo no existe."""
        with pytest.raises(ConfigError):
            cargar_config("archivo_inexistente.json")
    
    def test_obtener_estaciones(self):
        """Verifica que se obtiene una lista de estaciones."""
        estaciones = obtener_estaciones()
        assert isinstance(estaciones, list)
        assert len(estaciones) > 0
        assert "Terminal Menga" in estaciones
    
    def test_obtener_franjas_horarias(self):
        """Verifica que se obtienen las franjas horarias."""
        franjas = obtener_franjas_horarias()
        assert isinstance(franjas, list)
        assert len(franjas) > 0
        assert "05:30-09:00" in franjas
    
    def test_obtener_coordenadas(self):
        """Verifica que se obtienen coordenadas válidas."""
        coords = obtener_coordenadas()
        assert isinstance(coords, dict)
        assert len(coords) > 0
        
        # Verificar estructura de coordenadas
        for estacion, coord in coords.items():
            assert isinstance(coord, tuple)
            assert len(coord) == 2
            lat, lon = coord
            assert isinstance(lat, (int, float))
            assert isinstance(lon, (int, float))
            # Validar rangos geográficos de Cali
            assert 3.0 < lat < 4.0
            assert -77.0 < lon < -76.0


class TestRutas:
    """Tests para manejo de rutas."""
    
    def test_obtener_ruta_archivo(self):
        """Verifica que se construye correctamente la ruta absoluta."""
        ruta = obtener_ruta_archivo("test.txt")
        assert os.path.isabs(ruta)
        assert ruta.endswith("test.txt")
    
    def test_ruta_archivo_con_subdirectorio(self):
        """Verifica manejo de subdirectorios."""
        ruta = obtener_ruta_archivo("data/test.xlsx")
        assert os.path.isabs(ruta)
        assert "data" in ruta
        assert ruta.endswith("test.xlsx")


class TestValidaciones:
    """Tests para funciones de validación."""
    
    def test_validar_columnas_requeridas_exitoso(self):
        """Verifica validación exitosa de columnas."""
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"],
            "col3": [True, False, True]
        })
        
        # No debería lanzar excepción
        validar_columnas_requeridas(df, ["col1", "col2"])
    
    def test_validar_columnas_requeridas_faltantes(self):
        """Verifica que se detectan columnas faltantes."""
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"]
        })
        
        with pytest.raises(ValueError) as excinfo:
            validar_columnas_requeridas(df, ["col1", "col2", "col3"])
        
        assert "col3" in str(excinfo.value)
    
    def test_validar_columnas_vacias(self):
        """Verifica comportamiento con lista vacía de columnas."""
        df = pd.DataFrame({"col1": [1, 2, 3]})
        
        # No debería lanzar excepción
        validar_columnas_requeridas(df, [])


class TestParametrosModelo:
    """Tests para parámetros del modelo."""
    
    def test_parametros_random_forest(self):
        """Verifica que existen parámetros para Random Forest."""
        from utils import obtener_parametros_modelo
        
        params = obtener_parametros_modelo("random_forest")
        assert isinstance(params, dict)
        assert "n_estimators" in params
        assert "max_depth" in params
        assert "min_samples_split" in params
    
    def test_parametros_logistic_regression(self):
        """Verifica que existen parámetros para regresión logística."""
        from utils import obtener_parametros_modelo
        
        params = obtener_parametros_modelo("logistic_regression")
        assert isinstance(params, dict)
        assert "max_iter" in params


class TestManejoDatos:
    """Tests para carga y guardado de datos."""
    
    def test_cargar_dataframe_inexistente(self):
        """Verifica que se lanza DataFileError si el archivo no existe."""
        from utils import cargar_dataframe
        
        with pytest.raises(DataFileError):
            cargar_dataframe("archivo_que_no_existe.xlsx")
    
    def test_guardar_y_cargar_dataframe(self, tmp_path):
        """Verifica guardado y carga de DataFrame."""
        from utils import guardar_dataframe, cargar_dataframe
        
        # Crear DataFrame de prueba
        df_original = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"]
        })
        
        # Guardar en directorio temporal
        archivo_test = os.path.join(tmp_path, "test.xlsx")
        
        # Modificar temporalmente BASE_DIR para usar tmp_path
        import utils
        original_base_dir = utils.BASE_DIR
        utils.BASE_DIR = str(tmp_path)
        
        try:
            guardar_dataframe(df_original, "test.xlsx")
            df_cargado = cargar_dataframe("test.xlsx")
            
            # Verificar que son iguales
            pd.testing.assert_frame_equal(df_original, df_cargado)
        finally:
            # Restaurar BASE_DIR original
            utils.BASE_DIR = original_base_dir


class TestIntegracion:
    """Tests de integración para flujos completos."""
    
    def test_flujo_completo_configuracion(self):
        """Verifica que se puede cargar configuración y obtener todos los datos."""
        config = cargar_config()
        estaciones = obtener_estaciones()
        franjas = obtener_franjas_horarias()
        coords = obtener_coordenadas()
        
        # Verificar consistencia
        assert len(estaciones) == len(coords)
        
        # Verificar que todas las estaciones tienen coordenadas
        for estacion in estaciones:
            assert estacion in coords


# Fixtures para tests
@pytest.fixture
def df_ejemplo():
    """DataFrame de ejemplo para tests."""
    return pd.DataFrame({
        "Terminal": ["Terminal Menga", "Centro", "Univalle"],
        "Fecha": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        "Franja Horaria": ["05:30-09:00", "09:00-12:00", "12:00-15:00"],
        "Personas Actuales": [100, 150, 200],
        "Capacidad Máxima": [120, 180, 220],
        "Estado": ["Estable", "Estable", "Colapsada"]
    })


@pytest.fixture
def config_ejemplo():
    """Configuración de ejemplo para tests."""
    return {
        "estaciones": ["Terminal Menga", "Centro"],
        "franjas_horarias": ["05:30-09:00", "09:00-12:00"],
        "modelo": {
            "umbral_colapso": 0.80,
            "random_forest": {
                "n_estimators": 100,
                "max_depth": 20
            }
        }
    }


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v", "--tb=short"])