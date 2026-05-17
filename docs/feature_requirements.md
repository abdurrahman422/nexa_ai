# Nexa AI — Feature Requirements Document

## Document Purpose

This document defines the functional, technical, safety, and release requirements for Nexa AI, a futuristic Windows desktop personal voice assistant built with an Electron + React desktop interface and a Python FastAPI automation backend.

The system must support Bengali, English, Bangla-English mixed, and Banglish-style commands; use local SQLite memory; avoid paid APIs; stay lightweight enough for low-end Windows laptops; and remain modular, beginner-friendly, and production-oriented.

---

# 1. Onboarding & Profile

## Purpose

Help users configure Nexa AI quickly, establish how the assistant should address them, and collect only the preferences necessary for a personalized experience.

## User-Facing Features

- First-run welcome flow
- Name, preferred title, and language preference setup
- Choice of assistant address style: Sir, Madam, custom name, or neutral
- Voice input setup guidance
- Optional startup behavior preference
- Basic privacy explanation

## Example Voice/Text Commands

- “Call me Rahim.”
- “Address me as Sir.”
- “Use Banglish with me.”
- “Change my name to Ayesha.”

## Frontend Responsibilities

- Present onboarding screens and progress
- Collect user profile preferences
- Display microphone setup status
- Provide clear privacy and permission explanations

## Backend Responsibilities

- Store profile preferences
- Validate profile settings
- Expose profile read/update endpoints
- Apply addressing preference to assistant replies

## Required Database Tables

- `user_profile`
- `user_preferences`

## Required Free Libraries/Tools

- SQLite
- Electron local storage only for temporary UI state if needed

## Safety and Confirmation Rules

- No sensitive system permissions requested without explanation
- Profile deletion or reset must require confirmation

## Priority

- **MVP**

## Test Checklist

- New user can complete onboarding
- Profile persists after restart
- Address style is reflected in replies
- User can update name and preferred language
- Reset flow requires confirmation

---

# 2. Voice Core

## Purpose

Provide reliable voice input and assistant response handling for daily desktop interaction.

## User-Facing Features

- Push-to-talk or click-to-talk voice input
- Visual listening, processing, and speaking states
- Speech-to-text input
- Text-to-speech responses
- Fallback text input when voice is unavailable

## Example Voice/Text Commands

- “Nexa, open Chrome.”
- “Remind me at 8 PM.”
- “What is the weather today?”

## Frontend Responsibilities

- Show microphone controls and state animation
- Display transcript and assistant response
- Surface microphone errors clearly
- Allow switching between voice and text input

## Backend Responsibilities

- Receive transcribed command text
- Process request through command pipeline
- Return response text and action metadata
- Coordinate with text-to-speech layer

## Required Database Tables

- `interaction_logs`
- `voice_settings`

## Required Free Libraries/Tools

- Free speech-to-text option suitable for MVP
- Free text-to-speech option supported on Windows or through open libraries

## Safety and Confirmation Rules

- Do not trigger destructive actions from ambiguous speech
- Repeat or request confirmation when confidence is low

## Priority

- **MVP**

## Test Checklist

- Voice input state changes correctly
- Text fallback works
- Transcript is displayed accurately enough for supported commands
- Low-confidence commands do not execute unsafe actions
- Voice and text requests share the same backend pipeline

---

# 3. Command Understanding

## Purpose

Interpret user intent across Bengali, English, mixed Bangla-English, and Banglish phrasing with tolerance for typos and variations.

## User-Facing Features

- Multiple ways to express the same command
- Support for mixed-language commands
- Typo tolerance
- Graceful clarification when intent is unclear
- Human-like replies with Sir/Madam/name-based addressing

## Example Voice/Text Commands

- “Chrome open koro.”
- “YouTube e lo-fi song chalao.”
- “Kal 7 tay amake porar reminder dao.”
- “Open my downloads folder.”
- “Wether bolo ajker.”

