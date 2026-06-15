# Khat

> "A principal palavra egípcia antiga para o corpo físico que abriga o espírito é **Khat** (também grafado como Kha). Este termo refere-se especificamente ao corpo material e mortal, sujeito à decomposição, que servia como receptáculo ou 'navio' terreno para as partes imortais da alma (como o Ba e o Ka). É por causa da importância do Khat como âncora para o espírito que os antigos egípcios desenvolveram rituais complexos de mumificação para preservá-lo."

![Screenshot do Aplicativo](assets/screenshot.png)

Uma interface gráfica moderna e elegante (Khat) que serve como corpo e receptáculo para o utilitário [MarkItDown da Microsoft](https://github.com/microsoft/markitdown) (o espírito/motor).

Converta arquivos como PDF, Word, Excel, PPT, Áudio e Imagens para Markdown instantaneamente, sem precisar usar a linha de comando. Suporta integração nativa com modelos de IA (via OpenAI) para a transcrição rica de imagens complexas.

## Recursos
- **Multi-plataforma**: Construído com Electron, rodando nativamente no Windows, macOS e Linux (.deb, .rpm, .AppImage, flatpak).
- **Design Premium**: Interface baseada em *Glassmorphism* limpa e intuitiva construída com React e Vite.
- **Backend Autônomo**: Processamento via FastAPI no Python, empacotado internamente (Sidecar) via PyInstaller.
- **Suporte a LLM (Inteligência Artificial)**: Basta inserir sua chave de API nas configurações para liberar leitura de imagens e diagramas avançados.

## Estrutura do Projeto
- `/backend`: API Python e script de compilação do sidecar (`build.sh`).
- `/frontend`: Aplicação Vite + React e orquestrador Electron (`main.cjs`).
- `/suporte`: Documentações e planejamento do projeto.

## Como Rodar Localmente (Desenvolvimento)

### Pré-requisitos
- Node.js
- Python 3.10+

### Setup Rápido
1. Ative o ambiente Python no backend e instale as dependências:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # ou venv\Scripts\activate no Windows
   pip install "markitdown[all]" fastapi uvicorn python-multipart pyinstaller openai
   ```
2. Inicie o Electron no modo Dev:
   ```bash
   cd frontend
   npm install
   npm run electron:dev
   ```

## Compilando para Produção (Build)
Para gerar os instaladores e binários nativos de distribuição:
1. Compile o backend em um único executável:
   ```bash
   cd backend && ./build.sh
   ```
2. Empacote com o `electron-builder`:
   ```bash
   cd frontend && npm run electron:build
   ```
Os arquivos finais de instalação estarão dentro de `frontend/release/`.

## Licença e Créditos
Este projeto utiliza e funciona como uma interface gráfica para a biblioteca de código aberto `markitdown` criada pela Microsoft, distribuída sob a Licença MIT. 
Todo o código original de interface (GUI) e infraestrutura presente neste repositório também pode ser utilizado sob a Licença MIT.
