from typing import List

import numpy as np

from models import ConceptGraph, GraphEdge, GraphNode, Insight, RankedPaper
from rank import embed

SIMILAR_K = 3


def build_graph(
    papers: List[RankedPaper], insights: List[Insight], k: int = SIMILAR_K
) -> ConceptGraph:
    """Block 5 — paper and concept nodes, MENTIONS edges, top-k SIMILAR_TO edges.

    SIMILAR_TO is top-k per paper rather than a similarity threshold on purpose: all
    these papers came from one query, so they sit in a narrow high-similarity band and a
    fixed cutoff would swing between a near-complete graph and an empty one across
    queries. Top-k gives a consistently readable graph either way.
    """
    if not papers:
        return ConceptGraph(nodes=[], edges=[])

    nodes: List[GraphNode] = [
        GraphNode(id=p.arxiv_id, label=p.title, type="paper") for p in papers
    ]
    edges: List[GraphEdge] = []

    seen_concepts: set[str] = set()
    known_papers = {p.arxiv_id for p in papers}
    for insight in insights:
        if insight.arxiv_id not in known_papers:
            continue
        for concept in insight.concepts:
            node_id = f"concept::{concept.lower()}"
            if node_id not in seen_concepts:
                seen_concepts.add(node_id)
                nodes.append(GraphNode(id=node_id, label=concept, type="concept"))
            edges.append(
                GraphEdge(source=insight.arxiv_id, target=node_id, type="MENTIONS")
            )

    edges.extend(_similar_edges(papers, k))
    return ConceptGraph(nodes=nodes, edges=edges)


def _similar_edges(papers: List[RankedPaper], k: int) -> List[GraphEdge]:
    if len(papers) < 2:
        return []

    vecs = embed([f"{p.title}. {p.summary}" for p in papers])
    sims = vecs @ vecs.T
    np.fill_diagonal(sims, -np.inf)  # never link a paper to itself

    k = min(k, len(papers) - 1)
    edges: List[GraphEdge] = []
    emitted: set[frozenset] = set()

    for i, paper in enumerate(papers):
        for j in np.argsort(-sims[i])[:k]:
            pair = frozenset((i, int(j)))
            if pair in emitted:  # SIMILAR_TO is undirected — emit each pair once
                continue
            emitted.add(pair)
            edges.append(
                GraphEdge(
                    source=paper.arxiv_id,
                    target=papers[int(j)].arxiv_id,
                    type="SIMILAR_TO",
                )
            )
    return edges