## Frontend Responsibilities

- Display recognized intent and clarification prompts when needed
- Show suggestions if multiple actions are possible

## Backend Responsibilities

- Normalize input text
- Handle transliteration variants and aliases
- Perform fuzzy matching
- Map text to intent and entities
- Return confidence scores and clarification needs

## Required Database Tables

- `command_aliases`
- `intent_examples`
- `interaction_logs`

## Required Free Libraries/Tools

- `rapidfuzz` or equivalent free fuzzy-matching library
- Lightweight rule-based NLP utilities

## Safety and Confirmation Rules

- Destructive or sensitive commands require stronger confidence
- If multiple intents are plausible, ask before acting

## Priority

- **MVP**

## Test Checklist

- English commands resolve correctly
- Bengali commands resolve correctly
- Mixed-language commands resolve correctly
- Common typos resolve correctly
- Ambiguous commands trigger clarification
- Replies use configured addressing style

---

# 4. Main Dashboard

## Purpose

Provide the central visual control surface for Nexa AI.

## User-Facing Features

- Futuristic cyberpunk/Jarvis-style dashboard
- Microphone state
- Recent commands
- Upcoming reminders
- Quick actions
- System status indicators
- Connection status for online features

## Example Voice/Text Commands

- “Show my reminders.”
- “What did I ask recently?”
- “Open dashboard.”

## Frontend Responsibilities

- Render dashboard cards and assistant states
- Display logs, reminders, and quick actions
- Maintain responsive layout on smaller screens

## Backend Responsibilities

- Provide dashboard data summaries
- Return recent activity and reminder counts
- Return online/offline capability status

## Required Database Tables

- `interaction_logs`
- `reminders`
- `system_status_cache`

## Required Free Libraries/Tools

- React
- Electron

## Safety and Confirmation Rules

- Sensitive data shown on dashboard should be minimized by default

## Priority

- **MVP**

## Test Checklist

- Dashboard loads quickly
- Reminder card reflects database data
- Recent command list updates after use
- Offline status appears correctly
- Layout remains usable on low-resolution screens

---

# 5. App & Website Launcher

## Purpose

Let users open installed applications and common websites through natural commands.

## User-Facing Features

- Launch applications by name
- Open saved websites
- Support aliases such as “browser” for Chrome/Edge preference
- Add/edit favorite websites

## Example Voice/Text Commands

- “Open Chrome.”
- “Discord kholo.”
- “Open YouTube.”
- “Study portal open koro.”

## Frontend Responsibilities

- Show launch results and failures
- Manage favorite apps/sites and aliases

## Backend Responsibilities

- Resolve app paths and aliases
- Launch approved applications
- Open URLs in browser
- Store and retrieve favorites

## Required Database Tables

- `app_shortcuts`
- `website_shortcuts`
- `command_aliases`

## Required Free Libraries/Tools

- Native Windows process launching utilities

## Safety and Confirmation Rules

- Opening approved apps/sites does not require confirmation
- Unknown executable paths require caution and validation

## Priority

- **MVP**

## Test Checklist

- Known app launches successfully
- Website alias opens correct URL
- Unknown alias fails gracefully
- User-defined shortcuts persist

---

# 6. System Control

## Purpose

Allow safe control of common desktop functions.

## User-Facing Features

- Volume up/down/mute
- Brightness where supported
- Lock screen
- Sleep, shutdown, restart with confirmation
- Open folders and common Windows utilities

## Example Voice/Text Commands

- “Volume 20 percent koro.”
- “Mute kore dao.”
- “Lock my PC.”
- “Shutdown computer.”

## Frontend Responsibilities

- Show action result
- Present confirmation dialogs for sensitive commands

## Backend Responsibilities

- Execute approved OS commands
- Detect unsupported hardware functions
- Log sensitive actions

## Required Database Tables

- `permission_rules`
- `security_events`

## Required Free Libraries/Tools

