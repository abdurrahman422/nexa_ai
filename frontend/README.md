# Nexa AI Frontend

## 1. Frontend Purpose

The frontend will provide the desktop user interface for Nexa AI. It will present the futuristic assistant experience, capture user interaction, show live system status, and communicate with the Python FastAPI backend through local REST and WebSocket connections.

## 2. Planned Stack

- Electron
- React
- Vite
- TypeScript
- Tailwind CSS
- Framer Motion
- Lucide React

## 3. Folder Responsibilities

- `electron/` — future Electron main-process and preload-layer files
- `src/app/` — application bootstrap, routing, and top-level UI composition
- `src/components/` — reusable UI, layout, and animation components
- `src/pages/` — screen-level modules for major product areas
- `src/hooks/` — reusable React hooks
- `src/services/` — frontend API clients and WebSocket service wrappers
- `src/state/` — shared client-side state management
- `src/styles/` — global styles, theme definitions, and Tailwind-related styling
- `src/types/` — shared TypeScript types used by the frontend
- `src/utils/` — small reusable helper utilities
- `tests/` — future frontend test files

## 4. UI Design Goal

- Futuristic cyberpunk/Jarvis-style desktop interface
- Dark theme
- Neon cyan and purple accents
- Glassmorphism surfaces
- Lightweight animation

## 5. Performance Rules

- Avoid heavy 3D in MVP
- Lazy-load large pages later
- Keep animation efficient for low-end laptops

## 6. Note

This phase creates only the frontend folder skeleton. Actual Electron, React, Vite, and Tailwind implementation will be added in later phases.


## Phase 04.2 Tailwind Theme Setup

Phase 04.2 adds the Nexa AI frontend theme foundation.

### Added

- Tailwind CSS setup
- Nexa AI theme color tokens
- PostCSS configuration
- Global CSS utilities
- Cyberpunk dark background
- Neon cyan and purple accents
- Glassmorphism utility classes
- Lightweight visual foundation for future UI components

### Not Added Yet

- Electron shell is not implemented yet.
- Backend integration is not implemented yet.
- Voice UI is not implemented yet.
- Reusable UI component library will be added in Phase 04.3.

## Phase 04.3 Reusable UI Components

Phase 04.3 adds the first reusable Nexa AI frontend UI component library.

### Added Components

- `GlassCard`
- `NeonButton`
- `StatusBadge`
- `MetricCard`
- `SectionHeader`

### Notes

- Components are frontend-only.
- Components use React, TypeScript, and Tailwind CSS.
- Components follow the Nexa AI cyberpunk/Jarvis-style design language.
- No backend integration has been added yet.
- No Electron shell has been added yet.
- Animated orb and waveform components will be added in Phase 04.4.
