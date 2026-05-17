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