- Native Windows command utilities
- Free Windows automation libraries where needed

## Safety and Confirmation Rules

- Shutdown, restart, sleep, and similar actions require confirmation
- Ambiguous commands must not trigger system state changes

## Priority

- **MVP**

## Test Checklist

- Safe controls execute correctly
- Unsupported actions return a clear message
- Shutdown/restart require confirmation
- Actions are logged when appropriate

---

# 7. YouTube & Browser Automation

## Purpose

Help users control media and browser workflows through voice.

## User-Facing Features

- Open YouTube searches
- Play/pause, next, previous where feasible
- Search the web
- Open tabs or URLs
- Basic browser navigation

## Example Voice/Text Commands

- “YouTube e Rabindra Sangeet chalao.”
- “Pause video.”
- “Search AI news.”
- “Open a new tab.”

## Frontend Responsibilities

- Show action acknowledgment
- Display browser automation status when active

## Backend Responsibilities

- Trigger browser URL actions
- Send supported automation commands
- Handle search query construction

## Required Database Tables

- `browser_preferences`
- `interaction_logs`

## Required Free Libraries/Tools

- Free browser automation utilities as applicable

## Safety and Confirmation Rules

- No automatic form submission for sensitive sites without confirmation
- Avoid unsafe arbitrary script execution

## Priority

- **MVP**

## Test Checklist

- YouTube search opens expected result page
- Browser search opens correctly
- Supported playback controls work when available
- Unsupported browser actions fail gracefully

---

# 8. Web Intelligence

## Purpose

Provide fresh information from free/public internet sources when local knowledge is insufficient.

## User-Facing Features

- Weather lookup
- News headlines
- Dictionary definitions
- Basic web facts
- Online/offline awareness

## Example Voice/Text Commands

- “Ajker weather bolo.”
- “Latest tech news bolo.”
- “Meaning of resilient?”
- “Dhaka weather today.”

## Frontend Responsibilities

- Display sourced answers clearly
- Show loading and offline states
- Distinguish live internet answers from local responses

## Backend Responsibilities

- Call free/public data sources
- Normalize responses
- Cache lightweight results where appropriate
- Handle source failures gracefully

## Required Database Tables

- `web_cache`
- `interaction_logs`

## Required Free Libraries/Tools

- Public weather APIs or public weather sources
- Public dictionary sources
- RSS feeds or other free news sources

## Safety and Confirmation Rules

- Clearly identify uncertain or unavailable live information
- Do not fabricate online results when sources fail

## Priority

- **MVP**

## Test Checklist

- Weather query returns live data
- News query returns current headlines
- Dictionary query returns definition
- Offline mode gives a clear fallback message
- Failed external source does not crash the app

---

# 9. AI Chat & Conversation

## Purpose

Support natural interaction beyond strict commands while staying lightweight and useful in the MVP.

## User-Facing Features

- Conversational responses
- Human-like addressing
- Follow-up questions
- Simple productivity help
- Lightweight local or rules-based conversational behavior in MVP

## Example Voice/Text Commands

- “What can you do?”
- “Help me plan today.”
- “Can you explain this simply?”

## Frontend Responsibilities

- Render chat history
- Show assistant typing/processing state
- Separate action responses from general chat where useful

## Backend Responsibilities

- Route conversational requests
- Use templates, rules, and lightweight logic in MVP
- Preserve short conversational context

## Required Database Tables

- `conversation_sessions`
- `conversation_messages`

## Required Free Libraries/Tools

- Lightweight rule-based utilities

## Safety and Confirmation Rules

- Do not present speculative answers as facts
- Sensitive real-world advice should remain cautious and limited

## Priority

- **V2**

## Test Checklist

- Basic chat works without paid APIs
- Address style remains consistent
- Short context is preserved
- Unsupported questions receive honest fallback responses

---

# 10. Contacts, WhatsApp & Email Draft

## Purpose

Help users prepare messages faster without sending them unintentionally.

