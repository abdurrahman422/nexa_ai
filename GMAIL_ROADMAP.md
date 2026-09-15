# NEXA AI — Gmail Integration

> **Project:** NEXA AI  
> **Module:** Gmail Integration  
> **Current Status:** Phase 2B Complete  
> **Next Milestone:** Phase 2C — Human Approval & Real Gmail Sending  
> **Repository Owner:** `supti-medha`

---

## 📌 Overview

NEXA AI is a secure desktop AI assistant built around a modular, agent-based architecture.

The Gmail integration is designed around three core principles:

- Secure access to the user's own Gmail account
- Strict separation between AI reasoning and privileged Gmail actions
- Human approval before sensitive actions such as sending an email

Third-party Gmail and Google Workspace repositories were reviewed during development as references only.

NEXA does **not** depend on those third-party repositories as its runtime Gmail engine.

The Gmail integration uses the official **Google Gmail API**.

---

# ✅ Phase 1 — Gmail Foundation

**Status:** Complete

Phase 1 established the Gmail architecture, provider abstraction, security boundaries, and Human-in-the-Loop foundation.

---

## Phase 1 Architecture

```text
NEXA Host Agent
      │
      ▼
  GmailAgent
      │
      ▼
 GmailProvider
  Abstraction
      │
      ├── MockGmailProvider
      │
      └── GoogleGmailProvider
      │
      ▼
HITL Approval Controller
```

---

## Phase 1 Completed Work

- Created `GmailAgent`
- Created Gmail provider abstraction
- Implemented `MockGmailProvider`
- Added `GoogleGmailProvider` support
- Added Gmail-related backend API routes
- Added Gmail request/response schemas
- Added Human-in-the-Loop approval architecture
- Added Gmail write-operation security restrictions
- Added Gmail unit and integration tests

---

## 🔐 Core Gmail Security Architecture

```text
LLM
 │
 │ Requests / Prepares Action
 ▼
GmailAgent
 │
 ▼
Security / Approval Layer
 │
 ▼
Gmail Provider
 │
 ▼
Google Gmail API
```

The LLM is **never allowed to directly send an email**.

Incoming email content is treated as:

```text
UNTRUSTED INPUT
```

This prevents malicious instructions contained inside emails from automatically triggering privileged actions.

---

# ✅ Phase 2A — Real Gmail Read/Search Integration

**Status:** Complete

Phase 2A replaced mock Gmail behavior with real Gmail access through Google's official Gmail API.

---

## 2A.1 — Official Google Gmail API Integration

NEXA supports real Gmail access through:

```text
GoogleGmailProvider
```

Provider selection supports:

```env
NEXA_GMAIL_PROVIDER=google
```

Phase 2A originally used the Gmail read-only scope:

```text
https://www.googleapis.com/auth/gmail.readonly
```

This allowed NEXA to read Gmail information without giving it direct email-sending authority.

---

## 2A.2 — Google Cloud OAuth Setup

A dedicated Google Cloud project was configured for NEXA AI.

Configuration includes:

- Gmail API enabled
- Google Auth Platform configured
- OAuth application configured as External
- Development application running in Testing mode
- Google test-user support
- Desktop OAuth client configured

OAuth credentials are stored outside the Git repository.

Example local credentials location:

```text
D:\NEXA-Secrets\gmail\credentials.json
```

OAuth account tokens are stored outside the repository under the user's local NEXA directory.

Example:

```text
%USERPROFILE%\.nexa_ai\gmail\
```

### ⚠️ Never Commit These Files

```text
credentials.json
token.json
.env
OAuth access tokens
OAuth refresh tokens
Private keys
```

No Gmail OAuth token should ever be committed to GitHub.

---

## 2A.3 — Real Gmail Features

NEXA can access real Gmail data.

Supported operations include:

- Search emails
- List unread emails
- List recent emails
- Search by sender
- Search by subject
- Open an email
- Read email content
- Read Gmail threads
- Retrieve message metadata
- Retrieve attachment metadata
- Download permitted attachments
- Display normalized Gmail previews

