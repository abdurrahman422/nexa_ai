# Nexa AI

Nexa AI is a local-first Windows desktop assistant project. It now has a React/Electron/Vite frontend and a Python FastAPI backend. The project is beyond the original Phase 01 planning skeleton, but it is still not a finished product: some screens are wired to real backend endpoints, while others are preview-only or not wired yet.

## Current Reality

- Frontend: React 19, TypeScript, Vite, Electron shell, custom dark assistant UI.
- Backend: FastAPI at `http://127.0.0.1:8000`.
- No paid API is required for the MVP.
- Dashboard chat now supports local persona replies, smart task routing, weather/time, search-backed live answers, optional hosted LLM providers, safe YouTube open/search, and WhatsApp draft-only contact workflows.
- Online voice features require an internet connection; no local speech model is downloaded.
- The frontend and backend run separately during development.
- The backend must be running before backend-backed UI controls will work.

## Quick Start on Windows

Open PowerShell in the project root:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai"
```

### 1. Check Python

```powershell
python --version
```

If that fails, try:

```powershell
py --version
```

Install Python 3.11+ from `https://www.python.org/downloads/windows/` if neither command works. During installation, enable "Add python.exe to PATH".

### 2. Create and Run the Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run_backend.py
```

Backend URL:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

### 3. Run the Frontend

Open a second PowerShell terminal:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\frontend"
npm.cmd install
npm.cmd run dev
```

The web dev server runs at:

```text
http://127.0.0.1:5173
```

`npm.cmd` is recommended on Windows PowerShell because plain `npm` may be blocked by PowerShell script execution policy.

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` is not recognized | Install Python 3.11+ and enable "Add python.exe to PATH", or use `py -3` if available. |
| `.venv` points to an old/missing Python path | Deactivate the venv, rename or recreate `.venv`, then run `python -m venv .venv` again. Do not rely on a copied `.venv`. |
| `pip` launcher points to the wrong path | Use `python -m pip install -r requirements.txt` instead of plain `pip`. |
| PowerShell blocks activation script | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` in PowerShell, then reopen the terminal. |
| `npm` is blocked by PowerShell policy | Use `npm.cmd install`, `npm.cmd run dev`, and `npm.cmd run build`. |
| Backend UI says offline | Start `python run_backend.py` in the `backend` folder and keep it running. |
| Online voice is unavailable | Confirm the backend is running, microphone permission is allowed, and the internet connection works. |

## Feature Status

| Feature | Status | Notes |
|---|---|---|
| Dashboard command center | Working / Wired, Backend required | Can route recognized launch commands to backend action endpoints after confirmation. |
| Launcher | Working / Wired, Backend required | Whitelisted apps/websites only. Unknown targets are blocked backend-side. |
| Web answers | Working / Wired, Backend required | Uses safe public sources through the backend. |
| Files/document preview | Working / Wired, Backend required | Read-only search and preview. File write operations are intentionally disabled. |
| Reminders | Working / Wired, Backend required | Local reminder records with confirmation. |
| Permissions/security center | Working / Wired, Backend required | Toggleable backend permissions plus locked-off unsafe capabilities. |
| Voice STT | Backend + internet required | Online Bangla push-to-talk through Google Web Speech; no local model. |
| TTS | Backend + internet required | Online Edge neural Bangla/English voices, permission-gated. |
| Audit/history | Working / Wired, Backend required | Backend audit events plus local preview history. |
| AI Chat | Working / Wired, Backend required | Real chat UI with local history, Open-Meteo weather, DuckDuckGo/Wikipedia web answers, and no action execution. |
| LLM provider router | Backend required, Optional keys | Gemini primary with Groq/OpenRouter/Cloudflare/Mistral/Cerebras fallback when configured in local `.env`. |
| WhatsApp draft composer | Working / Wired, Backend required | Local contacts, aliases, relationship/tone, safe `wa.me` draft URLs only. Nexa never clicks Send. |
| Automation workflow templates | Preview only | Template cards are not executable workflows. |
| Profile settings | Working / Wired locally | Stored in frontend local storage, not backend profile API. |
| Windows packaging | Working / Standalone | `npm.cmd run package:windows` bundles Electron and a PyInstaller backend; destination machines do not need Python or pip. Optional Inno Setup creates shortcuts and an installer. |

## SmartVoice-Inspired Extensions

Nexa includes selected, safety-adapted capabilities inspired by the MIT-licensed
SmartVoice project. See `THIRD_PARTY_NOTICES.md` for attribution.

- Advanced YouTube player: search/play, pause/resume, seek, volume/mute,
  captions, fullscreen, theater mode, speed, next/previous, autoplay, sleep
  timer, status, close, and microphone audio ducking.
- Smart reminders: natural-language relative time, recurring schedules, and
  snooze. Reminder writes still require explicit confirmation.