## User-Facing Features

- Save contacts
- Draft WhatsApp messages
- Draft email messages
- Support tone hints such as formal, polite, short

## Example Voice/Text Commands

- “Write a polite email to my teacher about missing class.”
- “Draft a WhatsApp message to Rafi saying I will be late.”
- “Save Tanvir as my project partner.”

## Frontend Responsibilities

- Show generated draft before use
- Allow editing and copy actions
- Manage contacts

## Backend Responsibilities

- Store contacts
- Generate template-based drafts in MVP
- Resolve contact names

## Required Database Tables

- `contacts`
- `message_drafts`

## Required Free Libraries/Tools

- None required beyond local logic in MVP

## Safety and Confirmation Rules

- Never auto-send messages in MVP
- Require user review before copying, opening, or sending later integrations

## Priority

- **MVP**

## Test Checklist

- Contact can be created and retrieved
- Draft is generated with requested tone
- No message is sent automatically
- Missing contact triggers clarification

---

# 11. File Search & File Organizer

## Purpose

Help users find and lightly organize local files through natural commands.

## User-Facing Features

- Search files by name, type, or folder
- Open result location
- Move or rename files with confirmation
- Suggest simple organization actions

## Example Voice/Text Commands

- “Find my PDF notes.”
- “Show files named assignment.”
- “Move this file to Documents.”

## Frontend Responsibilities

- Display search results
- Show file metadata and candidate actions
- Present confirmation dialog for modifications

## Backend Responsibilities

- Search allowed directories
- Index lightweight metadata if needed
- Perform file actions safely
- Record actions

## Required Database Tables

- `file_index`
- `file_action_history`

## Required Free Libraries/Tools

- Native filesystem tools

## Safety and Confirmation Rules

- Renaming, moving, or deleting requires confirmation
- Deletion should be excluded from MVP unless safely reversible

## Priority

- **MVP**

## Test Checklist

- File search returns matching results
- Search handles partial names
- Move/rename prompts for confirmation
- Unsupported or missing paths fail gracefully

---

# 12. PDF & Document Assistant

## Purpose

Help users extract value from local study and work documents.

## User-Facing Features

- Open PDF/document
- Extract text where possible
- Summarize document sections
- Answer simple questions from document content

## Example Voice/Text Commands

- “Summarize this PDF.”
- “What is chapter 2 about?”
- “Find where mitochondria is mentioned.”

## Frontend Responsibilities

- Show selected document
- Display extracted text snippets, summaries, and answers

## Backend Responsibilities

- Parse supported documents
- Extract text
- Run lightweight summarization or retrieval-based logic
- Track recent documents

## Required Database Tables

- `documents`
- `document_chunks`
- `document_queries`

## Required Free Libraries/Tools

- Free PDF/document parsing libraries

## Safety and Confirmation Rules

- Do not modify original documents without explicit instruction
- Be transparent when extraction quality is poor

## Priority

- **MVP**

## Test Checklist

- Supported PDF text extraction works
- Search within document works
- Summary generation works at MVP level
- Corrupt or scanned files fail gracefully

---

# 13. Reminder, Task & Study Assistant

## Purpose

Support personal productivity, revision, and follow-through.

## User-Facing Features

- Create reminders
- View upcoming reminders
- Mark tasks complete
- Basic study schedule support
- Revision prompts

## Example Voice/Text Commands

- “Remind me to study math at 8 PM.”
- “What are my tasks today?”
- “Add physics revision tomorrow morning.”

## Frontend Responsibilities

- Show calendar/task views
- Display reminder states and completion
- Surface due items prominently

## Backend Responsibilities

- Parse reminder time
- Store reminders and tasks
- Trigger notifications
- Handle recurrence in later versions

## Required Database Tables

- `reminders`
- `tasks`
- `study_sessions`

## Required Free Libraries/Tools

- Local scheduling utilities

## Safety and Confirmation Rules

