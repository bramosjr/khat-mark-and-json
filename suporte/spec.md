# MarkItDown GUI - Specification (Spec)

## Visão Geral
O objetivo deste projeto é criar uma interface gráfica de usuário (GUI) web/desktop elegante, moderna e altamente responsiva para o conversor [MarkItDown da Microsoft](https://github.com/microsoft/markitdown). O grande diferencial é que **a aplicação será multiplataforma**, podendo ser instalada de forma nativa e offline no Windows, macOS e distribuições Linux (suportando pacotes como `.deb`, `.rpm`, `.AppImage` e `flatpak`). 

Isso permitirá que os usuários convertam arquivos como PDF, Word, Excel, PPT, Imagens e Áudio em Markdown através de uma experiência unificada, onde quer que estejam.

## Objetivos Principais
- Prover uma zona de *Drag and Drop* (arrastar e soltar) intuitiva para upload rápido de arquivos.
- Exibir uma pré-visualização (*preview*) do texto Markdown gerado de imediato após a conversão.
- Atingir o mais alto nível de excelência em design visual ("Aesthetics over Generic"), focando numa experiência "Premium".
- Empacotamento para Desktop (Standalone) para múltiplos sistemas operacionais.

## Arquitetura (Proposta de Stack Tecnológica)
Para mesclar a interface web premium com as capacidades do Python e empacotar para desktop, utilizaremos o padrão **Electron + Python Sidecar**:
1. **Desktop Wrapper (Electron)**: Utilizaremos o Electron para criar a janela principal do aplicativo. Ele vai gerenciar o ciclo de vida do app e utilizar o `electron-builder` para gerar os binários em todas as plataformas (Windows, Mac, Linux deb/rpm/AppImage/flatpak).
2. **Backend (Processamento como Sidecar)**: API em Python utilizando **FastAPI** para integrar a biblioteca `markitdown`. Esse backend será empacotado em um executável autossuficiente via **PyInstaller** e rodará em background junto com a interface Electron.
3. **Frontend (Interface)**: Aplicação **React + Vite** construída do zero utilizando **Vanilla CSS**, rodando dentro da janela do Electron.
4. **Design System**: Paleta de cores moderna (Dark Mode com toques de Glassmorphism), tipografia com caráter e fortes micro-interações.

## Diretrizes e Requisitos de Design (Aesthetics)
- Rejeitar elementos genéricos. A interface deve ser "viva".
- **Micro-interações:** Animações CSS nas ações de soltar o arquivo, carregar (*loading state* customizado) e transições suaves entre estados da UI.
- Feedback em tempo real em todas as interações e de status de processamento da IA.