### Example NEXA Commands

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

## 2A.4 — Mock Gmail Routing Bug Fix

During Phase 2A, an important integration bug was discovered.

The backend Gmail API correctly returned real Gmail data, but the NEXA desktop chat interface was still displaying Phase 1 mock information.

Examples included:

```text
supervisor@university.edu
accounts@example.com
msg-supervisor
thread-report
```

The issue was caused by old hardcoded mock-routing logic inside the chat service.

The routing was corrected.

Current architecture:

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

## 2A.5 — Natural-Language Gmail Routing Fix

The Gmail command parser was improved.

Previously:

```text
Show my latest 5 unread emails
```

could incorrectly interpret the word `latest` as a request to open a single email.

The routing logic was corrected.

Now:

```text
Show my latest 5 unread emails
```

returns:

```text
5 email results
```

while:

```text
Open my latest unread email
```

returns:

```text
1 opened email
```

**Status:** ✅ Fixed

---

## 2A.6 — Multi-Account Gmail Isolation

A major security improvement was introduced to safely support multiple Gmail accounts.

The previous single-token architecture was replaced with isolated per-account OAuth tokens.

```text
NEXA
 │
 ├── Google Account A
 │      └── Token A
 │
 ├── Google Account B
 │      └── Token B
 │
 └── Google Account C
        └── Token C
```

Each connected Google account receives its own isolated OAuth token.

Therefore:

```text
User A Token ≠ User B Token
```

and:

```text
User A Gmail ≠ User B Gmail
```

A teammate who clones NEXA from GitHub must connect their own Google account.

They do not automatically receive access to another user's Gmail mailbox.

---

## 2A.7 — Gmail Account Management UI

A Gmail account management section was added to NEXA Settings.

Example interface:

```text
Gmail Accounts

Connected as: user@gmail.com

[ Active ]
[ Connect account ]
[ Switch ]
[ Disconnect ]
[ Refresh ]
```

Supported functionality:

- View connected Gmail accounts
- Connect a Gmail account
- Connect additional Gmail accounts
- Switch the active Gmail account
- Disconnect an account
- Refresh Gmail account status
- Maintain isolated account tokens

**Status:** ✅ Complete

---

## 2A.8 — Improved OAuth Connection Flow

Originally, Gmail OAuth required the user to manually copy an authorization URL from the backend terminal.

That behavior was removed.

The current connection flow is:

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
Google OAuth Login
   │
   ▼
User Grants Permission
   │
   ▼
NEXA Detects Completion
   │
   ▼
Account List Refreshes
   │
   ▼
Connected Account Becomes Active
```

The OAuth operation runs asynchronously.

The backend exposes only sanitized OAuth status information.

OAuth URLs and OAuth token values are not intentionally returned to:

```text
Chat UI
LLM Context
Conversation History
```

The loading state correctly clears on:

```text
Success
Error
Timeout
Cancellation
```

**Status:** ✅ Fixed

---

## 2A.9 — Disconnect / Reconnect Flow

The Gmail account lifecycle was manually tested.

```text
Connected Gmail
      │
      ▼
Disconnect
      │
      ▼
Account Removed
      │
      ▼
Connect Account
      │
      ▼
Google OAuth
      │
      ▼
New Token
      │
      ▼
Account Active
```

**Status:** ✅ Verified

---

## 🧪 Phase 2A Validation

| Validation | Result |
|---|---|
| Google Gmail Provider Tests | ✅ 13 Passed |
| Gmail Integration Tests | ✅ 15 Passed |
| Full Backend Test Suite | ✅ 342 Passed |
| Frontend `npm run check` | ✅ Passed |
| `git diff --check` | ✅ Passed |
| Real Gmail Read/Search | ✅ Working |
| OAuth Browser Flow | ✅ Working |
| Disconnect / Reconnect | ✅ Working |
| Multi-Account Architecture | ✅ Implemented |

---

## ✅ Phase 2A Final Status

```text
PHASE 2A
================================

