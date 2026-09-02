# Nexa AI — Full Code Audit Report

**Date:** 2026-07-11
**Scope:** Entire repository (`backend/` FastAPI + `frontend/` Electron/React), ~22K lines of source.
**Method:** Static review of all backend modules and key frontend modules, plus empirical verification of suspected bugs and a full run of the backend test suite.
**Constraint:** No code was modified. This is a report only.

---

## Executive summary

Nexa AI is a local-first desktop assistant with a well-thought-out safety model: whitelisted apps/websites, locked-off dangerous permissions, read-only file search, draft-only WhatsApp, and an audit log. The safety *architecture* is genuinely good.

However, the audit found several real problems:

- **1 Critical**: Live third-party API keys (Gemini, Groq, Mistral, Cerebras, Serper) are committed in plaintext in `backend/.env` and present on disk. These are real, spendable credentials.
- **A `eval()` call** on user input in the calculator (contained, but a bad pattern and a latent crash).
- **Whitelist bypass via substring matching** — "open password" launches Microsoft Word; the safe-directory and file-search blockers over-match on substrings ("temp" blocks "attempt.pdf", "move" blocks "movie").
- **3 failing backend tests** (272 pass / 3 fail) around pending-task continuation.
- **A 3,215-line `chat/service.py`** god-module with two functions named `conversational_answer` (the first is dead code shadowed by the second).
- **~1.3 GB of dead virtualenvs** (`.venv.broken-*`) and a large amount of dead/facade code.

Counts by severity: **1 Critical, 4 High, 9 Medium, 11 Low.**

---

## CRITICAL

### C1. Live API keys committed in `backend/.env`
- **File:** `backend/.env` (lines 16, 33, 38, 54, 59)
- **Problem:** Real, active API keys are stored in plaintext and present in the working tree:
  - `SERPER_API_KEY=4a36426a…` (Serper.dev)
  - `GEMINI_API_KEY=AQ.Ab8RN6…` (Google Gemini)
  - `GROQ_API_KEY=gsk_1D1t…` (GroqCloud)
  - `MISTRAL_API_KEY=2577b6b4…` (Mistral)
  - `CEREBRAS_API_KEY=csk-r22x…` (Cerebras)
- **Why it matters:** Anyone with access to this machine, a backup, or a leaked copy can spend against these accounts. Even though `.env` is in `.gitignore` (verified — it is *not* currently tracked in git), the file itself is the secret store and it is sitting in a synced Desktop folder. The `.env.example` correctly warns "Never commit real API keys," but the real `.env` ignores that.
- **Recommended fix:**
  1. **Rotate/revoke all five keys immediately** — treat them as compromised.
  2. Keep secrets out of the repo tree entirely (OS keychain, or a `.env` stored outside the project and referenced by absolute path).
  3. Confirm they were never committed historically: `git log -p --all -- backend/.env` (currently clean, but verify after any history rewrite).
  4. Add a pre-commit secret scanner (e.g. `gitleaks`).

---

## HIGH

### H1. `eval()` executes user-influenced arithmetic
- **File:** `backend/app/tools/calculator.py:26`
- **Problem:** `result = eval(expression, {"__builtins__": {}}, {})`. The input is gated by `CALCULATOR_RE` (digits/operators only), so it is not currently an arbitrary-code-execution hole. But:
  - `eval` on any request-derived string is a fragile pattern; a future regex loosening turns it into RCE.
  - `1/0` raises `ZeroDivisionError` (verified) which propagates up to a generic `except Exception` in the chat handler and surfaces as a raw Python error string to the user.
- **Why it matters:** Defense-in-depth. A calculator should never need `eval`, and the current form is one regex edit away from a serious vulnerability.
- **Recommended fix:** Parse the two/three-operand expression manually (or use `ast.literal_eval` on a computed value / a tiny shunting-yard evaluator). Handle division-by-zero explicitly with a friendly message.

