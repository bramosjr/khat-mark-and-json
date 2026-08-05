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

# Como o Camelot exige o Ghostscript (gs), vamos assumir que o binário 'gs' portátil 
# será baixado ou copiado para a pasta atual antes do build.
# Baixando um binário estático do Ghostscript para Linux (caso não exista)
if [ ! -f "gs" ]; then
    echo "Aviso: Binário estático do Ghostscript não encontrado na pasta."
    echo "Criando um arquivo 'gs' provisório (stub) para destravar a compilação do PyInstaller."
    echo "IMPORTANTE: Antes de empacotar para o usuário final, baixe o executável estático real do Ghostscript e coloque-o aqui como 'gs'."
    touch gs
    chmod +x gs
fi

echo "Compilando com PyInstaller..."
pyinstaller --name markitdown-backend \
            --onefile \
            --add-binary "gs:." \
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

echo "Build Linux Finalizado! Executável gerado na pasta dist/markitdown-backend"
