import pdfplumber
import pandas as pd
import re
from core.mov_helpers import extraer_caja_texto


def normalize_amount(txt):
    """
    Convierte textos como '130,25' a flotantes ignorando cualquier punto de miles si existiese
    """
    if not txt:
        return 0.0
    txt = txt.replace(".", "").replace(",", ".")
    try:
        return float(txt)
    except ValueError:
        return 0.0


def limpiar_movimientos_pdf_portada(path):
    """
    Toma un PDF bancario con formato ruidoso (portada, headers repetidos).
    Ignora tablas y funciona buscando únicamente líneas que comiencen con 
    un número de identificación (ej: 1712530128).
    """
    filas = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            # Extraemos todo el texto puro línea por línea
            texto = page.extract_text()
            if not texto:
                continue
            
            lineas = texto.split("\n")
            
            for linea in lineas:
                linea = linea.strip()
                
                # -----------------------------
                # 🔑 REGLA DE INICIO (El RUC/CC tiene usualmente entre 10 y 13 dígitos)
                # Ejemplo de fila soportada: 
                # 1712530128 VEGA JIMENEZ... 2025-12-01 00044433 TRANSFERENCIA 130,25 108541,57
                # -----------------------------
                if not re.match(r"^\d{10,13}\b", linea):
                    continue
                
                # -----------------------------
                # MONTOS Y SALDOS (los dos últimos números decimales al final de la línea)
                # -----------------------------
                montos = re.findall(r"\b\d+,\d{2}\b", linea)
                if len(montos) < 2:
                    continue  # Requiere al menos monto y saldo
                
                # Saldo siempre es el último número. Monto el penúltimo.
                saldo = normalize_amount(montos[-1])
                monto = normalize_amount(montos[-2])
                
                # Eliminar los montos numéricos de la línea para facilitar el re.search siguiente
                linea_sin_montos = linea
                for m in montos:
                    linea_sin_montos = linea_sin_montos.replace(m, "")

                # -----------------------------
                # FECHA (obligatoria)
                # -----------------------------
                m_fecha = re.search(r"\b\d{4}-\d{2}-\d{2}\b", linea_sin_montos)
                if not m_fecha:
                    continue
                fecha_raw = m_fecha.group(0)
                
                # Transformar '2025-12-01' a '01/12/2025'
                partes = fecha_raw.split("-")
                fecha = f"{partes[2]}/{partes[1]}/{partes[0]}"
                
                # -----------------------------
                # DOCUMENTO (Buscamos lo que sigue exactamente a la fecha raw, eliminando ceros iniciales)
                # -----------------------------
                nro_doc = ""
                # Tomamos la línea que sigue después de "2025-12-01"
                partes_linea = linea_sin_montos.split(fecha_raw, 1)
                if len(partes_linea) > 1:
                    # Buscamos el primer bloque de al menos 4-5 dígitos
                    m_doc = re.search(r"\b\d{4,}\b", partes_linea[1])
                    if m_doc:
                        nro_doc = m_doc.group(0)
                        # Eliminar ceros a la izquierda, pero si solo son ceros, dejar uno.
                        nro_doc_limpio = nro_doc.lstrip("0")
                        nro_doc = nro_doc_limpio if nro_doc_limpio else "0"
                    
                # -----------------------------
                # TIPO (Débito/Crédito)
                # -----------------------------
                # Generalmente el formato lo dice, pero la asunción estándar en los otros scripts:
                # Si el regex la trata como "CREDITO" lo mantenemos. Validemos texto.
                tipo = "DEBITO"
                if "CRÉDITO" in linea.upper() or "CREDITO" in linea.upper():
                    tipo = "CREDITO"
                
                # *Nota*: En este PDF, un truco clásico es que si no hay un signo -, si sumó al saldo
                # se verifica contablemente en el core de Vega. Dejaremos que pandas y core hagan el cruce numérico exacto.
                
                # -----------------------------
                # CONCEPTO (El resto de la línea)
                # -----------------------------
                concepto = linea_sin_montos
                # Limpiar Fecha raw, Ruc al inicio, y Doc literal
                concepto = re.sub(r"^\d{10,13}\b", "", concepto)
                concepto = concepto.replace(fecha_raw, "")
                if nro_doc and m_doc:
                    # Quitamos el fragmento original con ceros para limpiar de verdad
                    concepto = concepto.replace(m_doc.group(0), "")
                
                # Opcional: limpiar la palabra "TRANSFERENCIA INTERNET H" que suele aportar ruido irrelevante si se desea
                # concepto = concepto.replace("TRANSFERENCIA INTERNET H", "")
                
                concepto = re.sub(r"\s{2,}", " ", concepto).strip()
                
                # -----------------------------
                # RECAUDADOR
                # -----------------------------
                recaudador = extraer_caja_texto(concepto)

                filas.append({
                    "Fecha": fecha,
                    "Concepto": concepto,
                    "Tipo": tipo,
                    "Monto": monto,
                    "Saldo": saldo,
                    "Nro. Documento": nro_doc,
                    "Recaudador": recaudador
                })

    df = pd.DataFrame(
        filas,
        columns=[
            "Fecha",
            "Concepto",
            "Tipo",
            "Monto",
            "Saldo",
            "Nro. Documento",
            "Recaudador"
        ]
    )

    return df
