# Nexa AI — Full Project Code Audit

**Date:** 2026-07-11
**Auditor:** Claude Code (read-only audit — no code was modified)
**Scope:** `backend/` (FastAPI, ~9,900 LOC Python), `frontend/` (React 19 + Electron 33, ~12,100 LOC TS/TSX), project configuration, docs, and repo hygiene.
**Verification:** Findings marked ✅ were reproduced by running the actual code or test suite; the rest are from static review.

---

## Executive Summary

Nexa AI is a local-first desktop assistant with a genuinely thoughtful safety design (whitelists, permission center, locked capabilities, audit log, draft-only messaging). The core safety intent is good. The main problems are:

1. **Live API keys sitting in plaintext** in `backend/.env` (Gemini, Groq, Mistral, Cerebras, Serper) — they must be rotated.
2. **The packaged Electron app cannot talk to the backend** — CORS only allows the Vite dev origin, so production (`file://`) builds break.
3. **3 backend tests fail** (pending-task continuation flow regression), reproduced in isolation. ✅
4. **A completely unauthenticated local API** that can launch apps/websites and toggle its own security permissions.
5. **Heavy duplication and dead code**: three separate intent-classification engines, a shadowed duplicate function, two unused "pipeline" layers, ~1.3 GB of leftover broken virtualenvs.
6. **A 3,215-line chat god-module** and a 3,601-line `App.tsx` that make the routing brittle (several confirmed misrouting bugs, e.g. "open password" launches Microsoft Word ✅).

| Severity | Count |
|---|---|
| Critical | 4 |
| High | 9 |
| Medium | 17 |
| Low | 12 |

---

## 1. Critical Issues

### C-1. Live API keys stored in plaintext `.env` (and reused across reports)
- **Severity:** Critical (Security / Secrets)
- **File:** `backend/.env` (lines 16, 33, 38, 54, 59)
- **Problem:** Real, currently-formatted API keys for Serper, Gemini, Groq, Mistral, and Cerebras are present in plaintext. The file is correctly git-ignored (verified: only `.env.example` is tracked, and no key appears in tracked files), but the keys exist on disk, have been pasted into an audit context, and `.env.example` itself says "Never commit real API keys."
- **Why it matters:** Anyone with disk access, a backup copy, or a screen share of this folder gets working credentials. Groq/Cerebras/Gemini keys are billable and rate-limited resources tied to your account.
- **Recommended fix:** Rotate **all five keys** now. Store them via OS credential storage or at minimum keep `.env` out of any shared/synced folder. Add a startup check that refuses to log key values, and never paste `.env` contents into reports.

### C-2. Packaged (production) Electron app is blocked by backend CORS
- **Severity:** Critical (Bug — production-breaking)
- **File:** `backend/app/main.py:25-34`, `frontend/electron/main.cjs:51-55`
- **Problem:** CORS `allow_origins` only lists `http://127.0.0.1:5173` / `http://localhost:5173`. In production the renderer is loaded with `loadFile(...dist/index.html)`, so its origin is `file://` (sent as `Origin: null`/`file://`). Every `fetch()` from the packaged app to `http://127.0.0.1:8000` will fail the CORS check in the renderer.
- **Why it matters:** The app only works in dev mode. A packaged build ships with a dead backend connection — every page (chat, permissions, reminders, voice) fails.
- **Recommended fix:** Either serve the frontend from the backend, use a custom `app://` protocol with `protocol.registerSchemesAsPrivileged` and add that origin, or (local-only app) add the appropriate origin(s) explicitly. Test a packaged build end-to-end before release.

### C-3. Backend test suite is failing (3 regressions in pending-task flow) ✅
- **Severity:** Critical (Bug / Process)
- **Files:** `backend/tests/test_chat.py`, `backend/tests/test_pending_tasks.py` vs `backend/app/chat/service.py:2675-2836`
- **Problem:** `3 failed, 272 passed` (verified by running pytest; failures reproduce in isolation, so they are genuine logic regressions, not test pollution):
  - `test_pending_generation_collects_platform_app_type_then_generates_code_context`
  - `test_app_planning_continuation_completes_pending_task`
  - `test_login_page_details_continuation_uses_generation_pending_task`
  The multi-turn continuation logic (`_handle_pending_task`) no longer clears/completes pending tasks the way the contract tests expect — e.g. "android app, medicine reminder" after "ami ekta app banate cai" leaves a dangling `PendingTask`.
- **Why it matters:** The pending-task state machine drives the assistant's multi-turn conversations. A stuck pending task silently hijacks unrelated follow-up messages for up to 30 minutes (TTL).
- **Recommended fix:** Debug `_handle_pending_task` for the `app_planning_details` / `llm_generation_details` branches until the suite is green; make a green test suite a hard gate for every phase commit.

