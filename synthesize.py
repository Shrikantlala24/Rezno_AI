from typing import List

from llm import get_llm
from models import RankedPaper, SupportedClaim, Synthesis
from web_search import web_search

# Length instruction injected into prompts based on response_length parameter
_LENGTH_INSTRUCTIONS = {
    "brief": (
        "Length: Respond in 1-2 sentences only. Be concise and direct. "
        "Include at most 2 key claims."
    ),
    "standard": (
        "Length: Respond in 3-5 sentences. Include a reasonable set of supporting claims."
    ),
    "detailed": (
        "Length: Provide a thorough 5-8 sentence synthesis. Surface as many supported claims "
        "as possible. Where papers disagree, explain both positions."
    ),
}

PROMPT = """You are synthesizing a research summary for the research question below.

Question: {query}

Papers:
{papers}

{length_instruction}

Task:
1. Write a prose summary answering the question, citing papers inline by arxiv_id in square brackets (e.g. [2401.12345]).
2. Provide a list of key claims made in your answer. For each claim, specify:
   - claim: concise statement of the finding
   - arxiv_id: paper ID supporting it
   - supporting_sentence: the EXACT verbatim sentence from the paper's abstract that supports the claim.
If no sentence in the abstract supports a claim, do not include that claim."""

FOLLOW_UP_PROMPT = """You are answering a follow-up question about research papers that have already been retrieved.

Papers currently in context:
{papers}

Key concepts across these papers: {concepts}

Conversation so far:
{history}

Follow-up question: {question}

{length_instruction}

Task:
1. Write an answer grounded ONLY in these abstracts.
2. Provide a list of key claims in your answer. For each claim, specify the supporting arxiv_id and the EXACT verbatim sentence from that abstract."""

WEB_SEARCH_PROMPT = """You are answering a general question in a research assistant chat using live web search results.

Question: {question}

Web Search Results:
{web_context}

Conversation so far:
{history}

Answer the question clearly in 2-4 sentences based on the web search results above. Do NOT invent arXiv IDs or paper citations."""


def _format_papers(papers: List[RankedPaper]) -> str:
    blocks = []
    for p in papers:
        blocks.append(f"[{p.arxiv_id}] {p.title}\nAbstract: {p.summary[:1200]}")
    return "\n\n".join(blocks)


def synthesize(
    query: str,
    papers: List[RankedPaper],
    top_n: int = 8,
    response_length: str = "standard",
) -> Synthesis:
    top = papers[:top_n]
    if not top:
        return Synthesis(summary="No papers found for this query.", citations=[], claims=[])

    formatted = _format_papers(top)
    length_instruction = _LENGTH_INSTRUCTIONS.get(response_length, _LENGTH_INSTRUCTIONS["standard"])

    try:
        model = get_llm().with_structured_output(Synthesis)
        res = model.invoke(PROMPT.format(query=query, papers=formatted, length_instruction=length_instruction))
        if not res.citations:
            res.citations = [p.arxiv_id for p in top]
        return res
    except Exception:
        response = get_llm().invoke(PROMPT.format(query=query, papers=formatted, length_instruction=length_instruction))
        return Synthesis(
            summary=response.text().strip(),
            citations=[p.arxiv_id for p in top],
            claims=[],
        )


def follow_up(
    question: str,
    history: List,
    papers: List[RankedPaper],
    concepts: List[str],
    top_n: int = 8,
    response_length: str = "standard",
) -> Synthesis:
    """Answer grounded in papers in session context with evidence-linked claims."""
    top = papers[:top_n]
    transcript = "\n".join(
        f"{m.role if hasattr(m, 'role') else m['role']}: {m.content if hasattr(m, 'content') else m['content']}"
        for m in history
    ) or "(none)"

    formatted = _format_papers(top)
    length_instruction = _LENGTH_INSTRUCTIONS.get(response_length, _LENGTH_INSTRUCTIONS["standard"])
    prompt_text = FOLLOW_UP_PROMPT.format(
        papers=formatted,
        concepts=", ".join(concepts) or "(none extracted)",
        history=transcript,
        question=question,
        length_instruction=length_instruction,
    )

    try:
        model = get_llm().with_structured_output(Synthesis)
        res = model.invoke(prompt_text)
        if not res.citations:
            res.citations = [p.arxiv_id for p in top]
        return res
    except Exception:
        response = get_llm().invoke(prompt_text)
        return Synthesis(
            summary=response.text().strip(),
            citations=[p.arxiv_id for p in top],
            claims=[],
        )


def follow_up_general(
    question: str,
    history: List,
) -> str:
    """Answer using Tavily web search integration."""
    transcript = "\n".join(
        f"{m.role if hasattr(m, 'role') else m['role']}: {m.content if hasattr(m, 'content') else m['content']}"
        for m in history
    ) or "(none)"

    # Run Tavily web search
    search_results = web_search([question], search_depth="advanced")

    web_snippets = []
    if search_results:
        for item in search_results:
            if "answer" in item and item["answer"]:
                web_snippets.append(f"Summary Answer: {item['answer']}")
            for r in item.get("results", [])[:4]:
                web_snippets.append(f"- [{r.get('title')}]({r.get('url')}): {r.get('content')}")

    web_context = "\n".join(web_snippets) if web_snippets else "(No web results retrieved)"

    response = get_llm().invoke(
        WEB_SEARCH_PROMPT.format(
            question=question,
            web_context=web_context,
            history=transcript,
        )
    )
    return response.text().strip()


