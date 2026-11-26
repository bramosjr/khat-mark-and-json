"""--dry-run e conversão real acusam conversor sem dependência (issue #3)."""
import sys

import pytest

import cli
from core.automation import Automation, AutomationError
from tests.test_formatos import AMOSTRAS

CASOS = [
    (".docx", "md", "mammoth"), (".docx", "json", "mammoth"), (".docx", "md", "lxml"),
    (".pptx", "md", "pptx"), (".pptx", "json", "pptx"),
    (".xlsx", "md", "openpyxl"), (".xlsx", "json", "openpyxl"),
    (".xls", "md", "xlrd"), (".xls", "json", "xlrd"),
    (".ods", "md", "odf"), (".ods", "md", "openpyxl"), (".ods", "json", "odf"),
    (".odt", "md", "odf"), (".odt", "json", "odf"),
    (".pdf", "md", "pdfminer"), (".pdf", "md", "pdfplumber"), (".pdf", "json", "fitz"),
    (".msg", "md", "olefile"),
    (".csv", "json", "pandas"), (".html", "md", "markitdown"),
]


def _arquivo(tmp_path, extensao):
    caminho = tmp_path / f"amostra{extensao}"
    caminho.write_bytes(b"x")  # o conteúdo não importa: a recusa vem antes
    return str(caminho)


@pytest.mark.parametrize("dry_run", [True, False])
@pytest.mark.parametrize("extensao,formato,modulo", CASOS)
def test_dependencia_ausente_e_recusada(tmp_path, monkeypatch, extensao, formato, modulo, dry_run):
    origem = _arquivo(tmp_path, extensao)
    monkeypatch.setitem(sys.modules, modulo, None)  # o Python trata como não instalado

    with pytest.raises(AutomationError) as erro:
        Automation().executar(origem, formato=formato, dry_run=dry_run)

    assert erro.value.codigo == "DEPENDENCIA_AUSENTE"
    assert modulo in erro.value.mensagem


@pytest.mark.parametrize("formato", ["md", "json"])
@pytest.mark.parametrize("extensao", sorted(AMOSTRAS))
def test_dry_run_passa_com_ambiente_completo(tmp_path, extensao, formato):
    r = Automation().executar(_arquivo(tmp_path, extensao), formato=formato, dry_run=True)
    assert r["ok"] is True


def test_describe_declara_o_codigo_novo():
    assert "DEPENDENCIA_AUSENTE" in cli.describe()["codigos_erro"]
