# Memory Policy

## Local First

Nexa memory is local-only. It does not sync to cloud services and must not invent personal facts.

## Short-Term Context

Stores:

- last 10 messages
- last intent
- last route
- last topic
- last assistant question
- language style
- address style

## Pending Tasks

Supported pending tasks:

- WhatsApp draft waiting for contact number
- WhatsApp draft waiting for message text
- app/project planning info
- LLM generation details
- YouTube search query
- location permission

Pending tasks:

- expire after `NEXA_PENDING_TASK_TTL_MINUTES` or default 30 minutes
- clear after completion
- can be cancelled with `cancel`, `bad dao`, or `stop`
- never override dangerous-command blocking

## Profile Memory

Stores safe preferences only:

- display preference
- address style
- saved project preferences

Known contacts live in the local WhatsApp contact store. Sensitive or inferred facts must not be invented.
