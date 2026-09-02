# P3-E.1 Stability and Intent Fix Report

## Summary

This pass fixed the current intent-routing and visible Dashboard stability issues without adding new LLM providers or new product features.

## Bugs Found and Fixed

| ID | Area | Problem | Fix |
| --- | --- | --- | --- |
| P3E1-01 | Backend chat intent | `how are u` / `how r u` could fall through to generic question detection and become web search. | Added casual patterns and kept local conversation routing before fallback web search. |
| P3E1-02 | Backend greeting detection | Greeting matching could treat `hi` inside words like `achi` as greeting. | Greeting detection uses token/phrase boundary matching. |
| P3E1-03 | Backend safety routing | `Rahim er WhatsApp contact delete koro` was blocked because every `delete` looked dangerous. | Safe local contact commands are detected before dangerous deletion blocking, while system/file delete stays blocked. |
| P3E1-04 | Assistant conversation | Repeated casual responses were too identical. | Added deterministic reply variation based on message/history. |
| P3E1-05 | Dashboard UI | Local personal conversation could show provider/source debug chips. | Dashboard hides local-conversation provider/source/chips unless `nexa_debug_chat_chips` is enabled in localStorage. |
| P3E1-06 | WhatsApp contacts | Contact lookup was exact-only except direct nickname match. | Added case-insensitive, nickname-aware, one-safe-match fuzzy resolution with ambiguity protection. |

## Files Changed

| File | Changes |
| --- | --- |
| `backend/app/chat/service.py` | Intent priority, casual patterns, local reply variation, local debug chip suppression, contact ambiguity handling. |
| `backend/app/contacts/store.py` | Nickname/case/fuzzy contact resolution and safe unique fuzzy delete support. |
| `backend/app/contacts/__init__.py` | Exported `find_contact_matches`. |
| `backend/tests/test_chat.py` | Added regression coverage for `how are u`, reply variation, alias/fuzzy WhatsApp contacts, and ambiguous contacts. |
| `frontend/src/pages/dashboard/CommandCenterPage.tsx` | Hides local personal-conversation source/debug chips by default. |
| `frontend/scripts/dashboard-chat-contract-test.cjs` | Updated contract check for local conversation source-card suppression. |
| `docs/P3_E_1_STABILITY_AND_INTENT_FIX_REPORT.md` | This report. |

## Test Results

| Command | Result | Notes |
| --- | --- | --- |
| `cd backend; .\.venv\Scripts\python.exe -m pytest` | Blocked in Codex shell | `.venv` launcher points to missing `C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe`. |
| `cd backend; python -m pytest` | Blocked in Codex shell | `python` is not available on PATH in this shell. |
| Bundled Python syntax check | Passed | `py_compile` passed for `app/chat/service.py`, `app/contacts/store.py`, and `tests/test_chat.py`. |
| `cd backend; .\.venv\Scripts\python.exe scripts\smoke_test_backend.py` | Blocked in Codex shell | Same stale `.venv` launcher problem. |
| Bundled Python `-m pytest` | Blocked | Bundled runtime does not include `pytest`. |
| `cd frontend; npm.cmd run test` | Passed | TypeScript check and Dashboard contract tests passed. |
| `cd frontend; npm.cmd run build` | Passed after escalation | First sandbox run hit Vite config access denial; escalated rerun passed. |

## Manual Test Table

| Manual input | Expected result | Status from code path |
| --- | --- | --- |
| `hi` | Greeting | Token-based greeting path. |
| `achi` | Not greeting | Does not match `hi` substring. |
| `how are u` | Casual/personal assistant response, no web search/source cards | Covered by new backend test and Dashboard meta suppression. |
| `how r u` | Casual/personal assistant response | Routed as casual conversation. |
| `ki koro` | Casual assistant reply | Existing covered path retained. |
| `kemon aso` | Casual assistant reply | Existing covered path retained. |
| `ami tension e achi` | `user_frustration` supportive reply | Greeting substring issue avoided. |
| `Rahim er WhatsApp contact delete koro` | Safe `contact_delete` | Contact command is allowlisted before dangerous delete block. |
| `delete system32` | Blocked dangerous | Dangerous/system deletion remains blocked. |
| `delete all files` | Blocked dangerous | Existing regression test retained. |
| `Rahim`, `rahim`, `Rohim`, alias/nickname | Resolve safely when one match exists | Contact resolver supports case-insensitive, nickname, and unique fuzzy matches. |
| Ambiguous contact match | Ask clarification, do not execute | Added backend regression coverage. |
| `google theke search kore bolo python latest version` | Web/search answer | Explicit search phrase still routes to `web_search`. |
| `youtube e python tutorial search koro` | YouTube skill because YouTube is mentioned | YouTube detection remains explicit keyword-based. |
| `whatsapp e Rahim ke bolo ami pore call korbo` | WhatsApp draft only, no auto-send | Draft URL only; no Send click or chat scraping. |

## Remaining Limitations

- Backend pytest and smoke could not be executed from this Codex shell because the local `.venv` launcher is still stale here.
- Fuzzy contact matching is intentionally conservative: it only auto-resolves one safe match and asks clarification for ambiguous matches.
- Local reply variation is deterministic and lightweight, not an LLM conversation model.
- WhatsApp remains draft-only; Nexa never clicks Send or reads private chats.

## Next Recommended Step

Run the backend commands from the repaired local PowerShell environment:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
python -m pytest
python scripts\smoke_test_backend.py
```

Expected result after the environment launcher is repaired: backend pytest should pass with the new regression coverage.
