# 🚀 NEXA AI — Secure Gmail Integration

> **Project:** NEXA AI  
> **Module:** Gmail Integration  
> **Status:** ✅ Phase 1 → Phase 2A → Phase 2B → Phase 2C Complete  
> **Latest Refinement:** AI Email Drafting + Profile-Aware Signatures  
> **Active Remote Branch:** `origin/supti-medha`  
> **Repository Owner:** `supti-medha`  
> **Architecture:** Secure • Modular • Human-Controlled • Audit-Friendly

---

## 📌 Overview

NEXA AI is a desktop AI assistant built around a modular, agent-based architecture.

The Gmail integration provides real Gmail access while maintaining a strict security boundary between:

- AI reasoning
- Gmail account access
- privileged Gmail operations
- email sending
- OAuth credentials
- user approval

The Gmail module uses the official **Google Gmail API**.

Third-party Gmail / Google Workspace repositories may be used for reference during development, but NEXA does **not** depend on them as its active Gmail runtime engine.

---

# 🔐 Core Security Philosophy

The Gmail integration follows three primary principles:

1. **The LLM never gets direct Gmail sending authority**
2. **Sensitive Gmail actions require explicit human approval**
3. **OAuth credentials and tokens never enter the LLM context**

Received emails are treated as:

```text
UNTRUSTED INPUT
```

This prevents malicious instructions inside received emails from automatically triggering privileged Gmail actions.

---

# 🏗️ High-Level Architecture

```text
User
 │
 ▼
NEXA Desktop UI
 │
 ▼
Chat / Command Router
 │
 ▼
GmailAgent
 │
 ├── Gmail Provider Abstraction
 │      ├── MockGmailProvider
 │      └── GoogleGmailProvider
 │
 ├── Email Drafting Layer
 │
 ├── Approval Controller
 │
 ├── Draft Fingerprint / Revalidation
 │
 ├── Audit Layer
 │
 ▼
Official Google Gmail API
```

---

# 🔒 Gmail Send Security Boundary

The LLM cannot directly execute Gmail send operations.

```text
LLM
 │
 │ prepares content only
 ▼
GmailAgent
 │
 ▼
Draft Creation
 │
 ▼
User Review
 │
 ▼
Explicit Approval
 │
 ▼
Final Revalidation
 │
 ▼
Explicit Send Approved Draft
 │
 ▼
Google Gmail API
```

The following architecture is forbidden:

```text
LLM
 │
 ▼
Gmail Send API
```

---

# ✅ Phase 1 — Gmail Foundation

**Status:** Complete

Phase 1 established the Gmail architecture, provider abstraction, Human-in-the-Loop foundation, and security boundaries.

## Completed Work

- Created `GmailAgent`
- Created Gmail provider abstraction
- Implemented `MockGmailProvider`
- Added Google Gmail provider support
- Added Gmail backend routes
- Added Gmail request / response schemas
- Added Human-in-the-Loop architecture
- Added Gmail write-operation restrictions
- Added Gmail tests
- Prevented direct AI-controlled sending

---

# ✅ Phase 2A — Real Gmail Read/Search + OAuth

**Status:** Complete

Phase 2A connected NEXA to real Gmail accounts through Google's official Gmail API.

---

## Official Gmail Provider

Active production provider:

```text
GoogleGmailProvider
```

Example provider configuration:

```env
NEXA_GMAIL_PROVIDER=google
```

---

## Google OAuth

NEXA uses Google OAuth 2.0.

The Gmail integration supports:

- Gmail API enabled
- Google Auth Platform
- External OAuth application
- Testing-mode development
- Google test users
- Desktop OAuth client
- Local token persistence
- Browser-based authorization flow

OAuth credentials are stored outside the repository.

Example:

```text
D:\NEXA-Secrets\gmail\credentials.json
```

Account tokens are stored under the local NEXA user directory.

Example:

```text
%USERPROFILE%\.nexa_ai\gmail\
```

---

## ⚠️ Never Commit Secrets

Never commit:

```text
credentials.json
token.json
.env
OAuth access tokens
OAuth refresh tokens
private keys
API keys
```

Real secrets must never be pushed to GitHub.

---

# 📬 Real Gmail Read Features

NEXA supports:

