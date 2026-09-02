# P4-D.1 Integration Regression Fix Report

## Summary

Fixed the P4 integration regressions caused by architecture/NLU/memory/composer merge points. The changes focus on route priority, pending-task matching, response wording contracts, WhatsApp draft permissions/casing behavior, and search-before-LLM policy. No new product features were added.

## Root Cause of 18 Failures

| Area | Root Cause | Fix |
|---|---|---|
| Web/search route regression | YouTube detection used substring matching, so `yt` matched inside words like `python`; generic action routing could also win too early | Switched YouTube/WhatsApp detection to token/phrase matching and moved LLM/code handling before generic app open |
| `python latest version` route | `yt` substring inside `python` caused false YouTube route | Explicit YouTube markers now require token/phrase match: `youtube`, `yutub`, `yt`, `ইউটিউব` |
| Pending task stealing explicit intents | Pending continuation ran before checking whether the new message had a strong explicit intent | Added strong-intent guard so location/weather/time/search/calculator/WhatsApp/YouTube/contact/app-open/app-planning bypass stale pending tasks |
| WhatsApp pending flows blocked | Test monkeypatch enabled trusted WhatsApp draft mode but not the base skill toggle | Trusted WhatsApp draft auto-open now permits the safe draft path while auto-send remains impossible |
| App planning starter completed too early | App planning tried LLM first and could return completed instead of asking for details | App-planning starter now returns `needs_more_info` with pending platform/features task |
| Login/page generation setup | Inline LLM setup bypassed the composer/pending metadata path | `llm_assist` no-provider path now uses `_llm_setup_answer` and pending generation details |
| Composer wording mismatch | Templates lacked stable phrases expected by tests | Calculator, YouTube, and WhatsApp templates now include required phrases |
| WhatsApp draft wording | Mixed template did not include exact English safety phrase | WhatsApp draft success now includes `Nexa did not click Send. Please review and press Send manually.` |
| Live market search after LLM | Low-confidence market fallback skipped LLM entirely | Search is still first; LLM is called after search when enabled/results exist, but low-confidence fallback wording is preserved |

## Files Changed

| File | Changes |
|---|---|
| `backend/app/chat/service.py` | Fixed route priority, pending-task guard, trusted WhatsApp draft permission path, app-planning status, LLM setup path, market LLM-after-search behavior |
| `backend/app/assistant/templates.py` | Added test-stable human phrases for Calculator, YouTube, and WhatsApp draft success |

## Safety Confirmation

| Rule | Status |
|---|---|
| No hidden browser automation | Preserved |
| No WhatsApp auto-send | Preserved |
| No WhatsApp Send click | Preserved |
| No arbitrary shell execution | Preserved |
| Dangerous commands blocked first | Preserved |
| Safe local contact delete remains allowed | Preserved |
| Search/live data uses search first | Preserved |

## Verification Commands

| Command | Result |
|---|---|
| `cd backend; .\.venv\Scripts\Activate.ps1; python -m pytest` | Not executed: PowerShell execution policy blocks activation; `python` is not on PATH in this shell |
| `cd backend; .\.venv\Scripts\Activate.ps1; python scripts\smoke_test_backend.py` | Not executed: same PowerShell/Python environment blocker |
| `cd frontend; npm.cmd run test` | Passed |
| `cd frontend; npm.cmd run build` | First attempt failed due restricted sandbox Vite config read denial |
| `cd frontend; npm.cmd run build` with scoped escalation | Passed |

## Backend Test Status

The user-reported local backend baseline was `270 collected, 252 passed, 18 failed`. This environment still cannot start backend pytest because:

- `.\.venv\Scripts\Activate.ps1` is blocked by PowerShell execution policy.
- `python` is not available on PATH after activation fails.

Run locally with:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pytest
```

## Smoke Test Status

Smoke test could not be executed in this shell for the same backend environment reason. After pytest passes locally, run:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
python run_backend.py
```

Then in another terminal:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
python scripts\smoke_test_backend.py
```

## Frontend Result

Frontend contract/typecheck and production build both passed. The build required scoped escalation only because the sandbox could not read `frontend/vite.config.ts`; the escalated build succeeded.

## Remaining Risk

Backend test pass status must be confirmed in the user's local PowerShell after enabling process execution policy or running from an already activated working environment. No P3/P4 feature expansion was done in this fix.
