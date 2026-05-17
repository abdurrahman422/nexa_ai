# Nexa AI — 30-Phase Production Roadmap

## Core Development Rules

### Development Rule: One Phase at a Time

Complete, test, and commit one phase before beginning the next. Nexa AI should grow through stable layers, not through a single oversized implementation rush.

### Codex Rule: One Sub-Step Prompt at a Time

When working with Codex, provide one sub-step prompt at a time. Small prompts produce clearer code, easier testing, and fewer hidden mistakes.

### Beginner Workflow

1. Give Codex prompt  
2. Run command  
3. Test  
4. Fix error  
5. Commit

### Branching Strategy

- `main` — stable production-ready branch
- `dev` — integration branch for completed phases
- `feature/phase-name` — short-lived branch for each phase

### Definition of Done for Each Phase

A phase is complete only when:

- all five sub-steps are finished
- the expected output exists
- the phase test checklist passes
- documentation affected by the phase is updated
- the work is committed with the planned commit message

### Warning

Never ask Codex to build the full app at once. Build one phase, one sub-step, one verified result at a time.

---

## Phase 01: Planning & Blueprint

### Goal

Define the product, features, architecture, and delivery path before writing implementation code.

### 5 Sub-Steps

- **Step 1:** Write the product vision document
- **Step 2:** Write the feature requirements document
- **Step 3:** Write the technical architecture document
- **Step 4:** Write the 30-phase production roadmap
- **Step 5:** Review all documents for consistency, missing constraints, and repeated terminology

### Expected Output

A complete documentation foundation that guides every later phase.

### Test Checklist

- Product scope is clear
- MVP, V2, and future scope are separated
- Architecture matches feature requirements
- Constraints are repeated consistently
- Roadmap contains exactly 30 phases

### Git Commit Message

`docs: add phase 01 planning and blueprint documents`

---

## Phase 02: Monorepo Skeleton

### Goal

Create the initial repository structure and shared project conventions.

### 5 Sub-Steps

- **Step 1:** Define top-level folder structure
- **Step 2:** Add shared documentation and configuration placeholders
- **Step 3:** Add root-level README and contribution guidance
- **Step 4:** Add repository-wide formatting, linting, and ignore rules
- **Step 5:** Verify that the structure supports frontend, backend, docs, and future packages cleanly

### Expected Output

A clean monorepo skeleton ready for implementation work.

### Test Checklist

- Folder layout is understandable
- Root documentation exists
- Shared config conventions are documented
- No implementation modules are mixed together
- New contributors can understand where future work belongs

### Git Commit Message

`chore: create monorepo skeleton and shared conventions`

---

## Phase 03: Backend Core Foundation

### Goal

Establish the FastAPI backend foundation and backend project conventions.

### 5 Sub-Steps

- **Step 1:** Create backend application structure
- **Step 2:** Add configuration management strategy
- **Step 3:** Add health-check endpoint design
- **Step 4:** Add logging and error-handling foundation
- **Step 5:** Add first backend test scaffold

### Expected Output

A minimal but production-oriented FastAPI foundation.

### Test Checklist

- Backend starts successfully
- Health-check works
- Config loads correctly
- Errors are normalized
- Test runner can execute backend tests

### Git Commit Message

`feat: establish backend core foundation`

---

## Phase 04: Frontend Design System

### Goal

Create the visual language and reusable UI foundations for the cyberpunk/Jarvis-style experience.

### 5 Sub-Steps

- **Step 1:** Define color, spacing, typography, and motion tokens
- **Step 2:** Configure Tailwind design conventions
- **Step 3:** Design reusable buttons, panels, cards, and badges
- **Step 4:** Define Framer Motion animation guidelines
- **Step 5:** Create visual QA checklist for consistency and performance

### Expected Output

A coherent design system that future screens can reuse instead of reinventing.

### Test Checklist

- Design tokens are documented
- Reusable component list is clear
- Motion rules avoid unnecessary heaviness
- UI style matches Nexa AI vision
- Components are accessible and consistent

### Git Commit Message

`feat: define frontend design system foundation`

---

## Phase 05: Electron App Shell

### Goal

Create the secure desktop runtime shell around the future React experience.

### 5 Sub-Steps

- **Step 1:** Define Electron main-process responsibilities
- **Step 2:** Define secure preload bridge responsibilities
- **Step 3:** Define renderer startup flow
- **Step 4:** Define backend startup and shutdown lifecycle
- **Step 5:** Verify desktop app shell boundaries and security posture

