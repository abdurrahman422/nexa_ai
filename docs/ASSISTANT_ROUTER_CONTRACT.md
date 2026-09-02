# Assistant Router Contract

## Purpose

The assistant router decides whether a user message should use local persona, calculator, weather, time, search, YouTube, WhatsApp, contacts, app launch, LLM, or clarification.

## Stable Classification Shape

`app.nlu.classifier.NLUClassification`

| Field | Description |
|---|---|
| `intent` | Canonical intent name |
| `confidence` | Float confidence from 0 to 1 |
| `route` | Execution route name |
| `language_style` | `bangla`, `banglish`, `english`, or `mixed` |
| `entities` | Extracted values such as app, query, recipient, message, phone |
| `normalized_text` | Normalized input |
| `raw_text` | Original input |
| `reason` | Human-readable routing reason |
| `needs_tool` | Tool route required |
| `needs_search` | Search route required |
| `needs_llm` | LLM route required |
| `needs_action` | Safe action route involved |
| `needs_clarification` | Ask one precise follow-up |

## Router Priority

1. Dangerous/system/file command block
2. Calculator/simple math
3. Local contact save/query/delete
4. Weather/time/location/translation
5. Explicit YouTube/WhatsApp skills
6. Contact-message draft intent
7. Identity/profile/casual local persona
8. Current/live/latest/search
9. Safe app open
10. LLM code generation/app planning/general QA
11. Clarification for truly incomplete input

## Import Boundary

Use:

```python
from app.router.task_router import route_task
```

The router must stay independent from FastAPI and frontend code.