Real Gmail OAuth           ✅
Read Email                 ✅
Search Email               ✅
Unread Email Listing       ✅
Open Email                 ✅
Read Thread                ✅
Real Chat Integration      ✅
Mock Data Removal          ✅
Multi-Account Support      ✅
Per-Account Token Storage  ✅
Connect Account            ✅
Switch Account             ✅
Disconnect Account         ✅
OAuth Auto Browser         ✅
Secure Token Handling      ✅
Read-Only Protection       ✅

STATUS: COMPLETE
```

---

# ✅ Phase 2B — Gmail Compose, Draft, Reply, Forward & Attachments

**Status:** Complete

Phase 2B introduced Gmail write-preparation capabilities while preserving NEXA's most important Gmail security boundary:

> **NEXA can prepare Gmail content, but it cannot automatically send email.**

The user remains in control of the final sending action.

NEXA now supports:

- Natural-language email composition
- Gmail draft creation
- Reply drafts
- Reply-All drafts
- Forward drafts
- Local file attachments
- AI-assisted email drafting
- Secure recipient validation
- MIME message generation
- Gmail browser draft navigation
- Attachment validation
- Attachment metadata sanitization

Actual Gmail sending remains disabled until Phase 2C.

---

## 🔐 Phase 2B Security Model

Phase 2B follows a strict draft-only architecture.

```text
User Request
    │
    ▼
NEXA Chat Router
    │
    ▼
GmailAgent
    │
    ▼
Draft Preparation
    │
    ▼
GoogleGmailProvider
    │
    ▼
Gmail Draft Created
    │
    ▼
Gmail Opens in Browser
    │
    ▼
User Reviews / Edits
    │
    ▼
User Manually Presses Send
```

The following architecture is intentionally forbidden:

```text
LLM
 │
 ▼
Gmail Send API
```

During Phase 2B:

```text
messages.send   ❌ Not used by active Google provider
drafts.send     ❌ Not used
Automatic Send  ❌ Disabled
Manual Send     ✅ User-controlled in Gmail
```

The active `GoogleGmailProvider.send_prepared()` path rejects direct sending.

A legacy `ExistingSkillGmailProvider.send_prepared()` implementation still exists in the codebase, but it is not instantiated or selected by the active Gmail provider factory.

---

## 2B.1 — Natural-Language Email Composition

NEXA can prepare Gmail drafts directly from conversational commands.

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

Natural-language parsing supports commands such as:

```text
Write an email...
Draft an email...
Prepare an email...
Create an email...
Send an email...
```

Even when the user says:

```text
Send an email...
```

NEXA still creates only a Gmail draft.

The word `send` does not bypass the Phase 2B draft-only security boundary.

---

## 2B.2 — AI-Assisted Email Drafting

A dedicated email drafting layer was introduced:

```text
backend/app/email_drafting.py
```

It supports contextual email generation when the user provides an intent but does not provide a complete subject or body.

Supported writing styles include:

- Formal
- Professional
- Polite
- Friendly
- Academic
- Apology
- Short / concise

Example:

```text
Write a formal academic email to professor@example.com
about my late project submission.
```

NEXA can generate an appropriate subject and body while avoiding unsupported facts.

The drafting layer is designed to avoid inventing:

```text
Dates
Deadlines
Causes
Promises
Meeting times
Personal facts
```

unless the user explicitly provides them.

Explicit user-provided subject and body content are preserved whenever possible.

---

## 2B.3 — Official Gmail Draft Creation

`GoogleGmailProvider` supports real Gmail draft creation using the official Gmail API.

Draft creation uses:

```text
users().drafts().create(...)
```

The message is constructed as an RFC-compatible MIME email using:

```text
EmailMessage
```

and encoded using URL-safe Base64 before being submitted to Gmail.

Architecture:

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
URL-safe Base64
     │
     ▼
Gmail drafts.create
     │
     ▼
Real Gmail Draft
```

The provider performs draft readback verification using Gmail's raw draft representation.

This verification confirms:

```text
Draft ID
Message ID
Thread ID
Body Presence
Stored Draft Content
```

---

