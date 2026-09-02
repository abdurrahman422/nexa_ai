# P2 Manual UI Smoke Checklist

Use this checklist when browser automation is unavailable or blocked.

## Setup

Start the backend:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend"
.\.venv\Scripts\Activate.ps1
python run_backend.py
```

Start the frontend:

```powershell
cd "C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\frontend"
npm.cmd run web:dev
```

Open:

```text
http://127.0.0.1:5173
```

## Pages

| Page | Expected result | Pass |
|---|---|---|
| Dashboard | Page loads and backend status shows connected when backend is running. | [ ] |
| Launcher | App/website launcher page loads; launch actions require confirmation. | [ ] |
| Web Answers | Web answer input loads; backend-required behavior is clear. | [ ] |
| Files/Document Preview | Read-only file search UI loads; file write operations are disabled. | [ ] |
| Reminders | Reminder creation/list UI loads; backend required. | [ ] |
| Settings | Settings loads; profile area shows local-only behavior. | [ ] |
| Security Center | Permissions list loads from backend when backend is running. | [ ] |
| History/Audit | History page loads and audit events panel can show backend events. | [ ] |
| Voice Push-to-Talk | Voice/PTT panel loads; transcription is preview-only and backend-required. | [ ] |
| Automation | Automation page loads; workflow templates are preview-only. | [ ] |
| AI Chat placeholder | Chat placeholder loads and is labeled not wired yet. | [ ] |

## Label Checks

| Label | Expected location | Pass |
|---|---|---|
| Not wired yet | AI Chat placeholder page/cards. | [ ] |
| Preview only | Automation workflow templates and preview-only modules. | [ ] |
| Local-only profile settings | Settings profile/personalization card. | [ ] |
| File write operations disabled | Files page/module note. | [ ] |
| Backend connected/online | Dashboard/sidebar/topbar status while backend is running. | [ ] |

## Notes

- Do not test destructive file operations; they are intentionally not implemented.
- Do not add arbitrary apps or websites; launcher targets are whitelist-only.
- Do not treat AI Chat or workflow templates as implemented features.

## P2.1 Sign-off Attempt Notes

Date: 2026-06-11

Automated browser verification could not be completed in this Codex session because the in-app browser runtime failed before navigation with:

```text
windows sandbox failed: runner error: CreateProcessAsUserW failed: 5
```

The app was opened in the normal browser with:

```powershell
Start-Process "http://127.0.0.1:5173"
```

HTTP-level runtime checks passed:

| Check | Result | Notes |
|---|---|---|
| Frontend dev server | Pass | `http://127.0.0.1:5173` returned HTTP 200. |
| Backend health | Pass | `http://127.0.0.1:8000/api/health` returned backend health JSON. |
| Backend-online detection path | Functionally detectable | Frontend polls backend `/api/health`, and the endpoint was reachable while frontend was running. |

Visual sign-off still needs manual confirmation in the opened browser:

| Page | Visual status | Note |
|---|---|---|
| Dashboard | Manual pending | Confirm page loads, backend says connected, command controls are visible. |
| Launcher | Manual pending | Confirm launch controls ask for confirmation. |
| Web Answers | Manual pending | Confirm input/buttons are visible and backend-required behavior is clear. |
| Files/Document Preview | Manual pending | Confirm read-only search UI loads and file write operations are disabled. |
| Reminders | Manual pending | Confirm create/list UI loads. |
| Settings | Manual pending | Confirm local-only profile label is visible. |
| Security Center | Manual pending | Confirm permissions list loads. |
| History/Audit | Manual pending | Confirm audit panel loads. |
| Voice Push-to-Talk | Manual pending | Confirm PTT panel loads and preview-only/backend-required messaging is clear. |
| Automation | Manual pending | Confirm workflow templates are preview-only. |
| AI Chat placeholder | Manual pending | Confirm Not wired yet label is visible. |
