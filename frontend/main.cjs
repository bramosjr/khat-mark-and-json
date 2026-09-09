const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const os = require('os');
const crypto = require('crypto');
const { checkForUpdate, readVersionInfo } = require('./update-checker.cjs');

const khatToken = crypto.randomBytes(32).toString('hex');
ipcMain.handle('get-token', () => khatToken);

let cachedVersionInfo = null;
let latestUpdateStatus = { updateAvailable: false, latestVersion: null, currentVersion: null };

function getVersionInfo() {
  if (!cachedVersionInfo) {
    cachedVersionInfo = readVersionInfo({
      resourcesPath: process.resourcesPath,
      isPackaged: app.isPackaged,
      appDir: __dirname,
    });
  }
  return cachedVersionInfo;
}

ipcMain.handle('get-version-info', () => getVersionInfo());
ipcMain.handle('get-update-status', () => latestUpdateStatus);

const ALLOWED_EXTERNAL_HOSTS = ['github.com', 'pypi.org'];
ipcMain.handle('open-external', (_event, url) => {
  try {
    const parsed = new URL(url);
    if (parsed.protocol === 'https:' && ALLOWED_EXTERNAL_HOSTS.includes(parsed.hostname)) {
      shell.openExternal(url);
    }
  } catch (err) {
    console.error('URL externa inválida:', url);
  }
});

let mainWindow;
let pythonProcess = null;

function startPythonBackend() {
  const isProd = app.isPackaged;
  const ext = os.platform() === 'win32' ? '.exe' : '';
  let cmd, args;
  
  if (isProd) {
    const exeName = os.platform() === 'win32' ? 'markitdown-backend.exe' : 'markitdown-backend';
    const backendPath = path.join(process.resourcesPath, exeName);
    cmd = backendPath;
    args = [];
    console.log('Iniciando o backend (produção) em:', backendPath);
  } else {
    // Em desenvolvimento, roda usando raw Python do venv para melhor output e debug
    const pythonExec = os.platform() === 'win32' ? 'python.exe' : 'python';
    cmd = path.join(__dirname, '..', 'backend', 'venv', 'bin', pythonExec);
    args = [path.join(__dirname, '..', 'backend', 'main.py')];
    console.log('Iniciando o backend Python puro em:', cmd);
  }
  
  try {
    pythonProcess = spawn(cmd, args, {
      detached: false,
      stdio: 'pipe',
      windowsHide: true,
      env: { ...process.env, KHAT_TOKEN: khatToken }
    });

    pythonProcess.stdout.on('data', (data) => {
      console.log(`Backend: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`Backend Error: ${data}`);
    });

    pythonProcess.on('close', (code) => {
      console.log(`Backend finalizado com código ${code}`);
    });
  } catch (err) {
    console.error('Falha ao iniciar o processo Python:', err);
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    title: "MarkItDown",
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false
    },
    autoHideMenuBar: true,
    backgroundColor: '#5C2E20', // Matches our CSS --bg-primary (Argila Escura)
    icon: path.join(__dirname, 'public', 'icone.png')
  });

  if (app.isPackaged) {
    mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));
  } else {
    mainWindow.loadURL('http://localhost:5173');
  }
}

const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', (event, commandLine, workingDirectory) => {
    // Someone tried to run a second instance, we should focus our window.
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(() => {
    app.setAppUserModelId('com.bramosjr.markitdown');
    startPythonBackend();
    createWindow();

    checkForUpdate({
      resourcesPath: process.resourcesPath,
      isPackaged: app.isPackaged,
      appDir: __dirname,
      userDataPath: app.getPath('userData'),
    }).then((status) => {
      latestUpdateStatus = status;
      if (status.updateAvailable && mainWindow) {
        mainWindow.webContents.send('dep-update:available', status);
      }
    }).catch((err) => console.error('Falha ao checar atualização do MarkItDown:', err));

    app.on('activate', function () {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });
}

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

app.on('will-quit', () => {
  // Garante que o processo em Python morre quando o Electron fecha
  if (pythonProcess) {
    pythonProcess.kill();
  }
});
