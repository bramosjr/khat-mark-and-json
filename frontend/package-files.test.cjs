const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const pacote = require('./package.json');

const padroes = pacote.build.files || [];
const casa = (padrao, arquivo) => path.matchesGlob(arquivo, padrao);
// Mesma regra do electron-builder: o último padrão que casa decide.
const empacotado = (arquivo) => padroes.reduce((dentro, p) => (
  p.startsWith('!') ? dentro && !casa(p.slice(1), arquivo) : dentro || casa(p, arquivo)
), false);

function requisitados(arquivo, vistos = new Set()) {
  vistos.add(arquivo);
  const codigo = fs.readFileSync(path.join(__dirname, arquivo), 'utf-8');
  for (const [, alvo] of codigo.matchAll(/require\('\.\/([^']+\.cjs)'\)/g)) {
    if (!vistos.has(alvo)) requisitados(alvo, vistos);
  }
  return vistos;
}

test('tudo o que o app carrega entra no pacote', () => {
  const necessarios = [...requisitados('main.cjs'), 'preload.cjs', 'package.json',
    'public/icone.png', 'dist/index.html', 'dist/assets/index-abc.js'];
  assert.deepEqual(necessarios.filter((a) => !empacotado(a)), []);
});

test('fontes, testes e configuração de desenvolvimento ficam de fora', () => {
  const fora = ['src/App.jsx', 'src/utils/formatResult.test.mjs', 'cli-args.test.cjs',
    'app-update-checker.test.cjs', 'package-files.test.cjs', 'vite.config.js',
    'eslint.config.js', 'index.html', 'README.md', 'build/copyright'];
  assert.deepEqual(fora.filter(empacotado), []);
});
