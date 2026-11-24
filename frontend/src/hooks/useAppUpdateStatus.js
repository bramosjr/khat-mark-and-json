import { useCallback, useEffect, useState } from 'react'

const DEFAULT_STATUS = {
  updateAvailable: false, latestVersion: null, currentVersion: null, releaseUrl: null, enabled: true,
}

export function useAppUpdateStatus() {
  const [appUpdateStatus, setAppUpdateStatus] = useState(DEFAULT_STATUS)

  useEffect(() => {
    if (!window.electronAPI?.getAppUpdateStatus) return undefined

    window.electronAPI.getAppUpdateStatus().then(setAppUpdateStatus).catch(() => {})
    return window.electronAPI.onAppUpdateAvailable((status) => setAppUpdateStatus(status))
  }, [])

  const setEnabled = useCallback(async (enabled) => {
    if (!window.electronAPI?.setAppUpdateEnabled) return
    try {
      const isEnabled = await window.electronAPI.setAppUpdateEnabled(enabled)
      setAppUpdateStatus((prev) => ({
        ...prev,
        enabled: isEnabled,
        updateAvailable: isEnabled ? prev.updateAvailable : false,
      }))
    } catch {
      // Mantém o estado anterior se o IPC falhar.
    }
  }, [])

  return { appUpdateStatus, setEnabled }
}
