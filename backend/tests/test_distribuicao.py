"""Versão e licença declaradas de forma coerente em tudo o que é distribuído."""
import json
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
FRONT = RAIZ / "frontend"
VERSAO, LICENCA = "0.1.2", "AGPL-3.0-only"


def _texto(caminho):
    return (RAIZ / caminho).read_text(encoding="utf-8")


def _pacote():
    return json.loads(_texto("frontend/package.json"))


def test_versao_igual_nos_tres_lugares():
    lock = json.loads(_texto("frontend/package-lock.json"))
    primeira = re.search(r'<release version="([^"]+)"', _texto("frontend/build/khat-mark-and-json.metainfo.xml"))
    assert [_pacote()["version"], lock["version"], lock["packages"][""]["version"],
            primeira.group(1)] == [VERSAO] * 4


def test_pacotes_declaram_agpl():
    lock = json.loads(_texto("frontend/package-lock.json"))
    meta = _texto("frontend/build/khat-mark-and-json.metainfo.xml")
    assert _pacote()["license"] == lock["packages"][""]["license"] == LICENCA
    assert f"<project_license>{LICENCA}</project_license>" in meta
    assert LICENCA in _texto("frontend/build/copyright")


def test_codigo_do_projeto_continua_mit():
    assert _texto("LICENSE").startswith("MIT License")


def test_texto_da_agpl_e_aviso():
    agpl = _texto("licenses/AGPL-3.0.txt")
    assert "GNU AFFERO GENERAL PUBLIC LICENSE" in agpl and "13. Remote Network Interaction" in agpl
    aviso = _texto("NOTICE.md")
    for trecho in (LICENCA, "PyMuPDF", "MIT", "https://github.com/bramosjr/khat-mark-and-json"):
        assert trecho in aviso


@pytest.mark.parametrize("plataforma", ["linux", "win", "mac"])
def test_pacote_leva_licencas(plataforma):
    destinos = {r["to"] for r in _pacote()["build"][plataforma]["extraResources"]}
    assert {"licenses/LICENSE-MIT.txt", "licenses/AGPL-3.0.txt", "licenses/NOTICE.md",
            "licenses/LICENCAS-TERCEIROS.txt"} <= destinos


@pytest.mark.parametrize("script", ["build_linux.sh", "build_windows.sh"])
def test_build_gera_lista_de_licencas(script):
    assert "gera_licencas.py" in _texto(f"backend/{script}")


def test_lista_de_licencas_cobre_as_dependencias(tmp_path):
    import gera_licencas
    destino = tmp_path / "l.txt"
    gera_licencas.gerar(destino)
    texto = destino.read_text(encoding="utf-8")
    for nome in ("PyMuPDF", "markitdown", "mammoth", "pandas", "charset-normalizer",
                 "react", "lucide-react", "@fontsource-variable/outfit", "PyInstaller"):
        assert re.search(rf"^## {nome} ", texto, re.IGNORECASE | re.MULTILINE), nome
    assert "AFFERO" in texto and "pytest" not in texto.lower().split("## ")[0]
    assert "The Outfit Project Authors" in texto and "SIL OPEN FONT LICENSE" in texto
    assert not re.search(r"^## (pytest|xlwt) ", texto, re.IGNORECASE | re.MULTILINE)


@pytest.fixture(scope="module")
def secoes(tmp_path_factory):
    import gera_licencas
    destino = tmp_path_factory.mktemp("lic") / "l.txt"
    gera_licencas.gerar(destino)
    partes = re.split(r"(?m)^={70}\n", destino.read_text(encoding="utf-8"))[1:]
    return {p.split("\n", 1)[0][3:].rsplit(" ", 1)[0].lower(): p for p in partes}


def test_toda_secao_traz_texto(secoes):
    assert len(secoes) > 60
    assert [nome for nome, s in secoes.items() if "\n--- " not in s] == []


@pytest.mark.parametrize("nome,trecho", [
    ("markitdown", "Copyright (c) Microsoft Corporation"),
    ("magika", "Apache License"),
    ("flatbuffers", "Apache License"),
    ("odfpy", "Apache License"),
    ("pypdfium2", "pdfium.txt"),          # textos que o gerador ignorava
    ("pypdfium2", "freetype.txt"),
    ("python", "PYTHON SOFTWARE FOUNDATION LICENSE"),
    ("cobble", "não publica o texto da licença"),
])
def test_textos_que_faltavam(secoes, nome, trecho):
    assert trecho in secoes[nome]


def test_componente_sem_texto_interrompe_a_geracao(tmp_path, monkeypatch):
    import gera_licencas
    monkeypatch.setattr(gera_licencas, "TEXTOS_EXTERNOS", tmp_path / "vazio")
    with pytest.raises(gera_licencas.LicencaAusente, match="sem texto de licença para cobble"):
        gera_licencas.gerar(tmp_path / "l.txt")


def test_licenca_do_cobble_traz_a_declaracao_do_autor_sem_preencher_o_modelo():
    texto = _texto("licenses/terceiros/cobble-0.1.4.txt")
    assert "2-Clause BSD <http://opensource.org/licenses/BSD-2-Clause>" in texto
    assert "sem indicar a variante" not in texto
    # o modelo fica como a OSI o publica: ninguém preenche em nome do autor
    assert "Copyright <YEAR> <COPYRIGHT HOLDER>" in texto
    assert "Redistributions in binary form must reproduce" in texto
    assert "IN NO EVENT SHALL THE COPYRIGHT HOLDER" in " ".join(texto.split())
    assert "titular e o ano" in texto
