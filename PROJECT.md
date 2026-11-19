# Rezno AI — Master Project Reference (PROJECT.md)

> **Audience**: AI Agents, System Architects, Core Maintainers, Academic Examiners.  
> **Purpose**: Single authoritative source of truth for the complete Rezno AI project.

---

## 1. Executive Summary & Problem Space

**Rezno AI** is an academic literature intelligence engine designed to solve the structural breakdowns in scientific paper discovery, comprehension, and synthesis. 

### Core Problems Solved:
1. **The Lexical Mismatch**: Academic repositories (arXiv, PubMed) rely on exact keyword Apache Lucene matching over titles and abstracts. Conversational researcher inquiries (e.g. *"how to make LLMs remember long context without VRAM blowup"*) fail to match the formal canonical terms used in papers (*"sparse sliding-window attention with linear complexity"*).
2. **The Hallucination & Attribution Gap**: Off-the-shelf LLMs and naive RAG pipelines fabricate citations and conflate metrics across papers. Rezno mandates that **every single generated claim is verified with an exact, verbatim sentence quoted directly from the paper's abstract**.
3. **The Disconnected Paper Problem**: Traditional search engines return flat, isolated lists. Rezno constructs a **dual-layer bipartite knowledge graph** showing shared canonical concepts and direct vector-similarity edges between papers.

---

## 2. High-Level Architecture & Pipeline Flow

The computational engine operates as a strictly deterministic, strongly-typed sequential pipeline (`pipeline.py`):

