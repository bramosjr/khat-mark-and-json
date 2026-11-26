"""CSV para Markdown usa a mesma regra de codificação do JSON."""
import pytest

from core.automation import Automation

PORTUGUES = "nome,cidade\nJoão,São Paulo\nConceição,Maçã\n"
TABELA = "| nome | cidade |\n| --- | --- |\n| João | São Paulo |\n| Conceição | Maçã |"


def _markdown(tmp_path, dados: bytes):
    origem = tmp_path / "d.csv"
    origem.write_bytes(dados)
    return Automation().executar(str(origem))["conteudo"]


@pytest.mark.parametrize("codificacao", ["utf-8", "utf-8-sig", "latin-1", "cp1252", "utf-16"])
def test_texto_em_portugues_sai_certo(tmp_path, codificacao):
    assert _markdown(tmp_path, PORTUGUES.encode(codificacao)).strip() == TABELA


def test_arquivo_minimo_em_latin1(tmp_path):
    md = _markdown(tmp_path, "nome,cidade\nJoão,São Paulo\n".encode("latin-1"))
    assert "| João | São Paulo |" in md


def test_japones_em_shift_jis(tmp_path):
    dados = "名前,年齢,住所\r\n佐藤太郎,30,東京\r\n三木英子,25,大阪\r\n髙橋淳,35,名古屋\r\n".encode("cp932")
    assert "| 佐藤太郎 | 30 | 東京 |" in _markdown(tmp_path, dados)


def test_utf8_sai_igual_ao_do_markitdown(tmp_path):
    """Para UTF-8 nada muda: mesma saída do motor chamado direto no arquivo."""
    from markitdown import MarkItDown
    dados = '﻿a,b\n1,"x|y"\n\n2,"l1\nl2",extra\n3\nção,日本\n'.encode("utf-8")
    md = _markdown(tmp_path, dados)
    assert md == MarkItDown().convert(str(tmp_path / "d.csv")).text_content
