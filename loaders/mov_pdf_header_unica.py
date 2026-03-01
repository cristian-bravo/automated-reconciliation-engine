import re

import pandas as pd
import pdfplumber

from core.mov_helpers import extraer_caja_texto
from core.utils import clean_illegal_chars, normalize_amount, normalize_doc

_HEADER_FIRMA = [
    "FECHA",
    "OFICINA",
    "TIPO",
    "CONCEPTO",
    "NRO DOCUMENTO",
    "MONTO",
    "SALDO",
]


def _texto_limpio(value):
    if value is None:
        return ""
    text = clean_illegal_chars(str(value))
    text = text.replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()


def _header_normalizado(value):
    return _texto_limpio(value).upper()


def _es_header(row):
    if not row or len(row) < len(_HEADER_FIRMA):
        return False
    return [_header_normalizado(x) for x in row[: len(_HEADER_FIRMA)]] == _HEADER_FIRMA


def _fila_a_mapa(row, columnas_pdf):
    if not columnas_pdf:
        return {}

    cells = list(row or [])
    if len(cells) < len(columnas_pdf):
        cells += [None] * (len(columnas_pdf) - len(cells))

    return {col: cells[i] for i, col in enumerate(columnas_pdf)}


def _normalize_amount_layout(value):
    """
    Reusa el normalizador global y corrige este layout cuando viene en
    formato US con miles por coma (ej: 3,967.14).
    """
    if pd.isna(value):
        return None

    raw = _texto_limpio(value).replace("$", "")
    if not raw:
        return None

    if "," in raw and "." in raw and raw.rfind(".") > raw.rfind(","):
        try:
            return round(float(raw.replace(",", "")), 2)
        except ValueError:
            pass

    return normalize_amount(raw)


def _tipo_estandar(value):
    tipo = _texto_limpio(value).upper()
    if tipo == "C":
        return "CREDITO"
    if tipo == "D":
        return "DEBITO"
    return tipo


def _parse_record(row, columnas_pdf):
    row_map = _fila_a_mapa(row, columnas_pdf)
    fecha_raw = _texto_limpio(row_map.get("FECHA"))

    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", fecha_raw):
        return None

    concepto = _texto_limpio(row_map.get("CONCEPTO"))
    monto = _normalize_amount_layout(row_map.get("MONTO"))
    saldo = _normalize_amount_layout(row_map.get("SALDO"))

    return {
        "Fecha": pd.to_datetime(fecha_raw, format="%d/%m/%Y", errors="coerce"),
        "Concepto": concepto,
        "Tipo": _tipo_estandar(row_map.get("TIPO")),
        "Monto": monto,
        "Saldo": saldo,
        "Nro. Documento": normalize_doc(_texto_limpio(row_map.get("NRO DOCUMENTO"))),
        "Recaudador": extraer_caja_texto(concepto),
    }


def _es_continuacion_concepto(row, columnas_pdf):
    row_map = _fila_a_mapa(row, columnas_pdf)

    fecha = _texto_limpio(row_map.get("FECHA"))
    concepto = _texto_limpio(row_map.get("CONCEPTO"))
    nro_doc = _texto_limpio(row_map.get("NRO DOCUMENTO"))
    monto = _texto_limpio(row_map.get("MONTO"))
    saldo = _texto_limpio(row_map.get("SALDO"))

    return (not fecha) and bool(concepto) and not nro_doc and not monto and not saldo


def limpiar_movimientos_pdf_header_unica(path):
    """
    Parser dedicado para el PDF con portada y una sola cabecera:
    - Primera pagina: portada + header + data
    - Paginas siguientes: solo data usando la misma cabecera
    """
    filas = []
    columnas_pdf = None

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables() or []

            for table in tables:
                if not table:
                    continue

                for row in table:
                    if _es_header(row):
                        columnas_pdf = [_header_normalizado(c) for c in row[: len(_HEADER_FIRMA)]]
                        continue

                    if columnas_pdf is None:
                        # Primera pagina puede traer portada antes de hallar la cabecera.
                        continue

                    record = _parse_record(row, columnas_pdf)
                    if record is not None:
                        filas.append(record)
                        continue

                    if filas and _es_continuacion_concepto(row, columnas_pdf):
                        row_map = _fila_a_mapa(row, columnas_pdf)
                        extra = _texto_limpio(row_map.get("CONCEPTO"))
                        if extra:
                            concepto = f"{filas[-1]['Concepto']} {extra}".strip()
                            filas[-1]["Concepto"] = concepto
                            filas[-1]["Recaudador"] = extraer_caja_texto(concepto)

    df = pd.DataFrame(
        filas,
        columns=[
            "Fecha",
            "Concepto",
            "Tipo",
            "Monto",
            "Saldo",
            "Nro. Documento",
            "Recaudador",
        ],
    )

    if not df.empty:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce")
        df["Saldo"] = pd.to_numeric(df["Saldo"], errors="coerce")
        df["Nro. Documento"] = df["Nro. Documento"].fillna("").astype(str).str.strip()

    return df
