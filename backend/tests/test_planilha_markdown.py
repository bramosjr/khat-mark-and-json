"""Markdown de planilha não mostra NaN/NaT nas células vazias (issue #3)."""
import datetime

import pytest

from core.automation import Automation

TEXTO = "tem NaN no meio"


def _xlsx_ou_ods(motor):
    def gerar(p):
        import pandas as pd
        pd.DataFrame({
            "a": [None, "x"], "b": [TEXTO, None],
            "data": [datetime.datetime(2026, 1, 1), None],
        }).to_excel(p, index=False, engine=motor)
    return gerar


def _xls(p):
    import xlwt
    livro = xlwt.Workbook()
    aba = livro.add_sheet("Plan1")
    for coluna, nome in enumerate(["a", "b"]):
        aba.write(0, coluna, nome)
    aba.write(1, 1, TEXTO)
    aba.write(2, 0, "x")
    livro.save(str(p))


@pytest.mark.parametrize("extensao,gerar", [
    (".xlsx", _xlsx_ou_ods("openpyxl")), (".ods", _xlsx_ou_ods("odf")), (".xls", _xls),
])
def test_celulas_vazias_ficam_vazias(tmp_path, extensao, gerar):
    origem = tmp_path / f"p{extensao}"
    gerar(origem)

    md = Automation().executar(str(origem))["conteudo"]

    celulas = [c.strip() for linha in md.splitlines() if linha.startswith("|")
               for c in linha.split("|")]
    assert "NaN" not in celulas and "NaT" not in celulas
    assert TEXTO in celulas and "x" in celulas
    assert len({linha.count("|") for linha in md.splitlines() if linha.startswith("|")}) == 1


def test_csv_preserva_o_texto_nan(tmp_path):
    origem = tmp_path / "p.csv"
    origem.write_text("a,b\nNaN,1\n")
    assert "| NaN | 1 |" in Automation().executar(str(origem))["conteudo"]
