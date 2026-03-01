import os

from utils.environment import get_base_path


BASE_DIR = get_base_path()
INPUT_DIR = os.path.join(BASE_DIR, "input")
INPUT_RANGE_DIR = os.path.join(BASE_DIR, "input_date_range")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CONCIL_DIR = os.path.join(OUTPUT_DIR, "conciliacion")
LIMPIO_DIR = os.path.join(OUTPUT_DIR, "limpio")
OUTPUT_BY_DAY_DIR = os.path.join(OUTPUT_DIR, "por_dia")
OUTPUT_BY_RANGE_DIR = os.path.join(OUTPUT_DIR, "por_rango")


def ensure_runtime_directories():
    for path in (
        INPUT_DIR,
        INPUT_RANGE_DIR,
        OUTPUT_DIR,
        CONCIL_DIR,
        LIMPIO_DIR,
        OUTPUT_BY_DAY_DIR,
        OUTPUT_BY_RANGE_DIR,
    ):
        os.makedirs(path, exist_ok=True)


# Mantiene comportamiento actual: crear carpetas al importar config/path_manager
ensure_runtime_directories()

