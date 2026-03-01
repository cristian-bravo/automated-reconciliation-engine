import os
import shutil
import sys

from config import INPUT_DIR, INPUT_RANGE_DIR, OUTPUT_DIR
from core.logger import log_info, log_warning


def _configure_console_output():
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None or not hasattr(stream, "reconfigure"):
            continue
        try:
            stream.reconfigure(errors="replace")
        except Exception:
            pass


def _borrar_archivos_en_carpeta(path, alias):
    if not os.path.exists(path):
        log_warning(f"\u26A0\uFE0F Carpeta no encontrada: {alias}")
        return 0

    eliminados = 0

    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file():
                    os.remove(entry.path)
                    eliminados += 1
            except Exception:
                # Mantiene la limpieza robusta: si un archivo falla, continua con el resto.
                continue
    except FileNotFoundError:
        log_warning(f"\u26A0\uFE0F Carpeta no encontrada: {alias}")
        return 0

    log_info(f"\U0001F9F9 {alias} \u2192 {eliminados} archivos eliminados")
    return eliminados


def _resetear_carpeta_generada(path, alias):
    if not os.path.exists(path):
        log_warning(f"\u26A0\uFE0F Carpeta no encontrada: {alias}")
        os.makedirs(path, exist_ok=True)
        return False

    try:
        shutil.rmtree(path)
    except Exception:
        # Si no puede eliminarla, intenta continuar recreando.
        pass

    os.makedirs(path, exist_ok=True)
    log_info(f"\U0001F9F9 {alias} \u2192 eliminado")
    return True


def _limpiar_subcarpetas_en_carpeta(path, alias):
    """
    Borra SOLO subcarpetas dentro de una carpeta base (no borra archivos sueltos).
    Si la carpeta base no existe, la crea.
    """
    os.makedirs(path, exist_ok=True)

    eliminadas = 0

    try:
        entries = list(os.scandir(path))
    except Exception:
        entries = []

    for entry in entries:
        if not entry.is_dir():
            continue

        sub_alias = f"{alias}/{entry.name}"
        try:
            shutil.rmtree(entry.path)
            eliminadas += 1
        except Exception:
            log_warning(f"\u26A0\uFE0F No se pudo eliminar: {sub_alias} (archivo en uso)")
            continue

    log_info(f"\U0001F9F9 Limpieza previa: {alias} \u2192 {eliminadas} carpetas eliminadas")
    return eliminadas


def limpiar_output_ejecucion():
    """
    Limpieza automática previa a la ejecución principal.
    Elimina solo subcarpetas de output/por_dia y output/por_rango.
    """
    _configure_console_output()

    por_dia = _limpiar_subcarpetas_en_carpeta(os.path.join(OUTPUT_DIR, "por_dia"), "output/por_dia")
    por_rango = _limpiar_subcarpetas_en_carpeta(os.path.join(OUTPUT_DIR, "por_rango"), "output/por_rango")

    return {
        "por_dia_eliminadas": por_dia,
        "por_rango_eliminadas": por_rango,
    }


def limpiar_inputs():
    """
    Elimina todos los archivos (sin borrar carpetas) en /input y /input_date_range.
    """
    _configure_console_output()

    _borrar_archivos_en_carpeta(INPUT_DIR, "/input")
    _borrar_archivos_en_carpeta(INPUT_RANGE_DIR, "/input_date_range")
    _resetear_carpeta_generada(os.path.join(OUTPUT_DIR, "por_dia"), "output/por_dia")
    _resetear_carpeta_generada(os.path.join(OUTPUT_DIR, "por_rango"), "output/por_rango")

    log_info("\u2705 Limpieza finalizada")
