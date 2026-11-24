const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const {
  readAppUpdateState,
  setAppUpdateEnabled,
  isAppUpdateEnabled,
  parseLatestRelease,
  checkForAppUpdate,
  DEFAULT_RELEASES_URL,
} = require('./app-update-checker.cjs');

function makeTmpDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'khat-app-update-test-'));
}

const REPO_RELEASE_URL = 'https://github.com/bramosjr/khat-mark-and-json/releases/tag/v0.2.0';

test('readAppUpdateState retorna padrão (habilitado) quando o arquivo não existe', () => {
  const tmp = makeTmpDir();
  assert.deepEqual(readAppUpdateState(tmp), {
    enabled: true, lastCheckedAt: null, latestVersion: null, releaseUrl: null,
  });
});

test('readAppUpdateState tolera JSON corrompido', () => {
  const tmp = makeTmpDir();
  fs.writeFileSync(path.join(tmp, 'app-update-state.json'), '{nao é json');
  assert.equal(readAppUpdateState(tmp).enabled, true);
});

test('setAppUpdateEnabled persiste a preferência sem apagar o resto do estado', () => {
  const tmp = makeTmpDir();
  fs.writeFileSync(path.join(tmp, 'app-update-state.json'), JSON.stringify({
    enabled: true, lastCheckedAt: 5, latestVersion: '0.2.0', releaseUrl: REPO_RELEASE_URL,
  }));
  setAppUpdateEnabled(tmp, false);
  assert.equal(isAppUpdateEnabled(tmp), false);
  assert.equal(readAppUpdateState(tmp).latestVersion, '0.2.0');
  setAppUpdateEnabled(tmp, true);
  assert.equal(isAppUpdateEnabled(tmp), true);
});

test('parseLatestRelease extrai versão e url da resposta da API', () => {
  const r = parseLatestRelease({ tag_name: 'v0.2.0', html_url: REPO_RELEASE_URL });
  assert.deepEqual(r, { version: '0.2.0', url: REPO_RELEASE_URL });
});

test('parseLatestRelease ignora html_url fora do repositório do projeto', () => {
  const r = parseLatestRelease({ tag_name: 'v0.2.0', html_url: 'https://evil.example.com/x' });
  assert.equal(r.url, DEFAULT_RELEASES_URL);
});

test('parseLatestRelease rejeita resposta sem tag_name', () => {
  assert.throws(() => parseLatestRelease({}));
  assert.throws(() => parseLatestRelease(null));
});

test('checkForAppUpdate detecta versão nova e grava cache', async () => {
  const tmp = makeTmpDir();
  const result = await checkForAppUpdate({
    appVersion: '0.1.0',
    userDataPath: tmp,
    fetchFn: async () => ({ version: '0.2.0', url: REPO_RELEASE_URL }),
    now: 1000,
  });
  assert.deepEqual(result, {
    updateAvailable: true, latestVersion: '0.2.0', currentVersion: '0.1.0',
    releaseUrl: REPO_RELEASE_URL, enabled: true,
  });
  assert.equal(readAppUpdateState(tmp).lastCheckedAt, 1000);
});

test('checkForAppUpdate compara numericamente (0.10.0 > 0.9.0)', async () => {
  const tmp = makeTmpDir();
  const result = await checkForAppUpdate({
    appVersion: '0.9.0', userDataPath: tmp,
    fetchFn: async () => ({ version: '0.10.0', url: REPO_RELEASE_URL }), now: 1,
  });
  assert.equal(result.updateAvailable, true);
});

test('checkForAppUpdate não avisa quando já está na última versão', async () => {
  const tmp = makeTmpDir();
  const result = await checkForAppUpdate({
    appVersion: '0.2.0', userDataPath: tmp,
    fetchFn: async () => ({ version: '0.2.0', url: REPO_RELEASE_URL }), now: 1,
  });
  assert.equal(result.updateAvailable, false);
});

test('checkForAppUpdate respeita o opt-out: não chama a rede', async () => {
  const tmp = makeTmpDir();
  setAppUpdateEnabled(tmp, false);
  let calls = 0;
  const result = await checkForAppUpdate({
    appVersion: '0.1.0', userDataPath: tmp,
    fetchFn: async () => { calls += 1; return { version: '9.9.9', url: REPO_RELEASE_URL }; },
    now: 1,
  });
  assert.equal(calls, 0);
  assert.equal(result.updateAvailable, false);
  assert.equal(result.enabled, false);
});

test('checkForAppUpdate reusa cache dentro de 7 dias, sem chamar a rede', async () => {
  const tmp = makeTmpDir();
  fs.writeFileSync(path.join(tmp, 'app-update-state.json'), JSON.stringify({
    enabled: true, lastCheckedAt: 1000, latestVersion: '0.2.0', releaseUrl: REPO_RELEASE_URL,
  }));
  let calls = 0;
  const result = await checkForAppUpdate({
    appVersion: '0.1.0', userDataPath: tmp,
    fetchFn: async () => { calls += 1; return { version: '0.9.9', url: REPO_RELEASE_URL }; },
    now: 1000 + 60 * 1000,
  });
  assert.equal(calls, 0);
  assert.equal(result.latestVersion, '0.2.0');
  assert.equal(result.updateAvailable, true);
});

test('checkForAppUpdate rechecka após 7 dias', async () => {
  const tmp = makeTmpDir();
  fs.writeFileSync(path.join(tmp, 'app-update-state.json'), JSON.stringify({
    enabled: true, lastCheckedAt: 0, latestVersion: '0.2.0', releaseUrl: REPO_RELEASE_URL,
  }));
  let calls = 0;
  await checkForAppUpdate({
    appVersion: '0.1.0', userDataPath: tmp,
    fetchFn: async () => { calls += 1; return { version: '0.3.0', url: REPO_RELEASE_URL }; },
    now: 8 * 24 * 60 * 60 * 1000,
  });
  assert.equal(calls, 1);
});

test('checkForAppUpdate falha em silêncio quando a rede cai (sem gravar cache)', async () => {
  const tmp = makeTmpDir();
  const result = await checkForAppUpdate({
    appVersion: '0.1.0', userDataPath: tmp,
    fetchFn: async () => { throw new Error('ENOTFOUND'); }, now: 5,
  });
  assert.equal(result.updateAvailable, false);
  assert.equal(readAppUpdateState(tmp).lastCheckedAt, null);
});

test('checkForAppUpdate sem appVersion conhecida não avisa', async () => {
  const tmp = makeTmpDir();
  const result = await checkForAppUpdate({
    appVersion: null, userDataPath: tmp,
    fetchFn: async () => ({ version: '0.2.0', url: REPO_RELEASE_URL }), now: 1,
  });
  assert.equal(result.updateAvailable, false);
});
