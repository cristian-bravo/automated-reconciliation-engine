import unittest
from unittest.mock import patch

import pandas as pd

from loaders.pdf_models.model_1 import parse_model_1


class _FakePage:
    def __init__(self, text=""):
        self._text = text

    def extract_text(self):
        return self._text


class _FakePdf:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _valid_df():
    return pd.DataFrame(
        [
            {
                "Fecha": pd.Timestamp("2026-03-06"),
                "Concepto": "TRANSFERENCIA INTERNET",
                "Tipo": "CREDITO",
                "Monto": 11.35,
                "Saldo": 3684.76,
                "Nro. Documento": "73526313",
                "Recaudador": "",
            }
        ]
    )


class ParseModel1Tests(unittest.TestCase):
    def test_prioriza_pdf2_para_formato_documento_beneficiaria(self):
        pages = [
            _FakePage(
                "Fecha Concepto Tipo Monto Saldo Documento Beneficiaria\n"
                "2026-3-6 TRANSFERENCIA INTERNET 73526313 Credito $11,35 $3.684,76"
            )
        ]

        with patch("loaders.pdf_models.model_1.pdfplumber.open", return_value=_FakePdf(pages)), \
             patch("loaders.pdf_models.model_1.limpiar_movimientos_pdf2", return_value=_valid_df()) as pdf2, \
             patch("loaders.pdf_models.model_1.limpiar_movimientos_pdf_portada") as portada, \
             patch("loaders.pdf_models.model_1.limpiar_movimientos_pdf_header_unica") as header:
            result = parse_model_1("fake.pdf")

        self.assertEqual(len(result), 1)
        pdf2.assert_called_once_with("fake.pdf")
        portada.assert_not_called()
        header.assert_not_called()

    def test_prioriza_header_unica_para_formato_con_oficina(self):
        pages = [
            _FakePage(
                "FECHA OFICINA TIPO CONCEPTO NRO DOCUMENTO MONTO SALDO\n"
                "09/03/2026 AG. NORTE C TRANSFERENCIA INTERNET 3180161 $ $5.95 $ $3,690.71"
            )
        ]

        with patch("loaders.pdf_models.model_1.pdfplumber.open", return_value=_FakePdf(pages)), \
             patch("loaders.pdf_models.model_1.limpiar_movimientos_pdf_header_unica", return_value=_valid_df()) as header, \
             patch("loaders.pdf_models.model_1.limpiar_movimientos_pdf2") as pdf2, \
             patch("loaders.pdf_models.model_1.limpiar_movimientos_pdf_portada") as portada:
            result = parse_model_1("fake.pdf")

        self.assertEqual(len(result), 1)
        header.assert_called_once_with("fake.pdf")
        pdf2.assert_not_called()
        portada.assert_not_called()


if __name__ == "__main__":
    unittest.main()
