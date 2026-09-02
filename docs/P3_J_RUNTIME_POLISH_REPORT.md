# P3-J Runtime Polish Report

Generated: 2026-06-13 16:18 +06:00

## Summary

Implemented scoped runtime polish for WhatsApp draft opening, Banglish code-generation routing, trusted app open behavior tests, and cleaner Dashboard metadata. No hidden WhatsApp send, chat reading, credential scraping, arbitrary shell execution, file write/delete/move/rename, or unrelated product features were added.

## Files Changed

| File | Change |
| --- | --- |
| `backend/app/actions/website.py` | Added strict whitelist validation for `whatsapp://send`, `https://web.whatsapp.com/send`, and `https://wa.me/...` draft URLs. |
| `backend/app/schemas/chat.py` | Added `whatsapp_draft_open_target` request field. |
| `backend/app/chat/service.py` | Added WhatsApp draft target selection/fallback, cleaner trusted action chips, Banglish generation phrase routing, and LLM setup response when no provider is configured. |
| `backend/tests/test_chat.py` | Added backend coverage for WhatsApp target preferences, LLM setup routing, and trusted calculator open behavior. |
| `frontend/src/lib/backendAssistantClient.ts` | Sends WhatsApp draft open target preference to `/api/chat/message`. |
| `frontend/src/pages/dashboard/CommandCenterPage.tsx` | Sends Dashboard preference and hides technical/debug chips in normal mode. |
| `frontend/src/pages/settings/SettingsPageV2.tsx` | Added `WhatsApp Draft Open Target` setting with Auto/App/Web/wa.me options. |
| `frontend/scripts/dashboard-chat-contract-test.cjs` | Added frontend contract checks for the new setting, preference wiring, and clean chip behavior. |
| `docs/P3_J_RUNTIME_POLISH_REPORT.md` | Added this report. |

## Behavior Implemented

| Area | Result |
| --- | --- |
| WhatsApp draft target | `Auto` tries `whatsapp://send?...`, then `wa.me`, then WhatsApp Web fallback. |
| WhatsApp App target | Uses strict `whatsapp://send?phone=<digits>&text=<encoded>` only. |
| WhatsApp Web target | Uses strict `https://web.whatsapp.com/send?phone=<digits>&text=<encoded>` only. |
| wa.me target | Existing `https://wa.me/<digits>?text=<encoded>` still works. |
| WhatsApp safety | Draft opens only with prefilled text. Nexa never clicks Send. |
| Banglish generation routing | `home page banao`, `homepage banao`, `website banao`, `react component banao`, etc. route to `llm_assist`, not casual chat. |
| Missing LLM config | Returns a clear setup message asking for Gemini/Groq/OpenRouter key instead of casual fallback. |
| Trusted app open | Added coverage that calculator opens directly only when `trusted_quick_launch` is enabled. |
| Dashboard chips | Normal user mode hides internal chips like whitelisted URL/trusted skill/no browser automation/provider local. |

## Test Results

| Command | Result | Notes |
| --- | --- | --- |
| `python -m py_compile backend\app\chat\service.py backend\app\actions\website.py backend\app\schemas\chat.py backend\tests\test_chat.py` | PASS | Used bundled Codex Python for syntax verification. |
| `cd backend; .\.venv\Scripts\python.exe -m pytest` | BLOCKED | This shell's `.venv` launcher points to missing `C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe`. |
| `cd backend; .\.venv\Scripts\python.exe scripts\smoke_test_backend.py` | BLOCKED | Same stale `.venv` launcher issue. |
| Bundled Python `-m pytest tests\test_chat.py -q` | BLOCKED | Bundled runtime does not include `pytest`. |
| `cd frontend; npm.cmd run test` | PASS | Typecheck and Dashboard contract checks passed. |
| `cd frontend; npm.cmd run build` | PASS | First sandbox attempt was denied reading Vite config; rerun with scoped build approval passed. |

## Manual Test Table

| Manual Case | Expected Status | Verification |
| --- | --- | --- |
| `whatsapp e Rahim ke bolo ami pore call korbo` | Opens selected draft target, prefilled text, no Send click | Not manually tested; backend path and frontend wiring implemented, backend runtime blocked by stale `.venv`. |
| `home page banao` | Routes to LLM/code generation or setup message | Covered by backend syntax/test additions; full pytest blocked in this shell. |
| `calculator open koro` | Direct open if trusted quick launch ON, confirmation if OFF | Covered by backend test addition; full pytest blocked in this shell. |
| `how are u` | Human local reply, no source/debug chips | Existing frontend contract still passes for casual chat chip hiding. |
| `delete system32` | Blocked | Safety path unchanged. |

## Remaining Limitations

- Backend pytest and smoke must be rerun in the repaired local backend environment because this Codex shell still has a broken `.venv` launcher.
- The WhatsApp app protocol depends on Windows/app registration. If unavailable, Auto falls back to safe web URLs.
- WhatsApp still shows its own app/web confirmation UI when the platform requires it; Nexa does not and must not bypass that.
- LLM generation requires an enabled provider and API key in `.env`.

## Next Recommended Step

Rerun in the working local backend environment:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
python -m pytest
python scripts\smoke_test_backend.py
```

Then manually test the Dashboard cases above with the backend and frontend running.

