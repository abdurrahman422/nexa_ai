<div align="center">

# ⟡ NEXA AI ⟡
### A Next-Generation Desktop AI Operating System

<p><strong>Think.</strong> <strong>Speak.</strong> <strong>Search.</strong> <strong>Build.</strong> <strong>Automate.</strong></p>

<p>
<a href="#overview">Overview</a> •
<a href="#feature-status">Features</a> •
<a href="#architecture">Architecture</a> •
<a href="#roadmap">Roadmap</a> •
<a href="#installation">Installation</a>
</p>

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=22&duration=2800&pause=900&color=2EF2FF&center=true&vCenter=true&width=760&lines=LOCAL-FIRST+AI+DESKTOP+ASSISTANT;BANGLA+%7C+BANGLISH+%7C+ENGLISH;VOICE+%C2%B7+VISION+%C2%B7+AUTOMATION+%C2%B7+DEVELOPMENT;A+LIVING+AI+OPERATING+SYSTEM" alt="Nexa AI animated title" />

<br />

<img src="https://img.shields.io/badge/Platform-Windows-111827?style=for-the-badge&logo=windows&logoColor=white" alt="Windows" />
<img src="https://img.shields.io/badge/Desktop-Electron-0f172a?style=for-the-badge&logo=electron&logoColor=9FEAF9" alt="Electron" />
<img src="https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-0b1220?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React" />
<img src="https://img.shields.io/badge/Backend-FastAPI-0b1220?style=for-the-badge&logo=fastapi&logoColor=00D084" alt="FastAPI" />
<img src="https://img.shields.io/badge/AI-Multi--LLM%20Ready-0b1220?style=for-the-badge&logo=google-gemini&logoColor=8AB4F8" alt="AI" />

<br /><br />

> **Nexa AI is designed to feel less like an application and more like an intelligent operating layer for your computer.**

</div>

---

## ◈ Overview

**Nexa AI** is a Windows desktop AI assistant / AI Operating System project built around a local-first architecture.

Its long-term goal is to let a user interact with their computer naturally through text, voice, safe desktop actions, file discovery, web research, browser workflows, automation, and AI-powered development tools.

The project is intentionally modular so the AI model, voice engine, automation layer, interface, and desktop actions can evolve independently.

---

## ✦ Feature Status

> Status reflects the implementation summaries and repository state available during development. Items marked ❌ are planned and are not presented as completed.

| System | Status | Notes |
|---|:---:|---|
| Electron desktop application | ✅ | Desktop shell |
| React + TypeScript frontend | ✅ | Vite-based frontend |
| FastAPI backend | ✅ | Local API service |
| Token-driven design system | ✅ | Reusable visual tokens |
| Shared UI primitives | ✅ | Reusable component architecture |
| AI-OS navigation / shell | ✅ | Grouped navigation + command bar |
| Command preview | ✅ | Existing command workflow |
| Safe website launcher | ✅ | Whitelist + confirmation |
| Safe app launcher | ✅ | Whitelist + confirmation |
| Read-only local file search | ✅ | Safe-folder metadata search |
| Server-side dangerous-command blocking | ✅ | Safety layer |
| Audit / history foundation | ✅ | Existing audit/history infrastructure |
| 3D environment engine | ✅ | Three.js / React Three Fiber |
| Holographic AI Core / Earth | ✅ | Cinematic environment |
| Neural network environment | ✅ | Reactive scene |
| Energy / orbit / particle systems | ✅ | Environment layer |
| Cinematic HUD | ✅ | Holographic overlays |
| Interaction engine | ✅ | Event-driven motion infrastructure |
| AI activity reactions | ✅ | Thinking / command / voice states |
| Earth ↔ UI synchronization | ✅ | Energy / pulse synchronization |
| Cinematic AI processing states | ✅ | Multi-channel activity model |
| Multi-LLM provider architecture | 🚧 | Provider selection / failover direction |
| OpenAI provider | 🚧 | Verify exact adapter state in current tree |
| Gemini provider | 🚧 | Verify exact adapter state in current tree |
| Automatic quota failover | 🚧 | Planned provider failover behavior |
| End-to-end Bangla voice assistant | 🚧 | STT/TTS pipeline evolving |
| Push-to-talk | 🚧 | Voice UX target |
| Continuous voice conversation | ❌ | Planned |
| Natural AI voice reply | 🚧 | TTS architecture evolving |
| Web search answers | 🚧 | Controlled search workflow |
| Browser control | ❌ | Planned |
| YouTube control | ❌ | Planned |
| n8n automation | ❌ | Planned |
| Email automation | ❌ | Planned |
| WhatsApp workflows | ❌ | Planned |
| PDF / document intelligence | 🚧 | Foundation / roadmap |
| AI memory / long-term context | 🚧 | Planned architecture |
| RAG / vector search | ❌ | Planned |
| AI coding workspace | ❌ | Planned |
| Sandboxed website/project generation | ❌ | Planned |
| Calendar / reminders | 🚧 | Partial / roadmap |
| Windows production installer | 🚧 | Release work |

