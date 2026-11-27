"""Camelot e Ghostscript fora do projeto; scripts de build consistentes."""
import re
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
RAIZ = BACKEND.parent

ARQUIVOS = [
    "backend/requirements.txt", "backend/build_linux.sh", "backend/build_windows.sh",
    "backend/build_version_info.py", "backend/main.py", "backend/core/mcp_server.py",
    "backend/core/offline_parsers.py", "backend/core/output_wrapper.py",
    "frontend/src/components/AboutModal.jsx", "README.md",
]


@pytest.mark.parametrize("arquivo", ARQUIVOS)
def test_sem_camelot_nem_ghostscript(arquivo):
    texto = (RAIZ / arquivo).read_text(encoding="utf-8")
    achados = re.findall(r"camelot|ghostscript|gswin|gsdll|\bgs\b", texto, re.IGNORECASE)
    assert achados == []


@pytest.mark.parametrize("script", ["build_linux.sh", "build_windows.sh"])
def test_script_gera_version_info_e_inclui_multipart(script):
    texto = (BACKEND / script).read_text(encoding="utf-8")
    assert "build_version_info.py" in texto
    assert re.search(r'--hidden-import "?multipart"?', texto)
    assert "rm -rf dist" not in texto  # um build não apaga o binário da outra plataforma


def test_linux_tem_um_unico_script():
    assert not (BACKEND / "build.sh").exists()
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    assert "build.sh" not in readme and "build_linux.sh" in readme


@pytest.mark.parametrize("script", ["build_linux.sh", "build_windows.sh"])
def test_executavel_nao_leva_o_readline(script):
    """O módulo readline traz a libreadline (GPL) e o app não o usa."""
    assert re.search(r'--exclude-module "?readline"? ', (BACKEND / script).read_text(encoding="utf-8"))


def test_readme_instala_o_frontend_antes_de_compilar_o_backend():
    """gera_licencas.py, chamado no fim do build, lê frontend/node_modules."""
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    secao = readme[readme.index("## Compilando para Produção"):readme.index("## Atualizando")]
    assert 0 <= secao.find("cd frontend && npm ci") < secao.find("./build_linux.sh")