- Search email
- List unread email
- List recent email
- Search by sender
- Search by subject
- Open email
- Read email content
- Read Gmail threads
- Retrieve message metadata
- Retrieve attachment metadata
- Download permitted attachments
- Display Gmail previews

Example commands:

```text
Show my latest 5 unread emails
```

```text
Search my emails from Google
```

```text
Find unread emails from Quora
```

```text
Read my latest email from Google
```

```text
Show the full thread of my latest Google email
```

---

# 🐛 Real Gmail Routing Fix

An early integration bug caused the desktop UI to return old mock Gmail data even though the backend successfully accessed real Gmail.

Examples of old mock values included:

```text
supervisor@university.edu
accounts@example.com
msg-supervisor
thread-report
```

The routing logic was corrected.

Current flow:

```text
NEXA Chat UI
 │
 ▼
GmailAgent
 │
 ▼
GoogleGmailProvider
 │
 ▼
Official Gmail API
 │
 ▼
User's Real Gmail
```

**Status:** ✅ Fixed

---

# 🧠 Natural-Language Gmail Routing

The Gmail router distinguishes between list and single-message operations.

Example:

```text
Show my latest 5 unread emails
```

returns multiple results.

While:

```text
Open my latest unread email
```

opens one email.

**Status:** ✅ Fixed

---

# 👥 Multi-Account Gmail Isolation

NEXA supports multiple Gmail accounts using isolated OAuth tokens.

```text
NEXA
 │
 ├── Gmail Account A
 │      └── Token A
 │
 ├── Gmail Account B
 │      └── Token B
 │
 └── Gmail Account C
        └── Token C
```

Each Gmail account receives its own token.

```text
Account A Token ≠ Account B Token
```

A teammate cloning the project must connect their own Gmail account.

They do not automatically receive access to another user's Gmail.

---

# ⚙️ Gmail Account Management

NEXA Settings provides Gmail account management.

Supported actions:

- View connected accounts
- Connect Gmail account
- Connect additional Gmail account
- Switch active Gmail account
- Disconnect account
- Refresh account state
- Maintain isolated account tokens

Example:

```text
Gmail Accounts

Connected as: user@gmail.com

[ Active ]
[ Connect account ]
[ Switch ]
[ Disconnect ]
[ Refresh ]
```

---

# 🌐 Improved OAuth Browser Flow

OAuth no longer requires manually copying authorization URLs from the backend console.

Current flow:

```text
Settings
 │
 ▼
Gmail Accounts
 │
 ▼
Connect Account
 │
 ▼
Default Browser Opens
 │
 ▼
Google Login
 │
 ▼
User Grants Permission
 │
 ▼
NEXA Detects Completion
 │
 ▼
Account List Refreshes
```

OAuth loading state handles:

```text
Success
Error
Timeout
Cancellation
```

OAuth URLs and token values are not intentionally exposed to:

```text
LLM Context
Chat History
Normal Frontend Responses
```

---

# ✅ Phase 2B — Compose, Draft, Reply, Forward & Attachments

**Status:** Complete

Phase 2B introduced Gmail content preparation and real Gmail draft creation.

Supported capabilities:

- Natural-language composition
- AI-assisted email drafting
- Gmail draft creation
- Reply draft
- Reply-All draft
- Forward draft
- Local attachments
- MIME generation
- Recipient validation
- Header injection protection
- Secure attachment validation
- Draft browser navigation

---

# ✍️ Natural-Language Email Composition

Example:

```text
Write an email to professor@example.com saying the meeting is tomorrow at 10 AM.
Subject: Project Meeting
```

NEXA extracts:

```text
To:
professor@example.com

Subject:
Project Meeting

Body:
The meeting is tomorrow at 10 AM.
```

Supported commands include:

```text
Write an email...
Draft an email...
Prepare an email...
Create an email...
Send an email...
```

The word `send` in natural language does **not** give the LLM direct sending authority.

---

# 🤖 AI-Assisted Email Drafting

Main drafting layer:

```text
backend/app/email_drafting.py
```

NEXA can generate email subject/body when the user provides intent but incomplete content.

Supported styles include:

- Formal
- Professional
- Academic
- Friendly
- Polite
- Apology
- Brief
- Detailed

