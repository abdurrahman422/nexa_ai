# P3-C.1/C.2 Trusted Skills and Intent Fix Report

Date: 2026-06-12

## Scope

Fixed P3-C.1/P3-C.2 only:

- intent priority for casual chat, web search, translation, YouTube, and WhatsApp
- trusted no-confirm YouTube safe open/search
- trusted no-confirm WhatsApp Web/draft open
- WhatsApp remains draft-only and never auto-sends

No hidden browser automation, arbitrary shell execution, chat scraping, credential bypass, file write/delete/move/rename, smart home, packaging, or workflow automation was added.

## Files Changed

| File | Change |
| --- | --- |
| `backend/app/chat/service.py` | Tightened intent priority, added casual phrases, narrowed YouTube triggers, added trusted safe website execution for YouTube/WhatsApp, and added known-contact WhatsApp draft behavior. |
| `backend/app/actions/website.py` | Allowed only safe YouTube search URLs and WhatsApp Web/`wa.me/<phone>?text=...` draft URL patterns. |
| `backend/app/permissions/store.py` | Added `trusted_youtube_auto_open` and `trusted_whatsapp_draft_auto_open`, default enabled and user-configurable. |
| `backend/app/schemas/chat.py` | Added `auto_execute_safe` to chat responses. |
| `backend/tests/test_chat.py` | Added/updated tests for casual chat, web search routing, YouTube trusted open/search, WhatsApp trusted draft/open, unknown contacts, and blocked dangerous commands. |
| `frontend/src/lib/backendAssistantClient.ts` | Added `auto_execute_safe` to chat DTO. |
| `frontend/src/pages/dashboard/CommandCenterPage.tsx` | Skips confirmation cards when backend returns `auto_execute_safe` with an executed safe action; shows done result instead. |
| `frontend/src/pages/settings/SettingsPageV2.tsx` | Added trusted YouTube and trusted WhatsApp draft auto-open toggles. |
| `frontend/scripts/dashboard-chat-contract-test.cjs` | Added contract checks for no-confirm trusted skills and casual chat handling. |

## Intent Priority

Final routing order:

1. Dangerous command block
2. Weather
3. Time
4. Translation/explanation
5. Explicit YouTube skill only when message contains `youtube`, `yutub`, or `ইউটিউব`
6. Explicit WhatsApp skill only when message contains `whatsapp`, `WhatsApp`, `হোয়াটসঅ্যাপ`, or `হোয়াটসঅ্যাপ`
7. Explicit web/search phrases such as `google theke search kore bolo`, `search kore bolo`, `internet theke bolo`, `web theke bolo`, `latest`, and `today news`
8. Casual/personal assistant conversation
9. Generic app/website open only for explicit open/launch/start style requests
10. Web search/question fallback

## Behavior Summary

| Prompt | Result |
| --- | --- |
| `how are you` | Local casual assistant response, not web search. |
| `google theke search kore bolo python latest version` | Normal completed web/search answer, not YouTube. |
| `youtube open koro` | Direct safe YouTube open when `trusted_youtube_auto_open` is enabled. |
| `youtube e python tutorial search koro` | Direct safe YouTube search URL open when trusted setting is enabled. |
| `whatsapp open koro` | Direct safe WhatsApp Web open when `trusted_whatsapp_draft_auto_open` is enabled. |
| `whatsapp e Rahim ke bolo ami pore call korbo` | Direct WhatsApp draft URL open for known contact Rahim. Nexa does not click Send. |
| Unknown WhatsApp contact | Asks for phone number/contact details; does not open anything. |
| `delete system32` | Blocked first. |

## WhatsApp Safety

- Auto-send remains locked off through `auto_send_messaging`.
- Nexa never clicks the WhatsApp Send button.
- Nexa does not read private chats.
- Nexa does not scrape WhatsApp.
- Nexa does not bypass login.
- Draft URLs are limited to whitelisted `wa.me/<phone>?text=...` patterns.

## Commands Run

| Command | Result |
| --- | --- |
| Bundled Python `py_compile app/chat/service.py app/schemas/chat.py app/permissions/store.py app/actions/website.py tests/test_chat.py` | Passed. |
| `cd backend; .\.venv\Scripts\python.exe -m pytest` | Blocked in this Codex session. The venv launcher points to missing `C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe`. |
| `cd backend; .\.venv\Scripts\python.exe scripts\smoke_test_backend.py` | Blocked for the same venv launcher issue. |
| `cd frontend; npm.cmd run test` | Passed. |
| `cd frontend; npm.cmd run build` | Passed after rerunning outside the restricted sandbox. Initial sandbox run failed on Vite config path access. |

## Backend Verification Note

Full backend pytest and smoke tests could not run in this session because `.venv\Scripts\python.exe` cannot launch:

```text
Unable to create process using '"C:\Users\Abdur Rahman\AppData\Local\Programs\Python\Python311\python.exe" -m pytest'
```

Run in the repaired backend environment:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
python -m pytest
python scripts\smoke_test_backend.py
```

## Manual Dashboard Checklist

| Prompt | Expected |
| --- | --- |
| `how are you` | Conversational assistant reply. |
| `google theke search kore bolo python latest version` | Web/search answer, no YouTube action. |
| `youtube open koro` | YouTube opens directly when trusted setting is enabled. |
| `youtube e python tutorial search koro` | YouTube search opens directly when trusted setting is enabled. |
| `whatsapp open koro` | WhatsApp Web opens directly when trusted setting is enabled. |
| `whatsapp e Rahim ke bolo ami pore call korbo` | WhatsApp draft opens for known contact, no Send click. |
| `delete system32` | Blocked. |
