// O Electron vai dentro do pacote: não pode voltar a uma versão com falha conhecida (issue #12).
const test = require('node:test');
const assert = require('node:assert/strict');
const pacote = require('./package.json');
const lock = require('./package-lock.json');
const { isNewerVersion } = require('./version-compare.cjs');

const MINIMA = '43.8.13';

test('o Electron declarado e o do lock não são anteriores ao piso de segurança', () => {
  const declarada = pacote.devDependencies.electron.replace(/^[\^~]/, '');
  const travada = lock.packages['node_modules/electron'].version;
  assert.deepEqual([declarada, travada].filter((v) => isNewerVersion(MINIMA, v)), []);
});

// O extrator que instala o binário do Electron: a 1.0.9 e a 1.0.10 terminam com
// instrução ilegal em CPUs sem BMI2 (ex.: AMD FX); a 1.0.5 e anteriores não têm a
// correção de segurança da 1.0.6. Rever quando sair uma versão corrigida.
test('o extrator do Electron fica fixado numa versão que roda sem BMI2 e já corrigida', () => {
  const extrator = '@electron-internal/extract-zip';
  assert.equal(pacote.overrides?.[extrator], '1.0.8');
  const instaladas = Object.entries(lock.packages)
    .filter(([caminho]) => caminho.endsWith(`node_modules/${extrator}`))
    .map(([, dados]) => dados.version);
  assert.deepEqual(instaladas, ['1.0.8']);
});
