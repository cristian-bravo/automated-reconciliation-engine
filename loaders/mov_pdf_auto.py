from loaders.pdf_dispatcher import parse_pdf


def limpiar_movimientos_pdf_auto(path):
    """
    Mantiene la interfaz histórica del proyecto y delega al dispatcher
    de modelos PDF (PDF_MODEL_1 / PDF_MODEL_2).
    """
    return parse_pdf(path)

