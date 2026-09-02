# Safety Policy

## Blocked Always

Nexa must block:

- `delete system32`
- `delete all files`
- `format drive`
- `format C drive`
- arbitrary `cmd` or PowerShell execution
- registry editor actions
- arbitrary executable paths
- file write/delete/move/rename operations
- hidden browser automation
- WhatsApp auto-send

## Allowed With Guardrails

| Action | Policy |
|---|---|
| Safe app open | Only whitelisted apps; confirmation unless trusted quick launch is enabled |
| Safe website open | Only whitelisted URLs/patterns |
| YouTube open/search | Safe URL only; no credential or browser automation |
| WhatsApp draft | Draft URL only; user manually presses Send |
| Contact delete | Only local Nexa contact mapping, never file/system delete |

## Safety Order

Dangerous checks run before pending tasks, tools, search, or LLM.

## Audit

Blocked and executed events should be recorded when the audit log is available.

## API Keys

No API keys may be hard-coded in source code, docs, tests, or reports. Use `.env` and placeholder-only `.env.example`.
