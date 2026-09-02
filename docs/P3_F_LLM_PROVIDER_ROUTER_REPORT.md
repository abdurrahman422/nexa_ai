# P3-F Hosted LLM Provider Router Report

## Summary

Implemented an opt-in hosted LLM provider router for Nexa AI without replacing existing local/tool/search behavior. The router is only used for tasks that need deeper generation or reasoning, while greetings, casual chat, weather, time, YouTube, WhatsApp open actions, app launch, contact commands, and dangerous-command decisions stay local/tool-first.

## Provider Router

Fallback order:

1. Gemini
2. Groq
3. OpenRouter
4. Cloudflare Workers AI
5. Mistral
6. Cerebras

The router is controlled by environment variables and does not hard-code or return API keys. Missing keys or provider failures return `None` and safely fall through to the next provider.

## LLM Usage Policy

| Request type | Route |
| --- | --- |
| Greetings / `how are you` / casual chat | Local assistant |
| Weather | Open-Meteo |
| Current time | Local timezone database |
| Live/current/news/gold price | Search first; optional LLM polish only after source data |
| YouTube open/search | Safe YouTube skill |
| WhatsApp open | Safe WhatsApp skill |
| WhatsApp formal/friendly draft composition | Optional LLM draft text, still draft-only |
| App launcher | Safe app/tool path |
| Dangerous command | Blocked before LLM |
| Coding, long writing, rewrite, complex explanation | Hosted LLM if enabled/configured |

## Files Changed

| File | Changes |
| --- | --- |
| `backend/app/llm/schemas.py` | Added LLM request/response/routing dataclasses. |
| `backend/app/llm/policy.py` | Added local/search/tool/LLM decision policy. |
| `backend/app/llm/router.py` | Added opt-in provider fallback router and safe system prompt wrapper. |
| `backend/app/llm/providers/*.py` | Added Gemini, Groq, OpenRouter, Cloudflare, Mistral, and Cerebras provider clients. |
| `backend/app/schemas/chat.py` | Added `llm_used`, `llm_provider`, `fallback_used`, and `source_type` metadata. |
| `backend/app/chat/service.py` | Integrated LLM route for appropriate requests, optional search-result polishing, and WhatsApp draft composition without auto-send. |
| `backend/.env.example` | Added placeholder-only hosted LLM configuration. |
| `backend/tests/test_chat.py` | Added mocked router/policy tests. |
| `frontend/src/lib/backendAssistantClient.ts` | Added LLM metadata fields to chat DTO. |
| `frontend/src/pages/dashboard/CommandCenterPage.tsx` | Shows LLM provider chip from LLM metadata while preserving clean local casual replies. |
| `frontend/scripts/dashboard-chat-contract-test.cjs` | Added Dashboard LLM chip contract check. |

## Environment Configuration

Added to `backend/.env.example` only:

```env
NEXA_LLM_ROUTER_ENABLED=true
NEXA_LLM_PRIMARY=gemini

GEMINI_API_KEY=
GEMINI_MODEL=

GROQ_API_KEY=
GROQ_MODEL=

OPENROUTER_API_KEY=
OPENROUTER_MODEL=

CLOUDFLARE_ACCOUNT_ID=
CLOUDFLARE_API_TOKEN=
CLOUDFLARE_MODEL=

MISTRAL_API_KEY=
MISTRAL_MODEL=

CEREBRAS_API_KEY=
CEREBRAS_MODEL=

NEXA_LLM_TIMEOUT_SECONDS=20
NEXA_LLM_MAX_RETRIES=2
```

Security note: real API keys must stay in local `.env` only and must not be committed.

## Tests Added

| Test | Coverage |
| --- | --- |
| Provider fallback | Gemini missing/failing falls back to Groq. |
| Missing keys | No configured keys returns safely without crash. |
| Weather no LLM | Weather route does not call LLM. |
| Casual no LLM | `how are you` does not call LLM. |
| Coding request | Coding prompt can use LLM when enabled. |
| WhatsApp draft | Formal/friendly draft may use LLM text but still never auto-sends. |
| Live gold price | Search is called before optional LLM polishing. |
| Dangerous command | Dangerous command is blocked before LLM. |

## Verification Results

| Command | Result | Notes |
| --- | --- | --- |
| Backend `py_compile` with bundled Python | Passed | New LLM package, chat schema/service, and tests compile. |
| `cd backend; .\.venv\Scripts\python.exe -m pytest` | Blocked in this Codex shell | `.venv` launcher points to missing `C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe`. |
| `cd backend; .\.venv\Scripts\python.exe scripts\smoke_test_backend.py` | Blocked in this Codex shell | Same stale `.venv` launcher path. |
| `cd frontend; npm.cmd run test` | Passed | TypeScript and Dashboard contract tests passed. |
| `cd frontend; npm.cmd run build` | Passed after escalation | First sandbox run hit Vite config access denial; escalated rerun passed. |

## Remaining Limitations

- Hosted providers are only used when `NEXA_LLM_ROUTER_ENABLED=true` and provider credentials are configured.
- Live/current data still depends on search providers first; the LLM is not allowed to invent prices, news, or weather.
- `NEXA_LLM_MAX_RETRIES` is documented for configuration compatibility; current provider fallback uses provider-level attempts plus safe fallback, not repeated retry loops per provider.
- Backend pytest/smoke must be run from a repaired local backend environment because this Codex shell cannot launch the current `.venv`.

## Manual Test Table

| Prompt | Expected |
| --- | --- |
| `hi` | Local greeting, no LLM chip. |
| `how are you` | Local casual reply, no LLM chip/source cards. |
| `write code for a React button` | LLM answer if router enabled and provider key exists; provider chip visible. |
| `explain recursion simply` | LLM answer if configured. |
| `today gold price Bangladesh` | Search first; optional LLM polish only after sources. |
| `ajker weather ki` | Open-Meteo, no LLM. |
| `india te koita baje` | Local timezone answer, no LLM. |
| `youtube e python tutorial search koro` | YouTube skill, no LLM. |
| `whatsapp e Rahim ke bolo formal friendly ami pore call korbo` | Optional LLM draft composition, WhatsApp draft only, no Send click. |
| `delete system32` | Blocked before LLM. |

## Next Step

Repair or recreate the backend `.venv` launcher, then run:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
python -m pytest
python scripts\smoke_test_backend.py
```

Then configure one hosted provider key locally in `backend/.env` and manually test the Dashboard with one coding prompt plus one live-data prompt.
