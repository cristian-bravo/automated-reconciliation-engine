import os
import sys


COLAB_DEFAULT_BASE_PATH = "/content/drive/MyDrive/Conciliacion"


def is_running_in_colab():
    return "google.colab" in sys.modules or "COLAB_RELEASE_TAG" in os.environ


def get_base_path():
    """
    Prioridad:
    1) Override por variable de entorno CONCILIACION_DRIVE_PATH
    2) Ruta default de Colab
    3) Ruta local del proyecto
    """
    override = os.environ.get("CONCILIACION_DRIVE_PATH", "").strip()
    if override:
        return override

    if is_running_in_colab():
        return COLAB_DEFAULT_BASE_PATH

    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

