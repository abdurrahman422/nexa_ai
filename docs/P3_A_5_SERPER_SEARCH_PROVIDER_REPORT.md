# P3-A.5 Serper Search Provider Report

Date: 2026-06-11

Scope: Added Serper.dev as the main optional Google-like search provider for Dashboard Chat. Did not implement WhatsApp/email, workflow automation, smart home/ESP32, packaging, arbitrary shell execution, or file write/delete/move/rename.

## Summary

Nexa AI now supports `NEXA_SEARCH_PROVIDER=serper` with `SERPER_API_KEY` for stronger Google-like search inside Dashboard chat. When configured, Serper is tried first for broad search queries, and Nexa falls back to the existing free providers if Serper is missing, unconfigured, or fails.

No Serper API key was hard-coded in source code, tests, docs, or reports.

## Files Changed

| File | Change |
|---|---|
| `backend/app/search/providers/serper.py` | New Serper.dev provider using `POST https://google.serper.dev/search` and `SERPER_API_KEY` from environment only. |
| `backend/app/search/providers/__init__.py` | Exported Serper provider. |
| `backend/app/search/models.py` | Added shared search result/answer dataclasses. |
| `backend/app/search/service.py` | Added `NEXA_SEARCH_PROVIDER=serper` selection and fallback to free providers. |
| `backend/app/search/__init__.py` | Updated exports for shared models. |
| `backend/.env.example` | Added placeholder-only Serper/search provider configuration and key safety warning. |
| `backend/tests/test_chat.py` | Added mocked Serper tests for provider selection, market search, answer box parsing, fallback, missing key, dangerous command, weather/time separation. |
| `docs/P3_A_5_SERPER_SEARCH_PROVIDER_REPORT.md` | This report. |

## Configuration

Add these to your backend environment or `.env` file:

```env
NEXA_SEARCH_PROVIDER=serper
SERPER_API_KEY=your_serper_api_key_here
```

Security rule:

- Never commit a real API key.
- The backend reads Serper only from `SERPER_API_KEY`.
- If the key is missing, Nexa does not crash; it falls back to free providers.

## Provider Behavior

When configured:

1. Serper.dev runs first for broad web/search/market/news/current factual queries.
2. If Serper returns an `answerBox` or `knowledgeGraph`, Nexa uses it as a higher-confidence answer.
3. If no exact answer exists, Nexa returns source cards from `organic`, `topStories`, `news`, or `places`.
4. If Serper fails or is missing, Nexa falls back to:
   - DuckDuckGo Instant Answer
   - Wikipedia Summary
   - Wikipedia Search

Weather and time do not use Serper:

- Weather stays on Open-Meteo.
- Current time stays on the local timezone database.

## Market/Current Query Rules

For queries such as:

- `today gold price Bangladesh`
- `latest bitcoin price`
- `dollar rate`
- `stock price`
- `Bangladesh news today`

Nexa marks live/current data carefully:

- Shows provider/source cards.
- Shows live-data warning chip.
- Uses exact value only when provider response gives one.
- Otherwise says related live sources were found but one exact value could not be verified.
- Never invents a price.

## Dashboard UI

No Dashboard route changes were needed in this phase because P3-A.4 already added:

- provider chips
- source cards
- live-data warning chips
- no redirect to Web Search page
- no browser tab opens for normal answers

Serper responses use that same response shape, so results appear inside Dashboard chat.

## Tests Run

| Command | Result | Notes |
|---|---|---|
| Bundled Python `-m compileall app scripts tests` | Pass | Backend source compiles. |
| `cd backend; .\.venv\Scripts\python.exe -m pytest` | Blocked | `.venv` launcher still points to missing `C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe`. |
| `cd backend; .\.venv\Scripts\python.exe scripts\smoke_test_backend.py` | Blocked | Same broken `.venv` launcher issue. |
| `cd frontend; npm.cmd run test` | Pass | TypeScript and Dashboard contract checks passed. |
| `cd frontend; npm.cmd run build` | Pass after escalation | First sandbox run failed loading Vite config; rerun outside sandbox passed. |

## Mocked Backend Tests Added

| Test | Purpose |
|---|---|
| Serper selected when env vars exist | Verifies `NEXA_SEARCH_PROVIDER=serper` uses Serper first. |
| Market query returns source cards | Verifies `today gold price Bangladesh` can return Serper source-backed market results. |
| Python latest answer parsing | Verifies mocked Serper `answerBox` becomes a source-backed answer. |
| Serper failure fallback | Verifies free provider fallback. |
| Missing API key | Verifies no crash when `SERPER_API_KEY` is absent. |
| Weather/time separation | Verifies weather/time do not use Serper. |

## Manual Dashboard Tests

After fixing backend `.venv` and adding your real key locally, run:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
$env:NEXA_SEARCH_PROVIDER="serper"
$env:SERPER_API_KEY="your_serper_api_key_here"
python run_backend.py
```

Then run the frontend:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\frontend"
npm.cmd run web:dev
```

Manual prompts:

| Prompt | Expected |
|---|---|
| `today gold price Bangladesh` | Serper-backed answer or related live source cards inside Dashboard chat. |
| `google theke search kore bolo today gold price Bangladesh` | Cleaned query, Dashboard answer/source cards. |
| `python latest version` | Source-backed Dashboard answer. |
| `Bangladesh news today` | Dashboard answer/source cards. |
| `india te koita baje` | Local timezone answer, not Serper. |
| `ajker weather ki` | Open-Meteo weather answer, not Serper. |
| `delete system32` | Blocked, no execution. |

## Limitations

| Area | Limitation |
|---|---|
| Serper runtime | Requires user-provided API key in environment. |
| Backend tests | Could not execute in project `.venv` until the stale Python path is fixed. |
| Exact live data | Nexa only shows exact live values when provider response gives one clearly. |
| Dashboard manual test | Not completed here because backend `.venv` is still broken. |

## Next Step

Recreate/fix the backend `.venv`, set `NEXA_SEARCH_PROVIDER=serper` and `SERPER_API_KEY` locally, then run backend pytest/smoke and the manual Dashboard prompts.
