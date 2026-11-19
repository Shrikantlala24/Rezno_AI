# Research Agent — Simple Sequential Plan

> A research paper discovery tool that takes a user query, searches arxiv, ranks papers by relevance, extracts key insights, builds a knowledge graph, and returns a synthesized summary — all in a fixed sequential pipeline.

**Architecture**: Fixed sequential pipeline (no LLM orchestration)  
**Stack**: ArXiv SDK, sentence-transformers, FAISS, LangChain, Streamlit  
**Scope**: MVP — abstract-only, in-memory, local  

---

## User Flow

```
User types query
  → search arxiv (50 papers)
    → rank papers (BM25 + semantic)
      → extract insights (concepts + embeddings)
        → build knowledge graph (in-memory)
          → synthesize summary (LLM)
            → Streamlit UI (papers + graph + summary)
```

No LLM decisions. No tool routing. Just: **run step 1 → 2 → 3 → 4 → 5 → done.**

---

## Pipeline Steps

### Step 1: arxiv_search
- **Input**: user query string
- **Process**: call arxiv SDK, fetch top 50 papers
- **Output**: `List[ArxivPaper]`

```python
search = arxiv.Search(query=query, max_results=50)
papers = list(client.results(search))
```

---

### Step 2: rank_papers
- **Input**: `List[ArxivPaper]`, user query
- **Process**: BM25 score + semantic similarity → weighted sum → sort
- **Output**: `List[RankedPaper]` (top 20)

```python
final_score = 0.4 * bm25_score + 0.6 * semantic_score
ranked = sorted(papers, key=lambda x: x.score, reverse=True)[:20]
```

---

### Step 3: extract_insights
- **Input**: top 20 `RankedPaper`
- **Process**: spaCy NER on abstracts + MiniLM embeddings
- **Output**: `List[Insight]` — key concepts + 384-dim embeddings per paper

```python
embeddings = model.encode([p.summary for p in papers])
concepts = spacy_extract(p.summary)
```

---

### Step 4: build_knowledge_graph
- **Input**: papers + insights
- **Process**: create nodes (papers, concepts), edges (MENTIONS, SIMILAR_TO if cosine > 0.7)
- **Output**: in-memory graph dict `{nodes, edges}`

```python
graph = {
    "nodes": papers + concepts,
    "edges": mentions_edges + similarity_edges
}
```

---

### Step 5: synthesize_response
- **Input**: query + top 5 ranked papers + graph context
- **Process**: single LLM call (Claude) with structured prompt
- **Output**: `{summary, citations}`

```python
response = claude.messages.create(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": prompt}]
)
```

---

## Data Schemas

```python
class ArxivPaper(BaseModel):
    arxiv_id: str
    title: str
    authors: List[str]
    summary: str
    published: str
    pdf_url: str
    primary_category: str

class RankedPaper(ArxivPaper):
    relevance_score: float
    bm25_score: float
    semantic_score: float

class Insight(BaseModel):
    arxiv_id: str
    key_concepts: List[str]
    embeddings: List[float]   # 384-dim

class GraphData(BaseModel):
    nodes: List[dict]         # {id, type, label}
    edges: List[dict]         # {source, target, type, score}
```

---

## Stack

| Layer | Choice |
|-------|--------|
| Search | `arxiv` SDK |
| Embeddings | `sentence-transformers` MiniLM-L6-v2 |
| Ranking | `scikit-learn` TF-IDF + cosine similarity |
| NLP | `spacy` en_core_web_sm |
| LLM | `anthropic` Claude |
| Graph viz | `pyvis` or `streamlit-agraph` |
| UI | `streamlit` |

---

## File Structure

```
research-agent/
├── pipeline/
│   ├── search.py           # Step 1: arxiv_search
│   ├── rank.py             # Step 2: rank_papers
│   ├── extract.py          # Step 3: extract_insights
│   ├── graph.py            # Step 4: build_knowledge_graph
│   └── synthesize.py       # Step 5: synthesize_response
├── models.py               # Pydantic schemas
├── prompts.py              # LLM prompt templates
├── app.py                  # Streamlit UI
└── requirements.txt
```

---

## MVP Scope

**In**: arxiv search, hybrid ranking, abstract extraction, in-memory graph, Streamlit UI  
**Out**: PDF parsing, Neo4j, S3, Tavily, citation metrics, multi-turn dialogue

---

## Phase 2 Upgrade Path

Once sequential version works, upgrade to harness by:
1. Wrapping each pipeline step as a `Tool`
2. Adding `tools.json` registry
3. Replacing the fixed call sequence with LLM tool-decision loop
