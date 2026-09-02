# P3-A.3 Universal Chat And Quick Launch Report

Date: 2026-06-11

Scope: P3-A.3 only. Implemented universal Dashboard/chat search behavior and Trusted Quick Launch Mode. Did not implement WhatsApp/email, workflow automation, smart home/ESP32, packaging, arbitrary shell/app execution, or file write/delete/move/rename.

## Summary

Nexa Dashboard chat now behaves more like a ChatGPT + Google-style answer box inside the app UI:

- Normal questions go to `POST /api/chat/message`.
- Weather stays on Open-Meteo.
- Current time questions are answered from Python timezone data.
- Bangla/Banglish search phrases are cleaned before lookup.
- Translation/explanation prompts are handled locally when possible.
- General questions fall back to safe public providers instead of only DuckDuckGo instant answers.
- Source/provider chips and search result snippets are available to the Dashboard.
- Safe installed app launch can be easier through `Trusted Quick Launch Mode`, default OFF.

## Files Changed

| File | Change |
|---|---|
| `backend/app/chat/service.py` | Reworked chat router for weather, current time, translation/explanation, universal web fallback, app launch requests, dangerous blocking, and Trusted Quick Launch Mode. |
| `backend/app/schemas/chat.py` | Added search result and action status fields to chat responses. |
| `backend/app/schemas/__init__.py` | Exported new chat schema types. |
| `backend/app/permissions/store.py` | Added `trusted_quick_launch`, default OFF. |
| `backend/app/actions/app_whitelist.py` | Expanded safe installed-app whitelist and alias matching for calculator/notepad/paint/chrome/vscode/word/excel/file explorer; kept dangerous/system targets blocked. |
| `backend/tests/test_chat.py` | Added/updated tests for universal web query, query cleaning, India time intent, translation intent, dangerous blocking, quick launch permission behavior, unknown app blocking, and weather. |
| `frontend/src/lib/backendAssistantClient.ts` | Added typed `search_results` and `action` fields for chat responses. |
| `frontend/src/pages/dashboard/CommandCenterPage.tsx` | Dashboard renders search result sources and app launch status from chat responses; app/website previews still confirm when needed. |
| `frontend/src/pages/settings/SettingsPageV2.tsx` | Added Trusted Quick Launch Mode toggle and quick-toggle entry. |
| `frontend/src/styles/global.css` | Added Dashboard search result styling. |
| `frontend/scripts/dashboard-chat-contract-test.cjs` | Added contract checks for source chips, search result rendering, app launch status, and no Web Search redirect. |

## Universal Chat Router

| Intent | Status | Notes |
|---|---|---|
| Weather | Implemented | Uses Open-Meteo, Dhaka default, source chips. |
| Current time | Implemented | Supports India/Kolkata and Bangladesh/Dhaka via `zoneinfo`; source chip is Local timezone database. |
| Translation/explanation | Implemented | Local simple Bangla translation/explanation helper first. |
| General web search | Implemented | Cleans Bangla/Banglish search phrases and uses safe providers. |
| Software/latest/news/price queries | Implemented as safe web search | No Google scraping; returns safe answer or clear unavailable state with sources. |
| App open request | Implemented | Safe installed app whitelist; Trusted Quick Launch controls auto-open. |
| Dangerous command | Implemented | Blocked and audited. |
| Unknown app | Implemented | Returns “I could not find that installed app”; no execution. |

## Search Providers

Current no-key providers:

| Provider | Use |
|---|---|
| DuckDuckGo Instant Answer | First safe answer attempt. |
| Wikipedia summary/search | General fallback with title/snippet/source URL. |
| Open-Meteo | Weather. |
| Local timezone database | Current time. |
| Local translation helper | Simple translation/explanation. |

Provider abstraction is now cleaner in `backend/app/chat/service.py`, so future Google Custom Search, Brave, Tavily, or SerpAPI can be added behind the same chat response shape if an API key is provided later. No paid API is required for this MVP.