### C-4. Unauthenticated local API can launch programs and toggle its own security controls
- **Severity:** Critical (Security / Architecture)
- **Files:** `backend/app/main.py`, `backend/app/api/routes/actions.py:51`, `backend/app/api/routes/permissions.py:47`
- **Problem:** The FastAPI server on `127.0.0.1:8000` has **no authentication at all**. Any process on the machine — and via CSRF/DNS-rebinding tricks, potentially web pages — can:
  - `PUT /api/permissions` to enable `trusted_quick_launch`, `trusted_whatsapp_draft_auto_open`, etc. (the security center's own toggles),
  - `POST /api/actions/app/open` with `user_confirmed: true` to launch whitelisted apps (`subprocess.Popen`),
  - `POST /api/actions/website/open` to open URLs in the default browser,
  - read audit history, contacts (names + phone numbers), and file-search results.
  CORS restricts *browsers reading responses*; it does not restrict non-browser processes and does not authenticate anyone.
- **Why it matters:** The elaborate "confirmation required" model is enforced by a boolean **the client sends** (`user_confirmed`). There is no server-side proof a human confirmed anything. The permission store that gates everything is itself writable by the same unauthenticated API.
- **Recommended fix:** Generate a random token at backend startup, hand it to Electron (env var/stdout handshake), require it on every request (`Authorization` header). Keep binding to `127.0.0.1`. Consider requiring a fresh per-action nonce for "confirmed" executions instead of a client-set boolean.

---

## 2. High Issues

### H-1. `eval()` used in the calculator
- **Severity:** High (Security — defense in depth)
- **File:** `backend/app/tools/calculator.py:26`
- **Problem:** `eval(expression, {"__builtins__": {}}, {})` executes user-derived text. It's gated by a strict regex (digits/operators only), so it is not exploitable *today*, but the entire safety of an `eval` on user input rests on one regex never changing.
- **Why it matters:** A future edit that loosens `CALCULATOR_RE` (e.g. adding `%`, `**`, parentheses, or names) silently turns this into code execution. `10**9**9` style inputs would also be a CPU/memory DoS if `**` is ever allowed.
- **Recommended fix:** Replace with an AST-based evaluator (`ast.parse(..., mode="eval")` walking only `BinOp/Num/UnaryOp`) or a tiny tokenizer loop. Also handle `ZeroDivisionError` explicitly — today `1/0` bubbles up and the chat layer shows a raw `"division by zero"` as a "blocked" status (verified ✅).

### H-2. Whitelist alias matching by substring: "open password" launches Microsoft Word ✅
- **Severity:** High (Bug with safety implications)
- **File:** `backend/app/actions/app_whitelist.py:104-117` (`raw in key`)
- **Problem:** `normalize_app_key` matches aliases with `raw in key` (substring). Verified: `get_allowed_app("open password")` → `(True, winword …)` because `"word" ⊂ "password"`. Similarly `"excel" ⊂ "excellent"`, `"files" ⊂ "profiles"`.
- **Why it matters:** With Trusted Quick Launch enabled, unrelated messages silently launch apps. It also erodes trust in the whitelist as a *precision* control.
- **Recommended fix:** Match aliases on word boundaries (token equality or `\b` regex), not substring containment.

### H-3. Three parallel, divergent intent-classification engines
- **Severity:** High (Architecture / Duplication)
- **Files:** `backend/app/chat/service.py:633-790` (`classify_task` — production), `backend/app/nlu/classifier.py` + `backend/app/router/task_router.py` (used **only** by tests/evals), `frontend/src/lib/commandUnderstanding.ts` (684-line TS copy)
- **Problem:** The production chat path uses `classify_task`; the `nlu`/`router` packages that `test_nlu_router.py` and `test_architecture_boundaries.py` verify are a separate brain the API never calls; the frontend re-implements intent detection a third time.
- **Why it matters:** Tests pass against code users never run — a false sense of coverage. Keyword lists (dangerous words, YouTube/WhatsApp hints, Banglish markers) already differ between the three copies and will keep drifting.
- **Recommended fix:** Pick one classifier (the `app/nlu` package is the cleaner shape), route `chat/service.py` through it, and delete the frontend copy in favor of the backend's `/commands/preview` response.

### H-4. `backend/app/chat/service.py` is a 3,215-line god module
- **Severity:** High (Architecture / Maintainability)
- **File:** `backend/app/chat/service.py`
- **Problem:** One module contains routing, ~30 keyword sets, weather/search/translation/calculator handlers, WhatsApp draft composition, contact CRUD parsing, pending-task state transitions, YouTube handling, and response formatting. `app/assistant/pipeline.py` explicitly documents the intended decomposition ("normalize → safety → classify → route → execute → compose") that never happened.
- **Why it matters:** This is where the failing tests, the shadowed duplicate function (H-5), and the dead helpers (D-2) came from — the file is too big to change safely. Every new skill increases collision risk in the keyword-routing chain, whose behavior depends on the *order* of ~25 `if` checks.
- **Recommended fix:** Extract each intent handler into `app/skills/<intent>.py` behind a common interface; keep `classify_task` and the dispatch table separate; target < 400 lines per module.

### H-5. Duplicate `conversational_answer` — first definition is dead, silently shadowed ✅
- **Severity:** High (Bug-prone dead code)
- **File:** `backend/app/chat/service.py:851` and `:1193`
- **Problem:** Two `def conversational_answer(...)` exist in the same module; the second (line 1193) shadows the first (~60 lines, line 851–909, including a duplicated capabilities/greeting block). Python raises no error.
- **Why it matters:** Anyone editing the first copy sees no effect and no warning. It also signals that linting (`ruff`/`flake8` F811 would flag this) is not running at all.
- **Recommended fix:** Delete the first definition; add `ruff` to CI (`F811`, `F401`, etc.).

### H-6. Confirmation model is client-asserted
- **Severity:** High (Security design)
- **Files:** `frontend/src/lib/backendAssistantClient.ts:398` (`user_confirmed: true` hardcoded), `backend/app/chat/service.py:1889/2908` (server builds requests with `user_confirmed=True`), `backend/app/api/routes/reminders.py:51`
- **Problem:** "Requires explicit confirmation" is enforced by a boolean that the caller sets. The frontend hardcodes `user_confirmed: true` for reminder creation; the chat service sets `user_confirmed=True` itself for trusted-mode executions. Nothing distinguishes a genuine user click from any programmatic call.
- **Why it matters:** Combined with C-4 (no auth), the confirmation ceremony provides UX, not security. Docs (`SAFETY_POLICY.md`) imply a stronger guarantee than the code provides.
- **Recommended fix:** Server-issued, single-use confirmation tokens: preview response returns a nonce; the execute call must return it. Even without full auth this stops blind one-shot POSTs.

### H-7. Chat/LLM request path can block a worker for minutes; retry config is dead
- **Severity:** High (Performance / Reliability)
- **Files:** `backend/app/llm/router.py:75-83`, `backend/app/llm/providers/_common.py:31`, `backend/.env:28-29`
- **Problem:** `complete()` tries up to 6 hosted providers **sequentially**, each with a fresh `httpx.post` and a 20 s timeout → worst case ~2 minutes for one chat message, synchronously. `NEXA_LLM_TIMEOUT_SECONDS=20` is honored but `NEXA_LLM_MAX_RETRIES` is read by nothing (verified: zero references in code). A new TCP+TLS connection is opened per call (no shared `httpx.Client`).
- **Why it matters:** The UI shows "Thinking…" with no cap; a provider outage degrades every message. Dead config keys mislead operators into thinking retries exist.
- **Recommended fix:** Share one `httpx.Client` with connection pooling; enforce an overall deadline (e.g. 25 s) across the fallback chain; implement or delete `NEXA_LLM_MAX_RETRIES`; consider async endpoints for the network-bound routes.

### H-8. Dangerous-keyword screening over-blocks ordinary questions
- **Severity:** High (Logic / UX)
- **Files:** `backend/app/actions/safety.py:22-38`, `backend/app/chat/service.py:643`
- **Problem:** `contains_dangerous_keyword` substring-matches words like `delete`, `remove`, `format`, `restart` against the whole message *before any other routing*. "How do I delete a row in Excel?", "how to format a date in Python", "my PC keeps restarting" → hard-blocked with "Blocked for safety."
- **Why it matters:** For an assistant whose target users ask how-to questions, this makes a large class of legitimate queries unusable, and it teaches users to rephrase around the safety layer (the worst outcome for a safety control).
- **Recommended fix:** Only apply the destructive-keyword block when the message also matches an *action/imperative* pattern (or when an execution intent is already detected). For pure Q&A intents, answer normally while still refusing to execute anything.

### H-9. `App.tsx` is a 3,601-line god component with a monolithic import line
- **Severity:** High (Architecture / Frontend)
- **File:** `frontend/src/app/App.tsx` (line 22 imports ~50 symbols in one statement)
- **Problem:** Page routing (11 pages via `useState`), backend health polling, voice session state, onboarding, command preview, history, and audit views all live in one component. Any state change re-renders the world; code review of a diff in this file is impractical.
- **Why it matters:** Same failure mode as H-4 mirrored to the client: high collision risk, unreviewable diffs, and re-render performance cliffs as features grow.
- **Recommended fix:** One component per page (already partly done under `src/pages/`), a small router (even a `switch` in a 100-line shell), and colocated state via context/hooks per feature.

---

## 3. Medium Issues

### M-1. File-search blocked-term/path filters misfire on substrings ✅
- **Files:** `backend/app/files/search.py:21-40`, `backend/app/files/safe_directories.py:6-16`
- **Problem (verified):** `"brunch photos"` is blocked as a search (`"run" ⊂ "brunch"`); `Desktop/attempt.pdf` is silently excluded from all results (`"temp" ⊂ "attempt"`). Any folder whose name contains "windows", "temp", or "appdata" as a substring disappears.
- **Why it matters:** Users get "no results" for files that exist, with no hint why.
- **Fix:** Match blocked terms on word boundaries; match blocked path keywords against whole path *segments*, not the raw string.

### M-2. Full recursive directory walk per search request
- **File:** `backend/app/files/search.py:136-163`
- **Problem:** `directory.rglob("*")` walks Desktop/Downloads/Documents on every request; each entry does `is_symlink()`, `resolve()` (inside `is_path_within_safe_directories`), and `stat()`. A Downloads folder with tens of thousands of files makes every search multi-second, and `resolve()` per entry is O(depth) syscalls.
- **Fix:** Use `os.scandir` recursion with pruning (skip blocked directories *before* descending), skip `resolve()` when the walk root is already a safe dir, and add a total-entries-scanned cap.

### M-3. Weather and time answers ignore the asked location
- **File:** `backend/app/chat/service.py:57-63` (hardcoded Dhaka lat/long), `:1597-1612` (only Dhaka/Kolkata)
- **Problem:** "What's the weather in London?" returns Dhaka weather; "time in New York?" returns Dhaka time. The reply labels say "Dhaka", so it's honest but wrong for the question.
- **Fix:** Extract the location entity; use Open-Meteo's geocoding API (same free provider); reply "I can only check Dhaka right now" when unsupported instead of answering a different question.

### M-4. Global single-session state breaks with more than one client
- **Files:** `backend/app/memory/pending_tasks.py:11,35`, `backend/app/memory/context_store.py:11,35`
- **Problem:** Pending tasks and conversation context are module-level dicts keyed by a constant `"local"`. Two open windows (or the Commands page + Chat page) share and clobber one pending task; state is lost on restart, and the TTL (30 min) means an abandoned task hijacks a later, unrelated message.
- **Fix:** Key by a client-supplied session ID (the request schema already carries `source`); persist or at least expose pending state via API so the UI can show/cancel it.

### M-5. TTS endpoint holds a global lock for the entire speech duration
- **File:** `backend/app/voice/tts_engine.py:53-83`
- **Problem:** `speak_text` runs `engine.runAndWait()` (seconds to tens of seconds for 400 chars) inside `_speak_lock` in a sync route. Concurrent calls serialize and each pins a threadpool worker; a loop of TTS requests starves the whole API.
- **Fix:** Queue speech on a dedicated worker thread and return immediately (`status: "queued"`), or at least add a per-request duration cap and reject when busy.

### M-6. Upload size limit enforced only after reading the whole body into memory
- **File:** `backend/app/api/routes/voice.py:113-114`
- **Problem:** `data = await audio.read()` loads the entire upload, then checks `len(data) > MAX_UPLOAD_BYTES`. A 2 GB POST is fully buffered before rejection.
- **Fix:** Stream to the temp file in chunks and abort as soon as the running total exceeds 15 MB (or check `Content-Length` first when present).

### M-7. Gemini API key sent in the URL query string
- **File:** `backend/app/llm/providers/gemini.py:14`
- **Problem:** `...:generateContent?key={key}` puts the credential in the URL, where proxies/logs/exception messages can capture it.
- **Fix:** Use the `x-goog-api-key` header (supported by the same endpoint).

### M-8. Electron entry-point triplication with real divergence
- **Files:** `frontend/electron/main.cjs` + `preload.cjs` (actually used), `frontend/electron/main.ts` + `preload.ts` (never compiled — `electron:build` is `echo ...`), `frontend/dist-electron/main.js` (stale committed build of the TS version)
- **Problem:** `package.json#main` points to `main.cjs`. The TS variants differ materially: `preload.ts` does **not** expose `backendUrl` (which `App.tsx:154` reads), `main.ts` lacks the single-instance lock that `main.cjs` has. Anyone "fixing" the TS files changes nothing.
- **Fix:** Delete two