---

# 🧠 Product Vision

Nexa AI is being built toward a desktop AI layer where the user can speak or type natural requests such as:

> **“Nexa, open YouTube and search for the latest AI news.”**

> **“Find my latest PDF and summarize it.”**

> **“Draft an email to my boss based on this information.”**

And eventually:

> **“Create a new website project in a new workspace, build it, run the safe sandbox, fix any errors, and show me the result.”**

The final experience is intended to be voice-first when useful, text-first when faster, and automation-ready when safe.

---

# 🏗 Architecture

```text
┌──────────────────────────────────────────────────────────┐
│                         NEXA AI                           │
│                 Windows AI Operating System              │
└──────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   Voice / Chat        Desktop UI        Automation
        │                  │                  │
        ▼                  ▼                  ▼
   STT / LLM          React / Electron      n8n / APIs
        │                  │                  │
        └────────────┬─────┴───────┬──────────┘
                     ▼             ▼
                 AI Router      Tool Layer
                     │             │
          ┌──────────┼─────────┐   ├─ Apps
          │          │         │   ├─ Websites
          ▼          ▼         ▼   ├─ Files
        OpenAI     Gemini   Future  ├─ Browser
        Adapter    Adapter  Models  └─ Automation
                     │
                     ▼
               Unified Response
                     │
                     ▼
                Memory / Audit
```

---

# 🧩 Frontend Architecture

The current frontend is organized into reusable layers:

```text
frontend/src/
├── app/
├── components/
│   ├── hud/
│   ├── shell/
│   └── ui/
├── design/
├── environment/
├── interaction/
├── pages/
├── providers/
├── styles/
│   ├── tokens.css
│   ├── index.css
│   ├── legacy/
│   └── system/
└── main.tsx
```

## Design System

Token categories include:

- colors
- spacing
- typography
- radius
- glass surfaces
- shadows / elevation
- blur
- icons
- motion timing
- easing
- z-index

## Environment Engine

The environment layer is isolated under `src/environment/` and provides the cinematic AI ecosystem:

- 3D AI Core / Earth
- atmosphere
- stars
- particles
- neural network
- orbit systems
- energy rings
- energy beams
- nebula
- HUD-adjacent environment
- adaptive quality
- reduced-motion handling
- pause-on-blur
- lazy loading

## Interaction Engine

The interaction system provides an event-driven foundation for:

- AI thinking
- command execution states
- voice states
- notifications
- pointer tracking
- magnetic interactions
- reflections
- energy borders
- liquid-glass effects
- floating voice-orb behavior

---

# 🎙 Voice Pipeline

Target pipeline:

```text
Microphone
    │
    ▼
Speech-to-Text
    │
    ▼
Language / Intent Detection
    │
    ▼
AI Model Router
    │
    ▼
Response
    │
    ├──────────────► Text UI
    │
    └──────────────► Text-to-Speech
                           │
                           ▼
                       AI Voice
```

Target languages:

- বাংলা
- Banglish
- English

Planned voice capabilities:

- push-to-talk
- continuous listening
- interruption / barge-in
- voice activity visualization
- AI voice reply
- voice search
- voice browser control
- voice YouTube control
- voice automation

---

# 🤖 Multi-LLM Strategy

Nexa AI is intended to support a user-selectable multi-provider architecture.

### Planned provider selector

```text
AI Models
├── Smart Auto
├── OpenAI
├── Gemini
├── Claude
├── DeepSeek
└── Ollama
```

The user should eventually be able to choose:

- preferred provider
- preferred model
- provider priority
- automatic failover
- whether provider switching requires confirmation

### Automatic failover

```text
Selected Model
      │
      ▼
Generate response
      │
      ├── Success ─────────► Continue
      │
      └── 429 / quota / timeout
                    │
                    ▼
             Next enabled model
                    │
                    ▼
             Continue context
```

The conversation should remain intact when a provider changes.

---

# 🖥 Safe Desktop Control

Nexa AI is designed around:

- explicit whitelists
- backend-side validation
- confirmation before real actions
- dry-run / preview where appropriate
- dangerous-command blocking
- safe file containment
- audit logging

Example:

```text
User
  │
  ▼
Intent
  │
  ▼
Whitelist
  │
  ▼
Confirmation
  │
  ▼
Backend action
```

Unknown or dangerous actions must never be executed merely because a frontend requests them.

---

# 📁 File Intelligence

The safe baseline is read-only discovery.

Expected safe areas:

- Desktop
- Downloads
- Documents

Default model:

```text
Search
  │
  ▼
Metadata result
  │
  ▼
User review
```

Future work may add controlled document reading, summarization, attachment workflows, and sandboxed project operations with explicit permissions.

---

# 🌐 Web / Browser / YouTube Roadmap

## Browser

Planned:

- open browser
- navigate
- search
- read structured page content
- interact with selected page controls
- collect results
- summarize
- complete safe workflows

## YouTube

Planned:

- search
- open video
- play
- pause
- resume
- seek
- change video
- search by voice
- voice navigation

These should use controlled tools and permission boundaries.

---

# ⚙ Automation & n8n

n8n is planned as an optional workflow/orchestration layer.

Potential workflows:

- email drafting
- calendar actions
- notifications
- Google Sheets
- reports
- external APIs
- document workflows

Target architecture:

```text
Nexa AI
   │
   ▼
Workflow Intent
   │
   ▼
Permission / Preview
   │
   ▼
n8n Webhook
   │
   ▼
External Service
```

Sensitive actions should require explicit approval.

---

# 📧 Email & WhatsApp Roadmap

### Email

Planned:

- generate draft
- review draft
- edit draft
- confirm recipient
- confirm send
- send through configured provider

### WhatsApp

Planned safe workflow:

```text
Find contact
     ↓
Prepare message
     ↓
Preview
     ↓
Confirm
     ↓
Send
```

No hidden mass messaging.

---

# 💻 AI Development Workspace

One major future capability is an AI development workspace.

Example:

> “Nexa, build me a new website.”

Target workflow:

```text
User Request
     │
     ▼
Create Workspace
     │
     ▼
Generate Project
     │
     ▼
Write Code
     │
     ▼
Run Safe Build
     │
     ▼
Preview
     │
     ▼
Detect Errors
     │
     ▼
Fix
     │
     ▼
Rebuild
     │
     ▼
Show Result
```

The intended model is **sandboxed workspace execution**, not unrestricted access to the entire machine.

Potential safeguards:

- workspace directory isolation
- allowlisted tools
- approval gates
- audit logging
- resource limits
- safe process execution
- preview before external actions

---

# 🧠 Memory & RAG Roadmap

Future memory capabilities:

- short-term conversation memory
- long-term preferences
- workspace memory
- document memory
- semantic search
- embeddings
- vector storage
- RAG
- memory controls
- export/delete

---

# 🔐 Security Philosophy

Security is a first-class part of Nexa AI.

Core principles:

- least privilege
- explicit permissions
- whitelist-first execution
- server-side validation
- safe filesystem boundaries
- confirmation for sensitive actions
- audit logs
- no hidden automation
- no arbitrary executable launch
- no silent destructive actions

