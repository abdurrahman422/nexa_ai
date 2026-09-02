# P3-A.6 Final Answer Synthesis Report

Date: 2026-06-12

Scope: Final answer synthesis and Dashboard source-card UX only. No unrelated product features were added.

## Summary

Dashboard chat now prioritizes a human-friendly final answer before raw search sources. Search/market responses still keep source transparency, but detailed source cards are hidden by default behind a `View sources` toggle.

## Files Changed

| File | Change |
|---|---|
| `backend/app/search/service.py` | Added snippet/value synthesis for related search results, including cautious live market summaries and conflicting-value handling. |
| `backend/app/chat/service.py` | Ensures non-exact search provider results are synthesized before returning chat response; adds compact `sources`, `show_search_results_by_default=false`, and `live_data_warning`. |
| `backend/app/search/__init__.py` | Exports `synthesize_related_answer`. |
| `backend/app/schemas/chat.py` | Added `sources`, `show_search_results_by_default`, and `live_data_warning` response fields. |
| `backend/tests/test_chat.py` | Added tests for synthesized gold-price answers, compact sources, collapsed detailed results, live-data warning, and conflicting snippets. |
| `frontend/src/lib/backendAssistantClient.ts` | Added new response fields to chat DTO. |
| `frontend/src/pages/dashboard/CommandCenterPage.tsx` | Shows answer first, compact source chips below, and hides detailed result cards behind `View sources`. |
| `frontend/src/styles/global.css` | Added small styling for the source toggle. |
| `frontend/scripts/dashboard-chat-contract-test.cjs` | Added contract checks for final answer first, hidden source cards, and `View sources` toggle. |

## Behavior

Search response layout is now:

1. Final synthesized assistant answer.
2. Short explanation or caution when needed.
3. Compact source/provider chips.
4. `View sources` button for detailed result cards.

For market/live queries:

- If exact answer exists, Nexa can show it with live-data warning.
- If snippets contain values, Nexa summarizes values and sources.
- If snippets conflict, Nexa says prices/rates vary by source and avoids claiming one exact value.
- If no exact value is found, Nexa still gives a useful summary from related sources when available.

## Tests Run

| Command | Result | Notes |
|---|---|---|
| Bundled Python `-m compileall app scripts tests` | Pass | Backend source compiles. |
| `cd backend; .\.venv\Scripts\python.exe -m pytest` | Blocked | `.venv` launcher still points to missing `C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe`. |
| `cd backend; .\.venv\Scripts\python.exe scripts\smoke_test_backend.py` | Blocked | Same broken `.venv` launcher issue. |
| `cd frontend; npm.cmd run test` | Pass | TypeScript and Dashboard contract checks passed. |
| `cd frontend; npm.cmd run build` | Pass after escalation | First sandbox run failed loading Vite config; rerun outside sandbox passed. |

Frontend contract checks included:

```text
PASS Dashboard shows final answer text first
PASS Dashboard hides source cards by default
PASS Dashboard has View sources toggle
PASS Dashboard renders source chips
```

## Manual Tests To Run After Backend Venv Fix

| Prompt | Expected |
|---|---|
| `today gold price Bangladesh` | Final answer first; compact sources; detailed cards hidden until `View sources`. |
| `python latest version` | Final answer first; provider/source chips visible. |
| `Bangladesh news today` | Final answer or summary first; source cards collapsed. |
| `ajker weather ki` | Weather remains Open-Meteo. |
| `india te koita baje` | Time remains local timezone database. |
| `delete system32` | Dangerous command blocked. |

## Remaining Limitation

Full backend pytest/smoke and live manual Dashboard testing are still blocked until the local backend `.venv` is recreated or repaired.
