#!/bin/bash
set -e

echo "Iniciando compilação do Backend para Linux..."

# Garante que o ambiente virtual existe
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller

echo "Compilando com PyInstaller..."
pyinstaller --name markitdown-backend \
            --onefile \
            --clean \
            --noconfirm \
            --collect-all "magika" \
            --collect-all "markitdown" \
            --collect-all "mammoth" \
            --collect-all "pptx" \
            --hidden-import "xlrd" \
            --hidden-import "uvicorn" \
            --hidden-import "fastapi" \
            --hidden-import "multipart" \
            --hidden-import "pandas" \
            --hidden-import "odf" \
            --hidden-import "fitz" \
            --hidden-import "pdfplumber" \
            main.py

echo "Gerando version-info.json..."
python build_version_info.py
python gera_licencas.py

echo "Build Linux Finalizado! Executável gerado na pasta dist/markitdown-backend"
