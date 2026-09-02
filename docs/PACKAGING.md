# Nexa AI — Windows Packaging Readiness

## How to run (development)

Backend:
```powershell
cd backend
python --version                 # install Python 3.11+ if this fails
python -m venv .venv             # recreate if .venv points to an old Python path
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m compileall app scripts
python run_backend.py            # serves http://127.0.0.1:8000
```

Frontend (desktop app):
```powershell
cd frontend
npm.cmd install                  # first time only; use npm.cmd in PowerShell
npm.cmd run dev                  # Vite + Electron window
```

Production build check:
```powershell
cd frontend
npm.cmd run test                 # TypeScript project check
npm.cmd run build                # tsc + vite build
```

Backend smoke check:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python scripts\smoke_test_backend.py
```

Troubleshooting notes:
- If `python` is not recognized, install Python 3.11+ and enable "Add python.exe to PATH".
- If `.venv` is broken or points to an old path, recreate it with `python -m venv .venv`.
- If PowerShell blocks `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- If `npm` is blocked by PowerShell, use `npm.cmd`.

## First-run downloads (one-time, internet required)

- Whisper STT model (`small`, ~460 MB) downloads automatically into
  `backend/models/whisper/` on the first transcription. Configure size with
  the `NEXA_WHISPER_MODEL` env var (`tiny` | `base` | `small`, default `small`).
- After that, STT is fully offline.

## Current portable packaging workflow

```powershell
cd frontend
npm.cmd run package:windows
```

This builds the frontend and creates `release/NexaAI-Windows.zip` with the
Electron runtime and a PyInstaller one-folder backend executable.
If Inno Setup 6 is installed, adding `-BuildInstaller` to
`scripts/package-windows.ps1` produces an installer as well. Destination
computers do not require Python, pip, Node.js, or a virtual environment.

Electron checks backend health at startup, launches the bundled backend when
needed, keeps writable data/models under Electron's user-data directory, and
stops the process during app shutdown.

## Rebuilding the development environment

```powershell
cd backend
powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -ForceRecreate
```

The previous environment is preserved as a timestamped `.venv.backup-*` until
you have verified the new one.

## Remaining release hardening

1. **Signing** — code-sign `NexaAI.exe`, `nexa-backend.exe`, and the installer
   before public distribution to reduce Windows SmartScreen warnings.
2. **Models** — do NOT bundle Whisper/Vosk models in the installer; download
   on first run (or offer an optional offline model pack).
3. **Never package**: `backend/.venv*`, `backend/models/`, `frontend/node_modules/`,
   `*.tsbuildinfo`, `__pycache__`, `*.pyc`, local sqlite data files.

## Release checklist

- [x] `python -m compileall app scripts` passes
- [x] backend pytest suite passes
- [x] `npm.cmd run test` passes
- [x] standalone backend health/readiness smoke test passes
- [ ] All `/api/*/health` endpoints return ok
- [ ] `"delete system32"` (and Bangla equivalents) blocked server-side even with `user_confirmed: true`
- [ ] Website/app whitelists unchanged and enforced
- [ ] File search remains read-only metadata
- [ ] TTS disabled by default; locked permissions cannot be enabled
- [ ] No always-on microphone; push-to-talk only
- [ ] Audit events recorded for executed/blocked actions