- If time is ambiguous, ask for clarification
- Editing or deleting reminders should require confirmation when ambiguous

## Priority

- **MVP**

## Test Checklist

- Reminder creation works
- Reminder persists after restart
- Due reminders appear on time
- Ambiguous date/time requests trigger clarification
- Task completion updates correctly

---

# 14. Automation Builder

## Purpose

Allow users to combine repeated actions into reusable workflows.

## User-Facing Features

- Create named automations from simple steps
- Run saved automation by command
- Edit or disable automation

## Example Voice/Text Commands

- “Create study mode: open Chrome, open notes, mute notifications.”
- “Run study mode.”

## Frontend Responsibilities

- Provide automation editor
- Show ordered steps and validation

## Backend Responsibilities

- Store automation definitions
- Validate supported actions
- Execute steps sequentially with logs

## Required Database Tables

- `automations`
- `automation_steps`
- `automation_runs`

## Required Free Libraries/Tools

- Internal orchestration only

## Safety and Confirmation Rules

- Sensitive steps require confirmation during creation or execution
- Invalid or risky actions must be rejected

## Priority

- **V2**

## Test Checklist

- Automation can be created
- Steps run in order
- Failed step is logged
- Sensitive automation requires confirmation

---

# 15. Security & Permissions

## Purpose

Protect users from accidental, unsafe, or unauthorized actions.

## User-Facing Features

- Permission prompts
- Trusted action settings
- Confirmation prompts
- Security history

## Example Voice/Text Commands

- “Allow file search in Downloads.”
- “Show recent sensitive actions.”

## Frontend Responsibilities

- Present permission dialogs clearly
- Show what an action will do before approval
- Expose permission settings

## Backend Responsibilities

- Enforce permission rules
- Classify actions by risk level
- Record security events
- Block unauthorized actions

## Required Database Tables

- `permission_rules`
- `security_events`

## Required Free Libraries/Tools

- Native OS permission checks where applicable

## Safety and Confirmation Rules

- Destructive actions require confirmation
- Access to user files must be scoped
- Secrets must not be stored in plain text if introduced later

## Priority

- **MVP**

## Test Checklist

- Permission-denied actions are blocked
- Confirmation is required for sensitive actions
- Security event logs are created
- Rules persist after restart

---

# 16. Memory & Personalization

## Purpose

Allow Nexa AI to remember useful preferences locally without depending on cloud services.

## User-Facing Features

- Remember preferred name/title
- Remember favorite apps/sites
- Remember recent actions
- Remember lightweight preferences

## Example Voice/Text Commands

- “Remember that I prefer Edge.”
- “Call me Madam from now on.”
- “What apps do I use most?”

## Frontend Responsibilities

- Show editable preferences
- Explain what is remembered locally

## Backend Responsibilities

- Store and retrieve SQLite-backed preferences
- Keep data schema maintainable
- Use personalization in responses and routing

## Required Database Tables

- `user_profile`
- `user_preferences`
- `interaction_logs`

## Required Free Libraries/Tools

- SQLite

## Safety and Confirmation Rules

- Local memory should be inspectable and resettable
- Sensitive data storage should be minimized

## Priority

- **MVP**

## Test Checklist

- Preferences persist
- Personalization affects replies
- User can inspect stored preferences
- Memory reset works with confirmation

---

# 17. ESP32 Smart Home Control

## Purpose

Extend Nexa AI beyond desktop automation into low-cost smart home control.

## User-Facing Features

- Control connected devices such as lights or fans
- Show device state
- Trigger device scenes

## Example Voice/Text Commands

- “Turn on study room light.”
- “Fan off kore dao.”
- “Run bedtime mode.”

## Frontend Responsibilities

- Device dashboard
- Device state display
- Scene controls

## Backend Responsibilities

- Communicate with ESP32 devices
- Store device registry
- Validate device commands

## Required Database Tables

- `smart_devices`
- `device_states`
- `device_events`