- Optional AI Image Studio using Hugging Face Inference Providers. Set
  `HUGGINGFACE_API_KEY` and enable the permission in Security Center. The UI
  now includes a background queue and a local generated-image gallery.
- Optional Windows media controls and normal-close for whitelisted apps.
  This permission is off by default; force-close, shell access, shutdown, and
  arbitrary process control remain blocked.
- Content Writer exports confirmed Markdown/TXT files only to
  `backend/data/generated_content`.
- Performance Dashboard aggregates the local audit trail and exports CSV/JSON.
- Reminder Center supports natural language, recurrence, snooze, and editing.
- Edge neural Bangla/English voice output is permission-gated and needs an
  internet connection.
- Search already falls back across configured Serper, free DuckDuckGo/
  Wikipedia, Brave, and SerpAPI providers.

Advanced YouTube control needs Google Chrome and the Python `selenium` package
from `backend/requirements.txt`. YouTube UI changes, consent dialogs, ads, or
CAPTCHAs may occasionally require selector updates.

## Windows Release Bundle

```powershell
cd frontend
npm.cmd run package:windows
```

This creates `release/NexaAI-Windows.zip`. With Inno Setup 6 installed, run
`powershell -ExecutionPolicy Bypass -File scripts/package-windows.ps1 -BuildInstaller`
to also build `release/installer/NexaAI-Setup.exe`. The packaged app includes
its Python backend and dependencies, starts it automatically, and stops it when
Nexa exits. Python is required only for development or rebuilding the package.

## Backend Smoke Test

After starting the backend:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
python scripts\smoke_test_backend.py
```

This checks health, permissions, locked permissions, dangerous command blocking, unknown target blocking, dry-run safety, and recent audit events.

## Optional Provider Configuration

Copy `backend/.env.example` to `backend/.env` and set only the providers you want to use. Never commit real keys.

```env
NEXA_SEARCH_PROVIDER=serper
SERPER_API_KEY=your_serper_api_key_here

NEXA_LLM_ROUTER_ENABLED=true
NEXA_LLM_PRIMARY=gemini
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=
OPENROUTER_API_KEY=
CLOUDFLARE_ACCOUNT_ID=
CLOUDFLARE_API_TOKEN=
MISTRAL_API_KEY=
CEREBRAS_API_KEY=
```

Live/current data such as gold price and news uses search first. LLM providers may summarize source results, but they must not invent live data.

### Optional Google Cloud Streaming Voice Input

Nexa's Voice Room uses Google Cloud streaming STT when configured and falls back
to browser Web Speech automatically. Create a Google Cloud service account with
Speech-to-Text access, download its JSON key outside the repository, and add the
following local values to `backend/.env`:

```env
NEXA_GOOGLE_STT_ENABLED=true
GOOGLE_APPLICATION_CREDENTIALS=C:\absolute\private\path\google-stt.json
```

Never commit the service-account JSON. In Settings → Voice, select `Auto` for
Google-first recognition with browser fallback, or choose either engine directly.

## Trusted Skill Settings

In Settings/Security:

- `Trusted YouTube Auto Open` lets recognized YouTube open/search commands open whitelisted YouTube URLs directly.
- `Trusted WhatsApp Draft Auto Open` lets known-contact WhatsApp draft URLs open directly.
- WhatsApp remains draft-only. Nexa does not click Send, read chats, scrape credentials, or send messages silently.
- Local WhatsApp contacts support aliases, relationship, and default tone.

## Frontend Checks

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\frontend"
npm.cmd run test
npm.cmd run build
```

`npm.cmd run test` is currently a TypeScript project check. It is not a full UI/unit test suite yet.

## Current Limitations

- Hosted LLM providers are optional and require user-provided keys in local `.env`; the app still works in local/free-provider mode.
- Live search quality depends on configured search providers. Serper is optional and key-based; free fallback providers are weaker.
- Automation workflow templates are preview-only.
- File delete/move/rename/edit is intentionally disabled.
- WhatsApp is draft-only with local contacts. Email automation is not implemented.
- Smart home/ESP32 support is future work.
- Online YouTube, Edge TTS, search, and hosted image providers naturally need an internet connection while used.
- Hugging Face image generation needs a user-provided token; Settings stores it only in Nexa's local app-data configuration.

## Documentation Links

- [Product Vision](docs/product_vision.md)
- [Feature Requirements](docs/feature_requirements.md)
- [Technical Architecture](docs/technical_architecture.md)
- [Packaging Plan](docs/PACKAGING.md)
- [Full Audit Report](CODEX_FULL_PROJECT_AUDIT_REPORT.md)

## Project Policy

Nexa AI should remain local-first, safety-gated, low-end laptop friendly, and usable without paid APIs for the MVP.