## Secret handling

Never commit:

- API keys
- access tokens
- passwords
- private certificates
- production `.env`

Use environment variables or a secure secret-management strategy.

If a real key has ever been exposed, rotate it immediately.

---

# 🧪 Testing

The project uses a combination of:

- TypeScript compilation
- frontend production builds
- Python compilation
- backend runtime checks
- API smoke tests
- safety checks
- interaction tests
- WebGL/runtime verification where applicable

Typical development commands:

```powershell
# Backend
cd backend
python -m compileall app
python run_backend.py

# Frontend
cd frontend
npm install
npm run build
npm run dev
```

---

# 🛠 Technology Stack

> Exact package versions should always be taken from repository manifests.

### Frontend

- Electron
- React
- TypeScript
- Vite
- Framer Motion
- Three.js
- React Three Fiber
- Drei
- custom CSS / token-driven design system

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic
- local persistence / audit infrastructure

### AI / Voice

- OpenAI integration (where configured)
- Google Gemini integration (where configured)
- Vosk readiness foundation
- faster-whisper direction
- TTS integration as implemented

### Automation

- REST APIs
- webhooks
- n8n (planned)

---

# 📡 API Architecture

The backend exposes local REST endpoints.

Known API families:

```text
/api/health
/api/actions/*
/api/commands/*
/api/audit/*
/api/database/*
/api/voice/*
```

Exact available endpoints should be confirmed against the current route files before release.

The frontend should communicate with the backend through a dedicated client layer rather than duplicating HTTP logic.

---

# 📦 Installation — Windows

> Replace `<YOUR_GITHUB_REPO_URL>` with your real repository URL.

### 1. Install prerequisites

- Git
- Python
- Node.js LTS

### 2. Clone the repository

```powershell
git clone <YOUR_GITHUB_REPO_URL>
cd NexaAI
```

### 3. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Optional activation:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Environment

Create:

```text
backend/.env
```

Use the repository `.env.example` when available.

Never upload `backend/.env` to GitHub.

### 5. Start backend

```powershell
python run_backend.py
```

Expected local API:

```text
http://127.0.0.1:8000
```

### 6. Start desktop frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Use the actual npm script defined in `frontend/package.json`.

---

# 🗂 Repository Structure

```text
NexaAI/
├── backend/
│   ├── app/
│   │   ├── actions/
│   │   ├── api/
│   │   ├── audit/
│   │   ├── automation/
│   │   ├── command_engine/
│   │   ├── contacts/
│   │   ├── core/
│   │   ├── database/
│   │   ├── files/
│   │   ├── pdf/
│   │   ├── scheduler/
│   │   ├── schemas/
│   │   ├── security/
│   │   └── voice/
│   ├── requirements.txt
│   └── run_backend.py
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── design/
│   │   ├── environment/
│   │   ├── interaction/
│   │   ├── pages/
│   │   ├── providers/
│   │   └── styles/
│   ├── package.json
│   └── vite.config.*
│
├── README.md
└── TODO.md
```

---

# 🚀 Roadmap

## Foundation ✅

- [x] Electron desktop foundation
- [x] React + TypeScript frontend
- [x] FastAPI backend
- [x] API health/status
- [x] command preview
- [x] safe desktop actions
- [x] read-only file search
- [x] audit foundation

## AI OS UI ✅

- [x] token-driven design system
- [x] reusable UI primitives
- [x] AI-OS navigation
- [x] command bar
- [x] premium page hero
- [x] modular CSS architecture

## Environment ✅

- [x] 3D AI Core / Earth
- [x] neural network
- [x] particles
- [x] stars
- [x] orbit systems
- [x] energy rings
- [x] energy beams
- [x] cinematic HUD
- [x] adaptive rendering
- [x] AI activity-reactive environment

## Interaction ✅ / 🚧

