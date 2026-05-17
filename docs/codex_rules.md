# Nexa AI — Codex Development Rules

## 1. Core Codex Rule

- Never ask Codex to build the full app at once.
- Work one phase at a time.
- Work one sub-step prompt at a time.
- Every phase has exactly 5 sub-steps.
- After each sub-step, run, test, fix, and commit if stable.

## 2. Project Constraints

- No paid APIs.
- No heavy local AI models in MVP.
- Must run on low-end Windows laptops.
- Must keep frontend and backend separated.
- Must use free/public internet sources only when needed.
- Must use SQLite for local memory.
- Must keep sensitive actions confirmation-based.

## 3. Architecture Rules

- Electron + React frontend is only for UI.
- Python FastAPI backend owns automation and business logic.
- REST is for request/response.
- WebSocket is for live events.
- SQLite is the local database.
- Modules must stay small and separated.

## 4. Frontend Rules

- Use Electron + React + Vite + TypeScript.
- Use Tailwind CSS.
- Use Framer Motion only for lightweight animations.
- Avoid heavy 3D/Three.js in MVP.
- Use reusable UI components.
- Keep cyberpunk/Jarvis-style design consistent.
- Optimize for 1366x768 and 1920x1080.

## 5. Backend Rules

- Use Python FastAPI.
- Keep routers, services, database, and modules separated.
- Add health checks.
- Add structured logging.
- Normalize errors.
- Never execute raw user text directly.
- Always pass commands through command engine and safety checks.

## 6. Command Engine Rules

- Support Bengali, English, Banglish, and mixed commands.
- Use normalization, synonym mapping, `rapidfuzz` fuzzy matching, intent detection, slot extraction, confidence scoring, safety checks, and execution plans.
- Low-confidence commands must ask clarification.
- Sensitive commands must require confirmation.

## 7. Safety Rules

- Never auto-send WhatsApp/email in MVP.
- Never delete files without strong confirmation.
- Shutdown/restart must require confirmation.
- File move/rename must require confirmation.
- Log sensitive actions.

## 8. Git Rules

- Commit after each stable sub-step.
- Use clear commit messages.
- Suggested branch names:
  - `main`
  - `dev`
  - `feature/phase-01-planning`
  - `feature/phase-02-skeleton`

## 9. Testing Rules

- Run the app after each implementation sub-step.
- Check terminal errors.
- Check frontend UI.
- Check backend API.
- Check WebSocket if involved.
- Fix errors before moving forward.

## 10. Documentation Rules

- Update README when setup changes.
- Update architecture docs when architecture changes.
- Keep roadmap aligned with actual progress.
