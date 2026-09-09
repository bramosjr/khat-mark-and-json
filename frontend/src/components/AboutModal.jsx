import { X, ExternalLink } from 'lucide-react'

export function AboutModal({ versionInfo, updateStatus, onClose }) {
  const openLink = (url) => {
    if (window.electronAPI?.openExternal) {
      window.electronAPI.openExternal(url)
    }
  }

  return (
    <div className="modal-overlay animate-fade-in">
      <div className="modal-content glass-panel">
        <div className="modal-header">
          <h2>Sobre</h2>
          <button onClick={onClose} className="close-btn"><X size={20} /></button>
        </div>
        <div className="modal-body">
          <p><strong>Khat Mark And Json</strong> — versão {versionInfo.app_version || 'desconhecida'}</p>
          <p>Motor de conversão: MarkItDown v{versionInfo.markitdown_version || 'desconhecida'}</p>
          {updateStatus.updateAvailable && (
            <p className="update-banner-inline">
              Nova versão do MarkItDown disponível: {updateStatus.latestVersion}
            </p>
          )}
          <p>
            <button className="about-link" onClick={() => openLink('https://github.com/bramosjr/khat-mark-and-json')}>
              Repositório do Khat Mark And Json <ExternalLink size={14} />
            </button>
          </p>
          <p>
            <button className="about-link" onClick={() => openLink('https://github.com/microsoft/markitdown')}>
              Repositório do MarkItDown <ExternalLink size={14} />
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