---

# 📏 Intelligent Email Length

Email generation now adapts to the user's request.

Typical targets:

```text
Brief email:
60–90 words

Normal professional / academic email:
90–140 words

Detailed email:
120–180 words
```

The system does not blindly force identical email lengths.

The generated email should remain:

- natural
- professional
- useful
- concise
- context-aware

---

# 🛡️ Fact-Safe Drafting

NEXA must not invent unsupported facts.

Examples of information that should not be invented:

```text
Dates
Times
Deadlines
Achievements
Excuses
Medical reasons
Meeting availability
Commitments
Promises
Project status
Submission reasons
```

If information is missing, NEXA uses neutral wording instead.

Example:

```text
If needed, I can provide additional context.
```

Instead of inventing:

```text
I am available to meet tomorrow at 10 AM.
```

unless the user actually provided that information.

---

# 👤 Profile-Aware Email Signatures

NEXA now supports profile-aware email signatures.

Example profile:

```text
Supti Das Medha
```

Generated email:

```text
Best regards,
Supti Das Medha
```

The application no longer generates placeholder signatures such as:

```text
[Your Name]
```

and no longer guesses a human name from an email local-part.

For example:

```text
suptidasmedha@gmail.com
```

must **not** automatically become:

```text
Suptidasmedha
```

---

# 🔄 Profile Name Flow

Frontend profile source:

```text
localStorage key:
nexa-ai:user-profile
```

Profile field:

```text
userName
```

Example:

```text
Supti Das Medha
```

Runtime flow:

```text
NEXA Profile
 │
 ▼
profile.userName
 │
 ▼
requestChatMessage(...)
 │
 ▼
profileName
 │
 ▼
profile_name
 │
 ▼
Backend Chat Schema
 │
 ▼
Gmail Email Drafting
 │
 ▼
Email Signature
```

---

# 🎯 Profile Name Priority

Email signature name resolution uses:

```text
1. Trusted NEXA profile display name
2. Gmail account display/profile name
3. Neutral closing with no invented name
```

Email local-part guessing is disabled.

---

# 🗣️ Address Style Preservation

Adding profile-name support does not break the existing assistant addressing preference.

Both are sent together:

```text
address_style
profile_name
```

Frontend request path:

```text
profile.addressingPreference
        ↓
addressStyle
        ↓
address_style
```

and:

```text
profile.userName
        ↓
profileName
        ↓
profile_name
```

---

# 📧 Real Gmail Draft Creation

Draft creation uses:

```text
users().drafts().create(...)
```

Message flow:

```text
PreparedEmail
 │
 ▼
EmailMessage
 │
 ▼
RFC / MIME Message
 │
 ▼
URL-Safe Base64
 │
 ▼
Gmail drafts.create
 │
 ▼
Real Gmail Draft
```

---

# 🔑 Gmail Compose OAuth Scope

Gmail draft functionality requires:

```text
https://www.googleapis.com/auth/gmail.compose
```

The application verifies Gmail permissions before draft creation.

If an older read-only token is detected, NEXA can require reconnection.

---

# 📥 Reply Support

NEXA supports reply drafts.

Example:

```text
Reply to my latest email from professor@example.com and say I will submit tomorrow.
```

Reply flow:

```text
User Request
 │
 ▼
Search Matching Email
 │
 ▼
Select Source Message
 │
 ▼
Build Reply Metadata
 │
 ▼
Create Reply Draft
```

Thread information is preserved:

```text
Thread ID
In-Reply-To
References
Re: Subject
```

---

# 👥 Reply-All Support

Reply-All safely determines recipients.

```text
Original Sender
 │
 ├── Original To
 │
 ├── Original CC
 │
 ▼
Remove Active User
 │
 ▼
Deduplicate
 │
 ▼
Reply-All Draft
```

---

# 📤 Forward Support

Example:

```text
Forward my latest email from supervisor@university.edu to colleague@example.com
```

Forward drafts may contain:

```text
Original Sender
Original Date
Original Subject
Original Body
```

Original attachments are not automatically copied.

Only explicitly requested new attachments are added.

---

# 📎 Local Attachment Support

Example:

