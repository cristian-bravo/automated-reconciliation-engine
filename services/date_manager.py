from config import LOCALES
from core.logger import log_info, log_warning


def log_resumen_deteccion_diaria(mov_files, trs_files, fechas):
    log_info(f"\U0001F4C2 Movimientos detectados: {len(mov_files)} fechas")
    log_info(f"\U0001F4C2 TRS detectados: {len(trs_files)} fechas")
    log_info("\U0001F4C5 Fechas a procesar:")
    log_info(" | ".join(fechas) if fechas else "-")


def log_fechas_huerfanas(mov_files, trs_files):
    solo_banco = sorted(set(mov_files.keys()) - set(trs_files.keys()))
    solo_trs = sorted(set(trs_files.keys()) - set(mov_files.keys()))

    for fecha in solo_banco:
        log_warning(f"\u26A0\uFE0F {fecha} \u2192 falta TRS (se omite)")
    for fecha in solo_trs:
        log_warning(f"\u26A0\uFE0F {fecha} \u2192 falta archivo Banco (se omite)")


def log_resumen_fecha_diaria(fecha, trs_files):
    trs_fecha = trs_files.get(fecha, {})
    faltantes_trs = [code for code in LOCALES.keys() if code not in trs_fecha]

    if faltantes_trs:
        log_warning(f"\u26A0\uFE0F {fecha} \u2192 faltan TRS: {', '.join(faltantes_trs)}")

    log_info(f"\U0001F4C6 {fecha} \u2192 TRS: {len(trs_fecha)} + Banco: 1")