## 2B.4 — Gmail Compose OAuth Scope

Phase 2A originally used Gmail read-only permissions.

Phase 2B requires Gmail draft creation capability.

The Gmail integration therefore supports:

```text
https://www.googleapis.com/auth/gmail.compose
```

NEXA verifies the active OAuth token before creating a draft.

If the connected Gmail account only has the previous read-only permission, NEXA safely requests reconnection instead of silently failing.

OAuth credentials and account tokens remain outside the Git repository.

Protected locations include:

```text
D:\NEXA-Secrets\gmail\credentials.json

%USERPROFILE%\.nexa_ai\gmail\
```

OAuth secrets are never intentionally exposed to:

```text
LLM Context
Chat History
Frontend Responses
Git Repository
```

---

## 2B.5 — Recipient & Header Protection

Outgoing Gmail draft recipients are validated before draft creation.

Validation applies to:

```text
To
CC
BCC
```

NEXA rejects invalid recipient addresses.

Header-injection protection also prevents carriage-return or newline characters from being inserted into sensitive email headers.

Protected fields include:

```text
Recipients
Subject
Email Headers
```

This prevents malicious input from manipulating MIME headers.

---

## 2B.6 — Reply Draft Support

NEXA can prepare reply drafts against received Gmail messages.

Example:

```text
Reply to my latest email from professor@example.com
and say I will submit tomorrow.
```

Flow:

```text
User Request
     │
     ▼
Search Matching Received Email
     │
     ▼
Select Source Message
     │
     ▼
Build Reply Metadata
     │
     ▼
Create Gmail Reply Draft
```

Reply drafts preserve Gmail threading information:

```text
Thread ID
In-Reply-To
References
Re: Subject
```

NEXA prefers the original message's `Reply-To` address when available.

Received-message selection excludes inappropriate source messages such as:

```text
DRAFT
SENT
TRASH
SPAM
```

This prevents NEXA from accidentally replying to the wrong Gmail item.

---

## 2B.7 — Reply-All Support

Reply-All drafting is supported.

NEXA calculates the appropriate recipients from the original email while excluding the active Gmail user's own address.

```text
Original Sender
      │
      ├── To Recipients
      │
      └── CC Recipients
              │
              ▼
      Remove Active User
              │
              ▼
      Deduplicate Addresses
              │
              ▼
        Reply-All Draft
```

Reply-All preserves the original Gmail thread and appropriate reply headers.

---

## 2B.8 — Forward Draft Support

NEXA can create a forward draft from an existing Gmail message.

Example:

```text
Forward my latest email from supervisor@university.edu
to colleague@example.com
```

The forwarded draft contains source information such as:

```text
Original Sender
Original Date
Original Subject
Original Body
```

The destination address is isolated from the original recipients.

NEXA does not automatically copy original message attachments during forwarding.

Only new attachments explicitly requested by the user are added.

---

## 📎 2B.9 — Local Attachment Support

Secure local-file attachment support was completed in Phase 2B.

Example:

```text
Draft an email to test@example.com
saying please see the attached file.
Subject: NEXA Attachment Test.
Attach D:\Test\sample.txt
```

NEXA performs the following flow:

```text
Natural-Language Request
        │
        ▼
Extract Explicit Attachment Path
        │
        ▼
Remove Attachment Directive
from Email Body
        │
        ▼
Resolve Local File
        │
        ▼
Security Validation
        │
        ▼
MIME Type Detection
        │
        ▼
EmailMessage.add_attachment(...)
        │
        ▼
Gmail Draft
```

The attachment command itself does not appear inside the final email body.

Input:

```text
Please see the attached file.
Attach D:\Test\sample.txt
```

Final body:

```text
Please see the attached file.
```

Attachment:

```text
sample.txt
```

---

## Attachment Path Support

Supported attachment input includes Windows absolute paths:

```text
D:\Test\sample.txt
```

Quoted paths containing spaces:

```text
"D:\Project Files\Final Report.pdf"
```

Multiple explicitly requested attachments:

