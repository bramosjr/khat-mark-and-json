const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const {
  readVersionInfo,
  readUpdateCache,
  writeUpdateCache,
  shouldCheck,
  checkForUpdate,
} = require('./update-checker.cjs');

function makeTmpDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'khat-update-test-'));
}

test('readVersionInfo retorna valores padrão quando o arquivo não existe', () => {
  const tmp = makeTmpDir();
  const info = readVersionInfo({ resourcesPath: tmp, isPackaged: true, appDir: tmp });
  assert.deepEqual(info, { app_version: null, markitdown_version: null, built_at: null, libraries: {} });
});

test('readVersionInfo lê version-info.json em produção', () => {
  const tmp = makeTmpDir();
  fs.writeFileSync(path.join(tmp, 'version-info.json'), JSON.stringify({
    app_version: '1.0.0', markitdown_version: '0.1.7', built_at: '2026-09-08T00:00:00Z',
  }));
  const info = readVersionInfo({ resourcesPath: tmp, isPackaged: true, appDir: tmp });
  assert.equal(info.markitdown_version, '0.1.7');
});

test('readUpdateCache/writeUpdateCache fazem round-trip', () => {
  const tmp = makeTmpDir();
  writeUpdateCache(tmp, { lastCheckedAt: 123, latestVersion: '0.2.0' });
  const cache = readUpdateCache(tmp);
  assert.deepEqual(cache, { lastCheckedAt: 123, latestVersion: '0.2.0' });
});

test('shouldCheck é true quando nunca checou', () => {
  assert.equal(shouldCheck({ lastCheckedAt: null }), true);
});

test('shouldCheck é false dentro de 7 dias', () => {
  const now = Date.now();
  assert.equal(shouldCheck({ lastCheckedAt: now - 1000 }, now), false);
});

test('shouldCheck é true após 7 dias', () => {
  const now = Date.now();
  const eightDaysAgo = now - 8 * 24 * 60 * 60 * 1000;
  assert.equal(shouldCheck({ lastCheckedAt: eightDaysAgo }, now), true);
});

test('checkForUpdate detecta atualização disponível usando fetchFn injetado', async () => {
  const resourcesTmp = makeTmpDir();
  const userDataTmp = makeTmpDir();
  fs.writeFileSync(path.join(resourcesTmp, 'version-info.json'), JSON.stringify({
    app_version: '1.0.0', markitdown_version: '0.1.7', built_at: '2026-09-08T00:00:00Z',
  }));
  const result = await checkForUpdate({
    resourcesPath: resourcesTmp,
    isPackaged: true,
    appDir: resourcesTmp,
    userDataPath: userDataTmp,
    fetchFn: async () => '0.2.0',
    now: Date.now(),
  });
  assert.deepEqual(result, { updateAvailable: true, latestVersion: '0.2.0', currentVersion: '0.1.7' });
});

test('checkForUpdate não marca atualização quando já está na última versão', async () => {
  const resourcesTmp = makeTmpDir();
  const userDataTmp = makeTmpDir();
  fs.writeFileSync(path.join(resourcesTmp, 'version-info.json'), JSON.stringify({
    app_version: '1.0.0', markitdown_version: '0.2.0', built_at: '2026-09-08T00:00:00Z',
  }));
  const result = await checkForUpdate({
    resourcesPath: resourcesTmp,
    isPackaged: true,
    appDir: resourcesTmp,
    userDataPath: userDataTmp,
    fetchFn: async () => '0.2.0',
    now: Date.now(),
  });
  assert.equal(result.updateAvailable, false);
});

test('checkForUpdate reusa cache dentro da janela de 7 dias, sem chamar fetchFn', async () => {
  const resourcesTmp = makeTmpDir();
  const userDataTmp = makeTmpDir();
  fs.writeFileSync(path.join(resourcesTmp, 'version-info.json'), JSON.stringify({
    app_version: '1.0.0', markitdown_version: '0.1.7', built_at: '2026-09-08T00:00:00Z',
  }));
  writeUpdateCache(userDataTmp, { lastCheckedAt: Date.now(), latestVersion: '0.2.0' });
  let calls = 0;
  const result = await checkForUpdate({
    resourcesPath: resourcesTmp,
    isPackaged: true,
    appDir: resourcesTmp,
    userDataPath: userDataTmp,
    fetchFn: async () => { calls += 1; return '0.9.9'; },
    now: Date.now(),
  });
  assert.equal(calls, 0);
  assert.equal(result.latestVersion, '0.2.0');
});
