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
