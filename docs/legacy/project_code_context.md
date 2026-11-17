# Rezno AI — Project Code Context & Comprehensive Deployment Blueprint

This document serves as the authoritative, end-to-end technical context for AI Agents and DevOps engineers managing code understanding, CI/CD pipeline creation, containerization, and production deployment of **Rezno AI**.

---

## 1. Executive Summary & Application Vision

### 1.1 What We Are Building
**Rezno AI** is an advanced, full-stack **arXiv Research Assistant & Concept Graph Explorer**. It assists researchers by performing multi-query arXiv retrieval, semantic embedding-based paper ranking, grounded LLM response synthesis with precise sentence-level claim citations, interactive concept graph visualization, and side-by-side run comparison.

### 1.2 User Interface & Core Feature Modules
1. **Header & Shell**: Global controls, active session status indicator, and dark/light mode toggle.
2. **Conversation Rail (Left Panel, 30% Width)**:
   - Interactive research query composer.
   - Live step-by-step progress logging during query routing, paper fetching, ranking, and answer synthesis.
   - Chat message thread with grounded synthesis blocks, collapsible sentence-level claim evidence accordions, and fallback warnings for ungrounded live web searches.
3. **Research Workspace Rail (Right Panel, 70% Width)**:
   - **Papers Tab**: Filterable paper cards, relevance scoring, screening workflow controls (`unreviewed`, `keep`, `maybe`, `skip`), user research notes, arXiv links, BibTeX export, and interactive citation chaining (fetching forward citing / backward reference papers via OpenAlex/arXiv APIs).
   - **Concept Graph Tab**: High-performance 2D force-directed node graph (WebGL/Canvas via `react-force-graph-2d`), layout controls (Force vs. Radial algorithms), connection filters (`MENTIONS` vs `SIMILAR_TO`), node inspection drawer, and JSON graph export.
   - **Compare Tab**: Side-by-side comparative analysis between any two research runs in the session (common vs. unique papers and extracted concepts).
   - **Settings Popover**: Real-time slider controls for search depth (`per_query`, `top_k`, `num_queries`) and answer detail (`response_length`).

---

## 2. Technical Stack & Dependencies