## Trusted Quick Launch Mode

Default: **OFF**

When OFF:

- `calculator open koro` returns an app-launch preview requiring confirmation.
- Dashboard shows an inline confirmation card.

When ON:

- Recognized safe installed apps can open without confirmation through the existing safe backend app executor.
- Every attempt is audited.
- Unknown apps do not execute.
- Dangerous/system commands remain blocked.

Never auto-run targets:

- `cmd`
- `powershell`
- registry editor
- system32 operations
- format/delete/shutdown scripts
- arbitrary shell command
- unknown executable paths
- file delete/move/rename/write operations

Website launches remain confirmation-required; Trusted Quick Launch Mode is limited to safe installed apps.

## Expected Manual Dashboard Results

| Prompt | Expected Result |
|---|---|
| `today gold price Bangladesh` | Dashboard chat answer from safe web fallback or clear unavailable state with source chips. |
| `python latest version` | Dashboard chat answer from safe web/search fallback with source chips. |
| `ei sentence er Bangla ki: I am working on my project` | Local Bangla translation in Dashboard chat. |
| `india te koita baje` | Current India time/date/timezone in Dashboard chat. |
| `ajker weather ki` | Open-Meteo Dhaka weather in Dashboard chat. |
| `calculator open koro` | Confirmation when Trusted Quick Launch is OFF; auto-open only when ON. |
| `chrome open koro` | Confirmation when Trusted Quick Launch is OFF; auto-open only when ON if installed/available. |
| `delete system32` | Blocked message in Dashboard chat; no execution. |

## Tests Run

| Command | Result | Notes |
|---|---|---|
| Bundled Python `-m compileall app scripts tests` | Pass | Backend source bytecode-compiles. |
| `cd backend; .\.venv\Scripts\python.exe -m pytest` | Blocked | Local `.venv` launcher still points to missing `C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe`. |
| `cd backend; .\.venv\Scripts\python.exe scripts\smoke_test_backend.py` | Blocked | Same broken `.venv` launcher issue. |
| `cd frontend; npm.cmd run test` | Pass | TypeScript check plus Dashboard chat contract test. |
| `cd frontend; npm.cmd run build` | Pass after escalation | First sandbox run failed loading Vite config; rerun outside sandbox passed. |

Frontend contract test output:

```text
PASS Dashboard imports chat endpoint client
PASS Dashboard sends typed input to chat endpoint
PASS Voice transcript uses the same chat pipeline
PASS Question flow does not show Command not recognized
PASS Action commands remain confirmation-gated
PASS Dashboard renders source chips
PASS Dashboard renders search result sources
PASS Dashboard renders app launch status
PASS Dashboard does not redirect Web questions to Web Search page
PASS Dangerous/backend blocked responses render in chat
```

## Remaining Limitations

| Area | Limitation | Next Step |
|---|---|---|
| Backend runtime | `.venv` is broken in this shell, so pytest/smoke could not execute. | Recreate `.venv`, install requirements, rerun backend pytest/smoke. |
| Live market/news precision | Free/no-key providers may not always return precise current prices/news. | Add optional API-key provider later behind the provider abstraction. |
| Translation | Local translation is simple, phrase/dictionary based. | Add optional local model or approved provider later. |
| App discovery | MVP uses safe whitelist plus OS command availability; it does not execute unknown discovered paths. | Add richer Start Menu indexing only if it preserves whitelist/safety rules. |
| Manual UI sign-off | Browser automation was not rerun for this report because backend runtime is blocked. | Manually test Dashboard after fixing `.venv`. |

## Exact Next Step

Fix the backend environment:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
deactivate
Rename-Item .venv .venv_broken
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest
python scripts\smoke_test_backend.py
```

Then run the frontend:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\frontend"
npm.cmd run web:dev
```

Open Dashboard and manually test the prompts listed above. Do not start P3 workflow/email/smart-home/packaging/file-write work until this manual runtime sign-off is complete.
