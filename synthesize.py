from typing import List

from llm import get_llm
from models import RankedPaper, Synthesis

PROMPT = """You are synthesizing a research summary for the question below.

Question: {query}

Papers:
{papers}

Write 3-5 sentences that directly answer the question, grounded only in these
abstracts. Cite papers inline by arxiv_id in square brackets, e.g. [2401.12345].
Note any disagreement between papers or open questions. Do not speculate beyond
what the abstracts support. Output only the summary text."""

FOLLOW_UP_PROMPT = """You are answering a follow-up question about research papers that
have already been retrieved. Answer only from the abstracts below and the conversation
so far — do not invent papers or findings that are not present here.

Papers currently in context:
{papers}

Key concepts across these papers: {concepts}

Conversation so far:
{history}

Follow-up question: {question}

Answer in 2-5 sentences, citing papers inline by arxiv_id in square brackets. If the
question cannot be answered from these abstracts, say so plainly and suggest what the
user could search for instead."""


def _format_papers(papers: List[RankedPaper]) -> str:
    blocks = []
    for p in papers:
        blocks.append(f"[{p.arxiv_id}] {p.title}\n{p.summary[:1200]}")
    return "\n\n".join(blocks)


def synthesize(query: str, papers: List[RankedPaper], top_n: int = 8) -> Synthesis:
    top = papers[:top_n]
    if not top:
        return Synthesis(summary="No papers found for this query.", citations=[])

    response = get_llm().invoke(PROMPT.format(query=query, papers=_format_papers(top)))

    return Synthesis(
        summary=response.text().strip(),
        citations=[p.arxiv_id for p in top],
    )


def follow_up(
    question: str,
    history: List[dict],
    papers: List[RankedPaper],
    concepts: List[str],
    top_n: int = 8,
) -> str:
    """Answer from papers already in session context — no search, no rank, no extract."""
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in history) or "(none)"
    response = get_llm().invoke(
        FOLLOW_UP_PROMPT.format(
            papers=_format_papers(papers[:top_n]),
            concepts=", ".join(concepts) or "(none extracted)",
            history=transcript,
            question=question,
        )
    )
    return response.text().strip()
