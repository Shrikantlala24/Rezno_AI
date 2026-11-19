"""Serialization between backend research objects and workspace UI dicts."""

import logging
from types import SimpleNamespace


def paper_to_ui(paper) -> dict:
    """Flatten a backend `RankedPaper` into a renderable dict."""
    try:
        authors = [str(a) for a in (getattr(paper, "authors", None) or [])]
        author_line = ", ".join(authors[:5]) + (
            " et al." if len(authors) > 5 else ""
        )
        return {
            "arxiv_id": str(getattr(paper, "arxiv_id", "") or ""),
            "title": str(getattr(paper, "title", "") or ""),
            "authors": authors,
            "author_line": author_line,
            "summary": str(getattr(paper, "summary", "") or ""),
            "published": str(getattr(paper, "published", "") or "")[:10],
            "pdf_url": str(getattr(paper, "pdf_url", "") or ""),
            "abs_url": str(getattr(paper, "abs_url", "") or ""),
            "primary_category": str(
                getattr(paper, "primary_category", "") or ""
            ),
            "relevance_score": float(
                getattr(paper, "relevance_score", 0.0) or 0.0
            ),
            "status": str(
                getattr(paper, "status", "unreviewed") or "unreviewed"
            ),
            "note": str(getattr(paper, "note", "") or ""),
        }
    except Exception as e:
        logging.exception(f"Error: {e}")
        return {
            "arxiv_id": "",
            "title": "Unreadable paper record",
            "authors": [],
            "author_line": "",
            "summary": "",
            "published": "",
            "pdf_url": "",
            "abs_url": "",
            "primary_category": "",
            "relevance_score": 0.0,
            "status": "unreviewed",
            "note": "",
        }


def run_to_ui(run_payload: dict) -> dict:
    """Flatten a stored pipeline run into a renderable workspace run dict."""
    from app import research_backend as rb

    result = run_payload.get("result")
    graph = getattr(result, "graph", None)
    nodes: list = []
    edges: list = []
    citation_ids: list[str] = []
    try:
        nodes = list(getattr(graph, "nodes", None) or [])
        edges = list(getattr(graph, "edges", None) or [])
        synthesis = getattr(result, "synthesis", None)
        citation_ids = [
            str(c) for c in (getattr(synthesis, "citations", None) or [])
        ]
    except Exception as e:
        logging.exception(f"Error: {e}")

    paper_nodes = 0
    concept_nodes = 0
    for node in nodes:
        if str(getattr(node, "type", "")) == "paper":
            paper_nodes += 1
        else:
            concept_nodes += 1

    ui_papers = [paper_to_ui(p) for p in (run_payload.get("papers") or [])]
    paper_by_id = {p["arxiv_id"]: p for p in ui_papers}

    ui_nodes: list[dict] = []
    for node in nodes:
        try:
            node_id = str(getattr(node, "id", "") or "")
            is_paper = str(getattr(node, "type", "")) == "paper"
            paper = paper_by_id.get(node_id, {})
            abs_url = str(paper.get("abs_url", "") or "")
            if is_paper and not abs_url and node_id:
                abs_url = f"https://arxiv.org/abs/{node_id}"
            ui_nodes.append(
                {
                    "id": node_id,
                    "label": str(getattr(node, "label", "") or node_id),
                    "type": "paper" if is_paper else "concept",
                    "pdf_url": str(paper.get("pdf_url", "") or ""),
                    "abs_url": abs_url,
                }
            )
        except Exception as e:
            logging.exception(f"Error: {e}")

    ui_edges: list[dict] = []
    for index, edge in enumerate(edges):
        try:
            kind = str(getattr(edge, "type", "") or "MENTIONS").upper()
            ui_edges.append(
                {
                    "id": f"e{index}",
                    "source": str(getattr(edge, "source", "") or ""),
                    "target": str(getattr(edge, "target", "") or ""),
                    "type": "SIMILAR_TO"
                    if kind == "SIMILAR_TO"
                    else "MENTIONS",
                }
            )
        except Exception as e:
            logging.exception(f"Error: {e}")

    return {
        "id": str(run_payload.get("id", "")),
        "query": str(run_payload.get("query", "")),
        "timestamp": str(run_payload.get("timestamp", "")),
        "search_status": str(run_payload.get("search_status", "ok") or "ok"),
        "search_error": str(getattr(result, "search_error", "") or ""),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "paper_node_count": paper_nodes,
        "concept_node_count": concept_nodes,
        "papers": ui_papers,
        "nodes": ui_nodes,
        "edges": ui_edges,
        "concepts": rb.concepts_for_result(result),
        "citation_ids": citation_ids,
    }


def citation_entries_for(arxiv_id: str) -> list[dict]:
    """Normalize `citations.get_citations` output for the citation panel."""
    from app import research_backend as rb

    if rb.get_citations is None:
        return []
    data = rb.get_citations(arxiv_id) or {}
    out: list[dict] = []
    for kind, key in (("reference", "references"), ("citing", "citations")):
        for entry in data.get(key) or []:
            authors = [str(a) for a in (entry.get("authors") or [])]
            out.append(
                {
                    "kind": kind,
                    "title": str(entry.get("title", "") or ""),
                    "year": str(entry.get("year", "") or ""),
                    "authors": ", ".join(authors[:3]),
                    "arxiv_id": str(entry.get("arxiv_id") or ""),
                }
            )
    return out


def _fallback_bibtex(papers: list[dict]) -> str:
    blocks: list[str] = []
    for paper in papers:
        key = str(paper.get("arxiv_id", "")).replace(".", "_") or "paper"
        authors = " and ".join(paper.get("authors") or [])
        year = str(paper.get("published", ""))[:4]
        blocks.append(
            "@misc{"
            f"{key},\n"
            f"  title={{{paper.get('title', '')}}},\n"
            f"  author={{{authors}}},\n"
            f"  year={{{year}}},\n"
            f"  eprint={{{paper.get('arxiv_id', '')}}},\n"
            "  archivePrefix={arXiv},\n"
            f"  primaryClass={{{paper.get('primary_category', '')}}},\n"
            f"  url={{{paper.get('abs_url', '')}}}\n"
            "}"
        )
    return "\n\n".join(blocks) + "\n"


def bibtex_for(papers: list[dict]) -> str:
    """BibTeX for the UI paper dicts, using the backend generator if reachable."""
    from app import research_backend as rb

    if rb.generate_bibtex is not None:
        try:
            objects = [
                SimpleNamespace(
                    arxiv_id=p.get("arxiv_id", ""),
                    title=p.get("title", ""),
                    authors=list(p.get("authors") or []),
                    summary=p.get("summary", ""),
                    published=p.get("published", ""),
                    pdf_url=p.get("pdf_url", ""),
                    abs_url=p.get("abs_url", ""),
                    primary_category=p.get("primary_category", ""),
                    categories=[p.get("primary_category", "")],
                    relevance_score=float(p.get("relevance_score", 0.0)),
                    status=p.get("status", "unreviewed"),
                    note=p.get("note", ""),
                )
                for p in papers
            ]
            return str(rb.generate_bibtex(objects))
        except Exception as e:
            logging.exception(f"Error: {e}")
    return _fallback_bibtex(papers)
