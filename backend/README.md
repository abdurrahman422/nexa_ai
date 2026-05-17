# Nexa AI Backend

## 1. Backend Purpose

The backend will provide the local automation and business-logic layer for Nexa AI. It will interpret commands, enforce safety rules, manage local data, coordinate automation modules, expose APIs to the desktop UI, and support future integrations such as smart-home control.

## 2. Planned Stack

- Python 3.11+
- FastAPI
- Uvicorn
- SQLite
- `rapidfuzz`
- PyMuPDF
- `requests`
- `feedparser`
- BeautifulSoup
- `pyttsx3`
- SpeechRecognition

## 3. Folder Responsibilities

- `app/api/` — future FastAPI routers and HTTP-facing API structure
- `app/core/` — configuration, logging, startup, and shared backend foundations
- `app/database/` — SQLite access, models, migrations, and repositories
- `app/command_engine/` — normalization, fuzzy matching, intent detection, slot extraction, and execution planning
- `app/automation/` — desktop automation capabilities and adapters
- `app/voice/` — future speech-to-text and text-to-speech support
- `app/files/` — file search and organization logic
- `app/web/` — free-source web intelligence integrations
- `app/pdf/` — PDF and document processing
- `app/scheduler/` — reminders, tasks, and scheduled events
- `app/contacts/` — contacts and message-draft support
- `app/security/` — permission checks, confirmations, and audit logging
- `app/smart_home/` — future ESP32 smart-home integrations
- `app/events/` — WebSocket events and internal event dispatch
- `app/utils/` — shared backend helper utilities
- `tests/` — future backend test suite
- `scripts/` — future backend setup, maintenance, and utility scripts
- `data/` — local runtime data such as future SQLite files
- `logs/` — backend log output

## 4. Backend Architecture Rules

- Routers should only handle the HTTP layer.
- Services should contain business logic.
- Command engine must process raw user text before any execution.
- Sensitive actions must pass through security checks.
- No paid APIs in MVP.
- No heavy local AI models in MVP.
- Keep modules small.

## 5. Performance Rules

- Avoid unnecessary background polling.
- Use lightweight SQLite.
- Defer expensive tasks.
- Optimize for low-end Windows laptops.

## 6. Note

This phase creates only the backend folder skeleton. Actual FastAPI implementation will be added in later phases.


## Phase 03.1 Backend Setup

Phase 03.1 created the basic Python backend setup files for Nexa AI.

### Created Files

- `backend/requirements.txt`
- `backend/requirements-dev.txt`
- `backend/.env.example`
- `backend/run_backend.py`
- `backend/app/__init__.py`

### Current Backend Dependencies

The Phase 03 backend foundation currently includes only lightweight core dependencies:

- `fastapi`
- `uvicorn[standard]`
- `python-dotenv`
- `pydantic`

Development/testing dependencies:

- `pytest`
- `httpx`

### Important Notes

- The FastAPI application entrypoint will be created in Phase 03.2.
- The `/api/health` endpoint will be created in Phase 03.2.
- No voice system has been implemented yet.
- No automation features have been implemented yet.
- No database implementation has been added yet.
- No command engine has been implemented yet.
- No heavy AI models or paid APIs have been added.

This step only prepares the backend setup foundation.

## Phase 03.3 Backend Config System

Phase 03.3 added the backend configuration foundation.

### Added

- `backend/app/core/config.py`
- `Settings`
- `get_settings()`
- environment variable loading
- feature flag defaults
- root endpoint now includes environment information
- `/api/health` now includes environment information and phase `03.3`

### Current Scope

- No database implementation yet
- No WebSocket implementation yet
- No voice system yet
- No automation system yet
- No command engine yet
- No paid APIs or heavy AI models added
