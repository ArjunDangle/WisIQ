# Architecture & Tech Stack

## Overview
We are building the frontend for "WisIQ", an enterprise hardware AI assistant. The backend is a FastAPI service that streams tokenized responses via Server-Sent Events (SSE). 

## Core Stack
* **Framework:** Next.js (App Router) using the `src/` directory pattern.
* **Language:** TypeScript (Strict mode enabled).
* **Styling:** Tailwind CSS.
* **Animations:** Framer Motion.
* **State Management:** Zustand (preferred for managing chat history and session IDs).
* **Markdown Parsing:** `react-markdown` with `remark-gfm` and `react-syntax-highlighter` for code blocks and tables.
* **Icons:** `lucide-react`.

## Production Directory Structure
* `src/app`: App Router structure (`layout.tsx`, `page.tsx`). Purely for routing and layout.
* `src/components/ui`: Reusable, generic UI components (shadcn/ui aesthetic).
* `src/components/features/chat`: Domain-specific components (`ChatContainer`, `MessageBubble`, `ChatInput`, `HardwareBadge`).
* `src/hooks`: Custom React hooks (`useChatStream.ts`, `useHealthCheck.ts`).
* `src/services`: Pure fetch API wrappers separating network logic from UI (`chat.service.ts`, `health.service.ts`).
* `src/store`: Global state management (`chat.store.ts`).
* `src/types`: Global TypeScript interfaces and enums (`api.types.ts`, `chat.types.ts`).
* `src/lib`: Utility functions (e.g., Tailwind merge, UUID generators).
* `src/constants`: Environment variables and app configuration (`config.ts`).

## Development Rules
* Use functional components and React Hooks exclusively.
* Strictly separate presentation components (`components/`) from data-fetching (`services/`) and state-management (`store/` & `hooks/`).
* Ensure the application is fully responsive (mobile-first approach).
* All external API calls must hit the URLs defined in `src/constants/config.ts` (populated by `.env.local`).