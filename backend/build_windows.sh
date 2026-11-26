#!/bin/bash
set -e

echo "Iniciando compilação do Backend para Windows (usando Wine)..."

# Necessita que o python para Windows esteja instalado no Wine
# Exemplo genérico assumindo que 'wine python' invoca o Python do Windows.

wine python -m pip install -r requirements.txt
wine python -m pip install pyinstaller

echo "Compilando com PyInstaller via Wine..."
WINEDLLOVERRIDES="ucrtbase=n,b" wine pyinstaller --name markitdown-backend \
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
wine python build_version_info.py

echo "Build Windows Finalizado! Executável gerado na pasta dist/"
