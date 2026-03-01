import unittest
from unittest.mock import patch

import pandas as pd

import detect
from loaders.mov_pdf_header_unica import limpiar_movimientos_pdf_header_unica
from loaders.mov_pdf_auto import limpiar_movimientos_pdf_auto
from loaders.pdf_dispatcher import PDF_MODEL_1


class _FakePage:
    def __init__(self, text="", tables=None):
        self._text = text
        self._tables = tables or []

    def extract_text(self):
        return self._text

    def extract_tables(self):
        return self._tables


class _FakePdf:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class MovPdfHeaderUnicaTests(unittest.TestCase):
    def test_detecta_nuevo_formato_por_firma_de_columnas(self):
        pages = [
            _FakePage(
                text=(
                    "Pagina 1 de 3\n"
                    "Portada de requerimiento\n"
                    "FECHA OFICINA TIPO CONCEPTO NRO DOCUMENTO MONTO SALDO\n"
                )
            ),
            _FakePage(text="Solo data"),
        ]

        with patch("loaders.pdf_dispatcher.pdfplumber.open", return_value=_FakePdf(pages)):
            tipo = detect.detectar_formato_mov_pdf("fake.pdf")

        self.assertEqual(tipo, PDF_MODEL_1)

    def test_parser_mapea_nro_documento_y_conserva_registros(self):
        header = ["FECHA", "OFICINA", "TIPO", "CONCEPTO", "NRO DOCUMENTO", "MONTO", "SALDO"]

        page1_table = [[
            *header
        ], [
            "18/02/2026",
            "AG. NORTE",
            "C",
            "TRANSFERENCIA INTERNET",
            "3936490",
            "$ $12.95",
            "$ $3,967.14",
        ], [
            "18/02/2026",
            "AG. NORTE",
            "C",
            "021042TRANSFERENCIA\nINTERBANCARIA RECIBI",
            "6096224",
            "$ $7.95",
            "$ $4,312.67",
        ]]

        page2_table = [[
            "17/02/2026",
            "AG. SUR",
            "D",
            "TRANSFERENCIA INTERNET",
            "15428564",
            "$ $1.30",
            "$ $5,412.77",
        ], [
            "17/02/2026",
            "AG. SUR",
            "C",
            "CAJA NO. 2 PAGO TARJETA",
            "16001170",
            "$ $42.40",
            "$ $5,505.04",
        ]]

        pages = [
            _FakePage(tables=[page1_table]),
            _FakePage(tables=[page2_table]),
        ]

        with patch("loaders.mov_pdf_header_unica.pdfplumber.open", return_value=_FakePdf(pages)):
            df = limpiar_movimientos_pdf_header_unica("fake.pdf")

        self.assertEqual(
            list(df.columns),
            ["Fecha", "Concepto", "Tipo", "Monto", "Saldo", "Nro. Documento", "Recaudador"],
        )
        self.assertEqual(len(df), 4)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["Fecha"]))
        self.assertEqual(df.loc[0, "Nro. Documento"], "3936490")
        self.assertNotEqual(df.loc[0, "Nro. Documento"], "C")
        self.assertAlmostEqual(df.loc[0, "Monto"], 12.95, places=2)
        self.assertAlmostEqual(df.loc[0, "Saldo"], 3967.14, places=2)
        self.assertEqual(df.loc[1, "Nro. Documento"], "6096224")
        self.assertIn("INTERBANCARIA RECIBI", df.loc[1, "Concepto"])
        self.assertEqual(df.loc[2, "Tipo"], "DEBITO")
        self.assertEqual(df.loc[3, "Recaudador"], "CAJA 2")

    def test_pool_auto_enruta_al_parser_nuevo(self):
        expected = pd.DataFrame([{"Nro. Documento": "1"}])

        with patch("loaders.mov_pdf_auto.parse_pdf", return_value=expected), \
             patch("builtins.print"):
            result = limpiar_movimientos_pdf_auto("fake.pdf")

        self.assertIs(result, expected)


if __name__ == "__main__":
    unittest.main()
