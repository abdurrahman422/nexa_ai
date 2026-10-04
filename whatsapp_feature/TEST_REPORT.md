# WhatsApp text-send verification

Date: 2026-09-28. Python 3.12, Windows. Tests run in the new isolated `whatsapp_feature/.venv`.

## Executed

`python -B -m unittest discover -s whatsapp_feature/tests -v`

**63 tests passed** in the final run:

- 27 browser-adapter tests: delayed loading, QR login, invalid-number dialog, exact contact-panel verification, numeric contact-name spoof, group rejection, composer protection, exact whitespace, Send timing, multiline key handling, outgoing-message identity and receipt parsing.
- 26 sender/ledger/CLI tests: permission default, input validation, same-ID login retry, failures on either side of the durable click boundary, duplicate results, restart, competing process lock, damaged/missing database, changed payload, disk write failures and draft isolation.
- 10 original FastAPI integration tests: backend health, optional extension entry point, isolated data/config paths, updated runtime descriptions, disabled sending, exact multiline body with LLM rewriting forbidden, draft/non-send handling and Bangla/Banglish parsing.

Browser operations and send results were mocked. The FastAPI integration used the real original app with temporary runtime data and a mocked sender. No Chrome window or WhatsApp account was opened; no message was sent. Original application files were imported with bytecode disabled.

Additional checks: CLI doctor and launcher help succeeded; `pip check` reported no broken requirements. The installed dependency versions are recorded in `requirements.lock.txt`. A Starlette/httpx deprecation warning appeared; it did not fail tests.

## Issues found and fixed during verification

- An initial test left a test-only SQLite connection open on Windows; the test now closes it explicitly.
- The original chat composer collapsed multiline text even when asked for an exact send. The new optional runtime adapter preserves text and prevents LLM rewriting for supported explicit send forms.
- Numeric contact display names must not bypass contact-info verification. The adapter now always checks the contact drawer.

## Not verified

- Real Chrome/WhatsApp Web selector compatibility, QR authentication, real text entry/clicks or recipient delivery.
- Live network/session-expiry failures and real sent/delivered/read indicators.
- Packaged Electron distribution or full frontend interaction. The original packaging is unchanged.
- Full regression suite of unrelated features, because some existing tests mutate original data.

The real-send acceptance test requires the user's account, exact recipient and approved text. It remains pending. Test success must not be described as proof of live delivery.

## Preservation

The final comparison covers **34,902 readable original files: 0 modified, 0 missing, 0 added outside this feature folder**. Existing `.pytest_cache` and `backend/.pytest_cache` could not be read both before and after. See `integrity_report.json`; unreadable paths are explicitly reported, not assumed unchanged.