```text
Draft an email to test@example.com saying please see the attached file.
Subject: NEXA Attachment Test.
Attach D:\Test\sample.txt
```

Flow:

```text
User Request
 │
 ▼
Extract Attachment Path
 │
 ▼
Remove Attachment Directive From Body
 │
 ▼
Resolve File
 │
 ▼
Security Validation
 │
 ▼
MIME Detection
 │
 ▼
EmailMessage.add_attachment(...)
 │
 ▼
Gmail Draft
```

---

# 📁 Supported Attachment Paths

Windows absolute path:

```text
D:\Test\sample.txt
```

Quoted path:

```text
"D:\Project Files\Final Report.pdf"
```

Multiple attachments:

```text
Attach D:\Files\a.txt and D:\Files\b.pdf
```

Unicode filenames are supported.

NEXA does not recursively scan the entire computer for files.

---

# 🔍 Attachment Validation

Attachments must pass:

- file existence check
- regular-file validation
- readable-file check
- filename validation
- extension validation
- protected-path validation
- file-size validation
- combined-size validation

Limits:

```text
Maximum single attachment:
10 MiB

Maximum combined attachments:
25 MiB
```

Validation is all-or-nothing.

---

# 🔐 Sensitive Attachment Blocking

Sensitive files are blocked.

Examples:

```text
credentials.json
token.json
.env
*.pem
*.key
*.p12
```

Protected locations include:

```text
D:\NEXA-Secrets\
%USERPROFILE%\.nexa_ai\gmail\
```

---

# 🧼 Attachment Metadata Sanitization

Safe frontend metadata may contain:

```text
File Name
MIME Type
Size
Validation Status
```

It must not expose:

```text
Local filesystem path
OAuth token path
Secret directory path
Raw attachment bytes
```

---

# ✅ Phase 2C — Human Approval & Controlled Real Send

**Status:** Complete

Phase 2C introduced controlled real Gmail sending.

The final secure flow is:

```text
User Request
 │
 ▼
NEXA Generates Email
 │
 ▼
Gmail Draft Created
 │
 ▼
User Reviews Draft
 │
 ▼
Approve Draft
 │
 ▼
Approved
 │
 ▼
Send Approved Draft
 │
 ▼
Final Revalidation
 │
 ▼
Gmail drafts.send
 │
 ▼
Sent
```

Approval and sending are intentionally separate actions.

---

# 🧩 Phase 2C.1 — Approval Controller

Implemented:

- ephemeral approval state
- approval IDs
- TTL / expiry support
- approval status transitions
- canonical draft fingerprint
- draft/account binding
- recipient binding
- attachment binding

Approval states include:

```text
pending
approved
cancelled
expired
invalidated
sending
sent
```

---

# 🧩 Phase 2C.2 — Approval UI

The NEXA UI provides approval controls.

Pending draft:

```text
[ Approve Draft ]
[ Cancel ]
```

Approved draft:

```text
[ Send Approved Draft ]
```

Approval alone does not send the email.

---

# 🧩 Phase 2C.3 — Draft Change Invalidation

An approved draft cannot authorize a modified version.

Example:

```text
Draft Version A
 │
 ▼
Approved
 │
 ▼
User edits Gmail draft
 │
 ▼
Draft Version B
 │
 ▼
Fingerprint mismatch
 │
 ▼
Approval invalidated
```

Revalidation verifies:

- active Gmail account
- draft ID
- recipients
- subject
- body
- attachment metadata
- attachment digest
- canonical fingerprint

---

# 🧩 Phase 2C.4 — Controlled Send Gate

Final send endpoint:

```text
POST /api/gmail/draft-approvals/{approval_id}/send
```

The request uses only the approval ID.

It does not allow last-minute recipient/body override parameters.

Google send operation:

```python
service.users().drafts().send(
    userId="me",
    body={"id": draft_id},
).execute()
```

NEXA uses:

```text
drafts.send
```

for the approved draft.

Direct active-runtime:

```text
messages.send
```

is not used.

---

# 🔒 Duplicate Send Protection

Before real send:

```text
approved
 │
 ▼
atomic claim
 │
 ▼
sending
 │
 ▼
provider.send_draft(...)
 │
 ▼
sent
```

A second concurrent send attempt cannot claim the same approval.

