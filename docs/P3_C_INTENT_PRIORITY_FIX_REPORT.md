# P3-C Intent Priority Fix Report

Date: 2026-06-12

## Scope

Fixed the reported P3-C intent priority regressions only.

No new features, hidden browser automation, arbitrary shell execution, or WhatsApp auto-send behavior were added.

## Files Changed

| File | Change |
| --- | --- |
| `backend/app/chat/service.py` | Reordered intent detection so dangerous commands remain first, weather/time/translation route before casual fallback, YouTube/WhatsApp route before generic actions, and general search phrases route to web search. Added missing translation markers such as `English ki`, `er Bangla`, and `er English`. |
| `backend/tests/test_chat.py` | Updated `hello` expectation from old `normal_chat` to new P3-B `greeting` intent. |
| `docs/P3_C_INTENT_PRIORITY_FIX_REPORT.md` | Added this report. |

## Issues Fixed

| Failure | Cause | Fix |
| --- | --- | --- |
| `test_chat_endpoint_works` expected `normal_chat`, got `greeting` | P3-B intentionally changed greetings to a dedicated greeting intent. | Updated test expectation to `greeting`; greeting behavior was not reverted. |
| `google theke search kore bolo python latest version` returned `preview_only` | Search-style Google phrasing could fall into action-style handling instead of web search in the current routing. | Added explicit search-request detection before generic app/website action preview. |
| `ei sentence er Bangla ki: I am working on my project` returned `casual_chat` | Casual project phrase detection ran before translation detection. | Translation detection now runs before casual/project fallback, with expanded translation markers. |

## Final Intent Priority

1. Dangerous/system command block
2. Weather
3. Current time
4. Translation/explanation
5. YouTube skill when clearly mentioning YouTube
6. WhatsApp skill when clearly mentioning WhatsApp
7. General search request
8. Greetings/thanks/capabilities/frustration/casual chat
9. Generic app/website action preview only for explicit open/launch/start style commands
10. Web search/question fallback

## Safety Status

- Dangerous commands still block first.
- WhatsApp draft flow still requires confirmation.
- WhatsApp auto-send remains impossible.
- No private chat reading was added.
- No Google HTML scraping was added.
- No arbitrary shell execution was added.

## Commands Run

| Command | Result |
| --- | --- |
| Bundled Python `py_compile app/chat/service.py tests/test_chat.py` | Passed. |
| `cd backend; .\.venv\Scripts\python.exe -m pytest` | Blocked in this Codex session. The venv launcher points to missing `C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe`. |
| `cd backend; .\.venv\Scripts\python.exe scripts\smoke_test_backend.py` | Blocked for the same venv launcher issue. |
| `cd frontend; npm.cmd run test` | Passed. |
| `cd frontend; npm.cmd run build` | Passed after rerunning outside the restricted sandbox. Initial sandbox run failed on Vite config path access. |

## Backend Verification Note

Full backend pytest could not be executed in this Codex session because `.venv\Scripts\python.exe` cannot launch:

```text
Unable to create process using '"C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe" -m pytest'
```

Run this in the repaired backend environment:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
python -m pytest
python scripts\smoke_test_backend.py
```

Expected result from the user-reported test suite after this fix: `38 passed`.

## Manual Dashboard Checks

| Prompt | Expected |
| --- | --- |
| `hello` | Friendly greeting. |
| `google theke search kore bolo python latest version` | Final web/search answer, not action preview. |
| `ei sentence er Bangla ki: I am working on my project` | Translation answer. |
| `youtube e python tutorial search koro` | YouTube safe search/open action. |
| `whatsapp e Rahim ke bolo ami pore call korbo` | WhatsApp draft confirmation; no auto-send. |
| `delete system32` | Blocked. |
