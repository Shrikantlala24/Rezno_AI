# Rezno AI — Project Context & Progress Document

> **Last Updated:** November 15, 2026  
> **Status:** Frontend v2 Complete (Vanilla Web Architecture), Ready for Backend Integration  
> **Local Server:** `http://localhost:3000/`

---

## 1. Executive Summary & Architectural Pivot

Rezno AI is an academic literature research agent designed for researchers, scientists, and engineers. It performs arXiv retrieval, cross-encoder re-ranking, executive synthesis with claim-level evidence verification, concept mapping, and paper screening.

### Why We Pivoted from Reflex to Vanilla Frontend:
* **Previous State (`Version_1/`)**: Originally built using Reflex (`reflex[db]==0.9.6.post2`). Encountered heavy cloud build times, Node/SSR compilation issues with `react-force-graph-2d`, high latency, and memory bloat that breached free-tier VM limits.
* **The Pivot**: All legacy Reflex code, configurations, and experiments were preserved and cleanly archived into the `Version_1/` directory.
* **The New Architecture**:
  * **Frontend**: Pure HTML5, modern CSS3, and vanilla ES6 JavaScript. Zero bundlers, zero npm dependencies, zero build latency, instant hot-reload.
  * **Graph Visualization**: Self-contained `force-graph.min.js` (177 KB) running on HTML5 Canvas/WebGL with zero external network or CDN dependencies.
  * **Target Backend**: A lean, modular Python backend (e.g. FastAPI / SSE streaming) to connect to the existing retrieval and ranking logic.

---

## 2. Directory Structure

```
Rezno_AI/
├── assets/
│   ├── GeistPixel.woff2            # Local variable font asset
│   ├── GeistPixel.ttf
│   ├── favicon.ico                 # App favicon
│   └── vendor/
│       └── force-graph.min.js      # Standalone 2D physics graph engine (177 KB)
├── css/
│   ├── tokens.css                  # Semantic tokens (scholarly palette, typography, light/dark)
│   └── app.css                     # Component-scoped styling, layout shell, responsive rules
├── js/
│   ├── icons.js                    # Crisp Lucide-compatible inline SVG icons
│   ├── mock_data.js                # Realistic arXiv research runs & data schemas
│   ├── state.js                    # Reactive application state store & event dispatcher
│   ├── graph.js                    # Interactive 2D Concept Map controller & floating HUD
│   └── app.js                      # Master UI orchestrator, markdown parser, triage & PDF modal
├── Version_1/                      # Archived Reflex codebase and legacy configuration
├── index.html                      # Semantic application markup
└── context.md                      # This living context document
```

---

## 3. Detailed Breakdown of What Was Built

### A. Design System & Scholarly Typography (`css/tokens.css`)
* **Color Palette**:
  * **Canvas Background**: Warm Archival Paper (`#FBFBFA`) in light mode; Deep Slate (`#0C1017`) in dark mode (avoids harsh pitch-black glare).
  * **Surface / Sheets**: Pure White (`#FFFFFF`) / Slate Surface (`#141923`).
  * **Ink / Typography**: High-contrast Slate-Black (`#14171A`) / Light Gray (`#F0F3F6`), with accessible muted tones for abstracts (`#4E555F` / `#9AA4B2`).
  * **Academic Pine**: `#0D5C52` (light) / `#2DD4BF` (dark) for kept literature, active citations, and verified claims.
  * **Amber / Coral Accents**: `#92400E` / `#B4341B` for review states, triage warnings, and stop actions.
