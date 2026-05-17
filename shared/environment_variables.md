# Nexa AI — Environment Variables

This document lists planned environment variables for future development and deployment.

| Variable | Purpose |
|---|---|
| `APP_ENV` | Selects the runtime environment such as development, test, or production |
| `BACKEND_HOST` | Host address for the local FastAPI backend |
| `BACKEND_PORT` | Port used by the local FastAPI backend |
| `SQLITE_DB_PATH` | Filesystem path to the local SQLite database |
| `LOG_LEVEL` | Controls backend logging verbosity |
| `ENABLE_VOICE` | Enables or disables voice features |
| `ENABLE_WEB_INTELLIGENCE` | Enables or disables internet-backed intelligence features |
| `ENABLE_SMART_HOME` | Enables or disables future smart-home modules |
| `ENABLE_DEV_TOOLS` | Enables or disables development-only tooling |

## Rules

- No paid API keys are required in MVP.
- Secrets should not be committed.
- `.env` and `.env.local` are ignored by Git.