### Expected Output

A desktop shell architecture that safely hosts the UI and backend connection.

### Test Checklist

- Main, preload, and renderer responsibilities are separated
- Backend lifecycle is documented
- Renderer avoids privileged direct access
- Startup flow is understandable
- Security boundary is explicit

### Git Commit Message

`feat: define electron app shell architecture`

---

## Phase 06: Sidebar & Topbar Layout

### Goal

Plan the primary application navigation frame.

### 5 Sub-Steps

- **Step 1:** Define persistent sidebar sections
- **Step 2:** Define topbar status elements
- **Step 3:** Define responsive behavior for smaller displays
- **Step 4:** Define active-state and navigation patterns
- **Step 5:** Validate layout against all planned modules

### Expected Output

A navigation blueprint that can support the full product without clutter.

### Test Checklist

- Every major module has a logical destination
- Navigation remains understandable for beginners
- Small-screen behavior is planned
- Status indicators are purposeful
- No critical screen is orphaned

### Git Commit Message

`docs: define sidebar and topbar layout plan`

---

## Phase 07: Splash Loading Screen

### Goal

Design the startup experience while backend readiness is being checked.

### 5 Sub-Steps

- **Step 1:** Define startup states
- **Step 2:** Define visual loading treatment
- **Step 3:** Define backend health-check dependency
- **Step 4:** Define startup timeout and failure behavior
- **Step 5:** Define transition into onboarding or dashboard

### Expected Output

A clear startup-state plan for a polished first impression.

### Test Checklist

- Loading state is finite
- Backend readiness is represented
- Failure state is recoverable
- Transition destination is correct
- Visual design remains lightweight

### Git Commit Message

`docs: specify splash loading screen behavior`

---

## Phase 08: Welcome Onboarding

### Goal

Plan the first-run welcome flow that introduces Nexa AI without overwhelming users.

### 5 Sub-Steps

- **Step 1:** Define onboarding entry conditions
- **Step 2:** Define welcome content and tone
- **Step 3:** Define privacy and local-first messaging
- **Step 4:** Define step progression and skip rules
- **Step 5:** Define completion handoff to profile setup

### Expected Output

A beginner-friendly onboarding flow specification.

### Test Checklist

- New users understand what Nexa AI does
- Privacy is explained early
- Flow is short enough to complete
- Skip behavior is intentional
- Profile setup follows naturally

### Git Commit Message

`docs: define welcome onboarding flow`

---

## Phase 09: Profile Setup

### Goal

Plan user identity, language, and preferred addressing setup.

### 5 Sub-Steps

- **Step 1:** Define required profile fields
- **Step 2:** Define Sir/Madam/name-based addressing options
- **Step 3:** Define language and Banglish preference options
- **Step 4:** Define validation and edit behavior
- **Step 5:** Define persistence and reset behavior

### Expected Output

A precise profile setup specification.

### Test Checklist

- Required fields are minimal
- Addressing options are clear
- Language preferences support mixed usage
- Profile can be edited later
- Reset behavior is safe

### Git Commit Message

`docs: define profile setup requirements`

---

## Phase 10: Voice & Permissions Setup

### Goal

Plan first-run microphone access and permission education.

### 5 Sub-Steps

- **Step 1:** Define microphone permission request flow
- **Step 2:** Define voice input troubleshooting guidance
- **Step 3:** Define fallback text input path
- **Step 4:** Define permission explanation copy
- **Step 5:** Define completion and retry states

### Expected Output

A trustworthy voice-permission setup experience.

### Test Checklist

- Mic permission request is understandable
- Failure path is documented
- Text fallback exists
- User is not forced into voice mode
- Permission wording is transparent

### Git Commit Message

`docs: specify voice and permissions setup`

---

## Phase 11: SQLite Database System

### Goal

Design the local persistence system and migration discipline.

### 5 Sub-Steps

- **Step 1:** Finalize table list from requirements
- **Step 2:** Define schema ownership by module
- **Step 3:** Define migration strategy
- **Step 4:** Define indexing and retention rules
- **Step 5:** Define backup, reset, and integrity-check expectations

### Expected Output

A maintainable SQLite data architecture.

### Test Checklist

