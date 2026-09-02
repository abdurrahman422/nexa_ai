# Nexa AI — Project Audit Report

Last updated: 2026-06-11 (UI v2 redesign pass)

## UI v2 Redesign (latest)

The frontend was redesigned to match the premium dark glass/neon reference mockups while keeping every backend API connection and safety gate:

- **New shell:** icon sidebar (lucide-react), topbar (command input, voice status pill, due-reminder badge, profile), right rail on Dashboard/Launcher/Web/Settings, footer chips. Classes prefixed `nx-` in an additive CSS block.
- **AI Command Center (Dashboard):** animated orb hero, natural-language command bar (Bangla/Banglish/English) → intent detection → inline confirm panel → real backend execution; quick action tiles; live Command Understanding; real System Status; Recent Commands + Today's Activity from the real audit log; suggestion chips; push-to-talk panel in the rail.
- **App & Website Launcher:** whitelisted apps/websites grid → Launch Preview → confirm → backend open; Recent Launches from audit log; custom-launcher config shown as **locked by safety policy** (not faked).
- **Web Search:** safe answers (DuckDuckGo/Wikipedia), Speak button (TTS), recent searches (local), website shortcut tiles with confirm-to-open, "how it stays safe" panel.
- **Settings v2:** numbered cards — profile/addressing/language (persisted), voice toggles (real permissions), safety card with **locked** switches (Always Ask only), privacy toggles (real permissions), notifications prefs, backup/export + confirmed clear-history; rail has profile summary, backend quick toggles, change log.
- **Automations:** reminders live; workflow templates shown as preview-only with a locked-off note (no hidden/auto-run automation).
- **Robustness fix:** splash screen could hang forever if the window started hidden (requestAnimationFrame paused) — added a timer fallback.
- **Verified in live preview:** all 10 pages render; `"delete system32"` → blocked panel; `"ক্যালকুলেটর চালাও"` → open_app + confirmation; real web answer rendered; backend permission toggles load in Settings; zero console errors. `npm run build` ✅ (1625 modules), `compileall` ✅.

Mockup elements intentionally NOT faked: "Upgrade to Pro", auto-execute mode, browser automation workflows, arbitrary launcher aliases, fake stats — replaced with real data or honest locked/preview states.

---

Audited path: `D:\Abdur\nexaai\nexaai`

---

## 1. Project Summary

Nexa AI is a local-first Windows desktop AI assistant (Bangla / Banglish / English):

- **Frontend:** Electron + Vite + React 19 + TypeScript, premium glass/neon custom CSS UI.
- **Backend:** Python 3.13 + FastAPI at `http://127.0.0.1:8000`.
- **Safety model:** whitelist-based real actions, server-side dangerous-keyword blocking, explicit confirmation + dry-run gates, read-only file search, permission center with server-side enforcement, no shell=True anywhere.

## 2. What Is WORKING ✅ (verified live 2026-06-11)

| Area | Status |
|---|---|
| Backend compile + run | ✅ exit 0, serves on 127.0.0.1:8000 |
| Frontend build (tsc + vite) | ✅ 68 modules, 0 errors |
| All 14 health/status endpoints | ✅ ok |
| Safe website open (whitelist + confirm + dry-run) | ✅ |
| Safe app open (whitelist + confirm, shell=False) | ✅ |
| `"delete system32"` with `user_confirmed: true` | ✅ **blocked server-side** |
| Read-only file search (Desktop/Downloads/Documents) | ✅ |
| Bangla/Banglish command matching | ✅ |
| **Permission center** (`/api/permissions`) | ✅ toggles enforce server-side; locked capabilities rejected |
| **STT engine abstraction** (`/api/voice/stt/engines`) | ✅ faster-whisper preferred, Vosk diagnostic fallback |
| **Push-to-talk transcription** (`POST /api/voice/stt/transcribe`) | ✅ wav upload → Whisper small → preview-only transcript |
| **Bangla low-quality warning** | ✅ returns clear JSON warning when transcript lacks Bangla script |
| **TTS** (`/api/voice/tts/*`, pyttsx3, off by default) | ✅ status + speak (permission-gated) |
| **Web answers** (`POST /api/web/answer`, DuckDuckGo/Wikipedia only) | ✅ live answer verified |
| **Document preview** (`POST /api/documents/preview`, read-only PDF/TXT/MD) | ✅ |
| **Reminders** (`/api/reminders`, local SQLite, confirm-to-create) | ✅ |
| **Real audit log** (`GET /api/audit/recent`, SQLite) | ✅ records executed/blocked events |
| Frontend pages: Web Answers, Security Center, Reminders, Files+Preview, Voice PTT, TTS settings, Audit trail | ✅ wired to backend |

## 3. STT Configuration

