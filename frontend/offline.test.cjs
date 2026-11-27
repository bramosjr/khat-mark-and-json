// A interface não pode buscar nada fora do computador ao abrir.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const pacote = require('./package.json');

const ler = (arquivo) => fs.readFileSync(path.join(__dirname, arquivo), 'utf-8');
const FONTE = '@fontsource-variable/outfit';
// O que o navegador carrega sozinho: <link>, src=, url() e @import com endereço externo.
const CARGA_EXTERNA = /<link\b[^>]*href=["'](?:https?:)?\/\/|\bsrc=["'{\s]*(?:https?:)?\/\/|url\(\s*["']?(?:https?:)?\/\/|@import\s+(?:url\()?\s*["']?(?:https?:)?\/\/|\bimport\s+["'](?:https?:)?\/\//i;

const arquivos = ['index.html', ...fs.readdirSync(path.join(__dirname, 'src'), { recursive: true })
  .filter((a) => /\.(css|jsx?|mjs)$/.test(a)).map((a) => path.join('src', a))];

test('index.html e o código da interface não carregam recurso externo', () => {
  assert.deepEqual(arquivos.filter((a) => CARGA_EXTERNA.test(ler(a))), []);
});

test('a fonte Outfit vem de dependência com versão exata, importada pela interface', () => {
  assert.match(pacote.dependencies[FONTE] || '', /^\d+\.\d+\.\d+$/);
  assert.ok(ler('src/main.jsx').includes(`import '${FONTE}'`));
  assert.match(ler('src/index.css'), /font-family:\s*'Outfit Variable'/);
});

test('o corretor ortográfico fica desligado, para não baixar dicionários', () => {
  const janela = ler('main.cjs').match(/webPreferences:\s*\{[^}]*\}/)[0];
  assert.match(janela, /spellcheck:\s*false/);
});

// Observado no Electron 41: só spellcheck: false (ou desabilitar na sessão) não
// impede o download. É preciso esvaziar a lista de idiomas antes de abrir a janela.
test('a sessão fica sem idiomas de corretor antes de a janela abrir', () => {
  const principal = ler('main.cjs');
  const esvazia = principal.indexOf('session.defaultSession.setSpellCheckerLanguages([])');
  assert.ok(esvazia > 0 && esvazia < principal.indexOf('    createWindow();'));
});
