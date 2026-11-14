# Research Agent — Living Plan

> A harness-based AI agent that takes a research query, autonomously orchestrates a sequence of tools to search arxiv, rank papers by relevance, extract semantic insights, build a knowledge graph of concept relationships, and synthesize a cited summary — all driven by an LLM deciding what to do at each step.

**Project**: Harness-based research paper agent with knowledge graph  
**Stack**: LangChain, ArXiv SDK, sentence-transformers, FAISS, React + Tailwind (UI)  
**Architecture**: LLM-driven harness (LLM decides tool calls, not fixed pipeline)  
**Two build tracks exist**: `plan.md` (this file, harness) and `simple_plan.md` (fixed sequential pipeline, no LLM routing) — sequential is the recommended build-first path, harness is the upgrade  
**Status**: Block-level logic + dependencies mapped, UI direction locked  
**Last updated**: Session 4 — UI design + block internals

---

## 0. UI Design (Locked)

**Not Streamlit for final product** — building in **React + Tailwind** for design control. Streamlit remains fine for internal testing/prototyping only.

**Layout**: Split screen, Obsidian-style
- **Left panel**: Chat interface — user query, pipeline step breadcrumbs (e.g. `arxiv_search → rank_papers → extract_insights`), paper result cards with relevance score badges, synthesized summary with inline arxiv citation links, follow-up input bar
- **Right panel**: Interactive knowledge graph canvas — paper nodes (larger, blue) and concept nodes (smaller, teal), dashed edges for SIMILAR_TO, solid edges for MENTIONS, hover tooltips, filter tabs (Papers/Concepts/Authors), zoom/pan, mini-map
- **Bidirectional linking**: clicking a graph node sends a query to chat; clicking a paper chip in chat highlights it on the graph (Obsidian graph-view behavior)

Reference mockup image saved by user: `ChatGPT_Image_ui_reference.png` — matches this spec closely (dark theme, green status dot, breadcrumb pipeline labels, score badges, legend, minimap).

---

## 1. Vision

User types a research query → LLM orchestrates 6 tools in sequence → returns ranked papers + knowledge graph + synthesized summary.

**User flow**:
```
Input (user query)
  → Prompt template (system context + tools.json)
    → LLM tool-decision (selects tool + builds args)
      → Output parser (validates tool call structure)
        → Loop (calls tool, feeds result to next LLM turn)
          → Storage (S3 + FAISS + in-memory graph)
            → LLM compilation (final synthesis)
              → Streamlit output (papers + graph + summary)
```

---

## 2. Architecture: Harness Pattern

**Key concept**: The LLM is the orchestrator. It reads `tools.json`, decides which tool to call, in what order, with what inputs. We don't hardcode the sequence — the LLM reasons about it.

**Components**:
- `tools.json` — tool registry (name, description, input schema, output schema)
- `Prompt template` — system prompt that injects tools.json + user query + reasoning instructions
- `LLM tool-decision` — Claude/GPT call that returns `{tool_name, tool_args}`
- `Output parser` — Pydantic model that validates + deserializes the LLM's tool call
- `Loop controller` — calls the actual tool function, captures output, feeds back to LLM
- `Compilation LLM` — separate final LLM call for synthesis (different prompt, different goal)

**Why harness over fixed pipeline**:
- Fixed pipeline: `search → rank → extract → graph` always in that order
- Harness: LLM can reorder, skip, or repeat tools based on context
- More flexible for future tools (e.g., add `fetch_pdf` without rewiring logic)

---

## 3. Tool Registry (tools.json) — 6 Tools

