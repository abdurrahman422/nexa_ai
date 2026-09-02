# P3-C.3 WhatsApp Contact Mapping Report

Date: 2026-06-12

## Scope

Implemented local-only WhatsApp contact mapping for draft-only messaging.

No WhatsApp auto-send, private chat reading, hidden browser automation, credential scraping, arbitrary URLs, arbitrary shell execution, file write/delete/move/rename, smart home, packaging, or workflow automation was added.

## Files Changed

| File | Change |
| --- | --- |
| `backend/app/contacts/store.py` | Added local JSON contact store under `backend/data/whatsapp_contacts.json` with phone validation, timestamps, nickname support, save/list/get/delete. |
| `backend/app/contacts/__init__.py` | Exported contact store helpers. |
| `backend/app/schemas/contacts.py` | Added contact API schemas. |
| `backend/app/api/routes/contacts.py` | Added `/api/contacts` list/save/delete routes. |
| `backend/app/main.py` | Registered contacts router. |
| `backend/app/schemas/__init__.py` | Exported contact schemas. |
| `backend/app/chat/service.py` | Added contact save/query/delete command routing and WhatsApp draft lookup from local contacts. |
| `backend/tests/test_chat.py` | Added tests for save, retrieve, delete, malformed phone rejection, known contact draft, unknown contact, auto-send impossible, and dangerous command block. |
| `frontend/src/lib/backendAssistantClient.ts` | Added contacts API client types and functions. |
| `frontend/src/pages/settings/SettingsPageV2.tsx` | Added `Local WhatsApp Contacts` section with add/delete/list form. |
| `frontend/scripts/dashboard-chat-contract-test.cjs` | Added frontend contract check for the local WhatsApp contact form. |
| `docs/P3_C_3_WHATSAPP_CONTACT_MAPPING_REPORT.md` | Added this report. |

## Behavior

| Prompt | Result |
| --- | --- |
| `Rahim er number save koro 017xxxxxxxx` | Saves Rahim locally with normalized `88017...` number. |
| `Rahim ke WhatsApp contact hisebe save koro 017xxxxxxxx` | Saves Rahim as a local WhatsApp contact. |
| `Rahim er number ki` | Returns saved local WhatsApp number. |
| `Rahim er WhatsApp contact delete koro` | Deletes local contact mapping. |
| `whatsapp e Rahim ke bolo ami pore call korbo` | If Rahim exists, opens safe `https://wa.me/<phone>?text=<encoded>` draft URL when trusted WhatsApp draft auto-open is enabled. |
| `whatsapp e Unknown ke bolo hi` | Asks for phone number; does not guess or open anything. |
| `delete system32` | Blocked before contact/WhatsApp handling. |

## Storage

Storage is local-only JSON:

```text
backend/data/whatsapp_contacts.json
```

Each contact stores:

- `name`
- `phone_number`
- optional `nickname`
- `created_at`
- `updated_at`

No cloud sync was added.

## Safety

- WhatsApp auto-send remains impossible.
- Nexa never clicks the Send button.
- Nexa does not read private chats.
- Nexa does not scrape WhatsApp or bypass login.
- Unknown contacts are not guessed.
- Allowed WhatsApp URLs remain limited to `web.whatsapp.com` and safe `wa.me/<phone>?text=...` draft URLs.

## Commands Run

| Command | Result |
| --- | --- |
| Bundled Python `py_compile app/contacts/store.py app/api/routes/contacts.py app/schemas/contacts.py app/chat/service.py app/main.py tests/test_chat.py` | Passed. |
| `cd backend; .\.venv\Scripts\python.exe -m pytest` | Blocked in this Codex session. The venv launcher points to missing `C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe`. |
| `cd backend; .\.venv\Scripts\python.exe scripts\smoke_test_backend.py` | Blocked for the same venv launcher issue. |
| `cd frontend; npm.cmd run test` | Passed. |
| `cd frontend; npm.cmd run build` | Passed after rerunning outside the restricted sandbox. Initial sandbox run failed on Vite config path access. |

## Backend Verification Note

Full backend pytest and smoke tests could not run in this Codex session because `.venv\Scripts\python.exe` cannot launch:

```text
Unable to create process using '"C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe" -m pytest'
```

Run in the repaired backend environment:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
python -m pytest
python scripts\smoke_test_backend.py
```

## Manual Checklist

| Prompt | Expected |
| --- | --- |
| `Rahim er number save koro 017xxxxxxxx` | Contact saved locally. |
| `whatsapp e Rahim ke bolo ami pore call korbo` | WhatsApp draft opens for Rahim; user must manually press Send. |
| `whatsapp e Unknown ke bolo hi` | Nexa asks for phone number. |
| `delete system32` | Blocked. |
