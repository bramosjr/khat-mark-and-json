import test from 'node:test';
import assert from 'node:assert/strict';
import { formatResult } from './formatResult.js';

test('o resultado em JSON é JSON puro, que um leitor aceita', () => {
  const dados = { source_type: 'document', content: '```js\nx\n```' };
  const texto = formatResult('json', { json_data: dados });
  assert.deepEqual(JSON.parse(texto), dados);
  assert.ok(texto.startsWith('{') && texto.endsWith('}'));
});

test('o JSON sai indentado com dois espaços', () => {
  assert.equal(formatResult('json', { json_data: { a: 1 } }), '{\n  "a": 1\n}');
});

test('o Markdown sai sem alteração, inclusive com blocos de código', () => {
  const markdown = '# t\n\n```json\n{}\n```';
  assert.equal(formatResult('md', { markdown }), markdown);
});
