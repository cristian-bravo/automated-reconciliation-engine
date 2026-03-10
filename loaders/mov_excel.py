import os

import pandas as pd

from core.mov_helpers import extraer_caja_texto, extraer_nro_documento_fila

_COLUMNAS_FINALES = [
    "Fecha",
    "Concepto",
    "Tipo",
    "Monto",
    "Saldo",
    "Nro. Documento",
    "Recaudador",
]

_COLUMNAS_CANONICAS = {
    "fecha": "Fecha",
    "descripcion": "Concepto",
    "descripción": "Concepto",
    "concepto": "Concepto",
    "tipo": "Tipo",
    "monto": "Monto",
    "saldo": "Saldo",
    "saldo contable": "Saldo",
    "documento": "Nro. Documento",
    "nro documento": "Nro. Documento",
    "nro. documento": "Nro. Documento",
    "numero de documento": "Nro. Documento",
    "número de documento": "Nro. Documento",
    "debito": "Debito",
    "débito": "Debito",
    "credito": "Credito",
    "crédito": "Credito",
}


def _preferred_engines(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".xlsb":
        return ["pyxlsb", None]
    if ext == ".xls":
        return ["xlrd", None]
    if ext in {".xlsx", ".xlsm"}:
        return ["openpyxl", None]
    return [None]


def _read_excel_with_fallbacks(path, **kwargs):
    last_exc = None
    for engine in _preferred_engines(path):
        try:
            if engine is None:
                return pd.read_excel(path, **kwargs)
            return pd.read_excel(path, engine=engine, **kwargs)
        except Exception as exc:
            last_exc = exc
    raise last_exc


def _row_to_text(row):
    values = ["" if pd.isna(value) else str(value) for value in row.tolist()]
    return " ".join(values).strip().lower()


def _renombrar_columnas(df):
    mapping = {}
    for col in df.columns:
        col_str = str(col).strip()
        mapping[col] = _COLUMNAS_CANONICAS.get(col_str.lower(), col_str)
    return df.rename(columns=mapping)


def _normalizar_documento(value):
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _parse_amount(value):
    if pd.isna(value):
        return None

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return round(float(value), 2)

    text = str(value).strip().replace("$", "").replace(" ", "").replace("\u00A0", "")
    if not text or text.lower() == "nan":
        return None

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif text.count(",") > 1:
        text = text.replace(",", "")
    elif text.count(",") == 1:
        left, right = text.split(",", 1)
        if len(right) == 2:
            text = f"{left}.{right}"
        else:
            text = f"{left}{right}"
    elif text.count(".") > 1:
        parts = text.split(".")
        if len(parts[-1]) == 2:
            text = "".join(parts[:-1]) + "." + parts[-1]
        else:
            text = "".join(parts)

    try:
        return round(float(text), 2)
    except ValueError:
        return None


def _normalizar_fechas(series):
    def _parse_fecha(value):
        if pd.isna(value):
            return pd.NaT

        if isinstance(value, pd.Timestamp):
            return value

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return pd.to_datetime(value, unit="D", origin="1899-12-30", errors="coerce")

        text = str(value).strip()
        if not text or text.lower() == "nan":
            return pd.NaT

        text = text.replace(".", "/").replace("-", "/")
        return pd.to_datetime(text, dayfirst=True, errors="coerce")

    return series.apply(_parse_fecha)


def _armar_salida(df):
    df = df.copy()
    df = _renombrar_columnas(df)
    df = df.dropna(how="all")

    if "Fecha" not in df.columns or "Concepto" not in df.columns:
        return None

    if "Monto" not in df.columns:
        if "Credito" not in df.columns and "Debito" not in df.columns:
            return None

        credito = df["Credito"].apply(_parse_amount) if "Credito" in df.columns else pd.Series(0, index=df.index)
        debito = df["Debito"].apply(_parse_amount) if "Debito" in df.columns else pd.Series(0, index=df.index)
        df["Monto"] = credito.fillna(0) - debito.fillna(0)

    if "Tipo" not in df.columns:
        df["Tipo"] = ""
    if "Saldo" not in df.columns:
        df["Saldo"] = None
    if "Nro. Documento" not in df.columns:
        df["Nro. Documento"] = None

    df["Fecha"] = _normalizar_fechas(df["Fecha"])
    df["Concepto"] = df["Concepto"].fillna("").astype(str).str.strip()
    df["Tipo"] = df["Tipo"].fillna("").astype(str).str.strip()
    df["Monto"] = df["Monto"].apply(_parse_amount)
    df["Saldo"] = df["Saldo"].apply(_parse_amount)
    df["Nro. Documento"] = df["Nro. Documento"].apply(_normalizar_documento)
    df["Recaudador"] = df["Concepto"].apply(extraer_caja_texto)

    mascara_registros = (
        df["Monto"].notna()
        | df["Nro. Documento"].notna()
        | df["Concepto"].ne("")
    )
    df = df.loc[mascara_registros].copy()

    if df.empty:
        return None

    return df[_COLUMNAS_FINALES]


def _parse_formato_header_despues_de_metadata(path):
    raw = _read_excel_with_fallbacks(path, header=None)

    header_row = None
    for i, row in raw.iterrows():
        row_text = _row_to_text(row)
        if "fecha" in row_text and "concepto" in row_text and "monto" in row_text:
            header_row = i
            break

    if header_row is None:
        return None

    df = _read_excel_with_fallbacks(path, header=header_row)
    return _armar_salida(df)


def _parse_formato_tabular(path):
    raw = _read_excel_with_fallbacks(path)
    return _armar_salida(raw)


def _parse_formato_legacy(path):
    raw = _read_excel_with_fallbacks(path, header=None)

    df = raw.iloc[5:].reset_index(drop=True)
    df = df.drop(columns=[0, 1])
    df.columns = df.iloc[0]
    df = df.iloc[1:].reset_index(drop=True)
    df = df.loc[:, ~df.columns.astype(str).str.contains("Unnamed")]

    df["_inicio"] = df["Fecha"].notna()

    for c in ["Fecha", "Concepto", "Tipo", "Beneficiario"]:
        if c in df.columns:
            df[c] = df[c].ffill()

    movimientos = []
    current = None

    for _, r in df.iterrows():
        if r["_inicio"]:
            if current:
                movimientos.append(current)

            current = {
                "Fecha": r.get("Fecha"),
                "Concepto": r.get("Concepto"),
                "Tipo": r.get("Tipo"),
                "Monto": r.get("Monto"),
                "Saldo": r.get("Saldo"),
                "Nro. Documento": None,
                "Recaudador": extraer_caja_texto(r.get("Concepto")),
            }
        else:
            doc = extraer_nro_documento_fila(r)
            if doc:
                current["Nro. Documento"] = doc

    if current:
        movimientos.append(current)

    return pd.DataFrame(movimientos)


def limpiar_movimientos_excel(path):
    for parser in (_parse_formato_header_despues_de_metadata, _parse_formato_tabular):
        df = parser(path)
        if df is not None and not df.empty:
            return df

    return _parse_formato_legacy(path)
