import os

import pandas as pd

from config import CONCIL_DIR, INPUT_DIR, INPUT_RANGE_DIR, LOCALES, OUTPUT_BY_DAY_DIR, OUTPUT_BY_RANGE_DIR
from core.logger import log_error, log_info, log_success, log_warning
from loaders.mov_excel import limpiar_movimientos_excel
from loaders.mov_pdf_auto import limpiar_movimientos_pdf_auto
from loaders.trs import limpiar_trs
from services.date_manager import (
    log_fechas_huerfanas,
    log_resumen_deteccion_diaria,
    log_resumen_fecha_diaria,
)
from services.export_service import ejecutar_core_y_exportar
from services.input_detector import detectar_inputs_diarios, detectar_inputs_rango


def _snapshot_file(path):
    if not os.path.exists(path):
        return {"exists": False, "size": None, "mtime_ns": None}
    st = os.stat(path)
    return {"exists": True, "size": st.st_size, "mtime_ns": st.st_mtime_ns}


def _same_snapshot(a, b):
    return a == b


def new_qa_state():
    return {
        "inputs_validados": True,
        "limpieza_correcta": True,
        "exportacion_correcta": True,
        "compatible_colab": True,
        "errores_fechas": [],
        "errores_rangos": [],
        "fechas_incompletas": set(),
        "export_diario_ok": 0,
        "export_rango_ok": 0,
        "fatal_error": None,
    }


def validate_cleanup_integrity(qa_state, setup_context):
    if qa_state is None or not setup_context:
        return

    resumen_path = setup_context.get("resumen_mensual_path")
    before = setup_context.get("resumen_snapshot_before_cleanup")
    if not resumen_path or before is None:
        return

    after = _snapshot_file(resumen_path)
    if before.get("exists") and not _same_snapshot(before, after):
        qa_state["limpieza_correcta"] = False
        log_warning("\u26A0\uFE0F resumen_mensual.xlsx fue modificado durante limpieza previa")


def _mark_error_fecha(qa_state, fecha):
    if qa_state is None:
        return
    qa_state["errores_fechas"].append(fecha)


def _mark_error_rango(qa_state, rango_key):
    if qa_state is None:
        return
    qa_state["errores_rangos"].append(rango_key)


def _registrar_fecha_incompleta(qa_state, fecha):
    if qa_state is None:
        return
    qa_state["fechas_incompletas"].add(fecha)


def limpiar_salidas_legacy():
    """Limpia reportes Excel legacy dentro de /output/conciliacion/ al iniciar."""
    import glob

    if os.path.exists(CONCIL_DIR):
        for f in glob.glob(os.path.join(CONCIL_DIR, "*.xlsx")):
            try:
                os.remove(f)
            except Exception:
                pass


def _folder_has_files(path):
    if not os.path.exists(path):
        return False
    try:
        return any(entry.is_file() for entry in os.scandir(path))
    except Exception:
        return False


def procesar_rango(qa_state=None):
    rangos_files = detectar_inputs_rango()

    if not rangos_files:
        return False

    procesado_alguno = False

    for rango_key, datos in rangos_files.items():
        try:
            mov_paths = datos.get("mov_paths", [])
            trs_por_local_paths = datos.get("trs_por_local_paths", {})

            if not mov_paths and not trs_por_local_paths:
                continue

            if not mov_paths:
                log_warning(f"\u26A0\uFE0F {rango_key} \u2192 faltan archivos Banco (rango)")
                continue
            if not trs_por_local_paths:
                log_warning(f"\u26A0\uFE0F {rango_key} \u2192 faltan TRS (rango)")
                continue

            log_info(f"\n\u25B6 Procesando en modo RANGO DE FECHAS (Lote conjunto: {rango_key})")

            mov_list = []
            mov_es_pdf = False

            for mov_path in mov_paths:
                try:
                    if mov_path.lower().endswith(".pdf"):
                        mov_es_pdf = True
                        mov_df = limpiar_movimientos_pdf_auto(mov_path)
                    else:
                        mov_df = limpiar_movimientos_excel(mov_path)
                except Exception:
                    log_warning(f"\u26A0\uFE0F {rango_key} \u2192 archivo de Banco corrupto o inv\u00E1lido (se omite)")
                    continue

                if mov_df is None or mov_df.empty:
                    continue
                mov_list.append(mov_df)

            if not mov_list:
                log_warning(f"\u26A0\uFE0F No hay movimientos validos en el rango {rango_key}.")
                continue

            mov = pd.concat(mov_list, ignore_index=True)

            trs_por_local = {}
            trs_list = []
            for local_code, paths in trs_por_local_paths.items():
                dfs_local = []
                for path in paths:
                    try:
                        df_local = limpiar_trs(path, local_code)
                    except Exception:
                        log_warning(f"\u26A0\uFE0F {rango_key} \u2192 TRS corrupto ({local_code}) (se omite)")
                        continue

                    if df_local is not None and not df_local.empty:
                        dfs_local.append(df_local)

                if dfs_local:
                    df_trs_local = pd.concat(dfs_local, ignore_index=True)
                    trs_por_local[local_code] = df_trs_local
                    trs_list.append(df_trs_local)

            if not trs_list:
                log_warning(f"\u26A0\uFE0F No hay TRS validos en el rango {rango_key}.")
                continue

            trs_all = pd.concat(trs_list, ignore_index=True)
            ejecutar_core_y_exportar(
                rango_key,
                mov,
                trs_por_local,
                trs_all,
                mov_es_pdf,
                es_rango=True,
                qa_state=qa_state,
            )
            procesado_alguno = True

        except Exception:
            log_error(f"\u274C Error en rango {rango_key} \u2192 se contin\u00FAa con los dem\u00E1s")
            _mark_error_rango(qa_state, rango_key)
            continue

    return procesado_alguno