### H2. App whitelist bypass via substring alias matching
- **File:** `backend/app/actions/app_whitelist.py:104-117` (`normalize_app_key`)
- **Problem:** Alias resolution does `if key == raw or raw in key`. Because `"word"` is an alias, **"open password" normalizes to `word` and successfully launches Microsoft Word** (verified: `get_allowed_app('open password')` → allowed, `winword`). Any input containing a whitelisted alias as a substring resolves to that app.
- **Why it matters:** The whitelist is the core safety boundary for app launching. Substring matching makes it match unintended inputs, launching apps the user did not ask for. `"excel"`, `"word"`, `"paint"`, `"chrome"` etc. are all common substrings.
- **Recommended fix:** Match on whole tokens/words, not substrings. Tokenize the normalized text and require the alias to appear as a complete token (or exact phrase), e.g. `alias in key.split()` for single-word aliases.

### H3. Over-broad substring blocking causes false positives in file search & safe dirs
- **Files:**
  - `backend/app/files/safe_directories.py:6-16, 63-70` (`BLOCKED_PATH_KEYWORDS` includes `"temp"`, `"windows"`)
  - `backend/app/files/search.py:21-40` (`BLOCKED_SEARCH_TERMS` includes `"move"`, `"open"`, `"run"`, `"edit"`)
- **Problem:** Blocking is `keyword in text`. Verified consequences:
  - `contains_blocked_path_keyword("…/Desktop/attempt.pdf")` → **True** (matches "temp" inside "at**temp**t"). Any file whose name contains "temp", "move", etc. is silently skipped.
  - `is_blocked_file_search_text("brunch photos")` → **True** (matches "**r**un"? no — matches "move"? no) — actually matches because "brunch" contains no term, but `"remove"`/`"move"` catch words like "movie": `is_blocked_file_search_text("movie")` returns True.
- **Why it matters:** This is a correctness/UX bug: legitimate searches ("find my movie files", "attempt.pdf") are blocked or filtered out with no explanation, making the feature look broken. It also means the "safety" filter is matching the wrong things.
- **Recommended fix:** Use word-boundary matching for the intent/verb blocklist (`\bmove\b`), and for path keywords match on path *segments* (`part in Path(p).parts` lowercased) rather than raw substring.

### H4. `chat/service.py` is a 3,215-line god-module with duplicate/dead functions
- **File:** `backend/app/chat/service.py`
- **Problem:**
  - Two top-level definitions of `conversational_answer` (line 851 and line 1193). Python keeps the **last** definition, so the first (~50 lines, 851–909) is **dead code** that can never run yet looks authoritative.
  - The module mixes routing, NLU keyword tables, HTTP calls, WhatsApp parsing, translation, calculator dispatch, weather, and response building. A dedicated `app/nlu`, `app/router`, `app/assistant`, `app/search` already exist but `service.py` re-implements much of it inline (e.g. its own `CALCULATOR_RE`, `normalize_text`, `wikipedia_search`, `clean_web_query`).
- **Why it matters:** Extremely hard to test, reason about, or modify safely. The duplicate function is a live footgun — an editor of the "wrong" copy will see no effect.
- **Recommended fix:** Delete the dead first `conversational_answer`. Then split `service.py` along the seams that already have packages: move routing into `app/router`, NLU keyword tables into `app/nlu`, and keep `service.py` as a thin orchestrator.

---

## MEDIUM

### M1. Three backend tests fail
- **Files:** `backend/tests/test_pending_tasks.py:95, 107`; `backend/tests/test_chat.py::test_pending_generation_collects_platform_app_type_then_generates_code_context`
- **Problem:** 272 pass, **3 fail**. Failures are in pending-task continuation: after supplying details (e.g. "android app, medicine reminder" or "html css diye"), `get_pending_task()` is expected to be `None` but the task is still set — the continuation path isn't clearing the pending task in these branches.
- **Why it matters:** A stuck pending task changes routing for the next user message and indicates the multi-turn state machine has a real branch bug, not just a flaky test.
- **Recommended fix:** Trace `_handle_pending_task` for `app_planning_details` and `llm_generation_details`: when the branch produces a terminal answer, ensure `clear_pending_task()` runs on all exits (some early-return branches set/keep the task). Update or fix to match intended behavior.

