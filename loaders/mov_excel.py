import pandas as pd
from core.mov_helpers import extraer_nro_documento_fila, extraer_caja_texto


def limpiar_movimientos_excel(path):

    # =========================================================
    # 🆕 FORMATO CON METADATA ARRIBA (Fecha | Oficina | Tipo ...)
    # =========================================================
    raw = pd.read_excel(path, header=None, engine="pyxlsb")

    header_row = None

    for i, row in raw.iterrows():
        row_text = " ".join(row.astype(str)).lower()

        if "fecha" in row_text and "concepto" in row_text and "monto" in row_text:
            header_row = i
            break

    if header_row is not None:
        df = pd.read_excel(path, header=header_row, engine="pyxlsb")

        df.columns = df.columns.str.strip()

        df = df.rename(columns={
            "Documento": "Nro. Documento",
            "Saldo Contable": "Saldo"
        })

        df["Recaudador"] = df["Concepto"].apply(extraer_caja_texto)

        columnas_finales = [
            "Fecha",
            "Concepto",
            "Tipo",
            "Monto",
            "Saldo",
            "Nro. Documento",
            "Recaudador",
        ]

        return df[columnas_finales]

    # =========================================================
    # 🆕 NUEVO FORMATO (exportado desde PDF)
    # =========================================================
    raw = pd.read_excel(path)

    if "FECHA" in raw.columns and "Fecha" not in raw.columns:
        df = raw.copy()

        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
            .str.upper()
        )

        df = df.rename(columns={
            "FECHA": "Fecha",
            "DESCRIPCION": "Concepto",
            "NUMERO DE DOCUMENTO": "Nro. Documento",
            "SALDO": "Saldo",
            "DEBITO": "Debito",
            "CREDITO": "Credito",
        })

        df["Monto"] = df["Credito"].fillna(0) - df["Debito"].fillna(0)

        df["Tipo"] = ""
        df["Recaudador"] = df["Concepto"].apply(extraer_caja_texto)

        columnas_finales = [
            "Fecha",
            "Concepto",
            "Tipo",
            "Monto",
            "Saldo",
            "Nro. Documento",
            "Recaudador",
        ]

        return df[columnas_finales]

    # =========================================================
    # 📦 FORMATO EXCEL VIEJO (NO SE TOCA)
    # =========================================================
    raw = pd.read_excel(path, header=None)

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