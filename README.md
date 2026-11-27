# Khat Mark And Json

<p align="center">
  <img src="assets/screenshot.png" width="49%" alt="Tela Inicial do Aplicativo">
  <img src="assets/screenshot2.png" width="49%" alt="Aplicativo em Ação">
</p>

> "A principal palavra egípcia antiga para o corpo físico que abriga o espírito é **Khat** (também grafado como Kha). Este termo refere-se especificamente ao corpo material e mortal, sujeito à decomposição, que servia como receptáculo ou 'navio' terreno para as partes imortais da alma (como o Ba e o Ka). É por causa da importância do Khat como âncora para o espírito que os antigos egípcios desenvolveram rituais complexos de mumificação para preservá-lo."

Inspirado nessa mitologia, o **Khat Mark And Json** nasceu com um propósito exato: fornecer um "corpo" visual e acessível. 

Enquanto a robusta biblioteca original [MarkItDown da Microsoft](https://github.com/microsoft/markitdown) atua nos bastidores como o poderoso "espírito" do projeto — operando de forma invisível através de linhas de código e terminais de comando — este projeto é o seu **receptáculo terreno**. 

O **Khat** constrói uma interface gráfica (*GUI*) moderna que materializa esse motor em algo tátil e amigável. Ele abriga a incrível força de conversão para Markdown limpo e extração de dados estruturados em JSON dentro de um "corpo" visual elegante, permitindo que o imenso poder da ferramenta ganhe forma, se torne duradouro e seja operado por qualquer pessoa sem necessidade de conhecimento em programação.

## Recursos
- **Saída Dupla (Markdown e JSON)**: Escolha entre converter seus documentos para um formato de leitura limpo (Markdown) ou extrair todos os dados em um formato puramente estruturado (JSON), pronto para bancos de dados e APIs.
- **Plataformas**: a versão 0.1.2 é distribuída para **Linux x86_64**, em `.deb`, `.rpm`, `.pacman` e AppImage. O `.deb` foi instalado; o `.rpm` e o `.pacman` tiveram o conteúdo conferido, sem teste de instalação; o AppImage não foi executado. Não há pacotes para Windows ou macOS.
- **Design Premium**: Interface baseada em *Glassmorphism* limpa e intuitiva construída com React e Vite.
- **Backend Autônomo**: Processamento via FastAPI no Python, empacotado internamente (Sidecar) via PyInstaller.
- **Suporte a LLM (Inteligência Artificial)**: Basta inserir sua chave de API nas configurações para liberar leitura de imagens e diagramas avançados.
- **Suporte Estendido de Arquivos**: Além dos formatos suportados nativamente pelo motor original (PDF, DOCX, XLSX, PPTX, HTML, CSV e Imagens), o **Khat estende a biblioteca da Microsoft**, adicionando interceptadores exclusivos para dar suporte inédito a arquivos do LibreOffice/OpenDocument (`.ods` e `.odt`).

## Estrutura do Projeto
- `/backend`: API Python e scripts de compilação do sidecar (`build_linux.sh` e `build_windows.sh`; o de Windows não foi testado).
- `/frontend`: Aplicação Vite + React e orquestrador Electron (`main.cjs`).

## Como Rodar Localmente (Desenvolvimento)

### Pré-requisitos
- Node.js
- Python 3.12+ (exigido pelas versões fixadas em `backend/constraints.txt`)

### Setup Rápido
1. Ative o ambiente Python no backend e instale as dependências:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # ou venv\Scripts\activate no Windows
   pip install -r requirements.txt pyinstaller -c constraints.txt
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
   cd backend && ./build_linux.sh
   ```
   Para rodar os testes e conferir o executável gerado, instale antes as dependências de teste:
   ```bash
   cd backend && venv/bin/pip install -r requirements-dev.txt -c constraints.txt
   venv/bin/python verificar_binario.py
   ```
2. Empacote com o `electron-builder`:
   ```bash
   cd frontend && npm run electron:build
   ```
Os arquivos finais de instalação estarão dentro de `frontend/release/`.

No app instalado, `khat-mark-and-json --help` (ou `-h`) e `--version` respondem no terminal e encerram, sem abrir a janela (no Windows, esse comportamento não foi verificado). A conversão por linha de comando é feita pelo `markitdown-backend`, descrito abaixo.

## Atualizando as versões das dependências
O `backend/requirements.txt` lista as dependências diretas; o `backend/constraints.txt` fixa a versão de cada pacote, direto ou indireto. Sem ele, uma instalação nova recebe versões não testadas, que já quebraram a conversão de `.docx`. As versões foram testadas no Linux; pacotes que só existem no Windows não estão fixados. Versões fixas não recebem correções de segurança sozinhas: revise-as antes de cada versão do app.

1. No `constraints.txt`, mude a versão do pacote. Ao adicionar uma dependência, inclua-a no `requirements.txt` e depois fixe no `constraints.txt` as versões que o `pip freeze` mostrar para ela e para as que ela trouxer.
2. Instale em um ambiente novo, para não perder o anterior, e rode os testes (os da lista de licenças exigem o `npm install` do `frontend` já feito):
   ```bash
   cd backend && python -m venv venv-teste
   venv-teste/bin/pip install -r requirements-dev.txt -c constraints.txt
   venv-teste/bin/pip install pyinstaller -c constraints.txt
   venv-teste/bin/python -m pytest
   ```
   Se o `pip` apontar conflito, ajuste as versões relacionadas. Se os testes de licença falharem, obtenha o texto da licença da nova versão na fonte oficial e salve em `licenses/terceiros/`.
3. Compare as saídas de conversão com as da versão anterior, compile e rode o `verificar_binario.py`. Os testes sozinhos não garantem que as saídas sejam iguais.

## Automação por agentes de IA (CLI e servidor MCP)

O mesmo binário do backend (`markitdown-backend`; em desenvolvimento, `python backend/main.py`) funciona como CLI e como servidor MCP quando recebe argumentos. **Sem argumentos**, sobe o servidor HTTP usado pela interface gráfica. Tudo é 100% offline e headless: não abre janelas, não usa rede nem LLM.

### CLI

```bash
markitdown-backend convert ARQUIVO [--formato md|json] [--saida CAMINHO] [--sobrescrever] [--max-chars N] [--dry-run] [--json]
markitdown-backend describe        # (ou --schema) lista comandos, ferramentas MCP e códigos de saída, em JSON
```

- Sem `--saida`, o conteúdo vai para o stdout. Markdown acima de `--max-chars` (padrão 200000) é truncado, com aviso no stderr; JSON acima desse limite exige `--saida`.
- `--saida` recusa sobrescrever um arquivo existente, salvo com `--sobrescrever`.
- `--dry-run` valida tudo (caminhos, extensão, tamanho, confinamento, dependências do conversor) sem converter nem gravar.
- Com `--json`, a saída e os erros são JSON: `{"erro": "...", "codigo": "..."}`.
- Extensões aceitas: `.pdf .docx .pptx .xlsx .xls .csv .ods .odt .html .htm .xml .json .txt .md .epub .msg` (`.zip` fica de fora por segurança). Limite de entrada: 50 MB (`--max-input-mb`).
- CSV, em Markdown e em JSON, aceita UTF-8, UTF-16 com marca inicial e Windows-1252/Latin-1; outras codificações dependem de detecção automática. Em JSON, se alguma linha tiver mais campos que o cabeçalho, as colunas extras entram como `Unnamed: N`.

**Códigos de saída:** `0` sucesso · `1` erro de negócio (campo `codigo`: `ENTRADA_INVALIDA`, `ARQUIVO_NAO_ENCONTRADO`, `EXTENSAO_NAO_SUPORTADA`, `ARQUIVO_GRANDE`, `CAMINHO_RECUSADO`, `SAIDA_EXISTE`, `CONTEUDO_GRANDE`, `CONVERSAO_FALHOU`, `ERRO_DE_ESCRITA`, `DEPENDENCIA_AUSENTE`) · `2` uso incorreto ou argumento inválido.

### Servidor MCP (stdio, JSON-RPC 2.0)

```bash
markitdown-backend mcp [--automation-read-root DIR] [--automation-write-root DIR] [--max-input-mb N]
```

Métodos: `initialize` (negocia `2025-06-18`, `2025-03-26` e `2024-11-05`), `ping`, `tools/list` e `tools/call`. Ferramentas:

- `inspecionar`: versões, extensões, modo, confinamento e limites (somente leitura).
- `executar`: `{arquivo, formato?, saida?, max_chars?, sobrescrever?, dry_run?}`, com a mesma semântica da CLI.

Erros de domínio voltam como resultado com `isError: true`; JSON inválido e método inexistente são erros de protocolo (`-32700`, `-32601`). O stdout carrega só o protocolo; qualquer ruído de bibliotecas e subprocessos é desviado para o stderr.

**Confinamento (fail-closed):** sem nenhuma raiz, não há confinamento. Com qualquer raiz, cada direção precisa da sua: ler exige `--automation-read-root` e gravar exige `--automation-write-root`. Uma flag `--automation-*` desconhecida, sem valor, ou qualquer argumento solto aborta com código `2`. O modo ponte `--connect` não é suportado (somente headless) e também retorna `2`.

Registro num cliente MCP (o app **não** faz isso por você):

```json
{ "mcpServers": { "khat-mark-and-json": {
  "command": "/caminho/para/markitdown-backend",
  "args": ["mcp", "--automation-read-root", "/caminho/dos/documentos", "--automation-write-root", "/caminho/das/saidas"]
} } }
```

## Licença e Créditos
Este projeto utiliza e funciona como uma interface gráfica para a biblioteca de código aberto `markitdown` criada pela Microsoft, distribuída sob a Licença MIT. 
Todo o código original de interface (GUI) e infraestrutura presente neste repositório também pode ser utilizado sob a Licença MIT.

---

## Licença
O código deste projeto é **MIT** ([LICENSE](LICENSE)). Os **pacotes e executáveis** incluem o PyMuPDF (AGPL) e, como um todo, são distribuídos sob **AGPL-3.0-only** ([texto](licenses/AGPL-3.0.txt)). Detalhes e licenças de terceiros em [NOTICE.md](NOTICE.md).

## ☕ Apoie o Projeto (Doações)
Este projeto é desenvolvido e mantido de forma totalmente independente e de código aberto. Se o **Khat Mark And Json** economizou seu tempo e otimizou seu fluxo de trabalho, considere apoiar o desenvolvimento contínuo fazendo uma doação via **Pix**!

**Chave Pix (Aleatória):**
`0d323a66-4090-4e03-aa6d-889abfac5ee7`

Qualquer valor é imensamente agradecido e ajuda a manter ferramentas livres e gratuitas vivas! ❤️
