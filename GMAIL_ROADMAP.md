# NEXA AI — Gmail Integration Development Roadmap

> **Project:** NEXA AI  
> **Module:** Gmail Integration  
> **Current Status:** Phase 2B Complete
> **Next Milestone:** Phase 2C - Human Approval & Real Email Sending
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

## Architecture

```text
NEXA Host Agent
        │
        ▼
    GmailAgent
        │
        ▼
 GmailProvider
   Abstraction
    │       │
    │       └── GoogleGmailProvider
    │
    └── MockGmailProvider
        │
        ▼
HITL Approval Controller
```

## Completed Work

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

## 🔐 Core Security Architecture

```text
LLM
 │
 │ Requests or prepares an action
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

NEXA now supports real Gmail access through:

```text
GoogleGmailProvider
```

Provider selection supports:

```env
NEXA_GMAIL_PROVIDER=google
```

The current Gmail OAuth scope is intentionally restricted to:

```text
https://www.googleapis.com/auth/gmail.readonly
```

This allows NEXA to read Gmail information while preventing email sending or mailbox modification during Phase 2A.

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
```

No Gmail OAuth token should ever be committed to GitHub.

---

## 2A.3 — Real Gmail Features

NEXA can now access real Gmail data.

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

A major security improvement was introduced to safely support multiple users and Gmail accounts.

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

That behavior has been removed.

The current connection flow is:

```text
Settings
   │
   ▼
Gmail Accounts
   │
   ▼
Connect account
   │
   ▼
Default Browser Opens Automatically
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

The OAuth operation now runs asynchronously.

The backend exposes only sanitized OAuth status information.

OAuth URLs and OAuth token values are not returned to:

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

The Gmail account lifecycle has been manually tested.

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
Connect account
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

# 🧪 Phase 2A Validation

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

# ✅ Phase 2A Final Status

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

# ✅ Phase 2B — Compose, Preview & Draft

**Status:** Complete

Phase 2B will introduce Gmail write preparation while maintaining the rule that NEXA must not automatically send emails.

The AI can prepare an email, but the user remains in control.

### Phase 2B Validation

- Focused Phase 2B tests: **67 passed**
- Full backend tests: **409 passed**
- Manual compose attachment test: **passed**

Phase 2C is next. Gmail sending and approval workflows remain unimplemented.

---

## Planned Phase 2B Flow

Example user request:

```text
Write an email to professor@example.com.

Subject: Project Meeting

Tell him that I would like to meet tomorrow at 10 AM.
```

NEXA should generate:

```text
To:
professor@example.com

CC:
None

BCC:
None

Subject:
Project Meeting

Body:
Dear Professor,

I would like to meet with you tomorrow at 10 AM.

Best regards,
...
```

The UI should then present:

```text
[ Edit ]
[ Save Draft ]
[ Approve ]
[ Cancel ]
```

---

## Phase 2B Planned Features

### Email Composition

- Natural-language email composition
- Recipient extraction
- Subject generation
- Email body generation
- CC support
- BCC support
- Sending-account selection

### Email Preview

The user must be able to review:

```text
Sending Account
To
CC
BCC
Subject
Body
Attachments
```

before any privileged Gmail action occurs.

### Draft Support

Planned actions:

```text
Save Draft
Edit Draft
Discard Draft
```

### Reply Support

Planned support:

```text
Reply
Reply All
Forward
```

### Attachment Support

Planned flow:

```text
Select Attachment
      │
      ▼
Preview Attachment
      │
      ▼
Verify Attachment
      │
      ▼
Attach to Draft
```

### Safety Checks

Before any Gmail write preparation:

```text
Validate recipient
Validate active Gmail account
Validate attachments
Validate subject and body
Detect suspicious recipient changes
```

---

# ⏳ Phase 2C — Human Approval & Real Email Sending

**Status:** Planned

Phase 2C introduces actual email sending.

This phase must preserve strict Human-in-the-Loop controls.

---

## Secure Send Architecture

Required flow:

```text
User Request
     │
     ▼
NEXA Generates Email
     │
     ▼
Email Preview
     │
     ▼
User Reviews Email
     │
     ▼
Explicit User Approval
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

The following architecture is forbidden:

```text
LLM
 │
 ▼
Send Email
```

The LLM must never have direct Gmail sending authority.

---

# 🔐 Phase 2C Planned Security Features

## Explicit Approval

NEXA must require a clear user action such as:

```text
Approve & Send
```

before Gmail sending is allowed.

---

## Approval Expiration

Existing approval must become invalid if the email content changes.

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

## Recipient Revalidation

Immediately before sending:

```text
Recheck To
Recheck CC
Recheck BCC
```

---

## Attachment Revalidation

Immediately before sending:

```text
Verify file still exists
Verify selected attachment
Verify file has not changed unexpectedly
```

---

## Account Revalidation

Before sending:

```text
Confirm active Gmail account
```

NEXA must ensure the email is being sent from the account the user expects.

---

## Audit Logging

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

## Failure Handling

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
| Compose Email | ✅ Complete | Phase 2B |
| Email Preview | ✅ Complete | Phase 2B |
| Save Draft | ✅ Complete | Phase 2B |
| Edit Draft | ✅ Complete | Phase 2B |
| Reply | ✅ Complete | Phase 2B |
| Reply All | ✅ Complete | Phase 2B |
| Forward | ✅ Complete | Phase 2B |
| Attachments | ✅ Complete | Phase 2B |
| Recipient Protection | ✅ Complete | Phase 2B |
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
░░░░░░░░░░░░░░░░░░░░ 0%
Compose + Preview + Draft
⏳ NEXT


Phase 2C
░░░░░░░░░░░░░░░░░░░░ 0%
Approval + Real Send
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
⏳ NEXT
     │
     ▼
Phase 2C
⏳ AFTER PHASE 2B
```

The immediate next development milestone is:

## ➡️ Phase 2B — Compose + Preview + Draft

Phase 2C should begin only after Phase 2B is stable, secure, and fully tested.

---

# Current Gmail Module Status

**NEXA Gmail Read/Search integration is operational.**

The current implementation supports:

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
Read-Only Gmail Protection
```

The next major development objective is to safely introduce Gmail write preparation without giving the LLM direct email-sending authority.

---

## Development Status

**Phase 1:** ✅ Complete  
**Phase 2A:** ✅ Complete  
**Phase 2B:** ⏳ Next  
**Phase 2C:** ⏳ Planned  

---

> **NEXA AI** — Secure, modular, human-controlled AI automation.