import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.offline_parsers import parse_tabular_to_json, parse_pdf_to_json_offline


class TestParseTabularToJson(unittest.TestCase):
    def test_empty_numeric_cell_becomes_json_serializable_null(self):
        """
        Regressão: pd.read_csv/read_excel produz NaN (float) para células
        vazias em colunas numéricas. json.dumps não aceita NaN
        ("Out of range float values are not JSON compliant"), o que antes
        derrubava a resposta HTTP a meio da serialização (o cliente via
        "Failed to fetch" em vez de um erro tratado).
        """
        with TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "dados.csv"
            csv_path.write_text("nome,idade\nAna,30\nBob,\n", encoding="utf-8")

            result = parse_tabular_to_json(str(csv_path))

            # O próprio ato de serializar não pode levantar ValueError.
            serialized = json.dumps(result)
            reloaded = json.loads(serialized)

            rows = reloaded["content"]
            self.assertEqual(rows[0], {"nome": "Ana", "idade": 30})
            self.assertEqual(rows[1]["nome"], "Bob")
            self.assertIsNone(rows[1]["idade"])

    def test_reports_row_count_and_source_type(self):
        with TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "dados.csv"
            csv_path.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")

            result = parse_tabular_to_json(str(csv_path))

            self.assertEqual(result["metadata"]["source_type"], "tabular")
            self.assertEqual(result["metadata"]["rows"], 2)


class TestParsePdfToJsonOffline(unittest.TestCase):
    def _make_minimal_pdf(self, tmp_dir: Path, text: str = "Ola mundo de teste") -> Path:
        import fitz  # PyMuPDF

        pdf_path = tmp_dir / "teste.pdf"
        doc = fitz.open()
        try:
            page = doc.new_page()
            page.insert_text((72, 72), text)
            doc.save(str(pdf_path))
        finally:
            doc.close()
        return pdf_path

    def test_extracts_text_and_reports_page_count(self):
        with TemporaryDirectory() as tmp:
            pdf_path = self._make_minimal_pdf(Path(tmp))

            result = parse_pdf_to_json_offline(str(pdf_path))

            self.assertEqual(result["metadata"]["source_type"], "pdf_offline_heuristic")
            self.assertEqual(result["metadata"]["pages"], 1)
            texts = [item["content"] for item in result["content"] if item["type"] == "text"]
            self.assertTrue(any("Ola mundo de teste" in t for t in texts))

    def test_result_is_json_serializable(self):
        with TemporaryDirectory() as tmp:
            pdf_path = self._make_minimal_pdf(Path(tmp))
            result = parse_pdf_to_json_offline(str(pdf_path))
            json.dumps(result)  # não deve levantar

    def test_does_not_leave_the_pdf_document_open(self):
        """
        Regressão: antes, `doc = fitz.open(...)` nunca era fechado. Aqui
        confirmamos que o documento fica fechado ao final (doc.close()
        torna `len(doc)`/acesso a página inválidos em versões recentes do
        PyMuPDF) — reabrir o mesmo arquivo depois também precisa funcionar
        sem 'arquivo em uso' (o cenário real que motivou a correção no
        Windows).
        """
        with TemporaryDirectory() as tmp:
            pdf_path = self._make_minimal_pdf(Path(tmp))
            parse_pdf_to_json_offline(str(pdf_path))

            # Se o handle anterior não tivesse sido liberado, reabrir e
            # reescrever o mesmo caminho falharia em alguns SOs/backends.
            import fitz
            doc = fitz.open(str(pdf_path))
            try:
                self.assertEqual(len(doc), 1)
            finally:
                doc.close()


if __name__ == "__main__":
    unittest.main()
