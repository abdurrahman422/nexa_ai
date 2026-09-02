# P3-A.4 Search Provider Upgrade Report

Date: 2026-06-11

Scope: P3-A.4 only. Improved Dashboard/chat search quality and provider structure. Did not implement WhatsApp/email, workflow automation, smart home/ESP32, packaging, arbitrary executable launching, or file write/delete/move/rename.

## Summary

Dashboard chat now has a stronger Google-like search provider layer while still staying inside the app UI. Normal answer/search prompts are handled by `POST /api/chat/message`; the Dashboard does not redirect to Web Search and does not open browser tabs for normal answers.

The default provider mode is free/no-key. Optional provider hooks were added for later API-key use.

## Files Changed

| File | Change |
|---|---|
| `backend/app/search/service.py` | Added search provider abstraction, query cleaning, free provider fallback, optional provider hooks, market/live-query handling, result confidence, and source snippets. |
| `backend/app/search/__init__.py` | Exported search service functions/types. |
| `backend/app/chat/service.py` | Chat web-search branch now uses the search provider abstraction and returns source cards, confidence, and live-data chips. |
| `backend/app/schemas/chat.py` | Added `confidence` on search results plus top-level `confidence` and `live_data` response fields. |
| `backend/tests/test_chat.py` | Added tests for market query snippets, query cleaning, provider fallback order, and no Google HTML scraping rule. |
| `frontend/src/lib/backendAssistantClient.ts` | Added typed `confidence` and `live_data` fields. |
| `frontend/scripts/dashboard-chat-contract-test.cjs` | Added contract checks for live-data chips and related-source rendering. |
| `docs/P3_A_4_SEARCH_PROVIDER_UPGRADE_REPORT.md` | This report. |

## Providers Added

| Provider | Mode | Requires Key | Notes |
|---|---|---:|---|
| DuckDuckGo Instant Answer | `free` | No | First answer attempt. Also uses related topics when available. |
| Wikipedia Summary | `free` | No | Good for factual/topic lookups. |
| Wikipedia Search | `free` | No | General fallback that returns title/snippet/source cards. |
| SearXNG | `searxng` | No, if you host/use an endpoint | Optional JSON endpoint via `NEXA_SEARXNG_URL`. |
| Google Custom Search | `google_cse` | Yes | Optional official API only; no Google HTML scraping. |
| Brave Search | `brave` | Yes | Optional official API. |
| SerpAPI | `serpapi` | Yes | Optional API provider. |

## Environment Configuration

Default free mode:

```powershell
$env:NEXA_SEARCH_PROVIDER="free"
```

Optional SearXNG:

```powershell
$env:NEXA_SEARCH_PROVIDER="searxng"
$env:NEXA_SEARXNG_URL="https://your-searxng.example"
```

Optional Google Custom Search:

```powershell
$env:NEXA_SEARCH_PROVIDER="google_cse"
$env:NEXA_GOOGLE_CSE_KEY="your_key"
$env:NEXA_GOOGLE_CSE_ID="your_search_engine_id"
```

Optional Brave Search:

```powershell
$env:NEXA_SEARCH_PROVIDER="brave"
$env:NEXA_BRAVE_SEARCH_KEY="your_key"
```

Optional SerpAPI:

```powershell
$env:NEXA_SEARCH_PROVIDER="serpapi"
$env:NEXA_SERPAPI_KEY="your_key"
```

If an optional provider fails or is not configured, the backend falls back to the free providers.

## Market/Live Query Behavior

Detected live/market query terms include:

- gold price
- silver price
- dollar rate
- exchange rate
- stock price
- bitcoin price
- fuel price

For these queries, chat responses include:

- `intent: market_search`
- `live_data: true`
- confidence value
- `Live data may vary` chip
- source cards when related snippets are available

If an exact value cannot be verified, Nexa now says:

```text
I found related sources but could not verify one exact live price.
```

It should not fall back to a bare “No reliable result” when provider snippets exist.

## Query Cleaning

Improved cleaning handles:

- `google theke search kore bolo`
- `search kore bolo`
- `google e khuje bolo`
- `khujte paro`
- `etar answer ki`
- `ajker`
- `Bangladesh e`

Example:

```text
google theke search kore bolo today gold price Bangladesh
```

Cleaned query:

```text
today gold price bangladesh
```

## Dashboard UI

Dashboard chat now receives richer search response data:

- multiple source cards
- provider chips
- confidence chips
- live-data warning chip
- source URLs inside the app

The Dashboard remains the primary answer surface. It does not redirect normal questions to Web Search and does not open browser tabs for normal answers.

## Tests Run

| Command | Result | Notes |
|---|---|---|
| Bundled Python `-m compileall app scripts tests` | Pass | Backend source compiles. |
| `cd backend; .\.venv\Scripts\python.exe -m pytest` | Blocked | `.venv` launcher still points to missing `C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe`. |
| `cd backend; .\.venv\Scripts\python.exe scripts\smoke_test_backend.py` | Blocked | Same broken `.venv` launcher issue. |
| `cd frontend; npm.cmd run test` | Pass | TypeScript check plus Dashboard contract tests. |
| `cd frontend; npm.cmd run build` | Pass after escalation | First sandbox run failed loading Vite config; rerun outside sandbox passed. |

Frontend contract test output included:

```text
PASS Dashboard renders search result sources
PASS Dashboard renders live-data warning chip
PASS Dashboard handles no exact answer but related sources found
PASS Dashboard does not redirect Web questions to Web Search page
```

## Manual Dashboard Tests

After fixing the backend `.venv`, start backend and frontend, then test:

| Prompt | Expected |
|---|---|
| `today gold price Bangladesh` | Answer inside Dashboard; exact value only if verified; otherwise related source cards and live-data warning. |
| `google theke search kore bolo today gold price Bangladesh` | Cleaned search query; Dashboard answer/source cards. |
| `python latest version` | Dashboard answer/source cards. |
| `Bangladesh news today` | Dashboard answer/source cards or clear provider limitation. |
| `india te koita baje` | Current India time from local timezone database. |
| `ajker weather ki` | Open-Meteo weather answer. |
| `delete system32` | Blocked in Dashboard; no execution. |

## Limitations

| Area | Current Limitation |
|---|---|
| Free search | No-key providers are weaker than real search APIs for live prices/news. |
| Exact live prices | Exact market values are only shown when a provider returns a reliable value. Otherwise Nexa shows related sources and warning. |
| Optional APIs | Google CSE/Brave/SerpAPI require user-provided keys later. |
| Backend runtime verification | Blocked by broken `.venv` in this shell. |

## Next Step

Recreate the backend `.venv`, then run:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
python -m pytest
python scripts\smoke_test_backend.py
```

Then manually test the Dashboard prompts above before starting another P3 feature phase.
