import pdfplumber
import pandas as pd
import re


def normalize_amount(txt):
    return float(txt.replace(".", "").replace(",", "."))


def limpiar_movimientos_pdf2(path):
    """
    Loader adaptativo para PDFs bancarios impredecibles.
    Mantiene el MISMO nombre de función y archivo.
    """

    filas = []

    with pdfplumber.open(path) as pdf:
        for page_idx, page in enumerate(pdf.pages):

            table = page.extract_table()
            if not table:
                continue

            # Solo ignorar la fila 0 si es la primera página (portada)
            filas_target = table[1:] if page_idx == 0 else table
            
            for row in filas_target:
                if not row or not row[0]:
                    continue

                bloque = row[0].replace("\n", " ").strip()

                # -----------------------------
                # FECHA (obligatoria)
                # -----------------------------
                m_fecha = re.search(r"\d{4}-\d{1,2}-\d{1,2}", bloque)
                if not m_fecha:
                    continue
                fecha = m_fecha.group(0)

                # -----------------------------
                # DOCUMENTO (opcional)
                # -----------------------------
                m_doc = re.search(r"\b\d{6,}\b", bloque)
                nro_doc = m_doc.group(0) if m_doc else ""

                # -----------------------------
                # MONTOS (obligatorios)
                # -----------------------------
                montos = re.findall(r"\$([\d\.,]+)", bloque)
                if len(montos) < 2:
                    continue

                monto = normalize_amount(montos[0])
                saldo = normalize_amount(montos[1])

                # -----------------------------
                # TIPO
                # -----------------------------
                tipo = (
                    "CREDITO"
                    if "CRÉDITO" in bloque.upper() or "CREDITO" in bloque.upper()
                    else "DEBITO"
                )

                # -----------------------------
                # CONCEPTO LIMPIO
                # -----------------------------
                concepto = bloque
                concepto = concepto.replace(fecha, "")
                if nro_doc:
                    concepto = concepto.replace(nro_doc, "")
                concepto = re.sub(r"\$[\d\.,]+", "", concepto)
                concepto = re.sub(r"\s{2,}", " ", concepto).strip()

                filas.append({
                    "Fecha": fecha,
                    "Concepto": concepto,
                    "Tipo": tipo,
                    "Monto": monto,
                    "Saldo": saldo,
                    "Nro. Documento": nro_doc,
                })

    return pd.DataFrame(
        filas,
        columns=[
            "Fecha",
            "Concepto",
            "Tipo",
            "Monto",
            "Saldo",
            "Nro. Documento",
        ]
    )
