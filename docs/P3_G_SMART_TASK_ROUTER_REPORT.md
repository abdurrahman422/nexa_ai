# P3-G Smart Task Router Report

## Summary

Implemented the smart task router layer for Nexa AI. Chat routing now produces a structured decision before execution:

- `intent`
- `confidence`
- `route`
- `reason`
- `needs_action`
- `needs_llm`
- `needs_search`
- `needs_confirmation`

The router keeps safety first, avoids random web searches for normal conversation, sends live/current prompts to search first, sends coding/writing/math-generation prompts to the LLM router, and keeps WhatsApp draft-only.

## Files Changed

| File | Changes |
| --- | --- |
| `backend/app/chat/service.py` | Added `SmartTaskRoute`, `classify_task`, local calculator route, low-confidence clarification, route-debug gating, improved WhatsApp `sms dao` parsing, and dispatcher integration. |
| `backend/app/schemas/chat.py` | Added optional `route_debug` metadata. |
| `backend/tests/test_chat.py` | Added route coverage for local persona, weather, search-first, calculator, LLM, WhatsApp draft, and low-confidence clarification. |
| `docs/P3_G_SMART_TASK_ROUTER_REPORT.md` | This report. |

## Router Policy

| Priority | Route | Behavior |
| --- | --- | --- |
| 1 | Safety | Dangerous/system/file commands block before search, tools, or LLM. |
| 2 | Local contacts | Contact save/lookup/delete uses local storage. |
| 3 | Local calculator | Simple arithmetic such as `2 + 3 * 4` uses local solver. |
| 4 | Weather/time | Weather uses Open-Meteo; time uses local timezone database. |
| 5 | Translation | Short/simple translation uses local helper; long/ambiguous translation can route to LLM. |
| 6 | YouTube | Only explicit YouTube/yutub/ইউটিউব keyword routes to YouTube skill. |
| 7 | WhatsApp | Explicit WhatsApp or clear contact-message command routes to draft-only WhatsApp flow. |
| 8 | Local persona | Greetings, casual chat, project/support messages stay local. |
| 9 | Live/current/search | Latest/news/price/current/search prompts use search first; LLM may summarize after sources. |
| 10 | LLM | Coding, homepage/page generation, writing, report, formal message, complex explanation, and math explanation use hosted LLM router. |
| 11 | Low confidence | Ask clarification or use LLM if configured; no random web search. |

## Dashboard Behavior

| Response type | UI behavior |
| --- | --- |
| Local chat | Clean assistant bubble, no source/debug chips. |
| Search | Final answer first, source chips, detailed cards behind `View sources`. |
| LLM | Final answer with subtle provider chip. |
| Action | Done/action status or confirmation card depending on trusted settings. |
| WhatsApp | Draft/open status only; no auto-send or Send click. |
| Route debug | Only returned when `NEXA_DEBUG_TASK_ROUTER=true`; normal UI does not show it. |

## Test Coverage Added

| Test | Expected |
| --- | --- |
| `how are u` | Local casual reply; no search and no LLM. |
| Router debug flag | `route_debug` absent normally, present only when debug env is enabled. |
| `Bangladesh er weather ki` | Weather API/tool route, no LLM. |
| `python latest version` | Search-first route. |
| `2 + 3 * 4` | Local calculator route. |
| `amar jonno homepage banaw` | LLM route. |
| `whatsapp e amar boss ke sms dao...` | WhatsApp draft route, no Send click. |
| `how would that work` | Clarification, no random search. |

## Verification Results

| Command | Result | Notes |
| --- | --- | --- |
| Backend `py_compile` with bundled Python | Passed | `service.py`, `chat.py`, and `test_chat.py` compile. |
| `cd backend; .\.venv\Scripts\python.exe -m pytest` | Blocked in this Codex shell | `.venv` launcher still points to missing `C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe`. |
| `cd backend; .\.venv\Scripts\python.exe scripts\smoke_test_backend.py` | Blocked in this Codex shell | Same stale `.venv` launcher problem. |
| `cd frontend; npm.cmd run test` | Passed | TypeScript and Dashboard contract tests passed. |
| `cd frontend; npm.cmd run build` | Passed after escalation | First sandbox run hit Vite config access denial; escalated rerun passed. |

## Manual Examples

| Prompt | Expected route | Status |
| --- | --- | --- |
| `how are u` | Local persona | Implemented. |
| `Bangladesh er weather ki` | Weather API/tool | Implemented. |
| `today gold price Bangladesh` | Search first, optional LLM after sources | Implemented. |
| `whatsapp e amar boss ke sms dao kalke ami office e aste parbo na` | WhatsApp draft action; LLM composition only if tone requested/configured | Implemented draft-only route. |
| `amar jonno homepage banaw` | LLM | Implemented. |
| `python latest version` | Search first | Implemented. |
| `delete system32` | Blocked before anything else | Implemented. |

## Remaining Limitations

- Backend pytest/smoke could not be run from this Codex shell until the backend `.venv` launcher is recreated or fixed.
- The local calculator intentionally supports only simple numeric arithmetic.
- Low-confidence intent currently asks clarification when LLM is unavailable; a future pass can add an explicit LLM classifier prompt once backend pytest is green in the repaired environment.
- WhatsApp remains draft-only and never clicks Send.

## Next Step

Run backend verification from a repaired PowerShell environment:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
python -m pytest
python scripts\smoke_test_backend.py
```

Then manually test the Dashboard prompts in the table above with backend running.
