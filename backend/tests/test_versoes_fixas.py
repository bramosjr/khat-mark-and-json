"""As versões do build ficam fixas em constraints.txt, usado por quem instala."""
import re
from importlib.metadata import distribution
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.version import Version

import gera_licencas

BACKEND = Path(__file__).resolve().parent.parent
RAIZ = BACKEND.parent
RESTRICOES = BACKEND / "constraints.txt"


def _nome(texto: str) -> str:
    return re.sub(r"[-_.]+", "-", texto).lower()


def _linhas(arquivo: Path) -> list:
    return [linha.strip() for linha in arquivo.read_text(encoding="utf-8").splitlines()
            if linha.strip() and not linha.startswith("#")]


def _fixadas() -> dict:
    return {_nome(n): v for n, v in (linha.split("==") for linha in _linhas(RESTRICOES))}


def test_toda_linha_fixa_uma_versao_exata_sem_repetir():
    linhas = _linhas(RESTRICOES)
    assert [l for l in linhas if not re.fullmatch(r"[A-Za-z0-9._-]+==[A-Za-z0-9.+!]+", l)] == []
    assert len(_fixadas()) == len(linhas)


def test_dependencias_diretas_e_pyinstaller_estao_fixadas():
    diretas = [Requirement(l).name
               for arquivo in ("requirements.txt", "requirements-dev.txt")
               for l in _linhas(BACKEND / arquivo) if not l.startswith("-")]
    fixadas = _fixadas()
    assert [n for n in diretas + ["pyinstaller"] if _nome(n) not in fixadas] == []


def test_ambiente_tem_as_versoes_fixadas_inclusive_as_indiretas():
    fixadas = _fixadas()
    divergentes = []
    for dist in gera_licencas._dependencias_python(BACKEND / "requirements.txt"):
        nome = _nome(dist.metadata["Name"])
        if fixadas.get(nome) != dist.version:
            divergentes.append(f"{nome}: instalado {dist.version}, fixado {fixadas.get(nome)}")
    for nome in ("pyinstaller", "pytest", "xlwt"):
        if fixadas.get(nome) != distribution(nome).version:
            divergentes.append(f"{nome}: instalado {distribution(nome).version}")
    assert divergentes == []


@pytest.mark.parametrize("arquivo", ["backend/build_linux.sh", "backend/build_windows.sh", "README.md"])
def test_toda_instalacao_usa_o_arquivo_de_restricoes(arquivo):
    instalacoes = [l.strip() for l in (RAIZ / arquivo).read_text(encoding="utf-8").splitlines()
                   if "pip install" in l]
    assert instalacoes
    assert [l for l in instalacoes if "-c constraints.txt" not in l] == []


# Pisos de segurança (issue #12): abaixo destas versões há falhas conhecidas.
@pytest.mark.parametrize("nome, minima", [
    ("pillow", "13.0.0"), ("pyasn1", "0.6.5"), ("setuptools", "84.1.0"),
    ("soupsieve", "4.0"), ("urllib3", "2.8.0"),
])
def test_versao_fixada_nao_volta_a_uma_com_falha_conhecida(nome, minima):
    assert Version(_fixadas()[nome]) >= Version(minima)
