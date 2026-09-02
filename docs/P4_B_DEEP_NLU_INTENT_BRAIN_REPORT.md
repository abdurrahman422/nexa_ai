# P4-B Deep NLU Intent Brain Report

## Summary

Implemented a modular Bangla/Banglish/English NLU layer for Nexa AI so intent routing can be reused outside the current chat service. The new classifier returns a structured result with intent, route, confidence, language style, entities, normalized text, raw text, routing reason, and tool/search/LLM/action/clarification flags.

## Architecture Map

| Module | Purpose |
|---|---|
| `backend/app/nlu/normalizer.py` | Unicode/text normalization, token checks, language-style detection |
| `backend/app/nlu/banglish.py` | Banglish/Bangla phrase canonicalization |
| `backend/app/nlu/patterns.py` | Central pattern and regex inventory for intents/entities |
| `backend/app/nlu/classifier.py` | Main NLU classifier returning `NLUClassification` |
| `backend/app/router/task_router.py` | Stable router facade over the NLU brain |
| `backend/tests/test_nlu_router.py` | 100+ real prompt route tests |

## Files Changed

| File | Change |
|---|---|
| `backend/app/nlu/normalizer.py` | Added reusable normalization helpers and language-style detection |
| `backend/app/nlu/banglish.py` | Added canonicalization for common Bangla/Banglish/English variants |
| `backend/app/nlu/patterns.py` | Added central hint sets and regexes for router intents/entities |
| `backend/app/nlu/classifier.py` | Added structured classification for chat, search, calculator, YouTube, WhatsApp, app launch, LLM/code generation, profile, identity, location, and dangerous commands |
| `backend/app/nlu/__init__.py` | Exported NLU public API |
| `backend/app/router/task_router.py` | Updated facade to return `NLUClassification` |
| `backend/tests/test_architecture_boundaries.py` | Aligned P4 architecture smoke expectations with P4-B intent names |
| `backend/tests/test_nlu_router.py` | Added deep NLU route coverage with more than 100 parametrized real prompts |

## Required Prompt Coverage

| Prompt | Expected Intent | Route |
|---|---|---|
| `what is the computer` | `general_qa` | `llm_or_local_general` |
| `computer ki` | `general_qa` | `llm_or_local_general` |
| `tomar nam ki` | `identity` | `local_persona` |
| `amar somporke ki jano` | `user_profile` | `local_profile_memory` |
| `recent global news ki` | `search_current` | `search_first` |
| `2+2=?` | `calculator` | `local_calculator` |
| `ami ekta app banate cai` | `app_planning` | `app_planning` |
| `ekta login page banabo` | `llm_code_generation` | `llm_code_generation` |
| `home page banao` | `llm_code_generation` | `llm_code_generation` |
| `youtube e bangla gan chalao` | `youtube_search` | `youtube_search_url` |
| `ইউটিউব খুলে একটা বাংলা গান চালাও` | `youtube_search` | `youtube_search_url` |
| `whatsapp e Rahim ke bolo ami pore call korbo` | `whatsapp_draft` | `whatsapp_draft_tool` |
| `milon k bolo ami kal asbo na` | `contact_message_intent` | `confirm_whatsapp_or_contact_message` |
| `calculator open koro` | `app_open_request` | `safe_app_launcher` |
| `delete system32` | `dangerous_block` | `blocked` |

## Policy Behavior

| Policy | Status |
|---|---|
| Normal casual talk avoids web search | Implemented in classifier priority |
| Weather/time/calculator/basic actions avoid LLM | Implemented via dedicated routes |
| Current/live/news/latest routes to search | Implemented via `search_current` |
| YouTube requires explicit YouTube/YT/Yutub/Bangla YouTube wording | Implemented |
| WhatsApp/contact-message intent extracts recipient/message | Implemented |
| Dangerous commands block before all other routes | Implemented |
| Clarification only for truly short/incomplete messages | Implemented |

## Commands Run

| Command | Result |
|---|---|
| `python -m pytest backend\tests\test_nlu_router.py backend\tests\test_architecture_boundaries.py` | Failed: `python` is not available on PATH in this shell |
| `.\.venv\Scripts\python.exe -m pytest tests\test_nlu_router.py tests\test_architecture_boundaries.py` | Failed: venv launcher points to missing `C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe` |
| `.\.venv\Scripts\Activate.ps1; python -m pytest` | Failed: PowerShell execution policy blocks activation, then `python` is not on PATH |
| `.\.venv\Scripts\Activate.ps1; python scripts\smoke_test_backend.py` | Failed: PowerShell execution policy blocks activation, then `python` is not on PATH |
| `npm.cmd run test` from `frontend` | Passed |
| `npm.cmd run build` from `frontend` | First attempt failed due sandbox read denial for Vite config |
| `npm.cmd run build` from `frontend` with scoped escalation | Passed |

## Backend Test Status

Backend tests were not executable in this shell because the local Python environment is broken:

- PowerShell activation is blocked by execution policy.
- `python` is not available on PATH.
- Direct `.venv\Scripts\python.exe` fails because its launcher references a missing Python 3.11 install path.

Recommended local verification after repairing the backend venv:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pytest
python scripts\smoke_test_backend.py
```

## Frontend Verification

| Check | Result |
|---|---|
| TypeScript/frontend contract tests | Passed |
| Production build | Passed after scoped sandbox escalation |

## Remaining Limitations

| Area | Limitation |
|---|---|
| Backend runtime | Needs venv repair or Python PATH fix before backend tests can run in this shell |
| NLU | This is deterministic pattern-based NLU; ambiguous conversational intent may still need future classifier/LLM assist |
| Bangla text | Clean Unicode Bangla patterns were added, but older mojibake literals still exist from prior files and can be cleaned in a later maintenance pass |

## Final Status

P4-B implementation is complete at the code/test-definition level. Frontend verification passed. Backend pytest and smoke could not run because the current local Python environment is not executable from this shell.
