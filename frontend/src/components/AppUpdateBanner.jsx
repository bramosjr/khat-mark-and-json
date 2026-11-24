import { X, ExternalLink } from 'lucide-react'

export function AppUpdateBanner({ latestVersion, currentVersion, releaseUrl, onDismiss }) {
  const openRelease = () => {
    if (window.electronAPI?.openExternal) {
      window.electronAPI.openExternal(releaseUrl)
    }
  }

  return (
    <div className="update-banner animate-fade-in">
      <span>
        Nova versão do Khat Mark And Json disponível: {latestVersion}
        {currentVersion ? ` (atual: ${currentVersion})` : ''}
      </span>
      <button className="update-banner-link" onClick={openRelease}>
        Baixar <ExternalLink size={14} />
      </button>
      <button className="update-banner-close" onClick={onDismiss} title="Dispensar">
        <X size={16} />
      </button>
    </div>
  )
}
