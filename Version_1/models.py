from typing import List, Literal

from pydantic import BaseModel, Field


class ArxivPaper(BaseModel):
    arxiv_id: str
    title: str
    authors: List[str]
    summary: str
    published: str
    pdf_url: str
    abs_url: str
    primary_category: str
    categories: List[str]


class RankedPaper(ArxivPaper):
    relevance_score: float
    status: Literal["unreviewed", "keep", "maybe", "skip"] = "unreviewed"
    note: str | None = None


class SupportedClaim(BaseModel):
    claim: str
    arxiv_id: str
    supporting_sentence: str


class Synthesis(BaseModel):
    summary: str
    citations: List[str]
    claims: List[SupportedClaim] = Field(default_factory=list)


class ResearchAnalysis(Synthesis):
    """One LLM response containing both the answer and graph concepts."""

    insights: List["Insight"] = Field(default_factory=list)



class QueryPlan(BaseModel):
    """Block 1 structured output."""

    queries: List[str] = Field(description="arXiv boolean query variants, 3-4 of them")


class Insight(BaseModel):
    arxiv_id: str
    concepts: List[str]


class Route(BaseModel):
    intent: Literal["new_search", "follow_up_grounded", "follow_up_general"]


class GraphNode(BaseModel):
    id: str
    label: str
    type: Literal["paper", "concept"]


class GraphEdge(BaseModel):
    source: str
    target: str
    type: Literal["MENTIONS", "SIMILAR_TO"]


class ConceptGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class SearchRun(BaseModel):
    id: str
    query: str
    queries: List[str]
    candidate_count: int
    papers: List[RankedPaper]
    insights: List[Insight] = Field(default_factory=list)
    graph: ConceptGraph | None = None
    synthesis: Synthesis | None = None
    search_status: Literal["success", "partial_results", "no_results", "search_error"] = "success"
    search_error: str | None = None
    timestamp: str = ""


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    intent: Literal["new_search", "follow_up_grounded", "follow_up_general"] | None = None
    search_run_id: str | None = None
    is_unsourced: bool = False
    is_fallback: bool = False
    claims: List[SupportedClaim] = Field(default_factory=list)
    response_length: str = "standard"   # "brief" | "standard" | "detailed"


