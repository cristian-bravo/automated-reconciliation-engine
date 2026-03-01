# core/utils.py
import pandas as pd
import re


# ===============================
# Normalizaciones existentes
# ===============================

def normalize_doc(x):
    if pd.isna(x):
        return ""
    s = str(x).strip()
    return s[:-2] if s.endswith(".0") else s


def normalize_amount(x):
    if pd.isna(x):
        return None
    s = str(x).replace("$", "").replace(" ", "")
    # soporta 1.234,56 y 1234.56
    if s.count(",") == 1 and s.count(".") >= 1:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return round(float(s), 2)
    except:
        return None


# ===============================
# Limpieza de caracteres ilegales
# ===============================

_ILLEGAL_CHARS_RE = re.compile(r"[\x00-\x1F\x7F]")

def clean_illegal_chars(value):
    """
    Elimina caracteres invisibles/ilegales para Excel.
    Necesario para datos que vienen de PDFs.
    """
    if isinstance(value, str):
        return _ILLEGAL_CHARS_RE.sub("", value)
    return value
