const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const os = require('os');
const crypto = require('crypto');
const { checkForUpdate, readVersionInfo } = require('./update-checker.cjs');
const {
  checkForAppUpdate, readAppUpdateState, setAppUpdateEnabled, isAppUpdateEnabled,
} = require('./app-update-checker.cjs');
const { cliResponse } = require('./cli-args.cjs');

app.name = 'khat-mark-and-json';
app.setAppUserModelId('khat-mark-and-json');

const khatToken = crypto.randomBytes(32).toString('hex');
ipcMain.handle('get-token', () => khatToken);

let cachedVersionInfo = null;
let latestUpdateStatus = { updateAvailable: false, latestVersion: null, currentVersion: null };
let latestAppUpdateStatus = {
  updateAvailable: false, latestVersion: null, currentVersion: null, releaseUrl: null, enabled: true,
};

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
ipcMain.handle('get-app-update-status', () => ({
  ...latestAppUpdateStatus,
  enabled: readAppUpdateState(app.getPath('userData')).enabled,
}));
ipcMain.handle('set-app-update-enabled', (_event, enabled) => {
  const userDataPath = app.getPath('userData');
  setAppUpdateEnabled(userDataPath, enabled === true);
  const isEnabled = isAppUpdateEnabled(userDataPath);
  if (!isEnabled) {
    latestAppUpdateStatus = { ...latestAppUpdateStatus, updateAvailable: false, enabled: false };
  }
  return isEnabled;
});

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
    title: "Khat Mark And Json",
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

const cliText = cliResponse(process.argv.slice(1), getVersionInfo().app_version || app.getVersion());

// A ordem importa: --help e --version respondem antes do bloqueio de instância
// única, para não acionar a janela de um app que já esteja aberto.
if (cliText !== null) {
  process.stdout.write(cliText);
  app.exit(0);
} else if (!app.requestSingleInstanceLock()) {
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

    const userDataPath = app.getPath('userData');
    // Uma única preferência (opt-out) governa todas as checagens que usam a rede.
    if (isAppUpdateEnabled(userDataPath)) {
      checkForUpdate({
        resourcesPath: process.resourcesPath,
        isPackaged: app.isPackaged,
        appDir: __dirname,
        userDataPath,
      }).then((status) => {
        latestUpdateStatus = status;
        if (status.updateAvailable && mainWindow) {
          mainWindow.webContents.send('dep-update:available', status);
        }
      }).catch((err) => console.error('Falha ao checar atualização do MarkItDown:', err));

      checkForAppUpdate({
        appVersion: getVersionInfo().app_version || app.getVersion(),
        userDataPath,
      }).then((status) => {
        latestAppUpdateStatus = status;
        if (status.updateAvailable && mainWindow) {
          mainWindow.webContents.send('app-update:available', status);
        }
      }).catch((err) => console.error('Falha ao checar atualização do app:', err));
    }

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
