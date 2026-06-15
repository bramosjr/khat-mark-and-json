# MarkItDown GUI - Plan

Este plano descreve as tarefas e fluxos para a implementação da interface gráfica do MarkItDown como uma aplicação desktop multiplataforma, baseadas em issues lógicas.

## Fase 1: Fundação do Backend e Standalone
- [ ] **Task 1.1: Setup do Backend Python**
  - Inicializar ambiente virtual (`venv`).
  - Instalar dependências: `fastapi`, `uvicorn`, `markitdown`, `python-multipart`, `pyinstaller`.
  - Estruturar a pasta `backend/`.
- [ ] **Task 1.2: Criação da API de Conversão**
  - Criar endpoint `POST /api/convert` que integre com a biblioteca `markitdown`.
  - Configurar tratamento de exceções (arquivos não suportados, corrompidos).
- [ ] **Task 1.3: Empacotamento do Backend (PyInstaller)**
  - Configurar um script de build para gerar o executável do backend (ex: `backend.exe` ou binário linux) com PyInstaller.

## Fase 2: Fundação do Frontend e Design
- [ ] **Task 2.1: Inicialização do Vite + React**
  - Inicializar projeto (`npx create-vite-app@latest frontend --template react`).
  - Limpar boilerplate desnecessário e configurar para rodar localmente.
- [ ] **Task 2.2: Setup do Design System e CSS**
  - Configurar `index.css` com variáveis de Dark Mode, fontes modernas e keyframes de animação.

## Fase 3: Componentização e Integração Web
- [ ] **Task 3.1: Componentes da Interface**
  - Implementar o *Drag and Drop* com micro-interações.
  - Implementar o *Markdown Preview* com suporte a download/cópia.
- [ ] **Task 3.2: Conexão com o Backend**
  - O frontend deve localizar dinamicamente a porta onde o backend FastAPI está rodando e se comunicar via requisições `fetch`.

## Fase 4: Integração Desktop (Electron)
- [ ] **Task 4.1: Setup do Electron**
  - Inicializar o Electron na raiz do projeto (`main.js`, `preload.js`).
  - Configurar o Electron para inicializar/encerrar o executável gerado pelo PyInstaller (o backend) automaticamente quando o app abre/fecha.
- [ ] **Task 4.2: Conexão Electron <-> Frontend**
  - Fazer o Electron carregar os arquivos estáticos compilados do React (build do Vite).

## Fase 5: Compilação Multiplataforma (electron-builder)
- [ ] **Task 5.1: Configuração do electron-builder**
  - Adicionar e configurar o `electron-builder` no `package.json`.
  - Declarar os alvos de compilação: Windows (`nsis`), macOS (`dmg`), e Linux (`deb`, `rpm`, `AppImage`, `flatpak`).
  - Garantir que o executável do backend gerado pelo PyInstaller seja copiado como um "extraResource" ou "sidecar" dentro do pacote final.
- [ ] **Task 5.2: Testes de Build**
  - Gerar e validar os empacotamentos. Testar a funcionalidade completa em modo de produção (binário final).
