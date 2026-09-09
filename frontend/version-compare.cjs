// Compara versões no formato semver simples (major.minor.patch, com sufixos opcionais).
// Retorna true se `latest` for mais nova que `current`.
function parseVersion(v) {
  const clean = String(v).trim().replace(/^v/i, '');
  const [core] = clean.split(/[-+]/); // ignora pré-release/build metadata na comparação
  return core.split('.').map((part) => {
    const n = parseInt(part, 10);
    return Number.isNaN(n) ? 0 : n;
  });
}

function isNewerVersion(latest, current) {
  if (!latest || !current) return false;
  const a = parseVersion(latest);
  const b = parseVersion(current);
  const len = Math.max(a.length, b.length);
  for (let i = 0; i < len; i++) {
    const x = a[i] || 0;
    const y = b[i] || 0;
    if (x > y) return true;
    if (x < y) return false;
  }
  return false;
}

module.exports = { isNewerVersion, parseVersion };