| # | Tool | Input | Output | Library |
|---|------|-------|--------|---------|
| 1 | `arxiv_search` | query, max_results, sort_by | List[Paper] | `arxiv` SDK |
| 2 | `rank_papers` | papers, query, top_k | List[RankedPaper] with scores | `scikit-learn`, `sentence-transformers` |
| 3 | `extract_insights` | papers, depth | List[Insight] {concepts, embeddings} | `spacy`, `sentence-transformers` |
| 4 | `build_knowledge_graph` | papers, insights | graph_id, stats | in-memory dict (MVP) |
| 5 | `fetch_graph_context` | graph_id, query | subgraph {papers, concepts, edges} | in-memory traversal |
| 6 | `synthesize_response` | query, papers, insights, context | {response, citations} | `anthropic` / LangChain |

**LOCKED**: All 6 tools confirmed. Pydantic models for all inputs/outputs.

---

## 4. Stack (Locked)

| Layer | Choice | Reason |
|-------|--------|--------|
| LLM orchestration | LangChain (LCEL chains) | Tool calling, memory, chain abstraction |
| LLM model | Claude via Anthropic SDK | Tool-decision + compilation |
| Search | ArXiv SDK (direct) | Structured metadata, free, no dedup needed |
| Embeddings | `sentence-transformers` (MiniLM-L6-v2, 384-dim) | Fast, local, free |
| Vector search | FAISS (local) | No cloud cost, good for MVP |
| Knowledge graph | In-memory dict (MVP) → Neo4j (Phase 2) | Neo4j is overkill for MVP |
| UI | Streamlit | Rapid prototyping |
| Storage | JSON files / session state (MVP) → S3 (Phase 2) | Avoid infra cost for MVP |

**Removed from MVP**: Neo4j, S3, Tavily, Pinecone — all deferred to Phase 2.

---

## 5. Data Schemas (Locked)

### ArxivPaper
```python
class ArxivPaper(BaseModel):
    arxiv_id: str
    title: str
    authors: List[str]
    summary: str           # abstract
    published: str         # ISO datetime
    pdf_url: str
    abs_url: str
    primary_category: str
    categories: List[str]
```

### RankedPaper
```python
class RankedPaper(BaseModel):
    arxiv_id: str
    title: str
    relevance_score: float   # 0-1, hybrid BM25 + semantic
    bm25_score: float
    semantic_score: float
```

### Insight
```python
class Insight(BaseModel):
    arxiv_id: str
    key_concepts: List[str]
    embeddings: List[float]  # 384-dim MiniLM
    summary: str             # LLM one-liner
```

### ToolCall (LLM output — parsed by output parser)
```python
class ToolCall(BaseModel):
    tool_name: Literal["arxiv_search","rank_papers","extract_insights",
                       "build_knowledge_graph","fetch_graph_context","synthesize_response"]
    tool_args: dict
    reasoning: str           # LLM explains why it chose this tool
```

---

## 6. Prompt Design

### System prompt (orchestrator)
```
You are a research agent. Given a user query and a list of tools, decide which tool to call next.

Available tools: {tools_json}

Rules:
- Always start with arxiv_search
- Always rank before extracting
- Always extract before building graph
- Return ONLY valid JSON matching ToolCall schema
- Include your reasoning in the 'reasoning' field
```

### Compilation prompt (final LLM)
```
You are synthesizing a research summary.

Query: {query}
Top papers: {ranked_papers[:5]}
Key concepts: {concepts}
Graph relationships: {graph_edges}

Write a 3-5 sentence summary that:
1. Directly answers the query
2. Cites papers by arxiv_id
3. Highlights concept relationships
4. Notes open research questions
```

---

## 7. Ranking Strategy (Locked)

**Hybrid: BM25 (0.4) + Semantic similarity (0.6)**

- BM25 (term-frequency relevance) catches exact keyword matches in title/abstract
- Semantic similarity (cosine similarity of MiniLM embeddings) catches meaning even without exact words
- Weighted toward semantic (0.6) because research queries are concept-heavy, not keyword-heavy

```python
final_score = 0.4 * normalize(bm25_score) + 0.6 * normalize(semantic_score)
```

