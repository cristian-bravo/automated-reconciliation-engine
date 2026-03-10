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

    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return round(float(x), 2)

    s = str(x).strip().replace("$", "").replace(" ", "").replace("\u00A0", "")
    if not s:
        return None

    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif s.count(",") > 1:
        s = s.replace(",", "")
    elif s.count(",") == 1:
        left, right = s.split(",", 1)
        if len(right) == 2:
            s = f"{left}.{right}"
        else:
            s = f"{left}{right}"
    elif s.count(".") > 1:
        parts = s.split(".")
        if len(parts[-1]) == 2:
            s = "".join(parts[:-1]) + "." + parts[-1]
        else:
            s = "".join(parts)

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
