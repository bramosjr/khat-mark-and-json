import { X, ExternalLink } from 'lucide-react'

export function UpdateBanner({ latestVersion, onDismiss }) {
  const openRepo = () => {
    if (window.electronAPI?.openExternal) {
      window.electronAPI.openExternal('https://github.com/microsoft/markitdown')
    }
  }

  return (
    <div className="update-banner animate-fade-in">
      <span>Nova versão do MarkItDown disponível: {latestVersion}</span>
      <button className="update-banner-link" onClick={openRepo}>
        Ver no GitHub <ExternalLink size={14} />
      </button>
      <button className="update-banner-close" onClick={onDismiss} title="Dispensar">
        <X size={16} />
      </button>
    </div>
  )
}