| Component Layer | Technology | Key Packages & Versions | Purpose / Description |
| :--- | :--- | :--- | :--- |
| **App Framework** | [Reflex](https://reflex.dev) | `reflex[db]==0.9.6.post2` | Python web app framework compiling frontend to Next.js/React and managing backend state via WebSockets. |
| **Frontend Runtime** | Bun / Node.js | Bun `v1.3.13` (or Node.js 18+) | Installed automatically in `.web/` by Reflex for compiling React components & bundle assets. |
| **Graph Component** | react-force-graph-2d | Custom wrapper `ForceGraph2D` | Canvas 2D WebGL interactive force-directed graph running at 60fps browser-side. |
| **Embedding / Ranker**| Sentence Transformers | `sentence-transformers`, `numpy` | `all-MiniLM-L6-v2` embedding generation for cosine-similarity semantic ranking. |
| **LLM Integrations** | LangChain / Google / Anthropic | `langchain`, `langchain-google-genai`, `langchain-anthropic` | Multi-query expansion, intent routing, structured output extraction, and grounded answer synthesis. |
| **Data Provider** | arXiv API | `arxiv` | Programmatic research paper search & metadata fetch with bounded HTTP timeouts. |
| **Styling & Design** | Tailwind CSS v4 / Radix Themes | `TailwindV4Plugin`, `RadixThemesPlugin` | Modern HSL-tailored color tokens, responsive CSS flex/grid layouts, dark mode utilities. |
| **Static Type System**| Pyright | `pyrightconfig.json` | Configured with `"typeCheckingMode": "basic"` to prevent descriptor false-positives on Reflex `rx.State` fields. |

---

## 3. Architecture & Codebase Map

```
Rezno_AI/
├── pyproject.toml              # Dependency definitions & Python environment metadata
├── pyrightconfig.json          # Pyright config suppressing Reflex descriptor false-positives
├── rxconfig.py                 # Reflex app settings & plugins (TailwindV4, RadixThemes)
├── requirements.txt            # Explicit pip dependency lock list
├── .env.example                # Template for LLM API keys & environment configs
│
├── app/                        # Main Reflex Application Package
│   ├── app.py                  # Entrypoint, page routes (`/`), root layout container
│   ├── research_backend.py     # Resilient adapter connecting Reflex UI to pipeline modules
│   ├── workspace_serialize.py  # Data converters (pipeline backend models <-> UI plain dicts)
│   ├── graph_layout.py         # Pure-Python force & radial graph layout calculations
│   │
│   ├── components/             # Modular UI Component Views
│   │   ├── header.py           # Top navigation bar, session status, theme toggle
│   │   ├── conversation_rail.py# Left panel chat container, flow steps, query input
│   │   ├── message_list.py     # User & assistant chat bubbles, claim evidence drawer
│   │   ├── workspace_rail.py   # Right panel workspace container, tab bar, run status strip
│   │   ├── papers_tab.py       # Paper cards list, screening buttons, citation chaining
│   │   ├── graph_tab.py        # Concept Graph canvas, toolbar, legend, selection drawer
│   │   ├── compare_tab.py      # Run comparison matrix & diff calculation UI
│   │   ├── settings_popover.py # Search hyperparameter controls & session resets
│   │   └── force_graph.py      # Reflex wrapper component (`ForceGraph2D`) for `react-force-graph-2d`
│   │
│   └── states/                 # Reactive State Management (rx.State)
│       ├── conversation_state.py # Message state, async thread worker, thinking progress
│       ├── workspace_state.py  # Session paper runs (up to 10), screening status, BibTeX export
│       ├── graph_state.py      # Graph layout mode, zoom, node selection, canvas callbacks
│       ├── compare_state.py    # Side-by-side run selection & diff calculation
│       ├── shell_state.py      # Active workspace tab selection ('papers' | 'graph' | 'compare')
│       └── theme_state.py      # Global dark/light mode toggle
│
├── pipeline.py                 # Core deterministic pipeline orchestration (`run_pipeline`)
├── plan_query.py               # LLM query planner (expands 1 prompt into N arXiv search queries)
├── search.py                   # Concurrent arXiv query searcher with per-query retry isolation
├── rank.py                     # MiniLM vector embedding paper ranking engine
├── synthesize.py               # Grounded answer synthesis & claims extractor
├── route.py                    # Intent classifier (`new_search` vs `follow_up_grounded` vs `follow_up_general`)
├── citations.py                # Reference/citing paper lookup adapter
├── bibtex.py                   # BibTeX string generator for retrieved papers
├── models.py                   # Core Pydantic data schemas (ArxivPaper, RankedPaper, Synthesis, etc.)
└── llm.py                      # Dynamic LLM provider loader (Gemini vs Anthropic)
```

---

## 4. Operational Data Flow & Execution Pipelines

### 4.1 Search Pipeline Execution Sequence (`run_pipeline`)
```
[User Input] 
     │
     ▼
1. plan_query() ───► Expands 1 prompt into N targeted arXiv boolean query strings
     │
     ▼
2. search()     ───► Parallel arXiv API fetch (ThreadPoolExecutor, timeout-isolated)
     │
     ▼
3. rank()       ───► Sentence-Transformers (`all-MiniLM-L6-v2`) cosine vector ranking
     │
     ▼
4. synthesize() ───► LLM produces grounded summary + sentence-level claim citations
     │
     ▼
5. build_graph()───► Extracts concept/paper nodes & MENTIONS/SIMILAR_TO relationship edges
     │
     ▼
6. run_to_ui()  ───► Serializes results to UI dicts & updates WorkspaceState / GraphState
```

### 4.2 LLM Provider Resolution Logic (`llm.py`)
The application automatically selects the active LLM backend using the following precedence:
1. `LLM_MODEL` environment variable (if explicitly set, e.g. `google_genai:gemini-2.5-pro`).
2. `GOOGLE_API_KEY` (if present, defaults to `gemini-2.5-flash`).
3. `ANTHROPIC_API_KEY` (if present, fallback to Claude models).
4. If **no valid key** is supplied, `research_backend.py` gracefully catches missing credentials and surfaces a user-facing warning without crashing the backend process.

---

## 5. Environment & Runtime Specifications

### 5.1 Environment Variables Matrix

| Variable Name | Required? | Default / Example | Purpose |
| :--- | :--- | :--- | :--- |
| `GOOGLE_API_KEY` | Recommended | `AIzaSy...` | Primary key for Gemini LLM query expansion, synthesis, & routing. |
| `ANTHROPIC_API_KEY` | Optional | `sk-ant-...` | Fallback key if Google Gemini is not configured. |
| `LLM_MODEL` | Optional | `google_genai:gemini-2.5-pro` | Explicit model string override. |
| `PORT` | Production | `8000` | Port for Reflex backend engine (WebSockets/API). |
| `FRONTEND_PORT` | Production | `3000` | Port for frontend Next.js server (if hosted separately). |
| `API_URL` | Production | `http://backend.domain.com:8000` | Public backend URL for frontend WebSocket connections. |

### 5.2 Resource & Hardware Requirements
- **CPU**: Minimum 2 Cores (4 Cores recommended for parallel arXiv HTTP requests & vector embedding computations).
- **RAM**: Minimum 4 GB (8 GB recommended; `sentence-transformers` loads PyTorch weights into memory).
- **Disk**: 5 GB available storage (for Python virtualenv, cached HuggingFace models, `.web` node modules).
- **GPU**: Optional (CPU execution for `all-MiniLM-L6-v2` is lightweight and fast).

---

## 6. Containerization Blueprint (Docker)

To deploy **Rezno AI** reliably in containerized environments (AWS ECS, GCP Cloud Run, Kubernetes, Docker Swarm), use the following multi-stage build strategy.

### 6.1 Recommended Production `Dockerfile`

```dockerfile
# ==========================================
# Stage 1: Build Frontend (.web Next.js bundle)
# ==========================================
FROM oven/bun:1.1 as builder

WORKDIR /app
COPY pyproject.toml requirements.txt rxconfig.py pyrightconfig.json ./
COPY app ./app
COPY assets ./assets

# Install Python & Reflex CLI to build frontend assets
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv && \
    python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install reflex[db]==0.9.6.post2

ENV PATH="/opt/venv/bin:$PATH"

# Pre-compile Reflex frontend assets into static bundle
RUN reflex export --frontend-only --no-zip

# ==========================================
# Stage 2: Final Runtime Container
# ==========================================
FROM python:3.11-slim as runner

# Prevent Python from writing .pyc files and buffer outputs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000 \
    FRONTEND_PORT=3000

WORKDIR /app

# Install system runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code & pre-built frontend
COPY . .
COPY --from=builder /app/.web ./.web

# Expose HTTP / WebSocket Ports
EXPOSE 8000 3000

# Health check endpoint for container orchestrators
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/ping || exit 1

# Launch production Reflex application server
CMD ["reflex", "run", "--env", "prod"]
```

---

## 7. Complete CI/CD Pipeline Specification

Below is the complete GitHub Actions workflow configuration (`.github/workflows/ci-cd.yml`) designed for automated linting, testing, Docker image creation, and production deployment.

### 7.1 `.github/workflows/ci-cd.yml`

```yaml
name: Rezno AI CI/CD Pipeline

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ----------------------------------------------------
  # Job 1: Code Quality, Linting & Type Validation
  # ----------------------------------------------------
  lint-and-typecheck:
    name: Lint & Typecheck
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt pyright black flake8 pytest

      - name: Run Black Code Formatting Check
        run: |
          black --check app pipeline.py search.py rank.py route.py synthesize.py

      - name: Run Flake8 Linter
        run: |
          flake8 app pipeline.py search.py rank.py route.py synthesize.py --max-line-length=100 --ignore=E203,W503

      - name: Run Pyright Type Checker
        run: |
          pyright

  # ----------------------------------------------------
  # Job 2: Automated Testing
  # ----------------------------------------------------
  test:
    name: Run Unit & Integration Diagnostics
    runs-on: ubuntu-latest
    needs: lint-and-typecheck
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt pytest

      - name: Run Diagnostic Test Suite
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          python diagnostic_test.py
          pytest --ignore=.web --ignore=venv

  # ----------------------------------------------------
  # Job 3: Docker Build & Push (on main branch)
  # ----------------------------------------------------
  build-and-push:
    name: Build & Push Container Image
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract Docker Metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,format=long
            type=raw,value=latest

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and Push Docker Image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ----------------------------------------------------
  # Job 4: Continuous Deployment Trigger
  # ----------------------------------------------------
  deploy:
    name: Trigger Production Deployment
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to Cloud Hosting (Example: Webhook Trigger)
        run: |
          echo "Triggering production deployment roll-out..."
          # Insert deployment webhooks (e.g. Render, Railway, AWS ECS update service, or kubectl rollout)
```

---

## 8. Production Deployment & Monitoring Strategies

### 8.1 Single-Server vs Decoupled Deployments

1. **Unified Deployment (Recommended for simplicity)**:
   - Run `reflex run --env prod` in a single container.
   - Frontend static assets are served on port `3000`, while WebSockets and backend state logic run on port `8000`.
   - Put a reverse proxy like **Nginx**, **Caddy**, or **Cloudflare** in front to terminate TLS and forward WebSocket traffic (`/websocket`).

2. **Decoupled Deployment (Scalable production)**:
   - **Frontend**: Export static Next.js assets (`reflex export`) and host on **Vercel**, **Netlify**, or AWS **S3 + CloudFront**.
   - **Backend**: Host the Python Reflex server (`reflex run --backend-only`) on AWS **ECS**, **Render**, **Railway**, or **GCP Cloud Run**.

### 8.2 Reverse Proxy Configuration (Nginx Example)
```nginx
server {
    listen 80;
    server_name research.yourdomain.com;

    # Frontend HTTP Traffic
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Reflex Backend WebSocket Traffic
    location /_event {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 9. Troubleshooting & Common Pitfalls

1. **Pyright `Field` Descriptor False Positives**:
   - *Symptom*: Red squiggles on state assignments like `self.selected_node_id = ""`.
   - *Fix*: Ensure `pyrightconfig.json` is present in the workspace root with `"reportAttributeAccessIssue": "none"`.

2. **ArXiv API Rate Limits & Timeouts**:
   - *Symptom*: Searches hanging or returning connection reset errors.
   - *Fix*: `search.py` wraps `arxiv.Client` with a custom `_TimeoutSession` (15s timeout limit) and isolates per-query failures using `ThreadPoolExecutor`.

3. **Memory Spikes during Model Initialization**:
   - *Symptom*: Container OOM (Out-Of-Memory) kill during initial search.
   - *Fix*: Ensure the hosting container has at least 4 GB RAM available for HuggingFace `sentence-transformers` model allocation.

---

## 10. Developer & AI Agent Quick Reference

- **Run Dev Server**: `reflex run`
- **Run Diagnostic Checks**: `python diagnostic_test.py`
- **Run Type Checker**: `pyright`
- **Export Production Web Bundle**: `reflex export`
- **Clear App State & Build Cache**: `rm -rf .web`

---

## 11. Zerops Native PaaS Deployment Guide

### 1.1 Overview
[Zerops](https://zerops.io) provides zero-downtime, auto-scaling deployment using a declarative [`zerops.yaml`](file:///d:/WORK FROM HOME/Github 2/Projects/Rezno_AI/zerops.yaml) configuration located at the repository root.

### 1.2 Step-by-Step Zerops Setup
1. **Create Project & Service in Zerops Dashboard**:
   - Create a new project (e.g., `rezno-ai-prod`).
   - Add a **Python** service named `rezno-ai` (matching the `setup: rezno-ai` key in `zerops.yaml`).
2. **Configure Environment Variables**:
   - In the Zerops dashboard for the `rezno-ai` service, set:
     - `GOOGLE_API_KEY`: Secret API key for Gemini models.
     - `ANTHROPIC_API_KEY`: (Optional) Fallback API key.
     - `PORT`: `8000`
     - `FRONTEND_PORT`: `3000`
3. **Connect Repository**:
   - Link your GitHub repository to Zerops CI/CD.
   - Set trigger to push on `main`. Zerops will automatically execute the build and deploy steps defined in `zerops.yaml`.