### M2. CORS + no authentication on a local server binding
- **Files:** `backend/app/main.py:25-34`
- **Problem:** `allow_origins` is limited to localhost:5173 (good), but `allow_credentials=True` with `allow_methods=["*"]`/`allow_headers=["*"]`, and **every endpoint is unauthenticated**. Any process/page on the machine that can reach `127.0.0.1:8000` can trigger app launches, file searches over Desktop/Downloads/Documents, contact reads, and permission toggles.
- **Why it matters:** A malicious local webpage (via a browser that ignores the Origin allowlist, or any local script) can drive the assistant's side effects. For a desktop assistant this is the main remote-ish attack surface.
- **Recommended fix:** Add a per-session shared secret/token that the Electron shell injects and the backend requires on every request; bind strictly to loopback (already `127.0.0.1`); consider rejecting requests without the expected token header.

### M3. Permission bypass: trusted auto-open skips the `actions_*` permission gate
- **File:** `backend/app/chat/service.py:2214-2448`, `1854-1956`
- **Problem:** `_whatsapp_skill_response` checks `whatsapp_draft_skill` **or** `trusted_whatsapp_draft_auto_open`. If only the "trusted auto open" toggle is on, drafts open even when the base skill permission is off. `_execute_trusted_website_open` does re-check `actions_website`, but the layering is inconsistent across YouTube/WhatsApp/app paths and hard to audit.
- **Why it matters:** The permission model's intent (base capability gates the feature; "trusted" only removes the confirmation step) is not consistently enforced. Defaults ship with `trusted_youtube_auto_open` and `trusted_whatsapp_draft_auto_open` = **True**, so auto-open is on out of the box.
- **Recommended fix:** Require the base permission AND the trusted toggle for auto-open; default the "trusted_*" toggles to `False` so first-run always confirms.

### M4. Blocking network I/O and blocking `subprocess`/TTS inside sync request handlers
- **Files:** `backend/app/chat/service.py` (httpx sync calls), `backend/app/llm/providers/_common.py:31`, `backend/app/voice/tts_engine.py:78` (`engine.runAndWait()`), `backend/app/actions/app_executor.py:70`
- **Problem:** Route handlers are sync `def` and perform blocking work: synchronous `httpx.get/post` to weather/search/LLM providers (up to 20s timeout each, tried across up to 6 LLM providers serially), and `pyttsx3 runAndWait()` which blocks until speech finishes. Under Starlette these run in a threadpool, but multiple slow calls will exhaust it and stall the whole backend.
- **Why it matters:** A single search that fans out to several 8–20s providers can hold a worker thread for a minute; concurrent users/requests degrade sharply. This is the main scalability limit.
- **Recommended fix:** Use `async def` handlers with `httpx.AsyncClient`, run provider fallbacks with an overall deadline (and consider concurrency), and offload TTS to a background task rather than blocking the response.

### M5. New SQLite connection per operation; no shared pool/WAL
- **Files:** `backend/app/audit/event_log.py:33-37`, `backend/app/reminders/store.py:36-40`
- **Problem:** Every read/write opens a fresh `sqlite3.connect(...)`, runs `CREATE TABLE IF NOT EXISTS`, then closes. Combined with a global `threading.Lock`, all DB access is serialized and each op pays connection + schema-check overhead.
- **Why it matters:** Fine at current scale, but wasteful and a scalability floor. Under load the global lock serializes even reads.
- **Recommended fix:** Use a single connection (or small pool) with `check_same_thread=False` and WAL mode (`PRAGMA journal_mode=WAL`), create schema once at startup.

### M6. JSON stores rewrite the whole file with no atomicity or corruption guard
- **Files:** `backend/app/contacts/store.py:93-95`, `backend/app/permissions/store.py:151-154`
- **Problem:** `write_text(json.dumps(...))` overwrites in place. A crash/interruption mid-write leaves a truncated/corrupt JSON file; the readers swallow the error and silently return `{}` — i.e. **all contacts or permissions silently reset to defaults**.
- **Why it matters:** Silent data loss (contacts) or silent security-relevant reset (permissions revert to defaults, which include several `True`s).
- **Recommended fix:** Write to a temp file in the same directory and `os.replace()` (atomic on Windows/POSIX). Consider a `.bak` copy. Log when a read fails instead of silently returning `{}`.