This prevents accidental duplicate sends.

---

# ⚠️ Send Failure Handling

If the Gmail provider reports an uncertain or failed operation:

- NEXA does not silently retry privileged sends
- failure is sanitized
- ambiguous outcome fails closed
- user may be advised to check Gmail Sent
- approval state does not automatically authorize another unsafe retry

---

# ⏱️ TOCTOU Limitation

Gmail does not provide a transaction that can simultaneously:

```text
Compare Draft
+
Lock Gmail Web UI
+
Send Draft
```

NEXA performs final revalidation immediately before sending.

A tiny external-edit race window may still theoretically exist between revalidation and the Gmail API send operation.

This limitation is documented rather than hidden.

---

# 🧩 Phase 2C.5 — Audit & Error Handling

The Gmail audit system records important lifecycle events.

Examples:

```text
Approval Created
Approval Approved
Approval Cancelled
Approval Expired
Approval Invalidated
Draft Changed
Account Mismatch
Send Claimed
Send Succeeded
Send Blocked
Provider Failure
Duplicate Send Attempt
```

Audit logs must not contain:

```text
OAuth tokens
API keys
Email body
Raw MIME
Attachment bytes
Local file paths
Draft fingerprints
Secret values
```

---

# 🧩 Phase 2C.6 — Final Verification

Phase 2C underwent:

- focused Gmail tests
- full backend regression
- frontend TypeScript validation
- frontend contract tests
- route audit
- send-path audit
- approval-state audit
- API sanitization review
- audit privacy review
- duplicate send verification
- secret scanning
- real Gmail manual send verification

---

# 🧪 Real Gmail Send Verification

A real approved Gmail draft was manually tested.

Flow:

```text
Create Draft
 │
 ▼
Review Draft
 │
 ▼
Approve Draft
 │
 ▼
NO AUTOMATIC SEND
 │
 ▼
Send Approved Draft
 │
 ▼
Gmail API
 │
 ▼
Recipient Inbox
```

Verified:

```text
Draft creation        ✅
Approval              ✅
Approve-only no send  ✅
Explicit send         ✅
Recipient received    ✅
Sent folder copy      ✅
Duplicate protection  ✅
```

---

# 🤖 Hosted LLM Integration

NEXA contains an LLM routing layer.

Supported providers include:

```text
Gemini
Groq
OpenRouter
Cloudflare Workers AI
Mistral
Cerebras
```

Provider fallback ordering is supported.

Example primary provider configuration:

```env
NEXA_LLM_PRIMARY=groq
```

---

# ⚡ Current Groq Configuration

Current development configuration uses Groq.

Example:

```env
NEXA_LLM_PRIMARY=groq
GROQ_API_KEY=<YOUR_PRIVATE_GROQ_API_KEY>
GROQ_MODEL=openai/gpt-oss-20b
```

Never commit the actual API key.

---

# 🧠 Current Groq Model

Current working model:

```text
openai/gpt-oss-20b
```

The previous configured model:

```text
llama-3.1-8b-instant
```

was found unavailable for the current account/API environment.

NEXA was updated to use the available Groq-hosted model.

---

# 🔐 Environment File

NEXA backend environment file:

```text
D:\nexa_ai\backend\.env
```

It is ignored by Git.

Typical configuration:

```env
NEXA_LLM_PRIMARY=groq
GROQ_API_KEY=<PRIVATE_KEY>
GROQ_MODEL=openai/gpt-oss-20b
```

Never paste real secrets into:

- GitHub
- documentation
- screenshots
- chat logs
- source files

---

# 🖥️ Local Development

## Backend

PowerShell:

```powershell
Set-Location D:\nexa_ai\backend

D:\nexa_ai\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Expected:

```text
INFO: Application startup complete.
INFO: Uvicorn running on http://127.0.0.1:8000
```

---

## Frontend

PowerShell:

```powershell
Set-Location D:\nexa_ai\frontend
npm.cmd run dev
```

---

# 🧪 Latest Verification Status

Latest Gmail/email-drafting verification:

```text
Focused Gmail Tests:
✅ 97 Passed

Full Backend Suite:
✅ 477 Passed

Frontend TypeScript Check:
✅ Passed

Frontend Contract Tests:
✅ Passed

