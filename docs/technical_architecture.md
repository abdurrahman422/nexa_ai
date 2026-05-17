# Nexa AI — Technical Architecture

## 1. System Overview

Nexa AI is a Windows desktop personal voice assistant composed of two primary runtime systems:

1. **Desktop Client**
   - Built with Electron, React, Vite, and TypeScript
   - Provides the futuristic cyberpunk/Jarvis-style user experience
   - Handles visual interaction, microphone controls, status display, settings, and local desktop shell behavior

2. **Automation Backend**
   - Built with Python FastAPI
   - Owns command interpretation, business logic, local automation, scheduling, file/document processing, web intelligence, permissions, and persistence

The frontend and backend remain deliberately separate. The desktop UI is responsible for presentation and user interaction; the backend is responsible for capability execution and safety. They communicate locally through REST APIs for request/response work and WebSockets for real-time events such as listening state, command progress, reminder alerts, and execution results.

Nexa AI uses SQLite as its local database, free/public internet sources only when live external information is needed, and lightweight rule-based or retrieval-oriented logic in the MVP instead of heavy local AI models. Sensitive actions must pass through confirmation-aware security rules before execution.

---

## 2. High-Level Architecture Diagram

```text
┌────────────┐
│    User    │
└─────┬──────┘
      │ voice / text / clicks
      ▼
┌──────────────────────────────┐
│ Electron + React Desktop UI  │
│  - Renderer                  │
│  - Preload bridge            │
│  - Main process              │
└──────────────┬───────────────┘
               │ REST / WebSocket
               ▼
┌──────────────────────────────┐
│ Python FastAPI Backend       │
│  - Routers                   │
│  - Services                  │
│  - Security                  │
│  - Scheduler                 │
└──────────────┬───────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│ Domain Modules                                               │
│ Command Engine | Voice | Automation | Files | Documents     │
│ Reminders | Messaging Drafts | Web Intelligence | Smart Home │
└───────┬───────────────┬──────────────┬──────────────┬────────┘
        │               │              │              │
        ▼               ▼              ▼              ▼
┌────────────┐   ┌────────────┐  ┌────────────┐  ┌────────────┐
│   SQLite   │   │  Windows   │  │  Internet  │  │   ESP32    │
│ local data │   │ automation │  │ free data  │  │  future    │
└────────────┘   └────────────┘  └────────────┘  └────────────┘
```

---

## 3. Frontend Architecture

### Electron Main Process

The Electron main process owns:

- Application lifecycle
- Native window creation
- System tray behavior if introduced
- Backend process startup and shutdown coordination
- OS-level integration that should not be exposed directly to the renderer
- Secure registration of IPC handlers

The main process should remain thin. It should orchestrate the desktop shell, not contain business logic.

### Preload Layer

The preload layer is the security boundary between Electron and the React renderer.

Responsibilities:

- Expose a minimal, typed API to the renderer
- Wrap IPC safely
- Avoid direct Node.js access in the renderer
- Keep privileged desktop capabilities explicit and auditable

### React Renderer

The renderer is responsible for:

- Dashboard screens
- Voice interaction surfaces
- Chat/transcript views
- Settings and permissions UI
- Reminder/task views
- File/document result presentation
- Automation and future smart-home control surfaces

### Pages

Recommended top-level pages:

- Onboarding
- Dashboard
- Assistant / Chat
- Reminders & Tasks
- Files
- Documents
- Contacts & Drafts
- Automations
- Settings
- Security / Permissions

### Reusable UI Components

Reusable components should include:

- Voice orb / microphone control
- Status badge
- Command result card
- Confirmation modal
- Permission prompt
- Reminder card
- File result row
- Document summary panel
- Reusable cyberpunk panels, buttons, tabs, and cards

### State Management Strategy

Use a lightweight, predictable state model:

- Local component state for ephemeral UI concerns
- Central client state for:
  - user profile
  - active session
  - websocket connection status
  - command progress
  - reminders
  - permissions
- Server state fetched through the API client should remain distinct from transient visual state

Avoid overly complex global state early. The architecture should favor clarity over abstraction.

