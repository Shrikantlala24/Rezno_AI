"""The fixed sequential pipeline. Every block always runs, in this order.

There is no LLM orchestration here by design: with a single fixed path there is no
decision for a model to make, so a router-LLM would only add latency and cost.
"""

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from graph import build_graph
from models import ConceptGraph, Insight, RankedPaper, Synthesis
from plan_query import plan_query
from rank import rank
from search import search
from synthesize import analyze_research

Progress = Optional[Callable[[str], None]]


@dataclass
class PipelineResult:
    query: str
    queries: List[str]
    candidate_count: int
    papers: List[RankedPaper]
    insights: List[Insight] = field(default_factory=list)
    graph: Optional[ConceptGraph] = None
    synthesis: Optional[Synthesis] = None
    search_status: str = "success"
    search_error: str | None = None

    @property
    def concepts(self) -> List[str]:
        seen: dict[str, None] = {}
        for insight in self.insights:
            for c in insight.concepts:
                seen.setdefault(c, None)
        return list(seen)


def run_pipeline(
    query: str,
    top_k: int = 20,
    per_query: int = 80,
    num_queries: int = 4,
    show: int = 8,
    expand: bool = True,
    with_graph: bool = True,
    with_synthesis: bool = True,
    response_length: str = "standard",
    on_progress: Progress = None,
) -> PipelineResult:
    def step(message: str) -> None:
        if on_progress:
            on_progress(message)

    step("Planning search queries")
    queries = plan_query(query, num_queries=num_queries) if expand else [query]

    step("Searching arXiv")
    search_result = search(queries, per_query=per_query, on_progress=step)
    if not search_result.papers and query not in queries:
        step("Retrying the original query")
        fallback = search([query], per_query=per_query, on_progress=step)
        # The original query is the final authority: if it fails, expose that
        # failure instead of incorrectly reporting the planner's empty result.
        search_result = fallback
    candidates = search_result.papers

    step(f"Ranking {len(candidates)} candidates")
    papers = rank(candidates, query, top_k=top_k)

    result = PipelineResult(
        query=query,
        queries=queries,
        candidate_count=len(candidates),
        papers=papers,
        search_status=search_result.status,
        search_error=(search_result.errors[0] if search_result.errors else None),
    )

    if with_synthesis:
        step("Analyzing papers and synthesizing answer")
        result.synthesis, result.insights = analyze_research(
            query, papers, top_n=show, response_length=response_length
        )

    if with_graph and papers:
        step("Building concept graph")
        result.graph = build_graph(papers, result.insights)

    return result
