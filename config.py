# config.py
"""
Fachada de compatibilidad para configuracion.
Las rutas y deteccion de entorno viven en utils.environment / utils.path_manager.
"""
from utils.environment import COLAB_DEFAULT_BASE_PATH, get_base_path, is_running_in_colab
from utils.path_manager import (
    BASE_DIR,
    CONCIL_DIR,
    INPUT_DIR,
    INPUT_RANGE_DIR,
    LIMPIO_DIR,
    OUTPUT_BY_DAY_DIR,
    OUTPUT_BY_RANGE_DIR,
    OUTPUT_DIR,
    ensure_runtime_directories,
)


IS_COLAB = is_running_in_colab()

# Asegura carpetas base en local/Colab
ensure_runtime_directories()


# Catalogo de locales (codigo -> nombre oficial)
LOCALES = {
    "vs": "Vega Supermercado",
    "vm": "Vega Mayorista",
    "sv": "Super Vega",
    "v2": "Vega Supermercado 2",
}


# Mapeo de visualizacion de nombres en reportes
LOCALES_DISPLAY = {
    "vega supermercado": "Supermercado",
    "vega mayorista": "Mayorista",
    "super vega": "Super Vega",
    "vega supermercado 2": "Vega 2",
}

