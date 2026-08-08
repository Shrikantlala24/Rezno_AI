# Project Status: Research Agent (React/TypeScript Migration)

## Completed Stages

- **Stage 0: Initial Project Setup**
  - Dependency set installed cleanly via `bun`.
  - Next.js 15, React 19, Tailwind v4 project skeleton established.
  - Light theme and warm amber accent palette (`#8B6F4E`) verified against reference specifications.
  - Primary font (`GeistPixel`) wired in globally.

- **Stage 1: Frontend Build — Layout, Components, Static Shell**
  - Three-column responsive workspace layout implemented:
    - Left rail: Icon sidebar + collapsible controls & citations panel.
    - Center column: Conversation thread with message bubbles, evidence expander, live indicator, and input bar.
    - Right panel: Paper Workspace with run selector, tabs, expanded/collapsed paper cards, screening state, and citation chaining.
  - Adherence to the **Modularity Standard** (Tier 1 primitives, Tier 2 domain components, Tier 3 `*Client.tsx` containers).

- **Stage 2: Backend Port + Real Data Wiring**
  - **Stage 2a**: Faithful TypeScript port of all Python pipeline blocks (`plan-query`, `search`, `rank`, `extract-insights`, `build-graph`, `synthesize`, `route`, `follow-up-grounded`, `follow-up-general`, `citations`, `bibtex`) using Zod schemas (`src/lib/schemas/paper.ts`), LangChain JS Gemini client (`src/lib/clients/gemini.ts`), and the arXiv API.
  - **Stage 2b**: Thin Next.js API route handlers in `src/app/api/` wired to the frontend UI with real loading states, router intent handling, and live pipeline execution.

---

## Upcoming Stages

- **Stage 3**: Real Concept Graph visualization & Compare Searches tab implementation.
- **Stage 4**: Eval harness & benchmark test case integration.
- **Stage 5**: Database persistence & user authentication.
- **Stage 6**: Production deployment configuration.
