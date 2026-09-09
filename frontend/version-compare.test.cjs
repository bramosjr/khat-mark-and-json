const test = require('node:test');
const assert = require('node:assert/strict');
const { isNewerVersion } = require('./version-compare.cjs');

test('detecta versão maior', () => {
  assert.equal(isNewerVersion('0.2.0', '0.1.7'), true);
});

test('detecta versão igual como não-nova', () => {
  assert.equal(isNewerVersion('0.1.7', '0.1.7'), false);
});

test('detecta versão menor como não-nova', () => {
  assert.equal(isNewerVersion('0.1.0', '0.1.7'), false);
});

test('lida com diferentes números de segmentos', () => {
  assert.equal(isNewerVersion('0.2', '0.1.7'), true);
});

test('retorna false para entradas vazias', () => {
  assert.equal(isNewerVersion(null, '0.1.7'), false);
  assert.equal(isNewerVersion('0.2.0', null), false);
});