- Engine: **faster-whisper**, model **small** (default; `NEXA_WHISPER_MODEL=tiny|base|small`), CPU `int8`.
- Bangla: `language="bn"`, `task="transcribe"`, `condition_on_previous_text=False`.
- Model auto-downloads to `backend/models/whisper/` on first use (git-ignored).
- Voice flow: **audio → STT transcript → command preview → user confirmation → safe backend action.** Transcripts never execute directly.
- Vosk kept as diagnostic fallback (`/api/voice/stt/status|readiness|test-transcription`); the bundled streaming ONNX Bangla model cannot load in the classic Python Vosk API (clean JSON error, no crash).
- Bundled `test.wav` transcribes poorly (very low-quality audio) — the new warning field fires correctly: *"Bangla transcription quality is low. Try small/medium model or clearer audio."* Real microphone input is the production path.

## 4. Safety / Security Status ✅

- Dangerous keywords (delete/format/shutdown/system32/registry/cmd/powershell + Bangla equivalents) blocked first, server-side, even with `user_confirmed: true` (re-verified live).
- Whitelists unchanged: 7 websites, 5 apps. Unknown targets blocked. `subprocess.Popen([command], shell=False)` only.
- File search/document preview strictly read-only inside safe folders; symlinks skipped; blocked path keywords filtered.
- Permission center: 8 toggleable feature permissions (TTS **off** by default) + 5 **locked** permissions that the API refuses to enable (file write ops, auto-send messaging, always-on mic, shell execution, arbitrary app execution).
- Microphone: push-to-talk only; stream fully stopped and released after each recording; 60s cap; 15MB upload cap.
- Web answers: fixed host whitelist (api.duckduckgo.com, en/bn.wikipedia.org); no scraping, no arbitrary URLs.
- Audit: every executed/blocked action, transcription, TTS call, web answer, and reminder mutation is recorded to local SQLite and viewable in History.

## 5. Incomplete / Foundation-only

1. **n8n integration** — not started (future optional phase; localhost + token design documented in master prompt).
2. **WhatsApp/email automation** — not started by design; locked off in the permission center until a confirmed-flow phase is approved.
3. **Windows installer** — packaging plan + release checklist in `docs/PACKAGING.md`; electron-builder/PyInstaller not yet added.
4. **Web answers** are instant-answer grade (DuckDuckGo/Wikipedia); LLM summarization would need an API key (not added).
5. **Document assistant** extracts text previews; no semantic summarization yet (would need an LLM).
6. Bundled Vosk ONNX model unusable by classic Vosk runtime (Whisper is the production path).

## 6. Files Changed in This Build

**Backend new:** `app/permissions/` (store), `app/audit/event_log.py`, `app/voice/whisper_engine.py`, `app/voice/stt_engines.py`, `app/voice/tts_engine.py`, `app/web/` (answers), `app/documents/` (reader), `app/reminders/` (store), `app/api/routes/{permissions,web,documents,reminders}.py`, `app/schemas/{permissions,web,documents,reminders}.py`.
**Backend modified:** `app/main.py` (router registration), `app/api/routes/{voice,actions,audit}.py` (new endpoints, permission enforcement, audit recording), `app/schemas/{voice,__init__}.py`, `app/voice/vosk_config.py` (absolute model path), `requirements.txt`.
**Frontend new:** `src/lib/backendAssistantClient.ts`, `src/lib/audioRecorder.ts`, `src/components/voice/PushToTalkPanel.tsx`, `src/components/history/AuditEventsPanel.tsx`, `src/components/settings/TtsSettingsCard.tsx`, `src/pages/{web/WebAnswersPage,automation/RemindersPage,security/SecurityCenterPage,files/FilesPage}.tsx`.
**Frontend modified:** `src/app/App.tsx` (routing + PTT/audit/TTS wiring), `src/lib/index.ts`, `src/styles/global.css` (additive themed block only).
**Other:** `.gitignore` (models, *.bin/pt/onnx/gguf, venvs, tsbuildinfo, sqlite), `docs/PACKAGING.md`.

UI design system untouched — all new UI reuses the existing glass/neon classes plus a small additive CSS block.

## 7. Test Results (2026-06-11)

- `python -m compileall app` → exit 0
- `python run_backend.py` → serves; all 14 endpoints ok
- `npm run build` → passes (68 modules)
- Safety: `"delete system32"` + `user_confirmed:true` → blocked; google dry-run → preview_only; locked permission enable attempt → rejected
- Live web answer (Bitcoin) → answered from DuckDuckGo
- HTTP audio upload → Whisper small transcript + correct warning JSON

## 8. How to Run

```powershell
# Backend
cd backend
.\.venv\Scripts\python.exe run_backend.py

# Frontend (desktop)
cd frontend
npm run dev
```

First transcription downloads the Whisper model (~460 MB, one time).

## 9. Next Recommended Phases

1. Commit this build.
2. Production packaging (electron-builder + backend bundling per `docs/PACKAGING.md`).
3. Optional: n8n foundation, LLM-powered summarization for web/document answers (needs API key — owner decision), WhatsApp/email confirmed-flow foundation.
