# P3-K Universal Answer Engine Report

Generated: 2026-06-13

## Summary

Implemented a universal answer policy so Nexa handles normal questions, identity/profile questions, simple math, app/project planning, location-permission questions, and common general knowledge without falling into the vague low-confidence message. Existing weather, search, YouTube, WhatsApp draft-only behavior, trusted app launch, LLM routing, and dangerous-command blocking remain intact.

## Files Changed

| File | Change |
| --- | --- |
| `backend/app/chat/service.py` | Added universal routing intents, calculator percent/math support, local identity/profile/location replies, app-planning fallback, general knowledge fallback, and specific clarification wording. |
| `backend/tests/test_chat.py` | Added coverage for calculator, identity, profile/memory, news search, app planning, location permission, and general knowledge fallback. |
| `frontend/scripts/dashboard-chat-contract-test.cjs` | Added checks that Dashboard does not embed the old generic clarification and renders clean answer text. |
| `docs/P3_K_UNIVERSAL_ANSWER_ENGINE_REPORT.md` | Added this report. |

## Behavior Added

| User Input | Result |
| --- | --- |
| `2+2=?`, `2 + 2`, `10*5`, `20% of 500` | Local calculator answer, no LLM. |
| `tomar nam ki?`, `what is your name`, `who are you` | Local Nexa identity reply. |
| `amar somporke ki ki jano?` | Local memory/profile reply that does not invent facts. |
| `what is the computer`, `computer ki`, `AI ki`, `programming ki` | LLM if configured; otherwise short useful local fallback. |
| `ami ekta app banate cai` | Helpful app-planning follow-up asking platform/features. |
| `recent global news ki?`, `latest global news`, `today news` | Search-first route. |
| `my location`, `ami ekhon kothai achi` | Asks for browser/device location permission; does not guess. |
| Truly incomplete follow-up like `how would that work` | Specific clarification remains available. |

## Safety Confirmation

- Dangerous commands still block before tools, search, or LLM.
- WhatsApp remains draft-only.
- Nexa does not click WhatsApp Send.
- No WhatsApp chat reading, credential scraping, or hidden automation was added.
- No arbitrary shell execution was added.
- Existing YouTube, WhatsApp, weather, search, and app-launch behavior was not removed.

## Test Results

| Command | Result | Notes |
| --- | --- | --- |
| `python -m py_compile backend\app\chat\service.py backend\tests\test_chat.py` | PASS | Used bundled Codex Python for syntax verification. |
| `cd backend; .\.venv\Scripts\python.exe -m pytest` | BLOCKED | This shell's `.venv` launcher still points to missing `C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe`. |
| `cd backend; .\.venv\Scripts\python.exe scripts\smoke_test_backend.py` | BLOCKED | Same stale `.venv` launcher issue. |
| `cd frontend; npm.cmd run test` | PASS | Typecheck and Dashboard contract checks passed. |
| `cd frontend; npm.cmd run build` | PASS | Initial sandbox run denied Vite config access; scoped build rerun passed. |

## Manual Test Status

| Manual Case | Expected | Status |
| --- | --- | --- |
| `2+2=?` | Local calculator answer `4` | Not manually run; covered by backend test addition. |
| `what is the computer` | Useful general answer, not vague clarification | Not manually run; covered by backend test addition. |
| `tomar nam ki?` | Nexa identity reply | Not manually run; covered by backend test addition. |
| `amar somporke ki ki jano?` | No invented personal facts | Not manually run; covered by backend test addition. |
| `recent global news ki?` | Search-first answer | Not manually run; covered by backend test addition. |
| `ami ekta app banate cai` | App-planning follow-up | Not manually run; covered by backend test addition. |
| `home page banao` | LLM route or setup message | Existing behavior retained. |
| `may location` | Location permission explanation | Not manually run; backend location intent added. |
| `whatsapp e Rahim ke bolo ami pore call korbo` | Draft only, no Send click | Existing behavior retained. |
| `delete system32` | Blocked | Existing safety retained. |

## Remaining Limitations

- Full backend pytest and smoke must be rerun in the working local `.venv` because this Codex shell cannot launch the backend venv.
- Local general-answer fallback covers only common topics. More detailed open-ended answers need an enabled LLM provider.
- Exact location requires frontend/browser/device permission support; Nexa does not guess location.

## Next Recommended Step

Run backend verification in the repaired local environment:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
python -m pytest
python scripts\smoke_test_backend.py
```

Then test the manual Dashboard prompts with backend and frontend running.

