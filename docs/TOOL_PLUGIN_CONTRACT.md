# Tool Plugin Contract

## Purpose

Tools are backend modules that perform a narrow, safe task behind the assistant router. A future assistant project can replace or add tools if it follows the same boundaries.

## Tool Interface Expectations

Each tool should:

- Accept structured input, not raw shell commands.
- Return structured status/result/error data.
- Never format final user-facing prose directly; use `app.assistant.response_composer`.
- Never bypass `app.safety`.
- Avoid network unless the tool's purpose requires it.
- Avoid hard-coded absolute paths.
- Read API keys only from environment variables.

## Current Tool Categories

| Tool | Route |
|---|---|
| Calculator | `local_calculator` |
| Weather | `weather_api` |
| Time | `time_tool` |
| Search | `search_first` |
| YouTube | `youtube_open_url`, `youtube_search_url` |
| WhatsApp | `whatsapp_draft_tool`, `whatsapp_open_url` |
| App Launcher | `safe_app_launcher` |
| Contacts | `local_contacts` |
| LLM Provider Router | `llm_code_generation`, `llm_or_local_general`, `app_planning` |

## LLM Provider Interface

LLM providers must:

- Be optional.
- Use environment keys only.
- Never decide dangerous-command safety.
- Never invent live data.
- Be used after search for current/live information, not before.
- Return provider metadata for UI chips.

## WhatsApp Rule

WhatsApp tools may only open safe draft URLs. They must not send, click Send, scrape credentials, read private chats, or automate hidden browser actions.
