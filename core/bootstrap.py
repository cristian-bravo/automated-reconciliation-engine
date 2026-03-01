import importlib.util
import os
import subprocess
import sys

from core.logger import configure_console_output, log_info
from utils.environment import is_running_in_colab
from utils.path_manager import OUTPUT_DIR, ensure_runtime_directories


def _ensure_colab_dependencies():
    """
    Solo en Colab: si falta una libreria requerida, instala requirements.txt.
    Debe ejecutarse antes de importar modulos pesados (pandas, pdfplumber, etc.).
    """
    if not is_running_in_colab():
        return

    required_modules = ("pandas", "openpyxl", "xlrd", "pdfplumber", "reportlab")
    missing = [name for name in required_modules if importlib.util.find_spec(name) is None]
    if not missing:
        return

    configure_console_output()
    log_info("\U0001F4E6 Instalando dependencias...")

    req_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "requirements.txt")
    if not os.path.exists(req_path):
        raise FileNotFoundError(f"requirements.txt no encontrado: {req_path}")

    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])


def _snapshot_file(path):
    if not os.path.exists(path):
        return {"exists": False, "size": None, "mtime_ns": None}
    st = os.stat(path)
    return {"exists": True, "size": st.st_size, "mtime_ns": st.st_mtime_ns}


def setup_environment():
    """
    Preparacion de entorno:
    - dependencias en Colab
    - configuracion de consola
    - creacion de carpetas base
    - snapshot QA de resumen_mensual antes de limpieza
    """
    _ensure_colab_dependencies()
    configure_console_output()
    ensure_runtime_directories()

    log_info("\U0001F680 Iniciando proceso")

    resumen_mensual_path = os.path.join(OUTPUT_DIR, "resumen_mensual.xlsx")
    return {
        "resumen_mensual_path": resumen_mensual_path,
        "resumen_snapshot_before_cleanup": _snapshot_file(resumen_mensual_path),
        "is_colab": is_running_in_colab(),
    }

