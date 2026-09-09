import { useEffect, useState } from 'react'

const DEFAULT_STATUS = { updateAvailable: false, latestVersion: null, currentVersion: null }
const DEFAULT_VERSION_INFO = { app_version: null, markitdown_version: null, built_at: null, libraries: {} }

export function useUpdateStatus() {
  const [versionInfo, setVersionInfo] = useState(DEFAULT_VERSION_INFO)
  const [updateStatus, setUpdateStatus] = useState(DEFAULT_STATUS)

  useEffect(() => {
    if (!window.electronAPI) return undefined

    window.electronAPI.getVersionInfo().then(setVersionInfo).catch(() => {})
    window.electronAPI.getUpdateStatus().then(setUpdateStatus).catch(() => {})

    const unsubscribe = window.electronAPI.onUpdateAvailable((status) => {
      setUpdateStatus(status)
    })
    return unsubscribe
  }, [])

  return { versionInfo, updateStatus }
}
