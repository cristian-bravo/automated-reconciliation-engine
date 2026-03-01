# core/mov_helpers.py
import pandas as pd
import re

def extraer_nro_documento_fila(row):
    for v in row:
        if pd.isna(v):
            continue
        s = str(v).strip()
        if s.endswith(".0"):
            s = s[:-2]
        if s.isdigit() and 6 <= len(s) <= 20:
            return s
    return None

def extraer_caja_texto(texto):
    if pd.isna(texto):
        return ""
    m = re.search(r"CAJA\s*NO\.?\s*(\d+)", str(texto), re.IGNORECASE)
    if m:
        return f"CAJA {m.group(1)}"
    return ""