### API Client

The API client should:

- Centralize REST calls
- Apply consistent request/response typing
- Normalize backend errors
- Attach request identifiers where useful
- Prevent components from manually constructing endpoint logic

### WebSocket Event Listener

The WebSocket client should listen for events such as:

- `voice.listening.started`
- `voice.listening.stopped`
- `command.processing`
- `command.completed`
- `command.failed`
- `reminder.triggered`
- `security.confirmation.required`
- `backend.status.changed`

### UI Performance Rules

- Lazy-load heavier pages and optional panels
- Keep animations lightweight and transform-based where possible
- Avoid large rerender cascades
- Use debouncing for search fields
- Keep dashboard queries minimal
- Prefer virtualized lists when search results become large
- Maintain usability on lower-resolution and lower-memory devices

---

## 4. Backend Architecture

### FastAPI App

The FastAPI application is the backend entrypoint and should provide:

- REST endpoints
- WebSocket endpoints
- Application startup/shutdown hooks
- Dependency wiring
- Middleware for logging, correlation IDs, and error handling

### API Routers

Routers should be grouped by domain, for example:

- `profile`
- `voice`
- `commands`
- `apps`
- `browser`
- `files`
- `documents`
- `reminders`
- `contacts`
- `web`
- `permissions`
- `automations`
- `smart_home`

### Service Modules

Service modules hold business logic and should remain independent of HTTP transport wherever practical.

### Command Engine

The command engine is responsible for:

- Text normalization
- Synonym handling
- Fuzzy matching using `rapidfuzz`
- Intent detection
- Slot extraction
- Confidence scoring
- Clarification behavior
- Routing toward executable actions or conversational responses

### Automation Engine

The automation engine executes supported operating-system and workflow actions such as:

- Launch app
- Open website
- Search browser
- Control approved system settings
- Run reusable future automations

It should receive validated execution plans rather than raw user text.

### Voice Engine

The voice engine coordinates:

- Speech-to-text ingestion
- Text-to-speech generation
- Voice-session status events
- Handoff into the command engine

### File and Document Modules

These modules should handle:

- File search
- Safe file metadata inspection
- Confirmed rename/move operations
- PDF/document parsing
- Text extraction
- Chunk creation
- Lightweight retrieval and summarization support

### Web Intelligence Module

Responsibilities:

- Weather lookup
- News retrieval through RSS or other free feeds
- Dictionary lookup
- Basic web retrieval through free/public sources
- Caching and source-failure handling

### Scheduler Module

Responsibilities:

- Reminder scheduling
- Task due-date checks
- Notification dispatch
- Future recurrence handling

### Smart Home Module

Initially inactive in MVP, but architecturally planned for:

- ESP32 device registry
- Device commands
- State reporting
- Local-network communication

### Security Layer

The security layer should be shared infrastructure, not an afterthought.

Responsibilities:

- Action classification
- Permission evaluation
- Confirmation checks
- Audit logging
- Policy enforcement before execution

---

## 5. API Communication Flow

### REST Request/Response Pattern

Use REST for:

- Profile reads and updates
- Reminder creation
- Shortcut management
- Contact management
- Search requests
- Settings retrieval
- File/document metadata operations

Typical pattern:

```text
Frontend action
→ API client
→ FastAPI router
→ service layer
→ database or module
→ normalized response
→ UI update
```

### WebSocket Event Pattern

Use WebSockets for:

- Voice session state
- Live command progress
- Reminder notifications
- Long-running task completion
- Security confirmation requests
- Backend health/status events

Typical pattern:

```text
Backend event occurs
→ event publisher
→ WebSocket channel
→ frontend event listener
→ state update
→ visual/audio feedback
```

### Frontend-Backend Error Handling

- Every backend error should be normalized into:
  - machine-readable code
  - human-readable message
  - optional remediation hint
- UI should distinguish:
  - invalid request
  - denied action
  - unavailable dependency
  - offline source failure
  - unexpected backend fault
- Sensitive-action denials should explain why execution stopped
- Long-running tasks should report progress or pending state instead of appearing frozen

---

## 6. Command Execution Pipeline

