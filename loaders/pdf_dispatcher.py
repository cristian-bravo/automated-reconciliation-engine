import os
import re
import unicodedata

import pdfplumber

from core.logger import log_info, log_warning

PDF_MODEL_1 = "PDF_MODEL_1"
PDF_MODEL_2 = "PDF_MODEL_2"

_MODEL_1_DOC_HEADER_PATTERNS = (
    "NRO DOCUMENTO",
    "NRO. DOCUMENTO",
    "NUMERO DE DOCUMENTO",
    "NUMERO DOCUMENTO",
)

_MODEL_2_DOC_HEADER_PATTERNS = _MODEL_1_DOC_HEADER_PATTERNS + (
    "NRO DOC",
    "NRO. DOC",
)


def _normalize_text(value):
    if value is None:
        return ""
    text = str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.upper()
    text = text.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip()


def _normalize_table_row(row):
    cells = []
    for cell in row or []:
        norm = _normalize_text(cell)
        if norm:
            cells.append(norm)
    return cells


def _extract_pdf_text_and_headers(path, max_pages=3):
    text_chunks = []
    header_rows = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages[:max_pages]:
            text = page.extract_text() or ""
            if text:
                text_chunks.append(_normalize_text(text))

            tables = page.extract_tables() or []
            for table in tables:
                if not table:
                    continue
                for row in table[:3]:
                    norm_row = _normalize_table_row(row)
                    if norm_row:
                        header_rows.append(norm_row)

    return " ".join(text_chunks), header_rows


def _has_any_doc_header(text, patterns):
    return any(pattern in text for pattern in patterns)


def _row_contains_tokens(row, tokens):
    row_text = " ".join(row)
    return all(any(token in cell for cell in row) or token in row_text for token in tokens)


def _looks_like_model_1(text, header_rows):
    if not text and not header_rows:
        return False

    has_doc_header = _has_any_doc_header(text, _MODEL_1_DOC_HEADER_PATTERNS)
    has_main_headers = all(token in text for token in ("FECHA", "CONCEPTO", "TIPO", "MONTO", "SALDO"))
    has_office_or_account = ("OFICINA" in text) or ("CUENTA" in text)

    # Regla principal: formato de estado de cuenta con cabecera "Fecha ... Monto Saldo"
    if has_main_headers and has_doc_header and has_office_or_account:
        return True

    for row in header_rows:
        row_text = " ".join(row)
        row_has_doc = _has_any_doc_header(row_text, _MODEL_1_DOC_HEADER_PATTERNS)
        if row_has_doc and _row_contains_tokens(row, ("FECHA", "CONCEPTO", "TIPO", "MONTO", "SALDO")):
            if ("OFICINA" in row_text) or ("CUENTA" in row_text):
                return True

    # Variantes históricas del formato principal (portada / requerimiento)
    has_institutional_text = any(
        token in text
        for token in (
            "BANCO PICHINCHA",
            "MOVIMIENTOS FINANCIEROS",
            "DETALLE DE LAS TRANSACCIONES",
            "CUENTA BENEFICIARIA",
        )
    )
    has_transaction_pattern = bool(
        re.search(
            r"(TRANSF\.?\s+DIRECTA\s+(DE|A)|TRANSFERENCIA\s+INTERNET|INTERBANCARIA)",
            text,
        )
    )
    has_line_structure = bool(
        re.search(r"\b\d{10,13}\b.*\b\d{4}-\d{2}-\d{2}\b.*\b\d+,\d{2}\b.*\b\d+,\d{2}\b", text)
    )

    return has_institutional_text and (has_transaction_pattern or has_line_structure)


def _looks_like_model_2(text, header_rows):
    if not text and not header_rows:
        return False

    has_doc_header = _has_any_doc_header(text, _MODEL_2_DOC_HEADER_PATTERNS)
    has_headers_text = all(token in text for token in ("FECHA", "OFICINA", "CONCEPTO", "DEBITO", "CREDITO", "SALDO"))
    if has_doc_header and has_headers_text:
        return True

    for row in header_rows:
        row_text = " ".join(row)
        if not _has_any_doc_header(row_text, _MODEL_2_DOC_HEADER_PATTERNS):
            continue
        if _row_contains_tokens(row, ("FECHA", "OFICINA", "CONCEPTO", "DEBITO", "CREDITO", "SALDO")):
            return True

    return False


def detect_pdf_model(path):
    try:
        text, header_rows = _extract_pdf_text_and_headers(path)
    except Exception:
        return None

    if _looks_like_model_1(text, header_rows):
        return PDF_MODEL_1

    if _looks_like_model_2(text, header_rows):
        return PDF_MODEL_2

    return None


def parse_pdf(path):
    model = detect_pdf_model(path)
    pdf_name = os.path.splitext(os.path.basename(path))[0]

    if model is None:
        log_warning(f"\u26A0\uFE0F PDF {pdf_name} \u2192 MODELO DESCONOCIDO (se omite)")
        return None

    log_info(f"\U0001F4C4 PDF {pdf_name} \u2192 {model}")

    try:
        if model == PDF_MODEL_1:
            from loaders.pdf_models.model_1 import parse_model_1

            return parse_model_1(path)

        if model == PDF_MODEL_2:
            from loaders.pdf_models.model_2 import parse_model_2

            return parse_model_2(path)
    except Exception as exc:
        log_warning(f"\u26A0\uFE0F PDF {pdf_name} \u2192 ERROR AL PARSEAR ({exc})")
        return None

    log_warning(f"\u26A0\uFE0F PDF {pdf_name} \u2192 MODELO DESCONOCIDO (se omite)")
    return None