Manual Gmail Draft Test:
✅ Passed

Profile-Aware Signature:
✅ Passed

Explicit Approval:
✅ Passed

Controlled Send:
✅ Passed
```

---

# 🧪 Previous Regression Milestones

During development, successful backend suite milestones included:

```text
324 passed
342 passed
409 passed
438 passed
457 passed
466 passed
472 passed
474 passed
476 passed
477 passed
```

The increasing totals reflect additional regression coverage added during development.

---

# ✅ Current Email Drafting Verification

Verified manually:

```text
Normal academic email length     ✅
Professional tone                ✅
2–3 paragraph structure          ✅
Fact-safe content                ✅
No invented date/time            ✅
No [Your Name] placeholder       ✅
No guessed local-part name       ✅
Real profile display name        ✅
Profile spacing preserved        ✅
Address style preserved          ✅
```

Example final sign-off:

```text
Best regards,
Supti Das Medha
```

---

# 🧪 Frontend Contract Coverage

Frontend contract tests verify:

- typed chat requests
- voice request pipeline
- backend chat routing
- address style propagation
- profile-name propagation
- Gmail approval UI
- action confirmation gates
- source rendering
- backend status rendering
- voice/STT/TTS integration
- YouTube integration
- WhatsApp draft flow
- no WhatsApp auto-send path

---

# 🛡️ Gmail Security Principles

The Gmail module must continue following these rules:

```text
1. Never expose OAuth tokens to the LLM.

2. Never commit Gmail credentials or tokens.

3. Never expose API keys to Git.

4. Never allow the LLM to directly send email.

5. Treat received emails as untrusted input.

6. Require explicit human approval before sending.

7. Keep Gmail account tokens isolated.

8. Use minimum required OAuth permissions.

9. Revalidate recipients before sending.

10. Revalidate attachments before sending.

11. Revalidate the Gmail account before sending.

12. Invalidate approval after draft changes.

13. Prevent duplicate sends.

14. Keep sensitive operations auditable.

15. Never silently retry privileged send operations.

16. Fail safely.
```

---

# 🔐 Secret Safety Check

Before committing Gmail-related code:

```powershell
git diff --cached | Select-String -Pattern 'GROQ_API_KEY|gsk_|GEMINI_API_KEY|client_secret|access_token|refresh_token|private_key'
```

Tracked sensitive-file check:

```powershell
git ls-files | Select-String 'credentials\.json|token\.json|NEXA-Secrets|(^|/)\.env$'
```

Expected result:

```text
No real secrets tracked.
```

---

# 🧾 Git Safety Rules

Avoid:

```text
git add .
git add -A
```

Prefer explicitly staging expected files.

Example:

```powershell
git add backend/app/email_drafting.py
git add backend/app/chat/service.py
```

Always inspect:

```powershell
git status --short
git --no-pager diff --cached --stat
```

before commit.

---

# 📦 Latest Development Commit

Latest verified Gmail drafting refinement:

```text
Commit:
96fa262

Message:
feat: improve Gmail drafting and profile-aware signatures
```

Remote:

```text
origin/supti-medha
```

Final sync verification:

```text
origin/supti-medha...HEAD

