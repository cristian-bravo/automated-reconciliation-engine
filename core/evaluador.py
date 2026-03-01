# core/evaluador.py
def evaluar(doc, monto, doc_to_montos, monto_to_docs, pairs_ref, origen="Banco", destino="Caja"):
    """
    Retorna (estado, detalle_revision)
    """
    if (doc, monto) in pairs_ref:
        return "COINCIDE", ""

    doc_ok = doc in doc_to_montos if doc else False
    monto_ok = monto in monto_to_docs if monto is not None else False

    if doc_ok and monto_ok:
        # monto_destino = valor registrado en el OTRO sistema (ej: PDF cuando se evalúa desde TRS)
        monto_destino = doc_to_montos[doc][0]
        return "REVISAR", f"Doc y monto existen por separado ({origen}: {monto} | {destino}: {monto_destino})"
        
    if monto_ok:
        # Extraer hasta 6 números de documento que tengan ese monto, y unirlos
        docs_con_monto = list(monto_to_docs[monto])[:6]
        str_docs = ";".join(docs_con_monto)
        return "REVISAR", f"Monto coincide con Nro. Doc: {str_docs}"
        
    if doc_ok:
        # Averiguar la diferencia tomando el primer monto registrado para ese doc
        monto_registrado = doc_to_montos[doc][0]
        # Validamos que ambos sean flotantes válidos
        try:
            diferencia = abs(monto_registrado - monto)
            return "REVISAR", f"Documento coincide, dif. monto: {round(diferencia, 2)} ({origen}: {monto} | {destino}: {monto_registrado})"
        except Exception:
            return "REVISAR", f"Documento coincide: {doc} ({origen}: {monto})"

    return "NO COINCIDE", ""
