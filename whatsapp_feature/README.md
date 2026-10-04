# Nexa WhatsApp text-send reliability extension

This began as an add-only implementation of the text-send reliability follow-ups. The main app now binds its tested sender from `whatsapp_feature/` during the normal backend launch; the optional isolated launcher remains available for a separate runtime.

**Implementation and offline verification are complete; live WhatsApp login/sending/receipt verification is still pending.** No real messages were sent. DOM selectors must be checked against the user's actual WhatsApp Web UI before treating this as production-ready.

## What is implemented

| Follow-up | Implementation / remaining verification |
|---|---|
| End-to-end flow | Browser flow and original FastAPI/chat integration exercised with mocks; live account test pending |
| Login retry | QR window remains available in the backend process; repeat the same ID after login; nothing queues automatically |
| Page loading / Send | Explicit readiness waits; Send is located only after writing; stale elements are re-found during waits |
| Recipient verification | Exact full phone in the active conversation's contact-info drawer; no whole-page/suffix matching; ambiguous panels and groups blocked |
| Duplicate/crash protection | SQLite FULL synchronous boundary before clicking, cross-process lock, request/body fingerprint, fail-closed damaged/missing ledger |
| Result verification | New outgoing ID + exact text required; submitted, sent, delivered and explicit read evidence are distinguished |
| Failure tests | Offline tests cover failures before/after click, crash, concurrency, corrupt records, login and DOM evidence |
| UI/docs | This guide, status page and in-memory permission/skill descriptions; original files remain unchanged |

Additional safeguards: existing drafts are never overwritten; exact text is verified twice; multiline sending releases Shift; WebDriver special-key characters are rejected; long explicit sends do not go through draft-rewriting LLMs.

## Run using the existing desktop UI

Use the standard app flow. `backend/run_backend.py` activates the hardened sender automatically, and the Electron development launcher uses that backend entry point. Sending remains disabled until **WhatsApp Web Sending** is enabled in Settings. Its browser profile and durable ledger live under the configured backend data directory in `whatsapp-send-state`.

For a completely separate, isolated runtime, the optional launcher remains available. From `C:\Users\User\Desktop\idp`:

```powershell
.\whatsapp_feature\.venv\Scripts\python.exe -B -m whatsapp_feature.run_backend
```

Then start the frontend normally in another terminal (`npm.cmd run dev` from `frontend`). The existing Electron shell reuses an already-running backend on port 8000. If the original backend is running, stop it yourself before launching the extension. This new launcher does not kill or replace running processes. Do not run two backends on the same port.

The optional launcher keeps its own backend data and does not import existing contacts or accounts. The normal app launch uses the existing backend data directory instead. The packaged backend includes the adapter modules; live WhatsApp browser behavior still depends on the current WhatsApp Web UI.

The new backend launcher writes its runtime data only under `whatsapp_feature/runtime/`. Its `.env`, contacts, permissions, chat memory, reminders, model path and WhatsApp profile are separate. Old accounts, contact records and API keys are **not automatically imported**. This prevents new use of the extension from writing to the old backend's files. Sending defaults to disabled; enable **WhatsApp Web Sending** in Security Center and use a direct phone number or save an exact contact in this isolated runtime.

Example command shape (replace the recipient only when you intend a real send):

```text
Send a WhatsApp message to <phone number> saying <your exact message>
WhatsApp e <contact name> ke message pathao: <your exact message>
```

Bangla explicit send syntax is also supported. Unsupported or ambiguous command forms do not gain extra send authority. Draft commands retain their draft behavior. The CLI accepts international numbers; the original chat contact resolver is still Bangladesh-focused.

The existing chat UI uses `submitted` for executed actions. The response text and new ledger retain the richer acknowledgement result. The extension guide is at `http://127.0.0.1:8000/whatsapp-extension`; health is `/api/whatsapp-extension/health`.

## Standalone CLI

No browser or messages:

```powershell
.\whatsapp_feature\.venv\Scripts\python.exe -B -m whatsapp_feature.main doctor
.\whatsapp_feature\.venv\Scripts\python.exe -B -m whatsapp_feature.main draft --phone 01712345678 --text "Draft example only"
```

