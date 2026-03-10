import unittest
from unittest.mock import patch

import pandas as pd

import detect
from core.utils import normalize_amount
from loaders.mov_excel import limpiar_movimientos_excel


class MovExcelTests(unittest.TestCase):
    def test_loader_soporta_metadata_superior_en_archivo_bancario(self):
        raw = pd.DataFrame(
            [
                ["Nombre:", "VEGA", None, None, None, None, None],
                ["Numero de Cuenta:", "2100183427", None, None, None, "Oficina:", "LAGO AGRIO"],
                ["Asesor:", "MARIA", None, None, None, None, None],
                ["Periodo:", None, None, None, None, None, None],
                [None, "Desde:", 46086, "Hasta:", 46086, None, None],
                [None, "Saldo Inicial:", "4,112.97", None, None, None, None],
                ["Fecha", "Oficina", "Tipo", "Concepto", "Documento", "Monto", "Saldo Contable"],
                [46086, "AG. NORTE", "C", "TRANSFERENCIA INTERNET", 73210623, "1,234.50", "6,014.41"],
            ]
        )

        parsed = pd.DataFrame(
            {
                "Fecha": [46086],
                "Oficina": ["AG. NORTE"],
                "Tipo": ["C"],
                "Concepto": ["TRANSFERENCIA INTERNET"],
                "Documento": [73210623],
                "Monto": ["1,234.50"],
                "Saldo Contable": ["6,014.41"],
            }
        )

        with patch("loaders.mov_excel._read_excel_with_fallbacks", side_effect=[raw, parsed]):
            df = limpiar_movimientos_excel("fake.xlsb")

        self.assertEqual(
            list(df.columns),
            ["Fecha", "Concepto", "Tipo", "Monto", "Saldo", "Nro. Documento", "Recaudador"],
        )
        self.assertEqual(len(df), 1)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["Fecha"]))
        self.assertEqual(df.loc[0, "Fecha"].strftime("%d/%m/%Y"), "05/03/2026")
        self.assertEqual(df.loc[0, "Nro. Documento"], "73210623")
        self.assertAlmostEqual(df.loc[0, "Monto"], 1234.50, places=2)
        self.assertAlmostEqual(df.loc[0, "Saldo"], 6014.41, places=2)

    @patch("detect.log_warning")
    @patch("detect._listdir_safe")
    @patch("detect.os.path.isfile", return_value=True)
    def test_detecta_pdf_y_excel_como_archivos_banco(self, _mock_isfile, mock_listdir, _mock_warning):
        mock_listdir.return_value = [
            "Mis Movimientos 05-03-2026.xlsb",
            "Estado Cuenta 06-03-2026.xlsx",
            "Banco 07-03-2026.pdf",
            "trs-vs-05-03-2026.xls",
            "nota 05-03-2026.txt",
        ]

        mov_files, trs_files = detect.detectar_archivos()

        self.assertEqual(
            set(mov_files.keys()),
            {"05_03_2026", "06_03_2026", "07_03_2026"},
        )
        self.assertTrue(mov_files["05_03_2026"].endswith(".xlsb"))
        self.assertTrue(mov_files["06_03_2026"].endswith(".xlsx"))
        self.assertTrue(mov_files["07_03_2026"].endswith(".pdf"))
        self.assertEqual(set(trs_files["05_03_2026"].keys()), {"vs"})


class NormalizeAmountTests(unittest.TestCase):
    def test_soporta_formatos_us_y_latam(self):
        self.assertEqual(normalize_amount("1,234.56"), 1234.56)
        self.assertEqual(normalize_amount("1.234,56"), 1234.56)
        self.assertEqual(normalize_amount("$ 1,234.56"), 1234.56)


if __name__ == "__main__":
    unittest.main()