## Required Free Libraries/Tools

- ESP32 ecosystem tools
- Local-network protocols such as HTTP or MQTT using free tooling

## Safety and Confirmation Rules

- Critical appliances should require confirmation or explicit trust configuration
- Device failures must be reported clearly

## Priority

- **Future**

## Test Checklist

- Device can be discovered or registered
- State updates correctly
- Commands reach device
- Offline device errors are handled clearly

---

# 18. Packaging & Release

## Purpose

Deliver Nexa AI as a reliable Windows desktop product.

## User-Facing Features

- Installable Windows build
- Stable startup behavior
- Version visibility
- Update-ready architecture

## Example Voice/Text Commands

- “What version are you?”
- “Open settings.”

## Frontend Responsibilities

- Surface app version
- Provide release information and basic diagnostics

## Backend Responsibilities

- Support packaged deployment
- Maintain environment configuration
- Provide health checks and logs

## Required Database Tables

- `app_metadata`
- `release_history`

## Required Free Libraries/Tools

- Free Electron packaging tools
- Free Python packaging utilities

## Safety and Confirmation Rules

- Update or migration steps must preserve local data where possible
- Failed startup should provide recoverable diagnostics

## Priority

- **MVP**

## Test Checklist

- App can be packaged for Windows
- SQLite data survives restart
- Version info is visible
- Startup failures are logged

---

# MVP Feature List

- Onboarding and profile setup
- Voice input and text fallback
- Bengali, English, Bangla-English, and Banglish command handling
- Typo-tolerant command interpretation
- Human-like replies with configurable addressing
- Main dashboard
- App and website launcher
- Basic system controls
- YouTube and browser actions
- Weather, news, dictionary, and basic web intelligence from free/public sources
- Contacts storage and draft generation for WhatsApp/email
- File search and light file organization
- PDF/document assistance
- Reminders, tasks, and basic study support
- Security and permission foundation
- Local SQLite memory and personalization
- Windows packaging foundation

# V2 Feature List

- Richer conversational AI behavior without depending on paid APIs
- Automation builder
- More advanced reminder recurrence and productivity planning
- Stronger file organization workflows
- Deeper browser automation
- Expanded study assistant capabilities
- Better personalization and usage insights

# Future Feature List

- ESP32 smart home control
- Advanced plugin/extension system
- Multi-device ecosystem
- More capable offline intelligence if lightweight options become practical
- Advanced document workflows
- Deeper communication integrations

# Features Intentionally Excluded from MVP

- Paid API dependencies
- Heavy local AI models
- Fully autonomous message sending
- Advanced long-term conversational reasoning
- Complex workflow builder
- Smart home control
- Large-scale cloud sync
- Full browser replacement
- Destructive file operations without careful confirmation

# No-Paid-API Implementation Notes

- Prefer rule-based logic, public feeds, open endpoints, and local storage
- Use free/public sources for weather, dictionary, news, and other live information
- Design every module so paid services are optional, never mandatory
- Keep the product useful offline for local actions such as reminders, launching, file search, and profile memory
- Avoid architecture that assumes a commercial LLM is always available

# Low-End Laptop Performance Notes

- Keep startup lean and defer nonessential work
- Avoid heavy local AI models in the MVP
- Prefer SQLite over heavier infrastructure
- Use modular loading so inactive capabilities consume minimal resources
- Cache only lightweight data
- Minimize background polling
- Keep UI animation tasteful but efficient
- Use local automation and simple retrieval strategies before expensive processing
- Test on modest Windows hardware throughout development, not only at the end

# Cross-Cutting Product Requirements

- The product must remain modular and maintainable
- The codebase should be understandable to beginner developers while following production-ready boundaries
- All user-facing actions should fail clearly rather than silently
- Internet-dependent features must degrade gracefully when offline
- Sensitive operations must be auditable and confirmation-aware
- The assistant should sound respectful, concise, and personalized