```text
Raw text / voice input
→ normalize text
→ synonym mapping
→ fuzzy matching
→ intent detection
→ slot extraction
→ confidence scoring
→ safety check
→ execution plan
→ action execution
→ response generation
→ UI / voice feedback
```

### Pipeline Responsibilities

1. **Normalize text**
   - Lowercase where relevant
   - Trim noise
   - Normalize mixed-language patterns and common transliterations

2. **Synonym mapping**
   - Map equivalent verbs, app names, and phrase variants

3. **Fuzzy matching**
   - Use `rapidfuzz` for typo tolerance and alias matching

4. **Intent detection**
   - Determine the likely requested capability

5. **Slot extraction**
   - Extract entities such as app name, time, website, filename, contact, or query

6. **Confidence scoring**
   - Quantify certainty before execution

7. **Safety check**
   - Classify action risk
   - Verify permissions
   - Trigger confirmation when required

8. **Execution plan**
   - Convert intent into structured executable steps

9. **Action execution**
   - Execute through the relevant service or automation adapter

10. **Response generation**
    - Produce clear human-facing feedback using preferred addressing style

11. **UI / voice feedback**
    - Send REST response and/or WebSocket events to frontend

---

## 7. Voice Pipeline

```text
Microphone capture
→ speech-to-text
→ command engine
→ response generation
→ text-to-speech
→ frontend status events
```

### Detailed Flow

1. User activates listening from the desktop UI
2. Frontend shows active listening state
3. Microphone audio is captured through the chosen voice input path
4. Speech-to-text converts audio into command text
5. Backend receives recognized text
6. Command engine processes the request
7. Backend generates response text and execution result
8. Text-to-speech produces spoken feedback
9. Frontend receives live events for:
   - listening
   - processing
   - confirmation required
   - completed
   - failed

### Design Constraints

- Text input must remain available as fallback
- Low-confidence speech should not directly trigger risky actions
- MVP voice logic should remain lightweight and free of paid dependencies

---

## 8. Database Architecture

SQLite is the local source of truth for profile data, preferences, logs, reminders, shortcuts, and assistant memory. The schema should favor clarity, migrations, and strong separation by domain.

| Table | Purpose |
|---|---|
| `user_profile` | Core identity and addressing preferences |
| `user_preferences` | Configurable assistant settings |
| `command_aliases` | Alternate command phrases and aliases |
| `intent_examples` | Example utterances for supported intents |
| `interaction_logs` | User requests, outcomes, timestamps |
| `conversation_sessions` | Grouped chat sessions |
| `conversation_messages` | Individual conversational messages |
| `app_shortcuts` | Known apps and launch metadata |
| `website_shortcuts` | Saved websites and aliases |
| `contacts` | Local contact directory |
| `message_drafts` | Generated WhatsApp/email drafts |
| `reminders` | Reminder definitions and status |
| `tasks` | Task records |
| `file_index` | Searchable file metadata |
| `file_action_history` | Confirmed file operations |
| `documents` | Tracked documents |
| `document_chunks` | Parsed document text chunks |
| `permission_rules` | Allowed/denied action rules |
| `security_events` | Sensitive action audit log |
| `web_cache` | Cached free-source responses |
| `smart_devices` | Future ESP32 device registry |
| `automation_workflows` | Saved reusable workflows |
| `automation_steps` | Ordered steps inside workflows |

### Database Guidelines

- Use migrations from the beginning
- Add indexes to frequent lookup columns
- Keep write operations narrow and explicit
- Avoid storing unnecessary sensitive data
- Use transaction boundaries for multi-step changes
- Maintain a clear retention policy for logs and cache entries

---

## 9. Security and Permission Model

### Safe Actions

Examples:

- Open approved app
- Open approved website
- Read reminders
- Search weather
- Search local files in allowed locations

These may execute immediately when confidence is high.

### Sensitive Actions

Examples:

- Rename or move files
- Open restricted folders
- Lock, sleep, shutdown, or restart the PC
- Modify permissions
- Execute multi-step automations

These require stricter validation and may require confirmation.

### Confirmation-Required Actions