**No citation metrics** (Phase 2 — requires Semantic Scholar API).  
**No recency boost** (MVP — query-relevance is more important than newness).

---

## 8. Knowledge Graph (MVP Design)

**In-memory dict** (not Neo4j for MVP):

```python
graph = {
    "nodes": {
        "papers": [{"id": arxiv_id, "title": ..., "score": ...}],
        "concepts": [{"id": concept_name}]
    },
    "edges": [
        {"source": arxiv_id, "target": concept_name, "type": "MENTIONS"},
        {"source": arxiv_id1, "target": arxiv_id2, "type": "SIMILAR_TO", "score": 0.85}
    ]
}
```

**SIMILAR_TO edge threshold**: cosine similarity > 0.7 between paper embeddings.  
**Visualization**: `streamlit-agraph` or `pyvis` (lightweight, no D3 needed).

---

## 8.5 Block-Level Logic & Dependencies (Detailed)

### Block 1 — arxiv_search
- **Package**: `arxiv`
- **Logic**: `arxiv.Client()` handles rate limiting (3s between requests) automatically. `arxiv.Search(query, max_results, sort_by)` builds the query string. `client.results(search)` is a **generator** — lazy paging, only fetches on iteration. PDF URL requires filtering `result.links` for `link.title == "pdf"`.
- **No auth, no API key needed.**

### Block 2 — rank_papers
- **Packages**: `scikit-learn` (TF-IDF as BM25 stand-in), `sentence-transformers` (MiniLM embeddings)
- **Logic — two independent scoring passes, merged**:
  - Pass A (keyword): `TfidfVectorizer` → sparse vectors for query + abstracts → `cosine_similarity` → catches exact terminology matches
  - Pass B (semantic): `SentenceTransformer('all-MiniLM-L6-v2')` encodes query + abstracts into 384-dim vectors → `cosine_similarity` → catches meaning without shared words
  - Merge: `score = 0.4 * normalize(tfidf) + 0.6 * normalize(semantic)` — min-max normalize first since raw ranges differ
- **Model download**: MiniLM (~80MB) auto-downloads on first run via `sentence-transformers`

### Block 3 — extract_insights
- **Packages**: `spacy` (NER), `sentence-transformers` (reuse embeddings from Block 2), `anthropic` (optional deep mode)
- **Logic**: `spacy.load("en_core_web_sm")` → `nlp(abstract)` runs tokenize → POS-tag → NER pipeline → `doc.ents` gives labeled spans (PERSON, ORG, etc.) with no manual regex.
  - **Light mode**: keyword-based concept extraction, no LLM call, cheap
  - **Deep mode**: sends abstract to Claude with structured JSON-extraction prompt, one API call per paper, more accurate, slower
- **Model download**: `en_core_web_sm` (~13MB) needs separate manual download: `python -m spacy download en_core_web_sm` — NOT bundled with pip install, common setup gotcha

### Block 4 — build_knowledge_graph
- **Package**: none (stdlib dict/list for MVP; Neo4j deferred to Phase 2)
- **Logic**:
  - Every paper → node `{id: arxiv_id, type: paper, label: title}`
  - Every unique concept across insights → node `{id: concept_name, type: concept}`
  - **MENTIONS edges**: deterministic for-loop, paper → its extracted concepts
  - **SIMILAR_TO edges**: pairwise cosine similarity between paper embeddings (O(n²), trivial at 20 papers = 190 comparisons); use `sklearn.metrics.pairwise.cosine_similarity` for the whole matrix in one call instead of nested loops. Threshold > 0.7 to create edge.

### Block 5 — fetch_graph_context
- **Package**: none (stdlib traversal)
- **Logic**: Build adjacency dict `{node_id: [connected_ids]}` once from edges for O(1) lookup. Find concept nodes matching query tokens (substring match for MVP, no fuzzy matching yet). BFS outward `hop_distance` steps from those nodes. Returns filtered subgraph — avoids dumping entire graph into LLM context.

