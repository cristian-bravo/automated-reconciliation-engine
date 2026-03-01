# loaders/mov_pdf.py
import pandas as pd
import pdfplumber

from core.utils import normalize_amount, clean_illegal_chars
from core.mov_helpers import extraer_caja_texto


def limpiar_movimientos_pdf(path):
    filas = []

    # ===============================
    # Extraer tablas del PDF
    # ===============================
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue

            # Omitir header de la tabla
            for row in table[1:]:
                if row and len(row) >= 7:
                    filas.append(row)

    # ===============================
    # DataFrame base
    # ===============================
    df = pd.DataFrame(
        filas,
        columns=[
            "Fecha",
            "Oficina",
            "Nro. Documento",
            "Concepto",
            "Debito",
            "Credito",
            "Saldo",
        ],
    )

    # ===============================
    # Limpieza de caracteres ilegales (PDFs)
    # ===============================
    df = df.map(clean_illegal_chars)

    # ===============================
    # Normalización de montos
    # ===============================
    df["Debito"] = df["Debito"].apply(normalize_amount)
    df["Credito"] = df["Credito"].apply(normalize_amount)

    # Forzar tipos correctos (evita FutureWarning)
    debito = df["Debito"].fillna(0).infer_objects(copy=False)
    credito = df["Credito"].fillna(0).infer_objects(copy=False)

    # ===============================
    # Lógica contable (NO CAMBIADA)
    # ===============================
    df["Monto"] = credito.where(credito > 0, debito)
    df["Tipo"] = credito.apply(
        lambda x: "CREDITO" if x > 0 else "DEBITO"
    )

    # ===============================
    # Recaudador / Caja
    # ===============================
    df["Recaudador"] = df["Concepto"].apply(extraer_caja_texto)

    # ===============================
    # Columnas finales
    # ===============================
    return df[
        [
            "Fecha",
            "Concepto",
            "Tipo",
            "Monto",
            "Saldo",
            "Nro. Documento",
            "Recaudador",
        ]
    ]
