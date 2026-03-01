import pandas as pd

from core.mov_helpers import extraer_caja_texto
from loaders.mov_pdf import limpiar_movimientos_pdf


_CANONICAL_COLS = [
    "Fecha",
    "Concepto",
    "Tipo",
    "Monto",
    "Saldo",
    "Nro. Documento",
    "Recaudador",
]


def _standardize_output(df):
    if not isinstance(df, pd.DataFrame):
        return df

    out = df.copy()

    for col in _CANONICAL_COLS:
        if col not in out.columns:
            out[col] = None

    out["Nro. Documento"] = out["Nro. Documento"].fillna("").astype(str).str.strip()
    out["Recaudador"] = out["Recaudador"].where(
        out["Recaudador"].notna() & (out["Recaudador"].astype(str).str.strip() != ""),
        out["Concepto"].fillna("").astype(str).apply(extraer_caja_texto),
    )

    return out[_CANONICAL_COLS]


def parse_model_2(path):
    """
    Parser del formato legacy (PDF_MODEL_2).
    """
    df = limpiar_movimientos_pdf(path)
    return _standardize_output(df)

