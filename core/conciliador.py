# core/conciliador.py
from core.evaluador import evaluar
from core.utils import normalize_doc, normalize_amount
from config import LOCALES


def conciliar(mov, trs_all):
    # Normalización
    mov["_doc"] = mov["Nro. Documento"].apply(normalize_doc)
    mov["_monto"] = mov["Monto"].apply(normalize_amount)

    trs_all["_doc"] = trs_all["Nro. Documento"].apply(normalize_doc)
    trs_all["_monto"] = trs_all["Valor"].apply(normalize_amount)

    set_trs_docs = set(trs_all["_doc"])
    set_trs_montos = set(trs_all["_monto"])
    set_trs_pairs = set(zip(trs_all["_doc"], trs_all["_monto"]))

    # (voucher, valor) → Recaudador + Sucursal
    pair_to_info = {}
    trs_doc_to_montos = {}
    trs_monto_to_docs = {}
    
    for _, r in trs_all.iterrows():
        d = r["_doc"]
        m = r["_monto"]
        key = (d, m)
        pair_to_info[key] = {
            "Recaudador": r.get("Recaudador", ""),
            "Sucursal": LOCALES.get(r.get("local_code"), "")
        }
        
        # Mapeos de uno a muchos (dict de lists)
        trs_doc_to_montos.setdefault(d, []).append(m)
        trs_monto_to_docs.setdefault(m, []).append(str(d))

    estados = []
    detalles = []
    sucursales = []
    recaudadores = []

    # ===== MOVIMIENTOS =====
    for _, r in mov.iterrows():
        estado, detalle = evaluar(
            r["_doc"], r["_monto"],
            trs_doc_to_montos, trs_monto_to_docs, set_trs_pairs,
            "Banco", "Caja"
        )

        estados.append(estado)
        detalles.append(detalle)

        if estado == "COINCIDE":
            info = pair_to_info.get((r["_doc"], r["_monto"]), {})
            sucursales.append(info.get("Sucursal", ""))
            recaudadores.append(info.get("Recaudador", ""))
        else:
            sucursales.append("")
            recaudadores.append("")

    # ORDEN: Sucursal → Recaudador  |  Detalle con mayúscula
    mov["Sucursal"] = sucursales
    mov["Recaudador"] = recaudadores
    mov["estado"] = estados
    mov["Detalle"] = detalles

    mov.drop(columns=["detalle", "detalle_revision"], errors="ignore", inplace=True)

    # ===== TRS =====
    trs_estados = []
    trs_detalles = []

    set_mov_pairs = set(zip(mov["_doc"], mov["_monto"]))
    mov_doc_to_montos = {}
    mov_monto_to_docs = {}
    
    for _, r in mov.iterrows():
        d = r["_doc"]
        m = r["_monto"]
        mov_doc_to_montos.setdefault(d, []).append(m)
        mov_monto_to_docs.setdefault(m, []).append(str(d))

    for _, r in trs_all.iterrows():
        estado, detalle = evaluar(
            r["_doc"], r["_monto"],
            mov_doc_to_montos, mov_monto_to_docs, set_mov_pairs,
            "Caja", "Banco"
        )
        trs_estados.append(estado)
        trs_detalles.append(detalle)

    trs_all["estado"] = trs_estados
    trs_all["Detalle"] = trs_detalles
    trs_all.drop(columns=["detalle", "detalle_revision"], errors="ignore", inplace=True)

    return (
        mov.drop(columns=["_doc", "_monto"]),
        trs_all.drop(columns=["_doc", "_monto"])
    )
