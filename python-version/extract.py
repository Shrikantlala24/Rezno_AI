from typing import List

from llm import get_llm
from models import Insight, InsightSet, RankedPaper

PROMPT = """Extract the key technical concepts from each paper abstract below.

{papers}

For each paper, return 3-6 concepts: methods, architectures, techniques, tasks, or
problems the paper is about. These must be technical concepts, NOT author names,
institutions, dates, or dataset sizes.

CANONICALIZATION IS THE MOST IMPORTANT PART OF THIS TASK. The concept names are used
to link papers to each other, so the same idea must get the exact same string every
time it appears across all papers:
- Collapse surface variants into one canonical name: "LLMs", "large language models",
  and "Large Language Model" all become "large language models".
- Collapse acronym and expansion into one: "RAG" and "retrieval-augmented generation"
  become "retrieval-augmented generation". Prefer the expanded form unless the acronym
  is overwhelmingly the standard name (e.g. "BERT", "LoRA").
- Use lowercase except for proper model or method names (BERT, LoRA, FlashAttention).
- Prefer the specific concept over the vague one: "rotary position embeddings" beats
  "embeddings".

Before returning, re-read your full concept list across all papers and merge any two
names that mean the same thing.

Return one entry per paper, using the exact arxiv_id shown in brackets."""


def _format(papers: List[RankedPaper]) -> str:
    return "\n\n".join(f"[{p.arxiv_id}] {p.title}\n{p.summary[:1000]}" for p in papers)


def extract_insights(papers: List[RankedPaper]) -> List[Insight]:
    """Block 4 — ONE batched call across all abstracts, not one call per paper."""
    if not papers:
        return []

    model = get_llm().with_structured_output(InsightSet)
    try:
        result = model.invoke(PROMPT.format(papers=_format(papers)))
    except Exception:
        return []

    valid = {p.arxiv_id for p in papers}
    return [
        Insight(
            arxiv_id=i.arxiv_id,
            concepts=[c.strip() for c in i.concepts if c and c.strip()],
        )
        for i in result.insights
        if i.arxiv_id in valid
    ]