```text
Attach D:\Files\a.txt and D:\Files\b.pdf
```

Unicode filenames are also supported.

Filename-only lookup is restricted to approved locations.

NEXA does not recursively search the entire computer for attachment files.

---

## Attachment Validation

All attachments must pass validation before any Gmail draft is created.

Validation includes:

- File exists
- Regular file
- Readable file
- Safe filename
- Safe extension
- Protected-path checks
- Per-file size limit
- Total attachment size limit

Current limits:

```text
Maximum single attachment:
10 MiB

Maximum combined attachment size:
25 MiB
```

Attachment validation is all-or-nothing.

Example:

```text
Attachment A = Valid
Attachment B = Missing
```

Result:

```text
Entire draft operation fails safely.
```

NEXA does not create a partially attached draft.

---

## Sensitive File Protection

Sensitive files cannot be attached through NEXA.

Blocked examples include:

```text
credentials.json
token.json
.env
*.pem
*.key
*.p12
```

Protected paths include:

```text
D:\NEXA-Secrets\

%USERPROFILE%\.nexa_ai\gmail\
```

This prevents Gmail OAuth credentials and private key material from being accidentally attached to email drafts.

---

## Attachment Metadata Sanitization

Internally, NEXA may need a local filesystem path to read the selected file.

However, local paths are not returned in user-facing attachment metadata.

Safe metadata contains information such as:

```text
File Name
MIME Type
File Size
Validation Status
```

Example:

```json
{
  "file_name": "report.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 12345,
  "exists": true,
  "safe_status": "validated"
}
```

The following information is excluded:

```text
local_path
OAuth Token Paths
Secret Directory Paths
Raw Attachment Bytes
```

---

## MIME Attachment Architecture

Attachments are added as separate MIME parts.

The email body remains the primary editable text body.

```text
EmailMessage
   │
   ├── text/plain body
   │
   ├── attachment #1
   │
   ├── attachment #2
   │
   └── ...
```

NEXA uses:

```python
EmailMessage.add_attachment(...)
```

MIME type is inferred from the filename.

If the type cannot be determined, NEXA uses:

```text
application/octet-stream
```

---

## 2B.10 — Gmail Draft Browser Navigation

After NEXA successfully creates a Gmail draft, it can open Gmail in the user's default browser.

For normal compose and forward drafts, NEXA attempts to open the exact created draft when a safe message identifier is available.

Example:

```text
https://mail.google.com/mail/u/0/#drafts/<message-id>
```

For reply flows where an exact Gmail deep-link cannot be safely verified, NEXA falls back to:

```text
https://mail.google.com/mail/u/0/#drafts
```

This allows the user to:

```text
Review
Edit
Verify Recipients
Verify Attachments
Manually Press Send
```

NEXA does not press Send for the user during Phase 2B.

---

## 2B.11 — Attachment Parser Regression Fix

During manual verification, a parsing bug was discovered.

The command:

```text
Subject: NEXA Attachment Test.
Attach D:\Test\sample.txt
```

initially caused the word:

```text
Attachment
```

inside the email subject to be incorrectly interpreted as an attachment command.

This caused the subject to become:

```text
NEXA
```

instead of:

```text
NEXA Attachment Test
```

The attachment parser was corrected.

Attachment commands now require an actual path-like argument.

Therefore ordinary language such as:

```text
NEXA Attachment Test
attachment support
attachment issue
please see the attached file
this attachment is important
```

does not trigger attachment parsing.

Actual commands such as:

```text
Attach D:\Test\sample.txt
```

```text
Attach: D:\Test\sample.txt
```

```text
Attaching "D:\Project Files\report.pdf"
```

continue to work.

A regression test was added to preserve this behavior.

---

## 🧪 Phase 2B Automated Validation

Phase 2B underwent focused and full-regression testing.

