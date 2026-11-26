const test = require('node:test');
const assert = require('node:assert/strict');
const { cliResponse } = require('./cli-args.cjs');

for (const flag of ['--help', '-h']) {
  test(`${flag} devolve a ajuda com a versão e a CLI do backend`, () => {
    const texto = cliResponse([flag], '1.2.3');
    assert.match(texto, /^Khat Mark And Json 1\.2\.3\n/);
    assert.match(texto, /khat-mark-and-json \[--help \| -h \| --version\]/);
    assert.match(texto, /markitdown-backend/);
    assert.ok(texto.endsWith('\n'));
  });
}

test('--version devolve só a versão', () => {
  assert.equal(cliResponse(['--version'], '1.2.3'), '1.2.3\n');
});

test('acha a opção entre os argumentos do Electron', () => {
  assert.equal(cliResponse(['.', '--no-sandbox', '--version'], '1.2.3'), '1.2.3\n');
});

test('com --help e --version juntos, a ajuda prevalece', () => {
  assert.match(cliResponse(['--version', '--help'], '1.2.3'), /Uso:/);
});

for (const args of [[], ['.'], ['--no-sandbox'], ['--helpx'], ['--version=2'], ['-v'], ['/tmp/--help.pdf'], ['--', '--help']]) {
  test(`abre a interface com ${JSON.stringify(args)}`, () => {
    assert.equal(cliResponse(args, '1.2.3'), null);
  });
}
