# Nexa AI — Project Handover

> Paste-ready context for a new chat / new session. Self-contained.

## What this is
"Nexa AI" — a local-first desktop AI assistant. **Electron + React + Vite + TypeScript** frontend, **FastAPI** backend. Bangla/Banglish/English chat, voice, command execution (whitelist + confirmation gated), reminders, file search, web answers.

## Paths & how to run
- **Frontend (working dir):** `C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\frontend`
- **Backend:** `C:\Users\Abdur Rahman\Desktop\nexaai\nexaai\nexaai\backend` → run with `.\.venv\Scripts\python.exe run_backend.py` (serves `http://127.0.0.1:8000`)
- Build: `npm run build` (runs `tsc -b && vite build`). Type-check only: `npx tsc -b`.
- Dev/preview live: `npm run dev` — **the only way to actually SEE animations/motion**; the in-tool browser pane throttles rAF/CSS animations and `:focus`, so motion looks frozen there.

## Hard constraints (every task repeats these — never violate)
- **Do NOT modify** backend, APIs, routing, app state, business logic, safety/permissions/whitelist, or Electron shell.
- Build must pass with **0 TypeScript errors**.
- Animations must be **GPU-only** (transform / opacity / filter / translate longhand) and **reduced-motion gated** (`@media (prefers-reduced-motion: reduce)`).
- **Zero regression** — existing chat/features must keep working.

## Design system (the leverage point)
Token-driven. `src/styles/tokens.css` is the single source of truth — editing palette tokens re-skins everything. Modular CSS in `src/styles/system/*`, imported in cascade order by `src/styles/index.css`. Order matters (later wins): base, layout, cards, dashboard, page-hero, chat, buttons, forms, utilities, animations, primitives, sidebar, topbar, environment, interaction, alive, cinematic, hud, omega, omega2, omega3, ai-models.

**Current palette:** premium cyber neon — cyan `#2ef2ff`, blue `#3b7bff`, violet `#b24dff`, magenta `#ff3df0`, emerald `#10ffb8`, orange `#ff9a3d`.

## What's already built (visual "OMEGA" system — mostly done)
- **WebGL scene** (`src/environment/`, three.js + R3F + drei): massive holographic Earth (radius 4.1, GLSL vertex-distortion shader), energy beams (18 on high tier), thousands of particles, nebula, hex-grid, orbit satellites, energy rings, neural network, fog. Config in `src/environment/config.ts` (ENV_PALETTE + QUALITY_PRESETS low/med/high). Activity bus (`activity.ts` + `ActivityDriver.tsx`) drives AI thinking/command/voice modes → CSS vars `--nx-core-pulse/energy`, `--nx-ai-*`, root attrs `data-ai-mode`/`data-ai-state`.
- **CSS motion layers:** `alive.css` (breathing), `cinematic.css` (rotating conic borders, gradient text, hero tilt), `hud.css` + `CinematicHud.tsx` (corner brackets, scanlines, waveform, radar, glyph rain, cursor spotlight, AI-mode flash), `omega.css` (neon card borders, mouse tilt, sidebar/topbar effects), `omega2.css` (input focus, icons, toasts, click ripple via `OmegaFX.tsx`), `omega3.css` (independent card float via `translate` longhand, volumetric godrays, shockwave). Aurora + godrays mounted in `App.tsx`.
- **Physics pointer:** `src/interaction/hooks/usePointer.ts` — spring-eased inertial pointer publishing `--nx-mx/--nx-my/--nx-pointer-x/y`; self-parks when idle.
- **Key gotcha solved:** pointer tilt (on `transform`) + card float (on `translate` longhand) compose without conflict; entrance `nxRise` uses `backwards` fill so it releases `transform` back to the tilt.

## Most recent feature: Multi-LLM system (COMPLETE, verified)
- **Module:** `src/lib/llm/` — `BaseProvider` → `OpenAIProvider`, `GeminiProvider`, `ClaudeProvider`, `DeepSeekProvider`, `OllamaProvider`, `NexaBackendProvider`; `ProviderRegistry`, `ProviderManager` (config/status/analytics/persistence/subscription), `LLMRouter`, `errors.ts`, `useLLM` hook, `chat()` entry. OpenAI + DeepSeek share `OpenAICompatibleProvider`.
- **UI:** `src/components/settings/AiModelsSettings.tsx` (styled by `system/ai-models.css`), rendered as section 8 in `SettingsPageV2`. Model selector (Smart Auto / GPT / Gemini Pro / Gemini Flash / Claude / DeepSeek / Ollama), per-provider enable + key + model + Test, status (🟢🟡🔴⚪), drag-drop priority, analytics.
- **Zero-regression key:** the existing FastAPI chat (`requestChatMessage`) is registered as provider `nexa-backend` and is the **guaranteed final fallback** — with no API keys, the router resolves to it, so default behavior is identical. **Never remove it from the router's attempt order.**
- **Deliberately NOT routed:** the Dashboard Command Center chat (`pages/dashboard/CommandCenterPage.tsx`) stays on the direct backend path because it depends on backend action/confirmation/`pending_task` fields for safety-gated command execution. Only the **AI Chat page** (`pages/chat/ChatPage.tsx`) uses the router.
- **Persistence:** `localStorage` keys `nexa.llm.settings` + `nexa.llm.analytics`.
- **Verified:** 0 TS errors, build passes, 20/20 deterministic failover logic tests, Settings UI renders + persists, 0 console errors.

## Verification patterns (given tooling limits)
Preview pane **throttles animations, sometimes has a 0×0 viewport, screenshots time out, and `document.hasFocus()` is false (so `:focus` CSS won't evaluate)**. So verify via: `npx tsc -b` (0 errors) + `npm run build` + serve with `vite preview` + browser-pane JS checks: `glError === 0`, computed styles, DOM/attribute assertions, `localStorage` reads, click-through hit-tests, and console-error reads (expect none). For pure logic, bundle a test with `npx esbuild ... --bundle --platform=node --format=esm` + `node` (polyfill `localStorage`).

## Open items / caveats
- **The user keeps referencing an uploaded screenshot that does NOT arrive** on the assistant side — flag this each time and proceed with the current app layout, or ask them to re-attach.
- **Onboarding gate:** to reach the shell in preview, fill the name input (via native setter + `input` event) and click "Continue Setup", then any advance button.
- **Security note from an earlier audit:** `backend/.env` contains live API keys (Serper/Gemini/Groq/Mistral/Cerebras) — must never be committed/exposed; user should rotate. Do not touch backend.
- The user consistently wants **bold/dramatic** results, not conservative tweaks.

## Memory files
`C:\Users\Abdur Rahman\.claude\projects\C--Users-Abdur-Rahman-Desktop-nexaai\memory\` — `MEMORY.md` (index) + `multi-llm-architecture.md`.