### M7. Phone-number normalization rejects valid formats and hard-codes Bangladesh
- **File:** `backend/app/contacts/store.py:68-79`
- **Problem:** Only Bangladesh mobile shapes are accepted; anything else raises `ValueError`. The `"1"`+10-digit branch is unreachable-ish and can mis-handle intl numbers. There is no support for any non-BD contact.
- **Why it matters:** Correctness/usability — legitimate contacts can't be saved, and the error surfaces to the user as a block.
- **Recommended fix:** Store E.164 with an explicit country code and validate more permissively (e.g. `phonenumbers` library), keeping BD as the default region.

### M8. Weather is hard-coded to Dhaka regardless of the query
- **File:** `backend/app/chat/service.py:57-62, 1435-1449`
- **Problem:** `WEATHER_URL` has fixed lat/long for Dhaka. Any weather question ("weather in London") returns Dhaka's weather, with the answer labeled "Dhaka weather now".
- **Why it matters:** Silently wrong answers — worse than "not supported," because it looks authoritative.
- **Recommended fix:** Geocode the location from the query (Open-Meteo has a free geocoding endpoint) or explicitly state only Dhaka is supported.

### M9. Duplicate Vite config and duplicate WhatsApp/URL helpers
- **Files:** `frontend/vite.config.ts` + `frontend/vite.config.js` + `frontend/vite.config.d.ts` (three copies); `backend/app/tools/whatsapp_tool.py` duplicates `_whatsapp_draft_urls` from `chat/service.py:2176`
- **Problem:** Three Vite configs (the `.js`/`.d.ts` look like stale compiled output of the `.ts`) risk drift; two independent WhatsApp URL builders can diverge.
- **Why it matters:** Maintenance hazard — edits to one copy don't propagate; unclear which is authoritative.
- **Recommended fix:** Keep only `vite.config.ts`, gitignore the compiled `.js/.d.ts/.tsbuildinfo`. Have `chat/service.py` import from `app/tools/whatsapp_tool.py` (or delete the unused tool).

---

## LOW

### L1. ~1.3 GB of dead virtualenvs in the tree
- **Files:** `backend/.venv.broken-old-pc` (125M), `backend/.venv.broken-p3i` (412M), `backend/.venv_broken` (399M), plus the active `.venv` (412M)
- **Fix:** Delete the three `*broken*` venvs. They bloat the Desktop folder and any backup/sync.

### L2. Committed build artifacts
- **Files:** `frontend/dist-electron/main.js`, `frontend/dist-electron/preload.js` are tracked in git; `frontend/tsconfig.node.tsbuildinfo` (42 KB) and `tsconfig.tsbuildinfo` present.
- **Fix:** Add `dist-electron/` and `*.tsbuildinfo` to `.gitignore`; remove from tracking.

### L3. Two parallel Electron entry points (`.ts` vs `.cjs`)
- **Files:** `frontend/electron/main.ts` (ESM, opens DevTools, no single-instance lock) vs `frontend/electron/main.cjs` (CJS, single-instance lock, `package.json main` points here). The `.ts` is compiled to `dist-electron/main.js` but unused at runtime.
- **Fix:** Pick one source of truth. The `.cjs` is the one actually run; either generate it from the `.ts` or drop the `.ts`/`dist-electron` path.

### L4. Stale/inconsistent phase strings in health endpoints
- **Files:** `health.py:17` (`"phase": "03.4"`), `actions.py:28` (`"32.3"`), `commands.py:20` (`"15.2"`), `database.py:25` (`"22.4"`)
- **Fix:** Remove hard-coded phase numbers or derive from a single version constant; they're already inconsistent and misleading.

