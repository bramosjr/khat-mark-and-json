const fs = require('fs');
const path = require('path');
const https = require('https');
const { isNewerVersion } = require('./version-compare.cjs');

const CACHE_FILE_NAME = 'dep-update-cache.json';
const CHECK_INTERVAL_MS = 7 * 24 * 60 * 60 * 1000; // 1 semana
const PYPI_URL = 'https://pypi.org/pypi/markitdown/json';

function readVersionInfo({ resourcesPath, isPackaged, appDir }) {
  const filePath = isPackaged
    ? path.join(resourcesPath, 'version-info.json')
    : path.join(appDir, '..', 'backend', 'dist', 'version-info.json');
  try {
    const raw = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(raw);
  } catch (err) {
    return { app_version: null, markitdown_version: null, built_at: null };
  }
}

function readUpdateCache(userDataPath) {
  const filePath = path.join(userDataPath, CACHE_FILE_NAME);
  try {
    const raw = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(raw);
  } catch (err) {
    return { lastCheckedAt: null, latestVersion: null };
  }
}

function writeUpdateCache(userDataPath, cache) {
  const filePath = path.join(userDataPath, CACHE_FILE_NAME);
  fs.writeFileSync(filePath, JSON.stringify(cache, null, 2));
}

function shouldCheck(cache, now = Date.now()) {
  if (!cache || !cache.lastCheckedAt) return true;
  return now - cache.lastCheckedAt >= CHECK_INTERVAL_MS;
}

function fetchLatestMarkItDownVersion() {
  return new Promise((resolve, reject) => {
    const req = https.get(PYPI_URL, { headers: { 'User-Agent': 'khat-update-checker' } }, (res) => {
      if (res.statusCode !== 200) {
        res.resume();
        reject(new Error(`PyPI respondeu ${res.statusCode}`));
        return;
      }
      let body = '';
      res.on('data', (chunk) => { body += chunk; });
      res.on('end', () => {
        try {
          const data = JSON.parse(body);
          resolve(data.info.version);
        } catch (err) {
          reject(err);
        }
      });
    });
    req.on('error', reject);
    req.setTimeout(10000, () => req.destroy(new Error('Timeout ao consultar o PyPI')));
  });
}

async function checkForUpdate({
  resourcesPath, isPackaged, appDir, userDataPath,
  fetchFn = fetchLatestMarkItDownVersion, now = Date.now(),
}) {
  const versionInfo = readVersionInfo({ resourcesPath, isPackaged, appDir });
  const currentVersion = versionInfo.markitdown_version;
  let cache = readUpdateCache(userDataPath);

  if (shouldCheck(cache, now)) {
    try {
      const latestVersion = await fetchFn();
      cache = { lastCheckedAt: now, latestVersion };
      writeUpdateCache(userDataPath, cache);
    } catch (err) {
      // Falha silenciosa: sem internet ou PyPI fora do ar. Tenta de novo na próxima checagem.
      return { updateAvailable: false, latestVersion: cache.latestVersion || null, currentVersion };
    }
  }

  const updateAvailable = isNewerVersion(cache.latestVersion, currentVersion);
  return { updateAvailable, latestVersion: cache.latestVersion, currentVersion };
}

module.exports = {
  readVersionInfo,
  readUpdateCache,
  writeUpdateCache,
  shouldCheck,
  fetchLatestMarkItDownVersion,
  checkForUpdate,
  CHECK_INTERVAL_MS,
};
