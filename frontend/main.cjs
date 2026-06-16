const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const os = require('os');
const crypto = require('crypto');

const khatToken = crypto.randomBytes(32).toString('hex');
ipcMain.handle('get-token', () => khatToken);

let mainWindow;
let pythonProcess = null;

function startPythonBackend() {
  const isProd = app.isPackaged;
  const ext = os.platform() === 'win32' ? '.exe' : '';
  let cmd, args;
  
  if (isProd) {
    const backendPath = path.join(process.resourcesPath, 'markitdown-backend', `markitdown-backend${ext}`);
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
      contextIsolation: true
    },
    autoHideMenuBar: true,
    backgroundColor: '#0a0a0c', // Matches our CSS --bg-primary
    icon: path.join(__dirname, 'public', 'icone.png')
  });

  if (app.isPackaged) {
    mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));
  } else {
    mainWindow.loadURL('http://localhost:5173');
  }
}

app.whenReady().then(() => {
  app.setAppUserModelId('com.bramosjr.markitdown');
  startPythonBackend();
  createWindow();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

app.on('will-quit', () => {
  // Garante que o processo em Python morre quando o Electron fecha
  if (pythonProcess) {
    pythonProcess.kill();
  }
});
