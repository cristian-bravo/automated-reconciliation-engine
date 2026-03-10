import os
import re

from config import INPUT_DIR, INPUT_RANGE_DIR, LOCALES
from core.logger import log_warning

LOCAL_CODES = set(LOCALES.keys())
BANK_EXTENSIONS = {".pdf", ".xls", ".xlsx", ".xlsb", ".xlsm"}


def _listdir_safe(path, alias):
    if not os.path.exists(path):
        log_warning(f"\u26A0\uFE0F Carpeta no encontrada: {alias}")
        os.makedirs(path, exist_ok=True)
        return []

    try:
        return sorted(os.listdir(path))
    except Exception:
        log_warning(f"\u26A0\uFE0F Carpeta no accesible: {alias}")
        return []


def _warn_archivo_ignorado(nombre, motivo="nombre no reconocido"):
    log_warning(f"\u26A0\uFE0F Archivo ignorado: {motivo} ({nombre})")


def _es_archivo_banco(nombre):
    low = nombre.lower()
    ext = os.path.splitext(low)[1]
    return "trs" not in low and ext in BANK_EXTENSIONS


def _extraer_fecha(nombre: str):
    m = re.search(r"(\d{2})[._-](\d{2})[._-](\d{2,4})", nombre)
    if not m:
        return None
    dd, mm, yy = m.groups()
    if len(yy) == 2:
        yy = "20" + yy
    return f"{dd}_{mm}_{yy}"


def detectar_archivos():
    files = _listdir_safe(INPUT_DIR, "/input")

    mov_files = {}
    trs_files = {}

    for f in files:
        full = os.path.join(INPUT_DIR, f)
        if not os.path.isfile(full):
            continue

        fecha = _extraer_fecha(f)
        if not fecha:
            _warn_archivo_ignorado(f)
            continue

        low = f.lower()

        if _es_archivo_banco(f):
            if fecha in mov_files:
                log_warning(f"\u26A0\uFE0F {fecha} \u2192 archivo Banco duplicado (se ignora)")
                continue
            mov_files[fecha] = full
            continue

        if "trs" in low:
            m = re.search(r"trs[._-]([a-z0-9]{2})[._-]", low)
            if not m:
                _warn_archivo_ignorado(f)
                continue
            code = m.group(1)
            if code not in LOCAL_CODES:
                _warn_archivo_ignorado(f)
                continue
            trs_files.setdefault(fecha, {})
            if code in trs_files[fecha]:
                log_warning(f"\u26A0\uFE0F {fecha} \u2192 TRS duplicado: {code} (se ignora)")
                continue
            trs_files[fecha][code] = full
            continue

        _warn_archivo_ignorado(f)

    return mov_files, trs_files


def _extraer_rango(nombre: str):
    """
    Busca los dos primeros numeros en el nombre del archivo (ej. 15 y 31)
    para formar una firma unica del rango (ej. '15-31').
    """
    nums = re.findall(r"\b\d{1,2}\b", nombre)
    if len(nums) >= 2:
        return f"{nums[0]}-{nums[1]}"
    return "GENERAL"


def detectar_archivos_rango():
    """
    Detecta archivos en la carpeta de rango de fechas y los agrupa por
    el rango detectado en el nombre del archivo.
    Retorna: { rango_key: { "mov_paths": [...], "trs_por_local_paths": { local: [...] } } }
    """
    files = _listdir_safe(INPUT_RANGE_DIR, "/input_date_range")
    rangos_files = {}

    for f in files:
        full = os.path.join(INPUT_RANGE_DIR, f)
        if not os.path.isfile(full):
            continue

        low = f.lower()

        rango_key = _extraer_rango(low)
        if rango_key not in rangos_files:
            rangos_files[rango_key] = {"mov_paths": [], "trs_por_local_paths": {}}

        if _es_archivo_banco(f):
            rangos_files[rango_key]["mov_paths"].append(full)
            continue

        if "trs" in low:
            m = re.search(r"trs[._-]([a-z0-9]{2})[._-]", low)
            if not m:
                _warn_archivo_ignorado(f)
                continue
            code = m.group(1)
            if code not in LOCAL_CODES:
                _warn_archivo_ignorado(f)
                continue

            rangos_files[rango_key]["trs_por_local_paths"].setdefault(code, [])
            rangos_files[rango_key]["trs_por_local_paths"][code].append(full)
            continue

        _warn_archivo_ignorado(f)

    return rangos_files


def detectar_formato_mov_pdf(path):
    """
    Wrapper de compatibilidad.
    Conserva el nombre historico, pero ahora devuelve los modelos
    estandarizados (PDF_MODEL_1 / PDF_MODEL_2) o None.
    """
    from loaders.pdf_dispatcher import detect_pdf_model

    return detect_pdf_model(path)
