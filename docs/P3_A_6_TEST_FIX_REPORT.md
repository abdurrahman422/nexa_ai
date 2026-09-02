# P3-A.6 Backend Test Fix Report

Date: 2026-06-12

## Scope

Fixed only the remaining backend pytest failure causes reported after P3-A.6 final answer synthesis.

No unrelated P3 features were added.

## Files Changed

| File | Change |
| --- | --- |
| `backend/app/search/service.py` | Market/live fallback wording now uses `could not verify one exact live price` and keeps final synthesized answers. |
| `backend/app/chat/service.py` | Market queries force `live_data=True` and `live_data_warning=True` even when the provider result did not set live data. |
| `backend/requirements.txt` | Added `tzdata` for Windows timezone support. |
| `docs/P3_A_6_TEST_FIX_REPORT.md` | Added this verification report. |

## Why Tests Failed

| Test | Cause | Fix |
| --- | --- | --- |
| `test_market_query_returns_related_sources_without_generic_failure` | Code returned the generic phrase `could not verify one exact value`; the test expects market-specific wording. | Updated market/live fallback wording to `could not verify one exact live price`. |
| `test_gold_price_snippets_return_synthesized_answer` | A mocked market provider response did not set `SearchAnswer.live_data`, so the chat response returned `live_data_warning=False`. | Chat search handling now treats `is_market_query(query)` as live data and forces `live_data=True` plus `live_data_warning=True`. |

## Expected Runtime Behavior

For market/live queries such as gold price, dollar rate, bitcoin price, stock price, and fuel price:

- `live_data=True`
- `live_data_warning=True`
- final synthesized answer remains first
- source chips remain available
- detailed source cards remain optional/collapsible in the Dashboard UI
- fallback wording uses: `I found related live sources for <query>, but could not verify one exact live price. Prices/rates may vary by source and update time.`

## Commands Run

| Command | Result |
| --- | --- |
| `cd backend; .\.venv\Scripts\python.exe -m pytest` | Blocked in this Codex session. The venv launcher points to missing `C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe`. |
| `cd backend; .\.venv\Scripts\python.exe scripts\smoke_test_backend.py` | Blocked for the same venv launcher issue. |
| `cd frontend; npm.cmd run test` | Passed. |
| `cd frontend; npm.cmd run build` | Passed after rerunning outside the restricted sandbox. Initial sandbox run failed on Vite config path access. |

## Backend Pytest Result

Not completed in this Codex session because the backend `.venv` executable cannot create a process:

```text
Unable to create process using '"C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe" -m pytest'
```

Additional environment checks:

- `where.exe python`: no Python found on PATH
- `where.exe py`: no Python launcher found on PATH
- bundled Codex Python exists, but does not have `pytest` installed

## Backend Smoke Result

Not completed in this Codex session because the same `.venv` launcher failure prevents running the smoke script:

```text
Unable to create process using '"C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe" scripts\smoke_test_backend.py'
```

## Frontend Result

`npm.cmd run test`: Passed.

Dashboard contract checks passed, including:

- final answer text shown first
- source cards hidden by default
- `View sources` toggle present
- live-data warning chip rendered
- no redirect to Web Search page
- dangerous/backend blocked responses render in chat

`npm.cmd run build`: Passed.

## Remaining Verification Step

On the machine/session where the backend `.venv` has a valid base Python, run:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
python -m pytest
python scripts\smoke_test_backend.py
```

Expected result after this fix: the two reported backend pytest failures should pass.
