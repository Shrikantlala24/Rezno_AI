from typing import List

from backend.core.models import (
    Insight,
    RankedPaper,
    ResearchAnalysis,
    SupportedClaim,
    Synthesis,
)
from backend.integrations.llm import generate_structured, generate_text
from backend.integrations.web_search import web_search

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

COMBINED_ANALYSIS_PROMPT = PROMPT + """

3. For every paper, return 3-6 canonical technical concepts in `insights`. Each
insight must contain that paper's arxiv_id and concepts. Use the same normalized
concept string for the same idea across papers. Concepts are methods,
architectures, techniques, tasks, or problems; never authors, institutions, or dates.
"""

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
        blocks.append(f"[{p.arxiv_id}] {p.title}\nAbstract: {p.summary[:850]}")
    return "\n\n".join(blocks)


def analyze_research(
    query: str,
    papers: List[RankedPaper],
    top_n: int = 8,
    response_length: str = "standard",
) -> tuple[Synthesis, List[Insight]]:
    """Generate synthesis, supported claims, and concepts in one LLM call.

    Args:
        query: Original research question.
        papers: Ranked search results.
        top_n: Maximum papers included in the compact prompt.
        response_length: Requested response detail level.

    Returns:
        Synthesis plus validated insights for deterministic graph construction.
    """
    top = papers[:top_n]
    if not top:
        return Synthesis(summary="No papers found for this query.", citations=[]), []
    formatted = _format_papers(top)
    length_instruction = _LENGTH_INSTRUCTIONS.get(response_length, _LENGTH_INSTRUCTIONS["standard"])
    try:
        analysis = generate_structured(
            COMBINED_ANALYSIS_PROMPT.format(query=query, papers=formatted, length_instruction=length_instruction),
            ResearchAnalysis,
            model_type="flash",
        )
    except Exception:
        analysis = None

    if not analysis:
        return (
            Synthesis(
                summary="Research analysis was unavailable. The retrieved papers are listed in the workspace.",
                citations=[paper.arxiv_id for paper in top],
                claims=[],
            ),
            [],
        )

    valid_ids = {paper.arxiv_id for paper in papers}
    paper_map = {paper.arxiv_id: paper for paper in papers}
    filtered_citations = [c for c in (analysis.citations or []) if c in valid_ids]
    citations = filtered_citations or [paper.arxiv_id for paper in top]

    # Invariant: verify supported claims against abstract text
    verified_claims: List[SupportedClaim] = []
    for claim in getattr(analysis, "claims", []):
        if claim.arxiv_id in paper_map:
            abstract = paper_map[claim.arxiv_id].summary
            sentence = claim.supporting_sentence.strip()
            if sentence and (sentence in abstract or sentence in abstract.replace("\n", " ")):
                verified_claims.append(claim)

    insights = [
        Insight(arxiv_id=insight.arxiv_id, concepts=[concept.strip() for concept in insight.concepts if concept.strip()])
        for insight in getattr(analysis, "insights", [])
        if insight.arxiv_id in valid_ids
    ]
    return Synthesis(summary=analysis.summary, citations=citations, claims=verified_claims), insights


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

    paper_map = {p.arxiv_id: p for p in top}
    valid_ids = set(paper_map.keys())
    try:
        res = generate_structured(prompt_text, Synthesis, model_type="flash")
        filtered_citations = [c for c in (getattr(res, "citations", []) or []) if c in valid_ids]
        res.citations = filtered_citations or [p.arxiv_id for p in top]
        verified_claims: List[SupportedClaim] = []
        for claim in getattr(res, "claims", []):
            if claim.arxiv_id in paper_map:
                abstract = paper_map[claim.arxiv_id].summary
                sentence = claim.supporting_sentence.strip()
                if sentence and (sentence in abstract or sentence in abstract.replace("\n", " ")):
                    verified_claims.append(claim)
        res.claims = verified_claims
        return res
    except Exception:
        return Synthesis(
            summary="Unable to generate follow-up response.",
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

    try:
        res_text = generate_text(
            WEB_SEARCH_PROMPT.format(
                question=question,
                web_context=web_context,
                history=transcript,
            ),
            model_type="flash_lite",
        )
        return res_text.strip()
    except Exception as e:
        return f"Unable to generate response from web search results: {e}"
