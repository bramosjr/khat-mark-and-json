#!/bin/bash
# Script para empacotar o backend usando PyInstaller

# Garante que estamos usando o ambiente virtual local
source venv/bin/activate

# Limpa builds anteriores se existirem
rm -rf build/ dist/

echo "Iniciando empacotamento com PyInstaller..."
pyinstaller --name markitdown-backend \
            --onefile \
            --clean \
            --noconfirm \
            --hidden-import uvicorn \
            --hidden-import fastapi \
            --hidden-import markitdown \
            --hidden-import multipart \
            --collect-all magika \
            --collect-all markitdown \
            main.py

echo "Build do backend concluído. O executável está na pasta 'dist/'"
