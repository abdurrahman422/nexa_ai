# Phase 33 Summary — Better Bangla / Banglish Command Matching

## Phase Name

Phase 33 — Better Bangla / Banglish Command Matching

## Goal

The goal of Phase 33 was to improve Bangla and Banglish command matching so Nexa AI can better understand common Bangladesh-style user commands for apps, websites, file search, and dangerous/blocked operations.

## Completed Sub-Steps

### 33.1 — Bangla/Banglish Phrase Dictionary

- Created reusable command phrase dictionary.
- Added website phrase mappings.
- Added app phrase mappings.
- Added file search phrase hints.
- Added dangerous command phrase detection.
- Added command phrase normalization helpers.
- No UI or execution logic was changed in this step.

### 33.2 — App Command Matcher Improvement

- Improved app command detection using phrase helpers.
- Added support for Bangla/Banglish app commands.
- Improved Notepad, Calculator, Chrome, File Explorer, and VS Code detection.
- Kept app execution through backend only.
- UI theme remained unchanged.

### 33.2b — Fix Bangla App Intent Detection

- Fixed incorrect detection where Bangla app commands were being classified as YouTube search.
- Ensured app detection runs before website/YouTube detection.
- `ক্যালকুলেটর চালাও` now detects as `open_app`.
- Dangerous commands still detect as blocked.

### 33.3 — Website Command Matcher Improvement

- Improved website command detection using phrase helpers.
- YouTube commands still map safely to YouTube search/website execution flow.
- Google, GitHub, Facebook, Gmail, ChatGPT, and Stack Overflow commands map to `open_website`.
- App detection remains higher priority than website detection.
- Dangerous phrases remain blocked first.

### 33.4 — File Search Command Matcher Improvement

- Improved file search command detection.
- Added Bangla/Banglish scope detection for Downloads, Desktop, and Documents.
- Added extension detection for PDF, Word, images, Excel, and PowerPoint.
- Improved file search query cleanup.
- Dangerous file operations remain blocked.
- No file open/delete/move/rename/edit action was added.

### 33.5 — Validation and Commit

- Validate frontend build.
- Validate Commands page app command matching.
- Validate Commands page website command matching.
- Validate Commands page file search matching.
- Validate blocked dangerous commands.
- Validate existing execution flows.
- Commit Phase 33.

## Files Created or Updated

- `frontend/src/lib/commandPhrases.ts`
- `frontend/src/lib/index.ts`
- `frontend/src/lib/commandUnderstanding.ts`
- `frontend/src/app/App.tsx`
- `docs/phase_33_summary.md`

## Current Working Features

- Bangla/Banglish app commands are detected better.
- Bangla/Banglish website commands are detected better.
- Bangla/Banglish file search commands are detected better.
- Dangerous commands are blocked earlier.
- Commands page execution flow still works.
- Voice page execution flow still works.
- File search remains read-only.
- UI theme remains unchanged.

## Supported App Examples

- `notepad kholo`
- `নোটপ্যাড খোলো`
- `calculator kholo`
- `ক্যালকুলেটর চালাও`
- `chrome kholo`
- `ক্রোম খোলো`
- `file explorer kholo`
- `vs code kholo`

## Supported Website Examples

- `youtube kholo`
- `ইউটিউব খোলো`
- `google kholo`
- `গুগল খোলো`
- `facebook kholo`
- `gmail kholo`
- `chatgpt kholo`
- `stack overflow kholo`

## Supported File Search Examples

- `Downloads folder e pdf khuje dao`
- `ডাউনলোডে পিডিএফ খুঁজে দাও`
- `desktop e report file search koro`
- `ডেস্কটপে ছবি খুঁজে দাও`
- `ডকুমেন্টে ওয়ার্ড ফাইল খুঁজুন`

## Safety Rules

- Dangerous phrases are checked first.
- App execution still requires backend whitelist.
- Website execution still requires backend whitelist.
- File search remains metadata-only.
- No file content is read.
- No file is opened, moved, renamed, edited, or deleted.
- UI theme was not redesigned.

## Test Checklist

- `npm run build` works.
- `ক্যালকুলেটর চালাও` detects as `open_app`.
- `নোটপ্যাড খোলো` detects as `open_app`.
- `গুগল খোলো` detects as `open_website`.
- `ইউটিউব খোলো` detects as YouTube website command.
- `ডাউনলোডে পিডিএফ খুঁজে দাও` detects as `file_search`.
- `delete system32` is blocked.
- `powershell kholo` is blocked.
- Commands page execution still works.
- Voice page execution still works.
- File search UI still works.
- Existing premium Nexa AI UI remains intact.

## Next Phase

Phase 34 — Real Microphone Speech-to-Text

The next phase will replace/supplement voice demo transcript behavior with real microphone speech recognition:

- Speech recognition capability check
- Start/stop real listening
- Live transcript from real speech
- Transcript to command detector
- Validation and commit