| Validation | Result |
|---|---|
| Focused Phase 2B Test Suite | ✅ 67 Passed |
| Full Backend Test Suite | ✅ 409 Passed |
| Backend Compile Check | ✅ Passed |
| Frontend `npm run check` | ✅ Passed |
| `git diff --check` | ✅ Passed |
| Compose Draft | ✅ Verified |
| Reply Draft | ✅ Tested |
| Reply-All Draft | ✅ Tested |
| Forward Draft | ✅ Tested |
| Local Attachment Validation | ✅ Tested |
| Multiple Attachments | ✅ Tested |
| Sensitive File Blocking | ✅ Tested |
| Oversized File Blocking | ✅ Tested |
| MIME Attachment Structure | ✅ Tested |
| Metadata Sanitization | ✅ Tested |
| Draft-Only Send Protection | ✅ Verified |

---

## 🧪 Phase 2B Manual Verification

A real Gmail draft was manually tested using:

```text
Draft an email to <test-account>
saying please see the attached file.
Subject: NEXA Attachment Test.
Attach D:\Test\sample.txt
```

Verified result:

```text
Recipient                 ✅
Subject                   ✅ NEXA Attachment Test
Body                      ✅ please see the attached file
Attachment Directive      ✅ Removed from body
sample.txt Attachment     ✅ Present
Gmail Draft Creation      ✅
Automatic Email Sending   ✅ Did NOT occur
```

The manual test confirmed that the final real Gmail draft contained the expected subject, body, and local attachment.

---

## 🔐 Phase 2B Send-Path Verification

Final Phase 2B review confirmed:

```text
GoogleGmailProvider
        │
        └── send_prepared()
              │
              └── Direct Send Disabled
```

Search results:

```text
drafts().send
→ No active backend occurrence

messages().send
→ One legacy ExistingSkillGmailProvider occurrence
```

The legacy provider is not instantiated by the active runtime provider factory.

The active runtime creates only:

```text
MockGmailProvider
GoogleGmailProvider
```

Therefore the legacy direct-send implementation is not part of the active Phase 2B Gmail path.

---

## 🔒 Phase 2B Secret & Git Safety Verification

Before the Phase 2B commit, the staged diff was checked for sensitive information.

Protected files were not tracked:

```text
credentials.json
token.json
NEXA-Secrets
.env
```

Test-only credentials use non-secret placeholder values such as:

```text
access-token
refresh-token
client-id
client-secret
```

No real Gmail OAuth credential was committed.

---

## ✅ Phase 2B Final Status

```text
PHASE 2B
================================================

Natural-Language Compose       ✅
AI-Assisted Drafting           ✅
Recipient Validation           ✅
Header Injection Protection    ✅
Real Gmail Draft Creation      ✅
Compose OAuth Scope            ✅
Draft Readback Verification    ✅

Reply                          ✅
Reply-All                      ✅
Forward                        ✅
Gmail Thread Preservation      ✅
Reply-To Handling              ✅

Local Attachments              ✅
Windows Paths                  ✅
Quoted Paths                   ✅
Multiple Attachments           ✅
Unicode Filenames              ✅
MIME Attachment Parts          ✅
Sensitive File Blocking        ✅
Size Validation                ✅
Metadata Sanitization          ✅
All-or-Nothing Validation      ✅

Gmail Browser Draft Opening    ✅
Manual User Review             ✅
Manual Gmail Send              ✅

Automatic Send                 ❌ DISABLED
messages.send                  ❌ NOT ACTIVE
drafts.send                    ❌ NOT USED

Focused Tests                  ✅ 67 Passed
Full Backend Tests             ✅ 409 Passed
Frontend Typecheck             ✅ Passed
Manual Attachment Test         ✅ Passed
Git Diff Check                 ✅ Passed

STATUS: COMPLETE
```

---

## Phase 2B Git Milestone

Phase 2B was committed as:

```text
979adee
feat: complete Gmail Phase 2B draft workflow
```

and pushed successfully to:

```text
origin/supti-medha
```

Final repository state:

```text
Working Tree: Clean
Remote Sync: Up To Date
```

---

# ⏳ Phase 2C — Human Approval & Real Gmail Sending

**Status:** Planned

Phase 2C will introduce actual Gmail sending.

This phase must preserve strict Human-in-the-Loop control.