- All required modules map to tables
- Migration rules are clear
- Lookup-heavy tables have indexing guidance
- Sensitive data is minimized
- Reset and integrity rules are defined

### Git Commit Message

`docs: define sqlite database system`

---

## Phase 12: REST API & WebSocket Event Bus

### Goal

Plan local frontend-backend communication contracts.

### 5 Sub-Steps

- **Step 1:** Define REST domain groups
- **Step 2:** Define common response and error shapes
- **Step 3:** Define WebSocket event names
- **Step 4:** Define reconnect and health behavior
- **Step 5:** Define API versioning and documentation approach

### Expected Output

A stable communication contract for UI and backend development.

### Test Checklist

- REST and event responsibilities are distinct
- Errors have consistent format
- WebSocket events cover live UX needs
- Reconnect behavior is defined
- API versioning path exists

### Git Commit Message

`docs: design rest api and websocket event bus`

---

## Phase 13: Command Understanding Engine V1

### Goal

Define the first version of lightweight multilingual command interpretation.

### 5 Sub-Steps

- **Step 1:** Define supported MVP intents
- **Step 2:** Define normalization rules
- **Step 3:** Define synonym and alias strategy
- **Step 4:** Define rapidfuzz typo-tolerance strategy
- **Step 5:** Define ambiguity and fallback handling

### Expected Output

A command-understanding specification ready for MVP implementation.

### Test Checklist

- English examples are covered
- Bengali examples are covered
- Banglish examples are covered
- Typo tolerance is planned
- Ambiguous input has safe fallback behavior

### Git Commit Message

`docs: define command understanding engine v1`

---

## Phase 14: Slot Extraction & Execution Plan

### Goal

Define how intents become structured, safe, executable actions.

### 5 Sub-Steps

- **Step 1:** Define slot types by intent
- **Step 2:** Define missing-slot clarification rules
- **Step 3:** Define confidence scoring inputs
- **Step 4:** Define execution-plan schema
- **Step 5:** Define safe rejection cases

### Expected Output

A bridge specification between language understanding and action execution.

### Test Checklist

- Every MVP intent has required slots
- Missing data triggers clarification
- Confidence rules are explicit
- Execution plan separates intent from action
- Unsafe plans are rejected

### Git Commit Message

`docs: specify slot extraction and execution planning`

---

## Phase 15: Command Understanding UI

### Goal

Plan how the product exposes recognized commands, uncertainty, and clarifications to users.

### 5 Sub-Steps

- **Step 1:** Define transcript display
- **Step 2:** Define recognized-intent display
- **Step 3:** Define clarification prompt patterns
- **Step 4:** Define confidence/error messaging
- **Step 5:** Define correction-feedback loop

### Expected Output

A user-facing UX plan for transparent command understanding.

### Test Checklist

- Users can see what was heard
- Users can understand what the system plans to do
- Clarifications are concise
- Errors are actionable
- Corrections can improve future handling

### Git Commit Message

`docs: define command understanding ui behavior`

---

## Phase 16: Main Dashboard / AI Command Center

### Goal

Plan the central operational screen of Nexa AI.

### 5 Sub-Steps

- **Step 1:** Define primary dashboard widgets
- **Step 2:** Define real-time system status areas
- **Step 3:** Define recent activity display
- **Step 4:** Define reminder/task visibility
- **Step 5:** Define responsive and performance behavior

### Expected Output

A focused dashboard specification that acts as the assistant command center.

### Test Checklist

- Dashboard supports daily use
- Information hierarchy is clear
- Critical statuses are visible
- Performance remains lightweight
- Layout works on lower-resolution screens

### Git Commit Message

`docs: define main dashboard command center`

---

## Phase 17: App & Website Launcher

### Goal

Plan rapid launching of apps and websites through natural commands.

### 5 Sub-Steps

- **Step 1:** Define supported launcher actions
- **Step 2:** Define app and website shortcut records
- **Step 3:** Define alias resolution rules
- **Step 4:** Define unknown-target behavior
- **Step 5:** Define favorite-management UX

### Expected Output

A complete app/site launcher specification.

### Test Checklist

- App launch flow is clear
- Website launch flow is clear
- Aliases are supported
- Unknown names fail gracefully
- Favorites can be managed

### Git Commit Message

`docs: define app and website launcher`

---

## Phase 18: System Control Engine

### Goal

Plan safe control of supported Windows actions.

### 5 Sub-Steps

