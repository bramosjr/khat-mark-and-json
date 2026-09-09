import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.llm_parsers import (
    parse_with_llm,
    _strip_markdown_json_fence,
    _require_model,
    PROVIDERS,
)


def _make_minimal_pdf(tmp_dir: Path) -> Path:
    import fitz  # PyMuPDF

    pdf_path = tmp_dir / "teste.pdf"
    doc = fitz.open()
    try:
        page = doc.new_page()
        page.insert_text((72, 72), "conteudo de teste")
        doc.save(str(pdf_path))
    finally:
        doc.close()
    return pdf_path


class TestStripMarkdownJsonFence(unittest.TestCase):
    def test_strips_json_fence(self):
        self.assertEqual(_strip_markdown_json_fence('```json\n{"a": 1}\n```'), '{"a": 1}')

    def test_strips_bare_fence(self):
        self.assertEqual(_strip_markdown_json_fence('```\n{"a": 1}\n```'), '{"a": 1}')

    def test_leaves_plain_json_untouched(self):
        self.assertEqual(_strip_markdown_json_fence('{"a": 1}'), '{"a": 1}')


class TestRequireModel(unittest.TestCase):
    def test_returns_stripped_model_name(self):
        self.assertEqual(_require_model("  gemini-3.8-flash  ", "Gemini"), "gemini-3.8-flash")

    def test_raises_on_empty(self):
        with self.assertRaises(ValueError):
            _require_model("", "Gemini")

    def test_raises_on_none(self):
        with self.assertRaises(ValueError):
            _require_model(None, "Gemini")


class TestProviderRegistry(unittest.TestCase):
    def test_registers_expected_providers(self):
        self.assertEqual(
            set(PROVIDERS.keys()),
            {"openai", "gemini", "anthropic", "openai_compatible"},
        )


class TestParseWithLlmErrorPaths(unittest.TestCase):
    """
    Estes testes cobrem só os caminhos de erro que não chegam a fazer uma
    chamada de rede real (provedor desconhecido, modelo/URL não
    informados) — os caminhos de sucesso dependem de APIs externas de
    terceiros e ficam fora do escopo de um teste automatizado local.
    """

    def test_unknown_provider_raises_without_network_call(self):
        with TemporaryDirectory() as tmp:
            pdf_path = _make_minimal_pdf(Path(tmp))
            with self.assertRaises(ValueError) as ctx:
                parse_with_llm(str(pdf_path), "provedor-inexistente", "fake-key")
            self.assertIn("Provedor de LLM desconhecido", str(ctx.exception))

    def test_gemini_without_model_raises_clear_error(self):
        with TemporaryDirectory() as tmp:
            pdf_path = _make_minimal_pdf(Path(tmp))
            with self.assertRaises(ValueError) as ctx:
                parse_with_llm(str(pdf_path), "gemini", "fake-key", model_name="")
            self.assertIn("Informe o nome do modelo", str(ctx.exception))

    def test_anthropic_without_model_raises_clear_error(self):
        with TemporaryDirectory() as tmp:
            pdf_path = _make_minimal_pdf(Path(tmp))
            with self.assertRaises(ValueError) as ctx:
                parse_with_llm(str(pdf_path), "anthropic", "fake-key", model_name=None)
            self.assertIn("Informe o nome do modelo", str(ctx.exception))

    def test_openai_compatible_without_base_url_raises_clear_error(self):
        with TemporaryDirectory() as tmp:
            pdf_path = _make_minimal_pdf(Path(tmp))
            with self.assertRaises(ValueError) as ctx:
                parse_with_llm(
                    str(pdf_path), "openai_compatible", "fake-key",
                    model_name="llama-3.3-70b", base_url="",
                )
            self.assertIn("URL base", str(ctx.exception))

    def test_provider_name_is_case_insensitive(self):
        with TemporaryDirectory() as tmp:
            pdf_path = _make_minimal_pdf(Path(tmp))
            # 'GEMINI' deve rotear pro mesmo handler que 'gemini' — falha
            # por falta de modelo (esperado), não por provedor desconhecido.
            with self.assertRaises(ValueError) as ctx:
                parse_with_llm(str(pdf_path), "GEMINI", "fake-key", model_name="")
            self.assertIn("Informe o nome do modelo", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
