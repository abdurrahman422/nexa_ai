# P4-A Core Architecture Refactor Report

Generated: 2026-06-13

## Summary

Implemented a merge-ready assistant architecture boundary while preserving the existing `/api/chat/message` DTO and behavior. The current chat service remains the compatibility implementation, but the API route now enters through `assistant.pipeline`, and new assistant, NLU, router, tool, safety, and memory modules provide stable extraction points for future merging with another desktop/web AI assistant project.

## New Architecture Map

| Layer | New Module(s) | Responsibility |
| --- | --- | --- |
| Assistant pipeline | `backend/app/assistant/pipeline.py`, `state.py`, `types.py`, `response_composer.py` | Pipeline entrypoint, request context, shared route/context types, persona/address composition. |
| NLU | `backend/app/nlu/normalizer.py`, `classifier.py`, `patterns.py`, `banglish.py` | Text normalization, compatibility intent classifier, central pattern groups, Banglish phrase normalization. |
| Router | `backend/app/router/task_router.py`, `route_policy.py` | Route facade and documented pipeline order. |
| Tools | `backend/app/tools/calculator.py`, `weather.py`, `time_tool.py`, `search_tool.py`, `youtube_tool.py`, `whatsapp_tool.py`, `app_launcher.py` | Tool adapters for local calculator, weather, time, search, YouTube URLs, WhatsApp draft URLs, and app launch. |
| Safety | `backend/app/safety/safety_router.py`, `dangerous_patterns.py` | Safety facade and dangerous command pattern boundary. |
| Memory | `backend/app/memory/context_store.py`, `pending_tasks.py` | Conversation context helpers and pending WhatsApp draft type. |
| API bridge | `backend/app/api/routes/chat.py` | `/api/chat/message` now calls `run_chat_pipeline(request)`. |

## Pipeline Order

1. Normalize input
2. Safety check
3. Load conversation context/pending task
4. Classify intent
5. Decide route
6. Execute tool/search/LLM/local answer
7. Compose human response
8. Save memory/context
9. Return frontend-safe DTO

## Files Created

| File |
| --- |
| `backend/app/assistant/__init__.py` |
| `backend/app/assistant/pipeline.py` |
| `backend/app/assistant/response_composer.py` |
| `backend/app/assistant/state.py` |
| `backend/app/assistant/types.py` |
| `backend/app/nlu/__init__.py` |
| `backend/app/nlu/banglish.py` |
| `backend/app/nlu/classifier.py` |
| `backend/app/nlu/normalizer.py` |
| `backend/app/nlu/patterns.py` |
| `backend/app/router/__init__.py` |
| `backend/app/router/route_policy.py` |
| `backend/app/router/task_router.py` |
| `backend/app/tools/__init__.py` |
| `backend/app/tools/app_launcher.py` |
| `backend/app/tools/calculator.py` |
| `backend/app/tools/search_tool.py` |
| `backend/app/tools/time_tool.py` |
| `backend/app/tools/weather.py` |
| `backend/app/tools/whatsapp_tool.py` |
| `backend/app/tools/youtube_tool.py` |
| `backend/app/safety/__init__.py` |
| `backend/app/safety/dangerous_patterns.py` |
| `backend/app/safety/safety_router.py` |
| `backend/app/memory/__init__.py` |
| `backend/app/memory/context_store.py` |
| `backend/app/memory/pending_tasks.py` |
| `backend/tests/test_architecture_boundaries.py` |

## Files Updated

| File | Change |
| --- | --- |
| `backend/app/api/routes/chat.py` | Routes chat requests through `assistant.pipeline.run_chat_pipeline`. |
| `backend/app/chat/service.py` | Uses `assistant.response_composer` and `tools.calculator`; preserves market fallback phrase; trusted app launch returns `auto_execute_safe`; retains existing feature compatibility. |
| `backend/tests/test_chat.py` | Existing P3 regression coverage retained and extended from prior reliability work. |

## Current Bug Fixes

| Bug | Fix |
| --- | --- |
| Market answer phrase broken by LLM/source composer | Low-confidence live market fallback now skips LLM rewrite and preserves `could not verify one exact live price`; `live_data_warning` remains tied to live data. |
| Trusted calculator quick launch returned `auto_execute_safe=false` | Trusted whitelisted app launch attempts now set `auto_execute_safe=true` when Trusted Quick Launch is enabled; confirmation remains when disabled. |
| Persona/action status mixed in chat service | `assistant.response_composer` now owns address labels and composed user-facing action text. |
| Intent/router logic lacked merge boundary | Added `assistant`, `nlu`, `router`, `tools`, `safety`, and `memory` package boundaries. |

## Safety Regression Coverage

- `delete system32` remains blocked.
- `format drive` remains blocked.
- `delete all files` remains blocked.
- shell/cmd/powershell style requests remain blocked.
- WhatsApp auto-send remains impossible.
- Local WhatsApp contact delete remains scoped to local contact mapping only.

## Verification Results

| Command | Result | Notes |
| --- | --- | --- |
| `python -m py_compile` over touched backend modules/tests | PASS | Used bundled Codex Python because the project `.venv` launcher is stale in this shell. |
| `cd backend; .\.venv\Scripts\python.exe -m pytest` | BLOCKED | `.venv` points to missing `C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe`. |
| `cd backend; .\.venv\Scripts\python.exe scripts\smoke_test_backend.py` | BLOCKED | Same stale `.venv` launcher issue. |
| `cd frontend; npm.cmd run test` | PASS | Typecheck and Dashboard contract tests passed. |
| `cd frontend; npm.cmd run build` | PASS | Initial sandbox run denied Vite config access; scoped build rerun passed. |

## Remaining Limitations

- Full backend pytest and smoke must be rerun in the user’s repaired local backend `.venv`.
- This P4-A pass creates modular boundaries and moves selected helpers behind them; deeper extraction of all chat service logic can happen incrementally in P4-B/P4-C.
- API compatibility is intentionally preserved, so no frontend DTO migration was done.

## Next Recommended Step

Run backend verification in the repaired local environment:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
python -m pytest
python scripts\smoke_test_backend.py
```

Then continue with an incremental P4-B extraction that moves one tool at a time out of `chat/service.py` behind the new `backend/app/tools/*` adapters.