```
                       [User Natural Language Query]
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 1. Query Planning (plan_query.py)                                      │
 │    Expands 1 prompt into 3-4 Lucene queries (Canonical, Method, Cat)   │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 2. Concurrent Retrieval (search.py)                                    │
 │    Bounded HTTP timeouts (25s), ThreadPoolExecutor, per-query retry    │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 3. Dense Vector Re-Ranking (rank.py)                                   │
 │    all-MiniLM-L6-v2 (384-dim) normalized dot-product (doc_vecs @ q_vec)│
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 4. Grounded Synthesis & Verification (synthesize.py)                   │
 │    Joint summary + verbatim quote claim verification (SupportedClaim)  │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 5. Bipartite Knowledge Graph (graph.py)                                │
 │    Paper ──MENTIONS──▶ Concept, and Paper ──SIMILAR_TO──▶ Paper (top-k)│
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 6. Intent Routing (route.py)                                           │
 │    Grounded follow-up vs. broad Tavily search vs. new arXiv retrieval │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Subsystem Breakdown ("The Brain & Spine")

### 3.1 Multi-Query Planning (`plan_query.py`)
* **Role**: Translates colloquial natural language questions into formal arXiv Lucene boolean syntax.
* **Mechanism**: Invokes an LLM with structured output (`QueryPlan`) to generate 3–4 variants:
  * Canonical terminology preprint phrasing.
  * Known model/architecture names.
  * Subject category scoping (`cat:cs.CL`, `cat:cs.LG`, `cat:cs.AI`).
* **Guardrails**: ASCII regex whitelist validation (`^[\w\s:\-\[\]".]+$`), max length $\le 300$, LRU cached (`maxsize=128`), with automatic fallback to the original query on exception.

### 3.2 Resilient Retrieval (`search.py`)
* **Role**: Fetches hundreds of candidate preprints from arXiv API concurrently without blocking.
* **Mechanism**: Custom `_TimeoutSession` overriding `requests` defaults to enforce a hard 25-second timeout.
* **Failure Isolation**: Parallel query execution via `ThreadPoolExecutor`. If one query fails or times out, surviving queries still return papers (`status="partial_results"`).
* **Normalization**: Automatically strips version suffixes (`2106.09685v1` ➔ `2106.09685`) and deduplicates candidates.

### 3.3 Dense Semantic Re-Ranking (`rank.py`)
* **Role**: Reranks candidate pools based on deep semantic relevance to the user's specific query intent.
* **Mechanism**: Employs local sentence-transformer `all-MiniLM-L6-v2` (384-dimensional embeddings).
* **Mathematical Operation**: Unit-normalized embedding dot product:
  $$\text{scores} = \mathbf{D}_{\text{papers}} \cdot \mathbf{q}_{\text{query}}^T$$
* **Optimization**: Pre-warms model weights in a daemon background thread on module import to eliminate first-call cold start latency. Prunes candidate pools down to precision top-$k$ (default 20).

### 3.4 Grounded Claim Synthesis & Verification (`synthesize.py`)
* **Role**: Produces an executive literature brief with zero-hallucination guarantees.
* **Mechanism**: Uses structured Pydantic schema `ResearchAnalysis`. Generates:
  * Prose summary with bracketed citations (`[2106.09685]`).
  * List of `SupportedClaim` objects, each requiring:
    1. `claim`: Clear statement of the finding.
    2. `arxiv_id`: Supporting paper ID.
    3. `supporting_sentence`: The **EXACT, unedited verbatim sentence** extracted directly from the paper's abstract.
  * If no sentence in the abstract supports a claim, the claim is rejected.
* **Efficiency**: Single-pass LLM invocation generates the summary, validates claims, and extracts concepts simultaneously.

### 3.5 Bipartite Knowledge Graph Topology (`graph.py`)
* **Role**: Transforms tabular papers into an interactive, explorable conceptual web.
* **Node Types**:
  * `Paper` nodes (keyed by `arxiv_id`).
  * `Concept` nodes (canonical technical concepts normalized across papers, e.g., `concept::lora`).
* **Edge Types**:
  * Directed `MENTIONS` edges (`Paper ──▶ Concept`).
  * Undirected `SIMILAR_TO` edges (`Paper ──▶ Paper`) based on pairwise cosine similarity matrix of paper embeddings ($S = \mathbf{V} \cdot \mathbf{V}^T$, $\text{diag}(S) = -\infty$).
* **Dynamic Top-K Formula**: Employs $k$-nearest-neighbors per paper ($k = \min(3, N-1)$) rather than a static distance threshold, preventing graph saturation ("hairball") on dense topics while ensuring connected graphs on niche topics.

### 3.6 Intent Classifier & Contextual Router (`route.py`)
* **Role**: Manages multi-turn conversation without repeating full search pipelines unnecessarily.
* **Classification Routes**:
  * `follow_up_grounded`: User asks about already loaded papers ➔ answers strictly from loaded abstracts.
  * `follow_up_general`: Conceptual/introductory questions ➔ answers via live web search context (Tavily).
  * `new_search`: User pivots to an unrelated topic ➔ triggers a fresh arXiv search.
* **Efficiency**: Fast-path regex matching evaluates common intents in 0ms before falling back to LLM classification.

### 3.7 Citation Chaining (`citations.py`) & BibTeX (`bibtex.py`)
* **Role**: Traverses the intellectual heritage of literature.
* **Mechanism**: Queries Semantic Scholar Graph API for backward references and forward citing papers.
* **Export**: Deterministically formats kept papers into standard `.bib` entries for LaTeX/Overleaf workflows.

### 3.8 Offline Evaluation & Benchmark Suite (`evaluate.py`)
* **Role**: Provides quantitative proof of retrieval and ranking performance for academic evaluation.
* **Decoupled Metrics**:
  * **Pool Recall**:
    $$\text{Pool Recall} = \frac{|\text{Expected Papers} \cap \text{Retrieved Candidate Pool}|}{|\text{Expected Papers}|}$$
    *(Measures query planning and search engine coverage)*.
  * **Recall@k**:
    $$\text{Recall@k} = \frac{|\text{Expected Papers} \cap \text{Top-k Ranked Papers}|}{|\text{Expected Papers}|}$$
    *(Measures MiniLM vector re-ranking precision)*.
* **Test Cases (`eval_cases.py`)**: Ground-truth test queries mapped to canonical landmark papers (LoRA, RAG, Longformer, etc.).

---

## 4. Frontend & Presentation Subsystem ("The Face")

* **Tech Stack**: Vanilla ES6 JavaScript, HTML5 Canvas, modern CSS3 (Zero npm, zero bundler, zero build latency).
* **Graph Engine**: Standalone 2D physics simulation via `force-graph.min.js` (177 KB WebGL/Canvas).
* **Two-Rail Split Layout**:
  * *Left Rail (35%)*: Inquiry composer, streaming progress steps, executive brief with interactive citation badges, collapsible verified claims drawer.
  * *Right Rail (65%)*: Evidence Desk with Papers list, interactive Force/Radial Concept Map, run comparison diff matrix, and in-app slide-over PDF reader.
* **Resilient Hybrid State Store (`js/state.js`)**: Automatically detects live backend API; if offline or unconfigured, gracefully falls back to mock research runs with an indicator badge.

---

## 5. Core Data Schemas (`models.py`)

| Model | Key Fields | Purpose |
| :--- | :--- | :--- |
| `ArxivPaper` | `arxiv_id`, `title`, `authors`, `summary`, `published`, `pdf_url`, `categories` | Raw normalized paper metadata from arXiv. |
| `RankedPaper` | Inherits `ArxivPaper` + `relevance_score`, `status`, `note` | Paper with dense semantic similarity score and user triage state. |
| `SupportedClaim` | `claim`, `arxiv_id`, `supporting_sentence` | Verified atomic scientific claim backed by verbatim abstract quote. |
| `Synthesis` | `summary`, `citations`, `claims` | Complete grounded research response. |
| `ConceptGraph` | `nodes: List[GraphNode]`, `edges: List[GraphEdge]` | Bipartite graph payload for 2D visualization canvas. |
| `SearchRun` | `id`, `query`, `candidate_count`, `papers`, `graph`, `synthesis` | Self-contained, immutable snapshot of one complete research run. |

---

## 6. Directory Layout & Organization

```
Rezno_AI/
├── backend/                    # Core Python Intelligence & API Server
│   ├── main.py                 # FastAPI application & static mount
│   ├── pipeline.py             # Deterministic sequential pipeline orchestrator
│   ├── plan_query.py           # Multi-query expansion & Lucene planning
│   ├── search.py               # Concurrent arXiv API retrieval
│   ├── rank.py                 # MiniLM-L6-v2 dense vector re-ranker
│   ├── synthesize.py           # Grounded synthesis & verbatim claim extractor
│   ├── graph.py                # Bipartite knowledge graph builder
│   ├── route.py                # Intent classifier & context router
│   ├── citations.py            # Semantic Scholar citation chaining
│   ├── bibtex.py               # BibTeX exporter
│   ├── models.py               # Pydantic data schemas
│   ├── llm.py                  # Dynamic LLM provider loader (Gemini / Anthropic)
│   ├── evaluate.py             # Evaluation runner (Pool Recall vs Recall@k)
│   ├── eval_cases.py           # Benchmark ground-truth test cases
│   └── diagnostic_test.py      # Search depth & sorting diagnostics
├── frontend/                   # Vanilla Web Interface (Zero Build)
│   ├── index.html              # Main application markup
│   ├── css/                    # Modular CSS & design tokens
│   ├── js/                     # Modular controllers, state store, graph engine
│   └── assets/                 # Fonts, icons, and vendor graph bundle
├── docs/                       # Research Notes & Architecture Deep Dives
│   ├── rezno_brain_spine_deep_dive.md
│   └── context.md
├── legacy/                     # Archived Historical Implementations
│   └── reflex_v1/              # Preserved Reflex components and configurations
├── tests/                      # Automated Pytest Suite
│   ├── __init__.py
│   └── test_pipeline.py        # Core unit & integration tests
├── DECISIONS.md                # Architectural Decision Records (ADRs)
├── PROJECT.md                  # This master reference document
├── GEMINI.md                   # Agent guardrails & operating rules
├── pyproject.toml              # Root project dependencies & metadata
├── requirements.txt            # Locked pip dependencies
└── README.md                   # Top-level GitHub showcase document
```

---

## 7. Quickstart & Operational Commands

### Environment Setup
```bash
# Clone the repository
git clone https://github.com/your-username/Rezno_AI.git
cd Rezno_AI

# Install dependencies via uv (recommended) or pip
uv sync
# OR
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# Set up API keys in .env
cp .env.example .env
# Edit .env with GOOGLE_API_KEY (or ANTHROPIC_API_KEY)
```

### Running the Application
```bash
# Launch unified server (FastAPI backend + static frontend at http://localhost:8000)
uv run uvicorn backend.main:app --reload
```

### Running CLI Pipeline
```bash
# Run standalone research pipeline directly from terminal
uv run python -m backend.run "low rank adaptation parameter efficient fine tuning"
```

### Running Evaluation Benchmarks
```bash
# Run formal retrieval and ranking evaluation suite
uv run python -m backend.evaluate --top-k 20 --expand
```

### Running Automated Tests
```bash
# Execute pytest suite
uv run pytest tests/
```