def procesar_diario(qa_state=None):
    mov_files, trs_files = detectar_inputs_diarios()

    log_fechas_huerfanas(mov_files, trs_files)
    fechas = sorted(set(mov_files.keys()) & set(trs_files.keys()))
    log_resumen_deteccion_diaria(mov_files, trs_files, fechas)

    if not fechas:
        log_warning("\u26A0\uFE0F No hay fechas compatibles para procesar en modo diario.")
        return False

    procesado_alguno = False

    for fecha in fechas:
        log_info("")
        log_resumen_fecha_diaria(fecha, trs_files)

        try:
            mov_path = mov_files[fecha]
            mov_es_pdf = mov_path.lower().endswith(".pdf")

            if mov_es_pdf:
                try:
                    mov = limpiar_movimientos_pdf_auto(mov_path)
                except Exception:
                    log_error(f"\u274C Error en {fecha} \u2192 PDF corrupto o inv\u00E1lido (se contin\u00FAa con las dem\u00E1s)")
                    _mark_error_fecha(qa_state, fecha)
                    continue

                if mov is None or mov.empty:
                    log_warning("\u26A0\uFE0F No se pudo parsear el PDF de movimientos, se omite la fecha.")
                    continue
            else:
                log_info("\U0001F4CA Movimientos desde Excel")
                try:
                    mov = limpiar_movimientos_excel(mov_path)
                except Exception:
                    log_error(f"\u274C Error en {fecha} \u2192 Excel de movimientos corrupto (se contin\u00FAa con las dem\u00E1s)")
                    _mark_error_fecha(qa_state, fecha)
                    continue

                if mov is None or mov.empty:
                    log_warning("\u26A0\uFE0F No hay movimientos validos en Excel, se omite la fecha.")
                    continue

            trs_por_local = {}
            trs_list = []
            for local_code, path in trs_files[fecha].items():
                try:
                    df_trs = limpiar_trs(path, local_code)
                except Exception:
                    log_warning(f"\u26A0\uFE0F {fecha} \u2192 TRS corrupto: {local_code} (se omite)")
                    continue

                if df_trs is None or df_trs.empty:
                    continue

                trs_por_local[local_code] = df_trs
                trs_list.append(df_trs)

            if len(trs_por_local) < len(LOCALES):
                _registrar_fecha_incompleta(qa_state, fecha)

            if not trs_list:
                log_warning("\u26A0\uFE0F No hay TRS validos, se omite la fecha")
                continue

            trs_all = pd.concat(trs_list, ignore_index=True)
            ejecutar_core_y_exportar(fecha, mov, trs_por_local, trs_all, mov_es_pdf, qa_state=qa_state)
            procesado_alguno = True

        except Exception:
            log_error(f"\u274C Error en {fecha} \u2192 se contin\u00FAa con las dem\u00E1s")
            _mark_error_fecha(qa_state, fecha)
            continue

    return procesado_alguno


def run_full_process(qa_state=None):
    if qa_state is None:
        qa_state = new_qa_state()

    os.makedirs(CONCIL_DIR, exist_ok=True)
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(INPUT_RANGE_DIR, exist_ok=True)
    os.makedirs(OUTPUT_BY_DAY_DIR, exist_ok=True)
    os.makedirs(OUTPUT_BY_RANGE_DIR, exist_ok=True)

    limpiar_salidas_legacy()

    has_daily_files = _folder_has_files(INPUT_DIR)
    has_range_files = _folder_has_files(INPUT_RANGE_DIR)

    if has_daily_files:
        log_info("\U0001F4C2 Carpeta diaria detectada")
    if has_range_files:
        log_info("\U0001F4C2 Carpeta rango detectada")

    if not has_daily_files and not has_range_files:
        log_info("No hay archivos en /input ni /input_date_range. Finaliza sin error.")
        return qa_state

    if has_daily_files:
        log_info("\u25B6 Procesando diaria...")
        procesar_diario(qa_state=qa_state)

    if has_range_files:
        log_info("\u25B6 Procesando rango...")
        procesar_rango(qa_state=qa_state)

    return qa_state


def print_final_summary(qa_state):
    errores_total = len(qa_state.get("errores_fechas", [])) + len(qa_state.get("errores_rangos", []))
    if qa_state.get("fatal_error"):
        log_error(f"\u274C Error global: {qa_state['fatal_error']}")

    log_success("\n\u2705 Proceso finalizado")
    log_warning(f"\u26A0\uFE0F Fechas con error: {errores_total}")

    log_info("\n\U0001F9EA QA RESULTADO:")
    log_info(("\u2714" if qa_state.get("inputs_validados") else "\u26A0\uFE0F") + " Inputs validados")
    log_info(("\u2714" if qa_state.get("limpieza_correcta") else "\u26A0\uFE0F") + " Limpieza correcta")
    log_info(("\u2714" if qa_state.get("exportacion_correcta") else "\u26A0\uFE0F") + " Exportaci\u00F3n correcta")
    log_info(("\u2714" if qa_state.get("compatible_colab") else "\u26A0\uFE0F") + " Compatible con Colab")

    incompletas = len(qa_state.get("fechas_incompletas", []))
    if incompletas:
        log_warning(f"\u26A0\uFE0F {incompletas} fecha(s) con datos incompletos")
    else:
        log_info("\u2714 Sin fechas con datos incompletos")