### L5. Unused config / dead facade modules
- **Files:** `backend/app/core/errors.py` (imported nowhere), `backend/app/core/logging.py` (`setup_logging` never called — backend has no logging configured), `backend/app/tools/{time_tool,weather,search_tool,app_launcher,youtube_tool}.py` (thin facades, mostly unused), `NEXA_LLM_MAX_RETRIES` env var (documented, read nowhere).
- **Fix:** Either wire up logging (recommended — there is effectively no structured logging) and error helpers, or remove the dead modules. Remove or implement `NEXA_LLM_MAX_RETRIES`.

### L6. Broad `except Exception: pass` / silent swallowing throughout
- **Files:** `files/search.py:87, 143, 160`, `contacts/store.py:88`, `permissions/store.py:121`, `search/service.py:185`, many more.
- **Problem:** Errors are silently discarded with no logging, making field debugging very hard.
- **Fix:** Log at debug/warning level before swallowing; narrow the exception types (avoid `except (OSError, Exception)` which is redundant, as in `search.py:87`).

### L7. `App.tsx` is 3,601 lines with a single massive import line
- **File:** `frontend/src/app/App.tsx:22` (one `import { ... } from "@/lib"` spanning ~40 symbols), whole file 3,601 lines.
- **Fix:** Split into route/page containers and hooks; break the barrel import.

### L8. `_pick_local_reply` uses `sum(ord(...))` as a pseudo-random seed
- **File:** `backend/app/chat/service.py:1179-1186`
- **Problem:** Deterministic "variety" via char-code sum is a code smell (collisions, not really varied). Harmless but odd.
- **Fix:** Use `random.choice` seeded per turn, or rotate by history length only.

### L9. `assert result is not None` in request path
- **File:** `backend/app/chat/service.py:1903`
- **Problem:** `assert` is stripped under `python -O`; if the loop ever left `result` as `None`, this would raise `AssertionError` (500) instead of a handled response.
- **Fix:** Replace with an explicit guard returning a blocked/failed response.

### L10. LLM provider order ignores config, and no timeout budget across fallbacks
- **Files:** `backend/app/llm/router.py:75-83`
- **Problem:** Providers are tried strictly serially; with 6 providers × up to 20s timeout, worst case is ~120s for one message. `NEXA_LLM_MAX_RETRIES` is unused.
- **Fix:** Add a total deadline; short-circuit after the first success (already) but cap total wall-clock; consider dropping unconfigured providers before the loop (they return `None` fast, but still add attempts).

### L11. `vosk-models.html` (43 KB) and test artifacts checked into backend root
- **Files:** `backend/vosk-models.html`, `backend/whisper_test_result.json`, `backend/stderr.log`, `backend/stdout.log`
- **Fix:** Move to `docs/` or delete; ensure logs are gitignored (they are via `*.log`, but the files still exist on disk).

---

## What is done well (context)

- **Safety-first design**: hard-locked permissions (`shell_command_execution`, `auto_send_messaging`, `file_write_operations`) that the API genuinely refuses to enable (`permissions/store.py:136-139`).
- **App executor explicitly blocks `cmd`/`powershell`** even if they somehow reach it (`app_executor.py:55-67`), and uses `subprocess.Popen([command], shell=False)` — no shell injection.
- **Network egress is host-whitelisted** in `web/answers.py` and `search/service.py` (`_safe_get` checks `hostname in ALLOWED_HOSTS`).
- **File search resolves symlinks and re-checks containment** (`is_path_within_safe_directories`), and never reads file contents.
- **Good test coverage** (275 tests) including architecture-boundary tests.
- **LLM router keeps keys server-side** and never returns them.

---

## Suggested remediation order

1. **C1** — rotate the five leaked API keys today; move secrets out of the tree.
2. **H2, H3** — fix substring matching in the app whitelist and the path/search blocklists (correctness + safety).
3. **M1** — fix the 3 failing pending-task tests.
4. **H1** — replace `eval()` in the calculator.
5. **H4** — delete the dead `conversational_answer`; begin splitting `chat/service.py`.
6. **M2, M3** — add local auth token; make "trusted" toggles require base permission and default off.
7. **M4, M5, M6** — async I/O, SQLite WAL/shared connection, atomic JSON writes.
8. **L1, L2, L11** — clean dead venvs and committed artifacts.