---

## Phase 2C Secure Send Architecture

Required flow:

```text
User Request
     │
     ▼
NEXA Generates Email
     │
     ▼
Gmail Draft / Preview
     │
     ▼
User Reviews Email
     │
     ▼
Explicit Approve & Send
     │
     ▼
HITL Approval Controller
     │
     ▼
Final Security Validation
     │
     ▼
Google Gmail API
     │
     ▼
Email Sent
```

The following architecture remains forbidden:

```text
LLM
 │
 ▼
Send Email
```

The LLM must never have direct Gmail sending authority.

---

## Phase 2C Planned Security Features

### Explicit Approval

NEXA must require a clear user action such as:

```text
Approve & Send
```

before Gmail sending is allowed.

---

### Approval Expiration

Existing approval must become invalid if the draft changes.

```text
Draft Approved
      │
      ▼
Draft Changed
      │
      ▼
Previous Approval Invalidated
```

---

### Recipient Revalidation

Immediately before sending:

```text
Recheck To
Recheck CC
Recheck BCC
```

---

### Attachment Revalidation

Immediately before sending:

```text
Verify File Still Exists
Verify Selected Attachment
Verify File Has Not Changed Unexpectedly
```

---

### Account Revalidation

Before sending:

```text
Confirm Active Gmail Account
```

NEXA must ensure the email is being sent from the account the user expects.

---

### Audit Logging

Important Gmail events should be recorded:

```text
Draft Created
Preview Generated
Approval Requested
Approval Granted
Email Sent
Send Failed
Approval Cancelled
```

Sensitive OAuth tokens must never appear inside audit logs.

---

### Failure Handling

The Gmail send pipeline should safely handle:

```text
API Failure
Network Failure
Expired OAuth
Permission Failure
Invalid Recipient
Attachment Failure
```

Dangerous or privileged Gmail operations must never be silently retried.

---

# 🗺️ Gmail Module Roadmap

| Feature | Status | Phase |
|---|---|---|
| Gmail Provider Architecture | ✅ Complete | Phase 1 |
| Mock Gmail Provider | ✅ Complete | Phase 1 |
| HITL Foundation | ✅ Complete | Phase 1 |
| Official Gmail API | ✅ Complete | Phase 2A |
| Gmail OAuth | ✅ Complete | Phase 2A |
| Read Emails | ✅ Complete | Phase 2A |
| Search Emails | ✅ Complete | Phase 2A |
| Unread Listing | ✅ Complete | Phase 2A |
| Open Email | ✅ Complete | Phase 2A |
| Read Thread | ✅ Complete | Phase 2A |
| Multi-Account OAuth | ✅ Complete | Phase 2A |
| Per-Account Token Isolation | ✅ Complete | Phase 2A |
| Connect Account | ✅ Complete | Phase 2A |
| Switch Account | ✅ Complete | Phase 2A |
| Disconnect Account | ✅ Complete | Phase 2A |
| Automatic OAuth Browser Flow | ✅ Complete | Phase 2A |
| Natural-Language Compose | ✅ Complete | Phase 2B |
| AI-Assisted Drafting | ✅ Complete | Phase 2B |
| Gmail Draft Creation | ✅ Complete | Phase 2B |
| Reply | ✅ Complete | Phase 2B |
| Reply All | ✅ Complete | Phase 2B |
| Forward | ✅ Complete | Phase 2B |
| Local Attachments | ✅ Complete | Phase 2B |
| Multiple Attachments | ✅ Complete | Phase 2B |
| MIME Attachment Support | ✅ Complete | Phase 2B |
| Recipient Protection | ✅ Complete | Phase 2B |
| Header Injection Protection | ✅ Complete | Phase 2B |
| Sensitive File Protection | ✅ Complete | Phase 2B |
| Metadata Sanitization | ✅ Complete | Phase 2B |
| Browser Draft Navigation | ✅ Complete | Phase 2B |
| Explicit Send Approval | ⏳ Pending | Phase 2C |
| Real Gmail Send | ⏳ Pending | Phase 2C |
| Approval Expiration | ⏳ Pending | Phase 2C |
| Final Recipient Validation | ⏳ Pending | Phase 2C |
| Final Attachment Validation | ⏳ Pending | Phase 2C |
| Active Account Revalidation | ⏳ Pending | Phase 2C |
| Gmail Audit Trail | ⏳ Pending | Phase 2C |
| Safe Error Handling | ⏳ Pending | Phase 2C |

