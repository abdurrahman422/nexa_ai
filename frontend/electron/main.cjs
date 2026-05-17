const { app, BrowserWindow, Menu } = require("electron");
const path = require("node:path");

const isDev = process.env.NEXA_ELECTRON_DEV === "1";
const devServerUrl = process.env.NEXA_DEV_SERVER_URL || "http://127.0.0.1:5173";

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    title: "Nexa AI",
    width: 1440,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    center: true,
    backgroundColor: "#020617",
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, "preload.cjs"),
    },
  });

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
    mainWindow.focus();
  });

  mainWindow.webContents.on("did-finish-load", () => {
    console.log("[Nexa AI] Renderer loaded successfully.");
  });

  mainWindow.webContents.on(
    "did-fail-load",
    (_event, errorCode, errorDescription, validatedURL) => {
      console.error("[Nexa AI] Renderer load failed:", {
        errorCode,
        errorDescription,
        validatedURL,
      });
    }
  );

  if (isDev) {
    console.log("[Nexa AI] Loading dev server:", devServerUrl);
    mainWindow.loadURL(devServerUrl);
  } else {
    const htmlPath = path.join(__dirname, "../dist/index.html");
    console.log("[Nexa AI] Loading production file:", htmlPath);
    mainWindow.loadFile(htmlPath);
  }
}

const gotLock = app.requestSingleInstanceLock();

if (!gotLock) {
  app.quit();
} else {
  app.whenReady().then(() => {
    app.name = "Nexa AI";
    Menu.setApplicationMenu(null);
    createWindow();

    app.on("second-instance", () => {
      if (mainWindow) {
        if (mainWindow.isMinimized()) mainWindow.restore();
        mainWindow.focus();
      }
    });

    app.on("activate", () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      }
    });
  });
}

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});