Login-only (opens a visible browser; no message queued):

```powershell
.\whatsapp_feature\.venv\Scripts\python.exe -B -m whatsapp_feature.main connect
```

Real sending requires all of `send`, an exact phone number, text, a stable request ID and `--allow-send`. Do not run this placeholder command unchanged:

```powershell
.\whatsapp_feature\.venv\Scripts\python.exe -B -m whatsapp_feature.main send --phone "<recipient>" --text "<approved message>" --request-id "approved-test-001" --allow-send
.\whatsapp_feature\.venv\Scripts\python.exe -B -m whatsapp_feature.main status approved-test-001
```

CLI state defaults to `whatsapp_feature/state/`; the backend launcher uses `whatsapp_feature/runtime/whatsapp-state/`. To use the backend's same session/ledger from the CLI, pass `--state-dir whatsapp_feature/runtime/whatsapp-state` **before** the subcommand. Do not use different state folders to retry an uncertain send: each folder has independent history. Old sender history is also separate.

For login and failures proven to occur before Send, repeat the same ID and same body. After `unknown`, `sending`, `submitted`, `sent`, `delivered` or `read`, the same ID will not click Send again. Do not delete/reset state or invent another ID to bypass an uncertain outcome. Intentionally sending the same message again requires a distinct explicit request ID; the old Dashboard may omit IDs and therefore identical commands can remain deduplicated. Use the CLI for that deliberate repeat.

If a draft is left in the composer after a failure, review/clear it manually before retrying. Chrome is closed after normal attempts; a login-required session is retained while the backend runs. The standalone CLI waits for Enter after QR login and exits without sending; rerun its explicit command afterward.

## Verification

```powershell
.\whatsapp_feature\.venv\Scripts\python.exe -B -m unittest discover -s whatsapp_feature/tests -v
```

Tests use temporary state, fake browser elements and FastAPI TestClient. They do not open Chrome, read WhatsApp history or send messages. `-B` avoids adding bytecode files to old source folders. The original application's entire test suite is not run because some tests write existing data.

The integrity baseline/report are local snapshots of the original development machine and are intentionally not committed. The initial preservation comparison is historical; the normal-app integration described above intentionally modifies project files.

The initial integrity inventory contains 34,902 readable original files. Two existing pytest-cache directories could not be read and are explicitly excluded from any preservation claim. `integrity_report.json` records the final comparison.

## Installation elsewhere

Create a fresh environment under this folder. Standalone CLI needs `requirements.txt`; the optional backend launcher additionally needs the original backend requirements:

```powershell
py -3.12 -m venv whatsapp_feature/.venv
.\whatsapp_feature\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

The development machine's original backend virtual environment could not be executed, so a new Python 3.12 environment was created here; the old environment was not repaired or modified. `requirements.lock.txt` records the versions installed for verification.

## Limits and live acceptance

- WhatsApp DOM selectors, localized labels, emojis and actual receipt behavior are not live-verified. Unknown layouts fail closed and require an adapter update.
- No group sending, attachments, incoming-message reading or auto-reply; those were explicitly excluded from this request.
- No automatic resend after an ambiguous click; this favors preventing duplicates over guaranteed delivery. It is not a mathematical exactly-once delivery guarantee.
- Read receipts may be unavailable. A double-check indicates delivered, not automatically read.
- The contact-info selector approach deliberately rejects ambiguous numbers. Do not interact with the dedicated browser during an explicit send.
- Runtime binding changes only this launched process, not installed source. Existing static frontend wording can remain; the new guide states the actual behavior.

Live acceptance requires the user's logged-in session and an explicitly approved recipient/message. Verify: QR retry, exact text in correct chat, observed acknowledgement, repeat-ID non-duplication, and no send from a draft command. Record actual results separately; offline tests are not evidence of real delivery.

Browser waits follow [Selenium's explicit-wait guidance](https://www.selenium.dev/documentation/webdriver/waits/). WhatsApp-specific selectors are implementation assumptions, not an official stable API.
