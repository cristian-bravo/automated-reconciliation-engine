# loaders/trs.py
import pandas as pd
import re
from core.mov_helpers import extraer_caja_texto
from config import LOCALES

def _solo_numeros(texto):
    if pd.isna(texto):
        return ""
    m = re.search(r"(\d+)", str(texto))
    return m.group(1) if m else ""

def limpiar_trs(path, local_code):
    raw = pd.read_excel(path, header=None)

    df = raw.iloc[8:].reset_index(drop=True)
    df = df.drop(index=1).reset_index(drop=True)
    df.columns = df.iloc[0]
    df = df.iloc[1:].reset_index(drop=True)

    df.columns = [str(c).strip() for c in df.columns]

    # Recaudador desde Detalle del Pago
    df["Recaudador"] = df["Detalle del Pago"].apply(extraer_caja_texto)

    # Factura solo numérica desde Documentos
    df["Factura"] = df["Documentos"].apply(_solo_numeros)

    # Renombrar No.Voucher → Nro. Documento
    df.rename(columns={"No.Voucher": "Nro. Documento"}, inplace=True)

    # Columnas finales en el orden solicitado
    df_final = df[[
        "Fecha",
        "Factura",
        "Recaudador",
        "Nro. Documento",
        "Valor",
        "Detalle del Pago",
    ]].copy()

    df_final.rename(columns={"Detalle del Pago": "Detalle"}, inplace=True)

    # Mantener info interna para conciliación/export
    df_final["local_code"] = local_code
    df_final["local_nombre"] = LOCALES.get(local_code, local_code)

    return df_final
