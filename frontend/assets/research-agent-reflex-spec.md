# Research Agent — Reflex Build Spec

You are building a Reflex (Python web framework) app that replicates a chat UI
called **Research Agent**. This document describes exactly what to build:
layout, visual design, components, states, and interaction behavior. It does
**not** dictate Reflex syntax, state-management patterns, component library
choices, or file structure — make those decisions yourself. Everything below
is a product/UI requirement, not a code instruction.

A reference implementation exists in Streamlit (attached separately). Use it
only to understand *what data and controls exist* — do not port its layout
technique. Its scrolling architecture was broken in several ways; Section 2
below tells you exactly what correct behavior looks like instead.

---

## 0. What the product does (context only)

Research Agent is a chat interface over a research pipeline: the user asks a
question, the backend searches arXiv, ranks papers, synthesizes an answer
with citations, and builds a concept graph. The right side of the screen is
a persistent "workspace" showing the papers/graph/comparisons for whichever
search is currently active, while the left side is an ordinary chat thread.
You are not implementing the backend pipeline — assume it exists behind a
few functions/API calls and focus entirely on the UI shell, state wiring,
and interaction design described below.

---

## 1. Overall layout

Full-height, two-column app shell. No page-level scrolling — the app fills
the viewport exactly once, like a chat app (ChatGPT, Claude, Slack), not
like a long document.

```
+----------------------------------------------------------------+
| Header: brand + subtitle (left)         session status (right) |
+---------------------------+--------------------------------------+
| LEFT (30% width)          | RIGHT (70% width)                    |
| "Conversation" rail       | "Research workspace" rail            |
|                           |                                       |
+---------------------------+--------------------------------------+
```

- Left column: **30%** width, right column: **70%** width, with a visible
  gap between them (~24–32px).
- On narrow viewports (below ~900px), stack the columns vertically instead
  of side-by-side, and switch from "fixed-height app shell" to normal page
  scrolling for that breakpoint (see Section 2.4).
- Max content width ~1680px, centered, with ~26px horizontal page padding
  on desktop.

---

## 2. Scroll & layout architecture — READ THIS CAREFULLY

This is the part the Streamlit reference build got wrong repeatedly, so it
is being spelled out explicitly. **Every scrollable region in this app must
follow the same pattern:**

```
+----------------------------+
| fixed header(s)            |   <- never moves, sized to its content
+----------------------------+
| ONE scrolling region       |   <- fills all remaining space, scrolls
|                             |      independently, own scrollbar
+----------------------------+
| fixed footer (if any)      |   <- never moves (e.g. the message composer)
+----------------------------+
```

### 2.1 Rules, universally

- Any "header" element (rail title, settings bar, run-status strip, tab
  bar) must be a real, non-shrinking layout item — sized by its content,
  never overlapped or clipped by scrolling content, and never implemented
  by absolute/sticky positioning with a hand-computed pixel offset. If the
  header's content wraps to two lines, the layout must still work with zero
  changes.
- Each scrollable region must be the **only** thing that scrolls in its
  area — no nested scrollbars-within-scrollbars, no page-level scroll
  fighting with an inner scroll, on desktop.
- A footer that must always be reachable (the chat composer) is a fixed,
  non-shrinking layout item below the scroll region — it must be
  impossible for it to be pushed off-screen by content growing inside the
  scroll region above it.

### 2.2 Left rail (Conversation) — specific application

- Fixed header: "Conversation" title + "grounded synthesis" label.
- ONE scrolling region: the message list (all chat turns, the empty state,
  and the "thinking" status indicator all live inside this single scroll
  region — see Section 4).
- Fixed footer: the message composer (textarea + Send button). Always
  visible, always reachable, regardless of how much content is in the
  scroll region above it.
- When a new message is sent, auto-scroll the message list to the bottom
  so the new turn and the "thinking" indicator are immediately visible —
  do not require the user to manually scroll to see their own message go
  out or the response come in.

### 2.3 Right rail (Research workspace) — specific application

- Fixed header row: "Research workspace" title (left) + small caption
  "papers · graph · comparison" + a settings icon-button (right) that opens
  a popover/panel (see Section 6).
