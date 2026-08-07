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


class Synthesis(BaseModel):
    summary: str
    citations: List[str]


class QueryPlan(BaseModel):
    """Block 1 structured output."""

    queries: List[str] = Field(description="arXiv boolean query variants, 3-4 of them")


class Insight(BaseModel):
    arxiv_id: str
    concepts: List[str]


class InsightSet(BaseModel):
    """Block 4 structured output — one batched call covers every paper."""

    insights: List[Insight]


class Route(BaseModel):
    intent: Literal["new_search", "follow_up"]


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
