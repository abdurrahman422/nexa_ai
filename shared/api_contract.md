# Nexa AI — Shared API Contract

## Backend Base URL

`http://127.0.0.1:8000`

## REST Purpose

REST APIs will handle direct request/response operations between the Electron React frontend and the Python FastAPI backend. REST should be used for actions such as loading profile data, creating reminders, searching files, updating preferences, and requesting command execution results.

## WebSocket Purpose

WebSocket communication will handle live events that should reach the frontend immediately without polling, such as voice state changes, reminder alerts, command progress, backend status updates, and confirmation requests.

## Planned Endpoint Groups

- `/api/health`
- `/api/profile`
- `/api/commands`
- `/api/apps`
- `/api/system`
- `/api/voice`
- `/api/files`
- `/api/web`
- `/api/reminders`
- `/api/contacts`
- `/api/security`
- `/api/smart-home`

## Standard Success Response Shape

```json
{
  "success": true,
  "data": {},
  "request_id": "string",
  "timestamp": "ISO-8601 string"
}
```

## Standard Error Response Shape

```json
{
  "success": false,
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  },
  "request_id": "string",
  "timestamp": "ISO-8601 string"
}
```

## Request ID and Timestamp Note

- Every response should include a `request_id` for tracing across frontend logs and backend logs.
- Every response should include a server-generated ISO-8601 `timestamp`.
- WebSocket events should also include event timestamps where useful for UI ordering and diagnostics.

## Frontend-Backend Communication Rules

- The frontend must never execute automation logic directly.
- The frontend should call the backend through a centralized API client.
- REST is for explicit user or screen requests.
- WebSocket is for live backend-driven updates.
- Errors must be normalized before reaching UI components.
- Sensitive actions must not be executed until backend safety checks pass.
- The frontend should treat the backend as the source of truth for persisted state.
- Communication should remain local-first and use the loopback interface by default.

