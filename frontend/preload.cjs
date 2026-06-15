const { contextBridge, ipcRenderer } = require('electron');

// Expõe APIs seguras para o frontend, se necessário.
// Atualmente, nosso React fala diretamente com o backend (FastAPI) via fetch (HTTP),
// então o preload está aqui apenas como uma fundação segura.
contextBridge.exposeInMainWorld('electronAPI', {
  isElectron: true,
  getToken: () => ipcRenderer.invoke('get-token')
});