0    0
```

Meaning:

```text
Remote ahead: 0
Local ahead:  0
```

Repository was synchronized successfully after push.

---

# 🗂️ Important Gmail Milestone Commits

```text
Phase 2B
979adee
feat: complete Gmail Phase 2B draft workflow
```

```text
Phase 2C.1
e2f04b8
feat: add Gmail Phase 2C.1 approval controller
```

```text
Phase 2C.2
239f2da
feat: add Gmail Phase 2C.2 approval preview UI
```

```text
Phase 2C.3
4ef3fcb
feat: add Gmail Phase 2C.3 approval invalidation
```

```text
Phase 2C.4
247fa30
feat: add Gmail Phase 2C.4 controlled send gate
```

```text
Phase 2C.5
02a86ce
feat: add Gmail Phase 2C.5 audit and error handling
```

```text
Phase 2C.6
fcd921b
docs: mark Gmail Phase 2C complete
```

```text
Post-Phase 2C Drafting Refinement
96fa262
feat: improve Gmail drafting and profile-aware signatures
```

---

# 🗺️ Gmail Module Roadmap

| Feature | Status | Phase |
|---|---|---|
| Gmail Provider Architecture | ✅ Complete | Phase 1 |
| Mock Gmail Provider | ✅ Complete | Phase 1 |
| HITL Foundation | ✅ Complete | Phase 1 |
| Official Gmail API | ✅ Complete | Phase 2A |
| OAuth | ✅ Complete | Phase 2A |
| Read Email | ✅ Complete | Phase 2A |
| Search Email | ✅ Complete | Phase 2A |
| Unread Email Listing | ✅ Complete | Phase 2A |
| Gmail Threads | ✅ Complete | Phase 2A |
| Multi-Account OAuth | ✅ Complete | Phase 2A |
| Token Isolation | ✅ Complete | Phase 2A |
| Account Connect | ✅ Complete | Phase 2A |
| Account Switch | ✅ Complete | Phase 2A |
| Account Disconnect | ✅ Complete | Phase 2A |
| OAuth Browser Flow | ✅ Complete | Phase 2A |
| Natural-Language Compose | ✅ Complete | Phase 2B |
| AI-Assisted Drafting | ✅ Complete | Phase 2B |
| Real Gmail Draft | ✅ Complete | Phase 2B |
| Reply | ✅ Complete | Phase 2B |
| Reply-All | ✅ Complete | Phase 2B |
| Forward | ✅ Complete | Phase 2B |
| Local Attachments | ✅ Complete | Phase 2B |
| Multiple Attachments | ✅ Complete | Phase 2B |
| MIME Attachments | ✅ Complete | Phase 2B |
| Recipient Validation | ✅ Complete | Phase 2B |
| Header Protection | ✅ Complete | Phase 2B |
| Sensitive File Blocking | ✅ Complete | Phase 2B |
| Draft Browser Navigation | ✅ Complete | Phase 2B |
| Approval Controller | ✅ Complete | Phase 2C |
| Approval UI | ✅ Complete | Phase 2C |
| Draft Fingerprint | ✅ Complete | Phase 2C |
| Draft Change Invalidation | ✅ Complete | Phase 2C |
| Account Revalidation | ✅ Complete | Phase 2C |
| Recipient Revalidation | ✅ Complete | Phase 2C |
| Attachment Revalidation | ✅ Complete | Phase 2C |
| Controlled `drafts.send` | ✅ Complete | Phase 2C |
| Duplicate Send Protection | ✅ Complete | Phase 2C |
| Audit Trail | ✅ Complete | Phase 2C |
| Safe Error Handling | ✅ Complete | Phase 2C |
| Real Send Verification | ✅ Complete | Phase 2C |
| Intelligent Email Length | ✅ Complete | Refinement |
| Fact-Safe Drafting | ✅ Complete | Refinement |
| Profile-Aware Signature | ✅ Complete | Refinement |
| Frontend `profile_name` Propagation | ✅ Complete | Refinement |
| Address Style Preservation | ✅ Complete | Refinement |
| Groq LLM Integration | ✅ Working | LLM Layer |

---

# 📊 Overall Progress

```text
Phase 1
████████████████████ 100%
Gmail Foundation
✅ COMPLETE


Phase 2A
████████████████████ 100%
Real Gmail Read/Search + OAuth + Multi-Account
✅ COMPLETE


Phase 2B
████████████████████ 100%
Compose + Draft + Reply + Forward + Attachments
✅ COMPLETE


Phase 2C
████████████████████ 100%
Human Approval + Controlled Real Send
✅ COMPLETE


Post-Phase 2C Refinement
████████████████████ 100%
Draft Quality + Profile-Aware Signatures
✅ COMPLETE
```

---

# 📦 Current Gmail Capabilities

NEXA Gmail currently supports:

```text
Official Gmail API
Real Gmail OAuth

Read Email
Search Email
Unread Email Listing
Open Email
Read Thread

Multi-Account Gmail
Account Connect
Account Switch
Account Disconnect
Per-Account Token Isolation

Natural-Language Email Compose
AI-Assisted Email Drafting
Real Gmail Draft Creation

Reply
Reply-All
Forward

Local Attachments
Multiple Attachments
Windows Paths
Quoted Paths
Unicode Filenames
MIME Attachments