- **Step 1:** Define safe system-control actions
- **Step 2:** Define sensitive system-control actions
- **Step 3:** Define confirmation requirements
- **Step 4:** Define unsupported-device handling
- **Step 5:** Define action logging expectations

### Expected Output

A risk-aware system-control specification.

### Test Checklist

- Safe and sensitive controls are separated
- Shutdown/restart rules are explicit
- Unsupported actions return useful feedback
- Audit expectations are defined
- UI confirmation needs are clear

### Git Commit Message

`docs: define system control engine`

---

## Phase 19: YouTube & Browser Automation

### Goal

Plan browser and media control capabilities that remain safe and lightweight.

### 5 Sub-Steps

- **Step 1:** Define supported YouTube actions
- **Step 2:** Define supported browser actions
- **Step 3:** Define query-building rules
- **Step 4:** Define limitations and unsupported actions
- **Step 5:** Define browser-safety rules

### Expected Output

A bounded browser automation specification.

### Test Checklist

- Supported actions are useful
- Unsupported actions are documented
- Search behavior is predictable
- Sensitive browser actions are restricted
- Automation remains lightweight

### Git Commit Message

`docs: define youtube and browser automation`

---

## Phase 20: Web Intelligence Module

### Goal

Plan live information retrieval from free/public sources only.

### 5 Sub-Steps

- **Step 1:** Define weather data strategy
- **Step 2:** Define RSS/news strategy
- **Step 3:** Define dictionary strategy
- **Step 4:** Define web cache rules
- **Step 5:** Define offline and source-failure behavior

### Expected Output

A free-source web intelligence plan with graceful degradation.

### Test Checklist

- No paid API dependency is introduced
- Source types are identified
- Cache behavior is clear
- Offline messaging is honest
- Stale/live distinctions are defined

### Git Commit Message

`docs: define web intelligence module`

---

## Phase 21: Voice STT System

### Goal

Plan speech-to-text support suitable for low-end Windows laptops.

### 5 Sub-Steps

- **Step 1:** Define STT requirements
- **Step 2:** Compare feasible free STT approaches
- **Step 3:** Define MVP microphone-to-text flow
- **Step 4:** Define confidence and failure handling
- **Step 5:** Define performance expectations

### Expected Output

A practical STT system plan for MVP implementation.

### Test Checklist

- Free options are prioritized
- Low-end device constraints are considered
- Failure path is clear
- Confidence affects safety
- Text fallback remains available

### Git Commit Message

`docs: define voice stt system`

---

## Phase 22: Text-to-Speech System

### Goal

Plan spoken responses that are lightweight and personalized.

### 5 Sub-Steps

- **Step 1:** Define TTS requirements
- **Step 2:** Define free TTS option strategy
- **Step 3:** Define response queue behavior
- **Step 4:** Define interruption and mute behavior
- **Step 5:** Define persona-aware reply formatting

### Expected Output

A clear TTS specification for assistant responses.

### Test Checklist

- TTS has a free path
- Responses can be queued safely
- User can mute or interrupt
- Reply style respects profile
- Performance remains suitable for low-end devices

### Git Commit Message

`docs: define text to speech system`

---

## Phase 23: Always-On Voice Mode

### Goal

Plan future hands-free listening while respecting performance and privacy.

### 5 Sub-Steps

- **Step 1:** Define wake-word or activation strategy options
- **Step 2:** Define privacy expectations
- **Step 3:** Define CPU/battery limits
- **Step 4:** Define idle and sleep behavior
- **Step 5:** Define MVP exclusion and later rollout conditions

### Expected Output

A future-ready always-on voice plan without forcing it into MVP.

### Test Checklist

- Privacy tradeoffs are explicit
- Resource concerns are documented
- Activation behavior is bounded
- MVP exclusion is clear
- Future entry conditions are defined

### Git Commit Message

`docs: plan always on voice mode`

---

## Phase 24: Natural Reply & Persona Engine

### Goal

Plan respectful, human-like responses that use Sir/Madam/name-based addressing.

### 5 Sub-Steps

- **Step 1:** Define response tone rules
- **Step 2:** Define address-style insertion rules
- **Step 3:** Define success, failure, and clarification templates
- **Step 4:** Define multilingual reply behavior
- **Step 5:** Define consistency and overuse limits

### Expected Output

A reply-engine specification that gives Nexa AI a coherent voice.

### Test Checklist