Examples:

- Shutdown/restart
- File move/rename
- Any future send-message action
- Any automation containing sensitive steps
- Device control for safety-critical smart-home endpoints

### Audit Logs

`security_events` should record:

- timestamp
- user request
- action type
- risk level
- decision
- confirmation result
- outcome

### Local Data Privacy

- Data remains local by default
- Store only what is necessary for product value
- Make memory inspectable and resettable
- Avoid plaintext storage of secrets if credentials are introduced later
- Do not transmit local personal data to internet services unless explicitly needed and approved

---

## 10. Free Internet Source Strategy

### Weather

- Use free/public weather sources or public APIs with no paid dependency
- Cache short-lived responses to reduce repeated calls

### News RSS

- Prefer RSS feeds from reliable publishers or public aggregators
- Normalize headlines, timestamps, and source labels

### Dictionary

- Use free dictionary sources
- Return concise definitions and source-aware fallbacks

### Basic Web Lookup

- Use public web sources only where necessary
- Prefer lightweight retrieval over complex scraping

### Graceful Failure Rules

- If offline, say the system is offline
- If a source fails, report unavailability honestly
- Never fabricate fresh data
- Cache should be labeled by timestamp so stale information is not confused with live results

---

## 11. Performance Optimization for Low-End Laptops

### Lazy Loading

- Load nonessential pages and modules only when needed
- Defer heavy document parsing until a document is opened

### Low Polling

- Prefer events over repeated polling
- Keep background checks sparse and purposeful

### Lightweight Animations

- Use restrained Framer Motion effects
- Favor opacity and transform animations over layout-heavy motion

### Background Task Queue

- Run slower tasks such as indexing, parsing, and web fetches off the critical interaction path
- Report task state back through events

### No Heavy Local AI Model in MVP

- Use rules, fuzzy matching, retrieval, templates, and lightweight heuristics
- Keep the app fast on modest CPUs and limited RAM

### SQLite Optimization

- Index common lookups
- Keep transactions short
- Avoid unnecessary full-table scans
- Use caches carefully

### Avoid Always-Running Heavy Processing

- No permanent heavyweight inference loop
- No constant aggressive file scans
- No unnecessary background services when idle

---

## 12. Packaging Strategy

### Electron Packaging

- Package the desktop client into a Windows-friendly distributable
- Keep configuration externalized where safe
- Include frontend assets, icons, and required runtime glue

### Python Backend Packaging

- Package the FastAPI backend into a self-contained local runtime suitable for Windows distribution
- Ensure backend dependencies are pinned and reproducible

### Local Backend Startup Strategy

- Electron main process launches the local backend on app startup
- Frontend waits for backend health readiness before enabling dependent features
- App shutdown should terminate backend cleanly

### Windows Installer Goal

- Produce an installable Windows build suitable for non-technical users
- Preserve SQLite data across upgrades where appropriate
- Provide clear failure diagnostics

### Future Update Strategy

- Introduce controlled update checks later
- Keep migrations versioned
- Separate app versioning from data schema versioning

---

## 13. Development Principles

### Phase-by-Phase Development

Build Nexa AI in deliberate phases:

1. documentation
2. foundation
3. command core
4. desktop shell
5. modules
6. packaging
7. expansion

### Small Modules

- Prefer many clear modules over one oversized service
- Keep boundaries explicit
- Make replacement easier than entanglement

### Test After Each Phase

- Verify each layer before stacking more on top
- Add unit, integration, and smoke tests as the project grows
- Test on representative low-end Windows hardware early

### Never Implement All Features at Once

- Ship vertical slices
- Prove the command path before multiplying features
- Add complexity only after the core remains stable

### Keep Documentation Updated

- Update docs when architecture changes
- Treat documentation as part of the product, not a later cleanup task

---

## Closing Architecture Position

Nexa AI should feel futuristic at the surface and disciplined underneath. The correct technical shape is a light, local-first desktop system with a vivid UI, a strict backend boundary, a confirmation-aware automation core, and enough modularity that future capabilities such as ESP32 control can be added as new limbs rather than surgeries on the spine.
