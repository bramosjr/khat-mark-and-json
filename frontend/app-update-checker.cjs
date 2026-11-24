// Aviso de nova versão do PRÓPRIO app (GitHub Releases). Só notifica: nunca baixa
// nem instala nada. Best-effort: qualquer falha de rede é silenciosa.
// Preferência do usuário (opt-out) e cache ficam em app-update-state.json no userData.
const fs = require('fs');
const path = require('path');
const https = require('https');
const { isNewerVersion } = require('./version-compare.cjs');

const STATE_FILE_NAME = 'app-update-state.json';
const CHECK_INTERVAL_MS = 7 * 24 * 60 * 60 * 1000; // 7 dias
const REQUEST_TIMEOUT_MS = 3000;
const REPO_SLUG = 'bramosjr/khat-mark-and-json';
const LATEST_RELEASE_API_URL = `https://api.github.com/repos/${REPO_SLUG}/releases/latest`;
const REPO_URL_PREFIX = `https://github.com/${REPO_SLUG}/`;
const DEFAULT_RELEASES_URL = `${REPO_URL_PREFIX}releases`;

const DEFAULT_STATE = Object.freeze({
  enabled: true, lastCheckedAt: null, latestVersion: null, releaseUrl: null,
});

function readAppUpdateState(userDataPath) {
  try {
    const raw = fs.readFileSync(path.join(userDataPath, STATE_FILE_NAME), 'utf-8');
    const parsed = JSON.parse(raw);
    if (parsed === null || typeof parsed !== 'object') return { ...DEFAULT_STATE };
    return {
      enabled: parsed.enabled !== false,
      lastCheckedAt: typeof parsed.lastCheckedAt === 'number' ? parsed.lastCheckedAt : null,
      latestVersion: typeof parsed.latestVersion === 'string' ? parsed.latestVersion : null,
      releaseUrl: typeof parsed.releaseUrl === 'string' ? parsed.releaseUrl : null,
    };
  } catch (err) {
    return { ...DEFAULT_STATE };
  }
}

function writeAppUpdateState(userDataPath, state) {
  fs.writeFileSync(path.join(userDataPath, STATE_FILE_NAME), JSON.stringify(state, null, 2));
}

function isAppUpdateEnabled(userDataPath) {
  return readAppUpdateState(userDataPath).enabled;
}

function setAppUpdateEnabled(userDataPath, enabled) {
  writeAppUpdateState(userDataPath, { ...readAppUpdateState(userDataPath), enabled: Boolean(enabled) });
}

function shouldCheck(state, now = Date.now()) {
  if (!state.lastCheckedAt) return true;
  return now - state.lastCheckedAt >= CHECK_INTERVAL_MS;
}

// Valida a resposta da API. A URL só é aceita se apontar para o repositório do projeto;
// qualquer outra cai no link padrão de releases (nunca abrimos URL arbitrária vinda da rede).
function parseLatestRelease(data) {
  if (!data || typeof data.tag_name !== 'string' || !data.tag_name.trim()) {
    throw new Error('Resposta de release inválida');
  }
  const version = data.tag_name.trim().replace(/^v/i, '');
  const url = typeof data.html_url === 'string' && data.html_url.startsWith(REPO_URL_PREFIX)
    ? data.html_url
    : DEFAULT_RELEASES_URL;
  return { version, url };
}

function fetchLatestAppRelease() {
  return new Promise((resolve, reject) => {
    const req = https.get(
      LATEST_RELEASE_API_URL,
      { headers: { 'User-Agent': 'khat-update-checker', Accept: 'application/vnd.github+json' } },
      (res) => {
        if (res.statusCode !== 200) {
          res.resume();
          reject(new Error(`GitHub respondeu ${res.statusCode}`));
          return;
        }
        let body = '';
        res.setEncoding('utf-8');
        res.on('data', (chunk) => { body += chunk; });
        res.on('end', () => {
          try {
            resolve(parseLatestRelease(JSON.parse(body)));
          } catch (err) {
            reject(err);
          }
        });
      },
    );
    req.on('error', reject);
    req.setTimeout(REQUEST_TIMEOUT_MS, () => req.destroy(new Error('Timeout ao consultar o GitHub')));
  });
}

async function checkForAppUpdate({
  appVersion, userDataPath, fetchFn = fetchLatestAppRelease, now = Date.now(),
}) {
  let state = readAppUpdateState(userDataPath);
  const build = () => ({
    updateAvailable: state.enabled && isNewerVersion(state.latestVersion, appVersion),
    latestVersion: state.latestVersion,
    currentVersion: appVersion || null,
    releaseUrl: state.releaseUrl || DEFAULT_RELEASES_URL,
    enabled: state.enabled,
  });

  if (!state.enabled || !appVersion) return build();

  if (shouldCheck(state, now)) {
    try {
      const { version, url } = await fetchFn();
      state = { ...state, lastCheckedAt: now, latestVersion: version, releaseUrl: url };
      writeAppUpdateState(userDataPath, state);
    } catch (err) {
      // Falha silenciosa (sem internet, rate limit...). Tenta de novo na próxima abertura.
    }
  }
  return build();
}

module.exports = {
  readAppUpdateState,
  isAppUpdateEnabled,
  setAppUpdateEnabled,
  parseLatestRelease,
  fetchLatestAppRelease,
  checkForAppUpdate,
  DEFAULT_RELEASES_URL,
  CHECK_INTERVAL_MS,
};