- Replies sound respectful
- Address style is applied correctly
- Failure messages remain useful
- Multilingual behavior is planned
- Persona does not reduce clarity

### Git Commit Message

`docs: define natural reply and persona engine`

---

## Phase 25: Contacts, WhatsApp & Email Draft

### Goal

Plan local contacts and safe message-drafting assistance.

### 5 Sub-Steps

- **Step 1:** Define contact fields
- **Step 2:** Define draft-generation inputs
- **Step 3:** Define review-before-use workflow
- **Step 4:** Define WhatsApp/email draft differences
- **Step 5:** Define explicit non-sending rule for MVP

### Expected Output

A safe communications-assistant specification.

### Test Checklist

- Contacts are locally stored
- Draft inputs are clear
- User review is mandatory
- Channels are distinguished
- Auto-send is excluded from MVP

### Git Commit Message

`docs: define contacts and message draft module`

---

## Phase 26: File Search & File Organizer

### Goal

Plan local file discovery and cautious organization workflows.

### 5 Sub-Steps

- **Step 1:** Define searchable locations
- **Step 2:** Define query and filter capabilities
- **Step 3:** Define file index strategy
- **Step 4:** Define move/rename confirmation rules
- **Step 5:** Define deletion limits and future expansion

### Expected Output

A practical and safe file-assistant plan.

### Test Checklist

- File search scope is explicit
- Partial-name search is supported
- Indexing strategy is lightweight
- Destructive behavior is constrained
- Organizer actions are confirmation-based

### Git Commit Message

`docs: define file search and organizer`

---

## Phase 27: PDF & Document Assistant

### Goal

Plan document reading, search, summarization, and question support.

### 5 Sub-Steps

- **Step 1:** Define supported document types
- **Step 2:** Define extraction pipeline
- **Step 3:** Define chunking and retrieval strategy
- **Step 4:** Define summary and Q&A boundaries
- **Step 5:** Define poor-extraction fallback behavior

### Expected Output

A lightweight document-assistant specification.

### Test Checklist

- Supported file types are listed
- Extraction path is defined
- Retrieval avoids heavy AI dependency
- Summary limits are realistic
- Bad documents fail transparently

### Git Commit Message

`docs: define pdf and document assistant`

---

## Phase 28: Reminder, Task & Study Assistant

### Goal

Plan productivity features that support daily use and student workflows.

### 5 Sub-Steps

- **Step 1:** Define reminder fields and states
- **Step 2:** Define task fields and completion states
- **Step 3:** Define study-session concepts
- **Step 4:** Define scheduler and notification behavior
- **Step 5:** Define recurrence as later expansion

### Expected Output

A clear productivity-assistant specification.

### Test Checklist

- Reminders and tasks are distinct
- Study workflows are represented
- Notification path is clear
- Ambiguous times trigger clarification
- Recurrence is not overbuilt too early

### Git Commit Message

`docs: define reminder task and study assistant`

---

## Phase 29: Automation Builder

### Goal

Plan reusable multi-step workflows without compromising safety.

### 5 Sub-Steps

- **Step 1:** Define workflow structure
- **Step 2:** Define supported action types
- **Step 3:** Define step ordering and validation
- **Step 4:** Define sensitive-step confirmation rules
- **Step 5:** Define run history and failure behavior

### Expected Output

A modular automation-builder specification.

### Test Checklist

- Workflow model is clear
- Unsupported actions are excluded
- Ordering rules exist
- Sensitive steps remain guarded
- Failures are logged and visible

### Git Commit Message

`docs: define automation builder`

---

## Phase 30: Security, Smart Home, Packaging & Release

### Goal

Finalize the product path by consolidating security, future ESP32 direction, packaging, and release readiness.

### 5 Sub-Steps

- **Step 1:** Finalize security categories, confirmations, and audit expectations
- **Step 2:** Define ESP32 integration boundary for future work
- **Step 3:** Define Windows packaging and installer path
- **Step 4:** Define release-readiness checklist
- **Step 5:** Define post-release maintenance and documentation process

### Expected Output

A final release blueprint that connects safety, extensibility, and shipping discipline.

### Test Checklist

- Security rules are complete
- Smart-home future path is modular
- Packaging plan is realistic
- Release checklist is actionable
- Maintenance responsibilities are defined

### Git Commit Message

`docs: finalize security smart home packaging and release roadmap`
