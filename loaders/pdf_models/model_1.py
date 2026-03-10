import re
import unicodedata

import pandas as pd
import pdfplumber

from core.mov_helpers import extraer_caja_texto
from loaders.mov_pdf2 import limpiar_movimientos_pdf2
from loaders.mov_pdf_header_unica import limpiar_movimientos_pdf_header_unica
from loaders.mov_pdf_portada import limpiar_movimientos_pdf_portada


_REQUIRED_BASE_COLS = {"Fecha", "Concepto", "Tipo", "Monto", "Saldo", "Nro. Documento"}
_CANONICAL_COLS = [
    "Fecha",
    "Concepto",
    "Tipo",
    "Monto",
    "Saldo",
    "Nro. Documento",
    "Recaudador",
]


def _is_valid_mov_df(df):
    return isinstance(df, pd.DataFrame) and (not df.empty) and _REQUIRED_BASE_COLS.issubset(df.columns)


def _standardize_output(df):
    if df is None:
        return None

    if not isinstance(df, pd.DataFrame):
        return df

    out = df.copy()

    if "Nro. Documento" not in out.columns:
        out["Nro. Documento"] = ""
    out["Nro. Documento"] = out["Nro. Documento"].fillna("").astype(str).str.strip()

    if "Recaudador" not in out.columns:
        if "Concepto" in out.columns:
            out["Recaudador"] = out["Concepto"].fillna("").astype(str).apply(extraer_caja_texto)
        else:
            out["Recaudador"] = ""

    for col in _CANONICAL_COLS:
        if col not in out.columns:
            out[col] = None

    return out[_CANONICAL_COLS]


def _normalize_text(value):
    if value is None:
        return ""
    text = str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.upper()
    return re.sub(r"\s+", " ", text).strip()


def _extract_first_pages_text(path, max_pages=2):
    chunks = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages[:max_pages]:
            text = page.extract_text() or ""
            if text:
                chunks.append(_normalize_text(text))

    return " ".join(chunks)


def _select_parsers_for_model_1(path):
    try:
        text = _extract_first_pages_text(path)
    except Exception:
        text = ""

    if (
        "FECHA OFICINA TIPO CONCEPTO" in text
        and "MONTO SALDO" in text
        and ("NRO DOCUMENTO" in text or "NRO. DOCUMENTO" in text or "NUMERO DE DOCUMENTO" in text)
    ):
        return (
            limpiar_movimientos_pdf_header_unica,
            limpiar_movimientos_pdf2,
            limpiar_movimientos_pdf_portada,
        )

    if (
        "FECHA CONCEPTO TIPO MONTO SALDO" in text
        and "DOCUMENTO BENEFICIARIA" in text
    ):
        return (
            limpiar_movimientos_pdf2,
            limpiar_movimientos_pdf_portada,
            limpiar_movimientos_pdf_header_unica,
        )

    return (
        limpiar_movimientos_pdf_portada,
        limpiar_movimientos_pdf2,
        limpiar_movimientos_pdf_header_unica,
    )


def parse_model_1(path):
    """
    Parser del modelo principal (PDF_MODEL_1).
    Agrupa variantes históricas del formato principal y mantiene salida canónica.
    """
    parsers = _select_parsers_for_model_1(path)

    last_exc = None

    for parser in parsers:
        try:
            df = parser(path)
        except Exception as exc:
            last_exc = exc
            continue

        if _is_valid_mov_df(df):
            return _standardize_output(df)

    if last_exc is not None:
        raise last_exc

    return _standardize_output(pd.DataFrame(columns=_CANONICAL_COLS))
