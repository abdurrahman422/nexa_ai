# API Chat Contract

## Endpoint

`POST /api/chat/message`

The endpoint is the stable frontend contract for Dashboard chat, voice transcripts, safe actions, search/weather/time answers, LLM answers, WhatsApp drafts, YouTube actions, pending tasks, and blocked safety responses.

## Request DTO

```json
{
  "message": "string, 1-800 chars",
  "history": [{ "role": "user|assistant|string", "content": "string" }],
  "source": "chat_page",
  "address_style": "Boss|Sir|Vai|Neutral|null",
  "whatsapp_draft_open_target": "auto|app|web|wa_me"
}
```

## Response DTO

Important fields:

| Field | Meaning |
|---|---|
| `status` | `completed`, `preview_only`, `needs_more_info`, `blocked`, `executed`, `needs_configuration`, etc. |
| `intent` | Stable assistant intent such as `weather`, `web_search`, `whatsapp_draft`, `youtube_search`, `blocked_dangerous` |
| `answer` | Final human-facing answer for the Dashboard bubble |
| `blocked` | True only when a request is blocked by policy |
| `requires_confirmation` | True when user confirmation is required before safe action execution |
| `auto_execute_safe` | True only for trusted, whitelisted actions that the backend executed safely |
| `action` | Optional safe app/website/WhatsApp draft action details |
| `pending_task` | Optional pending state prompt such as waiting for phone number/message |
| `chips` | UI chips; normal mode should show only useful chips |
| `search_results` | Detailed sources, hidden by default unless requested |
| `show_search_results_by_default` | Usually false for final synthesized answers |
| `llm_used`, `llm_provider` | LLM metadata only when an LLM was actually used |
| `source_type` | `local`, `tool`, `search`, `llm`, or `hybrid` |

## Guarantees

- Dangerous/system/file commands are blocked before tools, search, or LLM.
- WhatsApp is draft-only; Nexa never clicks Send.
- Unknown executable paths and arbitrary shell text are not executed.
- Normal search answers stay inside the app UI.
- Missing information returns a precise pending task prompt when possible.