* **Typographic Hierarchy**:
  * **Body & Reading**: Clean academic grotesque (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`) with calibrated line heights (`1.5`–`1.65`) and constrained line length (`< 75ch`).
  * **Identifiers & Math**: Tabular monospace (`ui-monospace`, `Menlo`, `Consolas`) strictly reserved for arXiv IDs (`arXiv:2106.09685`), scores, and LaTeX expressions.
* **Eliminated Generic AI Tells**:
  * ❌ Removed tracked-out ALL-CAPS eyebrow labels (`GROUNDED SYNTHESIS`, `SCREENING · KEEP`).
  * ❌ Removed middle-dot chains (`A · B · C`) and repetitive card-within-card borders.
  * ❌ Standardized sentence case across all labels and actions.

---

### B. Application Shell & Layout (`index.html`, `css/app.css`)
* **Top Header (`.app-header`)**:
  * Brand mark: Open-book symbol in Pine + `Rezno` wordmark + `arXiv research agent` descriptor.
  * Status indicator: Quiet connection pill (`● arXiv connected`) and query counter (`2 queries`).
  * Controls: Theme switcher (Sun/Moon) and Pipeline Settings trigger.
* **Two-Rail Split Layout (`.workspace-split`)**:
  * **Left Rail (35% width, `.rail-synthesis`)**: Dedicated to inquiries, streaming synthesis, verified claims, and grounded input composer.
  * **Right Rail (65% width, `.rail-evidence`)**: Evidence Desk hosting Literature, Concept Map, and Compare views.
  * **Responsive**: Stacks into single-column scrollable page below `960px`.

---

### C. Left Rail: Synthesis & Conversation Thread (`js/app.js`)
* **Empty State**: Explains the research workflow with quiet process pills (`Retrieve → Rank → Synthesize → Concept Map`).
* **Inquiry Prompt Card (`.inquiry-card`)**: Left-accented card showcasing the user's research question.
* **Executive Literature Brief (`.synthesis-card`)**:
  * Formatted like a scientific executive summary.
  * **Interactive Citation Badges (`.cite-badge`)**: Citations like `[2106.09685]` are interactive buttons. Clicking one cross-highlights the paper on the Evidence Desk or focuses the node on the Concept Map.
* **Verified Claims Matrix (`.evidence-matrix`)**:
  * Collapsible evidence drawer listing claims with their direct supporting sentence in quotes and arXiv source pill.
* **Progress Indicator (`.progress-card`)**:
  * Linear calm spinner with real-time pipeline status updates (`Planning parallel arXiv queries`, `Re-ranking top-k candidates`, `Synthesizing brief`).
* **Grounded Input Composer (`.composer-box`)**:
  * Auto-growing textarea with `Enter to send` hint.
  * Active **Stop** button when searching to cancel in-flight queries.

---

### D. Right Rail: Evidence Desk (`js/app.js`, `js/graph.js`)
* **Command Desk Toolbar (`.desk-toolbar`)**:
  * Segmented view switcher with live count pills:
    * `Literature (4)`
    * `Concept Map (10)`
    * `Compare Runs`
  * Active run selector dropdown and `Export BibTeX` button.
* **Sub-Bar Filter Group (`.desk-subbar`)**:
  * 1-click status filtering: `All (4)`, `Keep (2)`, `Review (1)`, `Discard (1)`.
* **View 1: Literature Preprint Cards (`.paper-card`)**:
  * Status left-borders: **Deep Pine** for `Keep`, **Amber** for `Review`, muted with strikethrough for `Discard`.
  * Metadata: Category (`cs.CL`), year, arXiv ID, and match score (`94% match`).
  * Title and author line formatted to standard preprint conventions.
  * Actions: 1-click triage buttons (`Keep`, `Review`, `Discard`), in-app **Read PDF** button, and abstract link.
  * Methodology note input for recording research notes.
  * Expandable Citation Chaining panel: Fetch references & forward citing papers from Semantic Scholar with an `Add` button to incorporate them into the workspace.
* **View 2: Knowledge Graph Canvas (`.graph-canvas-frame`)**:
  * Rendered via `force-graph.min.js` on HTML5 Canvas.
  * Physics simulation with particle flow along mentions edges.
  * Floating Canvas HUD: `Force` / `Radial` layout toggle, `Zoom In`/`Out`, `Zoom to Fit`, `Download Image`, and `Fullscreen`.
  * Node selection drawer with connection degree, direct PDF opening, and literature cross-jump.
* **View 3: Compare Runs View**:
  * Run A & Run B dropdown selectors.
  * Venn overlap metrics (Shared papers, Unique to A, Unique to B).
  * Converging concept tags.

---

### E. In-App PDF Reader Slide-Over Drawer (`.pdf-drawer`)
* Eliminates context-switching to external arXiv tabs.
* Full-height slide-over drawer from the right edge with backdrop blur.
* Embeds the paper's PDF with external link fallback and quick-close button.

---

### F. Pipeline Settings Popover (`.popover-dialog`)
* Triggered from header gear button.
* Sliders: Papers per query (10–150), Ranking Top-K (5–50), Query formulations (1–6).
* Full session reset action ("Clear Session History").

---

## 4. Current State & Verification

* **HTTP Server**: Active and responding with `200 OK` on `http://localhost:3000/`.
* **Asset Integrity**: All styles (`css/tokens.css`, `css/app.css`), scripts (`js/*.js`), fonts (`assets/GeistPixel.woff2`), and vendor graph libraries load with zero HTTP errors.
* **Code Quality**: All JavaScript files validated with `node -c` (0 syntax errors).
* **Interactivity**: Verified cross-rail citation clicks, 1-click triage, floating graph HUD, and in-app PDF slide-over reader.

---

## 5. Next Steps: Backend Architecture & Integration

With the frontend contract, data shapes, and UI states locked in:

1. **FastAPI Modular Server**:
   - Create a clean `backend/` directory (e.g. `main.py`, `routers/`, `schemas.py`).
   - Wrap existing pipeline logic from `Version_1/` (`pipeline.py`, `search.py`, `rank.py`, `synthesize.py`, `citations.py`, `bibtex.py`).
2. **Streaming Protocol (Server-Sent Events)**:
   - Implement `/api/synthesize` as an SSE stream delivering:
     - `event: progress` (updates the progress bar text).
     - `event: papers` (populates the Evidence Desk literature cards).
     - `event: graph` (sends the nodes/edges for the Concept Map).
     - `event: token` (streams the executive brief text token-by-token).
     - `event: claims` (delivers the verified claims matrix).
3. **Citation & BibTeX Endpoints**:
   - `/api/citations/{arxiv_id}` (fetches Semantic Scholar references & citing papers).
   - `/api/bibtex` (generates `.bib` file for kept papers).
