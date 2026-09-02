# P3-H WhatsApp Draft Composer Report

## Summary

Implemented the advanced WhatsApp draft composer and contact intelligence layer. Nexa can now extract recipient, message, tone, and contact relationship from natural Dashboard chat/voice text, compose a safer draft, and open WhatsApp with prefilled text only. Nexa still never clicks Send, never reads chats, never scrapes credentials, and never runs hidden browser automation.

## Files Changed

| File | Changes |
| --- | --- |
| `backend/app/contacts/store.py` | Expanded local contact records with `aliases`, `relationship`, and `default_tone`; added alias matching and alias add support while keeping old nickname records compatible. |
| `backend/app/contacts/__init__.py` | Exported `add_contact_alias`. |
| `backend/app/schemas/contacts.py` | Added aliases, relationship, and default tone to API schemas. |
| `backend/app/api/routes/contacts.py` | Saves and returns new contact intelligence fields. |
| `backend/app/chat/service.py` | Added contact relationship/tone save parsing, alias command parsing, flexible WhatsApp draft parser, tone inference, local draft templates, optional LLM composition, missing-message prompt, and draft-only safe URL behavior. |
| `backend/tests/test_chat.py` | Added tests for relationship/tone, alias matching, missing message, formal/friendly drafts, exact-message preservation, and safe draft behavior. |
| `frontend/src/lib/backendAssistantClient.ts` | Added contact aliases, relationship, and default tone DTO fields. |
| `frontend/src/pages/settings/SettingsPageV2.tsx` | Added relationship, default tone, and aliases fields to Local WhatsApp Contacts. |
| `frontend/scripts/dashboard-chat-contract-test.cjs` | Updated Settings contract check for contact intelligence fields. |
| `docs/P3_H_WHATSAPP_DRAFT_COMPOSER_REPORT.md` | This report. |

## Implemented Behavior

| Input | Behavior |
| --- | --- |
| `Rahim er number save koro 017xxxxxxxx` | Saves local WhatsApp contact. |
| `Boss er number save koro 017xxxxxxxx relationship boss` | Saves contact with `relationship=boss` and formal default tone. |
| `Rahim er alias Rohim add koro` | Adds alias for safe contact resolution. |
| `Rahim er number ki` | Looks up saved local number. |
| `Rahim er WhatsApp contact delete koro` | Deletes local contact only. |
| `whatsapp e Rahim ke bolo ami pore call korbo` | Resolves Rahim, composes friendly draft, opens/returns WhatsApp draft only. |
| `whatsapp e amar boss ke sms dao kalke ami office e aste parbo na` | Resolves boss, composes formal office absence draft, opens/returns WhatsApp draft only. |
| `Rahim ke WhatsApp e likho meeting ta 5tay` | Resolves Rahim and prepares draft text. |
| `WhatsApp Rahim draft` | Finds recipient but asks: `Boss, Rahim-er jonno message ta ki likhbo?` |
| Unknown contact | Asks for phone number and does not guess. |
| Ambiguous contact | Asks which contact the user means and does not execute. |

## Draft Safety

- Uses only safe draft URLs: `https://wa.me/<phone>?text=<encoded_final_draft>`.
- No auto-send path was added.
- No browser Send click automation was added.
- No private chat reading was added.
- No credential scraping was added.
- Dangerous/system commands remain blocked by the existing safety router.

## Composition Policy

| Condition | Composer |
| --- | --- |
| `relationship=boss` or `client` | Formal draft. |
| `relationship=friend` or `family` | Friendly draft. |
| User asks `formal`, `professional`, `friendly`, `shundor kore`, or `valo kore` | Optional LLM composition if configured; local fallback otherwise. |
| User says exact/same/hubohu | Preserves message without over-editing. |
| LLM unavailable | Local templates are used. |

## Verification Results

| Command | Result | Notes |
| --- | --- | --- |
| Backend `py_compile` with bundled Python | Passed | Contact store/schema/routes, chat service, and tests compile. |
| `cd backend; .\.venv\Scripts\python.exe -m pytest` | Blocked in this Codex shell | `.venv` launcher points to missing `C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe`. |
| `cd backend; .\.venv\Scripts\python.exe scripts\smoke_test_backend.py` | Blocked in this Codex shell | Same stale `.venv` launcher problem. |
| `cd frontend; npm.cmd run test` | Passed | TypeScript and Dashboard contract tests passed. |
| `cd frontend; npm.cmd run build` | Passed after escalation | First sandbox run hit Vite config access denial; escalated rerun passed. |

## Manual Test Table

| Prompt | Expected |
| --- | --- |
| `Rahim er number save koro 01712345678` | Contact saved locally. |
| `Boss er number save koro 01712345678 relationship boss` | Boss saved with formal tone. |
| `Rahim er alias Rohim add koro` | Alias saved and resolves to Rahim. |
| `whatsapp e Rahim ke bolo ami pore call korbo` | Friendly draft opens/previews; Nexa does not press Send. |
| `whatsapp e amar boss ke sms dao kalke ami office e aste parbo na` | Formal draft opens/previews; Nexa does not press Send. |
| `Rahim ke WhatsApp e likho exact message meeting ta 5tay` | Draft text remains `meeting ta 5tay`. |
| `WhatsApp Rahim draft` | Asks what message to write. |
| `whatsapp e Unknown ke bolo hi` | Asks for phone number. |
| `delete system32` | Blocked before any WhatsApp/contact flow. |

## Remaining Limitations

- Backend pytest/smoke must be run from a repaired backend `.venv`; this Codex shell still has a stale Python launcher path.
- Contact storage remains local JSON, not cloud synced.
- LLM composition is optional and only used when configured; local templates cover common formal/friendly drafts.
- The Settings UI supports comma-separated aliases but not a full alias management table yet.

## Next Step

Run backend verification from a repaired local PowerShell environment:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
python -m pytest
python scripts\smoke_test_backend.py
```

Then manually test the prompts above with backend and frontend running.