- Fixed run-status strip directly below the header: paper/node/edge counts
  on the left, timestamp on the right (see Section 5.2). If there is no
  active run, show a neutral placeholder strip instead ("no active research
  run / waiting").
- Fixed tab bar below that: **Papers / Concept graph / Compare**.
- Below the tab bar: **only the content of the currently active tab
  scrolls**, independently. Switching tabs does not affect scroll position
  of other tabs. The header, run-status strip, and tab bar never move,
  never get overlapped by tab content, and are never implemented as
  sticky-with-guessed-offset — they are real fixed-size layout regions,
  full stop.

### 2.4 Narrow viewports (< ~900px)

- Below this breakpoint, stack the two columns vertically.
- Abandon the "fixed app shell, everything scrolls internally" model for
  this breakpoint — instead let the page scroll normally (the way any
  ordinary mobile web page does), so a user can always reach content in
  the second (stacked) column and the composer stays reachable via a
  sticky-to-bottom footer or ordinary scroll, at your discretion, as long
  as it is never trapped below an unreachable fold.

---

## 3. Design tokens

These are pulled verbatim from an existing, real design-token extraction
(`design-tokens.css` / `design-tokens.json` / `design-system-extraction.md`)
from the same author's other codebase — this is the authoritative palette,
not a guess. It replaces any invented hex values. Implement it as real CSS
custom properties (light theme on `:root`, dark theme on a `.dark` class
toggle), whatever Reflex's idiomatic mechanism for that is — the values
below are fixed, the delivery mechanism is your call.

### 3.1 Color tokens — light theme (`:root`, default)

```
--radius: 0.625rem;
--background: hsl(97 4% 100%);
--foreground: oklch(0.241 0.005 285.823);
--card: oklch(1 0 0);
--card-foreground: oklch(0.241 0.005 285.823);
--popover: oklch(1 0 0);
--popover-foreground: oklch(0.241 0.005 285.823);
--primary: oklch(0.31 0.006 285.885);
--primary-foreground: oklch(0.985 0 0);
--secondary: oklch(0.967 0.001 286.375);
--secondary-foreground: oklch(0.31 0.006 285.885);
--muted: oklch(0.967 0.001 286.375);
--muted-foreground: oklch(0.652 0.016 285.938);
--accent: oklch(0.967 0.001 286.375);
--accent-foreground: oklch(0.31 0.006 285.885);
--destructive: oklch(0.577 0.245 27.325);
--border: oklch(0.85 0.004 286.32);
--input: oklch(0.85 0.004 286.32);
--ring: oklch(0.605 0.015 286.067);
```

### 3.2 Color tokens — dark theme (`.dark` class override)

```
--background: #000000;
--foreground: oklch(0.985 0 0);
--card: #0f0f0f;
--card-foreground: oklch(0.985 0 0);
--popover: #000000;
--popover-foreground: oklch(0.985 0 0);
--primary: oklch(0.92 0.004 286.32);
--primary-foreground: #0f0f0f;
--secondary: #111111;
--secondary-foreground: oklch(0.985 0 0);
--muted: #111111;
--muted-foreground: oklch(0.705 0.015 286.067);
--accent: #111111;
--accent-foreground: oklch(0.985 0 0);
--destructive: oklch(0.704 0.191 22.216);
--border: oklch(1 0 0 / 10%);
--input: oklch(1 0 0 / 15%);
--ring: oklch(0.552 0.016 285.938);
```

Implement **both** themes and a way to toggle between them (a simple
light/dark toggle in the header is enough — doesn't need to be
sophisticated). Default to light on first load.

### 3.3 Semantic mapping — apply these tokens consistently

- `background` → page background. `card` / `popover` → surfaces that sit
  above the page (paper cards, the settings popover, the composer, the
  "Thinking…" status box, dropdown menus).
- `foreground` → primary text. `muted-foreground` → labels, captions,
  eyebrows, metadata (this replaces the old "muted" gray usage —
  everywhere Section 4/5/6 says "muted" text, use `muted-foreground`).
- `primary` / `primary-foreground` → the app's one strong-contrast
  surface: the user's chat bubble, the "Send" button, any solid dark
  action button. (`primary` is a near-black/near-white depending on
  theme, not a saturated brand color — this app doesn't have one; treat
  `primary` as "ink".)
- `secondary` / `accent` → soft neutral fills (segmented-control track,
  hover states, subtle panel backgrounds) — these two tokens are
  numerically identical in the source and can be treated as
  interchangeable.
- `border` / `input` → all 1px borders and input outlines.
- `ring` → focus rings (`focus-visible`), not otherwise visible.
- `destructive` → reserved for genuine error states (search failed, etc.)
  — don't use it decoratively.

### 3.4 App-specific accent colors (layered on top, not from the token file)

The base token set above is a neutral system with no brand accent — this
app needs a few extra semantic colors that only apply to the concept
graph and a couple of small marks, since nothing in the base tokens
covers them:

| Purpose | Color | Notes |
|---|---|---|
| Concept-graph paper nodes | `#003C33` | dark green |
| Concept-graph concept nodes | `#5F7F70` | muted green |
| Concept-graph "similar to" edges | `#C6C7C4` | |
| Concept-graph "mentions" edges | `#D9DCD8` | |
| Fallback/avatar accent mark | `#FF7759` | coral, used sparingly (e.g. an icon-less fallback avatar) |
| Markdown/inline links | `#1863DC` | blue — links inside assistant messages, Abstract/PDF links |

Define these as their own tokens (e.g. `--graph-paper`, `--graph-concept`,
etc.) rather than hardcoding hex in components. They do **not** need dark
variants unless a value reads poorly on `#000000` — check contrast and
adjust only if necessary.

### 3.5 Typography

- **Font:** GeistPixel (a pixel/variable monospace font — this is a
  deliberate "technical tool" identity, not a default). Load it as a local
  variable font file if you have the asset available; otherwise fall back
  cleanly to `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
  monospace`. Apply it globally (body + all UI chrome), not just to code
  blocks.
- **Type scale** (rem, from the token set): `--text-xs: 0.75rem`,
  `--text-sm: 0.875rem`, `--text-base: 1rem`, `--text-lg: 1.125rem`,
  `--text-xl: 1.25rem`, `--text-2xl: 1.5rem`, `--text-3xl: 1.875rem`,
  `--text-4xl: 2.25rem`. Map the app's existing type usage onto this
  scale rather than picking arbitrary px values:
  - Page/brand title → `text-xl`–`text-2xl`, tight letter-spacing
    (-0.05em), medium weight.
  - Empty-state title → `text-2xl`, same tight tracking.
  - Paper card title → `text-lg`, semi-bold, tight tracking.
  - Body/markdown paragraphs, chat message text → `text-sm`, line-height
    ~1.75.
  - Labels/captions/eyebrows (e.g. "GROUNDED SYNTHESIS", "SCREENING ·
    UNREVIEWED", tab meta text, timestamps) → `text-xs`, uppercase, wide
    letter-spacing (~0.08–0.11em), `muted-foreground` color.
- Font weights used: `font-medium`, `font-semibold`, `font-bold` — no
  need for a wider weight range than that.

### 3.6 Shape, spacing, and elevation

- **Radius scale**, derived from `--radius: 0.625rem` (10px):
  `--radius-sm = radius - 4px` (~6px), `--radius-md = radius - 2px`
  (~8px), `--radius-lg = radius` (10px), `--radius-xl = radius + 4px`
  (~14px). Use `radius-lg`/`radius-xl` for cards/panels/popovers/dropdowns,
  `radius-md` for inputs and standard buttons.
  - **Exception, intentional:** the composer's "Send" button, the
    Keep/Maybe/Skip screening buttons, and the retrieve→rank→synthesize→
    map step pills in the empty state should stay **fully pill-shaped**
    (round ends, not `radius-md`) — that's a distinctive, deliberate shape
    accent in this app's screenshots, kept on top of the otherwise
    standard radius scale.
- **Spacing:** base unit `--spacing: 0.25rem` (4px); use a standard
  4px-multiple spacing scale throughout (common values in the source
  system: `p-4`, `px-4`, `py-2`, `p-6`, `gap-2`, `gap-3`, `gap-4`).
- **Shadows:** standard scale — `shadow-xs` (`0 1px 2px 0 rgb(0 0 0 /
  0.05)`) up through `shadow-xl`. Use `shadow-xs`/`shadow-sm` sparingly —
  most cards/panels should rely on the 1px `border` token, not a shadow,
  to stay flat and dense. Reserve a slightly stronger shadow (`shadow-md`
  or a custom soft elevated shadow) for the two elements that should read
  as "floating above" the scroll content: the composer and the
  "Thinking…" status card.
- **Chat bubbles:** user messages are a solid `primary`-background rounded
  rectangle with `primary-foreground` text, avatar-then-bubble as a row
  (avatar left, bubble follows — not right-aligned), with one corner
  (bottom-right) squared off slightly for a speech-bubble-tail effect.
  Assistant messages are plain text on `background` (no bubble), also
  preceded by a small round avatar.

### 3.7 Component class recipes (verbatim reference, adapt idiomatically)

These are the actual Tailwind/shadcn class recipes from the source
project. You are not required to use Tailwind or shadcn specifically —
translate the *intent* (structure, states, sizing) into whatever Reflex
idiomatically wants — but match this behavior exactly:

- **Primary button:** inline-flex, centered content, `gap-2`,
  `rounded-md`, `text-sm font-medium`, `h-9 px-4 py-2` (or `px-3` when an
  icon-only/icon+label button), background = `primary`, text =
  `primary-foreground`, hover = `primary` at 90% opacity, disabled =
  `pointer-events-none opacity-50`, focus-visible = ring using the `ring`
  token at 3px.
- **Secondary button:** identical structure, background = `secondary`,
  text = `secondary-foreground`, hover = `secondary` at 80% opacity.
- **Ghost button:** identical structure, transparent background, hover =
  `accent` background + `accent-foreground` text.
- **Input field:** `background`/`card` surface, `border` token outline,
  `foreground` text, `rounded-xl`-ish (use `radius-md`/`radius-lg`).
- **Card/panel:** `card` background, `card-foreground` text, `border`
  token outline, `radius-lg`–`radius-xl`, generous internal padding
  (`p-6`-ish for standalone cards, tighter for dense list rows).
- **Badge/pill** (e.g. paper status badges, step pills): small horizontal
  padding, `py-0.5`–`py-1`, `secondary`/`muted` background, `text-xs`,
  fully rounded, `whitespace-nowrap`.
- **Dropdown/select menu** (e.g. the Compare tab's Run A/Run B pickers):
  `popover` background, `popover-foreground` text, `border`, `radius-md`,
  `shadow-md`, `p-1`; items get `accent` background + `accent-foreground`
  text on focus/hover, `radius-sm`, small horizontal/vertical padding.
- **Tooltip/popover** (e.g. the settings gear popover): inverted-contrast
  surface (`foreground` background, `background` text) for tooltips
  specifically; the settings popover itself uses the normal `popover`/
  `popover-foreground` pairing, `border`, `shadow-md`, `radius-md`,
  small fade/zoom-in entrance animation.
- **Icons:** Lucide icon set, default size ~16px (`size-4` equivalent),
  color inherits from surrounding text color — don't hardcode icon colors
  independent of their text context except for the app-specific accents
  in 3.4 (graph nodes, avatar marks).

### 3.8 Motion

Keep motion minimal and utilitarian — this is a dense research tool, not
a marketing site:
- Buttons/interactive elements: `transition-all`, ~150ms, ease-out.
- Popovers/dropdowns/tooltips: a small fade + zoom-in on open (~95% →
  100% scale) is fine; nothing elaborate.
- The source project also contains several decorative effects (animated
  gradient backgrounds, per-character text shimmer, GSAP pixel-transition
  cards, heavy backdrop blur) — these exist in the source system but are
  **not required here** and should be avoided or used extremely sparingly;
  they don't fit a dense, information-first UI. Do not add them unless
  explicitly asked.

---

## 4. Left rail: Conversation

### 4.1 Header
Small row: "Conversation" (title, `foreground` color) left, "GROUNDED SYNTHESIS"
(small caption, uppercase, muted) right. Thin bottom border separating it
from the message list.

### 4.2 Empty state (no messages yet)
Centered card, vertically centered in the scroll region:
- Small square icon tile (rounded corners, thin border) containing a brand
  mark (arXiv icon in the reference; substitute your own).
- Title: "What are you researching?"
- One paragraph of muted explainer copy describing what happens when you
  ask a question (search variants → retrieve/rank papers → synthesize →
  build concept map).
- A horizontal row of 4 pill "steps" with arrows between them: **retrieve
  → rank → synthesize → map**. Purely decorative/explanatory, not
  interactive.

This empty state must disappear the instant the user sends their first
message and must **never** render simultaneously with a "thinking" status
or an actual message — those are mutually exclusive states driven by one
piece of state (has the conversation started / is a request in flight),
not by two independently-stale conditions. (This exact bug — empty state
and loading indicator both rendering at once, stacked, burying the input —
was the single biggest defect in the Streamlit reference. Design your state
so it is structurally impossible, not just usually-correct.)

### 4.3 Message list
Each turn is a row: small round avatar (colored circle with an icon/mark
inside — distinct color per role, e.g. coral/red-ish for user, amber/gold
for assistant) followed by the message content.

**User message:** dark rounded "bubble" containing the raw text the user
typed, left-aligned as a row (avatar, then bubble), not right-aligned like
some chat UIs — match the screenshots.

**Assistant message:** plain (no bubble) markdown-rendered text. Below the
text, one of:
- An **"Evidence · N supporting claims"** collapsible/expander. When
  expanded, lists each claim as bold text + a caption line with the arXiv
  ID and an italicized short supporting sentence in quotes.
- OR, if the answer wasn't grounded in retrieved papers (e.g. it came from
  a live web search fallback), a small uppercase caption instead: "LIVE WEB
  SEARCH · NOT FROM RETRIEVED PAPERS" (append "· ROUTER FALLBACK" when
  applicable).

Only one of these two footers appears per assistant message, never both.

### 4.4 "Thinking" / in-progress state
While a request is being processed, show an elevated card (soft shadow,
rounded, bordered) titled "Thinking…" with a small spinner, expandable to
show a live progress log — short status lines appended as the backend
progresses (e.g. "Route: new search", "Planning search queries",
"Searching arXiv", "Query 1/4", "Query 2/4", …). This card sits in the
message list scroll region, in place, as if it were the assistant's
in-progress turn. Once the response is ready, collapse/replace it with the
final assistant message (label can flip to something like "Answer ready"
and auto-collapse).

The internal progress log should have its own bounded max-height with its
own scroll if it grows long, rather than unboundedly growing the whole
card.

### 4.5 Composer (fixed footer)
- Small uppercase label above the input: "Ask a research question".
- A bordered, rounded, elevated card containing: a multi-line textarea
  (placeholder "Ask a research question…", a few lines tall, resizable)
  and a full-width "Send" button below it (dark pill button).
- Enter-to-submit is optional; a visible Send button is required.
- Clears the input on successful submit.
- This entire composer block is the fixed footer described in Section 2.2
  — it must never be pushed out of view.

---

## 5. Right rail: Research workspace

### 5.1 Header row
"Research workspace" title (left). On the right: a small caption "papers ·
graph · comparison", and a compact circular/square icon-button (gear icon)
that opens the settings popover described in Section 6. Keep this row
visually light — it's a fixed header, not a hero section.

### 5.2 Run-status strip
A thin row directly under the header, small uppercase muted text:
- Left: `{paper count} papers · {node count} nodes · {edge count} edges`
  (each number emphasized/darker than the surrounding label text).
- Right: a timestamp for when that search run completed.
- If there is no active run yet, replace this whole strip with a neutral
  placeholder: "NO ACTIVE RESEARCH RUN" (left) / "WAITING" (right).
- If the run has a degraded state (partial results, no results, or a
  search error), show a small inline banner/alert above this strip
  communicating that plainly (not blocking, not modal).

### 5.3 Tabs: Papers / Concept graph / Compare
Simple underline-style tabs, muted inactive label, ink-colored active
label with an underline indicator. Only one tab's content is mounted/
visible/scrollable at a time, per Section 2.3.

#### 5.3.1 Papers tab
- Small header row: "{N} papers · ranked evidence set" (left), "Download
  BibTeX" button (right).
- A vertical stack of collapsible paper rows, each collapsed by default,
  labeled `{index}  {title}{" · " + status if reviewed}`.
- Expanded, each paper shows:
  - A small icon tile (source mark, e.g. arXiv logo) + index/category/date
    eyebrow line + title (large, semi-bold) + arXiv ID + truncated author
    list (first 5 + "et al." if more) + a relevance score (right-aligned,
    small, e.g. "0.468").
  - A thin divider, then two links: "Abstract" and "PDF" (both open in a
    new tab).
  - Below the card: a short AI-written summary paragraph of the paper.
  - A row of three pill buttons: **Keep / Maybe / Skip**, plus a status
    caption to the right reflecting current screening state (e.g.
    "SCREENING · UNREVIEWED", updates to KEEP/MAYBE/SKIP once chosen).
  - A single-line text input: "Add a short screening note…" — freeform
    note per paper, persisted per session.
  - A collapsed "Citation chaining" expander containing a "Fetch
    references and citing papers" button. Once fetched, show two labeled
    lists — "REFERENCES · N" and "CITING PAPERS · N" — each entry showing
    title + year and an "Add" button that appends that paper into the
    current run's paper list (skip duplicates by arXiv ID).

#### 5.3.2 Concept graph tab
- A caption above the graph: "{N} papers · {M} concepts · {E} edges —
  click a paper node to open its PDF".
- An interactive node-link graph, pannable/zoomable, with two node types
  (paper, concept) visually distinguished by color and icon (see palette
  above), and two edge types (MENTIONS — directed, faint — and SIMILAR_TO —
  undirected, slightly darker, labeled "similar"). Clicking a paper node
  should open that paper's PDF in a new tab. Provide graph toolbar
  controls in the corner: refresh/re-layout, download, and expand-to-
  fullscreen icons.
- If there's no active run or the graph is empty, show a plain muted
  caption instead of an empty graph canvas: "The concept graph appears
  after a search."

#### 5.3.3 Compare tab
- If fewer than 2 search runs exist yet, show a dashed-border placeholder
  card: "Run at least two searches to compare result sets, shared papers,
  and shared concepts."
- Otherwise: two dropdowns ("Run A", "Run B") to pick which two runs to
  diff, each labeled with a truncated version of that run's original
  query.
- Below that: three summary metrics side by side — "Shared papers",
  "Unique to A", "Unique to B" — each a big number with a small label.
- Below that: a "Papers in both" list (arXiv ID + title per shared paper)
  and a "Shared concepts (N)" list of concept tags, when non-empty.

---

## 6. Settings popover (gear icon, top-right of workspace header)

A popover/panel (~380–400px wide, internally scrollable if it overflows
viewport height) containing, top to bottom:

1. **Pipeline controls** section:
   - "Papers per query" slider (10–150, step 10) + one-line help text
     underneath ("Candidate retrieval depth for every generated query.").
   - "Ranking top-k" slider (5–50, step 5) + help text ("Number of papers
     retained after ranking.").
   - "Query variants" slider (1–6, step 1) + help text ("Parallel
     formulations used to widen retrieval.").
2. **Response** section:
   - A segmented control with three options: Brief / Standard / Detailed.
   - Help text beneath that changes based on selection:
     - Brief → "1–2 sentences · tight evidence."
     - Standard → "3–5 sentences · balanced evidence."
     - Detailed → "5–8 sentences · expanded evidence."
3. **Session** section:
   - Two side-by-side stat tiles: "Messages" (count) and "Runs" (count).
   - If the active run has citation IDs, a collapsed "Citation IDs"
     expander containing them as a plain code block.
   - A full-width "Clear session" button that wipes all messages, all
     search runs, and the active-run selection, and returns the app to
     the empty state.

All of these controls are live/session-scoped — no save/cancel step,
changes apply immediately to the next request.

---

## 7. State model (behavioral, not implementation)

Describe your state however Reflex idiomatically wants it, but it must
represent these concepts distinctly and unambiguously:

- The list of chat messages (role, content, whether it's grounded in
  retrieved papers, which claims support it if any, which search run it's
  associated with if any).
- The list of search runs (each with its query, papers, concept graph,
  synthesis, status, timestamp), and which one is currently "selected" /
  active in the workspace.
- Whether a request is currently in flight (drives the "Thinking…" card
  and disables/holds the composer if you choose — at minimum it must
  suppress the empty state per Section 4.2).
- Pipeline settings (per-query count, top-k, num query variants, response
  length) — session-scoped, not per-message.
- Per-paper screening state (keep/maybe/skip + note text), keyed by paper
  + run so it doesn't collide across different search runs.
- Everything is in-memory / session-scoped. No persistence, no accounts,
  no database — matches the reference implementation's "dies when the tab
  closes" behavior. Don't add persistence unless asked.

---

## 8. Existing backend — already implemented, call it directly, do not stub

The arXiv search, ranking, synthesis, routing, citation-lookup, and BibTeX
generation logic is **already written** in separate modules. Do not
reimplement, mock, or stub any of it — call it directly, the same way the
reference Streamlit build does. Treat everything in this section as a
fixed interface you build the UI/state layer around.

### 8.1 Functions

- `pipeline.run_pipeline(question: str, *, top_k: int, per_query: int, num_queries: int, response_length: str, on_progress: Callable[[str], None]) -> result`
  Runs a brand-new search. `on_progress` is called repeatedly with short
  status strings (e.g. "Route: new search", "Searching arXiv", "Query
  1/4") — feed these into the live "Thinking…" progress log described in
  Section 4.4, in order, as they arrive. `result` carries: `queries`,
  `candidate_count`, `papers` (list of `RankedPaper`), `insights`,
  `graph`, `synthesis` (a `Synthesis`, possibly `None` on failure),
  `search_status` (one of `"ok"`, `"search_error"`, `"partial_results"`,
  `"no_results"`), `search_error`.

- `route.route(question: str, context_papers: list[RankedPaper], message_history: list[ChatMessage]) -> (intent: str, is_fallback: bool)`
  Decides what kind of turn this is. `intent` is one of `"new_search"`,
  `"follow_up_grounded"`, `"follow_up_general"`. Call this first, on every
  submitted question, before deciding which of the next two functions (or
  `run_pipeline`) to call. `context_papers` = the papers belonging to
  whichever search run is currently active/selected (empty list if none).
  `message_history` = all prior messages, i.e. everything except the
  message just submitted.

- `synthesize.follow_up(question: str, message_history: list[ChatMessage], papers: list[RankedPaper], concepts: list[str], *, top_n: int, response_length: str) -> Synthesis`
  Used when `intent == "follow_up_grounded"` — answers from the papers
  already in the active run's workspace, no new search. `concepts` is the
  deduplicated list of concept strings across the active run's insights
  (see 8.3). `top_n` = the same "Ranking top-k" setting from Section 6.

- `synthesize.follow_up_general(question: str, message_history: list[ChatMessage]) -> str`
  Used when `intent == "follow_up_general"` — answers via live web search,
  not grounded in retrieved papers. Returns plain text, not a `Synthesis`.

- `citations.get_citations(arxiv_id: str) -> dict`
  Returns `{"references": [...], "citations": [...]}`. Each entry is a
  dict with `title`, `year`, `authors` (list of str), and `arxiv_id`
  (possibly falsy/missing — only entries with a truthy `arxiv_id` can be
  "added" per Section 5.3.1's citation-chaining behavior). Call this only
  when the user opens a paper's "Citation chaining" panel and clicks
  fetch — it's not prefetched automatically.

- `bibtex.generate_bibtex(papers: list[RankedPaper]) -> str`
  Produces the full `.bib` file contents for the "Download BibTeX" button
  in Section 5.3.1 — feed this straight into a file-download action, don't
  reprocess it.

### 8.2 Data shapes (from `models`)

- `ChatMessage`: `role` ("user"/"assistant"), `content` (str), `intent`,
  `search_run_id` (nullable — which run this turn belongs to, if any),
  `is_unsourced` (bool — drives the "LIVE WEB SEARCH" footer vs. the
  "Evidence" expander in Section 4.3), `is_fallback` (bool), `claims`
  (list, possibly empty), `response_length` (str, the setting active when
  this turn was generated).
- `RankedPaper`: `arxiv_id`, `title`, `authors` (list), `summary`,
  `published` (date-ish string), `pdf_url`, `abs_url`,
  `primary_category`, `categories` (list), `relevance_score` (float),
  `status` (`"unreviewed"` / `"keep"` / `"maybe"` / `"skip"` — this is the
  screening state from Section 5.3.1, mutated directly by the Keep/
  Maybe/Skip buttons), `note` (nullable str — the screening-note text
  input).
- `SearchRun`: `id`, `query` (the original question), `queries` (the
  generated search variants), `candidate_count`, `papers` (list of
  `RankedPaper`, mutable — citation-chaining and screening edit this list/
  its items in place), `insights` (list, each with a `.concepts` list of
  strings — dedupe across all insights in a run to get the run's full
  concept list), `graph` (nullable; `.nodes` — each with `id`, `type`
  `"paper"`/`"concept"`, `label`; `.edges` — each with `source`, `target`,
  `type` `"MENTIONS"`/`"SIMILAR_TO"`), `synthesis` (a `Synthesis`,
  nullable), `search_status`, `search_error` (nullable), `timestamp`.
- `Synthesis`: `summary` (str — becomes the assistant message's
  `content`), `citations` (list of citation-id strings — shown in the
  Section 6 "Citation IDs" expander), `claims` (list, each with `.claim`
  str, `.arxiv_id` str, `.supporting_sentence` str — feeds the Evidence
  expander in Section 4.3).

### 8.3 Submit orchestration (exact sequence)

This is the logic that runs when the user submits a question — implement
it as-is, it's already correct in the reference build:

1. Append a `ChatMessage(role="user", content=question)` to the message
   list.
2. Let `current_run` = the currently selected `SearchRun` (or `None` if
   none exists yet). Let `context_papers` = `current_run.papers` if it
   exists, else `[]`.
3. Call `route(question, context_papers, message_history)` — pass every
   prior message *except* the one just appended in step 1.
4. Branch on `intent`:
   - **`"new_search"`** → call `run_pipeline(...)`, streaming its
     `on_progress` callback into the live status log. Build a new
     `SearchRun` from the result (generate an id, stamp current time),
     append it to the run list, and make it the selected/active run. Cap
     the run list at **10** runs — when adding the 11th, drop the oldest.
     Build the assistant `ChatMessage` from `result.synthesis.summary`
     (or a fallback string like "Search temporarily failed." if
     `synthesis` is `None`), with `is_unsourced = (len(result.papers) ==
     0)`, `claims = synthesis.claims`, `search_run_id` = the new run's id.
   - **`"follow_up_grounded"`** → call `follow_up(question,
     message_history, current_run.papers, concepts_of(current_run),
     top_n=<top-k setting>, response_length=<response-length setting>)`.
     Assistant message: `content = synthesis.summary`, `is_unsourced =
     False`, `claims = synthesis.claims`, `search_run_id =
     current_run.id`.
   - **`"follow_up_general"`** → call `follow_up_general(question,
     message_history)`. Assistant message: `content` = the returned
     string, `is_unsourced = True`, `is_fallback` = whatever `route()`
     returned, `claims = []`, `search_run_id = None`.
5. Append the assistant `ChatMessage`. Clear the in-flight/loading state.
   Auto-scroll per Section 2.2.

## 9. Explicit non-goals

- Do not build a settings/preferences page separate from the popover
  described above.
- Do not add authentication, multi-user support, or persistence beyond
  in-memory session state.
- Do not deviate from the monospace typographic identity — this is a
  deliberate "technical tool" aesthetic, not an oversight to "fix" with a
  default sans-serif font.
- Do not reimplement, mock, or stub `pipeline`, `route`, `synthesize`,
  `citations`, or `bibtex` — see Section 8. If a function genuinely can't
  be reached yet (e.g. missing API key in the dev environment), surface
  that as a real error state in the UI, not a fake success.
