"""Conversão de .msg (issue #3), com uma amostra versionada.

É a única amostra em arquivo: não há como gerar um .msg em tempo de teste.
Origem e licença em tests/fixtures/LEIAME.md.
"""
import io
import json
import re
from pathlib import Path

import pytest

import cli

AMOSTRA = Path(__file__).parent / "fixtures" / "outlook.msg"


@pytest.mark.parametrize("formato", ["md", "json"])
def test_msg_converte_pela_cli(formato):
    saida, erro = io.StringIO(), io.StringIO()

    codigo = cli.main(["convert", str(AMOSTRA), "--formato", formato, "--json"],
                      stdin=io.StringIO(""), stdout=saida, stderr=erro)

    assert codigo == 0, saida.getvalue()
    conteudo = json.dumps(json.loads(saida.getvalue())["conteudo"], ensure_ascii=False)
    # o cabeçalho montado prova que o leitor de Outlook rodou, não um texto bruto
    for trecho in ("# Email Message", "**From:** test.sender@example.com",
                   "**Subject:** Test Email Message", "This is the body of the test email message"):
        assert trecho in conteudo


def test_amostra_so_tem_enderecos_de_exemplo():
    """O arquivo original trazia dados pessoais nos metadados; a cópia não pode."""
    bruto = AMOSTRA.read_bytes()
    textos = (bruto.decode("latin-1"), bruto.decode("utf-16-le", "ignore"),
              bruto[1:].decode("utf-16-le", "ignore"))
    dominios = {d.lower() for t in textos
                for d in re.findall(r"[A-Za-z0-9._+=-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)", t)}
    assert dominios == {"example.com"}