### Block 6 — synthesize_response
- **Package**: `anthropic`
- **Logic**: Build prompt with query + top 5 papers (title + arxiv_id only, not full abstracts, to keep tokens low) + concepts + graph edges. **Stateless call** — LLM has no memory of Blocks 1-5, only sees what's explicitly in this prompt. Citations list is built in code from `[p.arxiv_id for p in top_5]`, NOT parsed from LLM's prose — keeps references accurate even if LLM's inline citation formatting slips.

### Dependency Summary Table

| Block | Packages | Downloaded model | Setup gotcha |
|-------|----------|-------------------|---------------|
| 1. arxiv_search | `arxiv` | none | none |
| 2. rank_papers | `scikit-learn`, `sentence-transformers` | MiniLM-L6-v2 (~80MB, auto) | pulls in PyTorch — biggest install |
| 3. extract_insights | `spacy`, `sentence-transformers`, `anthropic` | en_core_web_sm (~13MB, manual) | must run `python -m spacy download en_core_web_sm` separately |
| 4. build_knowledge_graph | none (stdlib) | — | — |
| 5. fetch_graph_context | none (stdlib) | — | — |
| 6. synthesize_response | `anthropic` | — | — |

---

## 9. Open Questions (Harness-specific — To Be Grilled)

- [ ] **LLM tool-decision format**: Structured output (JSON mode) or function-calling API?
- [ ] **Loop termination**: How does the LLM know it's done? (fixed steps vs LLM decides "done")
- [ ] **Error handling in loop**: If tool fails, does LLM retry, skip, or abort?
- [ ] **Context window management**: How much tool output to pass back each turn?
- [ ] **Output parser strictness**: Hard fail on invalid JSON, or LLM self-correction?
- [ ] **Compilation LLM**: Same model as orchestrator, or separate call?
- [ ] **Streamlit state**: How to persist graph between reruns?

---

## 10. MVP Scope

### In-scope (V1)
- ArXiv search (max 50 papers)
- Hybrid ranking (BM25 + semantic)
- Abstract-only insight extraction
- In-memory knowledge graph
- Streamlit UI with paper list + graph viz + summary

### Out-of-scope (Phase 2)
- Full PDF parsing
- Neo4j persistent graph
- S3 storage
- Tavily / other vendors
- Citation metrics
- Multi-turn dialogue

---

## 11. File Structure

```
research-harness/
├── tools/
│   ├── arxiv_search.py
│   ├── rank_papers.py
│   ├── extract_insights.py
│   ├── build_knowledge_graph.py
│   ├── fetch_graph_context.py
│   └── synthesize_response.py
├── harness.py          # main orchestrator loop
├── prompts.py          # all prompt templates
├── parsers.py          # Pydantic models + output parsing
├── tools.json          # tool registry
├── streamlit_app.py    # UI
└── requirements.txt
```

---

## 12. Decisions Log

| Decision | Choice | Locked? |
|----------|--------|---------|
| Architecture | Harness (LLM-driven) | ✅ |
| Search source | ArXiv SDK only | ✅ |
| Ranking | BM25 + semantic (0.4/0.6) | ✅ |
| Embeddings | MiniLM-L6-v2 (384-dim) | ✅ |
| Vector store | FAISS local | ✅ |
| Graph store | In-memory dict (MVP) | ✅ |
| UI | Streamlit | ✅ |
| LLM | Claude (Anthropic SDK) | ✅ |
| Tool count | 6 tools | ✅ |
| Output schema | Pydantic models | ✅ |
| UI framework | React + Tailwind (split screen chat + graph canvas) | ✅ |
| UI layout | Obsidian-style bidirectional chat ↔ graph linking | ✅ |
| LLM tool format | TBD (JSON mode vs function calling) | ❌ |
| Loop termination | TBD | ❌ |
| Error handling | TBD | ❌ |