- [x] interaction bus
- [x] thinking overlay
- [x] command execution overlay
- [x] notification system
- [x] magnetic interactions
- [x] pointer reflection
- [x] voice orb
- [x] AI activity synchronization
- [🚧] complete end-to-end voice assistant
- [🚧] full liquid-glass / physics polish

## Multi-LLM 🚧

- [ ] provider registry
- [ ] OpenAI adapter
- [ ] Gemini adapter
- [ ] Claude adapter
- [ ] DeepSeek adapter
- [ ] Ollama adapter
- [ ] user model selector
- [ ] provider priority
- [ ] automatic quota failover
- [ ] provider health dashboard
- [ ] usage analytics

## Voice AI 🚧

- [ ] reliable Bangla STT
- [ ] Banglish STT
- [ ] English STT
- [ ] push-to-talk
- [ ] continuous listening
- [ ] interruption / barge-in
- [ ] TTS provider abstraction
- [ ] natural voice reply
- [ ] voice-controlled tools
- [ ] full voice conversation

## Browser & YouTube ❌

- [ ] web search
- [ ] browser control
- [ ] browser navigation
- [ ] safe page interaction
- [ ] structured extraction
- [ ] YouTube control
- [ ] voice browser commands

## Automation ❌

- [ ] n8n integration
- [ ] webhook manager
- [ ] email automation
- [ ] calendar integration
- [ ] notifications
- [ ] Google Sheets
- [ ] external API workflows
- [ ] WhatsApp confirmation workflow

## Documents & Memory 🚧

- [ ] PDF intelligence
- [ ] document summarization
- [ ] OCR
- [ ] embeddings
- [ ] RAG
- [ ] long-term memory
- [ ] memory controls
- [ ] workspace memory

## AI Development Workspace ❌

- [ ] workspace creation
- [ ] sandboxed project directories
- [ ] project scaffolding
- [ ] AI code generation
- [ ] safe build execution
- [ ] preview server
- [ ] error detection
- [ ] automated repair loop
- [ ] iterative build/test
- [ ] project export

## Next-Generation Agents ❌

- [ ] browser agent
- [ ] coding agent
- [ ] research agent
- [ ] document agent
- [ ] planning agent
- [ ] multi-agent orchestration
- [ ] task queue
- [ ] background jobs
- [ ] agent memory
- [ ] tool marketplace

## Production Release 🚧

- [ ] Windows installer
- [ ] first-run onboarding
- [ ] crash reporting
- [ ] performance profiles
- [ ] accessibility audit
- [ ] security audit
- [ ] release automation
- [ ] signed builds
- [ ] versioned migrations
- [ ] production documentation

---

# 🔮 Future Vision

Nexa AI is not being designed as another chatbot.

The long-term direction is:

```text
              ┌─────────────────────────┐
              │        NEXA AI          │
              │   AI Operating Layer   │
              └────────────┬────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
          VOICE           CHAT          VISION
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                    MODEL ROUTER
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
         OpenAI         Gemini       Future Models
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                        TOOLS
                           │
       ┌────────┬──────────┼─────────┬──────────┐
       ▼        ▼          ▼         ▼          ▼
     Files   Browser    YouTube   Desktop     n8n
       │        │          │         │          │
       └────────┴──────────┼─────────┴──────────┘
                           ▼
                    MEMORY / AUDIT
```

**Nexa AI — From assistant to operating layer.**

---

# 🤝 Contributing

Contributions should preserve:

- security
- testability
- modular architecture
- least privilege
- explicit permissions
- clean UX
- maintainability

For major architectural changes, open an issue or discussion before introducing breaking changes.

---

# 📜 License

No license is currently documented here.

Add a `LICENSE` file before publishing this repository for public reuse.

---

# ⚠️ Security Disclaimer

Nexa AI can interact with local software and may eventually interact with external services.

Never run unreviewed automation with production credentials.

Never commit:

- API keys
- access tokens
- passwords
- private certificates
- production `.env` files

Sensitive automation must remain permissioned, auditable, and explicitly approved.

---

<div align="center">

### ⟡ THINK • SPEAK • SEARCH • BUILD • AUTOMATE ⟡

**Nexa AI**

</div>