---

# 📊 Overall Gmail Progress

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
░░░░░░░░░░░░░░░░░░░░ 0%
Human Approval + Real Send
⏳ PLANNED
```

---

# 🛡️ Security Principles

The Gmail module must continue following these security rules throughout development:

```text
1. Never expose OAuth tokens to the LLM.

2. Never commit Gmail credentials or tokens to Git.

3. Never allow the LLM to directly send email.

4. Treat received email content as untrusted input.

5. Require explicit human approval before sending.

6. Keep Gmail account tokens isolated from one another.

7. Use the minimum Google OAuth permissions required.

8. Revalidate recipients before sending.

9. Revalidate attachments before sending.

10. Revalidate the active Gmail account before sending.

11. Keep security-sensitive operations auditable.

12. Fail safely instead of silently performing privileged actions.
```

---

# 🚀 Current Development Position

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
⏳ NEXT
```

The immediate next development milestone is:

## ➡️ Phase 2C — Human Approval & Real Gmail Sending

Phase 2B is complete, validated, committed, and synchronized with the remote repository.

Phase 2C should introduce real Gmail sending only after explicit Human-in-the-Loop approval and final security revalidation.

---

# 📦 Current Gmail Module Capabilities

The current Gmail implementation supports:

```text
Official Gmail API
Real Gmail Read/Search
OAuth Authentication
Multi-Account Isolation
Account Connect
Account Switch
Account Disconnect
Automatic OAuth Browser Flow
Secure Local Token Storage

Natural-Language Email Composition
AI-Assisted Email Drafting
Real Gmail Draft Creation

Reply
Reply-All
Forward

Local Attachments
Windows File Paths
Quoted File Paths
Multiple Attachments
Unicode Filenames
MIME Attachment Parts
Sensitive File Blocking
Attachment Size Validation
Attachment Metadata Sanitization

Recipient Validation
Header Injection Protection
Gmail Thread Preservation
Draft Browser Navigation
```

The current implementation intentionally does **not** support automatic Gmail sending.

---

# 📈 Development Status

| Phase | Description | Status |
|---|---|---|
| Phase 1 | Gmail Foundation | ✅ Complete |
| Phase 2A | Real Gmail Read/Search + OAuth + Multi-Account | ✅ Complete |
| Phase 2B | Compose + Draft + Reply + Forward + Attachments | ✅ Complete |
| Phase 2C | Human Approval + Real Gmail Send | ⏳ Planned |

---

# 🔖 Latest Gmail Milestone

```text
Commit:
979adee

Message:
feat: complete Gmail Phase 2B draft workflow

Remote:
origin/supti-medha

Repository State:
Clean and synchronized
```

---

# ⚠️ Important Development Rule

Until Phase 2C has been explicitly implemented, reviewed, tested, and approved:

```text
NEXA MUST NOT SEND EMAIL AUTOMATICALLY.
```

Email flow must remain:

```text
NEXA Creates Draft
       │
       ▼
User Reviews Draft
       │
       ▼
User Manually Sends From Gmail
```

---

# ✅ Final Gmail Status

```text
NEXA GMAIL MODULE
================================================

Phase 1   ✅ COMPLETE
Phase 2A  ✅ COMPLETE
Phase 2B  ✅ COMPLETE
Phase 2C  ⏳ PLANNED

Current Runtime:
READ + SEARCH + COMPOSE + DRAFT + REPLY + FORWARD + ATTACHMENTS

Automatic Gmail Send:
DISABLED

Human Control:
ENFORCED
```

---

> **NEXA AI** — Secure, modular, human-controlled AI automation.
