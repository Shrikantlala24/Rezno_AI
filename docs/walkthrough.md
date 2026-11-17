# Walkthrough: Rezno AI — Conceptual & Technical Understanding

## What Was Accomplished
We conducted a comprehensive, rigorous investigation of Rezno AI's entire codebase, isolating the **core computational and intelligence engine ("the brain and spine")** from the presentation layers. 

We documented the entire system in two dedicated master artifacts:
1. [rezno_conceptual_and_technical_plan.md](file:///home/gg31/.gemini/antigravity-cli/brain/700b47a6-3d96-4d65-974a-32e34c058a2f/rezno_conceptual_and_technical_plan.md) — The approved architectural execution plan.
2. [rezno_brain_spine_deep_dive.md](file:///home/gg31/.gemini/antigravity-cli/brain/700b47a6-3d96-4d65-974a-32e34c058a2f/rezno_brain_spine_deep_dive.md) — The master deep-dive covering conceptual problem analysis, algorithmic mechanics, and evaluation methodology.

---

## Key Takeaways from the Breakdown

### 1. The Conceptual Problem (The "Why")
- **The Lexical Mismatch**: arXiv only indexes titles/abstracts using boolean Apache Lucene matching. Natural language inquiries (e.g. *"how to make LLMs remember long documents"*) fail because preprints use formal terminology (*"sparse sliding-window attention"*).
- **The Hallucination Trap**: Generalist LLMs invent citations or mix up metrics across papers. Academic rigor demands 100% auditability.
- **The Cognitive Overload**: Thousands of preprints monthly cannot be triaged linearly. Researchers need topological clustering (shared concepts and direct architectural relatives).

### 2. The Core Technical Engine (The "How")
- **Sequential Pipeline (`pipeline.py`)**: Strict, deterministic execution (`plan_query` ➔ `search` ➔ `rank` ➔ `synthesize` ➔ `graph`) that eliminates the cost, latency, and indeterminacy of autonomous agent loops.
- **Multi-Query Planning (`plan_query.py`)**: Converts 1 user prompt into 3–4 Lucene boolean queries combining canonical terms, methods, and category scopes (`cat:cs.CL`).
- **Resilient Retrieval (`search.py`)**: Custom `_TimeoutSession` (25s cap) with threaded per-query failure isolation and empty-result fallbacks.
- **Dense Vector Re-Ranking (`rank.py`)**: Embeds title + summary using local `all-MiniLM-L6-v2` (384-dim) and performs unit-normalized cosine dot products ($D \cdot q^T$) to filter hundreds of candidates down to top-20 precision.
- **Verbatim Claim Verification (`synthesize.py`)**: Pydantic structured output (`SupportedClaim`) forcing the LLM to extract the *exact verbatim sentence* from the abstract supporting every assertion.
- **Bipartite Knowledge Graph (`graph.py`)**: 
  - Directed `MENTIONS` edges: `Paper ──▶ Concept`.
  - Undirected `SIMILAR_TO` edges: `Paper ──▶ Paper` using dynamic top-k nearest neighbors in embedding space to prevent visual graph saturation.
- **Intent Routing (`route.py`)**: Heuristic shortcuts + LLM classifier routing user messages to grounded abstract answers, broad Tavily web search, or fresh arXiv retrieval.
- **Academic Benchmark System (`evaluate.py`)**: Mathematically decouples retrieval quality (**Pool Recall**) from re-ranking precision (**Recall@k**).

---

## File Links
- Master Technical Document: [rezno_brain_spine_deep_dive.md](file:///home/gg31/.gemini/antigravity-cli/brain/700b47a6-3d96-4d65-974a-32e34c058a2f/rezno_brain_spine_deep_dive.md)
- Core Pipeline: [pipeline.py](file:///home/gg31/Projects/contr/Rezno_AI/Version_1/pipeline.py)
- Vector Ranker: [rank.py](file:///home/gg31/Projects/contr/Rezno_AI/Version_1/rank.py)
- Graph Engine: [graph.py](file:///home/gg31/Projects/contr/Rezno_AI/Version_1/graph.py)
- Claim Synthesizer: [synthesize.py](file:///home/gg31/Projects/contr/Rezno_AI/Version_1/synthesize.py)
- Evaluation Harness: [evaluate.py](file:///home/gg31/Projects/contr/Rezno_AI/Version_1/evaluate.py)
