import os

from config import BASE_DIR, LOCALES
from core.conciliador import conciliar
from core.logger import log_info, log_warning
from export.excel import exportar_excel
from export.pdf import exportar_pdf


def _file_non_empty(path):
    try:
        return os.path.exists(path) and os.path.getsize(path) > 0
    except Exception:
        return False


def _listar_xlsx(dir_path):
    if not os.path.isdir(dir_path):
        return []
    return sorted(
        name
        for name in os.listdir(dir_path)
        if os.path.isfile(os.path.join(dir_path, name)) and name.lower().endswith(".xlsx")
    )


def qa_validar_exportacion_diaria(fecha_str, mov_excel_path, trs_por_local, qa_state):
    carpeta = os.path.dirname(mov_excel_path)
    xlsx_files = set(_listar_xlsx(carpeta))

    required = {
        f"conciliacion_movimientos_{fecha_str}.xlsx",
        f"conciliacion_consolidado_{fecha_str}.xlsx",
    }
    required.update(f"conciliacion_trs_{local_code}_{fecha_str}.xlsx" for local_code in trs_por_local.keys())

    missing_required = [name for name in sorted(required) if name not in xlsx_files]
    invalid_files = [name for name in sorted(required) if name in xlsx_files and not _file_non_empty(os.path.join(carpeta, name))]

    # En dias completos se espera exactamente 6 xlsx (mov + 4 trs + consolidado)
    if len(trs_por_local) == len(LOCALES):
        esperados_total = 2 + len(LOCALES)
        if len(xlsx_files) != esperados_total:
            log_warning(f"\u26A0\uFE0F {fecha_str} \u2192 exportaci\u00F3n diaria incompleta ({len(xlsx_files)}/{esperados_total} archivos)")
            if qa_state is not None:
                qa_state["exportacion_correcta"] = False

    if missing_required or invalid_files:
        if qa_state is not None:
            qa_state["exportacion_correcta"] = False
        if missing_required:
            log_warning(f"\u26A0\uFE0F {fecha_str} \u2192 faltan archivos exportados: {', '.join(missing_required)}")
        if invalid_files:
            log_warning(f"\u26A0\uFE0F {fecha_str} \u2192 archivos vac\u00EDos: {', '.join(invalid_files)}")
        return False

    if qa_state is not None:
        qa_state["export_diario_ok"] += 1
    return True


def qa_validar_exportacion_rango(rango_key, mov_excel_path, trs_por_local, qa_state):
    carpeta = os.path.dirname(mov_excel_path)
    folder_name = os.path.basename(carpeta)
    xlsx_files = set(_listar_xlsx(carpeta))

    required = {f"conciliacion_movimientos_{rango_key}.xlsx"}
    required.update(f"conciliacion_trs_{local_code}_{rango_key}.xlsx" for local_code in trs_por_local.keys())

    consolidado_files = sorted(
        f for f in xlsx_files if f.startswith("conciliacion_consolidado_") and f.endswith(".xlsx")
    )

    if len(consolidado_files) != 1:
        log_warning(f"\u26A0\uFE0F {rango_key} \u2192 consolidado de rango inv\u00E1lido")
        if qa_state is not None:
            qa_state["exportacion_correcta"] = False
        return False

    consolidado_name = consolidado_files[0]
    if "__" not in consolidado_name:
        log_warning(f"\u26A0\uFE0F {rango_key} \u2192 consolidado sin rango en nombre")
        if qa_state is not None:
            qa_state["exportacion_correcta"] = False

    if folder_name not in consolidado_name:
        log_warning(f"\u26A0\uFE0F {rango_key} \u2192 carpeta y consolidado no coinciden")
        if qa_state is not None:
            qa_state["exportacion_correcta"] = False

    required.add(consolidado_name)

    missing_required = [name for name in sorted(required) if name not in xlsx_files]
    invalid_files = [name for name in sorted(required) if name in xlsx_files and not _file_non_empty(os.path.join(carpeta, name))]

    if missing_required or invalid_files:
        if qa_state is not None:
            qa_state["exportacion_correcta"] = False
        if missing_required:
            log_warning(f"\u26A0\uFE0F {rango_key} \u2192 faltan archivos exportados: {', '.join(missing_required)}")
        if invalid_files:
            log_warning(f"\u26A0\uFE0F {rango_key} \u2192 archivos vac\u00EDos: {', '.join(invalid_files)}")
        return False

    if qa_state is not None:
        qa_state["export_rango_ok"] += 1
    return True


def ejecutar_core_y_exportar(fecha_str, mov, trs_por_local, trs_all, mov_es_pdf, es_rango=False, qa_state=None):
    mov_conc, trs_conc = conciliar(mov, trs_all)

    mov_excel_path = exportar_excel(
        fecha=fecha_str,
        mov=mov_conc,
        trs_por_local=trs_por_local,
        trs_all=trs_conc,
        es_rango=es_rango,
    )

    if mov_es_pdf and "Oficina" in mov.columns:
        exportar_pdf(mov_excel_path)

    carpeta_out = os.path.dirname(mov_excel_path)
    carpeta_rel = os.path.relpath(carpeta_out, start=BASE_DIR).replace("\\", "/")
    log_info(f"\U0001F4C1 Carpeta creada: {carpeta_rel}")

    if es_rango:
        qa_validar_exportacion_rango(fecha_str, mov_excel_path, trs_por_local, qa_state)
        log_info("\U0001F9FE Archivos del rango guardados correctamente")
    else:
        qa_validar_exportacion_diaria(fecha_str, mov_excel_path, trs_por_local, qa_state)
        log_info("\U0001F9FE Archivos del d\u00EDa guardados correctamente")

