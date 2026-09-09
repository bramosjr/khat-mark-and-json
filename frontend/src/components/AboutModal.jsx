import { X, ExternalLink } from 'lucide-react'

// Nome de exibição + link (PyPI, onde cada pacote Python realmente vive) de
// cada biblioteca de conversão — incluindo o MarkItDown, que entra na mesma
// lista em vez de ficar separado. Chave = nome do pacote em
// version-info.json (markitdown_version fica de fora de `libraries` porque
// também alimenta a checagem de atualização; é combinado aqui na hora de
// montar a lista).
const LIBRARY_INFO = {
  'markitdown': { label: 'MarkItDown', url: 'https://pypi.org/project/markitdown/' },
  'openai': { label: 'OpenAI SDK', url: 'https://pypi.org/project/openai/' },
  'google-genai': { label: 'Google GenAI SDK', url: 'https://pypi.org/project/google-genai/' },
  'anthropic': { label: 'Anthropic SDK', url: 'https://pypi.org/project/anthropic/' },
  'PyMuPDF': { label: 'PyMuPDF', url: 'https://pypi.org/project/PyMuPDF/' },
  'pdfplumber': { label: 'pdfplumber', url: 'https://pypi.org/project/pdfplumber/' },
  'camelot-py': { label: 'Camelot', url: 'https://pypi.org/project/camelot-py/' },
  'olefile': { label: 'olefile', url: 'https://pypi.org/project/olefile/' },
  'pandas': { label: 'pandas', url: 'https://pypi.org/project/pandas/' },
  'openpyxl': { label: 'openpyxl', url: 'https://pypi.org/project/openpyxl/' },
  'odfpy': { label: 'odfpy', url: 'https://pypi.org/project/odfpy/' },
}

// Ordem de exibição — MarkItDown primeiro (é o motor principal), as demais
// na mesma ordem de sempre.
const LIBRARY_ORDER = [
  'markitdown', 'openai', 'google-genai', 'anthropic', 'PyMuPDF',
  'pdfplumber', 'camelot-py', 'olefile', 'pandas', 'openpyxl', 'odfpy',
]

export function AboutModal({ versionInfo, updateStatus, onClose }) {
  const openLink = (url) => {
    if (window.electronAPI?.openExternal) {
      window.electronAPI.openExternal(url)
    }
  }

  const allLibraryVersions = {
    markitdown: versionInfo.markitdown_version,
    ...(versionInfo.libraries || {}),
  }
  const libraryEntries = LIBRARY_ORDER
    .filter((key) => key in allLibraryVersions && LIBRARY_INFO[key])
    .map((key) => ({ key, ...LIBRARY_INFO[key], version: allLibraryVersions[key] }))

  return (
    <div className="modal-overlay animate-fade-in">
      <div className="modal-content glass-panel">
        <div className="modal-header">
          <h2>Sobre</h2>
          <button onClick={onClose} className="close-btn"><X size={20} /></button>
        </div>
        <div className="modal-body">
          <p><strong>Khat Mark And Json</strong> — versão {versionInfo.app_version || 'desconhecida'}</p>
          {updateStatus.updateAvailable && (
            <p className="update-banner-inline">
              Nova versão do MarkItDown disponível: {updateStatus.latestVersion}
            </p>
          )}
          {libraryEntries.length > 0 && (
            <div className="about-libraries">
              <p className="about-libraries-title">Bibliotecas de conversão</p>
              <ul>
                {libraryEntries.map(({ key, label, url, version }) => (
                  <li key={key}>
                    <button className="about-link about-library-link" onClick={() => openLink(url)}>
                      {label} <ExternalLink size={12} />
                    </button>
                    <span>v{version || 'desconhecida'}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <p>
            <button className="about-link" onClick={() => openLink('https://github.com/bramosjr/khat-mark-and-json')}>
              Repositório do Khat Mark And Json <ExternalLink size={14} />
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