Sensitive File Blocking
Attachment Size Validation
Attachment Metadata Sanitization

Recipient Validation
Header Injection Protection
Thread Preservation

Profile-Aware Email Signature
Fact-Safe Email Generation
Intelligent Email Length

Human Draft Review
Approve Draft
Send Approved Draft

Draft Fingerprinting
Approval Invalidation
Final Revalidation
Duplicate Send Protection
Audit Logging
Controlled Gmail drafts.send
```

---

# 🚫 Intentionally Unsupported / Forbidden Behavior

NEXA must not:

```text
Allow LLM-controlled automatic sending

Expose Gmail OAuth tokens to the LLM

Expose API keys to the frontend

Commit .env files

Commit OAuth credentials

Automatically resend after uncertain send failure

Ignore draft modifications after approval

Use old approval for a modified draft

Guess names from email local-parts

Invent dates, times, excuses or commitments
```

---

# 🔄 Final Gmail Runtime Flow

```text
User
 │
 ▼
NEXA Chat / Voice
 │
 ▼
Intent Router
 │
 ▼
LLM Email Generation
 │
 ▼
Fact-Safety / Drafting Layer
 │
 ▼
Gmail Draft
 │
 ▼
User Reviews Draft
 │
 ▼
Approve Draft
 │
 ▼
Approval Controller
 │
 ▼
Final Draft / Account / Recipient /
Attachment Revalidation
 │
 ▼
Send Approved Draft
 │
 ▼
Official Gmail drafts.send
 │
 ▼
Sent
```

---

# 🧠 Human-in-the-Loop Guarantee

The send workflow must always remain:

```text
Draft
   ↓
Review
   ↓
Approve Draft
   ↓
Approved
   ↓
Explicit Send Approved Draft
   ↓
Final Validation
   ↓
Sent
```

Never:

```text
User Request
   ↓
LLM
   ↓
Automatic Send
```

---

# ✅ Final Development Status

```text
NEXA AI — GMAIL MODULE
================================================

Phase 1
Gmail Foundation                         ✅ COMPLETE

Phase 2A
Real Gmail + OAuth + Multi-Account       ✅ COMPLETE

Phase 2B
Compose + Draft + Reply + Forward        ✅ COMPLETE
Attachments                              ✅ COMPLETE

Phase 2C
Approval Controller                      ✅ COMPLETE
Approval Invalidation                    ✅ COMPLETE
Controlled Send                          ✅ COMPLETE
Audit + Error Handling                   ✅ COMPLETE
Real Send Verification                   ✅ COMPLETE

Email Drafting Refinement
Professional Length                      ✅ COMPLETE
Fact-Safe Drafting                       ✅ COMPLETE
Profile-Aware Signature                  ✅ COMPLETE
Frontend Profile Propagation             ✅ COMPLETE

LLM
Groq API                                 ✅ WORKING
openai/gpt-oss-20b                       ✅ WORKING

Testing
Focused Gmail Suite                      ✅ 97 PASSED
Full Backend Suite                       ✅ 477 PASSED
Frontend TypeScript                      ✅ PASSED
Frontend Contract Suite                  ✅ PASSED

Git
Latest Commit                            ✅ 96fa262
Remote                                   ✅ origin/supti-medha
Ahead / Behind                           ✅ 0 / 0
Repository Sync                          ✅ COMPLETE
================================================
```

---

# 🎯 Current Development Position

```text
Phase 1
✅ COMPLETE
    │
    ▼
Phase 2A
✅ COMPLETE
    │
    ▼
Phase 2B
✅ COMPLETE
    │
    ▼
Phase 2C
✅ COMPLETE
    │
    ▼
Drafting & Profile Refinement
✅ COMPLETE
```

The Gmail integration is now in a stable, tested, human-controlled state.

Future work should preserve all existing Gmail security boundaries.

---

# 🛡️ Final Rule

> **NEXA may assist with email generation and may execute a send only after explicit human-controlled approval and a separate explicit send action.**

The LLM itself must never possess direct Gmail sending authority.

---

## NEXA AI

**Secure. Modular. Human-Controlled. Privacy-Aware.**

```text
AI assists.
Security validates.
The human decides.
```
