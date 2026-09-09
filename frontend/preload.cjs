const { contextBridge, ipcRenderer } = require('electron');

// Expõe APIs seguras para o frontend.
// O React fala diretamente com o backend (FastAPI) via fetch (HTTP) para conversão,
// e usa este canal para token de autenticação, informações de versão e checagem de atualização.
contextBridge.exposeInMainWorld('electronAPI', {
  isElectron: true,
  getToken: () => ipcRenderer.invoke('get-token'),
  getVersionInfo: () => ipcRenderer.invoke('get-version-info'),
  getUpdateStatus: () => ipcRenderer.invoke('get-update-status'),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  onUpdateAvailable: (callback) => {
    const listener = (_event, payload) => callback(payload);
    ipcRenderer.on('dep-update:available', listener);
    return () => ipcRenderer.removeListener('dep-update:available', listener);
  },
});
