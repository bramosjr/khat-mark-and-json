"""Cada extensão aceita pela CLI precisa converter de verdade (issue #3).

As amostras são geradas em tempo de teste; nenhum binário é versionado.
.msg fica de fora: não há como gerar uma amostra sem ferramenta externa.
"""
import io
import json
import zipfile

import pytest

import cli
from core.automation import SUPPORTED_EXTENSIONS

MARCA = "KhatAmostra"


def _zip(caminho, partes):
    with zipfile.ZipFile(caminho, "w") as z:
        for nome, conteudo in partes.items():
            z.writestr(nome, conteudo)


def _docx(p):
    _zip(p, {
        "[Content_Types].xml":
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType='
            '"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
        "_rels/.rels":
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
            'relationships/officeDocument" Target="word/document.xml"/></Relationships>',
        "word/document.xml":
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f'<w:body><w:p><w:r><w:t>{MARCA}</w:t></w:r></w:p></w:body></w:document>',
    })


def _pptx(p):
    from pptx import Presentation
    apresentacao = Presentation()
    slide = apresentacao.slides.add_slide(apresentacao.slide_layouts[0])
    slide.shapes.title.text = MARCA
    apresentacao.save(str(p))


def _xlsx(p):
    import pandas as pd
    pd.DataFrame({"nome": [MARCA]}).to_excel(p, index=False, engine="openpyxl")


def _xls(p):
    import xlwt
    livro = xlwt.Workbook()
    aba = livro.add_sheet("Plan1")
    aba.write(0, 0, "nome")
    aba.write(1, 0, MARCA)
    livro.save(str(p))


def _ods(p):
    import pandas as pd
    pd.DataFrame({"nome": [MARCA]}).to_excel(p, index=False, engine="odf")


def _odt(p):
    from odf.opendocument import OpenDocumentText
    from odf.text import P
    doc = OpenDocumentText()
    doc.text.addElement(P(text=MARCA))
    doc.save(str(p))


def _pdf(p):
    import fitz
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), MARCA)
    doc.save(str(p))
    doc.close()


def _epub(p):
    _zip(p, {
        "mimetype": "application/epub+zip",
        "META-INF/container.xml":
            '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
            '<rootfiles><rootfile full-path="content.opf" '
            'media-type="application/oebps-package+xml"/></rootfiles></container>',
        "content.opf":
            '<package xmlns="http://www.idpf.org/2007/opf" version="2.0">'
            '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>t</dc:title></metadata>'
            '<manifest><item id="c" href="c.xhtml" media-type="application/xhtml+xml"/></manifest>'
            '<spine><itemref idref="c"/></spine></package>',
        "c.xhtml": f'<html xmlns="http://www.w3.org/1999/xhtml"><body><p>{MARCA}</p></body></html>',
    })


def _texto(modelo):
    return lambda p: p.write_text(modelo.format(m=MARCA), encoding="utf-8")


AMOSTRAS = {
    ".pdf": _pdf, ".docx": _docx, ".pptx": _pptx, ".xlsx": _xlsx, ".xls": _xls,
    ".ods": _ods, ".odt": _odt, ".epub": _epub,
    ".csv": _texto("nome\n{m}\n"),
    ".html": _texto("<html><body><p>{m}</p></body></html>"),
    ".htm": _texto("<html><body><p>{m}</p></body></html>"),
    ".xml": _texto("<a>{m}</a>"),
    ".json": _texto('{{"a": "{m}"}}'),
    ".txt": _texto("{m}\n"),
    ".md": _texto("# {m}\n"),
}


def test_toda_extensao_aceita_tem_amostra():
    assert set(SUPPORTED_EXTENSIONS) - set(AMOSTRAS) == {".msg"}


@pytest.mark.parametrize("formato", ["md", "json"])
@pytest.mark.parametrize("extensao", sorted(AMOSTRAS))
def test_extensao_converte_pela_cli(tmp_path, extensao, formato):
    origem = tmp_path / f"amostra{extensao}"
    AMOSTRAS[extensao](origem)
    saida, erro = io.StringIO(), io.StringIO()

    codigo = cli.main(["convert", str(origem), "--formato", formato, "--json"],
                      stdin=io.StringIO(""), stdout=saida, stderr=erro)

    assert codigo == 0, saida.getvalue()
    envelope = json.loads(saida.getvalue())
    assert MARCA in json.dumps(envelope["conteudo"], ensure_ascii=False)
