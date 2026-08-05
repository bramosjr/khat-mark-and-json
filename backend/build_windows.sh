#!/bin/bash
set -e

echo "Iniciando compilação do Backend para Windows (usando Wine)..."

# Necessita que o python para Windows esteja instalado no Wine
# Exemplo genérico assumindo que 'wine python' invoca o Python do Windows.

wine python -m pip install -r requirements.txt
wine python -m pip install pyinstaller

if [ ! -f "gswin64c.exe" ]; then
    echo "Baixando Ghostscript portatil para Windows..."
    # Fazendo o download do instalador e extraindo o binário ou baixando de fonte confiável
    # Aqui usaremos um stub, na prática o usuário deve fornecer o gswin64c.exe na pasta.
    echo "POR FAVOR, garanta que o 'gswin64c.exe' está na pasta backend!"
fi

echo "Compilando com PyInstaller via Wine..."
WINEDLLOVERRIDES="ucrtbase=n,b" wine pyinstaller --name markitdown-backend \
            --onefile \
            --add-binary "gswin64c.exe;." \
            --add-binary "gsdll64.dll;." \
            --collect-all "magika" \
            --collect-all "markitdown" \
            --hidden-import "uvicorn" \
            --hidden-import "fastapi" \
            --hidden-import "pandas" \
            --hidden-import "odf" \
            --hidden-import "fitz" \
            --hidden-import "pdfplumber" \
            --hidden-import "camelot" \
            main.py

echo "Build Windows Finalizado! Executável gerado na pasta dist/"
