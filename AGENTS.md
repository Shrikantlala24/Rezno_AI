# Agent Operating Manual & Onboarding Hub (AGENTS.md)

> **Universal entry point for AI Coding Agents** (Claude Code, Cursor, Copilot, Gemini CLI, Windsurf).  
> **Repository**: Rezno AI — Academic Literature Intelligence Engine

---

## 1. Project Overview

**Rezno AI** is an academic literature intelligence engine engineered to overcome the core breakdowns of scientific paper discovery, comprehension, and synthesis:
1. **Lexical Mismatch**: Translates conversational researcher inquiries into formal arXiv Lucene boolean queries across canonical terminology, method variants, and subject classifications (`backend/core/plan_query.py`).
2. **Dense Semantic Re-Ranking**: Projects retrieved preprint candidate pools into 384-dimensional dense vector space using `all-MiniLM-L6-v2` and computes normalized cosine similarity scores to surface true conceptual relevance (`backend/core/rank.py`).
3. **Verbatim Grounded Synthesis**: Completely eliminates citation hallucination by requiring that every generated claim be paired with an unedited, verbatim sentence extracted directly from the paper's abstract (`backend/core/synthesize.py`).
4. **Bipartite Concept Graph Topology**: Constructs dual-layer interactive knowledge graphs mapping both `Paper ──MENTIONS──▶ Concept` and `Paper ──SIMILAR_TO──▶ Paper` topological edges (`backend/core/graph.py`).

---

## 2. Repository Directory Map

```
Rezno_AI/
├── backend/
│   ├── api/                    # FastAPI web service layer
│   │   ├── routes/             # Search, citation, and bibtex route controllers
│   │   └── main.py             # FastAPI entrypoint, SSE streaming, static mount
│   ├── core/                   # The Brain & Spine (pure computational engine)
│   │   ├── models.py           # Strongly-typed Pydantic schemas (ArxivPaper, etc.)
│   │   ├── pipeline.py         # Sequential deterministic pipeline runner
│   │   ├── plan_query.py       # Multi-query expansion & Lucene planning
│   │   ├── search.py           # Resilient multi-threaded arXiv API client
│   │   ├── rank.py             # Sentence-transformer dense vector re-ranker
│   │   ├── synthesize.py       # Grounded synthesis with verbatim quote verification
│   │   ├── graph.py            # Dual-layer bipartite concept graph builder
│   │   └── route.py            # Intent router & conversational follow-up handler
│   ├── integrations/           # External service clients (LLM providers, BibTeX)
│   │   ├── llm.py              # Provider-agnostic LLM initializer (Gemini, Claude)
│   │   ├── citations.py        # Semantic Scholar & citation lookups
│   │   ├── bibtex.py           # BibTeX citation entry generator
│   │   └── web_search.py       # Tavily fallback search provider
│   ├── evaluation/             # Retrieval benchmark harness & diagnostics
│   │   ├── evaluate.py         # Precision@K, Recall@K, MRR evaluation benchmark
│   │   ├── eval_cases.py       # Ground-truth test query sets
│   │   └── diagnostic_test.py  # System diagnostic test suite
│   └── cli.py                  # Standalone command-line research interface
├── frontend/                   # Zero-build vanilla web cockpit (HTML5 / Tailwind / D3)
│   ├── index.html              # Main application view & HUD
│   ├── css/                    # Monospace, academic styling & layout sheets
│   ├── js/                     # Modular vanilla JS controllers & D3 graph renderer
│   └── assets/                 # Icons, fonts, and static assets
├── docs/                       # Architectural specifications and deep dives
│   ├── rezno_brain_spine_deep_dive.md
│   ├── walkthrough.md
│   └── legacy/                 # Historical prototyping notes and specs
├── legacy/
│   └── reflex_v1/              # Safely archived legacy Reflex & Streamlit files
├── tests/                      # Automated unittest & pytest verification suite
│   ├── test_backend_core.py    # Unit tests for core algorithms
│   ├── test_api_endpoints.py   # FastAPI TestClient HTTP/SSE tests
│   ├── test_shims.py           # Zero-breakage backward compatibility shim tests
│   └── test_smoke.py           # Repo structure & environment sanity checks
├── Version_1/                  # Zero-breakage backward-compatibility shims
├── pyproject.toml              # Modern Python packaging configuration (>=3.11)
├── requirements.txt            # Pinned production & development dependencies
├── DECISIONS.md                # Architectural Decision Records (ADRs)
├── PROJECT.md                  # Master technical reference & domain model
├── GEMINI.md                   # Agent guardrails and Git safety policy
└── README.md                   # Public repository showcase & benchmark guide
```

---

## 3. Developer & Agent Execution Cheat Sheet

All commands should be run from the repository root using the virtual environment:

### Environment Setup
```bash
# Using uv (recommended)
uv sync

# Using standard virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the Dev Server (API + Frontend UI)
```bash
python3 -m uvicorn backend.api.main:app --reload --port 8000
# Open http://localhost:8000 in your browser
```

### Run CLI Research Pipeline
```bash
python3 -m backend.cli --query "Speculative decoding in LLM inference" --top-k 10
# Or via legacy shim
python3 Version_1/run.py --query "Speculative decoding in LLM inference" --top-k 10
```

### Run Test Suites
```bash
# Run all unit tests
python3 -m unittest discover tests/

# Run specific test suites
python3 -m unittest tests/test_shims.py
python3 -m unittest tests/test_backend_core.py
python3 -m unittest tests/test_api_endpoints.py
```

### Run Evaluation Benchmarks
```bash
python3 -m backend.evaluation.evaluate --top-k 20 --expand
# Or via legacy shim
python3 Version_1/evaluate.py --top-k 20 --expand
```

---

## 4. Non-Negotiable Invariants & Guardrails

1. **Absolute Git Safety Policy**:
   - **NEVER** execute `git commit` or `git push` autonomously under any circumstances.
   - Always present git diffs, verification outputs, and test reports to the human user first.
   - Wait for explicit written approval (e.g., *"commit now"*) before committing.
   - **NEVER** commit directly to the `main` branch. All work must take place on isolated feature branches.

2. **Zero-Breakage Backward Compatibility**:
   - `Version_1/` contains lightweight forwarding shims for all historical modules (`pipeline.py`, `rank.py`, `search.py`, `models.py`, `run.py`, etc.).
   - Any external script or workflow expecting the `Version_1` path must continue to run without interruption.

3. **Resilient Frontend Architecture**:
   - The web interface (`frontend/`) operates in a resilient hybrid mode:
     - Automatically connects to live backend endpoints when available.
     - Gracefully falls back to realistic offline mock data (`js/mock_data.js`) when the backend is unreachable or offline, ensuring zero UI breakage.

4. **Verbatim Grounded Attribution**:
   - In `backend/core/synthesize.py`, every claim in `SupportedClaim` must be verified against an exact, unedited sentence in the source paper's abstract.
   - If an LLM-proposed claim cannot be matched to a verbatim sentence, it must be rejected to guarantee zero hallucinations.
