"""Correções que vieram com a atualização do MarkItDown."""
from core.automation import Automation


def test_json_com_acentos_so_no_fim_do_arquivo(tmp_path):
    origem = tmp_path / "tarde.json"
    origem.write_text('{"a": "' + "x" * 20000 + '", "b": "café, 日本語"}', encoding="utf-8")

    conteudo = Automation().executar(str(origem))["conteudo"]

    assert "café, 日本語" in conteudo
